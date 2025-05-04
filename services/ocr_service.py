import easyocr
import re
import time
import numpy as np

class OcrService:

    def __init__(self, image_pil):
        self.image_np = np.array(image_pil)  
        self.reader = easyocr.Reader(['fr'], gpu=False)
        self.fields = [
            'Hématies', 'Hémoglobine', 'Hématocrite', 'VGM', 'CCMH', 'TCMH', 'Leucocytes',
            'Polynucléaires Neutrophiles', 'Polynucléaires Eosinophiles',
            'Polynucléaires Basophiles', 'Lymphocytes', 'Monocytes', 'Plaquettes'
        ]
        # Plages normales pour chaque paramètre
        self.normal_ranges = {
            'Hématies': (4, 5.5), 'Hémoglobine': (12, 16), 'Hématocrite': (36, 46),
            'VGM': (80, 95), 'CCMH': (30, 35), 'TCMH': (27, 32), 'Leucocytes': (4000, 10000),
            'Polynucléaires Neutrophiles': (1800, 7000), 'Polynucléaires Eosinophiles': (0, 500),
            'Polynucléaires Basophiles': (0, 50), 'Lymphocytes': (1500, 4000),
            'Monocytes': (100, 1200), 'Plaquettes': (150000, 450000),
        }
        self.champs_avec_soit = {
            'Polynucléaires Neutrophiles',
            'Polynucléaires Eosinophiles',
            'Polynucléaires Basophiles',
            'Lymphocytes',
            'Monocytes'
        }


    def clean_text(self, text):
        text = text.replace('\n', ' ')
        text = re.sub(r'[^a-zA-ZÀ-ÿ0-9%\.\-,/\'\s]', '', text)
        return text.strip()

    def analyse(self):
        start_time = time.time()
        results = self.reader.readtext(self.image_np)

        cleaned_results = [(bbox, self.clean_text(text)) for bbox, text in [(r[0], r[1]) for r in results]]
        all_text = ' '.join([text for _, text in cleaned_results])

        structured_data = []
        for field in self.fields:
            pattern = rf'({field})\.?\s*[:\-]?\s*([\d\s]+[.,]?\d*)\s*([a-zA-Z/%°\'’\.]*)'
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    name, value, unit = match
                    unit = unit.replace('f1', 'fl').replace('gdl', 'g/dL')
                    value = value.replace(' ', '').replace(',', '.')
                    structured_data.append({
                        'champ': name.strip(),
                        'valeur': value,
                        'unité': unit.strip()
                    })

       

        interpreted_data = []
        for data in structured_data:
            champ = data['champ']
            valeur_finale = data['valeur']

         
            if champ in  self.champs_avec_soit:
                pattern_soit = rf"{re.escape(champ)}.*?Soit\s*[:=]?\s*([\d\s]+)"
                match_soit = re.search(pattern_soit, all_text, re.IGNORECASE)
                if match_soit:
                    valeur_extraite = match_soit.group(1).replace(" ", "")
                    if valeur_extraite.isdigit():  
                        valeur_finale = valeur_extraite
                        print(f"[DEBUG] Champ '{champ}' → Valeur absolue extraite après 'Soit :' : {valeur_finale}")

            try:
                val = float(valeur_finale.replace(",", "."))
                if champ in self.normal_ranges:
                    low, high = self.normal_ranges[champ]
                    etat = 'Normal' if low <= val <= high else 'Anormal'
                    data['référence'] = f"{low} - {high}"
                else:
                    etat = 'Intervalle inconnu'
                    data['référence'] = 'N/A'
            except ValueError:
                etat = 'Valeur non numérique'
                data['référence'] = 'Erreur'

            data['état'] = etat
            interpreted_data.append(data)


        print({
            'result avant clean': all_text,
            'résultats': interpreted_data,
            'temps': round(time.time() - start_time, 2)
        })
        return {
            'result avant clean': all_text,
            'résultats': interpreted_data,
            'temps': round(time.time() - start_time, 2)
        }
