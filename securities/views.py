from django.shortcuts import render
from django.http import JsonResponse

from rest_framework.decorators import api_view

from django.core.paginator import Paginator
from django_redis import get_redis_connection
from .cronjob import store, cronny
from securities.models import Stock
from .models import Combination
from datetime import datetime, time
import pprint
con = get_redis_connection("default")
info = {'previous_time': None, 'latest_time': None}
def index(request):
    return render(request, "securities/ranks.html")


@api_view(['GET', 'POST'])
def clean_end(request):
    data = Combination.objects.all()
    data.delete()
    return JsonResponse({'message':"Deleted Succesfully"})    

def check_market_hours(dt):
    if dt.weekday() >= 5:  # Weekend
        return "slate"
    elif dt.weekday() < 5 and (dt.time() < time(9, 30) or dt.time() > time(16, 0)):  # Weekday before 9:30 or after 4:00
        return "slate"
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
        return "slate"
    
@api_view(['GET', 'POST'])
def test_end(request):
    # store()
    combs = []
    market_state = "off"
    try:
        if not info['previous_time']:
            
            ad = Combination.objects.latest('date_time')
            info['previous_time'] = ad.date_time.replace(second=0, microsecond=0)
            print('setting the prvious time', )
            current_time = ad.date_time
            market_state = "slate"
            
        else:
            ad = Combination.objects.latest('date_time')
            info['latest_time'] = ad.date_time.replace(second=0, microsecond=0)
            print('previos time existing', info['previous_time'], info['latest_time'])
            if info['latest_time'] == info['previous_time']:
                current_time = ad.date_time
                market_state = "slate"
                
            else:
                print('previous time existing', info['latest_time'], info['previous_time'])
                current_time = datetime.now()
                info['previous_time'] = info['latest_time']
                market_state = "green"
                
            
        
        market_state = check_market_hours(current_time)
        current_time = str(current_time).split('.')[0]
        latest_data = info['latest_time']
        if latest_data:
            latest_time = latest_data
            filtered_combinations = Combination.objects.filter(date_time__hour=latest_time.hour, date_time__minute=latest_time.minute)
            combs = [{'symbol':item.symbol,'stdev':item.stdev,'score':item.z_score,'date':current_time} for item in filtered_combinations]
            combs.sort(key=lambda x: x['score'], reverse=True)
            return JsonResponse({"top_5": combs[:5], "low_5":combs[-5:], "market": market_state})
        else:
            return JsonResponse({"top_5": combs[:5], "low_5":combs[-5:], "market": market_state})
    except Exception as E:
        return JsonResponse({"top_5": combs[:5], "low_5":combs[-5:], "market": "error", 'error':str(E)})
    
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
