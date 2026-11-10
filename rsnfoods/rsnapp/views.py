import random
from datetime import timedelta
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.db.models import Count, Q, Sum
from django.utils import timezone

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from django.contrib import messages

from .forms import RestaurantForm

from .models import UserEx, Restaurant, Address, Food, Cart, CartItem, Order, OrderItem

from .decorators import not_logged_in, login_required, restricted_access

# Create your views here.


### - Language toggle (English / Bangla), kept in the session
def set_language(request, code):
    if code in ("en", "bn"):
        request.session["lang"] = code
    return redirect(request.META.get("HTTP_REFERER") or "index")


### - Public Area
def index(request):

    foods_show_on_site = Food.objects.filter(show_on_site=True)
    restaurants_show_on_site = Restaurant.objects.filter(show_on_site=True)

    return render(
        request,
        "index.html",
        context={"foods": foods_show_on_site, "restaurants": restaurants_show_on_site},
    )


PROFILE_FEATURES = [
    ("Role based logins", "Customers, owners and couriers each land on their own dashboard and cannot open each other's pages."),
    ("Cart and checkout", "Add foods, remove or clear them, then confirm the order with a delivery address."),
    ("Order stages", "Pending, Confirmed, Delivering and Delivered, with Cancelled and Returned handled too."),
    ("Smart delivery assignment", "The courier with the fewest active orders is chosen when the owner confirms."),
    ("Invoices", "A clean invoice page for each order that customers and owners can print."),
    ("Sales report", "Revenue, the last seven days as bars, best selling foods and order counts per status."),
    ("Favorites", "A heart on every food, with a quick favorites list in the header."),
    ("English and Bangla", "One tap switches the menus and dashboards between both languages."),
    ("Photos", "Owners upload photos, and demo foods use fast hosted images."),
]

PROFILE_ROADMAP = [
    ("Payments", ["Card payments", "bKash and Nagad", "Cash on delivery with settlement reports", "Refunds and wallet credit"]),
    ("Customer experience", ["Live order tracking on a map", "SMS, email and push notifications", "Coupons and loyalty points", "Ratings and reviews"]),
    ("Restaurant tools", ["Stock and ingredient tracking", "Opening hours and busy mode", "Menu categories and variants", "Kitchen display screen"]),
    ("Platform and integrations", ["iOS and Android apps", "Public API for partners", "Accounting and POS integration", "Multi-city and multi-branch support"]),
]


def project_profile(request):
    return render(
        request,
        "project_profile.html",
        {"features": PROFILE_FEATURES, "roadmap": PROFILE_ROADMAP},
    )


def view_restaurents(request):

    restaurants = Restaurant.objects.all()
    return render(request, "view_restaurents.html", {"restaurants": restaurants})


def view_restaurent(request, id):
    restaurant = Restaurant.objects.filter(id=id).first()
    if not restaurant:
        return render(request, "error.html", {"error": "Restaurant not found."})
    foods = Food.objects.filter(restaurant=restaurant)
    return render(
        request,
        "view_restaurent.html",
        {"restaurant": restaurant, "foods": foods},
    )


def find_and_send_to_dashboard(request):
    # print(f"User: {request.user} UserEx: {request.user.userex} {request.user.userex.user_type}")
    try:
        ut = request.user.userex.user_type
        if ut == "EndUser":
            return redirect("enduser_dashboard")
        elif ut == "RestaurantOwner":
            return redirect("ro_dashboard")
        elif ut == "DeliveryPerson":
            return redirect("dp_dashboard")
    except Exception as e:
        return redirect("/admin")

 

def not_implemented(request):
    return HttpResponse("Not Implemented")


@login_required
def dashboard(request, userEx):
    if userEx.user_type == "EndUser":
        return redirect("enduser_dashboard")
    elif userEx.user_type == "RestaurantOwner":
        return redirect("ro_dashboard")
    elif userEx.user_type == "DeliveryPerson":
        return redirect("dp_dashboard")


