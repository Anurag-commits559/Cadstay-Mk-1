from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User
from hostels.models import Hostel, Room, HostelImage


class HostelCRUDTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            username="owner_user",
            email="owner@test.com",
            password="StrongPassword123!",
            role=User.Role.OWNER,
        )
        self.other_user = User.objects.create_user(
            username="other_user",
            email="other@test.com",
            password="StrongPassword123!",
            role=User.Role.TENANT,
        )
        self.hostel = Hostel.objects.create(
            owner=self.owner,
            hostel_name="Sunshine Student PG",
            property_type=Hostel.PropertyType.PG,
            address="123 College St",
            area="Koramangala",
            city="Bangalore",
            pincode="560034",
            gender_allowed=Hostel.GenderAllowed.UNISEX,
            contact_phone="9876543210",
            status=Hostel.Status.ACTIVE,
            wifi=True,
            ac=True,
        )
        self.room = Room.objects.create(
            hostel=self.hostel,
            room_type=Room.RoomType.DOUBLE,
            rent=7500,
            security_deposit=10000,
            total_beds=2,
            available_beds=1,
        )

    def test_hostel_list_view(self):
        response = self.client.get(reverse('hostels:hostel_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sunshine Student PG")

    def test_hostel_search_filter(self):
        response = self.client.get(reverse('hostels:hostel_list'), {'q': 'Koramangala'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sunshine Student PG")

        response_miss = self.client.get(reverse('hostels:hostel_list'), {'q': 'NonExistentCity'})
        self.assertEqual(response_miss.status_code, 200)
        self.assertNotContains(response_miss, "Sunshine Student PG")

    def test_hostel_detail_view(self):
        response = self.client.get(reverse('hostels:hostel_detail', kwargs={'pk': self.hostel.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sunshine Student PG")
        self.assertContains(response, "7500")

    def test_my_listings_authenticated(self):
        self.client.login(username="owner_user", password="StrongPassword123!")
        response = self.client.get(reverse('hostels:my_listings'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sunshine Student PG")

    def test_hostel_add_wizard(self):
        self.client.login(username="owner_user", password="StrongPassword123!")
        form_data = {
            'hostel_name': 'Grand Heritage Stay',
            'property_type': 'HOSTEL',
            'gender_allowed': 'MALE',
            'contact_phone': '9876543210',
            'description': 'A wonderful place for students',
            'address': '45 Avenue Rd',
            'area': 'Indiranagar',
            'city': 'Bangalore',
            'pincode': '560038',
            'wifi': 'on',
            'ac': 'on',
            # Room formset management form
            'rooms-TOTAL_FORMS': '1',
            'rooms-INITIAL_FORMS': '0',
            'rooms-MIN_NUM_FORMS': '0',
            'rooms-MAX_NUM_FORMS': '1000',
            'rooms-0-room_type': 'SINGLE',
            'rooms-0-rent': '9000',
            'rooms-0-security_deposit': '5000',
            'rooms-0-total_beds': '1',
            'rooms-0-available_beds': '1',
            'rooms-0-bathroom_type': 'ATTACHED',
            'rooms-0-furnishing': 'FULLY',
            'publish': 'Publish listing',
        }
        test_image = SimpleUploadedFile("pg_photo.jpg", b"dummy_pg_image_data", content_type="image/jpeg")
        post_data = {**form_data, 'images': test_image}
        response = self.client.post(reverse('hostels:hostel_add'), post_data)
        self.assertEqual(response.status_code, 302)
        new_hostel = Hostel.objects.get(hostel_name='Grand Heritage Stay')
        self.assertEqual(new_hostel.owner, self.owner)
        self.assertEqual(new_hostel.status, Hostel.Status.ACTIVE)
        self.assertEqual(new_hostel.rooms.count(), 1)
        self.assertEqual(new_hostel.images.count(), 1)

    def test_hostel_edit(self):
        self.client.login(username="owner_user", password="StrongPassword123!")
        form_data = {
            'hostel_name': 'Sunshine Student PG - Renovated',
            'property_type': 'PG',
            'gender_allowed': 'UNISEX',
            'contact_phone': '9876543210',
            'description': 'Updated description',
            'address': '123 College St',
            'area': 'Koramangala',
            'city': 'Bangalore',
            'pincode': '560034',
            'rooms-TOTAL_FORMS': '1',
            'rooms-INITIAL_FORMS': '1',
            'rooms-MIN_NUM_FORMS': '0',
            'rooms-MAX_NUM_FORMS': '1000',
            'rooms-0-id': str(self.room.id),
            'rooms-0-hostel': str(self.hostel.id),
            'rooms-0-room_type': 'DOUBLE',
            'rooms-0-rent': '8000',
            'rooms-0-security_deposit': '10000',
            'rooms-0-total_beds': '2',
            'rooms-0-available_beds': '1',
            'rooms-0-bathroom_type': 'SHARED',
            'rooms-0-furnishing': 'SEMI',
        }
        response = self.client.post(reverse('hostels:hostel_edit', kwargs={'pk': self.hostel.pk}), form_data)
        self.assertEqual(response.status_code, 302)
        self.hostel.refresh_from_db()
        self.assertEqual(self.hostel.hostel_name, 'Sunshine Student PG - Renovated')

    def test_hostel_toggle_status(self):
        self.client.login(username="owner_user", password="StrongPassword123!")
        response = self.client.post(reverse('hostels:hostel_deactivate', kwargs={'pk': self.hostel.pk}))
        self.assertEqual(response.status_code, 302)
        self.hostel.refresh_from_db()
        self.assertEqual(self.hostel.status, Hostel.Status.INACTIVE)

    def test_hostel_delete(self):
        self.client.login(username="owner_user", password="StrongPassword123!")
        response = self.client.post(reverse('hostels:hostel_delete', kwargs={'pk': self.hostel.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Hostel.objects.filter(pk=self.hostel.pk).exists())

    def test_unauthorized_user_cannot_edit_or_delete(self):
        self.client.login(username="other_user", password="StrongPassword123!")
        response_edit = self.client.post(
            reverse('hostels:hostel_edit', kwargs={'pk': self.hostel.pk}),
            {'hostel_name': 'Hacked Name'}
        )
        self.assertEqual(response_edit.status_code, 403)

        response_delete = self.client.post(
            reverse('hostels:hostel_delete', kwargs={'pk': self.hostel.pk})
        )
        self.assertEqual(response_delete.status_code, 403)

    def test_hostel_image_requires_parent_hostel_before_save(self):
        img_file = SimpleUploadedFile("standalone.jpg", b"image_content", content_type="image/jpeg")
        # Attempting save without parent hostel must raise ValueError
        unassigned_image = HostelImage(image=img_file)
        with self.assertRaises(ValueError):
            unassigned_image.save()

        # Assigning parent hostel allows .save() to succeed without integrity error
        assigned_image = HostelImage(hostel=self.hostel, image=img_file)
        assigned_image.save()
        self.assertIsNotNone(assigned_image.pk)
        self.assertEqual(assigned_image.hostel, self.hostel)

    def test_image_upload_and_set_primary_and_delete(self):
        self.client.login(username="owner_user", password="StrongPassword123!")
        img1 = SimpleUploadedFile("gallery1.jpg", b"dummy_data_1", content_type="image/jpeg")
        img2 = SimpleUploadedFile("gallery2.jpg", b"dummy_data_2", content_type="image/jpeg")

        # Upload images
        response = self.client.post(
            reverse('hostels:image_upload', kwargs={'hostel_id': self.hostel.pk}),
            {'images': [img1, img2]}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.hostel.images.count(), 2)

        images = list(self.hostel.images.all())
        first_img, second_img = images[0], images[1]

        # Make second image primary
        resp_primary = self.client.post(reverse('hostels:image_primary', kwargs={'image_id': second_img.pk}))
        self.assertEqual(resp_primary.status_code, 302)
        second_img.refresh_from_db()
        first_img.refresh_from_db()
        self.assertTrue(second_img.is_primary)
        self.assertFalse(first_img.is_primary)

        # Delete image
        resp_delete = self.client.post(reverse('hostels:image_delete', kwargs={'image_id': second_img.pk}))
        self.assertEqual(resp_delete.status_code, 302)
        self.assertEqual(self.hostel.images.count(), 1)
