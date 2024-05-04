# Generated by Django 4.2.11 on 2024-03-31 21:18

import accounts.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Strike',
            fields=[
                ('id', models.CharField(default=accounts.models.generate_uuid, max_length=64, primary_key=True, serialize=False)),
                ('long_symbol', models.CharField(max_length=30)),
                ('short_symbol', models.CharField(max_length=30)),
                ('total_open_price', models.FloatField()),
                ('total_close_price', models.FloatField()),
                ('current_price', models.FloatField()),
                ('current_percentage', models.FloatField(default=0)),
                ('open_time', models.DateTimeField(auto_now=True)),
                ('close_time', models.DateTimeField(blank=True, null=True)),
                ('signal_exit', models.BooleanField(default=False)),
                ('closed', models.BooleanField(default=False)),
                ('first_long_stock', models.CharField(max_length=30)),
                ('fls_quantity', models.IntegerField(max_length=30)),
                ('fls_price', models.FloatField()),
                ('fls_close_price', models.FloatField()),
                ('fls_open', models.FloatField()),
                ('fls_close', models.FloatField()),
                ('second_long_stock', models.CharField(max_length=30)),
                ('sls_quantity', models.IntegerField(max_length=30)),
                ('sls_price', models.FloatField()),
                ('sls_close_price', models.FloatField()),
                ('sls_open', models.FloatField()),
                ('sls_close', models.FloatField()),
                ('third_long_stock', models.CharField(max_length=30)),
                ('tls_quantity', models.IntegerField(max_length=30)),
                ('tls_price', models.FloatField()),
                ('tls_close_price', models.FloatField()),
                ('tls_open', models.FloatField()),
                ('tls_close', models.FloatField()),
                ('first_short_stock', models.CharField(max_length=30)),
                ('fss_quantity', models.IntegerField(max_length=30)),
                ('fss_price', models.IntegerField(max_length=30)),
                ('fss_close_price', models.FloatField()),
                ('fss_open', models.FloatField()),
                ('fss_close', models.FloatField()),
                ('second_short_stock', models.CharField(max_length=30)),
                ('sss_quantity', models.IntegerField(max_length=30)),
                ('sss_price', models.IntegerField(max_length=30)),
                ('sss_close_price', models.FloatField()),
                ('sss_open', models.FloatField()),
                ('sss_close', models.FloatField()),
                ('third_short_stock', models.CharField(max_length=30)),
                ('tss_quantity', models.IntegerField(max_length=30)),
                ('tss_close_price', models.FloatField()),
                ('tss_price', models.IntegerField(max_length=30)),
                ('tss_open', models.FloatField()),
                ('tss_close', models.FloatField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
