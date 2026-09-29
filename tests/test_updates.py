from gpuharbor.updates import is_newer, normalize


def test_normalize_ignores_prefix_and_suffix():
    assert normalize("v0.2.1") == (0, 2, 1)
    assert normalize("1.0.0-dev") == (1, 0, 0)
    assert normalize("not-a-version") == ()


def test_is_newer_compares_numeric_parts():
    assert is_newer("v0.2.0", "0.1.0")
    assert is_newer("0.1.1", "0.1.0")
    assert not is_newer("v0.1.0", "0.1.0")
    assert not is_newer("0.1.0", "0.1.0-dev")


def test_is_newer_handles_missing_parts():
    assert is_newer("2.0", "1.9.9")
    assert not is_newer("garbage", "1.0.0")
    assert not is_newer("1.0.0", "garbage")
