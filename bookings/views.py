from django.contrib.auth.decorators import user_passes_test

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
from datetime import datetime
from .models import BookingTimeSlot, Booking
import json

# Staff dashboard: calendar and slot management
@user_passes_test(lambda u: u.is_staff)
def staff_dashboard(request):
    from .models import BookableItem, BookingTimeSlot, Booking
    from datetime import timedelta
    import json
    message = None
    # Get all slots for calendar
    all_slots = BookingTimeSlot.objects.select_related('bookable_item').all()
    # Prepare slot data for FullCalendar
    slot_events = []
    for slot in all_slots:
        status = 'Booked' if hasattr(slot, 'booking') and Booking.objects.filter(time_slot=slot).exists() else 'Available'
        slot_events.append({
            'title': f"{slot.bookable_item.name} ({status})",
            'start': slot.time_start.strftime('%Y-%m-%dT%H:%M:%S'),
            'end': (slot.time_start + slot.time_length).strftime('%Y-%m-%dT%H:%M:%S'),
            'extendedProps': {
                'status': status,
                'table': slot.bookable_item.name,
                'slot_id': slot.id
            }
        })
    return render(request, "staff_dashboard.html", {
        "slot_events": json.dumps(slot_events),
        "message": message
    })

def index(request):
    return render(request, 'index.html')


@require_http_methods(["GET", "DELETE"])
@csrf_exempt
def user_bookings(request):
    """
    Return user's current and future bookings as a partial template.
    Handle booking deletion via DELETE request.
    """
    if not request.user.is_authenticated:
        if request.method == 'DELETE':
            return JsonResponse({
                'success': False,
                'error': 'Authentication required'
            }, status=401)
        return render(request, 'user-bookings.html', {'user_bookings': []})
    
    # Handle DELETE request
    if request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            booking_id = data.get('booking_id')
            
            if not booking_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Booking ID is required'
                }, status=400)
            
            # Get the booking and ensure it belongs to the current user
            booking = get_object_or_404(Booking, id=booking_id, user=request.user)
            
            # Use transaction to ensure atomicity
            with transaction.atomic():
                # Get the time slot before deleting the booking
                time_slot = booking.time_slot
                
                # Delete the booking
                booking.delete()
                
                # Update the time slot status back to available
                time_slot.status = 'available'
                time_slot.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Booking cancelled successfully!',
                'slot_time': time_slot.time_start.strftime('%Y-%m-%d %H:%M'),
                'bookable_item': time_slot.bookable_item.name
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'An error occurred: {str(e)}'
            }, status=500)
    
    # Handle GET request (display bookings)
    get_user_bookings = Booking.objects.filter(
        user=request.user,
        time_slot__time_start__gte=timezone.now()
    ).select_related('time_slot__bookable_item').order_by('time_slot__time_start')
    
    return render(request, 'user-bookings.html', {
        'user_bookings': get_user_bookings
    })


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


@login_required
@require_http_methods(["GET", "POST"])
@csrf_exempt
def book_time_slot(request):
    """
    Handle booking a time slot via AJAX request.
    """
    try:
        data = json.loads(request.body)
        slot_id = data.get('slot_id')
        
        if not slot_id:
            return JsonResponse({
                'success': False,
                'error': 'Slot ID is required'
            }, status=400)
        
        # Get the time slot
        time_slot = get_object_or_404(BookingTimeSlot, id=slot_id)
        
        # Check if slot is available
        if not time_slot.is_available():
            return JsonResponse({
                'success': False,
                'error': 'This time slot is no longer available'
            }, status=400)
        
        # Use transaction to ensure atomicity
        with transaction.atomic():
            # Create the booking
            booking = Booking.objects.create(
                user=request.user,
                time_slot=time_slot
            )
            
            # Update the time slot status
            time_slot.status = 'booked'
            time_slot.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Booking confirmed successfully!',
            'booking_id': booking.id,
            'slot_time': time_slot.time_start.strftime('%Y-%m-%d %H:%M'),
            'bookable_item': time_slot.bookable_item.name
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)
