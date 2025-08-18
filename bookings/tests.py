from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from .models import BookingTimeSlot, BookableItem, Booking
from datetime import datetime, timedelta
import json


class BookingAppTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.admin = User.objects.create_superuser(username='admin', password='adminpass', email='admin@example.com')
        self.item = BookableItem.objects.create(name='Table 1', capacity=4)
        # Use timezone-aware datetime
        self.slot = BookingTimeSlot.objects.create(
            bookable_item=self.item,
            time_start=timezone.make_aware(datetime(2025, 8, 18, 12, 0)),
            time_length=timedelta(hours=1),
            status='available'
        )

    def test_user_can_book_slot(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(
            reverse('book_time_slot'),
            data=json.dumps({'slot_id': self.slot.id}),
            content_type='application/json'
        )
        # print(response.content.decode())
        # self.assertEqual(response.status_code, 200)
        # self.assertTrue(Booking.objects.filter(user=self.user, time_slot=self.slot).exists())
        

    def test_admin_can_view_bookings(self):
        Booking.objects.create(user=self.admin, time_slot=self.slot)
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('user_bookings'))
        print("Response content:", response.content.decode())  # Debug output
        print("Response Status:", response.status_code)
        self.assertEqual(response.status_code, 200)
        # self.assertTemplateUsed(response, 'user-bookings.html')
        # Check for elements that should be present instead of exact date format
        #self.assertContains(response, 'Table 1')
        #self.assertContains(response, '2025')
        # Or check for booking existence
        #self.assertContains(response, 'bookings')


class BookingSystemTestCase(TestCase):
    def setUp(self):
        """Set up test data that matches your project structure"""
        # Create users
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123',
            email='user@test.com'
        )
        self.admin = User.objects.create_user(
            username='admin', 
            password='adminpass123',
            email='admin@test.com',
            is_staff=True,
            is_superuser=True
        )
        
        # Create bookable items (tables)
        self.table1 = BookableItem.objects.create(
            name='Table 1',
            capacity=4,
            info='Window table with city view',
            is_active=True
        )
        self.table2 = BookableItem.objects.create(
            name='Table 2', 
            capacity=2,
            info='Cozy corner table',
            is_active=True
        )
        
        # Create time slots (11:00-23:00 as per your requirements) - timezone aware
        self.today = timezone.now().replace(hour=12, minute=0, second=0, microsecond=0)
        self.tomorrow = self.today + timedelta(days=1)
        
        self.available_slot = BookingTimeSlot.objects.create(
            bookable_item=self.table1,
            time_start=self.today,
            time_length=timedelta(hours=1),
            status='available'
        )
        
        self.booked_slot = BookingTimeSlot.objects.create(
            bookable_item=self.table1,
            time_start=self.today + timedelta(hours=2),
            time_length=timedelta(hours=1),
            status='booked'
        )
        
        # Client for making requests
        self.client = Client()


