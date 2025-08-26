import json
import re

# Carica il JSON
with open("sagre.json", "r", encoding="utf-8") as f:
    sagre = json.load(f)

def process_date(date_text):
    """
    Trasforma "28-29-30-31 Agosto 2025" -> "28-31 Agosto 2025"
    """
    # cerca pattern di numeri seguiti da mese e anno
    match = re.search(r"(\d+(?:-\d+)*)\s+([A-Za-z]+ \d{4})", date_text)
    if match:
        giorni = match.group(1).split("-")
        mese_anno = match.group(2)
        return f"{giorni[0]}-{giorni[-1]} {mese_anno}"
    return date_text

processed_sagre = []

for s in sagre:
    # separa città e provincia
    luogo = s.get("luogo", "")
    if "(" in luogo and ")" in luogo:
        citta, provincia = luogo.split("(")
        citta = citta.strip()
        provincia = provincia.replace(")", "").strip()
    else:
        citta = luogo
        provincia = ""

    # formatta date
    date_text = s.get("date", "")
    date_range = process_date(date_text)

    processed_sagre.append({
        "nome": s.get("nome", ""),
        "date": date_range,
        "citta": citta,
        "provincia": provincia
    })

# salva il JSON processato
with open("sagre_processed.json", "w", encoding="utf-8") as f:
    json.dump(processed_sagre, f, ensure_ascii=False, indent=2)

print(f"{len(processed_sagre)} sagre processate e salvate in sagre_processed.json")
