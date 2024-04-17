import requests
import pandas as pd
import os
import numpy as np
import json, random
from datetime import datetime, timedelta
from itertools import combinations
from django.core.paginator import Paginator
from django.conf import settings
from django.utils import timezone as tz
from django.core.cache import cache
from django_redis import get_redis_connection
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .views import update_strike
from .models import Stock, Company, Combination, Cronny

from accounts.models import Strike, Profile
from pprint import pprint
con = get_redis_connection("default")
print(cache.get("last_datetime"))



def cronny():
    data = [ update_strike(item.id) for item in Strike.objects.filter(closed=False)]
    if False in data:
        Cronny.objects.create(symbol=f"{len(data)}: False")
    else:
        Cronny.objects.create(symbol=f"{len(data)}: True")
    

def cleaner():
    d = tz.now() - timedelta(days=4)
    count = 0
    paginator = Paginator(Combination.objects.filter(date_time__lt=d), 1000) # chunks of 1000
    for page_idx in range(1, paginator.num_pages):
        for row in paginator.page(page_idx).object_list:
            count += 1
            row.delete()
            
    Cronny.objects.create(symbol=f"clean session: {count}")
    
def store():
    """
    Stores to the database then sends to the socket.
    """
    print('intitating')
    try:
        res = get_data()
        print(res["status_code"])
        
        if not 'log.txt' in os.listdir(os.getcwd()):
            f = open('log.txt', 'w')
            f.close()
        f = open('log.txt', 'a')
        f.write(f"\n{str(datetime.now())}")
        f.close()
            
            
        # import pprint
        if res["status_code"] == 200:
            stocks = res["stocks"]
            current_datetime = stocks[Company.DOW_JONES]["values"][0][
                "datetime"
            ]
            if current_datetime == cache.get("last_datetime"):
                print('this is the issue ignore')
                # return False
            # print(current_datetime, cache.get("last_datetime"))
            cache.set("last_datetime", current_datetime, timeout=None)
            con.rpush("last_200", str(current_datetime))
            con.ltrim("last_200", -200, -1)

            stock_items = create_stocks(stocks)
            stocks_list = stock_items["stocks_list"]
            if stocks_list:
                current_datetime = datetime.fromisoformat(current_datetime)
                combinations_list = get_combinations(stocks, current_datetime)

                if combinations_list:
                    first_datetime = datetime.fromisoformat(
                        con.lindex("last_200", 0).decode("utf-8")
                    )
                    combs = Combination.objects.filter(
                        date_time__gte=first_datetime
                    ).values("symbol", "strike", "date_time", "z_score")
                    
                    combinations_df = pd.DataFrame(
                        data=list(combs) + combinations_list
                    )
                    
                    combinations_df["date_time"] = pd.to_datetime(
                        combinations_df["date_time"]
                    )
                    calculated_combs = calc_stats(combinations_df)
                    strikes_list = []
                    for comb in calculated_combs.to_numpy():
                        strikes_list.append(
                            Combination(
                                symbol=comb[0],
                                avg=comb[1],
                                stdev=None if pd.isnull(comb[2]) else comb[2],
                                strike=comb[3],
                                date_time=current_datetime,
                                z_score=None if pd.isnull(comb[5]) else comb[5],
                            )
                        )
                    low_high = pd.concat(
                        [calculated_combs.head(), calculated_combs.tail()]
                    )["symbol"].to_list()
                    low_high.append(Company.DOW_JONES)
                    low_high = list(set(low_high))
                    if con.llen("last_200") > 120:
                        combinations_portion = con.lindex("last_200", -120)
                    else:
                        combinations_portion = con.lindex("last_200", 0)

                    stock_combs = combinations_df[
                        (combinations_df["symbol"].isin(low_high))
                        & (
                            combinations_df["date_time"]
                            >= datetime.fromisoformat(
                                combinations_portion.decode("utf-8")
                            )
                        )
                        & (combinations_df["date_time"] < current_datetime)
                    ][["symbol", "z_score", "date_time"]]

                    stock_combs = pd.concat(
                        [
                            stock_combs,
                            calculated_combs[
                                calculated_combs["symbol"].isin(low_high)
                            ][["symbol", "z_score", "date_time"]],
                        ]
                    )
                    stock_combs["date_time"] = stock_combs["date_time"].astype(
                        "string"
                    )
                    stock_combs = stock_combs.to_json(orient="records")
                    con.set("last_120", stock_combs)

                
                    
                
                    
                if stocks_list and strikes_list:
                    dow_stocks_serialized = json.dumps(stock_items["dow_stocks"])
                    con.set("last_30", dow_stocks_serialized)
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        "stock-update",
                        {
                            "type": "stock_update_data",
                            "data": {
                                "stocks": dow_stocks_serialized,
                                "combinations": stock_combs,
                            },
                        },
                    )
                    Stock.objects.bulk_create(stocks_list)
                    Combination.objects.bulk_create(strikes_list)

        else:
            print('status code bad')
    except Exception as e:
        print("Exception for stock update after crone execution. Message:", e)


def get_data():
    """Gets third-party API data"""
    try:
        twelve_key = settings.TWELVE_DATA_API_KEY
        all_symbols = ",".join(Company.all_symbols)
        res = requests.get(
            f"https://api.twelvedata.com/time_series?apikey={twelve_key}&interval=1min&symbol={all_symbols}&previous_close=true&dp=2&outputsize=1"  # noqa
        )
    except Exception as e:
        print(
            "Exception for fetching API data after crone execution. Message:",
            e,
        )

    return {"status_code": res.status_code, "stocks": res.json()}


