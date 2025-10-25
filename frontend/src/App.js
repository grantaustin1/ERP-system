import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import '@/App.css';
import Login from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';
import Members from '@/pages/Members';
import AccessControl from '@/pages/AccessControlEnhanced';
import BillingEnhanced from '@/pages/BillingEnhanced';
import InvoiceManagement from '@/pages/InvoiceManagement';
import MemberPortal from '@/pages/MemberPortalEnhanced';
import Settings from '@/pages/Settings';
import SettingsNew from '@/pages/SettingsNew';
import DebitOrderManagement from '@/pages/DebitOrderManagement';
import TransactionReconciliation from '@/pages/TransactionReconciliation';
import Cancellations from '@/pages/Cancellations';
import Levies from '@/pages/Levies';
import Marketing from '@/pages/Marketing';
import PackageSetup from '@/pages/PackageSetupEnhanced';
import Automations from '@/pages/AutomationsGeneric';
import Analytics from '@/pages/Analytics';
import Classes from '@/pages/Classes';
import DataImport from '@/pages/DataImport';
import PermissionMatrix from '@/pages/PermissionMatrix';
import UserRoleManagement from '@/pages/UserRoleManagement';
import POS from '@/pages/POS';
import ProductManagement from '@/pages/ProductManagement';
import Tasks from '@/pages/Tasks';
import Reports from '@/pages/Reports';
import AdvancedAnalytics from '@/pages/AdvancedAnalytics';
import PointsRewards from '@/pages/PointsRewards';
import EngagementDashboard from '@/pages/EngagementDashboard';
import SalesDashboard from '@/pages/SalesDashboard';
import LeadsContacts from '@/pages/LeadsContacts';
import SalesPipeline from '@/pages/SalesPipeline';
import SalesTasks from '@/pages/SalesTasks';
import WorkflowAutomation from '@/pages/WorkflowAutomation';
import SalesCRMSetup from '@/pages/SalesCRMSetup';
import ComplimentaryMembership from '@/pages/ComplimentaryMembership';
import { Toaster } from '@/components/ui/sonner';
import { PermissionProvider } from '@/contexts/PermissionContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// Axios interceptor for auth
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

function PrivateRoute({ children }) {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <div className="App">
      <PermissionProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/member-portal" element={<MemberPortal />} />
            <Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
            <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
            <Route path="/members" element={<PrivateRoute><Members /></PrivateRoute>} />
            <Route path="/access" element={<PrivateRoute><AccessControl /></PrivateRoute>} />
            <Route path="/classes" element={<PrivateRoute><Classes /></PrivateRoute>} />
            <Route path="/billing" element={<PrivateRoute><BillingEnhanced /></PrivateRoute>} />
            <Route path="/invoices" element={<PrivateRoute><InvoiceManagement /></PrivateRoute>} />
            <Route path="/cancellations" element={<PrivateRoute><Cancellations /></PrivateRoute>} />
            <Route path="/levies" element={<PrivateRoute><Levies /></PrivateRoute>} />
            <Route path="/marketing" element={<PrivateRoute><Marketing /></PrivateRoute>} />
            <Route path="/packages" element={<PrivateRoute><PackageSetup /></PrivateRoute>} />
            <Route path="/automations" element={<PrivateRoute><Automations /></PrivateRoute>} />
            <Route path="/analytics" element={<PrivateRoute><Analytics /></PrivateRoute>} />
            <Route path="/advanced-analytics" element={<PrivateRoute><AdvancedAnalytics /></PrivateRoute>} />
            <Route path="/rewards" element={<PrivateRoute><PointsRewards /></PrivateRoute>} />
            <Route path="/engagement" element={<PrivateRoute><EngagementDashboard /></PrivateRoute>} />
            <Route path="/sales" element={<PrivateRoute><SalesDashboard /></PrivateRoute>} />
            <Route path="/sales/leads" element={<PrivateRoute><LeadsContacts /></PrivateRoute>} />
            <Route path="/sales/pipeline" element={<PrivateRoute><SalesPipeline /></PrivateRoute>} />
            <Route path="/sales/tasks" element={<PrivateRoute><SalesTasks /></PrivateRoute>} />
            <Route path="/sales/workflows" element={<PrivateRoute><WorkflowAutomation /></PrivateRoute>} />
            <Route path="/sales/setup" element={<PrivateRoute><SalesCRMSetup /></PrivateRoute>} />
            <Route path="/sales/complimentary" element={<PrivateRoute><ComplimentaryMembership /></PrivateRoute>} />
            <Route path="/reports" element={<PrivateRoute><Reports /></PrivateRoute>} />
            <Route path="/import" element={<PrivateRoute><DataImport /></PrivateRoute>} />
            <Route path="/permission-matrix" element={<PrivateRoute><PermissionMatrix /></PrivateRoute>} />
            <Route path="/user-roles" element={<PrivateRoute><UserRoleManagement /></PrivateRoute>} />
            <Route path="/pos" element={<PrivateRoute><POS /></PrivateRoute>} />
            <Route path="/products" element={<PrivateRoute><ProductManagement /></PrivateRoute>} />
            <Route path="/tasks" element={<PrivateRoute><Tasks /></PrivateRoute>} />
            <Route path="/settings" element={<PrivateRoute><SettingsNew /></PrivateRoute>} />
            <Route path="/settings-old" element={<PrivateRoute><Settings /></PrivateRoute>} />
            <Route path="/debit-orders" element={<PrivateRoute><DebitOrderManagement /></PrivateRoute>} />
            <Route path="/reconciliation" element={<PrivateRoute><TransactionReconciliation /></PrivateRoute>} />
          </Routes>
        </BrowserRouter>
        <Toaster />
      </PermissionProvider>
    </div>
  );
}

export default App;