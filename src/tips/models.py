# ----------------------------------------------------------------------
# Django Models (tips/models.py)
# Implements the "Established Facts" Sourcing Hierarchy
# ----------------------------------------------------------------------

from django.db import models
from django.utils import timezone

class TipCategory(models.Model):
    """
    Defines broad categories for health tips, linked to the SA burden of disease.
    e.g., 'Infectious Diseases', 'Nutrition (FBDG)', 'Mental Health'.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon_class = models.CharField(
        max_length=50,
        default='fa-info-circle',
        help_text="Font Awesome class for pictorial navigation (e.g., 'fa-leaf')"
    )

    class Meta:
        verbose_name_plural = "Tip Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class HealthTip(models.Model):
    """
    Core model for verified health advice, enforcing academic rigour and compliance.
    """
    category = models.ForeignKey(TipCategory, on_delete=models.CASCADE, related_name='tips')
    
    # Content fields - text must be Grade 8 reading level max for accessibility [3]
    title = models.CharField(max_length=150, help_text="Simple, actionable title.")
    summary = models.TextField(max_length=250, help_text="Short summary for list views.")
    full_text = models.TextField(help_text="Full tip details. Must be simple and unambiguous.")
    
    # Multimedia field for low-literacy compliance [1, 2]
    audio_file = models.FileField(
        upload_to='tip_audio/',
        null=True,
        blank=True,
        help_text="Mandatory audio narration of the tip text for low-literacy users."
    )

    # Academic and Legal Compliance Fields
    citation_source = models.CharField(
        max_length=200,
        help_text="Primary source authority (e.g., 'NDOH FBDG', 'NICD Protocol', 'SAMRC Report')."
    )
    citation_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Direct link to the established fact source document."
    )
    last_updated = models.DateTimeField(default=timezone.now)
    is_critical = models.BooleanField(
        default=False,
        help_text="Flag for tips requiring immediate visibility (e.g., emergency contacts)."
    )
    
    class Meta:
        ordering = ['category', '-is_critical', 'title']
        verbose_name_plural = "Health Tips (Verified)"

    def __str__(self):
        return self.title
