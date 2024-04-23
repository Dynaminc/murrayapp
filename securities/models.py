from django.db import models


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

class Cronny(models.Model):
    symbol = models.CharField(max_length=30)
    date_time = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"{str(self.date_time)}: {self.symbol}"
        
        
class Combination(models.Model):
    symbol = models.CharField(max_length=30)
    strike = models.FloatField()
    avg = models.FloatField(null=True, blank=True)
    stdev = models.FloatField(null=True, blank=True)
    z_score = models.FloatField(null=True, blank=True)
    date_time = models.DateTimeField()

    class Meta:
        unique_together = [["symbol", "date_time"]]



