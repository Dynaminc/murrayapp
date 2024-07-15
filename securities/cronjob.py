import requests
import pandas as pd
import os
import numpy as np
import json, random
from datetime import datetime, timedelta, time
from itertools import combinations
from django.core.paginator import Paginator
from django.conf import settings
from django.db.models import Max
from django.db.models import Q
from django.db import IntegrityError
from django.utils import timezone as tz
from django.core.cache import cache
from .models import Stock, Company, Combination, Cronny, MiniCombination
from scipy.stats import zscore
from django.db.models import F
from .serializer import *
from pprint import pprint
from django_redis import get_redis_connection
con = get_redis_connection("default")
print(cache.get("last_datetime"))
from accounts.models import Strike, Profile
from .views import update_strike
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import OrderBy
from django.db.models import Max, Subquery, OuterRef
 
info = {}
info['main_count'] = 0
## Contains the most recent build for data retrieval, processing and storage, skips redis for now
def cronny():
    for item in Strike.objects.filter(closed=False):
        update_strike(item.id)
    

def get_data(timestamp):
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
        "DOW:NYSE",
        "WMT",
        "DIS:NYSE",
        "DJI"
    )
    
    # all_symbols = "AXP:NYSE"
    all_symbols = ",".join(SYMBOLS)
    try:
        
        # start_date = "2024-04-22"
        # end_date = "2024-04-23"

        # Assuming you want to retrieve data for the minute 10:15 AM on 2024-04-22
        specific_minute = datetime.strptime(str(timestamp), "%Y-%m-%d %H:%M:%S")

        # Construct the URL with the specific minute
        url = f"https://api.twelvedata.com/time_series?apikey={twelve_key}&symbol={all_symbols}&dp=4&previous_close=true&interval=1min&start_date={specific_minute.strftime('%Y-%m-%d %H:%M:%S')}&end_date={specific_minute.strftime('%Y-%m-%d %H:%M:%S')}"
        res = requests.get(url)         
        
        return {"status_code": res.status_code, "stocks": res.json()}
    
    
    except Exception as e:
        print(
            "Exception for fetching API data after crone execution. Message:",
            e,
        )
        
        return "Failed"
    
def get_minute_data():
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
        "DJI"
    )
    all_symbols = ",".join(SYMBOLS)
    try:
        twelve_key = settings.TWELVE_DATA_API_KEY
        res = requests.get(
            f"https://api.twelvedata.com/time_series?apikey={twelve_key}&interval=1min&symbol={all_symbols}&previous_close=true&dp=4&outputsize=1" 
        )
    except Exception as e:
        print(
            "Exception for fetching API data after crone execution. Message:",
            e,
        )

    return {"status_code": res.status_code, "stocks": res.json()}




def create_stocks(stocks, timestamp):
    stocks_list = []    
    json_stocks_list = []    
    dow_stocks = []
    companies = Company.objects.exclude(symbol=Company.DOW_JONES)
    
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
        "DOW:NYSE",
        "WMT",
        "DIS:NYSE",
        "DJI",
    )
    errors = []
    
    current_time = []
    for item in SYMBOLS:
        company = item.split(':')[0]
        try:
            stock_data  = [stock_item[1] for stock_item in stocks.items() if stock_item[0].split(':')[0] == company][0]
            stock = stock_data["values"][0]
            stock_dict = {
            "symbol": company,
            "close": float(stock["close"]),
            "low": stock["low"],
            "high": stock["high"],
            "previous_close": float(stock["previous_close"]),
            "date_time": stock["datetime"],
            }
            stock_dict_json = {
                "open": stock['open'],
                "symbol": company,
                "close": float(stock["close"]),
                "low": stock["low"],
                "high": stock["high"],
                "previous_close": float(stock["previous_close"]),
                "date_time": stock["datetime"],
            }
            current_datetime = datetime.strptime(stock["datetime"], "%Y-%m-%d %H:%M:%S")
            current_time.append(current_datetime)
            stock_obj = Stock(open=stock["open"], **stock_dict)
            stocks_list.append(stock_obj)
            json_stocks_list.append(stock_dict_json)
        except Exception as E:
            try:
                errors.append(f"{company}: {timestamp}")
                print('found missing data')
                Missing.objects.create(data=f"{company}: {timestamp}")
                latest_stock = Stock.objects.filter(symbol=company).latest('date_time')
                latest_datetime = latest_stock.date_time 
                current_datetime = timestamp
                current_time.append(current_datetime)
                f = open('missing_data.txt', 'a')
                f.write(f'\n {company} : {current_datetime.strftime("%Y-%m-%d %H:%M:%S")}')
                f.close()
            
                new_stock_dict = {
                    "symbol": company,
                    "close": float(latest_stock.close),
                    "low": latest_stock.low,
                    "high": latest_stock.high,
                    "previous_close": float(latest_stock.previous_close),
                    "date_time": current_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                }
                
                stock_dict_json = {
                    "open": latest_stock.open,
                    "symbol": company,
                    "close": float(latest_stock.close),
                    "low": latest_stock.low,
                    "high": latest_stock.high,
                    "previous_close": float(latest_stock.previous_close),
                    "date_time": current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                }
                stock_obj = Stock(open=float(latest_stock.open), **new_stock_dict)
                stocks_list.append(stock_obj)
                json_stocks_list.append(stock_dict_json)

            except Exception as E:
                print('Print Errr', E)
        stock_to_redis(json_stocks_list)                        
    
    print(len(stocks_list))
    
    try:
        Stock.objects.bulk_create(stocks_list, ignore_conflicts=True)
    except IntegrityError:
        pass
    
    error_data = '\n'.join(sorted(list(set(errors))))
    f = open('missing_data.txt', 'w')
    f.write(error_data)
    f.close()
    print('migration complete')    
    val = max(sorted(list(set(current_time))))
    print(val)
    return val

def stock_to_redis(json_stocks_list):
    existing_data = json.loads(con.get("stock_data") or "[]")
    # combined_data = existing_data + json_stocks_list
    combined_data = json_stocks_list
    unique_data = {f"{d['symbol']}_{d['date_time']}": d for d in combined_data}.values()
    serialized_data = json.dumps(list(unique_data))
    con.set("stock_data", serialized_data)
            
