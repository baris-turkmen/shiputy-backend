from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Profile, Like, Match, UserBlock, Report
from .serializers import ProfileSerializer
import logging
from datetime import date

logger = logging.getLogger(__name__)

class ShiputyAPITests(APITestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username='user1', 
            password='testpass123',
            email='user1@test.com'
        )
        self.user2 = User.objects.create_user(
            username='user2', 
            password='testpass123',
            email='user2@test.com'
        )
        self.user3 = User.objects.create_user(
            username='user3', 
            password='testpass123',
            email='user3@test.com'
        )
        
        # Create profiles with new fields
        self.profile1 = Profile.objects.create(
            user=self.user1,
            bio="Test bio 1",
            birth_date=date(1990, 1, 1),
            gender='M',
            location='City 1',
            preferred_gender='F',
            min_age_preference=20,
            max_age_preference=30,
            max_distance=50,
            is_premium=True,
            phone_number='+1234567890'
        )
        self.profile2 = Profile.objects.create(
            user=self.user2,
            bio="Test bio 2",
            birth_date=date(1995, 1, 1),
            gender='F',
            location='City 2',
            preferred_gender='M',
            min_age_preference=25,
            max_age_preference=35,
            max_distance=30,
            phone_number='+1234567891'
        )
        self.profile3 = Profile.objects.create(
            user=self.user3,
            bio="Test bio 3",
            birth_date=date(1992, 1, 1),
            gender='M',
            location='City 3',
            preferred_gender='A',
            min_age_preference=18,
            max_age_preference=40,
            max_distance=100,
            phone_number='+1234567892'
        )
        
        # Set up the API client
        self.client = APIClient()
        logger.info('Test setup completed')

    def get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    
    def test_jwt_authentication(self):
        """Test JWT authentication"""
        # Test login and token generation
        url = reverse('api:token_obtain_pair')
        response = self.client.post(url, {
            'username': 'user1',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        logger.info('JWT authentication test completed')

    def test_get_profiles_unauthenticated(self):
        """Test that unauthenticated users cannot access profiles"""
        url = reverse('api:profile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        logger.info('Unauthenticated profile access test completed')

    def test_profile_completion_percentage(self):
        """Test profile completion percentage calculation"""
        self.client.force_authenticate(user=self.user1)
        
        # Option 1: Use profile-detail endpoint instead
        url = reverse('api:profile-detail', kwargs={'pk': self.profile1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('completion_percentage', response.data)
        
        # Verify the completion percentage calculation
        expected_fields = ['bio', 'birth_date', 'gender', 'profile_picture', 'location', 
                          'phone_number', 'preferred_gender']
        filled_fields = sum(1 for field in expected_fields if getattr(self.profile1, field))
        expected_percentage = (filled_fields / len(expected_fields)) * 100
        
        self.assertEqual(response.data['completion_percentage'], expected_percentage)
        logger.info('Profile completion percentage test completed')

    def test_block_user(self):
        """Test blocking another user"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('api:profile-block', kwargs={'pk': self.profile2.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(UserBlock.objects.filter(
            blocker=self.user1,
            blocked=self.user2
        ).exists())
        logger.info('User block test completed')

    def test_report_user(self):
        """Test reporting another user"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('api:profile-report', kwargs={'pk': self.profile2.id})
        report_data = {
            'reason': 'FAKE',
            'description': 'This appears to be a fake profile',
            'reported': self.user2.id
        }
        response = self.client.post(url, report_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Report.objects.filter(
            reporter=self.user1,
            reported=self.user2
        ).exists())
        logger.info('User report test completed')

    def test_preference_based_filtering(self):
        """Test that profiles are filtered based on preferences"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('api:profile-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # User1 prefers females, so should only see profile2
        profiles = [profile['id'] for profile in response.data]
        self.assertIn(self.profile2.id, profiles)
        self.assertNotIn(self.profile3.id, profiles)
        logger.info('Preference-based filtering test completed')

    def test_blocked_users_filtering(self):
        """Test that blocked users are filtered from results"""
        # Create a block
        UserBlock.objects.create(blocker=self.user1, blocked=self.user2)
        
        self.client.force_authenticate(user=self.user1)
        url = reverse('api:profile-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profiles = [profile['id'] for profile in response.data]
        self.assertNotIn(self.profile2.id, profiles)
        logger.info('Blocked users filtering test completed')

    def test_get_profiles_authenticated(self):
        """Test that authenticated users can get profiles excluding their own"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('api:profile-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.profile1.id, [profile['id'] for profile in response.data])
        logger.info('Authenticated profile access test completed')
    
    def test_like_profile(self):
        """Test liking a profile"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('api:like-profile', kwargs={'profile_id': self.profile2.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['detail'], 'Like created')
        
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
        
        self.assertTrue(Match.objects.filter(
            user1=self.user2,
            user2=self.user1
        ).exists())
        logger.info('Match creation test completed')
