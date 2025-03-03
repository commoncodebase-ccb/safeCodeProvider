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
        try:
            exam_name = request.POST.get("exam_name")
            exam_time = request.POST.get("time")
            exam_password = request.POST.get("exam_password")

            if not exam_name or not exam_time or not exam_password:
                return JsonResponse({"error": "Eksik sınav bilgisi gönderildi."}, status=400)

            config_path = "config.json"

            exam_data = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as file:
                    try:
                        exam_data = json.load(file)
                    except json.JSONDecodeError:
                        exam_data = {}

            assignment_folder = "media/assignment_file"
            file_type = "unknown"

            if os.path.exists(assignment_folder):
                files = os.listdir(assignment_folder)
                if files:
                    latest_file = max(
                        [os.path.join(assignment_folder, f) for f in files],
                        key=os.path.getctime
                    )
                    file_extension = os.path.splitext(latest_file)[1].lstrip(".")
                    file_type = file_extension if file_extension else "unknown"

            exam_data.update({
                "exam_name": exam_name,
                "exam_time": exam_time,
                "exam_password": exam_password,
                "type": file_type
            })

            with open(config_path, "w", encoding="utf-8") as file:
                json.dump(exam_data, file, indent=4, ensure_ascii=False)

            return handle_docker_operations(config_path, request)

        except Exception as e:
            return JsonResponse({"error": f"Sunucu hatası: {str(e)}"}, status=500)



def handle_docker_operations(config_path, request):
    try:
        # 📌 1. config.json dosyasını oku
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)

        exam_type = config.get("type", "py").lower()
        exam_name = config.get("exam_name", "default_exam")

        # 📌 2. Dockerfile seçimi
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
            return JsonResponse({"error": f"Could not fint Dockerfile: {selected_dockerfile}"}, status=500)

        # 📌 3. Docker Image oluştur
        image_name = f"safe_code_{exam_type}_image"
        client = docker.from_env()

        try:
            client.images.build(path=os.path.join(os.getcwd(), "docker"), dockerfile=selected_dockerfile, tag=image_name)# building image
        except Exception as e:
            return JsonResponse({"error": f"Creating image is unsuccessful: {str(e)}"}, status=500)
        #creating container for all students in student list
        return JsonResponse({"message": "Exam is started successfully", "containers": container_names})

    except Exception as e:
        return JsonResponse({"error": f"Docker işlemleri sırasında hata oluştu: {str(e)}"}, status=500)


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