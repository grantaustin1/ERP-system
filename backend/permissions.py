"""
Enhanced RBAC & Permissions System
Defines resource-level permissions and role mappings for 15 roles and 10 modules
"""
from typing import List, Dict
from fastapi import HTTPException, Depends
from functools import wraps

# All available roles in the system
ROLES = {
    "business_owner": "Business Owner",
    "head_admin": "Head of Admin",
    "sales_head": "Sales Department Head",
    "fitness_head": "Fitness Department Head", 
    "marketing_head": "Marketing Department Head",
    "operations_head": "Operations Department Head",
    "hr_head": "HR Department Head",
    "maintenance_head": "Maintenance Department Head",
    "finance_head": "Finance Department Head",
    "debt_head": "Debt Collecting Department Head",
    "training_head": "Staff Development & Training Department Head",
    "personal_trainer": "Personal Trainer",
    "sales_manager": "Sales Manager (Club Level)",
    "fitness_manager": "Fitness Manager (Club Level)",
    "admin_manager": "Admin Manager (Club Level)",
}

# 10 Modules with CRUD permissions
MODULES = {
    "members": "Members Management",
    "billing": "Billing & Invoicing",
    "access": "Access Control",
    "classes": "Classes & Bookings",
    "marketing": "Marketing",
    "staff": "Staff Management",
    "reports": "Reports & Analytics",
    "import": "Data Import",
    "settings": "Settings",
    "audit": "Audit Logs",
}

# CRUD Actions
ACTIONS = ["view", "create", "edit", "delete"]

# Generate all permissions dynamically: module:action
PERMISSIONS = {}
for module, module_name in MODULES.items():
    for action in ACTIONS:
        perm_key = f"{module}:{action}"
        PERMISSIONS[perm_key] = f"{action.capitalize()} {module_name}"

# Default Role Permissions with sensible defaults
DEFAULT_ROLE_PERMISSIONS: Dict[str, List[str]] = {
    # 1. Business Owner - FULL ACCESS TO EVERYTHING
    "business_owner": list(PERMISSIONS.keys()),
    
    # 2. Head of Admin - Full access to all (Administrator)
    "head_admin": list(PERMISSIONS.keys()),
    
    # 3. Sales Department Head - Full access to Members, Marketing
    "sales_head": [
        "members:view", "members:create", "members:edit", "members:delete",
        "marketing:view", "marketing:create", "marketing:edit", "marketing:delete",
        "billing:view", "billing:create", "billing:edit",
        "reports:view", "reports:create",
        "import:view", "import:create",
        "settings:view",
        "audit:view",
    ],
    
    # 4. Fitness Department Head - Full access to Classes & Bookings, Staff (trainers)
    "fitness_head": [
        "classes:view", "classes:create", "classes:edit", "classes:delete",
        "members:view", "members:edit",
        "staff:view", "staff:create", "staff:edit", "staff:delete",
        "access:view", "access:edit",
        "reports:view", "reports:create",
        "settings:view",
        "audit:view",
    ],
    
    # 5. Marketing Department Head - Full access to Marketing
    "marketing_head": [
        "marketing:view", "marketing:create", "marketing:edit", "marketing:delete",
        "members:view", "members:create",
        "reports:view", "reports:create",
        "settings:view",
        "audit:view",
    ],
    
    # 6. Operations Department Head - Access Control, Settings
    "operations_head": [
        "access:view", "access:create", "access:edit", "access:delete",
        "settings:view", "settings:create", "settings:edit", "settings:delete",
        "members:view",
        "staff:view",
        "reports:view", "reports:create",
        "audit:view",
    ],
    
    # 7. HR Department Head - Full access to Staff Management
    "hr_head": [
        "staff:view", "staff:create", "staff:edit", "staff:delete",
        "members:view",
        "reports:view", "reports:create",
        "settings:view",
        "audit:view",
    ],
    
    # 8. Maintenance Department Head - Access Control, Settings (limited)
    "maintenance_head": [
        "access:view", "access:edit",
        "settings:view", "settings:edit",
        "reports:view",
        "audit:view",
    ],
    
    # 9. Finance Department Head - Full access to Billing & Invoicing
    "finance_head": [
        "billing:view", "billing:create", "billing:edit", "billing:delete",
        "members:view",
        "reports:view", "reports:create", "reports:edit",
        "settings:view",
        "audit:view",
    ],
    
    # 10. Debt Collecting Department Head - Billing (limited), Members (view/edit)
    "debt_head": [
        "billing:view", "billing:edit",
        "members:view", "members:edit",
        "reports:view",
        "settings:view",
        "audit:view",
    ],
    
    # 11. Staff Development & Training Department Head - Staff, Classes
    "training_head": [
        "staff:view", "staff:edit",
        "classes:view", "classes:create", "classes:edit",
        "reports:view",
        "settings:view",
        "audit:view",
    ],
    
    # 12. Personal Trainers - View Members, View/Book Classes
    "personal_trainer": [
        "members:view",
        "classes:view",
        "settings:view",
    ],
    
    # 13. Sales Managers (Club Level) - View/Edit within parameters
    "sales_manager": [
        "members:view", "members:create", "members:edit",
        "marketing:view", "marketing:edit",
        "billing:view", "billing:create",
        "reports:view",
        "import:view",
        "settings:view",
    ],
    
    # 14. Fitness Managers (Club Level) - View/Edit within parameters
    "fitness_manager": [
        "classes:view", "classes:create", "classes:edit",
        "members:view", "members:edit",
        "staff:view", "staff:edit",
        "access:view", "access:edit",
        "reports:view",
        "settings:view",
    ],
    
    # 15. Admin Managers (Club Level) - View/Edit within parameters
    "admin_manager": [
        "members:view", "members:create", "members:edit",
        "billing:view", "billing:create", "billing:edit",
        "access:view", "access:edit",
        "reports:view",
        "import:view", "import:create",
        "settings:view", "settings:edit",
        "audit:view",
    ],
}


def has_permission(user_role: str, required_permission: str, custom_permissions: List[str] = None) -> bool:
    """
    Check if a user role has a specific permission
    
    Args:
        user_role: The user's role (business_owner, head_admin, etc.)
        required_permission: The required permission (e.g., "members:create")
        custom_permissions: Optional custom permissions list (overrides default)
    
    Returns:
        bool: True if user has permission, False otherwise
    """
    # Use custom permissions if provided, otherwise use defaults
    permissions = custom_permissions if custom_permissions is not None else DEFAULT_ROLE_PERMISSIONS.get(user_role, [])
    
    return required_permission in permissions


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
