from django.shortcuts import render
from patient.models import Patient
from django.http import FileResponse, HttpResponse
import io
from datetime import datetime
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from assessments.models import DentalScreening, DietaryScreening
from django.views.decorators.clickjacking import xframe_options_exempt
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from userprofile.models import Profile
import logging
import os
from django.contrib.auth.decorators import login_required
import logging
import os
import io

# Import ML predictor
from ml_models.ml_predictor import MLPRiskPredictor

logger = logging.getLogger(__name__)


class ProfessionalRecommendationService:
    """Service class to handle professional recommendations logic"""
    
    # Centralized professional definitions - using exactly the professions you specified
    PROFESSIONALS = {
        'medical_doctor': 'Medical Doctor',
        'dentist': 'Dentist',
        'psychologist': 'Psychologist',
        'physiotherapist': 'Physiotherapist',
        'radiographer': 'Radiographer',
        'occupational_therapist': 'Occupational Therapist',
        'biokineticist': 'Biokineticist',
        'clinical_technologist': 'Clinical Technologist',
        'dietitian': 'Dietitian',
        'audiologist': 'Audiologist',
        'optometrist': 'Optometrist',
        'emergency_care_practitioner': 'Emergency Care Practitioner',
        'registered_nurse': 'Registered Nurse',
        'enrolled_nurse': 'Enrolled Nurse',
        'nursing_assistant': 'Nursing Assistant',
        'midwife': 'Midwife',
        # Additional dental specialists that may be used in recommendations
        'orthodontist': 'Orthodontist',
        'oral_surgeon': 'Oral Surgeon',
        'periodontist': 'Periodontist',
        'endodontist': 'Endodontist',
        'pediatric_dentist': 'Pediatric Dentist',
        'prosthodontist': 'Prosthodontist',
        'oral_pathologist': 'Oral Pathologist',
        'pediatrician': 'Pediatrician'
    }
    
    # Define recommendation rules based on user profession
    RECOMMENDATION_RULES = {
        'dentist': {
            'exclude': ['dentist'],
            'primary': ['orthodontist', 'oral_surgeon', 'periodontist', 'endodontist', 'pediatric_dentist', 'medical_doctor']
        },
        'medical_doctor': {
            'include': ['dentist', 'pediatric_dentist', 'orthodontist', 'oral_surgeon']
        },
        'registered_nurse': {
            'exclude': ['registered_nurse'],
            'primary': ['dentist', 'medical_doctor']
        },
        'enrolled_nurse': {
            'exclude': ['enrolled_nurse'],
            'primary': ['dentist', 'medical_doctor']
        },
        'nursing_assistant': {
            'exclude': ['nursing_assistant'],
            'primary': ['dentist', 'medical_doctor']
        },
        'default': {
            'include': ['dentist', 'pediatric_dentist', 'orthodontist', 'medical_doctor']
        }
    }
    
    @classmethod
    def get_recommended_professionals(cls, user_profession=None):
        """Get list of recommended professionals based on user's profession"""
        if not user_profession or user_profession not in cls.RECOMMENDATION_RULES:
            rule = cls.RECOMMENDATION_RULES['default']
        else:
            rule = cls.RECOMMENDATION_RULES[user_profession]
        
        if 'include' in rule:
            # Use specific include list
            professional_codes = rule['include']
        else:
            # Start with your specified list and apply exclusions
            base_professionals = [
                'medical_doctor', 'dentist', 'psychologist', 'physiotherapist',
                'radiographer', 'occupational_therapist', 'biokineticist',
                'clinical_technologist', 'dietitian', 'audiologist', 'optometrist',
                'emergency_care_practitioner', 'registered_nurse', 'enrolled_nurse',
                'nursing_assistant', 'midwife'
            ]
            
            professional_codes = base_professionals.copy()
            if 'exclude' in rule:
                professional_codes = [p for p in professional_codes if p not in rule['exclude']]
            
            # Apply primary recommendations if specified
            if 'primary' in rule:
                primary = [p for p in rule['primary'] if p in cls.PROFESSIONALS]
                others = [p for p in professional_codes if p not in primary]
                professional_codes = primary + others
        
        # Convert to tuple format for compatibility with existing template
        return [(code, cls.PROFESSIONALS[code]) for code in professional_codes if code in cls.PROFESSIONALS]
    
    @classmethod
    def get_professional_display_name(cls, code):
        """Get display name for a professional code"""
        return cls.PROFESSIONALS.get(code, code.replace('_', ' ').title())
    
    @classmethod
    def get_current_recommendation(cls, session):
        """Get current recommendation from session"""
        code = session.get('recommended_professional', '')
        if code:
            return {
                'code': code,
                'name': cls.get_professional_display_name(code)
            }
        return None

def get_ml_risk_prediction(dental_data, dietary_data):
    """Get ML risk prediction for a patient"""
    try:
        # Initialize ML predictor
        predictor = MLPRiskPredictor()
        
        # Check if model is trained
        if not predictor.is_trained:
            return {
                'risk_level': 'Unknown',
                'confidence': 0.0,
                'probability_low_risk': 0.0,
                'probability_medium_risk': 0.0,
                'probability_high_risk': 0.0,
                'error': 'ML model not trained',
                'available': False
            }
        
        # Get prediction
        prediction = predictor.predict_risk(dental_data, dietary_data)
        prediction['available'] = True
        prediction['error'] = None
        
        return prediction
        
    except Exception as e:
        logger.error(f"ML prediction error: {e}")
        return {
            'risk_level': 'Error',
            'confidence': 0.0,
            'probability_low_risk': 0.0,
            'probability_medium_risk': 0.0,
            'probability_high_risk': 0.0,
            'error': str(e),
            'available': False
        }

def get_risk_color(risk_level):
    """Get color for risk level"""
    colors_map = {
        'low': '#28a745',      # Green
        'medium': '#ffc107',   # Yellow/Orange
        'high': '#dc3545',     # Red
        'unknown': '#6c757d',  # Gray
        'error': '#6c757d'     # Gray
    }
    return colors_map.get(risk_level.lower(), '#6c757d')

