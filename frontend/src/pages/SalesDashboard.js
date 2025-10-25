import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import AdvancedSalesAnalytics from '@/components/AdvancedSalesAnalytics';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Users, 
  TrendingUp, 
  DollarSign, 
  CheckSquare,
  AlertCircle,
  Award,
  Target,
  Calendar,
  Phone,
  Mail,
  Eye,
  ExternalLink,
  Filter,
  X,
  Gift
} from 'lucide-react';
import { 
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
  LineChart,
  Line,
  Area,
  AreaChart
} from 'recharts';
import { toast } from 'sonner';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];

export default function SalesDashboard() {
  const [overview, setOverview] = useState(null);
  const [funnel, setFunnel] = useState(null);
  const [comprehensiveAnalytics, setComprehensiveAnalytics] = useState(null);
  const [complimentaryData, setComplimentaryData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [drillDownOpen, setDrillDownOpen] = useState(false);
  const [drillDownData, setDrillDownData] = useState(null);
  const [drillDownType, setDrillDownType] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDashboardData();
    fetchComprehensiveAnalytics();
    fetchComplimentaryData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [overviewRes, funnelRes] = await Promise.all([
        axios.get(`${API}/sales/reports/overview`),
        axios.get(`${API}/sales/reports/conversion-funnel`)
      ]);
      
      setOverview(overviewRes.data);
      setFunnel(funnelRes.data);
    } catch (error) {
      toast.error('Failed to fetch dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const fetchComprehensiveAnalytics = async () => {
    try {
      const response = await axios.get(`${API}/sales/analytics/dashboard/comprehensive`);
      setComprehensiveAnalytics(response.data);
    } catch (error) {
      console.error('Failed to fetch comprehensive analytics:', error);
    }
  };

  const fetchComplimentaryData = async () => {
    try {
      const response = await axios.get(`${API}/complimentary-dashboard?days=30`);
      setComplimentaryData(response.data);
    } catch (error) {
      console.error('Failed to fetch complimentary data:', error);
    }
  };

  const openDrillDown = (type, data) => {
    setDrillDownType(type);
    setDrillDownData(data);
    setDrillDownOpen(true);
  };

  const getStageColor = (stage) => {
    const colors = {
      new_lead: 'bg-blue-500',
      contacted: 'bg-cyan-500',
      qualified: 'bg-green-500',
      proposal: 'bg-yellow-500',
      negotiation: 'bg-orange-500',
      closed_won: 'bg-emerald-500',
      closed_lost: 'bg-red-500'
    };
    return colors[stage] || 'bg-gray-500';
  };

  return (
    <div className="flex h-screen bg-slate-900">
      <Sidebar />
      
      <div className="flex-1 p-8 overflow-auto">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <TrendingUp className="w-8 h-8 text-blue-400" />
              Sales Dashboard
            </h1>
            <p className="text-slate-400 mt-2">
              Track leads, opportunities, and sales performance
            </p>
          </div>

          {overview && (
            <>
              {/* Key Metrics Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                {/* Total Leads */}
                <Card className="bg-gradient-to-br from-blue-600 to-blue-800 border-0">
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-white text-sm font-medium">Total Leads</CardTitle>
                      <Users className="w-5 h-5 text-blue-200" />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-white">{overview.leads.total}</div>
                    <div className="text-blue-100 text-sm mt-1">
                      {overview.recent_activity.leads_last_30_days} new this month
                    </div>
                  </CardContent>
                </Card>

                {/* Pipeline Value */}
                <Card className="bg-gradient-to-br from-green-600 to-green-800 border-0">
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-white text-sm font-medium">Pipeline Value</CardTitle>
                      <DollarSign className="w-5 h-5 text-green-200" />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-white">
                      R {overview.opportunities.total_pipeline_value.toLocaleString()}
                    </div>
                    <div className="text-green-100 text-sm mt-1">
                      {overview.opportunities.total} opportunities
                    </div>
                  </CardContent>
                </Card>

                {/* Win Rate */}
                <Card className="bg-gradient-to-br from-purple-600 to-purple-800 border-0">
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-white text-sm font-medium">Win Rate</CardTitle>
                      <Award className="w-5 h-5 text-purple-200" />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-white">{overview.opportunities.win_rate}%</div>
                    <div className="text-purple-100 text-sm mt-1">
                      {overview.opportunities.by_stage.closed_won} won deals
                    </div>
                  </CardContent>
                </Card>

                {/* Pending Tasks */}
                <Card className="bg-gradient-to-br from-orange-600 to-orange-800 border-0">
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-white text-sm font-medium">Pending Tasks</CardTitle>
                      <CheckSquare className="w-5 h-5 text-orange-200" />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-white">{overview.tasks.pending}</div>
                    <div className="text-orange-100 text-sm mt-1">
                      {overview.tasks.overdue} overdue
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Charts Row */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                {/* Lead Status Distribution */}
                <Card className="bg-slate-800 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-white">Lead Status Distribution</CardTitle>
                    <CardDescription className="text-slate-400">
                      Breakdown of leads by current status
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={[
                            { name: 'New', value: overview.leads.new },
                            { name: 'Contacted', value: overview.leads.contacted },
                            { name: 'Qualified', value: overview.leads.qualified },
                            { name: 'Converted', value: overview.leads.converted }
                          ].filter(item => item.value > 0)}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                          outerRadius={100}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {[0, 1, 2, 3].map((entry, index) => (
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

                {/* Pipeline by Stage */}
                <Card className="bg-slate-800 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-white">Pipeline by Stage</CardTitle>
                    <CardDescription className="text-slate-400">
                      Opportunities distribution across stages
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart 
                        data={Object.entries(overview.opportunities.by_stage).map(([stage, count]) => ({
                          stage: stage.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                          count
                        }))}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis 
                          dataKey="stage" 
                          stroke="#94a3b8"
                          angle={-20}
                          textAnchor="end"
                          height={80}
                        />
                        <YAxis stroke="#94a3b8" />
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
              </div>

              {/* Conversion Funnel */}
              {funnel && (
                <Card className="bg-slate-800 border-slate-700 mb-8">
                  <CardHeader>
                    <CardTitle className="text-white">Lead Conversion Funnel</CardTitle>
                    <CardDescription className="text-slate-400">
                      Conversion rate: {overview.leads.conversion_rate}%
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {funnel.funnel.map((stage, idx) => {
                        const percentage = overview.leads.total > 0 
                          ? (stage.count / overview.leads.total * 100) 
                          : 0;
                        
                        return (
                          <div key={stage.stage}>
                            <div className="flex items-center justify-between mb-2">
                              <div className="text-white font-medium capitalize">
                                {stage.stage}
                              </div>
                              <div className="text-slate-400 text-sm">
                                {stage.count} leads ({percentage.toFixed(1)}%)
                              </div>
                            </div>
                            <div className="w-full bg-slate-700 rounded-full h-3">
                              <div 
                                className="h-3 rounded-full bg-gradient-to-r from-blue-500 to-purple-500"
                                style={{ width: `${percentage}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Advanced Sales Analytics */}
              <div className="mt-8">
                <AdvancedSalesAnalytics />
              </div>

              {/* Comprehensive Analytics - Lead Source Performance */}
              {comprehensiveAnalytics && (
                <>
                  <div className="mt-8">
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle className="text-white flex items-center gap-2">
                              <Target className="w-5 h-5 text-blue-400" />
                              Lead Source Performance
                            </CardTitle>
                            <CardDescription className="text-slate-400">
                              Conversion rates and performance by lead source
                            </CardDescription>
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            className="border-slate-600"
                            onClick={() => openDrillDown('source_performance', comprehensiveAnalytics.source_performance)}
                          >
                            <Eye className="w-4 h-4 mr-2" />
                            View Details
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart
                            data={comprehensiveAnalytics.source_performance.slice(0, 8)}
                          >
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis 
                              dataKey="source" 
                              stroke="#94a3b8"
                              angle={-20}
                              textAnchor="end"
                              height={80}
                            />
                            <YAxis stroke="#94a3b8" />
                            <Tooltip
                              contentStyle={{
                                backgroundColor: '#1e293b',
                                border: '1px solid #475569',
                                borderRadius: '8px',
                                color: '#f1f5f9'
                              }}
                            />
                            <Legend />
                            <Bar dataKey="total_leads" fill="#3b82f6" name="Total Leads" />
                            <Bar dataKey="converted_leads" fill="#10b981" name="Converted" />
                            <Bar dataKey="lost_leads" fill="#ef4444" name="Lost" />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Daily Trends */}
                  <div className="mt-8">
                    <Card className="bg-slate-800 border-slate-700">
                      <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                          <TrendingUp className="w-5 h-5 text-green-400" />
                          Daily Activity Trends
                        </CardTitle>
                        <CardDescription className="text-slate-400">
                          New leads, conversions, and losses over time
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={300}>
                          <AreaChart data={comprehensiveAnalytics.daily_trends}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis 
                              dataKey="date" 
                              stroke="#94a3b8"
                              tickFormatter={(date) => new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                            />
                            <YAxis stroke="#94a3b8" />
                            <Tooltip
                              contentStyle={{
                                backgroundColor: '#1e293b',
                                border: '1px solid #475569',
                                borderRadius: '8px',
                                color: '#f1f5f9'
                              }}
                              labelFormatter={(date) => new Date(date).toLocaleDateString()}
                            />
                            <Legend />
                            <Area type="monotone" dataKey="new_leads" stackId="1" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.6} name="New Leads" />
                            <Area type="monotone" dataKey="converted" stackId="2" stroke="#10b981" fill="#10b981" fillOpacity={0.6} name="Converted" />
                            <Area type="monotone" dataKey="lost" stackId="3" stroke="#ef4444" fill="#ef4444" fillOpacity={0.6} name="Lost" />
                          </AreaChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Loss Analysis */}
                  {comprehensiveAnalytics.loss_analysis.length > 0 && (
                    <div className="mt-8">
                      <Card className="bg-slate-800 border-slate-700">
                        <CardHeader>
                          <div className="flex items-center justify-between">
                            <div>
                              <CardTitle className="text-white flex items-center gap-2">
                                <AlertCircle className="w-5 h-5 text-red-400" />
                                Loss Reason Analysis
                              </CardTitle>
                              <CardDescription className="text-slate-400">
                                Top reasons why leads are lost
                              </CardDescription>
                            </div>
                            <Button
                              variant="outline"
                              size="sm"
                              className="border-slate-600"
                              onClick={() => openDrillDown('loss_analysis', comprehensiveAnalytics.loss_analysis)}
                            >
                              <Eye className="w-4 h-4 mr-2" />
                              View Details
                            </Button>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <ResponsiveContainer width="100%" height={300}>
                            <PieChart>
                              <Pie
                                data={comprehensiveAnalytics.loss_analysis.slice(0, 6)}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ reason, percentage }) => `${reason}: ${percentage}%`}
                                outerRadius={100}
                                fill="#8884d8"
                                dataKey="count"
                              >
                                {comprehensiveAnalytics.loss_analysis.slice(0, 6).map((entry, index) => (
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
                  )}

                  {/* Salesperson Performance */}
                  {comprehensiveAnalytics.salesperson_performance.length > 0 && (
                    <div className="mt-8">
                      <Card className="bg-slate-800 border-slate-700">
                        <CardHeader>
                          <div className="flex items-center justify-between">
                            <div>
                              <CardTitle className="text-white flex items-center gap-2">
                                <Award className="w-5 h-5 text-yellow-400" />
                                Salesperson Leaderboard
                              </CardTitle>
                              <CardDescription className="text-slate-400">
                                Performance ranked by conversion rate
                              </CardDescription>
                            </div>
                            <Button
                              variant="outline"
                              size="sm"
                              className="border-slate-600"
                              onClick={() => openDrillDown('salesperson_performance', comprehensiveAnalytics.salesperson_performance)}
                            >
                              <Eye className="w-4 h-4 mr-2" />
                              View All
                            </Button>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-3">
                            {comprehensiveAnalytics.salesperson_performance.slice(0, 5).map((person, index) => (
                              <div key={index} className="p-4 bg-slate-700/50 rounded-lg border border-slate-600">
                                <div className="flex items-center justify-between mb-2">
                                  <div className="flex items-center gap-3">
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                                      index === 0 ? 'bg-yellow-500 text-yellow-900' :
                                      index === 1 ? 'bg-slate-400 text-slate-900' :
                                      index === 2 ? 'bg-orange-600 text-orange-100' :
                                      'bg-slate-600 text-slate-200'
                                    }`}>
                                      #{index + 1}
                                    </div>
                                    <div>
                                      <p className="text-white font-semibold">{person.salesperson}</p>
                                      <p className="text-slate-400 text-sm">{person.total_leads} leads</p>
                                    </div>
                                  </div>
                                  <div className="text-right">
                                    <p className="text-2xl font-bold text-white">{person.conversion_rate}%</p>
                                    <p className="text-slate-400 text-xs">conversion rate</p>
                                  </div>
                                </div>
                                <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-slate-600">
                                  <div>
                                    <p className="text-xs text-slate-400">Converted</p>
                                    <p className="text-sm font-semibold text-green-400">{person.converted}</p>
                                  </div>
                                  <div>
                                    <p className="text-xs text-slate-400">In Progress</p>
                                    <p className="text-sm font-semibold text-blue-400">{person.in_progress}</p>
                                  </div>
                                  <div>
                                    <p className="text-xs text-slate-400">Lost</p>
                                    <p className="text-sm font-semibold text-red-400">{person.lost}</p>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  )}
                </>
              )}

              {/* Quick Actions */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card 
                  className="bg-slate-800 border-slate-700 cursor-pointer hover:bg-slate-700 transition-colors"
                  onClick={() => navigate('/sales/leads')}
                >
                  <CardContent className="p-6">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center">
                        <Users className="w-6 h-6 text-blue-400" />
                      </div>
                      <div>
                        <div className="text-white font-semibold">Manage Leads</div>
                        <div className="text-slate-400 text-sm">View and edit contacts</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card 
                  className="bg-slate-800 border-slate-700 cursor-pointer hover:bg-slate-700 transition-colors"
                  onClick={() => navigate('/sales/pipeline')}
                >
                  <CardContent className="p-6">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center">
                        <Target className="w-6 h-6 text-green-400" />
                      </div>
                      <div>
                        <div className="text-white font-semibold">Sales Pipeline</div>
                        <div className="text-slate-400 text-sm">Manage opportunities</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card 
                  className="bg-slate-800 border-slate-700 cursor-pointer hover:bg-slate-700 transition-colors"
                  onClick={() => navigate('/sales/tasks')}
                >
                  <CardContent className="p-6">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-full bg-orange-500/20 flex items-center justify-center">
                        <CheckSquare className="w-6 h-6 text-orange-400" />
                      </div>
                      <div>
                        <div className="text-white font-semibold">My Tasks</div>
                        <div className="text-slate-400 text-sm">Follow-ups and activities</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </>
          )}

          {loading && (
            <div className="flex items-center justify-center h-64">
              <div className="text-slate-400">Loading dashboard...</div>
            </div>
          )}
        </div>
      </div>

      {/* Drill-down Modal */}
      <Dialog open={drillDownOpen} onOpenChange={setDrillDownOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {drillDownType === 'source_performance' && (
                <>
                  <Target className="w-5 h-5 text-blue-400" />
                  Lead Source Performance Details
                </>
              )}
              {drillDownType === 'loss_analysis' && (
                <>
                  <AlertCircle className="w-5 h-5 text-red-400" />
                  Loss Reason Analysis Details
                </>
              )}
              {drillDownType === 'salesperson_performance' && (
                <>
                  <Award className="w-5 h-5 text-yellow-400" />
                  Salesperson Performance Details
                </>
              )}
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              Detailed breakdown and insights
            </DialogDescription>
          </DialogHeader>

          <div className="mt-4">
            {drillDownType === 'source_performance' && drillDownData && (
              <div className="space-y-4">
                {drillDownData.map((source, index) => (
                  <div key={index} className="p-4 bg-slate-700/50 rounded-lg border border-slate-600">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-lg font-semibold text-white">{source.source}</h3>
                      <Badge className="bg-blue-600/50">
                        {source.conversion_rate}% conversion
                      </Badge>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="p-3 bg-slate-800/50 rounded border border-slate-600">
                        <p className="text-xs text-slate-400 uppercase mb-1">Total Leads</p>
                        <p className="text-2xl font-bold text-white">{source.total_leads}</p>
                      </div>
                      <div className="p-3 bg-slate-800/50 rounded border border-slate-600">
                        <p className="text-xs text-slate-400 uppercase mb-1">Converted</p>
                        <p className="text-2xl font-bold text-green-400">{source.converted_leads}</p>
                      </div>
                      <div className="p-3 bg-slate-800/50 rounded border border-slate-600">
                        <p className="text-xs text-slate-400 uppercase mb-1">Lost</p>
                        <p className="text-2xl font-bold text-red-400">{source.lost_leads}</p>
                      </div>
                      <div className="p-3 bg-slate-800/50 rounded border border-slate-600">
                        <p className="text-xs text-slate-400 uppercase mb-1">In Progress</p>
                        <p className="text-2xl font-bold text-blue-400">{source.in_progress}</p>
                      </div>
                    </div>
                    
                    <div className="mt-3 pt-3 border-t border-slate-600">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs text-slate-400">Loss Rate</p>
                          <p className="text-sm font-semibold text-white">{source.loss_rate}%</p>
                        </div>
                        <div>
                          <p className="text-xs text-slate-400">Avg. Days to Convert</p>
                          <p className="text-sm font-semibold text-white">{source.avg_days_to_convert} days</p>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {drillDownType === 'loss_analysis' && drillDownData && (
              <div className="space-y-4">
                {drillDownData.map((reason, index) => (
                  <div key={index} className="p-4 bg-slate-700/50 rounded-lg border border-slate-600">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-lg font-semibold text-white">{reason.reason}</h3>
                      <Badge className="bg-red-600/50">
                        {reason.percentage}% of losses
                      </Badge>
                    </div>
                    
                    <div className="mb-3">
                      <p className="text-sm text-slate-400 mb-1">Total Lost Leads:</p>
                      <p className="text-2xl font-bold text-white">{reason.count}</p>
                    </div>
                    
                    {Object.keys(reason.by_source).length > 0 && (
                      <div className="mt-3 pt-3 border-t border-slate-600">
                        <p className="text-xs text-slate-400 uppercase mb-2">Breakdown by Source:</p>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(reason.by_source).map(([source, count]) => (
                            <Badge key={source} variant="outline" className="border-slate-500">
                              {source}: {count}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {drillDownType === 'salesperson_performance' && drillDownData && (
              <div className="space-y-4">
                {drillDownData.map((person, index) => (
                  <div key={index} className="p-4 bg-slate-700/50 rounded-lg border border-slate-600">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                          index === 0 ? 'bg-yellow-500 text-yellow-900' :
                          index === 1 ? 'bg-slate-400 text-slate-900' :
                          index === 2 ? 'bg-orange-600 text-orange-100' :
                          'bg-slate-600 text-slate-200'
                        }`}>
                          #{index + 1}
                        </div>
                        <h3 className="text-lg font-semibold text-white">{person.salesperson}</h3>
                      </div>
                      <Badge className="bg-green-600/50">
                        {person.conversion_rate}% conversion
                      </Badge>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="p-3 bg-slate-800/50 rounded border border-slate-600">
                        <p className="text-xs text-slate-400 uppercase mb-1">Total Leads</p>
                        <p className="text-2xl font-bold text-white">{person.total_leads}</p>
                      </div>
                      <div className="p-3 bg-slate-800/50 rounded border border-slate-600">
                        <p className="text-xs text-slate-400 uppercase mb-1">Converted</p>
                        <p className="text-2xl font-bold text-green-400">{person.converted}</p>
                      </div>
                      <div className="p-3 bg-slate-800/50 rounded border border-slate-600">
                        <p className="text-xs text-slate-400 uppercase mb-1">In Progress</p>
                        <p className="text-2xl font-bold text-blue-400">{person.in_progress}</p>
                      </div>
                      <div className="p-3 bg-slate-800/50 rounded border border-slate-600">
                        <p className="text-xs text-slate-400 uppercase mb-1">Lost</p>
                        <p className="text-2xl font-bold text-red-400">{person.lost}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
