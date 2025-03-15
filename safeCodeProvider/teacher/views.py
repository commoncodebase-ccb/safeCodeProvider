from django.shortcuts import render
from django.http import JsonResponse
import json
import os
from django.conf import settings
import csv
import shutil
import ctypes
import sys
import platform

from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

UPLOADS_DIR = "uploads"

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

def convert_csv_to_json(csv_filename):
    # CSV dosyasının tam yolunu oluştur
    csv_path = os.path.join(settings.MEDIA_ROOT, "student_list", csv_filename)

    # JSON dosyasının tam yolunu oluştur (Projenin kök dizini)
    json_path = os.path.join(settings.BASE_DIR, "students.json")

    students_data = []

    # CSV dosyasını oku
    with open(csv_path, mode="r", encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file)  # Sadece virgülle ayrılmış verileri okuyoruz
        for row in csv_reader:
            if len(row) == 2:  # Her satırda iki veri olduğundan emin ol
                student_id, _ = row  # Sadece id'yi al, ismi kullanmıyoruz
                students_data.append({"id": student_id, "isLogged": "false"})

    # JSON dosyasına yaz
    with open(json_path, mode="w", encoding="utf-8") as json_file:
        json.dump(students_data, json_file, indent=4, ensure_ascii=False)

    return json_path

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

            convert_csv_to_json(student_list_name)
            
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

def bring_code(request):
    try:
        body = json.loads(request.body)

        student_id = body.get("student_id")
        student_name = body.get('student_name').lower()

        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            config = json.load(file)

        file_name = config.get("file_name", "script").lower()
        exam_type = config.get("type", "py").lower()
        file_name += f".{exam_type}"

        folder_name = f"{student_id}_{student_name}"
        student_folder = os.path.join(UPLOADS_DIR, folder_name)#uploads/220717005_emre

        if not os.path.exists(student_folder):
            return JsonResponse({'status': 'error', 'message': 'Student folder not found'})
        
        # Öğrencinin kod dosyası yolunu oluştur
        code_file_path = os.path.join(student_folder, file_name)

        if not os.path.exists(code_file_path):
            return JsonResponse({'status': 'error', 'message': 'Code file not found'})
        
        with open(code_file_path, "r", encoding="utf-8") as file:
            code_content = file.read()

        return JsonResponse({
            "success": True,
            "content": code_content,
            "exam_type": exam_type
        })
    except Exception as e:
        return JsonResponse({"error": f"kod dondurulurken bir hata olustu: {str(e)}"})
    

@csrf_exempt
def open_student_port(request):
    print("Pathhhhh   " + os.getcwd())
    if request.method == "POST":
        try:
            # Kullanıcının ana dizinini al (Örneğin: /home/kullanici veya C:\Users\mazlu)
            home_dir = os.path.expanduser("~")

            # SafeCodeProvider'ın tam yolu
            project_path = os.getcwd()

            print("Pathhhhh   " + project_path)

            # İşletim sistemini tespit et
            system_type = platform.system()

            if system_type == "Windows":
                # Windows için yeni terminal açıp Django sunucusunu başlat
                os.system(f'start cmd /k "cd /d {project_path} && py manage.py runserver 8001 --settings=safeCodeProvider.settings.student_settings"')

            
            elif system_type == "Darwin":  # macOS
                # For macOS, use the `open` command to launch Terminal
                os.system(f'open -a Terminal "{project_path}" && python3 manage.py runserver 8001 --settings=safeCodeProvider.settings.student_settings')

            elif system_type == "Linux":
                # For Linux, use xterm or another terminal emulator
                os.system(f'xterm -e "cd {project_path} && python3 manage.py runserver 8001 --settings=safeCodeProvider.settings.student_settings"')

            else:
                return JsonResponse({"error": "Bilinmeyen işletim sistemi"}, status=500)

            # Config.json dosyasından "exam_time" değerini oku
            exam_time = 0  # Varsayılan değer
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    exam_time = config.get("exam_time", 0)

            return JsonResponse({"message": "✅ 8001 portu açıldı!", "exam_time": exam_time}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e) , "path": os.getcwd()}, status=500)

    return JsonResponse({"error": "Invalid request", "path": os.getcwd()}, status=400)


# Yönetici yetkisi olup olmadığını kontrol et
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


@csrf_exempt
def close_student_port(request):
    if request.method == "POST":
        try:
            # Linux/macOS için iptables komutu
            #os.system("sudo iptables -A INPUT -p tcp --dport 8001 -j DROP")
            
            # `close_port.py` dosyasını çalıştır
            
            os.system("start cmd /k py close_port.py")
            return JsonResponse({"message": "8001 portu kapatıldı!"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)
