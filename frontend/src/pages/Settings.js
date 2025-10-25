import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Package, Users, Shield, Plus, Edit, Tag, Trash2, Settings as SettingsIcon, CheckSquare } from 'lucide-react';
import { toast } from 'sonner';

export default function Settings() {
  const [membershipTypes, setMembershipTypes] = useState([]);
  const [paymentSources, setPaymentSources] = useState([]);
  const [fieldConfigurations, setFieldConfigurations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [membershipDialogOpen, setMembershipDialogOpen] = useState(false);
  const [staffDialogOpen, setStaffDialogOpen] = useState(false);
  const [sourceDialogOpen, setSourceDialogOpen] = useState(false);
  const [editingSource, setEditingSource] = useState(null);
  
  const [membershipForm, setMembershipForm] = useState({
    name: '',
    description: '',
    price: '',
    billing_frequency: 'monthly',
    duration_months: 1,
    payment_type: 'debit_order',
    rollover_enabled: false,
    levy_enabled: false,
    levy_frequency: 'annual',
    levy_timing: 'anniversary',
    levy_amount_type: 'fixed',
    levy_amount: '',
    levy_payment_method: 'debit_order',
    features: '',
    peak_hours_only: false,
    multi_site_access: false
  });

  const [staffForm, setStaffForm] = useState({
    email: '',
    password: '',
    full_name: '',
    role: 'staff'
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

  const [appSettings, setAppSettings] = useState({
    member_portal_enabled: true,
    member_portal_require_active_status: true,
    enable_email_notifications: true,
    enable_sms_notifications: true,
    enable_whatsapp_notifications: false,
    enable_inapp_notifications: true
  });


  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [membershipsRes, sourcesRes, fieldConfigsRes, eftSettingsRes, appSettingsRes] = await Promise.all([
        axios.get(`${API}/membership-types`),
        axios.get(`${API}/payment-sources`),
        axios.get(`${API}/field-configurations`),
        axios.get(`${API}/eft/settings`),
        axios.get(`${API}/settings/app`)
      ]);
      setMembershipTypes(membershipsRes.data);
      setPaymentSources(sourcesRes.data);
      setFieldConfigurations(fieldConfigsRes.data);
      setEftSettings(eftSettingsRes.data);
      setAppSettings(appSettingsRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleFieldConfigUpdate = async (fieldName, updates) => {
    try {
      await axios.put(`${API}/field-configurations/${fieldName}`, updates);
      toast.success('Field configuration updated!');
      fetchData();
    } catch (error) {
      toast.error('Failed to update field configuration');
    }
  };

  const handleResetFieldConfigs = async () => {
    try {
      await axios.post(`${API}/field-configurations/reset-defaults`);
      toast.success('Field configurations reset to defaults!');
      fetchData();
    } catch (error) {
      toast.error('Failed to reset configurations');
    }
  };

  const handleMembershipSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        ...membershipForm,
        price: parseFloat(membershipForm.price),
        levy_amount: membershipForm.levy_amount ? parseFloat(membershipForm.levy_amount) : 0,
        features: membershipForm.features.split('\n').filter(f => f.trim())
      };

      await axios.post(`${API}/membership-types`, data);
      toast.success('Membership type created!');

      setMembershipDialogOpen(false);
      setMembershipForm({
        name: '',
        description: '',
        price: '',
        billing_frequency: 'monthly',
        duration_months: 1,
        payment_type: 'debit_order',
        rollover_enabled: false,
        levy_enabled: false,
        levy_frequency: 'annual',
        levy_timing: 'anniversary',
        levy_amount_type: 'fixed',
        levy_amount: '',
        levy_payment_method: 'debit_order',
        features: '',
        peak_hours_only: false,
        multi_site_access: false
      });
      fetchData();
    } catch (error) {
      toast.error('Failed to save membership type');
    }
  };

  const handleStaffSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/auth/register`, {
        email: staffForm.email,
        password: staffForm.password,
        full_name: staffForm.full_name,
        role: staffForm.role
      });
      
      toast.success('Staff user created!');
      setStaffDialogOpen(false);
      setStaffForm({
        email: '',
        password: '',
        full_name: '',
        role: 'staff'
      });
    } catch (error) {
      toast.error('Failed to create staff user');
    }
  };

  const handleSourceSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingSource) {
        // Update existing source
        await axios.put(`${API}/payment-sources/${editingSource.id}`, sourceForm);
        toast.success('Payment source updated!');
      } else {
        // Create new source
        await axios.post(`${API}/payment-sources`, sourceForm);
        toast.success('Payment source created!');
      }
      
      setSourceDialogOpen(false);
      setEditingSource(null);
      setSourceForm({
        name: '',
        description: '',
        is_active: true,
        display_order: 0
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save payment source');
    }
  };

  const handleEditSource = (source) => {
    setEditingSource(source);
    setSourceForm({
      name: source.name,
      description: source.description || '',
      is_active: source.is_active,
      display_order: source.display_order
    });
    setSourceDialogOpen(true);
  };

  const handleDeleteSource = async (sourceId) => {
    if (!window.confirm('Are you sure you want to delete this payment source?')) {
      return;
    }
    
    try {
      await axios.delete(`${API}/payment-sources/${sourceId}`);
      toast.success('Payment source deleted!');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete payment source');
    }
  };

  const handleSaveEftSettings = async () => {
    try {
      await axios.post(`${API}/eft/settings`, eftSettings);
      toast.success('EFT settings saved successfully!');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save EFT settings');
    }
  };


  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-white mb-2" data-testid="settings-title">Settings</h1>
            <p className="text-slate-400">Manage membership packages, staff, and system configuration</p>
          </div>

          <Tabs defaultValue="memberships" className="w-full">
            <TabsList className="bg-slate-800/50 border-slate-700">
              <TabsTrigger value="memberships" className="data-[state=active]:bg-emerald-500">
                <Package className="w-4 h-4 mr-2" />
                Membership Packages
              </TabsTrigger>
              <TabsTrigger value="sources" className="data-[state=active]:bg-emerald-500">
                <Tag className="w-4 h-4 mr-2" />
                Payment Sources
              </TabsTrigger>
              <TabsTrigger value="staff" className="data-[state=active]:bg-emerald-500">
                <Users className="w-4 h-4 mr-2" />
                Staff Management
              </TabsTrigger>
              <TabsTrigger value="permissions" className="data-[state=active]:bg-emerald-500">
                <Shield className="w-4 h-4 mr-2" />
                Access Rights
              </TabsTrigger>
              <TabsTrigger value="field-config" className="data-[state=active]:bg-emerald-500">
                <CheckSquare className="w-4 h-4 mr-2" />
                Field Configuration
              </TabsTrigger>
              <TabsTrigger value="eft" className="data-[state=active]:bg-emerald-500">
                <SettingsIcon className="w-4 h-4 mr-2" />
                EFT Settings
              </TabsTrigger>
              <TabsTrigger value="app" className="data-[state=active]:bg-emerald-500">
                <SettingsIcon className="w-4 h-4 mr-2" />
                App Settings
              </TabsTrigger>
            </TabsList>

            {/* Membership Packages Tab */}
            <TabsContent value="memberships" className="mt-6">
              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-white">Membership Packages</CardTitle>
                    <CardDescription className="text-slate-400">Create and manage membership types</CardDescription>
                  </div>
                  <Dialog open={membershipDialogOpen} onOpenChange={setMembershipDialogOpen}>
                    <DialogTrigger asChild>
                      <Button className="bg-gradient-to-r from-emerald-500 to-teal-600" data-testid="add-membership-type-button">
                        <Plus className="w-4 h-4 mr-2" />
                        Add Package
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-2xl max-h-[90vh] overflow-y-auto">
                      <DialogHeader>
                        <DialogTitle>Create Membership Package</DialogTitle>
                        <DialogDescription className="text-slate-400">
                          Configure membership details and pricing
                        </DialogDescription>
                      </DialogHeader>
                      <form onSubmit={handleMembershipSubmit} className="space-y-4">
                        <div className="space-y-2">
                          <Label>Package Name</Label>
                          <Input
                            value={membershipForm.name}
                            onChange={(e) => setMembershipForm({ ...membershipForm, name: e.target.value })}
                            placeholder="e.g., Premium Monthly"
                            required
                            className="bg-slate-700/50 border-slate-600"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Description</Label>
                          <Input
                            value={membershipForm.description}
                            onChange={(e) => setMembershipForm({ ...membershipForm, description: e.target.value })}
                            placeholder="Brief description"
                            required
                            className="bg-slate-700/50 border-slate-600"
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Price (R)</Label>
                            <Input
                              type="number"
                              step="0.01"
                              value={membershipForm.price}
                              onChange={(e) => setMembershipForm({ ...membershipForm, price: e.target.value })}
                              placeholder="299.00"
                              required
                              className="bg-slate-700/50 border-slate-600"
                            />
                          </div>
                          <div className="space-y-2">
                            <Label>Duration (Months)</Label>
                            <Input
                              type="number"
                              value={membershipForm.duration_months}
                              onChange={(e) => setMembershipForm({ ...membershipForm, duration_months: parseInt(e.target.value) })}
                              placeholder="1"
                              required
                              className="bg-slate-700/50 border-slate-600"
                            />
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label>Billing Frequency</Label>
                          <Select
                            value={membershipForm.billing_frequency}
                            onValueChange={(value) => setMembershipForm({ ...membershipForm, billing_frequency: value })}
                          >
                            <SelectTrigger className="bg-slate-700/50 border-slate-600">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-slate-800 border-slate-700">
                              <SelectItem value="monthly">Monthly</SelectItem>
                              <SelectItem value="6months">6 Months</SelectItem>
                              <SelectItem value="yearly">Yearly</SelectItem>
                              <SelectItem value="one-time">One-time</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label>Payment Type</Label>
                          <Select
                            value={membershipForm.payment_type}
                            onValueChange={(value) => setMembershipForm({ ...membershipForm, payment_type: value })}
                          >
                            <SelectTrigger className="bg-slate-700/50 border-slate-600">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-slate-800 border-slate-700">
                              <SelectItem value="paid_upfront">Paid Upfront (Full term payment)</SelectItem>
                              <SelectItem value="debit_order">Debit Order (Recurring)</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        {membershipForm.payment_type === 'debit_order' && membershipForm.billing_frequency !== 'monthly' && (
                          <div className="p-4 rounded-lg bg-blue-900/20 border border-blue-500">
                            <div className="flex items-center justify-between mb-2">
                              <Label className="text-blue-200">Rollover to Monthly After Term</Label>
                              <Switch
                                checked={membershipForm.rollover_enabled}
                                onCheckedChange={(checked) => setMembershipForm({ ...membershipForm, rollover_enabled: checked })}
                              />
                            </div>
                            <p className="text-blue-300 text-xs">
                              When enabled, membership automatically converts to monthly recurring after the initial term ends
                            </p>
                          </div>
                        )}
                        
                        {/* Levy Configuration */}
                        <div className="p-4 rounded-lg bg-amber-900/20 border border-amber-500 space-y-4">
                            <div className="flex items-center justify-between">
                              <div>
                                <Label className="text-amber-200">Enable Levy Charges</Label>
                                <p className="text-amber-300 text-xs mt-1">Annual or bi-annual levies billed separately</p>
                              </div>
                              <Switch
                                checked={membershipForm.levy_enabled}
                                onCheckedChange={(checked) => setMembershipForm({ ...membershipForm, levy_enabled: checked })}
                              />
                            </div>
                            
                            {membershipForm.levy_enabled && (
                              <div className="space-y-3 pt-2 border-t border-amber-500/30">
                                <div className="grid grid-cols-2 gap-3">
                                  <div className="space-y-2">
                                    <Label className="text-amber-200">Levy Frequency</Label>
                                    <Select
                                      value={membershipForm.levy_frequency}
                                      onValueChange={(value) => setMembershipForm({ ...membershipForm, levy_frequency: value })}
                                    >
                                      <SelectTrigger className="bg-slate-700/50 border-slate-600">
                                        <SelectValue />
                                      </SelectTrigger>
                                      <SelectContent className="bg-slate-800 border-slate-700">
                                        <SelectItem value="annual">Annual</SelectItem>
                                        <SelectItem value="biannual">Bi-annual (Half-year)</SelectItem>
                                      </SelectContent>
                                    </Select>
                                  </div>
                                  
                                  <div className="space-y-2">
                                    <Label className="text-amber-200">Levy Timing</Label>
                                    <Select
                                      value={membershipForm.levy_timing}
                                      onValueChange={(value) => setMembershipForm({ ...membershipForm, levy_timing: value })}
                                    >
                                      <SelectTrigger className="bg-slate-700/50 border-slate-600">
                                        <SelectValue />
                                      </SelectTrigger>
                                      <SelectContent className="bg-slate-800 border-slate-700">
                                        <SelectItem value="anniversary">Membership Anniversary</SelectItem>
                                        <SelectItem value="fixed_dates">Fixed Dates (1 June & 1 Dec)</SelectItem>
                                      </SelectContent>
                                    </Select>
                                  </div>
                                </div>
                                
                                <div className="space-y-2">
                                  <Label className="text-amber-200">Levy Amount</Label>
                                  <Select
                                    value={membershipForm.levy_amount_type}
                                    onValueChange={(value) => setMembershipForm({ ...membershipForm, levy_amount_type: value })}
                                  >
                                    <SelectTrigger className="bg-slate-700/50 border-slate-600">
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent className="bg-slate-800 border-slate-700">
                                      <SelectItem value="fixed">Fixed Amount</SelectItem>
                                      <SelectItem value="same_as_membership">Same as Membership Fee</SelectItem>
                                    </SelectContent>
                                  </Select>
                                </div>
                                
                                {membershipForm.levy_amount_type === 'fixed' && (
                                  <div className="space-y-2">
                                    <Label className="text-amber-200">Levy Amount (R)</Label>
                                    <Input
                                      type="number"
                                      step="0.01"
                                      value={membershipForm.levy_amount}
                                      onChange={(e) => setMembershipForm({ ...membershipForm, levy_amount: e.target.value })}
                                      placeholder="150.00"
                                      className="bg-slate-700/50 border-slate-600"
                                    />
                                  </div>
                                )}
                                
                                {membershipForm.payment_type === 'paid_upfront' && (
                                  <div className="space-y-2">
                                    <Label className="text-amber-200">Levy Payment Method</Label>
                                    <Select
                                      value={membershipForm.levy_payment_method}
                                      onValueChange={(value) => setMembershipForm({ ...membershipForm, levy_payment_method: value })}
                                    >
                                      <SelectTrigger className="bg-slate-700/50 border-slate-600">
                                        <SelectValue />
                                      </SelectTrigger>
                                      <SelectContent className="bg-slate-800 border-slate-700">
                                        <SelectItem value="upfront">Pay Upfront with Membership</SelectItem>
                                        <SelectItem value="debit_order">Debit Order (Recurring)</SelectItem>
                                      </SelectContent>
                                    </Select>
                                    <p className="text-amber-300 text-xs mt-1">
                                      {membershipForm.levy_payment_method === 'upfront' 
                                        ? 'Levy will be included in upfront membership invoice'
                                        : 'Levy will be billed separately on debit order schedule'}
                                    </p>
                                  </div>
                                )}
                                
                                <div className="bg-amber-950/50 p-2 rounded">
                                  <p className="text-amber-200 text-xs font-medium">⚠️ Important:</p>
                                  <p className="text-amber-300 text-xs mt-1">
                                    {membershipForm.payment_type === 'debit_order' || membershipForm.levy_payment_method === 'debit_order'
                                      ? 'Levies on debit order are billed separately from membership fees to reduce payment failures.'
                                      : 'Levies paid upfront will be included in the initial membership invoice.'}
                                  </p>
                                </div>
                              </div>
                            )}
                          </div>
                        
                        <div className="space-y-2">
                          <Label>Features (one per line)</Label>
                          <textarea
                            value={membershipForm.features}
                            onChange={(e) => setMembershipForm({ ...membershipForm, features: e.target.value })}
                            placeholder="24/7 gym access\nAll equipment\nGroup classes"
                            rows={4}
                            className="w-full bg-slate-700/50 border-slate-600 rounded-md p-2 text-white"
                          />
                        </div>
                        <div className="flex items-center justify-between p-3 rounded-lg bg-slate-700/30">
                          <Label>Peak Hours Only</Label>
                          <Switch
                            checked={membershipForm.peak_hours_only}
                            onCheckedChange={(checked) => setMembershipForm({ ...membershipForm, peak_hours_only: checked })}
                          />
                        </div>
                        <div className="flex items-center justify-between p-3 rounded-lg bg-slate-700/30">
                          <Label>Multi-Site Access</Label>
                          <Switch
                            checked={membershipForm.multi_site_access}
                            onCheckedChange={(checked) => setMembershipForm({ ...membershipForm, multi_site_access: checked })}
                          />
                        </div>
                        <Button type="submit" className="w-full bg-gradient-to-r from-emerald-500 to-teal-600">
                          Create Package
                        </Button>
                      </form>
                    </DialogContent>
                  </Dialog>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {membershipTypes.map((type) => (
                      <div key={type.id} className="p-4 rounded-lg bg-slate-700/30 hover:bg-slate-700/50 transition-all" data-testid={`membership-type-${type.id}`}>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2 flex-wrap">
                              <h3 className="text-white font-semibold text-lg">{type.name}</h3>
                              <Badge>{type.billing_frequency}</Badge>
                              <Badge variant={type.payment_type === 'paid_upfront' ? 'default' : 'secondary'}>
                                {type.payment_type === 'paid_upfront' ? 'Paid Upfront' : 'Debit Order'}
                              </Badge>
                              {type.rollover_enabled && <Badge className="bg-blue-500">Rollover Enabled</Badge>}
                              {type.levy_enabled && <Badge className="bg-amber-500">{type.levy_frequency === 'annual' ? 'Annual' : 'Bi-annual'} Levy</Badge>}
                              {type.multi_site_access && <Badge variant="secondary">Multi-Site</Badge>}
                              {type.peak_hours_only && <Badge variant="outline">Peak Hours</Badge>}
                            </div>
                            <p className="text-slate-400 text-sm mb-3">{type.description}</p>
                            <div className="flex items-center gap-4 mb-3">
                              <span className="text-emerald-400 font-bold text-xl">R {type.price.toFixed(2)}</span>
                              <span className="text-slate-400 text-sm">•</span>
                              <span className="text-slate-400 text-sm">{type.duration_months} month{type.duration_months !== 1 ? 's' : ''}</span>
                              {type.levy_enabled && (
                                <>
                                  <span className="text-slate-400 text-sm">•</span>
                                  <span className="text-amber-400 text-sm font-medium">
                                    Levy: R {type.levy_amount_type === 'same_as_membership' ? type.price.toFixed(2) : (type.levy_amount || 0).toFixed(2)}
                                  </span>
                                </>
                              )}
                            </div>
                            {type.levy_enabled && (
                              <div className="mb-3 p-2 rounded bg-amber-900/20 border border-amber-500/30">
                                <p className="text-amber-300 text-xs">
                                  📋 {type.levy_frequency === 'annual' ? 'Annual' : 'Bi-annual'} levy charged {type.levy_timing === 'anniversary' ? 'on membership anniversary' : 'on 1 June & 1 December'} - Billed separately
                                </p>
                              </div>
                            )}
                            {type.features && type.features.length > 0 && (
                              <ul className="space-y-1">
                                {type.features.map((feature, idx) => (
                                  <li key={idx} className="text-slate-400 text-sm flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                                    {feature}
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>


            {/* Payment Sources Tab */}
            <TabsContent value="sources" className="mt-6">
              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-white">Payment Sources</CardTitle>
                    <CardDescription className="text-slate-400">
                      Manage how members find your gym for sales tracking
                    </CardDescription>
                  </div>
                  <Dialog open={sourceDialogOpen} onOpenChange={(open) => {
                    setSourceDialogOpen(open);
                    if (!open) {
                      setEditingSource(null);
                      setSourceForm({
                        name: '',
                        description: '',
                        is_active: true,
                        display_order: 0
                      });
                    }
                  }}>
                    <DialogTrigger asChild>
                      <Button className="bg-emerald-500 hover:bg-emerald-600">
                        <Plus className="w-4 h-4 mr-2" />
                        Add Source
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-md">
                      <DialogHeader>
                        <DialogTitle>{editingSource ? 'Edit' : 'Add'} Payment Source</DialogTitle>
                        <DialogDescription className="text-slate-400">
                          {editingSource ? 'Update the' : 'Create a new'} source for tracking member acquisition
                        </DialogDescription>
                      </DialogHeader>
                      <form onSubmit={handleSourceSubmit} className="space-y-4">
                        <div className="space-y-2">
                          <Label>Source Name *</Label>
                          <Input
                            value={sourceForm.name}
                            onChange={(e) => setSourceForm({ ...sourceForm, name: e.target.value })}
                            placeholder="e.g., Walk-in, Online, Social Media"
                            required
                            className="bg-slate-700/50 border-slate-600"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Description</Label>
                          <Input
                            value={sourceForm.description}
                            onChange={(e) => setSourceForm({ ...sourceForm, description: e.target.value })}
                            placeholder="Optional description"
                            className="bg-slate-700/50 border-slate-600"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Display Order</Label>
                          <Input
                            type="number"
                            value={sourceForm.display_order}
                            onChange={(e) => setSourceForm({ ...sourceForm, display_order: parseInt(e.target.value) || 0 })}
                            placeholder="0"
                            className="bg-slate-700/50 border-slate-600"
                          />
                          <p className="text-xs text-slate-400">Lower numbers appear first in dropdowns</p>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Switch
                            checked={sourceForm.is_active}
                            onCheckedChange={(checked) => setSourceForm({ ...sourceForm, is_active: checked })}
                            className="data-[state=checked]:bg-emerald-500"
                          />
                          <Label>Active</Label>
                        </div>
                        <div className="flex gap-2 pt-4">
                          <Button type="submit" className="flex-1 bg-emerald-500 hover:bg-emerald-600">
                            {editingSource ? 'Update' : 'Create'} Source
                          </Button>
                          <Button 
                            type="button" 
                            variant="outline" 
                            onClick={() => setSourceDialogOpen(false)}
                            className="border-slate-600 hover:bg-slate-700"
                          >
                            Cancel
                          </Button>
                        </div>
                      </form>
                    </DialogContent>
                  </Dialog>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div className="text-center py-8 text-slate-400">Loading...</div>
                  ) : paymentSources.length === 0 ? (
                    <div className="text-center py-8 text-slate-400">
                      No payment sources yet. Add your first source to start tracking member acquisition.
                    </div>
                  ) : (
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                      {paymentSources
                        .sort((a, b) => a.display_order - b.display_order)
                        .map((source) => (
                          <Card key={source.id} className="bg-slate-700/30 border-slate-600">
                            <CardContent className="p-4">
                              <div className="flex items-start justify-between mb-2">
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-1">
                                    <h3 className="font-semibold text-white">{source.name}</h3>
                                    {source.is_active ? (
                                      <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/50">
                                        Active
                                      </Badge>
                                    ) : (
                                      <Badge variant="outline" className="border-slate-600 text-slate-400">
                                        Inactive
                                      </Badge>
                                    )}
                                  </div>
                                  {source.description && (
                                    <p className="text-sm text-slate-400 mb-2">{source.description}</p>
                                  )}
                                  <p className="text-xs text-slate-500">Order: {source.display_order}</p>
                                </div>
                              </div>
                              <div className="flex gap-2 mt-3">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleEditSource(source)}
                                  className="flex-1 border-slate-600 hover:bg-slate-600"
                                >
                                  <Edit className="w-3 h-3 mr-1" />
                                  Edit
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleDeleteSource(source.id)}
                                  className="border-red-500/50 text-red-400 hover:bg-red-500/20"
                                >
                                  <Trash2 className="w-3 h-3" />
                                </Button>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>


            {/* Staff Management Tab */}
            <TabsContent value="staff" className="mt-6">
              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-white">Staff Users</CardTitle>
                    <CardDescription className="text-slate-400">Manage staff accounts and access</CardDescription>
                  </div>
                  <Dialog open={staffDialogOpen} onOpenChange={setStaffDialogOpen}>
                    <DialogTrigger asChild>
                      <Button className="bg-gradient-to-r from-emerald-500 to-teal-600" data-testid="add-staff-button">
                        <Plus className="w-4 h-4 mr-2" />
                        Add Staff
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="bg-slate-800 border-slate-700 text-white">
                      <DialogHeader>
                        <DialogTitle>Add Staff User</DialogTitle>
                        <DialogDescription className="text-slate-400">
                          Create a new staff account with role-based access
                        </DialogDescription>
                      </DialogHeader>
                      <form onSubmit={handleStaffSubmit} className="space-y-4">
                        <div className="space-y-2">
                          <Label>Full Name</Label>
                          <Input
                            value={staffForm.full_name}
                            onChange={(e) => setStaffForm({ ...staffForm, full_name: e.target.value })}
                            placeholder="John Doe"
                            required
                            className="bg-slate-700/50 border-slate-600"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Email</Label>
                          <Input
                            type="email"
                            value={staffForm.email}
                            onChange={(e) => setStaffForm({ ...staffForm, email: e.target.value })}
                            placeholder="staff@gym.com"
                            required
                            className="bg-slate-700/50 border-slate-600"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Password</Label>
                          <Input
                            type="password"
                            value={staffForm.password}
                            onChange={(e) => setStaffForm({ ...staffForm, password: e.target.value })}
                            placeholder="••••••••"
                            required
                            className="bg-slate-700/50 border-slate-600"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Role</Label>
                          <Select
                            value={staffForm.role}
                            onValueChange={(value) => setStaffForm({ ...staffForm, role: value })}
                          >
                            <SelectTrigger className="bg-slate-700/50 border-slate-600">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-slate-800 border-slate-700">
                              <SelectItem value="admin">Admin (Full Access)</SelectItem>
                              <SelectItem value="manager">Manager</SelectItem>
                              <SelectItem value="staff">Staff (Reception)</SelectItem>
                              <SelectItem value="trainer">Trainer</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <Button type="submit" className="w-full bg-gradient-to-r from-emerald-500 to-teal-600">
                          Create Staff Account
                        </Button>
                      </form>
                    </DialogContent>
                  </Dialog>
                </CardHeader>
                <CardContent>
                  <div className="text-center text-slate-400 py-8">
                    Staff management functionality - Create staff accounts with role-based permissions
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Access Rights Tab */}
            <TabsContent value="permissions" className="mt-6">
              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
                <CardHeader>
                  <CardTitle className="text-white">Role Permissions</CardTitle>
                  <CardDescription className="text-slate-400">Configure access rights for different staff roles</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    {[{role: 'admin', desc: 'Full system access'}, {role: 'manager', desc: 'Manage operations'}, {role: 'staff', desc: 'Reception duties'}, {role: 'trainer', desc: 'Member training'}].map(({role, desc}) => (
                      <div key={role} className="p-4 rounded-lg bg-slate-700/30">
                        <div className="mb-4">
                          <h3 className="text-white font-semibold capitalize">{role}</h3>
                          <p className="text-slate-400 text-sm">{desc}</p>
                        </div>
                        <div className="space-y-3">
                          {[
                            {key: 'manage_members', label: 'Manage Members'},
                            {key: 'manage_billing', label: 'Manage Billing'},
                            {key: 'manage_access', label: 'Access Control'},
                            {key: 'manage_staff', label: 'Manage Staff'},
                            {key: 'view_reports', label: 'View Reports'}
                          ].map(({key, label}) => (
                            <div key={key} className="flex items-center justify-between">
                              <span className="text-slate-300 text-sm">{label}</span>
                              <Switch defaultChecked={role === 'admin' || (role === 'manager' && key !== 'manage_staff')} />
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Field Configuration Tab */}
            <TabsContent value="field-config" className="mt-6">
              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-white">Field Configuration</CardTitle>
                    <CardDescription className="text-slate-400">
                      Configure which fields are mandatory and set validation rules
                    </CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    onClick={handleResetFieldConfigs}
                    className="bg-slate-700 border-slate-600 text-white hover:bg-slate-600"
                  >
                    Reset to Defaults
                  </Button>
                </CardHeader>
                <CardContent>
                  {/* Group by category */}
                  {['basic', 'contact', 'address', 'banking', 'membership'].map(category => {
                    const categoryFields = fieldConfigurations.filter(f => f.category === category);
                    if (categoryFields.length === 0) return null;

                    return (
                      <div key={category} className="mb-6">
                        <h3 className="text-white font-semibold capitalize mb-4 text-lg border-b border-slate-600 pb-2">
                          {category} Information
                        </h3>
                        <div className="space-y-4">
                          {categoryFields.map(field => (
                            <div key={field.field_name} className="p-4 rounded-lg bg-slate-700/30 border border-slate-600">
                              <div className="flex items-start justify-between mb-3">
                                <div className="flex-1">
                                  <div className="flex items-center space-x-2 mb-1">
                                    <h4 className="text-white font-medium">{field.label}</h4>
                                    <Badge variant={field.field_type === 'email' ? 'default' : field.field_type === 'phone' ? 'secondary' : 'outline'} className="text-xs">
                                      {field.field_type}
                                    </Badge>
                                  </div>
                                  <p className="text-slate-400 text-sm">Field: {field.field_name}</p>
                                </div>
                                <div className="flex items-center space-x-2">
                                  <Label className="text-slate-300 text-sm">Required</Label>
                                  <Switch
                                    checked={field.is_required}
                                    onCheckedChange={(checked) => handleFieldConfigUpdate(field.field_name, { is_required: checked })}
                                    className="data-[state=checked]:bg-emerald-500"
                                  />
                                </div>
                              </div>

                              {/* Validation Rules Display */}
                              {Object.keys(field.validation_rules).length > 0 && (
                                <div className="mt-3 p-3 bg-slate-800/50 rounded border border-slate-600">
                                  <p className="text-slate-300 text-xs font-semibold mb-2">Validation Rules:</p>
                                  <div className="flex flex-wrap gap-2">
                                    {field.validation_rules.min_length && (
                                      <Badge variant="outline" className="text-xs">
                                        Min: {field.validation_rules.min_length} chars
                                      </Badge>
                                    )}
                                    {field.validation_rules.max_length && (
                                      <Badge variant="outline" className="text-xs">
                                        Max: {field.validation_rules.max_length} chars
                                      </Badge>
                                    )}
                                    {field.validation_rules.numeric_only && (
                                      <Badge variant="outline" className="text-xs">
                                        Numbers only
                                      </Badge>
                                    )}
                                    {field.validation_rules.must_contain && (
                                      <Badge variant="outline" className="text-xs">
                                        Must contain: {field.validation_rules.must_contain.join(', ')}
                                      </Badge>
                                    )}
                                    {field.validation_rules.pattern === 'email' && (
                                      <Badge variant="outline" className="text-xs">
                                        Email format (requires @ and .)
                                      </Badge>
                                    )}
                                  </div>
                                  {field.error_message && (
                                    <p className="text-slate-400 text-xs mt-2 italic">
                                      Error message: "{field.error_message}"
                                    </p>
                                  )}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}

                  {fieldConfigurations.length === 0 && (
                    <div className="text-center py-12">
                      <CheckSquare className="h-12 w-12 mx-auto text-slate-600 mb-4" />
                      <p className="text-slate-400">Loading field configurations...</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* EFT Settings Tab */}
            <TabsContent value="eft">
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <SettingsIcon className="w-5 h-5 mr-2" />
                    EFT SDV Configuration
                  </CardTitle>
                  <CardDescription className="text-slate-400">
                    Configure Electronic Funds Transfer settings for automated billing and levy collection
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid md:grid-cols-2 gap-6">
                    {/* Client Profile Number */}
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

                    {/* Nominated Account */}
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
                      <p className="text-xs text-slate-400">16-digit Nedbank account for credits</p>
                    </div>

                    {/* Charges Account */}
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
                      <p className="text-xs text-slate-400">16-digit Nedbank account for fees/charges</p>
                    </div>

                    {/* Service User Number */}
                    <div className="space-y-2">
                      <Label className="text-white">Service User Number</Label>
                      <Input
                        type="text"
                        placeholder="Optional service identifier"
                        value={eftSettings.service_user_number}
                        onChange={(e) => setEftSettings({...eftSettings, service_user_number: e.target.value})}
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                      <p className="text-xs text-slate-400">Additional service identifier (optional)</p>
                    </div>

                    {/* Branch Code */}
                    <div className="space-y-2">
                      <Label className="text-white">Branch Code</Label>
                      <Input
                        type="text"
                        maxLength={6}
                        placeholder="000000"
                        value={eftSettings.branch_code}
                        onChange={(e) => setEftSettings({...eftSettings, branch_code: e.target.value})}
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                      <p className="text-xs text-slate-400">6-digit bank branch code</p>
                    </div>

                    {/* Bank Name */}
                    <div className="space-y-2">
                      <Label className="text-white">Bank Name</Label>
                      <Input
                        type="text"
                        value={eftSettings.bank_name}
                        onChange={(e) => setEftSettings({...eftSettings, bank_name: e.target.value})}
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                      <p className="text-xs text-slate-400">Bank name (default: Nedbank)</p>
                    </div>
                  </div>

                  {/* Billing Schedule Settings */}
                  <div className="border-t border-slate-700 pt-6 mt-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Billing Schedule & Automation</h3>
                    
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <Label className="text-white text-base">Advance Billing Days</Label>
                        <div className="flex items-start gap-4">
                          <Input
                            type="number"
                            min="0"
                            max="30"
                            value={eftSettings.advance_billing_days}
                            onChange={(e) => setEftSettings({...eftSettings, advance_billing_days: parseInt(e.target.value) || 5})}
                            className="bg-slate-700 border-slate-600 text-white w-32"
                          />
                          <div className="flex-1">
                            <p className="text-sm text-slate-400">
                              Generate billing files <strong className="text-emerald-400">{eftSettings.advance_billing_days} days</strong> before payment due date
                            </p>
                            <p className="text-xs text-slate-500 mt-1">
                              Recommended: 5 days to allow time for payment gateway processing
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg">
                        <div>
                          <Label className="text-white text-base">Enable Automatic File Generation</Label>
                          <p className="text-sm text-slate-400 mt-1">
                            Automatically generate EFT/DebiCheck files based on due dates
                          </p>
                        </div>
                        <Switch
                          checked={eftSettings.enable_auto_generation}
                          onCheckedChange={(checked) => setEftSettings({...eftSettings, enable_auto_generation: checked})}
                        />
                      </div>

                      {eftSettings.enable_auto_generation && (
                        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                          <p className="text-sm text-blue-300">
                            <strong>Auto-generation enabled:</strong> Files will be automatically generated {eftSettings.advance_billing_days} days before invoice/levy due dates.
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Notification Settings */}
                  <div className="border-t border-slate-700 pt-6 mt-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Payment Notification Settings</h3>
                    
                    <div className="space-y-4">
                      <div className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg">
                        <div>
                          <Label className="text-white text-base">Enable Payment Notifications</Label>
                          <p className="text-sm text-slate-400 mt-1">
                            Send automated notifications to members when payments are confirmed
                          </p>
                        </div>
                        <Switch
                          checked={eftSettings.enable_notifications}
                          onCheckedChange={(checked) => setEftSettings({...eftSettings, enable_notifications: checked})}
                        />
                      </div>

                      {eftSettings.enable_notifications && (
                        <div className="space-y-2">
                          <Label className="text-white">Notification Email</Label>
                          <Input
                            type="email"
                            placeholder="notifications@yourgym.com"
                            value={eftSettings.notification_email}
                            onChange={(e) => setEftSettings({...eftSettings, notification_email: e.target.value})}
                            className="bg-slate-700 border-slate-600 text-white"
                          />
                          <p className="text-xs text-slate-400">
                            Email address for EFT notification copies (optional)
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Save Button */}
                  <div className="flex justify-end pt-4 border-t border-slate-700">
                    <Button 
                      onClick={handleSaveEftSettings}
                      className="bg-emerald-500 hover:bg-emerald-600 text-white"
                    >
                      Save EFT Settings
                    </Button>
                  </div>

                  {/* Information Box */}
                  <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 mt-6">
                    <h4 className="text-blue-400 font-semibold mb-2">📋 Important Information</h4>
                    <ul className="text-sm text-slate-300 space-y-1">
                      <li>• EFT files are generated in Nedbank CPS format for Same Day Value processing</li>
                      <li>• Generated files are auto-saved to <code className="bg-slate-700 px-1 rounded">/app/eft_files/outgoing</code></li>
                      <li>• Incoming bank response files are monitored in <code className="bg-slate-700 px-1 rounded">/app/eft_files/incoming</code></li>
                      <li>• <strong>Advance billing:</strong> Files created {eftSettings.advance_billing_days} days before due date for payment gateway processing</li>
                      <li>• Payment confirmations automatically update member balances and invoice statuses</li>
                      <li>• All EFT transactions are logged for audit purposes</li>
                      <li>• Use manual generation or enable auto-generation based on your workflow</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
