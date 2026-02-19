# 🏢 Club Management SaaS - Backend API

Multi-tenant SaaS platform for sports club management with membership fees, automatic commission tracking, and club communications.

## 📋 Table of Contents
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [API Documentation](#api-documentation)
- [Database](#database)
- [Security](#security)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)

## ✨ Features

### Multi-Tenant Architecture
- ✅ Row-level multi-tenancy with `club_id` isolation
- ✅ SuperAdmin can manage all clubs
- ✅ Clubs have isolated data spaces
- ✅ Automatic tenant filtering in queries

### User Management
- ✅ JWT-based authentication
- ✅ Role-based access control (RBAC)
- ✅ 5 user roles: SuperAdmin, Club Admin, Treasurer, Board, Member
- ✅ Password hashing with bcrypt

### Core Features
- ✅ Club registration and management
- ✅ Member CRUD with status tracking
- ✅ Recurring fee plans (monthly, quarterly, etc.)
- ✅ Automatic fee generation
- ✅ Special/one-time fees
- ✅ Payment processing with partial payments
- ✅ **Automatic commission calculation**
- ✅ Events with attendance tracking
- ✅ Club news/announcements
- ✅ Audit logging

### Business Logic
- ✅ Automatic commission on every payment
- ✅ Configurable commission per club
- ✅ Fee status management (pending/paid/overdue)
- ✅ Payment distribution to multiple fees
- ✅ Overdue fee detection

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.109+
- **Database**: PostgreSQL (SQLAlchemy ORM)
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt (passlib)
- **Validation**: Pydantic
- **Migrations**: Alembic
- **Task Scheduling**: APScheduler
- **Caching**: Redis (optional)

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/              # API route handlers
│   │   ├── auth.py       # Authentication endpoints
│   │   ├── clubs.py      # Club management
│   │   └── ...           # Other endpoints
│   ├── core/             # Core utilities
│   │   ├── config.py     # Configuration
│   │   └── security.py   # Auth & security
│   ├── db/               # Database
│   │   └── database.py   # DB connection
│   ├── models/           # SQLAlchemy models
│   │   └── models.py     # All DB models
│   ├── schemas/          # Pydantic schemas
│   │   └── schemas.py    # Request/response schemas
│   ├── services/         # Business logic
│   └── main.py           # FastAPI app
├── scripts/              # Utility scripts
│   └── init_db.py        # Database initialization
├── tests/                # Test suite
├── requirements.txt      # Python dependencies
└── .env.example          # Environment template
```

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- pip or poetry

### Installation

1. **Clone the repository**
```bash
cd /path/to/cuociente_canotaje_app/backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Setup PostgreSQL database**
```bash
# Create database
createdb club_management

# Or using psql:
psql -U postgres
CREATE DATABASE club_management;
```

6. **Initialize database**
```bash
python scripts/init_db.py
```

This creates:
- Database tables
- SuperAdmin user: `admin@clubmanagement.com` / `admin123`
- Sample club with admin and treasurer

7. **Run the server**
```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

8. **Access API documentation**
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## 📚 API Documentation

### Authentication

#### Login
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "admin@clubmanagement.com",
  "password": "admin123"
}

Response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": { ... }
}
```

#### Get Current User
```bash
GET /api/auth/me
Authorization: Bearer <access_token>
```

### Clubs (SuperAdmin only)

#### Create Club
```bash
POST /api/clubs/
Authorization: Bearer <superadmin_token>
Content-Type: application/json

{
  "name": "My Sports Club",
  "contact_email": "contact@mysportsclub.com",
  "commission_percentage": 5.0
}
```

#### List Clubs
```bash
GET /api/clubs/?page=1&page_size=50
Authorization: Bearer <superadmin_token>
```

#### Get Club Details
```bash
GET /api/clubs/{club_id}
Authorization: Bearer <token>
```

#### Get Club Statistics
```bash
GET /api/clubs/{club_id}/stats
Authorization: Bearer <token>

Response:
{
  "club_id": 1,
  "club_name": "Demo Sports Club",
  "total_members": 150,
  "active_members": 140,
  "pending_fees": 25,
  "total_payments": 500
}
```

## 🗄️ Database

### Schema Overview

**12 Main Tables:**
1. `clubs` - Tenant table
2. `users` - System users with roles
3. `members` - Club members
4. `recurring_fee_plans` - Fee templates
5. `generated_fees` - Actual fee instances
6. `special_fees` - One-time fees
7. `payments` - Payment transactions
8. `commissions` - Platform commissions
9. `events` - Club events
10. `event_attendances` - Attendance tracking
11. `club_news` - Announcements
12. `audit_logs` - Security audit trail

### Key Relationships
- Club → Members (1:N)
- Member → Fees (1:N)
- Payment → Fees (M:N via payment_fees)
- Payment → Commission (1:1)
- Event → Special Fees (1:N)

### Migrations

Using Alembic for database migrations:

```bash
# Initialize Alembic (already done)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 🔒 Security

### Authentication Flow
1. User logs in with email/password
2. Server validates credentials
3. Server generates JWT access token (30 min) and refresh token (7 days)
4. Client includes token in `Authorization: Bearer <token>` header
5. Server validates token on each request

### Multi-Tenant Security
```python
# Every query is filtered by club_id
members = db.query(Member).filter(
    Member.club_id == current_user.club_id
).all()

# SuperAdmin bypasses club restriction
if current_user.role != UserRole.SUPERADMIN:
    verify_club_access(current_user, club_id)
```

### Password Policy
- Minimum 8 characters
- Hashed with bcrypt (12 rounds)
- Never stored in plain text

### Rate Limiting
- 60 requests per minute per IP
- Configurable in settings

## 🧪 Testing

### Run Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=app tests/

# Specific test
pytest tests/test_auth.py
```

### Test Structure
```
tests/
├── conftest.py           # Fixtures
├── test_auth.py          # Auth tests
├── test_clubs.py         # Club tests
├── test_members.py       # Member tests
└── ...
```

## 🚢 Deployment

### Docker

#### Build Image
```bash
docker build -t club-management-backend .
```

#### Run Container
```bash
docker run -d \
  --name club-api \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -e SECRET_KEY="your-secret-key" \
  club-management-backend
```

### Docker Compose

```bash
docker-compose up -d
```

This starts:
- FastAPI backend (port 8000)
- PostgreSQL (port 5432)
- Redis (port 6379)

### Production Checklist

- [ ] Change default passwords
- [ ] Set strong SECRET_KEY
- [ ] Configure DATABASE_URL
- [ ] Disable DEBUG mode
- [ ] Setup HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Setup database backups
- [ ] Configure logging
- [ ] Setup monitoring
- [ ] Enable rate limiting
- [ ] Configure Redis
- [ ] Setup email service

## 🔧 Configuration

### Environment Variables

See `.env.example` for all available variables.

**Required:**
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key (min 32 chars)

**Optional:**
- `DEBUG`: Enable debug mode (default: False)
- `CORS_ORIGINS`: Allowed CORS origins
- `REDIS_URL`: Redis connection string
- `SMTP_*`: Email configuration

## 📊 Business Logic

### Commission Calculation

```python
# When payment is approved:
payment_amount = 100.00
commission_percentage = 5.0

commission_amount = payment_amount * (commission_percentage / 100)
# commission_amount = 5.00

club_net_amount = payment_amount - commission_amount
# club_net_amount = 95.00

# Commission record is created automatically
```

### Fee Generation

Runs daily via scheduler:
1. For each active club
2. For each active recurring fee plan
3. For each active member
4. Check if fee already exists for period
5. If not, create new fee with calculated due date

### Overdue Detection

```python
# Runs daily
if current_date > fee.due_date and fee.status == "pending":
    fee.status = "overdue"
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License.

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Email: support@clubmanagement.com
- Documentation: See ARCHITECTURE.md

---

**Built with ❤️ for sports clubs worldwide**
