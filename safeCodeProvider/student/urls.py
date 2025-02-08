from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_login, name='student_login'),  # Giriş sayfası
    path('exam/', views.exam_page, name='exam_page'),     # Sınav sayfası
    path('control/', views.student_control, name='student_control'),  # API: Öğrenci giriş kontrolü
]