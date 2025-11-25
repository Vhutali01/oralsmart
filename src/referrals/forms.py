from django import forms
from .models import Referral, ReferralComment
from patient.models import Patient
from facility.models import Clinic


class ReferralForm(forms.ModelForm):
    """
    Form for creating and editing referrals
    """
    
    class Meta:
        model = Referral
        fields = [
            'patient',
            'receiving_facility',
            'dental_screening',
            'dietary_screening',
            'reason',
            'clinical_summary',
            'urgency',
            'specialty_required',
            'patient_preferences',
            'insurance_information',
            'appointment_date',
        ]
        widgets = {
            'reason': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Brief reason for referral'
            }),
            'clinical_summary': forms.Textarea(attrs={
                'rows': 5,
                'class': 'form-control',
                'placeholder': 'Detailed clinical findings, observations, and recommendations'
            }),
            'patient_preferences': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': 'Any patient or parent preferences, concerns, or special requirements'
            }),
            'insurance_information': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': 'Insurance details if applicable'
            }),
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'receiving_facility': forms.Select(attrs={'class': 'form-control'}),
            'dental_screening': forms.Select(attrs={'class': 'form-control'}),
            'dietary_screening': forms.Select(attrs={'class': 'form-control'}),
            'urgency': forms.Select(attrs={'class': 'form-control'}),
            'specialty_required': forms.Select(attrs={'class': 'form-control'}),
            'appointment_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
        }
        labels = {
            'patient': 'Patient',
            'receiving_facility': 'Referring To (Facility)',
            'dental_screening': 'Dental Screening (Optional)',
            'dietary_screening': 'Dietary Screening (Optional)',
            'reason': 'Reason for Referral',
            'clinical_summary': 'Clinical Summary',
            'urgency': 'Urgency Level',
            'specialty_required': 'Specialty Required',
            'patient_preferences': 'Patient Preferences/Concerns',
            'insurance_information': 'Insurance Information',
            'appointment_date': 'Suggested Appointment Date (Optional)',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter patients by current user
        if user:
            self.fields['patient'].queryset = Patient.objects.filter(created_by=user)
        
        # Filter clinics that accept referrals
        self.fields['receiving_facility'].queryset = Clinic.objects.filter(accepts_referrals=True)
        
        # Make some fields optional
        self.fields['dental_screening'].required = False
        self.fields['dietary_screening'].required = False
        self.fields['patient_preferences'].required = False
        self.fields['insurance_information'].required = False
        self.fields['appointment_date'].required = False


class ReferralCommentForm(forms.ModelForm):
    """
    Form for adding comments to referrals
    """
    
    class Meta:
        model = ReferralComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Add a comment or question...'
            })
        }
        labels = {
            'comment': 'Comment'
        }


class ReferralStatusUpdateForm(forms.ModelForm):
    """
    Form for updating referral status
    """
    
    class Meta:
        model = Referral
        fields = ['status', 'appointment_date']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'appointment_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            })
        }


class PortalAcknowledgeForm(forms.Form):
    """
    Simple form for acknowledging referral receipt via portal
    """
    acknowledge = forms.BooleanField(
        required=True,
        label='I acknowledge receipt of this referral',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Optional notes or comments'
        }),
        label='Notes'
    )
