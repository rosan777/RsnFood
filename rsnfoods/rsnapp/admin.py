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

admin.site.site_header = "RSN Foods Admin"
admin.site.site_title = "RSN Foods Admin"
admin.site.index_title = "Manage RSN Foods"


class UserExAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "user_type")
    list_filter = ("user_type",)
    search_fields = ("user__username", "user__email", "phone")


class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "address", "show_on_site")
    list_filter = ("show_on_site",)
    list_editable = ("show_on_site",)
    search_fields = ("name", "owner__username")


class FoodAdmin(admin.ModelAdmin):
    list_display = ("name", "restaurant", "price", "show_on_site")
    list_filter = ("show_on_site", "restaurant")
    list_editable = ("show_on_site",)
    search_fields = ("name", "restaurant__name")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "restaurant",
        "total",
        "status",
        "payment_status",
        "delivery_person",
        "created_at",
    )
    list_filter = ("status", "payment_status", "restaurant")
    search_fields = ("user__username", "restaurant__name", "delivery_address")
    inlines = [OrderItemInline]


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user")
    inlines = [CartItemInline]


admin.site.register(UserEx, UserExAdmin)
admin.site.register(Restaurant, RestaurantAdmin)
admin.site.register(Food, FoodAdmin)
admin.site.register(Address)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
