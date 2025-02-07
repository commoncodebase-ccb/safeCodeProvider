from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_login, name='student_login'),  # Giriş sayfası
    path('exam/', views.exam_page, name='exam_page'),     # Sınav sayfası (ileride ekleyeceğiz)
]