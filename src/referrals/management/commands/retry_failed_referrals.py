"""
Management command to retry failed referral deliveries
Run this as a scheduled task (cron job or celery beat)
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from referrals.models import Referral
from referrals.services import ReferralRouter


class Command(BaseCommand):
    help = 'Retry failed referral deliveries'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--max-attempts',
            type=int,
            default=3,
            help='Maximum number of retry attempts'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Only retry referrals from the last N days'
        )
    
    def handle(self, *args, **options):
        max_attempts = options['max_attempts']
        days = options['days']
        
        # Find failed referrals to retry
        cutoff_date = timezone.now() - timedelta(days=days)
        
        failed_referrals = Referral.objects.filter(
            delivery_status='failed',
            delivery_attempts__lt=max_attempts,
            created_at__gte=cutoff_date
        )
        
        self.stdout.write(f'Found {failed_referrals.count()} failed referrals to retry')
        
        router = ReferralRouter()
        success_count = 0
        fail_count = 0
        
        for referral in failed_referrals:
            self.stdout.write(f'Retrying referral {referral.referral_number}...')
            
            referral.delivery_attempts += 1
            referral.last_delivery_attempt = timezone.now()
            referral.save()
            
            if router.send_referral(referral):
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Successfully delivered {referral.referral_number}')
                )
                success_count += 1
            else:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Failed to deliver {referral.referral_number}')
                )
                fail_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nRetry completed: {success_count} successful, {fail_count} failed'
            )
        )
