from django.shortcuts import render
from django.utils import timezone
from datetime import datetime
from .models import BookingTimeSlot

def index(request):
    return render(request, 'index.html')


def available_time_slots(request):
    # Get date from query parameter, default to today if not provided
    date_str = request.GET.get('date')
    
    if date_str:
        try:
            # Parse date string in YYYY-MM-DD format
            filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            # If date format is invalid, default to today
            filter_date = timezone.now().date()
    else:
        # Default to today if no date parameter provided
        filter_date = timezone.now().date()
    
    slots = BookingTimeSlot.objects.filter(time_start__date=filter_date)
    return render(request, 'available-time-slots.html', {
        'slots': slots,
        'selected_date': filter_date
    })
