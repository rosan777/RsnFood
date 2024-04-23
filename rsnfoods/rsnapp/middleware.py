from django.shortcuts import redirect
from .models import UserEx


scopes = {
    "EndUser": "user",
    "RestaurantOwner": "res-owner",
    "DeliveryPerson": "delivery-person",
}


class UserSpecificMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        print("got a request")
        if request.user.is_authenticated:
            try:
                request.userEx = UserEx.objects.get(user=request.user)

                # check pathname
                # print(f"Path: {request.path.split('/')[1]}")
                # try:
                #     uscope = request.path.split("/")[1]
                #     # print(
                #     #     f"uscope: {uscope}, scope: {request.userEx.user_type}, valid scope: {uscope in scopes.values(),} valid for user: {scopes[request.userEx.user_type] == uscope}"
                #     # )

                #     if uscope in scopes.values():
                #         if scopes[request.userEx.user_type] != uscope:
                #             # return redirect(scopes[request.userEx.user_type] + "/")
                #             scope_url = (
                #                 "/" + scopes[request.userEx.user_type] + "/dashboard"
                #             )
                #             # print("redirecting to: ", scopes[request.userEx.user_type])
                #             return redirect(scope_url)

                #     # if scopes[request.userEx.user_type] != uscope:
                #     #     return redirect(scopes[request.userEx.user_type] + "/")
                # except Exception:
                #     pass

            except Exception:
                request.userEx = None
                pass
            # = UserEx.objects.get(user=request.user)
            # print(f"User: {request.user.username}")

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        # print("sending response")

        return response
