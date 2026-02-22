"""
Admin configuration for BlockWatts models
"""
from django.contrib import admin
from .models import UserBalance, EnergyListing, EnergyTransaction, EnergyPriceHistory


@admin.register(UserBalance)
class UserBalanceAdmin(admin.ModelAdmin):
    """Admin configuration for UserBalance model"""
    list_display = ['user', 'balance', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user')


@admin.register(EnergyListing)
class EnergyListingAdmin(admin.ModelAdmin):
    """Admin configuration for EnergyListing model"""
    list_display = ['seller', 'price_per_kWh', 'quantity_kWh', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['seller__username', 'seller__email']
    readonly_fields = ['total_value', 'created_at', 'updated_at']
    list_editable = ['is_active']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('seller')
    
    def total_value(self, obj):
        """Display total value in admin"""
        return f"₹{obj.total_value:.2f}"
    total_value.short_description = "Total Value"


@admin.register(EnergyTransaction)
class EnergyTransactionAdmin(admin.ModelAdmin):
    """Admin configuration for EnergyTransaction model"""
    list_display = ['buyer', 'seller', 'quantity', 'total_price', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['buyer__username', 'seller__username', 'buyer__email', 'seller__email']
    readonly_fields = ['price_per_kWh', 'timestamp']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('buyer', 'seller', 'listing')
    
    def price_per_kWh(self, obj):
        """Display price per kWh in admin"""
        return f"₹{obj.price_per_kWh:.4f}/kWh"
    price_per_kWh.short_description = "Price per kWh"


@admin.register(EnergyPriceHistory)
class EnergyPriceHistoryAdmin(admin.ModelAdmin):
    """Admin configuration for EnergyPriceHistory model"""
    list_display = ['datetime', 'open', 'high', 'low', 'close']
    list_filter = ['datetime', 'created_at']
    readonly_fields = ['created_at']
    date_hierarchy = 'datetime'
    ordering = ['-datetime']
    
    def get_readonly_fields(self, request, obj=None):
        """Make datetime readonly when editing existing objects"""
        if obj:  # Editing an existing object
            return self.readonly_fields + ['datetime']
        return self.readonly_fields
