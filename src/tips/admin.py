from django.contrib import admin
from .models import TipCategory, HealthTip

@admin.register(TipCategory)
class TipCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'icon_class']
    search_fields = ['name', 'description']
    ordering = ['name']

@admin.register(HealthTip)
class HealthTipAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_critical', 'citation_source', 'last_updated']
    list_filter = ['category', 'is_critical', 'last_updated']
    search_fields = ['title', 'summary', 'full_text', 'citation_source']
    ordering = ['category', '-is_critical', 'title']
    fieldsets = (
        ('Content', {
            'fields': ('category', 'title', 'summary', 'full_text', 'audio_file')
        }),
        ('Academic & Legal Compliance', {
            'fields': ('citation_source', 'citation_url', 'is_critical')
        }),
        ('Metadata', {
            'fields': ('last_updated',),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ('last_updated',)
