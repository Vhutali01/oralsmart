# OralSmart Referral System - Implementation Guide

## Overview
The OralSmart Referral System is a comprehensive, hybrid hub-and-spoke referral management solution that supports multiple delivery methods including internal notifications, API integration, email, SMS, and secure portal access.

## What Was Implemented

### 1. **Referrals App Structure**
- Complete Django app with models, views, forms, URLs, and admin
- Intelligent routing service with automatic fallback mechanisms
- Management commands for retry logic
- Signal handlers for notifications

### 2. **Database Models**

#### Referral Model
- Comprehensive patient referral tracking
- Support for multiple delivery methods
- Status lifecycle management (draft → sent → acknowledged → completed)
- Secure access tokens for external viewing
- Automatic referral number generation (REF-YYYY-NNNNNN)

#### ReferralDeliveryLog Model
- Tracks all delivery attempts
- Stores error messages and response data
- Audit trail for troubleshooting

#### ReferralComment Model
- Two-way communication between providers
- Support for internal and external users

#### ReferralAttachment Model
- File uploads for supporting documents
- X-rays, images, reports, etc.

### 3. **Updated Clinic Model**
Added referral management configuration fields:
- `accepts_referrals` - Enable/disable referral acceptance
- `associated_users` - Link OralSmart users to clinics
- `has_api_integration` - API integration settings
- `api_endpoint`, `api_key`, `api_format` - API configuration
- `referral_email` - Email for referral notifications
- `email_notification_enabled` - Email toggle
- `sms_notification_enabled`, `sms_number` - SMS settings
- `allow_portal_access`, `require_authentication` - Portal security
- `preferred_method` - Delivery method preference

### 4. **Intelligent Routing Service**
The `ReferralRouter` class provides:
- **Automatic method selection** based on clinic preferences
- **Fallback mechanisms** - tries multiple methods until successful
- **Delivery handlers** for each method:
  - `_deliver_internal()` - In-app notifications
  - `_deliver_api()` - API POST with FHIR/JSON formatting
  - `_deliver_email()` - HTML email with secure link
  - `_deliver_sms()` - SMS notifications (ready for Twilio)
  - `_deliver_portal()` - Passive secure link generation
- **Error handling and logging**
- **Admin notifications** on complete failure

### 5. **Views and Forms**
- `referral_list` - View sent and received referrals
- `referral_create` - Create and send new referrals
- `referral_detail` - Full referral details with comments
- `portal_view` - Public portal for external access (no login)
- `referral_resend` - Manual retry for failed deliveries
- `referral_cancel` - Cancel referrals
- `referral_stats` - Dashboard with statistics

### 6. **Templates**
- Modern, responsive Bootstrap 5 design
- Separate portal template for external users
- Clear status indicators and timelines
- Comment system for provider communication

### 7. **Admin Interface**
- Full CRUD operations for all models
- Advanced filtering and search
- Readonly fields for audit data
- Organized fieldsets

## Next Steps to Complete Implementation

### 1. **Run Migrations** (REQUIRED)
```bash
# Navigate to src directory
cd c:\Users\vhuta\dev\oralsmart\src

# Activate your virtual environment first
# Then create migrations
python manage.py makemigrations facility
python manage.py makemigrations referrals

# Apply migrations
python manage.py migrate
```

### 2. **Update Admin Registration for Facility**
Add the new fields to `facility/admin.py`:

```python
from django.contrib import admin
from .models import Clinic

@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ['name', 'clinic_type', 'accepts_referrals', 'preferred_method']
    list_filter = ['clinic_type', 'accepts_referrals', 'preferred_method']
    filter_horizontal = ['associated_users']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'clinic_type', 'address', 'phone_number', 'email', 'website', 'description', 'hours', 'emergency')
        }),
        ('Referral Configuration', {
            'fields': (
                'accepts_referrals',
                'associated_users',
                'preferred_method'
            )
        }),
        ('API Integration', {
            'fields': ('has_api_integration', 'api_endpoint', 'api_key', 'api_format'),
            'classes': ('collapse',)
        }),
        ('Email Settings', {
            'fields': ('email_notification_enabled', 'referral_email'),
        }),
        ('SMS Settings', {
            'fields': ('sms_notification_enabled', 'sms_number'),
            'classes': ('collapse',)
        }),
        ('Portal Settings', {
            'fields': ('allow_portal_access', 'require_authentication'),
        }),
    )
```

### 3. **Configure Email Settings**
Update your `.env` file or environment variables:

```env
# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_PORT=587
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=OralSmart <noreply@oralsmart.com>

# Site URL (for referral links)
SITE_URL=http://localhost:8000  # Change for production

# Referral Settings
REFERRAL_EXPIRY_DAYS=30
REFERRAL_MAX_RETRY_ATTEMPTS=3
```

### 4. **Setup Automated Retry (Optional)**
Schedule the retry command to run periodically:

**Option A: Using Celery Beat** (Recommended for production)
```python
# In settings.py
CELERY_BEAT_SCHEDULE = {
    'retry-failed-referrals': {
        'task': 'referrals.tasks.retry_failed_referrals',
        'schedule': crontab(minute=0, hour='*/1'),  # Every hour
    },
}
```

**Option B: Using Windows Task Scheduler or cron**
```bash
# Run manually
python manage.py retry_failed_referrals

# Or schedule in Task Scheduler to run hourly
```

### 5. **Add Navigation Links**
Update your `base.html` template to add referral menu items:

