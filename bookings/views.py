from django.shortcuts import render
from .models import BookingTimeSlot

def index(request):
    slots = BookingTimeSlot.objects.all()
    return render(request, 'index.html', {'slots': slots })
