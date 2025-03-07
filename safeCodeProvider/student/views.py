import csv  
import os  
import json  
from django.shortcuts import render 
from django.http import JsonResponse  
from django.conf import settings


def student_control(request):  # Öğrenci girişini ve doğrulamasını yapan fonksiyon
    if request.method == 'POST':  
        student_id = request.POST.get('student_id')
        student_name = request.POST.get('student_name') 
        exam_password = request.POST.get('exam_password') 

        # Exam configuration dosyasını oku
        config_path = os.path.join(settings.BASE_DIR, 'config.json') 
        try:
            with open(config_path, 'r') as config_file:  
                config_data = json.load(config_file)  
                correct_password = config_data.get('exam_password')  
        except FileNotFoundError:
            return JsonResponse({'status': 'error', 'message': 'Exam configuration not found'})  

        if exam_password != correct_password:  
            return JsonResponse({'status': 'error', 'message': 'Invalid exam password. Please try again.'})

        # Dinamik olarak student_list dosyasını bul
        student_list_path = os.path.join(settings.MEDIA_ROOT, 'student_list')  
        try:
            files = os.listdir(student_list_path)
            if files:
                student_list_file = os.path.join(student_list_path, files[0])  # İlk ve tek dosyayı al
            else:
                return JsonResponse({'status': 'error', 'message': 'Student list file not found'})  
        except FileNotFoundError:
            return JsonResponse({'status': 'error', 'message': 'Student list file not found'})  

        # Öğrencinin listede olup olmadığını kontrol et
        try:
            with open(student_list_file, 'r', encoding='utf-8') as csvfile:  
                reader = csv.reader(csvfile)  
                
                # İlk satırı başlık olarak alma, tüm satırları kontrol et
                student_exists = any(
                    row[0] == student_id and row[1].lower() == student_name.lower() 
                    for row in reader
                )
        except FileNotFoundError:
            return JsonResponse({'status': 'error', 'message': 'Student list file not found'})  

        if not student_exists:  
            return JsonResponse({'status': 'error', 'message': 'Student not found in the list'})  

        # Öğrenci için klasör oluştur
        #uploads_path = os.path.join(settings.BASE_DIR, 'uploads')  
        #os.makedirs(uploads_path, exist_ok=True)  
        #student_folder = os.path.join(uploads_path, f"{student_name}_{student_id}") 
        #os.makedirs(student_folder, exist_ok=True)

        return JsonResponse({'status': 'success', 'redirect_url': '/exam/'}) 

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})  

def student_login(request):  
    return render(request, 'student_login.html')

def exam_page(request):
    config_path = os.path.join(settings.BASE_DIR, 'config.json')
    pdf_text = "No instructions available."

    try:
        with open(config_path, 'r') as config_file:
            config_data = json.load(config_file)
            exam_time = int(config_data.get('exam_time', 10))  # Dakika cinsinden al
    except FileNotFoundError:
        exam_time = 10  # Varsayılan olarak 10 dakika

    
    return render(request, 'exam_page.html', {'exam_time': exam_time, 'pdf_text': pdf_text})
