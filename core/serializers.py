"""
Serializers for BlockWatts API endpoints
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserBalance, EnergyListing, EnergyTransaction, EnergyPriceHistory


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with balance information"""
    balance = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'balance']
        read_only_fields = ['id']
    
    def get_balance(self, obj):
        """Get user's current balance"""
        try:
            return str(obj.balance.balance)
        except UserBalance.DoesNotExist:
            return "0.00"


class UserBalanceSerializer(serializers.ModelSerializer):
    """Serializer for UserBalance model"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserBalance
        fields = ['id', 'username', 'balance', 'created_at', 'updated_at']
        read_only_fields = ['id', 'username', 'created_at', 'updated_at']


class EnergyListingSerializer(serializers.ModelSerializer):
    """Serializer for EnergyListing model"""
    seller_username = serializers.CharField(source='seller.username', read_only=True)
    total_value = serializers.ReadOnlyField()
    
    class Meta:
        model = EnergyListing
        fields = [
            'id', 'seller', 'seller_username', 'price_per_kWh', 
            'quantity_kWh', 'total_value', 'is_active', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'seller_username', 'total_value', 'created_at', 'updated_at']


class EnergyTransactionSerializer(serializers.ModelSerializer):
    """Serializer for EnergyTransaction model"""
    buyer_username = serializers.CharField(source='buyer.username', read_only=True)
    seller_username = serializers.CharField(source='seller.username', read_only=True)
    price_per_kWh = serializers.ReadOnlyField()
    
    class Meta:
        model = EnergyTransaction
        fields = [
            'id', 'buyer', 'buyer_username', 'seller', 'seller_username',
            'listing', 'quantity', 'total_price', 'price_per_kWh', 'timestamp'
        ]
        read_only_fields = [
            'id', 'buyer_username', 'seller_username', 
            'price_per_kWh', 'timestamp'
        ]


class EnergyPriceHistorySerializer(serializers.ModelSerializer):
    """Serializer for EnergyPriceHistory model"""
    
    class Meta:
        model = EnergyPriceHistory
        fields = [
            'id', 'open', 'high', 'low', 'close', 
            'datetime', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
