from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator

from .models import Referral, ReferralComment, ReferralDeliveryLog
from .forms import ReferralForm, ReferralCommentForm, ReferralStatusUpdateForm, PortalAcknowledgeForm
from .services import ReferralRouter





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
    
    # Allow access if user is sender, receiver, or has access through their facility
    user_facilities = []
    if hasattr(user, 'profile'):
        # In future, check if user belongs to referring or receiving facility
        pass
    
    has_access = is_sender or is_receiver or user.is_staff
    
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
        Q(receiving_user=user) | Q(receiving_facility__in=user_facilities)
    ).count()
    received_pending = Referral.objects.filter(
        Q(receiving_user=user) | Q(receiving_facility__in=user_facilities),
        status='sent'
    ).count()
    received_acknowledged = Referral.objects.filter(
        Q(receiving_user=user) | Q(receiving_facility__in=user_facilities),
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
