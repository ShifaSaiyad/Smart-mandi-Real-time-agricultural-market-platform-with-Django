from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class AdminDashboardAccessTests(TestCase):
    def test_staff_user_can_open_dashboard(self):
        user = User.objects.create_user(username="adminuser", password="pass12345", is_staff=True)
        client = Client()
        client.login(username="adminuser", password="pass12345")
        response = client.get(reverse("admin_dashboard:dashboard"))
        self.assertEqual(response.status_code, 200)

