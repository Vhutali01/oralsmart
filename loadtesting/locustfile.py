"""
OralSmart Load Testing with Locust
==================================

This module provides comprehensive load testing for the OralSmart Django application.
It simulates realistic user behaviors including authentication, patient management,
assessments, and report generation.

Usage:
    locust -f loadtesting/locustfile.py --host=http://localhost:8000

Features:
- Realistic user authentication flows
- CSRF token handling for Django forms
- Patient creation and management
- Assessment form submissions
- ML prediction testing
- PDF report generation testing
"""

import random
import time
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from locust.clients import HttpSession

from locust import HttpUser, task, between
from bs4 import BeautifulSoup
from faker import Faker
import json

fake = Faker()


class DjangoUserMixin:
    """Mixin to handle Django-specific functionality like CSRF tokens"""
    client: "HttpSession"
    
    def get_csrf_token(self, response):
        """Extract CSRF token from Django response"""
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
        if csrf_input:
            return csrf_input.get('value')
        return None
    
    def login_user(self, username='testuser', password='testpass123'):
        """Login to Django with CSRF protection"""
        # Get login page and CSRF token
        response = self.client.get('/login_user/')
        csrf_token = self.get_csrf_token(response)
        
        if not csrf_token:
            return False
            
        # Submit login form
        login_data = {
            'username': username,
            'password': password,
            'csrfmiddlewaretoken': csrf_token
        }
        
        response = self.client.post('/login_user/', data=login_data)
        return response.status_code in [200, 302]  # Success or redirect


