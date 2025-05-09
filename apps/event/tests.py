from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from rest_framework import status
from apps.user.models import CustomUser, OrganizationProfile
from apps.event.models import Event, Category, Hashtag, Ticket, UserTicket
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from django.test import TestCase
from django.core.exceptions import ValidationError

class EventViewSetTest(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(email="user@example.com", password="testpass123", role="user", is_verified=True, username="user1")
        self.org_user = CustomUser.objects.create_user(email="org@example.com", password="testpass123", role="organization", is_verified=True, username='user2')
        self.org_profile = OrganizationProfile.objects.create(user=self.org_user, name="OrgName")

        self.user_token = str(RefreshToken.for_user(self.user).access_token)
        self.org_token = str(RefreshToken.for_user(self.org_user).access_token)

        self.user_client = APIClient()
        self.user_client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')

        self.org_client = APIClient()
        self.org_client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.org_token}')

        self.unauth_client = APIClient()

        self.category = Category.objects.create(name="Music", organizer=self.org_user)
        self.hashtag = Hashtag.objects.create(name="fun")

        self.event = Event.objects.create(
            organizer=self.org_user,
            title="Concert",
            description="Live concert",
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=1),
            location="Addis Ababa"
        )
        self.event.category.add(self.category)
        self.event.hashtags.add(self.hashtag)

        self.ticket = Ticket.objects.create(
            event=self.event,
            name="VIP",
            price=500
        )
        self.user_ticket = UserTicket.objects.create(user=self.user, ticket=self.ticket)

        self.event_url = reverse('event-detail', kwargs={"id": self.event.id})
        self.event_list_url = reverse('event-list')
        self.like_url = reverse('event-like', kwargs={"id": self.event.id})
        self.tickets_url = reverse('event-tickets', kwargs={"id": self.event.id})
        self.user_tickets_url = reverse('event-user-tickets', kwargs={"id": self.event.id})
        
        
    def test_unauthorized_access(self):
        response = self.unauth_client.get(self.event_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_can_list_and_retrieve_events(self):
        response = self.user_client.get(self.event_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.user_client.get(self.event_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_cannot_create_event(self):
        data = {
            "title": "New Event",
            "description": "Something cool",
            "start_time": timezone.now() + timedelta(days=2),
            "end_time": timezone.now() + timedelta(days=2, hours=1),
            "start_date": timezone.now() + timedelta(days=2),
            "end_date": timezone.now() + timedelta(days=2),
            "location": "Somewhere",
            "category": [self.category.id],
            "hashtags_list": ["fun"]
        }
        response = self.user_client.post(self.event_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_org_can_create_event(self):
        data = {
            "title": "Org Event",
            "description": "Org desc",
            "start_time": timezone.now() + timedelta(days=3),
            "end_time": timezone.now() + timedelta(days=3, hours=1),
            "start_date": timezone.now() + timedelta(days=3),
            "end_date": timezone.now() + timedelta(days=3),
            "location": "Org place",
            "category": [self.category.id],
            "hashtags_list": ["fun"]
        }
        response = self.org_client.post(self.event_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_can_like_and_unlike_event(self):
        # Like
        response = self.user_client.post(self.like_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], "event Liked")

        # Unlike
        response = self.user_client.post(self.like_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], "event unliked")

    def test_user_cannot_like_own_event(self):
        # org trying to like own event
        response = self.org_client.post(self.like_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_can_view_event_tickets(self):
        response = self.user_client.get(self.tickets_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tickets', response.data)
        self.assertEqual(len(response.data['tickets']), 1)

    def test_user_can_view_user_tickets(self):
        response = self.user_client.get(self.user_tickets_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_org_can_update_event(self):
        data = {
            "title": "Updated Event",
            "description": "Updated description",
            "start_time": timezone.now() + timedelta(days=5),
            "end_time": timezone.now() + timedelta(days=5, hours=1),
            "start_date": timezone.now() + timedelta(days=5),
            "end_date": timezone.now() + timedelta(days=5),
            "location": "Updated location",
            "category": [self.category.id],
            "hashtags_list": ["fun"]
        }
        response = self.org_client.put(self.event_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Updated Event")

    def test_user_cannot_update_event(self):
        data = {
            "title": "User Edit Try",
            "hashtags_list": ["fun"],
            "category": [self.category.id]
        }
        response = self.user_client.put(self.event_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_org_can_delete_event(self):
        response = self.org_client.delete(self.event_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_cannot_delete_event(self):
        response = self.user_client.delete(self.event_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class EventModelTest(TestCase):
    def setUp(self):
        # Create users
        self.user = CustomUser.objects.create_user(
            email="user@example.com", password="testpass123", username="user1", role="user"
        )
        self.org_user = CustomUser.objects.create_user(
            email="org@example.com", password="testpass123", username="org1", role="organization"
        )

        # Create categories and hashtags
        self.category = Category.objects.create(name="Music", organizer=self.org_user)
        self.hashtag = Hashtag.objects.create(name="fun")

        # Create an event
        self.event = Event.objects.create(
            organizer=self.org_user,
            title="Concert",
            description="Live concert",
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=1),
            location="Addis Ababa"
        )
        self.event.category.add(self.category)
        self.event.hashtags.add(self.hashtag)

    def test_event_str_method(self):
        """Test the __str__ method of the Event model."""
        self.assertEqual(str(self.event), "Concert")

    def test_is_liked_method_user_likes_event(self):
        """Test that the is_liked method returns True if the user likes the event."""
        # Like the event by adding the user to the likes
        self.event.likes.add(self.user)
        self.assertTrue(self.event.is_liked(self.user))

    def test_is_liked_method_user_does_not_like_event(self):
        """Test that the is_liked method returns False if the user does not like the event."""
        self.assertFalse(self.event.is_liked(self.user))

    def test_latitude_validator_valid(self):
        """Test that valid latitude values are accepted."""
        self.event.latitude = 45.0
        try:
            self.event.full_clean()  
        except ValidationError:
            self.fail("Event latitude validation failed, even though the value is valid.")

    def test_latitude_validator_invalid(self):
        """Test that invalid latitude values raise a validation error."""
        self.event.latitude = 100.0  # Invalid latitude (> 90)
        with self.assertRaises(ValidationError):
            self.event.full_clean()

    def test_longitude_validator_valid(self):
        """Test that valid longitude values are accepted."""
        self.event.longitude = 45.0
        try:
            self.event.full_clean()  
        except ValidationError:
            self.fail("Event longitude validation failed, even though the value is valid.")

    def test_longitude_validator_invalid(self):
        """Test that invalid longitude values raise a validation error."""
        self.event.longitude = 200.0  # Invalid longitude (> 180)
        with self.assertRaises(ValidationError):
            self.event.full_clean()

    def test_cover_image_url_default_empty(self):
        """Test that cover_image_url defaults to an empty list."""
        self.assertEqual(self.event.cover_image_url, [])