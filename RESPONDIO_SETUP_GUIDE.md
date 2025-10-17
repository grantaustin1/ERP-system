# Respond.io WhatsApp Integration - Setup Guide

## Overview
Your ERP360 gym management system now has respond.io WhatsApp integration implemented! The system is currently running in **MOCK mode** for testing. Follow this guide to activate real WhatsApp messaging.

---

## Current Status: ✅ Initial Implementation Complete

### What's Been Implemented:

1. **RespondIO Service** (`/app/backend/services/respondio_service.py`)
   - Full API wrapper for respond.io
   - Phone number formatting for South African numbers (+27)
   - Contact management (create/update)
   - Message sending with templates
   - Error handling with retry logic
   - Automatic fallback to mock mode without API key

2. **Automation Engine Integration**
   - Updated `execute_action()` to use real WhatsApp
   - Automatic template selection based on trigger type
   - Parameter extraction from trigger data
   - Error handling and logging

3. **API Endpoints** (all require authentication)
   - `GET /api/whatsapp/status` - Check integration status
   - `GET /api/whatsapp/templates` - List available templates
   - `POST /api/whatsapp/test-message` - Send test message
   - `POST /api/whatsapp/format-phone` - Test phone formatting (no auth)

4. **Environment Configuration**
   - `.env` file updated with respond.io variables
   - Mock mode active (RESPOND_IO_API_KEY not set)
   - Ready for production credentials

---

## How to Activate Real WhatsApp Messaging

### Prerequisites

**1. Respond.io Account Requirements:**
- ✅ Respond.io account with **Growth Plan or above** (API access)
- ✅ WhatsApp Business API channel configured
- ✅ Message templates created and approved by WhatsApp

**2. Get Your API Credentials:**

Go to: https://app.respond.io

1. Click **Settings** (gear icon)
2. Click **Integrations** → **Developer API**
3. Click **"Generate API Key"**
4. Copy the API key (starts with `eyJ...`)
5. Copy your **Channel ID** (for WhatsApp channel)

### Step-by-Step Activation

#### Step 1: Update Environment Variables

Edit `/app/backend/.env` file:

```bash
# Replace empty values with your actual credentials
RESPOND_IO_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # Your actual API key
WHATSAPP_CHANNEL_ID="123456"  # Your WhatsApp channel ID
```

#### Step 2: Restart Backend

```bash
sudo supervisorctl restart backend
```

Check logs to verify:
```bash
tail -f /var/log/supervisor/backend.err.log
```

✅ You should NOT see "WhatsApp integration will be mocked" anymore

#### Step 3: Test Integration

**Test 1 - Check Status:**
```bash
curl -X GET "http://localhost:8001/api/whatsapp/status" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Expected response:
```json
{
  "integrated": true,
  "is_mocked": false,
  "api_key_configured": true,
  "channel_id_configured": true,
  "message": "WhatsApp integration is active via respond.io"
}
```

**Test 2 - List Templates:**
```bash
curl -X GET "http://localhost:8001/api/whatsapp/templates" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Test 3 - Send Test Message:**
```bash
curl -X POST "http://localhost:8001/api/whatsapp/test-message" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "0821234567",
    "template_name": "payment_failed_alert",
    "member_name": "John Smith"
  }'
```

---

## Creating WhatsApp Message Templates

### Required Templates for Gym System

You need to create these templates in respond.io:

#### 1. Payment Failed Alert
**Template Name:** `payment_failed_alert`
**Category:** TRANSACTIONAL
**Language:** English

**Template Content:**
```
Hi {{1}}, your payment of R{{2}} (Invoice: {{3}}) has failed. Please update your payment method to avoid service interruption.
```

**Parameters:**
1. Member name
2. Amount
3. Invoice number

#### 2. Member Welcome
**Template Name:** `member_welcome`
**Category:** TRANSACTIONAL
**Language:** English

**Template Content:**
```
Welcome {{1}}! Thank you for joining our gym. Your membership is now active. Show your QR code at reception for access.
```

**Parameters:**
1. Member name

#### 3. Membership Renewal Reminder
**Template Name:** `membership_renewal_reminder`
**Category:** MARKETING
**Language:** English

**Template Content:**
```
Hi {{1}}, your membership expires on {{2}}. Renew now to continue enjoying our facilities. Contact us for assistance.
```

**Parameters:**
1. Member name
2. Expiry date

