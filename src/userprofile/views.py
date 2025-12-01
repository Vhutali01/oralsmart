from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from userprofile.models import Profile
from .forms import ProfilePictureForm, UserNameForm, ProfileContactForm, ProfileProfessionForm, ProfileEmailForm, ProfilePhoneForm, ProfileAddressForm
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string

# Create your views here.

@login_required
def profile_view(request):

    user = request.user #gets user instance that is currently logged in and their details
    profile, _ = Profile.objects.get_or_create(user=user) #gets extra user profile data for profile viewing

    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile picture updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Error updating profile picture. Please try again.')
    else:
        form = ProfilePictureForm(instance=profile)

    # Get all clinics for dropdown
    from facility.models import Clinic
    clinics = Clinic.objects.all().order_by('name')
    
    #gives the profile.html template context data it can use to populate itself
    context = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': profile.email,
        'phone': profile.tel,
        'address': profile.address,
        'profession': profile.profession,
        'show_navbar': False,
        'form': form,
        'accepts_referrals': profile.accepts_referrals,
        'availability_status': profile.availability_status,
        'availability_choices': Profile.AVAILABILITY_STATUS,
        'affiliated_clinic': profile.affiliated_facility,
        'all_clinics': clinics,
    }
    
    return render(request, 'userprofile/profile.html', context)

#view that serves professions for a given authority body
def get_professions(request):
    body = request.GET.get('body')
    professions = []
    if body == 'HPCSA':
        professions = [
            {'value': 'medical_doctor', 'text': 'Medical Doctor'},
            {'value': 'dentist', 'text': 'Dentist'},
            {'value': 'psychologist', 'text': 'Psychologist'},
            {'value': 'physiotherapist', 'text': 'Physiotherapist'},
            {'value': 'radiographer', 'text': 'Radiographer'},
            {'value': 'occupational_therapist', 'text': 'Occupational Therapist'},
            {'value': 'biokineticist', 'text': 'Biokineticist'},
            {'value': 'clinical_technologist', 'text': 'Clinical Technologist'},
            {'value': 'dietitian', 'text': 'Dietitian'},
            {'value': 'audiologist', 'text': 'Audiologist'},
            {'value': 'optometrist', 'text': 'Optometrist'},
            {'value': 'emergency_care_practitioner', 'text': 'Emergency Care Practitioner'},
        ]
    elif body == 'SANC':
        professions = [
            {'value': 'registered_nurse', 'text': 'Registered Nurse'},
            {'value': 'enrolled_nurse', 'text': 'Enrolled Nurse'},
            {'value': 'nursing_assistant', 'text': 'Nursing Assistant'},
            {'value': 'midwife', 'text': 'Midwife'},
        ]
    return JsonResponse({'professions': professions})

