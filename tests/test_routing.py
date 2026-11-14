from routing import route, Route


def test_bare_url_is_save():
    assert route("  https://a.com/x  ") == Route("save", "https://a.com/x")


def test_plain_text_is_usage():
    assert route("hello") == Route("usage")


def test_find_with_arg():
    assert route("/find vault") == Route("/find", "vault")


def test_command_case():
    assert route("/FIND vault") == Route("/find", "vault")


def test_find_without_arg():
    assert route("/find   ") == Route("usage")


def test_review():
    assert route("/review") == Route("/review")


def test_unknown_command():
    assert route("/xyz") == Route("usage")


def test_url_inside_sentence():  assert route("look at https://a.com") == Route("usage")
