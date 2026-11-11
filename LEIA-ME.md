# Site Bosque Estrada Parque — www.bosqueestradaparque.com.br

Site estático com hospedagem grátis no GitHub Pages. A agenda e os posts vêm do Instagram a cada 3 horas.

---

## PARTE 1 — Subir o site no GitHub (10 min)

1. No GitHub do Bosque, clique em **New repository**. Nome: `site`, **Public** e **Create repository**.
2. Na tela do repositório vazio, clique em **uploading an existing file**. Arraste tudo o que está DENTRO da pasta `site` (index.html, CNAME, LEIA-ME.md e as pastas img, data e scripts) e clique em **Commit changes**.
   - No Mac, a pasta `.github` fica oculta e não vai junto. Crie o arquivo à mão:
     **Add file → Create new file** → nome `.github/workflows/instagram.yml` → cole o conteúdo do arquivo que está no final deste LEIA-ME → **Commit**.
3. **Settings → Actions → General → Workflow permissions** → marque **Read and write permissions** → **Save**.
4. **Settings → Pages** → Source: **Deploy from a branch** → Branch: `main` / `(root)` → **Save**.
   Em **Custom domain**, digite `www.bosqueestradaparque.com.br` → **Save**.

## PARTE 2 — DNS (na página do domínio que você deixou aberta)

Apague os registros antigos que apontam para o site pago (A, CNAME ou "redirecionamento" de `@` e `www`). Depois crie:

| Tipo | Nome | Valor |
|---|---|---|
| CNAME | www | `SEU-USUARIO-GITHUB.github.io` |
| A | @ (vazio) | 185.199.108.153 |
| A | @ (vazio) | 185.199.109.153 |
| A | @ (vazio) | 185.199.110.153 |
| A | @ (vazio) | 185.199.111.153 |

- Não mexa nos registros MX, que são do e-mail contato@.
- Pode levar de 15 minutos a algumas horas. Quando o GitHub mostrar "DNS check successful", volte em Settings → Pages e marque **Enforce HTTPS**.
- Cancele o site pago só depois que o novo abrir.

## PARTE 3 — Ligar o Instagram (API da Meta, 15 min, uma vez só)

1. **Conta profissional.** No app do Instagram, abra Configurações → Tipo de conta e confirme que o @bosqueestradaparque é **Empresa** ou **Criador de conteúdo**.
2. **Criar o app.** Acesse developers.facebook.com, entre com o Facebook que administra o Bosque e clique em **Meus apps → Criar app**.
   - Nome: `Site Bosque`
   - Caso de uso: **"Gerenciar mensagens e conteúdo no Instagram"** (Instagram API)
   - Portfólio empresarial: o do Bosque, se houver. Depois clique em **Criar app**.
3. **Gerar o token.** No painel do app, vá em **Instagram → Configuração da API com login do Instagram** (API setup with Instagram business login).
   - Na etapa **"1. Gerar tokens de acesso"**, clique em **Adicionar conta** e entre com o @bosqueestradaparque.
   - Clique em **Gerar token** ao lado da conta, aceite as permissões e **copie o token**. É um texto longo que começa com `IG...`.
   - O app pode ficar em "Modo de desenvolvimento". Para ler a própria conta não precisa de revisão da Meta.
4. **Guardar o token no GitHub.** No repositório, vá em **Settings → Secrets and variables → Actions → New repository secret**.
   - Nome: `IG_TOKEN`
   - Valor: o token copiado. Clique em **Add secret**.
5. **Testar.** Vá em **Actions → Sincronizar Instagram → Run workflow**. Em cerca de 1 minuto aparece um commit "Atualiza agenda do Instagram" e o site mostra os posts.

O token vale 60 dias e o robô renova sozinho a cada execução. Se a Action falhar com erro de token, gere um novo (passo 3) e troque o secret.

---


## PARTE 4 — Avaliações do Google (opcional, 15 min)

O site já mostra o botão **"Avaliar no Google"**. Hoje ele abre a página do Bosque no Maps. Para abrir direto a janela de estrelas:

**A. Link direto de avaliação (recomendado, grátis)**
1. Entre em business.google.com com a conta dona do perfil do Bosque, ou pesquise "Bosque Estrada Parque" no Google logado.
2. Clique em **Pedir avaliações** e copie o link (algo como `https://g.page/r/XXXX/review`).
3. No GitHub, abra `data/google.json`, troque o valor de `"review_url"` por esse link e salve.
4. Use o mesmo link no QR code das mesas e do caixa.

