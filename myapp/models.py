from django.db import models
from django.utils import timezone

class Image(models.Model):
    image = models.ImageField(upload_to='images/')
    heading = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.heading

class Comment(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    comment = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    def __str__(self):
        return f"Comment by {self.name} on {self.image.heading}"
class Advertisement(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='advertisements/', blank=True, null=True)
    order = models.PositiveIntegerField()
    is_google_adsense = models.BooleanField(default=False)
    google_adsense_code = models.TextField(blank=True, null=True, help_text="Paste Google AdSense code here")
    site_link = models.URLField(blank=True, null=True, help_text="Enter website URL for manual ads")
    position = models.CharField(
        max_length=50,
        choices=[
            ('upper-menu', 'Upper menu'),
            ('below-menu', 'Below menu'),
            ('left-side-of-page', 'Left side of the page'),
            ('right-side-of-page', 'Right side of the page'),
            ('below-page', 'Below the page'),
            ('below-footer', 'Below footer'),
        ],
        default='upper-menu'
    )
    status = models.CharField(
        max_length=10,
        choices=[('enable', 'Enable'), ('disable', 'Disable')],
        default='enable'
    )

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order']
        verbose_name = 'Advertisement'
        verbose_name_plural = 'Advertisements'

    def clean(self):
        """Validation to ensure proper field combinations"""
        from django.core.exceptions import ValidationError
        
        if self.is_google_adsense and not self.google_adsense_code:
            raise ValidationError("Google AdSense code is required when using AdSense")
        if not self.is_google_adsense and not self.image and not self.site_link:
            raise ValidationError("Either an image or site link is required for manual advertisements")