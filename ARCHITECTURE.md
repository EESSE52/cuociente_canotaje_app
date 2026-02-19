# 🏗️ Multi-Tenant SaaS Platform - Architecture & Database Design

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Multi-Tenant Architecture](#multi-tenant-architecture)
3. [Database Schema](#database-schema)
4. [API Structure](#api-structure)
5. [Security & Authentication](#security--authentication)
6. [Business Logic](#business-logic)
7. [MVP Phases](#mvp-phases)

---

## 🎯 System Overview

### Purpose
Multi-tenant SaaS platform for sports club management with:
- Membership management
- Fee collection & tracking
- Automatic commission calculation
- Club communications (news & events)
- Multi-level role-based access control

### Business Model
- **SuperAdmin** (Platform Provider) registers clubs
- Each **Club** receives credentials and isolated space
- **Members** pay fees through the platform
- **Platform** automatically collects commission on each payment
- Commission is configurable per club

---

## 🏢 Multi-Tenant Architecture

### Tenant Isolation Strategy
**Row-Level Multi-Tenancy** with `club_id` column:

```
Every table (except Club) includes:
- club_id: Foreign key to clubs table
- Indexes on (club_id, ...) for query optimization
- Application-level filtering ensures data isolation
```

### Advantages
✅ Simple implementation
✅ Cost-effective (single database)
✅ Easy backups and maintenance
✅ Good performance with proper indexing

### Security Measures
- All queries filtered by `club_id` at application level
- JWT tokens include `club_id` claim
- API middleware verifies club access
- SuperAdmin role bypasses club restrictions

---

## 📊 Database Schema

### Core Tables

#### 1. **clubs** (Main tenant table)
```sql
- id: Primary key
- name: Unique club name
- contact_email: Club contact
- commission_percentage: Platform commission (5.0 default)
- status: active | suspended | inactive
- registration_date: When club joined
- phone, address, logo_url, primary_color: Settings
- created_at, updated_at: Timestamps
```

#### 2. **users** (System users with roles)
```sql
- id: Primary key
- club_id: FK to clubs (null for SuperAdmin)
- email: Unique login email
- hashed_password: Bcrypt hashed password
- full_name: User's full name
- role: superadmin | club_admin | treasurer | board | member
- is_active, is_verified: Status flags
- member_id: Optional FK to members (if user is also a member)
- created_at, updated_at, last_login: Timestamps
```

**Role Hierarchy:**
1. **SuperAdmin**: Full platform access, manages all clubs
2. **Club Admin**: Full access to their club
3. **Treasurer**: Manages members, fees, payments
4. **Board**: Limited access (view reports)
5. **Member**: View own account and pay fees

#### 3. **members** (Club members who pay fees)
```sql
- id: Primary key
- club_id: FK to clubs
- first_name, last_name: Personal info
- email, phone: Contact info
- date_of_birth: Optional birthday
- member_number: Custom member ID
- member_type: regular | founding_contributor | exempt
- status: active | inactive | suspended
- join_date, end_date: Membership period
- notes: Additional info
- created_at, updated_at: Timestamps
```

#### 4. **recurring_fee_plans** (Monthly/quarterly fee templates)
```sql
- id: Primary key
- club_id: FK to clubs
- name, description: Plan info
- amount: Base fee amount
- periodicity: monthly | quarterly | biannual | annual
- due_day_of_month: When fee is due (1-31)
- discount_percentage: Optional discount
- is_active: Enable/disable plan
- created_at, updated_at: Timestamps
```

#### 5. **generated_fees** (Actual fee instances per member)
```sql
- id: Primary key
- club_id: FK to clubs
- member_id: FK to members
- fee_plan_id: FK to recurring_fee_plans
- amount: Original amount
- discount_amount: Discount applied
- final_amount: Amount to pay
- period_start, period_end: Fee period
- due_date: Payment deadline
- status: pending | paid | overdue | partially_paid
- paid_amount: Amount paid so far
- created_at, updated_at: Timestamps
```

#### 6. **special_fees** (One-time fees)
```sql
- id: Primary key
- club_id: FK to clubs
- member_id: FK to members
- event_id: Optional FK to events
- name, description: Fee details
- fee_type: event_registration | transport | food | founding_contributor | extraordinary | donation | other
- amount: Fee amount
- due_date: Payment deadline
- status: pending | paid | overdue | partially_paid
- paid_amount: Amount paid
- created_at, updated_at: Timestamps
```

#### 7. **payments** (Payment transactions)
```sql
- id: Primary key
- club_id: FK to clubs
- member_id: FK to members
- amount: Payment amount
- payment_method: cash | bank_transfer | credit_card | debit_card | online_gateway | other
- payment_date: When payment occurred
- status: pending | approved | rejected | cancelled
- reference_number: External reference
- receipt_url: Receipt file URL
- notes: Additional notes
- processed_by_user_id: FK to users (who processed)
- created_at, updated_at: Timestamps
```

**Many-to-Many Relationships:**
- `payment_fees`: Links payments to generated_fees
- `payment_special_fees`: Links payments to special_fees
- Both include `amount_applied` for partial payments

#### 8. **commissions** (Platform commission records)
```sql
- id: Primary key
- club_id: FK to clubs
- payment_id: FK to payments
- payment_amount: Total payment
- commission_percentage: % used for calculation
- commission_amount: Platform's commission
- club_net_amount: Club's net amount
- calculated_at: When calculated
```

**Business Rules:**
- Auto-generated when payment is approved
- Immutable (cannot be edited/deleted)
- Uses club's commission_percentage at time of payment

#### 9. **events** (Club events)
```sql
- id: Primary key
- club_id: FK to clubs
- name, description: Event details
- event_date: When event occurs
- location: Event location
- registration_fee: Optional fee amount
- auto_generate_fee: If true, create special_fee for attendees
- is_active: Enable/disable
- created_at, updated_at: Timestamps
```

#### 10. **event_attendances** (Attendance confirmations)
```sql
- id: Primary key
- event_id: FK to events
- member_id: FK to members
- confirmed: True if attending
- confirmed_at: When confirmed
```

#### 11. **club_news** (Club announcements)
```sql
- id: Primary key
- club_id: FK to clubs
- title, content: News details
- author_id: FK to users
- is_published: Published flag
- publish_date: When to publish (scheduling)
- attachment_url: Optional file
- created_at, updated_at: Timestamps
```

#### 12. **audit_logs** (Security audit trail)
```sql
- id: Primary key
- club_id: Optional FK to clubs
- user_id: FK to users
- action: Action performed (e.g., "create_payment")
- entity_type: Type of entity (e.g., "payment")
- entity_id: ID of entity
- changes: JSON with before/after
- ip_address, user_agent: Request info
- created_at: Timestamp
```

---

## 🔌 API Structure

### Base URL: `/api`

### Authentication Endpoints (`/api/auth`)
```
POST   /login          - Login with email/password
POST   /refresh        - Refresh access token
GET    /me             - Get current user info
POST   /register       - Register new user
```

### Club Management (`/api/clubs`)
```
POST   /               - Create club (SuperAdmin)
GET    /               - List all clubs (SuperAdmin)
GET    /{id}           - Get club details
PUT    /{id}           - Update club (SuperAdmin)
DELETE /{id}           - Delete club (SuperAdmin)
GET    /{id}/stats     - Get club statistics
```

### User Management (`/api/users`)
```
POST   /               - Create user
GET    /               - List users (filtered by club)
GET    /{id}           - Get user details
PUT    /{id}           - Update user
DELETE /{id}           - Delete user
```

### Member Management (`/api/members`)
```
POST   /               - Create member
GET    /               - List members (club-filtered)
GET    /{id}           - Get member details
PUT    /{id}           - Update member
DELETE /{id}           - Delete member
POST   /bulk           - Bulk import members (CSV)
GET    /{id}/account   - Get member account status
```

### Fee Plans (`/api/fee-plans`)
```
POST   /               - Create fee plan
GET    /               - List fee plans
GET    /{id}           - Get plan details
PUT    /{id}           - Update plan
DELETE /{id}           - Delete plan
POST   /{id}/generate  - Manually generate fees for all members
```

### Generated Fees (`/api/fees`)
```
POST   /               - Create fee (manual)
GET    /               - List fees (filters: member, status, due_date)
GET    /{id}           - Get fee details
PUT    /{id}           - Update fee
DELETE /{id}           - Delete fee
GET    /overdue        - List overdue fees
```

### Special Fees (`/api/special-fees`)
```
POST   /               - Create special fee
GET    /               - List special fees
GET    /{id}           - Get special fee details
PUT    /{id}           - Update special fee
DELETE /{id}           - Delete special fee
```

### Payments (`/api/payments`)
```
POST   /               - Create payment
GET    /               - List payments
GET    /{id}           - Get payment details
PUT    /{id}           - Update payment status
POST   /{id}/approve   - Approve payment (triggers commission)
POST   /{id}/cancel    - Cancel payment
GET    /reports        - Payment reports
```

### Commissions (`/api/commissions`)
```
GET    /               - List commissions (SuperAdmin)
GET    /{id}           - Get commission details
GET    /reports        - Commission reports
GET    /club/{id}      - Get commissions for specific club
```

### Events (`/api/events`)
```
POST   /               - Create event
GET    /               - List events
GET    /{id}           - Get event details
PUT    /{id}           - Update event
DELETE /{id}           - Delete event
POST   /{id}/attend    - Confirm attendance
GET    /{id}/attendees - List attendees
```

### News (`/api/news`)
```
POST   /               - Create news
GET    /               - List news
GET    /{id}           - Get news details
PUT    /{id}           - Update news
DELETE /{id}           - Delete news
POST   /{id}/publish   - Publish news
```

---

## 🔒 Security & Authentication

### JWT Token Structure
```json
{
  "sub": 123,              // User ID
  "email": "user@club.com",
  "role": "treasurer",
  "club_id": 5,            // Null for SuperAdmin
  "exp": 1234567890,       // Expiration
  "type": "access"         // access | refresh
}
```

### Permission Matrix

| Role         | Own Club | Other Clubs | Platform |
|--------------|----------|-------------|----------|
| SuperAdmin   | ✅ All   | ✅ All      | ✅ Full  |
| Club Admin   | ✅ Full  | ❌          | ❌       |
| Treasurer    | ✅ CRUD  | ❌          | ❌       |
| Board        | ✅ Read  | ❌          | ❌       |
| Member       | ✅ Self  | ❌          | ❌       |

### Security Features
- ✅ Bcrypt password hashing (12 rounds)
- ✅ JWT with expiration
- ✅ Rate limiting (60 requests/minute)
- ✅ Multi-tenant data isolation
- ✅ Audit logging for sensitive actions
- ✅ CORS configuration
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ Input validation (Pydantic)

---

## 💼 Business Logic

### Commission Calculation Flow

```
1. Member makes payment
2. Payment status = "pending"
3. Treasurer/Admin approves payment
4. System calculates commission:
   - commission_amount = payment_amount × (commission_percentage / 100)
   - club_net_amount = payment_amount - commission_amount
5. Commission record created (immutable)
6. Payment status = "approved"
7. Fee statuses updated based on payments
```

### Fee Generation Flow

```
1. Scheduler runs daily (configured hour)
2. For each active club:
   - Get all active recurring fee plans
   - For each active member:
     - Check if fee already exists for period
     - If not, create generated_fee:
       - Calculate due_date from plan
       - Apply discounts if applicable
       - Set status = "pending"
3. Check overdue fees:
   - If current_date > due_date AND status = "pending"
   - Update status = "overdue"
```

### Payment Distribution Flow

```
Member pays $100 for 2 fees:
- Fee A: $60 owed
- Fee B: $50 owed

Payment record created: $100

Distribution:
1. Apply $60 to Fee A → Fee A status = "paid"
2. Apply $40 to Fee B → Fee B status = "partially_paid"

payment_fees table:
- payment_id=1, fee_id=A, amount_applied=60
- payment_id=1, fee_id=B, amount_applied=40
```

---

## 🚀 MVP Phases

### Phase 1: Foundation (Weeks 1-4) ✅
- [x] Database schema design
- [x] SQLAlchemy models
- [x] FastAPI application structure
- [x] Authentication system (JWT)
- [x] Role-based access control
- [x] Multi-tenant architecture
- [ ] Basic API endpoints (Clubs, Users, Members)
- [ ] Database migrations (Alembic)

### Phase 2: Core Features (Weeks 5-8)
- [ ] Recurring fee plans CRUD
- [ ] Generated fees management
- [ ] Special fees
- [ ] Payment processing
- [ ] Commission calculation
- [ ] Member account view
- [ ] Basic admin dashboard

### Phase 3: Automation (Weeks 9-10)
- [ ] Scheduler setup (APScheduler)
- [ ] Automatic fee generation
- [ ] Overdue fee detection
- [ ] Email notifications (reminders)
- [ ] Weekly treasurer summary

### Phase 4: Communication (Weeks 11-12)
- [ ] Events CRUD
- [ ] Attendance tracking
- [ ] Automatic event fees
- [ ] Club news CRUD
- [ ] News publishing/scheduling

### Phase 5: Frontend (Weeks 13-16)
- [ ] React application setup
- [ ] SuperAdmin panel
- [ ] Treasurer panel
- [ ] Member panel
- [ ] Mobile-responsive design

### Phase 6: Polish & Deploy (Weeks 17-18)
- [ ] Testing (unit, integration)
- [ ] Documentation
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Production deployment

### Phase 7: Advanced Features (Future)
- [ ] Online payment gateway integration
- [ ] Advanced reporting & analytics
- [ ] CSV/Excel exports
- [ ] Multi-language support
- [ ] Mobile app (PWA)

---

## 📝 Development Guidelines

### Code Standards
- **Python**: PEP 8, type hints, docstrings
- **SQL**: Alembic migrations for schema changes
- **API**: RESTful design, OpenAPI documentation
- **Security**: No hardcoded secrets, environment variables

### Testing Strategy
- Unit tests for business logic
- Integration tests for APIs
- End-to-end tests for critical flows
- Load testing for multi-tenant isolation

### Deployment
```
Docker containers:
- Backend (FastAPI + Gunicorn)
- Database (PostgreSQL)
- Redis (caching/sessions)
- Frontend (React + Nginx)

Cloud options:
- AWS (ECS, RDS, ElastiCache)
- Google Cloud (Cloud Run, Cloud SQL)
- DigitalOcean (App Platform, Managed DB)
```

---

## 🎯 Key Success Metrics

### Technical
- API response time < 200ms (p95)
- Database query time < 50ms (p95)
- 99.9% uptime
- Zero data leaks between tenants

### Business
- Club onboarding < 15 minutes
- Payment processing < 2 minutes
- Commission tracking 100% accurate
- Member satisfaction > 4.5/5

---

## 📞 Support & Maintenance

### Monitoring
- Application logs
- Database performance
- API error rates
- Commission accuracy

### Backups
- Daily automated backups
- Point-in-time recovery
- Cross-region replication

### Updates
- Weekly dependency updates
- Monthly feature releases
- Quarterly security audits

---

**Created**: 2026-02-19
**Version**: 1.0.0
**Status**: In Development
