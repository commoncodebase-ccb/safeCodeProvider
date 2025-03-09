from django.conf import settings
from django.conf.urls.static import static
from django.urls import path  
from . import views 

urlpatterns = [
    path('', views.student_login, name='student_login'),  
    path('exam/', views.exam_page, name='exam_page'),  
    path('control/', views.student_control, name='student_control'),  # Öğrenci giriş kontrolünü sağlayan API URL'si
    path('save_code/', views.save_code, name='save_code'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)