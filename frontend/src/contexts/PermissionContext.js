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
      if (!token) {
        setLoading(false);
        return;
      }

      // Get current user info
      const response = await axios.get(`${API}/auth/me`);
      const user = response.data;
      setUserRole(user.role);

      // Get permission matrix to find user's permissions
      const matrixResponse = await axios.get(`${API}/rbac/permission-matrix`);
      const matrix = matrixResponse.data.matrix;

      // Find permissions for user's role
      const rolePermissions = matrix.find(r => r.role === user.role);
      if (rolePermissions) {
        setPermissions(rolePermissions.permissions);
      }
    } catch (error) {
      console.error('Failed to fetch user permissions:', error);
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
    const permission = `${module}:view`;
    const result = hasPermission(permission);
    if (module === 'settings' || module === 'staff' || module === 'import') {
      console.log(`[PermissionContext] canView('${module}') = ${result}, checking: ${permission}`);
    }
    return result;
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
