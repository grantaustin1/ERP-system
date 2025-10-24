import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  TrendingUp, 
  DollarSign, 
  MapPin, 
  Activity,
  Award,
  AlertTriangle,
  Users,
  BarChart3,
  Calendar
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  LineChart, 
  Line, 
  PieChart, 
  Pie, 
  Cell,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';
import { toast } from 'sonner';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

export default function AdvancedAnalytics() {
  const [revenueData, setRevenueData] = useState(null);
  const [geoData, setGeoData] = useState(null);
  const [attendanceData, setAttendanceData] = useState(null);
  const [ltvData, setLtvData] = useState(null);
  const [churnData, setChurnData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [revenuePeriod, setRevenuePeriod] = useState(12);
  const [attendancePeriod, setAttendancePeriod] = useState(90);

  useEffect(() => {
    fetchAllAnalytics();
  }, []);

  const fetchAllAnalytics = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchRevenueAnalytics(revenuePeriod),
        fetchGeographicDistribution(),
        fetchAttendanceDeepDive(attendancePeriod),
        fetchLifetimeValue(),
        fetchChurnPrediction()
      ]);
    } finally {
      setLoading(false);
    }
  };

  const fetchRevenueAnalytics = async (months) => {
    try {
      const response = await axios.get(`${API}/analytics/revenue-breakdown?period_months=${months}`);
      setRevenueData(response.data);
    } catch (error) {
      toast.error('Failed to fetch revenue analytics');
    }
  };

  const fetchGeographicDistribution = async () => {
    try {
      const response = await axios.get(`${API}/analytics/geographic-distribution`);
      setGeoData(response.data);
    } catch (error) {
      toast.error('Failed to fetch geographic data');
    }
  };

  const fetchAttendanceDeepDive = async (days) => {
    try {
      const response = await axios.get(`${API}/analytics/attendance-deep-dive?days_back=${days}`);
      setAttendanceData(response.data);
    } catch (error) {
      toast.error('Failed to fetch attendance analytics');
    }
  };

  const fetchLifetimeValue = async () => {
    try {
      const response = await axios.get(`${API}/analytics/member-lifetime-value`);
      setLtvData(response.data);
    } catch (error) {
      toast.error('Failed to fetch LTV data');
    }
  };

  const fetchChurnPrediction = async () => {
    try {
      const response = await axios.get(`${API}/analytics/churn-prediction`);
      setChurnData(response.data);
    } catch (error) {
      toast.error('Failed to fetch churn prediction');
    }
  };

  const getRiskColor = (level) => {
    switch (level) {
      case 'Critical': return 'bg-red-500';
      case 'High': return 'bg-orange-500';
      case 'Medium': return 'bg-yellow-500';
      default: return 'bg-blue-500';
    }
  };

  return (
    <div className="flex h-screen bg-slate-900">
      <Sidebar />
      
      <div className="flex-1 p-8 overflow-auto">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <BarChart3 className="w-8 h-8 text-blue-400" />
              Advanced Analytics
            </h1>
            <p className="text-slate-400 mt-2">
              Deep insights into revenue, attendance, member lifetime value, and churn risk
            </p>
          </div>

          {/* Tabs */}
          <Tabs defaultValue="revenue" className="space-y-6">
            <TabsList className="bg-slate-800 border-slate-700">
              <TabsTrigger value="revenue" className="data-[state=active]:bg-slate-700">
                <DollarSign className="w-4 h-4 mr-2" />
                Revenue
              </TabsTrigger>
              <TabsTrigger value="geographic" className="data-[state=active]:bg-slate-700">
                <MapPin className="w-4 h-4 mr-2" />
                Geographic
              </TabsTrigger>
              <TabsTrigger value="attendance" className="data-[state=active]:bg-slate-700">
                <Activity className="w-4 h-4 mr-2" />
                Attendance
              </TabsTrigger>
              <TabsTrigger value="ltv" className="data-[state=active]:bg-slate-700">
                <Award className="w-4 h-4 mr-2" />
                Lifetime Value
              </TabsTrigger>
              <TabsTrigger value="churn" className="data-[state=active]:bg-slate-700">
                <AlertTriangle className="w-4 h-4 mr-2" />
                Churn Risk
              </TabsTrigger>
            </TabsList>

            {/* Revenue Analytics Tab */}
            <TabsContent value="revenue" className="space-y-6">
              {revenueData && (
                <>
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader className="pb-2">
                        <CardDescription className="text-slate-400">Total Revenue</CardDescription>
                        <CardTitle className="text-2xl text-green-400">
                          R {revenueData.summary.total_revenue.toLocaleString()}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                    
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader className="pb-2">
                        <CardDescription className="text-slate-400">MRR</CardDescription>
                        <CardTitle className="text-2xl text-blue-400">
                          R {revenueData.summary.mrr.toLocaleString()}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                    
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader className="pb-2">
                        <CardDescription className="text-slate-400">ARPU</CardDescription>
                        <CardTitle className="text-2xl text-purple-400">
                          R {revenueData.summary.arpu.toLocaleString()}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                    
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader className="pb-2">
                        <CardDescription className="text-slate-400">Active Members</CardDescription>
                        <CardTitle className="text-2xl text-white">
                          {revenueData.summary.active_members}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                    
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader className="pb-2">
                        <CardDescription className="text-slate-400">Period</CardDescription>
                        <CardTitle className="text-2xl text-white">
                          {revenueData.summary.period_months} months
                        </CardTitle>
                      </CardHeader>
                    </Card>
                  </div>

                  {/* Charts */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Revenue by Membership Type */}
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader>
                        <CardTitle className="text-white">Revenue by Membership Type</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={300}>
                          <PieChart>
                            <Pie
                              data={revenueData.by_membership_type}
                              cx="50%"
                              cy="50%"
                              labelLine={false}
                              label={({ type, percentage }) => `${type}: ${percentage}%`}
                              outerRadius={100}
                              fill="#8884d8"
                              dataKey="revenue"
                            >
                              {revenueData.by_membership_type.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                              ))}
                            </Pie>
                            <Tooltip 
                              contentStyle={{ 
                                backgroundColor: '#1e293b', 
                                border: '1px solid #475569',
                                borderRadius: '8px',
                                color: '#f1f5f9'
                              }}
                            />
                          </PieChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>

                    {/* Revenue by Payment Method */}
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader>
                        <CardTitle className="text-white">Revenue by Payment Method</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={revenueData.by_payment_method}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis dataKey="method" stroke="#94a3b8" />
                            <YAxis stroke="#94a3b8" />
                            <Tooltip 
                              contentStyle={{ 
                                backgroundColor: '#1e293b', 
                                border: '1px solid #475569',
                                borderRadius: '8px',
                                color: '#f1f5f9'
                              }}
                            />
                            <Bar dataKey="revenue" fill="#3b82f6" />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Monthly Trend */}
                  {revenueData.monthly_trend.length > 0 && (
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-white">Monthly Revenue Trend</CardTitle>
                          <Select 
                            value={revenuePeriod.toString()} 
                            onValueChange={(value) => {
                              const period = parseInt(value);
                              setRevenuePeriod(period);
                              fetchRevenueAnalytics(period);
                            }}
                          >
                            <SelectTrigger className="w-32 bg-slate-700 border-slate-600 text-white">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-slate-800 border-slate-700">
                              <SelectItem value="3" className="text-white">3 months</SelectItem>
                              <SelectItem value="6" className="text-white">6 months</SelectItem>
                              <SelectItem value="12" className="text-white">12 months</SelectItem>
                              <SelectItem value="24" className="text-white">24 months</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={300}>
                          <LineChart data={revenueData.monthly_trend}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis dataKey="month" stroke="#94a3b8" />
                            <YAxis stroke="#94a3b8" />
                            <Tooltip 
                              contentStyle={{ 
                                backgroundColor: '#1e293b', 
                                border: '1px solid #475569',
                                borderRadius: '8px',
                                color: '#f1f5f9'
                              }}
                            />
                            <Line 
                              type="monotone" 
                              dataKey="revenue" 
                              stroke="#10b981" 
                              strokeWidth={2}
                              dot={{ fill: '#10b981', r: 4 }}
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  )}
                </>
              )}
            </TabsContent>

            {/* Geographic Distribution Tab */}
            <TabsContent value="geographic" className="space-y-6">
              {geoData && (
                <>
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader className="pb-2">
                        <CardDescription className="text-slate-400">Total Members</CardDescription>
                        <CardTitle className="text-2xl text-white">
                          {geoData.summary.total_members}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                    
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader className="pb-2">
                        <CardDescription className="text-slate-400">With Postcode</CardDescription>
                        <CardTitle className="text-2xl text-blue-400">
                          {geoData.summary.coverage.postcode}%
                        </CardTitle>
                      </CardHeader>
                    </Card>
                    
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader className="pb-2">
                        <CardDescription className="text-slate-400">With City</CardDescription>
                        <CardTitle className="text-2xl text-green-400">
                          {geoData.summary.coverage.city}%
                        </CardTitle>
                      </CardHeader>
                    </Card>
                    
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader className="pb-2">
                        <CardDescription className="text-slate-400">With State</CardDescription>
                        <CardTitle className="text-2xl text-purple-400">
                          {geoData.summary.coverage.state}%
                        </CardTitle>
                      </CardHeader>
                    </Card>
                  </div>

                  {/* Charts */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Top Postcodes */}
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader>
                        <CardTitle className="text-white">Top Postcodes</CardTitle>
                        <CardDescription className="text-slate-400">
                          Member distribution by area code
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={350}>
                          <BarChart data={geoData.by_postcode.slice(0, 10)} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis type="number" stroke="#94a3b8" />
                            <YAxis dataKey="postcode" type="category" stroke="#94a3b8" width={80} />
                            <Tooltip 
                              contentStyle={{ 
                                backgroundColor: '#1e293b', 
                                border: '1px solid #475569',
                                borderRadius: '8px',
                                color: '#f1f5f9'
                              }}
                            />
                            <Bar dataKey="count" fill="#3b82f6" />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>

                    {/* Top Cities */}
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader>
                        <CardTitle className="text-white">Top Cities</CardTitle>
                        <CardDescription className="text-slate-400">
                          Member concentration by city
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={350}>
                          <PieChart>
                            <Pie
                              data={geoData.by_city}
                              cx="50%"
                              cy="50%"
                              labelLine={false}
                              label={({ city, percentage }) => `${city}: ${percentage}%`}
                              outerRadius={100}
                              fill="#8884d8"
                              dataKey="count"
                            >
                              {geoData.by_city.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                              ))}
                            </Pie>
                            <Tooltip 
                              contentStyle={{ 
                                backgroundColor: '#1e293b', 
                                border: '1px solid #475569',
                                borderRadius: '8px',
                                color: '#f1f5f9'
                              }}
                            />
                          </PieChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </div>
                </>
              )}
            </TabsContent>

            {/* Attendance Deep Dive Tab */}
            <TabsContent value="attendance" className="space-y-6">
              {attendanceData && (
                <>
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader className="pb-2">
                        <CardDescription className="text-slate-400">Total Visits</CardDescription>
                        <CardTitle className="text-2xl text-white">
                          {attendanceData.summary.total_visits.toLocaleString()}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                    
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader className="pb-2">
                        <CardDescription className="text-slate-400">Unique Members</CardDescription>
                        <CardTitle className="text-2xl text-blue-400">
                          {attendanceData.summary.unique_members}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                    
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader className="pb-2">
                        <CardDescription className="text-slate-400">Avg Visits/Member</CardDescription>
                        <CardTitle className="text-2xl text-green-400">
                          {attendanceData.summary.avg_visits_per_member}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                    
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader className="pb-2">
                        <CardDescription className="text-slate-400">Period</CardDescription>
                        <CardTitle className="text-2xl text-white">
                          {attendanceData.summary.period_days} days
                        </CardTitle>
                      </CardHeader>
                    </Card>
                  </div>

                  {/* Charts */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Peak Hours */}
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader>
                        <CardTitle className="text-white">Peak Hours</CardTitle>
                        <CardDescription className="text-slate-400">
                          Top 5 busiest hours of the day
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          {attendanceData.peak_hours.map((peak, idx) => (
                            <div key={idx} className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg">
                              <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center">
                                  <span className="text-blue-400 font-bold text-sm">{idx + 1}</span>
                                </div>
                                <div>
                                  <div className="text-white font-medium">{peak.hour}</div>
                                  <div className="text-slate-400 text-sm">{peak.count} visits</div>
                                </div>
                              </div>
                              <Badge className="bg-blue-500 text-white">
                                {peak.percentage}%
                              </Badge>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>

                    {/* Frequency Distribution */}
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader>
                        <CardTitle className="text-white">Visit Frequency</CardTitle>
                        <CardDescription className="text-slate-400">
                          Member visit distribution
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={attendanceData.frequency_distribution}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis dataKey="range" stroke="#94a3b8" angle={-20} textAnchor="end" height={80} />
                            <YAxis stroke="#94a3b8" />
                            <Tooltip 
                              contentStyle={{ 
                                backgroundColor: '#1e293b', 
                                border: '1px solid #475569',
                                borderRadius: '8px',
                                color: '#f1f5f9'
                              }}
                            />
                            <Bar dataKey="members" fill="#10b981" />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Hourly Distribution */}
                  <Card className="bg-slate-800 border-slate-700">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-white">24-Hour Distribution</CardTitle>
                        <Select 
                          value={attendancePeriod.toString()} 
                          onValueChange={(value) => {
                            const period = parseInt(value);
                            setAttendancePeriod(period);
                            fetchAttendanceDeepDive(period);
                          }}
                        >
                          <SelectTrigger className="w-32 bg-slate-700 border-slate-600 text-white">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-slate-800 border-slate-700">
                            <SelectItem value="30" className="text-white">30 days</SelectItem>
                            <SelectItem value="60" className="text-white">60 days</SelectItem>
                            <SelectItem value="90" className="text-white">90 days</SelectItem>
                            <SelectItem value="180" className="text-white">180 days</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={attendanceData.hourly_distribution}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                          <XAxis dataKey="hour" stroke="#94a3b8" />
                          <YAxis stroke="#94a3b8" />
                          <Tooltip 
                            contentStyle={{ 
                              backgroundColor: '#1e293b', 
                              border: '1px solid #475569',
                              borderRadius: '8px',
                              color: '#f1f5f9'
                            }}
                          />
                          <Line 
                            type="monotone" 
                            dataKey="count" 
                            stroke="#3b82f6" 
                            strokeWidth={2}
                            dot={{ fill: '#3b82f6', r: 3 }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </>
              )}
            </TabsContent>

            {/* Lifetime Value Tab */}
            <TabsContent value="ltv" className="space-y-6">
              {ltvData && (
                <>
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader className="pb-2">
                        <CardDescription className="text-slate-400">Total LTV</CardDescription>
                        <CardTitle className="text-2xl text-green-400">
                          R {ltvData.summary.total_lifetime_value.toLocaleString()}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                    
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader className="pb-2">
                        <CardDescription className="text-slate-400">Avg LTV/Member</CardDescription>
                        <CardTitle className="text-2xl text-blue-400">
                          R {ltvData.summary.avg_ltv_per_member.toLocaleString()}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                    
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader className="pb-2">
                        <CardDescription className="text-slate-400">Members Analyzed</CardDescription>
                        <CardTitle className="text-2xl text-white">
                          {ltvData.summary.total_members_analyzed}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                  </div>

                  {/* LTV by Membership Type */}
                  <Card className="bg-slate-800 border-slate-700">
                    <CardHeader>
                      <CardTitle className="text-white">LTV by Membership Type</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-slate-700">
                              <th className="text-left py-3 px-4 text-slate-400">Type</th>
                              <th className="text-right py-3 px-4 text-slate-400">Members</th>
                              <th className="text-right py-3 px-4 text-slate-400">Avg LTV</th>
                              <th className="text-right py-3 px-4 text-slate-400">Avg Monthly</th>
                              <th className="text-right py-3 px-4 text-slate-400">Avg Duration</th>
                              <th className="text-right py-3 px-4 text-slate-400">Total LTV</th>
                            </tr>
                          </thead>
                          <tbody>
                            {ltvData.by_membership_type.map((type, idx) => (
                              <tr key={idx} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                                <td className="py-3 px-4 text-white font-medium">{type.membership_type}</td>
                                <td className="py-3 px-4 text-right text-slate-300">{type.member_count}</td>
                                <td className="py-3 px-4 text-right text-green-400 font-medium">
                                  R {type.avg_ltv.toLocaleString()}
                                </td>
                                <td className="py-3 px-4 text-right text-blue-400">
                                  R {type.avg_monthly_value.toLocaleString()}
                                </td>
                                <td className="py-3 px-4 text-right text-slate-300">
                                  {type.avg_duration_months} months
                                </td>
                                <td className="py-3 px-4 text-right text-white font-bold">
                                  R {type.total_ltv.toLocaleString()}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Top 10 Members by LTV */}
                  <Card className="bg-slate-800 border-slate-700">
                    <CardHeader>
                      <CardTitle className="text-white flex items-center gap-2">
                        <Award className="w-5 h-5 text-yellow-400" />
                        Top 10 Members by Lifetime Value
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {ltvData.top_members.map((member, idx) => (
                          <div key={idx} className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg">
                            <div className="flex items-center gap-4">
                              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-yellow-500 to-orange-500 flex items-center justify-center text-white font-bold">
                                #{idx + 1}
                              </div>
                              <div>
                                <div className="text-white font-medium">{member.member_name}</div>
                                <div className="text-slate-400 text-sm">
                                  {member.membership_type || 'No Type'} • {member.duration_months} months
                                </div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-green-400 font-bold text-lg">
                                R {member.ltv.toLocaleString()}
                              </div>
                              <div className="text-slate-400 text-sm">
                                R {member.monthly_value.toLocaleString()}/mo
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </>
              )}
            </TabsContent>

            {/* Churn Prediction Tab */}
            <TabsContent value="churn" className="space-y-6">
              {churnData && (
                <>
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader className="pb-2">
                        <CardDescription className="text-slate-400">Total Analyzed</CardDescription>
                        <CardTitle className="text-2xl text-white">
                          {churnData.summary.total_members_analyzed}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                    
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader className="pb-2">
                        <CardDescription className="text-slate-400">At Risk</CardDescription>
                        <CardTitle className="text-2xl text-orange-400">
                          {churnData.summary.at_risk_count}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                    
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader className="pb-2">
                        <CardDescription className="text-slate-400">Critical</CardDescription>
                        <CardTitle className="text-2xl text-red-400">
                          {churnData.summary.by_risk_level.critical}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                    
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader className="pb-2">
                        <CardDescription className="text-slate-400">High Risk</CardDescription>
                        <CardTitle className="text-2xl text-orange-400">
                          {churnData.summary.by_risk_level.high}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                    
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader className="pb-2">
                        <CardDescription className="text-slate-400">Medium Risk</CardDescription>
                        <CardTitle className="text-2xl text-yellow-400">
                          {churnData.summary.by_risk_level.medium}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                  </div>

                  {/* Risk Factors */}
                  <Card className="bg-slate-800 border-slate-700">
                    <CardHeader>
                      <CardTitle className="text-white">Common Risk Factors</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={churnData.common_risk_factors} layout="vertical">
                          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                          <XAxis type="number" stroke="#94a3b8" />
                          <YAxis dataKey="factor" type="category" stroke="#94a3b8" width={200} />
                          <Tooltip 
                            contentStyle={{ 
                              backgroundColor: '#1e293b', 
                              border: '1px solid #475569',
                              borderRadius: '8px',
                              color: '#f1f5f9'
                            }}
                          />
                          <Bar dataKey="count" fill="#f59e0b" />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* At-Risk Members List */}
                  <Card className="bg-slate-800 border-slate-700">
                    <CardHeader>
                      <CardTitle className="text-white flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5 text-red-400" />
                        Members at Risk
                      </CardTitle>
                      <CardDescription className="text-slate-400">
                        Showing top 20 members by churn risk score
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-slate-700">
                              <th className="text-left py-3 px-4 text-slate-400">Risk</th>
                              <th className="text-left py-3 px-4 text-slate-400">Member</th>
                              <th className="text-left py-3 px-4 text-slate-400">Contact</th>
                              <th className="text-left py-3 px-4 text-slate-400">Risk Factors</th>
                              <th className="text-right py-3 px-4 text-slate-400">Score</th>
                            </tr>
                          </thead>
                          <tbody>
                            {churnData.at_risk_members.slice(0, 20).map((member, idx) => (
                              <tr key={idx} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                                <td className="py-3 px-4">
                                  <Badge className={`${getRiskColor(member.risk_level)} text-white`}>
                                    {member.risk_level}
                                  </Badge>
                                </td>
                                <td className="py-3 px-4">
                                  <div className="text-white font-medium">{member.member_name}</div>
                                  <div className="text-slate-400 text-xs">
                                    {member.membership_type || 'No Type'}
                                  </div>
                                </td>
                                <td className="py-3 px-4">
                                  <div className="text-slate-300 text-xs">{member.email}</div>
                                  <div className="text-slate-400 text-xs">{member.phone}</div>
                                </td>
                                <td className="py-3 px-4">
                                  <div className="flex flex-wrap gap-1">
                                    {member.risk_reasons.slice(0, 2).map((reason, ridx) => (
                                      <span key={ridx} className="text-xs bg-slate-700 text-slate-300 px-2 py-1 rounded">
                                        {reason}
                                      </span>
                                    ))}
                                    {member.risk_reasons.length > 2 && (
                                      <span className="text-xs text-slate-400">
                                        +{member.risk_reasons.length - 2}
                                      </span>
                                    )}
                                  </div>
                                </td>
                                <td className="py-3 px-4 text-right">
                                  <span className="text-white font-bold">{member.risk_score}</span>
                                </td>
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
          </Tabs>
        </div>
      </div>
    </div>
  );
}
