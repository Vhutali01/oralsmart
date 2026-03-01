from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth.models import User
from patient.factory import (
    PatientWithMixedAssessmentsFactory,
    PatientWithBothAssessmentsFactory, 
    PatientWithDentalOnlyFactory,
    PatientWithDietaryOnlyFactory
)
from patient.models import Patient
from assessments.models import DentalScreening, DietaryScreening
import sys

# Try to import Profile (user profiles)
try:
    from userprofile.models import Profile as UserProfile
except ImportError:
    UserProfile = None

class Command(BaseCommand):
    help = 'Create patients with complete assessments using factories and manage database data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            help='Number of patients to create (if not provided, will prompt)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompts',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Batch size for bulk creation (default: 100)',
        )
        parser.add_argument(
            '--assessment-pattern',
            choices=['mixed', 'both', 'dental-only', 'dietary-only'],
            default='mixed',
            help='Assessment pattern: mixed (65%% both, 20%% dental, 15%% dietary), both (all have both), dental-only, dietary-only (default: mixed)',
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean all data from database',
        )
        parser.add_argument(
            '--clean-patients',
            action='store_true',
            help='Clean only patient data (keep users)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('OralSmart Patient Factory Manager\n')
        )
        
        # Handle cleaning operations
        if options.get('clean'):
            self.clean_all_data(options.get('force', False))
            return
        if options.get('clean_patients'):
            self.clean_patient_data(options.get('force', False))
            return
        
        # Show current database status
        self.show_current_status()
        
        # Get number of patients to create
        count = options.get('count')
        if not count:
            count = self.get_patient_count()
        
        if count <= 0:
            self.stdout.write(self.style.ERROR('Invalid number of patients. Exiting.'))
            return
        
        # Confirm creation if not forced
        if not options.get('force') and not self.confirm_creation(count):
            self.stdout.write(self.style.WARNING('Patient creation cancelled.'))
            return
        
        # Create patients
        batch_size = options.get('batch_size', 100)
        assessment_pattern = options.get('assessment_pattern', 'mixed')
        self.create_patients_in_batches(count, batch_size, assessment_pattern)
        
        # Show final status
        self.stdout.write('\n' + '='*50)
        self.show_current_status()
        
        pattern_description = {
            'mixed': 'mixed assessment patterns',
            'both': 'both dental and dietary assessments',
            'dental-only': 'dental assessments only',
            'dietary-only': 'dietary assessments only'
        }
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {count} patients with {pattern_description[assessment_pattern]}!')
        )

    def show_current_status(self):
        """Display current database status"""
        patient_count = Patient.objects.count()
        dental_count = DentalScreening.objects.count()
        dietary_count = DietaryScreening.objects.count()
        user_count = User.objects.count()
        
        self.stdout.write('Current Database Status:')
        self.stdout.write(f'   Users: {user_count}')
        self.stdout.write(f'   Patients: {patient_count}')
        self.stdout.write(f'   Dental Screenings: {dental_count}')
        self.stdout.write(f'   Dietary Screenings: {dietary_count}')
        self.stdout.write('')

    def get_patient_count(self):
        """Prompt user for number of patients to create"""
        while True:
            try:
                response = input('How many patients would you like to create? ')
                count = int(response)
                if count < 0:
                    self.stdout.write(self.style.ERROR('Please enter a positive number.'))
                    continue
                return count
            except ValueError:
                self.stdout.write(self.style.ERROR('Please enter a valid number.'))
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\nOperation cancelled.'))
                sys.exit(0)

    def confirm_creation(self, count):
        """Confirm patient creation with user"""
        self.stdout.write(
            self.style.WARNING(f'About to create {count} patients with complete assessments.')
        )
        self.stdout.write('   Each patient will have:')
        self.stdout.write('   • Patient demographics')
        self.stdout.write('   • Dental screening (all fields)')
        self.stdout.write('   • Dietary screening (11 sections)')
        self.stdout.write('')
        
        return self.get_confirmation()

    def get_confirmation(self):
        """Get yes/no confirmation from user"""
        while True:
            try:
                response = input('Do you want to continue? (y/n): ').lower().strip()
                if response in ['y', 'yes']:
                    return True
                elif response in ['n', 'no']:
                    return False
                else:
                    self.stdout.write(self.style.ERROR('Please enter y or n.'))
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\nOperation cancelled.'))
                return False

    def create_patients_in_batches(self, total_count, batch_size, assessment_pattern='mixed'):
        """Create patients in batches with progress reporting"""
        created_count = 0
        batches = (total_count + batch_size - 1) // batch_size  # Ceiling division
        
        # Select the appropriate factory
        factory_map = {
            'mixed': PatientWithMixedAssessmentsFactory,
            'both': PatientWithBothAssessmentsFactory,
            'dental-only': PatientWithDentalOnlyFactory,
            'dietary-only': PatientWithDietaryOnlyFactory
        }
        
        selected_factory = factory_map[assessment_pattern]
        
        self.stdout.write(f'🏭 Creating {total_count} patients with "{assessment_pattern}" pattern in {batches} batches of {batch_size}...')
        
        # Show pattern details
        if assessment_pattern == 'mixed':
            self.stdout.write('   Pattern: 65% both assessments, 20% dental only, 15% dietary only')
        elif assessment_pattern == 'both':
            self.stdout.write('   Pattern: All patients will have both dental and dietary assessments')
        elif assessment_pattern == 'dental-only':
            self.stdout.write('   Pattern: All patients will have dental assessments only')
        elif assessment_pattern == 'dietary-only':
            self.stdout.write('   Pattern: All patients will have dietary assessments only')
        
        self.stdout.write('')
        
        try:
            for batch_num in range(batches):
                # Calculate batch size for this iteration
                remaining = total_count - created_count
                current_batch_size = min(batch_size, remaining)
                
                self.stdout.write(f'Creating batch {batch_num + 1}/{batches} ({current_batch_size} patients)...', ending='')
                
                # Create patients with transaction for data integrity
                with transaction.atomic():
                    # Create patients using the selected factory
                    patients = []
                    for _ in range(current_batch_size):
                        patient = selected_factory.create()
                        patients.append(patient)
                    created_count += len(patients)
                
                self.stdout.write(self.style.SUCCESS(' Done'))
                
                # Show progress
                progress_percentage = (created_count / total_count) * 100
                self.stdout.write(f'Progress: {created_count}/{total_count} ({progress_percentage:.1f}%)')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\nError creating patients: {str(e)}')
            )
            raise CommandError(f'Failed to create patients: {str(e)}')
        
        self.stdout.write(f'\nBatch creation completed! Created {created_count} patients.')

    def clean_all_data(self, force=False):
        """Clean all data from database"""
        self.stdout.write('🧹 Database Cleaning - ALL DATA')
        self.show_current_status()
        
        if not force:
            self.stdout.write(
                self.style.ERROR('WARNING: This will delete ALL data including users!')
            )
            self.stdout.write('   This includes:')
            self.stdout.write('   • All patients and assessments')
            self.stdout.write('   • All users (including admin users)')
            self.stdout.write('   • All user profiles')
            self.stdout.write('')
            
            if not self.get_confirmation():
                self.stdout.write(self.style.WARNING('Database cleaning cancelled.'))
                return
        
        try:
            with transaction.atomic():
                # Delete in order to avoid foreign key constraints
                DentalScreening.objects.all().delete()
                DietaryScreening.objects.all().delete()
                Patient.objects.all().delete()
                if UserProfile:
                    UserProfile.objects.all().delete()
                User.objects.all().delete()
                
            self.stdout.write(self.style.SUCCESS('All data cleaned successfully!'))
            self.show_current_status()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error cleaning database: {str(e)}')
            )

    def clean_patient_data(self, force=False):
        """Clean only patient data, keep users"""
        self.stdout.write('🧹 Database Cleaning - PATIENT DATA ONLY')
        self.show_current_status()
        
        if not force:
            self.stdout.write(
                self.style.WARNING('This will delete all patient data but keep users.')
            )
            self.stdout.write('   This includes:')
            self.stdout.write('   • All patients')
            self.stdout.write('   • All dental screenings')
            self.stdout.write('   • All dietary screenings')
            self.stdout.write('   • Users will be preserved')
            self.stdout.write('')
            
            if not self.get_confirmation():
                self.stdout.write(self.style.WARNING('Patient data cleaning cancelled.'))
                return
        
        try:
            with transaction.atomic():
                # Delete patient data only
                DentalScreening.objects.all().delete()
                DietaryScreening.objects.all().delete()
                Patient.objects.all().delete()
                
            self.stdout.write(self.style.SUCCESS('Patient data cleaned successfully!'))
            self.show_current_status()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error cleaning patient data: {str(e)}')
            )
