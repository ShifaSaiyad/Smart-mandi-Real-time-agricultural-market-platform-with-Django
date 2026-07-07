from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie

from .forms import UserLoginForm, UserProfileForm, UserRegistrationForm, UserUpdateForm
from .models import UserProfile


def get_dashboard_redirect_for_user(user):
    if user.is_staff or user.is_superuser:
        return "admin_dashboard:dashboard"
    return "user_app:dashboard"


@never_cache
@ensure_csrf_cookie
def register_view(request):
    if request.user.is_authenticated:
        return redirect(get_dashboard_redirect_for_user(request.user))

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration completed successfully. Your account is already logged in now.")
            return redirect(get_dashboard_redirect_for_user(user))
    else:
        form = UserRegistrationForm()

    return render(request, "user_app/register.html", {"form": form})


@never_cache
@ensure_csrf_cookie
def login_view(request):
    if request.user.is_authenticated:
        return redirect(get_dashboard_redirect_for_user(request.user))

    form = UserLoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, "Login successful.")
        redirect_to = request.POST.get("next") or get_dashboard_redirect_for_user(user)
        return redirect(redirect_to)
    if request.method == "POST" and not form.is_valid():
        messages.error(request, "Login failed. Please check your username and password, then try again with a freshly loaded page.")

    return render(request, "user_app/login.html", {"form": form})


@never_cache
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("user_app:login")


@login_required
def dashboard_view(request):
    if request.user.is_staff or request.user.is_superuser:
        return redirect("admin_dashboard:dashboard")

    profile, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={"phone_number": "0000000000"},
    )
    return render(request, "user_app/dashboard.html", {"profile": profile})


@login_required
def profile_view(request):
    if request.user.is_staff or request.user.is_superuser:
        return redirect("admin_dashboard:dashboard")

    profile, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={"phone_number": "0000000000"},
    )

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("user_app:dashboard")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)

    return render(
        request,
        "user_app/profile.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
        },
    )

# Create your views here.