```html
{% if user.is_authenticated %}
<li class="nav-item">
    <a class="nav-link" href="{% url 'referrals:list' %}">
        <i class="fas fa-exchange-alt"></i> Referrals
    </a>
</li>
<li class="nav-item">
    <a class="nav-link" href="{% url 'referrals:create' %}">
        <i class="fas fa-plus"></i> New Referral
    </a>
</li>
{% endif %}
```

### 6. **Setup SMS (Optional)**
If you want SMS notifications:

1. Sign up for Twilio account
2. Install Twilio SDK:
```bash
pip install twilio
```

3. Add to settings:
```python
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
```

4. Uncomment SMS code in `referrals/services.py` (line ~450)

### 7. **Configure Clinic Settings**
In Django admin, configure each clinic's referral preferences:

1. Go to `/admin/facility/clinic/`
2. For each clinic:
   - Set `accepts_referrals` to True
   - Choose `preferred_method` (usually 'email')
   - Add `referral_email` address
   - Enable `email_notification_enabled`
   - Optionally link users via `associated_users`

## Usage Guide

### Creating a Referral

1. **Login as healthcare provider**
2. **Navigate to "Create Referral"**
3. **Fill out the form:**
   - Select patient (from your patients)
   - Choose receiving facility
   - Set urgency level
   - Specify specialty needed
   - Provide reason and clinical summary
   - Add any screening results
4. **Click "Create and Send Referral"**
5. **System automatically:**
   - Generates unique referral number
   - Creates secure access token
   - Attempts delivery via configured methods
   - Sends email/SMS notifications
   - Logs all attempts

### Receiving a Referral

**Internal Users (on OralSmart):**
1. Receive in-app notification
2. Get email alert
3. View in "Received Referrals" tab
4. Can acknowledge, comment, update status

**External Users (not on OralSmart):**
1. Receive email with secure link
2. Click link to view referral in portal
3. No login required
4. Can acknowledge receipt
5. Link valid for 30 days

### Tracking Referrals

- **Dashboard** shows sent/received/pending counts
- **Detail view** displays complete timeline
- **Delivery logs** show all attempts and methods
- **Comments** enable two-way communication
- **Status updates** track progress

## Features

### ✅ Implemented
- Multiple delivery methods with fallback
- Secure portal access for external users
- Comprehensive audit trails
- Status lifecycle management
- Two-way communication via comments
- Automatic referral numbering
- Email notifications with HTML templates
- API integration framework (FHIR/JSON)
- Manual retry for failed deliveries
- Management command for automated retries
- Full admin interface
- Responsive templates

### 🚧 Ready to Enable
- SMS notifications (Twilio integration code ready)
- API delivery (implementation ready)
- File attachments (model created)
- PDF generation (placeholder in code)

### 💡 Future Enhancements
- Push notifications
- Analytics dashboard
- Bulk referral operations
- Templates for common referrals
- Integration with electronic health records
- Appointment booking integration
- Referral outcome tracking
- Provider ratings and feedback

## Security Features

- **Token-based access** - 256-bit random tokens
- **Time-limited links** - 30-day expiration
- **View tracking** - Monitor access patterns
- **Optional authentication** - Extra PIN verification
- **HTTPS enforcement** - Secure transmission
- **Audit logging** - Complete activity trail
- **Permission checks** - Role-based access control

## Database Schema

```
Referral
├── referral_number (unique)
├── access_token (unique, secure)
├── patient (FK)
├── referring_user (FK)
├── referring_facility (FK)
├── receiving_facility (FK)
├── dental_screening (FK, optional)
├── dietary_screening (FK, optional)
├── status (choice field)
├── urgency (choice field)
├── delivery_method (choice field)
├── delivery_status (choice field)
└── timestamps (created, sent, acknowledged, completed)

ReferralDeliveryLog
├── referral (FK)
├── method (choice field)
├── status (success/failed)
├── error_message
├── response_data (JSON)
└── attempted_at

ReferralComment
├── referral (FK)
├── author (FK, optional)
├── author_name
├── comment
├── is_internal
└── created_at

ReferralAttachment
├── referral (FK)
├── file
├── filename
├── file_type
├── uploaded_by (FK)
└── uploaded_at
```

## Testing

### Manual Testing Steps

1. **Create a test clinic**
   - Set referral preferences
   - Add your email as referral_email

2. **Create a test referral**
   - Should generate referral number
   - Should attempt delivery
   - Check email for notification

3. **Test portal access**
   - Copy access token from database
   - Visit `/referrals/view/{token}/`
   - Verify patient data displays
   - Try acknowledging

4. **Test internal referrals**
   - Link a user to a clinic
   - Send referral to that clinic
   - Check user notifications

5. **Test failed delivery retry**
   - Set invalid email
   - Create referral
   - Run: `python manage.py retry_failed_referrals`

## Troubleshooting

### Emails not sending
- Check EMAIL_BACKEND setting
- Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
- Check spam folder
- Review delivery logs in admin

### Referral not created
- Check migrations are applied
- Verify user has associated facility
- Check form validation errors

### Portal link not working
- Verify SITE_URL in settings
- Check token hasn't expired
- Ensure referral status is not 'draft'

### Delivery fails
- Check ReferralDeliveryLog in admin
- Verify clinic configuration
- Check error messages in logs

## Support

For issues or questions:
1. Check delivery logs in Django admin
2. Review error messages in terminal
3. Check `referrals/services.py` logging output
4. Verify clinic configuration

## License

Part of the OralSmart healthcare management system.
