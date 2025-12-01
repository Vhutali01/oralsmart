from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from userprofile.models import Profile
from facility.models import Clinic
from django.db import transaction


class Command(BaseCommand):
    help = 'Creates test healthcare practitioners for referral system testing'

    def handle(self, *args, **options):
        test_practitioners = [
            {
                'username': 'dr_sarah_jones',
                'password': 'test123',
                'email': 'sarah.jones@example.com',
                'first_name': 'Sarah',
                'last_name': 'Jones',
                'profile': {
                    'phone_number': '555-0101',
                    'address': '123 Medical Plaza, City Center',
                    'role': 'dentist',
                    'specialization': 'General Dentistry',
                    'accepts_referrals': True,
                    'availability_status': 'available',
                    'consultation_details': 'Accepting new patients. General dental care and preventive services.'
                }
            },
            {
                'username': 'dr_michael_chen',
                'password': 'test123',
                'email': 'michael.chen@example.com',
                'first_name': 'Michael',
                'last_name': 'Chen',
                'profile': {
                    'phone_number': '555-0102',
                    'address': '456 Healthcare Ave, Downtown',
                    'role': 'orthodontist',
                    'specialization': 'Orthodontics',
                    'accepts_referrals': True,
                    'availability_status': 'available',
                    'consultation_details': 'Specialist in braces and alignment. Taking referrals for complex cases.'
                }
            },
            {
                'username': 'dr_emily_williams',
                'password': 'test123',
                'email': 'emily.williams@example.com',
                'first_name': 'Emily',
                'last_name': 'Williams',
                'profile': {
                    'phone_number': '555-0103',
                    'address': '789 Dental Street, Westside',
                    'role': 'oral_surgeon',
                    'specialization': 'Oral & Maxillofacial Surgery',
                    'accepts_referrals': True,
                    'availability_status': 'busy',
                    'consultation_details': 'Surgical procedures and extractions. Currently busy but accepting urgent referrals.'
                }
            },
            {
                'username': 'dr_james_patel',
                'password': 'test123',
                'email': 'james.patel@example.com',
                'first_name': 'James',
                'last_name': 'Patel',
                'profile': {
                    'phone_number': '555-0104',
                    'address': '321 Smile Blvd, Eastside',
                    'role': 'periodontist',
                    'specialization': 'Periodontics',
                    'accepts_referrals': True,
                    'availability_status': 'available',
                    'consultation_details': 'Gum disease treatment and dental implants. Open for consultations.'
                }
            },
            {
                'username': 'dr_lisa_martinez',
                'password': 'test123',
                'email': 'lisa.martinez@example.com',
                'first_name': 'Lisa',
                'last_name': 'Martinez',
                'profile': {
                    'phone_number': '555-0105',
                    'address': '654 Health Park, Northside',
                    'role': 'endodontist',
                    'specialization': 'Endodontics (Root Canal Specialist)',
                    'accepts_referrals': True,
                    'availability_status': 'available',
                    'consultation_details': 'Root canal therapy and endodontic treatments. Quick appointments available.'
                }
            },
            {
                'username': 'dr_robert_kim',
                'password': 'test123',
                'email': 'robert.kim@example.com',
                'first_name': 'Robert',
                'last_name': 'Kim',
                'profile': {
                    'phone_number': '555-0106',
                    'address': '987 Care Lane, South District',
                    'role': 'prosthodontist',
                    'specialization': 'Prosthodontics',
                    'accepts_referrals': True,
                    'availability_status': 'available',
                    'consultation_details': 'Dental prosthetics, crowns, and bridges. Expert in restorative dentistry.'
                }
            },
        ]

        # Get or create a test clinic for affiliation
        clinic, created = Clinic.objects.get_or_create(
            name='Central Dental Hub',
            defaults={
                'address': '100 Main Street, City Center',
                'phone_number': '555-1000',
                'email': 'info@centraldental.com',
                'accepts_referrals': True,
                'referral_email': 'referrals@centraldental.com'
            }
        )

        created_users = []

        with transaction.atomic():
            for practitioner_data in test_practitioners:
                # Check if user already exists
                if User.objects.filter(username=practitioner_data['username']).exists():
                    self.stdout.write(
                        self.style.WARNING(f"User {practitioner_data['username']} already exists. Skipping.")
                    )
                    continue

                # Create user
                user = User.objects.create_user(
                    username=practitioner_data['username'],
                    password=practitioner_data['password'],
                    email=practitioner_data['email'],
                    first_name=practitioner_data['first_name'],
                    last_name=practitioner_data['last_name']
                )

                # Update or create profile
                profile, profile_created = Profile.objects.get_or_create(user=user)
                profile.phone_number = practitioner_data['profile']['phone_number']
                profile.address = practitioner_data['profile']['address']
                profile.role = practitioner_data['profile']['role']
                profile.specialization = practitioner_data['profile']['specialization']
                profile.accepts_referrals = practitioner_data['profile']['accepts_referrals']
                profile.availability_status = practitioner_data['profile']['availability_status']
                profile.consultation_details = practitioner_data['profile']['consultation_details']
                profile.affiliated_facility = clinic
                profile.save()

                created_users.append({
                    'username': practitioner_data['username'],
                    'password': practitioner_data['password'],
                    'name': f"Dr. {practitioner_data['first_name']} {practitioner_data['last_name']}",
                    'specialization': practitioner_data['profile']['specialization']
                })

                self.stdout.write(
                    self.style.SUCCESS(f"Created practitioner: {practitioner_data['username']}")
                )

        if created_users:
            self.stdout.write(self.style.SUCCESS('\n' + '='*60))
            self.stdout.write(self.style.SUCCESS('TEST PRACTITIONERS CREATED SUCCESSFULLY'))
            self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
            
            for user in created_users:
                self.stdout.write(f"Name: {user['name']}")
                self.stdout.write(f"Specialization: {user['specialization']}")
                self.stdout.write(f"Username: {user['username']}")
                self.stdout.write(f"Password: {user['password']}")
                self.stdout.write('-'*60)
        else:
            self.stdout.write(self.style.WARNING('\nNo new users created. All practitioners already exist.'))
