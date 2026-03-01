#!/usr/bin/env python
"""
OralSmart Patient Factory Manager - Standalone Script
=====================================================

Create patients with complete assessments and manage database data.
Run from project root: python patient_manager.py

Features:
- Interactive patient creation with factories
- Database cleaning (all data or patients only)
- Progress tracking and batch processing
- Safe transaction handling

Usage:
    python patient_manager.py                    # Interactive mode
    python patient_manager.py --count 100        # Create 100 patients
    python patient_manager.py --clean            # Clean all data
    python patient_manager.py --clean-patients   # Clean only patient data
    python patient_manager.py --help             # Show help
"""

import os
import sys
import argparse
import django

# Setup Django environment
sys.path.append('src')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oralsmart.settings')
django.setup()

from patient.factory import PatientWithAssessmentsFactory
from patient.models import Patient
from assessments.models import DentalScreening, DietaryScreening
from django.contrib.auth.models import User
from django.db import transaction

# Try to import Profile (user profiles)
try:
    from userprofile.models import Profile as UserProfile
except ImportError:
    UserProfile = None

class PatientManager:
    def __init__(self):
        self.batch_size = 100
    
    def show_current_status(self):
        """Display current database status"""
        patient_count = Patient.objects.count()
        dental_count = DentalScreening.objects.count()
        dietary_count = DietaryScreening.objects.count()
        user_count = User.objects.count()
        
        print('Current Database Status:')
        print(f'   Users: {user_count}')
        print(f'   Patients: {patient_count}')
        print(f'   Dental Screenings: {dental_count}')
        print(f'   Dietary Screenings: {dietary_count}')
        print()

    def get_patient_count(self):
        """Prompt user for number of patients to create"""
        while True:
            try:
                response = input('How many patients would you like to create? ')
                count = int(response)
                if count < 0:
                    print('Please enter a positive number.')
                    continue
                return count
            except ValueError:
                print('Please enter a valid number.')
            except KeyboardInterrupt:
                print('\\nOperation cancelled.')
                sys.exit(0)

    def get_confirmation(self, message="Do you want to continue?"):
        """Get yes/no confirmation from user"""
        while True:
            try:
                response = input(f'{message} (y/n): ').lower().strip()
                if response in ['y', 'yes']:
                    return True
                elif response in ['n', 'no']:
                    return False
                else:
                    print('Please enter y or n.')
            except KeyboardInterrupt:
                print('\\nOperation cancelled.')
                return False

    def confirm_creation(self, count):
        """Confirm patient creation with user"""
        print(f'About to create {count} patients with complete assessments.')
        print('   Each patient will have:')
        print('   • Patient demographics')
        print('   • Dental screening (all fields)')
        print('   • Dietary screening (11 sections)')
        print()
        
        return self.get_confirmation()

    def create_patients_in_batches(self, total_count, batch_size=None):
        """Create patients in batches with progress reporting"""
        if batch_size is None:
            batch_size = self.batch_size
            
        created_count = 0
        batches = (total_count + batch_size - 1) // batch_size
        
        print(f'🏭 Creating {total_count} patients in {batches} batches of {batch_size}...\n')
        
        try:
            for batch_num in range(batches):
                remaining = total_count - created_count
                current_batch_size = min(batch_size, remaining)
                
                print(f'Creating batch {batch_num + 1}/{batches} ({current_batch_size} patients)...', end='')
                
                with transaction.atomic():
                    patients = PatientWithAssessmentsFactory.create_batch(current_batch_size)
                    created_count += len(patients)
                
                print(' Done')
                
                progress_percentage = (created_count / total_count) * 100
                print(f'Progress: {created_count}/{total_count} ({progress_percentage:.1f}%)')
                
        except Exception as e:
            print(f'\nError creating patients: {str(e)}')
            return False
        
        print(f'\nBatch creation completed! Created {created_count} patients.')
        return True

    def clean_all_data(self, force=False):
        """Clean all data from database"""
        print('🧹 Database Cleaning - ALL DATA')
        self.show_current_status()
        
        if not force:
            print('WARNING: This will delete ALL data including users!')
            print('   This includes:')
            print('   • All patients and assessments')
            print('   • All users (including admin users)')
            print('   • All user profiles')
            print()
            
            if not self.get_confirmation():
                print('Database cleaning cancelled.')
                return False
        
        try:
            with transaction.atomic():
                # Delete in order to avoid foreign key constraints
                DentalScreening.objects.all().delete()
                DietaryScreening.objects.all().delete()
                Patient.objects.all().delete()
                if UserProfile:
                    UserProfile.objects.all().delete()
                User.objects.all().delete()
                
            print('All data cleaned successfully!')
            self.show_current_status()
            return True
            
        except Exception as e:
            print(f'Error cleaning database: {str(e)}')
            return False

    def clean_patient_data(self, force=False):
        """Clean only patient data, keep users"""
        print('🧹 Database Cleaning - PATIENT DATA ONLY')
        self.show_current_status()
        
        if not force:
            print('This will delete all patient data but keep users.')
            print('   This includes:')
            print('   • All patients')
            print('   • All dental screenings')
            print('   • All dietary screenings')
            print('   • Users will be preserved')
            print()
            
            if not self.get_confirmation():
                print('Patient data cleaning cancelled.')
                return False
        
        try:
            with transaction.atomic():
                # Delete patient data only
                DentalScreening.objects.all().delete()
                DietaryScreening.objects.all().delete()
                Patient.objects.all().delete()
                
            print('Patient data cleaned successfully!')
            self.show_current_status()
            return True
            
        except Exception as e:
            print(f'Error cleaning patient data: {str(e)}')
            return False

    def create_patients(self, count=None, force=False):
        """Main method to create patients"""
        print('OralSmart Patient Factory Manager\n')
        
        # Show current status
        self.show_current_status()
        
        # Get count if not provided
        if count is None:
            if Patient.objects.count() == 0:
                print('Database is empty - no existing patients found.')
            count = self.get_patient_count()
        
        if count == 0:
            print('No patients to create. Exiting.')
            return True
        
        # Confirm creation
        if not force and not self.confirm_creation(count):
            print('Patient creation cancelled.')
            return False
        
        # Create patients
        print('=' * 50)
        success = self.create_patients_in_batches(count)
        
        if success:
            print('=' * 50)
            self.show_current_status()
            print(f'Successfully created {count} patients with assessments!')
            return True
        else:
            print('Patient creation failed.')
            return False

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='OralSmart Patient Factory Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python patient_manager.py                    # Interactive mode
    python patient_manager.py --count 100        # Create 100 patients
    python patient_manager.py --count 50 --force # Create 50 patients without prompts
    python patient_manager.py --clean            # Clean all data
    python patient_manager.py --clean-patients   # Clean only patient data
    python patient_manager.py --batch-size 50    # Use smaller batches
        """
    )
    
    parser.add_argument(
        '--count',
        type=int,
        help='Number of patients to create (if not provided, will prompt)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompts'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for bulk creation (default: 100)'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean all data from database (including users)'
    )
    
    parser.add_argument(
        '--clean-patients',
        action='store_true',
        help='Clean only patient data (keep users)'
    )
    
    return parser.parse_args()

def main():
    """Main function"""
    try:
        args = parse_arguments()
        manager = PatientManager()
        manager.batch_size = args.batch_size
        
        # Handle cleaning operations
        if args.clean:
            success = manager.clean_all_data(args.force)
            sys.exit(0 if success else 1)
        elif args.clean_patients:
            success = manager.clean_patient_data(args.force)
            sys.exit(0 if success else 1)
        else:
            # Create patients
            success = manager.create_patients(args.count, args.force)
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        print('\nOperation cancelled by user.')
        sys.exit(1)
    except Exception as e:
        print(f'Unexpected error: {str(e)}')
        sys.exit(1)

if __name__ == '__main__':
    main()
