# NoBroker Hostel & Roommate Finder

A web application that helps people find hostels/PGs and compatible roommates
directly — without going through a broker.

This repository currently implements **Member 1's scope: Authentication &
User Management** (the `accounts` app). Hostel listings, roommate matching,
advanced search, and payments will be added by other team members as
separate apps.

## Technology

- Python 3.x
- Django 5.x
- Bootstrap 5
- HTML5 / CSS3 / vanilla JavaScript
- SQLite (development) — swappable to MySQL later purely via `config/settings.py`
- Django ORM & built-in authentication system

## Project structure

```
hostel_roommate/
├── manage.py
├── requirements.txt
├── README.md
├── .gitignore
├── config/              # project settings, root URLs, WSGI/ASGI
├── accounts/            # Member 1: auth & user management (self-contained)
│   ├── models.py        # User (custom), UserProfile
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   ├── backends.py      # login with username OR email
│   ├── signals.py       # auto-creates UserProfile
│   ├── tests.py
│   └── templates/accounts/
├── templates/           # base.html, home.html, 404.html
└── static/              # css/style.css, js/main.js
├──requests_module/
│
├── __init__.py
├── apps.py
├── models.py
├── forms.py
├── views.py
├── urls.py
├── admin.py
├── tests.py
│
├── templates/
│   └── requests_module/
│       ├── favorites.html
│       ├── student_requests.html
│       ├── owner_requests.html
│       ├── notifications.html
│       ├── admin_dashboard.html
│       ├── admin_users.html
│       ├── admin_hostels.html
│       └── admin_reports.html
│
└── static/
    └── requests_module/
        ├── css/
        │   └── member4.css
        └── js/
            └── member4.js
```

## Installation

```bash
python -m venv venv
```

Activate the virtual environment:

- Windows: `venv\Scripts\activate`
- Linux/macOS: `source venv/bin/activate`

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

Create an admin account:

```bash
python manage.py createsuperuser
```

Run the development server:

```bash
python manage.py runserver
```

Open <http://127.0.0.1:8000/> in your browser.

Run the test suite:

```bash
python manage.py test
```

## The `accounts` module

### Custom user model

`accounts.User` extends Django's `AbstractUser` and adds a `role` field
(`TENANT` or `OWNER`, default `TENANT`). `AUTH_USER_MODEL = "accounts.User"`
is set from the start, as required for a safe custom-user setup.
Administrative access uses Django's standard `is_staff` / `is_superuser`
flags — there is no separate "ADMIN" role.

### User profile

`accounts.UserProfile` is a `OneToOneField` to `User` holding optional
fields: `profile_picture`, `phone_number`, `city`, `bio`, `created_at`,
`updated_at`. A profile is created automatically for every new user via a
`post_save` signal (`accounts/signals.py`).

### Pages & URLs

| URL                       | Purpose                                    |
|---------------------------|---------------------------------------------|
| `/`                       | Public home/landing page                   |
| `/register/`              | Registration                               |
| `/login/`                 | Login (username **or** email)              |
| `/logout/`                | Logout                                     |
| `/dashboard/`             | Authenticated dashboard                    |
| `/profile/`               | View own profile                           |
| `/profile/edit/`          | Edit account + profile details             |
| `/password/change/`       | Change password (Django's built-in views)  |
| `/admin/`                 | Django admin                               |

All authenticated-only pages use `@login_required` (or Django's
`LoginRequiredMixin`/class-based equivalents) and redirect anonymous users
to `/login/`.

### Security notes

- Passwords are always hashed via Django's `set_password` / auth system —
  never handled or stored as plain text.
- Login errors are generic ("Invalid username/email or password.") and do
  not reveal whether an account exists.
- CSRF protection is on everywhere; no views use `@csrf_exempt`.
- Users can only edit their own account/profile — the update forms are
  always bound to `request.user`, and `is_staff`/`is_superuser`/password are
  not editable from the profile form.
- Profile picture uploads are validated for file type and size
  (`MAX_PROFILE_IMAGE_SIZE_BYTES` in `config/settings.py`).
- `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` are all overridable via
  environment variables (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`,
  `DJANGO_ALLOWED_HOSTS`) so real secrets never need to be hardcoded.

### For the next developer integrating a new module

- Add your app to `INSTALLED_APPS` in `config/settings.py` and include its
  URLs from `config/urls.py` — don't touch `accounts/`.
- Reference the logged-in user via `request.user`, and relate your own
  models to it with:
  ```python
  owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  ```
- `request.user.role` tells you whether the user is a `TENANT` or `OWNER`.
- Add your own navbar links inside `templates/base.html` once your pages
  exist — none were added preemptively.
- Run `python manage.py makemigrations <yourapp>` for your own models; the
  `accounts` migrations are independent of yours.
