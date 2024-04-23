from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class UserEx(models.Model):

    # - user types
    USER_TYPES = (
        ("EndUser", "EndUser"),
        ("RestaurantOwner", "RestaurantOwner"),
        ("DeliveryPerson", "DeliveryPerson"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # - phone
    phone = models.CharField(max_length=20, null=True, blank=True)

    # - user type: EndUser, RestaurantOwner, DeliveryPerson
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default="EndUser")

    def __str__(self):
        return f"{self.user.username} - {self.user_type}"

    class Meta:
        db_table = "user_ex"
        verbose_name = "UserEx"
        verbose_name_plural = "UserEx"

# - address

class Address(models.Model):

    address_text = models.CharField(max_length=1000)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.address_text}, {self.city}, {self.state}, {self.zip_code}."

    class Meta:
        db_table = "address"
        verbose_name = "Address"
        verbose_name_plural = "Address"


# - restaurant

class Restaurant(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="restaurant", null=True, blank=True)

    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    address = models.OneToOneField(
        Address, on_delete=models.CASCADE, null=True, blank=True
    )

    show_on_site = models.BooleanField(default=False)  # handled by admin

    def __str__(self):
        return f"{self.name}"

    class Meta:
        db_table = "restaurant"
        verbose_name = "Restaurant"
        verbose_name_plural = "Restaurants"


class Food(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to="food", null=True, blank=True)
    price = models.FloatField(default=0.0)

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    show_on_site = models.BooleanField(default=False)  # handled by admin

    def __str__(self):
        return f"{self.name} - {self.description} - {self.price}"

    class Meta:
        db_table = "food"
        verbose_name = "Food"
        verbose_name_plural = "Foods"


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)


class Order(models.Model):
    CHOICES = (
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Cancelled", "Cancelled"),
        ("Delivering", "Delivering"),
        ("Delivered", "Delivered"),
        ("Returned", "Returned"),
    )
    PAYMENT_CHOICES = (
        ("PAID", "PAID"),
        ("UNPAID", "UNPAID"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    total = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, default="Pending", choices=CHOICES)
    payment_status = models.CharField(
        max_length=20, default="UNPAID", choices=PAYMENT_CHOICES
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    delivery_person = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="delivery_person",
        null=True,
        blank=True,
    )

    delivery_address = models.TextField(max_length=1000, default="")

    def __str__(self):
        return f"{self.user} - {self.restaurant} - {self.total} - {self.status}"

    class Meta:
        db_table = "order"
        verbose_name = "Order"
        verbose_name_plural = "Orders"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.order} - {self.food} - {self.quantity}"

    class Meta:
        db_table = "order_item"
        verbose_name = "OrderItem"
        verbose_name_plural = "OrderItems"
