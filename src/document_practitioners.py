"""
Script to update existing test practitioners and document them all.
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

# All professions from the Profile model
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

def document_all_practitioners():
    """Document all existing practitioners"""
    
    print("Documenting all test practitioners...")
    print("=" * 80)
    
    all_users = []
    
    for prof_code, prof_name in PROFESSIONS:
        for i in range(1, 4):
            username = f"{prof_code}_{i}"
            
            try:
                user = User.objects.get(username=username)
                profile = Profile.objects.get(user=user)
                
                full_name = f"Dr. {user.first_name} {user.last_name}" if user.first_name else username
                
                all_users.append({
                    'name': full_name,
                    'profession': prof_name,
                    'username': username,
                    'password': 'test123',
                    'clinic': profile.affiliated_facility.name if profile.affiliated_facility else 'No clinic',
                    'status': profile.get_availability_status_display() if profile.availability_status else 'N/A',
                    'accepts_referrals': 'Yes' if profile.accepts_referrals else 'No',
                })
                
                print(f"✓ Found: {full_name} ({username}) - {prof_name}")
                
            except User.DoesNotExist:
                print(f"✗ Missing: {username}")
            except Profile.DoesNotExist:
                print(f"⚠ User {username} exists but has no profile")
    
    print(f"\n{'=' * 80}")
    print(f"Found {len(all_users)} practitioners")
    
    return all_users

def update_test_users_file(all_users):
    """Update the referral_API_test_users.txt file with all practitioners"""
    
    output_file = 'referral_API_test_users.txt'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("ORALSMART REFERRAL SYSTEM - TEST PRACTITIONERS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total Practitioners: {len(all_users)}\n")
        f.write("Default Password: test123\n")
        f.write("All practitioners are configured for referral testing\n")
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
    print(f"  Grouped by {len(by_profession)} professions")

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("PRACTITIONER DOCUMENTATION SCRIPT")
    print("=" * 80 + "\n")
    
    all_users = document_all_practitioners()
    
    if all_users:
        update_test_users_file(all_users)
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total practitioners documented: {len(all_users)}")
        print(f"Professions covered: {len(set(u['profession'] for u in all_users))}")
        print(f"All credentials saved to: referral_API_test_users.txt")
        print("Default password for all users: test123")
        print("=" * 80 + "\n")
    else:
        print("\n⚠ No practitioners found.")
