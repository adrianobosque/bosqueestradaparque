"""Puxa nota e avaliações do Google (Places API New) e grava data/google.json.
Mostra no site só avaliações 5 estrelas com texto. As 'fixas' (escolhidas à mão) são preservadas.
Secrets: GOOGLE_API_KEY e GOOGLE_PLACE_ID. Sem eles, o script não faz nada."""
import json, os, pathlib, urllib.request

KEY, PID = os.environ.get("GOOGLE_API_KEY"), os.environ.get("GOOGLE_PLACE_ID")
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "google.json"


def main():
    if not (KEY and PID):
        print("GOOGLE_API_KEY/GOOGLE_PLACE_ID ausentes — pulando")
        return
    data = json.loads(OUT.read_text()) if OUT.exists() else {}
    req = urllib.request.Request(
        f"https://places.googleapis.com/v1/places/{PID}?languageCode=pt-BR",
        headers={"X-Goog-Api-Key": KEY,
                 "X-Goog-FieldMask": "rating,userRatingCount,googleMapsUri,reviews"})
    with urllib.request.urlopen(req, timeout=30) as r:
        p = json.load(r)
    novas = []
    for rv in p.get("reviews", []):
        txt = ((rv.get("originalText") or rv.get("text") or {}).get("text") or "").strip()
        if rv.get("rating") == 5 and len(txt) >= 20:
            a = rv.get("authorAttribution", {})
            novas.append({"autor": a.get("displayName"), "foto": a.get("photoUri"),
                          "texto": txt[:420], "quando": rv.get("relativePublishTimeDescription"),
                          "publicado": rv.get("publishTime")})
    # junta com as que já tínhamos (o Google devolve só 5 por vez), sem repetir, mais recentes primeiro
    vistos, todas = set(), []
    for rv in novas + data.get("reviews", []):
        k = (rv.get("autor"), rv.get("texto", "")[:60])
        if k not in vistos:
            vistos.add(k); todas.append(rv)
    todas.sort(key=lambda x: x.get("publicado") or "", reverse=True)
    data.update({"rating": p.get("rating"), "total": p.get("userRatingCount"),
                 "maps": data.get("maps") or p.get("googleMapsUri"),
                 "review_url": f"https://search.google.com/local/writereview?placeid={PID}",
                 "reviews": todas[:12]})
    data.setdefault("fixas", [])
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    print(f"nota {data['rating']} ({data['total']}) · {len(todas[:12])} avaliações 5★")


if __name__ == "__main__":
    main()