class OralSmartUser(HttpUser, DjangoUserMixin):
    """
    Simulates a healthcare professional using the OralSmart system
    """
    wait_time = between(2, 8)  # Wait 2-8 seconds between tasks
    
    def on_start(self):
        """Called when a simulated user starts - login required"""
        self.login_user()
    
    @task(3)
    def browse_landing_and_home(self):
        """Browse main pages - lightweight operation"""
        self.client.get('/')
        self.client.get('/home/')
    
    @task(5)
    def view_patient_list(self):
        """View patient list with search functionality"""
        # View all patients
        self.client.get('/patient_list/')
        
        # Test search functionality
        search_terms = ['Smith', 'John', 'Test']
        search_term = random.choice(search_terms)
        self.client.get(f'/patient_list/?search={search_term}')
        
        # Test pagination
        self.client.get('/patient_list/?page=2')
    
    @task(4)
    def create_patient(self):
        """Create a new patient - common workflow"""
        # Get the create patient form
        response = self.client.get('/create_patient/')
        csrf_token = self.get_csrf_token(response)
        
        if csrf_token:
            # Generate realistic patient data
            patient_data = {
                'name': fake.first_name(),
                'surname': fake.last_name(),
                'age': str(random.randint(0, 6)),  # Age as string choice 0-6
                'parent_id': str(fake.random_number(digits=13)),
                'parent_contact': fake.phone_number()[:12],  # Max 12 characters
                'csrfmiddlewaretoken': csrf_token
            }
            
            self.client.post('/create_patient/', data=patient_data)
    
    @task(3)
    def perform_dental_screening(self):
        """Simulate dental screening assessment"""
        # This would require a patient ID, so we'll simulate the GET request
        # In real scenarios, you'd track created patient IDs
        patient_id = random.randint(1, 100)  # Simulate existing patient
        
        response = self.client.get(f'/assessments/dental_screening/{patient_id}/')
        if response.status_code == 200:
            csrf_token = self.get_csrf_token(response)
            
            if csrf_token:
                # Simulate dental screening form data
                dental_data = {
                    'fluoride_use': random.choice(['daily', 'weekly', 'never']),
                    'brushing_frequency': random.choice(['twice_daily', 'once_daily', 'irregular']),
                    'last_dental_visit': fake.date_this_year().strftime('%Y-%m-%d'),
                    'dental_pain': random.choice(['yes', 'no']),
                    'csrfmiddlewaretoken': csrf_token
                }
                
                # Add random tooth data
                for tooth_num in range(11, 19):  # Sample tooth numbers
                    dental_data[f'tooth_{tooth_num}'] = random.choice(['healthy', 'decayed', 'missing', 'filled'])
                
                self.client.post(f'/assessments/dental_screening/{patient_id}/', data=dental_data)
    
    @task(3)
    def perform_dietary_screening(self):
        """Simulate dietary screening assessment"""
        patient_id = random.randint(1, 100)
        
        response = self.client.get(f'/assessments/dietary_screening/{patient_id}/')
        if response.status_code == 200:
            csrf_token = self.get_csrf_token(response)
            
            if csrf_token:
                dietary_data = {
                    'sugary_drinks': random.choice(['daily', 'weekly', 'rarely', 'never']),
                    'snacking_frequency': random.choice(['frequent', 'moderate', 'rare']),
                    'fruit_intake': random.choice(['high', 'moderate', 'low']),
                    'water_consumption': random.choice(['adequate', 'inadequate']),
                    'csrfmiddlewaretoken': csrf_token
                }
                
                self.client.post(f'/assessments/dietary_screening/{patient_id}/', data=dietary_data)
    
    @task(2)
    def generate_report(self):
        """Test report generation - resource intensive"""
        patient_id = random.randint(1, 100)
        
        # View report page
        self.client.get(f'/reports/report/{patient_id}/')
        
        # Generate PDF report
        with self.client.get(f'/reports/{patient_id}/', catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.failure("Patient not found for report generation")
    
    @task(1)
    def test_ml_prediction(self):
        """Test ML risk prediction API - computationally intensive"""
        # This endpoint requires POST with specific data structure
        prediction_data = {
            'dental_features': {
                'dmft_score': random.randint(0, 10),
                'fluoride_use': random.choice([0, 1]),
                'brushing_frequency': random.randint(1, 3)
            },
            'dietary_features': {
                'sugary_drinks': random.randint(0, 3),
                'snacking_frequency': random.randint(1, 4)
            }
        }
        
        # Get CSRF token first
        response = self.client.get('/home/')  # Get any page with CSRF
        csrf_token = self.get_csrf_token(response)
        
        if csrf_token:
            headers = {
                'X-CSRFToken': csrf_token,
                'Content-Type': 'application/json'
            }
            
            self.client.post('/ml/predict-risk/', 
                           data=json.dumps(prediction_data),
                           headers=headers)
    
    @task(1)
    def browse_clinics(self):
        """Browse clinic listings"""
        self.client.get('/clinics/')
        
        # Test clinic search
        search_terms = ['General', 'Pediatric', 'Emergency']
        search_term = random.choice(search_terms)
        self.client.get(f'/clinics/?search={search_term}')
    
    @task(1)
    def view_profile(self):
        """View user profile"""
        self.client.get('/profile_view/')


class HeavyUser(HttpUser, DjangoUserMixin):
    """
    Simulates users performing resource-intensive operations
    """
    wait_time = between(5, 15)  # Longer wait times for heavy operations
    weight = 1  # Lower weight - fewer of these users
    
    def on_start(self):
        self.login_user()
    
    @task(1)
    def stress_test_reports(self):
        """Generate multiple reports in sequence"""
        for patient_id in range(1, 6):  # Test first 5 patients
            self.client.get(f'/reports/{patient_id}/')
            time.sleep(2)  # Brief pause between reports
    
    @task(1)
    def stress_test_ml_predictions(self):
        """Make multiple ML predictions"""
        for _ in range(5):
            prediction_data = {
                'dental_features': {
                    'dmft_score': random.randint(0, 10),
                    'fluoride_use': random.choice([0, 1]),
                    'brushing_frequency': random.randint(1, 3)
                },
                'dietary_features': {
                    'sugary_drinks': random.randint(0, 3),
                    'snacking_frequency': random.randint(1, 4)
                }
            }
            
            response = self.client.get('/home/')
            csrf_token = self.get_csrf_token(response)
            
            if csrf_token:
                headers = {
                    'X-CSRFToken': csrf_token,
                    'Content-Type': 'application/json'
                }
                
                self.client.post('/ml/predict-risk/', 
                               data=json.dumps(prediction_data),
                               headers=headers)
                time.sleep(1)


class ReadOnlyUser(HttpUser, DjangoUserMixin):
    """
    Simulates users who primarily browse and read data
    """
    wait_time = between(1, 5)  # Fast browsing
    weight = 3  # Higher weight - more of these users
    
    def on_start(self):
        self.login_user()
    
    @task(10)
    def browse_patients(self):
        """Browse patient lists and details"""
        self.client.get('/patient_list/')
        
        # Random page browsing
        page = random.randint(1, 5)
        self.client.get(f'/patient_list/?page={page}')
    
    @task(5)
    def view_reports(self):
        """View existing reports"""
        patient_id = random.randint(1, 50)
        self.client.get(f'/reports/report/{patient_id}/')
    
    @task(3)
    def browse_clinics(self):
        """Browse clinic information"""
        self.client.get('/clinics/')
    
    @task(2)
    def check_model_status(self):
        """Check ML model status"""
        self.client.get('/ml/model-status/')


class PatientManagementUser(HttpUser, DjangoUserMixin):
    """
    Specialized user for patient management workflow testing
    """
    wait_time = between(3, 7)
    
    def on_start(self):
        self.login_user()
    
    @task(5)
    def create_and_manage_patient(self):
        """Complete patient creation and management workflow"""
        # Create patient
        response = self.client.get('/create_patient/')
        csrf_token = self.get_csrf_token(response)
        
        if csrf_token:
            patient_data = {
                'name': fake.first_name(),
                'surname': fake.last_name(),
                'age': str(random.randint(0, 6)),
                'parent_id': str(fake.random_number(digits=13)),
                'parent_contact': fake.phone_number()[:12],
                'csrfmiddlewaretoken': csrf_token
            }
            self.client.post('/create_patient/', data=patient_data)
        
        # Browse patient list
        self.client.get('/patient_list/')
        
        # Search for patients
        search_terms = ['Test', 'Smith', 'John', 'Maria']
        self.client.get(f'/patient_list/?search={random.choice(search_terms)}')
    
    @task(3)
    def manage_existing_patients(self):
        """Browse existing patient records"""
        # Browse patient list with pagination
        self.client.get('/patient_list/')
        
        # Test pagination
        for page in range(1, 4):
            self.client.get(f'/patient_list/?page={page}')
        
        # Test search functionality
        search_terms = ['Test', 'Smith', 'John', 'Maria']
        search_term = random.choice(search_terms)
        self.client.get(f'/patient_list/?search={search_term}')


class AssessmentWorkflowUser(HttpUser, DjangoUserMixin):
    """
    Specialized user for assessment screening workflows
    """
    wait_time = between(4, 10)  # Assessments take longer
    
    def on_start(self):
        self.login_user()
    
    @task(3)
    def complete_dental_assessment(self):
        """Complete full dental screening assessment"""
        patient_id = random.randint(1, 100)
        
        response = self.client.get(f'/assessments/dental_screening/{patient_id}/')
        if response.status_code == 200:
            csrf_token = self.get_csrf_token(response)
            
            if csrf_token:
                # Comprehensive dental assessment data
                dental_data = {
                    'fluoride_use': random.choice(['daily', 'weekly', 'never']),
                    'brushing_frequency': random.choice(['twice_daily', 'once_daily', 'irregular']),
                    'last_dental_visit': fake.date_this_year().strftime('%Y-%m-%d'),
                    'dental_pain': random.choice(['yes', 'no']),
                    'gum_bleeding': random.choice(['yes', 'no']),
                    'tooth_sensitivity': random.choice(['yes', 'no']),
                    'csrfmiddlewaretoken': csrf_token
                }
                
                # Add detailed tooth examination data
                for tooth_num in range(11, 28):  # Full dental chart
                    dental_data[f'tooth_{tooth_num}'] = random.choice([
                        'healthy', 'decayed', 'missing', 'filled', 'crown', 'needs_treatment'
                    ])
                
                self.client.post(f'/assessments/dental_screening/{patient_id}/', data=dental_data)
    
    @task(3)
    def complete_dietary_assessment(self):
        """Complete dietary screening assessment"""
        patient_id = random.randint(1, 100)
        
        response = self.client.get(f'/assessments/dietary_screening/{patient_id}/')
        if response.status_code == 200:
            csrf_token = self.get_csrf_token(response)
            
            if csrf_token:
                dietary_data = {
                    'sugary_drinks': random.choice(['daily', 'weekly', 'rarely', 'never']),
                    'snacking_frequency': random.choice(['frequent', 'moderate', 'rare']),
                    'fruit_intake': random.choice(['high', 'moderate', 'low']),
                    'vegetable_intake': random.choice(['high', 'moderate', 'low']),
                    'water_consumption': random.choice(['adequate', 'inadequate']),
                    'meal_frequency': random.choice(['regular', 'irregular']),
                    'candy_consumption': random.choice(['daily', 'weekly', 'rarely', 'never']),
                    'csrfmiddlewaretoken': csrf_token
                }
                
                self.client.post(f'/assessments/dietary_screening/{patient_id}/', data=dietary_data)
    
    @task(2)
    def review_assessments(self):
        """Review assessment pages"""
        patient_id = random.randint(1, 100)
        
        # Check if dental screening page exists
        self.client.get(f'/assessments/dental_screening/{patient_id}/')
        
        # Check if dietary screening page exists  
        self.client.get(f'/assessments/dietary_screening/{patient_id}/')


class ReportGenerationUser(HttpUser, DjangoUserMixin):
    """
    Specialized user for report generation stress testing
    """
    wait_time = between(5, 12)  # Reports take time to generate
    
    def on_start(self):
        self.login_user()
    
    @task(4)
    def generate_patient_reports(self):
        """Generate various patient reports"""
        patient_id = random.randint(1, 100)
        
        # View report page
        self.client.get(f'/reports/report/{patient_id}/')
        
        # Generate PDF report (resource intensive)
        with self.client.get(f'/reports/{patient_id}/', catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.failure("Patient not found for report generation")
            else:
                response.failure(f"Report generation failed with status {response.status_code}")
    
    @task(2)
    def view_multiple_reports(self):
        """View multiple patient reports"""
        # Test multiple report views
        for patient_id in range(1, 6):
            self.client.get(f'/reports/report/{patient_id}/')
            time.sleep(1)  # Brief pause between reports


class MLPredictionUser(HttpUser, DjangoUserMixin):
    """
    Specialized user for ML prediction performance testing
    """
    wait_time = between(2, 6)  # ML predictions are quick but CPU intensive
    
    def on_start(self):
        self.login_user()
    
    @task(5)
    def perform_risk_predictions(self):
        """Perform ML risk predictions"""
        prediction_data = {
            'dental_features': {
                'dmft_score': random.randint(0, 10),
                'fluoride_use': random.choice([0, 1]),
                'brushing_frequency': random.randint(1, 3),
                'last_visit_months': random.randint(1, 24),
                'pain_reported': random.choice([0, 1])
            },
            'dietary_features': {
                'sugary_drinks': random.randint(0, 3),
                'snacking_frequency': random.randint(1, 4),
                'fruit_intake': random.randint(1, 3),
                'water_consumption': random.choice([0, 1])
            },
            'demographic_features': {
                'age': random.randint(0, 6),
                'gender': random.choice([0, 1]),
                'socioeconomic_status': random.randint(1, 5)
            }
        }
        
        response = self.client.get('/home/')
        csrf_token = self.get_csrf_token(response)
        
        if csrf_token:
            headers = {
                'X-CSRFToken': csrf_token,
                'Content-Type': 'application/json'
            }
            
            self.client.post('/ml/predict-risk/', 
                           data=json.dumps(prediction_data),
                           headers=headers)
    
    @task(2)
    def check_model_status(self):
        """Check ML model status"""
        # Only use endpoints that actually exist
        self.client.get('/ml/model-status/')
        
        # Test training template download
        self.client.get('/ml/training-template/')
    
    @task(1)
    def multiple_predictions(self):
        """Perform multiple ML predictions in sequence"""
        for _ in range(3):
            prediction_data = {
                'dental_features': {
                    'dmft_score': random.randint(0, 10),
                    'fluoride_use': random.choice([0, 1]),
                    'brushing_frequency': random.randint(1, 3)
                },
                'dietary_features': {
                    'sugary_drinks': random.randint(0, 3),
                    'snacking_frequency': random.randint(1, 4)
                }
            }
            
            response = self.client.get('/home/')
            csrf_token = self.get_csrf_token(response)
            
            if csrf_token:
                headers = {
                    'X-CSRFToken': csrf_token,
                    'Content-Type': 'application/json'
                }
                
                self.client.post('/ml/predict-risk/', 
                               data=json.dumps(prediction_data),
                               headers=headers)
                time.sleep(0.5)


class AuthenticationLoadUser(HttpUser, DjangoUserMixin):
    """
    Specialized user for authentication load testing
    """
    wait_time = between(1, 3)  # Quick authentication cycles
    
    @task(5)
    def login_logout_cycle(self):
        """Test repeated login/logout cycles"""
        # Test login
        success = self.login_user(
            username=f'testuser{random.randint(1, 100)}',
            password='testpass123'
        )
        
        if success:
            # Browse a few pages while logged in
            self.client.get('/home/')
            self.client.get('/patient_list/')
            
            # Logout
            self.client.get('/logout_user/')
    
    @task(2)
    def failed_login_attempts(self):
        """Test failed login attempts"""
        response = self.client.get('/login_user/')
        csrf_token = self.get_csrf_token(response)
        
        if csrf_token:
            # Intentionally wrong credentials
            login_data = {
                'username': 'wronguser',
                'password': 'wrongpass',
                'csrfmiddlewaretoken': csrf_token
            }
            
            self.client.post('/login_user/', data=login_data)
    
    @task(1)
    def concurrent_sessions(self):
        """Test concurrent session handling"""
        # Multiple rapid logins
        for i in range(3):
            self.login_user(username=f'user{i}', password='testpass123')
            self.client.get('/home/')


class MixedHealthcareUser(HttpUser, DjangoUserMixin):
    """
    Simulates realistic mixed healthcare workflow
    """
    wait_time = between(3, 8)
    
    def on_start(self):
        self.login_user()
    
    @task(3)
    def complete_patient_visit_workflow(self):
        """Simulate complete patient visit workflow"""
        # 1. Create or find patient
        response = self.client.get('/create_patient/')
        csrf_token = self.get_csrf_token(response)
        
        patient_id = random.randint(1, 100)
        
        if csrf_token and random.choice([True, False]):  # 50% create new patient
            patient_data = {
                'name': fake.first_name(),
                'surname': fake.last_name(),
                'age': str(random.randint(0, 6)),
                'parent_id': str(fake.random_number(digits=13)),
                'parent_contact': fake.phone_number()[:12],
                'csrfmiddlewaretoken': csrf_token
            }
            self.client.post('/create_patient/', data=patient_data)
        else:
            # Browse existing patients
            self.client.get('/patient_list/')
        
        # 2. Perform assessments
        # Dental screening
        response = self.client.get(f'/assessments/dental_screening/{patient_id}/')
        if response.status_code == 200:
            csrf_token = self.get_csrf_token(response)
            if csrf_token:
                dental_data = {
                    'fluoride_use': random.choice(['daily', 'weekly', 'never']),
                    'brushing_frequency': random.choice(['twice_daily', 'once_daily', 'irregular']),
                    'dental_pain': random.choice(['yes', 'no']),
                    'csrfmiddlewaretoken': csrf_token
                }
                self.client.post(f'/assessments/dental_screening/{patient_id}/', data=dental_data)
        
        # 3. Generate risk prediction
        prediction_data = {
            'dental_features': {
                'dmft_score': random.randint(0, 10),
                'fluoride_use': random.choice([0, 1]),
                'brushing_frequency': random.randint(1, 3)
            },
            'dietary_features': {
                'sugary_drinks': random.randint(0, 3),
                'snacking_frequency': random.randint(1, 4)
            }
        }
        
        response = self.client.get('/home/')
        csrf_token = self.get_csrf_token(response)
        
        if csrf_token:
            headers = {
                'X-CSRFToken': csrf_token,
                'Content-Type': 'application/json'
            }
            self.client.post('/ml/predict-risk/', 
                           data=json.dumps(prediction_data),
                           headers=headers)
        
        # 4. Generate patient report
        self.client.get(f'/reports/report/{patient_id}/')
        self.client.get(f'/reports/{patient_id}/')
    
    @task(2)
    def administrative_tasks(self):
        """Perform administrative tasks"""
        # Browse clinic information
        self.client.get('/clinics/')
        
        # Check system status
        self.client.get('/ml/model-status/')
        
        # View profile
        self.client.get('/profile_view/')
        
        # Browse patient list
        self.client.get('/patient_list/')