def generate_combinations(current_datetime):
    timestamp = current_datetime
    combs = combinations(Company.SYMBOLS, 3)
    combinations_list = []
    
    stocks = json.loads(con.get("stock_data") or "[]")
    if not stocks:
        
        stock_to_redis([StockSerializer(item).data for item in Stock.objects.filter(date_time__gte=timestamp).all()])
        stocks = json.loads(con.get("stock_data") or "[]")
        
    for comb in combs:
        
        strike = f"{comb[0]}-{comb[1]}-{comb[2]}"
        stock_1 = [stock for stock in stocks if stock['symbol'] == comb[0] and stock['date_time'] == str(timestamp)][0]['close']
        stock_2 = [stock for stock in stocks if stock['symbol'] == comb[1] and stock['date_time'] == str(timestamp)][0]['close']
        stock_3 = [stock for stock in stocks if stock['symbol'] == comb[2] and stock['date_time'] == str(timestamp)][0]['close']
        combinations_list.append(
                                {
                                    "symbol": strike,
                                    "strike":round((float(stock_1) + float(stock_2) + float(stock_3)) / 3, 4),
                                    "date_time": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                                    "z_score" : 0,
                                }
                            )    
    return combinations_list


    
                
def calc_stats_b(df, timestamp):
 
    df['date_time'] = pd.to_datetime(df['date_time'])
    groups = df.groupby('symbol')
    symbols = list(set(groups.groups.keys()))
    sym = None
    data = []
    try:
        for symbol in symbols:
            group_df = groups.get_group(symbol)
            sym = symbol
            
            most_recent_time = group_df['date_time'].max()
            most_recent_200 = group_df.nlargest(200, 'date_time')['strike']
            most_recent_strike = group_df.loc[group_df['date_time'].idxmax(), 'strike']
            z_score = zscore(most_recent_200.tolist() + [most_recent_strike])[len(most_recent_200)]
            
            # most_recent_strike_B = group_df.nlargest(1, 'date_time')['strike'].iloc[0]
            # zscore_values = zscore(most_recent_200)
            # group_df['strike_zscore'] = zscore_values
            # avg = most_recent_200.mean()
            stdev = most_recent_200.std()
            # z_scoreb = (most_recent_strike_B - avg) / stdev
            # print(most_recent_time , "symbol", symbol, "z-score scipy: ", z_score, "z-score pandas", z_scoreb )
            
            data.append({"symbol": symbol, "strike": most_recent_strike, "avg": 0, "date_time": most_recent_time, "stdev": stdev, "z_score": z_score})
            
        return data        
    except Exception as E:
        print('error at symbol', sym, timestamp, E)
        return False   
    
def begin_calcs():
    timestamp_bytes = con.get("comb_time")
    if timestamp_bytes is not None:
        last_time = timestamp_bytes.decode("utf-8")
        try:
            last_time = datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")
            if last_time.date() != datetime.now().date():
                clean_redis()
                process_calcs()
        except Exception as E:
            print('hjsdfasd')
            process_calcs()
    else:
        print('hjsdsdaf')
        process_calcs()
        
def process_calcs():
    
    start_time = datetime.now()
    distinct_timestamps = Combination.objects.values("date_time").order_by("-date_time").distinct()[:200]
    print(len(distinct_timestamps))
    end_timestamp = distinct_timestamps[0]["date_time"]
    start_timestamp = end_timestamp - timedelta(days=1) 
    combinations_data = Combination.objects.filter(
        date_time__range=(start_timestamp, end_timestamp)
    ).values("symbol", "strike", "date_time", "z_score")

    unique_combinations = set()
    unique_combinations_data = []
    
    for combination in combinations_data:
        date_time_str = combination['date_time'].strftime("%Y-%m-%d %H:%M:%S")
        identifier = f"{combination['symbol']}_{date_time_str}"
        if identifier not in unique_combinations and not ('WBA' in combination['symbol'] or 'DJI' in combination['symbol']):
            unique_combinations.add(identifier)
            combination['date_time'] = combination['date_time'].strftime("%Y-%m-%d %H:%M:%S")
            unique_combinations_data.append(combination)

    serialized_data = json.dumps(list(unique_combinations_data), cls=DjangoJSONEncoder)
    # existing_data = json.loads(con.get("combinations_data") or "[]")
    # existing_data_dict = {f"{d['symbol']}_{d['date_time']}": d for d in existing_data}
    combined_data_dict = {f"{d['symbol']}_{d['date_time']}": d for d in json.loads(serialized_data)}
    # existing_data_dict.update(combined_data_dict)
    updated_data = json.dumps(list(combined_data_dict.values()))
    con.set("combinations_data", updated_data)

    con.set("comb_time", str(distinct_timestamps[0]["date_time"]))
    end_time = datetime.now()
    time_difference = end_time - start_time
    print(f"data created in {time_difference.total_seconds()} seconds" 'Saved')
    

def new_calc():
    start_time = datetime.now()
    error_count = 0
    print('Gettng minute data')
    res = get_minute_data()

    print('Gotten minute data')
    stocks = res["stocks"]
    print('GCrateing stocks')
    stock_time = create_stocks(stocks, start_time)
    print(stock_time)
    
    combinations_list = generate_combinations(stock_time) 
    print(len(combinations_list))
    
    if info['main_count'] == 10:
        clean_redis()
        process_calcs()
        info['main_count'] = 0
        print('Cleaned data for more redis speed')   
    else:
        print('beginngng caslcs')
        begin_calcs()
    combs = json.loads(con.get("combinations_data"))
        
        
    combinations_df = pd.DataFrame(
        data=list(combs) + combinations_list
    )
    combinations_df["date_time"] = pd.to_datetime(
        combinations_df["date_time"],  format='mixed'
    )

    calculated_combs = []
    calculated_combs = calc_stats_b(combinations_df, stock_time)
    strikes_list = [
        Combination(
            symbol=comb['symbol'],
            avg=comb['avg'],
            stdev=comb['stdev'],
            strike=comb['strike'],
            date_time=comb['date_time'],
            z_score=comb['z_score'],
        ) for comb in calculated_combs ]
    print(len(strikes_list))
    # try:
    #     Combination.objects.bulk_create(strikes_list, ignore_conflicts=True)
        
    # except IntegrityError:
    #     error_count += 1
    #     pass
    existing_data = json.loads(con.get("combinations_data") or "[]")
    existing_data_dict = {f"{d['symbol']}_{d['date_time']}": d for d in existing_data}
    combined_data_dict = {f"{d['symbol']}_{d['date_time']}": d for d in json.loads(json.dumps(calculated_combs, cls=DjangoJSONEncoder))}
    existing_data_dict.update(combined_data_dict)
    updated_data = json.dumps(list(existing_data_dict.values()))
    con.set("combinations_data", updated_data)
    end_time = datetime.now()
    time_difference = end_time - start_time
    print(stock_time, f" created in {time_difference.total_seconds()} seconds", 'Saved')
    Cronny.objects.create(symbol=f"{stock_time}")    
    info['main_count'] = info['main_count'] + 1
    return f"{stock_time} created in {time_difference.total_seconds()} seconds"
            
            
            
            
