import subprocess
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
    'assignment_files': ['py', 'java', 'c']
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
        uploaded_files = {}

        # Tekli dosyalar
        for file_type in ['student_list', 'exam_instruction']:
            uploaded_file = request.FILES.get(file_type)
            if not uploaded_file:
                return JsonResponse({'error': f'{file_type} Missing file!'}, status=400)

            allowed_extensions = ALLOWED_EXTENSIONS.get(file_type)
            file_extension = uploaded_file.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                return JsonResponse({'error': f'{file_type} sadece {", ".join(allowed_extensions)} formatında olmalıdır!'}, status=400)

            saved_name = save_uploaded_file(uploaded_file, file_type)
            uploaded_files[file_type] = saved_name

        # Çoklu assignment dosyaları
        assignment_files = request.FILES.getlist('assignment_files')
        if not assignment_files:
            return JsonResponse({'error': 'assignment_files Missing file(s)!'}, status=400)

        uploaded_files['assignment_files'] = []

        for uploaded_file in assignment_files:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            if file_extension not in ALLOWED_EXTENSIONS['assignment_files']:
                return JsonResponse({'error': f'assignment_files sadece {", ".join(ALLOWED_EXTENSIONS["assignment_files"])} formatında olmalıdır!'}, status=400)

            saved_name = save_uploaded_file(uploaded_file, 'assignment_files')
            uploaded_files['assignment_files'].append(saved_name)

        return JsonResponse({
            'message': 'All files uploaded successfully',
            'files': uploaded_files
        })

    return JsonResponse({'error': 'invalid request'}, status=400)

def convert_csv_to_json(csv_filename):
    # Generate full path to CSV file
    csv_path = os.path.join(settings.MEDIA_ROOT, "student_list", csv_filename)

    # Create full path of JSON file (Project root directory)
    json_path = os.path.join(settings.BASE_DIR, "students.json")

    students_data = []

    # read CSV file
    with open(csv_path, mode="r", encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file)  
        for row in csv_reader:
            if len(row) == 2: 
                student_id, _ = row 
                students_data.append({"id": student_id, "isLogged": "false"})

    # write JSON file
    with open(json_path, mode="w", encoding="utf-8") as json_file:
        json.dump(students_data, json_file, indent=4, ensure_ascii=False)

    return json_path

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def start_exam(request):
    if request.method == "POST":
        try:
            exam_name = request.POST.get("exam_name")
            exam_time = request.POST.get("time")
            exam_password = request.POST.get("exam_password")

            student_list = request.FILES.get("student_list")
            exam_instruction = request.FILES.get("exam_instruction")
            assignment_files = request.FILES.getlist("assignment_files")  # Çoklu dosya

            if not exam_name or not exam_time or not exam_password:
                return JsonResponse({"error": "Incomplete exam information was sent."}, status=400)

            if not student_list or not exam_instruction or not assignment_files:
                return JsonResponse({"error": "All files must be uploaded!"}, status=400)

            student_list_name = save_uploaded_file(student_list, "student_list")
            exam_instruction_name = save_uploaded_file(exam_instruction, "exam_instruction")

            assignment_file_names = []
            for file in assignment_files:
                saved_name = save_uploaded_file(file, "assignment_files")
                assignment_file_names.append(saved_name)

            convert_csv_to_json(student_list_name)

            config_path = "config.json"
            exam_data = {}

            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as file:
                    try:
                        exam_data = json.load(file)
                    except json.JSONDecodeError:
                        exam_data = {}

            # En son yüklenen dosyadan türünü bul (örn: py, java)
            file_type = "unknown"
            file_name = "unknown"
            if assignment_file_names:
                last_file = assignment_file_names[-1]
                file_name, file_extension = os.path.splitext(last_file)
                file_type = file_extension.lstrip(".")

            exam_data.update({
                "exam_name": exam_name,
                "exam_time": exam_time,
                "exam_password": exam_password,
                "file_name": file_name,
                "type": file_type,
                "student_list": student_list_name,
                "exam_instruction": exam_instruction_name,
                "assignment_files": assignment_file_names  # Liste halinde ekleniyor
            })

            with open(config_path, "w", encoding="utf-8") as file:
                json.dump(exam_data, file, indent=4, ensure_ascii=False)

            return handle_docker_operations(config_path, request)

        except Exception as e:
            return JsonResponse({"error": f"Sunucu hatası: {str(e)}"}, status=500)

    return JsonResponse({"error": "Geçersiz istek yöntemi"}, status=405)

