# Generated by Django 4.2.11 on 2024-04-11 20:26

import accounts.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0006_strike_max_percentage_strike_min_percentage'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.CharField(default=accounts.models.generate_uuid, max_length=64, primary_key=True, serialize=False)),
                ('details', models.TextField(blank=True, max_length=5000)),
                ('strike_id', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('previous_balance', models.DateTimeField(blank=True, null=True)),
                ('new_balance', models.DateTimeField(blank=True, null=True)),
                ('credit', models.BooleanField(default=True)),
                ('amount', models.FloatField(blank=True, null=True)),
                ('transaction_type', models.CharField(choices=[('WALLET_FUNDED', 'WALLET_FUNDED'), ('TRADE_CLOSED', 'TRADE_CLOSED'), ('TRADE_OPENED', 'TRADE_OPENED'), ('COMMISSION_FEE', 'COMMISSION_FEE'), ('CUSTOM', 'CUSTOM')], default='CUSTOM', max_length=1000)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.CharField(default=accounts.models.generate_uuid, max_length=64, primary_key=True, serialize=False)),
                ('details', models.TextField(blank=True, max_length=5000)),
                ('strike_id', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('notification_type', models.CharField(choices=[('TRADE_CLOSED', 'TRADE_CLOSED'), ('TRADE_OPENED', 'TRADE_OPENED'), ('EXIT_ALERT', 'EXIT_ALERT'), ('CUSTOM', 'CUSTOM')], default='CUSTOM', max_length=1000)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]