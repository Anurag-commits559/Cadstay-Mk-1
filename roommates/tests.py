from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from roommates.models import RoommateProfile


class RoommateCRUDTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(
            username="student_rahul",
            email="rahul@test.com",
            password="StrongPassword123!",
            role=User.Role.TENANT,
        )
        self.other_user = User.objects.create_user(
            username="student_rohit",
            email="rohit@test.com",
            password="StrongPassword123!",
            role=User.Role.TENANT,
        )
        self.profile = RoommateProfile.objects.create(
            user=self.student,
            location="Koramangala 4th Block",
            budget=8500,
            gender_preference="male",
            bio="CS student at Christ University, quiet and clean.",
            is_active=True,
        )

    def test_roommate_list_view(self):
        response = self.client.get(reverse('roommates:roommate_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "student_rahul")
        self.assertContains(response, "Koramangala 4th Block")

    def test_roommate_search_and_filters(self):
        response = self.client.get(reverse('roommates:roommate_list'), {'q': 'Christ'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "student_rahul")

        response_budget = self.client.get(reverse('roommates:roommate_list'), {'max_budget': '5000'})
        self.assertEqual(response_budget.status_code, 200)
        self.assertNotContains(response_budget, "student_rahul")

    def test_roommate_detail_view(self):
        response = self.client.get(reverse('roommates:roommate_detail', kwargs={'pk': self.profile.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "student_rahul")
        self.assertContains(response, "8500")

    def test_create_roommate_request(self):
        self.client.login(username="student_rohit", password="StrongPassword123!")
        post_data = {
            'location': 'HSR Layout Sector 1',
            'budget': '11000',
            'gender_preference': 'any',
            'bio': 'Software engineer intern looking for 2BHK flatmate.',
        }
        response = self.client.post(reverse('roommates:create_roommate_request'), post_data)
        self.assertEqual(response.status_code, 302)
        new_profile = RoommateProfile.objects.get(user=self.other_user)
        self.assertEqual(new_profile.location, 'HSR Layout Sector 1')
        self.assertEqual(new_profile.budget, 11000)

    def test_edit_roommate_request(self):
        self.client.login(username="student_rahul", password="StrongPassword123!")
        post_data = {
            'location': 'Koramangala 5th Block',
            'budget': '9000',
            'gender_preference': 'male',
            'bio': 'Updated bio description.',
        }
        response = self.client.post(reverse('roommates:edit_roommate_request', kwargs={'pk': self.profile.pk}), post_data)
        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.location, 'Koramangala 5th Block')
        self.assertEqual(self.profile.budget, 9000)

    def test_delete_roommate_request(self):
        self.client.login(username="student_rahul", password="StrongPassword123!")
        response = self.client.post(reverse('roommates:delete_roommate_request', kwargs={'pk': self.profile.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(RoommateProfile.objects.filter(pk=self.profile.pk).exists())

    def test_unauthorized_user_cannot_edit_or_delete(self):
        self.client.login(username="student_rohit", password="StrongPassword123!")
        response_edit = self.client.post(
            reverse('roommates:edit_roommate_request', kwargs={'pk': self.profile.pk}),
            {'location': 'Hacked Location', 'budget': '1000', 'gender_preference': 'any'}
        )
        self.assertEqual(response_edit.status_code, 403)

        response_delete = self.client.post(
            reverse('roommates:delete_roommate_request', kwargs={'pk': self.profile.pk})
        )
        self.assertEqual(response_delete.status_code, 403)
