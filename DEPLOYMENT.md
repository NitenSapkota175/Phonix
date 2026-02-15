# Phonix MLM Platform - Production Deployment Guide

This guide will help you deploy Phonix to production.

## Prerequisites

- Ubuntu 20.04+ or similar Linux server
- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- Nginx
- Domain name with DNS configured
- SSL certificate (Let's Encrypt recommended)

## 1. Server Setup

### Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### Install Dependencies
```bash
sudo apt install python3-pip python3-venv postgresql postgresql-contrib redis-server nginx git -y
```

### Install Certbot for SSL
```bash
sudo apt install certbot python3-certbot-nginx -y
```

## 2. Database Setup

### Create PostgreSQL Database
```bash
sudo -u postgres psql

CREATE DATABASE phonix_db;
CREATE USER phonix_user WITH PASSWORD 'your_secure_password';
ALTER ROLE phonix_user SET client_encoding TO 'utf8';
ALTER ROLE phonix_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE phonix_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE phonix_db TO phonix_user;
\q
```

## 3. Application Deployment

### Clone or Upload Project
```bash
cd /var/www/
sudo git clone <your-repo-url> phonix
# OR upload via SFTP
sudo chown -R $USER:$USER /var/www/phonix
cd phonix
```

### Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Requirements
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn  # WSGI server
```

### Configure Environment Variables
```bash
cp .env.example .env
nano .env
```

Update the `.env` file with production values:
```env
SECRET_KEY=your-very-long-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DB_ENGINE=django.db.backends.postgresql
DB_NAME=phonix_db
DB_USER=phonix_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://localhost:6379/0

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

SITE_URL=https://yourdomain.com
ADMIN_EMAIL=admin@yourdomain.com

TRON_API_KEY=your-trongrid-api-key
TRON_NETWORK=mainnet

SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### Run Migrations
```bash
python manage.py migrate
```

### Create Superuser
```bash
python manage.py createsuperuser
```

### Collect Static Files
```bash
python manage.py collectstatic --noinput
```

## 4. Gunicorn Setup

### Create Gunicorn Socket
```bash
sudo nano /etc/systemd/system/gunicorn.socket
```

Add:
```ini
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
```

### Create Gunicorn Service
```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Add:
```ini
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/phonix
Environment="PATH=/var/www/phonix/venv/bin"
ExecStart=/var/www/phonix/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          phonix.wsgi:application

[Install]
WantedBy=multi-user.target
```

### Start Gunicorn
```bash
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
sudo systemctl status gunicorn.socket
```

## 5. Nginx Configuration

### Create Nginx Config
```bash
sudo nano /etc/nginx/sites-available/phonix
```

Add:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /var/www/phonix/staticfiles/;
    }
    
    location /media/ {
        alias /var/www/phonix/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```

### Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/phonix /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Get SSL Certificate
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## 6. Celery Setup

### Create Celery Worker Service
```bash
sudo nano /etc/systemd/system/celery.service
```

Add:
```ini
[Unit]
Description=Celery Worker
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/var/www/phonix
Environment="PATH=/var/www/phonix/venv/bin"
ExecStart=/var/www/phonix/venv/bin/celery -A phonix worker --loglevel=info --detach

[Install]
WantedBy=multi-user.target
```

### Create Celery Beat Service
```bash
sudo nano /etc/systemd/system/celerybeat.service
```

Add:
```ini
[Unit]
Description=Celery Beat
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/phonix
Environment="PATH=/var/www/phonix/venv/bin"
ExecStart=/var/www/phonix/venv/bin/celery -A phonix beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler

[Install]
WantedBy=multi-user.target
```

### Start Celery Services
```bash
sudo systemctl daemon-reload
sudo systemctl start celery celerybeat
sudo systemctl enable celery celerybeat
sudo systemctl status celery celerybeat
```

## 7. Security & Permissions

### Set Correct Permissions
```bash
sudo chown -R www-data:www-data /var/www/phonix
sudo chmod -R 755 /var/www/phonix
```

### Configure Firewall
```bash
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

## 8. Verification & Testing

### Test Gunicorn
```bash
curl --unix-socket /run/gunicorn.sock localhost
```

### Check Logs
```bash
# Nginx logs
sudo tail -f /var/log/nginx/error.log

# Gunicorn logs
sudo journalctl -u gunicorn

# Celery logs
sudo journalctl -u celery
sudo journalctl -u celerybeat
```

### Access Admin Panel
Visit: `https://yourdomain.com/admin/`

## 9. Post-Deployment Tasks

1. **Test all functionality**:
   - User registration
   - Login/Logout
   - Deposit/Withdrawal workflow
   - Investment purchases
   - Admin approvals

2. **Set up monitoring**:
   - Install monitoring tools (optional: Sentry, New Relic)
   - Set up log rotation
   - Configure backups

3. **Database Backups**:
```bash
# Create backup script
sudo nano /usr/local/bin/backup-phonix.sh
```

Add:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump phonix_db > /backups/phonix_backup_$DATE.sql
```

Make executable and add to cron:
```bash
sudo chmod +x /usr/local/bin/backup-phonix.sh
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/backup-phonix.sh
```

## 10. Maintenance Commands

### Restart Services
```bash
sudo systemctl restart gunicorn
sudo systemctl restart celery celerybeat
sudo systemctl restart nginx
```

### Update Application
```bash
cd /var/www/phonix
source venv/bin/activate
git pull  # or upload new files
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn celery celerybeat
```

## Troubleshooting

### Check Service Status
```bash
sudo systemctl status gunicorn
sudo systemctl status celery
sudo systemctl status celerybeat
sudo systemctl status nginx
```

### Common Issues

1. **Static files not loading**: Run `collectstatic` and check Nginx config
2. **502 Bad Gateway**: Check Gunicorn socket and service status
3. **Database connection errors**: Verify PostgreSQL is running and credentials are correct
4. **Celery tasks not running**: Check Redis connection and Celery worker status

## Support

For issues, check the logs first:
- Application: `/var/log/gunicorn/`
- Nginx: `/var/log/nginx/`
- System services: `journalctl -u <service-name>`
