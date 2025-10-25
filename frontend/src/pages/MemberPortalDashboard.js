import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import {
  User,
  Bell,
  Calendar,
  DollarSign,
  TrendingUp,
  Activity,
  Award,
  CreditCard,
  Clock,
  CheckCircle,
  AlertCircle,
  Settings
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

export default function MemberPortalDashboard() {
  const [dashboardData, setDashboardData] = useState(null);
  const [workoutHistory, setWorkoutHistory] = useState([]);
  const [attendanceStats, setAttendanceStats] = useState(null);
  const [paymentHistory, setPaymentHistory] = useState(null);
  const [milestones, setMilestones] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // For demo, use first member or logged-in member
  const memberId = 'demo-member-id'; // Replace with actual logged-in member ID

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [dashboard, workout, attendance, payments, achievements, notifs] = await Promise.all([
        axios.get(`${API}/member-portal/dashboard/${memberId}`),
        axios.get(`${API}/member-portal/workout-history/${memberId}`),
        axios.get(`${API}/member-portal/attendance-stats/${memberId}`),
        axios.get(`${API}/member-portal/payment-history/${memberId}`),
        axios.get(`${API}/member-portal/milestones/${memberId}`),
        axios.get(`${API}/notifications/member/${memberId}?limit=10`)
      ]);
      
      setDashboardData(dashboard.data);
      setWorkoutHistory(workout.data.workout_history || []);
      setAttendanceStats(attendance.data);
      setPaymentHistory(payments.data);
      setMilestones(achievements.data.milestones || []);
      setNotifications(notifs.data.notifications || []);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      toast.error('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const markNotificationRead = async (notificationId) => {
    try {
      await axios.put(`${API}/notifications/${notificationId}/read`);
      setNotifications(notifications.map(n => 
        n.id === notificationId ? { ...n, status: 'read', read_at: new Date().toISOString() } : n
      ));
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR' }).format(amount);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-ZA', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const getStatusBadge = (status) => {
    const config = {
      active: { label: 'Active', className: 'bg-green-600 text-white' },
      inactive: { label: 'Inactive', className: 'bg-gray-500 text-white' },
      suspended: { label: 'Suspended', className: 'bg-red-600 text-white' },
      paid: { label: 'Paid', className: 'bg-green-600 text-white' },
      pending: { label: 'Pending', className: 'bg-yellow-600 text-white' },
      overdue: { label: 'Overdue', className: 'bg-red-600 text-white' }
    };
    const { label, className } = config[status] || { label: status, className: 'bg-gray-500 text-white' };
    return <Badge className={className}>{label}</Badge>;
  };

  if (loading && !dashboardData) {
    return (
      <div className="flex h-screen bg-gray-50">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading your dashboard...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 overflow-auto">
        <div className="p-8">
          {/* Header */}
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
                <User className="w-8 h-8 text-blue-600" />
                Welcome, {dashboardData?.member?.member_name || 'Member'}!
              </h1>
              <p className="text-gray-600 mt-1">Your personal fitness dashboard</p>
            </div>
            <Button variant="outline">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </Button>
          </div>

          {dashboardData && (
            <>
              {/* Quick Stats */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <Card>
                  <CardHeader className="pb-2">
                    <CardDescription>Membership Status</CardDescription>
                    <CardTitle className="text-2xl">
                      {getStatusBadge(dashboardData.member.status)}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-sm text-gray-600">
                      {dashboardData.member.membership_type}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardDescription>Total Visits</CardDescription>
                    <CardTitle className="text-3xl text-blue-600">
                      {dashboardData.stats.total_visits}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center text-sm text-gray-600">
                      <Activity className="w-4 h-4 mr-1" />
                      Keep it up!
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardDescription>Last Visit</CardDescription>
                    <CardTitle className="text-3xl text-green-600">
                      {dashboardData.stats.days_since_last_visit}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-sm text-gray-600">days ago</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardDescription>Notifications</CardDescription>
                    <CardTitle className="text-3xl text-orange-600">
                      {dashboardData.stats.unread_notifications}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center text-sm text-gray-600">
                      <Bell className="w-4 h-4 mr-1" />
                      Unread messages
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Tabs defaultValue="overview" className="space-y-6">
                <TabsList>
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="attendance">Attendance</TabsTrigger>
                  <TabsTrigger value="payments">Payments</TabsTrigger>
                  <TabsTrigger value="notifications">Notifications</TabsTrigger>
                  <TabsTrigger value="milestones">Milestones</TabsTrigger>
                </TabsList>

                {/* Overview Tab */}
                <TabsContent value="overview" className="space-y-6">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Membership Info */}
                    <Card>
                      <CardHeader>
                        <CardTitle>Membership Information</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Member Since:</span>
                            <span className="font-semibold">{formatDate(dashboardData.member.join_date)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Plan Type:</span>
                            <span className="font-semibold">{dashboardData.member.membership_type}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Status:</span>
                            {getStatusBadge(dashboardData.member.status)}
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Email:</span>
                            <span className="font-semibold">{dashboardData.member.email}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Phone:</span>
                            <span className="font-semibold">{dashboardData.member.phone}</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Upcoming Payments */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <CreditCard className="w-5 h-5" />
                          Upcoming Payments
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        {dashboardData.upcoming_payments.length === 0 ? (
                          <div className="text-center py-4 text-gray-600">
                            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-2" />
                            All payments up to date!
                          </div>
                        ) : (
                          <div className="space-y-3">
                            {dashboardData.upcoming_payments.map((payment, index) => (
                              <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                                <div>
                                  <div className="font-semibold">{formatCurrency(payment.amount)}</div>
                                  <div className="text-sm text-gray-600">Due: {formatDate(payment.due_date)}</div>
                                </div>
                                {getStatusBadge(payment.status)}
                              </div>
                            ))}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>

                  {/* Recent Invoices */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Recent Invoices</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {dashboardData.recent_invoices.length === 0 ? (
                        <div className="text-center py-8 text-gray-600">No invoices yet</div>
                      ) : (
                        <div className="overflow-x-auto">
                          <table className="w-full">
                            <thead className="border-b">
                              <tr className="text-left text-sm text-gray-600">
                                <th className="pb-3 font-semibold">Date</th>
                                <th className="pb-3 font-semibold">Amount</th>
                                <th className="pb-3 font-semibold">Status</th>
                                <th className="pb-3 font-semibold">Due Date</th>
                              </tr>
                            </thead>
                            <tbody>
                              {dashboardData.recent_invoices.map((invoice, index) => (
                                <tr key={index} className="border-b hover:bg-gray-50">
                                  <td className="py-3">{formatDate(invoice.created_at)}</td>
                                  <td className="py-3 font-semibold">{formatCurrency(invoice.amount)}</td>
                                  <td className="py-3">{getStatusBadge(invoice.status)}</td>
                                  <td className="py-3">{formatDate(invoice.due_date)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Attendance Tab */}
                <TabsContent value="attendance" className="space-y-6">
                  {attendanceStats && (
                    <>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <Card>
                          <CardHeader className="pb-2">
                            <CardDescription>Total Visits</CardDescription>
                            <CardTitle className="text-3xl">{attendanceStats.total_visits}</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="text-sm text-gray-600">Last {attendanceStats.period_days} days</div>
                          </CardContent>
                        </Card>

                        <Card>
                          <CardHeader className="pb-2">
                            <CardDescription>Avg Visits/Week</CardDescription>
                            <CardTitle className="text-3xl text-blue-600">{attendanceStats.avg_visits_per_week}</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="text-sm text-gray-600">Keep up the consistency!</div>
                          </CardContent>
                        </Card>

                        <Card>
                          <CardHeader className="pb-2">
                            <CardDescription>Current Streak</CardDescription>
                            <CardTitle className="text-3xl text-green-600">{attendanceStats.current_streak}</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="text-sm text-gray-600">days in a row</div>
                          </CardContent>
                        </Card>
                      </div>

                      <Card>
                        <CardHeader>
                          <CardTitle>Workout History</CardTitle>
                          <CardDescription>Your recent gym activities</CardDescription>
                        </CardHeader>
                        <CardContent>
                          {workoutHistory.length === 0 ? (
                            <div className="text-center py-8 text-gray-600">No workout history yet</div>
                          ) : (
                            <div className="space-y-3">
                              {workoutHistory.map((workout, index) => (
                                <div key={index} className="flex justify-between items-center p-4 border rounded-lg">
                                  <div>
                                    <div className="font-semibold">{workout.type}</div>
                                    <div className="text-sm text-gray-600">{formatDate(workout.date)}</div>
                                  </div>
                                  <div className="text-right">
                                    <div className="text-sm text-gray-600">Duration</div>
                                    <div className="font-semibold">{workout.duration}</div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    </>
                  )}
                </TabsContent>

                {/* Payments Tab */}
                <TabsContent value="payments" className="space-y-6">
                  {paymentHistory && (
                    <>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <Card>
                          <CardHeader className="pb-2">
                            <CardDescription>Total Paid</CardDescription>
                            <CardTitle className="text-3xl text-green-600">
                              {formatCurrency(paymentHistory.summary.total_paid)}
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="text-sm text-gray-600">All time</div>
                          </CardContent>
                        </Card>

                        <Card>
                          <CardHeader className="pb-2">
                            <CardDescription>Pending Amount</CardDescription>
                            <CardTitle className="text-3xl text-orange-600">
                              {formatCurrency(paymentHistory.summary.total_pending)}
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="text-sm text-gray-600">Outstanding balance</div>
                          </CardContent>
                        </Card>
                      </div>

                      <Card>
                        <CardHeader>
                          <CardTitle>Payment History</CardTitle>
                          <CardDescription>Last 12 transactions</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="overflow-x-auto">
                            <table className="w-full">
                              <thead className="border-b">
                                <tr className="text-left text-sm text-gray-600">
                                  <th className="pb-3 font-semibold">Date</th>
                                  <th className="pb-3 font-semibold">Description</th>
                                  <th className="pb-3 font-semibold">Amount</th>
                                  <th className="pb-3 font-semibold">Status</th>
                                </tr>
                              </thead>
                              <tbody>
                                {paymentHistory.invoices.map((invoice, index) => (
                                  <tr key={index} className="border-b hover:bg-gray-50">
                                    <td className="py-3">{formatDate(invoice.created_at)}</td>
                                    <td className="py-3">Invoice #{invoice.id?.slice(0, 8)}</td>
                                    <td className="py-3 font-semibold">{formatCurrency(invoice.amount)}</td>
                                    <td className="py-3">{getStatusBadge(invoice.status)}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </CardContent>
                      </Card>
                    </>
                  )}
                </TabsContent>

                {/* Notifications Tab */}
                <TabsContent value="notifications" className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Bell className="w-5 h-5" />
                        Recent Notifications
                      </CardTitle>
                      <CardDescription>Stay updated with your gym activity</CardDescription>
                    </CardHeader>
                    <CardContent>
                      {notifications.length === 0 ? (
                        <div className="text-center py-8 text-gray-600">
                          <Bell className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                          No notifications yet
                        </div>
                      ) : (
                        <div className="space-y-3">
                          {notifications.map((notification) => (
                            <div 
                              key={notification.id} 
                              className={`p-4 rounded-lg border ${notification.read_at ? 'bg-white' : 'bg-blue-50 border-blue-200'}`}
                            >
                              <div className="flex justify-between items-start">
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className="font-semibold">{notification.subject}</span>
                                    {!notification.read_at && (
                                      <Badge className="bg-blue-600 text-white">New</Badge>
                                    )}
                                  </div>
                                  <div className="text-sm text-gray-600 mb-2">{notification.message}</div>
                                  <div className="flex items-center gap-3 text-xs text-gray-500">
                                    <span className="flex items-center gap-1">
                                      <Clock className="w-3 h-3" />
                                      {formatDate(notification.created_at)}
                                    </span>
                                    <Badge variant="outline" className="capitalize">{notification.channel}</Badge>
                                  </div>
                                </div>
                                {!notification.read_at && (
                                  <Button 
                                    size="sm" 
                                    variant="ghost"
                                    onClick={() => markNotificationRead(notification.id)}
                                  >
                                    Mark as Read
                                  </Button>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Milestones Tab */}
                <TabsContent value="milestones" className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Award className="w-5 h-5 text-yellow-500" />
                        Your Achievements
                      </CardTitle>
                      <CardDescription>Celebrate your fitness journey milestones</CardDescription>
                    </CardHeader>
                    <CardContent>
                      {milestones.length === 0 ? (
                        <div className="text-center py-8 text-gray-600">
                          <Award className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                          Keep working out to unlock milestones!
                        </div>
                      ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {milestones.map((milestone, index) => (
                            <div key={index} className="p-4 border rounded-lg bg-gradient-to-br from-yellow-50 to-orange-50">
                              <div className="flex items-start gap-3">
                                <div className="text-3xl">{milestone.icon}</div>
                                <div className="flex-1">
                                  <div className="font-semibold text-lg mb-1">{milestone.title}</div>
                                  <div className="text-sm text-gray-600">{milestone.description}</div>
                                  {milestone.date && (
                                    <div className="text-xs text-gray-500 mt-2">{formatDate(milestone.date)}</div>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
