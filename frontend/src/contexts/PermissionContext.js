import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';

const PermissionContext = createContext();

export const PermissionProvider = ({ children }) => {
  const [permissions, setPermissions] = useState([]);
  const [userRole, setUserRole] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUserPermissions();
  }, []);

  const fetchUserPermissions = async () => {
    try {
      const token = localStorage.getItem('token');
      console.log('[PermissionContext] Token exists:', !!token);
      if (!token) {
        setLoading(false);
        return;
      }

      // Get current user info
      const response = await axios.get(`${API}/auth/me`);
      const user = response.data;
      console.log('[PermissionContext] Current user:', user.email, 'Role:', user.role);
      setUserRole(user.role);

      // Get permission matrix to find user's permissions
      console.log('[PermissionContext] Fetching permission matrix...');
      const matrixResponse = await axios.get(`${API}/rbac/permission-matrix`);
      const matrix = matrixResponse.data.matrix;
      console.log('[PermissionContext] Permission matrix loaded, entries:', matrix.length);

      // Find permissions for user's role
      const rolePermissions = matrix.find(r => r.role === user.role);
      if (rolePermissions) {
        console.log('[PermissionContext] Found permissions for role:', user.role, 'Count:', rolePermissions.permissions.length);
        console.log('[PermissionContext] Settings permissions:', rolePermissions.permissions.filter(p => p.startsWith('settings:')));
        console.log('[PermissionContext] Staff permissions:', rolePermissions.permissions.filter(p => p.startsWith('staff:')));
        console.log('[PermissionContext] Import permissions:', rolePermissions.permissions.filter(p => p.startsWith('import:')));
        setPermissions(rolePermissions.permissions);
      } else {
        console.warn('[PermissionContext] No permissions found for role:', user.role);
      }
    } catch (error) {
      console.error('[PermissionContext] Failed to fetch user permissions:', error);
      console.error('[PermissionContext] Error details:', error.response?.data || error.message);
    } finally {
      setLoading(false);
    }
  };

  const hasPermission = (permission) => {
    return permissions.includes(permission);
  };

  const hasAnyPermission = (permissionList) => {
    return permissionList.some(permission => permissions.includes(permission));
  };

  const hasAllPermissions = (permissionList) => {
    return permissionList.every(permission => permissions.includes(permission));
  };

  const canView = (module) => {
    return hasPermission(`${module}:view`);
  };

  const canCreate = (module) => {
    return hasPermission(`${module}:create`);
  };

  const canEdit = (module) => {
    return hasPermission(`${module}:edit`);
  };

  const canDelete = (module) => {
    return hasPermission(`${module}:delete`);
  };

  const value = {
    permissions,
    userRole,
    loading,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    canView,
    canCreate,
    canEdit,
    canDelete,
    refreshPermissions: fetchUserPermissions
  };

  return (
    <PermissionContext.Provider value={value}>
      {children}
    </PermissionContext.Provider>
  );
};

export const usePermissions = () => {
  const context = useContext(PermissionContext);
  if (context === undefined) {
    throw new Error('usePermissions must be used within a PermissionProvider');
  }
  return context;
};
