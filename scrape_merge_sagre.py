import requests
from bs4 import BeautifulSoup
import json
import csv
import re
from fuzzywuzzy import fuzz

def format_date(raw_date):
    """Converte '26-27-28 Agosto 2025' → '26 - 28 Agosto 2025'"""
    giorni = re.findall(r"\d{1,2}", raw_date)
    meseanno = re.findall(r"[A-Za-zÀ-ÿ]+ \d{4}", raw_date)
    if giorni and meseanno:
        if len(giorni) > 1:
            return f"{giorni[0]} - {giorni[-1]} {meseanno[0]}"
        else:
            return f"{giorni[0]} {meseanno[0]}"
    return raw_date.strip()

# ---------------- Fonti ----------------

def scrape_assosagre():
    url = "https://www.assosagre.it/calendario_sagre.php?id_regioni=0&id_province=0&data=all&ordina_sagra=date_sagra"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    sagre = []
    for s in soup.select(".datiSagra"):
        nome = s.find("h1").get_text(strip=True) if s.find("h1") else ""
        luogo = s.find("p").get_text(strip=True) if s.find("p") else ""
        date_raw = s.find("span", class_="Sagratelefono").get_text(strip=True) if s.find("span", class_="Sagratelefono") else ""
        date = format_date(date_raw)
        match = re.match(r"(.+)\s+\((\w+)\)", luogo)
        if match:
            citta, provincia = match.groups()
        else:
            citta, provincia = luogo, ""
        sagre.append({
            "nome": nome,
            "citta": citta.strip(),
            "provincia": provincia.strip(),
            "date": date,
            "fonte": "Assosagre"
        })
    return sagre

def scrape_solosagre():
    """Esempio da SoloSagere, da adattare HTML reale"""
    url = "https://www.solosagre.it/"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    sagre = []
    for s in soup.select(".evento"):
        nome = s.find("h2").get_text(strip=True) if s.find("h2") else ""
        citta = s.find("p", class_="luogo").get_text(strip=True) if s.find("p", class_="luogo") else ""
        date_raw = s.find("span", class_="data").get_text(strip=True) if s.find("span", class_="data") else ""
        date = format_date(date_raw)
        sagre.append({
            "nome": nome,
            "citta": citta,
            "provincia": "",
            "date": date,
            "fonte": "SoloSagere"
        })
    return sagre

def scrape_sagritaly():
    """Scraping dal sito Sagritaly"""
    url = "https://sagritaly.com/"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    sagre = []
    eventi = soup.select(".w-post-elm")
    for e in eventi:
        nome_tag = e.select_one(".post_title.usg_post_title_1.has_text_color.woocommerce-loop-product__title.color_link_inherit")
        nome = nome_tag.get_text(strip=True) if nome_tag else ""

        date_tag = e.select_one(".w-hwrapper.usg_hwrapper_2.has_text_color.align_none.valign_top")
        date_raw = date_tag.get_text(strip=True) if date_tag else ""
        date = format_date(date_raw)

        citta_tag = e.select_one(".post_custom_field.usg_post_custom_field_4.type_text.luogo_evento.color_link_inherit")
        citta = citta_tag.get_text(strip=True) if citta_tag else ""

        provincia_tag = e.select_one(".post_taxonomy.usg_post_taxonomy_2.style_simple.color_link_inherit")
        provincia_raw = provincia_tag.get_text(strip=True) if provincia_tag else ""
        provincia = provincia_raw.strip()[-2:] if provincia_raw else ""

        sagre.append({
            "nome": nome,
            "citta": citta,
            "provincia": provincia,
            "date": date,
            "fonte": "Sagritaly"
        })
    return sagre

def scrape_sagrefestival():
    """Placeholder SagreFestival"""
    url = "https://sagritaly.com/categoria/eventi-e-sagre/"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    sagre = []
    # da adattare selettori reali
    return sagre

# ---------------- Duplicati ----------------

def rimuovi_duplicati(sagre):
    uniche = []
    visti = []
    for s in sagre:
        key = f"{s['nome'].lower()}|{s['citta'].lower()}|{s['date'].lower()}"
        if any(fuzz.ratio(key, v) > 90 for v in visti):
            continue
        visti.append(key)
        uniche.append(s)
    return uniche

# ---------------- Main ----------------

if __name__ == "__main__":
    sagre = []
    sagre.extend(scrape_assosagre())
    sagre.extend(scrape_solosagre())
    sagre.extend(scrape_sagritaly())
    sagre.extend(scrape_sagrefestival())

    print(f"✅ Raccolte {len(sagre)} sagre totali (prima dei filtri)")

    sagre = rimuovi_duplicati(sagre)
    print(f"🎉 {len(sagre)} sagre uniche trovate")

    # JSON
    with open("sagre_final.json", "w", encoding="utf-8") as f:
        json.dump(sagre, f, ensure_ascii=False, indent=2)

    # CSV
    with open("sagre_final.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["nome","citta","provincia","date","fonte"])
        writer.writeheader()
        writer.writerows(sagre)

    print("💾 File salvati: sagre_final.json e sagre_final.csv")