@not_logged_in
def flogin(request):

    if request.method == "POST":

        if request.POST["email"] and request.POST["password"]:

            try:
                user = User.objects.get(email=request.POST["email"])
            except User.DoesNotExist:
                messages.error(request, "User with email does not exists")
                return render(request, "auth/login.html")

            user = authenticate(
                request, username=user.username, password=request.POST["password"]
            )
            if user is not None:
                login(request, user)
                # return to corresponding dashboard
                try:

                    userEx = UserEx.objects.get(user=user)
                    return dashboard(request, userEx)
                    print(f"userEx {userEx}")

                except Exception as e:
                    print(f"Error {e}")

                return redirect("index")
            else:
                messages.error(request, "Invalid password")
        else:
            messages.error(request, "Please fill in all fields")

    return render(request, "auth/login.html")


@not_logged_in
def fregister(request):

    if request.method == "POST":

        # check for password match
        if request.POST["password"] != request.POST["password2"]:
            messages.error(request, "Passwords do not match")
            return render(request, "auth/register.html")

        # check for users's existanse with email
        try:
            user = User.objects.get(email=request.POST["email"])
            messages.error(request, "User with email already exists")
            return render(request, "auth/register.html")
        except User.DoesNotExist:
            pass
        # check for userEx's existance with phone

        try:
            userEx = UserEx.objects.get(phone=request.POST["phone"])
            messages.error(request, "User with phone already exists")
            return render(request, "auth/register.html")
        except UserEx.DoesNotExist:
            pass

        # generate random username
        username = request.POST["email"].split("@")[0]
        username = username + str(random.randint(0, 1000))

        # Register User
        user = User.objects.create(
            username=username,
            first_name=request.POST["first_name"],
            last_name=request.POST["last_name"],
            email=request.POST["email"],
        )
        user.set_password(request.POST["password"]),

        user.save()

        userEx = UserEx.objects.create(
            user=user,
            phone=request.POST["phone"],
            user_type=request.POST["user_type"],
        )

        print(f"user created {user} ")
        login(request, user)
        return dashboard(request, userEx)

        # create UserEx

    return render(request, "auth/register.html")


def flogout(request):
    logout(request)
    return redirect("index")


### Common
# redirect to dashboard


def redirect_to_dashboard(request):
    if request.user.is_authenticated and request.user.userex:
        return dashboard(request, request.user.userex)

    return redirect("index")


### Restaurant Owner Area


@restricted_access(allowed=["RestaurantOwner"])
def ro_dashboard(request):
    orders = Order.objects.filter(restaurant__owner=request.user)
    return render(
        request,
        "res-owner/dashboard.html",
        context={
            "restaurants_count": Restaurant.objects.filter(owner=request.user).count(),
            "foods_count": Food.objects.filter(restaurant__owner=request.user).count(),
            "orders_count": orders.count(),
            "pending_count": orders.filter(status="Pending").count(),
        },
    )


@restricted_access(allowed=["RestaurantOwner"])
def ro_add_restaurant(request):
    if request.method == "POST":
        # form = RestaurantForm(request.POST, request.FILES)

        # form.instance.owner = request.user

        # form.save()
        # print(form.instance, request.FILES.get("image"))

        addr = Address.objects.create(
            address_text=request.POST["addr_address"],
            city=request.POST["addr_city"],
            state=request.POST["addr_state"],
            zip_code=request.POST["addr_zip_code"],
        )
        addr.save()

        res = Restaurant.objects.create(
            name=request.POST["name"],
            owner=request.user,
            image=request.FILES.get("image"),
            address=addr,
        )

        res.save()
        # request.POST["name"]
        # request.POST["description"]
        # request.FILES["image"]

        messages.success(request, "Restaurant added successfully")
        # print(f"name: {name}, description: {description}, image: {image}")

        # restaurant = Restaurant.objects.create(
        #     name=name, description=description, image=image, owner=request.user
        # )

        return redirect("ro_list_restaurant")

    return render(request, "res-owner/add_restaurant.html")


