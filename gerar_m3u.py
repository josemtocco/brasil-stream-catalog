#!/usr/bin/env python3
from __future__ import annotations
import asyncio,json,re
from collections import deque
from pathlib import Path
from urllib.parse import urljoin,urlparse,urldefrag
ROOT=Path(__file__).resolve().parent; CONFIG=ROOT/'config'; CATALOGO=ROOT/'catalogo.json'; PLAYLIST=ROOT/'canais.m3u'; REPORT=ROOT/'relatorio.json'
BAD={'guia de programação','guia de programacao','programação','programacao','pg não informado','pg nao informado','não informado','nao informado','sem nome','channel','canal'}
WORDS=('canal','canais','tv','live','ao-vivo','aovivo','assistir','watch','stream','player','play')
STREAM_RE=re.compile(r'''https?://[^"\'<>\s]+?\.(?:m3u8|mpd)(?:\?[^"\'<>\s]*)?''',re.I)
YT_RE=re.compile(r'''(?:youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=)|youtu\.be/)([A-Za-z0-9_-]{11})''',re.I)

def load(p,d):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except:return d
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def clean_name(v,fallback=''):
 v=re.sub(r'<[^>]+>',' ',v or '');v=re.sub(r'\s+',' ',v).strip(' -|•:');v=re.sub(r'\s+(?:ao vivo|live)\s*$','',v,flags=re.I).strip()
 if not v or v.casefold() in BAD:v=re.sub(r'\s+',' ',fallback or '').strip(' -|•:')
 return '' if v.casefold() in BAD else v
def canonical(v):return re.sub(r'[^a-z0-9]+','',clean_name(v).casefold())
def title(html,url):
 for p in [r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)',r'<meta[^>]+name=["\']twitter:title["\'][^>]+content=["\']([^"\']+)',r'<h1[^>]*>(.*?)</h1>',r'<title[^>]*>(.*?)</title>']:
  m=re.search(p,html or '',re.I|re.S)
  if m:
   n=clean_name(m.group(1))
   if n:return n
 s=urlparse(url).path.rstrip('/').split('/')[-1] if urlparse(url).path else ''
 return clean_name(s.replace('-',' ').replace('_',' ').title())
def streams(html,base):
 out=[]
 for u in STREAM_RE.findall(html or ''):
  u=urljoin(base,u)
  if u not in out:out.append(u)
 for raw in re.findall(r'''["']([^"']+\.(?:m3u8|mpd)(?:\?[^"']*)?)["']''',html or '',re.I):
  u=urljoin(base,raw.replace('\\/','/'))
  if u not in out:out.append(u)
 return out
def youtube(html):return list(dict.fromkeys(f'https://www.youtube.com/watch?v={v}' for v in YT_RE.findall(html or '')))
def norm(base,href):
 if not href:return ''
 u=urljoin(base,href);return urldefrag(u)[0]
def same(u,d):return urlparse(u).netloc.casefold()==d
def likely(u,t=''):return any(x in f'{u} {t}'.casefold() for x in WORDS)
def pageish(u,t=''):
 s=f'{u} {t}'.casefold();return bool(re.search(r'(?:page|pagina|página)[=/_-]?\d+',s)) or bool(re.search(r'[?&](?:page|pagina|p)=\d+',s)) or t.strip().isdigit()
def valid(u,timeout):
 h=urlparse(u).netloc.casefold()
 if 'youtube.com' in h or 'youtu.be' in h:return True
 try:
  import requests
  r=requests.get(u,headers={'User-Agent':'Mozilla/5.0','Range':'bytes=0-1024'},timeout=timeout,allow_redirects=True,stream=True);return r.status_code<500
 except:return False
async def sitemap(page,start,limit):
 base=f'{urlparse(start).scheme}://{urlparse(start).netloc}';out=[]
 for sm in [urljoin(base,'/sitemap.xml'),urljoin(base,'/sitemap_index.xml')]:
  try:
   await page.goto(sm,wait_until='domcontentloaded',timeout=20000);html=await page.content()
   for u in re.findall(r'<loc>\s*(.*?)\s*</loc>',html,re.I|re.S):
    u=u.strip()
    if u.startswith('http') and u not in out:out.append(u)
    if len(out)>=limit:return out
  except:pass
 return out
