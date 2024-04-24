from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from django.core.paginator import Paginator
from rest_framework import status
from django.db.models import F, Q
from django_redis import get_redis_connection
from django.utils import timezone as tz
from securities.models import Stock
from .models import Combination
from accounts.models import Strike, Profile, Transaction, Notification, tran_not_type
from accounts.serializer import StrikeSerializer, ProfileSerializer, TransactionSerializer, NotificationSerializer
from datetime import datetime, time, timedelta
import pytz
import pprint, random
from .utils import quick_run
from .cronjob import new_calc, clean_comb
from .serializer import *   
from .assess import get_test_data, json_migrator, all_strikes, export_file, top_low

con = get_redis_connection("default")
info = {'previous_time': None, 'latest_time': None}
def index(request):
    return render(request, "securities/ranks.html")


def quantify_strike(portfolio, price):
    unit_portfolio_size = 1000000 / 50
    quantity = unit_portfolio_size / price
    final_portfolio_size = int(quantity) * price
    
    return {'unit':unit_portfolio_size, 'quantity': int(quantity), 'final':final_portfolio_size}

def process_strike_symbol(symbol):
    split_symbol = symbol.split('-')
    portfolio = Profile.objects.first().porfolio
    data = []
    for item in split_symbol:
        price = Stock.objects.filter(symbol=item).latest('date_time').close
        # price = Stock.objects.filter(symbol=item).first().close
        portfolio_data = quantify_strike(portfolio, price)
        data.append({"title": item, "price": price, 'quantity': portfolio_data['quantity'], 'final': portfolio_data['final']})
    return data

def get_correct_close(array, title):
    data = [item for item in array if item['title'] == title][0]
    return data

