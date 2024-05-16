from django.core.management.base import BaseCommand
from securities.models import Missing
import os
import json
class Command(BaseCommand):
    help = 'Dump Combination and Stock data'
    def handle(self, *args, **kwargs):
        try:
            if 'missing_data.txt' in os.listdir():
                f = open('missing_data.txt','r')
                lines = f.readlines()
                for item in lines:
                    content = item.replace('\n','')
                    Missing.objects.create(data=content)
            self.stdout.write(self.style.SUCCESS('Data dumped successfully'))
        except Exception as E:
            self.stdout.write(self.style.SUCCESS(E))
        