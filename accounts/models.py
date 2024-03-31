from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.RESTRICT)
    first_name = models.CharField(max_length=100, blank=True, null=True)  # First name of the user
    last_name = models.CharField(max_length=100, blank=True, null=True)  # Last name of the user
    porfolio = models.FloatField()  # Last name of the user
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    