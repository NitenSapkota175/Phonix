# Installation Guide - Phonix MLM Platform

This guide provides detailed step-by-step instructions for installing and configuring the Phonix MLM platform on various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Installation](#development-installation)
3. [Database Setup](#database-setup)
4. [Redis Installation](#redis-installation)
5. [Environment Configuration](#environment-configuration)
6. [TRC20 Configuration](#trc20-configuration)
7. [Initial Setup](#initial-setup)
8. [Running the Application](#running-the-application)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+), macOS (10.15+), or Windows 10+
- **Python**: 3.9 or higher
- **PostgreSQL**: 12.0 or higher (recommended) or SQLite for development
- **Redis**: 6.0 or higher
- **Git**: For version control
- **Node.js**: Optional, for frontend asset compilation

### Recommended Specs

- **RAM**: 2GB minimum, 4GB+ recommended
- **Storage**: 10GB available space
- **CPU**: 2+ cores

## Development Installation

### 1. Install Python 3.9+

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3.9 python3.9-venv python3.9-dev
```

#### macOS
```bash
# Using Homebrew
brew install python@3.9
```

#### Windows
Download and install from [python.org](https://www.python.org/downloads/)

### 2. Clone the Repository

```bash
cd /path/to/workspace
cd Phonix
```

### 3. Create Virtual Environment

```bash
# Create virtual environment
python3.9 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 4. Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

## Database Setup

### Option 1: SQLite (Development Only)

SQLite is included with Python and requires no additional setup. The database file will be created automatically as `db.sqlite3`.

**Pros**: Zero configuration, quick setup  
**Cons**: Not suitable for production, limited concurrency

### Option 2: PostgreSQL (Recommended)

#### Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Download from [postgresql.org](https://www.postgresql.org/download/)

#### Create Database and User

```bash
# Access PostgreSQL as postgres user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE phonix_db;
CREATE USER phonix_user WITH PASSWORD 'your_secure_password';
ALTER ROLE phonix_user SET client_encoding TO 'utf8';
ALTER ROLE phonix_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE phonix_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE phonix_db TO phonix_user;
\q
```

#### Configure PostgreSQL Connection

Update your `.env` file:
```bash
DB_ENGINE=django.db.backends.postgresql
DB_NAME=phonix_db
DB_USER=phonix_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
```

## Redis Installation

Redis is required for Celery task queue and caching.

### Ubuntu/Debian
```bash
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

### macOS
```bash
brew install redis
brew services start redis

# Verify
redis-cli ping
```

### Windows
Download Redis from [github.com/microsoftarchive/redis](https://github.com/microsoftarchive/redis/releases)

Or use Docker:
```bash
docker run -d -p 6379:6379 redis:latest
```

## Environment Configuration

### 1. Create Environment File

```bash
cp .env.example .env
```

### 2. Configure Essential Variables

Edit `.env` with your preferred editor:

```bash
# Django Settings
SECRET_KEY=generate-a-random-secret-key-here
DEBUG=True  # Set to False in production
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=phonix_db
DB_USER=phonix_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Email Configuration (for notifications)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend  # Development
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=Phonix MLM <noreply@phonix.com>

# Application
SITE_URL=http://localhost:8000
ADMIN_EMAIL=admin@phonix.com
```

### 3. Generate Django Secret Key

```python
# In Python shell
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Or use this one-liner:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## TRC20 Configuration

### 1. Get TronGrid API Key

1. Visit [TronGrid](https://www.trongrid.io/)
2. Sign up for a free account
3. Create a new API key
4. Copy your API key

### 2. Create Master Wallet

> ⚠️ **CRITICAL SECURITY**: The master wallet private key controls all platform funds. Store it extremely securely!

#### For Development/Testing (Shasta Testnet)

```bash
# Use the provided utility script
python generate_master_wallet.py

# Output will show:
# Network: shasta
# Address: TYourTestWalletAddress...
# Private Key: your_private_key_in_hex...
```

#### For Production (Mainnet)

```bash
# Generate production wallet (NEVER share this!)
python generate_master_wallet.py --network mainnet

# IMPORTANT: 
# 1. Store private key in secure password manager
# 2. Create encrypted backup
# 3. Never commit to version control
# 4. Use hardware wallet for additional security (recommended)
```

### 3. Configure TRC20 Settings

Update `.env`:

```bash
# For Testnet (Development)
TRON_API_KEY=your-trongrid-api-key
TRON_NETWORK=shasta

# For Mainnet (Production)
TRON_API_KEY=your-trongrid-api-key
TRON_NETWORK=mainnet

# Master Wallet
MASTER_WALLET_ADDRESS=your-trc20-wallet-address
MASTER_WALLET_KEY=your-private-key-in-hex
```

### 4. Fund Master Wallet (Testnet)

For testing on Shasta testnet:
1. Visit [Shasta Faucet](https://www.trongrid.io/faucet)
2. Enter your wallet address
3. Request test TRX (for gas fees)
4. Request test USDT (for testing withdrawals)

## Initial Setup

### 1. Run Database Migrations

```bash
# Create migration files
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Verify
python manage.py showmigrations
```

### 2. Create Superuser

```bash
python manage.py createsuperuser

# Enter:
# - Username
# - Email
# - Password (min 8 characters)
```

### 3. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 4. (Optional) Load Demo Data

```bash
# Create test users and demo data
python setup_demo_data.py

# This creates:
# - 10 test users with referral relationships
# - Sample subscriptions
# - Test transactions
```

### 5. Verify Installation

```bash
# Check system configuration
python manage.py check

# Test database connection
python manage.py dbshell
# Type \q to exit

# Test Redis connection
python -c "import redis; r = redis.from_url('redis://localhost:6379/0'); print('Redis OK' if r.ping() else 'Redis Failed')"
```

## Running the Application

### Start All Services

You need 4 terminal windows/tabs:

#### Terminal 1: Django Development Server
```bash
cd /path/to/Phonix
source venv/bin/activate  # Windows: venv\Scripts\activate
python manage.py runserver
```
Access at: http://localhost:8000

#### Terminal 2: Celery Worker
```bash
cd /path/to/Phonix
source venv/bin/activate
celery -A phonix worker -l info
```

#### Terminal 3: Celery Beat Scheduler
```bash
cd /path/to/Phonix
source venv/bin/activate
celery -A phonix beat -l info
```

#### Terminal 4: Redis Server (if not running as service)
```bash
redis-server
```

### Verify Services Are Running

1. **Django**: Visit http://localhost:8000
2. **Admin Panel**: Visit http://localhost:8000/admin (login with superuser)
3. **Celery Worker**: Check for "ready" message in terminal
4. **Celery Beat**: Check for scheduled task listings
5. **Redis**: Run `redis-cli ping` (should return PONG)

### Test TRC20 Integration

```bash
# Run TRC20 setup test
python test_trc20_setup.py

# Expected output:
# ✓ Tron client initialized
# ✓ Connected to network: shasta/mainnet
# ✓ USDT contract loaded
# ✓ Master wallet configured
# ✓ Can query balances
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Error

**Error**: `django.db.utils.OperationalError: could not connect to server`

**Solution**:
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start if not running
sudo systemctl start postgresql

# Verify connection settings in .env
```

#### 2. Redis Connection Error

**Error**: `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solution**:
```bash
# Check if Redis is running
redis-cli ping

# Start if not running
redis-server

# Or as service:
sudo systemctl start redis-server
```

#### 3. Celery Worker Not Starting

**Error**: `ImportError: cannot import name 'app' from 'phonix'`

**Solution**:
```bash
# Ensure you're in project root directory
pwd  # Should show /path/to/Phonix

# Check celery.py exists
ls phonix/celery.py

# Reinstall Celery
pip install --upgrade celery
```

#### 4. TRC20 API Errors

**Error**: `TronError: API key not valid`

**Solution**:
1. Verify API key in `.env`
2. Check TronGrid dashboard for key status
3. Ensure no extra spaces in API key
4. Try generating new API key

#### 5. Migration Errors

**Error**: `django.db.migrations.exceptions.InconsistentMigrationHistory`

**Solution**:
```bash
# Reset database (DEVELOPMENT ONLY!)
python manage.py flush
python manage.py migrate --fake-initial

# For production, create new migration:
python manage.py makemigrations --merge
```

#### 6. Static Files Not Loading

**Error**: 404 errors for CSS/JS files

**Solution**:
```bash
# Collect static files
python manage.py collectstatic --noinput

# Check STATIC_ROOT in settings
# Ensure DEBUG=True for development
```

### Getting Help

If you encounter issues not covered here:

1. Check the logs:
   ```bash
   # Django logs (if configured)
   tail -f logs/django.log
   
   # Celery worker output
   # Check Terminal 2
   
   # PostgreSQL logs
   sudo tail -f /var/log/postgresql/postgresql-*.log
   ```

2. Verify configuration:
   ```bash
   # Check environment variables
   python manage.py diffsettings
   
   # Test database
   python manage.py check --database default
   ```

3. Contact support with:
   - Error message (full traceback)
   - Steps to reproduce
   - Python version: `python --version`
   - Django version: `python -m django --version`
   - OS and version

## Next Steps

Once installation is complete:

1. **Configure Email**: Set up SMTP for notifications (see `.env`)
2. **Security Review**: Review [DEPLOYMENT.md](DEPLOYMENT.md) security section
3. **Test Features**: Create test users and test all features
4. **Read Documentation**: Check other docs in `/docs` folder
5. **Production Setup**: Follow [DEPLOYMENT.md](DEPLOYMENT.md) for production

---

**Installation complete!** 🎉 You're ready to start using Phonix MLM Platform.
