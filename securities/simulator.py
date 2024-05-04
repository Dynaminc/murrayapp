from datetime import datetime, timedelta, time
from .models import Stock, Combination
import pandas as pd
from django.db.models import OuterRef, Subquery, Q  # Import necessary modules

def simulate_compute():
    start_timestamp = datetime(2024, 4, 25)
    end_timestamp = datetime.now()

    # Generate the range of minutes
    minutes_range = pd.date_range(start=start_timestamp, end=end_timestamp, freq='T')

    # Convert the DatetimeIndex to an array
    minutes_array = minutes_range.to_numpy()

    # Convert the array elements to datetime objects
    timestamps = pd.to_datetime(minutes_array)

    # Initialize a dictionary to store the data
    
    data = []
    # Process each timestamp
    
    for timestamp in timestamps:
        if timestamp.time() >= time(9, 30) and timestamp.time() <= time(15, 59): 
            print(timestamp)
            val = run_simulation(str(timestamp))
            if val:
                data.append(val)
        
    
    # Convert data to DataFrame
    df = pd.DataFrame(data)

    # Set open_time as index
    df.set_index('open_time', inplace=True)

    # Export DataFrame to Excel
    filename = f'simulation_percentages_{start_timestamp}_{end_timestamp}.xlsx'
    df.to_excel(filename)

    print(f'Exported data to {filename}')    
    
    
def export_min_max():
    timestamp = datetime(2024, 4, 24, 11)

    # Optimized filtering using Subquery and OuterRef
    tmp_distinct_timestamps = Stock.objects.filter(
        date_time__gte=timestamp
    ).values(
        "date_time",
        min_score=Subquery(Combination.objects.filter(date_time=Q(**{"date_time": "date_time"})).values("avg").order_by("avg").first()),  # Use Q object
        max_score=Subquery(Combination.objects.filter(date_time=Q(**{"date_time": "date_time"})).values("avg").order_by("-avg").first()),  # Use Q object
    ).distinct().order_by("date_time")

    data = []
    for timepoint in tmp_distinct_timestamps:
        short = timepoint["min_score"]  # Use pre-computed min score directly
        long = timepoint["max_score"]  # Use pre-computed max score directly
        info = {
            "timestamp": timepoint["date_time"],
            "short": short,
            "max": short,  # Consistent naming (max score refers to short's score)
            "long": long,
            "min": long,  # Consistent naming (min score refers to long's score)
        }
        data.append(info)

    # print(data)
    # timestamp = datetime(2024, 4, 24, 11)
    # start_timestamp = datetime.strptime(str(timestamp), "%Y-%m-%d %H:%M:%S")
    # tmp_distinct_timestamps = [item['date_time'] for item in Stock.objects.filter(date_time__gte=timestamp).values("date_time").order_by("date_time").distinct()]
    # data = []
    # for timepoint in sorted(tmp_distinct_timestamps):
    #     print(timepoint)
    #     filtered_combinations = Combination.objects.filter(date_time=timepoint)
    #     combs = [{'symbol':item.symbol,'score':item.avg,'date':timepoint} for item in filtered_combinations]
    #     combs.sort(key=lambda x: x['score'], reverse=True)
    #     try:
    #         short = combs[0]['symbol']
    #         long = combs[-1]['symbol']
    #         info = {'timestamp':timepoint, 'short':short, 'max':combs[0]['score'],  'long': long, 'min': combs[-1]['score'] }        
    #         data.append(info)
    #     except Exception as E:
    #         print(E)
        
    df = pd.DataFrame(data)
    # Set open_time as index
    df.set_index('timestamp', inplace=True)
    # Export DataFrame to Excel
    filename = f'min_max_{datetime.now()}.xlsx'
    df.to_excel(filename)
    print(f'Exported data to {filename}')    
    
def run_simulation(timestamp):
    
    # fetches the max and min of that time stamp
    try:
    
        start_timestamp = datetime.strptime(str(timestamp), "%Y-%m-%d %H:%M:%S")
        tmp_distinct_timestamps = [item['date_time'] for item in Stock.objects.values("date_time").order_by("date_time").distinct()]
        
        filtered_combinations = Combination.objects.filter(date_time = start_timestamp).exclude(symbol = "DJI")
        combs = [{'symbol':item.symbol,'stdev':item.stdev,'score':item.avg,'date': start_timestamp} for item in filtered_combinations ]
        combs.sort(key=lambda x: x['score'], reverse=True)
        # print({"top_5": combs[:5], "low_5":combs[-5:]})
        short = combs[0]['symbol']
        long = combs[-1]['symbol']
        info = {'short':short,'long': long, 'open_price':0, 'open_time':timestamp, 'max_close_price': 0,'min_close_price':0, 'max_percent': 0, 'min_percent':0, 'current_percent': 0, 'current_price': 0, 'min_percent_time': None, 'max_percent_time':None, 'close_time': None}
        
        # fetch all stocks
        symbol =f"{long}-{short}"
        split_symbol = symbol.split('-')
        stocks = Stock.objects.filter(Q(symbol=split_symbol[0]) | 
                            Q(symbol=split_symbol[1]) | 
                            Q(symbol=split_symbol[2]) | 
                            Q(symbol=split_symbol[3]) | 
                            Q(symbol=split_symbol[4]) | 
                            Q(symbol=split_symbol[5]) ).filter(date_time__gte=start_timestamp).all()

        # print(len(stocks), len(stocks)/31)
        
        initial_timestamp = start_timestamp #datetime(2024, 4,  24, 00)
        current_timestamp = datetime.now()  #datetime(2024, 4,  25, 16)
        
        # print([ item.close for item in stocks if item.date_time == start_timestamp])
        
        initial_strike_price = sum([ item.close for item in stocks if item.date_time == start_timestamp])
        info['open_price'] = initial_strike_price
        # Ensure initial_timestamp is before current_timestamp
        if initial_timestamp > current_timestamp:
            initial_timestamp, current_timestamp = current_timestamp, initial_timestamp
            
        while initial_timestamp < current_timestamp :
            if initial_timestamp.time() >= time(9, 30) and initial_timestamp.time() <= time(15, 59): 
                distinct_timestamps = tmp_distinct_timestamps
                distinct_timestamps.append(initial_timestamp)
                new_distinct_timestamps = sorted(distinct_timestamps)
                
                final =  new_distinct_timestamps.index(initial_timestamp) + 1 
                
                current_time = new_distinct_timestamps[final]
                
                current_strike_price = sum([ item.close for item in stocks if item.date_time == current_time])
                
                info['current_price'] = current_strike_price
                info['current_percent'] = (current_strike_price - initial_strike_price) / initial_strike_price * 100
                
                if info['current_percent'] > info['max_percent']:
                    info['max_percent'] = info['current_percent']
                    info['max_percent_time'] = str(current_time)
                    info['max_close_price'] = info['current_price']
                    
                    # print('current_strike_price', current_strike_price)    
                    
                if info['current_percent'] < info['min_percent']:
                    info['min_percent'] = info['current_percent']
                    info['min_percent_time'] = str(current_time)
                    info['min_close_price'] = info['current_price']
                    
                
            initial_timestamp += timedelta(minutes=1)
        info['close_time'] = str(initial_timestamp)
        return info
    except:
        print('Error', timestamp)
        return False