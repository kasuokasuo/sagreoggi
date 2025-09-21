import requests
from bs4 import BeautifulSoup
import pandas as pd
from fuzzywuzzy import fuzz
import csv
import json

# --- Config ---
URL = "https://sagreautentiche.it/ricerca-la-tua-sagra/"
RAW_CSV = "sagre_raw.csv"
JSON_FILE = "sagre_final.json"
CSV_FILE = "sagre_final.csv"
COMUNI_CSV = "comuni_italiani.csv"  # File con colonne: citta,provincia

# --- Carica mappa città -> provincia dal CSV ---
COMUNI_CSV = "comuni_italiani.csv"
mappa_citta_provincia = {}

import pandas as pd

df_comuni = pd.read_csv(COMUNI_CSV, sep=';')  # punto e virgola
df_comuni.columns = [c.strip().lower() for c in df_comuni.columns]

for _, row in df_comuni.iterrows():
    citta = str(row["citta"]).strip() if pd.notna(row["citta"]) else ""
    provincia = str(row["provincia"]).strip() if pd.notna(row["provincia"]) else "NO_PROV"

    if citta:  # solo se citta non è vuota
        mappa_citta_provincia[citta] = provincia

# --- Funzioni ---
def parse_date(date_str):
    months = {
        "Gennaio":1,"Febbraio":2,"Marzo":3,"Aprile":4,"Maggio":5,"Giugno":6,
        "Luglio":7,"Agosto":8,"Settembre":9,"Ottobre":10,"Novembre":11,"Dicembre":12
    }
    if not date_str or date_str.upper() == "NO_DATE":
        return None, None
    date_str = date_str.strip()
    try:
        if " - " in date_str:
            start_str, end_str = date_str.split(" - ")
            s_day, s_month, s_year = start_str.strip().split()
            e_day, e_month, e_year = end_str.strip().split()
            start = f"{int(s_year):04d}-{months[s_month]:02d}-{int(s_day):02d}"
            end   = f"{int(e_year):04d}-{months[e_month]:02d}-{int(e_day):02d}"
        else:
            d, m, y = date_str.strip().split()
            start = end = f"{int(y):04d}-{months[m]:02d}-{int(d):02d}"
        return start, end
    except Exception:
        return None, None
        
def format_date(start, end):
    """Formatta start/end compatto, senza zero iniziale e senza spazi tra i giorni se stesso mese"""
    import datetime

    months = [
        "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
    ]

    if not start or not end:
        return ""

    try:
        start_dt = datetime.datetime.strptime(start, "%Y-%m-%d")
        end_dt   = datetime.datetime.strptime(end, "%Y-%m-%d")
    except Exception:
        return ""

    # stessa data
    if start_dt == end_dt:
        return f"{start_dt.day} {months[start_dt.month-1]} {start_dt.year}"

    # stesso anno e mese
    if start_dt.year == end_dt.year and start_dt.month == end_dt.month:
        return f"{start_dt.day}-{end_dt.day} {months[start_dt.month-1]} {start_dt.year}"
    # stesso anno, mesi diversi
    elif start_dt.year == end_dt.year:
        return f"{start_dt.day} {months[start_dt.month-1]} - {end_dt.day} {months[end_dt.month-1]} {start_dt.year}"
    # anno diverso
    else:
        return f"{start_dt.day} {months[start_dt.month-1]} {start_dt.year} - {end_dt.day} {months[end_dt.month-1]} {end_dt.year}"


def normalize_name(name):
    return name.lower().strip()

# --- Scraping ---
response = requests.get(URL)
soup = BeautifulSoup(response.text, "html.parser")
raw_sagre = []

for div in soup.select("div.spacer-y.gap-2"):
    # Nome sagra
    h2 = div.find("h2")
    nome = h2.get_text(strip=True) if h2 else "NO_NOME"

    # Date
    time_tag = div.find("time", class_="time")
    date_str = time_tag.get_text(strip=True) if time_tag else "NO_DATE"
    start, end = parse_date(date_str)
    if start is None or end is None:
        continue

    # Città
    p_tag = div.find("p", class_="text-primary uppercase text-sm")
    if p_tag:
        b_tag = p_tag.find("b")
        citta = b_tag.get_text(strip=True) if b_tag else "NO_CITTA"
    else:
        citta = "NO_CITTA"

    provincia = mappa_citta_provincia.get(citta, "NO_PROV")

    raw_sagre.append({
        "nome": nome,
        "date": date_str,
        "start": start,
        "end": end,
        "citta": citta,
        "provincia": provincia
    })

# --- Salva CSV intermedio ---
with open(RAW_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["nome","date","start","end","citta","provincia"])
    writer.writeheader()
    for s in raw_sagre:
        writer.writerow(s)

# --- Deduplica fuzzy su nome+data+città ---
sagre_final = []
seen = []

for s in raw_sagre:
    norm_nome = normalize_name(s["nome"])
    chiave = (norm_nome, s["date"], s["citta"])
    if any(fuzz.ratio(norm_nome, n) > 90 and d == s["date"] and c == s["citta"] for n,d,c in seen):
        continue
    seen.append(chiave)
    sagre_final.append(s)

# --- Aggiorna città con provincia e formatta date compatto ---
for s in sagre_final:
    # Pulisci città e provincia separata
    citta = s.get("citta", "NO_CITTA").strip()
    provincia = mappa_citta_provincia.get(citta, "NO_PROV")
    s["citta"] = citta
    s["provincia"] = provincia

    # Mantieni start/end per calendario
    s["start"] = s.get("start","")[:10]
    s["end"]   = s.get("end","")[:10]

    # Format compatto per la colonna "date"
    s["date"] = format_date(s["start"], s["end"])

# --- Salva JSON e CSV finale con nome standard per il sito ---
with open("sagre_processed.json", "w", encoding="utf-8") as f:
    json.dump(sagre_final, f, ensure_ascii=False, indent=2)

with open("sagre_processed.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["nome","date","start","end","citta","provincia"])
    writer.writeheader()
    for s in sagre_final:
        writer.writerow(s)

print(f"💾 File salvati: sagre_final.json e sagre_final.csv")

# --- Check ---
no_prov = [s for s in sagre_final if s["provincia"] == "NO_PROV"]
print(f"Totale sagre raw: {len(raw_sagre)}")
print(f"Sagre uniche: {len(sagre_final)}")
print(f"Sagre senza provincia: {len(no_prov)}")
if no_prov:
    print([s["citta"] for s in no_prov])
print(f"💾 File salvati: {JSON_FILE}, {CSV_FILE}, sagre_final_prov.json, sagre_final_prov.csv")
