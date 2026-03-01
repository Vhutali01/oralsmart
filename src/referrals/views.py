from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden, FileResponse
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
import io
from datetime import datetime

from .models import Referral, ReferralComment, ReferralDeliveryLog
from .forms import ReferralForm, ReferralCommentForm, ReferralStatusUpdateForm, PortalAcknowledgeForm
from .services import ReferralRouter
from reports.views import generate_pdf_buffer





@login_required
def referral_detail(request, pk):
    """
    View referral details
    """
    referral = get_object_or_404(Referral, pk=pk)
    
    # Check permissions
    user = request.user
    
    is_sender = referral.referring_user == user
    is_receiver = (referral.receiving_user == user) if referral.receiving_user else False
    is_receiving_practitioner = (referral.receiving_practitioner == user) if referral.receiving_practitioner else False
    
    # Allow access if user is sender, receiver, receiving practitioner, or has access through their facility
    user_facilities = []
    if hasattr(user, 'profile'):
        # In future, check if user belongs to referring or receiving facility
        pass
    
    has_access = is_sender or is_receiver or is_receiving_practitioner or user.is_staff
    
    if not has_access:
        return HttpResponseForbidden("You don't have permission to view this referral.")
    
    # Handle comment submission
    if request.method == 'POST' and 'submit_comment' in request.POST:
        comment_form = ReferralCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.referral = referral
            comment.author = user
            comment.author_name = user.get_full_name() or user.username
            comment.is_internal = True
            try:
                comment.save()
                messages.success(request, 'Comment added successfully.')
                return redirect('referrals:detail', pk=pk)
            except Exception as e:
                messages.error(request, f'Error saving comment: {str(e)}')
        else:
            messages.error(request, f'Invalid form data: {comment_form.errors}')
    else:
        comment_form = ReferralCommentForm()
    
    # Handle status update
    if request.method == 'POST' and 'status' in request.POST:
        status_form = ReferralStatusUpdateForm(request.POST, instance=referral)
        if status_form.is_valid():
            updated_referral = status_form.save(commit=False)
            
            # Set acknowledged_at if status changed to acknowledged
            if updated_referral.status == 'acknowledged' and not referral.acknowledged_at:
                updated_referral.acknowledged_at = timezone.now()
            
            # Set completed_at if status changed to completed
            if updated_referral.status == 'completed' and not referral.completed_at:
                updated_referral.completed_at = timezone.now()
            
            updated_referral.save()
            messages.success(request, 'Referral status updated.')
            return redirect('referrals:detail', pk=pk)
    else:
        status_form = ReferralStatusUpdateForm(instance=referral)
    
    # Get delivery logs
    delivery_logs = referral.delivery_logs.all()[:5]
    
    # Get comments
    comments = referral.comments.all()
    
    context = {
        'referral': referral,
        'is_sender': is_sender,
        'is_receiver': is_receiver,
        'comment_form': comment_form,
        'status_form': status_form,
        'delivery_logs': delivery_logs,
        'comments': comments,
    }
    
    return render(request, 'referrals/referral_detail.html', context)


def portal_view(request, access_token):
    """
    Public portal view for external users to view referrals
    No login required - secured by access token
    """
    try:
        referral = Referral.objects.get(
            access_token=access_token,
            expires_at__gte=timezone.now()
        )
    except Referral.DoesNotExist:
        return render(request, 'referrals/portal_expired.html', status=404)
    
    # Track view
    referral.view_count += 1
    referral.last_viewed_at = timezone.now()
    referral.save(update_fields=['view_count', 'last_viewed_at'])
    
    # Handle acknowledgment
    if request.method == 'POST':
        ack_form = PortalAcknowledgeForm(request.POST)
        if ack_form.is_valid():
            if referral.status == 'sent':
                referral.status = 'acknowledged'
                referral.acknowledged_at = timezone.now()
                referral.save()
                
                # Add comment if notes provided
                notes = ack_form.cleaned_data.get('notes')
                if notes:
                    ReferralComment.objects.create(
                        referral=referral,
                        author_name=referral.receiving_facility.name,
                        comment=notes,
                        is_internal=False
                    )
                
                messages.success(request, 'Thank you! Referral acknowledged successfully.')
            
            return redirect('referrals:portal_view', access_token=access_token)
    else:
        ack_form = PortalAcknowledgeForm()
    
    context = {
        'referral': referral,
        'ack_form': ack_form,
        'can_acknowledge': referral.status == 'sent',
    }
    
    return render(request, 'referrals/portal_view.html', context)


@login_required
def referral_resend(request, pk):
    """
    Manually retry sending a failed referral
    """
    referral = get_object_or_404(Referral, pk=pk)
    
    # Check permissions
    if referral.referring_user != request.user:
        return HttpResponseForbidden("You don't have permission to resend this referral.")
    
    router = ReferralRouter()
    success = router.send_referral(referral)
    
    if success:
        messages.success(request, f'Referral {referral.referral_number} sent successfully!')
    else:
        messages.error(request, f'Failed to send referral. Please contact support.')
    
    return redirect('referrals:detail', pk=pk)


