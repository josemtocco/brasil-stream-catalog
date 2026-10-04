# Brasil Stream Catalog v3

Projeto GitHub para gerar uma playlist M3U para SS IPTV.

## IMPORTANTE

Esta versão **não utiliza a pasta `src/`**.

O arquivo:

```text
gerar_m3u.py
```

é autossuficiente e é o único ponto de entrada do gerador.

Portanto, não existe dependência de:

```text
from src.core import run
```

Isso elimina o erro:

```text
ModuleNotFoundError: No module named 'src'
```

## Estrutura

```text
brasil-stream-catalog/
├── .github/workflows/atualizar.yml
├── config/
│   ├── settings.json
│   └── sources.json
├── tests/
│   └── test_core.py
├── gerar_m3u.py
├── canais.m3u
├── catalogo.json
├── relatorio.json
├── requirements.txt
└── README.md
```

## Funcionamento

1. GitHub Actions instala Python.
2. Instala Playwright.
3. Instala Chromium.
4. Executa os testes.
5. Executa `python gerar_m3u.py`.
6. Pesquisa as fontes configuradas.
7. Tenta identificar páginas de canais.
8. Procura URLs públicas `.m3u8`/`.mpd`.
9. Também reconhece embeds públicos do YouTube.
10. Valida as transmissões.
11. Não substitui uma playlist existente por uma coleta vazia/insuficiente.
12. Atualiza a M3U.
13. Faz commit automático.

## Frequência

A atualização está configurada para ocorrer a cada 6 horas.

Também é possível iniciar manualmente em:

GitHub → Actions → Atualizar M3U → Run workflow

## Segurança da coleta

O projeto trabalha somente com transmissões publicamente acessíveis. Não tenta contornar DRM, autenticação, paywall ou qualquer mecanismo de proteção.