def new_calc_migratorb():
    combs = []
    market_state = "off"
    ad = Combination.objects.latest('date_time')
    latest_time = ad.date_time
    filtered_combinations = Combination.objects.filter(date_time = latest_time )
    print(len(filtered_combinations))
    combs = [{'symbol':item.symbol,'stdev':item.stdev,'score':item.z_score,'date':str(latest_time)} for item in filtered_combinations if item.z_score]
    combs.sort(key=lambda x: x['score'], reverse=True)
    print({"top_5": combs[:5], "low_5":combs[-5:], "market": market_state})
                
def new_calc_migrator():
    error_count = 0
    print('Cleaning')
    # clean_comb()
    print('Initiating Calcs')
    # begin_calcs() 
    process_calcs()
    
    my_time = str(datetime.now())
    con.set("initiated", my_time)
    print('Initiated')   
    
    # initial_timestamp = datetime(2024, 4,  25, 9)
    initial_timestamp = datetime.strptime(str(Cronny.objects.latest('date_time').symbol), "%Y-%m-%d %H:%M:%S")
    # datetime(2024, 4,  23, 10, 2)
    current_timestamp = datetime(2024, 4,  25, 16)
    
    # Ensure initial_timestamp is before current_timestamp
    if initial_timestamp > current_timestamp:
        initial_timestamp, current_timestamp = current_timestamp, initial_timestamp
    while initial_timestamp < current_timestamp:
        
        if initial_timestamp.time() >= time(9, 30) and initial_timestamp.time() <= time(15, 59):
            if con.get('initiated').decode("utf-8") != my_time:
                print(con.get('initiated').decode("utf-8"), my_time, 'unequal')
                
                break
            info['main_count'] = info['main_count'] + 1
            if info['main_count'] == 10:
                clean_redis()
                process_calcs()
                info['main_count'] = 0
                print('Cleaned data for more redis speed')   
            timestamp = initial_timestamp
            start_time = datetime.now()
            res = get_data(timestamp)
            
            stocks = res["stocks"]
            
            stock_time = create_stocks(stocks, timestamp)
            timestamp += timedelta(minutes=1)
            
            combinations_list = generate_combinations(stock_time) 
            # begin_calcs()
            
            combs = json.loads(con.get("combinations_data"))
            if not combs:
                break
            else:
                combinations_df = pd.DataFrame(
                    data=list(combs) + combinations_list
                )
                combinations_df["date_time"] = pd.to_datetime(
                    combinations_df["date_time"],  format='mixed'
                )

                calculated_combs = []
                calculated_combs = calc_stats_b(combinations_df, stock_time)
                strikes_list = [
                    Combination(
                        symbol=comb['symbol'],
                        avg=comb['avg'],
                        stdev=comb['stdev'],
                        strike=comb['strike'],
                        date_time=comb['date_time'],
                        z_score=comb['z_score'],
                    ) for comb in calculated_combs ]

                try:
                    Combination.objects.bulk_create(strikes_list, ignore_conflicts=True)
                except IntegrityError:
                    error_count += 1
                    pass
                existing_data = json.loads(con.get("combinations_data") or "[]")
                existing_data_dict = {f"{d['symbol']}_{d['date_time']}": d for d in existing_data}
                combined_data_dict = {f"{d['symbol']}_{d['date_time']}": d for d in json.loads(json.dumps(calculated_combs, cls=DjangoJSONEncoder))}
                existing_data_dict.update(combined_data_dict)
                updated_data = json.dumps(list(existing_data_dict.values()))
                con.set("combinations_data", updated_data)
                
                end_time = datetime.now()
                time_difference = end_time - start_time
                print(timestamp, f"{timestamp} created in {time_difference.total_seconds()} seconds")
                Cronny.objects.create(symbol=f"{timestamp}")    

        initial_timestamp += timedelta(minutes=1)
def clean_redis():
    
    count = 0 
    con.set("combinations_data", "[]")
    con.set("comb_time", "[]")
    con.set("stock_data", "[]")
    
    print('cleaned redis')
    
    
    return 'cleaned'            





def generate_dji_combinations(current_datetime, tmp_distinct_timestamps):
    timestamp = current_datetime
    distinct_timestamps = tmp_distinct_timestamps
    distinct_timestamps.append(timestamp)
    new_distinct_timestamps = sorted(distinct_timestamps)
    previous, current, final = new_distinct_timestamps.index(timestamp) - 1,  new_distinct_timestamps.index(timestamp), new_distinct_timestamps.index(timestamp) + 1 
    try:
        final_time = new_distinct_timestamps[final]
    except:
        final_time = new_distinct_timestamps[current]
    item = Stock.objects.filter(symbol="DJI").filter(date_time=final_time).first()
    stock = StockSerializer(item).data
    
    previous_instance = Combination.objects.filter(symbol="DJI").latest('date_time')
    
    if not previous_instance:
        print('no previous instance')
        previous_instance = Combination.objects.create(
                symbol="DJI",
                avg = 0,
                stdev=0,
                strike=stock['previous_close'],
                date_time=new_distinct_timestamps[previous],
                z_score=0,
            ) 
        
    current_percent = (stock['close'] - stock['previous_close']) / stock['previous_close'] * 100
    cummulative_percent  =  previous_instance.avg + current_percent
    final_time = None
    try:
        final_time = new_distinct_timestamps[final]
    except:
        final_time = new_distinct_timestamps[current]
        
    try:
        Combination.objects.create(
            symbol="DJI",
            avg=cummulative_percent,
            stdev=current_percent,
            strike=stock['close'],
            date_time=final_time,
            z_score=0,
        ) 
    except:
        current_instance = Combination.objects.filter(symbol="DJI").filter(date_time=final_time).first()
        print(cummulative_percent)
        current_instance.avg = cummulative_percent
        current_instance.save()
        pass
    
    
