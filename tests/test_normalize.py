from src.normalize import clean_name, canonical

def test_bad_name_fallback():
    assert clean_name("PG Não Informado","TV Cultura") == "TV Cultura"

def test_canonical():
    assert canonical("TV Cultura!") == "tvcultura"
