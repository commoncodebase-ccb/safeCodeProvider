from django.urls import path
from .views import teacher_home, upload_files, start_exam, submits_page

urlpatterns = [
    path('', teacher_home, name='teacher_home'),
    path('upload/', upload_files, name='upload_files'),
    path('start_exam/', start_exam, name='start_exam'),
     path('submits/', submits_page, name='submits_page'),
]