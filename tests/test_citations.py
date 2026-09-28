from wiki.citations import check_answer, extract_labels

PASSAGES = {
    "S1": "A plus-or-minus 3 percentage point poll needs 1/(0.03 squared) = 1,112 people.",
    "S2": "The final exam is 40% of the grade.",
}


def test_labels_are_found_in_all_common_bracket_styles():
    assert extract_labels("Yes [S1]. Also [S2][S3] and [S1, S4].") == ("S1", "S2", "S3", "S4")
    assert extract_labels("See [note] and [1] but no labels") == ()


def test_good_answer_is_ok():
    report = check_answer("You need 1,112 people [S1].", PASSAGES, "sample size for 3 points")
    assert report.status == "ok" and report.cited == ("S1",)


def test_number_formatting_differences_do_not_matter():
    assert check_answer("About 1112 people [S1].", PASSAGES).status == "ok"


def test_unknown_label_fails():
    report = check_answer("You need 1,112 people [S9].", PASSAGES)
    assert report.status == "failed" and report.unknown == ("S9",)


def test_answer_without_any_citation_fails():
    report = check_answer("You need about 1,112 people.", PASSAGES)
    assert report.status == "failed" and "cites no passage" in report.describe()


def test_invented_number_is_flagged_even_though_the_label_is_valid():
    report = check_answer("You need 2,000 people [S1].", PASSAGES)
    assert report.status == "failed" and report.unsupported_figures == ("2,000",)


def test_invented_month_is_flagged():
    report = check_answer("The final exam is on December 12 [S2].", PASSAGES, "When is the final exam?")
    assert report.status == "failed" and "December" in report.unsupported_figures


def test_numbers_from_the_question_are_allowed():
    report = check_answer("For 3 percentage points you need 1,112 people [S1].", PASSAGES, "3 percentage points?")
    assert report.status == "ok"


def test_figures_are_checked_against_the_cited_passage_only():
    # 40% exists in S2, but the answer cites S1
    report = check_answer("The exam is 40% of the grade [S1].", PASSAGES)
    assert report.unsupported_figures == ("40%",)


def test_single_digit_counts_are_ignored():
    assert check_answer("There are 3 steps [S1].", PASSAGES).status == "ok"


def test_uncited_claim_sentence_is_only_a_warning():
    report = check_answer("Polls need 1,112 people [S1]. Pollsters usually round this figure up.", PASSAGES)
    assert report.status == "warning" and len(report.uncited_sentences) == 1


def test_a_citation_covers_the_earlier_sentences_of_its_paragraph():
    answer = "Polls need a large sample. It is computed from the margin of error. That gives 1,112 people [S1]."
    assert check_answer(answer, PASSAGES).status == "ok"


def test_describe_lists_every_problem():
    text = check_answer("Answer 2,000 [S9]", PASSAGES).describe()
    assert "never retrieved" in text and "2,000" in text