@restricted_access(allowed=["RestaurantOwner"])
def ro_edit_restaurant(request, id):

    item = Restaurant.objects.filter(id=id, owner=request.user).first()
    if not item:
        return render(request, "error.html", {"error": "Restaurant not found."})

    if request.method == "POST":

        print("handle edit here", item, request.POST)

        item.name = request.POST["name"]
        if request.FILES.get("image"):
            item.image = request.FILES.get("image")
        item.save()

        addr_id = item.address.id
        addr = Address.objects.get(id=addr_id)
        addr.address_text = request.POST["addr_address"]
        addr.city = request.POST["addr_city"]
        addr.state = request.POST["addr_state"]
        addr.zip_code = request.POST["addr_zip_code"]
        addr.save()

        item = Restaurant.objects.get(id=id)

        messages.success(request, "Restaurant edited successfully")
        return render(request, "res-owner/edit_restaurant.html", context={"item": item})

    return render(request, "res-owner/edit_restaurant.html", context={"item": item})


@restricted_access(allowed=["RestaurantOwner"])
def ro_delete_restaurant(request, id):

    item = Restaurant.objects.filter(id=id, owner=request.user).first()
    if not item:
        return render(request, "error.html", {"error": "Restaurant not found."})

    if request.method == "POST":
        item.delete()
        messages.success(request, "Restaurant deleted successfully")
        return redirect("ro_list_restaurant")

    return render(request, "res-owner/delete.html", context={"item": item})


@restricted_access(allowed=["RestaurantOwner"])
def ro_list_restaurant(request):
    restaurants = Restaurant.objects.filter(owner=request.user)
    return render(
        request, "res-owner/list_restaurant.html", {"restaurants": restaurants}
    )


@restricted_access(allowed=["RestaurantOwner"])
def ro_list_food(request):

    items = Food.objects.filter(restaurant__owner=request.user)

    return render(request, "res-owner/list_food.html", context={"items": items})


@restricted_access(allowed=["RestaurantOwner"])
def ro_add_food(request):
    restaurants = Restaurant.objects.filter(owner=request.user)

    if request.method == "POST":
        try:
            restaurant = Restaurant.objects.get(
                id=request.POST["restaurant"], owner=request.user
            )
            food = Food.objects.create(
                name=request.POST["name"],
                description=request.POST["description"],
                price=float(request.POST["price"]),
                restaurant=restaurant,
                image=request.FILES.get("image"),
            )
            food.save()
            messages.success(request, "Food added successfully")

        except Exception as e:
            print(f"Error: {e}")
            messages.error(request, "Error adding food")
        return redirect("ro_list_food")

    return render(
        request,
        "res-owner/add_food.html",
        context={
            "restaurants": restaurants,
        },
    )


@restricted_access(allowed=["RestaurantOwner"])
def ro_edit_food(request, id):

    item = Food.objects.filter(id=id, restaurant__owner=request.user).first()
    if not item:
        return render(request, "error.html", {"error": "Food not found."})
    restaurants = Restaurant.objects.filter(owner=request.user)

    if request.method == "POST":
        try:

            item.name = request.POST["name"]
            item.description = request.POST["description"]
            item.price = float(request.POST["price"])
            if request.FILES.get("image"):
                item.image = request.FILES.get("image")
            item.restaurant = Restaurant.objects.get(
                id=request.POST["restaurant"], owner=request.user
            )
            item.save()

            messages.success(request, "Food edited successfully")
            item = Food.objects.get(id=id)
        except Exception as e:
            print(f"Error: {e}")
            messages.error(request, "Error editing food")

    return render(
        request,
        "res-owner/edit_food.html",
        context={"food": item, "restaurants": restaurants},
    )


