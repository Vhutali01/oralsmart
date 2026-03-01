"""
Test script for notification system
Run with: python manage.py shell < test_notifications.py
"""
from django.contrib.auth.models import User
from notifications.models import Notification
from referrals.models import Referral
from patient.models import Patient

# Get or create a test user
user = User.objects.first()
if not user:
    print("No users found. Please create a user first.")
    exit()

print(f"Testing notifications for user: {user.username}")

# Create a test notification
notification = Notification.objects.create(
    user=user,
    notification_type='new_referral',
    title='Test Notification',
    message='This is a test notification to verify the system is working correctly.',
    action_url='/patient_list/'
)

print(f"✓ Created test notification: {notification.id}")

# Check notification count
unread_count = Notification.objects.filter(user=user, is_read=False).count()
print(f"✓ Unread notifications for {user.username}: {unread_count}")

# Test marking as read
notification.mark_as_read()
print(f"✓ Marked notification {notification.id} as read")

# Verify it's marked as read
unread_count = Notification.objects.filter(user=user, is_read=False).count()
print(f"✓ Unread notifications after marking as read: {unread_count}")

print("\n✅ Notification system test completed successfully!")
print("\nNext steps:")
print("1. Start the development server: python manage.py runserver")
print("2. Log in with your user account")
print("3. Look for the bell icon in the navbar")
print("4. Try creating a referral to see live notifications")
