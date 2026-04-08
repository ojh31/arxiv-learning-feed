import io
import json
import os
import re

import anthropic
import pymupdf
import requests

SYSTEM_PROMPT = """\
You are an expert paper reviewer for an AI safety researcher at FAR.AI. \
The researcher's interests and priorities:

HIGH INTEREST:
- Deception, deceptive alignment, scheming, and alignment faking in AI systems
- Empirical demonstrations of alignment failures (e.g. emergent misalignment from finetuning, reward hacking, specification gaming)
- Monitoring and detecting misaligned behavior (e.g. CoT monitoring, obfuscation of reasoning, detecting when models hide misbehavior)
- White-box / mechanistic interpretability tools applied to alignment-relevant behaviors (e.g. deception probes, interventions to reduce sycophancy or harmful outputs — NOT applied to general capabilities like math reasoning)
- Clear threat modelling around loss of control and existential risk from misaligned AI
- Evaluations and benchmarks for dangerous capabilities or alignment failures
- Papers from frontier model developers (Anthropic, OpenAI, Google DeepMind) and AI safety orgs (METR, Apollo Research, FAR.AI, Redwood Research, ARC Evals) are generally interesting

MODERATE INTEREST — default to 30-40 unless exceptionally novel:
- Jailbreaking and adversarial robustness — only score above 50 if the contribution is highly novel (e.g. a fundamentally new attack paradigm or a new theoretical framework for robustness). Incremental improvements on existing attack/defense methods should score 20-30.
- Finetuning attacks (removing safety training, inserting backdoors via finetuning APIs, etc.) — same bar as jailbreaks. Default 30-40, only higher if exceptionally novel or reveals something fundamental about alignment.

LOW INTEREST — score these down:
- Papers about non-LLM models (classical ML, GNNs, CNNs, diffusion models, etc.)
- Mechanistic interpretability with no clear safety application (e.g. pure SAE feature analysis, circuit discovery for its own sake, or interpretability of toy models without a path to alignment)
- General capabilities work with no safety angle
- Incremental jailbreak attacks or defenses (yet another GCG variant, another guardrail, another red-teaming benchmark without novel insight)

To calibrate: the researcher's favorite papers include "Alignment faking in large language models" (Greenblatt et al.), \
"Emergent Misalignment" (Betley et al.), "Monitoring Reasoning Models for Misbehavior and the Risks of Promoting Obfuscation" (Baker et al.), \
"Stress Testing Deliberative Alignment for Anti-Scheming Training" (Schoen et al.), \
and "The Obfuscation Atlas" (Taufeeque et al.). These would all score 90+. \
For jailbreaking specifically, "Constitutional Classifiers: Defending against Universal Jailbreaks" (Sharma et al.) \
would score 80+ because it introduces a fundamentally new defense paradigm with rigorous evaluation — \
contrast this with papers that merely apply existing attack/defense techniques to a new model or domain, which should score much lower.

Score each paper out of 100 based on how relevant and worth reading it is for this researcher. Guidelines:
- 80-100: Directly addresses the researcher's core interests — deception/scheming, alignment failures, CoT monitoring, applied-to-safety mechinterp
- 60-79: Highly relevant adjacent AI safety work (alignment techniques, dangerous capability evals, governance with technical depth, or from a frontier/safety lab)
- 40-59: Moderately interesting — touches on relevant themes but not core focus
- 20-39: Tangentially related or incremental work in an interesting area
- 0-19: Not relevant (non-LLM, pure capabilities, interpretability without safety application, incremental jailbreak work)

For each paper, provide:
1. A score (0-100)
2. A 2-3 sentence summary of what the paper does
3. A 1-2 sentence explanation of why it is or isn't worth reading for this researcher

Respond with a JSON array of objects, one per paper, each with keys: "index", "score", "summary", "relevance". \
The "index" field should match the paper's index in the input list (0-indexed). \
Output ONLY valid JSON, no markdown fences or other text.\
"""


def judge_papers(papers: list[dict]) -> list[dict]:
    """Send papers with keyword score >= threshold to Claude for LLM review.

    Returns list of dicts with keys: index, score, summary, relevance.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Build the user message with all papers
    paper_descriptions = []
    for i, paper in enumerate(papers):
        paper_descriptions.append(
            f"[{i}] Title: {paper['title']}\n"
            f"Authors: {paper['authors']}\n"
            f"Abstract: {paper['summary']}\n"
            f"Keyword score: {paper['score']}"
        )

    user_message = (
        "Please review the following papers:\n\n"
        + "\n\n---\n\n".join(paper_descriptions)
    )

    # Call Claude Opus for judging
    response = client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    result_text = response.content[0].text
    reviews = json.loads(result_text)
    return reviews


def _arxiv_id_from_link(link: str) -> str:
    """Extract arXiv paper ID from a link like http://arxiv.org/abs/2604.05655v1."""
    m = re.search(r"(\d{4}\.\d{4,5})(v\d+)?", link)
    return m.group(0) if m else ""


def _fetch_pdf_text(arxiv_id: str, max_chars: int = 50000) -> str:
    """Download arXiv PDF and extract text."""
    url = f"https://arxiv.org/pdf/{arxiv_id}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    doc = pymupdf.open(stream=io.BytesIO(resp.content), filetype="pdf")
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text[:max_chars]


def summarize_full_text(papers: list[dict]) -> dict[int, str]:
    """Fetch full PDFs for papers and summarize with Haiku.

    Args:
        papers: list of paper dicts, each must have 'link' and an index key '_idx'.

    Returns:
        dict mapping paper list index to Haiku summary string.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    summaries = {}

    for paper in papers:
        idx = paper["_idx"]
        arxiv_id = _arxiv_id_from_link(paper["link"])
        if not arxiv_id:
            continue
        try:
            full_text = _fetch_pdf_text(arxiv_id)
            print(f"  Fetched {len(full_text)} chars for {arxiv_id}")
        except Exception as e:
            print(f"  Failed to fetch PDF for {arxiv_id}: {e}")
            continue

        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Summarize this paper as a bullet-point list of "
                            "key findings and points of interest. Use short, "
                            "easy-to-read bullets. Focus on what's novel, "
                            "what the main results are, and any surprising "
                            "or important takeaways.\n\n" + full_text
                        ),
                    }
                ],
            )
            summaries[idx] = response.content[0].text
        except Exception as e:
            print(f"  Haiku summarization failed for {arxiv_id}: {e}")

    return summaries