def create_stocks(stocks):
    """Creates stock objects"""
    stocks_list = []
    dow_stocks = []
    companies = Company.objects.exclude(symbol=Company.DOW_JONES)
    for company in companies:
        stock = stocks[company.symbol]["values"][0]

        if (
            stocks[company.symbol]["status"] == "ok"
            and Stock.objects.filter(
                symbol=company.symbol, date_time=stock["datetime"]
            ).first()
            is None
        ):
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

            if Company.DOW_JONES != company.symbol:
                dow_stocks.append({"company": company.name, **stock_dict})
    return {"stocks_list": stocks_list, "dow_stocks": dow_stocks}


def get_combinations(stocks, current_datetime):
    """Creates combinations and their corresponding strikes"""
    combinations_list = []
    combs = combinations(Company.SYMBOLS, 3)
    import pprint
    print('getting combs')
    pprint.pprint(combs)
    comb_data = {
        "date_time": current_datetime,
        "z_score" : 0
    }
    for comb in combs:
        stock_1 = stocks[comb[0]]["values"][0].get("close")
        stock_2 = stocks[comb[1]]["values"][0].get("close")
        stock_3 = stocks[comb[2]]["values"][0].get("close")
        if all([stock_1, stock_2, stock_3]):
            strike_val = round(
                (float(stock_1) + float(stock_2) + float(stock_3)) / 3,
                2,
            )
            if strike_val >= 0:
                # stdev = round(pd.Series([float(stock_1), float(stock_2), float(stock_3)]).std(), 2)
                # z_score = (float(stock_1) - float(strike_val)) / stdev
                combinations_list.append(
                    {
                        "symbol": f"{comb[0]}-{comb[1]}-{comb[2]}",
                        "strike": strike_val ,
                        **comb_data,
                    }
                )

        else:
            combinations_list.append(
                {
                    "symbol": Company.DOW_JONES,
                    "strike": float(stocks[Company.DOW_JONES]["values"][0]["close"]),
                    **comb_data,
                }
            )

    return combinations_list


def calc_stats(dframe):
    """Calculates Arithmetic Mean and Standard Deviation of symbols"""
    combs = (
        dframe.groupby("symbol", as_index=False)
        .agg(
            {
                "strike": [
                    ("avg", "mean"),
                    ("stdev", "std"),
                    ("strike", "last"),
                ],
                "date_time": "last",
            }
        )
        .assign(
            z_score=lambda x: ((x["strike"]["strike"]) - x["strike"]["avg"])
            / x["strike"]["stdev"]
        )
        .round(3)
        .sort_values(by="z_score")
        
    )
    
    combs.columns = [
        "symbol",
        "avg",
        "stdev",
        "strike",
        "date_time",
        "z_score",
    ]
    

    return combs

def remove_data():
    """Removes the stock and combination data which are older than a month"""
    one_month = 30 * 30 * 390
    stock = Stock.objects.all()[one_month:one_month + 1]
    if stock.exists():
        time_limit = stock[0].date_time
        Stock.objects.filter(date_time__lt=time_limit).delete()
        Combination.objects.filter(date_time__lt=time_limit).delete()
        print("Stock/Combination data removed!")
    else:
        print("Nothing to delete!")



def calc_stats_b(df):
    # Convert 'date_time' to datetime format
    df['date_time'] = pd.to_datetime(df['date_time'])

    # Group by 'symbol' and calculate statistics for each group
    groups = df.groupby('symbol')
    data = []
    for symbol, group_df in groups:
        most_recent_200 = group_df.nlargest(200, 'date_time')['strike']
        most_recent_strike = most_recent_200.iat[-1]
        avg = most_recent_200.mean()
        stdev = most_recent_200.std()
        z_score = (most_recent_strike - avg) / stdev
        most_recent_time = group_df['date_time'].max()
        data.append({"symbol": symbol, "strike": most_recent_strike, "avg": avg, "stdev": stdev, "date_time": most_recent_time, "z_score": z_score})

    return data

# Create your tests here.
def store_new():
    """
    Stores to the database then sends to the socket.
    """
    try:
        res = get_data()
        if res["status_code"] == 200:
            stocks = res["stocks"]
            current_datetime = stocks[Company.DOW_JONES]["values"][0][
                "datetime"
            ]
            if current_datetime == cache.get("last_datetime"):
                return False
            cache.set("last_datetime", current_datetime, timeout=None)
            con.rpush("last_200", str(current_datetime))
            con.ltrim("last_200", -200, -1)

            stock_items = create_stocks(stocks)
            stocks_list = stock_items["stocks_list"]
            # if stocks_list:
            if stocks_list:
                Stock.objects.bulk_create(stocks_list)
                    
            current_datetime = datetime.fromisoformat(current_datetime)
            combinations_list = get_combinations(stocks, current_datetime)
            
            if combinations_list:
                twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
                combs = Combination.objects.filter(date_time__gte=twenty_four_hours_ago).values("symbol", "strike", "date_time", "z_score")
                combinations_df = pd.DataFrame(
                    data=list(combs) + combinations_list
                )
                combinations_df["date_time"] = pd.to_datetime(
                    combinations_df["date_time"]
                )
                calculated_combs = calc_stats_b(combinations_df)
            
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

        else:
            Cronny.objects.create(symbol=f"Error Loaing")
    except Exception as e:
        Cronny.objects.create(symbol=f"Exception for stock update after crone execution. Message: {e}")
        print("Exception for stock update after crone execution. Message:", e)

