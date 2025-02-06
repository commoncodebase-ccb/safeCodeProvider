from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

def student_login_page(request):
    return HttpResponse("Öğrenci giriş sayfası burası!")

