"""
Add the following at the end of facility/views.py
"""

def get_working_hours_api(request):
    """
    API endpoint to get working hours constraints for a clinic or practitioner.
    Used by frontend to restrict date/time pickers.
    """
    clinic_id = request.GET.get('clinic_id')
    practitioner_id = request.GET.get('practitioner_id')
    
    clinic = None
    practitioner = None
    
    try:
        if clinic_id:
            clinic = Clinic.objects.get(id=clinic_id)
        elif practitioner_id:
            practitioner = Profile.objects.get(id=practitioner_id)
    except (Clinic.DoesNotExist, Profile.DoesNotExist):
        return JsonResponse({'error': 'Clinic or practitioner not found'}, status=404)
    
    constraints = get_working_constraints(clinic, practitioner)
    
    return JsonResponse({
        'working_days': constraints['working_days'],
        'start_time': constraints['start_time'].strftime('%H:%M'),
        'end_time': constraints['end_time'].strftime('%H:%M'),
        'formatted': format_working_hours(clinic, practitioner)
    })
