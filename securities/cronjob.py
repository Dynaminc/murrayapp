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

con = get_redis_connection("default")

res = {'status_code': 200,
 'stocks': {'AAPL': {'meta': {'currency': 'USD',
                              'exchange': 'NASDAQ',
                              'exchange_timezone': 'America/New_York',
                              'interval': '1min',
                              'mic_code': 'XNGS',
                              'symbol': 'AAPL',
                              'type': 'Common Stock'},
                     'status': 'ok',
                     'values': [{'close': '172.57',
                                 'datetime': '2024-03-15 15:59:00',
                                 'high': '172.60',
                                 'low': '172.42',
                                 'open': '172.45',
                                 'previous_close': '172.44',
                                 'volume': '1517377'}]},
            'AMGN': {'meta': {'currency': 'USD',
                              'exchange': 'NASDAQ',
                              'exchange_timezone': 'America/New_York',
                              'interval': '1min',
                              'mic_code': 'XNGS',
                              'symbol': 'AMGN',
                              'type': 'Common Stock'},
                     'status': 'ok',
                     'values': [{'close': '268.91',
                                 'datetime': '2024-03-15 15:59:00',
                                 'high': '268.93',
                                 'low': '268.63',
                                 'open': '268.80',
                                 'previous_close': '268.81',
                                 'volume': '213555'}]},
            'AXP': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'AXP',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '218.43',
                                'datetime': '2024-03-15 15:59:00',
                                'high': '218.50',
                                'low': '218.29',
                                'open': '218.30',
                                'previous_close': '218.32',
                                'volume': '66337'}]},
            'BA': {'meta': {'currency': 'USD',
                            'exchange': 'NYSE',
                            'exchange_timezone': 'America/New_York',
                            'interval': '1min',
                            'mic_code': 'XNYS',
                            'symbol': 'BA',
                            'type': 'Common Stock'},
                   'status': 'ok',
                   'values': [{'close': '182.53',
                               'datetime': '2024-03-15 15:59:00',
                               'high': '182.70',
                               'low': '182.48',
                               'open': '182.59',
                               'previous_close': '182.58',
                               'volume': '98405'}]},
            'CAT': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'CAT',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '346.95',
                                'datetime': '2024-03-15 15:59:00',
                                'high': '347.02',
                                'low': '346.30',
                                'open': '346.30',
                                'previous_close': '346.28',
                                'volume': '81290'}]},
            'CRM': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'CRM',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '294.17',
                                'datetime': '2024-03-15 15:59:00',
                                'high': '294.28',
                                'low': '293.85',
                                'open': '293.88',
                                'previous_close': '293.87',
                                'volume': '243200'}]},
            'CSCO': {'meta': {'currency': 'USD',
                              'exchange': 'NASDAQ',
                              'exchange_timezone': 'America/New_York',
                              'interval': '1min',
                              'mic_code': 'XNGS',
                              'symbol': 'CSCO',
                              'type': 'Common Stock'},
                     'status': 'ok',
                     'values': [{'close': '48.94',
                                 'datetime': '2024-03-15 15:59:00',
                                 'high': '48.96',
                                 'low': '48.91',
                                 'open': '48.94',
                                 'previous_close': '48.94',
                                 'volume': '1204404'}]},
            'CVX': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'CVX',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '155.62',
                                'datetime': '2024-03-15 15:59:00',
                                'high': '155.79',
                                'low': '155.24',
                                'open': '155.24',
                                'previous_close': '155.24',
                                'volume': '340962'}]},
            'DIS': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'DIS',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '111.96',
                                'datetime': '2024-03-15 15:59:00',
                                'high': '112.04',
                                'low': '111.83',
                                'open': '111.92',
                                'previous_close': '111.92',
                                'volume': '329240'}]},
            'DJI': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'DJI',
                             'type': 'Index'},
                    'status': 'ok',
                    'values': [{'close': '38720.53',
                                'datetime': '2024-03-15 15:59:00',
                                'high': '38720.53',
                                'low': '38679.13',
                                'open': '38679.87',
                                'previous_close': '38678.65',
                                'volume': '12946971'}]},
            'DOW': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'DOW',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '57.04',
                                'datetime': '2024-03-15 15:59:00',
                                'high': '57.05',
                                'low': '56.96',
                                'open': '57.00',
                                'previous_close': '56.99',
                                'volume': '464543'}]},
            'GS': {'meta': {'currency': 'USD',
                            'exchange': 'NYSE',
                            'exchange_timezone': 'America/New_York',
                            'interval': '1min',
                            'mic_code': 'XNYS',
                            'symbol': 'GS',
                            'type': 'Common Stock'},
                   'status': 'ok',
                   'values': [{'close': '387.22',
                               'datetime': '2024-03-15 15:59:00',
                               'high': '387.34',
                               'low': '386.75',
                               'open': '386.78',
                               'previous_close': '386.74',
                               'volume': '56273'}]},
            'HD': {'meta': {'currency': 'USD',
                            'exchange': 'NYSE',
                            'exchange_timezone': 'America/New_York',
                            'interval': '1min',
                            'mic_code': 'XNYS',
                            'symbol': 'HD',
                            'type': 'Common Stock'},
                   'status': 'ok',
                   'values': [{'close': '373.36',
                               'datetime': '2024-03-15 15:59:00',
                               'high': '373.51',
                               'low': '372.86',
                               'open': '372.87',
                               'previous_close': '372.87',
                               'volume': '80339'}]},
            'HON': {'meta': {'currency': 'USD',
                             'exchange': 'NASDAQ',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNGS',
                             'symbol': 'HON',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '197.68',
                                'datetime': '2024-03-15 15:59:00',
                                'high': '197.73',
                                'low': '197.59',
                                'open': '197.60',
                                'previous_close': '197.59',
                                'volume': '72018'}]},
            'IBM': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'IBM',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '191.09',
                                'datetime': '2024-03-15 15:59:00',
                                'high': '191.10',
                                'low': '190.94',
                                'open': '190.94',
                                'previous_close': '190.95',
                                'volume': '114793'}]},
            'INTC': {'meta': {'currency': 'USD',
                              'exchange': 'NASDAQ',
                              'exchange_timezone': 'America/New_York',
                              'interval': '1min',
                              'mic_code': 'XNGS',
                              'symbol': 'INTC',
                              'type': 'Common Stock'},
                     'status': 'ok',
                     'values': [{'close': '42.67',
                                 'datetime': '2024-03-15 15:59:00',
                                 'high': '42.69',
                                 'low': '42.63',
                                 'open': '42.65',
                                 'previous_close': '42.65',
                                 'volume': '940553'}]},
            'JNJ': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'JNJ',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '158.19',
                                'datetime': '2024-03-15 15:59:00',
                                'high': '158.22',
                                'low': '157.91',
                                'open': '157.91',
                                'previous_close': '157.93',
                                'volume': '327558'}]},
            'JPM': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'JPM',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '190.46',
                                'datetime': '2024-03-15 15:59:00',
                                'high': '190.58',
                                'low': '190.19',
                                'open': '190.20',
                                'previous_close': '190.20',
                                'volume': '319130'}]},
            'KO': {'meta': {'currency': 'USD',
                            'exchange': 'NYSE',
                            'exchange_timezone': 'America/New_York',
                            'interval': '1min',
                            'mic_code': 'XNYS',
                            'symbol': 'KO',
                            'type': 'Common Stock'},
                   'status': 'ok',
                   'values': [{'close': '59.88',
                               'datetime': '2024-03-15 15:59:00',
                               'high': '59.94',
                               'low': '59.64',
                               'open': '59.70',
                               'previous_close': '59.69',
                               'volume': '1226741'}]},
            'MCD': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'MCD',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '279.13',
                                'datetime': '2024-03-15 15:59:00',
                                'high': '279.14',
                                'low': '278.82',
                                'open': '278.91',
                                'previous_close': '278.92',
                                'volume': '58507'}]},
            'MMM': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'MMM',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '105.01',
                                'datetime': '2024-03-15 15:59:00',
                                'high': '105.11',
                                'low': '104.89',
                                'open': '104.92',
                                'previous_close': '104.91',
                                'volume': '337581'}]},
            'MRK': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'MRK',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '121.57',
                                'datetime': '2024-03-15 15:59:00',
                                'high': '121.79',
                                'low': '121.06',
                                'open': '121.56',
                                'previous_close': '121.54',
                                'volume': '555177'}]},
            'MSFT': {'meta': {'currency': 'USD',
                              'exchange': 'NASDAQ',
                              'exchange_timezone': 'America/New_York',
                              'interval': '1min',
                              'mic_code': 'XNGS',
                              'symbol': 'MSFT',
                              'type': 'Common Stock'},
                     'status': 'ok',
                     'values': [{'close': '416.42',
                                 'datetime': '2024-03-15 15:59:00',
                                 'high': '416.66',
                                 'low': '416.26',
                                 'open': '416.29',
                                 'previous_close': '416.29',
                                 'volume': '416188'}]},
            'NKE': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'NKE',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '99.67',
                                'datetime': '2024-03-15 15:59:00',
                                'high': '99.69',
                                'low': '99.49',
                                'open': '99.49',
                                'previous_close': '99.50',
                                'volume': '206816'}]},
            'PG': {'meta': {'currency': 'USD',
                            'exchange': 'NYSE',
                            'exchange_timezone': 'America/New_York',
                            'interval': '1min',
                            'mic_code': 'XNYS',
                            'symbol': 'PG',
                            'type': 'Common Stock'},
                   'status': 'ok',
                   'values': [{'close': '161.38',
                               'datetime': '2024-03-15 15:59:00',
                               'high': '161.50',
                               'low': '161.18',
                               'open': '161.19',
                               'previous_close': '161.18',
                               'volume': '255616'}]},
            'TRV': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'TRV',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '220.92',
                                'datetime': '2024-03-15 15:59:00',
                                'high': '220.95',
                                'low': '220.64',
                                'open': '220.73',
                                'previous_close': '220.71',
                                'volume': '43585'}]},
            'UNH': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'UNH',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '490.81',
                                'datetime': '2024-03-15 15:59:00',
                                'high': '491.15',
                                'low': '490.16',
                                'open': '490.16',
                                'previous_close': '490.14',
                                'volume': '122025'}]},
            'V': {'meta': {'currency': 'USD',
                           'exchange': 'NYSE',
                           'exchange_timezone': 'America/New_York',
                           'interval': '1min',
                           'mic_code': 'XNYS',
                           'symbol': 'V',
                           'type': 'Common Stock'},
                  'status': 'ok',
                  'values': [{'close': '283.08',
                              'datetime': '2024-03-15 15:59:00',
                              'high': '283.08',
                              'low': '282.78',
                              'open': '282.90',
                              'previous_close': '282.90',
                              'volume': '127654'}]},
            'VZ': {'meta': {'currency': 'USD',
                            'exchange': 'NYSE',
                            'exchange_timezone': 'America/New_York',
                            'interval': '1min',
                            'mic_code': 'XNYS',
                            'symbol': 'VZ',
                            'type': 'Common Stock'},
                   'status': 'ok',
                   'values': [{'close': '39.49',
                               'datetime': '2024-03-15 15:59:00',
                               'high': '39.58',
                               'low': '39.47',
                               'open': '39.51',
                               'previous_close': '39.52',
                               'volume': '940557'}]},
            'WBA': {'meta': {'currency': 'USD',
                             'exchange': 'NASDAQ',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNGS',
                             'symbol': 'WBA',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '20.82',
                                'datetime': '2024-03-15 15:59:00',
                                'high': '20.84',
                                'low': '20.81',
                                'open': '20.82',
                                'previous_close': '20.82',
                                'volume': '201009'}]},
            'WMT': {'meta': {'currency': 'USD',
                             'exchange': 'NYSE',
                             'exchange_timezone': 'America/New_York',
                             'interval': '1min',
                             'mic_code': 'XNYS',
                             'symbol': 'WMT',
                             'type': 'Common Stock'},
                    'status': 'ok',
                    'values': [{'close': '60.70',
                                'datetime': '2024-03-15 15:59:00',
                                'high': '60.72',
                                'low': '60.61',
                                'open': '60.61',
                                'previous_close': '60.61',
                                'volume': '508118'}]}}}

def cronny():
    Cronny.objects.create(symbol="crone good")
    
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
        # pprint.pprint(res)
        if res["status_code"] == 200:
            stocks = res["stocks"]
            current_datetime = stocks[Company.DOW_JONES]["values"][0][
                "datetime"
            ]
            if current_datetime == cache.get("last_datetime"):
                return False
            print(current_datetime, cache.get("last_datetime"))
            cache.set("last_datetime", current_datetime, timeout=None)
            con.rpush("last_200", str(current_datetime))
            con.ltrim("last_200", -200, -1)

            stock_items = create_stocks(stocks)
            stocks_list = stock_items["stocks_list"]
            
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

            if stocks_list:
                Stock.objects.bulk_create(stocks_list)
            if strikes_list:
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
                Combination.objects.bulk_create(strikes_list)

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
