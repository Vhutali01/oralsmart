from django.contrib import admin
from .models import Referral, ReferralDeliveryLog, ReferralComment, ReferralAttachment


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = [
        'referral_number',
        'patient',
        'referring_facility',
        'receiving_facility',
        'urgency',
        'status',
        'delivery_status',
        'created_at',
        'sent_at'
    ]
    list_filter = [
        'status',
        'urgency',
        'delivery_status',
        'specialty_required',
        'created_at',
        'sent_at'
    ]
    search_fields = [
        'referral_number',
        'patient__name',
        'patient__surname',
        'referring_facility__name',
        'receiving_facility__name',
        'reason'
    ]
    readonly_fields = [
        'referral_number',
        'access_token',
        'created_at',
        'updated_at',
        'sent_at',
        'acknowledged_at',
        'completed_at',
        'view_count',
        'last_viewed_at',
        'delivery_attempts',
        'last_delivery_attempt'
    ]
    fieldsets = (
        ('Identification', {
            'fields': ('referral_number', 'access_token')
        }),
        ('Patient Information', {
            'fields': ('patient', 'dental_screening', 'dietary_screening')
        }),
        ('Referral Details', {
            'fields': (
                'reason',
                'clinical_summary',
                'urgency',
                'specialty_required',
                'patient_preferences',
                'insurance_information'
            )
        }),
        ('Referring Provider', {
            'fields': ('referring_user', 'referring_facility')
        }),
        ('Receiving Provider', {
            'fields': (
                'receiving_facility',
                'receiving_user',
                'external_provider_name',
                'external_provider_email',
                'external_provider_phone'
            )
        }),
        ('Delivery Tracking', {
            'fields': (
                'delivery_method',
                'delivery_status',
                'delivery_attempts',
                'last_delivery_attempt',
                'delivery_error'
            )
        }),
        ('Status & Timestamps', {
            'fields': (
                'status',
                'created_at',
                'updated_at',
                'sent_at',
                'acknowledged_at',
                'appointment_date',
                'completed_at',
                'expires_at'
            )
        }),
        ('Portal Access', {
            'fields': (
                'view_count',
                'last_viewed_at',
                'allow_comments',
                'notifications_enabled'
            )
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'patient',
            'referring_user',
            'referring_facility',
            'receiving_facility',
            'receiving_user'
        )


@admin.register(ReferralDeliveryLog)
class ReferralDeliveryLogAdmin(admin.ModelAdmin):
    list_display = [
        'referral',
        'method',
        'status',
        'attempted_at'
    ]
    list_filter = [
        'method',
        'status',
        'attempted_at'
    ]
    search_fields = [
        'referral__referral_number',
        'error_message'
    ]
    readonly_fields = [
        'referral',
        'method',
        'status',
        'error_message',
        'response_data',
        'attempted_at'
    ]
    
    def has_add_permission(self, request):
        return False


@admin.register(ReferralComment)
class ReferralCommentAdmin(admin.ModelAdmin):
    list_display = [
        'referral',
        'get_author_name',
        'is_internal',
        'created_at'
    ]
    list_filter = [
        'is_internal',
        'created_at'
    ]
    search_fields = [
        'referral__referral_number',
        'author__username',
        'author_name',
        'comment'
    ]
    readonly_fields = ['created_at']
    
    def get_author_name(self, obj):
        return obj.author.get_full_name() if obj.author else obj.author_name
    get_author_name.short_description = 'Author'


@admin.register(ReferralAttachment)
class ReferralAttachmentAdmin(admin.ModelAdmin):
    list_display = [
        'referral',
        'filename',
        'file_type',
        'uploaded_by',
        'uploaded_at'
    ]
    list_filter = [
        'file_type',
        'uploaded_at'
    ]
    search_fields = [
        'referral__referral_number',
        'filename',
        'description'
    ]
    readonly_fields = ['uploaded_at']
