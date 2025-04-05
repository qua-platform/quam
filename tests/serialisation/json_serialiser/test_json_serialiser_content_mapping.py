import json


def test_save_backwards_compatibility_single_dict(
    serialiser, sample_quam_object, tmp_path
):
    """Test save still works with a single dict mapping (backward compatibility)."""
    target_folder = tmp_path / "single_dict_save"
    single_mapping = {"wiring_bc.json": ["wiring"]}

    serialiser.save(
        quam_obj=sample_quam_object,
        path=target_folder,
        content_mapping=single_mapping,
        include_defaults=False,
    )

    wiring_path = target_folder / "wiring_bc.json"
    default_path = target_folder / serialiser.default_filename

    assert wiring_path.exists()
    assert default_path.exists()
    with wiring_path.open("r", encoding="utf-8") as f:
        assert json.load(f) == {"wiring": sample_quam_object.wiring}
    with default_path.open("r", encoding="utf-8") as f:
        loaded = json.load(f)
        assert "components" in loaded
        assert loaded["other"] == "specific_value"
        assert loaded["__class__"] == "conftest.MockQuamRoot"
