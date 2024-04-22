    
import csv
from django.http import HttpResponse
from datetime import timedelta
import pandas as pd
from django.db.models import F, Q
from django.db.models.functions import ExtractMinute
from .models import Combination
from accounts.models import Strike, Profile, Transaction, Notification, tran_not_type
from accounts.serializer import StrikeSerializer, ProfileSerializer, TransactionSerializer, NotificationSerializer
from datetime import datetime, time, timedelta
import pytz
import pprint, random
from .serializer import *   
from django.http import JsonResponse

def convert_csv_to_excel(respose):
    # Usage example
    csv_file_path = 'spikes.csv'
    excel_file_path = 'spikes.xlsx'
    # convert_csv_to_excel(csv_file_path, excel_file_path)
    
    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_file_path)

    # Convert DataFrame to Excel file
    df.to_excel(excel_file_path, index=False)
    return JsonResponse({'message': 'File converted to Excel successfully'}, status=200)


def get_per_strike():
    strike_instances = Strike.objects.all()
    
    count = 0
    missing = 0
    fixed = 0
    
    for main_item in strike_instances:
        long, short = main_item.long_symbol, main_item.short_symbol
        for combo in [long, short]:
            comba  = combo.split('-')
            m = Combination.objects.filter(symbol=combo, date_time=main_item.open_time).first()
            strike = m.strike
            mean = m.avg
            stdev = m.stdev
            z_score = m.z_score
            # Create a dictionary to store the data
            data_dict = {
                'Strike Price': strike,
                'Mean': mean,
                'Std Deviation': stdev,
                'Z-Score': z_score,
                'date': str(main_item.open_time)
            }

            # Initialize keys for 'AAPL', 'PG', and 'WMT'
            data_dict[comba[0]] = None
            data_dict[comba[1]] = None
            data_dict[comba[2]] = None
            
            next_minute = main_item.open_time + timedelta(minutes=1)


            a = Stock.objects.filter(Q(symbol=comba[0]),date_time=main_item.open_time).first()
            b = Stock.objects.filter(Q(symbol=comba[1]),date_time=main_item.open_time).first()
            c = Stock.objects.filter(Q(symbol=comba[2]),date_time=main_item.open_time).first()
            if a:
                data_dict[comba[0]] = a.close
            else:
                missing += 1
                new_a = Stock.objects.filter(Q(symbol=comba[0]), date_time=next_minute).first()
                if new_a:
                    fixed += 1
                    data_dict[comba[0]] = new_a.close
            if b: 
                data_dict[comba[1]] = b.close
            else:
                missing += 1
                new_b = Stock.objects.filter(Q(symbol=comba[1]), date_time=next_minute).first()
                if new_b:
                    fixed += 1
                    data_dict[comba[1]] = new_b.close
            if c:
                data_dict[comba[2]] = c.close 
            else:
                missing += 1       
                new_c = Stock.objects.filter(Q(symbol=comba[2]), date_time=next_minute).first()
                if new_c:
                    fixed += 1
                    data_dict[comba[2]] = new_c.close                

def get_combination_data_last_200(combination, initial_timestamp):
    # Get the latest timestamp
    comba  = combination.split('-')
    
    # distinct_timestamps = Combination.objects.filter(symbol=combination).order_by('-date_time').values('date_time').distinct()[:200]
    distinct_timestamps = Combination.objects.filter(date_time__gte=initial_timestamp).order_by('-date_time').values('date_time').distinct()
     
    
    # Create a list to store DataFrames for each timestamp
    dfs = []
    print('iterationg')
    count = 0
    
    missing = 0
    fixed = 0
    # Iterate over each distinct timestamp
    for timestamp in distinct_timestamps:
        count += 1
        print(count)
        # Fetch the strike price, mean, std deviation, and z-score for the combination at the current timestamp
        m = Combination.objects.get(symbol=combination, date_time=timestamp['date_time'])
        strike = m.strike
        mean = m.avg
        stdev = m.stdev
        z_score = m.z_score
        # Create a dictionary to store the data
        data_dict = {
            'Strike Price': strike,
            'Mean': mean,
            'Std Deviation': stdev,
            'Z-Score': z_score,
            'date': str(timestamp['date_time'])
        }

        # Initialize keys for 'AAPL', 'PG', and 'WMT'
        data_dict[comba[0]] = None
        data_dict[comba[1]] = None
        data_dict[comba[2]] = None
        
        next_minute = timestamp['date_time'] + timedelta(minutes=1)


        a = Stock.objects.filter(Q(symbol=comba[0]),date_time=timestamp['date_time']).first()
        b = Stock.objects.filter(Q(symbol=comba[1]),date_time=timestamp['date_time']).first()
        c = Stock.objects.filter(Q(symbol=comba[2]),date_time=timestamp['date_time']).first()
        if a:
            data_dict[comba[0]] = a.close
        if b: 
            data_dict[comba[1]] = b.close
        if c:
            data_dict[comba[2]] = c.close 
        df = pd.DataFrame(data_dict, index=[0])
        dfs.append(df)
    print('done', ' missing ', missing, ' fixed ', fixed , ' total ', count)
    # Concatenate all DataFrames into a single DataFrame
    result_df = pd.concat(dfs, ignore_index=True)

    return result_df


