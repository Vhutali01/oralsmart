from django.urls import path
from . import views

app_name = 'referrals'

urlpatterns = [
    # Main referral views (require login)
    path('<int:pk>/', views.referral_detail, name='detail'),
    path('<int:pk>/resend/', views.referral_resend, name='resend'),
    path('<int:pk>/cancel/', views.referral_cancel, name='cancel'),
    path('stats/', views.referral_stats, name='stats'),
    
    # Public portal view (no login required)
    path('view/<str:access_token>/', views.portal_view, name='portal_view'),
]
