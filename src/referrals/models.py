from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from patient.models import Patient
from assessments.models import DentalScreening, DietaryScreening
from facility.models import Clinic
import secrets
from datetime import timedelta


class Referral(models.Model):
    """
    Main referral model supporting multiple delivery methods
    """
    
    URGENCY_CHOICES = [
        ('routine', 'Routine'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency')
    ]
    
    SPECIALTY_CHOICES = [
        ('general', 'General Dentistry'),
        ('orthodontics', 'Orthodontics'),
        ('pediatric', 'Pediatric Dentistry'),
        ('oral_surgery', 'Oral Surgery'),
        ('endodontics', 'Endodontics'),
        ('periodontics', 'Periodontics'),
        ('prosthodontics', 'Prosthodontics'),
        ('other', 'Other')
    ]
    
    DELIVERY_METHOD_CHOICES = [
        ('internal', 'Internal System'),
        ('api', 'API'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('portal', 'Portal Link'),
        ('manual', 'Manual')
    ]
    
    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('retrying', 'Retrying')
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('acknowledged', 'Acknowledged'),
        ('appointment_scheduled', 'Appointment Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired')
    ]
    
    # Unique identifier
    referral_number = models.CharField(max_length=20, unique=True, editable=False)
    
    # Patient & Assessment
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='referrals')
    dental_screening = models.ForeignKey(DentalScreening, on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    dietary_screening = models.ForeignKey(DietaryScreening, on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    
    # Referring party
    referring_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='referrals_sent')
    referring_facility = models.ForeignKey(Clinic, on_delete=models.PROTECT, related_name='referrals_from')
    
    # Receiving party (flexible for internal/external)
    receiving_facility = models.ForeignKey(Clinic, on_delete=models.PROTECT, related_name='referrals_to')
    receiving_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals_received')
    
    # External provider details (for non-system providers)
    external_provider_name = models.CharField(max_length=255, blank=True, help_text="Name of external provider")
    external_provider_email = models.EmailField(blank=True, help_text="Email of external provider")
    external_provider_phone = models.CharField(max_length=20, blank=True, help_text="Phone of external provider")
    
    # Referral details
    reason = models.TextField(help_text="Brief reason for referral")
    clinical_summary = models.TextField(help_text="Detailed clinical findings and notes")
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='routine')
    specialty_required = models.CharField(max_length=30, choices=SPECIALTY_CHOICES, default='general')
    
    # Additional information
    patient_preferences = models.TextField(blank=True, help_text="Patient/parent preferences or concerns")
    insurance_information = models.TextField(blank=True, help_text="Insurance details if applicable")
    
    # Delivery tracking
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHOD_CHOICES, blank=True)
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='pending')
    delivery_attempts = models.IntegerField(default=0)
    last_delivery_attempt = models.DateTimeField(null=True, blank=True)
    delivery_error = models.TextField(blank=True, help_text="Error message if delivery failed")
    
    # Status tracking
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    appointment_date = models.DateTimeField(null=True, blank=True, help_text="Scheduled appointment with receiving provider")
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(help_text="Referral expiration date")
    
    # Secure access
    access_token = models.CharField(max_length=64, unique=True, editable=False)
    view_count = models.IntegerField(default=0)
    last_viewed_at = models.DateTimeField(null=True, blank=True)
    
    # Communication settings
    allow_comments = models.BooleanField(default=True)
    notifications_enabled = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Referral'
        verbose_name_plural = 'Referrals'
        indexes = [
            models.Index(fields=['referral_number']),
            models.Index(fields=['access_token']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Generate referral number if not exists
        if not self.referral_number:
            year = timezone.now().year
            # Get last referral number for this year
            last_referral = Referral.objects.filter(
                referral_number__startswith=f'REF-{year}-'
            ).order_by('-referral_number').first()
            
            if last_referral:
                last_number = int(last_referral.referral_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.referral_number = f'REF-{year}-{new_number:06d}'
        
        # Generate access token if not exists
        if not self.access_token:
            self.access_token = secrets.token_urlsafe(32)
        
        # Set expiration date if not set (30 days from creation)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=30)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.referral_number} - {self.patient.name} to {self.receiving_facility.name}"
    
    def is_expired(self):
        """Check if referral has expired"""
        return timezone.now() > self.expires_at
    
    def is_urgent(self):
        """Check if referral is urgent or emergency"""
        return self.urgency in ['urgent', 'emergency']
    
    def get_portal_url(self):
        """Get the secure portal URL"""
        from django.urls import reverse
        return reverse('referrals:portal_view', kwargs={'access_token': self.access_token})


class ReferralDeliveryLog(models.Model):
    """
    Tracks all delivery attempts for audit and troubleshooting
    """
    
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('retrying', 'Retrying')
    ]
    
    referral = models.ForeignKey(Referral, on_delete=models.CASCADE, related_name='delivery_logs')
    method = models.CharField(max_length=20, choices=Referral.DELIVERY_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True)
    response_data = models.JSONField(null=True, blank=True, help_text="API response or other delivery data")
    attempted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-attempted_at']
        verbose_name = 'Delivery Log'
        verbose_name_plural = 'Delivery Logs'
    
    def __str__(self):
        return f"{self.referral.referral_number} - {self.method} - {self.status}"


class ReferralComment(models.Model):
    """
    Two-way communication between referring and receiving providers
    """
    referral = models.ForeignKey(Referral, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    author_name = models.CharField(max_length=255, help_text="Name if external user")
    comment = models.TextField()
    is_internal = models.BooleanField(default=True, help_text="Whether comment is from internal system user")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Referral Comment'
        verbose_name_plural = 'Referral Comments'
    
    def __str__(self):
        author = self.author.get_full_name() if self.author else self.author_name
        return f"Comment by {author} on {self.referral.referral_number}"


class ReferralAttachment(models.Model):
    """
    Additional documents or images attached to referral
    """
    referral = models.ForeignKey(Referral, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='referrals/attachments/%Y/%m/')
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Referral Attachment'
        verbose_name_plural = 'Referral Attachments'
    
    def __str__(self):
        return f"{self.filename} - {self.referral.referral_number}"
