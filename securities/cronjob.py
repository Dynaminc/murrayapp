import requests
import pandas as pd
import os
import numpy as np
import json, random
from datetime import datetime, timedelta
from itertools import combinations
from django.core.paginator import Paginator
from django.conf import settings
from django.db.models import Q
from django.utils import timezone as tz
from django.core.cache import cache
from .models import Stock, Company, Combination, Cronny
from scipy.stats import zscore


## Contains the most recent build for data retrieval, processing and storage, skips redis for now

def get_data():
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
        "WBA",
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


def create_stocks(stocks):
    stocks_list = []    
    dow_stocks = []
    companies = Company.objects.exclude(symbol=Company.DOW_JONES)
    current_time = []
    for company in companies:
        stock_data  = [stock_item[1] for stock_item in stocks.items() if stock_item[0].split(':')[0] == company.symbol][0]
        print(stock_data)
        # stock = stocks[company.symbol]["values"][0]
        stock = stock_data["values"][0]
        
        latest_stock = Stock.objects.filter(symbol=company.symbol).latest('date_time')
        latest_datetime = latest_stock.date_time 
        current_datetime = datetime.strptime(stock["datetime"], "%Y-%m-%d %H:%M:%S")
        current_time.append(current_datetime)
        time_diff = (current_datetime - latest_datetime)
        
        if time_diff > timedelta(minutes=1) and time_diff < timedelta(minutes=3): # fills in the blank minutes between
            while (current_datetime - latest_datetime) > timedelta(minutes=1):
                latest_datetime += timedelta(minutes=1)
                new_stock_dict = {
                    "symbol": company.symbol,
                    "close": float(latest_stock.close),  # Use the close price of the latest stock
                    "low": latest_stock.low,
                    "high": latest_stock.high,
                    "previous_close": float(latest_stock.previous_close),
                    "date_time": latest_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                }
                
                stock_obj = Stock(open=float(latest_stock.open), **new_stock_dict)
                stocks_list.append(stock_obj)
                
        stock_dict = {
            "symbol": company.symbol,
            "close": float(stock["close"]),
            "low": stock["low"],
            "high": stock["high"],
            "previous_close": float(stock["previous_close"]),
            "date_time": stock["datetime"],
        }
        stock_obj = Stock(open=stock["open"], **stock_dict)
        stocks_list.append(stock_obj)
        
    Stock.objects.bulk_create(stocks_list)
    return max(sorted(list(set(current_time))))

    
def generate_combinations(current_datetime):
    timestamp = current_datetime
    combs = combinations(Company.SYMBOLS, 3)
    combinations_list = []
    
    stocks = Stock.objects.filter(date_time__gte=timestamp).all()    
    for comb in combs:
        strike = f"{comb[0]}-{comb[1]}-{comb[2]}"
        stock_1 = [stock for stock in stocks if stock.symbol == comb[0] and stock.date_time == timestamp][0].close
        stock_2 = [stock for stock in stocks if stock.symbol == comb[1] and stock.date_time == timestamp][0].close
        stock_3 = [stock for stock in stocks if stock.symbol == comb[2] and stock.date_time == timestamp][0].close
        combinations_list.append(
                                {
                                    "symbol": strike,
                                    "strike":round((float(stock_1) + float(stock_2) + float(stock_3)) / 3, 4),
                                    "date_time": timestamp,
                                    "z_score" : 0,
                                }
                            )    
        
    return combinations_list
        
def calc_stats_b(df, timestamp):
    
    df['date_time'] = pd.to_datetime(df['date_time'])
    groups = df.groupby('symbol')
    sym = None
    
    data = []
    try:
        for symbol, group_df in groups:
            sym = symbol
            most_recent_strike = group_df.nlargest(1, 'date_time')['strike'].iloc[0]
            most_recent_200 = group_df.nlargest(200, 'date_time')['strike']
            avg = most_recent_200.mean()
            stdev = most_recent_200.std()
            most_recent_time = group_df['date_time'].max()
            z_score = (most_recent_strike - avg) / stdev
            
            data.append({"symbol": symbol, "strike": most_recent_strike, "avg": avg, "date_time": most_recent_time,"stdev": stdev, "z_score": z_score})
            
        return data        
    except Exception as E:
        
        print('error at symbol', sym, timestamp, E)
        return False   
                
def new_calc():
    res = get_data()
    stocks = res["stocks"]
    stock_time = create_stocks(stocks)
    combinations_list = generate_combinations(stock_time) 
    four_hours_ago = stock_time - timedelta(hours=4)
    combs = Combination.objects.filter(date_time__gte=four_hours_ago).values("symbol", "strike", "date_time", "z_score")
    combinations_df = pd.DataFrame(
        data=list(combs) + combinations_list
    )
    combinations_df["date_time"] = pd.to_datetime(
        combinations_df["date_time"]
    )
    
    calculated_combs = []
    
    calculated_combs = calc_stats_b(combinations_df, stock_time)
    
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
    
    Combination.objects.bulk_create(strikes_list)    
    
        
def clean_comb(): # rmove the precalculated combs for a new calculation
    count = 0 
    times = [datetime(2024, 4, 19, 12)]
    # strike = "VZ-WBA-WMT"
    for item in times:
        print('fetcging ')
        paginator = Paginator(Combination.objects.filter(date_time__gte=item), 1000)
        for page_idx in range(1, paginator.num_pages):
            for row in paginator.page(page_idx).object_list:
                count += 1
                row.delete()
        # data = Combination.objects.filter(date_time__date=item.date()).all()
        print('cleaned combinations')
        
        paginator = Paginator(Stock.objects.filter(date_time__gte=item), 1000) # chunks of 1000
        data = Stock.objects.filter(date_time__gte=item).all()
        for page_idx in range(1, paginator.num_pages):
            for row in paginator.page(page_idx).object_list:
                count += 1
                row.delete()
        
        print('cleaned stocks')
    Cronny.objects.create(symbol=f"clean stock and combo {count}")
    return 'cleaned'