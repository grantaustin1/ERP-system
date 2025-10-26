import { usePermissions } from '../contexts/PermissionContext';

/**
 * Enhanced permission checking hook with granular action-level checks
 * Usage: const { canPerform, canView, canCreate, canEdit, canDelete } = usePermissionCheck();
 */
export function usePermissionCheck() {
  const { canView: contextCanView, userPermissions, loading } = usePermissions();

  /**
   * Check if user can perform a specific action on a module
   * @param {string} module - Module name (e.g., 'members', 'billing')
   * @param {string} action - Action type ('view', 'create', 'edit', 'delete')
   * @returns {boolean}
   */
  const canPerform = (module, action) => {
    if (loading) return false;
    
    const permissionKey = `${module}:${action}`;
    return userPermissions?.includes(permissionKey) || false;
  };

  /**
   * Shorthand for view permission
   */
  const canView = (module) => canPerform(module, 'view');

  /**
   * Shorthand for create permission
   */
  const canCreate = (module) => canPerform(module, 'create');

  /**
   * Shorthand for edit permission
   */
  const canEdit = (module) => canPerform(module, 'edit');

  /**
   * Shorthand for delete permission
   */
  const canDelete = (module) => canPerform(module, 'delete');

  /**
   * Check if user has ANY of the specified permissions
   */
  const canPerformAny = (permissions) => {
    if (loading) return false;
    return permissions.some(perm => {
      const [module, action] = perm.split(':');
      return canPerform(module, action);
    });
  };

  /**
   * Check if user has ALL of the specified permissions
   */
  const canPerformAll = (permissions) => {
    if (loading) return false;
    return permissions.every(perm => {
      const [module, action] = perm.split(':');
      return canPerform(module, action);
    });
  };

  return {
    canPerform,
    canView,
    canCreate,
    canEdit,
    canDelete,
    canPerformAny,
    canPerformAll,
    loading,
    userPermissions
  };
}
