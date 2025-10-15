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
import { Package, Users, Shield, Plus, Edit } from 'lucide-react';
import { toast } from 'sonner';

export default function Settings() {
  const [membershipTypes, setMembershipTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [membershipDialogOpen, setMembershipDialogOpen] = useState(false);
  const [staffDialogOpen, setStaffDialogOpen] = useState(false);
  
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

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const response = await axios.get(`${API}/membership-types`);
      setMembershipTypes(response.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleMembershipSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        ...membershipForm,
        price: parseFloat(membershipForm.price),
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
              <TabsTrigger value="staff" className="data-[state=active]:bg-emerald-500">
                <Users className="w-4 h-4 mr-2" />
                Staff Management
              </TabsTrigger>
              <TabsTrigger value="permissions" className="data-[state=active]:bg-emerald-500">
                <Shield className="w-4 h-4 mr-2" />
                Access Rights
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
                              {type.multi_site_access && <Badge variant="secondary">Multi-Site</Badge>}
                              {type.peak_hours_only && <Badge variant="outline">Peak Hours</Badge>}
                            </div>
                            <p className="text-slate-400 text-sm mb-3">{type.description}</p>
                            <div className="flex items-center gap-4 mb-3">
                              <span className="text-emerald-400 font-bold text-xl">R {type.price.toFixed(2)}</span>
                              <span className="text-slate-400 text-sm">•</span>
                              <span className="text-slate-400 text-sm">{type.duration_months} month{type.duration_months !== 1 ? 's' : ''}</span>
                            </div>
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
          </Tabs>
        </div>
      </div>
    </div>
  );
}
