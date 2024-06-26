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
from django.core.paginator import Paginator
from datetime import datetime
from securities.cronjob import new_calc_migrator, clean_comb, new_calc, new_flow_migrator, dji_migrator, real_time_data, cronny, mig_flow
from securities.simulator import simulate_compute
from securities.assess import get_all_stocks, top_glow
from datetime import timedelta
from securities.assess import get_all_stocks, get_test_data, json_migrator

class Command(BaseCommand):
    help = 'Dump Combination and Stock data'

    # def add_arguments(self, parser):
    #     parser.add_argument('timestamp', type=str, help='Timestamp to filter data (format: YYYY-MM-DD HH:MM:SS)')

    def handle(self, *args, **kwargs):
        
        # initial_timestamp = datetime(2024, 5, 15)
        # clean_comb(initial_timestamp)
        # # print("cleaned data")
        # get_test_data()
        # # print('test data obtained')
        # json_migrator()
        # real_time_data()|
        initial_timestamp = datetime(2024, 5, 29, 14, 5)
        # clean_comb(initial_timestamp)
        new_flow_migrator(initial_timestamp)
        return
        initial_timestamp = datetime(2024, 5, 16, 13, 5)
        clean_comb(initial_timestamp)
        
        # mig_flow()
        
        # cronny()
        # final_time = datetime(2024, 4,  3, 9, 30)
        # print(final_time)
        # data = Combination.objects.filter(
        #                 date_time__gte=final_time,
        #                 date_time__lt=(final_time + timedelta(minutes=1))).all()
        # print(len(data))
        # data = Stock.objects.filter(
        #                 date_time__gte=final_time,
        #                 date_time__lt=(final_time + timedelta(minutes=1))).all()
        # print(len(data))
        # data.delete()
        
        # top_glow()
        
        # get_all_stocks()
        # dji_migrator()
        # simulate_compute()
        
        # new_flow_migrator()
        # real_time_data()
        # new_calc_migrator()
        
        # clean_comb()
        # new_calc()
####    CLEANER BLOCK     
        # count = 0 
        # times = [datetime(2024, 4, 22)]
        # # strike = "VZ-WBA-WMT"
        # for item in times:
        #     print('fetcging ')
        #     data = Combination.objects.filter(date_time__gte=item).all()
        #     data.delete()
        #     print('cleaned combinations')
        #     data = Stock.objects.filter(date_time__gte=item).all()
        #     data.delete()
        #     print('cleaned stocks')
            
####
            
        try:
            self.stdout.write(self.style.SUCCESS('Data dumped successfully'))
        except Exception as E:
            self.stdout.write(self.style.SUCCESS(E))
        
        
        # count = 0
        # stock_count = 0
        # try:

        #     combos = []
        #     stock_list = []
        #     for file in ['combination_3.json']: # for file in ['combination_1.json', 'combination_2.json']:
        #         print('Fetching ', file)
        #         with open(file, 'r') as f:
        #             data = json.load(f)

        #         for item in data:
        #             symbol = item['symbol']
        #             strike = item['strike']
        #             avg = item['avg']
        #             stdev = item['stdev']
        #             z_score = item['z_score']
        #             date_time = datetime.strptime(item['date_time'], '%Y-%m-%d %H:%M:%S')
        #             try:
                        
        #                 Combination.objects.create(symbol=symbol, strike=strike, avg=avg, stdev=stdev, z_score=z_score, date_time=date_time)
        #                 count += 1
        #                 print('count', count)
        #             except Exception as E:
        #                 print('Error', E)
                        
        #     self.stdout.write(self.style.SUCCESS('Data dumped successfully'))
        #     # with open('stocks.json', 'r') as f:
        #     #     data = json.load(f)

        #     # for item in data:
        #     #     symbol = item['symbol']
        #     #     date_time = datetime.strptime(item['date_time'], '%Y-%m-%d %H:%M:%S')
        #     #     open_price = item['open']
        #     #     high_price = item['high']
        #     #     low_price = item['low']
        #     #     close_price = item['close']
        #     #     previous_close = item.get('previous_close', None)
        #     #     Stock.objects.create(symbol=symbol, date_time=date_time, open=open_price, high=high_price, low=low_price, close=close_price, previous_close=previous_close)
        #     #     # stock_list.append()
        #     #     stock_count += 1
        #     #     print('Combos ', stock_count)    
                
            
        #     # self.stdout.write(self.style.SUCCESS('Data dumped successfully'))
            
        # except Exception as E:
        #     self.stdout.write(self.style.SUCCESS(E))
            