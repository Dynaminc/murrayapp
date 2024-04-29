import requests
import pandas as pd
import os
import numpy as np
import json, random
from datetime import datetime, timedelta, time
from itertools import combinations
from django.core.paginator import Paginator
from django.conf import settings
from django.db.models import Q
from django.db import IntegrityError
from django.utils import timezone as tz
from django.core.cache import cache
from .models import Stock, Company, Combination, Cronny
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
 
info = {}
info['main_count'] = 0
## Contains the most recent build for data retrieval, processing and storage, skips redis for now
def cronny():
    data = [ update_strike(item.id) for item in Strike.objects.filter(closed=False)]
    

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
    
    
    current_time = []
    print(len(stocks), 'all stocks')
    for item in SYMBOLS:
        company = item.split(':')[0]
        print(company,'copmany', len(stocks))
        

        try:
            stock_data  = [stock_item[1] for stock_item in stocks.items() if stock_item[0].split(':')[0] == company][0]
            print('herem done')
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
            print(E, 'Error', company )
            try:
                latest_stock = Stock.objects.filter(symbol=company).latest('date_time')
                latest_datetime = latest_stock.date_time 
                print(E, 'Error', 'latest datetime', latest_datetime , timestamp)
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
                print('except',)
                stock_obj = Stock(open=float(latest_stock.open), **new_stock_dict)
                stocks_list.append(stock_obj)
                print('appenddd', company, current_datetime)
                json_stocks_list.append(stock_dict_json)
            
            except Exception as E:
                print('Print Errr', E)
        stock_to_redis(json_stocks_list)                        
    
    print(len(stocks_list))
    # try:
    Stock.objects.bulk_create(stocks_list, ignore_conflicts=True)
    # except IntegrityError:
    #     pass
    
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
    clean_comb()
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
    item = Stock.objects.filter(symbol="DJI").filter(date_time=new_distinct_timestamps[final]).first()
    stock = StockSerializer(item).data
    print('fetched')
    
    previous_instance = Combination.objects.filter(symbol="DJI").filter(date_time=new_distinct_timestamps[previous]).first()
    
    if not previous_instance:
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
            stdev=0,
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
    
    
    
def generate_flow_combinations(current_datetime):
    timestamp = current_datetime
    distinct_timestamps = [item['date_time'] for item in Stock.objects.values("date_time").order_by("date_time").distinct()]
    distinct_timestamps.append(timestamp)
    new_distinct_timestamps = sorted(distinct_timestamps)
    previous, current, final = new_distinct_timestamps.index(timestamp) - 1,  new_distinct_timestamps.index(timestamp), new_distinct_timestamps.index(timestamp) + 1 
    print(new_distinct_timestamps.index(timestamp) - 1,  new_distinct_timestamps.index(timestamp), new_distinct_timestamps.index(timestamp) + 1 )
    
    stocks = [ StockSerializer(item).data for item in Stock.objects.filter(
                                            date_time__gte=new_distinct_timestamps[final],
                                            date_time__lt=(new_distinct_timestamps[final] + timedelta(minutes=1))).all()]
    
    # stocks = [ StockSerializer(item).data for item in Stock.objects.order_by('-date_time')[:31]]
    print('Stocks', len(stocks))
    dataset = Combination.objects.filter(
        Q(date_time=new_distinct_timestamps[previous]) |
        Q(date_time=new_distinct_timestamps[final])
    ).all()
    
    
    final_time = None
    try:
        final_time = new_distinct_timestamps[final]
    except:
        final_time = new_distinct_timestamps[current]
        
    previous_set = [item for item in dataset if item.date_time == new_distinct_timestamps[previous]]
    final_set = [item for item in dataset if item.date_time == final_time]
    print(timestamp, new_distinct_timestamps[previous], final_time)
    
    
    combs = combinations(Company.SYMBOLS, 3)
    for comb in combs:
        
        strike = f"{comb[0]}-{comb[1]}-{comb[2]}"
        
        # try:
        stock_1 = [stock for stock in stocks if stock['symbol'] == comb[0] ][0]
        stock_2 = [stock for stock in stocks if stock['symbol'] == comb[1] ][0]
        stock_3 = [stock for stock in stocks if stock['symbol'] == comb[2] ][0] 
        #and stock['date_time'].replace('T', ' ') == str(timestamp)
        
        
        current_percent = ((stock_1['close'] + stock_2['close'] + stock_3['close']) - (stock_1['previous_close'] + stock_2['previous_close'] + stock_3['previous_close']) ) / (stock_1['previous_close'] + stock_2['previous_close'] + stock_3['previous_close']) * 100
        
        
        
        previous_instance = [item for item in previous_set if item.symbol == strike][0]
        try:
            comb_instance = [item for item in final_set if item.symbol == strike][0]
            cummulative_percent  =  previous_instance.avg + current_percent
            comb_instance.avg = cummulative_percent
            comb_instance.save()
        except:
            cummulative_percent  =  previous_instance.avg + current_percent
            try:
                Combination.objects.create(
                    symbol=strike,
                    avg=cummulative_percent,
                    stdev=0,
                    strike=(stock_1['close'] + stock_2['close'] + stock_3['close'])/3,
                    date_time=timestamp,
                    z_score=0,
                ) 
            except:
                pass
            
        
        
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
        