def check_strike_symbol(strike, earning_symbols):
    for item in earning_symbols:
        if item in strike:
            return True
    return False
    

def is_in_trading(stock_time):
    queryset = Nonday.objects.all()
    nonday_of_interest = [nonday for nonday in Nonday.objects.all() if stock_time.date() == nonday.date_time.date()]
    if not nonday_of_interest:
        return True
    
    if nonday_of_interest[0] and nonday_of_interest[0].half_day:
        if stock_time.time() <= time(13, 00):
            return True
        else:
            return False
    
def mig_flow(initial_timestamp):
    
    initial_timestamp = datetime.strptime(str(Cronny.objects.latest('date_time').symbol), "%Y-%m-%d %H:%M:%S") 
    # datetime(2024, 4,  29, 9,39 ) # # datetime(2024, 4,  30, 16) 
    # print(initial_timestamp)
    pre_stocks = Stock.objects.filter(date_time__gte = initial_timestamp).all()

    print(len(pre_stocks))
    print("post clean")
    stocks = [item for item in pre_stocks if is_in_trading(item.date_time)]
    print(len(stocks))

    # stocks = [StockSerializer(item) for item in stock_query]
    # distinct_timestamps = [item['date_time'] for item in stocks.values("date_time").order_by("date_time").distinct()]
    distinct_timestamps = sorted(list(set([item.date_time for item in stocks])))
    new_distinct_timestamps = sorted(distinct_timestamps)
    
    
    # Get distinct symbols
    distinct_symbols = Combination.objects.values('symbol').distinct()

    # Initialize a list to store the most recent combination objects
    recent_objects = []

    # Iterate over distinct symbols
    for symbol in distinct_symbols:
        # Get the most recent combination object for each symbol
        most_recent_combination = Combination.objects.filter(symbol=symbol['symbol']).order_by('-date_time').first()
        print(most_recent_combination.date_time)
        # Add the most recent combination object to the list
        recent_objects.append(most_recent_combination)

    # Print the count of recent_objects
    print(len(recent_objects))
    
    dji_prev = 0
    prev_dict = {}
    for item in recent_objects:
        prev_dict[item.symbol] = item.avg
        if item.symbol == "DJI":
            dji_prev = item.avg
    
    print('dji_prev', dji_prev, len(prev_dict.keys()))
    
    prev_close = {}
    prev_close["DJI"] = dji_prev
    
    last_min = (initial_timestamp - timedelta(minutes = 1)).replace(second=0, microsecond=0)    
    last_stocks = Stock.objects.filter(date_time = last_min).all()
    if len(last_stocks) == 0:
        print('zero stcoks', len(last_stocks))       
        last_min = Stock.objects.filter(date_time__lt=initial_timestamp).latest('date_time').date_time
        last_stocks = Stock.objects.filter(date_time = last_min).all()
        print('last min', last_min)       
        print('final strocks', len(last_stocks))       
    for item in last_stocks:
        prev_close[item.symbol] = item.close
             
    print('strocks', len(last_stocks))   
    
    count = 0
    for timestamp in distinct_timestamps:
        current_date = timestamp.date()
        queryset = Nonday.objects.filter(date_time__date=current_date).first()
        proceed = False
        if queryset:
            if queryset.half_day == True and timestamp.time() <= time(13, 00):
                proceed = True
        else:
            proceed = True
            
        if proceed:        
            if timestamp.time() >= time(9, 30): 
                print(timestamp)
                final_set = [item for item in stocks if item.date_time == distinct_timestamps[count]]
                if count > 0:
                    prev_set = [item for item in stocks if item.date_time == distinct_timestamps[count-1]]        
                    for item in prev_set:
                        prev_close[item.symbol] = item.close
                
                # current_date = timestamp.date()
                # start_datetime = current_date - timedelta(days=1)
                # start_date = datetime.combine(start_datetime, datetime.strptime("15:59", "%H:%M").time())
                # end_date = datetime.combine((current_date + timedelta(days=1)), datetime.strptime("15:59", "%H:%M").time()) 
                # earnings_data = Earning.objects.filter(date_time__date__range=[start_date, end_date])
                # valid_earnings_data = [item.symbol for item in earnings_data if start_date <= item.date_time <= end_date]     
                
                
                earning_dates = {}
                valid_earnings_data = []
                for earnings in Earning.objects.all():
                    start_date = datetime.combine((earnings.date_time.date() - timedelta(days=1)), datetime.strptime("15:59", "%H:%M").time())
                    end_date = datetime.combine((earnings.date_time.date() + timedelta(days=1)), datetime.strptime("15:59", "%H:%M").time())
                    if start_date <= timestamp <= end_date:
                        valid_earnings_data.append(earnings.symbol)
                    
                
                specials = [cmbo for cmbo in list(prev_dict.keys()) if not check_strike_symbol(cmbo, valid_earnings_data)]
                # print('sd', len(list()))
                print(len(prev_dict.keys()), len(specials))
                for itm in specials:
                    comb = itm.split('-')
                    try:
                        strike = f"{comb[0]}-{comb[1]}-{comb[2]}"
                        
                        
                        stock_1 = [stock for stock in final_set if stock.symbol == comb[0] ][0]
                        stock_2 = [stock for stock in final_set if stock.symbol == comb[1] ][0]
                        stock_3 = [stock for stock in final_set if stock.symbol == comb[2] ][0] 
                        
                        
                        # current_percent = ((stock_1.close + stock_2.close + stock_3.close) - (stock_1.previous_close + stock_2.previous_close + stock_3.previous_close) ) / (stock_1.previous_close + stock_2.previous_close + stock_3.previous_close) * 100
                        current_percent = (((stock_1.close - prev_close[comb[0]] ) / prev_close[comb[0]]) + ((stock_2.close - prev_close[comb[1]] ) / prev_close[comb[1]]) + ((stock_3.close - prev_close[comb[2]] ) / prev_close[comb[2]])) * 100
                        # current_percent = (((stock_1.close - stock_1.previous_close ) / stock_1.previous_close) + ((stock_2.close - stock_2.previous_close ) / stock_2.previous_close) + ((stock_3.close - stock_3.previous_close ) / stock_3.previous_close)) * 100
                        cummulative_percent  =  prev_dict[strike] + current_percent
                        prev_dict[strike] = cummulative_percent 
                        try:
                            Combination.objects.create(
                                    symbol=strike,
                                    avg=cummulative_percent,
                                    stdev=current_percent,
                                    strike=(stock_1.close + stock_2.close + stock_3.close)/3,
                                    date_time=timestamp,
                                    z_score=0,
                                ) 
                        except Exception as E:
                            pass
                    except:
                        pass
                dji = [stock for stock in final_set if stock.symbol == "DJI" ][0]
                dji_current_percent = (dji.close - prev_close['DJI']) / prev_close['DJI'] * 100
                dji_cummulative_percent  =  dji_prev + dji_current_percent
                try:
                    Combination.objects.create(
                        symbol="DJI",
                        avg=dji_cummulative_percent,
                        stdev=dji_current_percent,
                        strike=dji.close,
                        date_time=timestamp,
                        z_score=0,
                    ) 
                except: 
                    pass
                Cronny.objects.create(symbol=f"{timestamp}")    
            count += 1
            
            
