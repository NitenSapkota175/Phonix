# Phonix MLM Platform

A comprehensive Multi-Level Marketing (MLM) investment platform built with Django, featuring a 20-level referral system, automated earnings distribution, TRC20 USDT integration, and rank-based bonuses.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Django](https://img.shields.io/badge/Django-4.2.7-green.svg)
![Celery](https://img.shields.io/badge/Celery-5.3.4-brightgreen.svg)
![License](https://img.shields.io/badge/License-Proprietary-red.svg)

## 🌟 Key Features

### Investment System
- **Tiered Subscription Packages** with monthly returns:
  - Tier 1: $50 - $3,000 (6% Monthly)
  - Tier 2: $3,001 - $5,000 (8% Monthly)
  - Tier 3: $5,001+ (10% Monthly)
- **Daily Bond Income** distributed Monday-Friday
- **3x Earnings Cap** on all subscriptions
- **Registration Bonus** ($10) for new users

### Multi-Level Marketing
- **20-Level Referral Commission Structure**
- **Direct Referral Requirements** for higher levels
- **Generation Income** with tiered commission rates (10% down to 0.3%)
- **Automatic Commission Distribution** via Celery tasks
- **3x User Earnings Cap** across all income sources

### Rank & Rewards System
- **6 Rank Tiers** based on leg volumes:
  - Connector, Builder, Professional, Executive, Director, Crown
- **Weekly Bonus Distribution** ($50 - $5,000)
- **52-Week Bonus Period** per rank achievement
- **Automatic Rank Advancement** checks

### Cryptocurrency Integration
- **TRC20 USDT Deposits** - Automatic detection and crediting
- **TRC20 USDT Withdrawals** - Automated processing with 5% fee
- **Unique Deposit Addresses** for each user
- **Master Wallet Management** for centralized fund control
- **Real-time Blockchain Monitoring** every minute

### Automation
- **Celery + Redis** for task queue management
- **Scheduled Tasks** for income distribution
- **Automated Earnings Engine** with cap enforcement
- **Transaction Tracking** with complete audit trail

## 📋 Table of Contents

- [System Requirements](#system-requirements)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Documentation](#documentation)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Deployment](#deployment)
- [Support](#support)

## 💻 System Requirements

- **Python**: 3.9 or higher
- **Database**: PostgreSQL 12+ (SQLite for development)
- **Cache/Queue**: Redis 6.0+
- **OS**: Linux, macOS, or Windows

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
cd /Users/yug/Desktop/Phonix

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# IMPORTANT: Set SECRET_KEY, database credentials, and TRC20 API keys
nano .env
```

### 3. Initialize Database

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# (Optional) Load demo data
python setup_demo_data.py
```

### 4. Start Services

```bash
# Terminal 1: Start Django development server
python manage.py runserver

# Terminal 2: Start Celery worker
celery -A phonix worker -l info

# Terminal 3: Start Celery Beat scheduler
celery -A phonix beat -l info

# Terminal 4: Start Redis (if not running as service)
redis-server
```

### 5. Access the Application

- **Frontend**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **Dashboard**: http://localhost:8000/dashboard

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Django Web Server                       │
├─────────────────────────────────────────────────────────────┤
│  Accounts  │  Investment  │  Wallet  │  Earnings  │  Ranks  │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    ┌─────────────────┐
                    │  PostgreSQL DB  │
                    └─────────────────┘
                              ↓
              ┌───────────────┴───────────────┐
              ↓                               ↓
    ┌─────────────────┐           ┌─────────────────┐
    │  Celery Worker  │←──────────│  Redis Queue    │
    └─────────────────┘           └─────────────────┘
              ↓                               ↑
    ┌─────────────────┐           ┌─────────────────┐
    │  Celery Beat    │───────────│  Beat Scheduler │
    └─────────────────┘           └─────────────────┘
              ↓
    ┌─────────────────┐
    │  TRON Blockchain│
    │  (TRC20 USDT)   │
    └─────────────────┘
```

## 📚 Documentation

Comprehensive documentation is available in the `/docs` directory:

- **[INSTALLATION.md](INSTALLATION.md)** - Detailed setup and installation guide
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design and architecture
- **[DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)** - Database models and relationships
- **[API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)** - API endpoints and usage
- **[USER_GUIDE.md](docs/USER_GUIDE.md)** - Feature documentation for end users
- **[DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)** - Developer reference and guidelines
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment instructions
- **[TRC20_TESTING.md](TRC20_TESTING.md)** - TRC20 integration testing guide

## 📁 Project Structure

```
Phonix/
├── accounts/              # User authentication and management
│   ├── models.py         # Custom User model with MLM fields
│   ├── views.py          # Auth views
│   └── utils.py          # MLM utility functions
├── investment/           # Subscription and investment management
│   ├── models.py         # Subscription model
│   ├── views.py          # Investment views
│   └── urls.py
├── wallet/               # Cryptocurrency wallet operations
│   ├── models.py         # Transaction, DepositAddress models
│   ├── tasks.py          # Deposit monitoring, withdrawal processing
│   ├── tron_utils.py     # TRC20 blockchain utilities
│   └── views.py
├── earnings/             # Commission and earnings distribution
│   ├── models.py         # Commission model and rates
│   ├── tasks.py          # Daily bond income, generation income
│   └── views.py
├── ranks/                # Rank advancement and bonuses
│   ├── models.py         # Rank model
│   ├── tasks.py          # Rank checks, weekly bonuses
│   └── views.py
├── dashboard/            # User dashboard
│   ├── views.py
│   └── templates/
├── phonix/               # Project settings
│   ├── settings.py       # Django and Celery configuration
│   ├── celery.py         # Celery app configuration
│   └── urls.py
├── static/               # Static files (CSS, JS, images)
├── templates/            # HTML templates
├── manage.py             # Django management script
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

## ⚙️ Configuration

### Critical Environment Variables

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False  # Set to False in production
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=phonix_db
DB_USER=phonix_user
DB_PASSWORD=your-secure-password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# TRC20 Blockchain
TRON_API_KEY=your-trongrid-api-key
TRON_NETWORK=mainnet  # or 'shasta' for testnet

# Master Wallet (CRITICAL - Keep Secure!)
MASTER_WALLET_ADDRESS=your-trc20-wallet-address
MASTER_WALLET_KEY=your-private-key-in-hex
```

> ⚠️ **Security Warning**: The `MASTER_WALLET_KEY` provides access to all platform funds. Never commit this to version control and store it securely.

## 🏃 Running the Application

### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Start all services (use separate terminals)
python manage.py runserver
celery -A phonix worker -l info
celery -A phonix beat -l info
redis-server
```

### Production Mode

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete production deployment instructions including:
- Gunicorn configuration
- Nginx setup
- Supervisor for process management
- SSL/TLS configuration
- Database optimization
- Security hardening

## 🧪 Testing

### Create Test Users

```bash
# Create test users with referral relationships
python create_test_users.py
```

### Verify MLM Structure

```bash
# Verify referral chains and commission calculations
python verify_mlm.py
```

### Test TRC20 Integration

```bash
# Test wallet generation and blockchain connectivity
python test_trc20_setup.py
```

### Run Unit Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts
python manage.py test investment
python manage.py test wallet
```

## 🚀 Deployment

### Quick Deployment Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Configure PostgreSQL database
- [ ] Set strong `SECRET_KEY`
- [ ] Configure secure `MASTER_WALLET_KEY`
- [ ] Enable SSL/TLS certificates
- [ ] Set up Nginx reverse proxy
- [ ] Configure Gunicorn with workers
- [ ] Set up Supervisor for process management
- [ ] Configure Redis for production
- [ ] Set up automated backups
- [ ] Enable monitoring and logging
- [ ] Configure email settings
- [ ] Test TRC20 integration on testnet first

Refer to [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## 🔐 Security Considerations

1. **Private Keys**: Never expose `MASTER_WALLET_KEY` in logs or error messages
2. **User Funds**: Individual deposit addresses have encrypted private keys
3. **3x Cap**: Enforced at multiple levels to prevent over-earning
4. **Transaction Validation**: All blockchain transactions are verified
5. **CSRF Protection**: Enabled for all POST requests
6. **SQL Injection**: Protected via Django ORM
7. **XSS Protection**: Template escaping enabled by default

## 📊 Key Business Logic

### Commission Distribution (20 Levels)

- **Level 1**: 10% (Direct referrals)
- **Level 2**: 5%
- **Level 3-5**: 3-2%
- **Level 6-10**: 1%
- **Level 11-15**: 0.5%
- **Level 16-20**: 0.3%

**Direct Requirements**: Levels 3+ require increasing direct referrals (2-10)

### Earnings Cap (3x Rule)

All earnings (daily bond income, commissions, bonuses) are subject to a 3x cap:
- User invests $1,000 across subscriptions
- Maximum lifetime earnings = $3,000
- System automatically stops earnings when cap is reached

### Rank Requirements

| Rank | Main Leg | Other Legs | Weekly Bonus |
|------|----------|------------|--------------|
| Connector | $5,000 | $5,000 | $50 |
| Builder | $10,000 | $10,000 | $200 |
| Professional | $20,000 | $20,000 | $500 |
| Executive | $50,000 | $50,000 | $1,000 |
| Director | $100,000 | $100,000 | $2,000 |
| Crown | $200,000 | $200,000 | $5,000 |

## 🛠️ Useful Commands

```bash
# Database
python manage.py makemigrations
python manage.py migrate
python manage.py dbshell

# Admin
python manage.py createsuperuser
python manage.py changepassword username

# Shell
python manage.py shell
python manage.py shell_plus  # If django-extensions installed

# Static files
python manage.py collectstatic

# Celery
celery -A phonix worker -l info
celery -A phonix beat -l info
celery -A phonix inspect active
celery -A phonix purge

# Testing
python manage.py test
python manage.py test --keepdb  # Reuse test database
```

## 📞 Support

For technical support or questions:

- **Email**: admin@phonix.com
- **Documentation**: Check `/docs` folder
- **Issues**: Report bugs or feature requests

## 📄 License

This is proprietary software. All rights reserved.

## 🙏 Acknowledgments

- Django Framework
- Celery Distributed Task Queue
- TronPy for TRC20 integration
- Redis for caching and queuing

---

**Built with ❤️ by the Phonix Team**