**B. Depoimentos 5★ automáticos + nota**
1. Acesse console.cloud.google.com, crie o projeto `Site Bosque` e ative a **Places API (New)**. A cobrança precisa estar ativa, mas 8 consultas por dia ficam bem dentro da cota grátis.
2. Em **APIs e serviços → Credenciais**, crie uma **Chave de API** e restrinja a chave à Places API (New).
3. Pegue o **Place ID** do Bosque em developers.google.com/maps/documentation/places/web-service/place-id (pesquise o nome; começa com `ChIJ...`).
4. No GitHub, vá em **Settings → Secrets → Actions** e crie `GOOGLE_API_KEY` e `GOOGLE_PLACE_ID`.
5. Rode **Actions → Run workflow**.

Daí em diante, o robô:
- Mostra **só as avaliações 5 estrelas com comentário**, até 6 no site, com nome do autor e "Google".
- Acumula as melhores ao longo do tempo. O Google entrega 5 avaliações por consulta.
- Coloca a nota pequena embaixo do bloco, com o link "ver todas".
- Preenche sozinho o link direto de avaliação.

**Depoimentos escolhidos à mão:** em `data/google.json`, dentro de `"fixas"`, adicione:
```json
"fixas":[{"autor":"Nome da pessoa","texto":"Comentário copiado do Google","quando":"out/2026"}]
```
As fixas aparecem primeiro.

> Regra do Google: o pedido de avaliação tem que ir para todos os clientes. Não pode filtrar quem está satisfeito antes de pedir, nem dar brinde em troca de estrelas. Isso pode derrubar avaliações ou o perfil. O site pede de forma aberta e só *exibe* os melhores comentários, o que é permitido.

---

## Como postar para o site se atualizar sozinho

**Agenda do mês:** no post do cartaz, a legenda precisa ter "Agenda de [mês]" e uma linha por show:
```
AGENDA DE DEZEMBRO 🎸
05/12 · Phil Aygah · 12h30
06/12 · Ani Belle · 13h
25/12 · Feriado · Blind Smoke · 12h30 · café 10h
```
- O site destaca sozinho o **próximo fim de semana**, com foto, artista, horário do show e do café. A lista do mês fica embaixo, com os shows que já passaram apagados.
- Se a linha não informar o café, o site usa o padrão: sábado 10h, domingo 8h. Em feriado, escreva "café 10h" na linha.
- **Troca de artista:** reposte com a legenda corrigida. Ou edite `data/agenda.json` direto no GitHub (ícone de lápis), salve, e em 1 minuto o site atualiza.

**Posts avulsos** caem nas abas do Instagram pelas palavras da legenda:
- "ao vivo", "show", "banda", "rock" → Música ao vivo
- "encontro", "evento", "festa", "motoclube" → Eventos
- o resto → Novidades

## Opcional — medir quem vem do Instagram

- Os links de cardápio e Instagram já levam `utm_source=site`.
- Os botões de WhatsApp, Como chegar, Cardápio e Instagram disparam eventos.
- Para medir no Meta Pixel: no `index.html`, procure `META PIXEL`, troque `SEU_PIXEL_ID` pelo ID do Gerenciador de Eventos e apague as linhas `<!--` e `-->` em volta.
- Na bio do Instagram, use `https://www.bosqueestradaparque.com.br/?utm_source=instagram&utm_medium=bio`.

## Trocar fotos

As fotos ficam na pasta `img/`. Para trocar, suba um arquivo com o mesmo nome (ex.: `hero.jpg` é a foto do topo).

---

### Conteúdo de `.github/workflows/instagram.yml`
```yaml
name: Sincronizar Instagram e Google
on:
  schedule:
    - cron: "17 */3 * * *"
  workflow_dispatch:
permissions:
  contents: write
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python scripts/sync_instagram.py
        continue-on-error: true
        env:
          IG_TOKEN: ${{ secrets.IG_TOKEN }}
      - run: python scripts/sync_google.py
        continue-on-error: true
        env:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
          GOOGLE_PLACE_ID: ${{ secrets.GOOGLE_PLACE_ID }}
      - run: |
          git config user.name "bosque-bot"
          git config user.email "bot@bosqueestradaparque.com.br"
          git add data
          git diff --cached --quiet || (git commit -m "Atualiza agenda do Instagram" && git push)
```
