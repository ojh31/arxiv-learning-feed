import os
import time as time_module
from datetime import datetime, time, timedelta
from pathlib import Path

import feedparser
import markdown as md
import requests
import yaml
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

from llm_judge import judge_papers, summarize_full_text
from scoring import score_entry

load_dotenv()

ROOT = Path(__file__).parent


def get_last_business_day():
    today = datetime.now().date()
    offset = max(1, (today.weekday() + 6) % 7 - 3)
    last_business_day = today - timedelta(days=offset)
    return datetime.combine(last_business_day, time.min)


# arXiv's API rate-limits aggressive clients with HTTP 429. Identify
# ourselves with a User-Agent (anonymous requests are throttled harder) and
# retry with exponential backoff, honoring any Retry-After header.
ARXIV_USER_AGENT = "arxiv-learning-feed/1.0 (mailto:oskar@far.ai)"
ARXIV_MAX_RETRIES = 5
ARXIV_BACKOFF_BASE = 5  # seconds; doubled each retry


def fetch_feed(url: str) -> feedparser.FeedParserDict:
    headers = {"User-Agent": ARXIV_USER_AGENT}
    last_status: int | None = None
    for attempt in range(ARXIV_MAX_RETRIES):
        response = requests.get(url, headers=headers, timeout=60)
        last_status = response.status_code
        if response.status_code == 200:
            return feedparser.parse(response.content)
        if response.status_code in (429, 503) and attempt < ARXIV_MAX_RETRIES - 1:
            retry_after = response.headers.get("Retry-After")
            delay = (
                int(retry_after)
                if retry_after and retry_after.isdigit()
                else ARXIV_BACKOFF_BASE * (2**attempt)
            )
            print(
                f"arXiv feed returned HTTP {response.status_code}, "
                f"retrying in {delay}s (attempt {attempt + 1}/{ARXIV_MAX_RETRIES})"
            )
            time_module.sleep(delay)
            continue
        break
    raise RuntimeError(
        f"arXiv feed returned HTTP {last_status} for {url!r} "
        f"after {ARXIV_MAX_RETRIES} attempts"
    )


def create_content(config: dict) -> str:
    # Fetch the arXiv feed with retries. A non-200 raises in fetch_feed; an
    # empty entry list on a 200 still means a bad response, so fail loudly
    # instead of silently sending an empty digest.
    feed = fetch_feed(config["url"])
    if not feed.entries:
        raise RuntimeError(f"arXiv feed returned no entries for {config['url']!r}")
    last_business_day = get_last_business_day()
    filtered_entries: list[feedparser.FeedParserDict] = [
        entry
        for entry in feed.entries
        if datetime(*entry.published_parsed[:6]) >= last_business_day
    ]

    # Prepare paper data
    papers = []
    for entry in filtered_entries:
        papers.append(
            {
                "title": entry.title,
                "authors": ", ".join(author.name for author in entry.authors),  # type: ignore # noqa: E501
                "summary": entry.summary,
                "link": entry.link,
                "score": score_entry(entry, config),
            }
        )
    papers = sorted(papers, key=lambda x: x["score"], reverse=True)
    print(f"Found {len(papers)} papers from {len(feed.entries)} entries")

    # LLM judge: review papers above keyword score threshold
    llm_threshold = -30
    llm_display_threshold = 50
    candidates = [p for p in papers if p["score"] >= llm_threshold]
    print(f"Sending {len(candidates)} papers to LLM judge (score >= {llm_threshold})")

    reviewed_papers = []
    rest_reviewed = []
    if candidates:
        try:
            reviews = judge_papers(candidates)
            review_by_index = {r["index"]: r for r in reviews}
            for i, paper in enumerate(candidates):
                if i in review_by_index:
                    r = review_by_index[i]
                    enriched = {
                        **paper,
                        "llm_score": r["score"],
                        "llm_summary": r["summary"],
                        "llm_relevance": r["relevance"],
                    }
                    if r["score"] > llm_display_threshold:
                        reviewed_papers.append(enriched)
                    elif r["score"] > 20:
                        rest_reviewed.append(enriched)
            reviewed_papers.sort(key=lambda x: x["llm_score"], reverse=True)
            rest_reviewed.sort(key=lambda x: x["llm_score"], reverse=True)
            print(f"LLM judge: {len(reviewed_papers)} top, {len(rest_reviewed)} rest")

            # Fetch full text and summarize top papers with Haiku
            if reviewed_papers:
                for j, p in enumerate(reviewed_papers):
                    p["_idx"] = j
                print(f"Summarizing {len(reviewed_papers)} top papers with Haiku...")
                full_summaries = summarize_full_text(reviewed_papers)
                for p in reviewed_papers:
                    raw = full_summaries.get(p["_idx"], "")
                    p["full_summary"] = md.markdown(raw) if raw else ""
                    del p["_idx"]
        except Exception as e:
            print(f"LLM judge failed: {e}")

    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader(ROOT))
    template = env.get_template("email_template.html")

    # Render the template with our data
    html_content = template.render(
        papers=papers, reviewed_papers=reviewed_papers, rest_reviewed=rest_reviewed
    )
    return html_content


def send_simple_message(subject: str, html: str):
    api_key = os.environ.get("MAILGUN_API_KEY")
    if not api_key:
        with open(ROOT / "key.txt", "r") as file:
            api_key = file.read().strip()
    response = requests.post(
        "https://api.mailgun.net/v3/sandbox9e8f7a4f3d3d469c9c07ce895892fa11.mailgun.org/messages",  # noqa: E501
        auth=("api", api_key),
        data={
            "from": "arXiv cs.LG+cs.AI<mailgun@sandbox9e8f7a4f3d3d469c9c07ce895892fa11.mailgun.org>",  # noqa: E501
            "to": "oskar@far.ai",
            "subject": subject,
            "html": html,
        },
    )
    print(response.status_code)
    print(response.text)


def main():
    # Parse the yaml config
    with open(ROOT / "config.yaml", "r") as file:
        config = yaml.safe_load(file)
        print(config)
    try:
        html_content = create_content(config)
    except Exception as e:
        print(f"An error occurred: {e}")
        html_content = "<h1>An error occurred</h1>"
        html_content += f"<p>{e}</p>"

    send_simple_message(config["subject"], html_content)


if __name__ == "__main__":
    main()