def convert_to_ascii(text):
    turkish_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    return text.translate(turkish_map)

def handle_docker_operations(config_path, request):
    try:
        # Read config.json file
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)

        exam_type = config.get("type", "py").lower()
        file_name = config.get("file_name", "script").lower()

        # Choosing Dockerfile based on exam type
        dockerfile_map = {
            "py": "docker/python.Dockerfile",
            "java": "docker/java.Dockerfile",
            "c": "docker/c.Dockerfile"
        }

        dockerfile_path = os.path.join(os.getcwd(), dockerfile_map.get(exam_type))

        if not dockerfile_path or not os.path.exists(dockerfile_path):
            return JsonResponse({"error": f"Unsupported or missing Dockerfile for exam type: {exam_type}"}, status=400)

        csv_dir = "media/student_list"  # CSV file path
        csv_files = os.listdir(csv_dir)

        if not csv_files:
            return JsonResponse({"error": "No CSV file found in student_list folder"}, status=400)

        csv_file_path = os.path.join(csv_dir, csv_files[0])

        script_dir = "media/assignment_files"  # Assignment files directory
        script_files = os.listdir(script_dir)

        if not script_files:
            return JsonResponse({"error": "No assignment files found in assignment_file folder"}, status=400)

        # Creating "uploads" directory to hold student-specific files
        uploads_dir = "uploads"
        os.makedirs(uploads_dir, exist_ok=True)

        # Read CSV file and create a folder for each student
        students = []
        with open(csv_file_path, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) >= 2:
                    student_id = row[0]
                    student_name = row[1].strip().lower().replace(" ", "-")
                    student_name = convert_to_ascii(student_name)
                    container_name = f"{student_id}-{student_name}-container"
                    folder_name = f"{student_id}_{student_name}"
                    students.append(folder_name)

        # Create student folders and copy all assignment files
        for student in students:
            folder_path = os.path.join(uploads_dir, student)  # uploads/studentID_studentName
            os.makedirs(folder_path, exist_ok=True)

            # Read the Dockerfile and modify it for the student
            with open(dockerfile_path, "r") as file:
                dockerfile_lines = file.readlines()

            # Make CMD command student specific
            if exam_type == "py":
                cmd_line = f'CMD ["/bin/sh", "-c", "python {file_name}.py"]\n'
            elif exam_type == "java":
                cmd_line = f'CMD ["/bin/sh", "-c", "javac {file_name}.java && java -cp . {file_name}"]\n'
            elif exam_type == "c":
                cmd_line = f'CMD ["/bin/sh", "-c", "gcc -o {file_name} {file_name}.c && ./{file_name}"]\n'
            else:
                return JsonResponse({"error": f"Unsupported file type: {exam_type}"}, status=400)

            # Replace last line with custom CMD
            dockerfile_lines[-1] = cmd_line

            student_dockerfile_path = os.path.join(folder_path, "Dockerfile")  # uploads/studentID_studentName/Dockerfile
            with open(student_dockerfile_path, "w") as file:
                file.writelines(dockerfile_lines)

            # Copy all assignment files into the student folder
            for script_file in script_files:
                script_file_path = os.path.join(script_dir, script_file)
                shutil.copy(script_file_path, os.path.join(folder_path, script_file))

        # Create Docker images for each student
        for student in students:
            safe_student_name = student.replace("_", "-")
            os.system(f"docker build -t {safe_student_name} {os.path.join(uploads_dir, student)}")

        # Remove any pre-existing containers and run new containers
        for student in students:
            safe_student_name = student.replace("_", "-")
            container_name = f"{safe_student_name}-container"

            # Find the existing container
            result = subprocess.run(
                ["docker", "ps", "-a", "-q", "--filter", f"name={container_name}"],
                capture_output=True, encoding="utf-8", text=True
            )

            container_id = result.stdout.strip()  # If there is an ID, get it, otherwise it will be an empty string

            # If there is a container, remove it
            if container_id:
                subprocess.run(["docker", "rm", "-f", container_id])

            # Start a new container
            subprocess.run(["docker", "run", "-d", "--name", container_name, safe_student_name, "tail", "-f", "/dev/null"])

        # Execute the command inside the container
        for student in students:
            safe_student_name = student.replace("_", "-")

            if exam_type == "py":
                docker_exec_cmd = f"docker exec {safe_student_name}-container python /app/{file_name}.py"
            elif exam_type == "java":
                docker_exec_cmd = f"docker exec {safe_student_name}-container javac /app/{file_name}.java && docker exec {safe_student_name}-container java -cp /app {file_name}"
            elif exam_type == "c":
                docker_exec_cmd = f"docker exec {safe_student_name}-container gcc /app/{file_name}.c -o /app/{file_name} && docker exec {safe_student_name}-container /app/{file_name}"
            else:
                return JsonResponse({"error": f"Unsupported file type: {exam_type}"}, status=400)

            try:
                result = subprocess.run(
                    docker_exec_cmd,
                    shell=True,
                    capture_output=True,
                    text=True
                )

                # Check if the command was successful
                if result.returncode == 0:
                    print(result.stdout)  # This contains the output of the Python script
                else:
                    print(f"Error executing script in container for {safe_student_name}:")
                    print(result.stderr)  # This contains any error messages

            except Exception as e:
                print(f"An error occurred while executing the script for {safe_student_name}: {str(e)}")

        return JsonResponse({"message": "Docker işlemleri başarıyla tamamlandı!"})

    except Exception as e:
        return JsonResponse({"error": f"Docker işlemleri sırasında hata oluştu: {str(e)}"}, status=500)


