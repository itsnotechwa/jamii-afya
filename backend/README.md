# Jamii Afya Backend API

Community emergency medical fund platform for Kenyan chamas/welfare groups, powered by Safaricom M-Pesa and CommsGrid SMS.

---

## Requirements

| Dependency | Version |
|---|---|
| Python | 3.10+ |
| MySQL / MariaDB | 10.5+ |
| Redis | 6+ |
| pip | latest |

---

## Quick Start

### 1. Clone and enter the project

```bash
cd backend/
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install PyMySQL        # MySQL driver (no C headers required)
```

> **Note:** `config/__init__.py` patches PyMySQL to satisfy Django's version gate automatically.

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key — generate with `python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DB_NAME` | MySQL database name (default: `jamii_fund`) |
| `DB_USER` | MySQL username |
| `DB_PASSWORD` | MySQL password |
| `DB_HOST` | MySQL host (default: `localhost`) |
| `REDIS_URL` | Redis broker URL (default: `redis://localhost:6379/0`) |
| `MPESA_CONSUMER_KEY` | Safaricom Daraja consumer key |
| `MPESA_CONSUMER_SECRET` | Safaricom Daraja consumer secret |
| `MPESA_SHORTCODE` | System M-Pesa shortcode |
| `MPESA_PASSKEY` | Lipa Na M-Pesa passkey |
| `MPESA_CALLBACK_URL` | Public HTTPS URL for STK push result (use ngrok in dev) |
| `MPESA_B2C_RESULT_URL` | Public HTTPS URL for B2C result |
| `MPESA_B2C_QUEUE_TIMEOUT_URL` | Public HTTPS URL for B2C timeout |
| `MPESA_B2C_INITIATOR` | Daraja B2C initiator name |
| `MPESA_B2C_SECURITY_CREDENTIAL` | Encrypted B2C security credential |
| `COMMSGRID_API_KEY` | CommsGrid Bearer token (from sms.paygrid.co.ke dashboard) |
| `COMMSGRID_SENDER_ID` | SMS sender ID approved for your account (e.g. `ALXTECH_ENT`) |
| `CORS_ALLOWED_ORIGINS` | Frontend origins, comma-separated |

### 5. Create the MySQL database

```bash
sudo mysql
```

```sql
CREATE DATABASE jamii_fund CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- If connecting as root via password auth (MariaDB):
SET PASSWORD FOR 'root'@'localhost' = PASSWORD('your-password');
FLUSH PRIVILEGES;
EXIT;
```

### 6. Run migrations

```bash
python3 manage.py migrate
```

### 7. Optional — demo seed data

Loads the demo users from the project README (`+254700000000` admin, `+254712345678` member, password `123456`), a group (`JAMIIDEMO01`), a confirmed contribution for the current month, one pending emergency, and a sample hospital. Safe to run repeatedly.

```bash
python3 manage.py seed_demo
```

Use `--reset-passwords` to set demo accounts back to `123456` if they already exist.

Automated tests use a separate database and are **not** affected by this command.

### 8. Create a superuser (admin)

If you did **not** run `seed_demo`, create an admin user manually:

```bash
python3 manage.py createsuperuser
```

You will be prompted for a phone number, email, and password.

### 9. Start the development server

```bash
python3 manage.py runserver
```

The API is now live at **http://127.0.0.1:8000**

---

## Running Celery (Background Tasks)

Celery handles SMS notifications, contribution reminders, and M-Pesa payout triggers. Requires Redis running.

Open a second terminal:

```bash
source .venv/bin/activate
celery -A config.celery worker --loglevel=info
```

To also run the periodic scheduler (contribution deadline reminders):

```bash
celery -A config.celery beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## API Documentation

| URL | Description |
|---|---|
| http://127.0.0.1:8000/ | Redirects to Swagger UI |
| http://127.0.0.1:8000/api/docs/ | **Swagger UI** — interactive, try endpoints live |
| http://127.0.0.1:8000/api/redoc/ | ReDoc — clean reference docs |
| http://127.0.0.1:8000/api/schema/ | Raw OpenAPI 3.0 YAML schema |
| http://127.0.0.1:8000/admin/ | Django admin panel |

### Authenticating in Swagger UI

1. Call `POST /api/auth/login/` with your credentials
2. Copy the `token` value from the response
3. Click the **Authorize 🔒** button at the top of Swagger UI
4. Enter: `Bearer <your_token>`
5. All subsequent requests will carry the JWT automatically

---

## Endpoint Summary

### Auth — `/api/auth/`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register/` | Public | Create account |
| POST | `/api/auth/login/` | Public | Login (phone or email) → JWT |
| POST | `/api/auth/refresh/` | Public | Refresh access token |
| GET/PATCH | `/api/auth/profile/` | JWT | View / update profile |
| POST | `/api/auth/verify/send/` | JWT | Send OTP to phone |
| POST | `/api/auth/verify/confirm/` | JWT | Confirm OTP |

