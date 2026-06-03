# Chatram — E-Commerce Backend

> **Live:** [https://ecommerce.chatram.in](https://ecommerce.chatram.in)
> **Frontend repo:** [eccommerc-react](https://github.com/jagadeesh-sagar/eccommerc-react)

A production-grade REST API for a full-featured e-commerce platform. Built with Django + DRF, deployed on AWS EC2 behind Nginx, with async task processing via Celery + Redis, real-time order chat via Django Channels WebSockets, media storage on AWS S3, and Razorpay payment integration.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 4.x + Django REST Framework |
| Database | PostgreSQL |
| Auth | JWT (HttpOnly cookies) via `djangorestframework-simplejwt` |
| Async Tasks | Celery + Redis (broker + result backend) |
| Real-time | Django Channels + WebSockets |
| Storage | AWS S3 (product images & videos via presigned URLs) |
| Payments | Razorpay |
| Containerisation | Docker + Docker Compose |
| Reverse Proxy | Nginx |
| Hosting | AWS EC2 |
| Tunnel (dev) | Cloudflare Tunnel |

---

## Features

### Auth & Users
- JWT stored in HttpOnly cookies — no localStorage exposure
- Custom `CookieJWTAuthentication` backend
- Cookie key-based token extraction with leading-space sanitisation
- Buyer and Seller roles with custom permission classes (`IsBuyer`, `IsSeller`)
- RBAC enforced at view level via DRF `permission_classes`

### Products
- Full product CRUD with category, brand, variants (color, size, SKU, stock)
- S3 presigned URL generation for direct browser-to-S3 uploads (images + videos)
- Product images and videos stored in separate S3 prefixes (`images/`, `videos/`)
- Product Q&A — buyers ask, sellers answer via `PATCH /user/product/seller-ans/<id>`

### Cart & Orders
- Cart with line items, quantity management
- Multi-address support per user
- Order creation from cart with address selection
- Seller order view — filtered to only show orders containing seller's products
- Order status tracking: `pending → processing → shipped → delivered → cancelled → returned`

### Payments — Razorpay
- `POST /user/payment/create-order/` — creates a Razorpay order and returns `order_id`, `amount`, `currency`, `key_id`
- `POST /user/payment/verify/` — HMAC-SHA256 signature verification using `razorpay_order_id + "|" + razorpay_payment_id`
- On successful verification, order status is updated and payment record is saved
- Razorpay credentials stored in environment variables (`RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`)
- Test mode supported — switch to live keys in `.env` for production

### Real-time Chat — WebSockets
- Django Channels with Redis channel layer
- Buyer ↔ Seller chat scoped per order (`/ws/chat/<order_id>/`)
- Channel consumer handles `connect`, `disconnect`, `receive`
- Messages are persisted to the database and broadcast to the room group
- Frontend `OrderChatPanel` connects to this WebSocket and renders the chat UI

### Celery Async Tasks
- **Broker:** Redis (`redis://localhost:6379/0`)
- **Result backend:** Redis
- **Beat scheduler:** `django-celery-beat` for periodic tasks

Tasks include:
- `send_order_confirmation_email` — triggered on order creation, sends confirmation to buyer
- `send_seller_notification` — notifies seller when their product is ordered
- `generate_presigned_url` — background URL generation for large media batches
- `update_order_status` — scheduled status transitions (e.g. auto-move to `shipped` after N days)
- `clean_expired_carts` — periodic beat task to purge abandoned carts

### Seller Dashboard API
- `GET /user/seller/registration/` — check if current user has a seller profile
- `POST /user/seller/registration/` — register as seller (sets `verified_status=True`)
- `GET/POST /user/brand/` — brand management
- `GET /user/products/` — list all products (used by seller dashboard Products tab)
- `POST /user/product/create/` — create product with optional variants
- `GET /user/product/image/` — generate S3 presigned URL for upload
- `POST /user/product/image/` — save S3 URL to product image record
- `GET /user/seller/orders/` — orders containing seller's products

---

## Project Structure

```
├── core/                        # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py                  # ASGI config (Channels + Daphne)
│   └── celery.py                # Celery app initialisation
│
├── user/                        # Main app
│   ├── models.py                # User, Seller, Product, Cart, Order, Payment, Chat
│   ├── serializers.py           # DRF serializers
│   ├── views.py                 # APIViews
│   ├── urls.py
│   ├── permissions.py           # IsBuyer, IsSeller
│   ├── authentication.py        # CookieJWTAuthentication
│   ├── consumers.py             # Django Channels WebSocket consumer
│   ├── tasks.py                 # Celery tasks
│   └── routing.py               # WebSocket URL routing
│
├── docker-compose.yml
├── Dockerfile
├── nginx.conf
├── requirements.txt
└── .env.example
```

---

## Local Setup

**Prerequisites:** Python 3.11+, PostgreSQL, Redis, Docker (optional)

### 1. Clone and create virtualenv

```bash
git clone https://github.com/jagadeesh-sagar/django-ecommerce-app.git
cd django-ecommerce-app
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=ecommerce_db
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432

# Redis / Celery
REDIS_URL=redis://localhost:6379/0

# AWS S3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=ap-south-1

# Razorpay
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxx
RAZORPAY_KEY_SECRET=your-razorpay-secret

# JWT Cookie
JWT_COOKIE_NAME=access_token
```

### 3. Database setup

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Run services

```bash
# Django dev server
python manage.py runserver

# Celery worker (separate terminal)
celery -A core worker -l info

# Celery beat — periodic tasks (separate terminal)
celery -A core beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Django Channels requires Daphne (or use runserver for dev)
daphne -p 8000 core.asgi:application
```

---

## Docker Compose

```bash
docker-compose up --build
```

Services started:
- `web` — Django + Daphne (ASGI)
- `db` — PostgreSQL
- `redis` — Redis (Celery broker + Channels layer)
- `celery` — Celery worker
- `celery-beat` — Celery beat scheduler
- `nginx` — Reverse proxy on port 80/443

---

## Razorpay Integration Flow

```
Frontend                          Backend                         Razorpay
   |                                 |                               |
   |-- POST /payment/create-order/ ->|                               |
   |                                 |-- razorpay.order.create() --> |
   |                                 |<-- { order_id, amount } ----- |
   |<-- { order_id, key_id, amount } |                               |
   |                                 |                               |
   |-- Razorpay checkout popup ------|-----------------------------> |
   |<-- { payment_id, signature } ---|------------------------------|
   |                                 |                               |
   |-- POST /payment/verify/ ------->|                               |
   |                                 |-- HMAC-SHA256 verify -------> |
   |                                 |-- Save payment record         |
   |                                 |-- Update order status         |
   |<-- { success: true } -----------|                               |
```

**Signature verification:**
```python
import hmac, hashlib

generated = hmac.new(
    key=RAZORPAY_KEY_SECRET.encode(),
    msg=f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
    digestmod=hashlib.sha256
).hexdigest()

assert generated == razorpay_signature
```

---

## WebSocket Chat

WebSocket endpoint: `ws://<host>/ws/chat/<order_id>/`

**Consumer flow:**
1. Client connects → joins room group `order_<order_id>`
2. Client sends `{ "message": "..." }` → saved to DB + broadcast to group
3. All group members receive `{ "message": "...", "sender": "...", "timestamp": "..." }`
4. On disconnect → leaves room group

**Channel layer config (`settings.py`):**
```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": { "hosts": [("127.0.0.1", 6379)] },
    }
}
```

**Routing (`routing.py`):**
```python
websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<order_id>\d+)/$", consumers.ChatConsumer.as_asgi()),
]
```

---

## AWS S3 — Media Upload Flow

Direct-to-S3 upload using presigned URLs (never proxied through Django):

```
1. GET /user/product/image/?file_name=photo.jpg&file_type=images&product_id=5
   → Django generates presigned PUT URL (valid 5 min) + final file_url

2. PUT <presigned_url>  (browser → S3 directly, no Django auth headers)

3. POST /user/product/image/  { product_id, image_url, is_primary, display_order }
   → Django saves the S3 URL to ProductImage model
```

S3 bucket policy allows public read on `images/` and `videos/` prefixes. CORS configured to allow PUT from the frontend origin.

---

## Key API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/user/login/` | Login, sets JWT cookie |
| POST | `/user/register/` | Register new user |
| POST | `/user/logout/` | Clear JWT cookie |
| GET | `/user/seller/registration/` | Check seller profile exists |
| POST | `/user/seller/registration/` | Register as seller |
| GET/POST | `/user/products/` | List / create products |
| POST | `/user/product/create/` | Create product with variants |
| GET | `/user/product/image/` | Get S3 presigned upload URL |
| POST | `/user/product/image/` | Save uploaded image/video URL |
| GET/POST | `/user/brand/` | List / create brands |
| GET/POST | `/user/cart/` | Get / update cart |
| POST | `/user/order/` | Place order |
| GET | `/user/seller/orders/` | Seller's orders |
| POST | `/user/payment/create-order/` | Create Razorpay order |
| POST | `/user/payment/verify/` | Verify Razorpay payment |
| PATCH | `/user/product/seller-ans/<id>` | Seller answers Q&A |
| WebSocket | `/ws/chat/<order_id>/` | Order chat |

---

## Deployment — AWS EC2

- Instance: Ubuntu 22.04 on EC2 (t3.micro or above)
- Nginx as reverse proxy → forwards HTTP to Daphne (ASGI) on port 8000
- WebSocket upgrade handled by Nginx (`proxy_set_header Upgrade $http_upgrade`)
- Static files served by Nginx from `/static/`
- Media served from S3 (not EC2)
- Celery worker and beat run as `systemd` services
- Redis runs on the same instance
- SSL via Cloudflare (proxy mode) or Let's Encrypt

```nginx
# nginx.conf (WebSocket support)
location /ws/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```

---

## Environment Variables Reference

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` / `False` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | PostgreSQL credentials |
| `REDIS_URL` | Redis connection URL |
| `AWS_ACCESS_KEY_ID` | AWS IAM access key |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret key |
| `AWS_STORAGE_BUCKET_NAME` | S3 bucket name |
| `AWS_S3_REGION_NAME` | S3 region (e.g. `ap-south-1`) |
| `RAZORPAY_KEY_ID` | Razorpay key ID (`rzp_test_...` or `rzp_live_...`) |
| `RAZORPAY_KEY_SECRET` | Razorpay key secret |
| `JWT_COOKIE_NAME` | Cookie name for JWT token |
| `CORS_ALLOWED_ORIGINS` | Frontend origin (e.g. `https://ecommerce.chatram.in`) |

---

## Related

- **Frontend:** [jagadeesh-sagar/eccommerc-react](https://github.com/jagadeesh-sagar/eccommerc-react) — React 19 + Vite + Tailwind CSS
- **Live site:** [https://ecommerce.chatram.in](https://ecommerce.chatram.in)
