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
  
  // Class booking drill-down state
  const [classBookingStats, setClassBookingStats] = useState(null);
  const [drillDownLevel, setDrillDownLevel] = useState(1); // 1=overview, 2=class list, 3=member list
  const [selectedClassForDrillDown, setSelectedClassForDrillDown] = useState(null);
  const [classBookings, setClassBookings] = useState([]);
  
  const navigate = useNavigate();

  useEffect(() => {
    fetchStats();
    fetchAlertData();
    fetchClassBookingStats();
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

  const fetchClassBookingStats = async () => {
    try {
      // Fetch all classes
      const classesResponse = await axios.get(`${API}/classes`);
      const classes = classesResponse.data;
      
      // Fetch all bookings
      const bookingsResponse = await axios.get(`${API}/bookings`);
      const bookings = bookingsResponse.data;
      
      // Calculate aggregate stats
      let totalCapacity = 0;
      let totalBooked = 0;
      let totalAvailable = 0;
      
      const classStats = classes.map(cls => {
        const classBookings = bookings.filter(b => b.class_id === cls.id);
        const confirmedCount = classBookings.filter(b => b.status === 'confirmed' || b.status === 'attended').length;
        const waitlistCount = classBookings.filter(b => b.status === 'waitlist').length;
        const available = Math.max(0, cls.capacity - confirmedCount);
        
        totalCapacity += cls.capacity;
        totalBooked += confirmedCount;
        totalAvailable += available;
        
        return {
          ...cls,
          confirmedCount,
          waitlistCount,
          available,
          bookings: classBookings
        };
      });
      
      setClassBookingStats({
        totalCapacity,
        totalBooked,
        totalAvailable,
        utilizationRate: totalCapacity > 0 ? ((totalBooked / totalCapacity) * 100).toFixed(1) : 0,
        classes: classStats
      });
      
    } catch (error) {
      console.error('Failed to fetch class booking stats:', error);
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
                        <div className="flex justify-between items-center mb-4">
                          <p className="text-sm text-slate-400">
                            {alertData?.red_members?.length || 0} at-risk members
                          </p>
                          <Button
                            onClick={() => openNotificationDialog('red')}
                            size="sm"
                            className="bg-red-600 hover:bg-red-700"
                          >
                            <Send className="w-4 h-4 mr-2" />
                            Send Notification
                          </Button>
                        </div>
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

          {/* Class Booking Overview */}
          <div className="mt-8">
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle className="text-white">Class Booking Overview</CardTitle>
                    <CardDescription className="text-slate-400">
                      {drillDownLevel === 1 && 'Total capacity utilization across all classes'}
                      {drillDownLevel === 2 && 'Booking details by class'}
                      {drillDownLevel === 3 && `Members booked for ${selectedClassForDrillDown?.name}`}
                    </CardDescription>
                  </div>
                  {drillDownLevel > 1 && (
                    <Button
                      onClick={() => {
                        if (drillDownLevel === 3) {
                          setDrillDownLevel(2);
                          setSelectedClassForDrillDown(null);
                        } else if (drillDownLevel === 2) {
                          setDrillDownLevel(1);
                        }
                      }}
                      variant="outline"
                      className="border-slate-600 text-slate-300"
                    >
                      ← Back
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {!classBookingStats ? (
                  <div className="text-center py-8 text-slate-400">Loading class booking data...</div>
                ) : (
                  <>
                    {/* Level 1: Overview */}
                    {drillDownLevel === 1 && (
                      <div className="space-y-6">
                        {/* Summary Stats */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <div className="bg-slate-700/50 p-4 rounded-lg">
                            <p className="text-sm text-slate-400">Total Capacity</p>
                            <p className="text-3xl font-bold text-white">{classBookingStats.totalCapacity}</p>
                          </div>
                          <div className="bg-green-500/10 p-4 rounded-lg border border-green-500/30">
                            <p className="text-sm text-green-400">Booked Slots</p>
                            <p className="text-3xl font-bold text-green-400">{classBookingStats.totalBooked}</p>
                          </div>
                          <div className="bg-blue-500/10 p-4 rounded-lg border border-blue-500/30">
                            <p className="text-sm text-blue-400">Available Slots</p>
                            <p className="text-3xl font-bold text-blue-400">{classBookingStats.totalAvailable}</p>
                          </div>
                          <div className="bg-purple-500/10 p-4 rounded-lg border border-purple-500/30">
                            <p className="text-sm text-purple-400">Utilization Rate</p>
                            <p className="text-3xl font-bold text-purple-400">{classBookingStats.utilizationRate}%</p>
                          </div>
                        </div>

                        {/* Visual Progress Bar */}
                        <div>
                          <div className="flex justify-between text-sm mb-2">
                            <span className="text-slate-400">Overall Capacity Utilization</span>
                            <span className="text-white font-semibold">
                              {classBookingStats.totalBooked} / {classBookingStats.totalCapacity}
                            </span>
                          </div>
                          <div className="w-full bg-slate-700 rounded-full h-4">
                            <div
                              className="bg-gradient-to-r from-green-500 to-emerald-600 h-4 rounded-full transition-all"
                              style={{ width: `${Math.min(classBookingStats.utilizationRate, 100)}%` }}
                            ></div>
                          </div>
                        </div>

                        {/* Drill Down Button */}
                        <div className="text-center">
                          <Button
                            onClick={() => setDrillDownLevel(2)}
                            className="bg-emerald-600 hover:bg-emerald-700"
                          >
                            View Class Details →
                          </Button>
                        </div>
                      </div>
                    )}

                    {/* Level 2: Class List */}
                    {drillDownLevel === 2 && (
                      <div className="space-y-4">
                        {classBookingStats.classes
                          .filter(cls => cls.confirmedCount > 0 || cls.waitlistCount > 0)
                          .map(cls => (
                            <div
                              key={cls.id}
                              className="bg-slate-700/50 p-4 rounded-lg hover:bg-slate-700 transition-colors cursor-pointer"
                              onClick={() => {
                                setSelectedClassForDrillDown(cls);
                                setDrillDownLevel(3);
                              }}
                            >
                              <div className="flex justify-between items-start">
                                <div className="flex-1">
                                  <h3 className="text-lg font-semibold text-white">{cls.name}</h3>
                                  <p className="text-sm text-slate-400">
                                    {cls.class_type} • {cls.duration_minutes} min
                                    {cls.is_recurring && ` • ${cls.day_of_week} ${cls.start_time}`}
                                  </p>
                                </div>
                                <div className="text-right">
                                  <Badge className={cls.confirmedCount >= cls.capacity ? 'bg-red-500' : 'bg-green-500'}>
                                    {cls.confirmedCount >= cls.capacity ? 'FULL' : 'Available'}
                                  </Badge>
                                </div>
                              </div>

                              <div className="mt-3">
                                <div className="flex justify-between text-sm mb-1">
                                  <span className="text-slate-400">Capacity</span>
                                  <span className="text-white">{cls.confirmedCount} / {cls.capacity}</span>
                                </div>
                                <div className="w-full bg-slate-600 rounded-full h-2">
                                  <div
                                    className={`h-2 rounded-full ${
                                      cls.confirmedCount >= cls.capacity
                                        ? 'bg-red-500'
                                        : cls.confirmedCount >= cls.capacity * 0.8
                                        ? 'bg-yellow-500'
                                        : 'bg-green-500'
                                    }`}
                                    style={{ width: `${Math.min((cls.confirmedCount / cls.capacity) * 100, 100)}%` }}
                                  ></div>
                                </div>
                              </div>

                              <div className="mt-3 grid grid-cols-3 gap-2 text-center">
                                <div className="bg-green-500/10 p-2 rounded">
                                  <p className="text-xs text-slate-400">Confirmed</p>
                                  <p className="text-lg font-bold text-green-400">{cls.confirmedCount}</p>
                                </div>
                                <div className="bg-yellow-500/10 p-2 rounded">
                                  <p className="text-xs text-slate-400">Waitlist</p>
                                  <p className="text-lg font-bold text-yellow-400">{cls.waitlistCount}</p>
                                </div>
                                <div className="bg-blue-500/10 p-2 rounded">
                                  <p className="text-xs text-slate-400">Available</p>
                                  <p className="text-lg font-bold text-blue-400">{cls.available}</p>
                                </div>
                              </div>

                              <div className="mt-3 text-right">
                                <span className="text-sm text-emerald-400 hover:text-emerald-300">
                                  Click to view members →
                                </span>
                              </div>
                            </div>
                          ))}

                        {classBookingStats.classes.filter(cls => cls.confirmedCount > 0 || cls.waitlistCount > 0).length === 0 && (
                          <div className="text-center py-12 text-slate-400">
                            <Users className="w-16 h-16 mx-auto mb-4 opacity-50" />
                            <p>No classes with bookings yet</p>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Level 3: Member List */}
                    {drillDownLevel === 3 && selectedClassForDrillDown && (
                      <div className="space-y-4">
                        {/* Class Info Header */}
                        <div className="bg-slate-700/50 p-4 rounded-lg">
                          <h3 className="text-xl font-bold text-white">{selectedClassForDrillDown.name}</h3>
                          <p className="text-slate-400">
                            {selectedClassForDrillDown.class_type} • {selectedClassForDrillDown.duration_minutes} min
                          </p>
                          <div className="mt-2 flex gap-4 text-sm">
                            <span className="text-slate-300">
                              <strong>Capacity:</strong> {selectedClassForDrillDown.confirmedCount} / {selectedClassForDrillDown.capacity}
                            </span>
                            <span className="text-slate-300">
                              <strong>Waitlist:</strong> {selectedClassForDrillDown.waitlistCount}
                            </span>
                          </div>
                        </div>

                        {/* Member List */}
                        <div className="space-y-2">
                          {selectedClassForDrillDown.bookings
                            .sort((a, b) => {
                              const statusOrder = { confirmed: 1, attended: 2, waitlist: 3, cancelled: 4 };
                              return statusOrder[a.status] - statusOrder[b.status];
                            })
                            .map(booking => (
                              <div
                                key={booking.id}
                                className="flex justify-between items-center p-3 bg-slate-700/50 rounded-lg hover:bg-slate-700"
                              >
                                <div>
                                  <p className="font-semibold text-white">{booking.member_name}</p>
                                  <p className="text-sm text-slate-400">
                                    Booked: {new Date(booking.booked_at).toLocaleDateString()}
                                  </p>
                                </div>
                                <Badge
                                  className={
                                    booking.status === 'confirmed'
                                      ? 'bg-green-500'
                                      : booking.status === 'attended'
                                      ? 'bg-blue-500'
                                      : booking.status === 'waitlist'
                                      ? 'bg-yellow-500'
                                      : 'bg-gray-500'
                                  }
                                >
                                  {booking.status}
                                  {booking.is_waitlist && ` (#${booking.waitlist_position})`}
                                </Badge>
                              </div>
                            ))}

                          {selectedClassForDrillDown.bookings.length === 0 && (
                            <div className="text-center py-8 text-slate-400">
                              No bookings for this class
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Notification Dialog */}
          <Dialog open={notificationDialogOpen} onOpenChange={setNotificationDialogOpen}>
            <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-2xl">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Send className="w-5 h-5" />
                  Send Bulk Notification - {selectedAlertLevel?.toUpperCase()} Alert
                </DialogTitle>
                <DialogDescription className="text-slate-400">
                  Send notifications to all members in this alert category
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4">
                {/* Template Selection */}
                <div>
                  <Label className="text-white">Select Message Template</Label>
                  <Select value={selectedTemplate} onValueChange={setSelectedTemplate}>
                    <SelectTrigger className="bg-slate-700 border-slate-600 text-white mt-2">
                      <SelectValue placeholder="Choose a template" />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-800 border-slate-700">
                      {templates.map((template) => (
                        <SelectItem key={template.id} value={template.id} className="text-white">
                          {template.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Template Preview */}
                {selectedTemplate && templates.find(t => t.id === selectedTemplate) && (
                  <div className="bg-slate-700/50 border border-slate-600 rounded-lg p-4">
                    <Label className="text-sm text-slate-400">Preview:</Label>
                    <div className="mt-2 space-y-2">
                      {templates.find(t => t.id === selectedTemplate).subject && (
                        <div>
                          <span className="text-xs text-slate-400">Subject:</span>
                          <p className="text-sm text-white">{templates.find(t => t.id === selectedTemplate).subject}</p>
                        </div>
                      )}
                      <div>
                        <span className="text-xs text-slate-400">Message:</span>
                        <p className="text-sm text-white whitespace-pre-wrap">
                          {templates.find(t => t.id === selectedTemplate).message}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Channel Selection */}
                <div>
                  <Label className="text-white mb-2 block">Notification Channels</Label>
                  <div className="grid grid-cols-2 gap-3">
                    <div
                      onClick={() => toggleChannel('email')}
                      className={`flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedChannels.includes('email')
                          ? 'bg-emerald-500/20 border-emerald-500'
                          : 'bg-slate-700/50 border-slate-600 hover:border-slate-500'
                      }`}
                    >
                      <Checkbox checked={selectedChannels.includes('email')} />
                      <Mail className="w-4 h-4" />
                      <span>Email</span>
                    </div>

                    <div
                      onClick={() => toggleChannel('whatsapp')}
                      className={`flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedChannels.includes('whatsapp')
                          ? 'bg-emerald-500/20 border-emerald-500'
                          : 'bg-slate-700/50 border-slate-600 hover:border-slate-500'
                      }`}
                    >
                      <Checkbox checked={selectedChannels.includes('whatsapp')} />
                      <MessageSquare className="w-4 h-4" />
                      <span>WhatsApp</span>
                    </div>

                    <div
                      onClick={() => toggleChannel('sms')}
                      className={`flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedChannels.includes('sms')
                          ? 'bg-emerald-500/20 border-emerald-500'
                          : 'bg-slate-700/50 border-slate-600 hover:border-slate-500'
                      }`}
                    >
                      <Checkbox checked={selectedChannels.includes('sms')} />
                      <Smartphone className="w-4 h-4" />
                      <span>SMS</span>
                    </div>

                    <div
                      onClick={() => toggleChannel('push')}
                      className={`flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedChannels.includes('push')
                          ? 'bg-emerald-500/20 border-emerald-500'
                          : 'bg-slate-700/50 border-slate-600 hover:border-slate-500'
                      }`}
                    >
                      <Checkbox checked={selectedChannels.includes('push')} />
                      <Bell className="w-4 h-4" />
                      <span>Push Notification</span>
                    </div>
                  </div>
                </div>

                {/* Summary */}
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
                  <p className="text-sm text-slate-300">
                    <strong>Recipients:</strong> {
                      selectedAlertLevel === 'green' ? alertData?.summary?.green_count :
                      selectedAlertLevel === 'amber' ? alertData?.summary?.amber_count :
                      alertData?.summary?.red_count
                    } members
                  </p>
                  <p className="text-sm text-slate-300">
                    <strong>Channels:</strong> {selectedChannels.length > 0 ? selectedChannels.join(', ') : 'None selected'}
                  </p>
                  <p className="text-xs text-slate-400 mt-2">
                    Note: This is currently in mock mode. Integrate with actual services for production.
                  </p>
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-2 pt-4">
                  <Button
                    onClick={() => setNotificationDialogOpen(false)}
                    variant="outline"
                    className="border-slate-600 text-slate-300"
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={sendBulkNotification}
                    disabled={sending || !selectedTemplate || selectedChannels.length === 0}
                    className="bg-emerald-600 hover:bg-emerald-700"
                  >
                    {sending ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        Sending...
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4 mr-2" />
                        Send to {
                          selectedAlertLevel === 'green' ? alertData?.summary?.green_count :
                          selectedAlertLevel === 'amber' ? alertData?.summary?.amber_count :
                          alertData?.summary?.red_count
                        } Members
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </div>
  );
}