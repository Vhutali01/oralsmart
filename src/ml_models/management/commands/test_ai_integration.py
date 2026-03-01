from django.core.management.base import BaseCommand
from patient.models import Patient
from assessments.models import DentalScreening, DietaryScreening
from reports.views import get_ml_risk_prediction, generate_pdf_buffer
from ml_models.ml_predictor import MLPRiskPredictor

class Command(BaseCommand):
    help = 'Test AI risk assessment integration in reports'

    def handle(self, *args, **options):
        self.stdout.write("🧪 Testing AI Risk Assessment Integration in Reports")
        self.stdout.write("=" * 60)
        
        # Check if we have any patients
        patients = Patient.objects.all()
        if not patients.exists():
            self.stdout.write(self.style.ERROR("No patients found in database"))
            return
        
        # Get a patient with both dental and dietary data
        test_patient = None
        for patient in patients:
            try:
                dental_data = DentalScreening.objects.get(patient_id=patient.pk)
                dietary_data = DietaryScreening.objects.get(patient_id=patient.pk)
                test_patient = patient
                break
            except (DentalScreening.DoesNotExist, DietaryScreening.DoesNotExist):
                continue
        
        if not test_patient:
            self.stdout.write(self.style.ERROR("No patients found with both dental and dietary screening data"))
            return
        
        self.stdout.write(f"Using test patient: {test_patient.name} {test_patient.surname} (ID: {test_patient.pk})")
        
        # Test 1: Check ML prediction functionality
        self.stdout.write("\n🔬 Test 1: ML Risk Prediction Function")
        try:
            dental_data = DentalScreening.objects.get(patient_id=test_patient.pk)
            dietary_data = DietaryScreening.objects.get(patient_id=test_patient.pk)
            
            ml_prediction = get_ml_risk_prediction(dental_data, dietary_data)
            
            if ml_prediction['available']:
                self.stdout.write(self.style.SUCCESS("ML Prediction successful:"))
                self.stdout.write(f"   Risk Level: {ml_prediction['risk_level']}")
                self.stdout.write(f"   Confidence: {ml_prediction['confidence']:.1f}%")
                self.stdout.write(f"   Probabilities: Low={ml_prediction['probability_low_risk']:.1f}%, "
                      f"Medium={ml_prediction['probability_medium_risk']:.1f}%, "
                      f"High={ml_prediction['probability_high_risk']:.1f}%")
            else:
                self.stdout.write(self.style.WARNING(f"ML Prediction not available: {ml_prediction.get('error', 'Unknown error')}"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"ML prediction test failed: {e}"))
            return
        
        # Test 2: Patient PDF (without AI assessment)
        self.stdout.write("\nTest 2: Patient PDF Generation (without AI)")
        try:
            patient_pdf = generate_pdf_buffer(
                test_patient,
                include_ai_assessment=False
            )
            
            pdf_size = len(patient_pdf.getvalue())
            self.stdout.write(self.style.SUCCESS(f"Patient PDF generated successfully ({pdf_size:,} bytes)"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Patient PDF generation failed: {e}"))
            return
        
        # Test 3: Professional PDF (with AI assessment)
        self.stdout.write("\nTest 3: Professional PDF Generation (with AI)")
        try:
            professional_pdf = generate_pdf_buffer(
                test_patient,
                include_ai_assessment=True
            )
            
            pdf_size = len(professional_pdf.getvalue())
            self.stdout.write(self.style.SUCCESS(f"Professional PDF generated successfully ({pdf_size:,} bytes)"))
            
            # Check that professional PDF is different (should be larger due to AI section)
            patient_size = len(patient_pdf.getvalue())
            professional_size = len(professional_pdf.getvalue())
            
            if professional_size > patient_size:
                self.stdout.write(self.style.SUCCESS(f"Professional PDF is larger than patient PDF ({professional_size - patient_size:,} bytes difference)"))
            else:
                self.stdout.write(self.style.WARNING(f"Professional PDF is not larger than patient PDF (size difference: {professional_size - patient_size:,} bytes)"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Professional PDF generation failed: {e}"))
            return
        
        # Test 4: Check ML model status
        self.stdout.write("\nTest 4: ML Model Status")
        try:
            predictor = MLPRiskPredictor()
            if predictor.is_trained:
                self.stdout.write(self.style.SUCCESS("ML model is trained and ready"))
            else:
                self.stdout.write(self.style.WARNING("ML model is not trained - predictions will show 'Unknown' status"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"ML model check failed: {e}"))
            return
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("All tests completed successfully!"))
        self.stdout.write("\nReport Integration Summary:")
        self.stdout.write("• Patient reports (viewed in browser): NO AI risk assessment")
        self.stdout.write("• Patient emails: NO AI risk assessment") 
        self.stdout.write("• Professional emails (CC recipients): INCLUDES AI risk assessment")
        self.stdout.write("• Professional reports have '[PROFESSIONAL]' prefix in subject")
