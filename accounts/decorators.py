from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.urls import reverse


def password_change_required(f):
    """
    Decorator for views that checks if the user's password is not expired, redirecting
    to the account_change_password page if necessary.
    """
    def decorator(request, *args, **kwargs):
        user = User.objects.get(id=request.user.id)
        if user and not user.passwordexpiration.expired():
            return f(request, *args, **kwargs)
        messages.success(request, "Your password has expired and must be changed.", extra_tags="password_expired")
        return redirect(reverse('account_change_password'))
    return decorator
