from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.forms import ValidationError
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse, reverse_lazy
from django.core.mail import EmailMultiAlternatives
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib import messages
from .models import User
from allauth.socialaccount.models import SocialAccount
import random
import logging
from django.utils import timezone
import pytz
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email


# User Signup
def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        name = request.POST['name']
        phone = request.POST['phone']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            return render(request, 'user_login/signin.html', {'message': 'User already exists with that username. Please sign in.'})

        user = User.objects.create_user(username=username, password=password, name=name, phone=phone, email=username, is_active=False)

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        verification_url = request.build_absolute_uri(reverse('user:verify_email', args=[uid, token]))

        subject = 'Welcome to PandharpurGuide, Verify your account'
        html_message = render_to_string('user_login/verification_email.html', {
            'name': user.name,
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'password': password,  
            'verification_url': verification_url,
            'domain': request.get_host(),
            'protocol': 'https' if request.is_secure() else 'http',
        })
        plain_message = strip_tags(html_message)

        email = EmailMultiAlternatives(subject, plain_message, settings.EMAIL_HOST_USER, [user.email])
        email.attach_alternative(html_message, "text/html")

        try:
            email.send()
        except Exception as e:
            user.delete()
            return render(request, 'user_login/signup.html', {'message': f'Error sending verification email: {str(e)}'})

        user.save()
        return render(request, 'user_login/signin.html', {'message': 'User created successfully. Please check your email for verification instructions.'})

    return render(request, 'user_login/signup.html')

def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()

            # Automatically log the user in after email verification
            authenticated_user = authenticate(request, username=user.username, password=user.password)
            if authenticated_user is not None:
                login(request, authenticated_user)

            # Optional: Log the time when the user is logged in
            ist = pytz.timezone('Asia/Kolkata')
            signin_time = timezone.now().astimezone(ist).strftime('%Y-%m-%d %H:%M:%S')
            messages.success(request, f'Account verified successfully and logged in at {signin_time}')

            return redirect('user:signin')  # Redirect to a page after successful login

        else:
            return render(request, 'user_login/verification_failure.html')
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return render(request, 'user_login/verification_failure.html')


# User Signin
def signin(request):
    if request.user.is_authenticated and request.user.is_active:
        return redirect('/')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        if not User.objects.filter(username=username).exists():
            return render(request, 'user_login/signup.html', {'message': "User doesn't exist. Please sign up"})

        user = User.objects.get(username=username)

        if user.is_staff:
            return render(request, 'user_login/signin.html', {'message': 'This is a staff account. Please use the staff signin page.'})

        if not user.is_active:
            return render(request, 'user_login/verification_prompt.html', {'email': username, 'message': 'Your account is not verified yet. Please check your email.'})

        authenticated_user = authenticate(request, username=username, password=password)

        if authenticated_user is not None and authenticated_user.is_active:
            request.session['username'] = username
            login(request, authenticated_user)

            ist = pytz.timezone('Asia/Kolkata')
            signin_time = timezone.now().astimezone(ist).strftime('%Y-%m-%d %H:%M:%S')

            messages.success(request, f'Signin successful at {signin_time}')

            return redirect('myapp:home')
        
        return render(request, 'user_login/signin.html', {'message': 'Incorrect username or password'})

    return render(request, 'user_login/signin.html')


# User Logout
def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        request.session.flush()
        
        messages.warning(request, 'Logged out successfully')
        
        return redirect('user:signin')  
    return redirect('user:signin') 

# User Password Reset View
class CustomPasswordResetView(PasswordResetView):
    template_name = 'user_login/password_reset.html'
    success_url = reverse_lazy('user:password_reset_done')
    email_template_name = 'user_login/reset_password.txt'
    html_email_template_name = 'user_login/reset_password.html'

    def form_valid(self, form):
        email = form.cleaned_data['email']
        if not User.objects.filter(email=email).exists():
            return render(self.request, self.template_name, {
                'form': form,
                'error': 'No account found with this email.'
            })

        user = User.objects.get(email=email)
        if user.is_staff:
            return render(self.request, self.template_name, {
                'form': form,
                'error': 'This is a staff account. Please use the staff password reset page.'
            })

        if not user.is_active:
            return render(self.request, 'user_login/verification_prompt.html', {
                'email': email,
                'message': 'Your account is not verified yet. Please verify your email before resetting your password.'
            })

        protocol = 'https' if self.request.is_secure() else 'http'
        domain = self.request.get_host()

        opts = {
            'use_https': self.request.is_secure(),
            'from_email': settings.EMAIL_HOST_USER,
            'request': self.request,
            'email_template_name': self.email_template_name,
            'html_email_template_name': self.html_email_template_name,
            'extra_email_context': {
                'protocol': protocol,
                'domain': domain,
            },
        }

        form.save(**opts)
        return super().form_valid(form)

# User Password Reset Confirm View
class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'user_login/password_reset_confirm.html'
    success_url = reverse_lazy('user:password_reset_complete')
    form_class = SetPasswordForm

    def dispatch(self, *args, **kwargs):
        uidb64 = kwargs.get('uidb64')
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            if user.is_staff:
                return render(self.request, 'user_login/password_reset_failure.html', {
                    'message': 'This is a staff account. Please use the staff password reset page.'
                })
            if not user.is_active:
                return render(self.request, 'user_login/verification_prompt.html', {
                    'email': user.email,
                    'message': 'Your account is not verified yet. Please verify your email before resetting your password.'
                })
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return render(self.request, 'user_login/password_reset_failure.html', {
                'message': 'Invalid reset link.'
            })
        return super().dispatch(*args, **kwargs)
    




        

