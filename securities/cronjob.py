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
from django.core.serializers.json import DjangoJSONEncoder


## Contains the most recent build for data retrieval, processing and storage, skips redis for now
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




def create_stocks(stocks, tmp_time):
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
    )
    
    
    current_time = []
    for item in SYMBOLS:
        company = item.split(':')[0]
        stock_data  = [stock_item[1] for stock_item in stocks.items() if stock_item[0].split(':')[0] == company][0]

        try:
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
        except:

            latest_stock = Stock.objects.filter(symbol=company).latest('date_time')
            latest_datetime = latest_stock.date_time 
            # new_current = latest_datetime + timedelta(minutes=1)
            current_datetime = datetime.strptime(str(tmp_time), "%Y-%m-%d %H:%M:%S")
            current_time.append(current_datetime)
            f = open('missing_data.txt', 'a')
            f.write(f'\n {company} : {latest_datetime.strftime("%Y-%m-%d %H:%M:%S")}')
            f.close()
        
            # time_diff = (current_datetime - latest_datetime)
            
            # if time_diff > timedelta(minutes=1) and time_diff < timedelta(minutes=2): 
            #     while (current_datetime - latest_datetime) > timedelta(minutes=1):
            #         latest_datetime += timedelta(minutes=1)
            new_stock_dict = {
                "symbol": company,
                "close": float(latest_stock.close),
                "low": latest_stock.low,
                "high": latest_stock.high,
                "previous_close": float(latest_stock.previous_close),
                "date_time": latest_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            }
            stock_dict_json = {
                "open": latest_stock.open,
                "symbol": company,
                "close": float(latest_stock.close),
                "low": latest_stock.low,
                "high": latest_stock.high,
                "previous_close": float(latest_stock.previous_close),
                "date_time": latest_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            }
          
            stock_obj = Stock(open=float(latest_stock.open), **new_stock_dict)
            stocks_list.append(stock_obj)
            json_stocks_list.append(stock_dict_json)
            
        # except:
        #     pass            
        # stock_dict = {
        #     "symbol": company,
        #     "close": float(stock["close"]),
        #     "low": stock["low"],
        #     "high": stock["high"],
        #     "previous_close": float(stock["previous_close"]),
        #     "date_time": stock["datetime"],
        # }
        # stock_dict_json = {
        #     "open": stock['open'],
        #     "symbol": company,
        #     "close": float(stock["close"]),
        #     "low": stock["low"],
        #     "high": stock["high"],
        #     "previous_close": float(stock["previous_close"]),
        #     "date_time": stock["datetime"],
        # }
        

        stock_to_redis(json_stocks_list)                        
    
    
    try:
        Stock.objects.bulk_create(stocks_list, ignore_conflicts=True)
        # Combination.objects.bulk_create(strikes_list, ignore_conflicts=True)
    except IntegrityError:
        pass
    val = max(sorted(list(set(current_time))))
    print(val)
    return val

def stock_to_redis(json_stocks_list):
    existing_data = json.loads(con.get("stock_data") or "[]")
    combined_data = existing_data + json_stocks_list
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
        print('strike', strike)
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
    print(len(combinations_list), 'culprit')
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
            # stdev = most_recent_200.std()
            # z_scoreb = (most_recent_strike_B - avg) / stdev
            # print(most_recent_time , "symbol", symbol, "z-score scipy: ", z_score, "z-score pandas", z_scoreb )
            
            data.append({"symbol": symbol, "strike": most_recent_strike, "avg": 0, "date_time": most_recent_time, "stdev": 0, "z_score": z_score})
            
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
                print('hjsdfasa')
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
    res = get_minute_data()
    
    stocks = res["stocks"]
    stock_time = create_stocks(stocks, start_time)
    combinations_list = generate_combinations(stock_time) 
    
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
    print(stock_time, f" created in {time_difference.total_seconds()} seconds", 'Saved')
    return f"{stock_time} created in {time_difference.total_seconds()} seconds"
            
def new_calc_migrator():
    error_count = 0
    print('Cleaning')
    clean_comb()
    print('Initiating Calcs')
    begin_calcs() 
    print('Initiated')   
    initial_timestamp = datetime(2024, 4, 22, 9, 44)
    current_timestamp = datetime.now()

    # Ensure initial_timestamp is before current_timestamp
    if initial_timestamp > current_timestamp:
        initial_timestamp, current_timestamp = current_timestamp, initial_timestamp
    while initial_timestamp < current_timestamp:
        initial_timestamp += timedelta(minutes=1)
        if initial_timestamp.time() >= time(9, 30) and initial_timestamp.time() <= time(16, 0):
            timestamp = initial_timestamp
            start_time = datetime.now()
            res = get_data(timestamp)
            
            stocks = res["stocks"]
            stock_time = create_stocks(stocks, timestamp)
            timestamp += timedelta(minutes=1)
            
            combinations_list = generate_combinations(stock_time) 
            # begin_calcs()
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
            print(timestamp, f" created in {time_difference.total_seconds()} seconds" 'Saved')
        
def clean_comb():
    count = 0 
    times = [datetime(2024, 4, 22, 9, 44)]
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
        
    Cronny.objects.create(symbol=f"clean stock and combo {count}")
    return 'cleaned'