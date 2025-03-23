import csv  
import os  
import json
import subprocess  
from django.shortcuts import render 
from django.http import JsonResponse  
from django.conf import settings

UPLOADS_DIR = "uploads"

def student_control(request):
    if request.method == 'POST':  
        student_id = request.POST.get('student_id')
        student_name = request.POST.get('student_name') 
        exam_password = request.POST.get('exam_password') 

        config_path = os.path.join(settings.BASE_DIR, 'config.json') 
        try:
            with open(config_path, 'r') as config_file:  
                config_data = json.load(config_file)  
                correct_password = config_data.get('exam_password')  
        except FileNotFoundError:
            return JsonResponse({'status': 'error', 'message': 'Exam configuration not found'})  

        if exam_password != correct_password:  
            return JsonResponse({'status': 'error', 'message': 'Invalid exam password. Please try again.'})

        student_list_path = os.path.join(settings.MEDIA_ROOT, 'student_list')  
        try:
            files = os.listdir(student_list_path)
            if files:
                student_list_file = os.path.join(student_list_path, files[0])
            else:
                return JsonResponse({'status': 'error', 'message': 'Student list file not found'})  
        except FileNotFoundError:
            return JsonResponse({'status': 'error', 'message': 'Student list file not found'})  
 
        try:
            with open(student_list_file, 'r', encoding='utf-8') as csvfile:  
                reader = csv.reader(csvfile)  
                student_exists = any(
                    row[0] == student_id and row[1].lower() == student_name.lower() 
                    for row in reader
                )
        except FileNotFoundError:
            return JsonResponse({'status': 'error', 'message': 'Student list file not found'})  

        if not student_exists:  
            return JsonResponse({'status': 'error', 'message': 'Student not found in the list'})  

# JSON dosyasının tam yolunu belirle
        json_path = os.path.join(settings.BASE_DIR, "students.json")

        # JSON dosyasını oku
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as json_file:
                students_data = json.load(json_file)  # JSON verisini liste olarak al
        
           # Kullanıcının ID'sini kontrol et ve isLogged değerini güncelle
            user_found = False
            for student in students_data:
                if student["id"] == student_id:
                    if student["isLogged"] == "true":
                        return JsonResponse({
                            "status": "error",
                            "message": "You are already logged in and cannot enter the exam."
                        })
                    student["isLogged"] = "true"
                    user_found = True
                    break

            if user_found:
                # Güncellenmiş veriyi tekrar JSON dosyasına yaz
                with open(json_path, "w", encoding="utf-8") as json_file:
                    json.dump(students_data, json_file, indent=4, ensure_ascii=False)


            else:
                return JsonResponse({"status": "error", "message": "Student ID not found"})
            
        return JsonResponse({
        'status': 'success',
        'redirect_url': '/exam/',
        'student_id': student_id,
        'student_name': student_name
    })

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})  

def student_login(request):  
    return render(request, 'student_login.html')

def exam_page(request):
    config_path = os.path.join(settings.BASE_DIR, 'config.json')
    try:
        with open(config_path, 'r') as config_file:
            config_data = json.load(config_file)
            exam_time = int(config_data.get('exam_time', 10))  # Dakika cinsinden
            exam_type = config_data.get('exam_type', 'py')  # Örneğin "py", "java", "c"
    except FileNotFoundError:
        exam_time = 10
        exam_type = 'py'
    
    # exam_instruction klasöründen PDF dosyasını dinamik olarak bulalım (dosya adını sabit kodlamıyoruz)
    pdf_url = ''
    exam_instruction_folder = os.path.join(settings.MEDIA_ROOT, 'exam_instruction')
    if os.path.exists(exam_instruction_folder):
        pdf_files = [f for f in os.listdir(exam_instruction_folder) if f.lower().endswith('.pdf')]
        if pdf_files:
            pdf_url = settings.MEDIA_URL + 'exam_instruction/' + pdf_files[0]
    
    # assignment_file klasöründen dosya içeriğini dinamik olarak oku
    assignment_content = ''
    assignment_folder = os.path.join(settings.MEDIA_ROOT, 'assignment_file') 
    if os.path.exists(assignment_folder):
        assignment_files = [f for f in os.listdir(assignment_folder) if not f.startswith('.')]
        if assignment_files:
            file_path = os.path.join(assignment_folder, assignment_files[0])
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    assignment_content = f.read()
            except Exception as e:
                assignment_content = f"Dosya okunurken hata oluştu: {e}"
    
    return render(request, 'exam_page.html', {
        'exam_time': exam_time,
        'exam_type': exam_type,
        'pdf_url': pdf_url,
        'assignment_content': assignment_content,
    })

