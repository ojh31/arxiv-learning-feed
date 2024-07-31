from feedparser import FeedParserDict


def score_entry(entry: FeedParserDict, config: dict) -> int:
    score = config["scoring"]["bias"]
    for title_dict in config["scoring"]["titles"]:
        if title_dict["title"] in entry.title.lower():
            score += title_dict["value"]
    for author_dict in config["scoring"]["authors"]:
        for entry_author in entry.authors:
            if author_dict["author"] in entry_author.name:
                score += author_dict["value"]
    for tag_dict in config["scoring"]["tags"]:
        if tag_dict["tag"] in entry.tags:
            score += tag_dict["value"]
    return score
