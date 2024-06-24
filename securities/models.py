from django.db import models
import uuid


class Company(models.Model):
    SYMBOLS = (
        "AXP",
        "AMGN",
        "AAPL",
        "BA",
        "CAT",
        "CSCO",
        "CVX",
        "GS",
        "HD",
        "HON",
        "IBM",
        "INTC",
        "JNJ",
        "KO",
        "JPM",
        "MCD",
        "MMM",
        "MRK",
        "MSFT",
        "NKE",
        "PG",
        "TRV",
        "UNH",
        "CRM",
        "VZ",
        "V",
        "AMZN",
        "WMT",
        "DIS",
        "DOW",
    )

    DOW_JONES = "DJI"

    all_symbols = list(SYMBOLS) + [DOW_JONES]

    def __str__(self):
        return self.name 

    name = models.CharField(max_length=255, unique=True)
    symbol = models.CharField(max_length=10, unique=True)


class Stock(models.Model):
    symbol = models.CharField(max_length=6)
    date_time = models.DateTimeField()
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    previous_close = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = [["symbol", "date_time"]]

    def __str__(self):
        return self.symbol
    
def generate_uuid():
    return str(uuid.uuid4())

class Earning(models.Model):
    id = models.CharField(max_length=64, default=generate_uuid,primary_key=True)
    symbol = models.CharField(max_length=30)
    date_time = models.DateTimeField()
    

    def __str__(self):
        return f"{str(self.date_time)}: {self.symbol}"
    
class Cronny(models.Model):
    symbol = models.CharField(max_length=30)
    date_time = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"{str(self.date_time)}: {self.symbol}"
        
        
class Missing(models.Model):
    data = models.CharField(max_length=100)
    date_time = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.data}"        
        
class Combination(models.Model):
    symbol = models.CharField(max_length=30)
    strike = models.FloatField()
    avg = models.FloatField(null=True, blank=True)
    stdev = models.FloatField(null=True, blank=True)
    z_score = models.FloatField(null=True, blank=True)
    date_time = models.DateTimeField()

    class Meta:
        unique_together = [["symbol", "date_time"]]

class MiniCombination(models.Model):
    symbol = models.CharField(max_length=30)
    strike = models.FloatField()
    avg = models.FloatField(null=True, blank=True)
    stdev = models.FloatField(null=True, blank=True)
    z_score = models.FloatField(null=True, blank=True)
    class Meta:
        unique_together = [["symbol"]]


