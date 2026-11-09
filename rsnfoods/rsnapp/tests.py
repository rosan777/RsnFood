from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import UserEx, Restaurant, Food, Cart, CartItem, Order, OrderItem


# Create your tests here.


def make_user(name, user_type):
    user = User.objects.create_user(
        username=name, email=f"{name}@test.com", password="pass12345"
    )
    UserEx.objects.create(user=user, phone=name, user_type=user_type)
    return user


class BaseTestCase(TestCase):
    def setUp(self):
        self.owner1 = make_user("owner1", "RestaurantOwner")
        self.owner2 = make_user("owner2", "RestaurantOwner")
        self.customer = make_user("customer", "EndUser")
        self.customer2 = make_user("customer2", "EndUser")
        self.delivery = make_user("delivery", "DeliveryPerson")

        self.res1 = Restaurant.objects.create(name="Res One", owner=self.owner1)
        self.res2 = Restaurant.objects.create(name="Res Two", owner=self.owner2)
        self.food1 = Food.objects.create(name="Burger", price=100, restaurant=self.res1)
        self.food2 = Food.objects.create(name="Pizza", price=200, restaurant=self.res2)

    def login(self, user):
        self.client.login(username=user.username, password="pass12345")


class OwnershipTests(BaseTestCase):
    def test_owner_cannot_edit_other_restaurant(self):
        self.login(self.owner1)
        response = self.client.post(
            reverse("ro_edit_restaurant", args=[self.res2.id]), {"name": "Hacked"}
        )
        self.assertContains(response, "Restaurant not found.")
        self.res2.refresh_from_db()
        self.assertEqual(self.res2.name, "Res Two")

    def test_owner_cannot_delete_other_food(self):
        self.login(self.owner1)
        self.client.post(reverse("ro_delete_food", args=[self.food2.id]))
        self.assertTrue(Food.objects.filter(id=self.food2.id).exists())

    def test_owner_can_delete_own_food(self):
        self.login(self.owner1)
        self.client.post(reverse("ro_delete_food", args=[self.food1.id]))
        self.assertFalse(Food.objects.filter(id=self.food1.id).exists())

    def test_owner_cannot_view_other_order(self):
        order = Order.objects.create(user=self.customer, restaurant=self.res2)
        self.login(self.owner1)
        response = self.client.get(reverse("ro_view_order", args=[order.id]))
        self.assertContains(response, "Order not found.")

    def test_customer_cannot_view_other_customer_order(self):
        order = Order.objects.create(user=self.customer, restaurant=self.res1)
        self.login(self.customer2)
        response = self.client.get(reverse("enduser_order", args=[order.id]))
        self.assertContains(response, "Order not found.")

    def test_delivery_cannot_open_unassigned_order(self):
        order = Order.objects.create(user=self.customer, restaurant=self.res1)
        self.login(self.delivery)
        response = self.client.get(reverse("dp_order", args=[order.id]))
        self.assertContains(response, "Order not found.")

    def test_customer_cannot_open_owner_pages(self):
        self.login(self.customer)
        response = self.client.get(reverse("ro_dashboard"))
        self.assertContains(response, "not authorized")


