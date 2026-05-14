"""
Script to create/update profiles for all test practitioners.
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oralsmart.settings')
django.setup()

from django.contrib.auth.models import User
from userprofile.models import Profile
from facility.models import Clinic

# All professions
PROFESSIONS = [
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
    ('registered_nurse', 'Registered Nurse'),
    ('enrolled_nurse', 'Enrolled Nurse'),
    ('nursing_assistant', 'Nursing Assistant'),
    ('midwife', 'Midwife'),
    ('orthodontist', 'Orthodontist'),
    ('oral_surgeon', 'Oral Surgeon'),
    ('periodontist', 'Periodontist'),
    ('endodontist', 'Endodontist'),
    ('pediatric_dentist', 'Pediatric Dentist'),
    ('prosthodontist', 'Prosthodontist'),
    ('oral_pathologist', 'Oral Pathologist'),
    ('pediatrician', 'Pediatrician'),
]

# Names for practitioners
FIRST_NAMES = ['Sarah', 'Michael', 'Emily', 'James', 'Lisa', 'Robert', 'Jennifer', 'David', 'Jessica']
LAST_NAMES = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez']

def setup_practitioners():
    """Create or update profiles for all practitioners"""
    
    print("Setting up test practitioners...")
    print("=" * 80)
    
    # Get or create clinics
    clinics = []
    clinic_names = [
        'City General Hospital',
        'Suburban Health Center',
        'Regional Medical Clinic',
        'Downtown Wellness Center',
        'Community Health Hub',
    ]
    
    for name in clinic_names:
        clinic, created = Clinic.objects.get_or_create(
            name=name,
            defaults={
                'address': f'123 {name} Street',
                'phone_number': '0123456789',
                'email': f'{name.lower().replace(" ", "_")}@example.com',
                'clinic_type': 'public' if 'Community' in name or 'General' in name else 'private',
                'hours': '08:00 - 17:00',
                'emergency': 'Available' if 'Hospital' in name else 'Not Available',
            }
        )
        clinics.append(clinic)
    
    all_users = []
    name_idx = 0
    
    for prof_code, prof_name in PROFESSIONS:
        print(f"\nSetting up {prof_name} practitioners...")
        
        for i in range(1, 4):
            username = f"{prof_code}_{i}"
            
            # Get first and last name
            first_name = FIRST_NAMES[name_idx % len(FIRST_NAMES)]
            last_name = LAST_NAMES[name_idx % len(LAST_NAMES)]
            
            try:
                # Get or create user
                user, user_created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': f'{username}@oralsmart.test'
                    }
                )
                
                # Set password
                user.set_password('test123')
                if not user.first_name:
                    user.first_name = first_name
                    user.last_name = last_name
                user.save()
                
                # Get or create profile
                profile, prof_created = Profile.objects.get_or_create(
                    user=user,
                    defaults={
                        'profession': prof_code,
                        'accepts_referrals': True,
                        'availability_status': 'available' if i <= 2 else 'busy',
                        'reg_num': f"REG{name_idx:04d}",
                        'health_professional_body': 'SANC' if 'nurse' in prof_code or 'midwife' in prof_code else 'HPCSA',
                        'affiliated_facility': clinics[name_idx % len(clinics)],
                        'consultation_details': f"Specializing in {prof_name.lower()}"
                    }
                )
                
                # Update if already existed
                if not prof_created:
                    profile.profession = prof_code
                    profile.accepts_referrals = True
                    profile.availability_status = 'available' if i <= 2 else 'busy'
                    if not profile.reg_num or profile.reg_num == "0":
                        profile.reg_num = f"REG{name_idx:04d}"
                    profile.health_professional_body = 'SANC' if 'nurse' in prof_code or 'midwife' in prof_code else 'HPCSA'
                    profile.affiliated_facility = clinics[name_idx % len(clinics)]
                    if not profile.consultation_details:
                        profile.consultation_details = f"Specializing in {prof_name.lower()}"
                    profile.save()
                
                full_name = f"Dr. {user.first_name} {user.last_name}"
                
                all_users.append({
                    'name': full_name,
                    'profession': prof_name,
                    'username': username,
                    'password': 'test123',
                    'clinic': profile.affiliated_facility.name,
                    'status': profile.availability_status.title(),
                    'accepts_referrals': 'Yes' if profile.accepts_referrals else 'No',
                })
                
                status = "Created" if user_created else "Updated"
                print(f"  ✓ {status}: {full_name} ({username}) at {profile.affiliated_facility.name}")
                
            except Exception as e:
                print(f"  ✗ Error with {username}: {str(e)}")
            
            name_idx += 1
    
    print(f"\n{'=' * 80}")
    print(f"Set up {len(all_users)} practitioners")
    
    return all_users

def update_test_users_file(all_users):
    """Update the referral_API_test_users.txt file"""
    
    output_file = 'referral_API_test_users.txt'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("ORALSMART REFERRAL SYSTEM - TEST PRACTITIONERS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total Practitioners: {len(all_users)}\n")
        f.write("Default Password: test123\n")
        f.write("All practitioners accept referrals and are affiliated with clinics\n")
        f.write("=" * 80 + "\n\n")
        
        # Group by profession
        by_profession = {}
        for user in all_users:
            prof = user['profession']
            if prof not in by_profession:
                by_profession[prof] = []
            by_profession[prof].append(user)
        
        # Write grouped by profession
        for profession in sorted(by_profession.keys()):
            f.write(f"\n{'=' * 80}\n")
            f.write(f"{profession.upper()}\n")
            f.write(f"{'=' * 80}\n")
            
            for user in by_profession[profession]:
                f.write(f"\nName: {user['name']}\n")
                f.write(f"Profession: {user['profession']}\n")
                f.write(f"Username: {user['username']}\n")
                f.write(f"Password: {user['password']}\n")
                f.write(f"Affiliated Clinic: {user['clinic']}\n")
                f.write(f"Availability: {user['status']}\n")
                f.write(f"Accepts Referrals: {user['accepts_referrals']}\n")
                f.write("-" * 80 + "\n")
    
    print(f"\n✓ Updated {output_file} with all {len(all_users)} practitioners")

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("PRACTITIONER SETUP SCRIPT")
    print("Creating/Updating 3 practitioners for each profession")
    print("=" * 80 + "\n")
    
    all_users = setup_practitioners()
    
    if all_users:
        update_test_users_file(all_users)
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total practitioners: {len(all_users)}")
        print(f"Professions: {len(set(u['profession'] for u in all_users))}")
        print(f"Clinics: {len(set(u['clinic'] for u in all_users))}")
        print("\nAll credentials saved to: referral_API_test_users.txt")
        print("Default password for all users: test123")
        print("=" * 80 + "\n")
