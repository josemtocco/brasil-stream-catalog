import re
from urllib.parse import urlparse

BAD = {
    "guia de programação","guia de programacao","programação","programacao",
    "pg não informado","pg nao informado","não informado","nao informado",
    "sem nome","channel","canal","assistir","ao vivo"
}

def clean_name(name, fallback=""):
    name = re.sub(r"\s+", " ", name or "").strip(" -|•:")
    name = re.sub(r"\s+(?:ao vivo|live)\s*$", "", name, flags=re.I).strip()
    if not name or name.casefold() in BAD:
        name = re.sub(r"\s+", " ", fallback or "").strip(" -|•:")
    return name

def slug_name(url):
    path = urlparse(url).path.rstrip("/")
    value = path.split("/")[-1] if path else ""
    return clean_name(value.replace("-", " ").replace("_", " ").title())

def canonical(name):
    return re.sub(r"[^a-z0-9]+", "", clean_name(name).casefold())
