import runpy

import pytest

from backend.core import api_key


@pytest.mark.parametrize("configured_key", [None, "", "   ", "\t\n"])
def test_api_key_rejects_missing_or_blank_configuration(
        monkeypatch, configured_key):
    monkeypatch.setattr("dotenv.load_dotenv", lambda: None)
    if configured_key is None:
        monkeypatch.delenv("PUBLIC_API_KEY", raising=False)
    else:
        monkeypatch.setenv("PUBLIC_API_KEY", configured_key)

    with pytest.raises(RuntimeError, match="PUBLIC_API_KEY"):
        runpy.run_path(api_key.__file__)


def test_api_key_accepts_nonempty_configuration(monkeypatch):
    monkeypatch.setattr("dotenv.load_dotenv", lambda: None)
    monkeypatch.setenv("PUBLIC_API_KEY", "test-public-api-key")

    module = runpy.run_path(api_key.__file__)

    assert module["PUBLIC_API_KEY"] == "test-public-api-key"
    module["require_api_key"]("test-public-api-key")
