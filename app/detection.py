import re
from app.config import MODEL_FAST, DEFAULT_MODE
from app.llm import call_ollama

NEWS_TRIGGERS = (
    "сми", "инцидент", "произош", "следств", "полици", "погиб", "насмерть",
    "пострадал", "взорв", "задерж", "обвин", "подписаться", "t.me/", "http://", "https://"
)

PROMO_TRIGGERS = (
    "меню", "маслениц", "ресторан", "акция", "скидк", "афиша", "ивент", "мероприят",
    "концерт", "выступ", "галерея", "усадьб", "мест", "билеты", "вход", "чай", "блины",
    "кофе", "декаф", "зерно", "эспрессо", "фильтр"
)

def looks_like_news_or_promo(text: str) -> bool:
    t = text.lower()
    if any(trg in t for trg in NEWS_TRIGGERS):
        return True
    hits = sum(1 for trg in PROMO_TRIGGERS if trg in t)
    return hits >= 2

def detect_mode(text: str) -> str:
    if looks_like_news_or_promo(text):
        return "digest"

    classifier_prompt = (
        "Классифицируй текст по типу. Верни строго ОДНО слово из списка:\n"
        "travel — личный рассказ/заметки/история/путешествие\n"
        "digest — новость/пост/обзор/промо/инфо-сообщение\n"
        "work — рабочий текст/требования/план/док/задачи/аналитика\n\n"
        "Только одно слово. Без объяснений.\n\n"
        f"TEXT:\n{text}"
    )

    raw = call_ollama(classifier_prompt, model=MODEL_FAST, num_predict=10, timeout=120).lower()
    raw = re.sub(r"[^a-z]", "", raw)
    if raw in ("travel", "work", "digest"):
        return raw
    return DEFAULT_MODE
