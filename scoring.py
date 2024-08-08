from feedparser import FeedParserDict


def score_entry(entry: FeedParserDict, config: dict) -> int:
    score = config["scoring"]["bias"]
    for title_dict in config["scoring"]["titles"]:
        if title_dict["title"] in entry.title.lower():
            assert "value" in title_dict, f"Value not found in title_dict: {title_dict}"
            score += title_dict["value"]
    for author_dict in config["scoring"]["authors"]:
        for entry_author in entry.authors:
            if author_dict["author"] in entry_author.name:
                score += author_dict["value"]
    for tag_dict in config["scoring"]["tags"]:
        entry_tags = [t.term for t in entry.tags]
        if tag_dict["tag"] in entry_tags:
            score += tag_dict["value"]
    return score
