from django.urls import path  
from . import views 

urlpatterns = [
    path('', views.student_login, name='student_login'),  
    path('exam/', views.exam_page, name='exam_page'),  
    path('control/', views.student_control, name='student_control'),  # Öğrenci giriş kontrolünü sağlayan API URL'si
]