#### 4. Invoice Overdue Reminder
**Template Name:** `invoice_overdue_reminder`
**Category:** TRANSACTIONAL
**Language:** English

**Template Content:**
```
Hi {{1}}, invoice {{2}} for R{{3}} is overdue. Please settle your account to avoid suspension.
```

**Parameters:**
1. Member name
2. Invoice number
3. Amount

### How to Create Templates

1. Go to: https://app.respond.io → **Settings** → **Message Templates**
2. Click **"New Template"**
3. Select **WhatsApp** channel
4. Fill in:
   - Template Name (use exact names above)
   - Category (TRANSACTIONAL or MARKETING)
   - Language (English)
   - Template content with {{1}}, {{2}} placeholders
5. Click **"Submit for Approval"**
6. Wait for WhatsApp approval (usually 1-24 hours)

**⚠️ Important:**
- Template names in code must match exactly
- Parameters use {{1}}, {{2}}, {{3}} format
- Cannot edit templates after approval (must create new version)

---

## Phone Number Formatting

The system automatically formats South African phone numbers:

**Examples:**
- Input: `0821234567` → Output: `+27821234567` ✅
- Input: `27821234567` → Output: `+27821234567` ✅
- Input: `082 123 4567` → Output: `+27821234567` ✅
- Input: `+27821234567` → Output: `+27821234567` ✅

**Test Formatting:**
```bash
curl -X POST "http://localhost:8001/api/whatsapp/format-phone?phone=0821234567"
```

---

## How Automation Triggers WhatsApp

### Example: Payment Failed Automation

**When:** Invoice payment fails
**What Happens:**

1. System calls `trigger_automation("payment_failed", trigger_data)`
2. Finds active automations with "payment_failed" trigger
3. Checks conditions (e.g., amount >= 500)
4. Executes actions including "send_whatsapp"
5. `execute_action()` is called with:
   ```python
   {
     "type": "send_whatsapp",
     "message": "Hi {member_name}, payment of R{amount} failed..."
   }
   ```
6. System:
   - Extracts member details from trigger_data
   - Selects appropriate template
   - Formats phone number
   - Sends via respond.io API
   - Logs message ID and status

**Trigger Data Example:**
```python
{
  "member_id": "uuid-123",
  "member_name": "John Smith",
  "email": "john@example.com",
  "phone": "+27821234567",
  "invoice_id": "uuid-inv-456",
  "invoice_number": "INV-001",
  "amount": 500.00,
  "failure_reason": "Insufficient funds"
}
```

---

## Template Auto-Selection

The system automatically selects templates based on trigger type:

| Trigger Type | Template Name |
|--------------|---------------|
| `payment_failed` | `payment_failed_alert` |
| `member_joined` | `member_welcome` |
| `invoice_overdue` | `invoice_overdue_reminder` |
| `membership_expiring` | `membership_renewal_reminder` |
| (other) | `general_notification` |

You can override by setting `template_name` in the action configuration.

---

## Mock Mode vs Production Mode

### Mock Mode (Current)
- ✅ No API key required
- ✅ No respond.io account needed
- ✅ Perfect for testing automation logic
- ✅ Logs messages to console
- ⚠️ No actual WhatsApp messages sent

**Log Example:**
```
[MOCK] Would send POST to message/send with data: {...}
INFO: WhatsApp Action (Mock): Sending to +27821234567: Hi John, payment failed...
```

### Production Mode (After Setup)
- ✅ Real WhatsApp messages sent
- ✅ Message delivery confirmation
- ✅ Message ID tracking
- ✅ Status updates via webhooks
- ✅ Professional business messaging

**Log Example:**
```
INFO: WhatsApp message sent to +27821234567 using template payment_failed_alert, message ID: msg_abc123
```

---

## Testing Checklist

Before going live, test these scenarios:

### Backend Tests
- [ ] Check integration status (should show `integrated: true`)
- [ ] List templates (should return your approved templates)
- [ ] Format various phone numbers (test edge cases)
- [ ] Send test message to your own number
- [ ] Verify message appears in WhatsApp

### Automation Tests
- [ ] Create test automation with WhatsApp action
- [ ] Trigger the automation manually
- [ ] Check execution history shows "sent" status
- [ ] Verify WhatsApp message received
- [ ] Test with different member phone formats

### Error Handling Tests
- [ ] Test with invalid phone number
- [ ] Test with missing template
- [ ] Test with API key removed (should fallback to mock)
- [ ] Test with invalid channel ID
- [ ] Verify error logs are clear

