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


DIA_SEM = r"(seg|ter|qua|qui|sex|s[aá]b|dom)\w*\.?"
HORA = r"\d{1,2}\s?h\s?\d{0,2}"


def shows_da_legenda(cap, ref=None):
    """Lê os shows da legenda. Aceita:
       '21/11 · Gu Salvator · 12h30'
       'Sáb 14 · Ani Belle — café 10h, almoço 12h, show 12h30'   (mês vem do cabeçalho ou da data do post)
    """
    ref = ref or datetime.date.today()
    mes_cab = None
    m_cab = re.search(r"\d{1,2}\s*(?:e|a|à|até|-|–|—)\s*\d{1,2}[/.](\d{1,2})", cap)
    if m_cab:
        mes_cab = int(m_cab.group(1))
    itens, vistos = [], set()
    for linha in cap.splitlines():
        if re.search(r"\b\d{1,2}\s*(e|a|à|até|-|–|—|/)\s*\d{1,2}[/.]\d{1,2}", linha, re.I) or re.search(r"final de semana|fim de semana", linha, re.I):
            continue  # cabeçalho ("14–15/11 · Fim de semana", "20 a 22/11 · Feriadão")
        m = re.search(r"\b(\d{1,2})[/.](\d{1,2})\b", linha)
        if m:
            dia, mes = int(m.group(1)), int(m.group(2))
            linha_sem_data = linha[:m.start()] + " " + linha[m.end():]
        else:
            m2 = re.search(DIA_SEM + r"\s+(\d{1,2})\b(?!\s*[/.:h]\d?)", linha, re.I)
            if not m2:
                continue
            dia = int(m2.group(2))
            if mes_cab:
                mes = mes_cab
            else:  # próxima ocorrência desse dia a partir da data do post
                mes = ref.month if dia >= ref.day else ref.month % 12 + 1
            linha_sem_data = linha[:m2.start()] + " " + linha[m2.end():]
        if not (1 <= dia <= 31 and 1 <= mes <= 12):
            continue
        # horário do show: 'show 12h30' > horário que não seja de café/almoço
        hs = re.search(r"show\D{0,8}(" + HORA + ")", linha_sem_data, re.I)
        sem_refeicao = re.sub(r"(caf[eé]|almo[cç]o)\D{0,15}" + HORA, " ", linha_sem_data, flags=re.I)
        hr = horario(hs.group(1)) if hs else horario(sem_refeicao)
        # artista: primeiro trecho com letras que não seja palavra de serviço
        txt = re.sub(DIA_SEM, " ", sem_refeicao, flags=re.I)
        txt = re.sub(r"\(?\b(feriado|feriadão|finados)\b\)?", " ", txt, flags=re.I)
        txt = re.sub(r"(show|[àa]s|a partir d[ae]s?)\s*" + HORA, " ", txt, flags=re.I)
        txt = re.sub(HORA, " ", txt, flags=re.I)
        nome = ""
        for parte in re.split(r"\s[—–-]\s|[·|,—–:]", txt):
            parte = re.sub(r"[^\wÀ-ú&'. ]", " ", parte).strip(" .")
            parte = re.sub(r"\s+", " ", parte)
            if re.search(r"[A-Za-zÀ-ú]{3}", parte) and not re.fullmatch(r"(?i)(show|caf[eé]|almo[cç]o|ao vivo|m[uú]sica ao vivo)", parte):
                nome = parte
                break
        if not nome or re.match(r"\d", nome):
            continue
        data = f"{dia:02d}/{mes:02d}"
        if (data, nome.lower()) in vistos:
            continue
        vistos.add((data, nome.lower()))
        item = {"data": data, "artista": nome[:60], "show": hr}
        if re.search(r"feriado|finados", linha, re.I):
            item["obs"] = "Feriado"
        c = re.search(r"caf[eé]\D{0,20}(" + HORA + ")", linha, re.I)
        if c:
            item["cafe"] = c.group(1).replace(" ", "")
        itens.append(item)
    return itens


def mes_da_legenda(cap):
    low = cap.lower()
    return next((mm for mm in MESES if f"agenda de {mm}" in low or f"programação de {mm}" in low), None)


