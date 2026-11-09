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
