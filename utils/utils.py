from PIL import Image, ExifTags
import numpy as np
import cv2

# Fonction pour corriger l'orientation d'une image en fonction des métadonnées EXIF
def correct_image_orientation(image: Image.Image) -> Image.Image:
    try:
        if hasattr(image, '_getexif'):
            exif = image._getexif()
            if exif:
                orientation = exif.get(274)
                if orientation == 3:
                    return image.rotate(180, expand=True)
                elif orientation == 6:
                    return image.rotate(270, expand=True)
                elif orientation == 8:
                    return image.rotate(90, expand=True)
    except Exception:
        pass
    return image

# Fonction pour prétraiter une image médicale (grayscale, CLAHE, filtre bilatéral, etc.)
def preprocess_medical_image(image: Image.Image) -> Image.Image:
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
    return Image.fromarray(img)
