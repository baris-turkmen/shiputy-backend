from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from .views import CustomTokenObtainPairView

router = DefaultRouter()
router.register(r'profiles', views.ProfileViewSet, basename='profile')

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    path('like/<int:profile_id>/', views.like_profile, name='like-profile'),
    path('matches/', views.get_matches, name='matches'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] 