@login_required
def referral_cancel(request, pk):
    """
    Cancel a referral
    """
    referral = get_object_or_404(Referral, pk=pk)
    
    # Check permissions
    if referral.referring_user != request.user:
        return HttpResponseForbidden("You don't have permission to cancel this referral.")
    
    if request.method == 'POST':
        referral.status = 'cancelled'
        referral.save()
        messages.success(request, 'Referral cancelled.')
        return redirect('patient_list')
    
    return render(request, 'referrals/referral_cancel_confirm.html', {'referral': referral})


@login_required
def referral_stats(request):
    """
    Dashboard showing referral statistics
    """
    user = request.user
    user_facilities = user.clinics.all()
    
    # Sent referrals stats
    sent_total = Referral.objects.filter(referring_user=user).count()
    sent_pending = Referral.objects.filter(referring_user=user, status='sent').count()
    sent_completed = Referral.objects.filter(referring_user=user, status='completed').count()
    
    # Received referrals stats
    received_total = Referral.objects.filter(
        Q(receiving_user=user) | Q(receiving_facility__in=user_facilities) | Q(receiving_practitioner=user)
    ).count()
    received_pending = Referral.objects.filter(
        Q(receiving_user=user) | Q(receiving_facility__in=user_facilities) | Q(receiving_practitioner=user),
        status='sent'
    ).count()
    received_acknowledged = Referral.objects.filter(
        Q(receiving_user=user) | Q(receiving_facility__in=user_facilities) | Q(receiving_practitioner=user),
        status='acknowledged'
    ).count()
    
    context = {
        'sent_total': sent_total,
        'sent_pending': sent_pending,
        'sent_completed': sent_completed,
        'received_total': received_total,
        'received_pending': received_pending,
        'received_acknowledged': received_acknowledged,
    }
    
    return render(request, 'referrals/referral_stats.html', context)


