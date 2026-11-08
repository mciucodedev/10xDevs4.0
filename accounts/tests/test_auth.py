from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

PASSWORD = "s3cret-Pass-99"


class RegisterTests(TestCase):
    def post_register(self, username: str = "ola", email: str = "ola@example.com") -> "object":
        return self.client.post(reverse("register"), {
            "username": username, "email": email, "password1": PASSWORD, "password2": PASSWORD,
        })

    def test_register_creates_user_and_logs_in(self) -> None:
        response = self.post_register()
        self.assertRedirects(response, "/", fetch_redirect_response=False)  # type: ignore[arg-type]
        self.assertTrue(User.objects.filter(username="ola").exists())
        self.assertIn("_auth_user_id", self.client.session)

    def test_register_rejects_duplicate_username(self) -> None:
        User.objects.create_user("ola", "x@example.com", PASSWORD)
        self.post_register(email="other@example.com")
        self.assertEqual(User.objects.filter(username="ola").count(), 1)

    def test_register_requires_unique_email_case_insensitive(self) -> None:
        User.objects.create_user("first", "Ola@Example.com", PASSWORD)
        self.post_register(username="second", email="ola@example.com")
        self.assertFalse(User.objects.filter(username="second").exists())

    def test_register_requires_email(self) -> None:
        self.post_register(email="")
        self.assertFalse(User.objects.filter(username="ola").exists())


class LoginTests(TestCase):
    def setUp(self) -> None:
        User.objects.create_user("ola", "ola@example.com", PASSWORD)

    def test_login_with_username(self) -> None:
        self.assertTrue(self.client.login(username="ola", password=PASSWORD))

    def test_login_with_email(self) -> None:
        self.assertTrue(self.client.login(username="OLA@example.com", password=PASSWORD))

    def test_wrong_password_fails(self) -> None:
        self.assertFalse(self.client.login(username="ola@example.com", password="nope"))

    def test_login_redirects_to_next(self) -> None:
        response = self.client.post(
            reverse("login") + "?next=/places/1/", {"username": "ola", "password": PASSWORD}
        )
        self.assertRedirects(response, "/places/1/", fetch_redirect_response=False)

    def test_logout_requires_post(self) -> None:
        self.client.login(username="ola", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.client.post(reverse("logout"))
        self.assertNotIn("_auth_user_id", self.client.session)
