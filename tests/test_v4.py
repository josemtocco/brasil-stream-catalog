import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import gerar_m3u

def test_no_src(): assert not (ROOT/'src').exists() and 'from src' not in (ROOT/'gerar_m3u.py').read_text()
def test_bad_names(): assert gerar_m3u.clean_name('PG Não Informado','TV Cultura')=='TV Cultura'
def test_streams():
 x='"https://example.com/live/index.m3u8" "https://example.com/a.mpd"';g=gerar_m3u.streams(x,'https://example.com/');assert 'https://example.com/live/index.m3u8' in g and 'https://example.com/a.mpd' in g
def test_youtube(): assert gerar_m3u.youtube('<iframe src="https://www.youtube.com/embed/dQw4w9WgXcQ"></iframe>')==['https://www.youtube.com/watch?v=dQw4w9WgXcQ']
def test_preserve():
 r=gerar_m3u.preserve([{'name':'Antigo','stream':'a'}],[{'name':'Novo','stream':'b'}]);assert {x['name'] for x in r}=={'Antigo','Novo'}
