from collections import defaultdict
from pathlib import Path
from sales_call_analyzer.keywords import POSITIVE_KEYWORDS, NEGATIVE_KEYWORDS
from sales_call_analyzer.utils import language_split, is_question, extract_numbers_with_context, sentiment_score

def assign_roles(labeled_segments):
    by_spk = defaultdict(list)
    for s in labeled_segments:
        by_spk[s["speaker"]].append(s["text"])
    scores = {}
    for spk, texts in by_spk.items():
        t = " ".join(texts).lower()
        score = sum(t.count(k.lower()) for k in POSITIVE_KEYWORDS)
        scores[spk] = score
    if not scores:
        return {}
    sales = max(scores.items(), key=lambda x: x[1])[0]
    roles = {}
    for spk in by_spk.keys():
        roles[spk] = "SALES_PERSON" if spk == sales else "CLIENT"
    return roles

def analyze_metrics(labeled_segments, input_path):
    total_text = " ".join(s["text"] for s in labeled_segments)
    roles = assign_roles(labeled_segments)
    speakers = set(s["speaker"] for s in labeled_segments)
    talk_counts = defaultdict(int)
    for s in labeled_segments:
        r = roles.get(s["speaker"], s["speaker"]) 
        talk_counts[r] += len(s["text"].split())
    total_words = sum(talk_counts.values())
    client_talk_percent = round(100.0 * talk_counts.get("CLIENT", 0) / total_words, 2) if total_words else 0.0
    sales_talk_percent = round(100.0 * talk_counts.get("SALES_PERSON", 0) / total_words, 2) if total_words else 0.0
    client_questions = 0
    keyword_details = []
    pos_counts = defaultdict(int)
    neg_counts = defaultdict(int)
    for s in labeled_segments:
        role = roles.get(s["speaker"], s["speaker"]) 
        if role == "CLIENT" and is_question(s["text"]):
            client_questions += 1
        lt = s["text"].lower()
        for k in POSITIVE_KEYWORDS:
            if k.lower() in lt:
                pos_counts[k] += 1
                keyword_details.append({"keyword": k, "speaker": role, "context": s["text"]})
        for k in NEGATIVE_KEYWORDS:
            if k.lower() in lt:
                neg_counts[k] += 1
                keyword_details.append({"keyword": k, "speaker": role, "context": s["text"]})
    numbers = []
    for s in labeled_segments:
        for n in extract_numbers_with_context(s["text"]):
            n["speaker"] = roles.get(s["speaker"], s["speaker"]) 
            numbers.append(n)
    lang = language_split(total_text)
    sentiment = sentiment_score(total_text)
    engagement_rating = min(100, int(round((client_talk_percent + client_questions * 5))))
    summary = "Sales call analysis generated."
    recs = []
    if client_talk_percent < 40:
        recs.append("Increase client talk time by asking open-ended questions.")
    if sentiment < 60:
        recs.append("Use more positive framing and reinforce company strengths.")
    if pos_counts.get("Projects", 0) == 0:
        recs.append("Reference past projects and outcomes to build credibility.")
    if neg_counts.get("Residential", 0) > 0:
        recs.append("Clarify focus on commercial/industrial to avoid residential confusion.")

    return {
        "call_id": Path(input_path).stem,
        "file_name": Path(input_path).name,
        "participants": ["SALES_PERSON", "CLIENT"],
        "engagement": {
            "client_questions": client_questions,
            "client_talk_percent": client_talk_percent,
            "sales_talk_percent": sales_talk_percent,
            "engagement_rating": engagement_rating,
        },
        "keywords": {
            "positive_counts": pos_counts,
            "negative_counts": neg_counts,
            "details": keyword_details,
        },
        "numeric_mentions": numbers,
        "language_usage": lang,
        "sentiment": {"positivity_score": sentiment, "summary": summary},
        "recommendations": recs,
        "segments": labeled_segments,
    }
