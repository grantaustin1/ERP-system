# ERP360 Enhanced Package Setup - User Guide

## Table of Contents
1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Creating Base Memberships](#creating-base-memberships)
4. [Adding Membership Variations](#adding-membership-variations)
5. [Configuring Payment Options](#configuring-payment-options)
6. [Managing Family Memberships](#managing-family-memberships)
7. [Member Registration with Payment Plans](#member-registration-with-payment-plans)
8. [Member Portal Features](#member-portal-features)
9. [Best Practices](#best-practices)

---

## Overview

The Enhanced Package Setup system allows gym administrators to create flexible membership packages with:
- Multiple payment options per membership
- Auto-renewal configurations
- Family/group membership support
- Customizable payment schedules

### Key Benefits
- **Flexibility:** Offer members choice in how they pay
- **Automation:** Auto-renewal reduces manual renewals
- **Family Packages:** Support multiple members under one billing account
- **Better Cash Flow:** Mix of upfront and recurring payment options

---

## Getting Started

### Accessing Package Setup
1. Log in to the ERP360 admin dashboard
2. Click **"Package Setup"** in the left sidebar
3. You'll see two tabs:
   - **Membership Structure** - Create base memberships and variations
   - **Payment Options** - Configure payment plans

---

## Creating Base Memberships

### Step-by-Step Guide

1. **Navigate to Membership Structure Tab**
   - This tab shows all existing base memberships

2. **Click "Create Base Membership"**
   - A dialog will open

3. **Fill in Membership Details:**

   **Basic Information:**
   - **Membership Name:** e.g., "Premium Gym Access", "Family Package"
   - **Base Price:** R500.00 (this is the reference price)
   - **Description:** Brief description of what's included

   **Duration:**
   - **Duration (Months):** How long the membership lasts (e.g., 12 months)

   **Multi-Member Support:**
   - **Max Members per Membership:**
     - Set to `1` for individual memberships
     - Set to `2-6` for family/group packages
   - Example: Family Package with max 4 members

   **Access Settings:**
   - **Peak Hours Only:** Toggle ON if membership is restricted to peak times
   - **Multi-Site Access:** Toggle ON if member can access multiple gym locations

4. **Click "Create"**
   - Membership appears in the list
   - Badge shows member capacity (e.g., "Up to 4 members")

### Example Base Memberships

**Individual Membership:**
- Name: Premium Individual
- Price: R500
- Duration: 12 months
- Max Members: 1
- Multi-Site: OFF

**Family Package:**
- Name: Family Gym Package
- Price: R1200
- Duration: 12 months
- Max Members: 4
- Multi-Site: ON

---

## Adding Membership Variations

Variations allow you to offer discounts for specific groups (students, seniors, corporate, etc.)

### Creating a Variation

1. **Find the base membership** in the list
2. **Click "Add Variation"** button
3. **Fill in Variation Details:**

   - **Variation Type:** Select from dropdown
     - Student Discount
     - Corporate Discount
     - Senior Discount
     - Family Package
     - Promotional

   - **Discount Percentage:** Enter discount (e.g., 10 for 10% off)
   - **Description:** Optional description (e.g., "Valid student ID required")

4. **Click "Create Variation"**
   - Variation appears under the base membership
   - Price is automatically calculated
   - Example: R500 base - 10% = R450

### Naming Convention
Variations automatically follow this format:
```
{Base Name} - {Variation Type}
```
Example: "Premium Individual - Student Discount"

---

## Configuring Payment Options

Payment options give members flexibility in how they pay for memberships.

### Accessing Payment Options

1. Click the **"Payment Options"** tab
2. Select a membership (base or variation) from the list
3. Selected membership highlights in blue

### Creating Payment Options

1. **Click "Add Payment Option"**
2. **Fill in Payment Details:**

#### Basic Settings

**Payment Option Name:**
- Give it a friendly name members will see
- Examples:
  - "Annual Upfront Saver"
  - "Monthly Budget Plan"
  - "Quarterly Flex"

**Payment Type:**
- **Single Payment:** One-time payment
- **Recurring Payments:** Multiple installments

**Payment Frequency:** (if recurring)
- Monthly
- Quarterly (every 3 months)
- Bi-annual (every 6 months)
- Annual (once per year)

#### Amount Configuration

**Installment Amount:**
- Amount charged per installment
- Example: R500 per month

**Number of Installments:**
- Total number of payments
- Example: 12 installments for 12-month membership

**Total Amount:**
- Automatically calculated
- Formula: Installment Amount × Number of Installments
- Example: R500 × 12 = R6000

#### Auto-Renewal Settings

Toggle **"Enable Auto-Renewal"** to configure:

**Auto-Renewal Frequency:**
- **Month-to-Month:** After contract ends, continue on monthly basis
  - Example: After 12-month contract, continues at R500/month
- **Same Duration:** Restart contract for same duration
  - Example: After 12 months, starts another 12-month contract

**Auto-Renewal Price:** (Optional)
- Leave blank to use same price
- Enter amount to change price after renewal
- Example: R550/month after first year

**Description:** (Optional)
- Additional details shown to members
- Example: "Best value - save 10% with upfront payment"

**Default Option:**
- Toggle ON to mark as recommended option
- Shows "Recommended" badge to members

3. **Click "Create Payment Option"**
   - Option appears in the list
   - Shows payment structure clearly

### Payment Option Examples

#### Example 1: Upfront Discount
```
Payment Name: Annual Upfront Saver
Payment Type: Single Payment
Installment Amount: R5400
Number of Installments: 1
Total: R5400 (10% discount from R6000)
Auto-Renewal: OFF
Description: Pay upfront and save 10%
```

#### Example 2: Monthly with Auto-Renewal
```
Payment Name: Monthly Budget Plan
Payment Type: Recurring
Payment Frequency: Monthly
Installment Amount: R500
Number of Installments: 12
Total: R6000
Auto-Renewal: ON
Auto-Renewal Frequency: Month-to-Month
Auto-Renewal Price: R500
Default: YES
Description: Flexible monthly payments
```

#### Example 3: Quarterly Corporate
```
Payment Name: Quarterly Corporate
Payment Type: Recurring
Payment Frequency: Quarterly
Installment Amount: R1500
Number of Installments: 4
Total: R6000
Auto-Renewal: ON
Auto-Renewal Frequency: Same Duration
Description: Quarterly invoicing for company billing
```

---

## Managing Family Memberships

Family memberships allow multiple people to share one membership fee.

### Setting Up Family Packages

1. **Create Base Membership** with:
   - Appropriate name (e.g., "Family Package")
   - Higher price to account for multiple members
   - **Max Members:** Set to desired number (2-6)
   - Enable Multi-Site Access (recommended)

2. **Add Payment Options** for the family package
   - Consider higher installment amounts
   - Example: R1200/month for 4 family members

### How Family Memberships Work

**Primary Member:**
- The person who signs up first
- Responsible for all billing
- Can view all family members in portal
- Manages the family account

**Family Members:**
- Added to the primary member's account
- Each gets their own QR code for access
- Share the membership benefits
- Cannot modify billing or add/remove members

**Member Capacity:**
- System tracks current vs maximum members
- Cannot exceed max_members limit
- Example: 3 of 4 members used

### Adding Family Members

**For Staff:**
1. When registering a member, select the family membership type
2. If adding to existing family:
   - Use the membership group management features
   - Link new member to primary member's group
3. System automatically:
   - Generates QR code for new member
   - Updates member count
   - Maintains single billing to primary member

**For Members (via Portal):**
- Members can view family members
- Primary member sees "Add Member" button
- Contact gym staff to complete addition
- Staff verifies and adds the member

---

## Member Registration with Payment Plans

When registering new members, staff can now select payment options.

### Registration Process

1. **Fill in Member Details:**
   - Personal information
   - Contact details
   - Banking information

2. **Select Membership Type:**
   - Choose from available memberships
   - Includes base memberships and variations

3. **Select Payment Plan:**
   - After choosing membership, payment options appear
   - Shows all available payment plans
   - Each option displays:
     - Payment name
     - Payment structure (e.g., R500 × 12 = R6000)
     - "(Recommended)" tag for default options

4. **Review and Submit:**
   - Selected payment plan saves with member profile
   - Member will be billed according to chosen plan

### What Happens After Registration

**If Payment Option Selected:**
- Member's record includes selected_payment_option_id
- Billing follows the specific payment schedule
- Auto-renewal applies if configured

**If No Payment Option:**
- Member uses default billing for that membership type
- Standard billing rules apply

---

## Member Portal Features

Members can log in to view their membership details.

### What Members See

**For Individual Memberships:**
- Personal QR code for gym access
- Membership details (type, status, dates)
- Payment plan information
- Recent invoices and payments

**For Family Memberships:**

**Primary Members See:**
- All family members listed
- Member capacity indicator (e.g., 3 of 4 members)
- "Add Member" button (if space available)
- Each family member's status
- All billing information

**Family Members See:**
- Their own QR code
- Family member list
- Note identifying them as family member
- Primary member's name
- Shared membership details

### Family Member Cards

Each family member displays:
- Name
- Role (Primary Member / Family Member)
- Status badge (Active, Suspended, etc.)
- For primary: "Billing account owner" label

---

## Best Practices

### Pricing Strategy

**1. Upfront Discounts:**
- Offer 5-15% discount for upfront payment
- Improves cash flow
- Example: R6000 annual vs R5400 upfront (10% off)

**2. Flexible Monthly Options:**
- Always offer monthly payment option
- Makes membership accessible
- Enable auto-renewal for retention

**3. Quarterly Compromise:**
- Middle ground between upfront and monthly
- Good for corporate clients
- Example: R1500 quarterly vs R500 monthly

### Auto-Renewal Configuration

**Month-to-Month:**
- Use for: Ongoing memberships after initial commitment
- Best for: Retention and steady revenue
- Example: "After 12 months, continues at R500/month"

**Same Duration:**
- Use for: Fixed-term contracts
- Best for: Annual or multi-month commitments
- Example: "Renews for another 12 months"

**No Auto-Renewal:**
- Use for: Upfront payments or flexible trials
- Requires manual renewal
- Good for: Trial periods or short-term memberships

### Family Package Recommendations

**Pricing Guidelines:**
- Don't just multiply by number of members
- Offer family discount (20-30% off individual total)
- Example:
  - Individual: R500/month
  - Family (4): R1200/month (not R2000)
  - Savings: R800/month (40%)

**Max Member Limits:**
- Couple: 2 members
- Small Family: 3-4 members
- Large Family: 5-6 members
- Corporate Group: 10-20 members

**Additional Considerations:**
- Enable multi-site access for families
- Consider age restrictions for family members
- May want separate junior/adult pricing

### Payment Option Naming

**Good Names:**
- "Annual Upfront Saver"
- "Monthly Budget Plan"
- "Quarterly Corporate"
- "Flexible Month-to-Month"

**Avoid:**
- Generic names like "Option 1", "Plan A"
- Technical names like "12-month-recurring"
- Confusing abbreviations

### Member Registration Tips

**Always:**
- Explain payment options to new members
- Highlight recommended option (default)
- Show total savings for upfront options
- Explain auto-renewal clearly

**Document:**
- Which payment option member selected
- Member's understanding of auto-renewal
- Family member relationships (if applicable)

---

## Troubleshooting

### Common Issues

**Payment Options Not Showing:**
- Ensure membership type is selected first
- Check that payment options exist for that membership
- Verify options are marked as active

**Cannot Add Family Member:**
- Check if group is at max capacity
- Verify member is primary member (only primary can add)
- Ensure new member has valid profile

**Auto-Renewal Not Working:**
- Verify auto-renewal is enabled on payment option
- Check renewal frequency is set
- Ensure member's payment option is still active

---

## Quick Reference

### Setup Checklist

- [ ] Create base memberships
- [ ] Set max_members for family packages
- [ ] Add variations (student, corporate, senior)
- [ ] Configure payment options for each membership
- [ ] Set at least one payment option as default
- [ ] Enable auto-renewal on recurring options
- [ ] Test member registration process
- [ ] Verify member portal displays correctly

### Payment Option Quick Setup

**Simple Monthly:**
```
Name: Monthly Plan
Type: Recurring → Monthly
Amount: R500 × 12 = R6000
Auto-Renewal: ON (Month-to-Month)
Default: YES
```

**Annual Upfront:**
```
Name: Annual Saver
Type: Single → One-time
Amount: R5400 × 1 = R5400
Auto-Renewal: OFF
Default: NO
```

---

## Support

For additional assistance:
- Contact your system administrator
- Refer to main ERP360 documentation
- Check video tutorials (if available)
- Email: support@yourgym.com

---

**Document Version:** 1.0  
**Last Updated:** October 2025  
**Applicable to:** ERP360 Gym Management System with Enhanced Package Setup
