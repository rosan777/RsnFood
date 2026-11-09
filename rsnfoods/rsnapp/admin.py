from django.contrib import admin

from .models import (
    UserEx,
    Restaurant,
    Food,
    Address,
    Cart,
    CartItem,
    Order,
    OrderItem,
)

# Register your models here.
admin.site.register(UserEx)
admin.site.register(Restaurant)
admin.site.register(Food)
admin.site.register(Address)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
