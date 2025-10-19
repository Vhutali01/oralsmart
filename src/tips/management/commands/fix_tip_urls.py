from django.core.management.base import BaseCommand
from tips.models import HealthTip

class Command(BaseCommand):
    help = 'Fix broken URLs in existing health tips'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Fixing broken URLs in health tips...'))
        
        # URL mapping for real websites
        url_fixes = {
            'https://www.health.gov.za/oral-health-guidelines': '',
            'https://www.hpcsa.co.za/dental-guidelines': 'https://www.hpcsa.co.za',
            'https://www.health.gov.za/fbdg': 'https://www.health.gov.za',
            'https://www.health.gov.za/fbdg-sugar': '',
            'https://www.health.gov.za/emergency': 'https://www.health.gov.za',
            'https://www.nicd.ac.za/hand-hygiene': 'https://www.nicd.ac.za'
        }
        
        updated_count = 0
        for tip in HealthTip.objects.all():
            if tip.citation_url in url_fixes:
                old_url = tip.citation_url
                tip.citation_url = url_fixes[old_url]
                tip.save()
                updated_count += 1
                
                if tip.citation_url:
                    self.stdout.write(f'Updated "{tip.title}" URL: {old_url} → {tip.citation_url}')
                else:
                    self.stdout.write(f'Removed broken URL for "{tip.title}": {old_url}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} health tips!')
        )