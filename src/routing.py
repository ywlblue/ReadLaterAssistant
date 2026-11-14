from dataclasses import dataclass

NEEDS_ARG = {"/find", "/ask", "/found", "/missed"}
NO_ARG = {"/review"}

USAGE = """Commands:
<url>            save a link (just paste it)
/find <words>    find saved items
/ask <question>  answer from saved items
/review          suggest up to 3 unread items
/found <id> | /missed <id>   feedback"""


@dataclass(frozen=True)
class Route:
    command: str
    arg: str = ""


def route(text: str) -> Route:
    text = text.strip()
    if text.startswith("/"):
        cmd, _, arg = text.partition(" ")
        cmd, arg = cmd.lower(), arg.strip()
        if cmd in NEEDS_ARG:
            return Route(cmd, arg) if arg else Route("usage")
        if cmd in NO_ARG:
            return Route(cmd)
        return Route("usage")  # /help、/start、/xyz
    if text.startswith(("http://", "https://")) and " " not in text:
        return Route("save", text)
    return Route("usage")
