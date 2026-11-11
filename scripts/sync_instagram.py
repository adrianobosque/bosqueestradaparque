"""Puxa os posts recentes do Instagram, classifica (música / eventos / novidades),
baixa as imagens para data/img e grava data/instagram.json.

Requer o secret IG_TOKEN (token de longa duração da "Instagram API with Instagram Login").
Roda no GitHub Actions (ver .github/workflows/instagram.yml).
"""
import json, os, re, sys, urllib.request, urllib.parse, urllib.error, datetime, pathlib

TOKEN = os.environ.get("IG_TOKEN")
IG_USER_ID = os.environ.get("IG_USER_ID") or "17841474228811076"  # @bosqueestradaparque
LIMIT = 30
ROOT = pathlib.Path(__file__).resolve().parent.parent
IMG = ROOT / "data" / "img"
OUT = ROOT / "data" / "instagram.json"

MUSICA = r"ao vivo|show|banda|m[uú]sica|ac[uú]stico|rock|country|blues|folk|palco|dj|programa[cç][aã]o musical|#agenda"
EVENTOS = r"evento|encontro|motoclube|moto ?clube|carros antigos|festa|festival|feriado|anivers[aá]rio|inscri[cç]|ingresso|especial de|dia d[aeo]s?|#evento"


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{e.code} {e.read().decode(errors='ignore')[:300]}") from None


def categoria(txt):
    t = txt.lower()
    if re.search(MUSICA, t):
        return "musica"
    if re.search(EVENTOS, t):
        return "eventos"
    return "novidades"


def data_evento(txt):
    m = re.search(r"\b(\d{1,2})[/.](\d{1,2})\b", txt)
    if not m:
        return None
    d, mth = int(m.group(1)), int(m.group(2))
    if 1 <= d <= 31 and 1 <= mth <= 12:
        return f"{d:02d}/{mth:02d}"
    return None


def horario(txt):
    m = re.search(r"\b(\d{1,2})\s?h\s?(\d{2})?\b", txt.lower())
    return f"{int(m.group(1))}h{m.group(2) or ''}" if m and int(m.group(1)) < 24 else None


def titulo(txt):
    linha = next((l.strip() for l in txt.splitlines() if l.strip()), "")
    linha = re.sub(r"^\W*\d{1,2}[/.]\d{1,2}\W*", "", linha)
    return linha[:90]


MESES = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]


def agenda_do_post(cap, img):
    """Cada linha da legenda com dd/mm vira um show: '21/11 · Gu Salvator · 12h30'."""
    itens = []
    vistos = set()
    for linha in cap.splitlines():
        m = re.search(r"\b(\d{1,2})[/.](\d{1,2})\b", linha)
        if not m:
            continue
        # cabeçalhos de fim de semana/feriadão ("14 e 15/11", "20 a 22/11 · Feriadão") não são shows
        if re.search(r"\b\d{1,2}\s*(e|a|à|até|-|–|/)\s*\d{1,2}[/.]\d{1,2}", linha, re.I) or re.search(r"final de semana|fim de semana", linha, re.I):
            continue
        resto = re.sub(r"\b\d{1,2}[/.]\d{1,2}\b", "", linha)
        hr = horario(resto)
        nome = re.sub(r"\b\d{1,2}\s?h\s?\d{0,2}\b", "", resto, flags=re.I)
        nome = re.sub(r"\b(seg|ter|qua|qui|sex|s[aá]b|dom)\w*\b", "", nome, flags=re.I)
        nome = re.sub(r"(show|[àa]s|a partir d[ae]s?)\b", "", nome, flags=re.I)
        nome = re.sub(r"^[\W_]+|[\W_]+$", "", re.sub(r"\s*[·|\-–—:]+\s*", " · ", nome)).strip(" ·")
        nome = re.sub(r"\b(feriado|finados|caf[eé])\b", "", nome, flags=re.I)
        nome = " · ".join(p.strip() for p in re.split(r"\s*·\s*", nome) if p.strip(" ·-–"))
        nome = nome.strip(" ·-–")
        if not re.search(r"[A-Za-zÀ-ú]{3}", nome) or re.match(r"\d", nome):
            continue
        data = f"{int(m.group(1)):02d}/{int(m.group(2)):02d}"
        if (data, nome.lower()) in vistos:
            continue
        vistos.add((data, nome.lower()))
        item = {"data": data, "artista": nome[:60], "show": hr}
        if re.search(r"feriado|finados", linha, re.I):
            item["obs"] = "Feriado"
        c = re.search(r"caf[eé][^\d]{0,20}(\d{1,2}\s?h\d{0,2})", linha, re.I)
        if c:
            item["cafe"] = c.group(1).replace(" ", "")
        itens.append(item)
    low = cap.lower()
    mes = next((mm for mm in MESES if f"agenda de {mm}" in low or f"programação de {mm}" in low), None)
    if len(itens) >= 3 or (mes and itens):
        if not mes and itens:
            mes = MESES[int(itens[0]["data"][3:]) - 1]
        return {"mes": mes.capitalize(), "cartaz": img, "itens": itens}
    return None


def main():
    if not TOKEN:
        sys.exit("IG_TOKEN ausente")
    fields = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp"
    q = f"fields={fields}&limit={LIMIT}&access_token={urllib.parse.quote(TOKEN)}"
    # 1) token do "login unificado"/usuário do sistema (Facebook Graph) — não expira
    # 2) token do "login do Instagram" (graph.instagram.com) — renovado a cada execução
    items = None
    for url in (f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media?{q}",
                f"https://graph.instagram.com/me/media?{q}"):
        try:
            items = get(url).get("data", [])
            print("ok:", url.split("?")[0])
            if "graph.instagram.com" in url:
                try:
                    get("https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=" + TOKEN)
                except Exception as e:
                    print("refresh falhou (segue):", e)
            break
        except Exception as e:
            print("falhou:", url.split("?")[0], e)
    if items is None:
        sys.exit("Não consegui ler o Instagram com esse token")

    IMG.mkdir(parents=True, exist_ok=True)
    keep, posts, agenda = set(), [], None
    for it in items:
        cap = it.get("caption") or ""
        src = it.get("thumbnail_url") if it.get("media_type") == "VIDEO" else it.get("media_url")
        img = None
        if src:
            name = f"{it['id']}.jpg"
            path = IMG / name
            if not path.exists():
                try:
                    with urllib.request.urlopen(src, timeout=20) as r:
                        path.write_bytes(r.read())
                except Exception as e:
                    print("imagem falhou:", it["id"], e)
            if path.exists():
                img, _ = f"data/img/{name}", keep.add(name)
        ag = agenda_do_post(cap, img)
        if ag and agenda is None:   # o mais recente vence
            agenda = ag
            continue
        posts.append({
            "id": it["id"],
            "categoria": categoria(cap),
            "data_evento": data_evento(cap),
            "horario": horario(cap),
            "titulo": titulo(cap),
            "legenda": cap[:400],
            "imagem": img,
            "permalink": it.get("permalink"),
            "publicado": it.get("timestamp"),
        })

    # remove imagens de posts que saíram da lista
    for f in IMG.glob("*.jpg"):
        if f.name not in keep:
            f.unlink()

    OUT.write_text(json.dumps({
        "updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "agenda": agenda,
        "posts": posts,
    }, ensure_ascii=False, indent=1))
    print(f"{len(posts)} posts gravados", flush=True)


if __name__ == "__main__":
    main()
