"""oralsmart URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from patient.views import create_patient, patient_list_view
from userauth.views import login_user, logout_user,register_user, home_view, landing
from userprofile.views import profile_view, get_professions
from assessments.views import dental_screening, dietary_screening
from reports.views import generate_pdf, view_report, send_report_email 
from userauth.views import activate, change_password, req_password_reset, confirm_password_reset
from facility.views import clinic_list, refer_patient
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),

    #landing page
    path('', landing, name='landing'),

    #for home page
    path('home/', home_view, name='home'),

    #for patient
    path('create_patient/', create_patient, name='create_patient'),
    path('patient_list/', patient_list_view, name='patient_list'),

    #for userauth
    path('login_user/', login_user, name='login'),
    path('logout_user/', logout_user, name='logout'),
    path('register_user/', register_user, name='register_user'),

    #for profile
    path('profile_view/', profile_view, name='profile'),
    path('ajax/get_professions/', get_professions, name='get_professions'), #gets professions for authority body dynamically

    #for screening assessments
    path('assessments/dietary_screening/<int:patient_id>/', dietary_screening, name='dietary_screening'),
    path('assessments/dental_screening/<int:patient_id>/', dental_screening, name='dental_screening'),

    #for reports
    path('reports/report/<int:patient_id>/', view_report, name='report'),
    path('reports/<int:patient_id>/', generate_pdf, name='generate_pdf'),
    path('reports/send-email/<int:patient_id>/', send_report_email, name='send_report_email'),

    #for activating account
    path('activate/<uidb64>/<token>/', activate, name='activate'),

    #for password reset
    path('change_password/', change_password, name='change_password'),
    path('reset_password/', req_password_reset, name='reset_password'),
    path('reset/<uidb64>/<token>/', confirm_password_reset, name='confirm_password_reset'),

    #for clinics
    path('clinics/', clinic_list, name='clinics'),
    path('clinics/refer/<int:clinic_id>/', refer_patient, name='refer_patient'),

    #for ML models
    path('ml/', include('ml_models.urls')),

    #for health tips
    path('tips/', include('tips.urls')),

    # Health check endpoint
    path('health/', include('oralsmart.health_urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
