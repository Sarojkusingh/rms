from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from tenants.models import Institution, InstitutionSettings
from subscriptions.models import Plan, Subscription, Usage
from audit.models import AuditLog
from .forms import LoginForm, UserProfileForm, InstitutionRegisterForm
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import datetime

User = get_user_model()

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard' if not request.user.is_super_admin else 'superadmin_dashboard')
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    # Log Audit
                    AuditLog.objects.create(
                        institution=user.institution,
                        user=user,
                        user_role=user.get_role_display(),
                        action=f"User logged in successfully.",
                        module="AUTH",
                        ip_address=request.META.get('REMOTE_ADDR')
                    )
                    
                    if form.cleaned_data.get('remember_me'):
                        request.session.set_expiry(1209600)  # 2 weeks
                    else:
                        request.session.set_expiry(0)  # Browser close expiry
                        
                    messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
                    if user.is_super_admin:
                        return redirect('superadmin_dashboard')
                    return redirect('dashboard')
                else:
                    messages.error(request, "This account is inactive.")
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
        
    return render(request, 'auth/login.html', {'form': form})

def logout_view(request):
    if request.user.is_authenticated:
        AuditLog.objects.create(
            institution=request.user.institution,
            user=request.user,
            user_role=request.user.get_role_display(),
            action=f"User logged out.",
            module="AUTH",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        logout(request)
        messages.info(request, "You have been logged out.")
    return redirect('login')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = InstitutionRegisterForm(request.POST)
        if form.is_valid():
            # 1. Create Institution
            inst = Institution.objects.create(
                name=form.cleaned_data['institution_name'],
                slug=form.cleaned_data['institution_slug'],
                contact_email=form.cleaned_data['contact_email']
            )
            
            # 2. Create default settings
            InstitutionSettings.objects.create(institution=inst)
            
            # 3. Create Owner User
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                role=User.Role.INSTITUTION_OWNER,
                institution=inst
            )
            
            # 4. Create Mock Starter Subscription & Usage
            starter_plan, _ = Plan.objects.get_or_create(
                name="Starter",
                defaults={
                    'student_limit': 500,
                    'faculty_limit': 50,
                    'storage_limit_gb': 10,
                    'price_monthly': 49.00
                }
            )
            
            today = datetime.date.today()
            Subscription.objects.create(
                institution=inst,
                plan=starter_plan,
                start_date=today,
                end_date=today + datetime.timedelta(days=14),  # 14 days trial
                next_billing_date=today + datetime.timedelta(days=14),
                is_trial=True,
                status=Subscription.Status.TRIAL
            )
            
            Usage.objects.create(
                institution=inst,
                current_admins=1,
                current_students=0,
                current_faculty=0
            )
            
            # 5. Login owner
            login(request, user)
            
            # Log Audit
            AuditLog.objects.create(
                institution=inst,
                user=user,
                user_role=user.get_role_display(),
                action=f"Self-registered Institution and Owner Account.",
                module="AUTH",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, f"Registration successful! Welcome to RMS SaaS, {user.username}.")
            return redirect('dashboard')
    else:
        form = InstitutionRegisterForm()
        
    return render(request, 'auth/register.html', {'form': form})

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            AuditLog.objects.create(
                institution=request.user.institution,
                user=request.user,
                user_role=request.user.get_role_display(),
                action="Updated profile information.",
                module="AUTH",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, "Your profile has been updated.")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
        
    return render(request, 'auth/profile.html', {
        'form': form,
        'breadcrumbs': [{'name': 'Profile', 'url': '#'}]
    })

@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            AuditLog.objects.create(
                institution=request.user.institution,
                user=request.user,
                user_role=request.user.get_role_display(),
                action="Changed password.",
                module="AUTH",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, "Your password was successfully updated!")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(request.user)
        
    return render(request, 'auth/change_password.html', {
        'form': form,
        'breadcrumbs': [{'name': 'Profile', 'url': '/profile/'}, {'name': 'Change Password', 'url': '#'}]
    })

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        # Always show success message to prevent email enumeration
        messages.success(request, f"If an account is associated with {email}, a password reset link has been sent.")
        
        # Look up user by email
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            # Don't reveal that the email doesn't exist
            return redirect('login')
        
        # Generate token and uid
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Build reset URL
        reset_url = request.build_absolute_uri(f'/reset-password/{uid}/{token}/')
        
        # Render email content
        email_html = render_to_string('auth/password_reset_email.html', {
            'user': user,
            'reset_url': reset_url,
            'expiry_hours': 1,
        })
        
        # Send email
        try:
            send_mail(
                subject='RMS SaaS — Password Reset Request',
                message=f'Hi {user.get_full_name() or user.username}, use this link to reset your password: {reset_url}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=email_html,
                fail_silently=False,
            )
        except Exception:
            # Log failure but don't expose it to the user
            pass
        
        # Audit log
        AuditLog.objects.create(
            institution=user.institution,
            user=user,
            user_role=user.get_role_display(),
            action="Requested password reset email.",
            module="AUTH",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return redirect('login')
    return render(request, 'auth/forgot_password.html')

def reset_password_view(request, uidb64=None, token=None):
    # Validate uidb64 and token
    valid_link = False
    user = None
    
    if uidb64 and token:
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            valid_link = default_token_generator.check_token(user, token)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            valid_link = False
    
    if not valid_link:
        return render(request, 'auth/reset_password.html', {
            'valid_link': False,
        })
    
    errors = []
    if request.method == 'POST':
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if not password:
            errors.append("Password is required.")
        elif password != confirm_password:
            errors.append("Passwords do not match.")
        else:
            # Validate password against Django validators
            try:
                validate_password(password, user=user)
            except ValidationError as e:
                errors.extend(e.messages)
        
        if not errors:
            user.set_password(password)
            user.save()
            
            # Audit log
            AuditLog.objects.create(
                institution=user.institution,
                user=user,
                user_role=user.get_role_display(),
                action="Password reset via email link.",
                module="AUTH",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, "Your password has been successfully reset. Please log in with your new password.")
            return redirect('login')
    
    return render(request, 'auth/reset_password.html', {
        'valid_link': True,
        'errors': errors,
    })

def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard' if not request.user.is_super_admin else 'superadmin_dashboard')
    
    # Query pricing plans to render on the landing page pricing section dynamically
    plans = Plan.objects.filter(is_active=True)[:4]
    return render(request, 'public/home.html', {'plans': plans})

def features_view(request):
    return render(request, 'public/features.html')

def pricing_view(request):
    plans = Plan.objects.filter(is_active=True)
    return render(request, 'public/pricing.html', {'plans': plans})

def about_view(request):
    return render(request, 'public/about.html')

def contact_view(request):
    if request.method == 'POST':
        messages.success(request, "Thank you for contacting us! We will get back to you shortly.")
        return redirect('contact')
    return render(request, 'public/contact.html')

