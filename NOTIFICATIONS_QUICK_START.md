# Quick Start Guide - In-App Notifications

## 🚀 Start Using Notifications

### 1. Start the Server
```bash
cd src
python manage.py runserver
```

### 2. Access the Application
Open your browser to: `http://127.0.0.1:8000`

### 3. Look for the Bell Icon
- Top-right corner of navbar (next to profile picture)
- Red badge shows unread count
- Click to see recent notifications

### 4. Test the System

#### Option A: Create a Test Referral
1. Go to "New patient" and create a patient
2. Go to "Referrals" tab
3. Click "Create Referral" 
4. Select a facility with associated users
5. Fill in referral details
6. Submit

#### Option B: Use Test Script
```bash
cd src
Get-Content test_notifications.py | python manage.py shell
```

### 5. Check Notifications
- Bell icon should show a badge with count
- Click bell to see dropdown with notifications
- Click "View all notifications" for full page
- Go to "Received Referrals" tab to see visual indicators

## 🔍 What to Look For

### In Navbar:
- 🔔 Bell icon with red badge (if unread)
- Dropdown with 5 most recent notifications
- Color-coded by urgency

### In Received Referrals Tab:
- Badge on tab showing count
- Bold text for unread referrals
- Colored left borders (red=emergency, yellow=urgent)
- "NEW" badges
- Blue dots on unread items

### Visual Indicators:
- **Emergency**: Red background, ⚠️ icon
- **Urgent**: Yellow background, ⚠️ icon
- **Routine**: Blue/info styling
- **Unread**: Bold, colored border, dot indicator
- **Read**: Normal styling

## 📱 User Actions

### Mark as Read:
- Click notification in dropdown → auto marks as read
- Click "Mark all as read" button
- Visit referral detail page → marks related notification as read

### View All Notifications:
- Click "View all notifications" in dropdown
- Or visit `/notifications/`

### Filter Notifications:
On notifications page:
- Toggle "Show read notifications"
- Filter by type (dropdown)

## 🔧 Admin Features

### Django Admin:
Visit `/admin/notifications/notification/` to:
- View all notifications
- Filter by user, type, read status
- Bulk mark as read/unread
- Delete old notifications

### Management:
Clean up old notifications:
```python
from notifications.models import Notification
Notification.cleanup_old_read_notifications(days=30)
```

## 🎯 Key URLs

| URL | Purpose |
|-----|---------|
| `/patient_list/` | Main page with referrals tabs |
| `/notifications/` | Full notifications page |
| `/notifications/api/count/` | Get unread count (JSON) |
| `/notifications/api/list/` | Get recent notifications (JSON) |
| `/admin/notifications/notification/` | Admin interface |

## ⚙️ Customization

### Change Polling Interval:
In `templates/navbar2.html`:
```javascript
// Change 30000 (30 seconds) to desired milliseconds
setInterval(loadNotifications, 30000);
```

### Adjust Notification Limit:
In `notifications/views.py`:
```python
# Change limit default from 10 to desired number
limit = int(request.GET.get('limit', 10))
```

## 🐛 Common Issues

**Problem**: Bell icon not showing  
**Solution**: Clear browser cache, check if logged in

**Problem**: Badge not updating  
**Solution**: Check browser console for errors, verify JavaScript is running

**Problem**: Notifications not appearing for new referrals  
**Solution**: Ensure receiving facility has associated users

**Problem**: Dropdown empty  
**Solution**: Check API endpoint `/notifications/api/list/` works

## 📞 Testing Checklist

- [ ] Bell icon visible in navbar
- [ ] Badge shows correct unread count
- [ ] Dropdown opens and shows notifications
- [ ] Clicking notification navigates to referral
- [ ] "Mark all as read" works
- [ ] Badge updates after marking as read
- [ ] Received referrals tab shows visual indicators
- [ ] Emergency referrals highlighted in red
- [ ] Urgent referrals highlighted in yellow
- [ ] Polling updates badge every 30 seconds
- [ ] Full notifications page works
- [ ] Filters work on notifications page

## 💡 Tips

1. **First Time Setup**: Run migrations first: `python manage.py migrate`
2. **Testing**: Use the test script to quickly create test notifications
3. **Performance**: System uses database indexes for fast queries
4. **Mobile**: UI is fully responsive on mobile devices
5. **Security**: All API endpoints are login-required and CSRF-protected

---

**Need Help?** Check `IN_APP_NOTIFICATIONS_SUMMARY.md` for detailed documentation.
