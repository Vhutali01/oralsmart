"""
Referral Router Service - Intelligent delivery routing with fallback mechanisms
"""
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
import requests
import logging

from .models import Referral, ReferralDeliveryLog

logger = logging.getLogger(__name__)


class ReferralRouter:
    """
    Intelligently routes referrals through appropriate channels
    with automatic fallback mechanisms
    """
    
    def send_referral(self, referral):
        """
        Main entry point - tries methods in order of preference
        Returns True if successfully delivered, False otherwise
        """
        facility = referral.receiving_facility
        
        # Build list of methods to try (in order)
        methods = self._get_delivery_methods(facility)
        
        logger.info(f"Attempting to send referral {referral.referral_number} via methods: {methods}")
        
        for method in methods:
            try:
                logger.info(f"Trying method: {method}")
                success = self._attempt_delivery(referral, method)
                
                if success:
                    referral.delivery_method = method
                    referral.delivery_status = 'delivered'
                    referral.sent_at = timezone.now()
                    referral.status = 'sent'
                    referral.save()
                    
                    # Log successful delivery
                    ReferralDeliveryLog.objects.create(
                        referral=referral,
                        method=method,
                        status='success'
                    )
                    
                    logger.info(f"Successfully delivered referral {referral.referral_number} via {method}")
                    return True
                    
            except Exception as e:
                logger.error(f"Failed to deliver via {method}: {str(e)}")
                
                # Log failed attempt
                ReferralDeliveryLog.objects.create(
                    referral=referral,
                    method=method,
                    status='failed',
                    error_message=str(e)
                )
                continue  # Try next method
        
        # All methods failed
        referral.delivery_status = 'failed'
        referral.delivery_attempts += 1
        referral.last_delivery_attempt = timezone.now()
        referral.save()
        
        logger.error(f"All delivery methods failed for referral {referral.referral_number}")
        self._notify_admin(referral)
        return False
    
    def _get_delivery_methods(self, facility):
        """
        Determine which methods to try and in what order
        """
        methods = []
        
        # Priority 1: Preferred method (if set and enabled)
        if facility.preferred_method:
            methods.append(facility.preferred_method)
        
        # Priority 2: Internal (if users associated)
        if facility.associated_users.exists():
            methods.append('internal')
        
        # Priority 3: API (if configured)
        if facility.has_api_integration and facility.api_endpoint:
            methods.append('api')
        
        # Priority 4: Email (most common fallback)
        if facility.email_notification_enabled and (facility.referral_email or facility.email):
            methods.append('email')
        
        # Priority 5: SMS (if enabled)
        if facility.sms_notification_enabled and facility.sms_number:
            methods.append('sms')
        
        # Priority 6: Portal (always available as last resort)
        if facility.allow_portal_access:
            methods.append('portal')
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(methods))
    
    def _attempt_delivery(self, referral, method):
        """
        Route to appropriate delivery handler
        """
        handlers = {
            'internal': self._deliver_internal,
            'api': self._deliver_api,
            'email': self._deliver_email,
            'sms': self._deliver_sms,
            'portal': self._deliver_portal,
        }
        
        handler = handlers.get(method)
        if handler:
            return handler(referral)
        
        logger.warning(f"No handler found for method: {method}")
        return False
    
    def _deliver_internal(self, referral):
        """
        Send to internal OralSmart users
        """
        from notifications.models import Notification
        from django.urls import reverse
        
        users = referral.receiving_facility.associated_users.all()
        
        if not users.exists():
            logger.warning(f"No users associated with facility {referral.receiving_facility.name}")
            return False
        
        # Determine notification type based on urgency
        if referral.urgency == 'emergency':
            notification_type = 'emergency_referral'
        elif referral.urgency == 'urgent':
            notification_type = 'urgent_referral'
        else:
            notification_type = 'new_referral'
        
        # Create in-app notification for each user
        for user in users:
            try:
                # Create notification
                Notification.objects.create(
                    user=user,
                    notification_type=notification_type,
                    title=f'New Referral: {referral.patient.name} {referral.patient.surname}',
                    message=f'{referral.urgency.title()} referral received from {referral.referring_facility.name}. Patient: {referral.patient.name} {referral.patient.surname}, Age: {referral.patient.age}',
                    referral=referral,
                    action_url=f'/referrals/{referral.id}/'
                )
                logger.info(f"Created in-app notification for user {user.username}")
            except Exception as e:
                logger.error(f"Failed to create notification for {user.username}: {str(e)}")
            
            # Send email notification for urgent/emergency cases
            if referral.urgency in ['urgent', 'emergency']:
                try:
                    send_mail(
                        subject=f'🚨 {referral.urgency.upper()} Referral - {referral.referral_number}',
                        message=f'''
Dear {user.get_full_name() or user.username},

You have received a {referral.urgency.upper()} patient referral in OralSmart.

Referral Number: {referral.referral_number}
Patient: {referral.patient.name} {referral.patient.surname}
Age: {referral.patient.age}
Urgency: {referral.urgency.title()}
Reason: {referral.reason}

Please log in to view full details and acknowledge receipt.

View Referral: {settings.SITE_URL}/referrals/{referral.id}/

Best regards,
OralSmart System
                        ''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    logger.error(f"Failed to send email to {user.email}: {str(e)}")
        
        return True
    
    def _deliver_api(self, referral):
        """
        POST to external API
        """
        facility = referral.receiving_facility
        
        if not facility.api_endpoint:
            return False
        
        # Format data based on API type
        if facility.api_format == 'fhir':
            payload = self._format_fhir(referral)
        else:
            payload = self._format_custom_json(referral)
        
        # Make API call
        try:
            response = requests.post(
                facility.api_endpoint,
                json=payload,
                headers={
                    'Authorization': f'Bearer {facility.api_key}' if facility.api_key else '',
                    'Content-Type': 'application/json'
                },
                timeout=30
            )
            
            # Log response
            ReferralDeliveryLog.objects.create(
                referral=referral,
                method='api',
                status='success' if response.status_code in [200, 201, 202] else 'failed',
                response_data={
                    'status_code': response.status_code,
                    'response': response.text[:500]  # First 500 chars
                }
            )
            
            return response.status_code in [200, 201, 202]
            
        except requests.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return False
    
    def _deliver_email(self, referral):
        """
        Send structured email with PDF attachment and secure link
        """
        facility = referral.receiving_facility
        recipient_email = facility.referral_email or facility.email
        
        if not recipient_email:
            return False
        
        # Generate portal URL
        portal_url = self._generate_portal_link(referral)
        
        # Prepare email content
        subject = f'Patient Referral - {referral.referral_number}'
        
        # Plain text version
        text_content = f'''
Dear {facility.name},

You have received a patient referral from {referral.referring_facility.name}.

PATIENT INFORMATION:
Name: {referral.patient.name} {referral.patient.surname}
Age: {referral.patient.age} years
Gender: {referral.patient.get_gender_display()}

REFERRAL DETAILS:
Referral Number: {referral.referral_number}
Urgency: {referral.urgency.title()}
Reason: {referral.reason}

REFERRING PROVIDER:
Provider: {referral.referring_user.get_full_name() or referral.referring_user.username}
Facility: {referral.referring_facility.name}
Contact: {referral.referring_facility.phone_number or 'N/A'}

View full referral details and respond online:
{portal_url}

This link is valid until: {referral.expires_at.strftime('%B %d, %Y')}

Best regards,
OralSmart Referral System
        '''
        
        # HTML version
        html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .info-box {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #007bff; }}
        .urgent {{ border-left-color: #dc3545; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; color: white; 
                   text-decoration: none; border-radius: 4px; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>New Patient Referral</h2>
        </div>
        <div class="content">
            <p>Dear {facility.name},</p>
            <p>You have received a <strong>{referral.urgency}</strong> patient referral.</p>
            
            <div class="info-box {'urgent' if referral.is_urgent() else ''}">
                <h3>Patient Information</h3>
                <p><strong>Name:</strong> {referral.patient.name} {referral.patient.surname}<br>
                <strong>Age:</strong> {referral.patient.age} years<br>
                <strong>Gender:</strong> {referral.patient.get_gender_display()}</p>
            </div>
            
            <div class="info-box">
                <h3>Referral Details</h3>
                <p><strong>Referral Number:</strong> {referral.referral_number}<br>
                <strong>Urgency:</strong> {referral.urgency.title()}<br>
                <strong>Reason:</strong> {referral.reason}</p>
            </div>
            
            <div class="info-box">
                <h3>Referring Provider</h3>
                <p><strong>Provider:</strong> {referral.referring_user.get_full_name() or referral.referring_user.username}<br>
                <strong>Facility:</strong> {referral.referring_facility.name}<br>
                <strong>Contact:</strong> {referral.referring_facility.phone_number or 'N/A'}</p>
            </div>
            
            <center>
                <a href="{portal_url}" class="button">View Full Referral Details</a>
            </center>
            
            <p style="font-size: 12px; color: #666;">
                This secure link is valid until {referral.expires_at.strftime('%B %d, %Y')}
            </p>
        </div>
        <div class="footer">
            <p>OralSmart Referral Management System<br>
            This is an automated message. Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
        '''
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email]
        )
        email.attach_alternative(html_content, "text/html")
        
        # TODO: Attach PDF if needed
        # pdf = self._generate_referral_pdf(referral)
        # email.attach(f'referral_{referral.referral_number}.pdf', pdf, 'application/pdf')
        
        try:
            email.send(fail_silently=False)
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def _deliver_sms(self, referral):
        """
        Send SMS notification with secure link
        """
        facility = referral.receiving_facility
        
        if not facility.sms_number:
            return False
        
        portal_url = self._generate_portal_link(referral)
        
        message = f'''
OralSmart Referral

New {referral.urgency} referral
Patient: {referral.patient.name} {referral.patient.surname}
From: {referral.referring_facility.name}

View details: {portal_url}

Ref: {referral.referral_number}
        '''.strip()
        
        # TODO: Implement SMS sending via Twilio or similar
        # try:
        #     client = TwilioClient(settings.TWILIO_SID, settings.TWILIO_TOKEN)
        #     client.messages.create(
        #         to=facility.sms_number,
        #         from_=settings.TWILIO_PHONE,
        #         body=message
        #     )
        #     return True
        # except Exception as e:
        #     logger.error(f"Failed to send SMS: {str(e)}")
        #     return False
        
        logger.info(f"SMS delivery attempted (not configured): {message}")
        return False  # Return False until SMS is properly configured
    
    def _deliver_portal(self, referral):
        """
        Generate secure portal link (passive method - link exists but not actively sent)
        """
        # Just ensure the access token exists
        if not referral.access_token:
            referral.save()  # Will auto-generate token
        
        logger.info(f"Portal link available for referral {referral.referral_number}")
        return True
    
    def _generate_portal_link(self, referral):
        """
        Create secure, time-limited portal URL
        """
        if not referral.access_token:
            referral.save()  # Will auto-generate token
        
        # Use Django's reverse to generate URL
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        path = f"/referrals/view/{referral.access_token}/"
        return f"{site_url}{path}"
    
    def _format_fhir(self, referral):
        """
        Format referral data as FHIR ServiceRequest resource
        """
        # Simplified FHIR format - expand as needed
        return {
            "resourceType": "ServiceRequest",
            "identifier": [{
                "system": "oralsmart-referrals",
                "value": referral.referral_number
            }],
            "status": "active",
            "intent": "order",
            "priority": "urgent" if referral.is_urgent() else "routine",
            "subject": {
                "display": f"{referral.patient.name} {referral.patient.surname}",
                "identifier": {
                    "value": str(referral.patient.id)
                }
            },
            "reasonCode": [{
                "text": referral.reason
            }],
            "note": [{
                "text": referral.clinical_summary
            }],
            "requester": {
                "display": referral.referring_user.get_full_name() or referral.referring_user.username,
                "organization": referral.referring_facility.name
            },
            "performer": [{
                "display": referral.receiving_facility.name
            }]
        }
    
    def _format_custom_json(self, referral):
        """
        Format referral data as custom JSON
        """
        return {
            "referral_number": referral.referral_number,
            "patient": {
                "name": referral.patient.name,
                "surname": referral.patient.surname,
                "age": referral.patient.age,
                "gender": referral.patient.get_gender_display(),
                "parent_name": f"{referral.patient.parent_name} {referral.patient.parent_surname}",
                "parent_contact": referral.patient.parent_contact,
            },
            "referral_details": {
                "reason": referral.reason,
                "clinical_summary": referral.clinical_summary,
                "urgency": referral.urgency,
                "specialty_required": referral.specialty_required,
                "created_at": referral.created_at.isoformat(),
            },
            "referring_provider": {
                "name": referral.referring_user.get_full_name() or referral.referring_user.username,
                "facility": referral.referring_facility.name,
                "contact": referral.referring_facility.phone_number,
                "email": referral.referring_facility.email,
            },
            "portal_url": self._generate_portal_link(referral),
        }
    
    def _notify_admin(self, referral):
        """
        Notify system administrators of failed delivery
        """
        try:
            admin_emails = [admin[1] for admin in getattr(settings, 'ADMINS', [])]
            if admin_emails:
                send_mail(
                    subject=f'Referral Delivery Failed - {referral.referral_number}',
                    message=f'''
A referral failed to deliver after all attempts:

Referral: {referral.referral_number}
Patient: {referral.patient.name} {referral.patient.surname}
Receiving Facility: {referral.receiving_facility.name}
Attempts: {referral.delivery_attempts}
Error: {referral.delivery_error}

Please review and manually contact the receiving facility.
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=admin_emails,
                    fail_silently=True,
                )
        except Exception as e:
            logger.error(f"Failed to notify admin: {str(e)}")
