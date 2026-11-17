from types import SimpleNamespace

from openai import NOT_GIVEN

from readlater import model


def call_and_capture(monkeypatch) -> dict:
    """Run get_response against a fake OpenAI client and return the arguments it was called with."""
    captured = {}

    class FakeClient:
        def __init__(self, **kwargs):
            self.responses = SimpleNamespace(create=self.create)

        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(output_text="ok", usage=None)

    monkeypatch.setattr(model, "OpenAI", FakeClient)
    monkeypatch.setenv("OPENAI_MODEL", "some-model")
    assert model.get_response("instructions", "text") == "ok"
    return captured


def test_reasoning_effort_is_sent_when_set(monkeypatch):
    monkeypatch.setenv("OPENAI_REASONING_EFFORT", "none")
    assert call_and_capture(monkeypatch)["reasoning"] == {"effort": "none"}


def test_reasoning_is_left_out_when_unset(monkeypatch):
    monkeypatch.delenv("OPENAI_REASONING_EFFORT", raising=False)
    assert call_and_capture(monkeypatch)["reasoning"] is NOT_GIVEN
