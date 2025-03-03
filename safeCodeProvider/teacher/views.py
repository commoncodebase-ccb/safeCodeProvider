from django.shortcuts import render
from django.http import JsonResponse
import json
import os
from django.conf import settings
import csv


import docker
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

CONFIG_FILE = os.path.join(settings.BASE_DIR, 'config.json')

ALLOWED_EXTENSIONS = {
    'student_list': ['csv'],
    'exam_instruction': ['pdf'],
    'assignment_file': ['py', 'java', 'c']
}

def teacher_home(request):
    return render(request, 'teacher_home.html')

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

@csrf_exempt
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

        
        # 1. config.json dosyasını oku
        config_path = os.path.join(os.getcwd(), "config.json")
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)

        exam_type = config.get("type", "py").lower()  # Varsayılan Python
        exam_name = config.get("exam_name", "default_exam")
        
        # 2. Dockerfile seçimi
        dockerfile_map = {
            "py": "python.Dockerfile",
            "java": "java.Dockerfile",
            "c": "c.Dockerfile"
        }
        
        selected_dockerfile = dockerfile_map.get(exam_type)
        if not selected_dockerfile:
            return JsonResponse({"error": f"Unsupported exam type: {exam_type}"}, status=400)
        
        dockerfile_path = os.path.join(os.getcwd(), "docker", selected_dockerfile)
        if not os.path.exists(dockerfile_path):
            return JsonResponse({"error": f"Dockerfile not found: {selected_dockerfile}"}, status=500)

        # 3. Docker Image oluştur
        image_name = f"safe_code_{exam_type}_image"
        client = docker.from_env()
        
        try:
            client.images.build(path=os.path.join(os.getcwd(), "docker"), dockerfile=selected_dockerfile, tag=image_name)
        except Exception as e:
            return JsonResponse({"error": f"Image build failed: {str(e)}"}, status=500)

        # 4. Öğrenci listesini oku
        student_list_file = request.FILES.get("student_list")
        if not student_list_file:
            return JsonResponse({"error": "No student list provided"}, status=400)
        
        file_path = os.path.join(os.getcwd(), "media", "student_list", "students.csv")


        student_ids = []
        try:
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if row:
                        student_ids.append(row[0].strip())  # CSV'deki ilk sütun öğrenci ID'si
        except Exception as e:
            return JsonResponse({"error": f"Failed to read student list: {str(e)}"}, status=500)

        # 5. Öğrenciler için container oluştur
        container_names = []
        for student_id in student_ids:
            container_name = f"{exam_name}_student_{student_id}"

            try:
                container = client.containers.run(
                    image_name,
                    detach=True,
                    name=container_name
                )
                container_names.append(container_name)
            except Exception as e:
                return JsonResponse({"error": f"Container creation failed for {student_id}: {str(e)}"}, status=500)

        return JsonResponse({"message": "Containers created successfully", "containers": container_names})

    return JsonResponse({"error": "Geçersiz istek!"}, status=400)

def submits_page(request):
    # config.json dosyasını oku
    config_path = os.path.join(settings.BASE_DIR, "config.json")
    with open(config_path, "r", encoding="utf-8") as config_file:
        config_data = json.load(config_file)
    exam_password = config_data.get("exam_password", "Not Found")

    # student_list klasöründeki ilk .csv dosyasını bul
    student_list_path = os.path.join(settings.MEDIA_ROOT, "student_list")
    student_file = next((f for f in os.listdir(student_list_path) if f.endswith(".csv")), None)

    students = []
    if student_file:
        csv_path = os.path.join(student_list_path, student_file)
        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) == 2:  # Beklenen format: "id, name"
                    students.append({"id": row[0], "name": row[1]})

    return render(request, "submits_page.html", {"exam_password": exam_password, "students": students})