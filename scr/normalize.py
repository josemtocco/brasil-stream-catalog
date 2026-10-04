import re
import unicodedata

BAD_NAMES = {
    "", "guia de programação", "programação", "pg não informado",
    "não informado", "nao informado", "sem nome", "channel", "canal"
}

def clean_text(value: str) -> str:
    value = value or ""
    value = re.sub(r"\s+", " ", value)
    return value.strip(" -|•·\t\r\n")

def canonical_name(value: str) -> str:
    value = clean_text(value).lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = re.sub(r"[^a-z0-9]+", " ", value).strip()
    return value

def valid_name(value: str) -> bool:
    c = canonical_name(value)
    if not c or c in {canonical_name(x) for x in BAD_NAMES}:
        return False
    if len(c) < 2 or len(c) > 100:
        return False
    return True

def infer_category(name: str, url: str = "", context: str = "") -> str:
    s = canonical_name(" ".join([name, url, context]))
    rules = [
        ("Notícias", ["news", "noticia", "jornal", "cnn", "band news", "record news"]),
        ("Esportes", ["sport", "esporte", "futebol", "goat", "caze", "cbf"]),
        ("Religião", ["gospel", "evangel", "catol", "canção nova", "cançao nova", "rede vida"]),
        ("Agro", ["agro", "rural", "canal do boi"]),
        ("Infantil", ["kids", "infantil", "cartoon", "toon", "anime"]),
        ("Música", ["music", "musica", "rádio", "radio"]),
        ("Cultura", ["cultura", "arte", "document"]),
        ("Educação", ["educa", "escola", "univers"]),
        ("Filmes", ["cine", "cinema", "movie", "film"]),
        ("Público", ["camara", "câmara", "senado", "justica", "justiça", "gov", "assembleia", "alrs", "tv brasil"]),
        ("Regional", ["rs ", "sp ", "mg ", "ba ", "ce ", "pr ", "sc ", "rio ", "regional"]),
        ("WebTV", ["webtv", "web tv", "web"]),
    ]
    for cat, keys in rules:
        if any(k in s for k in keys):
            return cat
    return "TV Aberta"
