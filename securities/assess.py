from django.conf import settings    
import pandas as pd
from .models import Stock, Company, Combination, Cronny
import requests, json
from datetime import datetime
from itertools import combinations
from django.db.models import Q
from .utils import quick_run
from scipy.stats import zscore,  describe
import pprint


# fetched all the needed data and saved it in a json
def get_test_data():
    """Gets third-party API data"""
    twelve_key = settings.TWELVE_DATA_API_KEY
    SYMBOLS = (
        "AXP:NYSE",
        "AMGN",
        "AAPL:NASDAQ",
        "BA:NYSE",
        "CAT:NYSE",
        "CSCO:NASDAQ",
        "CVX:NYSE",
        "GS:NYSE",
        "HD:NYSE",
        "HON",
        "IBM:NYSE",
        "INTC:NASDAQ",
        "JNJ:NYSE",
        "KO:NYSE",
        "JPM:NYSE",
        "MCD:NYSE",
        "MMM:NYSE",
        "MRK:NYSE",
        "MSFT:NASDAQ",
        "NKE:NYSE",
        "PG:NYSE",
        "TRV:NYSE",
        "UNH:NYSE",
        "CRM:NYSE",
        "VZ:NYSE",
        "V:NYSE",
        "AMZN:NASDAQ",
        "WMT:NYSE",
        "DIS:NYSE",
        "DOW:NYSE",
    )

    # all_symbols = "AXP:NYSE"
    all_symbols = ",".join(SYMBOLS)
    try:
        
        start_date = "2024-04-18"
        end_date = "2024-04-20"

        url = f"https://api.twelvedata.com/time_series?apikey={twelve_key}&symbol={all_symbols}&dp=4&previous_close=true&interval=1min&start_date={start_date}&end_date={end_date}"
        res = requests.get(url)

        if res.status_code == 200:
            data = res.json()
            with open('tmp.json','w') as json_file:
                json.dump(data, json_file)            
        return {"status_code": res.status_code, "stocks": res.json()}
    
    except Exception as e:
        print(
            "Exception for fetching API data after crone execution. Message:",
            e,
        )
        
        return "Failed"

# to get the json from the file and migrate into the database. for local and prod 
def json_migrator():
    stocks_list = []
    intital_time = datetime.now()
    with open('tmp.json', 'r') as json_file:
        data = json.load(json_file)
        for pre_stock_name, data in data.items(): #VZ, WMT, WBA, bulk_create the needed stock object
            if 'values' not in data.keys():
                print(pre_stock_name)
                return 'Failed'
            stock_name = pre_stock_name.split(':')[0]
            for stock in data['values']:
                # if not Stock.objects.filter(symbol=stock_name, date_time=stock["datetime"]).first():
                stock_dict = {
                    "symbol": stock_name,
                    "close": float(stock["close"]),
                    "low": stock["low"],
                    "high": stock["high"],
                    "previous_close": float(stock["previous_close"]),
                    "date_time": stock["datetime"],
                }
                stock_obj = Stock(open=stock["open"], **stock_dict)

                stocks_list.append(stock_obj)
    timestamp = datetime(2024, 4, 19, 12)
    filtered_stock_data = [stock_data for stock_data in stocks_list if datetime.strptime(stock_data.date_time, "%Y-%m-%d %H:%M:%S")  >= timestamp]
    print(len(filtered_stock_data), 'filtered')
    if filtered_stock_data:
        Stock.objects.bulk_create(filtered_stock_data)
    
    timestamp = datetime(2024, 4, 19, 12)
    stocks = Stock.objects.filter(date_time__gte=timestamp).all() # Q(symbol=comba[0]) |Q(symbol=comba[1]) |Q(symbol=comba[2]) , 
    distinct_stocks = Stock.objects.filter(date_time__gte=timestamp).values_list('symbol', flat=True).distinct()
    distinct_timestamps = Stock.objects.filter(date_time__gte=timestamp).values_list('date_time', flat=True).distinct()
    distinct_timestamps_list = list(distinct_timestamps)
    errors = []
    for stock in distinct_stocks:
        previous_stock = None
        data = [stock_data for stock_data in stocks if stock_data.symbol == stock and stock_data.date_time == distinct_timestamps_list[0]]
        if len(data) > 0:
            previous_stock = data[0]
        
        
        for timestamp in distinct_timestamps_list:
            try:
                stock_instance = [stock_data for stock_data in stocks if stock_data.symbol == stock and stock_data.date_time == timestamp][0]
                previous_stock = stock_instance
            except:
                print('Not found', stock, timestamp)
                errors.append(f"{stock}: {timestamp}")
                if not previous_stock:
                    print('still Not found', stock, timestamp)
                    data = [stock_data for stock_data in stocks if stock_data.symbol == stock and stock_data.date_time == distinct_timestamps_list[distinct_timestamps_list.index(timestamp) - 1]]
                    if len(data) > 0:
                        previous_stock = data[0]
                data = Stock.objects.create(symbol=stock,open=previous_stock.open,close=previous_stock.close,low=previous_stock.low,high=previous_stock.high,previous_close=previous_stock.previous_close,date_time = timestamp)
                stock_instance.save()
                
    final_time = datetime.now() - intital_time            
    print(f"Time difference: {final_time.total_seconds()} seconds", len(stocks_list))
    
    error_data = '\n'.join(sorted(list(set(errors))))
    f = open('missing_data.txt', 'w')
    f.write(error_data)
    f.close()
    print('migration complete')
    
    
