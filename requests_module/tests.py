from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from hostels.models import Hostel, Room
from .models import Favorite, BookingRequest


class Member4Tests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="student1",
            email="student@example.com",
            password="TestPassword123!",
            role="TENANT",
        )

        self.owner = User.objects.create_user(
            username="owner1",
            email="owner@example.com",
            password="TestPassword123!",
            role="OWNER",
        )

        self.hostel = Hostel.objects.create(
            owner=self.owner,
            hostel_name="Test Hostel",
            address="Test Address",
            area="Test Area",
            city="Mumbai",
            pincode="400001",
            contact_phone="9999999999",
            status="ACTIVE",
        )

        self.room = Room.objects.create(
            hostel=self.hostel,
            room_type="DOUBLE",
            rent=8000,
            total_beds=3,
            available_beds=2,
        )

    def test_favorite_creation(self):
        Favorite.objects.get_or_create(
            user=self.student,
            hostel=self.hostel,
        )

        self.assertEqual(
            Favorite.objects.filter(user=self.student).count(),
            1,
        )

    def test_student_can_view_requests(self):
        self.client.login(
            username="student1",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse("requests_module:my_requests")
        )

        self.assertEqual(response.status_code, 200)

    def test_owner_can_view_owner_requests(self):
        self.client.login(
            username="owner1",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse("requests_module:owner_requests")
        )

        self.assertEqual(response.status_code, 200)

    def test_student_cannot_access_owner_dashboard(self):
        self.client.login(
            username="student1",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse("requests_module:owner_requests")
        )

        self.assertEqual(response.status_code, 403)