@api_view(['GET','POST'])
def get_chart(request):
    id = request.GET.get('id', "")
    strike_instance = Strike.objects.filter(id=id).first() 
    short = strike_instance.short_symbol
    long = strike_instance.long_symbol
    
    shorts = Combination.objects.filter(symbol=short, date_time__gt=strike_instance.open_time)
    longs = Combination.objects.filter(symbol=long, date_time__gt=strike_instance.open_time)

  
    data = [
        {
            'time': comb.date_time,
            'svalue': comb.z_score,
            'lvalue': [item for item in longs if item.date_time == comb.date_time][0].z_score
        }
        for comb in shorts
    ]   
    strike_instance = Strike.objects.filter(id=id).first() 
    short = strike_instance.short_symbol
    long = strike_instance.long_symbol

    data = [{'time':comb.date_time, 'svalue': comb.z_score, 'lvalue': Combination.objects.filter(symbol=long).filter(date_time=comb.date_time).first().z_score } for comb in Combination.objects.filter(symbol=short) if comb.date_time > strike_instance.open_time]
    
    for item in data:
        item["time"] = datetime.fromisoformat(str(item["time"]))

    # Get the start and current time
    if len(data) < 1:
        return JsonResponse({ 'message':"Chart loaded Succesfully", "data":[]})
        
    start_time = data[0]["time"]
    current_time = datetime.now()

    # Fill in missing data points
    new_data = []
    prev_item = None
    for i in range((current_time - start_time).seconds // 60):
        new_time = start_time + timedelta(minutes=i)
        eastern = pytz.timezone('US/Eastern')
        dt = eastern.localize(new_time)
        if dt.weekday() < 5 and (dt.time() >= time(9, 30) and dt.time() <= time(16, 0)):
            for item in data:
                if item["time"] <= new_time:
                    prev_item = item
            new_data.append({
                "time": new_time,
                "svalue": prev_item["svalue"],
                "lvalue": prev_item["lvalue"] 
            })        
        
    for item in new_data:
        item["time"] = item["time"].isoformat()

    for item in new_data:
        print(item)  
    return JsonResponse({ 'message':"Chart loaded Succesfully", "data":new_data})
    # return JsonResponse({ 'message':"Chart loaded Succesfully", "data":data})

@api_view(['GET'])
def load_strikes(request):
    data = [StrikeSerializer(strike).data for strike in Strike.objects.all()]
    return JsonResponse({ 'message':"Strike Loaded Succesfully", "data":data})

@api_view(['GET'])
def update_striker(request):
    
    id = request.GET.get('id', '0')
    strike_instance = Strike.objects.filter(id=id).first() 
    if not strike_instance:
        return JsonResponse({ 'message':"strike not found"})
        
    if not strike_instance.closed:
        long = strike_instance.long_symbol
        short = strike_instance.short_symbol
        
        long_data = process_strike_symbol(long)
        short_data = process_strike_symbol(short)
        
        sum_total = 0
        sum_total += sum([item['final'] for item in long_data])
        sum_total += sum([item['final'] for item in short_data])
        
        strike_instance.current_price = sum_total
        strike_instance.current_percentage = (sum_total - strike_instance.total_open_price)/strike_instance.total_open_price * 100
        
        # strike_instance.max_percentage = strike_instance.current_percentage if strike_instance.current_percentage > strike_instance.max_percentage else strike_instance.max_percentage
        # strike_instance.min_percentage = strike_instance.current_percentage if strike_instance.current_percentage < strike_instance.min_percentage else strike_instance.min_percentage
        
        strike_instance.fls_close = get_correct_close(long_data, strike_instance.first_long_stock)['price']
        strike_instance.fls_close_price = get_correct_close(long_data, strike_instance.first_long_stock)['final']
        strike_instance.sls_close = get_correct_close(long_data, strike_instance.second_long_stock)['price']
        strike_instance.sls_close_price = get_correct_close(long_data, strike_instance.second_long_stock)['final']                
        strike_instance.tls_close = get_correct_close(long_data, strike_instance.third_long_stock)['price']
        strike_instance.tls_close_price = get_correct_close(long_data, strike_instance.third_long_stock)['final']                

        strike_instance.fss_close = get_correct_close(short_data, strike_instance.first_short_stock)['price']
        strike_instance.fss_close_price = get_correct_close(short_data, strike_instance.first_short_stock)['final']
        strike_instance.sss_close = get_correct_close(short_data, strike_instance.second_short_stock)['price']
        strike_instance.sss_close_price = get_correct_close(short_data, strike_instance.second_short_stock)['final']                
        strike_instance.tss_close = get_correct_close(short_data, strike_instance.third_short_stock)['price']
        strike_instance.tss_close_price = get_correct_close(short_data, strike_instance.third_short_stock)['final']             
        # process for exit signal             
        #signal_exit = models.BooleanField(default=False
                
        strike_instance.save()
        
        return JsonResponse({ 'message':"Trade loaded", "data":StrikeSerializer(strike_instance).data})
    else:
        return JsonResponse({ 'message':"Trade closed", "data":StrikeSerializer(strike_instance).data})

def update_strike(id):
    
    strike_instance = Strike.objects.filter(id=id).first() 
    if not strike_instance:
        return False
    if not strike_instance.closed:
        long = strike_instance.long_symbol
        short = strike_instance.short_symbol
        
        long_data = process_strike_symbol(long)
        short_data = process_strike_symbol(short)
        
        sum_total = 0
        sum_total += sum([item['final'] for item in long_data])
        sum_total += sum([item['final'] for item in short_data])
        
        strike_instance.current_price = sum_total
        strike_instance.current_percentage = (sum_total - strike_instance.total_open_price)/strike_instance.total_open_price * 100
        
        strike_instance.max_percentage = strike_instance.current_percentage if strike_instance.current_percentage > strike_instance.max_percentage else strike_instance.max_percentage
        strike_instance.min_percentage = strike_instance.current_percentage if strike_instance.current_percentage < strike_instance.min_percentage else strike_instance.min_percentage
        
        strike_instance.fls_close = get_correct_close(long_data, strike_instance.first_long_stock)['price']
        strike_instance.fls_close_price = get_correct_close(long_data, strike_instance.first_long_stock)['final']
        strike_instance.sls_close = get_correct_close(long_data, strike_instance.second_long_stock)['price']
        strike_instance.sls_close_price = get_correct_close(long_data, strike_instance.second_long_stock)['final']                
        strike_instance.tls_close = get_correct_close(long_data, strike_instance.third_long_stock)['price']
        strike_instance.tls_close_price = get_correct_close(long_data, strike_instance.third_long_stock)['final']                

        strike_instance.fss_close = get_correct_close(short_data, strike_instance.first_short_stock)['price']
        strike_instance.fss_close_price = get_correct_close(short_data, strike_instance.first_short_stock)['final']
        strike_instance.sss_close = get_correct_close(short_data, strike_instance.second_short_stock)['price']
        strike_instance.sss_close_price = get_correct_close(short_data, strike_instance.second_short_stock)['final']                
        strike_instance.tss_close = get_correct_close(short_data, strike_instance.third_short_stock)['price']
        strike_instance.tss_close_price = get_correct_close(short_data, strike_instance.third_short_stock)['final']             
        
        # process for exit signal             
        if strike_instance.current_percentage > 1.5 and not strike_instance.signal_exit:
            strike_instance.signal_exit = True
            Notification.objects.create(user=strike_instance.user, details=f"Strike has exceeded the {strike_instance.current_percentage}% mark", strike_id=strike_instance.id, notification_type=tran_not_type.EXIT_ALERT)   
        else:
            detail = f"Strike has exceeded the {strike_instance.current_percentage}% mark"
            if strike_instance.current_percentage > 1: 
                
                if not Notification.objects.filter(strike_id=strike_instance.id).filter(details=detail).first():
                    Notification.objects.create(user=strike_instance.user, details=detail, strike_id=strike_instance.id, notification_type=tran_not_type.CUSTOM)   
            if strike_instance.current_percentage < - 1:
                if not Notification.objects.filter(strike_id=strike_instance.id).filter(details=detail).first():
                    Notification.objects.create(user=strike_instance.user, details=detail, strike_id=strike_instance.id, notification_type=tran_not_type.CUSTOM)                       
            if strike_instance.current_percentage < - 1.5:
                if not Notification.objects.filter(strike_id=strike_instance.id).filter(details=detail).first():
                    Notification.objects.create(user=strike_instance.user, details=detail, strike_id=strike_instance.id, notification_type=tran_not_type.CUSTOM)                     
        strike_instance.save()
        
                
    return True

@api_view(['GET'])
def cronat(response):
    data = [ update_strike(item.id) for item in Strike.objects.filter(closed=False)]
    if False in data:
        Cronny.objects.create(symbol=f"{len(data)}: False")
    else:
        Cronny.objects.create(symbol=f"{len(data)}: True")
    return JsonResponse({'message': f'Updated', 'status': 400}, 
                                status=status.HTTP_200_OK)        
@api_view(['GET'])
def close_strike(request):
    id = request.GET.get('strike_id', 10)
    
    close_time = str(Stock.objects.latest('date_time').date_time)
    
    strike_instance = Strike.objects.filter(id=id).first() 
    if not strike_instance:
        return JsonResponse({ 'message':"Strike not found"}, status=status.HTTP_400_BAD_REQUEST)     
    if not strike_instance.closed:
        long = strike_instance.long_symbol
        short = strike_instance.short_symbol
        
        long_data = process_strike_symbol(long)
        short_data = process_strike_symbol(short)
        
        stock_time = Stock.objects.latest('date_time').date_time
        
        sum_total = 0
        sum_total += sum([item['final'] for item in long_data])
        sum_total += sum([item['final'] for item in short_data])
        
        
        strike_instance.total_close_price = sum_total
        strike_instance.close_time = stock_time
        strike_instance.fls_close = get_correct_close(long_data, strike_instance.first_long_stock)['price']
        strike_instance.fls_close_price = get_correct_close(long_data, strike_instance.first_long_stock)['final']
        strike_instance.sls_close = get_correct_close(long_data, strike_instance.second_long_stock)['price']
        strike_instance.sls_close_price = get_correct_close(long_data, strike_instance.second_long_stock)['final']                
        strike_instance.tls_close = get_correct_close(long_data, strike_instance.third_long_stock)['price']
        strike_instance.tls_close_price = get_correct_close(long_data, strike_instance.third_long_stock)['final']                

        strike_instance.fss_close = get_correct_close(short_data, strike_instance.first_short_stock)['price']
        strike_instance.fss_close_price = get_correct_close(short_data, strike_instance.first_short_stock)['final']
        strike_instance.sss_close = get_correct_close(short_data, strike_instance.second_short_stock)['price']
        strike_instance.sss_close_price = get_correct_close(short_data, strike_instance.second_short_stock)['final']                
        strike_instance.tss_close = get_correct_close(short_data, strike_instance.third_short_stock)['price']
        strike_instance.tss_close_price = get_correct_close(short_data, strike_instance.third_short_stock)['final']     
        strike_instance.closed = True
        
        strike_instance.save()

        profile_instance = Profile.objects.first()
        previous_balance = profile_instance.porfolio
        profile_instance.porfolio = previous_balance  + sum_total
        profile_instance.save()
        
        Transaction.objects.create(user=strike_instance.user, details=f'Your order has been closed for strike {strike_instance.long_symbol}/{strike_instance.short_symbol}', strike_id=strike_instance.id, previous_balance=previous_balance, new_balance=profile_instance.porfolio, amount=sum_total, transaction_type=tran_not_type.TRADE_CLOSED)       
        
        # previous_balance = profile_instance.porfolio
        # profile_instance.porfolio = previous_balance  - 10
        # profile_instance.save()
        
        # Transaction.objects.create(user=strike_instance.user, details=f"Broker's Commission for Strike:{strike_instance.long_symbol}/{strike_instance.short_symbol}", previous_balance=previous_balance, new_balance=profile_instance.porfolio, credit=False, amount=10, transaction_type=tran_not_type.COMMISSON_FEE)       
        Notification.objects.create(user=strike_instance.user, details=f"Strike {strike_instance.id} has been closed", strike_id=strike_instance.id, notification_type=tran_not_type.TRADE_CLOSED)   
        
        return JsonResponse({ 'message':"Trade Closed Succesfully", "data":StrikeSerializer(strike_instance).data})
    else:
        return JsonResponse({ 'message':"Trade Closed Already", "data":StrikeSerializer(strike_instance).data})



@api_view(['POST'])
def confirm_strike(request):
    serializer = StrikeManagementSerializer(data=request.POST)
    if not serializer.is_valid():
        return JsonResponse({'message': f'{serializer.errors}', 'status': 400}, 
                                status=status.HTTP_400_BAD_REQUEST)
        
    serialized = serializer.data
    short = serialized['short'] 
    long = serialized['long'] 
    stock_time = Stock.objects.latest('date_time').date_time

    long_data = process_strike_symbol(long)
    short_data = process_strike_symbol(short)
    
    sum_total = 0
    sum_total += sum([item['final'] for item in long_data])
    sum_total += sum([item['final'] for item in short_data])
    
    strike_instance = Strike.objects.create( 
            user = Profile.objects.first().user,
            long_symbol = long,
            short_symbol = short,
            total_open_price = sum_total,
            open_time = stock_time,
            current_price = sum_total,
            
            first_long_stock = long_data[0]['title'],
            fls_quantity = long_data[0]['quantity'],
            fls_price = long_data[0]['final'],
            fls_open = long_data[0]['price'],
            
            second_long_stock = long_data[1]['title'],
            sls_quantity = long_data[1]['quantity'],
            sls_price = long_data[1]['final'],
            sls_open = long_data[1]['price'],
            
            third_long_stock = long_data[2]['title'],
            tls_quantity = long_data[2]['quantity'],
            tls_price = long_data[2]['final'],
            tls_open = long_data[2]['price'],
            
            first_short_stock = short_data[0]['title'],
            fss_quantity = short_data[0]['quantity'],
            fss_price = short_data[0]['final'],
            fss_open = short_data[0]['price'],
            
            second_short_stock = short_data[1]['title'],
            sss_quantity = short_data[1]['quantity'],
            sss_price = short_data[1]['final'],
    
            sss_open = short_data[1]['price'],
            
            third_short_stock = short_data[2]['title'],
            tss_quantity = short_data[2]['quantity'],
            tss_price = short_data[2]['final'],
            tss_open = short_data[2]['price'],
            )
    
    profile_instance = Profile.objects.first()
    previous_balance = profile_instance.porfolio 
    profile_instance.porfolio = previous_balance - sum_total
    profile_instance.save()
    
    Transaction.objects.create(user=profile_instance.user, details=f'Your order has been placed for strike {strike_instance.long_symbol}/{strike_instance.short_symbol}', strike_id=strike_instance.id, previous_balance=previous_balance, new_balance=profile_instance.porfolio, credit=False, amount=sum_total, transaction_type=tran_not_type.TRADE_OPENED)

    # previous_balance = profile_instance.porfolio
    # profile_instance.porfolio = previous_balance  - 10
    # profile_instance.save()
    
    # Transaction.objects.create(user=strike_instance.user, details=f"Broker's Commission for Strike:{strike_instance.long_symbol}/{strike_instance.short_symbol}", previous_balance=previous_balance, new_balance=profile_instance.porfolio, credit=False, amount=10, transaction_type=tran_not_type.COMMISSON_FEE)       
            
    Notification.objects.create(user=strike_instance.user, details=f"Trade {strike_instance.id} has been opened", strike_id=strike_instance.id, notification_type=tran_not_type.TRADE_OPENED)   
    return JsonResponse({ 'message':"Strike Saved Succesfully", "data":StrikeSerializer(strike_instance).data})


@api_view(['POST'])
def add_fund(request):
    try:
        serializer = FundSerializer(data=request.POST)
        if not serializer.is_valid():
            return JsonResponse({'message': f'{serializer.errors}', 'status': 400}, 
                                    status=status.HTTP_400_BAD_REQUEST)
            
        serialized = serializer.data
        fund = int(serialized['fund'])
        
        profile_instance = Profile.objects.first()
        previous_balance = profile_instance.porfolio 
        profile_instance.porfolio = previous_balance + fund
        profile_instance.save()
        
        Transaction.objects.create(user=profile_instance.user,  details=f"Wallet has been funded",
                                new_balance=profile_instance.porfolio, 
                                credit=True, amount=fund, transaction_type=tran_not_type.WALLET_FUNDED)
        Notification.objects.create(user=profile_instance.user, details=f"Wallet has been funded with {fund}", notification_type=tran_not_type.WALLET_FUNDED)   
        
        return JsonResponse({'message':"Fund added Succesfully"})  
    except:
        return JsonResponse({'message':"Fund not added"})  

@api_view(['GET'])
def load_transactions(request):
    data = {}
    profile_instance = Profile.objects.first()
    transaction_instances = Transaction.objects.filter(user=profile_instance.user).all()
    data = [TransactionSerializer(item).data for item in transaction_instances]
    return JsonResponse({'data':data , 'message':"Trnasactions Loaded"})  

@api_view(['GET'])
def load_notifications(request):
    data = {}
    profile_instance = Profile.objects.first()
    notification_instances = Notification.objects.filter(user=profile_instance.user).all()
    data = [NotificationSerializer(item).data for item in notification_instances]
    return JsonResponse({'data':data , 'message':"Notifations Loaded"})  

@api_view(['GET'])
def load_stats(request):
    data = {}
    profile_instance = Profile.objects.first()
    for key, value in ProfileSerializer(profile_instance).data.items():
        data[key] = value
        
    strikes = Strike.objects.filter(user=profile_instance.user).all()
    profit_trades = [(strike.total_close_price - strike.total_open_price) for strike in strikes if strike.closed and strike.total_close_price > strike.total_open_price]
    data['total_profits'] = sum(profit_trades)
    data['win_rate'] =  0
    
    if len(strikes) > 0:
        data['win_rate'] = len(profit_trades) / len(strikes) * 10
        
    
    data['total_loss'] = sum([(strike.total_open_price - strike.total_close_price  ) for strike in strikes if strike.closed and strike.total_close_price < strike.total_open_price])
    
    data['operating_balance'] = sum([strike.total_close_price if strike.total_close_price else 0 for strike in strikes if not strike.closed ]) 
    
    open_prices = sum([strike.total_open_price if strike.total_open_price else 0  for strike in strikes if not strike.closed ])
    close_prices = sum([strike.total_close_price if strike.total_close_price else 0   for strike in strikes if not strike.closed ])
    
    data['operating_percent'] = 0
    data['cent_color'] = 'gray'
    if open_prices > 0:
        data['operating_percent'] = (close_prices - open_prices) / open_prices * 100
        if data['operating_percent'] > 0:
            data['cent_color'] = 'green'
        else:
            data['cent_color'] = 'red'
    
    data['total_trades'] = len(strikes)
    
    data['open_trades'] = len([strike for strike in strikes if not strike.closed])
    data['closed_trades'] = len([strike for strike in strikes if strike.closed])
    
    data['exit_alerts'] = len([strikes for strike in strikes if strike.signal_exit])
    return JsonResponse({'data':data , 'message':"Loaded Succesfully"})  

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
    
    
    return JsonResponse({'data':data, 'message':"Loaded Succesfully"})  



@api_view(['GET', 'POST'])
def trigger_store(request):
    print("initiated")    
    # data = clean_comb()
    # print("Fetching")
    # data = get_test_data()
    # print("Migrating")
    # json_migrator()
    # print("Getting all strikes ")
    # data = all_strikes()
    # print("Completed strikes")
    
    
    # data = new_calc()
    
    print("Exporting")
    # data = export_file()
    # now to export the last minute ranking
    
    # data = new_calc()
    
    data = top_low()
    
    print("Exported") 
    return JsonResponse({'message':"Loaded Succesfully", 'data': data})  

            

        
@api_view(['GET', 'POST'])
def trigger_lens(request):
    item = datetime(2024, 4, 19, 12)
    
    combination_data = Combination.objects.filter(date_time__gte=item).all()
    stock_data = Stock.objects.filter(date_time__gte=item).all()
    return JsonResponse({'message':"Loaded Succesfully",'combs':len(combination_data), 'stocks': len(stock_data)})  
    
@api_view(['GET', 'POST'])
def clean_end(request):
    try:
        print('cleaning')
        id = int(request.GET.get('id', 10))
        delete = request.GET.get('delete',False)
        d = tz.now() - timedelta(days=id)
        print(d)
        count = 0
        paginator = Paginator(Combination.objects.filter(date_time__lt=d), 1000) # chunks of 1000
        print('paginated')
        for page_idx in range(1, paginator.num_pages):
            for row in paginator.page(page_idx).object_list:
                if delete:  
                    count += 1
                    print('deleteded, ', count, row.date_time)
                    row.delete()
        return JsonResponse({'message':f"Deleted Succesfully {count}"})    
    except Exception as E:
        return JsonResponse({'message':f"Exception {E}"})    
    
    
    

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
    combs = []
    market_state = "off"
    try:
        market_state = check_market_hours(datetime.now())
        if not info['previous_time']:
            ad = Combination.objects.latest('date_time')
            info['previous_time'] = ad.date_time.replace(second=0, microsecond=0)
            info['latest_time'] = ad.date_time.replace(second=0, microsecond=0)
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
        # display_time = datetime.now()
        current_time = str(display_time).split('.')[0]
        
        eastern = pytz.timezone('US/Eastern')
        dt = eastern.localize(datetime.now())
        if dt.weekday() < 5 and (dt.time() >= time(9, 30) and dt.time() <= time(16, 0)):
            display_time = datetime.now()
            current_time = str(display_time).split('.')[0]
            
        latest_data = info['latest_time']
        print(latest_data, 'latest')
        if latest_data:
            latest_time = latest_data
            print(latest_time, current_time)
            filtered_combinations = Combination.objects.filter(date_time = latest_time )
            print(len(filtered_combinations))
            combs = [{'symbol':item.symbol,'stdev':item.stdev,'score':item.z_score,'date':str(latest_time)} for item in filtered_combinations if item.z_score]
            combs.sort(key=lambda x: x['score'], reverse=True)
            return JsonResponse({"top_5": combs[:5], "low_5":combs[-5:], "market": market_state})
        else:
            
            return JsonResponse({"top_5": combs[:5], "low_5":combs[-5:], "market": market_state})
    except Exception as E:
        return JsonResponse({"top_5": combs[:5], "low_5":combs[-5:], "market": "red", 'error':str(E)})
    
def stocks(request):
    combo = Combination.objects.filter(symbol__icontains='CSCO')
    print(len(combo))
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
