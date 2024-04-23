from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("restaurents/", views.view_restaurents, name="view_restaurents"),
    path("restaurents/<int:id>/", views.view_restaurent, name="view_restaurent"),
    # Auth
    path("login/", views.flogin, name="flogin"),
    path("register/", views.fregister, name="fregister"),
    path("logout/", views.flogout, name="logout"),
    path("dashboard/", views.find_and_send_to_dashboard, name="dashboard"),
    # End User Area
    path("user/dashboard", views.enduser_dashboard, name="enduser_dashboard"),
    path("user/orders", views.enduser_orders, name="enduser_orders"),
    path("user/order/<int:id>/", views.enduser_order, name="enduser_order"),
    path("user/cart", views.enduser_cart, name="enduser_cart"),
    path(
        "user/cart/remove/<int:id>/",
        views.enduser_remove_from_cart,
        name="enduser_remove_from_cart",
    ),
    path("user/cart/clear", views.enduser_clear_cart, name="enduser_clear_cart"),
    path("user/cart/checkout", views.enduser_checkout, name="enduser_checkout"),
    # Restaurant Owner Area
    path("res-owner/", views.redirect_to_dashboard),
    path("res-owner/dashboard", views.ro_dashboard, name="ro_dashboard"),
    path(
        "res-owner/list-restaurant",
        views.ro_list_restaurant,
        name="ro_list_restaurant",
    ),
    path("res-owner/add-restaurant", views.ro_add_restaurant, name="ro_add_restaurant"),
    path(
        "res-owner/edit-restaurant/<int:id>/",
        views.ro_edit_restaurant,
        name="ro_edit_restaurant",
    ),
    path(
        "res-owner/delete-restaurant/<int:id>/",
        views.ro_delete_restaurant,
        name="ro_delete_restaurant",
    ),
    path("res-owner/list-food/", views.ro_list_food, name="ro_list_food"),
    path("res-owner/add-food/", views.ro_add_food, name="ro_add_food"),
    path("res-owner/edit-food/<int:id>/", views.ro_edit_food, name="ro_edit_food"),
    path(
        "res-owner/delete-food/<int:id>/", views.ro_delete_food, name="ro_delete_food"
    ),
    path("res-owner/list-order/", views.ro_list_orders, name="ro_list_orders"),
    path("res-owner/view-order/<int:id>/", views.ro_view_order, name="ro_view_order"),
    # res owner won't create orders
    # path("res-owner/edit-order/<int:id>/", views.ro_edit_order, name="ro_edit_order"),
    path("delivery-person/dashboard", views.dp_dashboard, name="dp_dashboard"),
    path("delivery-person/orders", views.dp_orders, name="dp_orders"),
    path("delivery-person/order/<int:id>/", views.dp_order, name="dp_order"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
