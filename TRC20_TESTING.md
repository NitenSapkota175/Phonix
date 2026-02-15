# TRC20 Integration Testing Guide

This guide will help you test the TRC20 integration on Shasta testnet before going to mainnet.

## Prerequisites

1. **Install cryptography library**:
```bash
pip install cryptography==41.0.7
```

2. **Configure for Shasta Testnet**:

Create `.env` file (copy from `.env.example`):
```env
TRON_NETWORK=shasta
TRON_API_KEY=  # Optional for testnet
```

## Step 1: Get Test TRX

1. Visit: https://www.trongrid.io/shasta/
2. Enter a TRC20 address and claim test TRX
3. You'll receive ~10,000 test TRX (fake, no value)

## Step 2: Create Master Wallet

Run this Python script to generate your master wallet:

```python
# In Django shell: python manage.py shell
from wallet.tron_utils import generate_wallet

master_wallet = generate_wallet()
print(f"Address: {master_wallet['address']}")
print(f"Private Key: {master_wallet['private_key']}")

# Save these to your .env file!
# MASTER_WALLET_ADDRESS=<address>
# MASTER_WALLET_KEY=<private_key>
```

## Step 3: Fund Master Wallet

1. Go to Shasta faucet: https://www.trongrid.io/shasta/
2. Enter your master wallet address
3. Claim test TRX (need for transaction fees)
4. Get test USDT:
   - Use Shasta USDT contract: `TG3XXyExBkPp9nzdajDZsozEu4BkaSJozs`
   - Or ask in TRON developer communities

## Step 4: Test Address Generation

```python
# In Django shell
from accounts.models import User
from wallet.models import DepositAddress

# Get a test user
user = User.objects.first()

# Create deposit address (will auto-generate)
deposit_addr = DepositAddress.objects.create(user=user)

print(f"Generated Address: {deposit_addr.address}")
print(f"Encrypted Key Length: {len(deposit_addr.private_key_encrypted)}")

# Test decryption
private_key = deposit_addr.get_private_key()
print(f"Decrypted successfully: {len(private_key) == 64}")
```

## Step 5: Test Deposit Detection

1. **Send test USDT to generated address**

2. **Run monitoring task manually**:
```python
# In Django shell
from wallet.tasks import monitor_deposits

result = monitor_deposits()
print(result)
```

3. **Check for created transaction**:
```python
from wallet.models import Transaction

deposits = Transaction.objects.filter(type='deposit')
for d in deposits:
    print(f"{d.user.username}: ${d.amount} - {d.status}")
```

## Step 6: Test Manual Deposit Approval

1. Go to admin panel: http://127.0.0.1:8000/admin/
2. Navigate to Transactions
3. Find pending deposit
4. Select it and choose "Approve selected deposits"
5. Check user's wallet balance increased

## Step 7: Test Withdrawal

1. **As test user, request withdrawal**:
   - Go to Wallet page
   - Click Withdraw
   - Enter amount and TRC20 address
   - Submit

2. **As admin, approve**:
   - Admin panel → Transactions
   - Find pending withdrawal
   - Select "Approve selected withdrawals"

3. **Process crypto sending** (automatic if configured):
```python
# Or manually in shell
from wallet.tasks import process_withdrawal_crypto

result = process_withdrawal_crypto(transaction_id=<ID>)
print(result)
```

4. **Verify on blockchain**:
   - Go to: https://shasta.tronscan.org/
   - Search for transaction hash
   - Confirm transaction succeeded

## Step 8: Test Utilities

```python
# Test balance checking
from wallet.tron_utils import get_account_balance

balance = get_account_balance('your-address-here')
print(f"TRX: {balance['trx_balance']}")
print(f"USDT: {balance['usdt_balance']}")

# Test address validation
from wallet.tron_utils import validate_address

print(validate_address('TYour...address'))  # Should be True
print(validate_address('invalid'))  # Should be False

# Test encryption
from wallet.encryption import test_encryption
test_encryption()  # Should print ✅
```

## Common Issues & Solutions

### Issue: "Private key encryption error"
**Solution:** Make sure `SECRET_KEY` is set in settings.py or .env

### Issue: "Transaction not found on blockchain"
**Solution:** Wait a few seconds and try again. Testnet can be slower.

### Issue: "Insufficient TRX for fees"
**Solution:** Get more test TRX from the faucet for your master wallet

### Issue: "USDT balance shows 0 but I sent"
**Solution:** 
- Check transaction on tronscan.org
- Verify you used correct USDT contract
- Wait for confirmations

## Switching to Mainnet

When ready for production:

1. **Update .env**:
```env
TRON_NETWORK=mainnet
TRON_API_KEY=your-real-api-key  # Get from trongrid.io
```

2. **Generate new master wallet** (SECURELY!)
   - Use hardware wallet if possible
   - Store private key in secure vault
   - Never commit to git
   - Use environment variables only

3. **Fund master wallet** with real TRX and USDT
   - Recommend 500-1000 TRX for fees
   - Start with small USDT amount

4. **Test with small amounts first**

5. **Set up monitoring**:
   - Log all transactions
   - Alert on failures
   - Monitor wallet balances

## Security Checklist

- [ ] Master wallet private key is in `.env`, not in code
- [ ] `.env` is in `.gitignore`
- [ ] User private keys are encrypted in database
- [ ] Withdrawal limits are configured
- [ ] Admin approval required for large amounts
- [ ] Monitoring/alerts set up
- [ ] Backup of master wallet exists (offline, secure)

## Monitoring Commands

```bash
# Check Celery is running
celery -A phonix inspect active

# Check scheduled tasks
celery -A phonix inspect scheduled

# Monitor deposit task
celery -A phonix inspect active | grep monitor_deposits

# View Celery logs
celery -A phonix events
```

## Next Steps

After successful testing:

1. Document any issues encountered
2. Adjust monitoring frequency if needed
3. Set up production monitoring
4. Create runbook for common operations
5. Train support team on crypto operations

## Support

For issues:
- Check Django logs: `python manage.py runserver` output
- Check Celery logs
- Use tronscan.org to debug transactions
- Review `wallet/tasks.py` for error messages
