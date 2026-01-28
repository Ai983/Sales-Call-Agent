import re
import unicodedata
import time

def timestamp_id():
    return str(int(time.time()))

def safe_filename(name):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", name)

def is_devanagari(ch):
    return "devanagari" in unicodedata.name(ch, "").lower()

def language_split(text):
    words = re.findall(r"\w+", text, flags=re.UNICODE)
    hi = 0
    en = 0
    for w in words:
        if any(is_devanagari(c) for c in w):
            hi += 1
        else:
            en += 1
    total = hi + en
    if total == 0:
        return {"hindi_percent": 0.0, "english_percent": 0.0}
    return {"hindi_percent": round(100.0 * hi / total, 2), "english_percent": round(100.0 * en / total, 2)}

def is_question(text):
    from sales_call_analyzer.keywords import QUESTION_PATTERNS
    t = text.lower()
    return any(p in t for p in QUESTION_PATTERNS)

def extract_numbers_with_context(text):
    res = []
    for m in re.finditer(r"\b(\d+[\d,]*\+?|\d+\s*(m|lakh|crore)\+?)\b", text, flags=re.IGNORECASE):
        start = max(0, m.start() - 60)
        end = min(len(text), m.end() + 60)
        ctx = text[start:end].strip()
        res.append({"value": m.group(0), "context": ctx})
    return res

def sentiment_score(text):
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import torch
        name = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
        tok = AutoTokenizer.from_pretrained(name)
        mdl = AutoModelForSequenceClassification.from_pretrained(name)
        inputs = tok(text[:2000], return_tensors="pt", truncation=True)
        with torch.no_grad():
            logits = mdl(**inputs).logits
        probs = torch.softmax(logits, dim=-1)[0].tolist()
        pos = probs[2]
        return int(round(pos * 100))
    except Exception:
        pos_words = ["good","great","excellent","positive","success","happy"]
        neg_words = ["bad","poor","negative","fail","unhappy"]
        t = text.lower()
        pos = sum(t.count(w) for w in pos_words)
        neg = sum(t.count(w) for w in neg_words)
        total = pos + neg
        if total == 0:
            return 50
        return int(round(100.0 * pos / total))