async def crawl(browser,source,settings):
 start=source['url'];domain=urlparse(start).netloc.casefold();maxp=int(source.get('max_pages',180));maxc=int(source.get('max_channel_pages',140));maxcand=int(source.get('max_candidates',600));tm=int(settings.get('browser_timeout_ms',25000));wait=int(settings.get('render_wait_ms',700));allow=bool(settings.get('allow_youtube',True));page=await browser.new_page(user_agent=settings.get('user_agent','Mozilla/5.0'));q=deque([start]);seen=set();cand=[];records=[]
 try:
  for u in await sitemap(page,start,int(settings.get('max_sitemap_urls',300))):
   if same(u,domain):q.append(u)
  while q and len(seen)<maxp:
   u=q.popleft()
   if u in seen:continue
   seen.add(u)
   try:await page.goto(u,wait_until='domcontentloaded',timeout=tm);await page.wait_for_timeout(wait);html=await page.content()
   except Exception as e:print(' AVISO:',u,'->',e);continue
   n=title(html,u);ss=streams(html,u)
   if ss and n:records.append({'name':n,'category':source.get('category','TV'),'source':source['name'],'page':u,'stream':ss[0],'stream_type':'hls/mpd'})
   elif allow and n and youtube(html):records.append({'name':n,'category':source.get('category','TV'),'source':source['name'],'page':u,'stream':youtube(html)[0],'stream_type':'youtube'})
   try:
    for a in await page.locator('a[href]').all():
     href=await a.get_attribute('href');
     if not href:continue
     try:t=await a.inner_text()
     except:t=''
     child=norm(u,href)
     if not child or not same(child,domain) or child in seen:continue
     if likely(child,t) and child not in cand:cand.append(child)
     if (pageish(child,t) or likely(child,t)) and len(q)<maxp*3:q.append(child)
     if len(cand)>=maxcand:break
   except:pass
   if len(cand)>=maxcand:break
  done=0
  for u in cand:
   if done>=maxc or u in seen:continue
   done+=1
   try:await page.goto(u,wait_until='domcontentloaded',timeout=tm);await page.wait_for_timeout(wait);html=await page.content()
   except:continue
   n=title(html,u);ss=streams(html,u)
   if ss and n:records.append({'name':n,'category':source.get('category','TV'),'source':source['name'],'page':u,'stream':ss[0],'stream_type':'hls/mpd'})
   elif allow and n and youtube(html):records.append({'name':n,'category':source.get('category','TV'),'source':source['name'],'page':u,'stream':youtube(html)[0],'stream_type':'youtube'})
 finally:await page.close()
 out={}
 for r in records:
  k=canonical(r['name'])
  if k and k not in out:out[k]=r
 return list(out.values()),{'pages_scanned':len(seen),'channel_candidates':len(cand),'records':len(out)}
async def collect(sources,settings):
 from playwright.async_api import async_playwright
 allr=[];report=[]
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True)
  try:
   for s in sources:
    print(f"\n========== {s['name']} ==========")
    try:r,st=await crawl(b,s,settings);allr.extend(r);print(f"Páginas: {st['pages_scanned']} | Candidatos: {st['channel_candidates']} | Canais: {st['records']}");report.append({'source':s['name'],**st})
    except Exception as e:print('ERRO:',e);report.append({'source':s['name'],'error':str(e)})
  finally:await b.close()
 return allr,report
def merge(rs):
 o={}
 for r in rs:
  n=clean_name(r.get('name',''));s=r.get('stream','');k=canonical(n)
  if n and s and k and k not in o:r['name']=n;o[k]=r
 return list(o.values())
def preserve(old,new):
 o={}
 for r in old:
  k=canonical(r.get('name',''))
  if k:o[k]=r
 for r in new:
  k=canonical(r.get('name',''))
  if k:o[k]=r
 return list(o.values())
def write_m3u(rs):
 lines=['#EXTM3U']
 for r in sorted(rs,key=lambda x:((x.get('category') or 'TV').casefold(),x['name'].casefold())):
  n=r['name'].replace('"',"'");c=(r.get('category') or 'TV').replace('"',"'");logo=r.get('logo','');lf=f' tvg-logo="{logo}"' if logo else ''
  lines.append(f'#EXTINF:-1 tvg-name="{n}" group-title="{c}"{lf},{n}');lines.append(r['stream'])
 PLAYLIST.write_text('\n'.join(lines)+'\n',encoding='utf-8')
def run():
 print('=== BRASIL STREAM CATALOG v4 ===');settings=load(CONFIG/'settings.json',{});sources=load(CONFIG/'sources.json',[]);old=load(CATALOGO,[])
 if not sources:return 2
 try:raw,sr=asyncio.run(collect(sources,settings))
 except Exception as e:print('ERRO GERAL:',e);raw=[];sr=[]
 cur=merge(raw);ok=[r for r in cur if valid(r['stream'],int(settings.get('stream_timeout',10)))];minimum=int(settings.get('minimum_channels_to_publish',5));print(f'\nDescobertos: {len(cur)} | Válidos: {len(ok)} | Anterior: {len(old)}')
 if len(ok)<minimum:
  if old:print('Coleta insuficiente. Playlist anterior preservada.');save(REPORT,{'status':'preserved','discovered':len(cur),'valid':len(ok),'published':len(old),'sources':sr});return 0
 pub=preserve(old,ok);save(CATALOGO,pub);write_m3u(pub);save(REPORT,{'status':'updated','discovered':len(cur),'valid':len(ok),'published':len(pub),'sources':sr});print(f'SUCESSO: {len(pub)} canais publicados.');return 0
if __name__=='__main__':raise SystemExit(run())
