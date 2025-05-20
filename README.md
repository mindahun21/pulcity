# Pulcity

Pulcity is a Django-based event hosting and ticketing backend. It uses Docker, PostgreSQL, Redis, Celery, and Gunicorn to provide a production-ready backend environment.

## 🚀 Getting Started

### 1. Extract the Project

Unzip the project archive and navigate to the project directory:

```bash
unzip pulcity.zip
cd pulcity
```

## ⚙️ Environment Setup

Create a .env file in the root directory with the following structure:

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
DJANGO_ENV=development
ALLOWED_HOSTS=127.0.0.1,localhost

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Database
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=db
DB_PORT=5432

# Redis and Celery
REDIS_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=django-db

# Email (Optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_app_password

# Payment (Optional: Chapa)
CHAPA_SECRET=your_chapa_secret
CHAPA_SECRET_HASH=your_chapa_hash
CHAPA_CALLBACK_URL=http://localhost:5173/account/verified
CHAPA_RETURN_URL=http://localhost:5173/account/verified
```

## 🐳 Running the Project with Docker

Make sure Docker and Docker Compose are installed.

Build and Start the Containers:

```bash
docker compose up --build
```

# Pulcity Project Structure Overview

## apps/

The main Django app directory containing modular apps for different functionalities.

### community/

Handles community-related features.

- Models, views, serializers, tests, and migrations for community features.

### event/

Manages event-related features, split into submodules:

- `category/` — Event categories
- `event/` — Core event logic
- `rating/` — Event rating system
- `ticket/` — Ticketing system for events  
  Includes models, views, serializers, migrations, tests, and URL routing.

### notification/

Handles notifications in the system with its own models, views, serializers, and tests.

### payment/

Manages payment processing and related models, including multiple migrations evolving payment features, views, serializers, and tests.

### user/

User management and authentication, subdivided into:

- `auth/` — Authentication related logic (login, registration, etc.)
- `organization/` — Organization profiles and related user features
- Management commands for exporting schemas  
  Includes models, views, serializers, migrations, signals, tests, and URL routing.

---

## Common Structure Elements in Each App

- `admin.py`: Django admin configurations
- `apps.py`: App configuration
- `migrations/`: Database schema migrations
- `models.py`: Database models
- `serializers.py`: DRF serializers for API data
- `tests.py`: Unit and integration tests
- `urls.py`: API endpoint routing
- `views.py`: API views/controllers

---

## Notes

- The project uses a modular approach with apps focused on single responsibilities.
- Migrations show continuous evolution of the database schema.
- Submodules (e.g., event/category, event/rating) keep domain concerns separated.
- `user` app contains authentication and organization management features.
- Clear separation between community, event management, notifications, payments, and user handling.
