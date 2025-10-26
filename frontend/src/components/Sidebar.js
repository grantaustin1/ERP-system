import { useNavigate, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { LayoutDashboard, Users, ScanLine, FileText, UserX, DollarSign, TrendingUp, Package, Settings, LogOut, Dumbbell, Zap, BarChart3, Calendar, Upload, Shield, UserCog, ShoppingCart, Tag, CreditCard, Activity, CheckSquare, Receipt, FileBarChart, LineChart, Award, Target, Briefcase, Workflow, Gift, Bell, Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { usePermissions } from '@/contexts/PermissionContext';
import GlobalSearch from '@/components/GlobalSearch';

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { canView, loading } = usePermissions();
  const [userRole, setUserRole] = useState(null);
  const [memberStatus, setMemberStatus] = useState(null);
  const [appSettings, setAppSettings] = useState(null);

  // Get user role, member status, and app settings
  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const token = localStorage.getItem('token');
        if (token) {
          // Fetch user info
          const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/me`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (response.ok) {
            const data = await response.json();
            setUserRole(data.role);
            // If user has a member record, get member status
            if (data.member_id) {
              const memberResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/members/${data.member_id}`, {
                headers: { Authorization: `Bearer ${token}` }
              });
              if (memberResponse.ok) {
                const memberData = await memberResponse.json();
                setMemberStatus(memberData.membership_status);
              }
            }
          }
          
          // Fetch app settings
          const settingsResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/settings/app`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (settingsResponse.ok) {
            const settingsData = await settingsResponse.json();
            setAppSettings(settingsData);
          }
        }
      } catch (error) {
        console.error('Error fetching user info:', error);
      }
    };
    fetchUserInfo();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  // Organized menu items by category with their required permission modules
  const menuCategories = [
    {
      name: 'Core',
      items: [
        { path: '/', icon: LayoutDashboard, label: 'Dashboard', testId: 'nav-dashboard', module: null },
        { path: '/members', icon: Users, label: 'Members', testId: 'nav-members', module: 'members' },
        { path: '/access', icon: ScanLine, label: 'Access Control', testId: 'nav-access', module: 'access' },
        { path: '/classes', icon: Calendar, label: 'Classes', testId: 'nav-classes', module: 'classes' },
      ]
    },
    {
      name: 'Sales & CRM',
      items: [
        { path: '/sales', icon: Briefcase, label: 'Sales CRM', testId: 'nav-sales', module: null },
        { path: '/sales/complimentary', icon: Gift, label: 'Complimentary Passes', testId: 'nav-complimentary', module: null },
        { path: '/sales/workflows', icon: Workflow, label: 'Sales Workflows', testId: 'nav-sales-workflows', module: null },
        { path: '/sales/setup', icon: Settings, label: 'Sales Setup', testId: 'nav-sales-setup', module: null },
      ]
    },
    {
      name: 'Financial',
      items: [
        { path: '/pos', icon: ShoppingCart, label: 'Point of Sale', testId: 'nav-pos', module: 'billing' },
        { path: '/billing', icon: FileText, label: 'Billing', testId: 'nav-billing', module: 'billing' },
        { path: '/invoices', icon: Receipt, label: 'Invoices', testId: 'nav-invoices', module: 'billing' },
        { path: '/debit-orders', icon: CreditCard, label: 'Debit Orders', testId: 'nav-debit-orders', module: 'billing' },
        { path: '/levies', icon: DollarSign, label: 'Levies', testId: 'nav-levies', module: 'billing' },
        { path: '/reconciliation', icon: Activity, label: 'Reconciliation', testId: 'nav-reconciliation', module: 'billing' },
      ]
    },
    {
      name: 'Analytics & Reports',
      items: [
        { path: '/analytics', icon: BarChart3, label: 'Analytics', testId: 'nav-analytics', module: 'reports' },
        { path: '/advanced-analytics', icon: LineChart, label: 'Advanced Analytics', testId: 'nav-advanced-analytics', module: 'reports' },
        { path: '/reports', icon: FileBarChart, label: 'Reports', testId: 'nav-reports', module: 'reports' },
        { path: '/reports/financial', icon: DollarSign, label: 'Financial Reports', testId: 'nav-financial-reports', module: 'reports' },
        { path: '/reports/members', icon: Users, label: 'Member Analytics', testId: 'nav-member-analytics', module: 'reports' },
        { path: '/reports/sales', icon: Target, label: 'Sales Performance', testId: 'nav-sales-performance', module: 'reports' },
      ]
    },
    {
      name: 'Retention & Engagement',
      items: [
        { path: '/engagement', icon: Target, label: 'Engagement', testId: 'nav-engagement', module: null },
        { path: '/rewards', icon: Award, label: 'Points & Rewards', testId: 'nav-rewards', module: null },
        { path: '/member-portal', icon: Bell, label: 'Member Portal', testId: 'nav-member-portal', module: null, requireActiveMember: true },
        { path: '/admin/broadcast', icon: Send, label: 'Broadcast', testId: 'nav-broadcast', module: null, requireAdmin: true },
      ]
    },
    {
      name: 'Operations',
      items: [
        { path: '/tasks', icon: CheckSquare, label: 'Tasks', testId: 'nav-tasks', module: 'members' },
        { path: '/packages', icon: Package, label: 'Packages', testId: 'nav-packages', module: 'settings' },
        { path: '/products', icon: Tag, label: 'Products', testId: 'nav-products', module: 'billing' },
        { path: '/cancellations', icon: UserX, label: 'Cancellations', testId: 'nav-cancellations', module: 'members' },
      ]
    },
    {
      name: 'Marketing',
      items: [
        { path: '/marketing', icon: TrendingUp, label: 'Marketing', testId: 'nav-marketing', module: 'marketing' },
        { path: '/automations', icon: Zap, label: 'Automations', testId: 'nav-automations', module: 'settings' },
      ]
    },
    {
      name: 'System',
      items: [
        { path: '/import', icon: Upload, label: 'Import Data', testId: 'nav-import', module: 'import' },
        { path: '/permission-matrix', icon: Shield, label: 'Permissions', testId: 'nav-permissions', module: 'settings' },
        { path: '/user-roles', icon: UserCog, label: 'User Roles', testId: 'nav-user-roles', module: 'staff' },
        { path: '/settings', icon: Settings, label: 'Settings', testId: 'nav-settings', module: 'settings' },
      ]
    },
  ];

  // Filter menu items based on permissions and role requirements
  const isItemVisible = (item) => {
    // Check module-based permissions
    if (item.module && !canView(item.module)) {
      if (item.label === 'Settings' || item.label === 'User Roles' || item.label === 'Import Data' || item.label === 'Permissions') {
        console.log(`[Sidebar] Item '${item.label}' filtered out - no permission for module '${item.module}'`);
      }
      return false;
    }
    
    // Check if item requires admin role
    if (item.requireAdmin) {
      const adminRoles = ['business_owner', 'head_admin', 'admin_manager', 'sales_manager', 'fitness_manager'];
      if (!userRole || !adminRoles.includes(userRole)) {
        return false;
      }
    }
    
    // Check if item requires active member status (Member Portal)
    if (item.requireActiveMember) {
      // Check if member portal is globally enabled
      if (appSettings && !appSettings.member_portal_enabled) {
        return false;
      }
      
      // Check if member portal requires active status and if user's status is active
      if (appSettings && appSettings.member_portal_require_active_status) {
        if (memberStatus !== 'active') {
          return false;
        }
      }
    }
    
    return true;
  };

  // Filter categories to only show those with visible items
  const visibleCategories = menuCategories
    .map(category => ({
      ...category,
      items: category.items.filter(isItemVisible)
    }))
    .filter(category => category.items.length > 0);
  
  // Log System category status
  const systemCategory = menuCategories.find(cat => cat.name === 'System');
  if (systemCategory) {
    const systemVisibleItems = systemCategory.items.filter(isItemVisible);
    console.log('[Sidebar] System category - Total items:', systemCategory.items.length, 'Visible items:', systemVisibleItems.length);
    console.log('[Sidebar] System visible items:', systemVisibleItems.map(i => i.label));
  }
  console.log('[Sidebar] Visible categories:', visibleCategories.map(c => c.name));

  return (
    <div className="w-64 bg-slate-900/50 backdrop-blur-lg border-r border-slate-700 p-6 flex flex-col">
      {/* Logo */}
      <div className="mb-8">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-r from-emerald-500 to-teal-600 flex items-center justify-center">
            <Dumbbell className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-white font-bold text-lg">GymAccess</h2>
            <p className="text-slate-400 text-xs">Hub</p>
          </div>
        </div>
      </div>

      {/* Global Search */}
      <div className="mb-6">
        <GlobalSearch />
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-6 overflow-y-auto">
        {loading ? (
          <div className="text-slate-400 text-sm text-center py-4">Loading...</div>
        ) : (
          visibleCategories.map((category) => (
            <div key={category.name} className="space-y-2">
              {/* Category Header */}
              <div className="px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                {category.name}
              </div>
              
              {/* Category Items */}
              {category.items.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <button
                    key={item.path}
                    data-testid={item.testId}
                    onClick={() => navigate(item.path)}
                    className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all ${
                      isActive
                        ? 'bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-lg'
                        : 'text-slate-400 hover:bg-slate-800/50 hover:text-white'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="text-sm font-medium">{item.label}</span>
                  </button>
                );
              })}
            </div>
          ))
        )}
      </nav>

      {/* Logout Button */}
      <Button
        variant="outline"
        onClick={handleLogout}
        className="w-full border-red-500 text-red-400 hover:bg-red-500/10 hover:text-red-300"
        data-testid="logout-button"
      >
        <LogOut className="w-4 h-4 mr-2" />
        Logout
      </Button>
    </div>
  );
}
