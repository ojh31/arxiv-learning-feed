from feedparser import FeedParserDict


def score_entry(entry: FeedParserDict, config: dict) -> int:
    score = config["scoring"]["bias"]
    for word_dict in config["scoring"]["words"]:
        if word_dict["word"] in entry.title.lower():
            assert "value" in word_dict, f"Value not found in word_dict: {word_dict}"
            score += word_dict["value"]
        if word_dict["word"] in entry.summary.lower():
            assert "value" in word_dict, f"Value not found in word_dict: {word_dict}"
            score += word_dict["value"] * config["scoring"]["summary_multiplier"]
    for author_dict in config["scoring"]["authors"]:
        for entry_author in entry.authors:
            if author_dict["author"] in entry_author.name:
                score += author_dict["value"]
    for tag_dict in config["scoring"]["tags"]:
        entry_tags = [t.term for t in entry.tags]
        if tag_dict["tag"] in entry_tags:
            score += tag_dict["value"]
    return int(score)