@restricted_access(allowed=["RestaurantOwner"])
def ro_delete_food(request, id):

    item = Food.objects.filter(id=id, restaurant__owner=request.user).first()
    if not item:
        return render(request, "error.html", {"error": "Food not found."})

    if request.method == "POST":
        item.delete()
        messages.success(request, "Food deleted successfully")
        return redirect("ro_list_food")

    return render(request, "res-owner/delete.html", context={"item": item})


@restricted_access(allowed=["RestaurantOwner"])
def ro_sales(request):
    orders = Order.objects.filter(restaurant__owner=request.user)
    delivered = orders.filter(status="Delivered")

    # revenue of the last 7 days (delivered orders only), oldest day first
    today = timezone.localdate()
    days = []
    for n in range(6, -1, -1):
        day = today - timedelta(days=n)
        total = (
            delivered.filter(created_at__date=day).aggregate(t=Sum("total"))["t"] or 0
        )
        days.append({"day": day, "total": total})
    max_total = max([d["total"] for d in days] + [1])
    for d in days:
        d["percent"] = int(d["total"] * 100 / max_total)

    top_foods = (
        OrderItem.objects.filter(order__in=delivered)
        .values("food__name")
        .annotate(qty=Sum("quantity"))
        .order_by("-qty")[:5]
    )

    status_counts = []
    for status, _ in Order.CHOICES:
        status_counts.append({"status": status, "count": orders.filter(status=status).count()})

    return render(
        request,
        "res-owner/sales.html",
        context={
            "revenue": delivered.aggregate(t=Sum("total"))["t"] or 0,
            "orders_count": orders.count(),
            "delivered_count": delivered.count(),
            "days": days,
            "top_foods": top_foods,
            "status_counts": status_counts,
        },
    )


@restricted_access(allowed=["EndUser", "RestaurantOwner"])
def order_invoice(request, id):
    if request.userEx.user_type == "EndUser":
        order = Order.objects.filter(id=id, user=request.user).first()
    else:
        order = Order.objects.filter(id=id, restaurant__owner=request.user).first()
    if not order:
        return render(request, "error.html", {"error": "Order not found."})

    lines = []
    for item in OrderItem.objects.filter(order=order):
        lines.append(
            {
                "name": item.food.name,
                "quantity": item.quantity,
                "price": item.food.price,
                "line_total": item.food.price * item.quantity,
            }
        )

    return render(
        request,
        "invoice.html",
        context={"order": order, "lines": lines},
    )


@restricted_access(allowed=["RestaurantOwner"])
def ro_list_orders(request):
    orders = Order.objects.filter(restaurant__owner=request.user).order_by("-pk")
    return render(request, "res-owner/list_orders.html", context={"orders": orders})


def pick_delivery_person():
    # least busy delivery person first, oldest account breaks a tie
    return (
        User.objects.filter(userex__user_type="DeliveryPerson")
        .annotate(
            active_orders=Count(
                "delivery_person",
                filter=Q(delivery_person__status__in=["Confirmed", "Delivering"]),
            )
        )
        .order_by("active_orders", "id")
        .first()
    )


@restricted_access(allowed=["RestaurantOwner"])
def ro_view_order(request, id):
    order = Order.objects.filter(id=id, restaurant__owner=request.user).first()
    if not order:
        return render(request, "error.html", {"error": "Order not found."})

    items = OrderItem.objects.filter(order=order)

    if request.method == "POST":
        if request.POST["status"] not in dict(Order.CHOICES):
            messages.error(request, "Invalid order status")
            return redirect("ro_view_order", id=id)
        order.status = request.POST["status"]
        if request.POST["status"] == "Confirmed" and not order.delivery_person:
            # smart assignment: choose the delivery person with the
            # fewest active (Confirmed / Delivering) orders
            # on order confirmation from restaurant owner

            delivery_person = pick_delivery_person()

            if delivery_person:
                order.delivery_person = delivery_person
            else:
                # order is still confirmed, a delivery person is assigned
                # when the owner saves "Confirmed" again later
                messages.error(
                    request,
                    "No delivery person available right now. Confirm again later to assign one.",
                )
        order.save()
        messages.success(request, "Order status updated successfully")
        order = Order.objects.get(id=id)
        return redirect("ro_view_order", id=id)

    return render(
        request, "res-owner/view_order.html", context={"order": order, "items": items}
    )


