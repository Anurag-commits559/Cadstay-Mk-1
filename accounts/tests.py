from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class RegistrationTests(TestCase):
    def setUp(self):
        self.url = reverse("accounts:register")
        self.valid_data = {
            "first_name": "Asha",
            "last_name": "Rao",
            "username": "asharao",
            "email": "asha@example.com",
            "role": User.Role.TENANT,
            "password1": "StrongPass!2024",
            "password2": "StrongPass!2024",
        }

    def test_successful_registration(self):
        response = self.client.post(self.url, self.valid_data)
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertTrue(User.objects.filter(username="asharao").exists())
        user = User.objects.get(username="asharao")
        # Password must be hashed, never stored in plain text.
        self.assertNotEqual(user.password, "StrongPass!2024")
        self.assertTrue(user.check_password("StrongPass!2024"))
        # A profile should be auto-created via signal.
        self.assertTrue(hasattr(user, "profile"))

    def test_duplicate_username(self):
        User.objects.create_user(username="asharao", email="other@example.com", password="StrongPass!2024")
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="asha@example.com").exists())
        self.assertContains(response, "already taken")

    def test_duplicate_email(self):
        User.objects.create_user(username="other", email="asha@example.com", password="StrongPass!2024")
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="asharao").exists())
        self.assertContains(response, "already exists")

    def test_password_mismatch(self):
        data = {**self.valid_data, "password2": "SomethingElse!123"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="asharao").exists())
        self.assertContains(response, "do not match")


class LoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="StrongPass!2024"
        )
        self.url = reverse("accounts:login")

    def test_successful_login(self):
        response = self.client.post(self.url, {"username": "testuser", "password": "StrongPass!2024"})
        self.assertRedirects(response, reverse("accounts:dashboard"))

    def test_login_with_email(self):
        response = self.client.post(self.url, {"username": "test@example.com", "password": "StrongPass!2024"})
        self.assertRedirects(response, reverse("accounts:dashboard"))

    def test_invalid_login(self):
        response = self.client.post(self.url, {"username": "testuser", "password": "WrongPassword"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username/email or password.")


class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", email="alice@example.com", password="StrongPass!2024"
        )
        self.other_user = User.objects.create_user(
            username="bob", email="bob@example.com", password="StrongPass!2024"
        )

    def test_authenticated_user_can_view_profile(self):
        self.client.login(username="alice", password="StrongPass!2024")
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "alice@example.com")

    def test_user_can_edit_own_profile(self):
        self.client.login(username="alice", password="StrongPass!2024")
        response = self.client.post(
            reverse("accounts:edit_profile"),
            {
                "first_name": "Alice",
                "last_name": "Smith",
                "email": "alice@example.com",
                "phone_number": "9999999999",
                "city": "Mumbai",
                "bio": "Hello there",
            },
        )
        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Alice")
        self.assertEqual(self.user.profile.city, "Mumbai")

    def test_user_cannot_edit_another_users_profile_via_email_collision(self):
        # A user cannot "take over" another account's email through the edit form.
        self.client.login(username="alice", password="StrongPass!2024")
        response = self.client.post(
            reverse("accounts:edit_profile"),
            {
                "first_name": "Alice",
                "last_name": "Smith",
                "email": "bob@example.com",  # belongs to another user
                "phone_number": "",
                "city": "",
                "bio": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.email, "bob@example.com")


class AuthenticationRequiredTests(TestCase):
    def test_anonymous_user_cannot_access_dashboard(self):
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_anonymous_user_cannot_access_profile(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_anonymous_user_cannot_access_edit_profile(self):
        response = self.client.get(reverse("accounts:edit_profile"))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_cannot_access_password_change(self):
        response = self.client.get(reverse("accounts:password_change"))
        self.assertEqual(response.status_code, 302)


class PasswordChangeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="carol", email="carol@example.com", password="OldPass!2024"
        )
        self.client.login(username="carol", password="OldPass!2024")
        self.url = reverse("accounts:password_change")

    def test_password_change_success(self):
        response = self.client.post(
            self.url,
            {
                "old_password": "OldPass!2024",
                "new_password1": "BrandNewPass!2025",
                "new_password2": "BrandNewPass!2025",
            },
        )
        self.assertRedirects(response, reverse("accounts:password_change_done"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("BrandNewPass!2025"))

    def test_old_password_required(self):
        response = self.client.post(
            self.url,
            {
                "old_password": "WrongOldPassword",
                "new_password1": "BrandNewPass!2025",
                "new_password2": "BrandNewPass!2025",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("OldPass!2024"))
