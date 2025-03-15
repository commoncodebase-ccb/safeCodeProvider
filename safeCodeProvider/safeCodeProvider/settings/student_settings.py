from .settings import *

INSTALLED_APPS += ['student']
# Ensure the Student app uses its own URLs
ROOT_URLCONF = 'student.urls'
# app2 sadece 8002 portunda çalışsın
PORT = 8001
