import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Download,
  Calendar,
  Award,
  CreditCard,
  AlertCircle,
  Users,
  BarChart3,
  PieChart as PieChartIcon,
  FileText
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
  ResponsiveContainer
} from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export default function FinancialReports() {
  const [revenueData, setRevenueData] = useState(null);
  const [commissionsData, setCommissionsData] = useState(null);
  const [financialSummary, setFinancialSummary] = useState(null);
  const [paymentAnalysis, setPaymentAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Filters
  const [dateRange, setDateRange] = useState('30'); // days
  const [groupBy, setGroupBy] = useState('day');

  useEffect(() => {
    fetchAllReports();
  }, [dateRange, groupBy]);

  const fetchAllReports = async () => {
    setLoading(true);
    try {
      const endDate = new Date().toISOString();
      const startDate = new Date(Date.now() - parseInt(dateRange) * 24 * 60 * 60 * 1000).toISOString();
      
      const [revenue, commissions, summary, payments] = await Promise.all([
        axios.get(`${API}/reports/revenue?start_date=${startDate}&end_date=${endDate}&group_by=${groupBy}`),
        axios.get(`${API}/reports/commissions?start_date=${startDate}&end_date=${endDate}`),
        axios.get(`${API}/reports/financial-summary?start_date=${startDate}&end_date=${endDate}`),
        axios.get(`${API}/reports/payment-analysis?start_date=${startDate}&end_date=${endDate}`)
      ]);
      
      setRevenueData(revenue.data);
      setCommissionsData(commissions.data);
      setFinancialSummary(summary.data);
      setPaymentAnalysis(payments.data);
    } catch (error) {
      console.error('Failed to fetch reports:', error);
      toast.error('Failed to load financial reports');
    } finally {
      setLoading(false);
    }
  };

  const exportToCSV = (data, filename) => {
    // Simple CSV export
    const csv = Object.keys(data[0]).join(',') + '\n' + 
                data.map(row => Object.values(row).join(',')).join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    toast.success('Report exported successfully');
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR' }).format(amount);
  };

  const formatPercentage = (value) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  if (loading && !revenueData) {
    return (
      <div className="flex h-screen bg-gray-50">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading financial reports...</p>
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
                <BarChart3 className="w-8 h-8 text-blue-600" />
                Financial Reports & Analytics
              </h1>
              <p className="text-gray-600 mt-1">Comprehensive business intelligence and financial insights</p>
            </div>
            <div className="flex gap-2">
              <Select value={dateRange} onValueChange={setDateRange}>
                <SelectTrigger className="w-[180px]">
                  <Calendar className="w-4 h-4 mr-2" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="7">Last 7 days</SelectItem>
                  <SelectItem value="30">Last 30 days</SelectItem>
                  <SelectItem value="90">Last 90 days</SelectItem>
                  <SelectItem value="365">Last year</SelectItem>
                </SelectContent>
              </Select>
              <Select value={groupBy} onValueChange={setGroupBy}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="day">Group by Day</SelectItem>
                  <SelectItem value="week">Group by Week</SelectItem>
                  <SelectItem value="month">Group by Month</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Tabs defaultValue="overview" className="space-y-6">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="revenue">Revenue Analysis</TabsTrigger>
              <TabsTrigger value="commissions">Commissions</TabsTrigger>
              <TabsTrigger value="payments">Payment Analysis</TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-6">
              {financialSummary && (
                <>
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Total Revenue</CardDescription>
                        <CardTitle className="text-3xl">
                          {formatCurrency(financialSummary.revenue.total_revenue)}
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        {revenueData && (
                          <div className={`flex items-center text-sm ${revenueData.comparison.growth_percentage >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {revenueData.comparison.growth_percentage >= 0 ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
                            {formatPercentage(revenueData.comparison.growth_percentage)} vs previous period
                          </div>
                        )}
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Collection Rate</CardDescription>
                        <CardTitle className="text-3xl text-green-600">
                          {financialSummary.performance.collection_rate}%
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-sm text-gray-600">
                          {financialSummary.performance.total_transactions} total transactions
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Outstanding Receivables</CardDescription>
                        <CardTitle className="text-3xl text-orange-600">
                          {formatCurrency(financialSummary.revenue.outstanding_receivables)}
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-sm text-gray-600">
                          {financialSummary.performance.unpaid_invoice_count} unpaid invoices
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Active Members</CardDescription>
                        <CardTitle className="text-3xl text-blue-600">
                          {financialSummary.members.active_members}
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-sm text-gray-600">
                          {financialSummary.members.new_members} new this period
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Revenue Breakdown */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <Card>
                      <CardHeader>
                        <CardTitle>Revenue Breakdown</CardTitle>
                        <CardDescription>Revenue by source type</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          <div className="flex justify-between items-center">
                            <div>
                              <div className="font-semibold">Membership Revenue</div>
                              <div className="text-sm text-gray-600">Invoices & Subscriptions</div>
                            </div>
                            <div className="text-right">
                              <div className="font-bold text-lg">{formatCurrency(financialSummary.revenue.membership_revenue)}</div>
                              <div className="text-sm text-gray-600">
                                {((financialSummary.revenue.membership_revenue / financialSummary.revenue.total_revenue) * 100).toFixed(1)}%
                              </div>
                            </div>
                          </div>
                          <div className="flex justify-between items-center">
                            <div>
                              <div className="font-semibold">Retail Revenue</div>
                              <div className="text-sm text-gray-600">POS & Product Sales</div>
                            </div>
                            <div className="text-right">
                              <div className="font-bold text-lg">{formatCurrency(financialSummary.revenue.retail_revenue)}</div>
                              <div className="text-sm text-gray-600">
                                {((financialSummary.revenue.retail_revenue / financialSummary.revenue.total_revenue) * 100).toFixed(1)}%
                              </div>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle>Key Metrics</CardTitle>
                        <CardDescription>Performance indicators</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          <div className="flex justify-between items-center">
                            <span className="text-gray-600">Avg Revenue per Member</span>
                            <span className="font-bold">{formatCurrency(financialSummary.members.avg_revenue_per_member)}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-600">Failed Payments</span>
                            <span className="font-bold text-red-600">{formatCurrency(financialSummary.revenue.failed_payments)}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-600">Failed Payment Count</span>
                            <span className="font-bold">{financialSummary.performance.failed_payment_count}</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </>
              )}
            </TabsContent>

            {/* Revenue Analysis Tab */}
            <TabsContent value="revenue" className="space-y-6">
              {revenueData && (
                <>
                  {/* Revenue Trend Chart */}
                  <Card>
                    <CardHeader>
                      <div className="flex justify-between items-center">
                        <div>
                          <CardTitle>Revenue Trend</CardTitle>
                          <CardDescription>Revenue over time by source</CardDescription>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => exportToCSV(revenueData.revenue_trend, 'revenue_trend')}
                        >
                          <Download className="w-4 h-4 mr-2" />
                          Export
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={revenueData.revenue_trend}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="period" />
                          <YAxis />
                          <Tooltip formatter={(value) => formatCurrency(value)} />
                          <Legend />
                          <Line type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={2} name="Total Revenue" />
                          <Line type="monotone" dataKey="invoice_revenue" stroke="#10b981" strokeWidth={2} name="Membership" />
                          <Line type="monotone" dataKey="pos_revenue" stroke="#f59e0b" strokeWidth={2} name="Retail" />
                        </LineChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* Revenue by Service & Payment Method */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <Card>
                      <CardHeader>
                        <CardTitle>Revenue by Service Type</CardTitle>
                        <CardDescription>Breakdown by revenue source</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={250}>
                          <PieChart>
                            <Pie
                              data={Object.entries(revenueData.revenue_by_service).map(([name, value]) => ({ name, value }))}
                              cx="50%"
                              cy="50%"
                              labelLine={false}
                              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                              outerRadius={80}
                              fill="#8884d8"
                              dataKey="value"
                            >
                              {Object.entries(revenueData.revenue_by_service).map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                              ))}
                            </Pie>
                            <Tooltip formatter={(value) => formatCurrency(value)} />
                          </PieChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle>Revenue by Payment Method</CardTitle>
                        <CardDescription>Payment method distribution</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          {Object.entries(revenueData.revenue_by_payment_method).map(([method, amount], index) => (
                            <div key={method} className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }}></div>
                                <span className="font-medium">{method}</span>
                              </div>
                              <span className="font-bold">{formatCurrency(amount)}</span>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Comparison Card */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Period Comparison</CardTitle>
                      <CardDescription>Current vs previous period performance</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div>
                          <div className="text-sm text-gray-600 mb-1">Previous Period</div>
                          <div className="text-2xl font-bold">{formatCurrency(revenueData.comparison.previous_period_revenue)}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600 mb-1">Current Period</div>
                          <div className="text-2xl font-bold text-blue-600">{formatCurrency(revenueData.total_revenue)}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600 mb-1">Growth</div>
                          <div className={`text-2xl font-bold ${revenueData.comparison.growth_percentage >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatPercentage(revenueData.comparison.growth_percentage)}
                          </div>
                          <div className="text-sm text-gray-600">{formatCurrency(revenueData.comparison.growth_amount)}</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </>
              )}
            </TabsContent>

            {/* Commissions Tab */}
            <TabsContent value="commissions" className="space-y-6">
              {commissionsData && (
                <>
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Total Commissions</CardDescription>
                        <CardTitle className="text-3xl text-green-600">
                          {formatCurrency(commissionsData.summary.total_commissions)}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Total Deal Value</CardDescription>
                        <CardTitle className="text-3xl">
                          {formatCurrency(commissionsData.summary.total_deal_value)}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Total Conversions</CardDescription>
                        <CardTitle className="text-3xl text-blue-600">
                          {commissionsData.summary.total_conversions}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Avg Commission</CardDescription>
                        <CardTitle className="text-3xl">
                          {formatCurrency(commissionsData.summary.average_commission_per_consultant)}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                  </div>

                  {/* Consultant Leaderboard */}
                  <Card>
                    <CardHeader>
                      <div className="flex justify-between items-center">
                        <div>
                          <CardTitle>Sales Consultant Leaderboard</CardTitle>
                          <CardDescription>Commission earnings and performance (Rate: {commissionsData.commission_rate * 100}%)</CardDescription>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => exportToCSV(commissionsData.consultants, 'commissions')}
                        >
                          <Download className="w-4 h-4 mr-2" />
                          Export
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      {commissionsData.consultants.length === 0 ? (
                        <div className="text-center py-8 text-gray-600">
                          No commission data available for this period
                        </div>
                      ) : (
                        <div className="overflow-x-auto">
                          <table className="w-full">
                            <thead className="border-b">
                              <tr className="text-left text-sm text-gray-600">
                                <th className="pb-3 font-semibold">Rank</th>
                                <th className="pb-3 font-semibold">Consultant</th>
                                <th className="pb-3 font-semibold">Role</th>
                                <th className="pb-3 font-semibold">Conversions</th>
                                <th className="pb-3 font-semibold">Deal Value</th>
                                <th className="pb-3 font-semibold">Avg Deal Size</th>
                                <th className="pb-3 font-semibold">Commission Earned</th>
                              </tr>
                            </thead>
                            <tbody>
                              {commissionsData.consultants.map((consultant, index) => (
                                <tr key={consultant.consultant_id} className="border-b hover:bg-gray-50">
                                  <td className="py-4">
                                    <div className="flex items-center gap-2">
                                      {index < 3 && (
                                        <Award className={`w-5 h-5 ${index === 0 ? 'text-yellow-500' : index === 1 ? 'text-gray-400' : 'text-orange-600'}`} />
                                      )}
                                      <span className="font-semibold">#{index + 1}</span>
                                    </div>
                                  </td>
                                  <td className="py-4">
                                    <div>
                                      <div className="font-semibold">{consultant.consultant_name}</div>
                                      <div className="text-sm text-gray-600">{consultant.email}</div>
                                    </div>
                                  </td>
                                  <td className="py-4 text-sm capitalize">{consultant.role.replace('_', ' ')}</td>
                                  <td className="py-4">
                                    <div>
                                      <div className="font-semibold">{consultant.total_conversions}</div>
                                      <div className="text-xs text-gray-600">
                                        {consultant.leads_converted}L + {consultant.opportunities_won}O
                                      </div>
                                    </div>
                                  </td>
                                  <td className="py-4 font-semibold">{formatCurrency(consultant.total_deal_value)}</td>
                                  <td className="py-4">{formatCurrency(consultant.average_deal_size)}</td>
                                  <td className="py-4">
                                    <div className="font-bold text-lg text-green-600">
                                      {formatCurrency(consultant.commission_earned)}
                                    </div>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </>
              )}
            </TabsContent>

            {/* Payment Analysis Tab */}
            <TabsContent value="payments" className="space-y-6">
              {paymentAnalysis && (
                <>
                  {/* Overall Statistics */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Total Transactions</CardDescription>
                        <CardTitle className="text-3xl">
                          {paymentAnalysis.overall.total_transactions}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Success Rate</CardDescription>
                        <CardTitle className="text-3xl text-green-600">
                          {paymentAnalysis.overall.overall_success_rate}%
                        </CardTitle>
                      </CardHeader>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Failed Transactions</CardDescription>
                        <CardTitle className="text-3xl text-red-600">
                          {paymentAnalysis.overall.failed_transactions}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Failed Amount</CardDescription>
                        <CardTitle className="text-3xl text-red-600">
                          {formatCurrency(paymentAnalysis.failure_analysis.total_failed_amount)}
                        </CardTitle>
                      </CardHeader>
                    </Card>
                  </div>

                  {/* Payment Method Performance */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Payment Method Performance</CardTitle>
                      <CardDescription>Success rates and volumes by payment method</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {Object.entries(paymentAnalysis.by_payment_method).map(([method, data]) => (
                          <div key={method} className="border rounded-lg p-4">
                            <div className="flex justify-between items-start mb-3">
                              <div className="flex items-center gap-2">
                                <CreditCard className="w-5 h-5 text-blue-600" />
                                <h4 className="font-semibold text-lg">{method}</h4>
                              </div>
                              <div className="text-right">
                                <div className="text-2xl font-bold text-green-600">{data.success_rate}%</div>
                                <div className="text-sm text-gray-600">Success Rate</div>
                              </div>
                            </div>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                              <div>
                                <div className="text-sm text-gray-600">Total Transactions</div>
                                <div className="font-semibold">{data.total_transactions}</div>
                              </div>
                              <div>
                                <div className="text-sm text-gray-600">Successful</div>
                                <div className="font-semibold text-green-600">{data.successful}</div>
                              </div>
                              <div>
                                <div className="text-sm text-gray-600">Failed</div>
                                <div className="font-semibold text-red-600">{data.failed}</div>
                              </div>
                              <div>
                                <div className="text-sm text-gray-600">Total Amount</div>
                                <div className="font-semibold">{formatCurrency(data.total_amount)}</div>
                              </div>
                            </div>
                            <div className="mt-3">
                              <div className="flex gap-2">
                                <div className="flex-1 bg-gray-200 rounded-full h-2 overflow-hidden">
                                  <div 
                                    className="bg-green-500 h-full"
                                    style={{ width: `${data.success_rate}%` }}
                                  />
                                </div>
                                <div className="flex-1 bg-gray-200 rounded-full h-2 overflow-hidden">
                                  <div 
                                    className="bg-red-500 h-full"
                                    style={{ width: `${data.failure_rate}%` }}
                                  />
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Failure Reasons */}
                  {Object.keys(paymentAnalysis.failure_analysis.top_failure_reasons).length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <AlertCircle className="w-5 h-5 text-red-600" />
                          Top Failure Reasons
                        </CardTitle>
                        <CardDescription>Common reasons for payment failures</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          {Object.entries(paymentAnalysis.failure_analysis.top_failure_reasons)
                            .sort((a, b) => b[1] - a[1])
                            .map(([reason, count]) => (
                              <div key={reason} className="flex justify-between items-center p-3 bg-red-50 rounded-lg">
                                <span className="font-medium text-red-800">{reason}</span>
                                <span className="font-bold text-red-600">{count} failures</span>
                              </div>
                            ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
