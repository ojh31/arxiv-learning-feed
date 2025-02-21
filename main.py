from datetime import datetime, time, timedelta
from pathlib import Path

import feedparser
import requests
import yaml
from jinja2 import Environment, FileSystemLoader

from scoring import score_entry

ROOT = Path(__file__).parent


def get_last_business_day():
    today = datetime.now().date()
    offset = max(1, (today.weekday() + 6) % 7 - 3)
    last_business_day = today - timedelta(days=offset)
    return datetime.combine(last_business_day, time.min)


def create_content(config: dict) -> str:
    # Parse the arXiv feed
    feed = feedparser.parse(config["url"])
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

    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader(ROOT))
    template = env.get_template("email_template.html")

    # Render the template with our data
    html_content = template.render(papers=papers)
    return html_content


def send_simple_message(subject: str, html: str):
    with open("key.txt", "r") as file:
        api_key = file.read()
    response = requests.post(
        "https://api.mailgun.net/v3/sandbox9e8f7a4f3d3d469c9c07ce895892fa11.mailgun.org/messages",  # noqa: E501
        auth=("api", api_key),
        data={
            "from": "arXiv cs.LG<mailgun@sandbox9e8f7a4f3d3d469c9c07ce895892fa11.mailgun.org>",  # noqa: E501
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
