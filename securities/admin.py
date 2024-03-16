from django.contrib import admin # noqa
from .models import *
# Register your models here.
admin.site.register(Company)
admin.site.register(Stock)
admin.site.register(Combination)
admin.site.register(Cronny)