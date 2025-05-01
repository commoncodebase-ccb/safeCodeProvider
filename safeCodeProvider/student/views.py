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

# Determine the full path of the JSON file
        json_path = os.path.join(settings.BASE_DIR, "students.json")

        # Read the JSON file
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as json_file:
                students_data = json.load(json_file)  # Get JSON data as a list
        
        # Check the user's ID and update the isLogged value
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
                # Write the updated data back to the JSON file
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
            exam_time = int(config_data.get('exam_time', 10))  # In minutes
            exam_type = config_data.get('exam_type', 'py')  # For example "py", "java", "c"
    except FileNotFoundError:
        exam_time = 10
        exam_type = 'py'
    
    # Dynamically find the PDF file from the exam_instruction folder (we do not hardcode the file name)
    pdf_url = ''
    exam_instruction_folder = os.path.join(settings.MEDIA_ROOT, 'exam_instruction')
    if os.path.exists(exam_instruction_folder):
        pdf_files = [f for f in os.listdir(exam_instruction_folder) if f.lower().endswith('.pdf')]
        if pdf_files:
            pdf_url = settings.MEDIA_URL + 'exam_instruction/' + pdf_files[0]
    
    # Dynamically read the file content from the assignment_file folder
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
                assignment_content = f"An error occurred while reading the file: {e}"
    
    return render(request, 'exam_page.html', {
        'exam_time': exam_time,
        'exam_type': exam_type,
        'pdf_url': pdf_url,
        'assignment_content': assignment_content,
    })

def save_code(request):
    try:
        # Get the JSON data
        body = json.loads(request.body)

        # Get the information using the JSON data
        student_id = body.get('student_id')
        student_name = body.get('student_name').lower()
        code = body.get('code')

        # Open the configuration file
        config_path = "config.json"
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)

        file_name = config.get("file_name", "script").lower()
        exam_type = config.get("type", "py").lower()
        file_name += f".{exam_type}"

        # Path to the student's file
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


        # Check the existing container
        check_status_command = f"docker ps -a -f name={container_name} --format '{{{{.State}}}}'"
        container_status = os.popen(check_status_command).read().strip()

       
        code_file_path = os.path.join(student_folder, file_name)

        # if you want to add more languages, you can add them here with elif statements like below. 
        docker_exec_command=""
        if exam_type=="py":
            docker_exec_command = f"docker exec {container_name} python /app/{file_name}"
        elif exam_type=="java":
            docker_exec_command = f"docker exec {container_name} javac /app/{file_name}.java && docker exec {container_name} java -cp /app {file_name}"
        elif exam_type=="c":
            docker_exec_command = f"docker exec {container_name} gcc /app/{file_name}.c -o /app/{file_name} && docker exec {container_name}- /app/{file_name}"

        copy_command = f"docker cp {code_file_path} {container_name}:/app/{file_name}"
        os.system(copy_command)
        try:
                result = subprocess.run(
                    docker_exec_command,
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
        # Get the JSON data
        body = json.loads(request.body)

        # Get the JSON data
        student_id = body.get('student_id')
        student_name = body.get('student_name').lower()

        # Create Docker container and image names
        container_name = f"{student_id}-{student_name}-container"
        image_name = f"{student_id}-{student_name}"

        # First, stop and remove the container
        stop_container_command = f"docker stop {container_name} && docker rm {container_name}"
        delete_image_command = f"docker rmi -f {image_name}"

        print(f"Stopping and removing container: {container_name}")
        os.system(stop_container_command)  # Stop and remove the container
        print(f"Removing image: {image_name}")
        os.system(delete_image_command)  # Delete the image

        return JsonResponse({'status': 'success', 'message': 'Docker container and image deleted successfully!'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def get_config(request):
    config_path = os.path.join("config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            return JsonResponse(data)
    return JsonResponse({"error": "Config file not found"}, status=404)
    

def get_file_content(request):
    filename = request.GET.get('filename')
    file_path = os.path.join('media', 'assignment_files', filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return JsonResponse({'content': content})