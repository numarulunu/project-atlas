from atlas_backend import __version__


def test_version_is_030() -> None:
    assert __version__ == "0.3.0"
