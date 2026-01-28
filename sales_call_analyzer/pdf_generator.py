from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

def generate_pdf(data, out_path):
    doc = SimpleDocTemplate(str(out_path), pagesize=A4)
    styles = getSampleStyleSheet()
    elems = []
    elems.append(Paragraph("Sales Call Report", styles["Title"]))
    elems.append(Spacer(1, 12))
    elems.append(Paragraph(f"Call ID: {data['call_id']}", styles["Normal"]))
    elems.append(Paragraph(f"File: {data['file_name']}", styles["Normal"]))
    elems.append(Spacer(1, 12))
    elems.append(Paragraph("Engagement Metrics", styles["Heading2"]))
    eng = data["engagement"]
    eng_table = Table([
        ["Client Questions", eng["client_questions"]],
        ["Client Talk %", eng["client_talk_percent"]],
        ["Sales Talk %", eng["sales_talk_percent"]],
        ["Engagement Rating", eng["engagement_rating"]],
    ])
    eng_table.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 0.5, colors.black)]))
    elems.append(eng_table)
    elems.append(Spacer(1, 12))
    elems.append(Paragraph("Keyword Analysis", styles["Heading2"]))
    pos = data["keywords"]["positive_counts"]
    neg = data["keywords"]["negative_counts"]
    pos_rows = [[k, str(pos.get(k, 0))] for k in sorted(pos.keys())]
    neg_rows = [[k, str(neg.get(k, 0))] for k in sorted(neg.keys())]
    elems.append(Paragraph("Positive Keywords", styles["Heading3"]))
    elems.append(Table(pos_rows or [["None","0"]], style=TableStyle([("GRID", (0,0), (-1,-1), 0.5, colors.black)])))
    elems.append(Paragraph("Negative Keywords", styles["Heading3"]))
    elems.append(Table(neg_rows or [["None","0"]], style=TableStyle([("GRID", (0,0), (-1,-1), 0.5, colors.black)])))
    elems.append(Spacer(1, 12))
    elems.append(Paragraph("Company Numbers Mentioned", styles["Heading2"]))
    num_rows = [[n["value"], n["speaker"], n["context"][:80]] for n in data["numeric_mentions"]]
    elems.append(Table(num_rows or [["None","",""]], style=TableStyle([("GRID", (0,0), (-1,-1), 0.5, colors.black)])))
    elems.append(Spacer(1, 12))
    elems.append(Paragraph("Language Usage", styles["Heading2"]))
    lang = data["language_usage"]
    elems.append(Table([["English %", lang["english_percent"]],["Hindi %", lang["hindi_percent"]]], style=TableStyle([("GRID", (0,0), (-1,-1), 0.5, colors.black)])))
    elems.append(Spacer(1, 12))
    elems.append(Paragraph("Sentiment & Positivity", styles["Heading2"]))
    sent = data["sentiment"]
    elems.append(Table([["Positivity Score", sent["positivity_score"]]], style=TableStyle([("GRID", (0,0), (-1,-1), 0.5, colors.black)])))
    elems.append(Paragraph(sent.get("summary",""), styles["Normal"]))
    elems.append(Spacer(1, 12))
    elems.append(Paragraph("Actionable Suggestions", styles["Heading2"]))
    for r in data.get("recommendations", []):
        elems.append(Paragraph(f"• {r}", styles["Normal"]))
    elems.append(Spacer(1, 12))
    elems.append(Paragraph("Appendix: JSON Dump", styles["Heading2"]))
    j = json_min(data)
    elems.append(Paragraph(j[:4000], styles["Code"]))
    doc.build(elems)

def json_min(data):
    import json
    return json.dumps(data, ensure_ascii=False)