class CustomPageTemplate:
    """Custom page template with blue borders and logo"""
    
    def __init__(self, canvas_obj, doc):
        self.canvas = canvas_obj
        self.doc = doc
        
    def draw_page_frame(self):
        """Draw blue border and add logo/header to each page"""
        # Define blue color
        blue_color = HexColor('#2E86AB')  # Professional blue
        light_blue = HexColor('#A8DADC')  # Light blue for accents
        
        # Get page dimensions
        width, height = letter
        
        # Draw outer border (blue frame)
        self.canvas.setStrokeColor(blue_color)
        self.canvas.setLineWidth(3)
        self.canvas.rect(36, 36, width - 72, height - 72)  # 1 inch margin
        
        # Draw inner decorative border
        self.canvas.setStrokeColor(light_blue)
        self.canvas.setLineWidth(1)
        self.canvas.rect(45, 45, width - 90, height - 90)
        
        # Add header background
        self.canvas.setFillColor(light_blue)
        self.canvas.rect(45, height - 120, width - 90, 30, fill=1, stroke=0)
        
        # Add logo (if exists)
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'Logo2.png')
        if os.path.exists(logo_path):
            try:
                # Draw logo in top-left corner with better size and positioning
                self.canvas.drawImage(logo_path, 60, height - 115, width=100, height=30, 
                                    preserveAspectRatio=True, mask='auto')
            except Exception:
                # Add text fallback if logo can't be loaded
                self.canvas.setFillColor(blue_color)
                self.canvas.setFont('Helvetica-Bold', 12)
                self.canvas.drawString(60, height - 105, "OralSmart")
        
        # Add "OralSmart" text in header
        self.canvas.setFillColor(blue_color)
        self.canvas.setFont('Helvetica-Bold', 16)
        self.canvas.drawString(180, height - 105, "OralSmart Dental Care System")
        
        # Add current date in top-right corner
        current_date = datetime.now().strftime("%B %d, %Y")
        self.canvas.setFillColor(blue_color)
        self.canvas.setFont('Helvetica', 10)
        date_width = self.canvas.stringWidth(f"Generated: {current_date}")
        self.canvas.drawString(width - 90 - date_width, height - 105, f"Generated: {current_date}")
        
        # Add footer with page number
        self.canvas.setFillColor(blue_color)
        self.canvas.setFont('Helvetica', 9)
        footer_text = f"Page {self.canvas.getPageNumber()}"
        footer_width = self.canvas.stringWidth(footer_text)
        self.canvas.drawString((width - footer_width) / 2, 50, footer_text)
        
        # Reset colors for content
        self.canvas.setFillColor(colors.black)
        self.canvas.setStrokeColor(colors.black)

@login_required
def view_report(request, patient_id):

    patient = Patient.objects.get(id=patient_id)

    try:
        dental_data = DentalScreening.objects.get(patient_id=patient_id)
    except DentalScreening.DoesNotExist:
        dental_data = None
        
    try:
        dietary_data = DietaryScreening.objects.get(patient_id=patient_id)
    except DietaryScreening.DoesNotExist:
        dietary_data = None

    ml_prediction = get_ml_risk_prediction(dental_data=dental_data, dietary_data=dietary_data)
    risk_color = get_risk_color(ml_prediction['risk_level'])
    
    # Get recommended professionals using the service
    current_user_profile = getattr(request.user, 'profile', None)
    user_profession = current_user_profile.profession if current_user_profile else None
    
    recommended_professionals = ProfessionalRecommendationService.get_recommended_professionals(user_profession)
    current_recommendation = ProfessionalRecommendationService.get_current_recommendation(request.session)
    
    # Debug logging
    logger.info(f"Session data: {dict(request.session.items())}")
    logger.info(f"Current recommendation: {current_recommendation}")

    return render(
        request, 
        "reports/report.html", 
        {
            "patient_id": patient_id,
            "patient": patient,
            "dental_screening": dental_data,
            "dietary_screening": dietary_data,
            'show_navbar': True,
            'risk_prediction': ml_prediction,
            'risk_color': risk_color,
            'recommended_professionals': recommended_professionals,
            'current_recommendation': current_recommendation['name'] if current_recommendation else None,
            'current_recommendation_code': current_recommendation['code'] if current_recommendation else '',
        }
    )