class CartTests(BaseTestCase):
    def add_to_cart(self, food, quantity):
        return self.client.post(
            reverse("enduser_cart"),
            {"food_id": food.id, "quantity": quantity, "request_url": "/"},
        )

    def test_same_food_is_merged_into_one_row(self):
        self.login(self.customer)
        self.add_to_cart(self.food1, 1)
        self.add_to_cart(self.food1, 2)
        items = CartItem.objects.filter(cart__user=self.customer)
        self.assertEqual(items.count(), 1)
        self.assertEqual(items.first().quantity, 3)

    def test_only_one_restaurant_at_a_time(self):
        self.login(self.customer)
        self.add_to_cart(self.food1, 1)
        self.add_to_cart(self.food2, 1)
        self.assertEqual(CartItem.objects.filter(cart__user=self.customer).count(), 1)

    def test_empty_cart_checkout_redirects_to_cart(self):
        self.login(self.customer)
        response = self.client.post(
            reverse("enduser_checkout"), {"delivery_address": "Somewhere"}
        )
        self.assertRedirects(response, reverse("enduser_cart"))
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_creates_order_and_clears_cart(self):
        self.login(self.customer)
        self.add_to_cart(self.food1, 2)
        self.client.post(reverse("enduser_checkout"), {"delivery_address": "Pabna"})
        order = Order.objects.get(user=self.customer)
        self.assertEqual(order.total, 200)
        self.assertEqual(OrderItem.objects.filter(order=order).count(), 1)
        self.assertEqual(CartItem.objects.filter(cart__user=self.customer).count(), 0)

    def test_cannot_remove_other_users_cart_item(self):
        cart = Cart.objects.create(user=self.customer)
        item = CartItem.objects.create(cart=cart, food=self.food1, quantity=1)
        self.login(self.customer2)
        self.client.post(reverse("enduser_remove_from_cart", args=[item.id]))
        self.assertTrue(CartItem.objects.filter(id=item.id).exists())

    def test_remove_by_get_does_nothing(self):
        cart = Cart.objects.create(user=self.customer)
        item = CartItem.objects.create(cart=cart, food=self.food1, quantity=1)
        self.login(self.customer)
        self.client.get(reverse("enduser_remove_from_cart", args=[item.id]))
        self.assertTrue(CartItem.objects.filter(id=item.id).exists())


class OrderFlowTests(BaseTestCase):
    def test_confirm_assigns_delivery_person(self):
        order = Order.objects.create(user=self.customer, restaurant=self.res1)
        self.login(self.owner1)
        self.client.post(reverse("ro_view_order", args=[order.id]), {"status": "Confirmed"})
        order.refresh_from_db()
        self.assertEqual(order.status, "Confirmed")
        self.assertEqual(order.delivery_person, self.delivery)

    def test_confirm_without_delivery_person_still_confirms(self):
        self.delivery.delete()
        order = Order.objects.create(user=self.customer, restaurant=self.res1)
        self.login(self.owner1)
        self.client.post(reverse("ro_view_order", args=[order.id]), {"status": "Confirmed"})
        order.refresh_from_db()
        self.assertEqual(order.status, "Confirmed")
        self.assertIsNone(order.delivery_person)

    def test_confirm_keeps_existing_delivery_person(self):
        other = make_user("delivery2", "DeliveryPerson")
        order = Order.objects.create(
            user=self.customer, restaurant=self.res1, delivery_person=other
        )
        self.login(self.owner1)
        self.client.post(reverse("ro_view_order", args=[order.id]), {"status": "Confirmed"})
        order.refresh_from_db()
        self.assertEqual(order.delivery_person, other)

    def test_delivery_person_login_goes_to_dashboard(self):
        response = self.client.post(
            reverse("flogin"),
            {"email": "delivery@test.com", "password": "pass12345"},
        )
        self.assertRedirects(response, reverse("dp_dashboard"))


class DashboardTests(BaseTestCase):
    def test_each_dashboard_loads_with_counts(self):
        for user, url_name in [
            (self.owner1, "ro_dashboard"),
            (self.customer, "enduser_dashboard"),
            (self.delivery, "dp_dashboard"),
        ]:
            self.client.logout()
            self.login(user)
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Welcome")

    def test_admin_pages_load(self):
        admin_user = User.objects.create_superuser("boss", "boss@test.com", "pass12345")
        self.client.force_login(admin_user)
        for name in ["restaurant", "food", "order", "userex", "cart"]:
            response = self.client.get(f"/admin/rsnapp/{name}/")
            self.assertEqual(response.status_code, 200, name)


