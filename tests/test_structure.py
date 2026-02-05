from glm_ocr_json.ocr import _structure_text


def test_structure_text_detects_key_values_and_bullets():
    sample = """
    Subject: Invoice Reminder
    - Next payment due: January 15
    * Total: $123.45
    Notes line
    """.strip()

    structured = _structure_text(sample)

    assert structured["lines"][0] == "Subject: Invoice Reminder"
    assert {"key": "Subject", "value": "Invoice Reminder"} in structured["key_values"]
    assert "Next payment due: January 15" in structured["bullets"]
    assert structured["key_values"][-1]["value"] == "$123.45"
