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


# Photos are free-to-use Unsplash photos (see the credits in README.md); the link asks for a sharp 1000px version
def photo(photo_id):
    return f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w=1000&q=80"


# name, cover photo, address, foods (name, description, price, photo)
DEMO_RESTAURANTS = [
    (
        "Demo Kitchen",
        photo("photo-1631515243349-e0cb75fb8d3a"),
        ("12 Demo Road", "Pabna", "Rajshahi", "6600"),
        [
            (
                "Chicken Biryani",
                "Fragrant rice with spiced chicken",
                220.0,
                photo("photo-1631515243349-e0cb75fb8d3a"),
            ),
            (
                "Beef Burger",
                "Juicy beef patty with cheese",
                180.0,
                photo("photo-1572802419224-296b0aeee0d9"),
            ),
            (
                "Chicken Fry (4 pcs)",
                "Crispy fried chicken",
                250.0,
                photo("photo-1548340748-6d2b7d7da280"),
            ),
            (
                "Mango Lassi",
                "Cold and sweet yogurt drink",
                90.0,
                photo("photo-1623065422902-30a2d299bbe4"),
            ),
        ],
    ),
    (
        "Burger Barn",
        photo("photo-1639020715395-487e2d63b927"),
        ("45 Station Road", "Pabna", "Rajshahi", "6600"),
        [
            (
                "Bacon Cheese Burger",
                "Melted cheese and crispy bacon",
                260.0,
                photo("photo-1639020715395-487e2d63b927"),
            ),
            (
                "Burger and Fries",
                "Classic burger with a side of fries",
                240.0,
                photo("photo-1641848606108-1d583b3f94fb"),
            ),
        ],
    ),
    (
        "Napoli Pizza House",
        photo("photo-1604068549290-dea0e4a305ca"),
        ("8 Lake View Road", "Pabna", "Rajshahi", "6600"),
        [
            (
                "Margherita Pizza",
                "Tomato, mozzarella and fresh basil",
                450.0,
                photo("photo-1604068549290-dea0e4a305ca"),
            ),
            (
                "Classic Wood-fired Pizza",
                "Thin crust, baked golden",
                520.0,
                photo("photo-1517685645259-c6caddb7165d"),
            ),
            (
                "Cheese Slice Combo",
                "Fresh slices with extra cheese",
                300.0,
                photo("photo-1449785227466-10687c63e194"),
            ),
        ],
    ),
    (
        "Tokyo Noodle Bar",
        photo("photo-1569718212165-3a8278d5f624"),
        ("21 Bazar Road", "Pabna", "Rajshahi", "6600"),
        [
            (
                "Shrimp Ramen",
                "Soft egg, shrimp and snow peas",
                380.0,
                photo("photo-1569718212165-3a8278d5f624"),
            ),
            (
                "Spicy Korean Noodles",
                "Hot and spicy noodle bowl",
                320.0,
                photo("photo-1628610688436-e635552020fc"),
            ),
        ],
    ),
    (
        "Crispy Chicken Co",
        photo("photo-1657271511865-f610b280dca4"),
        ("3 College Road", "Pabna", "Rajshahi", "6600"),
        [
            (
                "Golden Fried Chicken",
                "Crunchy outside, juicy inside",
                280.0,
                photo("photo-1657271511865-f610b280dca4"),
            ),
            (
                "Chicken Tenders",
                "Tender strips with dipping sauce",
                230.0,
                photo("photo-1605291581926-df4bf7ee3e89"),
            ),
        ],
    ),
    (
        "Sweet Tooth Bakery",
        photo("photo-1677051726759-77ea1a1266d3"),
        ("17 Park Street", "Pabna", "Rajshahi", "6600"),
        [
            (
                "Chocolate Cake Slice",
                "Rich chocolate with a soft crumb",
                150.0,
                photo("photo-1677051726759-77ea1a1266d3"),
            ),
            (
                "Chocolate Syrup Cake",
                "Cake topped with warm chocolate syrup",
                170.0,
                photo("photo-1607257882338-70f7dd2ae344"),
            ),
            (
                "Mango Smoothie",
                "Fresh mango blended ice cold",
                110.0,
                photo("photo-1623065422902-30a2d299bbe4"),
            ),
        ],
    ),
]


class Command(BaseCommand):
    help = (
        "Create demo users, six restaurants and their foods (safe to run many times)."
    )

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

        for name, cover, (street, city, state, zip_code), foods in DEMO_RESTAURANTS:
            restaurant = Restaurant.objects.filter(owner=owner, name=name).first()
            if not restaurant:
                address = Address.objects.create(
                    address_text=street, city=city, state=state, zip_code=zip_code
                )
                restaurant = Restaurant.objects.create(
                    name=name, owner=owner, address=address, show_on_site=True
                )
                self.stdout.write(f"created {name}")
            # cover photo and food photos are refreshed on every run
            Restaurant.objects.filter(pk=restaurant.pk, image="").update(
                image_url=cover
            )
            for food_name, description, price, image_url in foods:
                food = Food.objects.filter(
                    restaurant=restaurant, name=food_name
                ).first()
                if not food:
                    Food.objects.create(
                        name=food_name,
                        description=description,
                        price=price,
                        image_url=image_url,
                        restaurant=restaurant,
                        show_on_site=True,
                    )
                else:
                    Food.objects.filter(pk=food.pk, image="").update(
                        image_url=image_url
                    )

        # a few delivered orders so the owner's Sales page has something to show
        customer = User.objects.get(email="enduser@example.com")
        courier = User.objects.get(email="deliveryperson@example.com")
        restaurant = Restaurant.objects.filter(owner=owner, name="Demo Kitchen").first()
        if restaurant and not Order.objects.filter(restaurant=restaurant).exists():
            foods = list(Food.objects.filter(restaurant=restaurant))
            for days_ago, food, quantity in [
                (0, foods[0], 2),
                (1, foods[1], 1),
                (3, foods[2], 3),
                (5, foods[0], 1),
            ]:
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
