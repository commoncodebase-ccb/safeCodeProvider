from django.shortcuts import render
from django.http import JsonResponse
import json
import os
from django.conf import settings
import csv
import shutil

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

def save_uploaded_file(uploaded_file, file_type):
    save_path = os.path.join(settings.MEDIA_ROOT, file_type)
    os.makedirs(save_path, exist_ok=True)
    file_path = os.path.join(save_path, uploaded_file.name)
    with open(file_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
    return uploaded_file.name

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
            student_list = request.FILES.get("student_list")
            exam_instruction = request.FILES.get("exam_instruction")
            assignment_file = request.FILES.get("assignment_file")

            if not exam_name or not exam_time or not exam_password:
                return JsonResponse({"error": "Eksik sınav bilgisi gönderildi."}, status=400)
            
            if not student_list or not exam_instruction or not assignment_file:
                return JsonResponse({"error": "Tüm dosyalar yüklenmelidir!"}, status=400)

            student_list_name = save_uploaded_file(student_list, "student_list")
            exam_instruction_name = save_uploaded_file(exam_instruction, "exam_instruction")
            assignment_file_name = save_uploaded_file(assignment_file, "assignment_file")

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
                    file_name, file_extension = os.path.splitext(os.path.basename(latest_file))
                    file_type = file_extension.lstrip(".") if file_extension else "unknown"

            exam_data.update({
                "exam_name": exam_name,
                "exam_time": exam_time,
                "exam_password": exam_password,
                "file_name": file_name,  # Dosya adı
                "type": file_type,  # Dosya uzantısı
                "student_list": student_list_name,
                "exam_instruction": exam_instruction_name,
                "assignment_file": assignment_file_name
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
        file_name = config.get("file_name", "script").lower()

        # 📌 2. Dockerfile seçimi
        dockerfile_map = {
            "py": "docker/python.Dockerfile",
            "java": "docker/java.Dockerfile",
            "c": "docker/c.Dockerfile"
        }
        dockerfile_path = os.path.join(os.getcwd(),dockerfile_map.get(exam_type))

        if not dockerfile_path or not os.path.exists(dockerfile_path):
            return JsonResponse({"error": f"Unsupported or missing Dockerfile for exam type: {exam_type}"}, status=400)

        # CSV dosyasının olduğu klasör
        csv_dir = "media/student_list"
        csv_files = os.listdir(csv_dir)

        if not csv_files:
            return JsonResponse({"error": "No CSV file found in student_list folder"}, status=400)
        
        csv_file_path = os.path.join(csv_dir, csv_files[0])

        # script dosyasının olduğu klasör
        script_dir = "media/assignment_file"
        script_files = os.listdir(script_dir)
        if not script_files:
            return JsonResponse({"error": "No assignment file found in assignment_file folder"}, status=400)
        
        script_file_path = os.path.join(script_dir, script_files[0])

        # "uploads" klasörü yoksa oluştur
        uploads_dir = "uploads"
        os.makedirs(uploads_dir, exist_ok=True)

        # CSV dosyasını oku ve öğrenci ID_İsim formatında listeye al
        students = []
        with open(csv_file_path, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) >= 2:
                    student_id = row[0]
                    student_name = row[1].strip().lower().replace(" ", "-")
                    container_name = f"{student_id}-{student_name}-container"
                    folder_name = f"{student_id}_{student_name}"
                    students.append(folder_name)

        # Öğrenci klasörlerini oluştur ve dosyaları kopyala
        for student in students:
            folder_path = os.path.join(uploads_dir, student)#uploads/ID_name
            os.makedirs(folder_path, exist_ok=True)
            
            with open(dockerfile_path, "r") as file:
                dockerfile_lines = file.readlines()

             # CMD komutunu öğrenciye özel hale getir
            if exam_type == "py":
                cmd_line = f'CMD ["/bin/sh", "-c", "python {file_name}.py"]\n'
            elif exam_type == "java":
                cmd_line = f'CMD ["/bin/sh", "-c", "javac {file_name}.java && java -cp . {file_name}"]\n'
            elif exam_type == "c":
                cmd_line = f'CMD ["/bin/sh", "-c", "gcc -o {file_name} {file_name}.c && ./{file_name}"]\n'
            else:
                return JsonResponse({"error": f"Unsupported file type: {exam_type}"}, status=400)


            # Son satırı özel CMD ile değiştir
            dockerfile_lines[-1] = cmd_line
            
            student_dockerfile_path = os.path.join(folder_path, "Dockerfile")
            with open(student_dockerfile_path, "w") as file:
                file.writelines(dockerfile_lines)

            shutil.copy(script_file_path, os.path.join(folder_path, os.path.basename(script_file_path)))

        # Docker image'leri oluştur
        for student in students:
            safe_student_name = student.replace("_", "-")
            os.system(f"docker build -t {safe_student_name} {os.path.join(uploads_dir, student)}")

        # Docker container'ları çalıştır
        for student in students:
            safe_student_name = student.replace("_", "-")
            os.system(f"docker run --name {safe_student_name}-container {safe_student_name}")


        return JsonResponse({"message": "Docker işlemleri başarıyla tamamlandı!"})
    
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