# HTMX Views for inline editing
@login_required
def edit_name(request):
    """HTMX view for editing user's name"""
    user = request.user
    
    if request.GET.get('cancel'):
        # Return display view on cancel
        context = {
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        return render(request, 'userprofile/partials/name_display.html', context)
    
    if request.method == 'POST':
        form = UserNameForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            # Return the updated display view
            context = {
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
            return render(request, 'userprofile/partials/name_display.html', context)
        else:
            # Return the form with errors
            return render(request, 'userprofile/partials/name_form.html', {'form': form})
    else:
        # Return the edit form
        form = UserNameForm(instance=user)
        return render(request, 'userprofile/partials/name_form.html', {'form': form})

@login_required
def edit_contact(request):
    """HTMX view for editing contact information"""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    if request.GET.get('cancel'):
        # Return display view on cancel
        context = {
            'phone': profile.tel,
            'address': profile.address,
        }
        return render(request, 'userprofile/partials/contact_display.html', context)
    
    if request.method == 'POST':
        form = ProfileContactForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            # Return the updated display view
            context = {
                'phone': profile.tel,
                'address': profile.address,
            }
            return render(request, 'userprofile/partials/contact_display.html', context)
        else:
            # Return the form with errors
            return render(request, 'userprofile/partials/contact_form.html', {'form': form})
    else:
        # Return the edit form
        form = ProfileContactForm(instance=profile)
        return render(request, 'userprofile/partials/contact_form.html', {'form': form})

@login_required
def edit_profession(request):
    """HTMX view for editing profession"""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    if request.GET.get('cancel'):
        # Return display view on cancel
        context = {
            'profession': profile.get_profession_display(),
        }
        return render(request, 'userprofile/partials/profession_display.html', context)
    
    if request.method == 'POST':
        form = ProfileProfessionForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            # Return the updated display view
            context = {
                'profession': profile.get_profession_display(),
            }
            return render(request, 'userprofile/partials/profession_display.html', context)
        else:
            # Return the form with errors
            return render(request, 'userprofile/partials/profession_form.html', {'form': form})
    else:
        # Return the edit form
        form = ProfileProfessionForm(instance=profile)
        return render(request, 'userprofile/partials/profession_form.html', {'form': form})

@login_required
def edit_email(request):
    """HTMX view for editing email"""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    if request.GET.get('cancel'):
        # Return display view on cancel
        context = {
            'email': profile.email,
        }
        return render(request, 'userprofile/partials/email_display.html', context)
    
    if request.method == 'POST':
        form = ProfileEmailForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            # Return the updated display view
            context = {
                'email': profile.email,
            }
            return render(request, 'userprofile/partials/email_display.html', context)
        else:
            # Return the form with errors
            return render(request, 'userprofile/partials/email_form.html', {'form': form})
    else:
        # Return the edit form
        form = ProfileEmailForm(instance=profile)
        return render(request, 'userprofile/partials/email_form.html', {'form': form})

@login_required
def edit_phone(request):
    """HTMX view for editing phone"""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    if request.GET.get('cancel'):
        # Return display view on cancel
        context = {
            'phone': profile.tel,
        }
        return render(request, 'userprofile/partials/phone_display.html', context)
    
    if request.method == 'POST':
        form = ProfilePhoneForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            # Return the updated display view
            context = {
                'phone': profile.tel,
            }
            return render(request, 'userprofile/partials/phone_display.html', context)
        else:
            # Return the form with errors
            return render(request, 'userprofile/partials/phone_form.html', {'form': form})
    else:
        # Return the edit form
        form = ProfilePhoneForm(instance=profile)
        return render(request, 'userprofile/partials/phone_form.html', {'form': form})

@login_required
def edit_address(request):
    """HTMX view for editing address"""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    if request.GET.get('cancel'):
        # Return display view on cancel
        context = {
            'address': profile.address,
        }
        return render(request, 'userprofile/partials/address_display.html', context)
    
    if request.method == 'POST':
        form = ProfileAddressForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            # Return the updated display view
            context = {
                'address': profile.address,
            }
            return render(request, 'userprofile/partials/address_display.html', context)
        else:
            # Return the form with errors
            return render(request, 'userprofile/partials/address_form.html', {'form': form})
    else:
        # Return the edit form
        form = ProfileAddressForm(instance=profile)
        return render(request, 'userprofile/partials/address_form.html', {'form': form})


# Practitioner Referral API Endpoints
@login_required
def get_practitioners(request):
    """
    API endpoint to get practitioners who accept referrals.
    Can filter by profession type.
    """
    profession = request.GET.get('profession', '')
    
    # Get all practitioners who accept referrals
    practitioners = Profile.objects.filter(
        accepts_referrals=True
    ).exclude(
        user=request.user  # Exclude self
    ).select_related('user', 'affiliated_facility')
    
    # Filter by profession if specified
    if profession:
        practitioners = practitioners.filter(profession=profession)
    
    # Filter by availability (exclude unavailable)
    practitioners = practitioners.exclude(availability_status='unavailable')
    
    data = []
    for p in practitioners:
        data.append({
            'id': p.user.id,
            'name': p.user.get_full_name() or p.user.username,
            'profession': p.profession,
            'profession_display': p.get_profession_display(),
            'specialization': p.specialization,
            'availability': p.availability_status,
            'availability_display': p.get_availability_status_display(),
            'facility': p.affiliated_facility.name if p.affiliated_facility else None,
            'facility_id': p.affiliated_facility.id if p.affiliated_facility else None,
            'address': p.address or '',
            'tel': p.tel or '',
            'email': p.email or p.user.email,
            'profile_picture': p.profile_picture_url,
            'consultation_details': p.consultation_details,
        })
    
    return JsonResponse({
        'practitioners': data,
        'count': len(data)
    })


@login_required
def toggle_referral_acceptance(request):
    """
    Toggle the current user's referral acceptance status.
    """
    if request.method == 'POST':
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.accepts_referrals = not profile.accepts_referrals
        profile.save()
        
        return JsonResponse({
            'success': True,
            'accepts_referrals': profile.accepts_referrals,
            'message': 'You are now accepting referrals.' if profile.accepts_referrals else 'You are no longer accepting referrals.'
        })
    
    return JsonResponse({'error': 'POST method required'}, status=405)


@login_required
def update_availability(request):
    """
    Update the current user's availability status.
    """
    if request.method == 'POST':
        status = request.POST.get('status', 'available')
        
        valid_statuses = ['available', 'busy', 'unavailable', 'on_leave']
        if status not in valid_statuses:
            return JsonResponse({'error': 'Invalid status'}, status=400)
        
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.availability_status = status
        profile.save()
        
        return JsonResponse({
            'success': True,
            'availability_status': profile.availability_status,
            'message': f'Your availability is now set to: {profile.get_availability_status_display()}'
        })
    
    return JsonResponse({'error': 'POST method required'}, status=405)


@login_required
def edit_clinic(request):
    """
    HTMX view for editing user's affiliated clinic.
    """
    from facility.models import Clinic
    
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)
    
    if request.GET.get('cancel'):
        # Return display view on cancel
        clinics = Clinic.objects.all().order_by('name')
        return render(request, 'userprofile/partials/clinic_display.html', {
            'affiliated_clinic': profile.affiliated_facility,
            'all_clinics': clinics,
        })
    
    if request.method == 'POST':
        clinic_id = request.POST.get('clinic_id')
        
        if clinic_id:
            try:
                clinic = Clinic.objects.get(id=clinic_id)
                profile.affiliated_facility = clinic
            except Clinic.DoesNotExist:
                pass
        else:
            profile.affiliated_facility = None
        
        profile.save()
        messages.success(request, 'Clinic affiliation updated successfully!')
        
        # Return display view after save
        clinics = Clinic.objects.all().order_by('name')
        return render(request, 'userprofile/partials/clinic_display.html', {
            'affiliated_clinic': profile.affiliated_facility,
            'all_clinics': clinics,
        })
    
    # GET request - return edit form
    clinics = Clinic.objects.all().order_by('name')
    return render(request, 'userprofile/partials/clinic_form.html', {
        'affiliated_clinic': profile.affiliated_facility,
        'all_clinics': clinics,
    })