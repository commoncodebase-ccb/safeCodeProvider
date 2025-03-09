import csv  
import io
import os  
import json
import subprocess
import sys  
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

        return JsonResponse({
        'status': 'success',
        'redirect_url': '/exam/',
        'student_id': student_id,
        'student_name': student_name
    })

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})  

def student_login(request):  
    return render(request, 'student_login.html')

def exam_run(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            student_id = data.get('student_id')
            code = data.get('code')
            file_extension = "py"  # Varsayılan olarak Python

            # Dosya uzantısını config.json'dan al
            config_path = os.path.join(settings.BASE_DIR, 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as config_file:
                    config_data = json.load(config_file)
                    file_extension = config_data.get('file_extension', 'py')
            
            # Dosyayı uploads içine kaydet
            uploads_dir = os.path.join(settings.BASE_DIR, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            file_path = os.path.join(uploads_dir, f"{student_id}.{file_extension}")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # Python kodu çalıştırma
            if file_extension == "py":
                old_stdout = sys.stdout  # Mevcut stdout'u kaydet
                sys.stdout = io.StringIO()  # Çıktıyı yakalamak için
                try:
                    exec(code, {}, {})  # Kullanıcı kodunu çalıştır
                    output = sys.stdout.getvalue()  # Çıktıyı al
                except Exception as e:
                    output = str(e)
                finally:
                    sys.stdout = old_stdout  # stdout'u geri yükle
            
            # Java kodu çalıştırma
            elif file_extension == "java":
                class_name = f"{student_id}_Program"
                java_file = os.path.join(uploads_dir, f"{class_name}.java")
                with open(java_file, 'w', encoding='utf-8') as f:
                    f.write(code)
                compile_status = os.system(f"javac {java_file}")
                if compile_status == 0:
                    output = os.popen(f"java -cp {uploads_dir} {class_name}").read()
                else:
                    output = "Java derleme hatası"
            
            # C kodu çalıştırma
            elif file_extension == "c":
                c_file = os.path.join(uploads_dir, f"{student_id}.c")
                exe_file = os.path.join(uploads_dir, f"{student_id}")
                with open(c_file, 'w', encoding='utf-8') as f:
                    f.write(code)
                compile_status = os.system(f"gcc {c_file} -o {exe_file}")
                if compile_status == 0:
                    output = os.popen(f"{exe_file}").read()
                else:
                    output = "C derleme hatası"
            
            else:
                output = "Unsupported language"
            
            return JsonResponse({'status': 'success', 'output': 'Code is running'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'output': str(e)})
    return JsonResponse({'status': 'error', 'output': 'Invalid request'})

def exam_submit(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            student_id = data.get('student_id')
            code = data.get('code')
            file_extension = "py"
            
            # Dosya uzantısını config.json'dan al
            config_path = os.path.join(settings.BASE_DIR, 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as config_file:
                    config_data = json.load(config_file)
                    file_extension = config_data.get('file_extension', 'py')
            
            # Öğrenci kodunu uploads içine kaydet
            uploads_dir = os.path.join(settings.BASE_DIR, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            file_path = os.path.join(uploads_dir, f"{student_id}.{file_extension}")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            return JsonResponse({'status': 'success', 'message': 'Exam submitted successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def exam_page(request):
    config_path = os.path.join(settings.BASE_DIR, 'config.json')
<<<<<<< HEAD
    pdf_text = "No instructions available."
    editor_type = "python"
    student_id = request.GET.get("student_id", "unknown")
    
    try:
        with open(config_path, 'r') as config_file:
            config_data = json.load(config_file)
            exam_time = int(config_data.get('exam_time', 10))
            file_extension = config_data.get('file_extension', 'py')
            if file_extension == "java":
                editor_type = "java"
            elif file_extension == "c":
                editor_type = "c"
    except FileNotFoundError:
        exam_time = 10

    return render(request, 'exam_page.html', {'exam_time': exam_time, 'pdf_text': pdf_text, 'editor_type': editor_type, 'student_id': student_id})
=======
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

from django.http import JsonResponse
import os
import json

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
        student_folder = os.path.join(UPLOADS_DIR, folder_name)
        print("student_folder:", student_folder)

        if not os.path.exists(student_folder):
            return JsonResponse({'status': 'error', 'message': 'Student folder not found'})
        
        # Öğrencinin kod dosyası yolunu oluştur
        code_file_path = os.path.join(student_folder, file_name)
        print("code_file_path:", code_file_path)

        # Kod dosyasını yaz
        with open(code_file_path, "w") as f:
            f.write(code)
        
        return JsonResponse({'status': 'success', "message": "Code saved successfully!"})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
>>>>>>> 17cbb0f1f4280b0487facb51512ee68a53d640d1
