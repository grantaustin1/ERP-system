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
  TrendingUp,
  TrendingDown,
  Target,
  DollarSign,
  Calendar,
  Download,
  Award,
  XCircle,
  CheckCircle,
  Users,
  Activity,
  BarChart3,
  PieChart as PieChartIcon
} from 'lucide-react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  FunnelChart,
  Funnel,
  LabelList,
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

export default function SalesPerformance() {
  const [funnelData, setFunnelData] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [sourceRoiData, setSourceRoiData] = useState(null);
  const [winLossData, setWinLossData] = useState(null);
  const [performanceData, setPerformanceData] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Filters
  const [funnelDays, setFunnelDays] = useState('90');
  const [roiDays, setRoiDays] = useState('90');
  const [winLossDays, setWinLossDays] = useState('90');
  const [performanceDays, setPerformanceDays] = useState('30');

  useEffect(() => {
    fetchAllReports();
  }, [funnelDays, roiDays, winLossDays, performanceDays]);

  const fetchAllReports = async () => {
    setLoading(true);
    try {
      const endDate = new Date().toISOString();
      const funnelStart = new Date(Date.now() - parseInt(funnelDays) * 24 * 60 * 60 * 1000).toISOString();
      const roiStart = new Date(Date.now() - parseInt(roiDays) * 24 * 60 * 60 * 1000).toISOString();
      const winLossStart = new Date(Date.now() - parseInt(winLossDays) * 24 * 60 * 60 * 1000).toISOString();
      const perfStart = new Date(Date.now() - parseInt(performanceDays) * 24 * 60 * 60 * 1000).toISOString();
      
      const [funnel, forecast, roi, winLoss, performance] = await Promise.all([
        axios.get(`${API}/reports/sales-funnel?start_date=${funnelStart}&end_date=${endDate}`),
        axios.get(`${API}/reports/pipeline-forecast`),
        axios.get(`${API}/reports/lead-source-roi?start_date=${roiStart}&end_date=${endDate}`),
        axios.get(`${API}/reports/win-loss-analysis?start_date=${winLossStart}&end_date=${endDate}`),
        axios.get(`${API}/reports/salesperson-performance?start_date=${perfStart}&end_date=${endDate}`)
      ]);
      
      setFunnelData(funnel.data);
      setForecastData(forecast.data);
      setSourceRoiData(roi.data);
      setWinLossData(winLoss.data);
      setPerformanceData(performance.data);
    } catch (error) {
      console.error('Failed to fetch sales reports:', error);
      toast.error('Failed to load sales performance data');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR' }).format(amount);
  };

  if (loading && !funnelData) {
    return (
      <div className="flex h-screen bg-gray-50">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading sales performance...</p>
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
                <Target className="w-8 h-8 text-blue-600" />
                Sales Performance & Forecasting
              </h1>
              <p className="text-gray-600 mt-1">Analyze pipeline, predict revenue, optimize conversions</p>
            </div>
          </div>

          <Tabs defaultValue="funnel" className="space-y-6">
            <TabsList>
              <TabsTrigger value="funnel">Sales Funnel</TabsTrigger>
              <TabsTrigger value="forecast">Pipeline Forecast</TabsTrigger>
              <TabsTrigger value="roi">Lead Source ROI</TabsTrigger>
              <TabsTrigger value="winloss">Win/Loss</TabsTrigger>
              <TabsTrigger value="performance">Team Performance</TabsTrigger>
            </TabsList>

            {/* Sales Funnel Tab */}
            <TabsContent value="funnel" className="space-y-6">
              {funnelData && (
                <>
                  <div className="flex justify-end">
                    <Select value={funnelDays} onValueChange={setFunnelDays}>
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

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Total Leads</CardDescription>
                        <CardTitle className="text-3xl">{funnelData.summary.total_leads}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-sm text-gray-600">Entered the funnel</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Closed Won</CardDescription>
                        <CardTitle className="text-3xl text-green-600">{funnelData.summary.total_won}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-sm text-gray-600">Successfully converted</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Conversion Rate</CardDescription>
                        <CardTitle className="text-3xl text-blue-600">{funnelData.summary.overall_conversion_rate}%</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-sm text-gray-600">Lead to customer</div>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle>Sales Funnel Visualization</CardTitle>
                      <CardDescription>Conversion rates at each stage</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={400}>
                        <BarChart data={funnelData.funnel_stages} layout="vertical">
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis type="number" />
                          <YAxis dataKey="label" type="category" width={120} />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="count" fill="#3b82f6" name="Count" />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Funnel Stage Details</CardTitle>
                      <CardDescription>Conversion and drop-off metrics</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {funnelData.funnel_stages.map((stage, index) => (
                          <div key={stage.stage} className="border rounded-lg p-4">
                            <div className="flex justify-between items-start mb-3">
                              <div>
                                <h4 className="font-semibold text-lg">{stage.label}</h4>
                                <div className="text-sm text-gray-600 mt-1">Stage {index + 1} of {funnelData.funnel_stages.length}</div>
                              </div>
                              <div className="text-right">
                                <div className="text-3xl font-bold text-blue-600">{stage.count}</div>
                                <div className="text-sm text-gray-600">Opportunities</div>
                              </div>
                            </div>
                            <div className="grid grid-cols-3 gap-4">
                              <div>
                                <div className="text-sm text-gray-600">Conversion Rate</div>
                                <div className="text-xl font-semibold text-green-600">{stage.conversion_rate}%</div>
                              </div>
                              <div>
                                <div className="text-sm text-gray-600">Drop-off</div>
                                <div className="text-xl font-semibold text-red-600">{stage.drop_off}</div>
                              </div>
                              <div>
                                <div className="text-sm text-gray-600">Drop-off Rate</div>
                                <div className="text-xl font-semibold text-orange-600">{stage.drop_off_rate}%</div>
                              </div>
                            </div>
                            <div className="mt-3 bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                style={{ width: `${stage.conversion_rate}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </>
              )}
            </TabsContent>

            {/* Pipeline Forecast Tab */}
            <TabsContent value="forecast" className="space-y-6">
              {forecastData && (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Total Pipeline</CardDescription>
                        <CardTitle className="text-3xl">{formatCurrency(forecastData.summary.total_pipeline_value)}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-sm text-gray-600">{forecastData.summary.total_opportunities} opportunities</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Predicted Revenue</CardDescription>
                        <CardTitle className="text-3xl text-green-600">{formatCurrency(forecastData.summary.predicted_revenue)}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-sm text-gray-600">Weighted forecast</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Closing This Month</CardDescription>
                        <CardTitle className="text-3xl text-blue-600">{forecastData.summary.closing_this_month}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-sm text-gray-600">{formatCurrency(forecastData.summary.closing_this_month_weighted)} weighted</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Avg Days to Close</CardDescription>
                        <CardTitle className="text-3xl text-purple-600">{forecastData.summary.avg_days_to_close}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-sm text-gray-600">Sales velocity</div>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle>Pipeline by Stage</CardTitle>
                      <CardDescription>Total and weighted values by stage probability</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={forecastData.pipeline_by_stage}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="stage" />
                          <YAxis />
                          <Tooltip formatter={(value) => formatCurrency(value)} />
                          <Legend />
                          <Bar dataKey="total_value" fill="#3b82f6" name="Total Value" />
                          <Bar dataKey="weighted_value" fill="#10b981" name="Weighted Value" />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Stage Probabilities</CardTitle>
                      <CardDescription>Weighted probability applied to each stage</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                        {Object.entries(forecastData.stage_probabilities).map(([stage, prob]) => (
                          <div key={stage} className="text-center p-4 bg-gray-50 rounded-lg">
                            <div className="text-sm text-gray-600 capitalize">{stage}</div>
                            <div className="text-2xl font-bold text-blue-600">{(prob * 100).toFixed(0)}%</div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </>
              )}
            </TabsContent>

            {/* Lead Source ROI Tab */}
            <TabsContent value="roi" className="space-y-6">
              {sourceRoiData && (
                <>
                  <div className="flex justify-end">
                    <Select value={roiDays} onValueChange={setRoiDays}>
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

                  {sourceRoiData.best_roi_source && sourceRoiData.worst_roi_source && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <Card>
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2">
                            <Award className="w-5 h-5 text-green-600" />
                            Best ROI Source
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold text-green-600 mb-3">{sourceRoiData.best_roi_source.source}</div>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-gray-600">ROI:</span>
                              <span className="font-bold text-green-600">+{sourceRoiData.best_roi_source.roi}%</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Conversion Rate:</span>
                              <span className="font-semibold">{sourceRoiData.best_roi_source.conversion_rate}%</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Revenue Generated:</span>
                              <span className="font-semibold">{formatCurrency(sourceRoiData.best_roi_source.revenue_generated)}</span>
                            </div>
                          </div>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2">
                            <TrendingDown className="w-5 h-5 text-red-600" />
                            Needs Optimization
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold text-red-600 mb-3">{sourceRoiData.worst_roi_source.source}</div>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-gray-600">ROI:</span>
                              <span className={`font-bold ${sourceRoiData.worst_roi_source.roi >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {sourceRoiData.worst_roi_source.roi >= 0 ? '+' : ''}{sourceRoiData.worst_roi_source.roi}%
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Conversion Rate:</span>
                              <span className="font-semibold">{sourceRoiData.worst_roi_source.conversion_rate}%</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Revenue Generated:</span>
                              <span className="font-semibold">{formatCurrency(sourceRoiData.worst_roi_source.revenue_generated)}</span>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  )}

                  <Card>
                    <CardHeader>
                      <CardTitle>ROI by Lead Source</CardTitle>
                      <CardDescription>Return on investment for each marketing channel</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={sourceRoiData.sources}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="source" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="roi" fill="#10b981" name="ROI (%)" />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Detailed Source Performance</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead className="border-b">
                            <tr className="text-left text-sm text-gray-600">
                              <th className="pb-3 font-semibold">Source</th>
                              <th className="pb-3 font-semibold">Leads</th>
                              <th className="pb-3 font-semibold">Converted</th>
                              <th className="pb-3 font-semibold">Conv. Rate</th>
                              <th className="pb-3 font-semibold">Revenue</th>
                              <th className="pb-3 font-semibold">Cost/Acq</th>
                              <th className="pb-3 font-semibold">ROI</th>
                            </tr>
                          </thead>
                          <tbody>
                            {sourceRoiData.sources.map((source) => (
                              <tr key={source.source} className="border-b hover:bg-gray-50">
                                <td className="py-4 font-semibold">{source.source}</td>
                                <td className="py-4">{source.total_leads}</td>
                                <td className="py-4 text-green-600 font-semibold">{source.converted_leads}</td>
                                <td className="py-4">
                                  <Badge variant={source.conversion_rate >= 20 ? 'default' : 'secondary'}>
                                    {source.conversion_rate}%
                                  </Badge>
                                </td>
                                <td className="py-4 font-semibold">{formatCurrency(source.revenue_generated)}</td>
                                <td className="py-4">{formatCurrency(source.cost_per_acquisition)}</td>
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
                </>
              )}
            </TabsContent>

            {/* Win/Loss Tab */}
            <TabsContent value="winloss" className="space-y-6">
              {winLossData && (
                <>
                  <div className="flex justify-end">
                    <Select value={winLossDays} onValueChange={setWinLossDays}>
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

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Win Rate</CardDescription>
                        <CardTitle className="text-3xl text-green-600">{winLossData.summary.win_rate}%</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-sm text-gray-600">{winLossData.summary.total_won} won</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Total Closed</CardDescription>
                        <CardTitle className="text-3xl">{winLossData.summary.total_closed}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-sm text-gray-600">{winLossData.summary.total_lost} lost</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Won Revenue</CardDescription>
                        <CardTitle className="text-3xl text-green-600">{formatCurrency(winLossData.summary.won_revenue)}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-sm text-gray-600">Avg: {formatCurrency(winLossData.summary.avg_won_deal_size)}</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardDescription>Lost Revenue</CardDescription>
                        <CardTitle className="text-3xl text-red-600">{formatCurrency(winLossData.summary.lost_revenue)}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-sm text-gray-600">Avg: {formatCurrency(winLossData.summary.avg_lost_deal_size)}</div>
                      </CardContent>
                    </Card>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <Card>
                      <CardHeader>
                        <CardTitle>Win vs Loss Distribution</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={300}>
                          <PieChart>
                            <Pie
                              data={[
                                { name: 'Won', value: winLossData.summary.total_won },
                                { name: 'Lost', value: winLossData.summary.total_lost }
                              ]}
                              cx="50%"
                              cy="50%"
                              labelLine={false}
                              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                              outerRadius={80}
                              fill="#8884d8"
                              dataKey="value"
                            >
                              <Cell fill="#10b981" />
                              <Cell fill="#ef4444" />
                            </Pie>
                            <Tooltip />
                          </PieChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle>Top Loss Reasons</CardTitle>
                        <CardDescription>Why deals are being lost</CardDescription>
                      </CardHeader>
                      <CardContent>
                        {winLossData.loss_reasons.length === 0 ? (
                          <div className="text-center py-8 text-gray-600">No loss data available</div>
                        ) : (
                          <div className="space-y-3">
                            {winLossData.loss_reasons.slice(0, 5).map((reason, index) => (
                              <div key={index} className="flex justify-between items-center p-3 bg-red-50 rounded-lg">
                                <span className="font-medium text-red-800">{reason.reason}</span>
                                <div className="text-right">
                                  <div className="font-bold text-red-600">{reason.count}</div>
                                  <div className="text-xs text-red-600">{reason.percentage}%</div>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle>Win Rate by Salesperson</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {winLossData.salesperson_performance.length === 0 ? (
                        <div className="text-center py-8 text-gray-600">No salesperson data available</div>
                      ) : (
                        <div className="overflow-x-auto">
                          <table className="w-full">
                            <thead className="border-b">
                              <tr className="text-left text-sm text-gray-600">
                                <th className="pb-3 font-semibold">Salesperson</th>
                                <th className="pb-3 font-semibold">Won</th>
                                <th className="pb-3 font-semibold">Lost</th>
                                <th className="pb-3 font-semibold">Total Closed</th>
                                <th className="pb-3 font-semibold">Win Rate</th>
                              </tr>
                            </thead>
                            <tbody>
                              {winLossData.salesperson_performance.map((person) => (
                                <tr key={person.salesperson_id} className="border-b hover:bg-gray-50">
                                  <td className="py-4 font-medium">{person.salesperson_name}</td>
                                  <td className="py-4 text-green-600 font-semibold">{person.won}</td>
                                  <td className="py-4 text-red-600 font-semibold">{person.lost}</td>
                                  <td className="py-4">{person.total_closed}</td>
                                  <td className="py-4">
                                    <Badge variant={person.win_rate >= 50 ? 'default' : 'secondary'}>
                                      {person.win_rate}%
                                    </Badge>
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

            {/* Team Performance Tab */}
            <TabsContent value="performance" className="space-y-6">
              {performanceData && (
                <>
                  <div className="flex justify-end">
                    <Select value={performanceDays} onValueChange={setPerformanceDays}>
                      <SelectTrigger className="w-[200px]">
                        <Calendar className="w-4 h-4 mr-2" />
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="7">Last 7 days</SelectItem>
                        <SelectItem value="30">Last 30 days</SelectItem>
                        <SelectItem value="90">Last 90 days</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle>Team Summary</CardTitle>
                      <CardDescription>Overall team performance metrics</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
                        <div>
                          <div className="text-sm text-gray-600">Total Leads</div>
                          <div className="text-3xl font-bold">{performanceData.team_summary.total_leads}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600">Opportunities</div>
                          <div className="text-3xl font-bold">{performanceData.team_summary.total_opportunities}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600">Deals Won</div>
                          <div className="text-3xl font-bold text-green-600">{performanceData.team_summary.total_won}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600">Revenue</div>
                          <div className="text-3xl font-bold text-blue-600">{formatCurrency(performanceData.team_summary.total_revenue)}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600">Pipeline Value</div>
                          <div className="text-3xl font-bold text-purple-600">{formatCurrency(performanceData.team_summary.total_pipeline_value)}</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {performanceData.top_performer && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <Award className="w-5 h-5 text-yellow-500" />
                          Top Performer
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold text-blue-600 mb-3">{performanceData.top_performer.salesperson_name}</div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <div className="text-gray-600">Won Revenue</div>
                            <div className="text-xl font-bold text-green-600">{formatCurrency(performanceData.top_performer.won_revenue)}</div>
                          </div>
                          <div>
                            <div className="text-gray-600">Win Rate</div>
                            <div className="text-xl font-bold">{performanceData.top_performer.opp_win_rate}%</div>
                          </div>
                          <div>
                            <div className="text-gray-600">Avg Deal Size</div>
                            <div className="text-xl font-bold">{formatCurrency(performanceData.top_performer.avg_deal_size)}</div>
                          </div>
                          <div>
                            <div className="text-gray-600">Pipeline Value</div>
                            <div className="text-xl font-bold text-purple-600">{formatCurrency(performanceData.top_performer.pipeline_value)}</div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  <Card>
                    <CardHeader>
                      <CardTitle>Individual Performance</CardTitle>
                      <CardDescription>Detailed metrics per salesperson</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead className="border-b">
                            <tr className="text-left text-sm text-gray-600">
                              <th className="pb-3 font-semibold">Salesperson</th>
                              <th className="pb-3 font-semibold">Leads</th>
                              <th className="pb-3 font-semibold">Conv. Rate</th>
                              <th className="pb-3 font-semibold">Won</th>
                              <th className="pb-3 font-semibold">Win Rate</th>
                              <th className="pb-3 font-semibold">Pipeline</th>
                              <th className="pb-3 font-semibold">Revenue</th>
                            </tr>
                          </thead>
                          <tbody>
                            {performanceData.salesperson_performance.map((person, index) => (
                              <tr key={person.salesperson_id} className="border-b hover:bg-gray-50">
                                <td className="py-4">
                                  <div className="flex items-center gap-2">
                                    {index === 0 && <Award className="w-4 h-4 text-yellow-500" />}
                                    <span className="font-medium">{person.salesperson_name}</span>
                                  </div>
                                </td>
                                <td className="py-4">{person.total_leads}</td>
                                <td className="py-4">
                                  <Badge variant={person.lead_conversion_rate >= 20 ? 'default' : 'secondary'}>
                                    {person.lead_conversion_rate}%
                                  </Badge>
                                </td>
                                <td className="py-4 text-green-600 font-semibold">{person.won_opportunities}</td>
                                <td className="py-4">
                                  <Badge variant={person.opp_win_rate >= 50 ? 'default' : 'secondary'}>
                                    {person.opp_win_rate}%
                                  </Badge>
                                </td>
                                <td className="py-4 font-semibold text-purple-600">{formatCurrency(person.pipeline_value)}</td>
                                <td className="py-4 font-bold text-green-600">{formatCurrency(person.won_revenue)}</td>
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