def all_flow(initial_timestamp):
    
    # stocks = Stock.objects.filter(date_time__gte = initial_timestamp).all()
    
    pre_stocks = Stock.objects.filter(date_time__gte = initial_timestamp).all()

    print(len(pre_stocks))
    print("post clean")
    stocks = [item for item in pre_stocks if is_in_trading(item.date_time)]
    print(len(stocks))

    # stocks = [StockSerializer(item) for item in stock_query]
    # distinct_timestamps = [item['date_time'] for item in stocks.values("date_time").order_by("date_time").distinct()]
    # distinct_timestamps = list(set([item.date_time for item in stocks]))
    distinct_timestamps = sorted(list(set([item.date_time for item in stocks])))
    new_distinct_timestamps = sorted(distinct_timestamps)
    
    prev_dict = {}
    prev_close = {}
    
    dji_prev = 0
    combs = combinations(Company.SYMBOLS, 3)
    for comb in combs:
        strike = f"{comb[0]}-{comb[1]}-{comb[2]}"
        prev_dict[strike] = 0
    
    last_min = (initial_timestamp - timedelta(minutes = 1)).replace(second=0, microsecond=0)    
    last_stocks = Stock.objects.filter(date_time = last_min).all()
    if len(last_stocks) == 0:
        print('zero stcoks', len(last_stocks))       
        last_min = Stock.objects.filter(date_time__lt=initial_timestamp).latest('date_time').date_time
        last_stocks = Stock.objects.filter(date_time = last_min).all()
        print('last min', last_min)       
        print('final strocks', len(last_stocks))       
    for item in last_stocks:
        prev_close[item.symbol] = item.close
             
    print('strocks', len(last_stocks))   
    
    count = 0
    
    for timestamp in distinct_timestamps:
        current_date = timestamp.date()
        queryset = Nonday.objects.filter(date_time__date=current_date).first()
        proceed = False
        if queryset:
            if queryset.half_day == True and timestamp.time() <= time(13, 00):
                proceed = True
        else:
            proceed = True
            
        if proceed:
            if timestamp.time() >= time(9, 30): 
                print(timestamp)
                final_set = [item for item in stocks if item.date_time == distinct_timestamps[count]]
                
                earning_dates = {}
                valid_earnings_data = []
                for earnings in Earning.objects.all():
                    start_date = datetime.combine((earnings.date_time.date() - timedelta(days=1)), datetime.strptime("15:59", "%H:%M").time())
                    end_date = datetime.combine((earnings.date_time.date() + timedelta(days=1)), datetime.strptime("15:59", "%H:%M").time())
                    if start_date <= timestamp <= end_date:
                        valid_earnings_data.append(earnings.symbol)
                
                specials = [cmbo for cmbo in list(prev_dict.keys()) if not check_strike_symbol(cmbo, valid_earnings_data)]
                # print('sd', len(list()))
                print(len(prev_dict.keys()), len(specials))
                for itm in specials:
                    comb = itm.split('-')
                    strike = f"{comb[0]}-{comb[1]}-{comb[2]}"
                    
                    
                    stock_1 = [stock for stock in final_set if stock.symbol == comb[0] ][0]
                    stock_2 = [stock for stock in final_set if stock.symbol == comb[1] ][0]
                    stock_3 = [stock for stock in final_set if stock.symbol == comb[2] ][0] 
                    
                    
                    # current_percent = ((stock_1.close + stock_2.close + stock_3.close) - (stock_1.previous_close + stock_2.previous_close + stock_3.previous_close) ) / (stock_1.previous_close + stock_2.previous_close + stock_3.previous_close) * 100
                    current_percent = (((stock_1.close - prev_close[comb[0]] ) / prev_close[comb[0]]) + ((stock_2.close - prev_close[comb[1]] ) / prev_close[comb[1]]) + ((stock_3.close - prev_close[comb[2]] ) / prev_close[comb[2]])) * 100
                    cummulative_percent  =  prev_dict[strike] + current_percent
                    prev_dict[strike] = cummulative_percent 
                    try:
                        Combination.objects.create(
                                symbol=strike,
                                avg=cummulative_percent,
                                stdev=current_percent,
                                strike=(stock_1.close + stock_2.close + stock_3.close)/3,
                                date_time=timestamp,
                                z_score=0,
                            ) 
                    except Exception as E:
                        print(E)
                        pass
            
                dji = [stock for stock in final_set if stock.symbol == "DJI" ][0]
                dji_current_percent = (dji.close - prev_close['DJI']) / prev_close['DJI'] * 100
                dji_cummulative_percent  =  dji_prev + dji_current_percent
                try:
                    Combination.objects.create(
                        symbol="DJI",
                        avg=dji_cummulative_percent,
                        stdev=dji_current_percent,
                        strike=dji.close,
                        date_time=timestamp,
                        z_score=0,
                    ) 
                except: 
                    pass
                Cronny.objects.create(symbol=f"{timestamp}")    
            final_set = [item for item in stocks if item.date_time == distinct_timestamps[count]]
            
            for item in final_set:
                prev_close[item.symbol] = item.close
                
            count += 1
            
        
