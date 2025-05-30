from flask import Flask, request, jsonify, render_template
from services.ocr_service import OcrService
from utils import utils  
from PIL import Image
import io

app = Flask(__name__)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    # Vérification si un fichier est présent dans la requête
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier reçu'}), 400
    
    file = request.files['file']
    # Vérification si le fichier a un nom
    if file.filename == '':
        return jsonify({'error': 'Fichier invalide'}), 400

    try:
        # Ouvrir l'image à partir du flux de la requête
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes))

        # Correction et prétraitement de l'image
        corrected_image = utils.auto_correct_orientation(image)
        # processed_image = utils.preprocess_medical_image(corrected_image)
        # processed_image.show()

        # Lancer l’analyse OCR
        analyser = OcrService(corrected_image)
        result = analyser.analyse()
        print(result) 

        # Retourner la réponse JSON avec le temps de traitement et les résultats des paramètres
        return jsonify({
            'Edite_date':result['edite_le_date'],
            'processing_time': result['temps'],
            'tables': result['tables'],
            'patient_info': result.get('person_info', {}),
            'status': 'success'
        })

    except Exception as e:
        # Gestion des erreurs
        return jsonify({'error': f'Erreur durant le traitement : {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
