# RsnFood

A simple food ordering website made with Django (university project).

Three kinds of users: customers (EndUser), restaurant owners (RestaurantOwner) and delivery persons (DeliveryPerson). The admin panel is at `/admin`.

## Run locally

Python 3.10 - 3.12 is recommended.

```
cd rsnfoods
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # optional, for /admin
python manage.py runserver
```

Open http://127.0.0.1:8000

## Run tests

```
python manage.py test
```

## Settings

`DJANGO_SECRET_KEY` and `DJANGO_DEBUG` can be set as environment variables. Without them, a local development key and `DEBUG = True` are used.

## Deploy on Vercel

The project is ready for Vercel (root directory: `rsnfoods`). `vercel.json` runs `collectstatic` and `migrate` on every deploy.

Environment variables to set on Vercel:

| Name | Value |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (for example from Neon) |
| `DJANGO_SECRET_KEY` | a long random string |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD` | optional, creates the admin user on deploy |

Note: Vercel's file system is not permanent, so uploaded images do not survive between deployments. Everything else (users, restaurants, foods, orders) is stored in PostgreSQL.
