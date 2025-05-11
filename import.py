import csv
import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.expected_conditions import text_to_be_present_in_element

# . Options pour éviter la détection Selenium
options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-usb"])
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
options.add_argument("--headless")  # Mode sans affichage (optionnel)
options.add_argument("--disable-gpu")  # Utile pour éviter certains bugs graphiques
options.add_argument("--no-sandbox")  # Utile sur certains systèmes
options.add_argument("--no-sandbox")  # Mode sans sandbox (utile pour certains environnements)
options.add_argument("--disable-software-rasterizer")  # Évite le fallback WebGL
options.add_argument("--enable-unsafe-swiftshader")  # Active SwiftShader si nécessaire

# . Initialiser le driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.maximize_window()

# . Ouvrir Booking


# Liste des villes en Tunisie
villes  = ["Sousse", "Djerba", "Monastir", "Mahdia", "Nabeul", "Tozeur", "Gabès", "Bizerte","Tabarka","Jendouba","Tataouine","Ksar Ghilane","Kairouan","Gammarth","Sidi Bou Saïd"]
#villes  = ["Sousse"]

# URL de base
base_url = "https://www.booking.com/searchresults.fr.html"

# Paramètres communs (sans dest_id)
params = {
    "label": "gen173nr-1BCAEoggI46AdIM1gEaOIBiAEBmAENuAEXyAEM2AEB6AEBiAIBqAIDuALGm5i-BsACAdICJDkzZjQwZjdiLTY4MjYtNGJiNC1iZjlmLTFhYTE5YWRlNTI4N9gCBeACAQ",
    "sid": "8e11517f25264d2433d276d0408b21f4",
    "aid": "304142",
    "lang": "fr",
    "checkin": "2025-03-09",
    "checkout": "2025-03-10",
    "group_adults": "1",
    "no_rooms": "1",
    "group_children": "0",
    "nflt": "ht_id%3D204"
}
hotels_data = []
commentaires = []
questions=[]
# Générer les URLs pour chaque ville
for ville in villes:
    params["ss"] = ville
    url = base_url + "?" + "&".join([f"{key}={value}" for key, value in params.items()])
    
    print(f"\n🔍 Scraping des hôtels à {ville}...")
    driver.get(url)
    time.sleep(2)  # Laisser le temps à la page de charger


    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.cca574b93c[data-results-container='1']"))
        )
    except:
        print("Aucun hôtel trouvé, vérifie les sélecteurs CSS !")
        driver.quit()
        exit()

    # . Scroller pour charger tous les hôtels
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break  
        last_height = new_height

    # . Trouver les hôtels après le scrolling
    hotels = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='property-card']")
    print(f"Nombre d'hôtels trouvés : {len(hotels)}")


    for hotel in hotels:
        if driver.session_id is None:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        try:
            try:
                nom = hotel.find_element(By.CSS_SELECTOR, "div[data-testid='title']").text.strip()
            except:
                nom="non disponible"
            # . Prix
            try:
                prix = hotel.find_element(By.CSS_SELECTOR, "span[data-testid='price-and-discounted-price']").text.strip()
            except:
                prix = "Non disponible"

            place = ville
            # . Note et expériences
            rate_container = hotel.find_elements(By.CSS_SELECTOR, "div[data-testid='review-score']")
            if rate_container:  # Vérifier si l'élément existe
                rate_container = rate_container[0]  # Récupérer le premier élément trouvé
                rate = rate_container.find_elements(By.CSS_SELECTOR, "div.ac4a7896c7")
                rating_category = rate_container.find_elements(By.CSS_SELECTOR, "div.a3b8729ab1.e6208ee469.cb2cbb3ccb")
                experiences_text = rate_container.find_elements(By.CSS_SELECTOR, "div.abf093bdfe.f45d8e4c32.d935416c47")

                rate = rate[0].text.strip() if rate else "Non disponible"
                rating_category = rating_category[0].text.strip() if rating_category else "Non disponible"
                experiences_text = experiences_text[0].text.strip() if experiences_text else "Non disponible"

                experiences = re.search(r'\d+', experiences_text)
                experiences = experiences.group() if experiences else "Non disponible"
            else:
                rate, rating_category, experiences = "Non disponible", "Non disponible", "Non disponible"
            '''
            try:
                rate_container = WebDriverWait(hotel, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='review-score']"))
                )    
                rate = rate_container.find_element(By.CSS_SELECTOR, "div.ac4a7896c7").text.strip()
                rating_category = rate_container.find_element(By.CSS_SELECTOR, "div.a3b8729ab1.e6208ee469.cb2cbb3ccb").text.strip()
                experiences_text = rate_container.find_element(By.CSS_SELECTOR, "div.abf093bdfe.f45d8e4c32.d935416c47").text.strip()
                experiences = re.search(r'\d+', experiences_text)
                experiences = experiences.group() if experiences else "Non disponible"
            except:
                rate, rating_category, experiences = "Non disponible", "Non disponible", "Non disponible"
            '''
            # . Lien de l'hôtel
            time.sleep(3)
            try:
                link_element = hotel.find_element(By.CSS_SELECTOR, "a[data-testid='title-link']")
                hotel_link = link_element.get_attribute("href")
            except:
                print(f" Pas de lien pour : {nom}")
                continue  # Passer à l'hôtel suivant
            
            # . Ouvrir la page de l'hôtel pour extraire des avis
            driver.execute_script("window.open('');")  
            driver.switch_to.window(driver.window_handles[1])  
            driver.get(hotel_link)
            # Attendre que la page charge
            time.sleep(10)
            try:
                adresse_container = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="PropertyHeaderAddressDesktop-wrapper"]')
                adresse_hotel = adresse_container.find_element(By.CSS_SELECTOR, 'div.a53cbfa6de.f17adf7576').text.strip().split("\n")[0] 
                
            except:
                adresse_hotel="Non disponible"

            # Localiser tous les éléments <li> dans la liste des points forts
            #points_forts_elements = driver.find_elements(By.CSS_SELECTOR, "ul[class*='c807d72881'] li")
            points_forts_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='property-most-popular-facilities-wrapper'] li")
            #environs_elements=driver.find_elements(By.CSS_SELECTOR, "div[data-testid='property-section--content'] li")
            #environs_elements = driver.find_elements(By.CSS_SELECTOR, "ul[data-testid='poi-block-list'] li")
            #environs_elements1 = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='property-section--content'] ul[data-testid='poi-block-list']:nth-of-type(1) li")
            #environs_elements2 = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='property-section--content'] ul[data-testid='poi-block-list']:nth-of-type(2) li")
            #environs_elements3 = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='property-section--content'] ul[data-testid='poi-block-list']:nth-of-type(3) li")
            #environs_elements4 = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='property-section--content'] ul[data-testid='poi-block-list']:nth-of-type(4) li")
            #environs_elements5 = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='property-section--content'] ul[data-testid='poi-block-list']:nth-of-type(5) li")
            environs_elements3 = driver.find_elements(By.XPATH, "(//div[@data-testid='property-section--content']//ul[@data-testid='poi-block-list'])[3]/li")
            environs_elements1 = driver.find_elements(By.XPATH, "(//div[@data-testid='property-section--content']//ul[@data-testid='poi-block-list'])[1]/li")
            environs_elements2 = driver.find_elements(By.XPATH, "(//div[@data-testid='property-section--content']//ul[@data-testid='poi-block-list'])[2]/li")
            environs_elements4 = driver.find_elements(By.XPATH, "(//div[@data-testid='property-section--content']//ul[@data-testid='poi-block-list'])[4]/li")
            environs_elements5 = driver.find_elements(By.XPATH, "(//div[@data-testid='property-section--content']//ul[@data-testid='poi-block-list'])[5]/li")
                # Extraire le texte des points forts
            points_forts = [point.text.strip() for point in points_forts_elements if point.text.strip()]
            environs_hotels_lieux = [environ.text.strip() for environ in environs_elements1 if environ.text.strip()]
            environs_hotels_restau = [environ.text.strip() for environ in environs_elements2 if environ.text.strip()]
            environs_hotels_plages = [environ.text.strip() for environ in environs_elements3 if environ.text.strip()]
            environs_hotels_tronsport = [environ.text.strip() for environ in environs_elements4 if environ.text.strip()]
            environs_hotels_aeroport = [environ.text.strip() for environ in environs_elements5 if environ.text.strip()]
            question_buttons = driver.find_elements(By.CSS_SELECTOR, "button.f23b02a2a0")
            for i, button in enumerate(question_buttons[:len(question_buttons) - 1]):  # Limit to len(question_buttons) - 1
                try:
                    # Récupérer le texte de la question
                    question_element = WebDriverWait(button, 2).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "span h3[data-testid='question']"))
                            )
                    question_text = question_element.text.strip()
                    if not question_text:  # Si la liste est vide, on passe au suivant
                        print("Aucune question trouvée pour ce bouton.")
                        continue

                    # Cliquer pour afficher la réponse
                    button.click()
                    time.sleep(1)  # Attendre que la réponse s'affiche
                    # Trouver la réponse associée
                    parent_div = button.find_element(By.XPATH, "./following-sibling::div")   
                    answer_element = parent_div.find_element(By.XPATH, ".//div[contains(@class, 'a53cbfa6de')]")
                    answer_text = answer_element.text.strip()

                    # Ajouter au dictionnaire
                    questions.append({
                        "nom hotel": nom,
                        "question":question_text,
                        "answer_text":answer_text
                    })

                except Exception as e:
                    print(f"Erreur lors de l'extraction : {e}")
                    questions.append({
                        "nom hotel": nom,
                        "question":"non disponible",
                        "answer_text":"non disponible"
                    })

            try:
                # Trouver et cliquer sur le bouton " commentaires clients"
                review_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "reviews-tab-trigger"))
                )     
                review_button.click()
                time.sleep(5)  # Attendre le chargement des nouveaux commentaires
            except Exception as e:
                print(" Bouton 'Voir tous les commentaires' non trouvé ou déjà cliqué:{e}")

            
            # Scroller après avoir cliqué pour charger tous les avis
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            # . Extraire les avis
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='review']"))
                    )
                reviews = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='review']")
                for review in reviews[:10]:  # Limiter à 5 avis par hôtel pour optimiser
                    try:
                        rating = review.find_element(By.CSS_SELECTOR, "div.ac4a7896c7").text.strip()
                    except:
                        rating = "Non disponible"

                    try:
                        title = review.find_element(By.CSS_SELECTOR, "h3[data-testid='review-title']").text.strip()
                    except:
                        title = "Non disponible"

                    try:
                        #positive_review = review.find_element(By.CSS_SELECTOR, "div[data-testid='review-positive-text.a53cbfa6de b5726afd0b'] span").text.strip()
                        positive_review = review.find_element(By.CSS_SELECTOR, "div.b5726afd0b span").text.strip()
                    except:
                        positive_review = "Non disponible"

                    try:
                        date_commentaire = review.find_element(By.CSS_SELECTOR, "span[data-testid='review-date']").text.strip()
                    except:
                        date_commentaire = "Non disponible"
                    commentaires.append({
                        "nom hotel":nom,
                        "Note": rating,
                        "Titre": title,
                        "Commentaire": positive_review,
                        "Date commentaire": date_commentaire

                    })
            except:
                commentaires.append({
                        "nom hotel":nom,
                        "Note": "non dispo",
                        "Titre": "non dispo",
                        "Commentaire": "non dispo",
                        "Date commentaire": "non dispo"

                    })
            try:
                rating_container = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="quality-rating"]')
                stars = rating_container.find_elements(By.CSS_SELECTOR, 'span svg')  # Compter les étoiles SVG
                etoile = len(stars)  # Nombre d'étoiles
            except:
                etoile = "Non disponible"

            time.sleep(2)
            try:
                # Attendre que le container principal apparaisse
                fineprint_container = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="PropertyFinePrintDesktop-wrapper"]'))
                )
                # Trouver la section contenant le texte
                content_section = fineprint_container.find_element(By.CSS_SELECTOR, 'div[data-testid="property-section--content"]')
                # Récupérer tous les paragraphes
                paragraphs = content_section.find_elements(By.TAG_NAME, "p")
                extracted_texts = []
                
                for p in paragraphs:
                    text = driver.execute_script("return arguments[0].textContent;", p).strip()
                    if text:  # Ne garde que les paragraphes non vides
                        extracted_texts.append(text)

                # Joindre le texte extrait
                savoir = "\n".join(extracted_texts) if extracted_texts else "Non disponible"

            except Exception as e:
                savoir = "Non disponible"
            try:
                # Attendre que le bloc soit visible
                child_policies_block = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-test-id="child-policies-block"]'))
                )

                if child_policies_block is None:
                    print("Le bloc des conditions pour les enfants n'a pas été trouvé.")
                
                # Extraire les éléments <h2> (titres)
                h2_elements = child_policies_block.find_elements(By.XPATH, ".//h2")

                # Extraire les éléments <p> (paragraphes)
                p_elements = child_policies_block.find_elements(By.XPATH, ".//p")
                # Extraire les informations structurées (par exemple : Lit bébé, prix)
                structured_info_elements = child_policies_block.find_elements(By.XPATH, ".//div[contains(@class, 'e88206330c')]")
                # Extraire les textes
                extracted_h2_texts = [driver.execute_script("return arguments[0].textContent;", el).strip() for el in h2_elements]
                extracted_p_texts = [driver.execute_script("return arguments[0].textContent;", el).strip() for el in p_elements]
                
                # Pour les informations structurées (par exemple : Lit bébé sur demande, prix)
                extracted_structured_info = []
                for el in structured_info_elements:
                    text = driver.execute_script("return arguments[0].textContent;", el).strip()
                    extracted_structured_info.append(text)

                # Joindre les textes extraits dans l'ordre souhaité
                child_policies_text = "\n".join(extracted_h2_texts + extracted_p_texts + extracted_structured_info)
                
            except Exception as e:
                child_policies_text = "Non disponible"
    #partie Recherche des restrictions d'âge...
            try:

                # Attendre que le bloc des restrictions d'âge soit visible
                age_restriction_blocks = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.f565581f7e'))
                    )
                arrive_element = age_restriction_blocks[0]
                depart_element = age_restriction_blocks[1]
                second_element = age_restriction_blocks[4]
                animaux_element = age_restriction_blocks[5]
                arrive = WebDriverWait(arrive_element, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.a53cbfa6de'))
                )
                depart = WebDriverWait(depart_element, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.a53cbfa6de'))
                )
                age = WebDriverWait(second_element, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.a53cbfa6de'))
                )
                animal = WebDriverWait(animaux_element, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.a53cbfa6de'))
                )
                time.sleep(2)  # Attendre 2 secondes
                # Extraire le texte
                try:
                    text_js1 = driver.execute_script("return arguments[0].innerText;", arrive)
                except:
                    text_js1="non disponible"
                try:  
                    text_js2 = driver.execute_script("return arguments[0].innerText;", depart)
                except:
                    text_js2="non dispo"
                try:
                    text_js3 = driver.execute_script("return arguments[0].innerText;", age)
                except:
                    text_js3="non disponible"
                try:
                    text_js4 = driver.execute_script("return arguments[0].innerText;", animal)
                except:
                    text_js4="non disponible"


            except Exception as e:
                print(f"Erreur lors de l'extraction du texte des restrictions d'âge : {e}")

            #  Fermer l'onglet de l'hôtel et revenir à la page principale
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

            # . Ajouter les données
            hotels_data.append({
                "Lieu": place,
                "Nom HOTEL": nom,
                "adresse":adresse_hotel,
                "Etoile":etoile,
                "Prix": prix,
                "Rate nominal": rate,
                "Rate ordinal": rating_category,
                "Expériences vécues": experiences,
                "points fort":points_forts,
                "Lieux à proximité":environs_hotels_lieux,
                "Restaurants et cafés":environs_hotels_restau,
                "Plages à proximité":environs_hotels_plages,
                "Transports en commun":environs_hotels_tronsport,
                "Aéroports les plus proches":environs_hotels_aeroport,
                "a savoir":savoir,
                "Enfants et lits":child_policies_text,
                "Arrive" : text_js1,
                "depart" : text_js2,
                "restriction d'age" : text_js3,
                "Animaux domestiques" : text_js4,
            })
        except Exception as e:
            print(f" Erreur lors de l'extraction d'un hôtel : {e}")

# . Fermer le driver après extraction
driver.quit()
df_hotels = pd.DataFrame(hotels_data)
df_commentaires = pd.DataFrame(commentaires)
df_questions_reponse = pd.DataFrame(questions)

# . Sauvegarde en CSV
'''
if hotels_data:
    csv_file = "hotels_hammamet.csv"
    with open(csv_file, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["Lieu", "Nom", "Prix", "Rate nominal", "Rate ordinal", "Expériences vécues"])
        writer.writeheader()
        writer.writerows(hotels_data)

    print(f". Les données ont été stockées dans {csv_file}")
else:
    print(" Aucune donnée collectée, vérifie le site et les sélecteurs CSS.")
'''
# . Enregistrer dans un fichier Excel avec 2 feuilles
excel_file = "hotels_data.xlsx"
with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
    df_hotels.to_excel(writer, sheet_name="Hotels", index=False)
    df_commentaires.to_excel(writer, sheet_name="Commentaires", index=False)
    df_questions_reponse.to_excel(writer, sheet_name="QuestionReponse", index=False)

# Save to JSON
excel_file.to_json("hotels_data.json", orient="records", force_ascii=False)

print(f". Données enregistrées dans {excel_file}")
