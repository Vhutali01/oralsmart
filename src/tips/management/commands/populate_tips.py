from django.core.management.base import BaseCommand
from tips.models import TipCategory, HealthTip
from django.utils import timezone

class Command(BaseCommand):
    help = 'Populate health tips database with South African health authority content'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample health tips data...'))
        
        # Create categories
        categories_data = [
            {
                'name': 'Oral Health',
                'description': 'Evidence-based oral health guidelines for South African communities',
                'icon_class': 'fa-tooth'
            },
            {
                'name': 'Nutrition (FBDG)',
                'description': 'Food-Based Dietary Guidelines for South Africa',
                'icon_class': 'fa-apple-alt'
            },
            {
                'name': 'Infectious Diseases',
                'description': 'Prevention and management guidelines from NICD',
                'icon_class': 'fa-shield-virus'
            },
            {
                'name': 'Emergency Contacts',
                'description': 'Critical health emergency information',
                'icon_class': 'fa-ambulance'
            }
        ]
        
        created_categories = []
        for cat_data in categories_data:
            category, created = TipCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'icon_class': cat_data['icon_class']
                }
            )
            created_categories.append(category)
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        # Create tips
        tips_data = [
            {
                'category': 'Oral Health',
                'title': 'Brush Teeth Twice Daily',
                'summary': 'Brush your teeth with fluoride toothpaste morning and evening to prevent tooth decay.',
                'full_text': 'The South African Department of Health recommends brushing teeth twice daily with fluoride toothpaste. Use a soft-bristled toothbrush and brush for at least 2 minutes. This removes plaque and bacteria that cause cavities and gum disease.',
                'citation_source': 'NDOH Oral Health Guidelines 2023',
                'citation_url': '',  # No URL - just citation
                'is_critical': False
            },
            {
                'category': 'Oral Health',
                'title': 'Visit Dentist Regularly',
                'summary': 'Schedule dental check-ups every 6 months to maintain optimal oral health.',
                'full_text': 'Regular dental check-ups help detect problems early and prevent serious oral health issues. The HPCSA recommends dental visits every 6 months for adults and children. Early detection saves money and prevents pain.',
                'citation_source': 'Health Professions Council of South Africa Guidelines',
                'citation_url': 'https://www.hpcsa.co.za',
                'is_critical': False
            },
            {
                'category': 'Nutrition (FBDG)',
                'title': 'Eat Variety of Foods Daily',
                'summary': 'Choose foods from all food groups every day for balanced nutrition.',
                'full_text': 'South African Food-Based Dietary Guidelines recommend eating a variety of foods from all food groups daily. Include vegetables, fruits, whole grains, lean proteins, and dairy products. This ensures your body gets all essential nutrients.',
                'citation_source': 'SA Food-Based Dietary Guidelines 2023',
                'citation_url': 'https://www.health.gov.za',
                'is_critical': False
            },
            {
                'category': 'Nutrition (FBDG)',
                'title': 'Limit Sugar Intake',
                'summary': 'Reduce sugary foods and drinks to prevent obesity and tooth decay.',
                'full_text': 'High sugar intake leads to obesity, diabetes, and tooth decay. The FBDG recommends limiting added sugars, sugary drinks, and processed foods. Choose water instead of sugary drinks, and fresh fruits instead of sweets.',
                'citation_source': 'SA Food-Based Dietary Guidelines - Sugar Recommendations',
                'citation_url': '',  # No URL - just citation
                'is_critical': False
            },
            {
                'category': 'Emergency Contacts',
                'title': 'Emergency Medical Services',
                'summary': 'Call 10177 for emergency medical assistance anywhere in South Africa.',
                'full_text': 'In medical emergencies, call 10177 for ambulance services. This number works nationwide and connects you to emergency medical services. For life-threatening situations, call immediately and stay on the line for instructions.',
                'citation_source': 'National Department of Health Emergency Services',
                'citation_url': 'https://www.health.gov.za',
                'is_critical': True
            },
            {
                'category': 'Infectious Diseases',
                'title': 'Hand Hygiene Prevention',
                'summary': 'Wash hands frequently with soap and water for 20 seconds to prevent infections.',
                'full_text': 'Proper hand hygiene is the most effective way to prevent the spread of infectious diseases. Wash hands with soap and water for at least 20 seconds, especially before eating, after using the toilet, and after coughing or sneezing.',
                'citation_source': 'NICD Infection Prevention Guidelines',
                'citation_url': 'https://www.nicd.ac.za',
                'is_critical': False
            }
        ]
        
        for tip_data in tips_data:
            category = TipCategory.objects.get(name=tip_data['category'])
            tip, created = HealthTip.objects.get_or_create(
                title=tip_data['title'],
                category=category,
                defaults={
                    'summary': tip_data['summary'],
                    'full_text': tip_data['full_text'],
                    'citation_source': tip_data['citation_source'],
                    'citation_url': tip_data['citation_url'],
                    'is_critical': tip_data['is_critical'],
                    'last_updated': timezone.now()
                }
            )
            if created:
                self.stdout.write(f'Created tip: {tip.title}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated health tips database!')
        )