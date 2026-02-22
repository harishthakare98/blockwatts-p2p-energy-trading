"""
Django signals for BlockWatts application
Handles automatic creation of UserBalance for new users
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserBalance
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_balance(sender, instance, created, **kwargs):
    """
    Signal to automatically create UserBalance when a new User is created
    
    Args:
        sender: The model class (User)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        try:
            UserBalance.objects.create(
                user=instance,
                balance=Decimal('10000.00')  # Default ₹10,000 balance
            )
            logger.info(f"UserBalance created for user: {instance.username} with ₹10,000 balance")
        except Exception as e:
            logger.error(f"Failed to create UserBalance for user {instance.username}: {str(e)}")


@receiver(post_save, sender=User)
def save_user_balance(sender, instance, **kwargs):
    """
    Signal to ensure UserBalance exists and is saved when User is updated
    
    Args:
        sender: The model class (User)
        instance: The actual instance being saved
        **kwargs: Additional keyword arguments
    """
    try:
        # Try to get existing UserBalance
        user_balance = instance.balance
        user_balance.save()
    except UserBalance.DoesNotExist:
        # Create UserBalance if it doesn't exist (fallback)
        UserBalance.objects.create(
            user=instance,
            balance=Decimal('10000.00')
        )
        logger.info(f"UserBalance created (fallback) for existing user: {instance.username}")
    except Exception as e:
        logger.error(f"Error handling UserBalance for user {instance.username}: {str(e)}")