def clean_comb():
    # clean_redis()
    # return 'cleaned'

    count = 0 
    times = [datetime(2024, 4, 29, 15, 29)]
    for item in times:
        print('Running clean module ')
        data = Combination.objects.filter(date_time__gte=item).all()
        data.delete()
        print('cleaned combinations')
        data = Stock.objects.filter(date_time__gte=item).all()
        data.delete()
        print('cleaned stocks')
        con.set("combinations_data", "[]")
        con.set("comb_time", "[]")
        con.set("stock_data", "[]")
        print('cleaned redis')
        
    
    return 'cleaned'
       

def new_flow_migrator():
    # clean_comb()
    ## ths block reverses the effect 
    # initial_timestamp = datetime(2024, 4,  24, 10, 58)
    # clean_avgs(initial_timestamp)
    # 
    # return
    
    error_count = 0
    my_time = str(datetime.now())
    con.set("initiated", my_time)
    print('Initiated')   
    
    count = 0 
    # initial_timestamp = datetime.strptime(str(Cronny.objects.latest('date_time').symbol), "%Y-%m-%d %H:%M:%S") #datetime(2024, 4,  24, 11,59)
    # datetime(2024, 4,  23, 10, 2)
    initial_timestamp = datetime(2024, 4,  29, 15, 29)
    current_timestamp = datetime(2024, 4,  29, 16)  #datetime(2024, 4,  25, 16)
    
    # Ensure initial_timestamp is before current_timestamp
    if initial_timestamp > current_timestamp:
        initial_timestamp, current_timestamp = current_timestamp, initial_timestamp
    while initial_timestamp < current_timestamp:
        print('here')
        
        if initial_timestamp.time() >= time(9, 30) and initial_timestamp.time() <= time(15, 59): 
            
            print('in neer', initial_timestamp)
            timestamp = initial_timestamp
            res = get_data(timestamp)
            stocks = res["stocks"]
            print(len(stocks), 'stokcs')
            stock_time = create_stocks(stocks, timestamp)
            generate_flow_combinations(timestamp)
            generate_dji_combinations(timestamp, [item['date_time'] for item in Stock.objects.filter(symbol="DJI").values("date_time").order_by("date_time").distinct()])
            Cronny.objects.create(symbol=f"{timestamp}")    
            print(timestamp)
            # count += 1
            # if count == 15:
            #     break
            
        initial_timestamp += timedelta(minutes=1)
        
        
def real_time_data():
    done = False
    while not done:
        try:
            start_time = datetime(2024, 4,  29, 15, 59)
            # datetime.now()
            print('start time', start_time)
            res = get_minute_data()
            stocks = res["stocks"]
            print('in here ere')
            stock_time = create_stocks(stocks, start_time)
            print(stock_time)
            generate_flow_combinations(stock_time)
            print('start time flow')
            generate_dji_combinations(stock_time, [item['date_time'] for item in Stock.objects.filter(symbol="DJI").values("date_time").order_by("date_time").distinct()])
            end_time = datetime.now()
            time_difference = end_time - start_time
            print(f"{stock_time}-{time_difference.total_seconds()}")
            Cronny.objects.create(symbol=f"{stock_time}m{time_difference.total_seconds()}")    
            done = True
        except:
            pass
            
            
        