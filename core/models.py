"""
Models for BlockWatts Peer-to-Peer Renewable Energy Trading Platform
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class UserBalance(models.Model):
    """
    User wallet/balance model for paper trading
    Each user gets ₹10,000 as starting balance for paper trading
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='balance'
    )
    balance = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('10000.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="User's current balance in ₹"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Balance"
        verbose_name_plural = "User Balances"

    def __str__(self):
        return f"{self.user.username} - ₹{self.balance}"


class EnergyListing(models.Model):
    """
    Energy listings created by sellers
    Represents available renewable energy for trading
    """
    seller = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='energy_listings'
    )
    price_per_kWh = models.DecimalField(
        max_digits=8, 
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))],
        help_text="Price in ₹ per kWh"
    )
    quantity_kWh = models.DecimalField(
        max_digits=10, 
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
        help_text="Energy quantity in kWh"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this listing is available for trading"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Energy Listing"
        verbose_name_plural = "Energy Listings"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.seller.username} - {self.quantity_kWh}kWh @ ₹{self.price_per_kWh}/kWh"

    @property
    def total_value(self):
        """Calculate total value of the listing"""
        return self.price_per_kWh * self.quantity_kWh


class EnergyTransaction(models.Model):
    """
    Completed energy transactions between buyers and sellers
    Records all successful trades on the platform
    """
    buyer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='buy_transactions'
    )
    seller = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='sell_transactions'
    )
    listing = models.ForeignKey(
        EnergyListing,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        help_text="Original listing (nullable for flexibility)"
    )
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
        help_text="Quantity of energy traded in kWh"
    )
    total_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Total transaction amount in ₹"
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Energy Transaction"
        verbose_name_plural = "Energy Transactions"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.buyer.username} ← {self.seller.username}: {self.quantity}kWh @ ₹{self.total_price}"

    @property
    def price_per_kWh(self):
        """Calculate price per kWh for this transaction"""
        if self.quantity > 0:
            return self.total_price / self.quantity
        return Decimal('0.00')


class EnergyPriceHistory(models.Model):
    """
    OHLC (Open, High, Low, Close) price data for energy trading
    Used for creating price charts and market analysis
    """
    open = models.DecimalField(
        max_digits=8, 
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))],
        help_text="Opening price in ₹ per kWh"
    )
    high = models.DecimalField(
        max_digits=8, 
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))],
        help_text="Highest price in ₹ per kWh"
    )
    low = models.DecimalField(
        max_digits=8, 
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))],
        help_text="Lowest price in ₹ per kWh"
    )
    close = models.DecimalField(
        max_digits=8, 
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))],
        help_text="Closing price in ₹ per kWh"
    )
    datetime = models.DateTimeField(
        db_index=True,
        help_text="Timestamp for this price data point"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Energy Price History"
        verbose_name_plural = "Energy Price History"
        ordering = ['-datetime']
        # Ensure unique datetime entries
        unique_together = ['datetime']

    def __str__(self):
        return f"OHLC {self.datetime.strftime('%Y-%m-%d %H:%M')} - ₹{self.close}/kWh"
