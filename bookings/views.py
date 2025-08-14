from django.shortcuts import render
from .models import BookingTimeSlot

def index(request):
	return render(request, 'index.html')

def get_bookings_slots(request):
    slots = BookingTimeSlot.objects.all()
    return render(request, 'index.html', {'slots': slots})