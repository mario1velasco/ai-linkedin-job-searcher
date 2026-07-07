"""Hello unit test module."""

from app_be.hello import hello


def test_hello():
    """Test the hello function."""
    assert hello() == "Hello APP-BE"