@login_required
@xframe_options_exempt
def generate_pdf(request, patient_id):
    """
    Generates a PDF report for a given patient, including dental and dietary screening data.
    This view handles both POST and GET requests:
    - POST: Saves the selected report sections to the session (no PDF generated).
    - GET: Generates and returns a PDF report based on the last selected sections.
    The PDF includes:
    - Patient information
    - Health professional information (if available)
    - Completed screening types (dental, dietary)
    - Detailed screening results for selected sections
    - DMFT (Decayed, Missing, Filled Teeth) assessment with tooth-level details
    - Dietary screening results
    If the patient does not exist or no screening data is available, a PDF with an error message is returned.
    Args:
        request (HttpRequest): The HTTP request object (supports GET and POST).
        patient_id (int or str): The primary key of the patient for whom the report is generated.
    Returns:
        FileResponse: A Django FileResponse containing the generated PDF, or an error PDF if data is missing.
    Notes:
        - The function uses ReportLab for PDF generation.
        - Only authenticated users' professional information is included.
        - Section selection is managed via session and POST data.
        - The report is styled with a blue color scheme and includes tables for clarity.
    """
    
    try:
        patient = Patient.objects.get(pk=patient_id)
    except Patient.DoesNotExist:
        # Return a PDF with error message for missing patient
        # This ensures the iframe always gets PDF content, not HTML
        from reportlab.pdfgen import canvas
        
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, 750, "Error: Patient Not Found")
        c.setFont("Helvetica", 12)
        c.drawString(100, 720, f"No patient found with ID: {patient_id}")
        c.drawString(100, 700, "Please check the patient ID and try again.")
        
        c.showPage()
        c.save()
        buf.seek(0)
        
        return FileResponse(buf, as_attachment=False, filename="error.pdf", content_type='application/pdf')

    if request.method == "POST":
        # Save recommended professional selection
        recommended_professional = request.POST.get('recommended_professional', '')
        logger.info(f"POST received - recommended_professional: '{recommended_professional}'")
        request.session['recommended_professional'] = recommended_professional
        request.session.save()  # Explicitly save the session
        logger.info(f"Session after save: {dict(request.session.items())}")
        
        return HttpResponse(status=204)
    else:
        # For GET, generate PDF with all available sections
        try:
            dental_data = DentalScreening.objects.get(patient_id=patient_id)
        except DentalScreening.DoesNotExist:
            dental_data = None
            
        try:
            dietary_data = DietaryScreening.objects.get(patient_id=patient_id)
        except DietaryScreening.DoesNotExist:
            dietary_data = None
            
        # Check if we have at least one type of screening data
        if not dental_data and not dietary_data:
            # Return a PDF with error message instead of HTML
            # This prevents the iframe from displaying a nested HTML page
            from reportlab.pdfgen import canvas
            
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=letter)
            
            # Add error message to PDF
            c.setFont("Helvetica-Bold", 16)
            c.drawString(100, 750, "Error: No Screening Data Found")
            c.setFont("Helvetica", 12)
            c.drawString(100, 720, f"No screening data found for patient ID: {patient_id}")
            c.drawString(100, 700, "Please complete at least one screening before generating a report.")
            c.drawString(100, 680, "Available screenings: Dental Screening, Dietary Screening")
            
            c.showPage()
            c.save()
            buf.seek(0)
            
            return FileResponse(buf, as_attachment=False, filename="error.pdf", content_type='application/pdf')
        
        buf = io.BytesIO()
        
        # Custom canvas class to add page decorations
        from reportlab.pdfgen.canvas import Canvas
        
        class CustomCanvas(Canvas):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.page_template = None
                
            def showPage(self):
                if not self.page_template:
                    self.page_template = CustomPageTemplate(self, None)
                self.page_template.draw_page_frame()
                super().showPage()
        
        #Create document template with custom canvas
        doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=90, leftMargin=90, 
                              topMargin=140, bottomMargin=80, canvasmaker=CustomCanvas)
        
        #Get styles
        styles = getSampleStyleSheet()
        
        # Define blue color scheme
        blue_color = HexColor('#2E86AB')
        light_blue = HexColor('#A8DADC')
        
        #Custom styles with blue accents
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=20,
            spaceBefore=10,
            alignment=1,  #Center alignment
            textColor=blue_color,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=12,
            textColor=blue_color,
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=light_blue,
            borderPadding=6,
            backColor=HexColor('#F8F9FA')
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            leftIndent=12,
            allowWidows=1,
            allowOrphans=1
        )
        
        #Build story (content)
        story = []
        
        #Title with date
        current_date = datetime.now().strftime("%B %d, %Y")
        story.append(Paragraph("OralSmart Dental Screening Report", title_style))
        story.append(Paragraph(f"Report Generated: {current_date}", ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=12,
            alignment=1,
            textColor=blue_color,
            spaceAfter=20
        )))
        
        #Patient Info with styled box
        story.append(Paragraph("Patient Information", heading_style))
        
        # Create patient info table for better layout
        patient_data = [
            [Paragraph(f"<b>Patient Name:</b> {patient.name}", normal_style), 
             Paragraph(f"<b>Patient Surname:</b> {patient.surname}", normal_style)],
            [Paragraph(f"<b>Patient Parent ID:</b> {patient.parent_id}", normal_style), 
             Paragraph(f"<b>Parent Contact:</b> {patient.parent_contact}", normal_style)]
        ]
        
        patient_table = Table(patient_data, colWidths=[3*inch, 3*inch])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#F0F8FF')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, light_blue),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(patient_table)
        story.append(Spacer(1, 12))
        
        # Health Professional Information
        if request.user.is_authenticated:
            try:
                health_professional = request.user
                profile = Profile.objects.get(user=health_professional)
                profession_display = dict(Profile.PROFESSIONS).get(profile.profession, profile.profession.replace('_', ' ').title())
                
                # Get recommended professional from session
                recommended_professional = request.session.get('recommended_professional', '')
                
                story.append(Paragraph("Health Professional Information", heading_style))
                
                professional_data = [
                    [Paragraph(f"<b>Name:</b> {health_professional.first_name}", normal_style), 
                     Paragraph(f"<b>Surname:</b> {health_professional.last_name}", normal_style)],
                    [Paragraph(f"<b>Profession:</b> {profession_display}", normal_style), 
                     Paragraph(f"<b>Registration No:</b> {profile.reg_num}", normal_style)]
                ]
                
                # Add recommended professional if selected
                if recommended_professional:
                    recommended_name = ProfessionalRecommendationService.get_professional_display_name(recommended_professional)
                    professional_data.append([
                        Paragraph(f"<b>Recommended Referral:</b> {recommended_name}", normal_style),
                        Paragraph("", normal_style)  # Empty cell for layout
                    ])
                
                professional_table = Table(professional_data, colWidths=[3*inch, 3*inch])
                professional_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#E8F4FD')),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, blue_color),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ]))
                story.append(professional_table)
                story.append(Spacer(1, 12))
                
            except Profile.DoesNotExist:
                # If no profile exists, show basic user information
                health_professional = request.user
                story.append(Paragraph("Health Professional Information", heading_style))
                professional_info = f"<b>Health Professional:</b> {health_professional.first_name} {health_professional.last_name}"
                if health_professional.email:
                    professional_info += f" ({health_professional.email})"
                
                # Add recommended professional if selected
                recommended_professional = request.session.get('recommended_professional', '')
                if recommended_professional:
                    recommended_name = ProfessionalRecommendationService.get_professional_display_name(recommended_professional)
                    professional_info += f"<br/><b>Recommended Referral:</b> {recommended_name}"
                
                story.append(Paragraph(professional_info, normal_style))
                story.append(Spacer(1, 12))
            except Exception:
                # If other error, skip this section
                pass
        
        
        # Add screening availability info with styled display
        available_screenings = []
        if dental_data:
            available_screenings.append("✓ Dental Screening")
        if dietary_data:
            available_screenings.append("✓ Dietary Screening")
        
        story.append(Paragraph("Available Screening Data", heading_style))
        
        # Create screening status table
        screening_data = [[Paragraph(f"<b>Completed Screenings:</b> {', '.join(available_screenings)}", normal_style)]]
        screening_table = Table(screening_data, colWidths=[6*inch])
        screening_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#E8F4FD')),
            ('TEXTCOLOR', (0, 0), (-1, -1), blue_color),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, blue_color),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(screening_table)
        story.append(Spacer(1, 12))
        
        # Note: AI Risk Assessment is only included in professional reports sent to healthcare providers
        # The patient-facing report does not include AI risk classification for privacy and clarity
        
        # Include dental screening sections if dental data exists
        if dental_data:
            #Section 1: Social/Behavioural/Medical Risk Factors (Dental)
            story.append(Paragraph("Social/Behavioural/Medical Risk Factors (Dental Screening)", heading_style))
            
            section1_data = [
                f"<b>Caregiver treatment:</b> {dental_data.caregiver_treatment}",
                f"<b>South African Citizen:</b> {dental_data.sa_citizen}",
                f"<b>Special needs:</b> {dental_data.special_needs}"
            ]
            
            # Add each item as a paragraph for proper bold rendering
            for item in section1_data:
                story.append(Paragraph(item, normal_style))
            story.append(Spacer(1, 12))

            #Section 2: Clinical Risk Factors (Dental)
            story.append(Paragraph("Clinical Risk Factors (Dental Screening)", heading_style))
            
            section2_data = [
                f"<b>Plaque:</b> {dental_data.plaque}",
                f"<b>Dry mouth:</b> {dental_data.dry_mouth}",
                f"<b>Enamel defects:</b> {dental_data.enamel_defects}",
                f"<b>Intra-oral appliance:</b> {dental_data.appliance}"
            ]
            
            # Add each item as a paragraph for proper bold rendering
            for item in section2_data:
                story.append(Paragraph(item, normal_style))
            story.append(Spacer(1, 12))

            #Section 3: Protective Factors (Dental)
            story.append(Paragraph("Protective Factors (Dental Screening)", heading_style))
            
            section3_data = [
                f"<b>Fluoride water:</b> {dental_data.fluoride_water}",
                f"<b>Fluoride toothpaste:</b> {dental_data.fluoride_toothpaste}",
                f"<b>Topical fluoride:</b> {dental_data.topical_fluoride}",
                f"<b>Regular checkups:</b> {dental_data.regular_checkups}"
            ]
        
            # Add each item as a paragraph for proper bold rendering
            for item in section3_data:
                story.append(Paragraph(item, normal_style))
            story.append(Spacer(1, 12))

            #Section 4: Disease Indicators (Dental)
            story.append(Paragraph("Disease Indicators (Dental Screening)", heading_style))
            
            section4_data = [
                f"<b>Sealed pits:</b> {dental_data.sealed_pits}",
                f"<b>Restorative procedures:</b> {dental_data.restorative_procedures}",
                f"<b>Enamel change:</b> {dental_data.enamel_change}",
                f"<b>Dentin discoloration:</b> {dental_data.dentin_discoloration}",
                f"<b>White spot lesions:</b> {dental_data.white_spot_lesions}",
                f"<b>Cavitated lesions:</b> {dental_data.cavitated_lesions}",
                f"<b>Multiple restorations:</b> {dental_data.multiple_restorations}",
                f"<b>Missing teeth:</b> {dental_data.missing_teeth}"
            ]
            
            # Add each item as a paragraph for proper bold rendering
            for item in section4_data:
                story.append(Paragraph(item, normal_style))
            story.append(Spacer(1, 12))

            #Section 5: DMFT Assessment (Dental only)
            tooth_names = {
                #Permanent Teeth
                "tooth_18": "Upper Right Third Molar (Wisdom Tooth)",
                "tooth_17": "Upper Right Second Molar",
                "tooth_16": "Upper Right First Molar",
                "tooth_15": "Upper Right Second Premolar",
                "tooth_14": "Upper Right First Premolar",
                "tooth_13": "Upper Right Canine",
                "tooth_12": "Upper Right Lateral Incisor",
                "tooth_11": "Upper Right Central Incisor",
                "tooth_21": "Upper Left Central Incisor",
                "tooth_22": "Upper Left Lateral Incisor",
                "tooth_23": "Upper Left Canine",
                "tooth_24": "Upper Left First Premolar",
                "tooth_25": "Upper Left Second Premolar",
                "tooth_26": "Upper Left First Molar",
                "tooth_27": "Upper Left Second Molar",
                "tooth_28": "Upper Left Third Molar (Wisdom Tooth)",
                "tooth_48": "Lower Right Third Molar (Wisdom Tooth)",
                "tooth_47": "Lower Right Second Molar",
                "tooth_46": "Lower Right First Molar",
                "tooth_45": "Lower Right Second Premolar",
                "tooth_44": "Lower Right First Premolar",
                "tooth_43": "Lower Right Canine",
                "tooth_42": "Lower Right Lateral Incisor",
                "tooth_41": "Lower Right Central Incisor",
                "tooth_31": "Lower Left Central Incisor",
                "tooth_32": "Lower Left Lateral Incisor",
                "tooth_33": "Lower Left Canine",
                "tooth_34": "Lower Left First Premolar",
                "tooth_35": "Lower Left Second Premolar",
                "tooth_36": "Lower Left First Molar",
                "tooth_37": "Lower Left Second Molar",
                "tooth_38": "Lower Left Third Molar (Wisdom Tooth)",
                #Primary Teeth
                "tooth_55": "Upper Right Second Primary Molar",
                "tooth_54": "Upper Right First Primary Molar",
                "tooth_53": "Upper Right Primary Canine",
                "tooth_52": "Upper Right Lateral Primary Incisor",
                "tooth_51": "Upper Right Central Primary Incisor",
                "tooth_61": "Upper Left Central Primary Incisor",
                "tooth_62": "Upper Left Lateral Primary Incisor",
                "tooth_63": "Upper Left Primary Canine",
                "tooth_64": "Upper Left First Primary Molar",
                "tooth_65": "Upper Left Second Primary Molar",
                "tooth_85": "Lower Right Second Primary Molar",
                "tooth_84": "Lower Right First Primary Molar",
                "tooth_83": "Lower Right Primary Canine",
                "tooth_82": "Lower Right Lateral Primary Incisor",
                "tooth_81": "Lower Right Central Primary Incisor",
                "tooth_71": "Lower Left Central Primary Incisor",
                "tooth_72": "Lower Left Lateral Primary Incisor",
                "tooth_73": "Lower Left Primary Canine",
                "tooth_74": "Lower Left First Primary Molar",
                "tooth_75": "Lower Left Second Primary Molar"
            }

            story.append(Paragraph("DMFT Assessment (Dental Screening)", heading_style))
            
            #add a new page for tooth data
            story.append(PageBreak())
            story.append(Paragraph("Tooth Assessment", heading_style))

            for code, status in dental_data.teeth_data.items():
                if status:
                    text = f"<b>{tooth_names.get(code, 'Unknown Tooth')} ({code}):</b> {status}"
                    story.append(Paragraph(text, normal_style))
                elif status == "":
                    text = f"<b>{tooth_names.get(code, 'Unknown Tooth')} ({code}):</b> No Issue (Assumed)"
                    story.append(Paragraph(text, normal_style))
                        
        # Include dietary screening sections if dietary data exists
        if dietary_data:
            story.append(Paragraph("Dietary Screening Results", heading_style))
            
            dietary_sections = [
                ("Sweet/Sugary Foods", dietary_data.sweet_sugary_foods, dietary_data.sweet_sugary_foods_daily, dietary_data.sweet_sugary_foods_weekly),
                ("Cold Drinks and Juices", dietary_data.cold_drinks_juices, dietary_data.cold_drinks_juices_daily, dietary_data.cold_drinks_juices_weekly),
                ("Take-aways and Processed Foods", dietary_data.takeaways_processed_foods, dietary_data.takeaways_processed_foods_daily, dietary_data.takeaways_processed_foods_weekly),
                ("Salty Snacks", dietary_data.salty_snacks, dietary_data.salty_snacks_daily, dietary_data.salty_snacks_weekly),
                ("Spreads", dietary_data.spreads, dietary_data.spreads_daily, dietary_data.spreads_weekly)
            ]
            
            for section_name, consumes, daily, weekly in dietary_sections:
                story.append(Paragraph(f"<b>{section_name}</b>", normal_style))
                story.append(Paragraph(f"<b>Consumes:</b> {consumes}", normal_style))
                if daily:
                    story.append(Paragraph(f"<b>Daily frequency:</b> {daily}", normal_style))
                if weekly:
                    story.append(Paragraph(f"<b>Weekly frequency:</b> {weekly}", normal_style))
                story.append(Spacer(1, 8))

        #build PDF
        doc.build(story)
        buf.seek(0)

        filename = f"report_{patient.name}_{patient.surname}_{patient_id}.pdf"
        return FileResponse(buf, as_attachment=False, filename=filename, content_type='application/pdf')

