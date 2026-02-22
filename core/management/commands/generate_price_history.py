"""
Django management command to generate dummy EnergyPriceHistory data
for BlockWatts Peer-to-Peer Renewable Energy Trading Platform
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from core.models import EnergyPriceHistory


class Command(BaseCommand):
    """
    Management command to generate dummy price history data
    
    Usage:
        python manage.py generate_price_history
        python manage.py generate_price_history --records 100
        python manage.py generate_price_history --clear
    """
    
    help = 'Generate dummy EnergyPriceHistory records for testing and development'

    def add_arguments(self, parser):
        """Add command line arguments"""
        parser.add_argument(
            '--records',
            type=int,
            default=50,
            help='Number of price history records to generate (default: 50)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing price history before generating new data',
        )
        parser.add_argument(
            '--base-price',
            type=float,
            default=5.0,
            help='Base price for energy in ₹ per kWh (default: 5.0)',
        )
        parser.add_argument(
            '--volatility',
            type=float,
            default=0.2,
            help='Price volatility factor (default: 0.2)',
        )

    def handle(self, *args, **options):
        """Main command handler"""
        try:
            records_count = options['records']
            clear_existing = options['clear']
            base_price = Decimal(str(options['base_price']))
            volatility = options['volatility']

            # Validate inputs
            if records_count <= 0:
                raise CommandError('Number of records must be positive')
            
            if base_price <= 0:
                raise CommandError('Base price must be positive')
            
            if volatility <= 0 or volatility >= 1:
                raise CommandError('Volatility must be between 0 and 1')

            # Clear existing data if requested
            if clear_existing:
                deleted_count = EnergyPriceHistory.objects.all().count()
                EnergyPriceHistory.objects.all().delete()
                self.stdout.write(
                    self.style.WARNING(f'Cleared {deleted_count} existing price history records')
                )

            # Generate price history data
            self.stdout.write(f'Generating {records_count} price history records...')
            
            generated_records = self.generate_price_data(
                records_count, base_price, volatility
            )

            # Display summary
            self.display_summary(generated_records)

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully generated {generated_records} price history records'
                )
            )

        except Exception as e:
            raise CommandError(f'Error generating price history: {str(e)}')

    def generate_price_data(self, count, base_price, volatility):
        """
        Generate realistic OHLC price data
        
        Args:
            count: Number of records to generate
            base_price: Base price in ₹ per kWh
            volatility: Price volatility factor
            
        Returns:
            Number of records created
        """
        records = []
        current_time = timezone.now()
        current_price = base_price
        
        for i in range(count):
            # Calculate datetime (going backward 1 hour for each record)
            record_time = current_time - timedelta(hours=i)
            
            # Generate OHLC values with realistic constraints
            ohlc_data = self.generate_ohlc_values(current_price, volatility)
            
            # Create price history record
            price_record = EnergyPriceHistory(
                open=ohlc_data['open'],
                high=ohlc_data['high'],
                low=ohlc_data['low'],
                close=ohlc_data['close'],
                datetime=record_time
            )
            
            records.append(price_record)
            
            # Update current price for next iteration (use close as next open)
            current_price = ohlc_data['close']
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                self.stdout.write(f'Generated {i + 1}/{count} records...')

        # Bulk create all records for better performance
        try:
            EnergyPriceHistory.objects.bulk_create(records, ignore_conflicts=True)
            return len(records)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error saving records: {str(e)}')
            )
            return 0

    def generate_ohlc_values(self, base_price, volatility):
        """
        Generate realistic OHLC values ensuring high >= max(open, close) >= min(open, close) >= low
        
        Args:
            base_price: Base price for this period (Decimal)
            volatility: Volatility factor (float)
            
        Returns:
            Dictionary with open, high, low, close values
        """
        # Convert volatility to Decimal for consistent arithmetic
        volatility_decimal = Decimal(str(volatility))
        
        # Generate random price movements (convert to Decimal)
        price_change = Decimal(str(random.uniform(-volatility, volatility)))
        
        # Calculate open price (previous close + some random movement)
        open_movement = Decimal(str(random.uniform(-volatility/2, volatility/2)))
        open_price = base_price * (Decimal('1') + open_movement)
        
        # Calculate close price
        close_price = open_price * (Decimal('1') + price_change)
        
        # Ensure prices are positive
        min_price = Decimal('0.0001')
        open_price = max(open_price, min_price)
        close_price = max(close_price, min_price)
        
        # Calculate high and low with realistic spreads
        high_spread = Decimal(str(random.uniform(0.01, volatility)))
        low_spread = Decimal(str(random.uniform(0.01, volatility)))
        
        # High should be the maximum of open, close + some spread
        high_price = max(open_price, close_price) * (Decimal('1') + high_spread)
        
        # Low should be the minimum of open, close - some spread
        low_price = min(open_price, close_price) * (Decimal('1') - low_spread)
        
        # Ensure low is positive
        low_price = max(low_price, min_price)
        
        # Round to 4 decimal places for currency precision
        return {
            'open': self.round_decimal(open_price),
            'high': self.round_decimal(high_price),
            'low': self.round_decimal(low_price),
            'close': self.round_decimal(close_price)
        }

    def round_decimal(self, value):
        """Round decimal to 4 places for price precision"""
        return value.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)

    def display_summary(self, records_created):
        """Display summary of generated data"""
        if records_created > 0:
            # Get latest records for summary
            latest_records = EnergyPriceHistory.objects.order_by('-datetime')[:5]
            
            self.stdout.write('\n' + '='*50)
            self.stdout.write('GENERATED DATA SUMMARY')
            self.stdout.write('='*50)
            
            for record in latest_records:
                self.stdout.write(
                    f"{record.datetime.strftime('%Y-%m-%d %H:%M')} | "
                    f"O: ₹{record.open} | H: ₹{record.high} | "
                    f"L: ₹{record.low} | C: ₹{record.close}"
                )
            
            # Calculate some statistics
            all_records = EnergyPriceHistory.objects.all()
            if all_records:
                prices = [float(record.close) for record in all_records]
                avg_price = sum(prices) / len(prices)
                max_price = max(prices)
                min_price = min(prices)
                
                self.stdout.write('\n' + '-'*30)
                self.stdout.write('PRICE STATISTICS')
                self.stdout.write('-'*30)
                self.stdout.write(f"Total Records: {all_records.count()}")
                self.stdout.write(f"Average Price: ₹{avg_price:.4f}")
                self.stdout.write(f"Highest Price: ₹{max_price:.4f}")
                self.stdout.write(f"Lowest Price: ₹{min_price:.4f}")
