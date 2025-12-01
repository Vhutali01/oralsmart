from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.db import models
import os

# Create your models here.

class Profile(models.Model):
    
    HEALTH_BODIES = [
        ('HPCSA', 'Health Professions Council of South Africa'),
        ('SANC', 'South African Nursing Council'),
    ]

    PROFESSIONS = [
        # HPCSA - Health Professions Council of South Africa
        ('medical_doctor', 'Medical Doctor'),
        ('dentist', 'Dentist'),
        ('psychologist', 'Psychologist'),
        ('physiotherapist', 'Physiotherapist'),
        ('radiographer', 'Radiographer'),
        ('occupational_therapist', 'Occupational Therapist'),
        ('biokineticist', 'Biokineticist'),
        ('clinical_technologist', 'Clinical Technologist'),
        ('dietitian', 'Dietitian'),
        ('audiologist', 'Audiologist'),
        ('optometrist', 'Optometrist'),
        ('emergency_care_practitioner', 'Emergency Care Practitioner'),
        
        # SANC - South African Nursing Council
        ('registered_nurse', 'Registered Nurse'),
        ('enrolled_nurse', 'Enrolled Nurse'),
        ('nursing_assistant', 'Nursing Assistant'),
        ('midwife', 'Midwife'),
        
        # Dental Specialists (for referral recommendations)
        ('orthodontist', 'Orthodontist'),
        ('oral_surgeon', 'Oral Surgeon'),
        ('periodontist', 'Periodontist'),
        ('endodontist', 'Endodontist'),
        ('pediatric_dentist', 'Pediatric Dentist'),
        ('prosthodontist', 'Prosthodontist'),
        ('oral_pathologist', 'Oral Pathologist'),
        ('pediatrician', 'Pediatrician'),
    ]
    
    AVAILABILITY_STATUS = [
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('unavailable', 'Unavailable'),
        ('on_leave', 'On Leave'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    profession = models.CharField(
        max_length=64,
        choices=PROFESSIONS,
        default='dentist'
    )

    health_professional_body = models.CharField(
        max_length=64,
        choices=HEALTH_BODIES,
        default='HPCSA'
    )

    reg_num = models.CharField(
        max_length=64,
        default="0",
    )

    email = models.CharField(max_length=64, null=True)

    address = models.CharField(max_length=64, null=True)
    
    tel = models.CharField(max_length=64, null=True)

    profile_pic = models.ImageField(upload_to='profile/', default='images/default/default_profile_pic.jpg',null=True, blank=True)
    
    # Referral-related fields
    accepts_referrals = models.BooleanField(
        default=False,
        help_text="Whether this practitioner accepts patient referrals"
    )
    
    specialization = models.CharField(
        max_length=255,
        blank=True,
        help_text="Areas of specialization or expertise"
    )
    
    availability_status = models.CharField(
        max_length=20,
        choices=AVAILABILITY_STATUS,
        default='available',
        help_text="Current availability for accepting new patients"
    )
    
    consultation_details = models.TextField(
        blank=True,
        help_text="Consultation hours, fees, or other relevant details"
    )
    
    affiliated_facility = models.ForeignKey(
        'facility.Clinic',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='affiliated_practitioners',
        help_text="Primary facility/clinic this practitioner is affiliated with"
    )
    
    # Working hours configuration
    working_days = models.JSONField(
        default=list,
        blank=True,
        help_text="List of working days (0=Monday, 6=Sunday). Default: [0,1,2,3,4] (Mon-Fri)"
    )
    work_start_time = models.TimeField(
        default='08:00',
        blank=True,
        null=True,
        help_text="Practitioner's start time"
    )
    work_end_time = models.TimeField(
        default='17:00',
        blank=True,
        null=True,
        help_text="Practitioner's end time"
    )

    def get_profile_picture_url(self):
        """
        Returns profile picture URL or default if none exists
        """
        if self.profile_pic:
            return self.profile_pic.url
        return f"{settings.MEDIA_URL}images/default/default_profile_pic.jpg"
    
    @property
    def profile_picture_url(self):
        """Property version of get_profile_picture_url"""
        return self.get_profile_picture_url()