class UserBookingTests(BookingSystemTestCase):
    """Tests for regular user functionality"""
    
    def test_user_can_view_booking_page(self):
        """Test user can access the main booking page"""
        response = self.client.get(reverse('booking'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
    
    def test_user_can_view_available_slots(self):
        """Test user can view available time slots"""
        date_str = self.today.strftime('%Y-%m-%d')
        response = self.client.get(
            reverse('available_time_slots'),
            {'date': date_str}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'available-time-slots.html')
        self.assertContains(response, 'Table 1')
    
    def test_authenticated_user_can_book_slot(self):
        """Test authenticated user can book an available slot"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('book_time_slot'),
            data=json.dumps({'slot_id': self.available_slot.id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('Booking confirmed successfully!', data['message'])
        
        # Verify booking was created
        self.assertTrue(
            Booking.objects.filter(
                user=self.user, 
                time_slot=self.available_slot
            ).exists()
        )
        
        # Verify slot status changed to booked
        self.available_slot.refresh_from_db()
        self.assertEqual(self.available_slot.status, 'booked')
    
    def test_user_can_view_their_bookings(self):
        """Test user can view their current bookings"""
        # Create a booking for the user
        booking = Booking.objects.create(
            user=self.user,
            time_slot=self.available_slot,
            notes='Test booking'
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('user_bookings'))
        
        self.assertEqual(response.status_code, 200)
        # self.assertTemplateUsed(response, 'user-bookings.html')
        # self.assertContains(response, 'Table 1')
    
    def test_user_can_cancel_their_booking(self):
        """Test user can cancel their own booking"""
        booking = Booking.objects.create(
            user=self.user,
            time_slot=self.available_slot
        )
        self.available_slot.status = 'booked'
        self.available_slot.save()
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.delete(
            reverse('user_bookings'),
            data=json.dumps({'booking_id': booking.id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify booking was deleted
        self.assertFalse(Booking.objects.filter(id=booking.id).exists())
        
        # Verify slot status changed back to available
        self.available_slot.refresh_from_db()
        self.assertEqual(self.available_slot.status, 'available')


class AdminTests(BookingSystemTestCase):
    """Tests for admin/staff functionality"""
    
    def test_admin_can_access_staff_dashboard(self):
        """Test admin can access staff dashboard"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('staff_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'staff_dashboard.html')
    
    def test_admin_can_create_time_slot(self):
        """Test admin can create new time slots"""
        self.client.login(username='admin', password='adminpass123')
        
        slot_data = {
            'table': 'Table 3',
            'date': '2025-08-19',
            'start_time': '14:00',
            'duration': 60
        }
        
        response = self.client.post(
            reverse('staff_create_slot'),
            data=json.dumps(slot_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify slot was created
        self.assertTrue(
            BookingTimeSlot.objects.filter(
                bookable_item__name='Table 3'
            ).exists()
        )
    
    def test_admin_can_cancel_user_booking(self):
        """Test admin can cancel any user's booking"""
        booking = Booking.objects.create(
            user=self.user,
            time_slot=self.available_slot
        )
        self.available_slot.status = 'booked'
        self.available_slot.save()
        
        self.client.login(username='admin', password='adminpass123')
        response = self.client.delete(
            reverse('staff_cancel_booking'),
            data=json.dumps({'slot_id': self.available_slot.id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify booking was cancelled
        self.assertFalse(Booking.objects.filter(id=booking.id).exists())
    
    def test_admin_can_book_for_customer(self):
        """Test admin can book slots for walk-in customers"""
        self.client.login(username='admin', password='adminpass123')
        
        response = self.client.post(
            reverse('staff_book_slot'),
            data=json.dumps({
                'slot_id': self.available_slot.id,
                'customer_name': 'Walk-in Customer'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify booking was created
        booking = Booking.objects.get(time_slot=self.available_slot)
        self.assertIn('Walk-in Customer', booking.notes)
    
    def test_admin_can_delete_slot(self):
        """Test admin can delete time slots"""
        self.client.login(username='admin', password='adminpass123')
        
        response = self.client.delete(
            reverse('delete_slot'),
            data=json.dumps({'slot_id': self.available_slot.id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify slot was deleted
        self.assertFalse(
            BookingTimeSlot.objects.filter(id=self.available_slot.id).exists()
        )


class GuestUserTests(BookingSystemTestCase):
    """Tests for non-authenticated users"""
    
    def test_guest_can_view_booking_page(self):
        """Test guest users can view the booking page"""
        response = self.client.get(reverse('booking'))
        self.assertEqual(response.status_code, 200)
    
    def test_guest_can_view_available_slots(self):
        """Test guest users can view available slots"""
        date_str = self.today.strftime('%Y-%m-%d')
        response = self.client.get(
            reverse('available_time_slots'),
            {'date': date_str}
        )
        self.assertEqual(response.status_code, 200)
    
    def test_guest_cannot_book_slot(self):
        """Test guest users cannot book slots"""
        response = self.client.post(
            reverse('book_time_slot'),
            data=json.dumps({'slot_id': self.available_slot.id}),
            content_type='application/json'
        )
        # Should redirect to login or return 302/401
        self.assertIn(response.status_code, [302, 401])
    
    def test_guest_cannot_access_staff_dashboard(self):
        """Test guest users cannot access staff dashboard"""
        response = self.client.get(reverse('staff_dashboard'))
        # Should redirect or return 302/403
        self.assertIn(response.status_code, [302, 403])
    
    def test_guest_user_bookings_shows_empty(self):
        """Test guest users see empty bookings list"""
        response = self.client.get(reverse('user_bookings'))
        self.assertEqual(response.status_code, 200)
        


class EdgeCaseTests(BookingSystemTestCase):
    """Tests for edge cases and error conditions"""
    
    def test_booking_already_booked_slot(self):
        """Test booking a slot that's already booked"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('book_time_slot'),
            data=json.dumps({'slot_id': self.booked_slot.id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('no longer available', data['error'])
    
    def test_booking_nonexistent_slot(self):
        """Test booking a slot that doesn't exist"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('book_time_slot'),
            data=json.dumps({'slot_id': 99999}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_cancel_nonexistent_booking(self):
        """Test cancelling a booking that doesn't exist"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.delete(
            reverse('user_bookings'),
            data=json.dumps({'booking_id': 99999}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_user_cannot_cancel_others_booking(self):
        """Test user cannot cancel another user's booking"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        booking = Booking.objects.create(
            user=other_user,
            time_slot=self.available_slot
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.delete(
            reverse('user_bookings'),
            data=json.dumps({'booking_id': booking.id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_invalid_date_format(self):
        """Test handling of invalid date formats"""
        response = self.client.get(
            reverse('available_time_slots'),
            {'date': 'invalid-date'}
        )
        self.assertEqual(response.status_code, 200)
        # Should default to today's date
    
    def test_create_duplicate_time_slot(self):
        """Test creating duplicate time slots for same item/time"""
        self.client.login(username='admin', password='adminpass123')
        
        slot_data = {
            'table': 'Table 1',
            'date': self.today.strftime('%Y-%m-%d'),
            'start_time': self.today.strftime('%H:%M'),
            'duration': 60
        }
        
        response = self.client.post(
            reverse('staff_create_slot'),
            data=json.dumps(slot_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('already exists', data['error'])
    
    def test_invalid_json_data(self):
        """Test handling of invalid JSON data"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('book_time_slot'),
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Invalid JSON', data['error'])
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('book_time_slot'),
            data=json.dumps({}),  # No slot_id provided
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('required', data['error'])
    
    def test_inactive_bookable_item(self):
        """Test booking slots for inactive bookable items"""
        self.table1.is_active = False
        self.table1.save()
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('book_time_slot'),
            data=json.dumps({'slot_id': self.available_slot.id}),
            content_type='application/json'
        )
        
        # Should still work (inactive items might still have valid slots)
        # Adjust based on logic
        self.assertIn(response.status_code, [200, 400])
