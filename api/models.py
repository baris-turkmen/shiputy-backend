from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    is_verified = models.BooleanField(default=False)
    preferred_gender = models.CharField(
        max_length=10, 
        choices=[('M', 'Male'), ('F', 'Female'), ('A', 'All')],
        default='A'
    )
    min_age_preference = models.IntegerField(default=18)
    max_age_preference = models.IntegerField(default=100)
    max_distance = models.IntegerField(default=50)  # in kilometers
    last_active = models.DateTimeField(auto_now=True)
    is_premium = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username}'s profile"
    
    @property
    def profile_completion(self):
        fields = ['bio', 'birth_date', 'gender', 'profile_picture', 'location', 
                 'phone_number', 'preferred_gender']
        filled_fields = sum(1 for field in fields if getattr(self, field))
        return (filled_fields / len(fields)) * 100

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

class UserBlock(models.Model):
    blocker = models.ForeignKey(User, related_name='blocking', on_delete=models.CASCADE)
    blocked = models.ForeignKey(User, related_name='blocked_by', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('blocker', 'blocked')

class Report(models.Model):
    REPORT_REASONS = [
        ('FAKE', 'Fake Profile'),
        ('HARM', 'Harmful Behavior'),
        ('SPAM', 'Spam'),
        ('OTHER', 'Other'),
    ]
    
    reporter = models.ForeignKey(User, related_name='reports_made', on_delete=models.CASCADE)
    reported = models.ForeignKey(User, related_name='reports_received', on_delete=models.CASCADE)
    reason = models.CharField(max_length=10, choices=REPORT_REASONS)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
