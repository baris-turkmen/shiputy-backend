from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Profile, Like, Match
from .serializers import ProfileSerializer
import logging

logger = logging.getLogger(__name__)

class TinderLikeAPITests(APITestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(username='user1', password='testpass123')
        self.user2 = User.objects.create_user(username='user2', password='testpass123')
        self.user3 = User.objects.create_user(username='user3', password='testpass123')
        
        # Create profiles
        self.profile1 = Profile.objects.create(
            user=self.user1,
            bio="Test bio 1",
            gender='M',
            location='City 1'
        )
        self.profile2 = Profile.objects.create(
            user=self.user2,
            bio="Test bio 2",
            gender='F',
            location='City 2'
        )
        self.profile3 = Profile.objects.create(
            user=self.user3,
            bio="Test bio 3",
            gender='O',
            location='City 3'
        )
        
        # Set up the API client
        self.client = APIClient()
        logger.info('Test setup completed')
    
    def test_get_profiles_unauthenticated(self):
        """Test that unauthenticated users cannot access profiles"""
        url = reverse('api:profile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        logger.info('Unauthenticated profile access test completed')
    
    def test_get_profiles_authenticated(self):
        """Test that authenticated users can get profiles excluding their own"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('api:profile-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Should only see user2 and user3's profiles
        self.assertNotIn(self.profile1.id, [profile['id'] for profile in response.data])
        logger.info('Authenticated profile access test completed')
    
    def test_like_profile(self):
        """Test liking a profile"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('api:like-profile', kwargs={'profile_id': self.profile2.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['detail'], 'Like created')
        
        # Verify like was created in database
        self.assertTrue(Like.objects.filter(
            from_user=self.user1,
            to_user=self.user2
        ).exists())
        logger.info('Profile like test completed')
    
    def test_match_creation(self):
        """Test match creation when users mutually like each other"""
        # User1 likes User2
        self.client.force_authenticate(user=self.user1)
        url = reverse('api:like-profile', kwargs={'profile_id': self.profile2.id})
        self.client.post(url)
        
        # User2 likes User1
        self.client.force_authenticate(user=self.user2)
        url = reverse('api:like-profile', kwargs={'profile_id': self.profile1.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['detail'], "It's a match!")
        
        # Verify match was created in database
        self.assertTrue(Match.objects.filter(
            user1=self.user2,
            user2=self.user1
        ).exists())
        logger.info('Match creation test completed')
    
    def test_duplicate_like(self):
        """Test that a user cannot like the same profile twice"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('api:like-profile', kwargs={'profile_id': self.profile2.id})
        
        # First like
        self.client.post(url)
        
        # Second like attempt
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Already liked')
        logger.info('Duplicate like test completed')
    
    def test_get_matches(self):
        """Test getting user matches"""
        # Create a match
        Match.objects.create(user1=self.user1, user2=self.user2)
        
        # Get matches for user1
        self.client.force_authenticate(user=self.user1)
        url = reverse('api:matches')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user1']['username'], 'user1')
        self.assertEqual(response.data[0]['user2']['username'], 'user2')
        logger.info('Get matches test completed')
    
    def test_like_nonexistent_profile(self):
        """Test liking a profile that doesn't exist"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('api:like-profile', kwargs={'profile_id': 9999})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'Profile not found')
        logger.info('Nonexistent profile like test completed')