def save_code(request):
    try:
        # JSON verisini al
        body = json.loads(request.body)

        # JSON verisini kullanarak bilgileri al
        student_id = body.get('student_id')
        student_name = body.get('student_name').lower()
        code = body.get('code')

        # Konfigürasyon dosyasını aç
        config_path = "config.json"
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)

        file_name = config.get("file_name", "script").lower()
        exam_type = config.get("type", "py").lower()
        file_name += f".{exam_type}"

        # Öğrencinin dosya yolu
        folder_name = f"{student_id}_{student_name}"
        print("folder_name:", folder_name)
        student_folder = os.path.join(UPLOADS_DIR, folder_name)#uploads/220717005_emre
        print("student_folder:", student_folder)

        if not os.path.exists(student_folder):
            return JsonResponse({'status': 'error', 'message': 'Student folder not found'})
        
        # Öğrencinin kod dosyası yolunu oluştur
        code_file_path = os.path.join(student_folder, file_name)#uploads/220717005_emre/main.py
        print("code_file_path:", code_file_path)

        # Kod dosyasını yaz
        with open(code_file_path, "w") as f:
            f.write(code)
        
        return JsonResponse({'status': 'success', "message": "Code saved successfully!"})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def run_code(request):
    try:
        data = json.loads(request.body)
        student_id = data.get("student_id")
        student_name = data.get("student_name")

        if not student_id or not student_name:
            return JsonResponse({"status": "error", "message": "Incomplete information was sent."})

        container_name = f"{student_id}-{student_name.lower()}-container" #220717005-emre-container
        image_name = f"{student_id}-{student_name.lower()}" #220717005-emre

        config_path = "config.json"

        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)

        file_name = config.get("file_name", "script").lower()#main
        exam_type = config.get("type", "py").lower()#py
        file_name += f".{exam_type}"  #main.py

        folder_name = f"{student_id}_{student_name}"  #220717005_emre
        student_folder = os.path.abspath(os.path.join(UPLOADS_DIR, folder_name))


        # Mevcut container'ı kontrol et
        check_status_command = f"docker ps -a -f name={container_name} --format '{{{{.State}}}}'"
        container_status = os.popen(check_status_command).read().strip()

        # Eski container varsa kaldır
        #if container_status:
        #    os.system(f"docker rm -f {container_name}")

        #os.system(f"docker build -t {image_name} {student_folder}")

        # Yeni container oluştur ve kodu çalıştıru
        #run_command = f"docker run --rm --name {container_name} -v {student_folder}:/app/uploads {image_name} python3 /app/uploads/{file_name} 2>&1"
        code_file_path = os.path.join(student_folder, file_name)
        copy_command = f"docker cp {code_file_path} {container_name}:/app/{file_name}"
        os.system(copy_command)
        try:
                result = subprocess.run(
                    f"docker exec {container_name} python /app/{file_name}",
                    shell=True,
                    capture_output=True,
                    text=True
                )

                # Check if the command was successful
                if result.returncode == 0:
                  
                    return JsonResponse({"status": "success", "output": result.stdout})
                else:
                    print(f"Error executing script in container for {container_name}:")
                    print(result.stderr)  # This contains any error messages
                    return JsonResponse({"status": "error", "output": result.stderr})


        

        except Exception as e:
            print(f"An error occurred while executing the script for {container_name}: {str(e)}")
            return JsonResponse({"status": "error", "output": str(e)})

        #terminal_output = os.popen(run_command).read().strip()
        
       # if "Traceback" in terminal_output or "Error" in terminal_output or "Exception" in terminal_output:
        
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Geçersiz JSON formatı."})


def delete_docker(request):
    try:
        # JSON verisini al
        body = json.loads(request.body)

        # JSON verisini kullanarak bilgileri al
        student_id = body.get('student_id')
        student_name = body.get('student_name').lower()

        # Docker container ve image isimlerini oluştur
        container_name = f"{student_id}-{student_name}-container"
        image_name = f"{student_id}-{student_name}"

        # Önce container'ı durdur ve sil
        stop_container_command = f"docker stop {container_name} && docker rm {container_name}"
        delete_image_command = f"docker rmi -f {image_name}"

        print(f"Stopping and removing container: {container_name}")
        os.system(stop_container_command)  # Container'ı durdur ve sil
        print(f"Removing image: {image_name}")
        os.system(delete_image_command)  # Image'ı sil

        return JsonResponse({'status': 'success', 'message': 'Docker container and image deleted successfully!'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
    

''''def get_exam_time(request):
    try:
        with open("config.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            exam_time = int(data.get("exam_time", 30))  # Default 30 dakika
            return JsonResponse({"exam_time": exam_time})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)'
'''