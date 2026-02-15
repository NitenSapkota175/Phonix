# API Documentation - Phonix MLM Platform

This document provides comprehensive information about the Phonix MLM platform's views, URLs, and API endpoints.

> **Note**: The platform currently uses Django views with templates. A REST API using Django REST Framework can be added for mobile apps or third-party integrations.

## Table of Contents

1. [URL Structure](#url-structure)
2. [Dashboard Views](#dashboard-views)
3. [Investment Views](#investment-views)
4. [Wallet Views](#wallet-views)
5. [Authentication Views](#authentication-views)
6. [Future REST API](#future-rest-api)

## URL Structure

### Root URL Configuration

**File**: `phonix/urls.py`

```python
urlpatterns = [
    path('admin/', admin.site.urls),                    # Django Admin
    path('dashboard/', include('dashboard.urls')),      # Dashboard app
    path('investment/', include('investment.urls')),    # Investment app
    path('wallet/', include('wallet.urls')),            # Wallet app
    path('', redirect to dashboard:index),              # Root → Dashboard
]
```

### Base URLs

- **Dashboard**: `/dashboard/`
- **Investment**: `/investment/`
- **Wallet**: `/wallet/`
- **Admin**: `/admin/`

All URLs require authentication except login and registration.

## Dashboard Views

### Dashboard App URLs

**File**: `dashboard/urls.py`

| URL Pattern | View | Name | Method | Auth Required |
|-------------|------|------|--------|---------------|
| `/dashboard/` | `index` | dashboard:index | GET | Yes |
| `/dashboard/login/` | `login_view` | dashboard:login | GET, POST | No |
| `/dashboard/register/` | `register_view` | dashboard:register | GET, POST | No |
| `/dashboard/logout/` | `logout_view` | dashboard:logout | POST | Yes |
| `/dashboard/profile/` | `profile_view` | dashboard:profile | GET, POST | Yes |
| `/dashboard/genealogy/` | `genealogy_view` | dashboard:genealogy | GET | Yes |

### 1. Dashboard Index

**Endpoint**: `GET /dashboard/`  
**View**: `dashboard.views.index`  
**Authentication**: Required

**Description**: Main dashboard showing user statistics and overview.

**Context Data**:
```python
{
    'user': User object,
    'wallet_balance': Decimal,
    'total_earnings': Decimal,
    'total_invested': Decimal,
    'active_subscriptions': QuerySet[Subscription],
    'recent_transactions': QuerySet[Transaction][:10],
    'direct_referrals': int,
    'total_referrals': int,  # All levels
    'current_rank': Rank object or None,
    'earnings_cap_percentage': float,
}
```

**Template**: `dashboard/index.html`

### 2. Login View

**Endpoint**: `GET/POST /dashboard/login/`  
**View**: `dashboard.views.login_view`  
**Authentication**: Not required

**POST Parameters**:
```python
{
    'username': str,  # or email
    'password': str,
}
```

**Response**:
- Success: Redirect to `/dashboard/`
- Failure: Re-render form with errors

### 3. Register View

**Endpoint**: `GET/POST /dashboard/register/`  
**View**: `dashboard.views.register_view`  
**Authentication**: Not required

**GET Parameters**:
```python
{
    'ref': str,  # Optional referral code
}
```

**POST Parameters**:
```python
{
    'username': str,
    'email': str,
    'password1': str,
    'password2': str,  # Confirmation
    'referral_code': str,  # Optional
}
```

**Process**:
1. Validate form data
2. Check if referral code exists (if provided)
3. Create user with `referred_by` set
4. Credit $10 registration bonus
5. Generate unique referral code
6. Update upline's direct_referrals_count
7. Log user in
8. Redirect to dashboard

**Response**:
- Success: Redirect to `/dashboard/`
- Failure: Re-render form with errors

### 4. Profile View

**Endpoint**: `GET/POST /dashboard/profile/`  
**View**: `dashboard.views.profile_view`  
**Authentication**: Required

**POST Parameters**:
```python
{
    'first_name': str,
    'last_name': str,
    'email': str,
    'trc20_wallet_address': str,  # For withdrawals
}
```

**Context Data**:
```python
{
    'user': User object,
    'deposit_address': DepositAddress object,
    'referral_link': str,
}
```

### 5. Genealogy View

**Endpoint**: `GET /dashboard/genealogy/`  
**View**: `dashboard.views.genealogy_view`  
**Authentication**: Required

**Description**: Displays user's downline structure.

**Context Data**:
```python
{
    'user': User object,
    'direct_referrals': QuerySet[User],
    'total_team_size': int,
    'team_volume': Decimal,  # Total investments
}
```

## Investment Views

### Investment App URLs

**File**: `investment/urls.py`

| URL Pattern | View | Name | Method | Auth Required |
|-------------|------|------|--------|---------------|
| `/investment/` | `subscription_list` | investment:list | GET | Yes |
| `/investment/purchase/` | `purchase_subscription` | investment:purchase | GET, POST | Yes |
| `/investment/<int:pk>/` | `subscription_detail` | investment:detail | GET | Yes |

### 1. Subscription List

**Endpoint**: `GET /investment/`  
**View**: `investment.views.subscription_list`  
**Authentication**: Required

**Description**: List all user's subscriptions.

**Query Parameters**:
```python
{
    'status': str,  # 'active' or 'completed'
}
```

**Context Data**:
```python
{
    'subscriptions': QuerySet[Subscription],
    'total_active': int,
    'total_invested': Decimal,
    'total_earned': Decimal,
}
```

### 2. Purchase Subscription

**Endpoint**: `GET/POST /investment/purchase/`  
**View**: `investment.views.purchase_subscription`  
**Authentication**: Required

**GET Context**:
```python
{
    'available_balance': Decimal,  # wallet + bonus
    'tier_info': {
        'tier_1': {'min': 50, 'max': 3000, 'rate': 6},
        'tier_2': {'min': 3001, 'max': 5000, 'rate': 8},
        'tier_3': {'min': 5001, 'max': None, 'rate': 10},
    }
}
```

**POST Parameters**:
```python
{
    'amount': Decimal,
    'use_bonus': bool,  # Use registration bonus
}
```

**Validation**:
- Amount >= $50
- User has sufficient balance
- Bonus usage <= 10% of amount (max $1)

**Process**:
1. Validate amount and balance
2. Calculate how much bonus can be used (10% max, $1 cap)
3. Deduct from wallet and/or bonus
4. Create Subscription record
5. Update user.total_invested
6. Create PURCHASE transaction
7. Trigger `distribute_generation_income` Celery task
8. Redirect to subscription detail

**Response**:
- Success: Redirect to `/investment/<subscription_id>/`
- Failure: Re-render form with errors

### 3. Subscription Detail

**Endpoint**: `GET /investment/<int:pk>/`  
**View**: `investment.views.subscription_detail`  
**Authentication**: Required

**Context Data**:
```python
{
    'subscription': Subscription object,
    'daily_income': Decimal,
    'earnings_progress': float,  # Percentage of 3x cap
    'days_active': int,
    'estimated_daily_income': Decimal,
    'remaining_capacity': Decimal,
}
```

## Wallet Views

### Wallet App URLs

**File**: `wallet/urls.py`

| URL Pattern | View | Name | Method | Auth Required |
|-------------|------|------|--------|---------------|
| `/wallet/` | `wallet_overview` | wallet:overview | GET | Yes |
| `/wallet/deposit/` | `deposit` | wallet:deposit | GET | Yes |
| `/wallet/withdraw/` | `withdraw` | wallet:withdraw | GET, POST | Yes |
| `/wallet/transactions/` | `transaction_history` | wallet:transactions | GET | Yes |
| `/wallet/transaction/<int:pk>/` | `transaction_detail` | wallet:detail | GET | Yes |

### 1. Wallet Overview

**Endpoint**: `GET /wallet/`  
**View**: `wallet.views.wallet_overview`  
**Authentication**: Required

**Context Data**:
```python
{
    'wallet_balance': Decimal,
    'registration_bonus': Decimal,
    'total_balance': Decimal,
    'deposit_address': DepositAddress object,
    'recent_transactions': QuerySet[Transaction][:20],
    'pending_withdrawals': QuerySet[Transaction],
}
```

### 2. Deposit View

**Endpoint**: `GET /wallet/deposit/`  
**View**: `wallet.views.deposit`  
**Authentication**: Required

**Description**: Display unique TRC20 deposit address with QR code.

**Context Data**:
```python
{
    'deposit_address': str,  # TRC20 address
    'deposit_address_obj': DepositAddress object,
    'qr_code_url': str,  # QR code image URL
    'network': str,  # 'TRON (TRC20)'
    'token': str,  # 'USDT'
    'min_deposit': Decimal,  # Minimum deposit amount
}
```

**Process**:
1. Get or create DepositAddress for user
2. Generate QR code for address
3. Display address and instructions
4. Deposits are automatically detected by `monitor_deposits` Celery task

### 3. Withdraw View

**Endpoint**: `GET/POST /wallet/withdraw/`  
**View**: `wallet.views.withdraw`  
**Authentication**: Required

**POST Parameters**:
```python
{
    'amount': Decimal,
    'wallet_address': str,  # TRC20 address
}
```

**Validation**:
- Amount <= wallet_balance
- Amount >= minimum withdrawal ($10)
- Valid TRC20 address format
- User has set withdrawal address in profile

**Process**:
1. Validate amount and address
2. Calculate 5% fee
3. Deduct from wallet_balance
4. Create WITHDRAWAL transaction (status: PENDING)
5. Admin approval required
6. After approval, `process_withdrawal_crypto` task sends funds
7. Update transaction status

**Response**:
- Success: Redirect to transaction detail
- Failure: Re-render form with errors

**Fee Structure**:
- Withdrawal fee: 5% of amount
- Example: Withdraw $100 → Pay $5 fee → Receive $95

### 4. Transaction History

**Endpoint**: `GET /wallet/transactions/`  
**View**: `wallet.views.transaction_history`  
**Authentication**: Required

**Query Parameters**:
```python
{
    'type': str,  # Filter by type
    'status': str,  # Filter by status
    'page': int,  # Pagination
}
```

**Context Data**:
```python
{
    'transactions': Paginated QuerySet[Transaction],
    'total_deposits': Decimal,
    'total_withdrawals': Decimal,
    'total_earnings': Decimal,
}
```

### 5. Transaction Detail

**Endpoint**: `GET /wallet/transaction/<int:pk>/`  
**View**: `wallet.views.transaction_detail`  
**Authentication**: Required

**Context Data**:
```python
{
    'transaction': Transaction object,
    'blockchain_url': str,  # TronScan link if txn_hash exists
}
```

## Authentication Views

Using Django's built-in authentication with custom templates.

### Login

**Endpoint**: `POST /dashboard/login/`  
**View**: `django.contrib.auth.views.LoginView` (customized)

### Logout

**Endpoint**: `POST /dashboard/logout/`  
**View**: `django.contrib.auth.views.LogoutView` (customized)

### Password Reset

Can be added using Django's built-in views:
- `/password-reset/`
- `/password-reset/done/`
- `/reset/<uidb64>/<token>/`
- `/reset/done/`

## Admin Panel

### Django Admin

**Endpoint**: `/admin/`  
**Authentication**: Superuser required

**Registered Models**:
- User (with custom admin)
- Subscription
- Transaction
- Commission
- DepositAddress
- Rank

**Capabilities**:
- View all users and their MLM structure
- Approve/reject withdrawal requests
- View all transactions
- Manually adjust balances (emergency use)
- View commission distribution
- Check rank calculations

## Future REST API

### Planned REST API Endpoints

Using Django REST Framework:

#### Authentication
- `POST /api/v1/auth/register/`
- `POST /api/v1/auth/login/`
- `POST /api/v1/auth/logout/`
- `POST /api/v1/auth/refresh/` (JWT refresh)

#### User
- `GET /api/v1/user/profile/`
- `PUT /api/v1/user/profile/`
- `GET /api/v1/user/stats/`
- `GET /api/v1/user/genealogy/`

#### Investment
- `GET /api/v1/subscriptions/`
- `POST /api/v1/subscriptions/`
- `GET /api/v1/subscriptions/{id}/`
- `GET /api/v1/subscriptions/{id}/earnings/`

#### Wallet
- `GET /api/v1/wallet/balance/`
- `GET /api/v1/wallet/deposit-address/`
- `POST /api/v1/wallet/withdraw/`
- `GET /api/v1/wallet/transactions/`
- `GET /api/v1/wallet/transactions/{id}/`

#### Earnings
- `GET /api/v1/earnings/commissions/`
- `GET /api/v1/earnings/summary/`

#### Rank
- `GET /api/v1/rank/current/`
- `GET /api/v1/rank/requirements/`
- `GET /api/v1/rank/leg-volumes/`

### API Authentication

#### JWT Token-Based

```python
# Login
POST /api/v1/auth/login/
{
    "username": "user123",
    "password": "SecurePass123"
}

# Response
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
        "id": 1,
        "username": "user123",
        "email": "user@example.com"
    }
}

# Use token in subsequent requests
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### API Response Format

#### Success Response
```json
{
    "success": true,
    "data": {
        "id": 1,
        "amount": "1000.00",
        "tier": "tier_1"
    },
    "message": "Subscription created successfully"
}
```

#### Error Response
```json
{
    "success": false,
    "error": {
        "code": "INSUFFICIENT_BALANCE",
        "message": "Insufficient wallet balance",
        "details": {
            "required": "1000.00",
            "available": "500.00"
        }
    }
}
```

### Rate Limiting

Recommended limits for API:
- Anonymous: 10 requests/minute
- Authenticated: 100 requests/minute
- Admin: 1000 requests/minute

Implementation using Django REST Framework throttling:
```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/minute',
        'user': '100/minute'
    }
}
```

## Webhooks (Future)

### Planned Webhook Events

For external integrations:

#### Events
- `user.registered` - New user registered
- `subscription.created` - New subscription purchased
- `subscription.completed` - Subscription reached 3x cap
- `transaction.completed` - Transaction completed
- `withdrawal.pending` - Withdrawal request created
- `rank.advanced` - User achieved new rank

#### Webhook Payload Example
```json
{
    "event": "subscription.created",
    "timestamp": "2024-01-01T12:00:00Z",
    "data": {
        "subscription_id": 123,
        "user_id": 456,
        "amount": "1000.00",
        "tier": "tier_1",
        "monthly_rate": "6.00"
    }
}
```

## Error Codes

### Standard HTTP Status Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Permission denied
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation failed
- `500 Internal Server Error` - Server error

### Custom Error Codes

```python
{
    'INSUFFICIENT_BALANCE': 'Insufficient wallet balance',
    'INVALID_AMOUNT': 'Invalid investment amount',
    'EARNINGS_CAP_REACHED': 'User has reached 3x earnings cap',
    'INVALID_REFERRAL_CODE': 'Invalid referral code',
    'DUPLICATE_EMAIL': 'Email already registered',
    'INVALID_TRC20_ADDRESS': 'Invalid TRC20 wallet address',
    'WITHDRAWAL_MINIMUM': 'Withdrawal amount below minimum',
}
```

---

This API documentation provides a complete reference for all current views and planned REST API endpoints. The platform is designed to be extended with a full REST API for mobile apps and third-party integrations.
