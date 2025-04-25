import easyocr
import time
import re
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Initialisation de l'OCR
reader = easyocr.Reader(['fr'])

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

# Route pour l'interface utilisateur (servir le HTML)
@app.route('/')
def index():
    return render_template('index.html')

# Route pour analyser l'image et extraire les données
@app.route('/api/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    
    # Enregistrer l'image dans un fichier temporaire
    image_path = 'analyse1.jpg'
    file.save(image_path)
    
    # Démarrer le chronomètre
    start_time = time.time()
    
    # Lire le texte de l'image
    results = reader.readtext(image_path)

    # Nettoyer les résultats OCR
    cleaned_results = [(bbox, clean_text(text)) for bbox, text in [(r[0], r[1]) for r in results]] 
    all_text = ' '.join([text for _, text in cleaned_results])
    
    # Trouver les lignes correspondantes aux champs de santé
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

    # Interpréter les résultats avec des intervalles normaux fictifs
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
    
    # Calcul du temps de traitement
    processing_time = time.time() - start_time
    
    return jsonify({
        "parameters": interpreted_data,
        "processing_time": processing_time
    })

if __name__ == '__main__':
    app.run(debug=True)