### Groups — `/api/groups/`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/groups/` | JWT | List my groups |
| POST | `/api/groups/` | JWT | Create group |
| GET/PUT/PATCH | `/api/groups/{id}/` | JWT | Group detail / update |
| POST | `/api/groups/join/` | JWT | Join via invite code |
| GET | `/api/groups/{id}/members/` | JWT | List members |
| PATCH | `/api/groups/{id}/update_member/` | JWT (admin) | Change member role/status |

### Contributions — `/api/contributions/`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/contributions/` | JWT | List contributions |
| POST | `/api/contributions/initiate/` | JWT | Trigger M-Pesa STK Push (blocked if in-flight or already confirmed) |
| GET | `/api/contributions/summary/` | JWT | Pool total + paid/unpaid breakdown for a group/period |
| POST | `/api/contributions/send_reminder/` | JWT (admin) | SMS reminders to all unpaid members for a period |
| POST | `/api/contributions/resend/` | JWT | Resend STK Push after failure/cancellation |
| GET | `/api/contributions/transactions/` | JWT | Full M-Pesa transaction history (`?status=` filter) |
| POST | `/api/contributions/recheck/` | JWT | Query Safaricom live for delayed STK push status |

### Emergencies — `/api/emergencies/`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/emergencies/` | JWT | List emergency requests |
| POST | `/api/emergencies/` | JWT | Submit emergency request |
| GET | `/api/emergencies/pending/` | JWT (admin) | All pending requests |
| POST | `/api/emergencies/{id}/vote/` | JWT (admin) | Approve or reject |
| POST | `/api/emergencies/{id}/upload_document/` | JWT | Attach supporting document |

### Notifications — `/api/notifications/`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/notifications/` | JWT | Notification inbox |
| GET | `/api/notifications/unread_count/` | JWT | Unread badge count |
| POST | `/api/notifications/mark_all_read/` | JWT | Mark all as read |
| PATCH | `/api/notifications/{id}/mark_read/` | JWT | Mark one as read |

### M-Pesa Webhooks — `/api/mpesa/` *(Safaricom → server, not for direct use)*
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/mpesa/callback/` | STK Push result |
| POST | `/api/mpesa/b2c/result/` | B2C payout result |
| POST | `/api/mpesa/b2c/timeout/` | B2C timeout |

### Audit — `/api/audit/` *(superadmin only)*
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/audit/` | Full audit trail |

---

## M-Pesa Sandbox Setup (ngrok)

Safaricom requires a public HTTPS URL for callbacks. During development, use [ngrok](https://ngrok.com):

```bash
ngrok http 8000
```

Copy the `https://xxxx.ngrok.io` URL and update your `.env`:

```
MPESA_CALLBACK_URL=https://xxxx.ngrok.io/api/mpesa/callback/
MPESA_B2C_RESULT_URL=https://xxxx.ngrok.io/api/mpesa/b2c/result/
MPESA_B2C_QUEUE_TIMEOUT_URL=https://xxxx.ngrok.io/api/mpesa/b2c/timeout/
```

Restart the server after updating `.env`.

---

## Project Structure

```
backend/
├── config/
│   ├── settings.py       # All configuration (reads from .env)
│   ├── urls.py           # Root URL routing
│   ├── celery.py         # Celery application
│   └── __init__.py       # PyMySQL driver patch
├── apps/
│   ├── users/            # Auth, OTP verification, profiles
│   ├── groups/           # Chama group management
│   ├── contributions/    # M-Pesa contribution payments
│   ├── emergencies/      # Emergency requests and voting
│   ├── mpesa/            # Daraja API integration + webhooks
│   ├── notifications/    # SMS + in-app notifications
│   └── audit/            # Audit log middleware
├── utils/
│   ├── permissions.py    # IsGroupAdmin permission class
│   ├── eligibility.py    # Contribution eligibility checker
│   ├── middleware.py      # Audit log middleware
│   └── sms.py            # Shared SMS utility (wraps CommsGrid)
├── requirements.txt
├── .env.example
└── manage.py
```

---

## Common Commands

```bash
# Check for configuration errors
python3 manage.py check

# Generate new migrations after model changes
python3 manage.py makemigrations

# Apply migrations
python3 manage.py migrate

# Open Django shell
python3 manage.py shell

# Export OpenAPI schema to a file
python3 manage.py spectacular --file schema.yaml
```
