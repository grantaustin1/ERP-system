import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Users, UserCheck, Ban, FileText, TrendingUp, Activity, AlertCircle, AlertTriangle, CheckCircle, RefreshCw, Send, Mail, MessageSquare, Smartphone, Bell } from 'lucide-react';
import { toast } from 'sonner';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [alertData, setAlertData] = useState(null);
  const [alertsLoading, setAlertsLoading] = useState(true);
  const [generatingMockData, setGeneratingMockData] = useState(false);
  const [notificationDialogOpen, setNotificationDialogOpen] = useState(false);
  const [selectedAlertLevel, setSelectedAlertLevel] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [selectedChannels, setSelectedChannels] = useState([]);
  const [sending, setSending] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchStats();
    fetchAlertData();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setStats(response.data);
    } catch (error) {
      toast.error('Failed to fetch dashboard stats');
    } finally {
      setLoading(false);
    }
  };

  const fetchAlertData = async () => {
    try {
      const response = await axios.get(`${API}/member-access/stats`);
      setAlertData(response.data);
    } catch (error) {
      console.error('Failed to fetch alert data:', error);
    } finally {
      setAlertsLoading(false);
    }
  };

  const generateMockData = async () => {
    setGeneratingMockData(true);
    try {
      await axios.post(`${API}/member-access/generate-mock-data`);
      toast.success('Mock access data generated successfully');
      await fetchAlertData();
    } catch (error) {
      toast.error('Failed to generate mock data');
    } finally {
      setGeneratingMockData(false);
    }
  };

  const openNotificationDialog = async (alertLevel) => {
    setSelectedAlertLevel(alertLevel);
    // Fetch templates
    try {
      const response = await axios.post(`${API}/notification-templates/seed-defaults`);
      const templatesRes = await axios.get(`${API}/notification-templates?category=${alertLevel}_alert`);
      setTemplates(templatesRes.data.templates || []);
      setNotificationDialogOpen(true);
    } catch (error) {
      toast.error('Failed to load notification templates');
    }
  };

  const sendBulkNotification = async () => {
    if (!selectedTemplate) {
      toast.error('Please select a template');
      return;
    }
    if (selectedChannels.length === 0) {
      toast.error('Please select at least one channel');
      return;
    }

    setSending(true);
    try {
      const response = await axios.post(`${API}/send-bulk-notification`, {
        template_id: selectedTemplate,
        alert_level: selectedAlertLevel,
        channels: selectedChannels
      });

      toast.success(response.data.message);
      setNotificationDialogOpen(false);
      setSelectedTemplate('');
      setSelectedChannels([]);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send notifications');
    } finally {
      setSending(false);
    }
  };

  const toggleChannel = (channel) => {
    setSelectedChannels(prev => 
      prev.includes(channel) 
        ? prev.filter(c => c !== channel)
        : [...prev, channel]
    );
  };

  const statCards = [
    { title: 'Total Members', value: stats?.total_members || 0, icon: Users, color: 'from-blue-500 to-cyan-600' },
    { title: 'Active Members', value: stats?.active_members || 0, icon: UserCheck, color: 'from-emerald-500 to-teal-600' },
    { title: 'Blocked Members', value: stats?.blocked_members || 0, icon: Ban, color: 'from-red-500 to-orange-600' },
    { title: 'Pending Invoices', value: stats?.pending_invoices || 0, icon: FileText, color: 'from-amber-500 to-yellow-600' },
    { title: 'Total Revenue', value: `R ${stats?.total_revenue?.toFixed(2) || 0}`, icon: TrendingUp, color: 'from-purple-500 to-pink-600' },
    { title: "Today's Access", value: stats?.today_access_count || 0, icon: Activity, color: 'from-indigo-500 to-blue-600' },
  ];

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-white mb-2" data-testid="dashboard-title">Dashboard</h1>
            <p className="text-slate-400">Welcome to GymAccess Hub Management System</p>
          </div>

          {loading ? (
            <div className="text-center text-slate-400 py-12">Loading stats...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {statCards.map((stat, index) => {
                const Icon = stat.icon;
                return (
                  <Card key={index} className="bg-slate-800/50 border-slate-700 backdrop-blur-lg hover:bg-slate-800/70 transition-all duration-300" data-testid={`stat-card-${index}`}>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-sm font-medium text-slate-400">{stat.title}</CardTitle>
                      <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${stat.color} flex items-center justify-center`}>
                        <Icon className="w-5 h-5 text-white" />
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold text-white">{stat.value}</div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}

          <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
              <CardHeader>
                <CardTitle className="text-white">Quick Actions</CardTitle>
                <CardDescription className="text-slate-400">Manage your gym operations</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <button
                  onClick={() => navigate('/members')}
                  className="w-full text-left p-4 rounded-lg bg-slate-700/50 hover:bg-slate-700 transition-colors text-white"
                  data-testid="quick-action-members"
                >
                  <Users className="inline-block w-5 h-5 mr-3 text-emerald-400" />
                  Manage Members
                </button>
                <button
                  onClick={() => navigate('/access')}
                  className="w-full text-left p-4 rounded-lg bg-slate-700/50 hover:bg-slate-700 transition-colors text-white"
                  data-testid="quick-action-access"
                >
                  <Activity className="inline-block w-5 h-5 mr-3 text-blue-400" />
                  Access Control
                </button>
                <button
                  onClick={() => navigate('/billing')}
                  className="w-full text-left p-4 rounded-lg bg-slate-700/50 hover:bg-slate-700 transition-colors text-white"
                  data-testid="quick-action-billing"
                >
                  <FileText className="inline-block w-5 h-5 mr-3 text-purple-400" />
                  Billing & Invoices
                </button>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
              <CardHeader>
                <CardTitle className="text-white">System Overview</CardTitle>
                <CardDescription className="text-slate-400">Real-time gym statistics</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Active Rate</span>
                    <span className="text-white font-semibold">
                      {stats?.total_members > 0 ? ((stats?.active_members / stats?.total_members) * 100).toFixed(1) : 0}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-emerald-500 to-teal-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${stats?.total_members > 0 ? (stats?.active_members / stats?.total_members) * 100 : 0}%` }}
                    ></div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Member Engagement Alerts */}
          <div className="mt-8">
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-white">Member Engagement Alerts</CardTitle>
                    <CardDescription className="text-slate-400">
                      Track member activity based on {alertData?.config?.days_period || 30}-day access patterns
                    </CardDescription>
                  </div>
                  <Button 
                    onClick={generateMockData}
                    disabled={generatingMockData}
                    size="sm"
                    variant="outline"
                    className="border-slate-600 text-slate-300"
                  >
                    {generatingMockData ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      'Generate Mock Data'
                    )}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {alertsLoading ? (
                  <div className="text-center text-slate-400 py-8">Loading engagement data...</div>
                ) : (
                  <>
                    {/* Alert Summary */}
                    <div className="grid grid-cols-3 gap-4 mb-6">
                      <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <CheckCircle className="w-5 h-5 text-green-400" />
                          <span className="text-sm text-green-400 font-semibold">Highly Engaged</span>
                        </div>
                        <div className="text-3xl font-bold text-white">{alertData?.summary?.green_count || 0}</div>
                        <p className="text-xs text-slate-400 mt-1">≥ {alertData?.config?.green_threshold} visits</p>
                      </div>

                      <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <AlertTriangle className="w-5 h-5 text-amber-400" />
                          <span className="text-sm text-amber-400 font-semibold">Moderately Engaged</span>
                        </div>
                        <div className="text-3xl font-bold text-white">{alertData?.summary?.amber_count || 0}</div>
                        <p className="text-xs text-slate-400 mt-1">{alertData?.config?.amber_range} visits</p>
                      </div>

                      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <AlertCircle className="w-5 h-5 text-red-400" />
                          <span className="text-sm text-red-400 font-semibold">At Risk</span>
                        </div>
                        <div className="text-3xl font-bold text-white">{alertData?.summary?.red_count || 0}</div>
                        <p className="text-xs text-slate-400 mt-1">0 visits</p>
                      </div>
                    </div>

                    {/* Member Lists by Alert Level */}
                    <Tabs defaultValue="green" className="w-full">
                      <TabsList className="grid w-full grid-cols-3 bg-slate-700/50">
                        <TabsTrigger value="green" className="data-[state=active]:bg-green-500">
                          <CheckCircle className="w-4 h-4 mr-2" />
                          Green ({alertData?.summary?.green_count || 0})
                        </TabsTrigger>
                        <TabsTrigger value="amber" className="data-[state=active]:bg-amber-500">
                          <AlertTriangle className="w-4 h-4 mr-2" />
                          Amber ({alertData?.summary?.amber_count || 0})
                        </TabsTrigger>
                        <TabsTrigger value="red" className="data-[state=active]:bg-red-500">
                          <AlertCircle className="w-4 h-4 mr-2" />
                          Red ({alertData?.summary?.red_count || 0})
                        </TabsTrigger>
                      </TabsList>

                      <TabsContent value="green" className="mt-4">
                        <div className="flex justify-between items-center mb-4">
                          <p className="text-sm text-slate-400">
                            {alertData?.green_members?.length || 0} highly engaged members
                          </p>
                          <Button
                            onClick={() => openNotificationDialog('green')}
                            size="sm"
                            className="bg-green-600 hover:bg-green-700"
                          >
                            <Send className="w-4 h-4 mr-2" />
                            Send Notification
                          </Button>
                        </div>
                        <div className="space-y-2 max-h-96 overflow-y-auto">
                          {alertData?.green_members?.length > 0 ? (
                            alertData.green_members.map((member) => (
                              <div key={member.id} className="flex items-center justify-between p-3 bg-green-500/5 border border-green-500/20 rounded-lg">
                                <div className="flex-1">
                                  <div className="font-medium text-white">
                                    {member.first_name} {member.last_name}
                                  </div>
                                  <div className="text-sm text-slate-400">{member.email}</div>
                                </div>
                                <div className="text-right">
                                  <Badge className="bg-green-500/20 text-green-400 border-green-500/50">
                                    {member.access_count} visits
                                  </Badge>
                                  <div className="text-xs text-slate-400 mt-1">
                                    Last: {member.days_since_last_access} days ago
                                  </div>
                                </div>
                              </div>
                            ))
                          ) : (
                            <div className="text-center text-slate-400 py-8">No members in this category</div>
                          )}
                        </div>
                      </TabsContent>

                      <TabsContent value="amber" className="mt-4">
                        <div className="flex justify-between items-center mb-4">
                          <p className="text-sm text-slate-400">
                            {alertData?.amber_members?.length || 0} moderately engaged members
                          </p>
                          <Button
                            onClick={() => openNotificationDialog('amber')}
                            size="sm"
                            className="bg-amber-600 hover:bg-amber-700"
                          >
                            <Send className="w-4 h-4 mr-2" />
                            Send Notification
                          </Button>
                        </div>
                        <div className="space-y-2 max-h-96 overflow-y-auto">
                          {alertData?.amber_members?.length > 0 ? (
                            alertData.amber_members.map((member) => (
                              <div key={member.id} className="flex items-center justify-between p-3 bg-amber-500/5 border border-amber-500/20 rounded-lg">
                                <div className="flex-1">
                                  <div className="font-medium text-white">
                                    {member.first_name} {member.last_name}
                                  </div>
                                  <div className="text-sm text-slate-400">{member.email}</div>
                                </div>
                                <div className="text-right">
                                  <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/50">
                                    {member.access_count} visits
                                  </Badge>
                                  <div className="text-xs text-slate-400 mt-1">
                                    Last: {member.days_since_last_access} days ago
                                  </div>
                                </div>
                              </div>
                            ))
                          ) : (
                            <div className="text-center text-slate-400 py-8">No members in this category</div>
                          )}
                        </div>
                      </TabsContent>

                      <TabsContent value="red" className="mt-4">
                        <div className="space-y-2 max-h-96 overflow-y-auto">
                          {alertData?.red_members?.length > 0 ? (
                            alertData.red_members.map((member) => (
                              <div key={member.id} className="flex items-center justify-between p-3 bg-red-500/5 border border-red-500/20 rounded-lg">
                                <div className="flex-1">
                                  <div className="font-medium text-white">
                                    {member.first_name} {member.last_name}
                                  </div>
                                  <div className="text-sm text-slate-400">{member.email}</div>
                                </div>
                                <div className="text-right">
                                  <Badge className="bg-red-500/20 text-red-400 border-red-500/50">
                                    0 visits
                                  </Badge>
                                  <div className="text-xs text-slate-400 mt-1">
                                    No activity in {alertData?.config?.days_period} days
                                  </div>
                                </div>
                              </div>
                            ))
                          ) : (
                            <div className="text-center text-slate-400 py-8">No members in this category</div>
                          )}
                        </div>
                      </TabsContent>
                    </Tabs>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}