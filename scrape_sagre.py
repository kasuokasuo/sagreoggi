import requests
from bs4 import BeautifulSoup
import json

url = "https://www.assosagre.it/calendario_sagre.php?id_regioni=0&id_province=0&data=all&ordina_sagra=date_sagra"

res = requests.get(url)
res.raise_for_status()

soup = BeautifulSoup(res.text, "html.parser")
sagre = []

for item in soup.select(".datiSagra"):
    # Nome
    nome_tag = item.find("h1")
    nome = nome_tag.get_text(strip=True) if nome_tag else "N/A"

    # Luogo (primo <p>, testo senza <i>)
    luogo_tag = item.find("p")
    if luogo_tag:
        # rimuove eventuali tag figli come <i>
        for child in luogo_tag.find_all():
            child.extract()
        luogo_text = luogo_tag.get_text(strip=True)
    else:
        luogo_text = ""

    # Date
    date_tag = item.find("span", class_="Sagratelefono")
    date_text = date_tag.get_text(strip=True) if date_tag else "N/A"

    sagre.append({
        "nome": nome,
        "date": date_text,
        "luogo": luogo_text
    })

# Salva in JSON
with open("sagre.json", "w", encoding="utf-8") as f:
    json.dump(sagre, f, ensure_ascii=False, indent=2)

print(f"{len(sagre)} sagre salvate in sagre.json")
