"""
URL patterns for core app
"""
from django.urls import path, include
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter
from . import views

# Create API router for ViewSets
router = DefaultRouter()
router.register(r'listings', views.EnergyListingViewSet)
router.register(r'transactions', views.EnergyTransactionViewSet)
router.register(r'price-history', views.EnergyPriceHistoryViewSet)
router.register(r'balances', views.UserBalanceViewSet)

urlpatterns = [
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup_view, name='signup'),
    
    # Protected Web views (HTML pages) - ALL require login
    path('dashboard/', views.dashboard, name='dashboard'),
    path('market/', views.live_market, name='live_market'),
    path('profile-settings/', views.profile_settings, name='profile_settings'),
    
    # API endpoints for AJAX calls
    path('api/deactivate-listing/', views.deactivate_listing, name='deactivate_listing'),
    path('api/buy-energy/', views.buy_energy, name='buy_energy'),
    path('api/market-data/', views.get_market_data, name='get_market_data'),
    
    # API router URLs
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
]
