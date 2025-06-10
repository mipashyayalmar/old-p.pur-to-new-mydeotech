from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Image, Advertisement, Comment
from .forms import ImageForm, AdvertisementForm
from django.contrib.auth.decorators import login_required

from django.shortcuts import render
from .models import Image 


# Home view (blog list)
def home(request):
    images = Image.objects.all().order_by('-created_at')
    advertisements = Advertisement.objects.filter(status='enable').order_by('order')
    form = ImageForm()
    search_query = request.GET.get('q', '')
    
    if search_query:
        images = images.filter(
            Q(heading__icontains=search_query) | 
            Q(description__icontains=search_query)
        )

    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('home')

    return render(request, 'home/home.html', {
        'images': images,
        'advertisements': advertisements,
        'form': form,
        'search_query': search_query
    })


def setting(request):
    return render(request, 'home/setting.html')  

@login_required(login_url='/')
def advertisement(request):
    form = AdvertisementForm()

    # Handle POST request for adding an advertisement
    if request.method == 'POST':
        form = AdvertisementForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('advertisement')

    # Render advertisement template with the form
    return render(request, 'advertisements/adverhome.html', {'form': form})
