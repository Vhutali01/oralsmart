"""
Signals for referral system
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Referral, ReferralComment


@receiver(post_save, sender=Referral)
def referral_status_changed(sender, instance, created, **kwargs):
    """
    Send notifications when referral status changes
    """
    if not created and instance.notifications_enabled:
        # TODO: Implement notification system
        # Send notification to referring user when status changes
        pass


@receiver(post_save, sender=ReferralComment)
def new_comment_notification(sender, instance, created, **kwargs):
    """
    Notify users when new comment is added
    """
    if created and instance.referral.notifications_enabled:
        # TODO: Implement notification system
        # Notify relevant parties about new comment
        pass
