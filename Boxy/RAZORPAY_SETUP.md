# Razorpay Integration Setup

This guide will help you integrate your Razorpay test API keys into the Boxy application.

## Step 1: Get Your Razorpay Test Keys

1. Go to [Razorpay Dashboard](https://dashboard.razorpay.com/)
2. Log in to your account
3. Navigate to **Settings** → **API Keys**
4. Generate or copy your **Test Key ID** and **Test Key Secret**
   - Test Key ID starts with `rzp_test_`
   - Test Key Secret is a long string

## Step 2: Configure Your Keys

1. Open `Boxy/config.py` file
2. Replace the placeholder values with your actual keys:

```python
RAZORPAY_KEY_ID = 'rzp_test_YOUR_ACTUAL_KEY_ID'
RAZORPAY_KEY_SECRET = 'YOUR_ACTUAL_KEY_SECRET'
```

**Example:**
```python
RAZORPAY_KEY_ID = 'rzp_test_1DP5mmOlF5F5Fa'
RAZORPAY_KEY_SECRET = 'L2g7mMCRKxWj3K7kP5nH8vQ9'
```

## Step 3: Install Required Package

Make sure you have the `requests` library installed:

```bash
pip install requests
```

## Step 4: Test the Integration

1. Start your Flask application
2. Create a delivery and mark it as delivered
3. Go to the payment page
4. Click "Pay Online" button
5. You should see the Razorpay checkout popup
6. Use Razorpay test cards for testing:
   - **Card Number:** `4111 1111 1111 1111`
   - **CVV:** Any 3 digits (e.g., `123`)
   - **Expiry:** Any future date (e.g., `12/25`)
   - **Name:** Any name

## Features

✅ **Order Creation:** Creates Razorpay orders on the backend
✅ **Signature Verification:** Verifies payment signatures for security
✅ **Payment Verification:** Confirms payment with Razorpay API
✅ **Automatic Status Update:** Updates delivery status after successful payment

## Security Notes

- ⚠️ **Never commit your real keys to version control**
- ⚠️ The `config.py` file is in `.gitignore` to prevent accidental commits
- ⚠️ For production, use environment variables instead of hardcoding keys

## Production Setup

For production, use environment variables:

```python
import os

RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')
```

Then set them in your environment:
```bash
export RAZORPAY_KEY_ID='rzp_live_YOUR_KEY'
export RAZORPAY_KEY_SECRET='YOUR_SECRET'
```

## Troubleshooting

**Error: "Failed to create order"**
- Check if your keys are correct
- Verify you're using Test keys (not Live keys) for testing
- Check your internet connection

**Error: "Payment signature verification failed"**
- This usually means the payment was tampered with
- Check that your Key Secret is correct

**Payment not updating in database**
- Check Flask server logs for errors
- Verify the payment was actually successful in Razorpay dashboard
- Check database connection

## Support

For Razorpay API documentation, visit: https://razorpay.com/docs/

