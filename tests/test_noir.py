from trenchcoat.noir.narration import say


def test_say_returns_string():
    line = say("engage")
    assert isinstance(line, str)
    assert len(line) > 10


def test_say_unknown_event_falls_back():
    line = say("not-a-real-event")
    assert isinstance(line, str)
