from django.contrib.auth.decorators import user_passes_test

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
from datetime import datetime
from .models import BookingTimeSlot, Booking, BookableItem
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

# Staff dashboard view.


# Add these views to your existing views.py file

@user_passes_test(lambda u: u.is_staff)
@csrf_exempt
@require_http_methods(["POST"])
def staff_create_slot(request):
    """
    Staff can create new time slots for bookable items
    """
    try:
        data = json.loads(request.body)
        
        # Get data from the form
        table_name = data.get('table', '').strip()
        date_str = data.get('date')
        start_time = data.get('start_time')
        duration_minutes = data.get('duration', 60)
        
        if not all([table_name, date_str, start_time]):
            return JsonResponse({
                'success': False,
                'error': 'Table name, date, and start time are required'
            }, status=400)
        
        # Get or create the bookable item
        bookable_item, created = BookableItem.objects.get_or_create(
            name=table_name,
            defaults={
                'capacity': 1,
                'info': f'Created via staff dashboard',
                'is_active': True
            }
        )
        
        # Parse the datetime
        try:
            # Combine date and time
            datetime_str = f"{date_str}T{start_time}"
            start_datetime = datetime.fromisoformat(datetime_str)
            # Make timezone aware if needed
            if timezone.is_naive(start_datetime):
                start_datetime = timezone.make_aware(start_datetime)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid date or time format'
            }, status=400)
        
        # Create duration
        from datetime import timedelta
        duration = timedelta(minutes=int(duration_minutes))
        
        # Check if slot already exists at this time
        existing_slot = BookingTimeSlot.objects.filter(
            bookable_item=bookable_item,
            time_start=start_datetime
        ).first()
        
        if existing_slot:
            return JsonResponse({
                'success': False,
                'error': 'A slot already exists for this item at this time'
            }, status=400)
        
        # Create the new slot
        new_slot = BookingTimeSlot.objects.create(
            bookable_item=bookable_item,
            time_start=start_datetime,
            time_length=duration,
            status='available'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Time slot created successfully for {table_name}',
            'slot_id': new_slot.id
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


@user_passes_test(lambda u: u.is_staff)
@csrf_exempt
@require_http_methods(["DELETE"])
def staff_cancel_booking(request):
    """
    Staff can cancel any user's booking
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
        
        # Check if there's a booking for this slot
        booking = Booking.objects.filter(time_slot=time_slot).first()
        
        if not booking:
            return JsonResponse({
                'success': False,
                'error': 'No booking found for this slot'
            }, status=400)
        
        # Use transaction to ensure atomicity
        with transaction.atomic():
            # Delete the booking
            booking.delete()
            
            # Update the time slot status back to available
            time_slot.status = 'available'
            time_slot.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Booking cancelled successfully'
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


@user_passes_test(lambda u: u.is_staff)
@csrf_exempt
@require_http_methods(["POST"])
def staff_book_slot(request):
    """
    Staff can book a slot for walk-in customers or phone bookings
    """
    try:
        data = json.loads(request.body)
        slot_id = data.get('slot_id')
        customer_name = data.get('customer_name', 'Walk-in Customer')
        
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
            # Create the booking (staff books on behalf of customer)
            booking = Booking.objects.create(
                user=request.user,  # Staff member who made the booking
                time_slot=time_slot,
                notes=f'Booked by staff for: {customer_name}'
            )
            
            # Update the time slot status
            time_slot.status = 'booked'
            time_slot.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Slot booked for {customer_name}',
            'booking_id': booking.id,
            'customer_name': customer_name
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



@user_passes_test(lambda u: u.is_staff)
def staff_dashboard(request):
    from .models import BookableItem, BookingTimeSlot, Booking
    import json
    
    # Get all slots for calendar
    all_slots = BookingTimeSlot.objects.select_related('bookable_item').all()
    
    # Prepare slot data for FullCalendar
    slot_events = []
    for slot in all_slots:
        # Check if there's a booking for this slot
        booking = Booking.objects.filter(time_slot=slot).first()
        is_booked = booking is not None
        status = 'Booked' if is_booked else 'Available'
        
        # Extract customer name from booking notes if it exists
        customer_name = None
        if booking:
            if 'Booked by staff for:' in booking.notes:
                customer_name = booking.notes.replace('Booked by staff for:', '').strip()
            else:
                customer_name = booking.user.username
        
        slot_events.append({
            'title': f"{slot.bookable_item.name} ({status})",
            'start': slot.time_start.strftime('%Y-%m-%dT%H:%M:%S'),
            'end': (slot.time_start + slot.time_length).strftime('%Y-%m-%dT%H:%M:%S'),
            'extendedProps': {
                'status': status,
                'table': slot.bookable_item.name,
                'slot_id': slot.id,
                'is_booked': is_booked,
                'booking_user': customer_name if customer_name else (booking.user.username if booking else None)
            }
        })
    
    return render(request, "staff_dashboard.html", {
        "slot_events": json.dumps(slot_events)
    })

@user_passes_test(lambda u: u.is_staff)
@csrf_exempt
@require_http_methods(["POST"])
def staff_create_template_slots(request):
    """
    Staff can create multiple time slots from a template
    """
    try:
        data = json.loads(request.body)
        slots_data = data.get('slots', [])
        
        if not slots_data:
            return JsonResponse({
                'success': False,
                'error': 'No slots data provided'
            }, status=400)
        
        created_slots = []
        skipped_slots = []
        
        # Use transaction to ensure all slots are created or none
        with transaction.atomic():
            for slot_data in slots_data:
                table_name = slot_data.get('table', '').strip()
                date_str = slot_data.get('date')
                start_time = slot_data.get('start_time')
                duration_minutes = slot_data.get('duration', 60)
                
                if not all([table_name, date_str, start_time]):
                    continue  # Skip invalid slots
                
                # Get or create the bookable item
                bookable_item, created = BookableItem.objects.get_or_create(
                    name=table_name,
                    defaults={
                        'capacity': 1,
                        'info': f'Created via staff template',
                        'is_active': True
                    }
                )
                
                # Parse the datetime
                try:
                    datetime_str = f"{date_str}T{start_time}"
                    start_datetime = datetime.fromisoformat(datetime_str)
                    if timezone.is_naive(start_datetime):
                        start_datetime = timezone.make_aware(start_datetime)
                except ValueError:
                    continue  # Skip invalid datetime
                
                # Create duration
                from datetime import timedelta
                duration = timedelta(minutes=int(duration_minutes))
                
                # Check if slot already exists at this time
                existing_slot = BookingTimeSlot.objects.filter(
                    bookable_item=bookable_item,
                    time_start=start_datetime
                ).first()
                
                if existing_slot:
                    skipped_slots.append(f"{table_name} at {start_time}")
                    continue
                
                # Create the new slot
                new_slot = BookingTimeSlot.objects.create(
                    bookable_item=bookable_item,
                    time_start=start_datetime,
                    time_length=duration,
                    status='available'
                )
                created_slots.append(new_slot)
        
        message = f'Created {len(created_slots)} slots successfully'
        if skipped_slots:
            message += f'. Skipped {len(skipped_slots)} existing slots'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'created_count': len(created_slots),
            'skipped_count': len(skipped_slots)
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