---

## Troubleshooting

### "WhatsApp integration will be mocked" in logs
**Solution:** RESPOND_IO_API_KEY not set in .env file
- Check `/app/backend/.env`
- Ensure API key is not empty
- Restart backend: `sudo supervisorctl restart backend`

### "Template not found" error
**Solution:** Template not created or not approved
- Go to respond.io → Message Templates
- Check template status (must be APPROVED)
- Verify template name matches exactly
- Wait for approval (up to 24 hours)

### "Phone number invalid" warning
**Solution:** Phone number format issue
- Test with `/api/whatsapp/format-phone` endpoint
- Ensure number starts with 0 or 27
- SA mobile numbers are 10 digits (after removing 0)
- Check for typos or extra characters

### Messages not sending (production mode)
**Checklist:**
- [ ] API key is correct (test with curl)
- [ ] Channel ID is correct
- [ ] Templates are APPROVED status
- [ ] Phone number is valid E.164 format
- [ ] WhatsApp Business API has credit
- [ ] No rate limiting (check respond.io dashboard)

### "API request failed" errors
**Common causes:**
- Invalid API key → Check respond.io settings
- Channel ID wrong → Verify in respond.io channels
- Rate limit exceeded → Check your plan limits
- Network issues → Check connectivity

---

## Cost Considerations

### Respond.io Pricing
- **Growth Plan:** $79/month (includes API access)
- **Advanced Plan:** $179/month (more features)
- WhatsApp messages: ~$0.005 - $0.05 per message (varies by country)

### Message Volume Estimates
**Example Gym (500 active members):**
- Payment failures: ~20/month × $0.01 = $0.20
- Renewals: ~50/month × $0.01 = $0.50
- Welcomes: ~30/month × $0.01 = $0.30
- **Total:** ~$1.00/month in WhatsApp costs

**Large Gym (2000 active members):**
- Estimate: ~$4-5/month in WhatsApp costs

---

## Security Best Practices

✅ **Do:**
- Keep API key in .env file only
- Never commit .env to git
- Use environment variables
- Rotate API keys periodically
- Monitor API usage in respond.io dashboard

❌ **Don't:**
- Hardcode API keys in code
- Share API keys in Slack/email
- Commit .env file to repository
- Use same API key across environments
- Ignore rate limit warnings

---

## Next Steps

### Immediate (Development)
1. [ ] Keep running in mock mode
2. [ ] Test all automation workflows
3. [ ] Verify message formatting
4. [ ] Check phone number handling

### Before Production
1. [ ] Sign up for respond.io Growth plan
2. [ ] Set up WhatsApp Business API
3. [ ] Create all required templates
4. [ ] Wait for template approvals
5. [ ] Add API key to .env
6. [ ] Test with real phone numbers
7. [ ] Monitor first 24 hours closely

### Production Launch
1. [ ] Verify all templates approved
2. [ ] Test end-to-end with real scenarios
3. [ ] Set up monitoring/alerts
4. [ ] Document for your team
5. [ ] Train staff on WhatsApp features

---

## Support & Resources

**Respond.io Documentation:**
- API Docs: https://developers.respond.io
- Help Center: https://respond.io/help
- Template Guidelines: https://respond.io/help/whatsapp/whatsapp-message-templates

**Your Implementation:**
- Service Class: `/app/backend/services/respondio_service.py`
- Integration Code: `/app/backend/server.py` (search for "send_whatsapp")
- Environment Config: `/app/backend/.env`

**Testing Endpoints:**
- Status: `GET /api/whatsapp/status`
- Templates: `GET /api/whatsapp/templates`
- Test Message: `POST /api/whatsapp/test-message`
- Format Phone: `POST /api/whatsapp/format-phone`

---

## Summary

✅ **Completed:**
- Respond.io service integration
- Phone number formatting (SA numbers)
- Template-based messaging
- Automation engine integration
- Error handling & retry logic
- API endpoints for testing
- Mock mode for development

🔄 **Next Actions:**
1. Get respond.io account (Growth plan)
2. Create WhatsApp templates
3. Add API credentials to .env
4. Test with real phone numbers
5. Go live!

**Current Status:** Ready for activation - just add API credentials!

---

**Document Version:** 1.0
**Last Updated:** October 2025
**Status:** Initial Implementation Complete
