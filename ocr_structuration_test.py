import easyocr
import time
import re

# Démarrer le chronomètre
start_time = time.time()

# Initialisation de l'OCR
reader = easyocr.Reader(['fr'])

# Lire le texte de l'image
results = reader.readtext('analyse1.jpg')

print('[RESULT] Résultats OCR bruts :', results)

# Définir les champs de santé à rechercher
fields = [
    'Hématies', 'Hémoglobine', 'Hématocrite', 'VGM', 'CCMH', 'TCMH', 'Leucocytes',
    'Polynucléaires Neutrophiles', 'Polynucléaires Eosinophiles',
    'Polynucléaires Basophiles', 'Lymphocytes', 'Monocytes', 'Plaquettes'
]

# Fonction pour nettoyer le texte (suppression des caractères inutiles)
def clean_text(text):
    text = text.replace('\n', ' ')
    text = re.sub(r'[^a-zA-ZÀ-ÿ0-9%\.\-,/\'\s]', '', text)
    return text.strip()

# 1. Nettoyer les résultats OCR
cleaned_results = [(bbox, clean_text(text)) for bbox, text in [(r[0], r[1]) for r in results]]

# 2. Grouper tous les textes dans un bloc
all_text = ' '.join([text for _, text in cleaned_results])
print('\n[DEBUG] Texte global OCR nettoyé :', all_text)

# 3. Trouver les lignes correspondantes aux champs
structured_data = []

for field in fields:
    pattern = rf'({field})\s*[:\-]?\s*([0-9]+[.,]?[0-9]*)\s*([a-zA-Z/%°\'’\.]*)'
    matches = re.findall(pattern, all_text, re.IGNORECASE)
    
    if matches:
        for match in matches:
            name, value, unit = match
            structured_data.append({
                'champ': name.strip(),
                'valeur': value.replace(',', '.'),
                'unité': unit.strip()
            })

print('\n[INFO] Structuration des données...')
print('[INFO] Données structurées :', structured_data)

# 4. Interpréter les résultats avec des intervalles normaux fictifs
normal_ranges = {
    'Hématies': (4.2, 5.7),
    'Hémoglobine': (12, 16),
    'Hématocrite': (36, 46),
    'VGM': (80, 95),
    'CCMH': (30, 35),
    'TCMH': (27, 32),
    'Leucocytes': (4000, 10000),
    'Polynucléaires Neutrophiles': (1800, 7000),
    'Polynucléaires Eosinophiles': (0, 500),
    'Polynucléaires Basophiles': (0, 50),
    'Lymphocytes': (1500, 4000),
    'Monocytes': (100, 1200),
    'Plaquettes': (150000, 450000),
}

interpreted_data = []

for data in structured_data:
    champ = data['champ']
    try:
        val = float(data['valeur'])
        if champ in normal_ranges:
            low, high = normal_ranges[champ]
            etat = 'Normal' if low <= val <= high else 'Anormal'
        else:
            etat = 'Intervalle inconnu'
    except ValueError:
        etat = 'Valeur non numérique'
    
    data['état'] = etat
    interpreted_data.append(data)

print('[INFO] Données interprétées :', interpreted_data)

# Temps d'exécution
print('[INFO] Temps de traitement :', time.time() - start_time, 'sec')
