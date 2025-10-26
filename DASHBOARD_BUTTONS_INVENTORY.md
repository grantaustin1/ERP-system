# Complete Dashboard Button Inventory

## All Buttons That Should Be Visible on Dashboard

### 1. Quick Actions Section
Located in the top section, these are primary action buttons:
- **"Manage Members"** button - Navigate to members page
- **"Access Control"** button - Navigate to access control
- **"Billing & Invoices"** button - Navigate to billing page

### 2. Member Engagement Alerts Section
Located in the "Member Engagement Alerts" card:
- **"Generate Mock Data"** button - Top right of card header
- **"Send Notification"** button (Green tab) - Send to highly engaged members
- **"Send Notification"** button (Amber tab) - Send to moderately engaged members  
- **"Send Notification"** button (Red tab) - Send to at-risk members

### 3. Stat Card Actions
Each stat card should have a "Click to view details →" link:
- **Total Members** card - Click to drill down
- **Active Members** card - Click to drill down
- **Blocked Members** card - Click to drill down
- **Total Revenue** card - Click to drill down
- **Today's Check-ins** card - Click to drill down
- **New Members This Month** card - Click to drill down

### 4. Drill-Down/Modal Actions
When viewing details (modals):
- **"Back"** button - Return to overview
- **"View Profile"** button - View member profile
- **"Close"** button - Close modal

### 5. Date Range Selector
- Date range picker buttons for filtering data

### 6. Chart/Widget Actions
- **Export** buttons on charts (if implemented)
- **Refresh** buttons on widgets (if implemented)

## Total Expected Interactive Elements
Minimum visible buttons on load: **10-12 buttons**
- 3 Quick Action buttons
- 1 Generate Mock Data button
- 3 Send Notification buttons (one per tab)
- 6+ stat card clickable links

## Common Issues
1. **Tooltips not working on plain HTML `<button>` elements** - WithTooltip expects React components
2. **CSS visibility** - Buttons might exist but not be visible due to styling
3. **Conditional rendering** - Some buttons only show based on data/state