class FeatureTests(BaseTestCase):
    def make_order(self, user, restaurant, status="Delivered", total=300):
        order = Order.objects.create(
            user=user, restaurant=restaurant, total=total, status=status
        )
        OrderItem.objects.create(order=order, food=self.food1, quantity=3)
        return order

    def test_invoice_for_customer_and_owner_only(self):
        order = self.make_order(self.customer, self.res1)
        url = reverse("order_invoice", args=[order.id])

        for user in [self.customer, self.owner1]:
            self.client.logout()
            self.login(user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Burger")
            self.assertContains(response, "300")

        for user in [self.customer2, self.owner2]:
            self.client.logout()
            self.login(user)
            self.assertContains(self.client.get(url), "Order not found.")

        self.client.logout()
        self.login(self.delivery)
        self.assertContains(self.client.get(url), "not authorized")

    def test_sales_page_counts_only_delivered_orders(self):
        self.make_order(self.customer, self.res1, "Delivered", 300)
        self.make_order(self.customer, self.res1, "Pending", 999)
        self.make_order(self.customer, self.res2, "Delivered", 555)
        self.login(self.owner1)
        response = self.client.get(reverse("ro_sales"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["revenue"], 300)
        self.assertEqual(response.context["orders_count"], 2)
        self.assertEqual(response.context["top_foods"][0]["qty"], 3)

    def test_sales_page_is_owner_only(self):
        self.login(self.customer)
        self.assertContains(self.client.get(reverse("ro_sales")), "not authorized")

    def test_smart_assignment_picks_least_busy_delivery_person(self):
        busy = self.delivery
        free = make_user("delivery2", "DeliveryPerson")
        busy_order = self.make_order(self.customer, self.res1, "Confirmed")
        busy_order.delivery_person = busy
        busy_order.save()

        new_order = self.make_order(self.customer2, self.res1, "Pending")
        self.login(self.owner1)
        self.client.post(
            reverse("ro_view_order", args=[new_order.id]), {"status": "Confirmed"}
        )
        new_order.refresh_from_db()
        self.assertEqual(new_order.delivery_person, free)

    def test_language_toggle_switches_to_bangla_and_back(self):
        self.login(self.customer)
        self.client.get(reverse("set_language", args=["bn"]))
        self.assertContains(self.client.get(reverse("enduser_dashboard")), "স্বাগতম")
        self.client.get(reverse("set_language", args=["en"]))
        self.assertContains(self.client.get(reverse("enduser_dashboard")), "Welcome")

    def test_language_toggle_ignores_unknown_code(self):
        self.client.get(reverse("set_language", args=["xx"]))
        self.assertContains(self.client.get(reverse("index")), "All Restaurants")


class SeedDemoTests(TestCase):
    def test_seed_demo_creates_data_once_and_logins_work(self):
        from django.core.management import call_command

        call_command("seed_demo")
        call_command("seed_demo")
        self.assertEqual(User.objects.filter(email__endswith="@example.com").count(), 3)
        self.assertEqual(Restaurant.objects.count(), 6)
        self.assertEqual(Food.objects.count(), 16)
        self.assertEqual(Order.objects.count(), 4)

        response = self.client.post(
            reverse("flogin"),
            {"email": "resowner@example.com", "password": "resowner@example.com"},
        )
        self.assertRedirects(response, reverse("ro_dashboard"))
        sales = self.client.get(reverse("ro_sales"))
        self.assertContains(sales, "Chicken Biryani")


class FoodPhotoTests(TestCase):
    def test_home_page_shows_food_photos_and_ice_tag(self):
        from django.core.management import call_command

        call_command("seed_demo")
        response = self.client.get(reverse("index"))
        self.assertContains(response, "photo-1631515243349-e0cb75fb8d3a")
        self.assertContains(response, "photo-1604068549290-dea0e4a305ca")
        self.assertContains(response, "Napoli Pizza House")
        self.assertContains(response, "photo-1639020715395-487e2d63b927")
        self.assertContains(response, "Served ice cold")
        self.assertContains(response, "&copy; 2024 FoodDemo")
        self.assertContains(response, "Django Food - (demo)")
        self.assertContains(response, "Technology used in this project")

    def test_uploaded_image_wins_over_image_url(self):
        owner = make_user("o", "RestaurantOwner")
        res = Restaurant.objects.create(name="R", owner=owner)
        food = Food.objects.create(
            name="X", restaurant=res, image="food/x.png", image_url="https://e.com/a.jpg"
        )
        self.assertTrue(food.picture_url.endswith("food/x.png"))
        food.image = ""
        self.assertEqual(food.picture_url, "https://e.com/a.jpg")
