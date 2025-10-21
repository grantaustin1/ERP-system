"""
Enhanced RBAC & Permissions System
Defines resource-level permissions and role mappings
"""
from typing import List, Dict
from fastapi import HTTPException, Depends
from functools import wraps

# Permission definitions
# Format: "resource:action"
PERMISSIONS = {
    # Member permissions
    "members:read": "View member information",
    "members:create": "Create new members",
    "members:update": "Update member information",
    "members:delete": "Delete members",
    "members:check_duplicate": "Check for duplicate members",
    
    # Invoice/Billing permissions
    "invoices:read": "View invoices",
    "invoices:create": "Create invoices",
    "invoices:update": "Update invoice status",
    "invoices:delete": "Delete invoices",
    "invoices:payment": "Record payments",
    
    # Class/Booking permissions
    "classes:read": "View classes",
    "classes:create": "Create new classes",
    "classes:update": "Update class details",
    "classes:delete": "Delete classes",
    "bookings:read": "View bookings",
    "bookings:create": "Create bookings",
    "bookings:update": "Update bookings",
    "bookings:cancel": "Cancel bookings",
    "bookings:checkin": "Check-in members to classes",
    
    # Access Control permissions
    "access:read": "View access logs",
    "access:validate": "Validate member access",
    "access:override": "Override access restrictions",
    
    # Automation permissions
    "automations:read": "View automations",
    "automations:create": "Create automations",
    "automations:update": "Update automations",
    "automations:delete": "Delete automations",
    "automations:test": "Test automations",
    
    # Report permissions
    "reports:view": "View reports",
    "reports:export": "Export reports (CSV, PDF)",
    "reports:blocked_members": "View blocked member attempts",
    "reports:analytics": "View analytics dashboard",
    
    # Import/Export permissions
    "import:members": "Import member data",
    "import:leads": "Import lead data",
    "export:data": "Export system data",
    
    # Settings permissions
    "settings:read": "View settings",
    "settings:update": "Update system settings",
    "settings:payment_sources": "Manage payment sources",
    "settings:field_config": "Configure field validation",
    
    # Audit permissions
    "audit:read": "View audit logs",
    
    # User Management permissions
    "users:read": "View users",
    "users:create": "Create new users",
    "users:update": "Update user roles and permissions",
    "users:delete": "Delete users",
}

# Role to Permissions mapping
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "admin": [
        # Admins have ALL permissions
        *PERMISSIONS.keys()
    ],
    
    "manager": [
        # Members
        "members:read", "members:create", "members:update", "members:check_duplicate",
        # Invoices
        "invoices:read", "invoices:create", "invoices:update", "invoices:payment",
        # Classes & Bookings
        "classes:read", "classes:create", "classes:update",
        "bookings:read", "bookings:create", "bookings:update", "bookings:cancel", "bookings:checkin",
        # Access
        "access:read", "access:validate", "access:override",
        # Automations
        "automations:read", "automations:create", "automations:update", "automations:test",
        # Reports
        "reports:view", "reports:export", "reports:blocked_members", "reports:analytics",
        # Import
        "import:members", "import:leads", "export:data",
        # Settings (limited)
        "settings:read",
        # Audit (read-only)
        "audit:read",
    ],
    
    "staff": [
        # Members (read, create, update only)
        "members:read", "members:create", "members:update", "members:check_duplicate",
        # Invoices (read, payment only)
        "invoices:read", "invoices:payment",
        # Classes & Bookings
        "classes:read",
        "bookings:read", "bookings:create", "bookings:update", "bookings:checkin",
        # Access
        "access:read", "access:validate",
        # Reports (view only)
        "reports:view", "reports:analytics",
        # Settings (read only)
        "settings:read",
    ],
    
    "member": [
        # Limited self-service permissions
        "members:read",  # Can only read own profile
        "invoices:read",  # Can only read own invoices
        "bookings:read", "bookings:create", "bookings:cancel",  # Manage own bookings
        "classes:read",  # View class schedule
    ],
    
    "guest": [
        # Very limited permissions
        "classes:read",  # View class schedule only
    ]
}


def has_permission(user_role: str, required_permission: str) -> bool:
    """
    Check if a user role has a specific permission
    
    Args:
        user_role: The user's role (admin, manager, staff, member, guest)
        required_permission: The required permission (e.g., "members:create")
    
    Returns:
        bool: True if user has permission, False otherwise
    """
    if user_role not in ROLE_PERMISSIONS:
        return False
    
    return required_permission in ROLE_PERMISSIONS[user_role]


def require_permission(permission: str):
    """
    Decorator to require specific permission for an endpoint
    
    Usage:
        @api_router.post("/members")
        @require_permission("members:create")
        async def create_member(data: MemberCreate, current_user: User = Depends(get_current_user)):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get('current_user')
            if not current_user:
                # Try to find it in args (less reliable)
                for arg in args:
                    if hasattr(arg, 'role'):
                        current_user = arg
                        break
            
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Check permission
            if not has_permission(current_user.role, permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied. Required permission: {permission}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def get_user_permissions(role: str) -> List[str]:
    """
    Get all permissions for a given role
    
    Args:
        role: The user's role
    
    Returns:
        List of permission strings the role has access to
    """
    return ROLE_PERMISSIONS.get(role, [])


def check_multiple_permissions(user_role: str, permissions: List[str]) -> bool:
    """
    Check if user has ALL of the specified permissions (AND logic)
    
    Args:
        user_role: The user's role
        permissions: List of required permissions
    
    Returns:
        bool: True if user has all permissions, False otherwise
    """
    return all(has_permission(user_role, perm) for perm in permissions)


def check_any_permission(user_role: str, permissions: List[str]) -> bool:
    """
    Check if user has ANY of the specified permissions (OR logic)
    
    Args:
        user_role: The user's role
        permissions: List of possible permissions
    
    Returns:
        bool: True if user has at least one permission, False otherwise
    """
    return any(has_permission(user_role, perm) for perm in permissions)
