from django.core.management.base import BaseCommand
from securities.models import Stock
import json

# python manage.py export_stock_data '2024-04-19 12:00:00' stocks.json

class Command(BaseCommand):
    help = 'Export stock data from a specific timestamp to a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('timestamp', type=str, help='Timestamp to export stock data from (format: YYYY-MM-DD HH:MM:SS)')
        parser.add_argument('output_file', type=str, help='Output JSON file path')

    def handle(self, *args, **kwargs):
        print(' fetching stocks')
        timestamp = kwargs['timestamp']
        output_file = kwargs['output_file']
        stocks = Stock.objects.filter(date_time__gte=timestamp)
        serialized_stocks = [{'symbol': stock.symbol, 'date_time': stock.date_time.strftime('%Y-%m-%d %H:%M:%S'),
                              'open': stock.open, 'high': stock.high, 'low': stock.low,
                              'close': stock.close, 'previous_close': stock.previous_close} for stock in stocks]

        with open(output_file, 'w') as f:
            json.dump(serialized_stocks, f, indent=2)

        self.stdout.write(self.style.SUCCESS('Stock data exported successfully'))
