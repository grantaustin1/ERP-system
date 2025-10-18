import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import '@/App.css';
import Login from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';
import Members from '@/pages/Members';
import AccessControl from '@/pages/AccessControl';
import BillingEnhanced from '@/pages/BillingEnhanced';
import MemberPortal from '@/pages/MemberPortalEnhanced';
import Settings from '@/pages/Settings';
import Cancellations from '@/pages/Cancellations';
import Levies from '@/pages/Levies';
import Marketing from '@/pages/Marketing';
import PackageSetup from '@/pages/PackageSetupEnhanced';
import Automations from '@/pages/Automations';
import { Toaster } from '@/components/ui/sonner';

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
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/member-portal" element={<MemberPortal />} />
          <Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
          <Route path="/members" element={<PrivateRoute><Members /></PrivateRoute>} />
          <Route path="/access" element={<PrivateRoute><AccessControl /></PrivateRoute>} />
          <Route path="/billing" element={<PrivateRoute><BillingEnhanced /></PrivateRoute>} />
          <Route path="/cancellations" element={<PrivateRoute><Cancellations /></PrivateRoute>} />
          <Route path="/levies" element={<PrivateRoute><Levies /></PrivateRoute>} />
          <Route path="/marketing" element={<PrivateRoute><Marketing /></PrivateRoute>} />
          <Route path="/packages" element={<PrivateRoute><PackageSetup /></PrivateRoute>} />
          <Route path="/automations" element={<PrivateRoute><Automations /></PrivateRoute>} />
          <Route path="/settings" element={<PrivateRoute><Settings /></PrivateRoute>} />
        </Routes>
      </BrowserRouter>
      <Toaster />
    </div>
  );
}

export default App;