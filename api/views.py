from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Profile, Match, Like
from .serializers import ProfileSerializer, MatchSerializer, LikeSerializer

# Create your views here.

class ProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer
    
    def get_queryset(self):
        # Exclude the current user's profile from the list
        return Profile.objects.exclude(user=self.request.user)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_profile(request, profile_id):
    try:
        to_user = Profile.objects.get(id=profile_id).user
        from_user = request.user
        
        # Check if like already exists
        if Like.objects.filter(from_user=from_user, to_user=to_user).exists():
            return Response({'detail': 'Already liked'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create new like
        like = Like.objects.create(from_user=from_user, to_user=to_user)
        
        # Check if there's a mutual like
        if Like.objects.filter(from_user=to_user, to_user=from_user).exists():
            # Create a match
            Match.objects.create(user1=from_user, user2=to_user)
            return Response({'detail': 'It\'s a match!'}, status=status.HTTP_201_CREATED)
        
        return Response({'detail': 'Like created'}, status=status.HTTP_201_CREATED)
    
    except Profile.DoesNotExist:
        return Response({'detail': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_matches(request):
    matches = Match.objects.filter(Q(user1=request.user) | Q(user2=request.user))
    serializer = MatchSerializer(matches, many=True)
    return Response(serializer.data)