@restricted_access(allowed=["RestaurantOwner"])
def ro_edit_order(request, id):
    return HttpResponse(f"Edit Food: {id}")


# Orders should not be deleted to keep track of the data
# @restricted_access(allowed=["RestaurantOwner"])
# def ro_delete_order(request, id):
#     return HttpResponse(f"Delete Food: {id}")


#### User Specific Area
@restricted_access(allowed=["EndUser"])
def enduser_cart(request):
    cart_items = CartItem.objects.filter(cart__user=request.user)

    if request.method == "POST":
        user_cart, _ = Cart.objects.get_or_create(user=request.user)

        # cart item can have items from one restaurant at a time

        food = Food.objects.filter(id=request.POST["food_id"]).first()
        if not food:
            return render(request, "error.html", {"error": "Food not found."})

        try:
            quantity = int(request.POST["quantity"])
        except ValueError:
            quantity = 0
        if quantity < 1:
            messages.error(request, "Quantity must be at least 1.")
            return redirect(request.POST["request_url"])

        for item in cart_items:
            if item.food.restaurant != food.restaurant:
                messages.error(
                    request, "You can only add items from one restaurant at a time."
                )
                return redirect(request.POST["request_url"])

        # same food twice = one cart row with a bigger quantity
        cart_item = cart_items.filter(food=food).first()
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem.objects.create(
                food=food,
                quantity=quantity,
                cart=user_cart,
            )
        cart_item.save()
        messages.success(request, "Item added to cart.")
        return redirect(request.POST["request_url"])

    total = 0
    for item in cart_items:
        total += item.food.price * item.quantity

    return render(
        request,
        "end-user/cart.html",
        context={"items": cart_items, "total": total},
    )


@restricted_access(allowed=["EndUser"])
def enduser_clear_cart(request):
    if request.method == "POST":
        cart_items = CartItem.objects.filter(cart__user=request.user)
        for item in cart_items:
            item.delete()
    return redirect("enduser_cart")


@restricted_access(allowed=["EndUser"])
def enduser_remove_from_cart(request, id):
    if request.method == "POST":
        item = CartItem.objects.filter(id=id, cart__user=request.user).first()
        if item:
            item.delete()
    return redirect("enduser_cart")


# order

# on order. restraunt will accept order and delivery person will be assigned


"""
# randomly choose delivery person
# on order confirmation from restaurant owner

delivery_persons = User.objects.filter(userex__user_type="DeliveryPerson")

if not delivery_persons:
    messages.error(request, "No delivery person available")
    return redirect("enduser_cart")

delivery_person = random.choice(delivery_persons)
"""


@restricted_access(allowed=["EndUser"])
def enduser_checkout(request):
    # on get request, user will add address and confirm order
    if not CartItem.objects.filter(cart__user=request.user).exists():
        messages.error(request, "Your cart is empty.")
        return redirect("enduser_cart")

    if request.method == "POST":

        if not request.POST["delivery_address"].strip():
            messages.error(request, "Please enter a delivery address.")
            return redirect("enduser_checkout")

        user_cart = Cart.objects.get(user=request.user)
        items = CartItem.objects.filter(cart=user_cart)
        order = Order.objects.create(
            user=request.user,
            restaurant=items.first().food.restaurant,
            total=0,
            delivery_address=request.POST["delivery_address"],
        )

        total = 0
        for item in items.all():
            order_item = OrderItem.objects.create(
                order=order,
                food=item.food,
                quantity=item.quantity,
            )
            total += item.food.price * item.quantity
            order_item.save()
            item.delete()
        order.total = total

        order.save()

        ## delete cart items
        items.all().delete()

        messages.success(request, "Order placed successfully")
        # in userdashboard, user will view all order
        # user dashboard == user orders
        return redirect("enduser_orders")

    user_cart = Cart.objects.get(user=request.user)
    cart_items = CartItem.objects.filter(cart__user=request.user)
    total = 0
    for item in cart_items:
        total += item.food.price * item.quantity

    user_cart = {"items": cart_items, "total": total}

    return render(request, "end-user/checkout.html", context=user_cart)

    # on post request,
    # # create order
    # # add order items from cart items
    # # clear cart items
    # # redirect to order list


