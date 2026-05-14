from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from referrals.models import Referral


class Notification(models.Model):
    """
    In-app notification system for users
    """
    
    NOTIFICATION_TYPES = [
        ('new_referral', 'New Referral'),
        ('urgent_referral', 'Urgent Referral'),
        ('emergency_referral', 'Emergency Referral'),
        ('status_update', 'Status Update'),
        ('new_comment', 'New Comment'),
        ('system', 'System Notification'),
    ]
    
    # Recipient
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    # Content
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Related objects
    referral = models.ForeignKey(
        Referral, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='notifications'
    )
    
    # URL to navigate to when clicked
    action_url = models.CharField(max_length=500, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Optional expiration date for temporary notifications"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.user.username} - {'Read' if self.is_read else 'Unread'}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def get_urgency_class(self):
        """Return CSS class for urgency level"""
        urgency_classes = {
            'emergency_referral': 'danger',
            'urgent_referral': 'warning',
            'new_referral': 'info',
            'status_update': 'secondary',
            'new_comment': 'primary',
            'system': 'dark',
        }
        return urgency_classes.get(self.notification_type, 'secondary')
    
    def get_icon(self):
        """Return Font Awesome icon class"""
        icons = {
            'emergency_referral': 'fa-exclamation-triangle',
            'urgent_referral': 'fa-exclamation-circle',
            'new_referral': 'fa-file-medical',
            'status_update': 'fa-sync-alt',
            'new_comment': 'fa-comment',
            'system': 'fa-bell',
        }
        return icons.get(self.notification_type, 'fa-bell')
    
    @classmethod
    def cleanup_old_read_notifications(cls, days=30):
        """Remove old read notifications (maintenance task)"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        deleted_count = cls.objects.filter(
            is_read=True,
            read_at__lt=cutoff_date
        ).delete()[0]
        return deleted_count
