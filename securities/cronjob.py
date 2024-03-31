import requests
import pandas as pd
import os
import numpy as np
import json, random
from datetime import datetime
from itertools import combinations

from django.conf import settings
from django.core.cache import cache
from django_redis import get_redis_connection
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Stock, Company, Combination, Cronny
from pprint import pprint
con = get_redis_connection("default")
print(cache.get("last_datetime"))

def cronny():
    Cronny.objects.create(symbol="crone good")
    
res = {'status_code': 200,
 'stocks': {'AAPL': {'meta': {'currency': 'USD',
                              'exchange': 'NASDAQ',
                              'exchange_timezone': 'America/New_York',
                              'interval': '1min',
                              'mic_code': 'XNGS',
                              'symbol': 'AAPL',
                              'type': 'Common Stock'},
                     'status': 'ok',
                     'values': [{'close': '171.52',
                                 'datetime': '2024-03-28 15:59:00',
                                 'high': '171.90',
                                 'low': '171.26',
                                 'open': '171.86',
                                 'previous_close': '171.86',
                                 'volume': '1669914'}]},
            'AMGN': {'meta': {'currency': 'USD',
                              'exchange': 'NASDAQ',
                              'exchange_timezone': 'America/New_York',
                              'interval': '1min',
                              'mic_code': 'XNGS',
                              'symbol': 'AMGN',
                              'type': 'Common Stock'},
                     'status': 'ok',
                     'values': [{'close': '284.27',
                                 'datetime': '2024-03-28 15:59:00',
                                 'high': '284.49',
                                 'low': '284.21',
                                 'open': '284.49',
                                 'previous_close': '284.51',
                                 'volume': '69510'}]},
            'AXP': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'AXP',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '227.69',
                                'datetime': '2024-03-28 15:59:00',
                                'high': '228.03',
                                'low': '227.66',
                                'open': '228.02',
                                'previous_close': '228.03',
                                'volume': '100972'}]},
            'BA': {'meta': {'currency': 'USD',
                            'exchange': 'NYSE',
                            'exchange_timezone': 'America/New_York',
                            'interval': '1min',
                            'mic_code': 'XNYS',
                            'symbol': 'BA',
                            'type': 'Common Stock'},
                   'status': 'ok',
                   'values': [{'close': '193.04',
                               'datetime': '2024-03-28 15:59:00',
                               'high': '193.30',
                               'low': '192.84',
                               'open': '193.04',
                               'previous_close': '193.06',
                               'volume': '159941'}]},
            'CAT': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'CAT',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '366.26',
                                'datetime': '2024-03-28 15:59:00',
                                'high': '367.15',
                                'low': '366.26',
                                'open': '367.04',
                                'previous_close': '367.09',
                                'volume': '76595'}]},
            'CRM': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'CRM',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '300.92',
                                'datetime': '2024-03-28 15:59:00',
                                'high': '301.66',
                                'low': '300.81',
                                'open': '300.96',
                                'previous_close': '300.98',
                                'volume': '235874'}]},
            'CSCO': {'meta': {'currency': 'USD',
                              'exchange': 'NASDAQ',
                              'exchange_timezone': 'America/New_York',
                              'interval': '1min',
                              'mic_code': 'XNGS',
                              'symbol': 'CSCO',
                              'type': 'Common Stock'},
                     'status': 'ok',
                     'values': [{'close': '49.89',
                                 'datetime': '2024-03-28 15:59:00',
                                 'high': '49.95',
                                 'low': '49.87',
                                 'open': '49.91',
                                 'previous_close': '49.91',
                                 'volume': '907689'}]},
            'CVX': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'CVX',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '157.71',
                                'datetime': '2024-03-28 15:59:00',
                                'high': '158.06',
                                'low': '157.67',
                                'open': '157.93',
                                'previous_close': '157.94',
                                'volume': '293194'}]},
            'DIS': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'DIS',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '122.34',
                                'datetime': '2024-03-28 15:59:00',
                                'high': '122.55',
                                'low': '122.33',
                                'open': '122.46',
                                'previous_close': '122.46',
                                'volume': '392587'}]},
            'DJI': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'DJI',
                             'type': 'Index'},
                    'status': 'ok',
                    'values': [{'close': '39786.20',
                                'datetime': '2024-03-28 15:59:00',
                                'high': '39857.71',
                                'low': '39786.20',
                                'open': '39840.27',
                                'previous_close': '39840.67',
                                'volume': '12888348'}]},
            'DOW': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'DOW',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '57.93',
                                'datetime': '2024-03-28 15:59:00',
                                'high': '57.99',
                                'low': '57.92',
                                'open': '57.95',
                                'previous_close': '57.95',
                                'volume': '204103'}]},
            'GS': {'meta': {'currency': 'USD',
                            'exchange': 'NYSE',
                            'exchange_timezone': 'America/New_York',
                            'interval': '1min',
                            'mic_code': 'XNYS',
                            'symbol': 'GS',
                            'type': 'Common Stock'},
                   'status': 'ok',
                   'values': [{'close': '417.57',
                               'datetime': '2024-03-28 15:59:00',
                               'high': '418.67',
                               'low': '417.57',
                               'open': '418.19',
                               'previous_close': '418.19',
                               'volume': '122186'}]},
            'HD': {'meta': {'currency': 'USD',
                            'exchange': 'NYSE',
                            'exchange_timezone': 'America/New_York',
                            'interval': '1min',
                            'mic_code': 'XNYS',
                            'symbol': 'HD',
                            'type': 'Common Stock'},
                   'status': 'ok',
                   'values': [{'close': '383.49',
                               'datetime': '2024-03-28 15:59:00',
                               'high': '384.19',
                               'low': '383.38',
                               'open': '383.91',
                               'previous_close': '383.92',
                               'volume': '209113'}]},
            'HON': {'meta': {'currency': 'USD',
                             'exchange': 'NASDAQ',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNGS',
                             'symbol': 'HON',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '205.25',
                                'datetime': '2024-03-28 15:59:00',
                                'high': '205.38',
                                'low': '205.18',
                                'open': '205.36',
                                'previous_close': '205.36',
                                'volume': '132734'}]},
            'IBM': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'IBM',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '190.91',
                                'datetime': '2024-03-28 15:59:00',
                                'high': '191.21',
                                'low': '190.79',
                                'open': '190.81',
                                'previous_close': '190.82',
                                'volume': '218019'}]},
            'INTC': {'meta': {'currency': 'USD',
                              'exchange': 'NASDAQ',
                              'exchange_timezone': 'America/New_York',
                              'interval': '1min',
                              'mic_code': 'XNGS',
                              'symbol': 'INTC',
                              'type': 'Common Stock'},
                     'status': 'ok',
                     'values': [{'close': '44.15',
                                 'datetime': '2024-03-28 15:59:00',
                                 'high': '44.26',
                                 'low': '44.12',
                                 'open': '44.26',
                                 'previous_close': '44.26',
                                 'volume': '2181756'}]},
            'JNJ': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'JNJ',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '158.17',
                                'datetime': '2024-03-28 15:59:00',
                                'high': '158.53',
                                'low': '158.15',
                                'open': '158.27',
                                'previous_close': '158.27',
                                'volume': '287555'}]},
            'JPM': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'JPM',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '200.28',
                                'datetime': '2024-03-28 15:59:00',
                                'high': '200.72',
                                'low': '200.28',
                                'open': '200.52',
                                'previous_close': '200.52',
                                'volume': '344523'}]},
            'KO': {'meta': {'currency': 'USD',
                            'exchange': 'NYSE',
                            'exchange_timezone': 'America/New_York',
                            'interval': '1min',
                            'mic_code': 'XNYS',
                            'symbol': 'KO',
                            'type': 'Common Stock'},
                   'status': 'ok',
                   'values': [{'close': '61.15',
                               'datetime': '2024-03-28 15:59:00',
                               'high': '61.24',
                               'low': '61.13',
                               'open': '61.17',
                               'previous_close': '61.18',
                               'volume': '794462'}]},
            'MCD': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'MCD',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '281.81',
                                'datetime': '2024-03-28 15:59:00',
                                'high': '282.20',
                                'low': '281.80',
                                'open': '282.01',
                                'previous_close': '282.03',
                                'volume': '150173'}]},
            'MMM': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'MMM',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '106.03',
                                'datetime': '2024-03-28 15:59:00',
                                'high': '106.20',
                                'low': '106.03',
                                'open': '106.16',
                                'previous_close': '106.15',
                                'volume': '205196'}]},
            'MRK': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'MRK',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '131.93',
                                'datetime': '2024-03-28 15:59:00',
                                'high': '132.18',
                                'low': '131.87',
                                'open': '132.02',
                                'previous_close': '132.03',
                                'volume': '391673'}]},
            'MSFT': {'meta': {'currency': 'USD',
                              'exchange': 'NASDAQ',
                              'exchange_timezone': 'America/New_York',
                              'interval': '1min',
                              'mic_code': 'XNGS',
                              'symbol': 'MSFT',
                              'type': 'Common Stock'},
                     'status': 'ok',
                     'values': [{'close': '420.03',
                                 'datetime': '2024-03-28 15:59:00',
                                 'high': '421.21',
                                 'low': '419.92',
                                 'open': '421.20',
                                 'previous_close': '421.21',
                                 'volume': '837856'}]},
            'NKE': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'NKE',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '93.97',
                                'datetime': '2024-03-28 15:59:00',
                                'high': '94.17',
                                'low': '93.97',
                                'open': '94.13',
                                'previous_close': '94.14',
                                'volume': '283487'}]},
            'PG': {'meta': {'currency': 'USD',
                            'exchange': 'NYSE',
                            'exchange_timezone': 'America/New_York',
                            'interval': '1min',
                            'mic_code': 'XNYS',
                            'symbol': 'PG',
                            'type': 'Common Stock'},
                   'status': 'ok',
                   'values': [{'close': '162.16',
                               'datetime': '2024-03-28 15:59:00',
                               'high': '162.47',
                               'low': '162.07',
                               'open': '162.21',
                               'previous_close': '162.21',
                               'volume': '364182'}]},
            'TRV': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'TRV',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '230.05',
                                'datetime': '2024-03-28 15:59:00',
                                'high': '230.74',
                                'low': '230.03',
                                'open': '230.70',
                                'previous_close': '230.71',
                                'volume': '58900'}]},
            'UNH': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'UNH',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '494.59',
                                'datetime': '2024-03-28 15:59:00',
                                'high': '495.28',
                                'low': '494.37',
                                'open': '494.78',
                                'previous_close': '494.84',
                                'volume': '183618'}]},
            'V': {'meta': {'currency': 'USD',
                           'exchange': 'NYSE',
                           'exchange_timezone': 'America/New_York',
                           'interval': '1min',
                           'mic_code': 'XNYS',
                           'symbol': 'V',
                           'type': 'Common Stock'},
                  'status': 'ok',
                  'values': [{'close': '278.78',
                              'datetime': '2024-03-28 15:59:00',
                              'high': '279.61',
                              'low': '278.69',
                              'open': '279.50',
                              'previous_close': '279.50',
                              'volume': '254364'}]},
            'VZ': {'meta': {'currency': 'USD',
                            'exchange': 'NYSE',
                            'exchange_timezone': 'America/New_York',
                            'interval': '1min',
                            'mic_code': 'XNYS',
                            'symbol': 'VZ',
                            'type': 'Common Stock'},
                   'status': 'ok',
                   'values': [{'close': '41.95',
                               'datetime': '2024-03-28 15:59:00',
                               'high': '42.01',
                               'low': '41.95',
                               'open': '41.99',
                               'previous_close': '41.99',
                               'volume': '584580'}]},
            'WBA': {'meta': {'currency': 'USD',
                             'exchange': 'NASDAQ',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNGS',
                             'symbol': 'WBA',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '21.68',
                                'datetime': '2024-03-28 15:59:00',
                                'high': '21.73',
                                'low': '21.67',
                                'open': '21.72',
                                'previous_close': '21.73',
                                'volume': '537746'}]},
            'WMT': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'WMT',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '60.16',
                                'datetime': '2024-03-28 15:59:00',
                                'high': '60.26',
                                'low': '60.16',
                                'open': '60.19',
                                'previous_close': '60.20',
                                'volume': '1039220'}]}}}  

