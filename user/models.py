from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class User(AbstractUser):
    name = models.CharField(max_length=50, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    is_admin = models.BooleanField(default=False)
    profile_image = models.ImageField(upload_to='user_profiles/', null=True, blank=True)
    groups = models.ManyToManyField(Group, related_name="custom_user_set", blank=True, help_text="The groups this user belongs to.")
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions_set", blank=True, help_text="Specific permissions for this user.")

    def __str__(self):
        return self.username
