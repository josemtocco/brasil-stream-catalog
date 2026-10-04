# Brasil Stream Catalog

Projeto para descoberta e consolidação de canais brasileiros com transmissão pública na internet.

## Objetivo

O projeto consulta agregadores/diretórios públicos, extrai páginas de canais e possíveis URLs de transmissão, normaliza nomes, remove duplicidades e mantém um catálogo persistente.

**Princípio importante:** o projeto prioriza páginas e streams publicamente acessíveis e fontes oficiais. Ele não tenta contornar DRM, autenticação, paywall, tokens privados ou proteções de acesso.

## Fontes monitoradas

- CXTV
- KE TV
- VidKS
- Televisão.TV
- TVAOVIVO.VIP
- AM Canais
- IPGO Web TV
- FotoDicas
- MultiRádio
- DM Play

As fontes são configuradas em `config/sources.json`. Como os sites mudam sua estrutura, cada fonte pode ser adaptada individualmente em `src/sources.py`.

## Saídas

O workflow gera no diretório principal:

- `canais.m3u` — lista M3U consolidada
- `catalogo.json` — catálogo detalhado
- `relatorio.json` — estatísticas da execução
- `logs/` — registros da execução

## Regras de segurança e estabilidade

- Não acessa áreas autenticadas.
- Não tenta quebrar DRM.
- Não gera URLs privadas.
- Não considera automaticamente um stream como autorizado só porque foi encontrado em um agregador.
- A propriedade `official` deve ser confirmada/configurada quando possível.
- Streams que exigem autenticação ou retornam erro são marcados como inativos, não removidos imediatamente.
- Canais antigos podem permanecer no catálogo por algumas execuções para evitar perda causada por indisponibilidade temporária.

## Execução local

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
python gerar_m3u.py
```

## GitHub Actions

O workflow em `.github/workflows/atualizar.yml` executa automaticamente a cada 6 horas e também pode ser executado manualmente.

O catálogo anterior é preservado durante uma falha de coleta. Uma execução não substitui um catálogo válido por um catálogo vazio.

## Personalização

Edite:

- `config/sources.json` para ativar/desativar fontes.
- `config/settings.json` para limites, categorias e retenção.
- `src/sources.py` para adaptar seletores de um agregador específico.

## Estrutura

```text
.
├── canais.m3u
├── catalogo.json
├── relatorio.json
├── gerar_m3u.py
├── requirements.txt
├── config/
│   ├── settings.json
│   └── sources.json
├── src/
│   ├── __init__.py
│   ├── core.py
│   ├── sources.py
│   ├── extract.py
│   ├── normalize.py
│   └── validate.py
├── scripts/
│   └── testar_fontes.py
└── .github/workflows/
    └── atualizar.yml
```