def generate_flow_combinations(current_datetime):
    timestamp = current_datetime
    distinct_timestamps = [item['date_time'] for item in Stock.objects.values("date_time").order_by("date_time").distinct() if is_in_trading(item['date_time'])]
    distinct_timestamps.append(timestamp)
    new_distinct_timestamps = sorted(distinct_timestamps)
    previous, current, final = new_distinct_timestamps.index(timestamp) - 1,  new_distinct_timestamps.index(timestamp), new_distinct_timestamps.index(timestamp) + 1 
    # print(new_distinct_timestamps.index(timestamp) - 1,  new_distinct_timestamps.index(timestamp), new_distinct_timestamps.index(timestamp) + 1 )

    final_time = None
    try:
        final_time = new_distinct_timestamps[final]
    except:
        final_time = new_distinct_timestamps[current]
            
    previous_time = new_distinct_timestamps[previous]
    stocks = [ StockSerializer(item).data for item in Stock.objects.filter(date_time = final_time).all()]
    print ('len ', len(stocks))
    
    prev_close = {}
    prev_close["DJI"] = 0
   
    last_stocks = [ StockSerializer(item).data for item in Stock.objects.filter(date_time = previous_time).all()]
    for item in last_stocks:
        prev_close[item['symbol']] = item['close']
    
    # stocks = [ StockSerializer(item).data for item in Stock.objects.filter(
    #                                         date_time__gte=final_time,
    #                                         date_time__lt=(final_time + timedelta(minutes=1))).all()]
    # stocks = [ StockSerializer(item).data for item in Stock.objects.order_by('-date_time')[:31]]
    print('Stocks', len(stocks))
    
    # Get distinct symbols
    distinct_symbols = Combination.objects.values('symbol').distinct()

    # Initialize a list to store the most recent combination objects
    recent_objects = []

    # Iterate over distinct symbols
    for symbol in distinct_symbols:
        # Get the most recent combination object for each symbol
        most_recent_combination = Combination.objects.filter(symbol=symbol['symbol']).order_by('-date_time').first()
        # Add the most recent combination object to the list
        recent_objects.append(most_recent_combination)

    # Print the count of recent_objects
    print(len(recent_objects))
    previous_set = list(recent_objects)
    print(len(previous_set))
    
    
    # current_date = timestamp.date()
    # start_datetime = current_date - timedelta(days=1)
    # start_date = datetime.combine(start_datetime, datetime.strptime("15:59", "%H:%M").time())
    # end_date = datetime.combine((current_date + timedelta(days=1)), datetime.strptime("15:59", "%H:%M").time()) 
    # earnings_data = Earning.objects.filter(date_time__date__range=[start_date, end_date])
    # valid_earnings_data = [item.symbol for item in earnings_data if start_date <= item.date_time <= end_date]

    earning_dates = {}
    valid_earnings_data = []
    for earnings in Earning.objects.all():
        start_date = datetime.combine((earnings.date_time.date() - timedelta(days=1)), datetime.strptime("15:59", "%H:%M").time())
        end_date = datetime.combine((earnings.date_time.date() + timedelta(days=1)), datetime.strptime("15:59", "%H:%M").time())
        if start_date <= timestamp <= end_date:
            valid_earnings_data.append(earnings.symbol)
            
    combs = combinations(Company.SYMBOLS, 3)
    
    pre_filtered_combinations = []
    
    for comb in [cmb for cmb in combs if not check_strike_symbol(f"{cmb[0]}-{cmb[1]}-{cmb[2]}", valid_earnings_data)]:
        
        strike = f"{comb[0]}-{comb[1]}-{comb[2]}"
        
        stock_1 = [stock for stock in stocks if stock['symbol'] == comb[0] ][0]
        stock_2 = [stock for stock in stocks if stock['symbol'] == comb[1] ][0]
        stock_3 = [stock for stock in stocks if stock['symbol'] == comb[2] ][0] 
        
        # current_percent = ((stock_1['close'] + stock_2['close'] + stock_3['close']) - (stock_1['previous_close'] + stock_2['previous_close'] + stock_3['previous_close']) ) / (stock_1['previous_close'] + stock_2['previous_close'] + stock_3['previous_close']) * 100
        current_percent = (((stock_1['close'] - prev_close[comb[0]] ) / prev_close[comb[0]]) + ((stock_2['close'] - prev_close[comb[1]] ) / prev_close[comb[1]]) + ((stock_3['close'] - prev_close[comb[2]] ) / prev_close[comb[2]])) * 100
        cummulative_percent = 0
        previous_instance = None 
        try:
            previous_instance = [item for item in previous_set if item.symbol == strike][0]    
            if previous_instance:
                cummulative_percent  =  previous_instance.avg + current_percent
            else:
                cummulative_percent  =  current_percent
                
            pre_filtered_combinations.append(
                 Combination(
                            symbol=strike,
                            avg=cummulative_percent,
                            stdev=current_percent,
                            strike=(stock_1['close'] + stock_2['close'] + stock_3['close'])/3,
                            date_time=timestamp,
                            z_score=0,
                        )
            )
            Combination.objects.create(
                symbol=strike,
                avg=cummulative_percent,
                stdev=current_percent,
                strike=(stock_1['close'] + stock_2['close'] + stock_3['close'])/3,
                date_time=timestamp,
                z_score=0,
            )  
        except Exception as E:
            pass
    print('now filtering db')
    
    start_time = datetime.now()
    pre_filtered_combinations.sort(key=lambda x: x.avg, reverse=True)
    cmb = pre_filtered_combinations[:20]+pre_filtered_combinations[-20:]
    
    instances = MiniCombination.objects.all()
    instances.delete()
    
    try:
        MiniCombination.objects.bulk_create(cmb, ignore_conflicts=True)
    except IntegrityError:
        pass
    # for item in cmb:
    #     MiniCombination.objects.create(
    #         symbol=item.symbol,
    #         avg=item.avg,
    #         stdev=item.stdev,
    #         strike=item.strike,
    #         z_score=0,
    #         date_time=timestamp,
    #     )     
      
    end_time = datetime.now()
    time_difference = end_time - start_time
    print(f"data created in {time_difference.total_seconds()} seconds" 'Saved')    
    
def clean_avgs(current_datetime):
    print('updating')
    Combination.objects.filter(date_time__gte=current_datetime).update(avg=0)
    print('updated')





