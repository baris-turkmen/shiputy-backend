from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Profile, Match, Like, UserBlock, Report
from .serializers import ProfileSerializer, MatchSerializer, LikeSerializer, ReportSerializer
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

# Create your views here.

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class ProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['user__username', 'location']
    filterset_fields = ['gender', 'location']
    
    def get_queryset(self):
        user = self.request.user
        if self.action == 'retrieve':
            return Profile.objects.all()
            
        # For list view
        blocked_users = UserBlock.objects.filter(blocker=user).values_list('blocked', flat=True)
        queryset = Profile.objects.exclude(
            Q(user=user) | 
            Q(user__in=blocked_users)
        )
        
        # Filter based on gender preferences
        if user.profile.preferred_gender != 'A':
            queryset = queryset.filter(gender=user.profile.preferred_gender)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        profile = self.get_object()
        UserBlock.objects.create(blocker=request.user, blocked=profile.user)
        return Response({'detail': 'User blocked'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        profile = self.get_object()
        serializer = ReportSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(reporter=request.user, reported=profile.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
