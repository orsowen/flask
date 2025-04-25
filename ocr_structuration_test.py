import easyocr
import re
import time
import numpy as np
from PIL import Image

class OcrService:
    def __init__(self, image_pil):
        self.image_np = np.array(image_pil)  # Convertir PIL en numpy array
        self.reader = easyocr.Reader(['fr'], gpu=False)  # Initialiser l'OCR avec la langue française
        self.fields = [
            'Hématies', 'Hémoglobine', 'Hématocrite', 'VGM', 'CCMH', 'TCMH', 'Leucocytes',
            'Polynucléaires Neutrophiles', 'Polynucléaires Eosinophiles',
            'Polynucléaires Basophiles', 'Lymphocytes', 'Monocytes', 'Plaquettes'
        ]
        # Plages normales pour chaque paramètre dans les analyses médicales
        self.normal_ranges = {
            'Hématies': (4.2, 5.7), 'Hémoglobine': (12, 16), 'Hématocrite': (36, 46),
            'VGM': (80, 95), 'CCMH': (30, 35), 'TCMH': (27, 32), 'Leucocytes': (4000, 10000),
            'Polynucléaires Neutrophiles': (1800, 7000), 'Polynucléaires Eosinophiles': (0, 500),
            'Polynucléaires Basophiles': (0, 50), 'Lymphocytes': (1500, 4000),
            'Monocytes': (100, 1200), 'Plaquettes': (150000, 450000),
        }

    # Fonction pour nettoyer le texte (retirer les caractères non désirés)
    def clean_text(self, text):
        text = text.replace('\n', ' ')  # Remplacer les retours à la ligne par des espaces
        text = re.sub(r'[^a-zA-ZÀ-ÿ0-9%\.\-,/\'\s]', '', text)  # Enlever les caractères spéciaux
        return text.strip()

    # Fonction pour analyser l'image et extraire les données OCR
    def analyse(self):
        start_time = time.time()  # Démarrer le chronomètre pour mesurer la durée de l'analyse

        # Lire le texte à partir de l'image
        results = self.reader.readtext(self.image_np)

        # Afficher les résultats OCR pour débogage
        print("[DEBUG] Résultats OCR bruts :")
        for bbox, text in results:
            print(f"Texte OCR brut détecté : {text}")

        # Nettoyer les résultats OCR
        cleaned_results = [(r[0], self.clean_text(r[1])) for r in results]
        all_text = ' '.join([text for _, text in cleaned_results])

        print("\n[INFO] Texte complet nettoyé de l'OCR :")
        print(all_text)

        # Structurer les données extraites avec les champs médicaux
        structured_data = []
        for field in self.fields:
            pattern = rf'({field})\s*[:\-]?\s*([0-9]+[.,]?[0-9]*)\s*([a-zA-Z/%°\'’\.]*)'  # Regex pour extraire les valeurs
            matches = re.findall(pattern, all_text, re.IGNORECASE)  # Chercher les correspondances
            if matches:
                for match in matches:
                    name, value, unit = match
                    structured_data.append({
                        'champ': name.strip(),
                        'valeur': value.replace(',', '.'),  # Remplacer les virgules par des points dans les valeurs
                        'unité': unit.strip()  # Nettoyer l'unité
                    })

        # Interpréter les données en fonction des plages normales
        interpreted_data = []
        for data in structured_data:
            champ = data['champ']
            try:
                val = float(data['valeur'])  # Convertir la valeur en flottant
                if champ in self.normal_ranges:
                    low, high = self.normal_ranges[champ]  # Plages normales pour chaque champ
                    etat = 'Normal' if low <= val <= high else 'Anormal'  # Vérifier si la valeur est dans l'intervalle normal
                else:
                    etat = 'Intervalle inconnu'  # Si la plage est inconnue
            except ValueError:
                etat = 'Valeur non numérique'  # Si la valeur n'est pas numérique

            data['état'] = etat  # Ajouter l'état à la donnée
            interpreted_data.append(data)

        # Retourner les résultats
        return {
            'résultats': interpreted_data,  # Résultats avec les états des données
            'temps': round(time.time() - start_time, 2)  # Temps de traitement de l'image
        }
