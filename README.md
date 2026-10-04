# Brasil Stream Catalog v4

Versão de ampliação da v3. Não utiliza `src/`.

## Novidades
- sitemap.xml e sitemap_index.xml;
- categorias e paginação;
- descoberta de links individuais;
- segunda fase dedicada às páginas de canais;
- extração de `.m3u8` e `.mpd` do HTML/JavaScript;
- iframes/embeds públicos do YouTube;
- limites diferentes para cada agregador;
- preservação dos canais já encontrados;
- proteção contra substituir uma playlist válida por coleta insuficiente;
- relatório por fonte em `relatorio.json`.

## IMPORTANTE
Este ZIP é um **overlay**. Ele NÃO contém `catalogo.json` nem `canais.m3u` de propósito. Ao copiar os arquivos para o repositório atual, mantenha esses dois arquivos para conservar os canais já encontrados.

As transmissões devem ser públicas/oficiais; o projeto não contorna DRM, login, paywall ou autenticação.
