# Brasil Stream Catalog v2

Versão corrigida após teste da primeira versão.

### Correções principais
- `gerar_m3u.py` importa `src` de forma segura.
- Coleta com Chromium/Playwright para páginas dinâmicas.
- Detecta HLS `.m3u8`, MPEG-DASH `.mpd` e embeds oficiais do YouTube.
- Rejeita nomes genéricos como `Guia de programação` e `PG Não Informado`.
- Não substitui uma playlist válida por uma coleta vazia ou insuficiente.
- Mantém canais anteriormente conhecidos quando uma fonte falha temporariamente.
- Gera `tvg-name` com o nome do canal.
- Testes automatizados incluídos.

### Execução
```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
pytest -q
python gerar_m3u.py
```

O projeto usa apenas transmissões públicas/oficiais encontradas nas páginas dos agregadores e não tenta contornar DRM, autenticação ou paywall.
