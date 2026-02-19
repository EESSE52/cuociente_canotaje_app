# 🏢 Club Management SaaS Platform

**Multi-tenant SaaS platform for sports club management** with membership fees, automatic commission tracking, and club communications.

## 🎯 Overview

This platform transforms sports club management by providing:
- **Multi-tenant architecture**: Each club gets isolated data space
- **Automated fee collection**: Recurring and special fees with automatic generation
- **Commission tracking**: Platform automatically calculates and tracks commissions on every payment
- **Role-based access**: SuperAdmin, Club Admin, Treasurer, Board, and Member roles
- **Club communications**: Events and news management

## 🏗️ Business Model

1. **Platform Provider** (SuperAdmin) registers clubs
2. Each **Club** receives credentials and isolated workspace
3. **Members** pay fees through the platform
4. **Platform automatically collects commission** on each payment (configurable %)
5. Complete transparency with commission tracking

## 📁 Project Structure

```
cuociente_canotaje_app/
├── backend/                # FastAPI backend (NEW)
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Config & security
│   │   ├── models/        # Database models
│   │   ├── schemas/       # Pydantic schemas
│   │   └── main.py        # FastAPI app
│   ├── scripts/           # Utility scripts
│   ├── Dockerfile         # Docker setup
│   ├── docker-compose.yml # Docker Compose
│   └── README.md          # Backend docs
├── frontend/              # React frontend (TODO)
│   └── src/
├── app_streamlit.py       # Legacy Streamlit app
├── ARCHITECTURE.md        # System architecture
└── README.md              # This file
```

## ✨ Features

### Implemented (Phase 1)
- ✅ **Multi-tenant architecture** with club_id isolation
- ✅ **Database schema** with 12+ tables (PostgreSQL)
- ✅ **JWT authentication** with role-based access control
- ✅ **User management** with 5 role levels
- ✅ **Club CRUD** (SuperAdmin only)
- ✅ **Members, Fees, Payments** data models
- ✅ **Automatic commission calculation**
- ✅ **Events and news** management
- ✅ **Audit logging** for security
- ✅ **API documentation** (Swagger/ReDoc)
- ✅ **Docker deployment** setup

### Coming Soon (Phases 2-7)
- 🔄 Complete API endpoints for all entities
- 🔄 Payment processing workflow
- 🔄 Automatic fee generation (scheduler)
- 🔄 Frontend panels (SuperAdmin, Treasurer, Member)
- 🔄 Email notifications
- 🔄 Payment gateway integration
- 🔄 Advanced reporting

## 🚀 Quick Start

### Backend API

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your database credentials

# Initialize database
python scripts/init_db.py

# Run server
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Access API docs: http://localhost:8000/api/docs

### Docker Deployment

```bash
cd backend
docker-compose up -d
```

This starts:
- PostgreSQL database (port 5432)
- Redis cache (port 6379)
- FastAPI backend (port 8000)

### Default Credentials

After running `init_db.py`:

1. **SuperAdmin**: `admin@clubmanagement.com` / `admin123`
2. **Club Admin**: `admin@demosportsclub.com` / `club123`
3. **Treasurer**: `treasurer@demosportsclub.com` / `treasurer123`

⚠️ **Change these passwords in production!**

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI 0.109+
- **Database**: PostgreSQL 15+ with SQLAlchemy ORM
- **Authentication**: JWT (python-jose)
- **Security**: bcrypt password hashing
- **Validation**: Pydantic
- **Migrations**: Alembic
- **Scheduler**: APScheduler
- **Cache**: Redis

### Frontend (Planned)
- **Framework**: React 18+
- **State**: Redux Toolkit
- **UI**: Material-UI / Tailwind CSS
- **API Client**: Axios
- **PWA**: Progressive Web App support

## 📊 Database Schema

### Core Entities
1. **Clubs**: Tenant table with commission settings
2. **Users**: System users with roles (SuperAdmin, Admin, Treasurer, Board, Member)
3. **Members**: Club members who pay fees
4. **Recurring Fee Plans**: Templates for monthly/quarterly fees
5. **Generated Fees**: Actual fee instances per member
6. **Special Fees**: One-time fees (events, donations, etc.)
7. **Payments**: Payment transactions (supports partial payments)
8. **Commissions**: Auto-generated platform commission records
9. **Events**: Club events with attendance tracking
10. **Club News**: Announcements with publishing
11. **Audit Logs**: Security and compliance tracking

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed schema.

## 🔒 Security

- ✅ JWT authentication with refresh tokens
- ✅ Bcrypt password hashing (12 rounds)
- ✅ Multi-tenant data isolation
- ✅ Role-based access control (RBAC)
- ✅ Rate limiting (60 req/min)
- ✅ Audit logging
- ✅ CORS configuration
- ✅ SQL injection prevention (ORM)

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)**: Complete system architecture and database design
- **[backend/README.md](backend/README.md)**: Backend API documentation
- **API Docs**: http://localhost:8000/api/docs (when running)

## 🧪 Testing

```bash
cd backend
pytest
pytest --cov=app tests/
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open Pull Request

## 📝 MVP Phases

### Phase 1: Foundation ✅ (Current)
- Database schema and models
- Authentication system
- Multi-tenant architecture
- Basic API endpoints

### Phase 2: Core Features (Next)
- Complete CRUD APIs
- Payment processing
- Commission calculation
- Member account view

### Phase 3: Automation
- Automatic fee generation
- Email notifications
- Scheduler setup

### Phase 4: Frontend
- React application
- Three panels (SuperAdmin, Treasurer, Member)
- Mobile-responsive design

### Phase 5: Production
- Testing
- Docker deployment
- CI/CD
- Production launch

## 📞 Support

- **Issues**: Create an issue on GitHub
- **Email**: support@clubmanagement.com
- **Documentation**: See docs/ folder

## 📄 License

This project is licensed under the MIT License.

---

## 🔄 Migration from Legacy App

The original `app_streamlit.py` was a simple kayaking ranking calculator. This has been transformed into a comprehensive **multi-tenant SaaS platform** for complete sports club management.

**Legacy app**: Simple athlete ranking
**New platform**: Full club management with fees, payments, commissions, events, and communications

---

**Built with ❤️ for sports clubs worldwide**

**Version**: 1.0.0 (MVP Phase 1 Complete)
**Last Updated**: 2026-02-19

