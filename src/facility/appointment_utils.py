"""
Utility functions for appointment scheduling and validation
"""
from datetime import datetime, time, timedelta
from django.utils import timezone


def get_working_constraints(clinic=None, practitioner=None):
    """
    Get working day and time constraints from clinic or practitioner.
    Returns dict with working_days, start_time, end_time
    """
    # Default constraints (Monday-Friday, 8 AM - 5 PM)
    constraints = {
        'working_days': [0, 1, 2, 3, 4],  # Mon-Fri
        'start_time': time(8, 0),
        'end_time': time(17, 0),
    }
    
    if clinic:
        constraints['working_days'] = clinic.get_working_days()
        constraints['start_time'] = clinic.opening_time
        constraints['end_time'] = clinic.closing_time
    elif practitioner and practitioner.affiliated_facility:
        # Use practitioner's facility constraints
        constraints['working_days'] = practitioner.affiliated_facility.get_working_days()
        constraints['start_time'] = practitioner.work_start_time or practitioner.affiliated_facility.opening_time
        constraints['end_time'] = practitioner.work_end_time or practitioner.affiliated_facility.closing_time
    elif practitioner:
        # Use practitioner's own constraints if no facility
        constraints['working_days'] = practitioner.working_days if practitioner.working_days else [0, 1, 2, 3, 4]
        constraints['start_time'] = practitioner.work_start_time or time(8, 0)
        constraints['end_time'] = practitioner.work_end_time or time(17, 0)
    
    return constraints


def is_valid_appointment_datetime(appointment_datetime, clinic=None, practitioner=None):
    """
    Validate if an appointment datetime falls within working constraints.
    Returns tuple: (is_valid, error_message)
    """
    if not appointment_datetime:
        return False, "Appointment date and time required"
    
    # Ensure timezone aware
    if timezone.is_naive(appointment_datetime):
        appointment_datetime = timezone.make_aware(appointment_datetime)
    
    # Check if appointment is in the past
    if appointment_datetime < timezone.now():
        return False, "Appointment cannot be in the past"
    
    # Get constraints
    constraints = get_working_constraints(clinic, practitioner)
    
    # Check if it's a working day
    if appointment_datetime.weekday() not in constraints['working_days']:
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        working_day_names = [day_names[d] for d in constraints['working_days']]
        return False, f"Appointments only available on: {', '.join(working_day_names)}"
    
    # Check if time is within working hours
    appointment_time = appointment_datetime.time()
    if not (constraints['start_time'] <= appointment_time <= constraints['end_time']):
        return False, f"Appointments available between {constraints['start_time'].strftime('%H:%M')} and {constraints['end_time'].strftime('%H:%M')}"
    
    return True, ""


def get_next_available_slots(clinic=None, practitioner=None, num_days=14, slots_per_day=8):
    """
    Generate list of next available appointment slots.
    Returns list of datetime objects.
    """
    constraints = get_working_constraints(clinic, practitioner)
    slots = []
    
    current_date = timezone.now().date()
    days_checked = 0
    
    while len(slots) < slots_per_day * num_days and days_checked < 60:
        days_checked += 1
        check_date = current_date + timedelta(days=days_checked)
        
        # Skip non-working days
        if check_date.weekday() not in constraints['working_days']:
            continue
        
        # Generate slots for this day
        start_time = constraints['start_time']
        end_time = constraints['end_time']
        
        # Calculate slot duration (e.g., hourly slots)
        total_hours = (datetime.combine(check_date, end_time) - datetime.combine(check_date, start_time)).seconds / 3600
        slot_duration = max(1, int(total_hours / slots_per_day))  # At least 1 hour per slot
        
        current_time = start_time
        while current_time < end_time:
            slot_datetime = timezone.make_aware(datetime.combine(check_date, current_time))
            
            # Only add future slots
            if slot_datetime > timezone.now():
                slots.append(slot_datetime)
            
            # Move to next slot
            current_datetime = datetime.combine(check_date, current_time)
            current_datetime += timedelta(hours=slot_duration)
            current_time = current_datetime.time()
            
            if current_time >= end_time:
                break
    
    return slots[:slots_per_day * num_days]


def format_working_hours(clinic=None, practitioner=None):
    """
    Format working hours as human-readable string.
    """
    constraints = get_working_constraints(clinic, practitioner)
    
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    working_day_names = [day_names[d] for d in sorted(constraints['working_days'])]
    
    days_str = ', '.join(working_day_names)
    time_str = f"{constraints['start_time'].strftime('%H:%M')} - {constraints['end_time'].strftime('%H:%M')}"
    
    return f"{days_str}, {time_str}"
