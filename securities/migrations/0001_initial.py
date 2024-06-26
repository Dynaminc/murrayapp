# Generated by Django 4.2.11 on 2024-05-04 13:41

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('symbol', models.CharField(max_length=10, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Cronny',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=30)),
                ('date_time', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=6)),
                ('date_time', models.DateTimeField()),
                ('open', models.FloatField()),
                ('high', models.FloatField()),
                ('low', models.FloatField()),
                ('close', models.FloatField()),
                ('previous_close', models.FloatField(blank=True, null=True)),
            ],
            options={
                'unique_together': {('symbol', 'date_time')},
            },
        ),
        migrations.CreateModel(
            name='Combination',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=30)),
                ('strike', models.FloatField()),
                ('avg', models.FloatField(blank=True, null=True)),
                ('stdev', models.FloatField(blank=True, null=True)),
                ('z_score', models.FloatField(blank=True, null=True)),
                ('date_time', models.DateTimeField()),
            ],
            options={
                'unique_together': {('symbol', 'date_time')},
            },
        ),
    ]
