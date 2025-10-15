import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, UserCheck, Ban, FileText, TrendingUp, Activity } from 'lucide-react';
import { toast } from 'sonner';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setStats(response.data);
    } catch (error) {
      toast.error('Failed to fetch dashboard stats');
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    { title: 'Total Members', value: stats?.total_members || 0, icon: Users, color: 'from-blue-500 to-cyan-600' },
    { title: 'Active Members', value: stats?.active_members || 0, icon: UserCheck, color: 'from-emerald-500 to-teal-600' },
    { title: 'Blocked Members', value: stats?.blocked_members || 0, icon: Ban, color: 'from-red-500 to-orange-600' },
    { title: 'Pending Invoices', value: stats?.pending_invoices || 0, icon: FileText, color: 'from-amber-500 to-yellow-600' },
    { title: 'Total Revenue', value: `R ${stats?.total_revenue?.toFixed(2) || 0}`, icon: TrendingUp, color: 'from-purple-500 to-pink-600' },
    { title: "Today's Access", value: stats?.today_access_count || 0, icon: Activity, color: 'from-indigo-500 to-blue-600' },
  ];

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-white mb-2" data-testid="dashboard-title">Dashboard</h1>
            <p className="text-slate-400">Welcome to GymAccess Hub Management System</p>
          </div>

          {loading ? (
            <div className="text-center text-slate-400 py-12">Loading stats...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {statCards.map((stat, index) => {
                const Icon = stat.icon;
                return (
                  <Card key={index} className="bg-slate-800/50 border-slate-700 backdrop-blur-lg hover:bg-slate-800/70 transition-all duration-300" data-testid={`stat-card-${index}`}>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-sm font-medium text-slate-400">{stat.title}</CardTitle>
                      <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${stat.color} flex items-center justify-center`}>
                        <Icon className="w-5 h-5 text-white" />
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold text-white">{stat.value}</div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}

          <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
              <CardHeader>
                <CardTitle className="text-white">Quick Actions</CardTitle>
                <CardDescription className="text-slate-400">Manage your gym operations</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <button
                  onClick={() => navigate('/members')}
                  className="w-full text-left p-4 rounded-lg bg-slate-700/50 hover:bg-slate-700 transition-colors text-white"
                  data-testid="quick-action-members"
                >
                  <Users className="inline-block w-5 h-5 mr-3 text-emerald-400" />
                  Manage Members
                </button>
                <button
                  onClick={() => navigate('/access')}
                  className="w-full text-left p-4 rounded-lg bg-slate-700/50 hover:bg-slate-700 transition-colors text-white"
                  data-testid="quick-action-access"
                >
                  <Activity className="inline-block w-5 h-5 mr-3 text-blue-400" />
                  Access Control
                </button>
                <button
                  onClick={() => navigate('/billing')}
                  className="w-full text-left p-4 rounded-lg bg-slate-700/50 hover:bg-slate-700 transition-colors text-white"
                  data-testid="quick-action-billing"
                >
                  <FileText className="inline-block w-5 h-5 mr-3 text-purple-400" />
                  Billing & Invoices
                </button>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
              <CardHeader>
                <CardTitle className="text-white">System Overview</CardTitle>
                <CardDescription className="text-slate-400">Real-time gym statistics</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Active Rate</span>
                    <span className="text-white font-semibold">
                      {stats?.total_members > 0 ? ((stats?.active_members / stats?.total_members) * 100).toFixed(1) : 0}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-emerald-500 to-teal-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${stats?.total_members > 0 ? (stats?.active_members / stats?.total_members) * 100 : 0}%` }}
                    ></div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}