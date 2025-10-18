import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, Users, DollarSign, Calendar, Award, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

export default function Analytics() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/analytics/payment-duration`);
      setAnalytics(response.data);
      toast.success('Analytics loaded successfully');
    } catch (error) {
      toast.error('Failed to load analytics');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex-1 p-8">
          <div className="text-center py-20 text-slate-400">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-emerald-500 mx-auto mb-4"></div>
            Loading analytics...
          </div>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex-1 p-8">
          <div className="text-center py-20 text-slate-400">
            No analytics data available
          </div>
        </div>
      </div>
    );
  }

  const { global_stats, by_membership_type, by_source, top_members, summary } = analytics;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">Payment Analytics Dashboard</h1>
              <p className="text-slate-400">Insights into member payment duration and revenue metrics</p>
            </div>
            <Button
              onClick={fetchAnalytics}
              className="bg-emerald-500 hover:bg-emerald-600"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh Data
            </Button>
          </div>

          {/* Global Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <Card className="bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 border-emerald-500/30 backdrop-blur-lg">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-slate-400 text-sm mb-1">Average Payment Duration</p>
                    <h3 className="text-3xl font-bold text-white">{global_stats.average_payment_months}</h3>
                    <p className="text-emerald-400 text-sm mt-1">months</p>
                  </div>
                  <Calendar className="w-10 h-10 text-emerald-400 opacity-70" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-blue-500/20 to-blue-600/10 border-blue-500/30 backdrop-blur-lg">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-slate-400 text-sm mb-1">Total Paying Members</p>
                    <h3 className="text-3xl font-bold text-white">{global_stats.total_paying_members}</h3>
                    <p className="text-blue-400 text-sm mt-1">active</p>
                  </div>
                  <Users className="w-10 h-10 text-blue-400 opacity-70" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-purple-500/20 to-purple-600/10 border-purple-500/30 backdrop-blur-lg">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-slate-400 text-sm mb-1">Total Revenue</p>
                    <h3 className="text-3xl font-bold text-white">R {global_stats.total_revenue.toFixed(2)}</h3>
                    <p className="text-purple-400 text-sm mt-1">lifetime</p>
                  </div>
                  <DollarSign className="w-10 h-10 text-purple-400 opacity-70" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-amber-500/20 to-amber-600/10 border-amber-500/30 backdrop-blur-lg">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-slate-400 text-sm mb-1">6+ Month Retention</p>
                    <h3 className="text-3xl font-bold text-white">{global_stats.retention_rate_6months}%</h3>
                    <p className="text-amber-400 text-sm mt-1">retention rate</p>
                  </div>
                  <TrendingUp className="w-10 h-10 text-amber-400 opacity-70" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Summary Stats */}
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg mb-8">
            <CardHeader>
              <CardTitle className="text-white">Payment Duration Summary</CardTitle>
              <CardDescription className="text-slate-400">Key metrics across all members</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center p-4 bg-slate-700/30 rounded-lg">
                  <p className="text-slate-400 text-sm mb-2">Longest Duration</p>
                  <p className="text-2xl font-bold text-emerald-400">{summary.longest_paying_member_months} months</p>
                </div>
                <div className="text-center p-4 bg-slate-700/30 rounded-lg">
                  <p className="text-slate-400 text-sm mb-2">Median Duration</p>
                  <p className="text-2xl font-bold text-blue-400">{summary.median_payment_months} months</p>
                </div>
                <div className="text-center p-4 bg-slate-700/30 rounded-lg">
                  <p className="text-slate-400 text-sm mb-2">Shortest Duration</p>
                  <p className="text-2xl font-bold text-amber-400">{summary.shortest_paying_member_months} months</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* By Membership Type */}
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
              <CardHeader>
                <CardTitle className="text-white">By Membership Type</CardTitle>
                <CardDescription className="text-slate-400">Average payment duration per membership plan</CardDescription>
              </CardHeader>
              <CardContent>
                {by_membership_type.length === 0 ? (
                  <p className="text-center py-8 text-slate-400">No data available</p>
                ) : (
                  <div className="space-y-4">
                    {by_membership_type
                      .sort((a, b) => b.avg_months - a.avg_months)
                      .map((type, index) => (
                        <div key={index} className="bg-slate-700/30 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="text-white font-semibold">{type.type_name}</h4>
                            <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/50">
                              {type.avg_months} mo
                            </Badge>
                          </div>
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <p className="text-slate-400">Members</p>
                              <p className="text-white font-medium">{type.member_count}</p>
                            </div>
                            <div>
                              <p className="text-slate-400">Avg Revenue</p>
                              <p className="text-white font-medium">R {type.avg_revenue_per_member.toFixed(2)}</p>
                            </div>
                          </div>
                          {/* Progress bar */}
                          <div className="mt-3 bg-slate-600/30 rounded-full h-2">
                            <div
                              className="bg-emerald-500 h-2 rounded-full transition-all"
                              style={{ width: `${Math.min((type.avg_months / 24) * 100, 100)}%` }}
                            ></div>
                          </div>
                        </div>
                      ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* By Source */}
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
              <CardHeader>
                <CardTitle className="text-white">By Acquisition Source</CardTitle>
                <CardDescription className="text-slate-400">Payment duration by how members found your gym</CardDescription>
              </CardHeader>
              <CardContent>
                {by_source.length === 0 ? (
                  <p className="text-center py-8 text-slate-400">No data available</p>
                ) : (
                  <div className="space-y-4">
                    {by_source
                      .sort((a, b) => b.avg_months - a.avg_months)
                      .map((source, index) => (
                        <div key={index} className="bg-slate-700/30 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="text-white font-semibold">{source.source_name}</h4>
                            <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/50">
                              {source.avg_months} mo
                            </Badge>
                          </div>
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <p className="text-slate-400">Members</p>
                              <p className="text-white font-medium">{source.member_count}</p>
                            </div>
                            <div>
                              <p className="text-slate-400">Avg Revenue</p>
                              <p className="text-white font-medium">R {source.avg_revenue_per_member.toFixed(2)}</p>
                            </div>
                          </div>
                          {/* Progress bar */}
                          <div className="mt-3 bg-slate-600/30 rounded-full h-2">
                            <div
                              className="bg-blue-500 h-2 rounded-full transition-all"
                              style={{ width: `${Math.min((source.avg_months / 24) * 100, 100)}%` }}
                            ></div>
                          </div>
                        </div>
                      ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Top Paying Members */}
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Award className="w-5 h-5 text-amber-400" />
                Top 10 Longest Paying Members
              </CardTitle>
              <CardDescription className="text-slate-400">Members with the longest payment history</CardDescription>
            </CardHeader>
            <CardContent>
              {top_members.length === 0 ? (
                <p className="text-center py-8 text-slate-400">No data available</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="border-b border-slate-600">
                      <tr className="text-left text-slate-400">
                        <th className="p-3">Rank</th>
                        <th className="p-3">Member Name</th>
                        <th className="p-3">Payment Duration</th>
                        <th className="p-3">Total Paid</th>
                      </tr>
                    </thead>
                    <tbody>
                      {top_members.map((member, index) => (
                        <tr key={index} className="border-b border-slate-700/50 hover:bg-slate-700/20">
                          <td className="p-3">
                            <Badge 
                              variant="outline"
                              className={`
                                ${index === 0 ? 'border-amber-500 text-amber-400' : ''}
                                ${index === 1 ? 'border-slate-400 text-slate-300' : ''}
                                ${index === 2 ? 'border-orange-500 text-orange-400' : ''}
                                ${index > 2 ? 'border-slate-600 text-slate-400' : ''}
                              `}
                            >
                              #{index + 1}
                            </Badge>
                          </td>
                          <td className="p-3 text-white font-medium">{member.member_name}</td>
                          <td className="p-3">
                            <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/50">
                              {member.months} months
                            </Badge>
                          </td>
                          <td className="p-3 text-white">R {member.total_paid.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
