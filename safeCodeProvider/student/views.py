import csv
import os
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings

def student_control(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        student_name = request.POST.get('student_name')
        exam_password = request.POST.get('exam_password')

        # Sınav şifresi doğrulama
        config_path = os.path.join(settings.BASE_DIR, 'config.json')
        try:
            with open(config_path, 'r') as config_file:
                config_data = json.load(config_file)
                correct_password = config_data.get('exam_password')
        except FileNotFoundError:
            return JsonResponse({'status': 'error', 'message': 'Exam configuration not found'})

        if exam_password != correct_password:
            return JsonResponse({'status': 'error', 'message': 'Invalid exam password. Please try again.'})

        # CSV dosyasındaki öğrenci kontrolü
        student_list_path = os.path.join(settings.MEDIA_ROOT, 'student_list/students.csv')
        try:
            with open(student_list_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                student_exists = any(
                    row['student_id'] == student_id and row['name'].lower() == student_name.lower()
                    for row in reader
                )
        except FileNotFoundError:
            return JsonResponse({'status': 'error', 'message': 'Student list file not found'})

        if not student_exists:
            return JsonResponse({'status': 'error', 'message': 'Student not found in the list'})

        # Eğer hata yoksa, öğrenciye özel klasörü oluştur
        uploads_path = os.path.join(settings.BASE_DIR, 'uploads')
        os.makedirs(uploads_path, exist_ok=True)
        student_folder = os.path.join(uploads_path, f"{student_name}_{student_id}")
        os.makedirs(student_folder, exist_ok=True)

        # *Başarılı yanıt ve yönlendirme*
        return JsonResponse({'status': 'success', 'redirect_url': '/exam/'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def student_login(request):
    return render(request, 'student_login.html')

def exam_page(request):
    return render(request, 'exam_page.html')