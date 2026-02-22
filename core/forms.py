"""
Forms for BlockWatts Peer-to-Peer Renewable Energy Trading Platform
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import EnergyListing, EnergyTransaction, UserBalance


class EnergyListingForm(forms.ModelForm):
    """
    Form for creating new energy listings
    """
    class Meta:
        model = EnergyListing
        fields = ['price_per_kWh', 'quantity_kWh']
        widgets = {
            'price_per_kWh': forms.NumberInput(attrs={
                'class': 'w-full pl-12 pr-4 py-4 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-primary-100 focus:border-primary-500 transition-all duration-200 text-lg font-medium bg-gray-50 hover:bg-white',
                'placeholder': 'Enter price per kWh',
                'step': '0.0001',
                'min': '0.0001',
            }),
            'quantity_kWh': forms.NumberInput(attrs={
                'class': 'w-full pl-12 pr-4 py-4 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-accent-100 focus:border-accent-500 transition-all duration-200 text-lg font-medium bg-gray-50 hover:bg-white',
                'placeholder': 'Enter energy quantity',
                'step': '0.01',
                'min': '0.01',
            })
        }
        labels = {
            'price_per_kWh': 'Price per kWh (₹)',
            'quantity_kWh': 'Energy Quantity (kWh)',
        }
        help_texts = {
            'price_per_kWh': 'Set your energy price in rupees per kilowatt-hour',
            'quantity_kWh': 'Specify the amount of energy you want to sell',
        }

    def clean_price_per_kWh(self):
        price = self.cleaned_data.get('price_per_kWh')
        if price is not None:
            if price <= 0:
                raise ValidationError("Price must be greater than zero.")
            if price > 1000:  # Maximum price limit
                raise ValidationError("Price cannot exceed ₹1000 per kWh.")
        return price

    def clean_quantity_kWh(self):
        quantity = self.cleaned_data.get('quantity_kWh')
        if quantity is not None:
            if quantity <= 0:
                raise ValidationError("Quantity must be greater than zero.")
            if quantity > 10000:  # Maximum quantity limit
                raise ValidationError("Quantity cannot exceed 10,000 kWh.")
        return quantity

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('price_per_kWh')
        quantity = cleaned_data.get('quantity_kWh')
        
        if price and quantity:
            total_value = price * quantity
            if total_value > 100000:  # Maximum total value limit
                raise ValidationError("Total listing value cannot exceed ₹100,000.")
        
        return cleaned_data


class CustomUserCreationForm(UserCreationForm):
    """
    Enhanced user registration form with additional fields
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500',
            'placeholder': 'Enter your email address'
        })
    )
    first_name = forms.CharField(
        max_length=30, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=30, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500',
            'placeholder': 'Enter your last name'
        })
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add custom styling to username and password fields
        self.fields['username'].widget.attrs.update({
            'class': 'mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500',
            'placeholder': 'Create a password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500',
            'placeholder': 'Confirm your password'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    """
    Form for updating user profile information
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-primary-100 focus:border-primary-500 transition-all duration-200 bg-gray-50 hover:bg-white',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-primary-100 focus:border-primary-500 transition-all duration-200 bg-gray-50 hover:bg-white',
                'placeholder': 'Enter your last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-secondary-100 focus:border-secondary-500 transition-all duration-200 bg-gray-50 hover:bg-white',
                'placeholder': 'Enter your email address'
            })
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        user = self.instance
        if User.objects.filter(email=email).exclude(pk=user.pk).exists():
            raise ValidationError("A user with this email already exists.")
        return email


class PasswordChangeForm(forms.Form):
    """
    Custom password change form
    """
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-danger-100 focus:border-danger-500 transition-all duration-200 bg-gray-50 hover:bg-white',
            'placeholder': 'Enter your current password'
        }),
        label="Current Password"
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-primary-100 focus:border-primary-500 transition-all duration-200 bg-gray-50 hover:bg-white',
            'placeholder': 'Enter your new password'
        }),
        label="New Password",
        min_length=8,
        help_text="Password must be at least 8 characters long."
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-primary-100 focus:border-primary-500 transition-all duration-200 bg-gray-50 hover:bg-white',
            'placeholder': 'Confirm your new password'
        }),
        label="Confirm New Password"
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password:
            if new_password != confirm_password:
                raise ValidationError("New passwords do not match.")
        
        return cleaned_data


class BalanceAddForm(forms.Form):
    """
    Form for adding balance to user account (demo purposes)
    """
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=1,
        max_value=100000,
        widget=forms.NumberInput(attrs={
            'class': 'w-full pl-12 pr-4 py-4 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-accent-100 focus:border-accent-500 transition-all duration-200 text-lg font-medium bg-gray-50 hover:bg-white',
            'placeholder': 'Enter amount to add',
            'step': '0.01',
            'min': '1'
        }),
        label="Amount (₹)",
        help_text="Add funds to your BlockWatts wallet (Demo mode)"
    )

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        if amount > 100000:
            raise ValidationError("Maximum amount per transaction is ₹100,000.")
        return amount


class EnergyPurchaseForm(forms.Form):
    """
    Form for purchasing energy from listings
    """
    listing_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-primary-100 focus:border-primary-500 transition-all duration-200',
            'placeholder': 'Enter quantity to purchase',
            'step': '0.01'
        }),
        label="Quantity (kWh)",
        required=False  # Optional if buying full listing
    )

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        return quantity


class MarketFilterForm(forms.Form):
    """
    Form for filtering market listings
    """
    SORT_CHOICES = [
        ('price_asc', 'Price (Low to High)'),
        ('price_desc', 'Price (High to Low)'),
        ('quantity_desc', 'Quantity (High to Low)'),
        ('time_desc', 'Newest First'),
        ('time_asc', 'Oldest First'),
    ]

    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500'
        })
    )
    
    min_price = forms.DecimalField(
        max_digits=10,
        decimal_places=4,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'border border-gray-300 rounded-lg px-3 py-2 text-sm w-24 focus:outline-none focus:ring-2 focus:ring-primary-500',
            'placeholder': '₹0.00',
            'step': '0.0001'
        })
    )
    
    max_price = forms.DecimalField(
        max_digits=10,
        decimal_places=4,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'border border-gray-300 rounded-lg px-3 py-2 text-sm w-24 focus:outline-none focus:ring-2 focus:ring-primary-500',
            'placeholder': '₹1000.00',
            'step': '0.0001'
        })
    )
    
    min_quantity = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'border border-gray-300 rounded-lg px-3 py-2 text-sm w-24 focus:outline-none focus:ring-2 focus:ring-primary-500',
            'placeholder': '0 kWh',
            'step': '0.01'
        })
    )
    
    max_quantity = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'border border-gray-300 rounded-lg px-3 py-2 text-sm w-24 focus:outline-none focus:ring-2 focus:ring-primary-500',
            'placeholder': '10000 kWh',
            'step': '0.01'
        })
    )


class ContactForm(forms.Form):
    """
    Contact form for user support
    """
    SUBJECT_CHOICES = [
        ('general', 'General Inquiry'),
        ('technical', 'Technical Support'),
        ('billing', 'Billing/Payment'),
        ('trading', 'Trading Issue'),
        ('account', 'Account Problem'),
        ('feedback', 'Feedback/Suggestion'),
    ]

    subject = forms.ChoiceField(
        choices=SUBJECT_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-primary-100 focus:border-primary-500 transition-all duration-200'
        })
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-primary-100 focus:border-primary-500 transition-all duration-200',
            'rows': 6,
            'placeholder': 'Please describe your issue or inquiry in detail...'
        }),
        max_length=2000,
        help_text="Maximum 2000 characters"
    )

    def clean_message(self):
        message = self.cleaned_data.get('message')
        if len(message.strip()) < 10:
            raise ValidationError("Message must be at least 10 characters long.")
        return message
