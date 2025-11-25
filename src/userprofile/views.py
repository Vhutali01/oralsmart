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

    #gives the profile.html template context data it can use to populate itself
    context = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': profile.email,
        'phone': profile.tel,
        'address': profile.address,
        'profession': profile.profession,
        'show_navbar': False,
        'form': form
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