from django.contrib import admin
from .models import Profile, Strike, Transaction, Notification
# Register your models here.
admin.site.register(Profile)
admin.site.register(Strike)
admin.site.register(Transaction)
admin.site.register(Notification)