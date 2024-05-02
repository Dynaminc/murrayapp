

from django.core.management.base import BaseCommand
from securities.models import Combination, Stock
import json
from django.core.paginator import Paginator
from datetime import datetime
from securities.simulator import simulate_compute

class Command(BaseCommand):
    help = 'Dump Combination and Stock data'

    # def add_arguments(self, parser):
    #     parser.add_argument('timestamp', type=str, help='Timestamp to filter data (format: YYYY-MM-DD HH:MM:SS)')

    def handle(self, *args, **kwargs):
    
        simulate_compute()
        try:
            self.stdout.write(self.style.SUCCESS('Data dumped successfully'))
        except Exception as E:
            self.stdout.write(self.style.SUCCESS(E))
