from PIL import Image, ExifTags
import numpy as np
import cv2
import pytesseract

# Fonction pour corriger l'orientation d'une image en fonction des métadonnées EXIF
def auto_correct_orientation(image: Image.Image) -> Image.Image:
    try:
        # Utilise Tesseract pour détecter l'orientation
        osd = pytesseract.image_to_osd(image)
        print("OSD result:", osd)

        rotation = int([line for line in osd.split('\n') if "Rotate:" in line][0].split(':')[1].strip())
        print("Detected rotation:", rotation)

        if rotation == 90:
            return image.rotate(-90, expand=True)
        elif rotation == 180:
            return image.rotate(-180, expand=True)
        elif rotation == 270:
            return image.rotate(-270, expand=True)
        else:
            return image  # Pas de rotation nécessaire

    except Exception as e:
        print(f"Erreur dans l'auto-correction de l'orientation : {e}")
        return image


    

# Fonction pour prétraiter une image médicale (grayscale, CLAHE, filtre bilatéral, etc.)
def preprocess_medical_image(image: Image.Image) -> Image.Image:
    # image.show(title="Original Image after ")
    img = np.array(image.convert('L'))  # Convertir l'image en niveaux de gris
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(16, 16))  # Appliquer CLAHE pour améliorer le contraste
    img = clahe.apply(img)
    img = cv2.bilateralFilter(img, 9, 75, 75)  # Appliquer un filtre bilatéral pour réduire le bruit
    img = cv2.adaptiveThreshold(
        img, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        21, 10
    )
    # Image.fromarray(img).show(title="Adaptive Threshold") 

    return Image.fromarray(img)
