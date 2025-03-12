import pandas as pd
from bs4 import BeautifulSoup as bs
import requests
import os
from openpyxl import Workbook

output_file = "hotels_tunisie.xlsx"

# Check if the file exists
if not os.path.exists(output_file):
    wb = Workbook()
    wb.save(output_file)

# Load existing data
try:
    existing_hotels = pd.read_excel(output_file, sheet_name="Hotels")
    existing_reviews = pd.read_excel(output_file, sheet_name="Reviews")
except Exception:
    existing_hotels = pd.DataFrame()
    existing_reviews = pd.DataFrame()

for i in range(0, 1000):
    url = f'https://tn.tunisiebooking.com/detail_hotel_{i}/'
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Skipping hotel ID {i}: Error {response.status_code}")
        continue

    soup = bs(response.text, 'html.parser')

    hotels, etoiles, note_desc, adresse = [], [], [], []
    hotel_name = soup.find('h1').text.strip()
    if not hotel_name:
        print(f"Skipping hotel ID {i}: No hotel found")
        continue
    hotels.append(hotel_name)

    etoile = soup.find('span', class_='span_tripadv')
    etoiles.append(etoile.text.strip() if etoile else "N/A")
    note = soup.find('span', class_='notetrip')
    note_desc.append(note.text.strip() if note else "N/A")

    address = soup.find('div', class_='adresse_hotel')
    adresse.append(address.text.strip() if address else "N/A")

    description_div = soup.find('div', id='descriptif_div')
    if description_div:
        paragraphs = [p.get_text(strip=True) for p in description_div.find_all('p')]
        full_description = " ".join(paragraphs)
    else:
        full_description = "N/A"

    securite_div = soup.find('div', class_='mesure_securite')
    if securite_div:
        spans = [span.get_text(strip=True) for span in securite_div.find_all('span')]
        mesure_securite = ". ".join(spans)
    else:
        mesure_securite = "N/A"

    avis_div = soup.find_all('div', class_='col-6 desc_avis')
    avis_txts, avis_dates, avis_notes, avis_stars = [], [], [], []
    for avis in avis_div:
        texte = avis.find('div', class_='desc_avis_txt')
        avis_txt = texte.get_text(strip=True) if texte else "N/A"

        dat = avis.find('div', class_='desc_avis_date')
        avis_date = dat.get_text(strip=True) if dat else "N/A"

        note = avis.find('span')
        avis_note = note.get_text(strip=True) if note else "N/A"

        star = avis.find('img')
        if star:
            star_rating = star['src'].split('ratings/')[1].split('-')[0]
        else:
            star_rating = 'N/A'

        avis_txts.append(avis_txt)
        avis_dates.append(avis_date)
        avis_notes.append(avis_note)
        avis_stars.append(star_rating)

    review = {
        'hotel_id': i,
        'texte': avis_txts,
        'date': avis_dates,
        'note': avis_notes,
        'stars': avis_stars
    }
    df_review = pd.DataFrame(review)

    q_r = soup.find_all('div', class_='list_questions')
    questions, responses = [], []
    for content in q_r:
        q_content = content.find('button')
        question = q_content.get_text(strip=True) if q_content else "N/A"
        questions.append(question)

        r_content = content.find('p')
        response = r_content.get_text(strip=True) if r_content else "N/A"
        responses.append(response)

    df_hotels = pd.DataFrame({
        'id': i,
        'Nom Hôtel': hotels,
        'Étoiles': etoiles,
        'description': full_description,
        'securite': mesure_securite,
        'Avis (desc)': note_desc,
        'Adresse': adresse,
        'Questions': [", ".join(questions)],
        'Responses': [", ".join(responses)]
    })

    # Append new hotel and review to existing data
    combined_hotels = pd.concat([existing_hotels, df_hotels], ignore_index=True)
    combined_reviews = pd.concat([existing_reviews, df_review], ignore_index=True)

    # Write updated data back to the file after each hotel
    with pd.ExcelWriter(output_file, mode='w', engine='openpyxl') as writer:
        combined_hotels.to_excel(writer, index=False, sheet_name="Hotels")
        combined_reviews.to_excel(writer, index=False, sheet_name="Reviews")

    print(f"Hotel ID {i} written to the file.")

    # Update existing data for the next iteration
    existing_hotels = combined_hotels
    existing_reviews = combined_reviews

print("Scraping terminé avec succès ✅.")
