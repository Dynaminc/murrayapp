from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework import status
from django.core.paginator import Paginator
from django_redis import get_redis_connection
from django.utils import timezone as tz
from .cronjob import store, cronny
from securities.models import Stock
from .models import Combination
from accounts.models import Profile
from datetime import datetime, time, timedelta
import pytz
import pprint
from .serializer import *
con = get_redis_connection("default")
info = {'previous_time': None, 'latest_time': None}
def index(request):
    return render(request, "securities/ranks.html")


def quantify_strike(portfolio, price):
    unit_portfolio_size = portfolio / 50
    quantity = unit_portfolio_size / price
    final_portfolio_size = int(quantity) * price
    return {'unit':unit_portfolio_size, 'quantity': int(quantity), 'final':final_portfolio_size}

def process_strike_symbol(symbol):
    split_symbol = symbol.split('-')
    portfolio = Profile.objects.first().porfolio
    data = []
    for item in split_symbol:
        price = Stock.objects.filter(symbol=item).first().close
        portfolio_data = quantify_strike(portfolio, price)
        data.append({"title": item, "price": price, 'quantity': portfolio_data['quantity'], 'final': portfolio_data['final']})
    return data

@api_view(['POST'])
def get_strike_breakdown(request):
    serializer = StrikeManagementSerializer(data=request.POST)
    if not serializer.is_valid():
        return JsonResponse({'message': f'{serializer.errors}', 'status': 400}, 
                                status=status.HTTP_400_BAD_REQUEST)
        
    serialized = serializer.data
    short = serialized['short'] 
    long = serialized['long'] 
    stock_time = str(Stock.objects.latest('date_time').date_time)
    
    data = {'stock_time':stock_time, 'portfolio':Profile.objects.first().porfolio, 'shortSymbol':short,'shortData':process_strike_symbol(short), 'longSymbol': long, 'longData': process_strike_symbol(long) }
    pprint.pprint(data)
    
    return JsonResponse({'data':data, 'message':"Loaded Succesfully"})  

@api_view(['GET', 'POST'])
def clean_end(request):
    d = tz.now() - timedelta(days=5)
    data = Combination.objects.filter(date_time__lt=d)
    data.delete()
    return JsonResponse({'message':f"Deleted Succesfully {len(data)}"})    

def check_market_hours(dat):
    eastern = pytz.timezone('US/Eastern')
    dt = eastern.localize(dat)
    print(dt)
    if dt.weekday() >= 5:  # Weekend
        return "red"
    elif dt.weekday() < 5 and (dt.time() < time(9, 30) or dt.time() > time(16, 0)):  # Weekday before 9:30 or after 4:00
        return "red"
    elif dt.time() >= time(9, 30) and dt.time() <= time(9, 45):  # 9:30 to 9:45
        return "yellow"
    elif dt.time() >= time(15, 45) and dt.time() <= time(16, 0):  # 15:45 to 16:00
        return "yellow"
    elif dt.time() >= time(9, 30) and dt.time() <= time(9, 45):  # 9:30 to 9:45
        return "yellow"
    elif dt.time() >= time(15, 45) and dt.time() <= time(16, 0):  # 15:45 to 16:00
        return "yellow"
    elif dt.time() >= time(9, 45) and dt.time() <= time(15, 45):  # 9:45 to 15:45
        return "green"
    else:
        return "red"
    
@api_view(['GET', 'POST'])
def test_end(request):
    # store()
    combs = []
    market_state = "off"
    try:
        market_state = check_market_hours(datetime.now())
        if not info['previous_time']:
            ad = Combination.objects.latest('date_time')
            info['previous_time'] = ad.date_time.replace(second=0, microsecond=0)
            display_time = ad.date_time
            # market_state = "slate"
            
        else:
            ad = Combination.objects.latest('date_time')
            info['latest_time'] = ad.date_time.replace(second=0, microsecond=0)
            
            
            if info['latest_time'] == info['previous_time']:
                display_time = ad.date_time
                # market_state = "slate"
                
            else:
                display_time = datetime.now()
                info['previous_time'] = info['latest_time']

            
        
        
        # print(market_state)
        current_time = str(display_time).split('.')[0]
        latest_data = info['latest_time']
        if latest_data:
            latest_time = latest_data
            filtered_combinations = Combination.objects.filter(date_time__hour=latest_time.hour, date_time__minute=latest_time.minute)
            print(len(filtered_combinations))
            combs = [{'symbol':item.symbol,'stdev':item.stdev,'score':item.z_score,'date':current_time} for item in filtered_combinations if item.stdev and item.z_score]
            combs.sort(key=lambda x: x['score'], reverse=True)
            return JsonResponse({"top_5": combs[:5], "low_5":combs[-5:], "market": market_state})
        else:
            return JsonResponse({"top_5": combs[:5], "low_5":combs[-5:], "market": market_state})
    except Exception as E:
        return JsonResponse({"top_5": combs[:5], "low_5":combs[-5:], "market": "red", 'error':str(E)})
    
def stocks(request):
    combinations = con.get("last_120").decode("utf-8")
    pprint.pprint(combinations)
    stocks_list = con.get("last_30").decode("utf-8")

    return JsonResponse({"stocks": stocks_list, "combinations": combinations})


def get_security_info(request, symbol):
    page_num = request.GET.get("page", 1)
    paginator = Paginator(
        Stock.objects.filter(symbol=symbol).order_by("-id"), 10
    )
    stock_result = paginator.page(page_num).object_list
    stock_info = []
    for stock in stock_result:
        stock_info.append(
            {
                "open": stock.open,
                "close": stock.close,
                "low": stock.low,
                "high": stock.high,
                "previous_close": stock.previous_close,
                "date_time": stock.date_time.strftime("%G-%m-%d %H:%M:%S"),
            }
        )

    return JsonResponse(
        {
            "data": stock_info,
            "num_of_pages": paginator.num_pages,
            "total_items": paginator.count,
        }
    )