def dji_migrator():
    
    error_count = 0
    my_time = str(datetime.now())
    con.set("initiated", my_time)
    print('Initiated')   
    
    tmp_distinct_timestamps = [item['date_time'] for item in Stock.objects.filter(symbol="DJI").values("date_time").order_by("date_time").distinct()]
    count = 0 
    initial_timestamp = datetime(2024, 4,  25, 15, 59)
    # datetime(2024, 4,  23, 10, 2)
    current_timestamp = datetime(2024, 4,  26, 16)  #datetime(2024, 4,  25, 16)
    
    # Ensure initial_timestamp is before current_timestamp
    if initial_timestamp > current_timestamp:
        initial_timestamp, current_timestamp = current_timestamp, initial_timestamp
    while initial_timestamp < current_timestamp:
        
        if initial_timestamp.time() >= time(9, 30) and initial_timestamp.time() <= time(15, 59): 
            timestamp = initial_timestamp
            generate_dji_combinations(timestamp, tmp_distinct_timestamps)
            Cronny.objects.create(symbol=f"{timestamp}")    
            print(timestamp)
            
        initial_timestamp += timedelta(minutes=1)
        
def clean_comb(initial):
    # clean_redis()
    # return 'cleaned'

    count = 0 
    times = [initial]
    for item in times:
        print('Running clean module ')
        
        # end_datetime = datetime.now()  # Replace with your end datetime condition

        # # Define the step size (1 day)
        # step = timedelta(days=1)
        # current_datetime = item
        # count = 0
        # while current_datetime <= end_datetime:
        #     next_datetime = current_datetime + step
            
        #     # Query data for the current day
        #     data = Combination.objects.filter(date_time__gte=current_datetime, date_time__lt=next_datetime).all()
        #     print('fetched')
        #     count += len(data)
            
        #     data.delete()
        #     print(f'\r deleted {count}', end='', flush=True)
        #     current_datetime = next_datetime
    
        
        data = Combination.objects.filter(date_time__gte=item).all()
        data.delete()
        
            # count+=1
            # for item in data:
            
        # print(len(data))
        # data.delete()
        print('cleaned combinations')
        # data = Stock.objects.filter(date_time__gte=item).all()
        # data.delete()
        # print('cleaned stocks')
        # con.set("combinations_data", "[]")
        # con.set("comb_time", "[]")
        # con.set("stock_data", "[]")
        # print('cleaned redis')
    
    return 'cleaned'
       

def new_flow_migrator(initial):
    error_count = 0
    my_time = str(datetime.now())
    con.set("initiated", my_time)
    print('Initiated')   
    
    count = 0 
    initial_timestamp = datetime.strptime(str(Cronny.objects.latest('date_time').symbol), "%Y-%m-%d %H:%M:%S") # datetime(2024, 4,  29, 9,39 ) # # datetime(2024, 4,  30, 16) 
    # initial_timestamp = datetime.strptime(str(initial), "%Y-%m-%d %H:%M:%S")
    # datetime(2024, 4,  23, 10, 2)
    # initial_timestamp = datetime(2024, 4,  29, 11, )
    
    current_timestamp = (datetime.now())
    # datetime(2024, 4,  30, 11, 15)  #datetime(2024, 4,  25, 16)
    
    # Ensure initial_timestamp is before current_timestamp
    if initial_timestamp > current_timestamp:
        initial_timestamp, current_timestamp = current_timestamp, initial_timestamp
    while initial_timestamp < current_timestamp:
        if initial_timestamp.time() >= time(9, 30) and initial_timestamp.time() <= time(15, 59): 
            intital_time = datetime.now()
            
            print('migration', initial_timestamp)
            timestamp = initial_timestamp
            res = get_data(timestamp)
            stocks = res["stocks"]
            print(len(stocks), 'stokcs')
            stock_time = create_stocks(stocks, timestamp)
            # if initial_timestamp.time() >= time(9, 30): 
            
            generate_flow_combinations(timestamp)
            generate_dji_combinations(timestamp, [item['date_time'] for item in Stock.objects.filter(symbol="DJI").values("date_time").order_by("date_time").distinct()])

            Cronny.objects.create(symbol=f"{timestamp}")    
            final_time = datetime.now() - intital_time            
            print(f"Time difference: {final_time.total_seconds()} seconds", timestamp)
            for item in Strike.objects.filter(closed=False):
                update_strike(item.id)
        initial_timestamp += timedelta(minutes=1)
        current_timestamp = (datetime.now())
        
def real_time_data():
    done = False
    count = 0 
    current_date = datetime.now().date()
    queryset = Nonday.objects.filter(date_time__date=current_date).first()
    proceed = False
    if queryset:
        if queryset.half_day == True and timestamp.time() <= time(13, 00):
            proceed = True
    else:
        proceed = True
        
    if proceed:    
        timestamp = (datetime.now() - timedelta(minutes = 2)).replace(second=0, microsecond=0)
        timestamp  = datetime.strptime(str(timestamp), "%Y-%m-%d %H:%M:%S")
        if timestamp.time() >= time(9, 30) and timestamp.time() <= time(15, 59): 
            res = get_data(timestamp)
            stocks = res["stocks"]
            stock_time = create_stocks(stocks, timestamp)
            generate_flow_combinations(timestamp)
            generate_dji_combinations(timestamp, [item['date_time'] for item in Stock.objects.filter(symbol="DJI").values("date_time").order_by("date_time").distinct()])
            end_time = datetime.now()
            Cronny.objects.create(symbol=f"{stock_time}")    
            done = True
            print('Finally Done', count)
            for item in Strike.objects.filter(closed=False):
                update_strike(item.id)
            
            
def quick_real_time_data(timestamp):
    done = False
    # timestamp = (datetime.now() - timedelta(minutes = 2)).replace(second=0, microsecond=0)
    timestamp  = datetime.strptime(str(timestamp), "%Y-%m-%d %H:%M:%S")
    if timestamp.time() >= time(9, 30) and timestamp.time() <= time(15, 59): 
        res = get_data(timestamp)
        stocks = res["stocks"]
        stock_time = create_stocks(stocks, timestamp)
        generate_flow_combinations(timestamp)
        generate_dji_combinations(timestamp, [item['date_time'] for item in Stock.objects.filter(symbol="DJI").values("date_time").order_by("date_time").distinct()])
        end_time = datetime.now()
        Cronny.objects.create(symbol=f"{stock_time}")    
        done = True
        print('Finally Done')
        for item in Strike.objects.filter(closed=False):
            update_strike(item.id)            
            
