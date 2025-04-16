from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from PIL import Image, ExifTags
import numpy as np
import cv2
import easyocr
import io

app = FastAPI()
reader = easyocr.Reader(['en', 'fr'])  # Add/remove languages as needed

def correct_orientation(image: Image.Image) -> Image.Image:
    """
    Detect and fix orientation of the image using EXIF data.
    """
    try:
        exif = image._getexif()
        if exif is not None:
            for tag, value in exif.items():
                decoded = ExifTags.TAGS.get(tag, tag)
                if decoded == "Orientation":
                    orientation = value

                    if orientation == 3:
                        print("[i] Rotating 180°")
                        return image.rotate(180, expand=True)
                    elif orientation == 6:
                        print("[i] Rotating 270° (90° CW)")
                        return image.rotate(270, expand=True)
                    elif orientation == 8:
                        print("[i] Rotating 90° (270° CW)")
                        return image.rotate(90, expand=True)
        else:
            print("[i] No EXIF orientation data found.")

    except Exception as e:
        print(f"[!] Error checking orientation: {e}")

    return image  # Return original if no rotation needed

def preprocess_image(image: Image.Image, text_type: str = "printed") -> Image.Image:
    try:
        img = np.array(image.convert('L'))

        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        img = clahe.apply(img)

        scale_factor = 3 if img.shape[0] < 1000 else 2
        img = cv2.resize(img, (img.shape[1] * scale_factor, img.shape[0] * scale_factor), interpolation=cv2.INTER_CUBIC)

        if text_type.lower() == "printed":
            _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        elif text_type.lower() == "handwritten":
            img = cv2.bilateralFilter(img, 9, 75, 75)
            img = cv2.medianBlur(img, 5)
            img = cv2.equalizeHist(img)
            img = cv2.adaptiveThreshold(
                img, 255,
                cv2.ADAPTIVE_THRESH_MEAN_C,
                cv2.THRESH_BINARY_INV,
                31, 15
            )

        return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_GRAY2RGB))

    except Exception as e:
        print(f"[!] Preprocessing error: {str(e)}")
        return image


@app.post("/ocr")
async def perform_ocr(
    file: UploadFile = File(...),
    text_type: str = Form("printed")
):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")

        # Step 1: Fix orientation using EXIF
        image = correct_orientation(image)

        # Step 2: Preprocess image
        processed_image = preprocess_image(image, text_type=text_type)

        # Step 3: OCR
        results = reader.readtext(np.array(processed_image))

        extracted = [
            {
                "text": text,
                "confidence": float(confidence),
                "bbox": bbox
            }
            for bbox, text, confidence in results
        ]

        return JSONResponse(content={"text_blocks": extracted})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
