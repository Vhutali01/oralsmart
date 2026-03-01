from django.db import models
import datetime

# Create your models here.

class Clinic(models.Model):
    name = models.CharField(max_length=64)
    address = models.CharField(max_length=64, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=254, blank=True, null=True)
    website = models.URLField(max_length=199, blank=True, null=True)
    description = models.TextField(max_length=254,blank=True, null=True)
    hours = models.CharField(max_length=64, blank=True, null=True)
    emergency = models.CharField(max_length=64, blank=True, null=True)
    #geolocation = models.CharField(max_length=64, blank=True, null=True)
    clinic_type = models.CharField(
        max_length=20, 
        choices=[('public', 'Public'), ('private', 'Private')],
        default='public'
    )
    accepts_referrals = models.BooleanField(default=True, help_text="Whether this clinic accepts referrals")
    referral_email = models.EmailField(max_length=254, blank=True, null=True, help_text="Email for receiving referrals (if different from main email)")
    
    # Working hours configuration
    working_days = models.JSONField(
        default=list,
        blank=True,
        help_text="List of working days (0=Monday, 6=Sunday). Default: [0,1,2,3,4] (Mon-Fri)"
    )
    opening_time = models.TimeField(
        default=datetime.time(8, 0),
        help_text="Clinic opening time"
    )
    closing_time = models.TimeField(
        default=datetime.time(17, 0),
        help_text="Clinic closing time"
    )

    def __str__(self):
        return self.name
    
    def get_working_days(self):
        """Return working days or default Mon-Fri"""
        return self.working_days if self.working_days else [0, 1, 2, 3, 4]
    
    def is_working_day(self, date):
        """Check if a given date falls on a working day"""
        return date.weekday() in self.get_working_days()
    
    def is_within_hours(self, time):
        """Check if a given time is within operating hours"""
        return self.opening_time <= time <= self.closing_time