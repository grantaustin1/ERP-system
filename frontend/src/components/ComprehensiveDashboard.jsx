import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { 
  TrendingUp, 
  TrendingDown,
  Filter,
  Download,
  Calendar,
  DollarSign,
  Users,
  AlertCircle,
  Target,
  Activity
} from 'lucide-react';
import { 
  PieChart, 
  Pie, 
  BarChart, 
  Bar, 
  LineChart,
  Line,
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

export default function ComprehensiveDashboard() {
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState('last_30_days');
  const [dashboardData, setDashboardData] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  
  const [customDateFrom, setCustomDateFrom] = useState('');
  const [customDateTo, setCustomDateTo] = useState('');

  useEffect(() => {
    fetchDashboardData();
  }, [dateRange]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      let params = {};
      
      if (dateRange === 'custom' && customDateFrom && customDateTo) {
        params.date_from = customDateFrom;
        params.date_to = customDateTo;
      } else {
        // Calculate date range based on selection
        const endDate = new Date();
        const startDate = new Date();
        
        switch(dateRange) {
          case 'last_7_days':
            startDate.setDate(endDate.getDate() - 7);
            break;
          case 'last_30_days':
            startDate.setDate(endDate.getDate() - 30);
            break;
          case 'last_90_days':
            startDate.setDate(endDate.getDate() - 90);
            break;
          case 'this_year':
            startDate.setMonth(0, 1);
            break;
          default:
            startDate.setDate(endDate.getDate() - 30);
        }
        
        params.date_from = startDate.toISOString().split('T')[0];
        params.date_to = endDate.toISOString().split('T')[0];
      }
      
      const response = await axios.get(`${API}/sales/analytics/dashboard/comprehensive`, { params });
      setDashboardData(response.data);
    } catch (error) {
      toast.error('Failed to fetch dashboard analytics');
      console.error('Dashboard fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCustomDateApply = () => {
    if (customDateFrom && customDateTo) {
      fetchDashboardData();
    } else {
      toast.error('Please select both start and end dates');
    }
  };

  if (loading && !dashboardData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">Loading comprehensive analytics...</div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">No data available</div>
      </div>
    );
  }

  const { summary, source_performance, status_funnel, loss_analysis, daily_trends, salesperson_performance } = dashboardData;

  return (
    <div className="space-y-6">
      {/* Header with Date Range Selector */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <CardTitle className="text-white flex items-center gap-2">
                <Activity className="w-5 h-5 text-blue-400" />
                Comprehensive Sales Analytics
              </CardTitle>
              <CardDescription className="text-slate-400 mt-1">
                Complete overview of your sales pipeline performance
              </CardDescription>
            </div>
            
            <div className="flex items-center gap-3">
              <Select value={dateRange} onValueChange={setDateRange}>
                <SelectTrigger className="w-[200px] bg-slate-700 border-slate-600 text-white">
                  <Calendar className="w-4 h-4 mr-2" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-700 border-slate-600">
                  <SelectItem value="last_7_days" className="text-white">Last 7 Days</SelectItem>
                  <SelectItem value="last_30_days" className="text-white">Last 30 Days</SelectItem>
                  <SelectItem value="last_90_days" className="text-white">Last 90 Days</SelectItem>
                  <SelectItem value="this_year" className="text-white">This Year</SelectItem>
                  <SelectItem value="custom" className="text-white">Custom Range</SelectItem>
                </SelectContent>
              </Select>
              
              {dateRange === 'custom' && (
                <div className="flex items-center gap-2">
                  <input
                    type="date"
                    value={customDateFrom}
                    onChange={(e) => setCustomDateFrom(e.target.value)}
                    className="bg-slate-700 border-slate-600 text-white rounded px-3 py-2 text-sm"
                  />
                  <span className="text-slate-400">to</span>
                  <input
                    type="date"
                    value={customDateTo}
                    onChange={(e) => setCustomDateTo(e.target.value)}
                    className="bg-slate-700 border-slate-600 text-white rounded px-3 py-2 text-sm"
                  />
                  <Button onClick={handleCustomDateApply} size="sm" className="bg-blue-600 hover:bg-blue-700">
                    Apply
                  </Button>
                </div>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-blue-600/20 to-blue-800/20 border-blue-500/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-400 uppercase mb-1">Total Leads</p>
                <p className="text-3xl font-bold text-white">{summary.total_leads}</p>
              </div>
              <div className="w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center">
                <Users className="w-6 h-6 text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-600/20 to-green-800/20 border-green-500/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-400 uppercase mb-1">Converted</p>
                <p className="text-3xl font-bold text-white">{summary.total_converted}</p>
                <p className="text-xs text-green-400 mt-1">
                  {summary.overall_conversion_rate}% conversion rate
                </p>
              </div>
              <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-green-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-red-600/20 to-red-800/20 border-red-500/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-400 uppercase mb-1">Lost</p>
                <p className="text-3xl font-bold text-white">{summary.total_lost}</p>
              </div>
              <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center">
                <TrendingDown className="w-6 h-6 text-red-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-yellow-600/20 to-yellow-800/20 border-yellow-500/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-400 uppercase mb-1">In Progress</p>
                <p className="text-3xl font-bold text-white">{summary.in_progress}</p>
              </div>
              <div className="w-12 h-12 rounded-full bg-yellow-500/20 flex items-center justify-center">
                <Target className="w-6 h-6 text-yellow-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabbed Analytics */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-slate-800 grid grid-cols-5 w-full">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="sources">Sources</TabsTrigger>
          <TabsTrigger value="funnel">Funnel</TabsTrigger>
          <TabsTrigger value="loss">Loss Analysis</TabsTrigger>
          <TabsTrigger value="team">Team</TabsTrigger>
        </TabsList>

        {/* Overview Tab - Daily Trends */}
        <TabsContent value="overview" className="mt-6">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Daily Trends</CardTitle>
              <CardDescription className="text-slate-400">
                Lead activity over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={daily_trends}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="date" stroke="#94a3b8" />
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
                  <Line type="monotone" dataKey="new_leads" stroke="#3b82f6" name="New Leads" strokeWidth={2} />
                  <Line type="monotone" dataKey="converted" stroke="#10b981" name="Converted" strokeWidth={2} />
                  <Line type="monotone" dataKey="lost" stroke="#ef4444" name="Lost" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Source Performance Tab */}
        <TabsContent value="sources" className="mt-6 space-y-6">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Source Performance</CardTitle>
              <CardDescription className="text-slate-400">
                Conversion rates by lead source
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={source_performance}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="source" stroke="#94a3b8" angle={-20} textAnchor="end" height={100} />
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
                  <Bar dataKey="conversion_rate" fill="#8b5cf6" name="Conversion %" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Source Performance Table */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white text-sm">Detailed Source Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left py-3 px-4 text-slate-400 font-medium">Source</th>
                      <th className="text-right py-3 px-4 text-slate-400 font-medium">Total</th>
                      <th className="text-right py-3 px-4 text-slate-400 font-medium">Converted</th>
                      <th className="text-right py-3 px-4 text-slate-400 font-medium">Lost</th>
                      <th className="text-right py-3 px-4 text-slate-400 font-medium">Conv. Rate</th>
                      <th className="text-right py-3 px-4 text-slate-400 font-medium">Avg Days</th>
                    </tr>
                  </thead>
                  <tbody>
                    {source_performance.map((source, index) => (
                      <tr key={index} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                        <td className="py-3 px-4 text-white font-medium">{source.source}</td>
                        <td className="text-right py-3 px-4 text-white">{source.total_leads}</td>
                        <td className="text-right py-3 px-4 text-green-400">{source.converted_leads}</td>
                        <td className="text-right py-3 px-4 text-red-400">{source.lost_leads}</td>
                        <td className="text-right py-3 px-4">
                          <span className={`font-semibold ${
                            source.conversion_rate > 30 ? 'text-green-400' :
                            source.conversion_rate > 15 ? 'text-yellow-400' :
                            'text-red-400'
                          }`}>
                            {source.conversion_rate}%
                          </span>
                        </td>
                        <td className="text-right py-3 px-4 text-slate-400">
                          {source.avg_days_to_convert > 0 ? `${source.avg_days_to_convert} days` : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Status Funnel Tab */}
        <TabsContent value="funnel" className="mt-6">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Sales Funnel</CardTitle>
              <CardDescription className="text-slate-400">
                Lead progression through sales stages
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {status_funnel.map((status, index) => {
                  const prevCount = index > 0 ? status_funnel[index - 1].count : status.count;
                  const dropOffRate = prevCount > 0 ? ((status.drop_off / prevCount) * 100).toFixed(1) : 0;
                  
                  return (
                    <div key={index}>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <span className="text-white font-medium">{status.status}</span>
                          {status.drop_off > 0 && (
                            <span className="text-xs text-red-400">
                              (-{status.drop_off} dropped, {dropOffRate}%)
                            </span>
                          )}
                        </div>
                        <div className="text-slate-400 text-sm">
                          {status.count} leads ({status.percentage}%)
                        </div>
                      </div>
                      <div className="w-full bg-slate-700 rounded-full h-4 relative overflow-hidden">
                        <div
                          className="h-4 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
                          style={{ width: `${status.percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Loss Analysis Tab */}
        <TabsContent value="loss" className="mt-6 space-y-6">
          {/* Loss Reasons Pie Chart */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Loss Reasons Distribution</CardTitle>
              <CardDescription className="text-slate-400">
                Why leads are not converting
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loss_analysis.length > 0 ? (
                <ResponsiveContainer width="100%" height={400}>
                  <PieChart>
                    <Pie
                      data={loss_analysis}
                      dataKey="count"
                      nameKey="reason"
                      cx="50%"
                      cy="50%"
                      outerRadius={120}
                      label={(entry) => `${entry.reason}: ${entry.percentage}%`}
                    >
                      {loss_analysis.map((entry, index) => (
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
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-center py-12 text-slate-400">No loss data available</div>
              )}
            </CardContent>
          </Card>

          {/* Loss Reasons by Source */}
          {loss_analysis.length > 0 && (
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white text-sm">Loss Reasons by Source</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {loss_analysis.map((reason, index) => (
                    <div key={index} className="p-4 bg-slate-700/50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-white font-semibold">{reason.reason}</h4>
                        <div className="flex items-center gap-2">
                          <span className="text-slate-400 text-sm">{reason.count} leads</span>
                          <span className="text-red-400 font-semibold">{reason.percentage}%</span>
                        </div>
                      </div>
                      {Object.keys(reason.by_source).length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-3">
                          {Object.entries(reason.by_source).map(([source, count]) => (
                            <span key={source} className="px-3 py-1 bg-slate-600 rounded-full text-xs text-slate-300">
                              {source}: {count}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Team Performance Tab */}
        <TabsContent value="team" className="mt-6">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Team Performance Leaderboard</CardTitle>
              <CardDescription className="text-slate-400">
                Top performers ranked by conversion rate
              </CardDescription>
            </CardHeader>
            <CardContent>
              {salesperson_performance.length > 0 ? (
                <div className="space-y-3">
                  {salesperson_performance.slice(0, 10).map((person, index) => (
                    <div 
                      key={index}
                      className="p-4 bg-slate-700/50 rounded-lg border border-slate-600 hover:border-slate-500 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className={`
                            w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg
                            ${index === 0 ? 'bg-yellow-500 text-yellow-900' : ''}
                            ${index === 1 ? 'bg-slate-400 text-slate-900' : ''}
                            ${index === 2 ? 'bg-orange-600 text-orange-100' : ''}
                            ${index > 2 ? 'bg-slate-600 text-slate-200' : ''}
                          `}>
                            #{index + 1}
                          </div>
                          <div>
                            <p className="text-white font-semibold">{person.salesperson}</p>
                            <p className="text-slate-400 text-sm">
                              {person.total_leads} leads • {person.converted} converted • {person.lost} lost
                            </p>
                          </div>
                        </div>
                        
                        <div className="text-right">
                          <p className="text-2xl font-bold text-white">{person.conversion_rate}%</p>
                          <p className="text-xs text-slate-400">conversion rate</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-slate-400">No team performance data available</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
