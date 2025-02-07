from django.shortcuts import render

from django.shortcuts import render
from django.http import JsonResponse
import json
import os
from django.conf import settings

CONFIG_FILE = os.path.join(settings.BASE_DIR, 'config.json')

ALLOWED_EXTENSIONS = {
    'student_list': ['csv'],
    'exam_instruction': ['pdf'],
    'assignment_file': ['py', 'java', 'c']
}

def teacher_home(request):
    return render(request, 'teacher/teacher_home.html')

def upload_files(request):
    if request.method == 'POST':
        required_files = ['student_list', 'exam_instruction', 'assignment_file']
        uploaded_files = {}

        for file_type in required_files:
            uploaded_file = request.FILES.get(file_type)
            if not uploaded_file:
                return JsonResponse({'error': f'{file_type} dosyası eksik!'}, status=400)

            # **Dosya uzantısını kontrol et**
            allowed_extensions = ALLOWED_EXTENSIONS.get(file_type)
            if allowed_extensions:
                file_extension = uploaded_file.name.split('.')[-1].lower()
                if file_extension not in allowed_extensions:
                    return JsonResponse({'error': f'{file_type} sadece {", ".join(allowed_extensions)} formatında olmalıdır!'}, status=400)

            # **Dosyayı kaydet**
            save_path = os.path.join(settings.MEDIA_ROOT, file_type)
            os.makedirs(save_path, exist_ok=True)

            file_path = os.path.join(save_path, uploaded_file.name)
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            uploaded_files[file_type] = uploaded_file.name

        return JsonResponse({'message': f"Tüm dosyalar başarıyla yüklendi: {', '.join(uploaded_files.values())}"})

    return JsonResponse({'error': 'Geçersiz istek'}, status=400)

def start_exam(request):
    if request.method == "POST":
        exam_name = request.POST.get("exam_name")
        exam_time = request.POST.get("time")
        exam_password = request.POST.get("exam_password")  # Rastgele şifre

        # Sınav bilgilerini kaydedeceğimiz dosya
        config_path = "config.json"

        # Mevcut sınavları yükle
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as file:
                try:
                    exam_data = json.load(file)
                except json.JSONDecodeError:
                    exam_data = {}
        else:
            exam_data = {}



        assignment_folder = "media/assignment_file"
        file_type = "unknown"

        if os.path.exists(assignment_folder):
            files = os.listdir(assignment_folder)
            if files:  # Eğer klasörde dosya varsa
                latest_file = max(
                    [os.path.join(assignment_folder, f) for f in files],
                    key=os.path.getctime
                )  # En son yüklenen dosyayı al
                file_extension = os.path.splitext(latest_file)[1].lstrip(".")  # Uzantıyı al
                file_type = file_extension if file_extension else "unknown"


        # Yeni sınavı ekleyelim
        exam_data["exam_name"] = exam_name
        exam_data["exam_time"] = exam_time
        exam_data["exam_password"] = exam_password
        exam_data["type"] = file_type  # Dosya tipi eklendi


        # JSON dosyasına yazalım
        with open(config_path, "w", encoding="utf-8") as file:
            json.dump(exam_data, file, indent=4, ensure_ascii=False)

        return JsonResponse({"message": "Sınav başarıyla oluşturuldu!", "exam_password": exam_password})

    return JsonResponse({"error": "Geçersiz istek!"}, status=400)