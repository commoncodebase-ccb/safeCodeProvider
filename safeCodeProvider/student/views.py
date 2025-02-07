import csv
import os
from django.shortcuts import render, redirect
from django.conf import settings

def student_login(request):
    error_message = None  # Hata mesajını başlangıçta None olarak ayarla

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        student_name = request.POST.get('student_name')
        exam_password = request.POST.get('exam_password')

        # Sınav şifresi doğrulama
        import json
        config_path = os.path.join(settings.BASE_DIR, 'config.json')
        with open(config_path, 'r') as config_file:
            config_data = json.load(config_file)
            correct_password = config_data.get('exam_password')

        if exam_password != correct_password:
            error_message = "Invalid exam password. Please try again."

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
            error_message = "Student list file not found."

        if not error_message and not student_exists:
            error_message = "Student not found in the list."

        if not error_message:  # Eğer hata yoksa, sınav sayfasına yönlendir
            base_dir = settings.BASE_DIR
            uploads_path = os.path.join(base_dir, 'uploads')
            os.makedirs(uploads_path, exist_ok=True)
            student_folder = os.path.join(uploads_path, f"{student_name}_{student_id}")
            os.makedirs(student_folder, exist_ok=True)
            return redirect('/exam')

    return render(request, 'student_login.html', {'error_message': error_message})

def exam_page(request):
    return render(request, 'exam_page.html')