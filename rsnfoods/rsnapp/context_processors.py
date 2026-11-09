from .translations import TEXTS


def language(request):
    lang = request.session.get("lang", "en")
    if lang not in TEXTS:
        lang = "en"
    return {"lang": lang, "t": TEXTS[lang]}
