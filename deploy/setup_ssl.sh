#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
# Phonix — SSL Setup with Let's Encrypt (Certbot)
# Usage: sudo bash deploy/setup_ssl.sh YOUR_DOMAIN
# ─────────────────────────────────────────────────────────────────
set -euo pipefail

DOMAIN="${1:?Usage: $0 <domain>}"

echo "=== Installing Certbot ==="
apt-get update -qq
apt-get install -y -qq certbot python3-certbot-nginx

echo "=== Obtaining SSL certificate for ${DOMAIN} ==="
certbot --nginx \
    -d "${DOMAIN}" \
    -d "www.${DOMAIN}" \
    --non-interactive \
    --agree-tos \
    --email "admin@${DOMAIN}" \
    --redirect

echo "=== Setting up auto-renewal ==="
systemctl enable certbot.timer
systemctl start certbot.timer

echo "=== Testing renewal ==="
certbot renew --dry-run

echo "=== SSL setup complete for ${DOMAIN} ==="
echo "Certificate will auto-renew via systemd timer."
