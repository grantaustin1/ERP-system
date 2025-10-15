import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, DollarSign, Users, Award, Target, Calendar } from 'lucide-react';
import { toast } from 'sonner';

export default function Commissions() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const response = await axios.get(`${API}/commissions/dashboard`);
      setDashboard(response.data);
    } catch (error) {
      toast.error('Failed to fetch commission dashboard');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => `R ${amount.toFixed(2)}`;
  const formatPercentage = (value) => `${value > 0 ? '+' : ''}${value.toFixed(1)}%`;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-white mb-2" data-testid="commissions-title">Sales Commission Dashboard</h1>
            <p className="text-slate-400">Track consultant performance and commission earnings</p>
          </div>

          {dashboard && (
            <div className="mb-6 flex items-center gap-4 text-slate-300">
              <Calendar className="w-5 h-5" />
              <span>Current: <strong>{dashboard.period.current_month}</strong></span>
              <span className="text-slate-500">vs</span>
              <span>Previous: <strong>{dashboard.period.previous_month}</strong></span>
            </div>
          )}

          {loading ? (
            <div className="text-center text-slate-400 py-12">Loading dashboard...</div>
          ) : dashboard ? (
            <div className="space-y-6">
              {dashboard.consultants.map((consultant, index) => {
                const isTopPerformer = index < 3;
                return (
                  <Card key={consultant.consultant_id} className={`border-2 ${isTopPerformer ? 'border-emerald-500 bg-emerald-900/10' : 'bg-slate-800/50 border-slate-700'}`}>
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-4">
                          {isTopPerformer && (
                            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center">
                              <span className="text-white font-bold text-lg">#{index + 1}</span>
                            </div>
                          )}
                          <div>
                            <CardTitle className="text-white text-xl">{consultant.consultant_name}</CardTitle>
                            {isTopPerformer && <Badge className="mt-1 bg-amber-500">Top Performer</Badge>}
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-slate-400 text-sm">Total Commission</p>
                          <p className="text-emerald-400 font-bold text-2xl">{formatCurrency(consultant.current_month.commission_total)}</p>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {/* Sales Count */}
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <Users className="w-4 h-4 text-blue-400" />
                            <p className="text-slate-400 text-sm">Sales</p>
                          </div>
                          <p className="text-white font-bold text-xl">{consultant.current_month.sales_count}</p>
                          <div className="flex items-center gap-1 mt-1">
                            {consultant.change.sales_count >= 0 ? (
                              <TrendingUp className="w-3 h-3 text-emerald-400" />
                            ) : (
                              <TrendingDown className="w-3 h-3 text-red-400" />
                            )}
                            <span className={`text-xs ${consultant.change.sales_count >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                              {formatPercentage(consultant.change.sales_pct)}
                            </span>
                          </div>
                        </div>

                        {/* Revenue */}
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <DollarSign className="w-4 h-4 text-emerald-400" />
                            <p className="text-slate-400 text-sm">Revenue</p>
                          </div>
                          <p className="text-white font-bold text-xl">{formatCurrency(consultant.current_month.revenue)}</p>
                          <div className="flex items-center gap-1 mt-1">
                            {consultant.change.revenue >= 0 ? (
                              <TrendingUp className="w-3 h-3 text-emerald-400" />
                            ) : (
                              <TrendingDown className="w-3 h-3 text-red-400" />
                            )}
                            <span className={`text-xs ${consultant.change.revenue >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                              {formatPercentage(consultant.change.revenue_pct)}
                            </span>
                          </div>
                        </div>

                        {/* Avg Deal Size */}
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <Award className="w-4 h-4 text-purple-400" />
                            <p className="text-slate-400 text-sm">Avg Deal</p>
                          </div>
                          <p className="text-white font-bold text-lg">{formatCurrency(consultant.current_month.avg_deal_size)}</p>
                        </div>

                        {/* Target Progress */}
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <Target className="w-4 h-4 text-amber-400" />
                            <p className="text-slate-400 text-sm">Target</p>
                          </div>
                          <p className="text-white font-bold text-lg">{consultant.target_progress.toFixed(0)}%</p>
                          <div className="w-full bg-slate-700 rounded-full h-2 mt-2">
                            <div
                              className={`h-2 rounded-full transition-all ${consultant.target_progress >= 100 ? 'bg-emerald-500' : 'bg-amber-500'}`}
                              style={{ width: `${Math.min(consultant.target_progress, 100)}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>

                      {/* Comparison with previous month */}
                      <div className="mt-4 pt-4 border-t border-slate-700 flex items-center justify-between text-sm">
                        <span className="text-slate-400">Previous Month:</span>
                        <span className="text-slate-300">
                          {consultant.previous_month.sales_count} sales • {formatCurrency(consultant.previous_month.revenue)}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            <p className="text-center text-slate-400">No commission data available</p>
          )}
        </div>
      </div>
    </div>
  );
}
