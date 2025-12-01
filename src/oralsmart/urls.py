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
from userprofile.views import profile_view, get_professions, edit_name, edit_contact, edit_profession, edit_email, edit_phone, edit_address, get_practitioners, toggle_referral_acceptance, update_availability, edit_clinic
from assessments.views import dental_screening, dietary_screening
from reports.views import generate_pdf, view_report, send_report_email, save_referral_details
from userauth.views import activate, change_password, req_password_reset, confirm_password_reset
from facility.views import clinic_list, refer_patient, refer_to_practitioner, get_working_hours_api
from referrals.views import generate_referral_pdf
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
    
    # HTMX profile editing endpoints
    path('profile/edit/name/', edit_name, name='edit_name'),
    path('profile/edit/contact/', edit_contact, name='edit_contact'),
    path('profile/edit/profession/', edit_profession, name='edit_profession'),
    path('profile/edit/email/', edit_email, name='edit_email'),
    path('profile/edit/phone/', edit_phone, name='edit_phone'),
    path('profile/edit/address/', edit_address, name='edit_address'),
    path('profile/edit/clinic/', edit_clinic, name='edit_clinic'),
    
    # Practitioner API endpoints
    path('api/practitioners/', get_practitioners, name='get_practitioners'),
    path('api/practitioners/toggle-acceptance/', toggle_referral_acceptance, name='toggle_referral_acceptance'),
    path('api/practitioners/update-availability/', update_availability, name='update_availability'),

    #for screening assessments
    path('assessments/dietary_screening/<int:patient_id>/', dietary_screening, name='dietary_screening'),
    path('assessments/dental_screening/<int:patient_id>/', dental_screening, name='dental_screening'),

    #for reports
    path('reports/report/<int:patient_id>/', view_report, name='report'),
    path('reports/<int:patient_id>/', generate_pdf, name='generate_pdf'),
    path('reports/send-email/<int:patient_id>/', send_report_email, name='send_report_email'),
    path('reports/save-referral/<int:patient_id>/', save_referral_details, name='save_referral_details'),

    #for activating account
    path('activate/<uidb64>/<token>/', activate, name='activate'),

    #for password reset
    path('change_password/', change_password, name='change_password'),
    path('reset_password/', req_password_reset, name='reset_password'),
    path('reset/<uidb64>/<token>/', confirm_password_reset, name='confirm_password_reset'),

    #for clinics
    path('clinics/', clinic_list, name='clinics'),
    path('clinics/refer/<int:clinic_id>/', refer_patient, name='refer_patient'),
    path('clinics/refer-practitioner/', refer_to_practitioner, name='refer_to_practitioner'),
    path('api/working-hours/', get_working_hours_api, name='working_hours_api'),

    #for referrals
    path('referrals/', include('referrals.urls')),
    path('referral/<int:pk>/pdf/', generate_referral_pdf, name='referral_pdf'),

    #for notifications
    path('notifications/', include('notifications.urls')),

    #for ML models
    path('ml/', include('ml_models.urls')),

    #for health tips
    path('tips/', include('tips.urls')),

    # Health check endpoint
    path('health/', include('oralsmart.health_urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