# to calculate the strikes for the data from 18 april    
def all_strikes():
    timestamp = datetime(2024, 4, 19, 12)
    combs = combinations(Company.SYMBOLS, 3)
    count = 0
    stocks = Stock.objects.filter(date_time__gte=timestamp).all() # Q(symbol=comba[0]) |Q(symbol=comba[1]) |Q(symbol=comba[2]) , 
    distinct_timestamps = Stock.objects.filter(date_time__gte=timestamp).values_list('date_time', flat=True).distinct()
    distinct_timestamps_list = list(distinct_timestamps)
    
    print('datapoints', len(distinct_timestamps_list))
    
    
    # combs = ['AXP-AAPL-BA']
    for comb in combs:
        combinations_list = []
        count += 1
        strike = f"{comb[0]}-{comb[1]}-{comb[2]}"
        # strike = 'AXP-AAPL-BA'
        print(strike)
        comba = strike.split('-')
        # print(len(stocks))
        for timestamp in distinct_timestamps_list: # gotten all the distinct timestamp, about to compute strikes and stdevs, using predata too

            try:
                stock_1 = [stock for stock in stocks if stock.symbol == comba[0] and stock.date_time == timestamp][0].close
            except Exception as E:
                print('error persists')
            try:                
                stock_2 = [stock for stock in stocks if stock.symbol == comba[1] and stock.date_time == timestamp][0].close
            except Exception as E:
                print('error persists')
            try:
                stock_3 = [stock for stock in stocks if stock.symbol == comba[2] and stock.date_time == timestamp][0].close
            except Exception as E:
                print('error persists')
            
            combinations_list.append(
                        {
                            "symbol": strike,
                            "strike":round((float(stock_1) + float(stock_2) + float(stock_3)) / 3, 4),
                            "date_time": timestamp,
                            "z_score" : 0,
                        }
                    )    
        combinations_df = pd.DataFrame(combinations_list)
        # print(len(combinations_list))
        
        
        calculated_combs = []
        
        for timestamp in distinct_timestamps_list:
            calculated_combs.append(calc_stats_b(combinations_df, timestamp))
            
        strikes_list = []

        strikes_list = [
            Combination(
                symbol=comb['symbol'],
                avg=comb['avg'],
                stdev=comb['stdev'],
                strike=comb['strike'],
                date_time=comb['date_time'],
                z_score=comb['z_score'],
            ) for comb in calculated_combs ]


        print('done with combination ', count, len(strikes_list))
        
        print('bulk creating')
        Combination.objects.bulk_create(strikes_list)
        print('bulk created')
        
    return "Cmmbinatoins computed"

def top_low():
    latest_time = Combination.objects.latest('date_time').date_time
    
    filtered_combinations = Combination.objects.filter(date_time = latest_time )
    print(len(filtered_combinations))
    combs = [{'symbol':item.symbol,'stdev':item.stdev,'score':item.z_score,'date':str(item.date_time)} for item in filtered_combinations ]
    combs.sort(key=lambda x: x['score'], reverse=True)
    
    # Create a DataFrame from the combs list
    df = pd.DataFrame(combs)
    
    # Export the DataFrame to an Excel file
    df.to_excel('new_combs_3.xlsx', index=False)
    
    return len(combs)
    
def clean_comb(): # rmove the precalculated combs for a new calculation
    
    times = [datetime(2024, 4, 22)]
    # strike = "VZ-WBA-WMT"
    for item in times:
        print('fetcging ')
        data = Combination.objects.filter(date_time__gte=item).all()
        print(len(data))
        # data = Combination.objects.filter(date_time__date=item.date()).all()
        data.delete()
        print('cleaned combinations')
        
        data = Stock.objects.filter(date_time__gte=item).all()
        print(len(data))
        data.delete()
        
        print('cleaned stocks')
    return 'cleaned'

def export_file():
    times = [datetime(2024, 4, 19, 13)]
    
    # strike = "AXP-AMGN-AAPL"
    for strike in ["HON-JNJ-MMM", "INTC-NKE-VZ"]:
        for item in times:
            quick_run(strike, item)
    return 'exported'
def calc_stats_b(df, timestamp):
    
    df['date_time'] = pd.to_datetime(df['date_time'])
    groups = df.groupby('symbol')
    sym = None
    try:
        for symbol, group_df in groups:
            sym = symbol
            group_df_sorted = group_df.sort_values('date_time')
            specific_time = pd.Timestamp(timestamp)
            index_of_specific_time = group_df_sorted[group_df_sorted['date_time'] == specific_time].index[0]
            start_index = max(0, index_of_specific_time - 199)
            end_index = index_of_specific_time + 1
            result_df = group_df_sorted.iloc[start_index:end_index]
            most_recent_strike = result_df.iloc[-1]['strike']
            z_scores_series = pd.Series(zscore(result_df['strike']))
            avg = result_df['strike'].mean()
            stdev = result_df['strike'].std() 
            z_score = z_scores_series.iloc[-1]
            
            return  {"symbol": symbol, "strike": most_recent_strike, "avg": avg, "date_time": timestamp,"stdev": stdev, "z_score": z_score}
        
    except Exception as E:
        
        print('error at symbol', sym, timestamp, E)
        return False