def generate_test_combinations(current_datetime):
    start_time = datetime.now()
    timestamp = current_datetime
    print(timestamp)
    distinct_timestamps = [item['date_time'] for item in Stock.objects.values("date_time").order_by("date_time").distinct() if is_in_trading(item['date_time'])]
    distinct_timestamps.append(timestamp)
    new_distinct_timestamps = sorted(distinct_timestamps)
    previous, current, final = new_distinct_timestamps.index(timestamp) - 1,  new_distinct_timestamps.index(timestamp), new_distinct_timestamps.index(timestamp) + 1 
    
    # print(new_distinct_timestamps.index(timestamp) - 1,  new_distinct_timestamps.index(timestamp), new_distinct_timestamps.index(timestamp) + 1 )

    final_time = None
    try:
        final_time = new_distinct_timestamps[final]
    except:
        final_time = new_distinct_timestamps[current]
            
                
    previous_time = new_distinct_timestamps[previous]
    print(previous_time, final_time)
    stocks = [ StockSerializer(item).data for item in Stock.objects.filter(date_time = final_time).all()]
    print ('len ', len(stocks))
    pprint(stocks[0])
    
    prev_close = {}
    prev_close["DJI"] = 0
   
    last_stocks = [ StockSerializer(item).data for item in Stock.objects.filter(date_time = previous_time).all()]
    
    for item in last_stocks:
        prev_close[item['symbol']] = item['close']
    print('last_stock')
    pprint(last_stocks[0])
    # stocks = [ StockSerializer(item).data for item in Stock.objects.filter(
    #                                         date_time__gte=final_time,
    #                                         date_time__lt=(final_time + timedelta(minutes=1))).all()]
    # stocks = [ StockSerializer(item).data for item in Stock.objects.order_by('-date_time')[:31]]
    print('Stocks', len(stocks))
    
    # Get distinct symbols
    distinct_symbols = Combination.objects.values('symbol').distinct()

    # Initialize a list to store the most recent combination objects
    recent_objects = []

    # Iterate over distinct symbols
    for symbol in distinct_symbols:
        # Get the most recent combination object for each symbol
        most_recent_combination = Combination.objects.filter(date_time__lt = final_time).filter(symbol=symbol['symbol']).order_by('-date_time').first()
        # Add the most recent combination object to the list
        recent_objects.append(most_recent_combination)

    # Print the count of recent_objects
    print(len(recent_objects), 'recent combos')
    print(recent_objects[0].symbol, recent_objects[0].date_time, recent_objects[0].avg )
    previous_set = list(recent_objects)
    print(len(previous_set))
    
    
    # current_date = timestamp.date()
    # start_datetime = current_date - timedelta(days=1)
    # start_date = datetime.combine(start_datetime, datetime.strptime("15:59", "%H:%M").time())
    # end_date = datetime.combine((current_date + timedelta(days=1)), datetime.strptime("15:59", "%H:%M").time()) 
    # earnings_data = Earning.objects.filter(date_time__date__range=[start_date, end_date])
    # valid_earnings_data = [item.symbol for item in earnings_data if start_date <= item.date_time <= end_date]

    earning_dates = {}
    valid_earnings_data = []
    for earnings in Earning.objects.all():
        start_date = datetime.combine((earnings.date_time.date() - timedelta(days=1)), datetime.strptime("15:59", "%H:%M").time())
        end_date = datetime.combine((earnings.date_time.date() + timedelta(days=1)), datetime.strptime("15:59", "%H:%M").time())
        if start_date <= timestamp <= end_date:
            valid_earnings_data.append(earnings.symbol)
            
    combs = combinations(Company.SYMBOLS, 3)
    
    pre_filtered_combinations = []
    
    for comb in [cmb for cmb in combs if not check_strike_symbol(f"{cmb[0]}-{cmb[1]}-{cmb[2]}", valid_earnings_data)]:
        
        strike = f"{comb[0]}-{comb[1]}-{comb[2]}"
        
        stock_1 = [stock for stock in stocks if stock['symbol'] == comb[0] ][0]
        stock_2 = [stock for stock in stocks if stock['symbol'] == comb[1] ][0]
        stock_3 = [stock for stock in stocks if stock['symbol'] == comb[2] ][0] 
        
        # current_percent = ((stock_1['close'] + stock_2['close'] + stock_3['close']) - (stock_1['previous_close'] + stock_2['previous_close'] + stock_3['previous_close']) ) / (stock_1['previous_close'] + stock_2['previous_close'] + stock_3['previous_close']) * 100
        current_percent = (((stock_1['close'] - prev_close[comb[0]] ) / prev_close[comb[0]]) + ((stock_2['close'] - prev_close[comb[1]] ) / prev_close[comb[1]]) + ((stock_3['close'] - prev_close[comb[2]] ) / prev_close[comb[2]])) * 100
        cummulative_percent = 0
        previous_instance = None 
        try:
            previous_instance = [item for item in previous_set if item.symbol == strike][0]    
            if previous_instance:
                cummulative_percent  =  previous_instance.avg + current_percent
            else:
                cummulative_percent  =  current_percent
                
            pre_filtered_combinations.append(
                 Combination(
                            symbol=strike,
                            avg=cummulative_percent,
                            stdev=current_percent,
                            strike=(stock_1['close'] + stock_2['close'] + stock_3['close'])/3,
                            date_time=timestamp,
                            z_score=0,
                        )
            )
        except Exception as E:
            pass
    print('now filtering db')
    
    
    pre_filtered_combinations.sort(key=lambda x: x.avg, reverse=True)
    cmb = pre_filtered_combinations[:5]+pre_filtered_combinations[-5:]
    print(current_datetime)
    for item in cmb:
        print(f"{item.symbol} {item.avg}")
        
    end_time = datetime.now()
    time_difference = end_time - start_time
    print(f"data created in {time_difference.total_seconds()} seconds" 'Saved')    


def test_datetime():
    year = int(input("year: "))
    month = int(input("month: "))
    day = int(input("day: "))
    hour = int(input("hour: "))
    minute = int(input("minute: "))
    current_datetime = datetime(year, month, day, hour, minute)
    generate_test_combinations(current_datetime)