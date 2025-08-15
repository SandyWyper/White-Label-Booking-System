from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User


class BookableItem(models.Model):
    """
    Represents a resource that can be reserved (e.g., table, dentist chair, tennis court, tee time).
    """
    name = models.CharField(max_length=200, help_text="Name of the bookable item")
    capacity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Number of people or reservations this item can accommodate at one time"
    )
    info = models.TextField(
        blank=True,
        help_text="Additional descriptive information (e.g., location, special features)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text="Whether this item is available for booking")

    class Meta:
        ordering = ['name']
        verbose_name = "Bookable Item"
        verbose_name_plural = "Bookable Items"

    def __str__(self):
        return self.name


class BookingTimeSlot(models.Model):
    """
    Represents a specific time period during which a bookable item can be reserved.
    """
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('pending', 'Pending'),
        ('booked', 'Booked'),
    ]

    bookable_item = models.ForeignKey(
        BookableItem,
        on_delete=models.CASCADE,
        related_name='time_slots',
        help_text="The bookable item this time slot belongs to"
    )
    time_start = models.DateTimeField(help_text="Start time of the booking slot")
    time_length = models.DurationField(help_text="Length of the time slot (e.g., 30 minutes, 1 hour)")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='available',
        help_text="Current booking status of the time slot"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['time_start']
        verbose_name = "Booking Time Slot"
        verbose_name_plural = "Booking Time Slots"
        unique_together = ['bookable_item', 'time_start']  # Prevent duplicate slots for same item at same time

    def __str__(self):
        return f"{self.bookable_item.name} - {self.time_start.strftime('%Y-%m-%d %H:%M')} ({self.get_status_display()})"

    @property
    def time_end(self):
        """Calculate the end time of the slot."""
        return self.time_start + self.time_length

    def is_available(self):
        """Check if this time slot is available for booking."""
        return self.status == 'available'


class Booking(models.Model):
    """
    Represents a confirmed booking made by a user for a specific time slot.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings',
        help_text="The user who made this booking"
    )
    time_slot = models.OneToOneField(
        BookingTimeSlot,
        on_delete=models.CASCADE,
        related_name='booking',
        help_text="The time slot that was booked"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes or special requests for the booking"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"

    def __str__(self):
        return f"{self.user.username} - {self.time_slot.bookable_item.name} on {self.time_slot.time_start.strftime('%Y-%m-%d %H:%M')}"

    @property
    def bookable_item(self):
        """Get the bookable item for this booking."""
        return self.time_slot.bookable_item

    @property
    def start_time(self):
        """Get the start time for this booking."""
        return self.time_slot.time_start

    @property
    def end_time(self):
        """Get the end time for this booking."""
        return self.time_slot.time_end