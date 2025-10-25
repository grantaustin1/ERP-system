import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import {
  Gift,
  Users,
  TrendingUp,
  TrendingDown,
  Calendar,
  CheckCircle,
  XCircle,
  Clock,
  Award,
  Plus,
  Settings,
  Edit,
  Trash2,
  UserPlus,
  AlertTriangle,
  Eye,
  BarChart3
} from 'lucide-react';

export default function ComplimentaryMembership() {
  const [dashboardData, setDashboardData] = useState(null);
  const [memberships, setMemberships] = useState([]);
  const [types, setTypes] = useState([]);
  const [consultants, setConsultants] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Filters
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterType, setFilterType] = useState('all');
  const [filterConsultant, setFilterConsultant] = useState('all');
  
  // Dialogs
  const [issuePassDialogOpen, setIssuePassDialogOpen] = useState(false);
  const [typeManagementOpen, setTypeManagementOpen] = useState(false);
  const [selectedType, setSelectedType] = useState(null);
  
  // Issue Pass Form
  const [passForm, setPassForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    complimentary_type_id: '',
    assigned_consultant_id: '',
    notes: '',
    auto_create_lead: true
  });
  
  // Type Form
  const [typeForm, setTypeForm] = useState({
    name: '',
    description: '',
    time_limit_days: 7,
    visit_limit: 3,
    no_access_alert_days: 3,
    notification_on_visits: [1, 2, 3],
    is_active: true,
    color: '#3b82f6',
    icon: '🎁'
  });

  useEffect(() => {
    fetchDashboardData();
    fetchMemberships();
    fetchTypes();
    fetchConsultants();
  }, []);

  useEffect(() => {
    fetchMemberships();
  }, [filterStatus, filterType, filterConsultant]);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/complimentary-dashboard?days=30`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    }
  };

  const fetchMemberships = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filterStatus !== 'all') params.status = filterStatus;
      if (filterType !== 'all') params.complimentary_type_id = filterType;
      if (filterConsultant !== 'all') params.assigned_consultant_id = filterConsultant;
      
      const response = await axios.get(`${API}/complimentary-memberships`, { params });
      setMemberships(response.data.memberships || []);
    } catch (error) {
      toast.error('Failed to fetch memberships');
    } finally {
      setLoading(false);
    }
  };

  const fetchTypes = async () => {
    try {
      const response = await axios.get(`${API}/complimentary-types`);
      setTypes(response.data.types || []);
    } catch (error) {
      console.error('Failed to fetch types:', error);
    }
  };

  const fetchConsultants = async () => {
    try {
      const response = await axios.get(`${API}/sales/consultants`);
      setConsultants(response.data.consultants || []);
    } catch (error) {
      console.error('Failed to fetch consultants:', error);
    }
  };

  const handleIssuePass = async (e) => {
    e.preventDefault();
    
    if (!passForm.first_name || !passForm.last_name || !passForm.complimentary_type_id) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    try {
      await axios.post(`${API}/complimentary-memberships`, passForm);
      toast.success('Complimentary pass issued successfully!');
      setIssuePassDialogOpen(false);
      setPassForm({
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        complimentary_type_id: '',
        assigned_consultant_id: '',
        notes: '',
        auto_create_lead: true
      });
      fetchMemberships();
      fetchDashboardData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to issue pass');
    }
  };

  const handleCreateType = async (e) => {
    e.preventDefault();
    
    try {
      if (selectedType) {
        // Update existing type
        await axios.put(`${API}/complimentary-types/${selectedType.id}`, typeForm);
        toast.success('Type updated successfully');
      } else {
        // Create new type
        await axios.post(`${API}/complimentary-types`, typeForm);
        toast.success('Type created successfully');
      }
      
      setTypeManagementOpen(false);
      setSelectedType(null);
      setTypeForm({
        name: '',
        description: '',
        time_limit_days: 7,
        visit_limit: 3,
        no_access_alert_days: 3,
        notification_on_visits: [1, 2, 3],
        is_active: true,
        color: '#3b82f6',
        icon: '🎁'
      });
      fetchTypes();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save type');
    }
  };

  const handleDeleteType = async (typeId) => {
    if (!window.confirm('Are you sure you want to delete this type?')) return;
    
    try {
      await axios.delete(`${API}/complimentary-types/${typeId}`);
      toast.success('Type deleted successfully');
      fetchTypes();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete type');
    }
  };

  const handleEditType = (type) => {
    setSelectedType(type);
    setTypeForm({
      name: type.name,
      description: type.description || '',
      time_limit_days: type.time_limit_days,
      visit_limit: type.visit_limit,
      no_access_alert_days: type.no_access_alert_days,
      notification_on_visits: type.notification_on_visits || [1, 2, 3],
      is_active: type.is_active,
      color: type.color || '#3b82f6',
      icon: type.icon || '🎁'
    });
    setTypeManagementOpen(true);
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      active: { label: 'Active', variant: 'default', icon: CheckCircle, color: 'bg-green-500' },
      expired: { label: 'Expired', variant: 'secondary', icon: XCircle, color: 'bg-gray-500' },
      completed: { label: 'Completed', variant: 'default', icon: Award, color: 'bg-blue-500' },
      converted: { label: 'Converted', variant: 'default', icon: TrendingUp, color: 'bg-purple-500' },
      not_using: { label: 'Not Using', variant: 'destructive', icon: AlertTriangle, color: 'bg-red-500' }
    };
    
    const config = statusConfig[status] || statusConfig.active;
    const Icon = config.icon;
    
    return (
      <Badge className={`${config.color} text-white`}>
        <Icon className="w-3 h-3 mr-1" />
        {config.label}
      </Badge>
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const calculateDaysRemaining = (expiryDate) => {
    const expiry = new Date(expiryDate);
    const now = new Date();
    const diff = Math.ceil((expiry - now) / (1000 * 60 * 60 * 24));
    return diff > 0 ? diff : 0;
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 overflow-auto">
        <div className="p-8">
          {/* Header */}
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
                <Gift className="w-8 h-8 text-blue-600" />
                Complimentary Membership Tracking
              </h1>
              <p className="text-gray-600 mt-1">Manage complimentary passes, track usage, and monitor conversions</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setTypeManagementOpen(true)}>
                <Settings className="w-4 h-4 mr-2" />
                Manage Types
              </Button>
              <Button onClick={() => setIssuePassDialogOpen(true)}>
                <UserPlus className="w-4 h-4 mr-2" />
                Issue Pass
              </Button>
            </div>
          </div>

          {/* Dashboard Metrics */}
          {dashboardData && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Total Issued (30 days)</CardDescription>
                  <CardTitle className="text-3xl">{dashboardData.total_issued}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center text-sm text-gray-600">
                    <Calendar className="w-4 h-4 mr-1" />
                    Last 30 days
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Active Memberships</CardDescription>
                  <CardTitle className="text-3xl text-green-600">{dashboardData.active_memberships}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center text-sm text-gray-600">
                    <CheckCircle className="w-4 h-4 mr-1" />
                    Currently valid
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Utilization Rate</CardDescription>
                  <CardTitle className="text-3xl text-blue-600">{dashboardData.utilization_rate}%</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center text-sm">
                    <TrendingUp className="w-4 h-4 mr-1 text-blue-600" />
                    <span className="text-gray-600">{dashboardData.accessing_count} accessing</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Conversion Rate</CardDescription>
                  <CardTitle className="text-3xl text-purple-600">{dashboardData.conversion_rate}%</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center text-sm">
                    <Award className="w-4 h-4 mr-1 text-purple-600" />
                    <span className="text-gray-600">{dashboardData.converted_count} converted</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Not Using</CardDescription>
                  <CardTitle className="text-3xl text-red-600">{dashboardData.not_accessing_count}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center text-sm text-gray-600">
                    <AlertTriangle className="w-4 h-4 mr-1 text-red-600" />
                    Needs follow-up
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Expired Passes</CardDescription>
                  <CardTitle className="text-3xl text-gray-600">{dashboardData.expired_count}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center text-sm text-gray-600">
                    <Clock className="w-4 h-4 mr-1" />
                    Time limit reached
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Utilization by Type */}
          {dashboardData && dashboardData.utilization_by_type && dashboardData.utilization_by_type.length > 0 && (
            <Card className="mb-8">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  Utilization by Type
                </CardTitle>
                <CardDescription>Performance breakdown by complimentary membership type</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {dashboardData.utilization_by_type.map((item, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h4 className="font-semibold text-lg">{item.type_name}</h4>
                          <p className="text-sm text-gray-600">Total issued: {item.total_issued}</p>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-blue-600">{item.utilization_percentage}%</div>
                          <div className="text-sm text-gray-600">Utilization</div>
                        </div>
                      </div>
                      <div className="grid grid-cols-3 gap-4 mt-3">
                        <div>
                          <div className="text-sm text-gray-600">Total Visits</div>
                          <div className="text-xl font-semibold">{item.total_visits}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600">Members Accessed</div>
                          <div className="text-xl font-semibold text-green-600">{item.members_accessed}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600">Conversion Rate</div>
                          <div className="text-xl font-semibold text-purple-600">{item.conversion_rate}%</div>
                        </div>
                      </div>
                      <div className="mt-3 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${item.utilization_percentage}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Filters and Memberships List */}
          <Card>
            <CardHeader>
              <CardTitle>Complimentary Memberships</CardTitle>
              <CardDescription>Track and manage all issued complimentary passes</CardDescription>
            </CardHeader>
            <CardContent>
              {/* Filters */}
              <div className="flex flex-wrap gap-4 mb-6">
                <div className="flex-1 min-w-[200px]">
                  <Label>Status</Label>
                  <Select value={filterStatus} onValueChange={setFilterStatus}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Statuses</SelectItem>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="not_using">Not Using</SelectItem>
                      <SelectItem value="expired">Expired</SelectItem>
                      <SelectItem value="completed">Completed</SelectItem>
                      <SelectItem value="converted">Converted</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex-1 min-w-[200px]">
                  <Label>Type</Label>
                  <Select value={filterType} onValueChange={setFilterType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      {types.map(type => (
                        <SelectItem key={type.id} value={type.id}>{type.icon} {type.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex-1 min-w-[200px]">
                  <Label>Consultant</Label>
                  <Select value={filterConsultant} onValueChange={setFilterConsultant}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Consultants</SelectItem>
                      {consultants.map(consultant => (
                        <SelectItem key={consultant.id} value={consultant.id}>{consultant.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Memberships Table */}
              {loading ? (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-4 text-gray-600">Loading memberships...</p>
                </div>
              ) : memberships.length === 0 ? (
                <div className="text-center py-12">
                  <Gift className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-600">No complimentary memberships found</p>
                  <Button className="mt-4" onClick={() => setIssuePassDialogOpen(true)}>
                    <UserPlus className="w-4 h-4 mr-2" />
                    Issue First Pass
                  </Button>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="border-b">
                      <tr className="text-left text-sm text-gray-600">
                        <th className="pb-3 font-semibold">Member</th>
                        <th className="pb-3 font-semibold">Type</th>
                        <th className="pb-3 font-semibold">Visits</th>
                        <th className="pb-3 font-semibold">Last Visit</th>
                        <th className="pb-3 font-semibold">Days Left</th>
                        <th className="pb-3 font-semibold">Consultant</th>
                        <th className="pb-3 font-semibold">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {memberships.map((membership) => (
                        <tr key={membership.id} className="border-b hover:bg-gray-50">
                          <td className="py-4">
                            <div>
                              <div className="font-semibold">{membership.member_name}</div>
                              <div className="text-sm text-gray-600">{membership.member_email}</div>
                              <div className="text-sm text-gray-600">{membership.member_phone}</div>
                            </div>
                          </td>
                          <td className="py-4">
                            <div className="flex items-center gap-2">
                              <span className="text-2xl">{types.find(t => t.id === membership.complimentary_type_id)?.icon || '🎁'}</span>
                              <span>{membership.complimentary_type_name}</span>
                            </div>
                          </td>
                          <td className="py-4">
                            <div>
                              <div className="font-semibold">{membership.visits_used} / {membership.visit_limit}</div>
                              <div className="text-sm text-gray-600">{membership.visits_remaining} remaining</div>
                            </div>
                          </td>
                          <td className="py-4 text-sm">{formatDate(membership.last_visit_date)}</td>
                          <td className="py-4">
                            <Badge variant={calculateDaysRemaining(membership.expiry_date) < 3 ? 'destructive' : 'secondary'}>
                              {calculateDaysRemaining(membership.expiry_date)} days
                            </Badge>
                          </td>
                          <td className="py-4 text-sm">{membership.assigned_consultant_name || 'Unassigned'}</td>
                          <td className="py-4">{getStatusBadge(membership.status)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Issue Pass Dialog */}
          <Dialog open={issuePassDialogOpen} onOpenChange={setIssuePassDialogOpen}>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Issue Complimentary Pass</DialogTitle>
                <DialogDescription>Create a new complimentary membership pass for a prospect</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleIssuePass} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>First Name *</Label>
                    <Input
                      value={passForm.first_name}
                      onChange={(e) => setPassForm({ ...passForm, first_name: e.target.value })}
                      placeholder="John"
                      required
                    />
                  </div>
                  <div>
                    <Label>Last Name *</Label>
                    <Input
                      value={passForm.last_name}
                      onChange={(e) => setPassForm({ ...passForm, last_name: e.target.value })}
                      placeholder="Doe"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Email</Label>
                    <Input
                      type="email"
                      value={passForm.email}
                      onChange={(e) => setPassForm({ ...passForm, email: e.target.value })}
                      placeholder="john@example.com"
                    />
                  </div>
                  <div>
                    <Label>Phone</Label>
                    <Input
                      value={passForm.phone}
                      onChange={(e) => setPassForm({ ...passForm, phone: e.target.value })}
                      placeholder="+27 123 456 7890"
                    />
                  </div>
                </div>

                <div>
                  <Label>Pass Type *</Label>
                  <Select value={passForm.complimentary_type_id} onValueChange={(value) => setPassForm({ ...passForm, complimentary_type_id: value })}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select pass type" />
                    </SelectTrigger>
                    <SelectContent>
                      {types.filter(t => t.is_active).map(type => (
                        <SelectItem key={type.id} value={type.id}>
                          {type.icon} {type.name} ({type.visit_limit} visits, {type.time_limit_days} days)
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Assign to Consultant</Label>
                  <Select value={passForm.assigned_consultant_id} onValueChange={(value) => setPassForm({ ...passForm, assigned_consultant_id: value })}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select consultant (optional)" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">None</SelectItem>
                      {consultants.map(consultant => (
                        <SelectItem key={consultant.id} value={consultant.id}>{consultant.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Notes</Label>
                  <Textarea
                    value={passForm.notes}
                    onChange={(e) => setPassForm({ ...passForm, notes: e.target.value })}
                    placeholder="Additional notes about this pass..."
                    rows={3}
                  />
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="auto_create_lead"
                    checked={passForm.auto_create_lead}
                    onChange={(e) => setPassForm({ ...passForm, auto_create_lead: e.target.checked })}
                    className="w-4 h-4"
                  />
                  <Label htmlFor="auto_create_lead" className="cursor-pointer">
                    Automatically create a lead in the CRM
                  </Label>
                </div>

                <div className="flex justify-end gap-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setIssuePassDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit">
                    <UserPlus className="w-4 h-4 mr-2" />
                    Issue Pass
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>

          {/* Type Management Dialog */}
          <Dialog open={typeManagementOpen} onOpenChange={setTypeManagementOpen}>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Manage Complimentary Types</DialogTitle>
                <DialogDescription>Create and manage different types of complimentary memberships</DialogDescription>
              </DialogHeader>

              <Tabs defaultValue="list">
                <TabsList>
                  <TabsTrigger value="list">Existing Types</TabsTrigger>
                  <TabsTrigger value="create">{selectedType ? 'Edit Type' : 'Create New'}</TabsTrigger>
                </TabsList>

                <TabsContent value="list" className="space-y-4">
                  {types.length === 0 ? (
                    <div className="text-center py-8">
                      <p className="text-gray-600">No types created yet</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {types.map(type => (
                        <div key={type.id} className="border rounded-lg p-4 flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-3xl">{type.icon}</span>
                              <div>
                                <h4 className="font-semibold text-lg">{type.name}</h4>
                                <p className="text-sm text-gray-600">{type.description}</p>
                              </div>
                              {!type.is_active && <Badge variant="secondary">Inactive</Badge>}
                            </div>
                            <div className="grid grid-cols-3 gap-4 text-sm mt-3">
                              <div>
                                <span className="text-gray-600">Time Limit:</span>
                                <span className="ml-2 font-semibold">{type.time_limit_days} days</span>
                              </div>
                              <div>
                                <span className="text-gray-600">Visit Limit:</span>
                                <span className="ml-2 font-semibold">{type.visit_limit} visits</span>
                              </div>
                              <div>
                                <span className="text-gray-600">Alert After:</span>
                                <span className="ml-2 font-semibold">{type.no_access_alert_days} days</span>
                              </div>
                            </div>
                            <div className="text-sm mt-2">
                              <span className="text-gray-600">Notify on visits:</span>
                              <span className="ml-2 font-semibold">{type.notification_on_visits.join(', ')}</span>
                            </div>
                          </div>
                          <div className="flex gap-2 ml-4">
                            <Button size="sm" variant="outline" onClick={() => handleEditType(type)}>
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => handleDeleteType(type.id)}>
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="create">
                  <form onSubmit={handleCreateType} className="space-y-4">
                    <div>
                      <Label>Name *</Label>
                      <Input
                        value={typeForm.name}
                        onChange={(e) => setTypeForm({ ...typeForm, name: e.target.value })}
                        placeholder="e.g., 3-Day Trial, Week Pass"
                        required
                      />
                    </div>

                    <div>
                      <Label>Description</Label>
                      <Textarea
                        value={typeForm.description}
                        onChange={(e) => setTypeForm({ ...typeForm, description: e.target.value })}
                        placeholder="Brief description of this pass type"
                        rows={2}
                      />
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <Label>Time Limit (Days) *</Label>
                        <Input
                          type="number"
                          min="1"
                          value={typeForm.time_limit_days}
                          onChange={(e) => setTypeForm({ ...typeForm, time_limit_days: parseInt(e.target.value) })}
                          required
                        />
                      </div>
                      <div>
                        <Label>Visit Limit *</Label>
                        <Input
                          type="number"
                          min="1"
                          value={typeForm.visit_limit}
                          onChange={(e) => setTypeForm({ ...typeForm, visit_limit: parseInt(e.target.value) })}
                          required
                        />
                      </div>
                      <div>
                        <Label>Alert After (Days) *</Label>
                        <Input
                          type="number"
                          min="1"
                          value={typeForm.no_access_alert_days}
                          onChange={(e) => setTypeForm({ ...typeForm, no_access_alert_days: parseInt(e.target.value) })}
                          required
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Icon</Label>
                        <Input
                          value={typeForm.icon}
                          onChange={(e) => setTypeForm({ ...typeForm, icon: e.target.value })}
                          placeholder="🎁"
                        />
                      </div>
                      <div>
                        <Label>Color</Label>
                        <Input
                          type="color"
                          value={typeForm.color}
                          onChange={(e) => setTypeForm({ ...typeForm, color: e.target.value })}
                        />
                      </div>
                    </div>

                    <div>
                      <Label>Notify Consultant on Visits (comma separated)</Label>
                      <Input
                        value={typeForm.notification_on_visits.join(',')}
                        onChange={(e) => setTypeForm({ 
                          ...typeForm, 
                          notification_on_visits: e.target.value.split(',').map(v => parseInt(v.trim())).filter(v => !isNaN(v))
                        })}
                        placeholder="1,2,3"
                      />
                      <p className="text-xs text-gray-600 mt-1">Consultant will be notified when member completes these visit numbers</p>
                    </div>

                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        id="is_active"
                        checked={typeForm.is_active}
                        onChange={(e) => setTypeForm({ ...typeForm, is_active: e.target.checked })}
                        className="w-4 h-4"
                      />
                      <Label htmlFor="is_active" className="cursor-pointer">Active (available for use)</Label>
                    </div>

                    <div className="flex justify-end gap-2 pt-4">
                      <Button 
                        type="button" 
                        variant="outline" 
                        onClick={() => {
                          setSelectedType(null);
                          setTypeForm({
                            name: '',
                            description: '',
                            time_limit_days: 7,
                            visit_limit: 3,
                            no_access_alert_days: 3,
                            notification_on_visits: [1, 2, 3],
                            is_active: true,
                            color: '#3b82f6',
                            icon: '🎁'
                          });
                        }}
                      >
                        Cancel
                      </Button>
                      <Button type="submit">
                        <Plus className="w-4 h-4 mr-2" />
                        {selectedType ? 'Update Type' : 'Create Type'}
                      </Button>
                    </div>
                  </form>
                </TabsContent>
              </Tabs>
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </div>
  );
}
