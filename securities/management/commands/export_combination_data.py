from django.core.management.base import BaseCommand
from securities.models import Combination
import json
# python manage.py export_combination_data 2024-04-19 13:00:00 combinations.json
# python manage.py export_combination_data '2024-04-19 12:00:00' combinations.json

class Command(BaseCommand):
    help = 'Export combination data from a specific timestamp to a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('timestamp', type=str, help='Timestamp to export combination data from (format: YYYY-MM-DD HH:MM:SS)')
        parser.add_argument('output_file', type=str, help='Output JSON file path')

    def handle(self, *args, **kwargs):
        print(' fetching comnination ')
        timestamp = kwargs['timestamp']
        output_file = kwargs['output_file']
        combinations = Combination.objects.filter(date_time__gte=timestamp)
        serialized_combinations = [{'symbol': combination.symbol, 'strike': combination.strike,
                                    'avg': combination.avg, 'stdev': combination.stdev,
                                    'z_score': combination.z_score, 'date_time': combination.date_time.strftime('%Y-%m-%d %H:%M:%S')}
                                   for combination in combinations]

        with open(output_file, 'w') as f:
            json.dump(serialized_combinations, f, indent=2)

        self.stdout.write(self.style.SUCCESS('Combination data exported successfully'))
