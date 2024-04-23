# Generated by Django 5.0.4 on 2024-04-08 23:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rsnapp', '0002_delete_x'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Cart',
                'verbose_name_plural': 'Carts',
                'db_table': 'cart',
            },
        ),
        migrations.CreateModel(
            name='CartItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(default=1)),
                ('cart', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='rsnapp.cart')),
                ('food', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='rsnapp.food')),
            ],
            options={
                'verbose_name': 'CartItem',
                'verbose_name_plural': 'CartItems',
                'db_table': 'cart_item',
            },
        ),
    ]