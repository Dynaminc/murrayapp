from django.shortcuts import render
from django.http import JsonResponse

from rest_framework.decorators import api_view

from django.core.paginator import Paginator
from django_redis import get_redis_connection
from .cronjob import store, cronny
from securities.models import Stock
from .models import Combination
from datetime import datetime 
import pprint
con = get_redis_connection("default")

def index(request):
    return render(request, "securities/ranks.html")


@api_view(['GET', 'POST'])
def clean_end(request):
    data = Combination.objects.all()
    data.delete()
    return JsonResponse({'message':"Deleted Succesfully"})    

@api_view(['GET', 'POST'])
def test_end(request):
    combs = []
    
    try:
        latest_data = Combination.objects.latest('date_time')
        if latest_data:
            latest_time = str(latest_data.date_time).split('.')[0].split(':')[:-1]
            combs = [{'symbol':item.symbol,'stdev':item.stdev,'score':item.z_score,'date':str(datetime.now()).split('.')[0]} for item in Combination.objects.all() if str(item.date_time).split('.')[0].split(':')[:-1] ==  latest_time]
            combs.sort(key=lambda x: x['score'], reverse=True)
            return JsonResponse({"top_5": combs[:5], "low_5":combs[-5:]})
        else:
            return JsonResponse({"top_5": combs[:5], "low_5":combs[-5:]})
    except Exception as E:
        return JsonResponse({"top_5": combs[:5], "low_5":combs[-5:], 'error':str(E)})
    
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
