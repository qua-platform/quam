def test_relative_list_referencing(BareQuamRoot):
    root = BareQuamRoot()
    root.l = [1, 2, 3, "#./0"]
    assert root.l[3] == 1

    root.l.append("#../")
    assert root.l[4] == root


def test_relative_dict_referencing(BareQuamRoot):
    root = BareQuamRoot()
    root.d = {"a": 1, "b": 2, "c": "#./a"}
    assert root.d.c == 1
    assert root.d["c"] == 1

    root.d["d"] = "#../"
    assert root.d.d == root
    assert root.d["d"] == root


def test_relative_component_referencing(BareQuamRoot, BareQuamComponent):
    root = BareQuamRoot()
    root.comp = BareQuamComponent()
    root.comp.a = 42
    root.comp.b = "#./a"

    assert root.comp.b == 42

    root.comp.c = "#../"
    assert root.comp.c == root

    root.comp.d = "#../comp"
    assert root.comp.d == root.comp
