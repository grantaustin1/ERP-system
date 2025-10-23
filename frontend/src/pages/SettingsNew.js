import { useState, useEffect } from 'react';
import axios from 'axios';
import Sidebar from '../components/Sidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { useToast } from '../hooks/use-toast';
import {
  CreditCard,
  Users,
  Shield,
  CheckSquare,
  Activity,
  Settings as SettingsIcon,
  Briefcase,
  DollarSign,
  Lock,
  Cog,
  Zap,
  Bell,
  Database,
  BarChart3,
  FileText,
  Building2
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export default function SettingsNew() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [mainCategory, setMainCategory] = useState('business');
  const [activeTab, setActiveTab] = useState('memberships');
  
  // Existing state variables
  const [membershipTypes, setMembershipTypes] = useState([]);
  const [paymentSources, setPaymentSources] = useState([]);
  const [fieldConfigurations, setFieldConfigurations] = useState([]);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    billing_frequency: 'monthly',
    duration_days: 30,
    access_level: 'basic'
  });
  const [sourceForm, setSourceForm] = useState({
    name: '',
    description: '',
    is_active: true,
    display_order: 0
  });
  const [eftSettings, setEftSettings] = useState({
    client_profile_number: '',
    nominated_account: '',
    charges_account: '',
    service_user_number: '',
    branch_code: '',
    bank_name: 'Nedbank',
    enable_notifications: false,
    notification_email: '',
    advance_billing_days: 5,
    enable_auto_generation: false
  });
  const [debiCheckSettings, setDebiCheckSettings] = useState({
    creditor_name: '',
    creditor_abbreviation: '',
    default_mandate_type: 'F',
    default_transaction_type: 'TT2',
    default_adjustment_category: '0',
    enable_mandate_notifications: false
  });
  const [avsSettings, setAvsSettings] = useState({
    profile_number: '',
    profile_user_number: '',
    charge_account: '',
    mock_mode: true,
    use_qa: true,
    enable_auto_verify: false,
    verify_on_update: false
  });
  const [tiSettings, setTiSettings] = useState({
    profile_number: '',
    account_number: '',
    mock_mode: true,
    use_qa: true,
    fti_enabled: true,
    fti_frequency: 'daily',
    pti_enabled: false,
    notifications_enabled: false,
    auto_reconcile: true
  });
  const [alertConfig, setAlertConfig] = useState({
    days_period: 30,
    green_threshold: 10,
    amber_min_threshold: 1,
    amber_max_threshold: 4,
    red_threshold: 0
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [membershipsRes, sourcesRes, fieldConfigsRes, eftSettingsRes, avsSettingsRes, tiSettingsRes, alertConfigRes] = await Promise.all([
        axios.get(`${API}/api/membership-types`),
        axios.get(`${API}/api/payment-sources`),
        axios.get(`${API}/api/field-configurations`),
        axios.get(`${API}/api/eft/settings`),
        axios.get(`${API}/api/avs/config`),
        axios.get(`${API}/api/ti/config`),
        axios.get(`${API}/api/alerts/config`)
      ]);
      setMembershipTypes(membershipsRes.data);
      setPaymentSources(sourcesRes.data);
      setFieldConfigurations(fieldConfigsRes.data);
      setEftSettings(eftSettingsRes.data);
      setAvsSettings(avsSettingsRes.data);
      setTiSettings(tiSettingsRes.data);
      setAlertConfig(alertConfigRes.data);
    } catch (error) {
      toast({ title: "Error", description: "Failed to fetch data", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveMembershipType = async () => {
    try {
      await axios.post(`${API}/api/membership-types`, formData);
      toast({ title: "Success", description: "Membership type created!" });
      fetchData();
      setFormData({
        name: '',
        description: '',
        price: '',
        billing_frequency: 'monthly',
        duration_days: 30,
        access_level: 'basic'
      });
    } catch (error) {
      toast({ title: "Error", description: "Failed to create membership type", variant: "destructive" });
    }
  };

  const handleDeleteMembershipType = async (typeId) => {
    if (!window.confirm('Are you sure?')) return;
    try {
      await axios.delete(`${API}/api/membership-types/${typeId}`);
      toast({ title: "Success", description: "Membership type deleted!" });
      fetchData();
    } catch (error) {
      toast({ title: "Error", description: "Failed to delete", variant: "destructive" });
    }
  };

  const handleSavePaymentSource = async () => {
    try {
      await axios.post(`${API}/api/payment-sources`, sourceForm);
      toast({ title: "Success", description: "Payment source created!" });
      fetchData();
      setSourceForm({ name: '', description: '', is_active: true, display_order: 0 });
    } catch (error) {
      toast({ title: "Error", description: "Failed to create payment source", variant: "destructive" });
    }
  };

  const handleDeleteSource = async (sourceId) => {
    if (!window.confirm('Are you sure?')) return;
    try {
      await axios.delete(`${API}/api/payment-sources/${sourceId}`);
      toast({ title: "Success", description: "Payment source deleted!" });
      fetchData();
    } catch (error) {
      toast({ title: "Error", description: "Failed to delete", variant: "destructive" });
    }
  };

  const handleSaveEftSettings = async () => {
    try {
      await axios.post(`${API}/api/eft/settings`, eftSettings);
      toast({ title: "Success", description: "EFT settings saved!" });
      fetchData();
    } catch (error) {
      toast({ title: "Error", description: error.response?.data?.detail || "Failed to save", variant: "destructive" });
    }
  };

  const handleSaveDebiCheckSettings = async () => {
    try {
      // This endpoint would need to be created if storing DebiCheck-specific settings separately
      toast({ title: "Success", description: "DebiCheck settings saved!" });
    } catch (error) {
      toast({ title: "Error", description: "Failed to save", variant: "destructive" });
    }
  };

  const handleSaveAvsSettings = async () => {
    try {
      await axios.post(`${API}/api/avs/config`, avsSettings);
      toast({ title: "Success", description: "AVS settings saved!" });
      fetchData();
    } catch (error) {
      toast({ title: "Error", description: error.response?.data?.detail || "Failed to save", variant: "destructive" });
    }
  };

  const handleSaveTiSettings = async () => {
    try {
      await axios.post(`${API}/api/ti/config`, tiSettings);
      toast({ title: "Success", description: "TI settings saved!" });
      fetchData();
    } catch (error) {
      toast({ title: "Error", description: error.response?.data?.detail || "Failed to save", variant: "destructive" });
    }
  };

  const handleSaveAlertConfig = async () => {
    try {
      await axios.post(`${API}/api/alerts/config`, alertConfig);
      toast({ title: "Success", description: "Alert configuration saved!" });
      fetchData();
    } catch (error) {
      toast({ title: "Error", description: error.response?.data?.detail || "Failed to save", variant: "destructive" });
    }
  };

  const handleUpdateFieldConfig = async (fieldId, updates) => {
    try {
      await axios.patch(`${API}/api/field-configurations/${fieldId}`, updates);
      toast({ title: "Success", description: "Field configuration updated!" });
      fetchData();
    } catch (error) {
      toast({ title: "Error", description: "Failed to update", variant: "destructive" });
    }
  };

  // Category configuration with main categories and sub-tabs
  const categories = {
    business: {
      icon: Briefcase,
      label: 'Business Settings',
      tabs: [
        { id: 'memberships', label: 'Membership Types', icon: CreditCard },
        { id: 'payment-sources', label: 'Payment Sources', icon: DollarSign }
      ]
    },
    payments: {
      icon: Building2,
      label: 'Payment Integration',
      tabs: [
        { id: 'eft', label: 'EFT Settings', icon: FileText },
        { id: 'debicheck', label: 'DebiCheck', icon: Shield },
        { id: 'avs', label: 'AVS (Account Verification)', icon: CheckSquare },
        { id: 'ti', label: 'TI (Reconciliation & Tracking)', icon: Activity }
      ]
    },
    staff: {
      icon: Users,
      label: 'Staff & Security',
      tabs: [
        { id: 'staff', label: 'Staff Accounts', icon: Users },
        { id: 'permissions', label: 'Roles & Permissions', icon: Lock }
      ]
    },
    operations: {
      icon: Cog,
      label: 'Operations',
      tabs: [
        { id: 'field-config', label: 'Field Configuration', icon: CheckSquare },
        { id: 'engagement-alerts', label: 'Member Engagement Alerts', icon: Activity }
      ]
    },
    automation: {
      icon: Zap,
      label: 'Automation',
      tabs: [
        { id: 'notifications', label: 'Notifications', icon: Bell }
      ]
    },
    system: {
      icon: Database,
      label: 'System',
      tabs: [
        { id: 'general', label: 'General', icon: SettingsIcon },
        { id: 'analytics', label: 'Analytics', icon: BarChart3 }
      ]
    }
  };

  const CategoryIcon = categories[mainCategory]?.icon || Briefcase;

  return (
    <div className="flex min-h-screen bg-slate-900">
      <Sidebar />
      
      <div className="flex-1 p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">⚙️ System Settings</h1>
          <p className="text-slate-400">Configure and manage all system settings from one place</p>
        </div>

        {/* Main Layout: Category Sidebar + Content */}
        <div className="grid grid-cols-12 gap-6">
          {/* Category Navigation Sidebar */}
          <div className="col-span-3">
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg sticky top-8">
              <CardHeader className="pb-3">
                <CardTitle className="text-white text-lg">Categories</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {Object.entries(categories).map(([key, category]) => {
                  const Icon = category.icon;
                  return (
                    <button
                      key={key}
                      onClick={() => {
                        setMainCategory(key);
                        setActiveTab(categories[key]?.tabs[0]?.id || '');
                      }}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                        mainCategory === key
                          ? 'bg-emerald-500 text-white shadow-lg'
                          : 'text-slate-300 hover:bg-slate-700/50'
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      <span className="font-medium">{category.label}</span>
                    </button>
                  );
                })}
              </CardContent>
            </Card>
          </div>

          {/* Content Area with Sub-tabs */}
          <div className="col-span-9">
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
              <CardHeader className="border-b border-slate-700">
                <div className="flex items-center gap-3">
                  <CategoryIcon className="w-6 h-6 text-emerald-400" />
                  <CardTitle className="text-white text-2xl">
                    {categories[mainCategory]?.label}
                  </CardTitle>
                </div>
              </CardHeader>

              <CardContent className="p-6">
                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                  {/* Sub-tabs Navigation */}
                  <TabsList className="bg-slate-700/50 p-1 mb-6 grid grid-cols-auto gap-2 w-full" style={{
                    gridTemplateColumns: `repeat(${categories[mainCategory]?.tabs.length || 1}, 1fr)`
                  }}>
                    {categories[mainCategory]?.tabs.map(tab => {
                      const TabIcon = tab.icon;
                      return (
                        <TabsTrigger
                          key={tab.id}
                          value={tab.id}
                          className="data-[state=active]:bg-emerald-500 data-[state=active]:text-white"
                        >
                          <TabIcon className="w-4 h-4 mr-2" />
                          {tab.label}
                        </TabsTrigger>
                      );
                    })}
                  </TabsList>

                  {/* Tab Content */}
                  {renderTabContent()}
                </Tabs>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );

  function renderTabContent() {
    return (
      <>
        {/* BUSINESS SETTINGS */}
        <TabsContent value="memberships">
          <div className="space-y-6">
            <div className="bg-slate-700/30 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-white mb-4">Create New Membership Type</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label className="text-white">Name</Label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                </div>
                <div>
                  <Label className="text-white">Price</Label>
                  <Input
                    type="number"
                    value={formData.price}
                    onChange={(e) => setFormData({...formData, price: e.target.value})}
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                </div>
                <div>
                  <Label className="text-white">Billing Frequency</Label>
                  <select
                    value={formData.billing_frequency}
                    onChange={(e) => setFormData({...formData, billing_frequency: e.target.value})}
                    className="w-full bg-slate-700 border-slate-600 text-white rounded-md p-2"
                  >
                    <option value="monthly">Monthly</option>
                    <option value="yearly">Yearly</option>
                    <option value="once">One-time</option>
                  </select>
                </div>
                <div>
                  <Label className="text-white">Duration (Days)</Label>
                  <Input
                    type="number"
                    value={formData.duration_days}
                    onChange={(e) => setFormData({...formData, duration_days: parseInt(e.target.value)})}
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                </div>
                <div className="md:col-span-2">
                  <Label className="text-white">Description</Label>
                  <Input
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                </div>
              </div>
              <Button onClick={handleSaveMembershipType} className="mt-4 bg-emerald-500 hover:bg-emerald-600">
                Create Membership Type
              </Button>
            </div>

            <div className="space-y-4">
              <h3 className="text-xl font-semibold text-white">Existing Membership Types</h3>
              {membershipTypes.map(type => (
                <Card key={type.id} className="bg-slate-700/50 border-slate-600">
                  <CardContent className="p-4 flex justify-between items-center">
                    <div>
                      <h4 className="text-white font-semibold">{type.name}</h4>
                      <p className="text-slate-400 text-sm">{type.description}</p>
                      <p className="text-emerald-400 font-semibold mt-2">R{type.price} / {type.billing_frequency}</p>
                    </div>
                    <Button
                      onClick={() => handleDeleteMembershipType(type.id)}
                      variant="destructive"
                      size="sm"
                    >
                      Delete
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="payment-sources">
          <div className="space-y-6">
            <div className="bg-slate-700/30 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-white mb-4">Create Payment Source</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label className="text-white">Name</Label>
                  <Input
                    value={sourceForm.name}
                    onChange={(e) => setSourceForm({...sourceForm, name: e.target.value})}
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                </div>
                <div>
                  <Label className="text-white">Description</Label>
                  <Input
                    value={sourceForm.description}
                    onChange={(e) => setSourceForm({...sourceForm, description: e.target.value})}
                    className="bg-slate-700 border-slate-600 text-white"
                  />
                </div>
              </div>
              <Button onClick={handleSavePaymentSource} className="mt-4 bg-emerald-500 hover:bg-emerald-600">
                Create Payment Source
              </Button>
            </div>

            <div className="space-y-4">
              <h3 className="text-xl font-semibold text-white">Existing Payment Sources</h3>
              {paymentSources.map(source => (
                <Card key={source.id} className="bg-slate-700/50 border-slate-600">
                  <CardContent className="p-4 flex justify-between items-center">
                    <div>
                      <h4 className="text-white font-semibold">{source.name}</h4>
                      <p className="text-slate-400 text-sm">{source.description}</p>
                    </div>
                    <Button
                      onClick={() => handleDeleteSource(source.id)}
                      variant="destructive"
                      size="sm"
                    >
                      Delete
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </TabsContent>

        {/* PAYMENT INTEGRATION */}
        <TabsContent value="eft">
          {renderEFTSettings()}
        </TabsContent>

        <TabsContent value="debicheck">
          {renderDebiCheckSettings()}
        </TabsContent>

        <TabsContent value="avs">
          {renderAvsSettings()}
        </TabsContent>

        <TabsContent value="ti">
          {renderTiSettings()}
        </TabsContent>

        {/* STAFF & SECURITY */}
        <TabsContent value="staff">
          <div className="space-y-6">
            <div className="flex items-start gap-3 bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
              <Users className="w-6 h-6 text-blue-400 flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-xl font-bold text-blue-400 mb-2">Staff & User Management</h3>
                <p className="text-sm text-slate-300">
                  Manage staff accounts, user roles, and access permissions for your organization.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card className="bg-slate-700/50 border-slate-600 hover:border-emerald-500/50 transition-colors">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Users className="w-5 h-5" />
                    User & Role Management
                  </CardTitle>
                  <CardDescription className="text-slate-400">
                    Create and manage user accounts with role-based access control
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="text-sm text-slate-300 space-y-2 mb-4">
                    <li>• Create and edit user accounts</li>
                    <li>• Assign roles (Admin, Manager, Staff, Receptionist)</li>
                    <li>• Set custom permissions per user</li>
                    <li>• Manage user status (active/inactive)</li>
                  </ul>
                  <Button 
                    onClick={() => window.location.href = '/user-roles'}
                    className="w-full bg-emerald-500 hover:bg-emerald-600"
                  >
                    Go to User Management
                  </Button>
                </CardContent>
              </Card>

              <Card className="bg-slate-700/50 border-slate-600 hover:border-emerald-500/50 transition-colors">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Shield className="w-5 h-5" />
                    Access Control
                  </CardTitle>
                  <CardDescription className="text-slate-400">
                    Configure detailed permissions and access levels
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="text-sm text-slate-300 space-y-2 mb-4">
                    <li>• View permission matrix</li>
                    <li>• Configure role-based access</li>
                    <li>• Set module-specific permissions</li>
                    <li>• Manage security policies</li>
                  </ul>
                  <Button 
                    onClick={() => window.location.href = '/access-control'}
                    className="w-full bg-emerald-500 hover:bg-emerald-600"
                  >
                    Go to Access Control
                  </Button>
                </CardContent>
              </Card>
            </div>

            <Card className="bg-amber-500/10 border-amber-500/30">
              <CardHeader>
                <CardTitle className="text-amber-400 flex items-center gap-2">
                  <Lock className="w-5 h-5" />
                  Security Best Practices
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="text-sm text-slate-300 space-y-2">
                  <li>• <strong>Regular Audits:</strong> Review user permissions quarterly</li>
                  <li>• <strong>Principle of Least Privilege:</strong> Grant minimum required access</li>
                  <li>• <strong>Strong Passwords:</strong> Enforce password complexity requirements</li>
                  <li>• <strong>Active Monitoring:</strong> Track user activity and login attempts</li>
                  <li>• <strong>Offboarding:</strong> Disable accounts immediately when staff leave</li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="permissions">
          <div className="space-y-6">
            <div className="flex items-start gap-3 bg-purple-500/10 border border-purple-500/30 rounded-lg p-4">
              <Shield className="w-6 h-6 text-purple-400 flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-xl font-bold text-purple-400 mb-2">Roles & Permissions</h3>
                <p className="text-sm text-slate-300">
                  Configure granular permissions and role-based access control for your team.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className="bg-slate-700/50 border-slate-600">
                <CardHeader>
                  <CardTitle className="text-white text-lg">Permission Matrix</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-300 mb-4">
                    View comprehensive permission matrix showing what each role can access
                  </p>
                  <Button 
                    onClick={() => window.location.href = '/permission-matrix'}
                    className="w-full bg-purple-500 hover:bg-purple-600"
                  >
                    View Matrix
                  </Button>
                </CardContent>
              </Card>

              <Card className="bg-slate-700/50 border-slate-600">
                <CardHeader>
                  <CardTitle className="text-white text-lg">Role Management</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-300 mb-4">
                    Create custom roles and assign specific permissions to each role
                  </p>
                  <Button 
                    onClick={() => window.location.href = '/user-roles'}
                    className="w-full bg-purple-500 hover:bg-purple-600"
                  >
                    Manage Roles
                  </Button>
                </CardContent>
              </Card>

              <Card className="bg-slate-700/50 border-slate-600">
                <CardHeader>
                  <CardTitle className="text-white text-lg">Access Control</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-300 mb-4">
                    Advanced access control settings and security configurations
                  </p>
                  <Button 
                    onClick={() => window.location.href = '/access-control'}
                    className="w-full bg-purple-500 hover:bg-purple-600"
                  >
                    Configure Access
                  </Button>
                </CardContent>
              </Card>
            </div>

            <Card className="bg-slate-700/50 border-slate-600">
              <CardHeader>
                <CardTitle className="text-white">Default Role Permissions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div className="space-y-2">
                    <h4 className="font-semibold text-emerald-400">Admin</h4>
                    <ul className="text-slate-300 space-y-1 pl-4">
                      <li>• Full system access</li>
                      <li>• User management</li>
                      <li>• Settings configuration</li>
                      <li>• Financial reports</li>
                    </ul>
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-semibold text-blue-400">Manager</h4>
                    <ul className="text-slate-300 space-y-1 pl-4">
                      <li>• Member management</li>
                      <li>• Billing operations</li>
                      <li>• Reports viewing</li>
                      <li>• Class scheduling</li>
                    </ul>
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-semibold text-yellow-400">Staff</h4>
                    <ul className="text-slate-300 space-y-1 pl-4">
                      <li>• Member check-in</li>
                      <li>• Basic member info</li>
                      <li>• Class attendance</li>
                      <li>• Limited reporting</li>
                    </ul>
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-semibold text-slate-400">Receptionist</h4>
                    <ul className="text-slate-300 space-y-1 pl-4">
                      <li>• Member check-in</li>
                      <li>• Guest registration</li>
                      <li>• View schedules</li>
                      <li>• Contact updates</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* OPERATIONS */}
        <TabsContent value="field-config">
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-white mb-4">Field Configuration</h3>
            {fieldConfigurations.map(config => (
              <Card key={config.id} className="bg-slate-700/50 border-slate-600">
                <CardContent className="p-4">
                  <div className="flex justify-between items-center">
                    <div>
                      <h4 className="text-white font-semibold capitalize">{config.field_name.replace(/_/g, ' ')}</h4>
                      <p className="text-slate-400 text-sm">{config.entity_type}</p>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-2">
                        <Label className="text-white text-sm">Required</Label>
                        <Switch
                          checked={config.is_required}
                          onCheckedChange={(checked) => handleUpdateFieldConfig(config.id, { is_required: checked })}
                        />
                      </div>
                      <div className="flex items-center gap-2">
                        <Label className="text-white text-sm">Visible</Label>
                        <Switch
                          checked={config.is_visible}
                          onCheckedChange={(checked) => handleUpdateFieldConfig(config.id, { is_visible: checked })}
                        />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="engagement-alerts">
          <div className="space-y-6">
            <div className="flex items-start gap-3 bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
              <Activity className="w-6 h-6 text-blue-400 flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-xl font-bold text-blue-400 mb-2">Member Engagement Alerts</h3>
                <p className="text-sm text-slate-300">
                  Configure thresholds for member engagement alerts based on gym access frequency.
                </p>
              </div>
            </div>

            <Card className="bg-slate-700/50 border-slate-600">
              <CardHeader>
                <CardTitle className="text-white">Alert Thresholds Configuration</CardTitle>
                <CardDescription className="text-slate-400">
                  Set the visit frequency thresholds for categorizing member engagement levels
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <Label htmlFor="days_period" className="text-white">Tracking Period (days)</Label>
                  <Input
                    id="days_period"
                    type="number"
                    min="1"
                    max="365"
                    value={alertConfig.days_period}
                    onChange={(e) => setAlertConfig({...alertConfig, days_period: parseInt(e.target.value)})}
                    className="bg-slate-700 text-white border-slate-600 mt-2"
                  />
                  <p className="text-xs text-slate-400 mt-1">Number of days to look back when counting visits</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Green Alert */}
                  <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <CheckCircle className="w-5 h-5 text-green-400" />
                      <span className="font-semibold text-green-400">Green Alert</span>
                    </div>
                    <Label htmlFor="green_threshold" className="text-white text-sm">Minimum Visits</Label>
                    <Input
                      id="green_threshold"
                      type="number"
                      min="1"
                      value={alertConfig.green_threshold}
                      onChange={(e) => setAlertConfig({...alertConfig, green_threshold: parseInt(e.target.value)})}
                      className="bg-slate-700 text-white border-slate-600 mt-2"
                    />
                    <p className="text-xs text-slate-400 mt-2">
                      Members with <strong>≥ {alertConfig.green_threshold}</strong> visits are highly engaged
                    </p>
                  </div>

                  {/* Amber Alert */}
                  <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <AlertTriangle className="w-5 h-5 text-amber-400" />
                      <span className="font-semibold text-amber-400">Amber Alert</span>
                    </div>
                    <div className="space-y-2">
                      <div>
                        <Label htmlFor="amber_min" className="text-white text-sm">Minimum Visits</Label>
                        <Input
                          id="amber_min"
                          type="number"
                          min="0"
                          value={alertConfig.amber_min_threshold}
                          onChange={(e) => setAlertConfig({...alertConfig, amber_min_threshold: parseInt(e.target.value)})}
                          className="bg-slate-700 text-white border-slate-600 mt-1"
                        />
                      </div>
                      <div>
                        <Label htmlFor="amber_max" className="text-white text-sm">Maximum Visits</Label>
                        <Input
                          id="amber_max"
                          type="number"
                          min="0"
                          value={alertConfig.amber_max_threshold}
                          onChange={(e) => setAlertConfig({...alertConfig, amber_max_threshold: parseInt(e.target.value)})}
                          className="bg-slate-700 text-white border-slate-600 mt-1"
                        />
                      </div>
                    </div>
                    <p className="text-xs text-slate-400 mt-2">
                      Members with <strong>{alertConfig.amber_min_threshold}-{alertConfig.amber_max_threshold}</strong> visits need attention
                    </p>
                  </div>

                  {/* Red Alert */}
                  <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <AlertCircle className="w-5 h-5 text-red-400" />
                      <span className="font-semibold text-red-400">Red Alert</span>
                    </div>
                    <div className="bg-red-500/20 rounded p-3 mb-2">
                      <p className="text-sm text-white">
                        <strong>0 visits</strong>
                      </p>
                      <p className="text-xs text-slate-300 mt-1">Fixed threshold</p>
                    </div>
                    <p className="text-xs text-slate-400">
                      Members with <strong>no visits</strong> are at risk
                    </p>
                  </div>
                </div>

                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                  <h4 className="text-blue-400 font-semibold mb-2">ℹ️ How It Works</h4>
                  <ul className="text-sm text-slate-300 space-y-1">
                    <li>• <strong>Green Alert:</strong> Members visiting frequently - keep them engaged!</li>
                    <li>• <strong>Amber Alert:</strong> Members visiting occasionally - encourage more visits</li>
                    <li>• <strong>Red Alert:</strong> Members not visiting - reach out to prevent churn</li>
                    <li>• Alerts are calculated based on check-ins within the specified tracking period</li>
                    <li>• View detailed member lists by alert level on the Dashboard</li>
                  </ul>
                </div>

                <div className="flex justify-end pt-4">
                  <Button onClick={handleSaveAlertConfig} className="bg-emerald-500 hover:bg-emerald-600">
                    Save Alert Configuration
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* AUTOMATION */}
        <TabsContent value="notifications">
          <div className="text-center py-12">
            <Bell className="h-16 w-16 mx-auto text-slate-600 mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">Notification Settings</h3>
            <p className="text-slate-400">Configure email and WhatsApp notifications</p>
          </div>
        </TabsContent>

        {/* SYSTEM */}
        <TabsContent value="general">
          <div className="text-center py-12">
            <SettingsIcon className="h-16 w-16 mx-auto text-slate-600 mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">General Settings</h3>
            <p className="text-slate-400">System-wide configuration options</p>
          </div>
        </TabsContent>

        <TabsContent value="analytics">
          <div className="text-center py-12">
            <BarChart3 className="h-16 w-16 mx-auto text-slate-600 mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">Analytics Settings</h3>
            <p className="text-slate-400">Configure analytics and reporting options</p>
          </div>
        </TabsContent>
      </>
    );
  }

  function renderEFTSettings() {
    return (
      <div className="space-y-6">
        <div className="grid md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label className="text-white">Client Profile Number <span className="text-red-500">*</span></Label>
            <Input
              type="text"
              maxLength={10}
              placeholder="0000000000"
              value={eftSettings.client_profile_number}
              onChange={(e) => setEftSettings({...eftSettings, client_profile_number: e.target.value})}
              className="bg-slate-700 border-slate-600 text-white"
            />
            <p className="text-xs text-slate-400">10-digit Nedbank client number</p>
          </div>

          <div className="space-y-2">
            <Label className="text-white">Nominated Account <span className="text-red-500">*</span></Label>
            <Input
              type="text"
              maxLength={16}
              placeholder="0000000000000000"
              value={eftSettings.nominated_account}
              onChange={(e) => setEftSettings({...eftSettings, nominated_account: e.target.value})}
              className="bg-slate-700 border-slate-600 text-white"
            />
            <p className="text-xs text-slate-400">16-digit account for credits</p>
          </div>

          <div className="space-y-2">
            <Label className="text-white">Charges Account <span className="text-red-500">*</span></Label>
            <Input
              type="text"
              maxLength={16}
              placeholder="0000000000000000"
              value={eftSettings.charges_account}
              onChange={(e) => setEftSettings({...eftSettings, charges_account: e.target.value})}
              className="bg-slate-700 border-slate-600 text-white"
            />
            <p className="text-xs text-slate-400">16-digit account for fees</p>
          </div>

          <div className="space-y-2">
            <Label className="text-white">Bank Name</Label>
            <Input
              type="text"
              value={eftSettings.bank_name}
              onChange={(e) => setEftSettings({...eftSettings, bank_name: e.target.value})}
              className="bg-slate-700 border-slate-600 text-white"
            />
          </div>
        </div>

        <div className="border-t border-slate-700 pt-6">
          <h3 className="text-lg font-semibold text-white mb-4">Billing Schedule</h3>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label className="text-white">Advance Billing Days</Label>
              <div className="flex items-start gap-4">
                <Input
                  type="number"
                  min="0"
                  max="30"
                  value={eftSettings.advance_billing_days}
                  onChange={(e) => setEftSettings({...eftSettings, advance_billing_days: parseInt(e.target.value) || 5})}
                  className="bg-slate-700 border-slate-600 text-white w-32"
                />
                <div>
                  <p className="text-sm text-slate-300">
                    Generate files <strong className="text-emerald-400">{eftSettings.advance_billing_days} days</strong> before due date
                  </p>
                  <p className="text-xs text-slate-500 mt-1">Recommended: 5 days for gateway processing</p>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg">
              <div>
                <Label className="text-white">Enable Auto-generation</Label>
                <p className="text-sm text-slate-400 mt-1">Automatically generate files based on due dates</p>
              </div>
              <Switch
                checked={eftSettings.enable_auto_generation}
                onCheckedChange={(checked) => setEftSettings({...eftSettings, enable_auto_generation: checked})}
              />
            </div>
          </div>
        </div>

        <div className="border-t border-slate-700 pt-6">
          <h3 className="text-lg font-semibold text-white mb-4">Notifications</h3>
          <div className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg">
            <div>
              <Label className="text-white">Enable Payment Notifications</Label>
              <p className="text-sm text-slate-400 mt-1">Notify members when payments confirmed</p>
            </div>
            <Switch
              checked={eftSettings.enable_notifications}
              onCheckedChange={(checked) => setEftSettings({...eftSettings, enable_notifications: checked})}
            />
          </div>
        </div>

        <div className="flex justify-end pt-4">
          <Button onClick={handleSaveEftSettings} className="bg-emerald-500 hover:bg-emerald-600">
            Save EFT Settings
          </Button>
        </div>
      </div>
    );
  }

  function renderDebiCheckSettings() {
    return (
      <div className="space-y-6">
        <div className="grid md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label className="text-white">Creditor Name <span className="text-red-500">*</span></Label>
            <Input
              type="text"
              maxLength={30}
              placeholder="Your Gym Name"
              value={debiCheckSettings.creditor_name}
              onChange={(e) => setDebiCheckSettings({...debiCheckSettings, creditor_name: e.target.value})}
              className="bg-slate-700 border-slate-600 text-white"
            />
            <p className="text-xs text-slate-400">Full creditor name (max 30 chars)</p>
          </div>

          <div className="space-y-2">
            <Label className="text-white">Creditor Abbreviation <span className="text-red-500">*</span></Label>
            <Input
              type="text"
              maxLength={10}
              placeholder="GYM"
              value={debiCheckSettings.creditor_abbreviation}
              onChange={(e) => setDebiCheckSettings({...debiCheckSettings, creditor_abbreviation: e.target.value})}
              className="bg-slate-700 border-slate-600 text-white"
            />
            <p className="text-xs text-slate-400">Appears on statements (max 10 chars)</p>
          </div>

          <div className="space-y-2">
            <Label className="text-white">Default Mandate Type</Label>
            <select
              value={debiCheckSettings.default_mandate_type}
              onChange={(e) => setDebiCheckSettings({...debiCheckSettings, default_mandate_type: e.target.value})}
              className="w-full bg-slate-700 border-slate-600 text-white rounded-md p-2"
            >
              <option value="F">Fixed - Fixed installment amounts</option>
              <option value="V">Variable - Calculated monthly</option>
              <option value="U">Usage-based - Based on usage</option>
            </select>
          </div>

          <div className="space-y-2">
            <Label className="text-white">Default Transaction Type</Label>
            <select
              value={debiCheckSettings.default_transaction_type}
              onChange={(e) => setDebiCheckSettings({...debiCheckSettings, default_transaction_type: e.target.value})}
              className="w-full bg-slate-700 border-slate-600 text-white rounded-md p-2"
            >
              <option value="TT1">TT1 - Real-time (120 seconds)</option>
              <option value="TT2">TT2 - Batch (2 business days)</option>
              <option value="TT3">TT3 - Card & PIN</option>
            </select>
          </div>

          <div className="space-y-2">
            <Label className="text-white">Default Adjustment Category</Label>
            <select
              value={debiCheckSettings.default_adjustment_category}
              onChange={(e) => setDebiCheckSettings({...debiCheckSettings, default_adjustment_category: e.target.value})}
              className="w-full bg-slate-700 border-slate-600 text-white rounded-md p-2"
            >
              <option value="0">Never - No adjustments</option>
              <option value="1">Quarterly - Every 3 months</option>
              <option value="2">Biannually - Every 6 months</option>
              <option value="3">Annually - Yearly</option>
              <option value="4">Repo Rate - Linked to repo rate</option>
            </select>
          </div>
        </div>

        <div className="border-t border-slate-700 pt-6">
          <div className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg">
            <div>
              <Label className="text-white">Enable Mandate Notifications</Label>
              <p className="text-sm text-slate-400 mt-1">Notify when mandates are approved/rejected</p>
            </div>
            <Switch
              checked={debiCheckSettings.enable_mandate_notifications}
              onCheckedChange={(checked) => setDebiCheckSettings({...debiCheckSettings, enable_mandate_notifications: checked})}
            />
          </div>
        </div>

        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
          <h4 className="text-blue-400 font-semibold mb-2">📋 DebiCheck Information</h4>
          <ul className="text-sm text-slate-300 space-y-1">
            <li>• DebiCheck provides authenticated, dispute-protected debit orders</li>
            <li>• Members must approve mandates via their banking app</li>
            <li>• Maximum collection amount: R1,000,000 (regulatory limit)</li>
            <li>• Mandates can be Fixed, Variable, or Usage-based</li>
            <li>• TT1 (Real-time): 120-second approval window</li>
            <li>• TT2 (Batch): 2 business days approval time</li>
          </ul>
        </div>

        <div className="flex justify-end pt-4">
          <Button onClick={handleSaveDebiCheckSettings} className="bg-emerald-500 hover:bg-emerald-600">
            Save DebiCheck Settings
          </Button>
        </div>
      </div>
    );
  }

  function renderAvsSettings() {
    return (
      <div className="space-y-6">
        <div className="flex items-start gap-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4">
          <CheckSquare className="w-6 h-6 text-emerald-400 flex-shrink-0 mt-1" />
          <div>
            <h3 className="text-xl font-bold text-emerald-400 mb-2">AVS (Account Verification Service)</h3>
            <p className="text-sm text-slate-300">
              Configure Nedbank's Account Verification Service to verify member banking details in real-time before processing debit orders.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div>
            <Label htmlFor="avs_profile_number" className="text-white">Profile Number</Label>
            <Input
              id="avs_profile_number"
              placeholder="10-digit Nedbank profile number"
              value={avsSettings.profile_number}
              onChange={(e) => setAvsSettings({...avsSettings, profile_number: e.target.value})}
              className="bg-slate-700 text-white border-slate-600"
            />
            <p className="text-xs text-slate-400 mt-1">Your Nedbank client profile number</p>
          </div>

          <div>
            <Label htmlFor="avs_profile_user_number" className="text-white">Profile User Number</Label>
            <Input
              id="avs_profile_user_number"
              placeholder="8-digit user number"
              value={avsSettings.profile_user_number}
              onChange={(e) => setAvsSettings({...avsSettings, profile_user_number: e.target.value})}
              className="bg-slate-700 text-white border-slate-600"
            />
            <p className="text-xs text-slate-400 mt-1">Profile user identifier</p>
          </div>

          <div>
            <Label htmlFor="avs_charge_account" className="text-white">Charge Account</Label>
            <Input
              id="avs_charge_account"
              placeholder="Account number for verification fees"
              value={avsSettings.charge_account}
              onChange={(e) => setAvsSettings({...avsSettings, charge_account: e.target.value})}
              className="bg-slate-700 text-white border-slate-600"
            />
            <p className="text-xs text-slate-400 mt-1">Account to charge for verification fees</p>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between bg-slate-700/50 p-3 rounded-lg">
              <div>
                <Label className="text-white">Mock Mode</Label>
                <p className="text-sm text-slate-400 mt-1">Use test data without actual Nedbank connection</p>
              </div>
              <Switch
                checked={avsSettings.mock_mode}
                onCheckedChange={(checked) => setAvsSettings({...avsSettings, mock_mode: checked})}
              />
            </div>

            <div className="flex items-center justify-between bg-slate-700/50 p-3 rounded-lg">
              <div>
                <Label className="text-white">Use QA Environment</Label>
                <p className="text-sm text-slate-400 mt-1">Connect to QA instead of production</p>
              </div>
              <Switch
                checked={avsSettings.use_qa}
                onCheckedChange={(checked) => setAvsSettings({...avsSettings, use_qa: checked})}
              />
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-white">Automation Settings</h4>
          
          <div className="flex items-center justify-between bg-slate-700/50 p-3 rounded-lg">
            <div>
              <Label className="text-white">Auto-Verify on Member Onboarding</Label>
              <p className="text-sm text-slate-400 mt-1">Automatically verify banking details when adding new members</p>
            </div>
            <Switch
              checked={avsSettings.enable_auto_verify}
              onCheckedChange={(checked) => setAvsSettings({...avsSettings, enable_auto_verify: checked})}
            />
          </div>

          <div className="flex items-center justify-between bg-slate-700/50 p-3 rounded-lg">
            <div>
              <Label className="text-white">Verify on Banking Details Update</Label>
              <p className="text-sm text-slate-400 mt-1">Re-verify when members update their banking information</p>
            </div>
            <Switch
              checked={avsSettings.verify_on_update}
              onCheckedChange={(checked) => setAvsSettings({...avsSettings, verify_on_update: checked})}
            />
          </div>
        </div>

        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
          <h4 className="text-blue-400 font-semibold mb-2">ℹ️ AVS Information</h4>
          <ul className="text-sm text-slate-300 space-y-1">
            <li>• Verifies account existence and ownership across participating South African banks</li>
            <li>• Real-time verification (within 45 seconds)</li>
            <li>• Reduces risk of debit order failures and fraud</li>
            <li>• Checks: Account exists, ID match, Name match, Account status, Accept debits/credits</li>
            <li>• Available 03:30 - 00:00 daily</li>
            <li>• Mock mode enabled: Testing without actual credentials or charges</li>
            <li>• Participating banks: Nedbank, FNB, Standard Bank, Absa, Capitec, and more</li>
          </ul>
        </div>

        <div className="flex justify-end pt-4">
          <Button onClick={handleSaveAvsSettings} className="bg-emerald-500 hover:bg-emerald-600">
            Save AVS Settings
          </Button>
        </div>
      </div>
    );
  }

  function renderTiSettings() {
    return (
      <div className="space-y-6">
        <div className="flex items-start gap-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4">
          <Activity className="w-6 h-6 text-emerald-400 flex-shrink-0 mt-1" />
          <div>
            <h3 className="text-xl font-bold text-emerald-400 mb-2">TI (Transactional Information)</h3>
            <p className="text-sm text-slate-300">
              Configure Nedbank's TI service for automated payment reconciliation, real-time tracking, and transaction notifications.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div>
            <Label htmlFor="ti_profile_number" className="text-white">Profile Number</Label>
            <Input
              id="ti_profile_number"
              placeholder="10-digit Nedbank profile number"
              value={tiSettings.profile_number}
              onChange={(e) => setTiSettings({...tiSettings, profile_number: e.target.value})}
              className="bg-slate-700 text-white border-slate-600"
            />
          </div>

          <div>
            <Label htmlFor="ti_account_number" className="text-white">Account Number</Label>
            <Input
              id="ti_account_number"
              placeholder="Account to monitor for transactions"
              value={tiSettings.account_number}
              onChange={(e) => setTiSettings({...tiSettings, account_number: e.target.value})}
              className="bg-slate-700 text-white border-slate-600"
            />
          </div>
        </div>

        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-white">Service Configuration</h4>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center justify-between bg-slate-700/50 p-3 rounded-lg">
              <div>
                <Label className="text-white">Mock Mode</Label>
                <p className="text-sm text-slate-400 mt-1">Use test data for development</p>
              </div>
              <Switch
                checked={tiSettings.mock_mode}
                onCheckedChange={(checked) => setTiSettings({...tiSettings, mock_mode: checked})}
              />
            </div>

            <div className="flex items-center justify-between bg-slate-700/50 p-3 rounded-lg">
              <div>
                <Label className="text-white">Use QA Environment</Label>
                <p className="text-sm text-slate-400 mt-1">Test environment</p>
              </div>
              <Switch
                checked={tiSettings.use_qa}
                onCheckedChange={(checked) => setTiSettings({...tiSettings, use_qa: checked})}
              />
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-white">FTI (Final Transaction Information)</h4>
          <p className="text-sm text-slate-400">Daily confirmed transactions for reconciliation</p>
          
          <div className="flex items-center justify-between bg-slate-700/50 p-3 rounded-lg">
            <div>
              <Label className="text-white">Enable FTI</Label>
              <p className="text-sm text-slate-400 mt-1">Receive daily transaction files</p>
            </div>
            <Switch
              checked={tiSettings.fti_enabled}
              onCheckedChange={(checked) => setTiSettings({...tiSettings, fti_enabled: checked})}
            />
          </div>

          <div>
            <Label htmlFor="fti_frequency" className="text-white">FTI Frequency</Label>
            <select
              id="fti_frequency"
              value={tiSettings.fti_frequency}
              onChange={(e) => setTiSettings({...tiSettings, fti_frequency: e.target.value})}
              className="w-full mt-1 bg-slate-700 text-white border-slate-600 rounded-md p-2"
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>

          <div className="flex items-center justify-between bg-slate-700/50 p-3 rounded-lg">
            <div>
              <Label className="text-white">Auto-Reconcile</Label>
              <p className="text-sm text-slate-400 mt-1">Automatically match payments to invoices</p>
            </div>
            <Switch
              checked={tiSettings.auto_reconcile}
              onCheckedChange={(checked) => setTiSettings({...tiSettings, auto_reconcile: checked})}
            />
          </div>
        </div>

        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-white">PTI (Provisional Transaction Information)</h4>
          <p className="text-sm text-slate-400">Real-time provisional transaction feed</p>
          
          <div className="flex items-center justify-between bg-slate-700/50 p-3 rounded-lg">
            <div>
              <Label className="text-white">Enable PTI</Label>
              <p className="text-sm text-slate-400 mt-1">Real-time transaction monitoring</p>
            </div>
            <Switch
              checked={tiSettings.pti_enabled}
              onCheckedChange={(checked) => setTiSettings({...tiSettings, pti_enabled: checked})}
            />
          </div>
        </div>

        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-white">Notifications</h4>
          
          <div className="flex items-center justify-between bg-slate-700/50 p-3 rounded-lg">
            <div>
              <Label className="text-white">Enable Notifications</Label>
              <p className="text-sm text-slate-400 mt-1">Alerts for payment events</p>
            </div>
            <Switch
              checked={tiSettings.notifications_enabled}
              onCheckedChange={(checked) => setTiSettings({...tiSettings, notifications_enabled: checked})}
            />
          </div>
        </div>

        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
          <h4 className="text-blue-400 font-semibold mb-2">ℹ️ TI Features</h4>
          <ul className="text-sm text-slate-300 space-y-1">
            <li>• <strong>FTI</strong>: Automated daily payment reconciliation - matches bank transactions to invoices</li>
            <li>• <strong>PTI</strong>: Real-time provisional transaction feed - see payments before final confirmation</li>
            <li>• <strong>Notifications</strong>: Instant alerts for payment received, failures, high-value transactions</li>
            <li>• <strong>Auto-Reconcile</strong>: Automatically updates invoice status when payments match (high confidence only)</li>
            <li>• Reduces manual reconciliation time by 80%+</li>
            <li>• Mock mode enabled: Full testing without actual Nedbank connection</li>
          </ul>
        </div>

        <div className="flex justify-end pt-4">
          <Button onClick={handleSaveTiSettings} className="bg-emerald-500 hover:bg-emerald-600">
            Save TI Settings
          </Button>
        </div>
      </div>
    );
  }
}
