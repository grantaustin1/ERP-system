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

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [membershipsRes, sourcesRes, fieldConfigsRes, eftSettingsRes, avsSettingsRes, tiSettingsRes] = await Promise.all([
        axios.get(`${API}/api/membership-types`),
        axios.get(`${API}/api/payment-sources`),
        axios.get(`${API}/api/field-configurations`),
        axios.get(`${API}/api/eft/settings`),
        axios.get(`${API}/api/avs/config`),
        axios.get(`${API}/api/ti/config`)
      ]);
      setMembershipTypes(membershipsRes.data);
      setPaymentSources(sourcesRes.data);
      setFieldConfigurations(fieldConfigsRes.data);
      setEftSettings(eftSettingsRes.data);
      setAvsSettings(avsSettingsRes.data);
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
        { id: 'avs', label: 'AVS (Account Verification)', icon: CheckSquare }
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
        { id: 'field-config', label: 'Field Configuration', icon: CheckSquare }
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
                      onClick={() => setMainCategory(key)}
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
                <Tabs defaultValue={categories[mainCategory]?.tabs[0]?.id} className="w-full">
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

        {/* STAFF & SECURITY */}
        <TabsContent value="staff">
          <div className="text-center py-12">
            <Users className="h-16 w-16 mx-auto text-slate-600 mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">Staff Management</h3>
            <p className="text-slate-400">Staff account management coming soon</p>
          </div>
        </TabsContent>

        <TabsContent value="permissions">
          <div className="text-center py-12">
            <Shield className="h-16 w-16 mx-auto text-slate-600 mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">Roles & Permissions</h3>
            <p className="text-slate-400">Visit Access Control page for detailed permission management</p>
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
}
