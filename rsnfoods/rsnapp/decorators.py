from django.shortcuts import redirect, render


# not logged in decorator
def not_logged_in(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("index")
        else:
            return view_func(request, *args, **kwargs)

    return wrapper_func


# login required decorator
def login_required(view_func):
    def wrapper_func(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("flogin")
        else:
            return view_func(request, *args, **kwargs)

    return wrapper_func


def restricted_access(allowed=[]):
    def res_owner_only(view_func):
        def wrapper_func(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect("flogin")

            try:
                if request.userEx.user_type in allowed:
                    print("allowed")
                    return view_func(request, *args, **kwargs)
                raise Exception("You are not authorized to view this page.")
            except Exception:
                print("not allowed")
                return render(
                    request,
                    "error.html",
                    {"error": "You are not authorized to view this page."},
                )

        return wrapper_func

    return res_owner_only