@login_required
def send_report_email(request, patient_id):
    """Send report via email to user and CC health professionals"""
    if request.method != 'POST':
        return HttpResponse('Method not allowed', status=405)
    
    try:
        patient = Patient.objects.get(pk=patient_id)
    except Patient.DoesNotExist:
        return HttpResponse('Patient not found', status=404)
    
    # Get form data
    recipient_email = request.POST.get('recipient_email')
    cc_emails = request.POST.get('cc_emails', '').strip()
    subject = request.POST.get('subject', f'OralSmart Dental Report - {patient.name} {patient.surname}')
    message_text = request.POST.get('message', '')
    
    if not recipient_email:
        return HttpResponse('Recipient email is required', status=400)
    
    # Parse CC emails (comma-separated)
    cc_list = []
    if cc_emails:
        cc_list = [email.strip() for email in cc_emails.split(',') if email.strip()]
    
    try:
        # Generate PDF report for patient (without AI risk assessment)
        recommended_professional = request.session.get('recommended_professional', '')
        pdf_buffer_patient = generate_pdf_buffer(patient, include_ai_assessment=False, user=request.user, recommended_professional=recommended_professional)
        
        # Create email context
        recommended_professional = request.session.get('recommended_professional', '')
        recommended_professional_name = ''
        if recommended_professional:
            recommended_professional_name = ProfessionalRecommendationService.get_professional_display_name(recommended_professional)
        
        email_context = {
            'patient_name': f'{patient.name} {patient.surname}',
            'patient_id': patient_id,
            'message': message_text,
            'sections_included': 'All available screening data',
            'sender_name': request.user.get_full_name() if request.user.is_authenticated else 'OralSmart Team',
            'recommended_professional': recommended_professional_name
        }
        
        # Render email template
        html_message = render_to_string('reports/email_template.html', email_context)
        plain_message = strip_tags(html_message)
        
        # Create email for patient (without AI assessment)
        patient_email = EmailMessage(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        
        # Attach patient PDF (without AI assessment)
        patient_filename = f"dental_report_{patient.name}_{patient.surname}_{patient_id}.pdf"
        patient_email.attach(patient_filename, pdf_buffer_patient.getvalue(), 'application/pdf')
        
        # Send patient email
        patient_email.send()
        logger.info(f"Patient report email sent for patient {patient_id} to {recipient_email}")
        
        # Send separate email to health professionals with AI assessment if CC recipients exist
        if cc_list:
            # Generate PDF report for professionals (with AI risk assessment)
            pdf_buffer_professional = generate_pdf_buffer(patient, include_ai_assessment=True, user=request.user, recommended_professional=recommended_professional)
            
            # Create email for health professionals (with AI assessment)
            professional_email = EmailMessage(
                subject=f"[PROFESSIONAL] {subject}",
                body=plain_message + "\n\nNote: This professional version includes AI risk assessment for clinical decision support.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=cc_list,
            )
            
            # Attach professional PDF (with AI assessment)
            professional_filename = f"dental_report_professional_{patient.name}_{patient.surname}_{patient_id}.pdf"
            professional_email.attach(professional_filename, pdf_buffer_professional.getvalue(), 'application/pdf')
            
            # Send professional email
            professional_email.send()
            logger.info(f"Professional report email sent for patient {patient_id} to CC recipients: {', '.join(cc_list)}")
        
        # Clear the recommended professional from session after successful email sending
        if 'recommended_professional' in request.session:
            del request.session['recommended_professional']
        
        return HttpResponse('Email sent successfully', status=200)
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return HttpResponse(f'Error sending email: {str(e)}', status=500)

def generate_pdf_buffer(patient, include_ai_assessment=True, user=None, recommended_professional=''):
    """Generate PDF buffer for email attachment"""
    try:
        dental_data = DentalScreening.objects.get(patient_id=patient.id)
    except DentalScreening.DoesNotExist:
        dental_data = None
        
    try:
        dietary_data = DietaryScreening.objects.get(patient_id=patient.id)
    except DietaryScreening.DoesNotExist:
        dietary_data = None
    
    buf = io.BytesIO()
    
    # Custom canvas class to add page decorations
    from reportlab.pdfgen.canvas import Canvas
    
    class CustomCanvas(Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.page_template = None
            
        def showPage(self):
            if not self.page_template:
                self.page_template = CustomPageTemplate(self, None)
            self.page_template.draw_page_frame()
            super().showPage()
    
    # Create document template with custom canvas
    doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=90, leftMargin=90, 
                          topMargin=140, bottomMargin=80, canvasmaker=CustomCanvas)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Define blue color scheme
    blue_color = HexColor('#2E86AB')
    light_blue = HexColor('#A8DADC')
    
    # Custom styles with blue accents
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=20,
        spaceBefore=10,
        alignment=1,  # Center alignment
        textColor=blue_color,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=12,
        textColor=blue_color,
        fontName='Helvetica-Bold',
        borderWidth=1,
        borderColor=light_blue,
        borderPadding=6,
        backColor=HexColor('#F8F9FA')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        leftIndent=12,
        allowWidows=1,
        allowOrphans=1
    )
    
    # Build story (content)
    story = []
    
    #Title with date
    current_date = datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph("OralSmart Dental Screening Report", title_style))
    story.append(Paragraph(f"Report Generated: {current_date}", ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=12,
        alignment=1,
        textColor=blue_color,
        spaceAfter=20
    )))
    
    #Patient Info with styled box
    story.append(Paragraph("Patient Information", heading_style))
    
    # Create patient info table for better layout
    patient_data = [
        [Paragraph(f"<b>Patient Name:</b> {patient.name}", normal_style), 
         Paragraph(f"<b>Patient Surname:</b> {patient.surname}", normal_style)],
        [Paragraph(f"<b>Patient Parent ID:</b> {patient.parent_id}", normal_style), 
         Paragraph(f"<b>Parent Contact:</b> {patient.parent_contact}", normal_style)]
    ]
    
    patient_table = Table(patient_data, colWidths=[3*inch, 3*inch])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#F0F8FF')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, light_blue),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 12))
    
    # Health Professional Information
    if user and user.is_authenticated:
        try:
            profile = Profile.objects.get(user=user)
            profession_display = dict(Profile.PROFESSIONS).get(profile.profession, profile.profession.replace('_', ' ').title())
            
            story.append(Paragraph("Health Professional Information", heading_style))
            
            professional_data = [
                [Paragraph(f"<b>Name:</b> {user.first_name}", normal_style), 
                 Paragraph(f"<b>Surname:</b> {user.last_name}", normal_style)],
                [Paragraph(f"<b>Profession:</b> {profession_display}", normal_style), 
                 Paragraph(f"<b>Registration No:</b> {profile.reg_num}", normal_style)]
            ]
            
            # Add recommended professional if available
            if recommended_professional:
                recommended_name = ProfessionalRecommendationService.get_professional_display_name(recommended_professional)
                professional_data.append([
                    Paragraph(f"<b>Recommended Referral:</b> {recommended_name}", normal_style),
                    Paragraph(f"<b>Date:</b> {timezone.now().strftime('%Y-%m-%d')}", normal_style)
                ])
            
            professional_table = Table(professional_data, colWidths=[3*inch, 3*inch])
            professional_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor('#E8F4FD')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, blue_color),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(professional_table)
            story.append(Spacer(1, 12))
            
        except Profile.DoesNotExist:
            # If no profile exists, show basic user information
            story.append(Paragraph("Health Professional Information", heading_style))
            professional_info = f"<b>Health Professional:</b> {user.first_name} {user.last_name}"
            if user.email:
                professional_info += f" ({user.email})"
            story.append(Paragraph(professional_info, normal_style))
            
            # Add recommended professional if available
            if recommended_professional:
                recommended_name = ProfessionalRecommendationService.get_professional_display_name(recommended_professional)
                recommended_info = f"<b>Recommended Referral:</b> {recommended_name} (Date: {timezone.now().strftime('%Y-%m-%d')})"
                story.append(Paragraph(recommended_info, normal_style))
            
            story.append(Spacer(1, 12))
        except Exception:
            # If other error, skip this section
            pass
    
    # Add screening availability info
    available_screenings = []
    if dental_data:
        available_screenings.append("Dental Screening")
    if dietary_data:
        available_screenings.append("Dietary Screening")
    
    story.append(Paragraph("Available Screening Data", heading_style))
    story.append(Paragraph(f"<b>Completed Screenings:</b> {', '.join(available_screenings)}", normal_style))
    story.append(Spacer(1, 12))
    
    # Add ML Risk Assessment Section for Email PDF (only for professionals)
    if include_ai_assessment and (dental_data or dietary_data):
        story.append(Paragraph("AI Risk Assessment", heading_style))
        
        # Get ML prediction
        ml_prediction = get_ml_risk_prediction(dental_data, dietary_data)
        
        if ml_prediction['available']:
            # Create risk level display with color coding
            risk_color = get_risk_color(ml_prediction['risk_level'])
            
            # Format confidence as percentage
            confidence_pct = f"{ml_prediction['confidence']:.1f}%"
            
            # Create risk assessment table
            risk_data = [
                [Paragraph(f"<b>Risk Level:</b>", normal_style),
                 Paragraph(f"<b>{ml_prediction['risk_level'].upper()}</b>", ParagraphStyle(
                     'RiskLevel',
                     parent=normal_style,
                     fontSize=12,
                     fontName='Helvetica-Bold',
                     textColor=HexColor(risk_color)
                 ))],
                [Paragraph(f"<b>Confidence:</b>", normal_style),
                 Paragraph(f"{confidence_pct}", normal_style)],
                [Paragraph(f"<b>Low Risk Probability:</b>", normal_style),
                 Paragraph(f"{ml_prediction['probability_low_risk']:.1f}%", normal_style)],
                [Paragraph(f"<b>Medium Risk Probability:</b>", normal_style),
                 Paragraph(f"{ml_prediction['probability_medium_risk']:.1f}%", normal_style)],
                [Paragraph(f"<b>High Risk Probability:</b>", normal_style),
                 Paragraph(f"{ml_prediction['probability_high_risk']:.1f}%", normal_style)]
            ]
            
            risk_table = Table(risk_data, colWidths=[2.5*inch, 3.5*inch])
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor('#F8F9FA')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, blue_color),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                # Highlight the risk level row
                ('BACKGROUND', (0, 0), (1, 0), HexColor('#E3F2FD')),
            ]))
            story.append(risk_table)
            
            # Add clinical recommendations based on risk level
            risk_level = ml_prediction['risk_level'].lower()
            if risk_level == 'high':
                recommendation_text = "⚠️ <b>HIGH RISK:</b> Immediate dental intervention recommended. Schedule comprehensive examination and treatment planning."
                rec_color = HexColor('#dc3545')
            elif risk_level == 'medium':
                recommendation_text = "⚡ <b>MEDIUM RISK:</b> Regular monitoring recommended. Schedule follow-up in 3-6 months."
                rec_color = HexColor('#ffc107')
            else:
                recommendation_text = "✅ <b>LOW RISK:</b> Continue preventive care. Regular dental check-ups recommended."
                rec_color = HexColor('#28a745')
            
            recommendation_style = ParagraphStyle(
                'Recommendation',
                parent=normal_style,
                fontSize=11,
                fontName='Helvetica-Bold',
                textColor=rec_color,
                borderWidth=2,
                borderColor=rec_color,
                borderPadding=10,
                backColor=HexColor('#FFFFFF'),
                spaceAfter=12
            )
            
            story.append(Spacer(1, 8))
            story.append(Paragraph(recommendation_text, recommendation_style))
            
        else:
            # ML prediction not available
            error_text = f"AI Risk Assessment: {ml_prediction.get('error', 'Not available')}"
            story.append(Paragraph(error_text, ParagraphStyle(
                'ErrorStyle',
                parent=normal_style,
                fontSize=11,
                textColor=HexColor('#6c757d'),
                fontStyle='italic'
            )))
        
        story.append(Spacer(1, 12))
    
    # Include dental screening sections if dental data exists
    if dental_data:
        # Section 1: Social/Behavioural/Medical Risk Factors (Dental)
        story.append(Paragraph("Social/Behavioural/Medical Risk Factors (Dental Screening)", heading_style))
        
        section1_data = [
            f"<b>Caregiver treatment:</b> {dental_data.caregiver_treatment}",
            f"<b>South African Citizen:</b> {dental_data.sa_citizen}",
            f"<b>Special needs:</b> {dental_data.special_needs}"
        ]
        
        # Add each item as a paragraph for proper bold rendering
        for item in section1_data:
            story.append(Paragraph(item, normal_style))
        story.append(Spacer(1, 12))

        # Section 2: Clinical Risk Factors (Dental)
        story.append(Paragraph("Clinical Risk Factors (Dental Screening)", heading_style))
        
        section2_data = [
            f"<b>Plaque:</b> {dental_data.plaque}",
            f"<b>Dry mouth:</b> {dental_data.dry_mouth}",
            f"<b>Enamel defects:</b> {dental_data.enamel_defects}",
            f"<b>Intra-oral appliance:</b> {dental_data.appliance}"
        ]
        
        # Add each item as a paragraph for proper bold rendering
        for item in section2_data:
            story.append(Paragraph(item, normal_style))
        story.append(Spacer(1, 12))

        # Section 3: Protective Factors (Dental)
        story.append(Paragraph("Protective Factors (Dental Screening)", heading_style))
        
        section3_data = [
            f"<b>Fluoride water:</b> {dental_data.fluoride_water}",
            f"<b>Fluoride toothpaste:</b> {dental_data.fluoride_toothpaste}",
            f"<b>Topical fluoride:</b> {dental_data.topical_fluoride}",
            f"<b>Regular checkups:</b> {dental_data.regular_checkups}"
        ]
    
        # Add each item as a paragraph for proper bold rendering
        for item in section3_data:
            story.append(Paragraph(item, normal_style))
        story.append(Spacer(1, 12))

        # Section 4: Disease Indicators (Dental)
        story.append(Paragraph("Disease Indicators (Dental Screening)", heading_style))
        
        section4_data = [
            f"<b>Sealed pits:</b> {dental_data.sealed_pits}",
            f"<b>Restorative procedures:</b> {dental_data.restorative_procedures}",
            f"<b>Enamel change:</b> {dental_data.enamel_change}",
            f"<b>Dentin discoloration:</b> {dental_data.dentin_discoloration}",
            f"<b>White spot lesions:</b> {dental_data.white_spot_lesions}",
            f"<b>Cavitated lesions:</b> {dental_data.cavitated_lesions}",
            f"<b>Multiple restorations:</b> {dental_data.multiple_restorations}",
            f"<b>Missing teeth:</b> {dental_data.missing_teeth}"
        ]
        
        # Add each item as a paragraph for proper bold rendering
        for item in section4_data:
            story.append(Paragraph(item, normal_style))
        story.append(Spacer(1, 12))

        # Section 5: DMFT Assessment (Dental only)
        tooth_names = {
                # Permanent Teeth
                "tooth_18": "Upper Right Third Molar (Wisdom Tooth)",
                "tooth_17": "Upper Right Second Molar",
                "tooth_16": "Upper Right First Molar",
                "tooth_15": "Upper Right Second Premolar",
                "tooth_14": "Upper Right First Premolar",
                "tooth_13": "Upper Right Canine",
                "tooth_12": "Upper Right Lateral Incisor",
                "tooth_11": "Upper Right Central Incisor",
                "tooth_21": "Upper Left Central Incisor",
                "tooth_22": "Upper Left Lateral Incisor",
                "tooth_23": "Upper Left Canine",
                "tooth_24": "Upper Left First Premolar",
                "tooth_25": "Upper Left Second Premolar",
                "tooth_26": "Upper Left First Molar",
                "tooth_27": "Upper Left Second Molar",
                "tooth_28": "Upper Left Third Molar (Wisdom Tooth)",
                "tooth_48": "Lower Right Third Molar (Wisdom Tooth)",
                "tooth_47": "Lower Right Second Molar",
                "tooth_46": "Lower Right First Molar",
                "tooth_45": "Lower Right Second Premolar",
                "tooth_44": "Lower Right First Premolar",
                "tooth_43": "Lower Right Canine",
                "tooth_42": "Lower Right Lateral Incisor",
                "tooth_41": "Lower Right Central Incisor",
                "tooth_31": "Lower Left Central Incisor",
                "tooth_32": "Lower Left Lateral Incisor",
                "tooth_33": "Lower Left Canine",
                "tooth_34": "Lower Left First Premolar",
                "tooth_35": "Lower Left Second Premolar",
                "tooth_36": "Lower Left First Molar",
                "tooth_37": "Lower Left Second Molar",
                "tooth_38": "Lower Left Third Molar (Wisdom Tooth)",
                # Primary Teeth
                "tooth_55": "Upper Right Second Primary Molar",
                "tooth_54": "Upper Right First Primary Molar",
                "tooth_53": "Upper Right Primary Canine",
                "tooth_52": "Upper Right Lateral Primary Incisor",
                "tooth_51": "Upper Right Central Primary Incisor",
                "tooth_61": "Upper Left Central Primary Incisor",
                "tooth_62": "Upper Left Lateral Primary Incisor",
                "tooth_63": "Upper Left Primary Canine",
                "tooth_64": "Upper Left First Primary Molar",
                "tooth_65": "Upper Left Second Primary Molar",
                "tooth_85": "Lower Right Second Primary Molar",
                "tooth_84": "Lower Right First Primary Molar",
                "tooth_83": "Lower Right Primary Canine",
                "tooth_82": "Lower Right Lateral Primary Incisor",
                "tooth_81": "Lower Right Central Primary Incisor",
                "tooth_71": "Lower Left Central Primary Incisor",
                "tooth_72": "Lower Left Lateral Primary Incisor",
                "tooth_73": "Lower Left Primary Canine",
                "tooth_74": "Lower Left First Primary Molar",
                "tooth_75": "Lower Left Second Primary Molar"
            }

        story.append(Paragraph("DMFT Assessment (Dental Screening)", heading_style))
        
        # Add a new page for tooth data
        story.append(PageBreak())
        story.append(Paragraph("Tooth Assessment", heading_style))

        for code, status in dental_data.teeth_data.items():
            if status:
                text = f"<b>{tooth_names.get(code, 'Unknown Tooth')} ({code}):</b> {status}"
                story.append(Paragraph(text, normal_style))
            elif status == "":
                text = f"<b>{tooth_names.get(code, 'Unknown Tooth')} ({code}):</b> No Issue (Assumed)"
                story.append(Paragraph(text, normal_style))
                    
    # Include dietary screening sections if dietary data exists
    if dietary_data:
        story.append(Paragraph("Dietary Screening Results", heading_style))
        
        dietary_sections = [
            ("Sweet/Sugary Foods", dietary_data.sweet_sugary_foods, dietary_data.sweet_sugary_foods_daily, dietary_data.sweet_sugary_foods_weekly),
            ("Cold Drinks and Juices", dietary_data.cold_drinks_juices, dietary_data.cold_drinks_juices_daily, dietary_data.cold_drinks_juices_weekly),
            ("Take-aways and Processed Foods", dietary_data.takeaways_processed_foods, dietary_data.takeaways_processed_foods_daily, dietary_data.takeaways_processed_foods_weekly),
            ("Salty Snacks", dietary_data.salty_snacks, dietary_data.salty_snacks_daily, dietary_data.salty_snacks_weekly),
            ("Spreads", dietary_data.spreads, dietary_data.spreads_daily, dietary_data.spreads_weekly)
        ]
        
        for section_name, consumes, daily, weekly in dietary_sections:
            story.append(Paragraph(f"<b>{section_name}</b>", normal_style))
            story.append(Paragraph(f"<b>Consumes:</b> {consumes}", normal_style))
            if daily:
                story.append(Paragraph(f"<b>Daily frequency:</b> {daily}", normal_style))
            if weekly:
                story.append(Paragraph(f"<b>Weekly frequency:</b> {weekly}", normal_style))
            story.append(Spacer(1, 8))

    # Build PDF
    doc.build(story)
    buf.seek(0)
    
    return buf