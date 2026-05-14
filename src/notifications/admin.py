from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'notification_type',
        'title',
        'is_read',
        'created_at',
        'read_at'
    ]
    list_filter = [
        'notification_type',
        'is_read',
        'created_at'
    ]
    search_fields = [
        'user__username',
        'user__email',
        'title',
        'message'
    ]
    readonly_fields = ['created_at', 'read_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Recipient', {
            'fields': ('user',)
        }),
        ('Content', {
            'fields': ('notification_type', 'title', 'message', 'action_url')
        }),
        ('Related Objects', {
            'fields': ('referral',)
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        self.message_user(request, f'{updated} notification(s) marked as read.')
    mark_as_read.short_description = "Mark selected as read"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.filter(is_read=True).update(
            is_read=False,
            read_at=None
        )
        self.message_user(request, f'{updated} notification(s) marked as unread.')
    mark_as_unread.short_description = "Mark selected as unread"
