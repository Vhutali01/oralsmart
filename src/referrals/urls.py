from django.urls import path
from . import views

app_name = 'referrals'

urlpatterns = [
    # Main referral views (require login)
    path('<int:pk>/', views.referral_detail, name='detail'),
    path('<int:pk>/resend/', views.referral_resend, name='resend'),
    path('<int:pk>/cancel/', views.referral_cancel, name='cancel'),
    path('stats/', views.referral_stats, name='stats'),
    
    # API endpoints for referral creation
    path('api/create-practitioner-referral/', views.create_practitioner_referral, name='create_practitioner_referral'),
    path('api/create-clinic-referral/', views.create_clinic_referral, name='create_clinic_referral'),
    
    # Public portal view (no login required)
    path('view/<str:access_token>/', views.portal_view, name='portal_view'),
]
