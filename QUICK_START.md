# Quick Start Guide - OralSmart Referral System

## 🚀 Get Started in 3 Steps

### Step 1: Run Migrations (Required)
```bash
cd c:\Users\vhuta\dev\oralsmart\src
python manage.py makemigrations facility referrals
python manage.py migrate
```

### Step 2: Configure Email (Optional but Recommended)
Add to your `.env` file or environment:
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=OralSmart <noreply@oralsmart.com>
SITE_URL=http://localhost:8000
```

### Step 3: Start Using!
```bash
python manage.py runserver
```
Visit: http://localhost:8000/referrals/

---

## 📋 Quick Usage

### Create a Referral
1. Login to OralSmart
2. Go to `/referrals/create/`
3. Fill out:
   - Select patient
   - Choose receiving facility
   - Set urgency
   - Add reason and clinical summary
4. Click "Create and Send Referral"

### View Referrals
- **Your Dashboard**: `/referrals/`
  - Sent tab: Referrals you created
  - Received tab: Referrals for your facility

### External Access (No Login)
Recipients receive an email with a secure link:
```
https://yoursite.com/referrals/view/abc123.../
```
- Valid for 30 days
- Can acknowledge receipt
- Can add comments

---

## 🔧 Configure Clinics

### In Django Admin (`/admin/facility/clinic/`)
1. Edit each clinic
2. Set referral preferences:
   - ✅ `accepts_referrals` = True
   - 📧 `referral_email` = reception@clinic.com
   - 📨 `email_notification_enabled` = True
   - 🎯 `preferred_method` = email

---

## 🎨 Add to Navigation

Update your `base.html`:
```html
{% if user.is_authenticated %}
<li class="nav-item">
    <a class="nav-link" href="{% url 'referrals:list' %}">
        <i class="fas fa-exchange-alt"></i> Referrals
    </a>
</li>
{% endif %}
```

---

## ✅ Verify Installation

### Check if Working:
```bash
# Test imports
python manage.py shell
>>> from referrals.models import Referral
>>> print("Success!")
```

### Access Points:
- **Admin**: http://localhost:8000/admin/referrals/
- **List**: http://localhost:8000/referrals/
- **Create**: http://localhost:8000/referrals/create/

---

## 🆘 Troubleshooting

### "Table doesn't exist"
→ Run migrations: `python manage.py migrate`

### "No such URL pattern"
→ Check `oralsmart/urls.py` includes: `path('referrals/', include('referrals.urls'))`

### Emails not sending
→ Check `EMAIL_BACKEND` and `EMAIL_HOST_USER` in settings

### Can't see referrals
→ Ensure user has associated facility in admin

---

## 📊 Features Enabled

✅ Multiple delivery methods (email, API, SMS, portal)
✅ Automatic fallback if one method fails
✅ Secure portal for external viewing
✅ Two-way communication via comments
✅ Complete audit trail
✅ Status tracking (draft → sent → acknowledged → completed)
✅ Urgent/emergency flagging
✅ Automatic retry for failed deliveries

---

## 📚 Full Documentation

- **Complete Guide**: `REFERRAL_SYSTEM_README.md`
- **Validation Report**: `VALIDATION_CHECKLIST.md`
- **Existing System**: `REFERRAL_SYSTEM_README.md` (in root)

---

## 🎉 That's It!

You're ready to manage referrals. The system handles:
- ✅ Email notifications automatically
- ✅ Secure link generation
- ✅ Delivery tracking
- ✅ Status updates
- ✅ Provider communication

Just run migrations and start creating referrals! 🚀
