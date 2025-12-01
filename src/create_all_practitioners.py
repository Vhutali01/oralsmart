"""
Script to create 3 test practitioners for each profession type.
This ensures comprehensive testing of the referral system with all professional types.
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

# First names pool
FIRST_NAMES = [
    'Sarah', 'Michael', 'Emily', 'James', 'Lisa', 'Robert', 'Jennifer', 'David',
    'Jessica', 'John', 'Ashley', 'Daniel', 'Amanda', 'Christopher', 'Melissa',
    'Matthew', 'Michelle', 'Joshua', 'Kimberly', 'Andrew', 'Elizabeth', 'Joseph',
    'Rebecca', 'Ryan', 'Laura', 'Jacob', 'Stephanie', 'Nicholas', 'Rachel', 'Tyler',
    'Nicole', 'Brandon', 'Samantha', 'Zachary', 'Heather', 'Kevin', 'Brittany',
    'Eric', 'Catherine', 'Brian', 'Angela', 'Justin', 'Christine', 'Aaron', 'Danielle',
    'Adam', 'Janet', 'Scott', 'Maria', 'Steven', 'Diana', 'Jonathan', 'Julie',
    'Thomas', 'Carolyn', 'Patrick', 'Victoria', 'Charles', 'Lauren', 'Benjamin',
    'Grace', 'Samuel', 'Olivia', 'Nathan', 'Emma', 'Alexander', 'Sophia', 'Jack',
]

# Last names pool
LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
    'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
    'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White',
    'Harris', 'Clark', 'Lewis', 'Robinson', 'Walker', 'Young', 'Hall', 'Allen',
    'King', 'Wright', 'Scott', 'Green', 'Baker', 'Adams', 'Nelson', 'Carter',
    'Mitchell', 'Roberts', 'Turner', 'Phillips', 'Campbell', 'Parker', 'Evans',
    'Edwards', 'Collins', 'Stewart', 'Morris', 'Rogers', 'Reed', 'Cook', 'Morgan',
    'Bell', 'Murphy', 'Bailey', 'Cooper', 'Richardson', 'Cox', 'Howard', 'Ward',
    'Peterson', 'Gray', 'James', 'Watson', 'Brooks', 'Kelly', 'Sanders', 'Price',
]

# Clinics for affiliation (ensure they exist)
CLINIC_NAMES = [
    'City General Hospital',
    'Suburban Health Center',
    'Regional Medical Clinic',
    'Downtown Wellness Center',
    'Community Health Hub',
]

def get_or_create_clinics():
    """Get or create test clinics for practitioner affiliation"""
    clinics = []
    for name in CLINIC_NAMES:
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
        if created:
            print(f"Created clinic: {name}")
    return clinics

def create_practitioners():
    """Create 3 practitioners for each profession"""
    
    print("Creating comprehensive test practitioners...")
    print("=" * 80)
    
    clinics = get_or_create_clinics()
    created_users = []
    
    # Counter for name generation
    name_index = 0
    
    for prof_code, prof_name in PROFESSIONS:
        print(f"\nCreating {prof_name} practitioners...")
        
        for i in range(3):
            # Generate unique name
            first_name = FIRST_NAMES[name_index % len(FIRST_NAMES)]
            last_name = LAST_NAMES[name_index % len(LAST_NAMES)]
            full_name = f"Dr. {first_name} {last_name}"
            
            # Create username from profession and number
            username = f"{prof_code}_{i+1}"
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                print(f"  ⚠ User {username} already exists, skipping...")
                name_index += 1
                continue
            
            try:
                # Create user
                user = User.objects.create_user(
                    username=username,
                    password='test123',
                    first_name=first_name,
                    last_name=last_name,
                    email=f'{username}@oralsmart.test'
                )
                
                # Get or create profile
                profile, created = Profile.objects.get_or_create(
                    user=user,
                    defaults={
                        'profession': prof_code,
                        'accepts_referrals': True,
                        'availability_status': 'available' if i < 2 else 'busy',
                        'reg_num': f"REG{prof_code.upper()}{1000 + name_index}",
                        'health_professional_body': 'SANC' if 'nurse' in prof_code or 'midwife' in prof_code else 'HPCSA',
                        'affiliated_facility': clinics[name_index % len(clinics)],
                        'consultation_details': f"Specializing in {prof_name.lower()}"
                    }
                )
                
                # If profile already existed, update it
                if not created:
                    profile.profession = prof_code
                    profile.accepts_referrals = True
                    profile.availability_status = 'available' if i < 2 else 'busy'
                    profile.reg_num = f"REG{prof_code.upper()}{1000 + name_index}"
                    profile.health_professional_body = 'SANC' if 'nurse' in prof_code or 'midwife' in prof_code else 'HPCSA'
                    profile.affiliated_facility = clinics[name_index % len(clinics)]
                    profile.consultation_details = f"Specializing in {prof_name.lower()}"
                    profile.save()
                
                created_users.append({
                    'name': full_name,
                    'profession': prof_name,
                    'username': username,
                    'password': 'test123',
                    'clinic': profile.affiliated_facility.name,
                    'status': profile.availability_status,
                })
                
                print(f"  ✓ Created: {full_name} ({username}) at {profile.affiliated_facility.name}")
                
            except Exception as e:
                print(f"  ✗ Error creating {username}: {str(e)}")
            
            name_index += 1
    
    print("\n" + "=" * 80)
    print(f"Successfully created {len(created_users)} practitioners")
    
    return created_users

def update_test_users_file(created_users):
    """Update the referral_API_test_users.txt file with all practitioners"""
    
    output_file = 'referral_API_test_users.txt'
    
    with open(output_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("ORALSMART REFERRAL SYSTEM - TEST PRACTITIONERS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total Practitioners: {len(created_users)}\n")
        f.write("Default Password: test123\n")
        f.write("All practitioners accept referrals and are affiliated with clinics\n")
        f.write("=" * 80 + "\n\n")
        
        # Group by profession
        by_profession = {}
        for user in created_users:
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
                f.write(f"Availability: {user['status'].title()}\n")
                f.write("-" * 80 + "\n")
    
    print(f"\n✓ Updated {output_file} with all {len(created_users)} practitioners")
    print(f"  Grouped by {len(by_profession)} professions")

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("COMPREHENSIVE PRACTITIONER CREATION SCRIPT")
    print("Creating 3 practitioners for each profession type")
    print("=" * 80 + "\n")
    
    created_users = create_practitioners()
    
    if created_users:
        update_test_users_file(created_users)
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total practitioners created: {len(created_users)}")
        print(f"Professions covered: {len(set(u['profession'] for u in created_users))}")
        print(f"Clinics used: {len(set(u['clinic'] for u in created_users))}")
        print("\nAll credentials saved to: referral_API_test_users.txt")
        print("Default password for all users: test123")
        print("=" * 80 + "\n")
    else:
        print("\n⚠ No new practitioners were created.")