def submits_page(request):
    # read config.json file
    config_path = os.path.join(settings.BASE_DIR, "config.json")
    with open(config_path, "r", encoding="utf-8") as config_file:
        config_data = json.load(config_file)
    exam_password = config_data.get("exam_password", "Not Found")

    # Find the first .csv file in the student_list folder
    student_list_path = os.path.join(settings.MEDIA_ROOT, "student_list")
    student_file = next((f for f in os.listdir(student_list_path) if f.endswith(".csv")), None)

    students = []
    if student_file:
        csv_path = os.path.join(student_list_path, student_file)
        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) == 2: # Expected format: "id, name"
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
        student_folder = os.path.join(UPLOADS_DIR, folder_name) #uploads/studentID_studentName

        if not os.path.exists(student_folder):
            return JsonResponse({'status': 'error', 'message': 'Student folder not found'})
        
        # Create student's code file path
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
        return JsonResponse({"error": f" An error occurred while returning the code: {str(e)}"})
    

@csrf_exempt
def open_student_port(request):
    print("Pathhhhh   " + os.getcwd())
    if request.method == "POST":
        try:
            # Get the user's home directory (For example: /home/user)
            home_dir = os.path.expanduser("~")

            # Full path to SafeCodeProvider
            project_path = os.getcwd()

            # Detect operating system
            system_type = platform.system()

            if system_type == "Windows":
                # Open a new terminal for Windows and start the Django server
                os.system(f'start cmd /k "cd /d {project_path} && py manage.py runserver 8001 --settings=safeCodeProvider.settings.student_settings"')

            
            elif system_type == "Darwin":  # macOS
                # For macOS, use the `open` command to launch Terminal
                os.system(f'open -a Terminal "{project_path}" && python3 manage.py runserver 8001 --settings=safeCodeProvider.settings.student_settings')

            elif system_type == "Linux":
                # For Linux, use xterm or another terminal emulator
                os.system(f'xterm -e "cd {project_path} && python3 manage.py runserver 8001 --settings=safeCodeProvider.settings.student_settings"')

            else:
                return JsonResponse({"error": "Bilinmeyen işletim sistemi"}, status=500)

            
            exam_time = 0 
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    exam_time = config.get("exam_time", 0)

            return JsonResponse({"message": "8001 port is opened!", "exam_time": exam_time}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e) , "path": os.getcwd()}, status=500)

    return JsonResponse({"error": "Invalid request", "path": os.getcwd()}, status=400)


# Check if you have administrator rights
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def remove_all_containers():
    try:
        # Get all container IDs
        result = subprocess.run(["docker", "ps", "-aq"], capture_output=True, text=True, check=True)
        container_ids = result.stdout.strip().split("\n")

        if container_ids and container_ids[0]:  # if the list is not empty
            print(f"Containers to be removed: {container_ids}")

            # Same Docker command for Windows and Linux/macOS
            subprocess.run(["docker", "rm", "-f"] + container_ids,encoding="utf-8", check=True)
            print("All containers removed successfully.")
        else:
            print("No containers found to remove.")

    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

@csrf_exempt
def close_student_port(request):
    if request.method == "POST":
        try:
            # First, stop and remove all Docker containers
            remove_all_containers()

            os.system("start cmd /k py close_port.py")
            return JsonResponse({"message": "8001 port is closed!"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)
