from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from .services.ocr_service import OcrService

def upload_image(request):
    if request.method == "POST" and request.FILES["image"]:
        # Récupérer l'image téléchargée
        image = request.FILES["image"]
        fs = FileSystemStorage(location='static/images')
        filename = fs.save(image.name, image)
        image_url = fs.url(filename)
        
        # Analyser l'image avec le service OCR
        ocr_service = OcrService(f'static/images/{filename}')
        result = ocr_service.analyse()

        return JsonResponse(result, safe=False)
    return render(request, "upload_image.html")
