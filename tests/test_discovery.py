from glm_ocr_json.discovery import discover_images


def test_discover_images_recursively_filters_pattern_and_extensions(tmp_path):
    patron = tmp_path / "PATRON"
    patron.mkdir()
    nested = patron / "nested"
    nested.mkdir()

    target_one = patron / "Screenshot_alpha.jpg"
    target_one.write_text("")
    target_two = nested / "Screenshot_beta.PNG"
    target_two.write_text("")
    ignored_ext = nested / "Screenshot_gamma.txt"
    ignored_ext.write_text("")
    ignored_name = patron / "image.png"
    ignored_name.write_text("")

    discovered = discover_images(patron)

    assert discovered == [target_one.resolve(), target_two.resolve()]
