"""
Views for BlockWatts Peer-to-Peer Renewable Energy Trading Platform
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models, transaction
from django.utils import timezone
from datetime import timedelta, date
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .forms import CustomUserCreationForm

from .models import UserBalance, EnergyListing, EnergyTransaction, EnergyPriceHistory
from .forms import EnergyListingForm
from .serializers import (
    UserBalanceSerializer, EnergyListingSerializer, 
    EnergyTransactionSerializer, EnergyPriceHistorySerializer
)


# =============================================================================
# WEB VIEWS (for HTML templates)
# =============================================================================

@login_required
def dashboard(request):
    """
    Enhanced dashboard view with proper statistics calculation and balance management
    """
    # Handle POST request (form submission for creating listings)
    if request.method == 'POST':
        form = EnergyListingForm(request.POST)
        if form.is_valid():
            # Calculate total cost
            total_cost = form.cleaned_data['price_per_kWh'] * form.cleaned_data['quantity_kWh']
            
            # Get user balance
            try:
                user_balance = request.user.balance
            except UserBalance.DoesNotExist:
                user_balance = UserBalance.objects.create(
                    user=request.user,
                    balance=10000.00
                )
            
            # Check if user has sufficient balance
            if user_balance.balance < total_cost:
                messages.error(
                    request, 
                    f'Insufficient balance! You need ₹{total_cost:.2f} but only have ₹{user_balance.balance:.2f}'
                )
            else:
                try:
                    with transaction.atomic():
                        # Save the listing
                        listing = form.save(commit=False)
                        listing.seller = request.user
                        listing.is_active = True
                        listing.save()
                        
                        # Deduct balance
                        user_balance.balance -= total_cost
                        user_balance.save()
                    
                    messages.success(
                        request, 
                        f'Energy listing created successfully! '
                        f'{listing.quantity_kWh} kWh at ₹{listing.price_per_kWh}/kWh. '
                        f'₹{total_cost:.2f} deducted from your balance.'
                    )
                    
                    return redirect('dashboard')
                    
                except Exception as e:
                    messages.error(request, f'Error creating listing: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors in the form below.')
    else:
        form = EnergyListingForm()
    
    # Get data for dashboard display
    active_listings = EnergyListing.objects.filter(
        is_active=True
    ).select_related('seller').order_by('-created_at')
    
    # Get all user transactions (unsliced for calculations) - FIXED: QuerySet slicing issue
    user_transactions_queryset = EnergyTransaction.objects.filter(
        models.Q(buyer=request.user) | models.Q(seller=request.user)
    ).select_related('buyer', 'seller', 'listing').order_by('-timestamp')
    
    # Calculate today's trades - FIXED
    today = timezone.now().date()
    todays_trades = user_transactions_queryset.filter(
        timestamp__date=today
    ).count()
    
    # Calculate this week's trades
    week_ago = timezone.now() - timedelta(days=7)
    weekly_trades = user_transactions_queryset.filter(
        timestamp__gte=week_ago
    ).count()
    
    # Calculate average price - FIXED with proper weighted average
    recent_transactions_for_avg = user_transactions_queryset[:50]  # Last 50 transactions
    if recent_transactions_for_avg.exists():
        # Calculate weighted average price
        total_value = sum(float(t.total_price) for t in recent_transactions_for_avg)
        total_quantity = sum(float(t.quantity) for t in recent_transactions_for_avg)
        avg_price = total_value / total_quantity if total_quantity > 0 else 0
    else:
        avg_price = 0
    
    # Get recent transactions for display (sliced AFTER calculations)
    recent_transactions = user_transactions_queryset[:10]
    
    # Calculate user's portfolio statistics
    user_purchases = user_transactions_queryset.filter(buyer=request.user)
    user_sales = user_transactions_queryset.filter(seller=request.user)
    
    total_purchased = user_purchases.aggregate(
        total_spent=models.Sum('total_price'),
        total_energy=models.Sum('quantity')
    )
    
    total_sold = user_sales.aggregate(
        total_earned=models.Sum('total_price'),
        total_energy=models.Sum('quantity')
    )
    
    # Calculate market statistics
    all_transactions_today = EnergyTransaction.objects.filter(
        timestamp__date=today
    )
    
    market_volume_today = all_transactions_today.aggregate(
        volume=models.Sum('total_price')
    )['volume'] or 0
    
    # Get latest market price
    latest_transaction = EnergyTransaction.objects.order_by('-timestamp').first()
    latest_price = float(latest_transaction.price_per_kWh) if latest_transaction else 0
    
    # Ensure user has a balance record
    try:
        user_balance = request.user.balance
    except UserBalance.DoesNotExist:
        user_balance = UserBalance.objects.create(
            user=request.user,
            balance=10000.00
        )
    
    context = {
        'form': form,
        'active_listings': active_listings,
        'recent_transactions': recent_transactions,
        'todays_trades': todays_trades,
        'weekly_trades': weekly_trades,
        'avg_price': avg_price,
        'user_balance': user_balance,
        'total_purchased': total_purchased,
        'total_sold': total_sold,
        'market_volume_today': market_volume_today,
        'latest_price': latest_price,
    }
    
    return render(request, 'dashboard.html', context)


# =============================================================================
# API ENDPOINTS FOR LISTING MANAGEMENT
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def deactivate_listing(request):
    """
    API endpoint to deactivate/remove a listing and refund balance
    """
    try:
        data = json.loads(request.body)
        listing_id = data.get('listing_id')
        
        if not listing_id:
            return JsonResponse({'error': 'Listing ID is required'}, status=400)
        
        try:
            listing = EnergyListing.objects.get(
                id=listing_id, 
                seller=request.user, 
                is_active=True
            )
        except EnergyListing.DoesNotExist:
            return JsonResponse(
                {'error': 'Listing not found or not owned by you'}, 
                status=404
            )
        
        # Calculate refund amount
        refund_amount = listing.price_per_kWh * listing.quantity_kWh
        
        with transaction.atomic():
            # Deactivate the listing
            listing.is_active = False
            listing.save()
            
            # Refund the balance to user
            user_balance = request.user.balance
            user_balance.balance += refund_amount
            user_balance.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Listing removed successfully. ₹{refund_amount:.2f} refunded to your balance.',
            'new_balance': float(user_balance.balance),
            'refund_amount': float(refund_amount)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def buy_energy(request):
    """
    API endpoint to buy energy from a listing
    """
    try:
        data = json.loads(request.body)
        listing_id = data.get('listing_id')
        
        if not listing_id:
            return JsonResponse({'error': 'Listing ID is required'}, status=400)
        
        try:
            listing = EnergyListing.objects.get(id=listing_id, is_active=True)
        except EnergyListing.DoesNotExist:
            return JsonResponse(
                {'error': 'Listing not found or no longer available'}, 
                status=404
            )
        
        # Check if trying to buy own listing
        if listing.seller == request.user:
            return JsonResponse({'error': 'Cannot buy your own listing'}, status=400)
        
        # Calculate total cost
        total_cost = listing.price_per_kWh * listing.quantity_kWh
        
        # Check buyer balance
        try:
            buyer_balance = request.user.balance
        except UserBalance.DoesNotExist:
            return JsonResponse({'error': 'Buyer balance not found'}, status=400)
        
        if buyer_balance.balance < total_cost:
            return JsonResponse({
                'error': f'Insufficient balance. Need ₹{total_cost:.2f}, have ₹{buyer_balance.balance:.2f}'
            }, status=400)
        
        # Process the transaction atomically
        try:
            with transaction.atomic():
                # Create transaction record
                energy_transaction = EnergyTransaction.objects.create(
                    buyer=request.user,
                    seller=listing.seller,
                    listing=listing,
                    quantity=listing.quantity_kWh,
                    total_price=total_cost
                )
                
                # Update balances
                buyer_balance.balance -= total_cost
                buyer_balance.save()
                
                seller_balance = listing.seller.balance
                seller_balance.balance += total_cost
                seller_balance.save()
                
                # Deactivate the listing
                listing.is_active = False
                listing.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Energy purchased successfully',
                'transaction_id': energy_transaction.id,
                'new_balance': float(buyer_balance.balance),
                'seller_name': listing.seller.username,
                'quantity': float(listing.quantity_kWh),
                'total_price': float(total_cost),
                'price_per_kWh': float(listing.price_per_kWh)
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Transaction failed: {str(e)}'}, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


# =============================================================================
# API VIEWSETS (for REST API)
# =============================================================================

class UserBalanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user balances
    """
    queryset = UserBalance.objects.all()
    serializer_class = UserBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Users can only see their own balance unless they're superuser"""
        if self.request.user.is_superuser:
            return UserBalance.objects.all()
        return UserBalance.objects.filter(user=self.request.user)


class EnergyListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing energy listings
    """
    queryset = EnergyListing.objects.filter(is_active=True)
    serializer_class = EnergyListingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return active listings with optional filtering"""
        queryset = EnergyListing.objects.filter(is_active=True)
        
        # Filter by seller if specified
        seller_id = self.request.query_params.get('seller', None)
        if seller_id is not None:
            queryset = queryset.filter(seller_id=seller_id)
            
        # Filter by price range if specified
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        if min_price is not None:
            queryset = queryset.filter(price_per_kWh__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price_per_kWh__lte=max_price)
            
        return queryset.select_related('seller').order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set the seller to the current user and handle balance deduction"""
        # Calculate total cost
        price = serializer.validated_data['price_per_kWh']
        quantity = serializer.validated_data['quantity_kWh']
        total_cost = price * quantity
        
        # Check user balance
        try:
            user_balance = self.request.user.balance
        except UserBalance.DoesNotExist:
            user_balance = UserBalance.objects.create(
                user=self.request.user,
                balance=10000.00
            )
        
        if user_balance.balance < total_cost:
            raise ValidationError(
                f'Insufficient balance. Need ₹{total_cost:.2f}, have ₹{user_balance.balance:.2f}'
            )
        
        # Save listing and deduct balance atomically
        with transaction.atomic():
            serializer.save(seller=self.request.user)
            user_balance.balance -= total_cost
            user_balance.save()
    
    @action(detail=False, methods=['get'])
    def my_listings(self, request):
        """Get current user's listings"""
        listings = EnergyListing.objects.filter(
            seller=request.user
        ).select_related('seller').order_by('-created_at')
        serializer = self.get_serializer(listings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def buy(self, request, pk=None):
        """Buy energy from a listing via API"""
        listing = self.get_object()
        
        # Check if trying to buy own listing
        if listing.seller == request.user:
            return Response(
                {'error': 'Cannot buy your own listing'}, 
                status=400
            )
        
        # Check if listing is still active
        if not listing.is_active:
            return Response(
                {'error': 'Listing is no longer active'}, 
                status=400
            )
        
        # Calculate total cost
        total_cost = listing.price_per_kWh * listing.quantity_kWh
        
        # Check buyer balance
        try:
            buyer_balance = request.user.balance
        except UserBalance.DoesNotExist:
            return Response(
                {'error': 'Buyer balance not found'}, 
                status=400
            )
        
        if buyer_balance.balance < total_cost:
            return Response(
                {'error': f'Insufficient balance. Need ₹{total_cost:.2f}, have ₹{buyer_balance.balance:.2f}'}, 
                status=400
            )
        
        # Process the transaction atomically
        try:
            with transaction.atomic():
                # Create transaction record
                energy_transaction = EnergyTransaction.objects.create(
                    buyer=request.user,
                    seller=listing.seller,
                    listing=listing,
                    quantity=listing.quantity_kWh,
                    total_price=total_cost
                )
                
                # Update balances
                buyer_balance.balance -= total_cost
                buyer_balance.save()
                
                seller_balance = listing.seller.balance
                seller_balance.balance += total_cost
                seller_balance.save()
                
                # Deactivate the listing
                listing.is_active = False
                listing.save()
            
            return Response({
                'success': True,
                'message': 'Energy purchased successfully',
                'transaction_id': energy_transaction.id,
                'new_balance': float(buyer_balance.balance)
            })
            
        except Exception as e:
            return Response(
                {'error': f'Transaction failed: {str(e)}'}, 
                status=500
            )


class EnergyTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing energy transactions (read-only)
    """
    queryset = EnergyTransaction.objects.all()
    serializer_class = EnergyTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter transactions based on user permissions"""
        if self.request.user.is_superuser:
            return EnergyTransaction.objects.all().select_related(
                'buyer', 'seller', 'listing'
            ).order_by('-timestamp')
        
        # Regular users see only their transactions
        return EnergyTransaction.objects.filter(
            models.Q(buyer=self.request.user) | models.Q(seller=self.request.user)
        ).select_related('buyer', 'seller', 'listing').order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def my_purchases(self, request):
        """Get current user's purchases"""
        transactions = EnergyTransaction.objects.filter(
            buyer=request.user
        ).select_related('buyer', 'seller', 'listing').order_by('-timestamp')
        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_sales(self, request):
        """Get current user's sales"""
        transactions = EnergyTransaction.objects.filter(
            seller=request.user
        ).select_related('buyer', 'seller', 'listing').order_by('-timestamp')
        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get transaction statistics for the user"""
        user_transactions = self.get_queryset()
        
        purchases = user_transactions.filter(buyer=request.user)
        sales = user_transactions.filter(seller=request.user)
        
        total_bought = purchases.aggregate(
            total=models.Sum('total_price'),
            quantity=models.Sum('quantity')
        )
        
        total_sold = sales.aggregate(
            total=models.Sum('total_price'),
            quantity=models.Sum('quantity')
        )
        
        return Response({
            'total_purchases': purchases.count(),
            'total_sales': sales.count(),
            'total_bought_value': total_bought['total'] or 0,
            'total_sold_value': total_sold['total'] or 0,
            'total_bought_quantity': total_bought['quantity'] or 0,
            'total_sold_quantity': total_sold['quantity'] or 0,
        })


class EnergyPriceHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing energy price history (read-only)
    """
    queryset = EnergyPriceHistory.objects.all()
    serializer_class = EnergyPriceHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on period parameter"""
        queryset = EnergyPriceHistory.objects.all()
        period = self.request.query_params.get('period', '24h')
        
        now = timezone.now()
        
        # Filter by time period
        if period == '24h':
            start_time = now - timedelta(hours=24)
        elif period == '7d':
            start_time = now - timedelta(days=7)
        elif period == '30d':
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(hours=24)  # default to 24h
            
        queryset = queryset.filter(datetime__gte=start_time)
        
        # Optional: Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            try:
                start_datetime = timezone.datetime.fromisoformat(start_date)
                queryset = queryset.filter(datetime__gte=start_datetime)
            except ValueError:
                pass  # Ignore invalid date format
                
        if end_date:
            try:
                end_datetime = timezone.datetime.fromisoformat(end_date)
                queryset = queryset.filter(datetime__lte=end_datetime)
            except ValueError:
                pass  # Ignore invalid date format
        
        return queryset.order_by('datetime')
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get the latest price data"""
        latest_price = EnergyPriceHistory.objects.order_by('-datetime').first()
        if latest_price:
            serializer = self.get_serializer(latest_price)
            return Response(serializer.data)
        return Response({'message': 'No price data available'})
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get price summary statistics"""
        period = self.request.query_params.get('period', '24h')
        queryset = self.get_queryset()
        
        if not queryset.exists():
            return Response({
                'message': 'No data available for the specified period'
            })
        
        # Calculate statistics
        stats = queryset.aggregate(
            avg_price=models.Avg('close'),
            max_price=models.Max('high'),
            min_price=models.Min('low'),
            latest_price=models.Max('close'),
            count=models.Count('id')
        )
        
        # Get first and last prices for percentage change
        first_price = queryset.order_by('datetime').first()
        last_price = queryset.order_by('-datetime').first()
        
        percentage_change = 0
        if first_price and last_price and first_price.close > 0:
            percentage_change = (
                (float(last_price.close) - float(first_price.close)) / 
                float(first_price.close) * 100
            )
        
        return Response({
            'period': period,
            'average_price': stats['avg_price'],
            'highest_price': stats['max_price'],
            'lowest_price': stats['min_price'],
            'latest_price': stats['latest_price'],
            'percentage_change': round(percentage_change, 2),
            'data_points': stats['count'],
            'period_start': first_price.datetime if first_price else None,
            'period_end': last_price.datetime if last_price else None,
        })


# =============================================================================
# ADDITIONAL UTILITY VIEWS
# =============================================================================

@login_required
def user_profile(request):
    """User profile view with comprehensive user data"""
    try:
        user_balance = request.user.balance
    except UserBalance.DoesNotExist:
        user_balance = UserBalance.objects.create(
            user=request.user,
            balance=10000.00
        )
    
    # Get user's recent listings
    user_listings = EnergyListing.objects.filter(
        seller=request.user
    ).order_by('-created_at')[:10]
    
    # Get user's recent transactions
    user_transactions = EnergyTransaction.objects.filter(
        models.Q(buyer=request.user) | models.Q(seller=request.user)
    ).select_related('buyer', 'seller', 'listing').order_by('-timestamp')[:10]
    
    # Calculate user statistics
    total_purchases = EnergyTransaction.objects.filter(buyer=request.user).count()
    total_sales = EnergyTransaction.objects.filter(seller=request.user).count()
    
    # Calculate earnings and spendings
    purchases_data = EnergyTransaction.objects.filter(buyer=request.user).aggregate(
        total_spent=models.Sum('total_price'),
        total_energy_bought=models.Sum('quantity')
    )
    
    sales_data = EnergyTransaction.objects.filter(seller=request.user).aggregate(
        total_earned=models.Sum('total_price'),
        total_energy_sold=models.Sum('quantity')
    )
    
    context = {
        'user_balance': user_balance,
        'recent_listings': user_listings,
        'recent_transactions': user_transactions,
        'total_purchases': total_purchases,
        'total_sales': total_sales,
        'purchases_data': purchases_data,
        'sales_data': sales_data,
    }
    
    return render(request, 'user_profile.html', context)


@login_required
def market_overview(request):
    """Market overview page with comprehensive market data"""
    # Get all active listings
    active_listings = EnergyListing.objects.filter(is_active=True).select_related('seller')
    
    # Calculate market statistics
    market_stats = active_listings.aggregate(
        total_listings=models.Count('id'),
        total_energy_available=models.Sum('quantity_kWh'),
        avg_price=models.Avg('price_per_kWh'),
        min_price=models.Min('price_per_kWh'),
        max_price=models.Max('price_per_kWh'),
    )
    
    # Get recent transactions for market activity
    recent_market_transactions = EnergyTransaction.objects.select_related(
        'buyer', 'seller', 'listing'
    ).order_by('-timestamp')[:20]
    
    # Calculate daily volume
    today = timezone.now().date()
    daily_volume = EnergyTransaction.objects.filter(
        timestamp__date=today
    ).aggregate(
        total_volume=models.Sum('total_price'),
        total_energy=models.Sum('quantity')
    )
    
    context = {
        'active_listings': active_listings[:20],  # Limit for page performance
        'market_stats': market_stats,
        'recent_transactions': recent_market_transactions,
        'daily_volume': daily_volume,
    }
    
    return render(request, 'market_overview.html', context)


@login_required
def live_market(request):
    """
    Live market page with real-time energy trading data
    """
    # Get all active listings
    active_listings = EnergyListing.objects.filter(
        is_active=True
    ).select_related('seller').order_by('-created_at')
    
    # Calculate market statistics
    market_stats = active_listings.aggregate(
        total_listings=models.Count('id'),
        total_energy_available=models.Sum('quantity_kWh'),
        avg_price=models.Avg('price_per_kWh'),
        min_price=models.Min('price_per_kWh'),
        max_price=models.Max('price_per_kWh'),
    )
    
    # Get recent transactions for market activity
    recent_market_transactions = EnergyTransaction.objects.select_related(
        'buyer', 'seller', 'listing'
    ).order_by('-timestamp')[:20]
    
    # Calculate daily volume
    today = timezone.now().date()
    daily_volume = EnergyTransaction.objects.filter(
        timestamp__date=today
    ).aggregate(
        total_volume=models.Sum('total_price'),
        total_energy=models.Sum('quantity'),
        total_trades=models.Count('id')
    )
    
    # Get top sellers and buyers
    top_sellers = EnergyTransaction.objects.filter(
        timestamp__date=today
    ).values('seller__username').annotate(
        total_sold=models.Sum('total_price'),
        energy_sold=models.Sum('quantity')
    ).order_by('-total_sold')[:5]
    
    top_buyers = EnergyTransaction.objects.filter(
        timestamp__date=today
    ).values('buyer__username').annotate(
        total_bought=models.Sum('total_price'),
        energy_bought=models.Sum('quantity')
    ).order_by('-total_bought')[:5]
    
    # Ensure user has a balance record
    try:
        user_balance = request.user.balance
    except UserBalance.DoesNotExist:
        user_balance = UserBalance.objects.create(
            user=request.user,
            balance=10000.00
        )
    
    context = {
        'active_listings': active_listings,
        'market_stats': market_stats,
        'recent_transactions': recent_market_transactions,
        'daily_volume': daily_volume,
        'top_sellers': top_sellers,
        'top_buyers': top_buyers,
        'user_balance': user_balance,
    }
    
    return render(request, 'live_market.html', context)


@login_required
def get_market_data(request):
    """
    API endpoint to get live market data for AJAX updates
    """
    try:
        # Get fresh market data
        active_listings = EnergyListing.objects.filter(is_active=True).select_related('seller')
        
        market_stats = active_listings.aggregate(
            total_listings=models.Count('id'),
            total_energy_available=models.Sum('quantity_kWh'),
            avg_price=models.Avg('price_per_kWh'),
            min_price=models.Min('price_per_kWh'),
            max_price=models.Max('price_per_kWh'),
        )
        
        # Get recent transactions
        recent_transactions = EnergyTransaction.objects.select_related(
            'buyer', 'seller'
        ).order_by('-timestamp')[:10]
        
        # Format listings data
        listings_data = []
        for listing in active_listings[:20]:  # Limit for performance
            listings_data.append({
                'id': listing.id,
                'seller_name': listing.seller.username,
                'quantity': float(listing.quantity_kWh),
                'price': float(listing.price_per_kWh),
                'total_value': float(listing.price_per_kWh * listing.quantity_kWh),
                'created_at': listing.created_at.isoformat(),
                'is_own': listing.seller == request.user,
            })
        
        # Format transactions data
        transactions_data = []
        for transaction in recent_transactions:
            transactions_data.append({
                'id': transaction.id,
                'buyer': transaction.buyer.username,
                'seller': transaction.seller.username,
                'quantity': float(transaction.quantity),
                'price': float(transaction.price_per_kWh),
                'total': float(transaction.total_price),
                'timestamp': transaction.timestamp.isoformat(),
            })
        
        return JsonResponse({
            'success': True,
            'market_stats': {
                'total_listings': market_stats['total_listings'] or 0,
                'total_energy': float(market_stats['total_energy_available'] or 0),
                'avg_price': float(market_stats['avg_price'] or 0),
                'min_price': float(market_stats['min_price'] or 0),
                'max_price': float(market_stats['max_price'] or 0),
            },
            'listings': listings_data,
            'transactions': transactions_data,
            'timestamp': timezone.now().isoformat(),
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def profile_settings(request):
    """
    Profile settings page with user information management
    """
    if request.method == 'POST':
        # Handle form submissions
        action = request.POST.get('action')
        
        if action == 'update_profile':
            # Update basic profile information
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            
            # Validate email uniqueness
            if email != request.user.email and User.objects.filter(email=email).exists():
                messages.error(request, 'This email address is already in use.')
            else:
                try:
                    request.user.first_name = first_name
                    request.user.last_name = last_name
                    request.user.email = email
                    request.user.save()
                    messages.success(request, 'Profile updated successfully!')
                except Exception as e:
                    messages.error(request, f'Error updating profile: {str(e)}')
        
        elif action == 'change_password':
            # Handle password change
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            elif len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
            else:
                try:
                    request.user.set_password(new_password)
                    request.user.save()
                    messages.success(request, 'Password changed successfully! Please log in again.')
                    return redirect('login')
                except Exception as e:
                    messages.error(request, f'Error changing password: {str(e)}')
        
        elif action == 'add_balance':
            # Handle balance addition (simulation)
            amount = request.POST.get('amount', '0')
            try:
                amount = float(amount)
                if amount > 0:
                    user_balance = request.user.balance
                    user_balance.balance += amount
                    user_balance.save()
                    messages.success(request, f'₹{amount:.2f} added to your account successfully!')
                else:
                    messages.error(request, 'Please enter a valid amount.')
            except (ValueError, UserBalance.DoesNotExist):
                messages.error(request, 'Error processing balance addition.')
        
        return redirect('profile_settings')
    
    # Get user statistics
    user_transactions = EnergyTransaction.objects.filter(
        models.Q(buyer=request.user) | models.Q(seller=request.user)
    ).select_related('buyer', 'seller', 'listing').order_by('-timestamp')
    
    user_listings = EnergyListing.objects.filter(
        seller=request.user
    ).order_by('-created_at')
    
    # Calculate user statistics
    total_purchases = user_transactions.filter(buyer=request.user).count()
    total_sales = user_transactions.filter(seller=request.user).count()
    
    purchases_data = user_transactions.filter(buyer=request.user).aggregate(
        total_spent=models.Sum('total_price'),
        total_energy_bought=models.Sum('quantity')
    )
    
    sales_data = user_transactions.filter(seller=request.user).aggregate(
        total_earned=models.Sum('total_price'),
        total_energy_sold=models.Sum('quantity')
    )
    
    # Ensure user has a balance record
    try:
        user_balance = request.user.balance
    except UserBalance.DoesNotExist:
        user_balance = UserBalance.objects.create(
            user=request.user,
            balance=10000.00
        )
    
    context = {
        'user_balance': user_balance,
        'recent_transactions': user_transactions[:10],
        'user_listings': user_listings[:10],
        'total_purchases': total_purchases,
        'total_sales': total_sales,
        'purchases_data': purchases_data,
        'sales_data': sales_data,
        'active_listings_count': user_listings.filter(is_active=True).count(),
        'total_listings_count': user_listings.count(),
    }
    
    return render(request, 'profile_settings.html', context)


def signup_view(request):
    """
    User registration view with redirect to login
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Save the new user
            user = form.save()
            
            # Create user balance record
            try:
                UserBalance.objects.create(
                    user=user,
                    balance=10000.00  # Starting balance
                )
                balance_message = " You have been credited with ₹10,000 starting balance."
            except Exception as e:
                print(f"Failed to create balance for user {user.username}: {e}")
                balance_message = ""
            
            # Success message for login page
            messages.success(
                request, 
                f'🎉 Welcome to BlockWatts, {user.username}! Your account has been created successfully.{balance_message} Please log in to access your energy trading dashboard.'
            )
            
            # Redirect to login page
            return redirect('login')
            
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/signup.html', {'form': form})