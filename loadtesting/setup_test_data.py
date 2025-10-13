"""
Database Setup Script for Load Testing
=====================================

This script sets up test data for load testing the OralSmart application.
Run this before performing load tests to ensure realistic data exists.

Usage:
    python loadtesting/setup_test_data.py
"""

import os
import sys
import django
from django.conf import settings

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oralsmart.settings')
django.setup()

from django.contrib.auth.models import User
from patient.models import Patient
from assessments.models import DentalScreening, DietaryScreening
from userprofile.models import Profile
from faker import Faker
import random
from datetime import date, timedelta

fake = Faker()


def create_test_users(count=5):
    """Create test users for load testing"""
    print(f"Creating {count} test users...")
    
    users = []
    for i in range(count):
        username = f"loadtest_user_{i+1}"
        email = f"loadtest_{i+1}@example.com"
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            print(f"User {username} already exists, skipping...")
            users.append(User.objects.get(username=username))
            continue
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password="loadtest123",
            first_name=fake.first_name(),
            last_name=fake.last_name()
        )
        
        # Create profile
        Profile.objects.create(
            user=user,
            email=email,
            tel=fake.phone_number()[:15],
            address=fake.address()[:100],
            profession=random.choice(['dentist', 'dental_hygienist', 'nurse'])
        )
        
        users.append(user)
        print(f"Created user: {username}")
    
    return users


def create_test_patients(users, count=50):
    """Create test patients for load testing"""
    print(f"Creating {count} test patients...")
    
    patients = []
    for i in range(count):
        user = random.choice(users)
        
        patient = Patient.objects.create(
            name=fake.first_name(),
            surname=fake.last_name(),
            age=str(random.randint(0, 6)),  # Age as string choice 0-6
            gender=random.choice(['0', '1']),  # '0' for Male, '1' for Female
            parent_name=fake.first_name(),
            parent_surname=fake.last_name(),
            parent_id=str(fake.random_number(digits=13)),
            parent_contact=fake.phone_number()[:12],  # Max 12 characters
            created_by=user
        )
        
        patients.append(patient)
        
        if (i + 1) % 10 == 0:
            print(f"Created {i + 1} patients...")
    
    return patients


