# ----------------------------------------------------------------------
# Django Views (tips/views.py)
# Public view to fetch and group tips for display.
# ----------------------------------------------------------------------

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import TipCategory, HealthTip

def tips_list(request):
    """
    Displays all health tips grouped by their category.
    Public access - no login required.
    """
    try:
        # Fetch categories and their related tips in one query
        categories = TipCategory.objects.prefetch_related('tips').all()
    except Exception as e:
        # Fallback for when database isn't set up yet
        categories = []
    
    context = {
        'categories': categories,
        'page_title': "Verified Health Tips"
    }
    return render(request, 'tips/tips_list.html', context)
