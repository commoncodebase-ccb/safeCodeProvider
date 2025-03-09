from django.conf import settings
from django.conf.urls.static import static
from django.urls import path  
from . import views 

urlpatterns = [
    path('', views.student_login, name='student_login'),  
    path('exam/', views.exam_page, name='exam_page'),  
    path('control/', views.student_control, name='student_control'),  # Öğrenci giriş kontrolünü sağlayan API URL'si
<<<<<<< HEAD
    path('exam_run/', views.exam_run, name='exam_run'), 
    path('exam_submit/', views.exam_submit, name='exam_submit'),
=======
    path('save_code/', views.save_code, name='save_code'),
>>>>>>> 17cbb0f1f4280b0487facb51512ee68a53d640d1
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)