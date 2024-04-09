from django.db import models
from django.contrib.auth.models import User
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.RESTRICT)
    first_name = models.CharField(max_length=100, blank=True, null=True)  # First name of the user
    last_name = models.CharField(max_length=100, blank=True, null=True)  # Last name of the user
    porfolio = models.FloatField()  # Last name of the user
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    

class Strike(models.Model):
    user = models.ForeignKey(User, on_delete=models.RESTRICT)
    id = models.CharField(max_length=64, default=generate_uuid,primary_key=True)
    long_symbol = models.CharField(max_length=30)
    short_symbol = models.CharField(max_length=30)
    
    total_open_price = models.FloatField(null=True, blank=True)
    total_close_price = models.FloatField(null=True, blank=True)
    current_price = models.FloatField(null=True, blank=True)
    current_percentage = models.FloatField(default=0)
    max_percentage = models.FloatField(default=0)
    min_percentage = models.FloatField(default=0)
     
    open_time = models.DateTimeField(auto_now_add=True)
    close_time = models.DateTimeField(null=True, blank=True)
    
    signal_exit = models.BooleanField(default=False)
    closed = models.BooleanField(default=False)
    
    first_long_stock = models.CharField(max_length=30,null=True, blank=True)
    fls_quantity = models.IntegerField(null=True, blank=True)
    fls_price = models.FloatField(null=True, blank=True)
    fls_close_price = models.FloatField(null=True, blank=True)
    fls_open = models.FloatField(null=True, blank=True)
    fls_close = models.FloatField(null=True, blank=True)
    
    second_long_stock = models.CharField(max_length=30, null=True, blank=True)
    sls_quantity = models.IntegerField(null=True, blank=True)
    sls_price = models.FloatField(null=True, blank=True)
    sls_close_price = models.FloatField(null=True, blank=True)
    sls_open = models.FloatField(null=True, blank=True)
    sls_close = models.FloatField(null=True, blank=True)
    
    third_long_stock = models.CharField(max_length=30, null=True, blank=True)
    tls_quantity = models.IntegerField(null=True, blank=True)
    tls_price = models.FloatField(null=True, blank=True)
    tls_close_price = models.FloatField(null=True, blank=True)
    tls_open = models.FloatField(null=True, blank=True)
    tls_close = models.FloatField(null=True, blank=True)
    
    first_short_stock = models.CharField(max_length=30, null=True, blank=True)
    fss_quantity = models.IntegerField(null=True, blank=True)
    fss_price = models.IntegerField(null=True, blank=True)
    fss_close_price = models.FloatField(null=True, blank=True)
    fss_open = models.FloatField(null=True, blank=True)
    fss_close = models.FloatField(null=True, blank=True)
    
    second_short_stock = models.CharField(max_length=30, null=True, blank=True)
    sss_quantity = models.IntegerField(null=True, blank=True)
    sss_price = models.IntegerField(null=True, blank=True)
    sss_close_price = models.FloatField(null=True, blank=True)
    sss_open = models.FloatField(null=True, blank=True)
    sss_close = models.FloatField(null=True, blank=True)    
    
    third_short_stock = models.CharField(max_length=30, null=True, blank=True)
    tss_quantity = models.IntegerField(null=True, blank=True)
    tss_close_price = models.FloatField(null=True, blank=True)
    tss_price = models.IntegerField(null=True, blank=True)
    tss_open = models.FloatField(null=True, blank=True)
    tss_close = models.FloatField(null=True, blank=True)            
    
    def __str__(self):
        profile_instance = Profile.objects.filter(user=self.user).first()
        return f"{profile_instance.first_name}: {self.short_symbol} {self.long_symbol}"