from web.backend.hotrank_ai_classifier import HotrankAiClassifier


def test_parse_category_accepts_other_alias():
    classifier = HotrankAiClassifier.__new__(HotrankAiClassifier)

    assert classifier._parse_category('{"category":"其他"}') == "其它"


def test_parse_category_reads_only_category_field():
    classifier = HotrankAiClassifier.__new__(HotrankAiClassifier)

    assert classifier._parse_category('{"category":"军事国际","confidence":0.1,"reason":"ignored"}') == "军事国际"
