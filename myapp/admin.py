from django.contrib import admin
from .models import Image, Advertisement

class ImageAdmin(admin.ModelAdmin):
    list_display = ('heading', 'description')
    search_fields = ('heading', 'description')

class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_google_adsense', 'position', 'status')
    list_filter = ('is_google_adsense', 'position', 'status')
    search_fields = ('title',)

admin.site.register(Image, ImageAdmin)
admin.site.register(Advertisement, AdvertisementAdmin)
