import { useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, Users, ScanLine, FileText, UserX, DollarSign, TrendingUp, Package, Settings, LogOut, Dumbbell, Zap, BarChart3, Calendar, Upload, Shield, UserCog, ShoppingCart, Tag, CreditCard, Activity, CheckSquare, Receipt } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { usePermissions } from '@/contexts/PermissionContext';

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { canView, loading } = usePermissions();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  // Map menu items to their required permission module
  const menuItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard', testId: 'nav-dashboard', module: null }, // Always visible
    { path: '/members', icon: Users, label: 'Members', testId: 'nav-members', module: 'members' },
    { path: '/access', icon: ScanLine, label: 'Access Control', testId: 'nav-access', module: 'access' },
    { path: '/classes', icon: Calendar, label: 'Classes', testId: 'nav-classes', module: 'classes' },
    { path: '/pos', icon: ShoppingCart, label: 'Point of Sale', testId: 'nav-pos', module: 'billing' },
    { path: '/billing', icon: FileText, label: 'Billing', testId: 'nav-billing', module: 'billing' },
    { path: '/invoices', icon: Receipt, label: 'Invoices', testId: 'nav-invoices', module: 'billing' },
    { path: '/debit-orders', icon: CreditCard, label: 'Debit Orders', testId: 'nav-debit-orders', module: 'billing' },
    { path: '/reconciliation', icon: Activity, label: 'Reconciliation', testId: 'nav-reconciliation', module: 'billing' },
    { path: '/analytics', icon: BarChart3, label: 'Analytics', testId: 'nav-analytics', module: 'reports' },
    { path: '/levies', icon: DollarSign, label: 'Levies', testId: 'nav-levies', module: 'billing' },
    { path: '/cancellations', icon: UserX, label: 'Cancellations', testId: 'nav-cancellations', module: 'members' },
    { path: '/packages', icon: Package, label: 'Package Setup', testId: 'nav-packages', module: 'settings' },
    { path: '/products', icon: Tag, label: 'Products', testId: 'nav-products', module: 'billing' },
    { path: '/marketing', icon: TrendingUp, label: 'Marketing', testId: 'nav-marketing', module: 'marketing' },
    { path: '/automations', icon: Zap, label: 'Automations', testId: 'nav-automations', module: 'settings' },
    { path: '/tasks', icon: CheckSquare, label: 'Tasks', testId: 'nav-tasks', module: 'members' },
    { path: '/import', icon: Upload, label: 'Import Data', testId: 'nav-import', module: 'import' },
    { path: '/permission-matrix', icon: Shield, label: 'Permissions', testId: 'nav-permissions', module: 'settings' },
    { path: '/user-roles', icon: UserCog, label: 'User Roles', testId: 'nav-user-roles', module: 'staff' },
    { path: '/settings', icon: Settings, label: 'Settings', testId: 'nav-settings', module: 'settings' },
  ];

  // Filter menu items based on permissions
  const visibleMenuItems = menuItems.filter(item => {
    // Dashboard is always visible
    if (!item.module) return true;
    // Check if user has view permission for this module
    return canView(item.module);
  });

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

      {/* Navigation */}
      <nav className="flex-1 space-y-2">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <button
              key={item.path}
              data-testid={item.testId}
              onClick={() => navigate(item.path)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                isActive
                  ? 'bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-lg'
                  : 'text-slate-400 hover:bg-slate-800/50 hover:text-white'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </button>
          );
        })}
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
