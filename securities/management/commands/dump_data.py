# from django.core.management import call_command
# from securities.models import Combination, Stock
# import json
# from django.core.serializers.json import DjangoJSONEncoder
# from datetime import datetime

# timestamp = '2024-04-19 13:00:00'
# combinations = Combination.objects.filter(date_time__gte=timestamp)
# stocks = Stock.objects.filter(date_time__gte=timestamp)

# # Convert datetime objects to strings
# serialized_combinations = [
#     {**item, 'date_time': item['date_time'].strftime('%Y-%m-%d %H:%M:%S')}
#     for item in combinations.values()
# ]
# serialized_stocks = [
#     {**item, 'date_time': item['date_time'].strftime('%Y-%m-%d %H:%M:%S')}
#     for item in stocks.values()
# ]

# # Dump serialized data to JSON files
# with open('combinations.json', 'w') as f:
#     json.dump(serialized_combinations, f, indent=2, cls=DjangoJSONEncoder)

# with open('stocks.json', 'w') as f:
#     json.dump(serialized_stocks, f, indent=2, cls=DjangoJSONEncoder)


from django.core.management.base import BaseCommand
from securities.models import Combination, Stock
import json
from datetime import datetime

class Command(BaseCommand):
    help = 'Dump Combination and Stock data'

    def add_arguments(self, parser):
        parser.add_argument('timestamp', type=str, help='Timestamp to filter data (format: YYYY-MM-DD HH:MM:SS)')

    def handle(self, *args, **kwargs):
        timestamp = kwargs['timestamp']
        combinations = Combination.objects.filter(date_time__gte=timestamp).values()
        stocks = Stock.objects.filter(date_time__gte=timestamp).values()

        with open('combinations.json', 'w') as f:
            json.dump(list(combinations), f, indent=2, default=str)

        with open('stocks.json', 'w') as f:
            json.dump(list(stocks), f, indent=2, default=str)

        self.stdout.write(self.style.SUCCESS('Data dumped successfully'))