@login_required(login_url='/')
def user_profile(request):
    if not request.user.is_authenticated:
        messages.error(request, "Please sign in to view your profile.")
        return redirect('user:signin')
    
    if request.user.is_staff:
        messages.error(request, "Staff accounts cannot access user profiles.")
        return redirect('user:staff_signin')

    user = request.user

    # Try to get social account data
    social_data = {}
    try:
        social_account = SocialAccount.objects.get(user=user, provider='google')
        social_data = {
            'full_name': social_account.extra_data.get('name'),
            'email': social_account.extra_data.get('email'),
            'picture': social_account.extra_data.get('picture'),
        }
    except SocialAccount.DoesNotExist:
        # User may have signed up with regular email/password
        social_data = {
            'full_name': user.get_full_name() or user.username,
            'email': user.email,
            'picture': None
        }

    context = {
        'user': user,
        'social_data': social_data
    }
    
    return render(request, 'user_login/user_profile.html', context)
# Set up logging
logger = logging.getLogger(__name__)

@login_required(login_url='/')
def user_profile_edit(request):
    if not request.user.is_authenticated:
        messages.error(request, "Please sign in to edit your profile.")
        return redirect('user:signin')
    
    if request.user.is_staff:
        messages.error(request, "Staff accounts cannot edit user profiles.")
        return redirect('user:staff_signin')
    
    user = request.user
    social_data = {}

    try:
        # Fetch Google social account data
        social_account = SocialAccount.objects.get(user=user, provider='google')
        extra_data = social_account.extra_data
        
        # Extract all available fields from Google OAuth
        social_data = {
            'google_id': extra_data.get('sub'),  # Unique Google ID
            'email': extra_data.get('email'),
            'email_verified': extra_data.get('email_verified', False),
            'full_name': extra_data.get('name'),
            'first_name': extra_data.get('given_name'),
            'last_name': extra_data.get('family_name'),
            'picture': extra_data.get('picture'),
            'locale': extra_data.get('locale'),
            'hosted_domain': extra_data.get('hd'),  # For Google Workspace accounts
        }
        logger.debug(f"Google social data: {social_data}")

    except SocialAccount.DoesNotExist:
        # Fallback for non-Google login
        social_data = {
            'google_id': None,
            'email': user.email,
            'email_verified': False,
            'full_name': user.get_full_name() or user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'picture': None,
            'locale': None,
            'hosted_domain': None,
        }
        logger.debug(f"Non-Google user data: {social_data}")

    if request.method == 'POST':
        logger.debug(f"POST data: {request.POST}")
        logger.debug(f"FILES data: {request.FILES}")

        # Mandatory email field
        email = request.POST.get('email')
        if not email:
            messages.error(request, "Email is required.")
            return render(request, 'user_login/user_profile_edit.html', {
                'user': user,
                'social_data': social_data
            })

        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Invalid email format.")
            return render(request, 'user_login/user_profile_edit.html', {
                'user': user,
                'social_data': social_data
            })

        # Check for email uniqueness (excluding current user)
        if email != user.email and request.user.__class__.objects.filter(email=email).exclude(pk=user.pk).exists():
            messages.error(request, "This email is already in use.")
            return render(request, 'user_login/user_profile_edit.html', {
                'user': user,
                'social_data': social_data
            })

        # Update user fields
        user.email = email
        user.name = request.POST.get('name', user.name)
        user.phone = request.POST.get('phone', user.phone)

        # Handle file uploads with validation
        if 'profile_image' in request.FILES:
            profile_image = request.FILES['profile_image']
            if not profile_image.content_type.startswith('image/'):
                messages.error(request, "Profile image must be a valid image file.")
                return render(request, 'user_login/user_profile_edit.html', {
                    'user': user,
                    'social_data': social_data
                })
            user.profile_image = profile_image
            logger.info(f"Profile image uploaded: {user.profile_image}")

        if 'aadhar_image' in request.FILES:
            aadhar_image = request.FILES['aadhar_image']
            if not aadhar_image.content_type.startswith('image/'):
                messages.error(request, "Aadhar image must be a valid image file.")
                return render(request, 'user_login/user_profile_edit.html', {
                    'user': user,
                    'social_data': social_data
                })
            user.aadhar_image = aadhar_image
            logger.info(f"Aadhar image uploaded: {user.aadhar_image}")

        if 'pancard_image' in request.FILES:
            pancard_image = request.FILES['pancard_image']
            if not pancard_image.content_type.startswith('image/'):
                messages.error(request, "Pancard image must be a valid image file.")
                return render(request, 'user_login/user_profile_edit.html', {
                    'user': user,
                    'social_data': social_data
                })
            user.pancard_image = pancard_image
            logger.info(f"Pancard image uploaded: {user.pancard_image}")

        try:
            user.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('user:user_profile')
        except Exception as e:
            logger.error(f"Error saving user profile: {str(e)}")
            messages.error(request, "An error occurred while updating your profile.")
            return render(request, 'user_login/user_profile_edit.html', {
                'user': user,
                'social_data': social_data
            })

    return render(request, 'user_login/user_profile_edit.html', {
        'user': user,
        'social_data': social_data
    })