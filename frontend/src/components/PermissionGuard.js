import { usePermissions } from '@/contexts/PermissionContext';

/**
 * PermissionGuard - Conditionally render children based on permissions
 * 
 * Usage:
 * <PermissionGuard permission="members:create">
 *   <Button>Create Member</Button>
 * </PermissionGuard>
 * 
 * <PermissionGuard permissions={['members:edit', 'members:delete']} requireAll={false}>
 *   <Button>Edit or Delete</Button>
 * </PermissionGuard>
 */
export const PermissionGuard = ({ 
  permission, 
  permissions, 
  requireAll = false,
  fallback = null,
  children 
}) => {
  const { hasPermission, hasAnyPermission, hasAllPermissions, loading } = usePermissions();

  if (loading) {
    return fallback;
  }

  let hasAccess = false;

  if (permission) {
    // Single permission check
    hasAccess = hasPermission(permission);
  } else if (permissions) {
    // Multiple permissions check
    hasAccess = requireAll 
      ? hasAllPermissions(permissions)
      : hasAnyPermission(permissions);
  }

  return hasAccess ? children : fallback;
};

export default PermissionGuard;
