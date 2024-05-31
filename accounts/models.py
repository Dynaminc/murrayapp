from django.db import models
from django.contrib.auth.models import User
import uuid

WALLET_FUNDED = 'WALLET_FUNDED'
TRADE_CLOSED = 'TRADE_CLOSED'
TRADE_OPENED = 'TRADE_OPENED'
COMMISSON_FEE ='COMMISSION_FEE'
CUSTOM = 'CUSTOM'
EXIT_ALERT = 'EXIT_ALERT'

CHECKED = "CHECKED"
DELETED = "DELETED"
INVISIBLE = "INVISIBLE"
VISIBLE = "VISIBLE"

class notif_status:
    CHECKED = "CHECKED"
    DELETED = "DELETED"
    INVISIBLE = "INVISIBLE"
    VISIBLE = "VISIBLE"
        
class tran_not_type:
    WALLET_FUNDED = 'WALLET_FUNDED'
    TRADE_CLOSED = 'TRADE_CLOSED'
    TRADE_OPENED = 'TRADE_OPENED'
    COMMISSON_FEE ='COMMISSION_FEE'
    CUSTOM = 'CUSTOM'
    EXIT_ALERT = 'EXIT_ALERT'
    
    
def generate_uuid():
    return str(uuid.uuid4())

class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, blank=True, null=True)  # First name of the user
    last_name = models.CharField(max_length=100, blank=True, null=True)  # Last name of the user
    size = models.FloatField(default=1000000)  # Last name of the user
    balance = models.FloatField()  # Last name of the user
    margin = models.IntegerField(default=3)
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Notification(models.Model):
    NOTIFICATION_STATUS_CHOICES = (
        (CHECKED,'checked'),
        (DELETED,'deleted'),
        (INVISIBLE,'invisible'),
        (VISIBLE,'visible'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    id = models.CharField(max_length=64, default=generate_uuid,primary_key=True)
    details = models.TextField(max_length=5000, null=False, blank=True)  # User's interests
    strike_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  
    status = models.CharField(choices=NOTIFICATION_STATUS_CHOICES, max_length=1000, default="INVSIBLE")  # Status of the notification
    
    TYPE_CHOICES = (
        (TRADE_CLOSED, 'TRADE_CLOSED'),
        (TRADE_OPENED, 'TRADE_OPENED'),
        (EXIT_ALERT, 'EXIT_ALERT'),
        (CUSTOM, 'CUSTOM'),
    ) 
    notification_type = models.CharField(choices=TYPE_CHOICES, max_length=1000, default='CUSTOM')  # Status of the bid
    def __str__(self):
        return f"{self.id}"
    
    
class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    id = models.CharField(max_length=64, default=generate_uuid,primary_key=True)
    details = models.TextField(max_length=5000, null=False, blank=True)  # User's interests
    strike_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  
    previous_balance = models.FloatField(null=True, blank=True)
    new_balance = models.FloatField(null=True, blank=True)
    credit = models.BooleanField(default=True)
    amount = models.FloatField(null=True, blank=True)
    TYPE_CHOICES = (
        (WALLET_FUNDED,'WALLET_FUNDED'),
        (TRADE_CLOSED, 'TRADE_CLOSED'),
        (TRADE_OPENED, 'TRADE_OPENED'),
        (COMMISSON_FEE, 'COMMISSION_FEE'),
        (CUSTOM, 'CUSTOM'),
    ) 
    transaction_type = models.CharField(choices=TYPE_CHOICES, max_length=1000, default='CUSTOM')  # Status of the bid
    def __str__(self):
        return f"{self.id}: {self.user} {self.details}"
    
class Strike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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
    
    target_profit = models.FloatField(null=False, default=1)            
    
    
    def __str__(self):
        profile_instance = Profile.objects.filter(user=self.user).first()
        return f"{self.id}: {self.short_symbol} {self.long_symbol}.  closed:  {self.closed}"