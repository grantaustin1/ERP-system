import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import {
  Users,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  DollarSign,
  Calendar,
  Download,
  Target,
  Award,
  UserX,
  UserCheck,
  MapPin,
  Filter
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'];

export default function MemberAnalytics() {
  const [retentionData, setRetentionData] = useState(null);
  const [ltvData, setLtvData] = useState(null);
  const [atRiskData, setAtRiskData] = useState(null);
  const [demographicsData, setDemographicsData] = useState(null);
  const [acquisitionData, setAcquisitionData] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Filters
  const [retentionPeriod, setRetentionPeriod] = useState('12');
  const [riskThreshold, setRiskThreshold] = useState('60');
  const [acquisitionDays, setAcquisitionDays] = useState('90');

  useEffect(() => {
    fetchAllAnalytics();
  }, [retentionPeriod, riskThreshold, acquisitionDays]);

  const fetchAllAnalytics = async () => {
    setLoading(true);
    try {
      const endDate = new Date().toISOString();
      const startDate = new Date(Date.now() - parseInt(acquisitionDays) * 24 * 60 * 60 * 1000).toISOString();
      
      const [retention, ltv, atRisk, demographics, acquisition] = await Promise.all([
        axios.get(`${API}/reports/retention-dashboard?period_months=${retentionPeriod}`),
        axios.get(`${API}/reports/member-ltv`),
        axios.get(`${API}/reports/at-risk-members?risk_threshold=${riskThreshold}`),
        axios.get(`${API}/reports/member-demographics`),
        axios.get(`${API}/reports/acquisition-cost?start_date=${startDate}&end_date=${endDate}`)
      ]);
      
      setRetentionData(retention.data);
      setLtvData(ltv.data);
      setAtRiskData(atRisk.data);
      setDemographicsData(demographics.data);
      setAcquisitionData(acquisition.data);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
      toast.error('Failed to load member analytics');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR' }).format(amount);
  };

  const getRiskBadge = (level) => {
    const config = {
      critical: { label: 'Critical Risk', className: 'bg-red-600 text-white' },
      high: { label: 'High Risk', className: 'bg-orange-600 text-white' },
      medium: { label: 'Medium Risk', className: 'bg-yellow-600 text-white' }
    };
    const { label, className } = config[level] || config.medium;
    return <Badge className={className}>{label}</Badge>;
  };

  if (loading && !retentionData) {
    return (
      <div className="flex h-screen bg-gray-50">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading member analytics...</p>
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
                <Users className="w-8 h-8 text-blue-600" />
                Member Analytics & Retention
              </h1>
              <p className="text-gray-600 mt-1">Understand your members, predict churn, maximize lifetime value</p>
            </div>
          </div>

          <Tabs defaultValue="retention" className="space-y-6">
            <TabsList>
              <TabsTrigger value="retention">Retention</TabsTrigger>
              <TabsTrigger value="ltv">Lifetime Value</TabsTrigger>
              <TabsTrigger value="at-risk">At-Risk Members</TabsTrigger>
              <TabsTrigger value="demographics">Demographics</TabsTrigger>
              <TabsTrigger value="acquisition">Acquisition</TabsTrigger>
            </TabsList>

            {/* Retention Tab */}
            <TabsContent value="retention" className="space-y-6">
              {retentionData && (
                <>
                  {/* Filter */}
                  <div className="flex justify-end">
                    <Select value={retentionPeriod} onValueChange={setRetentionPeriod}>
                      <SelectTrigger className="w-[200px]">
                        <Calendar className="w-4 h-4 mr-2" />
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="6">Last 6 months</SelectItem>
                        <SelectItem value="12">Last 12 months</SelectItem>
                        <SelectItem value="24">Last 24 months</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Total Members</CardDescription>
                        <CardTitle className="text-3xl">{retentionData.summary.total_members}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center text-sm text-gray-600">
                          <UserCheck className="w-4 h-4 mr-1" />
                          {retentionData.summary.active_members} active
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Retention Rate</CardDescription>
                        <CardTitle className="text-3xl text-green-600">{retentionData.summary.retention_rate}%</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center text-sm text-gray-600">
                          <TrendingUp className="w-4 h-4 mr-1" />
                          Keeping members engaged
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Churn Rate</CardDescription>
                        <CardTitle className="text-3xl text-red-600">{retentionData.summary.churn_rate}%</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center text-sm text-gray-600">
                          <UserX className="w-4 h-4 mr-1" />
                          {retentionData.summary.inactive_members} inactive
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Avg Tenure</CardDescription>
                        <CardTitle className="text-3xl text-blue-600">{retentionData.summary.avg_tenure_months} mo</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-sm text-gray-600">
                          {retentionData.summary.new_members_period} new this period
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Retention Trend Chart */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Retention Trend</CardTitle>
                      <CardDescription>Monthly retention rate over time</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={retentionData.retention_trend}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="month" />
                          <YAxis domain={[0, 100]} />
                          <Tooltip />
                          <Legend />
                          <Line type="monotone" dataKey="retention_rate" stroke="#10b981" strokeWidth={2} name="Retention Rate (%)" />
                        </LineChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* Cohort Analysis */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Retention by Cohort</CardTitle>
                      <CardDescription>Member retention rates by join month</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={retentionData.retention_by_cohort}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="cohort" />
                          <YAxis domain={[0, 100]} />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="retention_rate" fill="#3b82f6" name="Retention Rate (%)" />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </>
              )}
            </TabsContent>

            {/* LTV Tab */}
            <TabsContent value="ltv" className="space-y-6">
              {ltvData && (
                <>
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Total LTV</CardDescription>
                        <CardTitle className="text-3xl">{formatCurrency(ltvData.summary.total_ltv)}</CardTitle>
                      </CardHeader>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Average LTV</CardDescription>
                        <CardTitle className="text-3xl text-blue-600">{formatCurrency(ltvData.summary.average_ltv)}</CardTitle>
                      </CardHeader>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Avg LTV (Active)</CardDescription>
                        <CardTitle className="text-3xl text-green-600">{formatCurrency(ltvData.summary.average_ltv_active_members)}</CardTitle>
                      </CardHeader>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Highest LTV</CardDescription>
                        <CardTitle className="text-3xl text-purple-600">{formatCurrency(ltvData.summary.highest_ltv)}</CardTitle>
                      </CardHeader>
                    </Card>
                  </div>

                  {/* LTV by Membership Type */}
                  <Card>
                    <CardHeader>
                      <CardTitle>LTV by Membership Type</CardTitle>
                      <CardDescription>Average lifetime value per membership category</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={Object.entries(ltvData.ltv_by_membership_type).map(([name, data]) => ({ 
                          name, 
                          avg_ltv: data.avg_ltv,
                          member_count: data.member_count 
                        }))}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis />
                          <Tooltip formatter={(value, name) => name === 'avg_ltv' ? formatCurrency(value) : value} />
                          <Legend />
                          <Bar dataKey="avg_ltv" fill="#8b5cf6" name="Average LTV" />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* Top Members */}
                  <Card>
                    <CardHeader>
                      <div className="flex justify-between items-center">
                        <div>
                          <CardTitle>Top 20 Members by LTV</CardTitle>
                          <CardDescription>Highest value members</CardDescription>
                        </div>
                        <Button variant="outline" size="sm">
                          <Download className="w-4 h-4 mr-2" />
                          Export
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead className="border-b">
                            <tr className="text-left text-sm text-gray-600">
                              <th className="pb-3 font-semibold">Rank</th>
                              <th className="pb-3 font-semibold">Member</th>
                              <th className="pb-3 font-semibold">Status</th>
                              <th className="pb-3 font-semibold">Tenure</th>
                              <th className="pb-3 font-semibold">Total Revenue</th>
                              <th className="pb-3 font-semibold">Monthly Avg</th>
                            </tr>
                          </thead>
                          <tbody>
                            {ltvData.top_members.map((member, index) => (
                              <tr key={member.member_id} className="border-b hover:bg-gray-50">
                                <td className="py-4">
                                  <div className="flex items-center gap-2">
                                    {index < 3 && (
                                      <Award className={`w-5 h-5 ${index === 0 ? 'text-yellow-500' : index === 1 ? 'text-gray-400' : 'text-orange-600'}`} />
                                    )}
                                    <span className="font-semibold">#{index + 1}</span>
                                  </div>
                                </td>
                                <td className="py-4 font-medium">{member.member_name}</td>
                                <td className="py-4">
                                  <Badge variant={member.status === 'active' ? 'default' : 'secondary'}>
                                    {member.status}
                                  </Badge>
                                </td>
                                <td className="py-4">{member.tenure_months} months</td>
                                <td className="py-4 font-bold text-green-600">{formatCurrency(member.total_revenue)}</td>
                                <td className="py-4">{formatCurrency(member.monthly_avg_revenue)}</td>
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

            {/* At-Risk Members Tab */}
            <TabsContent value="at-risk" className="space-y-6">
              {atRiskData && (
                <>
                  {/* Filter */}
                  <div className="flex justify-end">
                    <Select value={riskThreshold} onValueChange={setRiskThreshold}>
                      <SelectTrigger className="w-[200px]">
                        <Filter className="w-4 h-4 mr-2" />
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="40">Risk Score ≥ 40</SelectItem>
                        <SelectItem value="60">Risk Score ≥ 60</SelectItem>
                        <SelectItem value="80">Risk Score ≥ 80</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Total At-Risk</CardDescription>
                        <CardTitle className="text-3xl text-orange-600">{atRiskData.summary.total_at_risk}</CardTitle>
                      </CardHeader>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Critical Risk</CardDescription>
                        <CardTitle className="text-3xl text-red-600">{atRiskData.summary.critical_risk}</CardTitle>
                      </CardHeader>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>High Risk</CardDescription>
                        <CardTitle className="text-3xl text-orange-600">{atRiskData.summary.high_risk}</CardTitle>
                      </CardHeader>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Medium Risk</CardDescription>
                        <CardTitle className="text-3xl text-yellow-600">{atRiskData.summary.medium_risk}</CardTitle>
                      </CardHeader>
                    </Card>
                  </div>

                  {/* At-Risk Members List */}
                  <Card>
                    <CardHeader>
                      <div className="flex justify-between items-center">
                        <div>
                          <CardTitle className="flex items-center gap-2">
                            <AlertTriangle className="w-5 h-5 text-red-600" />
                            At-Risk Members (Score ≥ {riskThreshold})
                          </CardTitle>
                          <CardDescription>Members likely to churn - prioritize for retention efforts</CardDescription>
                        </div>
                        <Button variant="outline" size="sm">
                          <Download className="w-4 h-4 mr-2" />
                          Export
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      {atRiskData.at_risk_members.length === 0 ? (
                        <div className="text-center py-8">
                          <UserCheck className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                          <p className="text-gray-600">No members at risk with current threshold</p>
                        </div>
                      ) : (
                        <div className="space-y-4">
                          {atRiskData.at_risk_members.map((member) => (
                            <div key={member.member_id} className="border rounded-lg p-4 hover:bg-gray-50">
                              <div className="flex justify-between items-start mb-3">
                                <div>
                                  <h4 className="font-semibold text-lg">{member.member_name}</h4>
                                  <div className="text-sm text-gray-600 mt-1">
                                    {member.email} • {member.phone}
                                  </div>
                                </div>
                                <div className="text-right">
                                  <div className="text-3xl font-bold text-red-600">{member.risk_score}</div>
                                  <div className="text-sm text-gray-600">Risk Score</div>
                                  {getRiskBadge(member.risk_level)}
                                </div>
                              </div>
                              <div className="grid grid-cols-2 gap-4 mb-3">
                                <div>
                                  <div className="text-sm text-gray-600">Membership Type</div>
                                  <div className="font-medium">{member.membership_type}</div>
                                </div>
                                <div>
                                  <div className="text-sm text-gray-600">Last Visit</div>
                                  <div className="font-medium">{member.last_visit ? new Date(member.last_visit).toLocaleDateString() : 'Never'}</div>
                                </div>
                              </div>
                              <div>
                                <div className="text-sm font-semibold text-gray-700 mb-2">Risk Factors:</div>
                                <div className="flex flex-wrap gap-2">
                                  {member.risk_factors.map((factor, idx) => (
                                    <Badge key={idx} variant="outline" className="text-red-600 border-red-300">
                                      {factor}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                              {member.unpaid_invoices > 0 && (
                                <div className="mt-3 p-2 bg-red-50 rounded text-sm text-red-800">
                                  ⚠️ {member.unpaid_invoices} unpaid invoice(s)
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </>
              )}
            </TabsContent>

            {/* Demographics Tab */}
            <TabsContent value="demographics" className="space-y-6">
              {demographicsData && (
                <>
                  {/* Summary Card */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Member Base Overview</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-3 gap-6">
                        <div>
                          <div className="text-sm text-gray-600">Total Members</div>
                          <div className="text-3xl font-bold">{demographicsData.summary.total_members}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600">Active Members</div>
                          <div className="text-3xl font-bold text-green-600">{demographicsData.summary.active_members}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600">Active Rate</div>
                          <div className="text-3xl font-bold text-blue-600">{demographicsData.summary.active_percentage}%</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Charts Grid */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Age Distribution */}
                    <Card>
                      <CardHeader>
                        <CardTitle>Age Distribution</CardTitle>
                        <CardDescription>Member breakdown by age group</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={Object.entries(demographicsData.age_distribution).map(([age, count]) => ({ age, count }))}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="age" angle={-45} textAnchor="end" height={80} />
                            <YAxis />
                            <Tooltip />
                            <Bar dataKey="count" fill="#3b82f6" />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>

                    {/* Gender Distribution */}
                    <Card>
                      <CardHeader>
                        <CardTitle>Gender Distribution</CardTitle>
                        <CardDescription>Member breakdown by gender</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={300}>
                          <PieChart>
                            <Pie
                              data={Object.entries(demographicsData.gender_distribution).map(([name, value]) => ({ name, value }))}
                              cx="50%"
                              cy="50%"
                              labelLine={false}
                              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                              outerRadius={80}
                              fill="#8884d8"
                              dataKey="value"
                            >
                              {Object.entries(demographicsData.gender_distribution).map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                              ))}
                            </Pie>
                            <Tooltip />
                          </PieChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>

                    {/* Membership Type Distribution */}
                    <Card>
                      <CardHeader>
                        <CardTitle>Membership Types</CardTitle>
                        <CardDescription>Distribution by membership category</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={300}>
                          <PieChart>
                            <Pie
                              data={Object.entries(demographicsData.membership_type_distribution).map(([name, value]) => ({ name, value }))}
                              cx="50%"
                              cy="50%"
                              labelLine={false}
                              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                              outerRadius={80}
                              fill="#8884d8"
                              dataKey="value"
                            >
                              {Object.entries(demographicsData.membership_type_distribution).map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                              ))}
                            </Pie>
                            <Tooltip />
                          </PieChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>

                    {/* Location Distribution */}
                    <Card>
                      <CardHeader>
                        <CardTitle>Top Locations</CardTitle>
                        <CardDescription>Members by location (Top 10)</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          {Object.entries(demographicsData.location_distribution).map(([location, count], index) => (
                            <div key={location} className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <MapPin className="w-4 h-4 text-gray-600" />
                                <span className="font-medium">{location}</span>
                              </div>
                              <span className="font-bold text-blue-600">{count}</span>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </>
              )}
            </TabsContent>

            {/* Acquisition Tab */}
            <TabsContent value="acquisition" className="space-y-6">
              {acquisitionData && (
                <>
                  {/* Filter */}
                  <div className="flex justify-end">
                    <Select value={acquisitionDays} onValueChange={setAcquisitionDays}>
                      <SelectTrigger className="w-[200px]">
                        <Calendar className="w-4 h-4 mr-2" />
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="30">Last 30 days</SelectItem>
                        <SelectItem value="90">Last 90 days</SelectItem>
                        <SelectItem value="180">Last 180 days</SelectItem>
                        <SelectItem value="365">Last year</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Total Leads</CardDescription>
                        <CardTitle className="text-3xl">{acquisitionData.summary.total_leads}</CardTitle>
                      </CardHeader>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Converted</CardDescription>
                        <CardTitle className="text-3xl text-green-600">{acquisitionData.summary.total_converted}</CardTitle>
                      </CardHeader>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Conversion Rate</CardDescription>
                        <CardTitle className="text-3xl text-blue-600">{acquisitionData.summary.overall_conversion_rate}%</CardTitle>
                      </CardHeader>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Avg Cost/Lead</CardDescription>
                        <CardTitle className="text-3xl">{formatCurrency(acquisitionData.summary.average_cost_per_lead)}</CardTitle>
                      </CardHeader>
                    </Card>
                  </div>

                  {/* Source Performance */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Lead Source Performance</CardTitle>
                      <CardDescription>Conversion rates and costs by source</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={acquisitionData.by_source}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="source" />
                          <YAxis yAxisId="left" />
                          <YAxis yAxisId="right" orientation="right" />
                          <Tooltip />
                          <Legend />
                          <Bar yAxisId="left" dataKey="conversion_rate" fill="#10b981" name="Conversion Rate (%)" />
                          <Bar yAxisId="right" dataKey="total_leads" fill="#3b82f6" name="Total Leads" />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* Source Details Table */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Detailed Source Analysis</CardTitle>
                      <CardDescription>Cost per acquisition and ROI by source</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead className="border-b">
                            <tr className="text-left text-sm text-gray-600">
                              <th className="pb-3 font-semibold">Source</th>
                              <th className="pb-3 font-semibold">Total Leads</th>
                              <th className="pb-3 font-semibold">Converted</th>
                              <th className="pb-3 font-semibold">Conv. Rate</th>
                              <th className="pb-3 font-semibold">Cost/Lead</th>
                              <th className="pb-3 font-semibold">Cost/Acquisition</th>
                              <th className="pb-3 font-semibold">ROI</th>
                            </tr>
                          </thead>
                          <tbody>
                            {acquisitionData.by_source.map((source) => (
                              <tr key={source.source} className="border-b hover:bg-gray-50">
                                <td className="py-4 font-semibold">{source.source}</td>
                                <td className="py-4">{source.total_leads}</td>
                                <td className="py-4 text-green-600 font-semibold">{source.converted_leads}</td>
                                <td className="py-4">
                                  <Badge variant={source.conversion_rate >= 50 ? 'default' : 'secondary'}>
                                    {source.conversion_rate}%
                                  </Badge>
                                </td>
                                <td className="py-4">{formatCurrency(source.cost_per_lead)}</td>
                                <td className="py-4 font-semibold">{formatCurrency(source.cost_per_acquisition)}</td>
                                <td className="py-4">
                                  <span className={`font-bold ${source.roi >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                    {source.roi >= 0 ? '+' : ''}{source.roi}%
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Best/Worst Performers */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <Award className="w-5 h-5 text-green-600" />
                          Best Performing Source
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        {acquisitionData.best_performing_source && (
                          <div>
                            <div className="text-2xl font-bold text-green-600 mb-2">{acquisitionData.best_performing_source.source}</div>
                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between">
                                <span className="text-gray-600">Conversion Rate:</span>
                                <span className="font-semibold">{acquisitionData.best_performing_source.conversion_rate}%</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600">Total Leads:</span>
                                <span className="font-semibold">{acquisitionData.best_performing_source.total_leads}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600">ROI:</span>
                                <span className="font-semibold text-green-600">+{acquisitionData.best_performing_source.roi}%</span>
                              </div>
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <TrendingDown className="w-5 h-5 text-red-600" />
                          Needs Improvement
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        {acquisitionData.worst_performing_source && (
                          <div>
                            <div className="text-2xl font-bold text-red-600 mb-2">{acquisitionData.worst_performing_source.source}</div>
                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between">
                                <span className="text-gray-600">Conversion Rate:</span>
                                <span className="font-semibold">{acquisitionData.worst_performing_source.conversion_rate}%</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600">Total Leads:</span>
                                <span className="font-semibold">{acquisitionData.worst_performing_source.total_leads}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600">ROI:</span>
                                <span className={`font-semibold ${acquisitionData.worst_performing_source.roi >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                  {acquisitionData.worst_performing_source.roi >= 0 ? '+' : ''}{acquisitionData.worst_performing_source.roi}%
                                </span>
                              </div>
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>
                </>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
