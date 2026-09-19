import pytest
from jwt import InvalidTokenError
from backend.core.security import (create_access_token, decode_access_token)


def test_create_access_token():
    token = create_access_token("42")

    assert isinstance(token, str)
    assert token.count(".") == 2


def test_decode_access_token():
    token = create_access_token("42")

    payload = decode_access_token(token)

    assert payload["sub"] == "42"
    assert "exp" in payload


def test_decode_access_token_rejects_invalid_token():
    with pytest.raises(InvalidTokenError):
        decode_access_token("not-a-valid-token")
