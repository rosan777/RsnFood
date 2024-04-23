from django.contrib import admin

from .models import UserEx, Restaurant, Food, Restaurant, Address

# Register your models here.
admin.site.register(UserEx)
admin.site.register(Restaurant)
admin.site.register(Food)
admin.site.register(Address)
