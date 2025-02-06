from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_login_page, name='student_login_page'),  # Öğrenci giriş sayfası
]