@restricted_access(allowed=["EndUser"])
def enduser_dashboard(request):
    orders = Order.objects.filter(user=request.user)
    return render(
        request,
        "end-user/dashboard.html",
        context={
            "orders_count": orders.count(),
            "active_count": orders.exclude(
                status__in=["Delivered", "Cancelled", "Returned"]
            ).count(),
            "cart_count": CartItem.objects.filter(cart__user=request.user).count(),
        },
    )


@restricted_access(allowed=["EndUser"])
def enduser_orders(request):
    orders = Order.objects.filter(user=request.user).all().order_by("-pk")
    return render(request, "end-user/orders.html", context={"orders": orders})


@restricted_access(allowed=["EndUser"])
def enduser_order(request, id):
    order = Order.objects.filter(id=id, user=request.user).first()
    if not order:
        return render(request, "error.html", {"error": "Order not found."})
    items = OrderItem.objects.filter(order=order)
    return render(
        request, "end-user/order.html", context={"order": order, "items": items}
    )


#### Delivery Person Area


@restricted_access(allowed=["DeliveryPerson"])
def dp_dashboard(request):
    orders = Order.objects.filter(delivery_person=request.user)
    return render(
        request,
        "delivery-person/dashboard.html",
        context={
            "assigned_count": orders.filter(status="Confirmed").count(),
            "delivering_count": orders.filter(status="Delivering").count(),
            "completed_count": orders.filter(status="Delivered").count(),
        },
    )


@restricted_access(allowed=["DeliveryPerson"])
def dp_orders(request):

    deliverying_orders = Order.objects.filter(
        delivery_person=request.user, status="Delivering"
    )

    assigned_orders = Order.objects.filter(
        delivery_person=request.user, status="Confirmed"
    )

    completed_orders = Order.objects.filter(
        delivery_person=request.user, status="Delivered"
    )

    return render(
        request,
        "delivery-person/orders.html",
        context={
            "assigned_orders": assigned_orders,
            "deliverying_orders": deliverying_orders,
            "completed_orders": completed_orders,
        },
    )


@restricted_access(allowed=["DeliveryPerson"])
def dp_order(request, id):
    order = Order.objects.filter(id=id, delivery_person=request.user).first()
    if not order:
        return render(request, "error.html", {"error": "Order not found."})

    if request.method == "POST":
        # print(f"Order: {order} {request.POST}")
        if (
            request.POST["status"] not in dict(Order.CHOICES)
            or request.POST["payment_status"] not in dict(Order.PAYMENT_CHOICES)
        ):
            messages.error(request, "Invalid order status")
            return redirect("dp_order", id=id)
        order.status = request.POST["status"]
        order.payment_status = request.POST["payment_status"]
        order.save()
        # print("ORDER DELIVERYINGX XXXX ", request.POST)
        messages.success(request, "Order status updated successfully")
        return redirect("dp_order", id=id)

    items = OrderItem.objects.filter(order=order)
    userEx = UserEx.objects.get(user=order.user)

    return render(
        request,
        "delivery-person/order.html",
        context={"order": order, "items": items, "userEx": userEx},
    )
