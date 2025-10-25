import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  TrendingUp, 
  TrendingDown,
  DollarSign,
  Users,
  Target,
  Award,
  ArrowUpRight,
  ArrowDownRight,
  BarChart3,
  Activity,
  Percent
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
  ResponsiveContainer,
  Cell,
  FunnelChart,
  Funnel
} from 'recharts';
import { toast } from 'sonner';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export default function AdvancedSalesAnalytics() {
  const [forecast, setForecast] = useState(null);
  const [teamPerformance, setTeamPerformance] = useState(null);
  const [conversionRates, setConversionRates] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('forecast');

  useEffect(() => {
    if (activeTab === 'forecast' && !forecast) {
      fetchForecast();
    } else if (activeTab === 'team' && !teamPerformance) {
      fetchTeamPerformance();
    } else if (activeTab === 'conversion' && !conversionRates) {
      fetchConversionRates();
    }
  }, [activeTab]);

  const fetchForecast = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/sales/analytics/forecasting`);
      setForecast(response.data);
    } catch (error) {
      toast.error('Failed to fetch sales forecast');
    } finally {
      setLoading(false);
    }
  };

  const fetchTeamPerformance = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/sales/analytics/team-performance`);
      setTeamPerformance(response.data);
    } catch (error) {
      toast.error('Failed to fetch team performance');
    } finally {
      setLoading(false);
    }
  };

  const fetchConversionRates = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/sales/analytics/conversion-rates`);
      setConversionRates(response.data);
    } catch (error) {
      toast.error('Failed to fetch conversion rates');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-ZA', {
      style: 'currency',
      currency: 'ZAR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  return (
    <div className="space-y-6">
      <Card className="bg-gradient-to-br from-blue-900/40 to-purple-900/40 border-blue-500/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <BarChart3 className="w-5 h-5 text-blue-400" />
            Advanced Sales Analytics
          </CardTitle>
          <CardDescription className="text-slate-300">
            Deep insights into forecasting, team performance, and conversion metrics
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3 bg-slate-800/50">
              <TabsTrigger value="forecast" className="data-[state=active]:bg-blue-600">
                <TrendingUp className="w-4 h-4 mr-2" />
                Sales Forecast
              </TabsTrigger>
              <TabsTrigger value="team" className="data-[state=active]:bg-purple-600">
                <Users className="w-4 h-4 mr-2" />
                Team Performance
              </TabsTrigger>
              <TabsTrigger value="conversion" className="data-[state=active]:bg-green-600">
                <Activity className="w-4 h-4 mr-2" />
                Conversion Rates
              </TabsTrigger>
            </TabsList>
            
            {/* Sales Forecast Tab */}
            <TabsContent value="forecast" className="space-y-4 mt-4">
              {loading ? (
                <div className="text-center py-12 text-slate-400">Loading forecast...</div>
              ) : forecast ? (
                <>
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card className="bg-slate-800/50 border-slate-700">
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-xs text-slate-400 uppercase mb-1">Total Forecast</p>
                            <p className="text-2xl font-bold text-white">
                              {formatCurrency(forecast.total_forecast)}
                            </p>
                          </div>
                          <div className="w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center">
                            <DollarSign className="w-6 h-6 text-blue-400" />
                          </div>
                        </div>
                        <Badge className="mt-2 bg-blue-600/50">
                          {forecast.forecast_period_months} months
                        </Badge>
                      </CardContent>
                    </Card>
                    
                    <Card className="bg-slate-800/50 border-slate-700">
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-xs text-slate-400 uppercase mb-1">Historical Revenue</p>
                            <p className="text-2xl font-bold text-white">
                              {formatCurrency(forecast.historical_revenue)}
                            </p>
                          </div>
                          <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center">
                            <TrendingUp className="w-6 h-6 text-green-400" />
                          </div>
                        </div>
                        <Badge className="mt-2 bg-green-600/50">
                          Closed Won
                        </Badge>
                      </CardContent>
                    </Card>
                    
                    <Card className="bg-slate-800/50 border-slate-700">
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-xs text-slate-400 uppercase mb-1">Confidence</p>
                            <p className="text-2xl font-bold text-white capitalize">
                              {forecast.confidence_level}
                            </p>
                          </div>
                          <div className="w-12 h-12 rounded-full bg-yellow-500/20 flex items-center justify-center">
                            <Target className="w-6 h-6 text-yellow-400" />
                          </div>
                        </div>
                        <Badge className="mt-2 bg-yellow-600/50">
                          Based on pipeline
                        </Badge>
                      </CardContent>
                    </Card>
                  </div>
                  
                  {/* Forecast by Stage Chart */}
                  <Card className="bg-slate-800/50 border-slate-700">
                    <CardHeader>
                      <CardTitle className="text-white text-sm">Forecast by Pipeline Stage</CardTitle>
                      <CardDescription className="text-slate-400 text-xs">
                        Weighted forecast based on opportunity probability
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart
                          data={Object.entries(forecast.by_stage).map(([stage, data]) => ({
                            stage: stage.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                            'Total Value': data.total_value,
                            'Weighted Forecast': data.weighted_value,
                            'Opportunities': data.count,
                            'Avg Probability': data.avg_probability
                          }))}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                          <XAxis dataKey="stage" stroke="#94a3b8" angle={-20} textAnchor="end" height={100} />
                          <YAxis stroke="#94a3b8" />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: '#1e293b',
                              border: '1px solid #475569',
                              borderRadius: '8px',
                              color: '#f1f5f9'
                            }}
                            formatter={(value, name) => {
                              if (name === 'Total Value' || name === 'Weighted Forecast') {
                                return formatCurrency(value);
                              }
                              return value;
                            }}
                          />
                          <Legend />
                          <Bar dataKey="Total Value" fill="#3b82f6" />
                          <Bar dataKey="Weighted Forecast" fill="#10b981" />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <div className="text-center py-12 text-slate-400">No forecast data available</div>
              )}
            </TabsContent>
            
            {/* Team Performance Tab */}
            <TabsContent value="team" className="space-y-4 mt-4">
              {loading ? (
                <div className="text-center py-12 text-slate-400">Loading team data...</div>
              ) : teamPerformance ? (
                <>
                  {/* Team Leaderboard */}
                  <Card className="bg-slate-800/50 border-slate-700">
                    <CardHeader>
                      <CardTitle className="text-white text-sm flex items-center gap-2">
                        <Award className="w-4 h-4 text-yellow-400" />
                        Team Leaderboard
                      </CardTitle>
                      <CardDescription className="text-slate-400 text-xs">
                        Top performers ranked by total won value
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {teamPerformance.team_metrics.slice(0, 10).map((member, index) => (
                          <div 
                            key={member.user_id} 
                            className="p-3 bg-slate-700/50 rounded-lg border border-slate-600"
                          >
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-3">
                                <div className={`
                                  w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm
                                  ${index === 0 ? 'bg-yellow-500 text-yellow-900' : ''}
                                  ${index === 1 ? 'bg-slate-400 text-slate-900' : ''}
                                  ${index === 2 ? 'bg-orange-600 text-orange-100' : ''}
                                  ${index > 2 ? 'bg-slate-600 text-slate-200' : ''}
                                `}>
                                  #{index + 1}
                                </div>
                                <div>
                                  <p className="text-white font-semibold text-sm">{member.user_name}</p>
                                  <p className="text-slate-400 text-xs">
                                    {member.leads.total} leads | {member.opportunities.total} opportunities
                                  </p>
                                </div>
                              </div>
                              
                              <div className="text-right">
                                <p className="text-white font-bold text-sm">
                                  {formatCurrency(member.opportunities.total_value)}
                                </p>
                                <Badge className="mt-1 bg-green-600/50 text-xs">
                                  {member.opportunities.win_rate}% win rate
                                </Badge>
                              </div>
                            </div>
                            
                            {/* Metrics Grid */}
                            <div className="grid grid-cols-3 gap-2 mt-2 pt-2 border-t border-slate-600">
                              <div>
                                <p className="text-xs text-slate-400">Conversion</p>
                                <p className="text-sm font-semibold text-white">
                                  {member.leads.conversion_rate}%
                                </p>
                              </div>
                              <div>
                                <p className="text-xs text-slate-400">Won Opps</p>
                                <p className="text-sm font-semibold text-white">
                                  {member.opportunities.won}
                                </p>
                              </div>
                              <div>
                                <p className="text-xs text-slate-400">Task Rate</p>
                                <p className="text-sm font-semibold text-white">
                                  {member.tasks.completion_rate}%
                                </p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <div className="text-center py-12 text-slate-400">No team data available</div>
              )}
            </TabsContent>
            
            {/* Conversion Rates Tab */}
            <TabsContent value="conversion" className="space-y-4 mt-4">
              {loading ? (
                <div className="text-center py-12 text-slate-400">Loading conversion data...</div>
              ) : conversionRates ? (
                <>
                  {/* Lead Conversion Funnel */}
                  <Card className="bg-slate-800/50 border-slate-700">
                    <CardHeader>
                      <CardTitle className="text-white text-sm flex items-center gap-2">
                        <Activity className="w-4 h-4 text-green-400" />
                        Lead Conversion Funnel
                      </CardTitle>
                      <CardDescription className="text-slate-400 text-xs">
                        Stage-to-stage conversion rates
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {Object.entries(conversionRates.lead_funnel).map(([stage, count], index) => {
                          const totalLeads = conversionRates.lead_funnel.new || 1;
                          const percentage = (count / totalLeads * 100).toFixed(1);
                          const conversionKey = index === 0 ? null : 
                            index === 1 ? 'new_to_contacted' :
                            index === 2 ? 'contacted_to_qualified' :
                            index === 3 ? 'qualified_to_converted' : null;
                          const conversionRate = conversionKey ? conversionRates.lead_conversion_rates[conversionKey] : null;
                          
                          return (
                            <div key={stage}>
                              <div className="flex items-center justify-between mb-2">
                                <div className="text-white font-medium capitalize flex items-center gap-2">
                                  {stage}
                                  {conversionRate && (
                                    <Badge className="bg-green-600/50 text-xs">
                                      {conversionRate}% conversion
                                    </Badge>
                                  )}
                                </div>
                                <div className="text-slate-400 text-sm">
                                  {count} leads ({percentage}%)
                                </div>
                              </div>
                              <div className="w-full bg-slate-700 rounded-full h-3 relative overflow-hidden">
                                <div
                                  className="h-3 rounded-full bg-gradient-to-r from-green-500 to-blue-500 transition-all duration-500"
                                  style={{ width: `${percentage}%` }}
                                />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </CardContent>
                  </Card>
                  
                  {/* Opportunity Conversion */}
                  <Card className="bg-slate-800/50 border-slate-700">
                    <CardHeader>
                      <CardTitle className="text-white text-sm flex items-center gap-2">
                        <Percent className="w-4 h-4 text-blue-400" />
                        Opportunity Conversion
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-4">
                        {Object.entries(conversionRates.opportunity_funnel).map(([stage, count]) => (
                          <div key={stage} className="p-3 bg-slate-700/50 rounded border border-slate-600">
                            <p className="text-xs text-slate-400 uppercase mb-1">
                              {stage.replace(/_/g, ' ')}
                            </p>
                            <p className="text-2xl font-bold text-white">{count}</p>
                          </div>
                        ))}
                      </div>
                      
                      {conversionRates.opportunity_conversion_rates && Object.keys(conversionRates.opportunity_conversion_rates).length > 0 && (
                        <div className="mt-4 pt-4 border-t border-slate-700">
                          <p className="text-xs text-slate-400 mb-3">Stage Conversion Rates:</p>
                          <div className="flex flex-wrap gap-2">
                            {Object.entries(conversionRates.opportunity_conversion_rates).map(([key, rate]) => (
                              <Badge key={key} className="bg-blue-600/50">
                                {key.replace(/_/g, ' ')}: {rate}%
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </>
              ) : (
                <div className="text-center py-12 text-slate-400">No conversion data available</div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
