from django.db import models
from django.utils import timezone

class TimeSlot(models.Model):
    datetime = models.DateTimeField()
    is_booked = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Slot: {self.datetime.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['datetime']

class Booking(models.Model):
    time_slot = models.OneToOneField(TimeSlot, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    notes = models.TextField(blank=True, null=True)
    booking_date = models.DateTimeField(default=timezone.now)
    
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')

    def __str__(self):
        return f"Booking: {self.customer_name} - {self.time_slot.datetime.strftime('%Y-%m-%d %H:%M')}"