@login_required
def create_practitioner_referral(request):
    """
    API endpoint to create a referral to an individual practitioner
    """
    from django.contrib.auth.models import User
    from patient.models import Patient
    from assessments.models import DentalScreening, DietaryScreening
    from notifications.models import Notification
    from datetime import timedelta
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        # Get required fields
        patient_id = request.POST.get('patient_id')
        practitioner_id = request.POST.get('practitioner_id')
        reason = request.POST.get('reason', '')
        clinical_summary = request.POST.get('clinical_summary', '')
        urgency = request.POST.get('urgency', 'routine')
        recommended_profession = request.POST.get('recommended_profession', '')
        
        # Validate patient
        try:
            patient = Patient.objects.get(id=patient_id, created_by=request.user)
        except Patient.DoesNotExist:
            return JsonResponse({'error': 'Patient not found'}, status=404)
        
        # Validate practitioner
        try:
            practitioner = User.objects.get(id=practitioner_id)
            if not hasattr(practitioner, 'profile') or not practitioner.profile.accepts_referrals:
                return JsonResponse({'error': 'This practitioner is not accepting referrals'}, status=400)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Practitioner not found'}, status=404)
        
        # Get screenings if available
        try:
            dental_screening = DentalScreening.objects.get(patient=patient)
        except DentalScreening.DoesNotExist:
            dental_screening = None
            
        try:
            dietary_screening = DietaryScreening.objects.get(patient=patient)
        except DietaryScreening.DoesNotExist:
            dietary_screening = None
        
        # Get user's affiliated facility if any
        referring_facility = None
        if hasattr(request.user, 'profile') and request.user.profile.affiliated_facility:
            referring_facility = request.user.profile.affiliated_facility
        
        # Create the referral
        referral = Referral.objects.create(
            referral_type='practitioner',
            patient=patient,
            referring_user=request.user,
            referring_facility=referring_facility,
            receiving_practitioner=practitioner,
            receiving_facility=practitioner.profile.affiliated_facility if hasattr(practitioner, 'profile') else None,
            dental_screening=dental_screening,
            dietary_screening=dietary_screening,
            reason=reason,
            clinical_summary=clinical_summary,
            urgency=urgency,
            recommended_profession=recommended_profession,
            status='sent',
            delivery_method='internal',
            delivery_status='delivered',
            expires_at=timezone.now() + timedelta(days=90),
            sent_at=timezone.now(),
        )
        
        # Create notification for the practitioner
        if urgency == 'emergency':
            notification_type = 'emergency_referral'
        elif urgency == 'urgent':
            notification_type = 'urgent_referral'
        else:
            notification_type = 'new_referral'
        
        Notification.objects.create(
            user=practitioner,
            notification_type=notification_type,
            title=f'New Referral: {patient.name} {patient.surname}',
            message=f'{urgency.title()} referral received from {request.user.get_full_name() or request.user.username}. Patient: {patient.name} {patient.surname}, Age: {patient.age}',
            referral=referral,
            action_url=f'/referrals/{referral.id}/'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Referral sent to {practitioner.get_full_name() or practitioner.username}',
            'referral_id': referral.id,
            'referral_number': referral.referral_number
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def create_clinic_referral(request):
    """
    API endpoint to create a referral to a clinic/facility.
    """
    from patient.models import Patient
    from facility.models import Clinic
    from assessments.models import DentalScreening, DietaryScreening
    from notifications.models import Notification
    from datetime import timedelta
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        patient_id = request.POST.get('patient_id')
        clinic_id = request.POST.get('clinic_id')
        urgency = request.POST.get('urgency', 'routine')
        reason = request.POST.get('reason', '')
        clinical_summary = request.POST.get('clinical_summary', '')
        patient_preferences = request.POST.get('patient_preferences', '')
        recommended_profession = request.POST.get('recommended_profession', '')
        
        if not patient_id or not clinic_id:
            return JsonResponse({'error': 'Patient ID and Clinic ID are required'}, status=400)
        
        # Validate patient
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return JsonResponse({'error': 'Patient not found'}, status=404)
        
        # Validate clinic
        try:
            clinic = Clinic.objects.get(id=clinic_id)
        except Clinic.DoesNotExist:
            return JsonResponse({'error': 'Clinic not found'}, status=404)
        
        # Get screenings if available
        try:
            dental_screening = DentalScreening.objects.get(patient=patient)
        except DentalScreening.DoesNotExist:
            dental_screening = None
            
        try:
            dietary_screening = DietaryScreening.objects.get(patient=patient)
        except DietaryScreening.DoesNotExist:
            dietary_screening = None
        
        # Get user's affiliated facility if any
        referring_facility = None
        if hasattr(request.user, 'profile') and request.user.profile.affiliated_facility:
            referring_facility = request.user.profile.affiliated_facility
        
        # Combine clinical_summary with patient preferences
        full_summary = clinical_summary
        if patient_preferences:
            full_summary += f"\n\nPatient/Parent Preferences: {patient_preferences}"
        
        # Create the referral
        referral = Referral.objects.create(
            referral_type='facility',
            patient=patient,
            referring_user=request.user,
            referring_facility=referring_facility,
            receiving_facility=clinic,
            dental_screening=dental_screening,
            dietary_screening=dietary_screening,
            reason=reason,
            clinical_summary=full_summary,
            urgency=urgency,
            recommended_profession=recommended_profession,
            status='sent',
            delivery_method='internal',
            delivery_status='delivered',
            expires_at=timezone.now() + timedelta(days=90),
            sent_at=timezone.now(),
        )
        
        # Create notifications for clinic staff if they have users
        if urgency == 'emergency':
            notification_type = 'emergency_referral'
        elif urgency == 'urgent':
            notification_type = 'urgent_referral'
        else:
            notification_type = 'new_referral'
        
        # Find users affiliated with this clinic and notify them
        from userprofile.models import Profile
        clinic_users = Profile.objects.filter(affiliated_facility=clinic).select_related('user')
        
        for profile in clinic_users:
            Notification.objects.create(
                user=profile.user,
                notification_type=notification_type,
                title=f'New Referral to {clinic.name}: {patient.name} {patient.surname}',
                message=f'{urgency.title()} referral received from {request.user.get_full_name() or request.user.username}. Patient: {patient.name} {patient.surname}, Age: {patient.age}',
                referral=referral,
                action_url=f'/referrals/{referral.id}/'
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Referral sent to {clinic.name}',
            'referral_id': referral.id,
            'referral_number': referral.referral_number
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def generate_referral_pdf(request, pk):
    """
    Generate PDF report for a specific referral
    """
    referral = get_object_or_404(Referral, pk=pk)
    
    # Check permissions
    user = request.user
    is_sender = referral.referring_user == user
    is_receiver = (referral.receiving_user == user) if referral.receiving_user else False
    is_receiving_practitioner = (referral.receiving_practitioner == user) if referral.receiving_practitioner else False
    
    has_access = is_sender or is_receiver or is_receiving_practitioner or user.is_staff
    
    if not has_access:
        return HttpResponseForbidden("You don't have permission to download this referral report.")
    
    # Get patient data
    patient = referral.patient
    
    # Get screening data
    dental_data = referral.dental_screening
    dietary_data = referral.dietary_screening
    
    # Generate PDF using the existing function from reports
    pdf_buffer = generate_pdf_buffer(
        patient=patient,
        include_ai_assessment=True,
        user=request.user,
        recommended_professional=referral.recommended_profession
    )
    
    # Create filename
    filename = f"referral_{referral.referral_number}_{patient.name}_{patient.surname}.pdf"
    
    # Return PDF as response
    pdf_buffer.seek(0)
    return FileResponse(pdf_buffer, as_attachment=True, filename=filename, content_type='application/pdf')
