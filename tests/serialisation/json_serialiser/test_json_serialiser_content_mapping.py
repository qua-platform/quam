import json

# Mock components and fixtures are now imported from conftest.py
from quam.serialisation.json import JSONSerialiser


def test_save_with_list_of_mappings_direct(serialiser, sample_quam_object, tmp_path):
    """Test save method directly with a list of content mappings."""
    target_folder = tmp_path / "multi_save_target_direct"

    # Define two different ways to split the content
    mapping1 = {"mapping1/wiring.json": ["wiring"]}
    mapping2 = {"mapping2/components.json": ["components"]}
    list_of_mappings = [mapping1, mapping2]

    # Save using the list of mappings passed directly to save()
    serialiser.save(
        quam_obj=sample_quam_object,
        path=target_folder,
        content_mapping=list_of_mappings,
        include_defaults=False,  # Exclude defaults for simplicity
    )

    # Check files created by the first mapping
    wiring_path = target_folder / "mapping1" / "wiring.json"
    default_path_1 = (
        target_folder / "mapping1" / serialiser.default_filename
    )  # Remainder after map1
    assert wiring_path.exists()
    assert default_path_1.exists()
    with wiring_path.open("r", encoding="utf-8") as f:
        assert json.load(f) == {"wiring": sample_quam_object.wiring}
    with default_path_1.open("r", encoding="utf-8") as f:
        # Should contain components, other, and __class__ (added by save)
        loaded = json.load(f)
        assert "components" in loaded
        assert loaded["other"] == "specific_value"
        assert loaded["__class__"] == "conftest.MockQuamRoot"

    # Check files created by the second mapping
    components_path = target_folder / "mapping2" / "components.json"
    default_path_2 = (
        target_folder / "mapping2" / serialiser.default_filename
    )  # Remainder after map2
    assert components_path.exists()
    assert default_path_2.exists()
    with components_path.open("r", encoding="utf-8") as f:
        expected_comp = sample_quam_object.to_dict()[
            "components"
        ]  # Get full dict structure
        assert json.load(f) == {"components": expected_comp}
    with default_path_2.open("r", encoding="utf-8") as f:
        # Should contain wiring, other, and __class__ (added by save)
        loaded = json.load(f)
        assert loaded["wiring"] == sample_quam_object.wiring
        assert loaded["other"] == "specific_value"
        assert loaded["__class__"] == "conftest.MockQuamRoot"


def test_save_with_list_mapping_on_instance(sample_quam_object, tmp_path):
    """Test saving when the serialiser instance is initialized with a list mapping."""
    target_folder = tmp_path / "multi_save_target_instance"

    mapping1 = {"instance1/wiring.json": ["wiring"]}
    mapping2 = {"instance2/components.json": ["components"]}
    list_of_mappings = [mapping1, mapping2]

    # Initialise serialiser with the list mapping
    list_serialiser = JSONSerialiser(content_mapping=list_of_mappings)

    # Save using the instance's list of mappings
    list_serialiser.save(
        quam_obj=sample_quam_object, path=target_folder, include_defaults=False
    )

    # Verify files - similar checks as test_save_with_list_of_mappings_direct
    wiring_path = target_folder / "instance1" / "wiring.json"
    default_path_1 = target_folder / "instance1" / JSONSerialiser.default_filename
    assert wiring_path.exists()
    assert default_path_1.exists()

    components_path = target_folder / "instance2" / "components.json"
    default_path_2 = target_folder / "instance2" / JSONSerialiser.default_filename
    assert components_path.exists()
    assert default_path_2.exists()


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


def test_save_override_instance_list_mapping_with_single(sample_quam_object, tmp_path):
    """Test overriding an instance list mapping with a single mapping in save()."""
    target_folder = tmp_path / "override_list_with_single"

    instance_list_mapping = [{"inst_list/w.json": ["wiring"]}]
    override_single_mapping = {"override/c.json": ["components"]}

    list_serialiser = JSONSerialiser(content_mapping=instance_list_mapping)

    # Call save, passing the single mapping - it should override the instance list
    list_serialiser.save(
        quam_obj=sample_quam_object,
        path=target_folder,
        content_mapping=override_single_mapping,
        include_defaults=False,
    )

    # Check only files from the override mapping are created
    assert (target_folder / "override" / "c.json").exists()
    assert (target_folder / "override" / JSONSerialiser.default_filename).exists()
    assert not (target_folder / "inst_list").exists()  # Should not be created


def test_save_override_instance_single_mapping_with_list(sample_quam_object, tmp_path):
    """Test overriding an instance single mapping with a list mapping in save()."""
    target_folder = tmp_path / "override_single_with_list"

    instance_single_mapping = {"inst_single/w.json": ["wiring"]}
    override_list_mapping = [
        {"override1/c.json": ["components"]},
        {"override2/o.json": ["other"]},
    ]

    single_serialiser = JSONSerialiser(content_mapping=instance_single_mapping)

    # Call save, passing the list mapping - it should override the instance single dict
    single_serialiser.save(
        quam_obj=sample_quam_object,
        path=target_folder,
        content_mapping=override_list_mapping,
        include_defaults=False,
    )

    # Check files from the override list mapping are created
    assert (target_folder / "override1" / "c.json").exists()
    assert (
        target_folder / "override1" / JSONSerialiser.default_filename
    ).exists()  # wiring, other, class
    assert (target_folder / "override2" / "o.json").exists()
    assert (
        target_folder / "override2" / JSONSerialiser.default_filename
    ).exists()  # wiring, components, class
    assert not (target_folder / "inst_single").exists()  # Should not be created