def store():
    """
    Stores to the database then sends to the socket.
    """
    print('intitating')
    # try:
    # res = get_data()  
    
    if not 'log.txt' in os.listdir(os.getcwd()):
        f = open('log.txt', 'w')
        f.close()
    f = open('log.txt', 'a')
    f.write(f"\n{str(datetime.now())}")
    f.close()
        
        
    # import pprint
    if res["status_code"] == 200:
        stocks = res["stocks"]
        # current_datetime = stocks[Company.DOW_JONES]["values"][0][
        #     "datetime"
        # ]
        current_datetime = str(datetime.now())
        # if current_datetime == cache.get("last_datetime"):
        #     print('this is the issue ignore')
        #     return False
        # print(current_datetime, cache.get("last_datetime"))
        cache.set("last_datetime", current_datetime, timeout=None)
        con.rpush("last_200", str(current_datetime))
        con.ltrim("last_200", -200, -1)

        stock_items = create_stocks(stocks)
        stocks_list = stock_items["stocks_list"]
        
        
        # if stocks_list:
        current_datetime = datetime.fromisoformat(current_datetime)
        combinations_list = get_combinations(stocks, current_datetime)
        print(len(combinations_list), 'jerer')
        if combinations_list:
            print(len(combinations_list))
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

            
                
            
                
            # if stocks_list and strikes_list:
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
            # Stock.objects.bulk_create(stocks_list)
            print('creating combinations')
            Combination.objects.bulk_create(strikes_list)

    else:
        print('status code bad')
    # except Exception as e:
    #     print("Exception for stock update after crone execution. Message:", e)


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
                (float(stock_1) + float(stock_2) + float(stock_3) +random.randint(100,500)) / 3,
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
            z_score=lambda x: ((x["strike"]["strike"]) - x["strike"]["avg"] + random.randint(10,50))
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