def create_test_assessments(patients, percentage=60):
    """Create dental and dietary assessments for some patients"""
    count = int(len(patients) * percentage / 100)
    print(f"Creating assessments for {count} patients ({percentage}%)...")
    
    selected_patients = random.sample(patients, count)
    
    for i, patient in enumerate(selected_patients):
        # Create dental screening (80% chance)
        if random.random() < 0.8:
            # Create teeth data JSON
            teeth_data = {}
            for tooth_num in range(11, 19):  # Upper right
                teeth_data[f'tooth_{tooth_num}'] = random.choice(['healthy', 'decayed', 'missing', 'filled'])
            for tooth_num in range(21, 29):  # Upper left  
                teeth_data[f'tooth_{tooth_num}'] = random.choice(['healthy', 'decayed', 'missing', 'filled'])
            for tooth_num in range(31, 39):  # Lower left
                teeth_data[f'tooth_{tooth_num}'] = random.choice(['healthy', 'decayed', 'missing', 'filled'])
            for tooth_num in range(41, 49):  # Lower right
                teeth_data[f'tooth_{tooth_num}'] = random.choice(['healthy', 'decayed', 'missing', 'filled'])
            
            dental_data = {
                'patient': patient,
                # Section 1
                'sa_citizen': random.choice(['yes', 'no']),
                'special_needs': random.choice(['yes', 'no']),
                'caregiver_treatment': random.choice(['yes', 'no']),
                # Section 2
                'appliance': random.choice(['yes', 'no']),
                'plaque': random.choice(['yes', 'no']),
                'dry_mouth': random.choice(['yes', 'no']),
                'enamel_defects': random.choice(['yes', 'no']),
                # Section 3
                'fluoride_water': random.choice(['yes', 'no']),
                'fluoride_toothpaste': random.choice(['yes', 'no']),
                'topical_fluoride': random.choice(['yes', 'no']),
                'regular_checkups': random.choice(['yes', 'no']),
                # Section 4
                'sealed_pits': random.choice(['yes', 'no']),
                'restorative_procedures': random.choice(['yes', 'no']),
                'enamel_change': random.choice(['yes', 'no']),
                'dentin_discoloration': random.choice(['yes', 'no']),
                'white_spot_lesions': random.choice(['yes', 'no']),
                'cavitated_lesions': random.choice(['yes', 'no']),
                'multiple_restorations': random.choice(['yes', 'no']),
                'missing_teeth': random.choice(['yes', 'no']),
                # Section 5
                'teeth_data': teeth_data
            }
            
            DentalScreening.objects.create(**dental_data)
        
        # Create dietary screening (70% chance)
        if random.random() < 0.7:
            dietary_data = {
                'patient': patient,
                # Section 1: Sweet/Sugary Foods
                'sweet_sugary_foods': random.choice(['yes', 'no']),
                'sweet_sugary_foods_daily': random.choice(['1-3_day', '3-4_day', '4-6_day']) if random.random() < 0.5 else None,
                'sweet_sugary_foods_weekly': random.choice(['1-3_week', '3-4_week', '4-6_week']) if random.random() < 0.5 else None,
                'sweet_sugary_foods_timing': random.choice(['with_meals', 'between_meals', 'both']) if random.random() < 0.5 else None,
                'sweet_sugary_foods_bedtime': random.choice(['yes', 'no']) if random.random() < 0.5 else None,
                
                # Section 2: Take-aways and Processed Foods
                'takeaways_processed_foods': random.choice(['yes', 'no']),
                'takeaways_processed_foods_daily': random.choice(['1-3_day', '3-4_day', '4-6_day']) if random.random() < 0.5 else None,
                'takeaways_processed_foods_weekly': random.choice(['1-3_week', '3-4_week', '4-6_week']) if random.random() < 0.5 else None,
                
                # Section 3: Fresh Fruit
                'fresh_fruit': random.choice(['yes', 'no']),
                'fresh_fruit_daily': random.choice(['1-3_day', '3-4_day', '4-6_day']) if random.random() < 0.5 else None,
                'fresh_fruit_weekly': random.choice(['1-3_week', '3-4_week', '4-6_week']) if random.random() < 0.5 else None,
                'fresh_fruit_timing': random.choice(['with_meals', 'between_meals', 'both']) if random.random() < 0.5 else None,
                'fresh_fruit_bedtime': random.choice(['yes', 'no']) if random.random() < 0.5 else None,
                
                # Section 4: Cold Drinks, Juices and Flavoured Water and Milk
                'cold_drinks_juices': random.choice(['yes', 'no']),
                'cold_drinks_juices_daily': random.choice(['1-3_day', '3-4_day', '4-6_day']) if random.random() < 0.5 else None,
                'cold_drinks_juices_weekly': random.choice(['1-3_week', '3-4_week', '4-6_week']) if random.random() < 0.5 else None,
                'cold_drinks_juices_timing': random.choice(['with_meals', 'between_meals', 'both']) if random.random() < 0.5 else None,
                'cold_drinks_juices_bedtime': random.choice(['yes', 'no']) if random.random() < 0.5 else None,
                
                # Section 5: Processed Fruit
                'processed_fruit': random.choice(['yes', 'no']),
                'processed_fruit_daily': random.choice(['1-3_day', '3-4_day', '4-6_day']) if random.random() < 0.5 else None,
                'processed_fruit_weekly': random.choice(['1-3_week', '3-4_week', '4-6_week']) if random.random() < 0.5 else None,
                'processed_fruit_timing': random.choice(['with_meals', 'between_meals', 'both']) if random.random() < 0.5 else None,
                'processed_fruit_bedtime': random.choice(['yes', 'no']) if random.random() < 0.5 else None,
                
                # Section 6: Spreads
                'spreads': random.choice(['yes', 'no']),
                'spreads_daily': random.choice(['1-3_day', '3-4_day', '4-6_day']) if random.random() < 0.5 else None,
                'spreads_weekly': random.choice(['1-3_week', '3-4_week', '4-6_week']) if random.random() < 0.5 else None,
                'spreads_timing': random.choice(['with_meals', 'between_meals', 'both']) if random.random() < 0.5 else None,
                'spreads_bedtime': random.choice(['yes', 'no']) if random.random() < 0.5 else None,
                
                # Section 7: Added Sugars
                'added_sugars': random.choice(['yes', 'no']),
                'added_sugars_daily': random.choice(['1-3_day', '3-4_day', '4-6_day']) if random.random() < 0.5 else None,
                'added_sugars_weekly': random.choice(['1-3_week', '3-4_week', '4-6_week']) if random.random() < 0.5 else None,
                'added_sugars_timing': random.choice(['with_meals', 'between_meals', 'both']) if random.random() < 0.5 else None,
                'added_sugars_bedtime': random.choice(['yes', 'no']) if random.random() < 0.5 else None,
                
                # Section 8: Salty Snacks
                'salty_snacks': random.choice(['yes', 'no']),
                'salty_snacks_daily': random.choice(['1-3_day', '3-4_day', '4-6_day']) if random.random() < 0.5 else None,
                'salty_snacks_weekly': random.choice(['1-3_week', '3-4_week', '4-6_week']) if random.random() < 0.5 else None,
                'salty_snacks_timing': random.choice(['with_meals', 'between_meals', 'both']) if random.random() < 0.5 else None,
                
                # Section 9: Dairy Products
                'dairy_products': random.choice(['yes', 'no']),
                'dairy_products_daily': random.choice(['1-3_day', '3-4_day', '4-6_day']) if random.random() < 0.5 else None,
                'dairy_products_weekly': random.choice(['1-3_week', '3-4_week', '4-6_week']) if random.random() < 0.5 else None,
                
                # Section 10: Vegetables
                'vegetables': random.choice(['yes', 'no']),
                'vegetables_daily': random.choice(['1-3_day', '3-4_day', '4-6_day']) if random.random() < 0.5 else None,
                'vegetables_weekly': random.choice(['1-3_week', '3-4_week', '4-6_week']) if random.random() < 0.5 else None,
                
                # Section 11: Water
                'water': random.choice(['yes', 'no']),
                'water_timing': random.choice(['with_meals', 'between_meals', 'after_sweets', 'before_bedtime']) if random.random() < 0.7 else None,
                'water_glasses': random.choice(['<2', '2-4', '5+']) if random.random() < 0.7 else None,
            }
            
            DietaryScreening.objects.create(**dietary_data)
        
        if (i + 1) % 10 == 0:
            print(f"Created assessments for {i + 1} patients...")


def main():
    """Main setup function"""
    print("Setting up test data for OralSmart load testing...")
    print("=" * 50)
    
    # Create test users
    users = create_test_users(5)
    
    # Create test patients
    patients = create_test_patients(users, 100)
    
    # Create assessments for 60% of patients
    create_test_assessments(patients, 60)
    
    print("\n" + "=" * 50)
    print("Test data setup completed!")
    print(f"Created:")
    print(f"- {len(users)} test users")
    print(f"- {len(patients)} test patients") 
    print(f"- Assessments for ~60% of patients")
    print("\nTest users (password: loadtest123):")
    for user in users:
        print(f"- {user.username}")
    
    print("\nYou can now run load tests!")


if __name__ == "__main__":
    main()