def check_empties():
    # Fetch the last 200 Stock records without the close value
    # stocks_without_close = Stock.objects.order_by('-date_time').values('symbol', 'date_time', 'open', 'high', 'low', 'previous_close')[:200]
    stocks_without_close = Stock.objects.filter(Q(close__isnull=True) | Q(close=0)).values('symbol', 'date_time', 'open', 'high', 'low','close', 'previous_close').order_by('-date_time')[:200]
    
    # Print the first few records as an example
    print(len(stocks_without_close))
    for stock in stocks_without_close[:5]:
        print(stock)
    return JsonResponse({"data":stocks_without_close})

def quick_run(combination, initial_timestamp ):
    # Example usage
    df = get_combination_data_last_200(combination, initial_timestamp)

    # Save the DataFrame to an Excel file
    excel_file_path = f'{combination}_data_{str(initial_timestamp)}.xlsx'
    df.to_excel(excel_file_path, index=False)


def export_top_and_bottom_spikes(request):
    print("INititated")
    # Get the latest timestamp
    latest_time = Combination.objects.latest('date_time').date_time

    # Calculate the start time for the last 200 minutes
    start_time = latest_time - timedelta(minutes=200)

    # Fetch unique timestamps within the last 200 minutes
    unique_timestamps = Combination.objects.filter(
        date_time__gte=start_time, date_time__lte=latest_time
    ).values('date_time').distinct()

    # Initialize a list to store all spikes
    all_spikes = []

    # Iterate over each unique timestamp
    print("Iterating")
    for timestamp in unique_timestamps:
        # Fetch combinations for the current timestamp
        filtered_combs = Combination.objects.filter(date_time=timestamp['date_time'])
        combs = [{'symbol':item.symbol,'stdev':item.stdev,'avg':item.avg, 'z_score':item.z_score,'date_time':str(item.date_time)} for item in filtered_combs if item.stdev and item.z_score ]
        combs.sort(key=lambda x: x['z_score'], reverse=True)
        
        # combs = [item for item in filtered_combs  if item.stdev and item.z_score ]
        # combs.sort(key=lambda x: x.z_score, reverse=True)
        
        # Get the top and bottom 5 combinations for the current timestamp
        top_5 = combs[:5] #filtered_combinations.order_by('-stdev')[:5]
        low_5 = combs[-5:]# filtered_combinations.order_by('stdev')[:5]

        # Prepare the response for the current timestamp
        top_spikes = [{
            'symbol': item['symbol'],
            'price': item['avg'],
            'stdev': item['stdev'],
            'z_score': item['z_score'],
            'date': item['date_time']
        } for item in top_5]

        low_spikes = [{
            'symbol': item['symbol'],
            'price': item['avg'],
            'stdev': item['stdev'],
            'z_score': item['z_score'],
            'date': item['date_time']
        } for item in low_5]

        # Append the current top and bottom spikes to the list
        all_spikes.extend(top_spikes)
        all_spikes.extend(low_spikes)

    # Save the file locally
    print("saving file")
    file_path = 'spikes.csv'
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['symbol', 'price', 'stdev', 'z_score', 'date'])
        writer.writeheader()
        writer.writerows(all_spikes)
        
    convert_csv_to_excel(request)
    # Return a JSON response indicating success
    return JsonResponse({'message': 'File saved successfully'}, status=200)
    
