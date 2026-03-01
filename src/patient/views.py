from django.shortcuts import render, redirect
from django.db.models import Q
from django.core.paginator import Paginator
from .forms import PatientForm
from .models import Patient
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def create_patient(request):
    if request.method == 'POST':
        try:
            #get form data
            name = request.POST.get('name')
            surname = request.POST.get('surname')
            gender = request.POST.get('gender')
            age = request.POST.get('age')
            parent_name = request.POST.get('parent_name')
            parent_surname = request.POST.get('parent_surname')
            parent_id = request.POST.get('parent_id')
            parent_contact = request.POST.get('parent_contact')
            screening_type = request.POST.get('screening_type')
            
            #validate required fields
            if not all([name, surname, gender, age, parent_name, parent_surname, parent_id, parent_contact]):
                missing_fields = []
                if not name: missing_fields.append('Child First Name')
                if not surname: missing_fields.append('Child Surname')
                if not gender: missing_fields.append('Gender')
                if not age: missing_fields.append('Age')
                if not parent_name: missing_fields.append('Parent First Name')
                if not parent_surname: missing_fields.append('Parent Surname')
                if not parent_id: missing_fields.append('Parent ID Number')
                if not parent_contact: missing_fields.append('Parent Contact Number')
                
                messages.error(request, f'⚠️ Please complete all required fields: {", ".join(missing_fields)}')
                return render(request, 'patient/create_patient.html', {'show_navbar': True})
            
            #create new patient
            patient = Patient.objects.create(
                name=name,
                surname=surname,
                gender=gender,
                age=age,
                parent_name=parent_name,
                parent_surname=parent_surname,
                parent_id=parent_id,
                parent_contact=parent_contact,
                created_by=request.user  # Associate with current user
            )
            
            messages.success(request, f'Patient {patient.name} {patient.surname} created successfully!')
            
            #check if screening was requested
            if screening_type:
                if screening_type == 'dental':
                    return redirect('dental_screening', patient_id=patient.id) #type: ignore
                elif screening_type == 'dietary':
                    return redirect('dietary_screening', patient_id=patient.id) #type: ignore
                elif screening_type == 'both':
                    #start with dietary screening, then proceed to dental
                    return redirect(f'/assessments/dietary_screening/{patient.id}/?perform_both=true') #type: ignore
            
            #if no screening, redirect to success page or patient list
            return redirect('create_patient')  # or wherever you want to redirect
            
        except Exception as e:
            error_msg = str(e)
            if 'parent_id' in error_msg.lower():
                messages.error(request, '⚠️ Invalid Parent ID. Please ensure it\'s exactly 13 digits.')
            elif 'parent_contact' in error_msg.lower():
                messages.error(request, '⚠️ Invalid Contact Number. Please ensure it\'s exactly 10 digits without spaces.')
            else:
                messages.error(request, f'⚠️ Error creating patient: Please check all fields and try again.')
            return render(request, 'patient/create_patient.html', {'show_navbar': True})
    
    #if GET request, render the form
    return render(request, 'patient/create_patient.html', {'show_navbar': True})

@login_required
def patient_list_view(request):
    """View to display all patients created by the current user with search functionality"""
    from referrals.models import Referral
    from assessments.models import DentalScreening, DietaryScreening
    from django.db.models import Exists, OuterRef, Q
    from facility.models import Clinic
    from userprofile.models import Profile
    
    user = request.user
    
    # Get search query from GET parameters
    search_query = request.GET.get('search', '').strip()
    
    # Get recommended profession from session (if coming from report page)
    recommended_profession = request.session.get('recommended_professional', '')
    
    # Base queryset - only show patients created by the current user
    # Annotate with screening status for display
    patients = Patient.objects.filter(created_by=request.user).annotate(
        has_dental_screening=Exists(DentalScreening.objects.filter(patient=OuterRef('pk'))),
        has_dietary_screening=Exists(DietaryScreening.objects.filter(patient=OuterRef('pk')))
    )
    
    # Apply search filter if search query exists
    if search_query:
        patients = patients.filter(
            Q(name__icontains=search_query) |
            Q(surname__icontains=search_query) |
            Q(parent_id__icontains=search_query) |
            Q(parent_contact__icontains=search_query) #|
            # Q(parent_name__icontains=search_query) |
            # Q(parent_surname__icontains=search_query)
        )
    
    # Order by most recent
    patients = patients.order_by('-id')
    
    # Pagination - 10 patients per page
    paginator = Paginator(patients, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Referrals sent by this user
    sent_referrals = Referral.objects.filter(referring_user=user).select_related(
        'patient', 'receiving_facility', 'referring_facility', 'receiving_practitioner'
    ).order_by('-created_at')
    
    # Referrals received by this user directly or as practitioner
    received_referrals = Referral.objects.filter(
        Q(receiving_user=user) | Q(receiving_practitioner=user)
    ).select_related('patient', 'referring_user', 'referring_facility').order_by('-created_at')
    
    # Get all patients with screening status annotations
    # Limit to most recent 50 patients for modal performance
    eligible_patients = Patient.objects.filter(
        created_by=request.user
    ).annotate(
        has_dental_screening=Exists(DentalScreening.objects.filter(patient=OuterRef('pk'))),
        has_dietary_screening=Exists(DietaryScreening.objects.filter(patient=OuterRef('pk')))
    ).order_by('-id')[:50]
    
    # Get clinics for the Clinics tab
    clinics = Clinic.objects.filter(accepts_referrals=True).order_by('name')
    
    # Get available professions for the filter
    professions = Profile.PROFESSIONS
    
    context = {
        'patients': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'search_query': search_query,
        'show_navbar': True,
        'total_patients': paginator.count,
        'sent_referrals': sent_referrals[:10],
        'received_referrals': received_referrals[:10],
        'eligible_patients': eligible_patients,
        'clinics': clinics,
        'professions': professions,
        'recommended_profession': recommended_profession,
        'back_url': '/home/',
    }
    
    return render(request, "patient/patient_list.html", context)