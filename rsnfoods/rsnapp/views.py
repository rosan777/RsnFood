import random
from django.http import HttpResponse
from django.shortcuts import render, redirect

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from django.contrib import messages

from .forms import RestaurantForm

from .models import UserEx, Restaurant, Address, Food, Cart, CartItem, Order, OrderItem

from .decorators import not_logged_in, login_required, restricted_access

# Create your views here.


### - Public Area
def index(request):

    foods_show_on_site = Food.objects.filter(show_on_site=True)
    restaurants_show_on_site = Restaurant.objects.filter(show_on_site=True)

    return render(
        request,
        "index.html",
        context={"foods": foods_show_on_site, "restaurants": restaurants_show_on_site},
    )


def view_restaurents(request):

    restaurants = Restaurant.objects.all()
    return render(request, "view_restaurents.html", {"restaurants": restaurants})


def view_restaurent(request, id):
    restaurant = Restaurant.objects.get(id=id)
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
        return redirect("delivery_person_dashboard")


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
    return render(request, "res-owner/dashboard.html")


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

    item = Restaurant.objects.get(id=id)

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

    if request.method == "POST":
        item = Restaurant.objects.get(id=id)
        item.delete()
        messages.success(request, "Restaurant deleted successfully")
        return redirect("ro_list_restaurant")

    item = Restaurant.objects.get(id=id)
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
            restaurant = Restaurant.objects.get(id=request.POST["restaurant"])
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

    item = Food.objects.get(id=id)
    restaurants = Restaurant.objects.filter(owner=request.user)

    if request.method == "POST":
        try:

            item.name = request.POST["name"]
            item.description = request.POST["description"]
            item.price = float(request.POST["price"])
            if request.FILES.get("image"):
                item.image = request.FILES.get("image")
            item.restaurant = Restaurant.objects.get(id=request.POST["restaurant"])
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

    if request.method == "POST":
        item = Food.objects.get(id=id)
        item.delete()
        messages.success(request, "Food deleted successfully")
        return redirect("ro_list_food")

    item = Food.objects.get(id=id)
    return render(request, "res-owner/delete.html", context={"item": item})


@restricted_access(allowed=["RestaurantOwner"])
def ro_list_orders(request):
    orders = Order.objects.filter(restaurant__owner=request.user).order_by("-pk")
    return render(request, "res-owner/list_orders.html", context={"orders": orders})


@restricted_access(allowed=["RestaurantOwner"])
def ro_view_order(request, id):
    order = Order.objects.get(id=id)

    items = OrderItem.objects.filter(order=order)

    if request.method == "POST":
        order.status = request.POST["status"]
        if request.POST["status"] == "Confirmed":
            # randomly choose delivery person
            # on order confirmation from restaurant owner

            delivery_persons = User.objects.filter(userex__user_type="DeliveryPerson")

            if not delivery_persons:
                messages.error(request, "No delivery person available right now")
                return redirect("ro_view_order", id=id)

            delivery_person = random.choice(delivery_persons)
            order.delivery_person = delivery_person
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

        food = Food.objects.get(id=request.POST["food_id"])

        for item in cart_items:
            if item.food.restaurant != food.restaurant:
                messages.error(
                    request, "You can only add items from one restaurant at a time."
                )
                return redirect(request.POST["request_url"])

        cart_item = CartItem.objects.create(
            food=food,
            quantity=request.POST["quantity"],
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
    cart_items = CartItem.objects.filter(cart__user=request.user)
    for item in cart_items:
        item.delete()
    return redirect("enduser_cart")


@restricted_access(allowed=["EndUser"])
def enduser_remove_from_cart(request, id):
    item = CartItem.objects.get(id=id)
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
    if request.method == "POST":

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

    return render(
        request,
        "end-user/dashboard.html",
    )


@restricted_access(allowed=["EndUser"])
def enduser_orders(request):
    orders = Order.objects.filter(user=request.user).all().order_by("-pk")
    return render(request, "end-user/orders.html", context={"orders": orders})


@restricted_access(allowed=["EndUser"])
def enduser_order(request, id):
    order = Order.objects.get(id=id)
    items = OrderItem.objects.filter(order=order)
    return render(
        request, "end-user/order.html", context={"order": order, "items": items}
    )


#### Delivery Person Area


@restricted_access(allowed=["DeliveryPerson"])
def dp_dashboard(request):
    return render(request, "delivery-person/dashboard.html")


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
    if request.method == "POST":
        order = Order.objects.get(id=id)
        # print(f"Order: {order} {request.POST}")
        order.status = request.POST["status"]
        order.payment_status = request.POST["payment_status"]
        order.save()
        # print("ORDER DELIVERYINGX XXXX ", request.POST)
        messages.success(request, "Order status updated successfully")
        return redirect("dp_order", id=id)

    order = Order.objects.get(id=id)
    items = OrderItem.objects.filter(order=order)
    userEx = UserEx.objects.get(user=order.user)

    return render(
        request,
        "delivery-person/order.html",
        context={"order": order, "items": items, "userEx": userEx},
    )
