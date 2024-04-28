from datetime import datetime, timedelta, time
from .models import Stock, Combination
from django.db.models import Q


def simulate_compute():
    timestamp = input("time: ")
    
    # fetches the max and min of that time stamp
    
    info = {'current_price': 0, 'open_price':0, 'max_close_price': 0, 'max_percent': 0, 'max_percent_time': None, 'min_percent':0, 'current_percent': 0,'min_percent_time': None, 'close_time': None}
    start_timestamp = datetime.strptime(str(timestamp), "%Y-%m-%d %H:%M:%S")
    tmp_distinct_timestamps = [item['date_time'] for item in Stock.objects.values("date_time").order_by("date_time").distinct()]
    
    filtered_combinations = Combination.objects.filter(date_time = start_timestamp).exclude(symbol = "DJI")
    combs = [{'symbol':item.symbol,'stdev':item.stdev,'score':item.avg,'date': start_timestamp} for item in filtered_combinations ]
    print(len(combs), 'all coms')
    combs.sort(key=lambda x: x['score'], reverse=True)
    print({"top_5": combs[:5], "low_5":combs[-5:]})
    short = combs[0]['symbol']
    long = combs[-1]['symbol']
    print(short, long)
    
    
    # fetch all stocks
    symbol =f"{long}-{short}"
    split_symbol = symbol.split('-')
    stocks = Stock.objects.filter(Q(symbol=split_symbol[0]) | 
                         Q(symbol=split_symbol[1]) | 
                         Q(symbol=split_symbol[2]) | 
                         Q(symbol=split_symbol[3]) | 
                         Q(symbol=split_symbol[4]) | 
                         Q(symbol=split_symbol[5]) ).filter(date_time__gte=start_timestamp).all()

    print(len(stocks), len(stocks)/31)
    
    initial_timestamp = start_timestamp #datetime(2024, 4,  24, 00)
    current_timestamp = datetime(2024, 4,  26, 16)  #datetime(2024, 4,  25, 16)
    
    initial_strike_price = sum([ item.close for item in stocks if item.date_time == start_timestamp])
    info['open_price'] = initial_strike_price
    # Ensure initial_timestamp is before current_timestamp
    if initial_timestamp > current_timestamp:
        initial_timestamp, current_timestamp = current_timestamp, initial_timestamp
        
    while initial_timestamp < current_timestamp :
        if initial_timestamp.time() >= time(9, 30) and initial_timestamp.time() <= time(15, 59): 
            distinct_timestamps = tmp_distinct_timestamps
            distinct_timestamps.append(timestamp)
            new_distinct_timestamps = sorted(start_timestamp)
            previous, current, final = new_distinct_timestamps.index(timestamp) - 1,  new_distinct_timestamps.index(timestamp), new_distinct_timestamps.index(timestamp) + 1 
            current_time = new_distinct_timestamps[final]
            current_strike_price = sum([ item.close for item in stocks if item.date_time == current_time])
            
            print('current_strike_price', current_strike_price)
            info['current_price'] = current_strike_price
            info['current_percent'] = (current_strike_price - initial_strike_price) / initial_strike_price * 100
            
            if info['current_percent'] > info['max_percent']:
                info['max_percent'] = info['current_percent']
                info['max_percent_time'] = str(current_time)
                info['max_close_price'] = info['current_price']
                info['close_time'] = str(current_time)
                
                
            if info['current_percent'] < info['min_percent']:
                info['min_percent'] = info['current_percent']
                info['min_percent_time'] = str(current_time)
                
            
        initial_timestamp += timedelta(minutes=1)

    print(info)