from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"

class Match(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user1_matches')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user2_matches')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Match between {self.user1.username} and {self.user2.username}"

class Like(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_given')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_received')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.from_user.username} likes {self.to_user.username}"