def agenda_do_post(cap, img, carrossel=False, ref=None):
    """Agenda do MÊS: legenda com 'Agenda de <mês>' ou muitas datas (e não é o carrossel semanal)."""
    itens = shows_da_legenda(cap, ref)
    mes = mes_da_legenda(cap)
    if (mes and itens) or (len(itens) >= 5 and not carrossel):
        if not mes and itens:
            mes = MESES[int(itens[0]["data"][3:]) - 1]
        return {"mes": mes.capitalize(), "cartaz": img, "itens": itens}
    return None


def data_post(it):
    try:
        return datetime.datetime.strptime(it.get("timestamp", "")[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def semana_do_post(cap, it, baixar):
    """Carrossel SEMANAL: uma foto por artista, na mesma ordem das linhas da legenda.
    Se houver mais fotos que shows, as primeiras são capa e são ignoradas."""
    if it.get("media_type") != "CAROUSEL_ALBUM" or mes_da_legenda(cap):
        return None
    itens = shows_da_legenda(cap, data_post(it))
    if not (1 <= len(itens) <= 6):
        return None
    filhos = [c for c in (it.get("children") or {}).get("data", [])]
    fotos = []
    for n, c in enumerate(filhos):
        src = c.get("thumbnail_url") if c.get("media_type") == "VIDEO" else c.get("media_url")
        fotos.append(baixar(src, f"{it['id']}_{n}.jpg") if src else None)
    # 1 foto por artista: se há mais fotos que shows, a 1ª é capa e os artistas vêm em seguida
    off = 1 if len(fotos) > len(itens) else 0
    for k, item in enumerate(itens):
        if off + k < len(fotos) and fotos[off + k]:
            item["foto"] = fotos[off + k]
    return {"post": it.get("permalink"), "publicado": it.get("timestamp"), "itens": itens}


def main():
    if not TOKEN:
        sys.exit("IG_TOKEN ausente")
    fields = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,children{media_type,media_url,thumbnail_url}"
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

    perfil = None
    try:
        pf = get(f"https://graph.facebook.com/v21.0/{IG_USER_ID}?fields=followers_count,media_count&access_token={urllib.parse.quote(TOKEN)}")
        perfil = {"seguidores": pf.get("followers_count"), "posts": pf.get("media_count")}
        print("perfil:", perfil)
    except Exception as e:
        print("perfil falhou (segue):", e)
    # visualizações totais = 6.910.412 (mídia kit, até 31/08/2026) + soma diária desde 01/09 (precisa de permissão de insights)
    try:
        base, ini = 6910412, datetime.date(2026, 9, 1)
        hoje, total, d = datetime.date.today(), 0, ini
        while d < hoje:
            fim = min(d + datetime.timedelta(days=30), hoje)
            r = get(f"https://graph.facebook.com/v21.0/{IG_USER_ID}/insights?metric=views&period=day&metric_type=total_value"
                    f"&since={int(datetime.datetime(d.year, d.month, d.day).timestamp())}&until={int(datetime.datetime(fim.year, fim.month, fim.day).timestamp())}"
                    f"&access_token={urllib.parse.quote(TOKEN)}")
            for m in r.get("data", []):
                total += (m.get("total_value") or {}).get("value", 0) or 0
            d = fim
        if perfil is not None:
            perfil["views"] = base + total
        print("views:", base + total)
    except Exception as e:
        print("views falhou (sem permissão de insights?):", e)

    IMG.mkdir(parents=True, exist_ok=True)
    keep, posts, agenda, semana = set(), [], None, None

    def baixar(src, name):
        path = IMG / name
        if not path.exists():
            try:
                with urllib.request.urlopen(src, timeout=20) as r:
                    path.write_bytes(r.read())
            except Exception as e:
                print("imagem falhou:", name, e)
        if path.exists():
            keep.add(name)
            return f"data/img/{name}"
        return None

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
        carrossel = it.get("media_type") == "CAROUSEL_ALBUM"
        if semana is None:          # o carrossel semanal mais recente vence
            sm = semana_do_post(cap, it, baixar)
            if sm:
                semana = sm
                print("semana:", [(i["data"], i["artista"], bool(i.get("foto"))) for i in sm["itens"]])
        ag = agenda_do_post(cap, img, carrossel, data_post(it))
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
        "semana": semana,
        "perfil": perfil,
        "posts": posts,
    }, ensure_ascii=False, indent=1))
    print(f"{len(posts)} posts gravados", flush=True)


if __name__ == "__main__":
    main()
