import React, { useState, useEffect } from 'react';
import { useToast } from '../hooks/use-toast';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '../components/ui/table';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Shield, Save, RotateCcw, CheckCircle2, XCircle } from 'lucide-react';
import { Checkbox } from '../components/ui/checkbox';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export default function PermissionMatrix() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [roles, setRoles] = useState([]);
  const [modules, setModules] = useState([]);
  const [permissionMatrix, setPermissionMatrix] = useState({});
  const [originalMatrix, setOriginalMatrix] = useState({});
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    fetchPermissionData();
  }, []);

  const fetchPermissionData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Fetch all roles, modules, and current permission matrix
      const [rolesRes, modulesRes, matrixRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/rbac/roles`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`${BACKEND_URL}/api/rbac/modules`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`${BACKEND_URL}/api/rbac/permission-matrix`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      const rolesData = await rolesRes.json();
      const modulesData = await modulesRes.json();
      const matrixData = await matrixRes.json();

      setRoles(rolesData.roles);
      setModules(modulesData.modules);

      // Build permission matrix object: { role_key: { "module:action": true/false } }
      const matrix = {};
      matrixData.matrix.forEach(roleData => {
        matrix[roleData.role] = {};
        matrixData.all_permissions.forEach(perm => {
          matrix[roleData.role][perm] = roleData.permissions.includes(perm);
        });
      });

      setPermissionMatrix(matrix);
      setOriginalMatrix(JSON.parse(JSON.stringify(matrix))); // Deep copy
      setHasChanges(false);

    } catch (error) {
      console.error('Error fetching permission data:', error);
      toast({
        title: "Error",
        description: "Failed to load permission data",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePermissionToggle = (roleKey, permissionKey) => {
    setPermissionMatrix(prev => {
      const newMatrix = { ...prev };
      newMatrix[roleKey] = {
        ...newMatrix[roleKey],
        [permissionKey]: !newMatrix[roleKey][permissionKey]
      };
      return newMatrix;
    });
    setHasChanges(true);
  };

  const handleSaveChanges = async () => {
    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      
      // Save each role's permissions
      const savePromises = roles.map(async (role) => {
        const permissions = Object.keys(permissionMatrix[role.key])
          .filter(perm => permissionMatrix[role.key][perm]);
        
        // Only save if there are changes for this role
        const originalPerms = Object.keys(originalMatrix[role.key])
          .filter(perm => originalMatrix[role.key][perm]);
        
        if (JSON.stringify(permissions.sort()) !== JSON.stringify(originalPerms.sort())) {
          return fetch(`${BACKEND_URL}/api/rbac/permission-matrix`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`
            },
            body: JSON.stringify({
              role: role.key,
              permissions: permissions
            })
          });
        }
        return null;
      });

      await Promise.all(savePromises.filter(p => p !== null));

      toast({
        title: "Success",
        description: "Permission changes saved successfully",
      });

      // Refresh data
      await fetchPermissionData();

    } catch (error) {
      console.error('Error saving permissions:', error);
      toast({
        title: "Error",
        description: "Failed to save permission changes",
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  const handleResetRole = async (roleKey, roleName) => {
    if (!window.confirm(`Reset ${roleName} to default permissions?`)) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/rbac/reset-role-permissions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ role: roleKey })
      });

      if (!response.ok) throw new Error('Failed to reset permissions');

      toast({
        title: "Success",
        description: `${roleName} permissions reset to defaults`,
      });

      await fetchPermissionData();

    } catch (error) {
      console.error('Error resetting permissions:', error);
      toast({
        title: "Error",
        description: "Failed to reset permissions",
        variant: "destructive"
      });
    }
  };

  const handleDiscardChanges = () => {
    setPermissionMatrix(JSON.parse(JSON.stringify(originalMatrix)));
    setHasChanges(false);
    toast({
      title: "Changes Discarded",
      description: "All unsaved changes have been discarded",
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading permission matrix...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield className="h-8 w-8 text-blue-600" />
              <div>
                <CardTitle className="text-2xl">Permission Matrix</CardTitle>
                <CardDescription>
                  Manage role-based permissions across all modules
                </CardDescription>
              </div>
            </div>
            <div className="flex gap-2">
              {hasChanges && (
                <>
                  <Button 
                    variant="outline" 
                    onClick={handleDiscardChanges}
                    disabled={saving}
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    Discard Changes
                  </Button>
                  <Button 
                    onClick={handleSaveChanges}
                    disabled={saving}
                  >
                    <Save className="h-4 w-4 mr-2" />
                    {saving ? 'Saving...' : 'Save Changes'}
                  </Button>
                </>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-64 sticky left-0 bg-white z-10">
                    <div className="font-bold">Module / Action</div>
                  </TableHead>
                  {roles.map(role => (
                    <TableHead key={role.key} className="text-center min-w-[120px]">
                      <div className="flex flex-col gap-1">
                        <div className="font-semibold text-xs">{role.name}</div>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleResetRole(role.key, role.name)}
                          className="h-6 text-xs"
                        >
                          <RotateCcw className="h-3 w-3 mr-1" />
                          Reset
                        </Button>
                      </div>
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {modules.map(module => (
                  <React.Fragment key={module.key}>
                    <TableRow className="bg-gray-50">
                      <TableCell 
                        colSpan={roles.length + 1}
                        className="font-bold text-sm sticky left-0 z-10 bg-gray-50"
                      >
                        {module.name}
                      </TableCell>
                    </TableRow>
                    {module.permissions.map(permission => (
                      <TableRow key={permission.key}>
                        <TableCell className="sticky left-0 bg-white z-10">
                          <div className="flex flex-col">
                            <span className="font-medium text-sm capitalize">
                              {permission.action}
                            </span>
                            <span className="text-xs text-gray-500">
                              {permission.key}
                            </span>
                          </div>
                        </TableCell>
                        {roles.map(role => (
                          <TableCell key={role.key} className="text-center">
                            <input
                              type="checkbox"
                              checked={permissionMatrix[role.key]?.[permission.key] || false}
                              onChange={() => handlePermissionToggle(role.key, permission.key)}
                              className="h-4 w-4 mx-auto cursor-pointer"
                            />
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </React.Fragment>
                ))}
              </TableBody>
            </Table>
          </div>

          {hasChanges && (
            <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-center gap-2 text-yellow-800">
                <CheckCircle2 className="h-5 w-5" />
                <span className="font-medium">You have unsaved changes</span>
              </div>
              <p className="text-sm text-yellow-700 mt-1">
                Click "Save Changes" to apply your permission updates or "Discard Changes" to cancel.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
