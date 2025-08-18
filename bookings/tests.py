from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import BookingTimeSlot, BookableItem, Booking
from datetime import datetime, timedelta
import json


class BookingAppTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.admin = User.objects.create_superuser(username='admin', password='adminpass', email='admin@example.com')
        self.item = BookableItem.objects.create(name='Table 1', capacity=4)
        self.slot = BookingTimeSlot.objects.create(
            bookable_item=self.item,
            time_start=datetime(2025, 8, 18, 12, 0),
            time_length=timedelta(hours=1),
            status='available'
        )

    def test_user_can_book_slot(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(
            reverse('bookings:book_time_slot'),
            data=json.dumps({'slot_id': self.slot.id}),
            content_type='application/json'
        )
        # print(response.content.decode())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Booking.objects.filter(user=self.user, time_slot=self.slot).exists())
        

    def test_admin_can_view_bookings(self):
        Booking.objects.create(user=self.admin, time_slot=self.slot)
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('bookings:user_bookings'))
        # print(response.content.decode())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user-bookings.html')
        self.assertContains(response, 'Aug. 18, 2025, noon')
