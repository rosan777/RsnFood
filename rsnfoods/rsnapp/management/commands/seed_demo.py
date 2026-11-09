from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from rsnapp.models import UserEx, Address, Restaurant, Food

# email, user type, phone; the password is the same as the email (matches the login page buttons)
DEMO_USERS = [
    ("resowner@example.com", "RestaurantOwner", "01700000001"),
    ("enduser@example.com", "EndUser", "01700000002"),
    ("deliveryperson@example.com", "DeliveryPerson", "01700000003"),
]

DEMO_FOODS = [
    ("Chicken Biryani", "Fragrant rice with spiced chicken", 220.0),
    ("Beef Burger", "Juicy beef patty with cheese", 180.0),
    ("Chicken Fry (4 pcs)", "Crispy fried chicken", 250.0),
    ("Mango Lassi", "Cold and sweet yogurt drink", 90.0),
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
            for name, description, price in DEMO_FOODS:
                Food.objects.create(
                    name=name,
                    description=description,
                    price=price,
                    restaurant=restaurant,
                    show_on_site=True,
                )
            self.stdout.write("created Demo Kitchen with foods")

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
