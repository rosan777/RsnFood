from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from datetime import timedelta

from django.utils import timezone

from rsnapp.models import UserEx, Address, Restaurant, Food, Order, OrderItem

# email, user type, phone; the password is the same as the email (matches the login page buttons)
DEMO_USERS = [
    ("resowner@example.com", "RestaurantOwner", "01700000001"),
    ("enduser@example.com", "EndUser", "01700000002"),
    ("deliveryperson@example.com", "DeliveryPerson", "01700000003"),
]

# Photos come from Wikimedia Commons (free licences, see the credits in README.md)
COMMONS = "https://commons.wikimedia.org/wiki/Special:FilePath/"

DEMO_FOODS = [
    (
        "Chicken Biryani",
        "Fragrant rice with spiced chicken",
        220.0,
        COMMONS + "Chicken_Hyderabadi_Biryani.JPG?width=900",
    ),
    (
        "Beef Burger",
        "Juicy beef patty with cheese",
        180.0,
        COMMONS + "NYC-Diner-Bacon-Cheeseburger.jpg?width=900",
    ),
    (
        "Chicken Fry (4 pcs)",
        "Crispy fried chicken",
        250.0,
        COMMONS + "Fried-Chicken-Set.jpg?width=900",
    ),
    (
        "Mango Lassi",
        "Cold and sweet yogurt drink",
        90.0,
        COMMONS + "Tasty_Mango_lassi_picture.JPG?width=900",
    ),
]


class Command(BaseCommand):
    help = "Create demo users, one restaurant and a few foods (safe to run many times)."

    def handle(self, *args, **options):
        owner = None

        for email, user_type, phone in DEMO_USERS:
            user = User.objects.filter(email=email).first()
            if not user:
                user = User.objects.create(
                    username=email.split("@")[0],
                    first_name=user_type,
                    last_name="Demo",
                    email=email,
                )
                user.set_password(email)
                user.save()
                UserEx.objects.create(user=user, phone=phone, user_type=user_type)
                self.stdout.write(f"created {email}")
            if user_type == "RestaurantOwner":
                owner = user

        if not Restaurant.objects.filter(owner=owner).exists():
            address = Address.objects.create(
                address_text="12 Demo Road",
                city="Pabna",
                state="Rajshahi",
                zip_code="6600",
            )
            restaurant = Restaurant.objects.create(
                name="Demo Kitchen", owner=owner, address=address, show_on_site=True
            )
            for name, description, price, image_url in DEMO_FOODS:
                Food.objects.create(
                    name=name,
                    description=description,
                    price=price,
                    image_url=image_url,
                    restaurant=restaurant,
                    show_on_site=True,
                )
            self.stdout.write("created Demo Kitchen with foods")

        # foods created by an older run get their photo link too
        for name, description, price, image_url in DEMO_FOODS:
            Food.objects.filter(name=name, image_url="", image="").update(
                image_url=image_url
            )

        # a few delivered orders so the owner's Sales page has something to show
        customer = User.objects.get(email="enduser@example.com")
        courier = User.objects.get(email="deliveryperson@example.com")
        restaurant = Restaurant.objects.filter(owner=owner).first()
        if restaurant and not Order.objects.filter(restaurant=restaurant).exists():
            foods = list(Food.objects.filter(restaurant=restaurant))
            for days_ago, food, quantity in [(0, foods[0], 2), (1, foods[1], 1), (3, foods[2], 3), (5, foods[0], 1)]:
                order = Order.objects.create(
                    user=customer,
                    restaurant=restaurant,
                    total=food.price * quantity,
                    status="Delivered",
                    payment_status="PAID",
                    delivery_person=courier,
                    delivery_address="12 Demo Road, Pabna",
                )
                Order.objects.filter(pk=order.pk).update(
                    created_at=timezone.now() - timedelta(days=days_ago)
                )
                OrderItem.objects.create(order=order, food=food, quantity=quantity)
            self.stdout.write("created sample delivered orders")

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
