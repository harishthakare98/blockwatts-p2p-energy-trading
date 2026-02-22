"""
Main URL configuration for blockwatts project.
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def redirect_to_login(request):
    """Redirect root URL to login page"""
    from django.contrib.auth.views import LoginView
    return redirect('login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # Built-in auth URLs
    path('', redirect_to_login, name='home'),  # Redirect root to login
    path('core/', include('core.urls')),  # Your core app URLs
]
