import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Activity, 
  TrendingUp, 
  Users, 
  Award,
  AlertCircle,
  CheckCircle,
  Zap
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
  ResponsiveContainer 
} from 'recharts';
import { toast } from 'sonner';

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#f97316', '#ef4444'];

export default function EngagementDashboard() {
  const [overview, setOverview] = useState(null);
  const [memberScore, setMemberScore] = useState(null);
  const [loading, setLoading] = useState(false);
  const [memberId, setMemberId] = useState('');

  useEffect(() => {
    fetchOverview();
  }, []);

  const fetchOverview = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/engagement/overview`);
      setOverview(response.data);
    } catch (error) {
      toast.error('Failed to fetch engagement overview');
    } finally {
      setLoading(false);
    }
  };

  const fetchMemberScore = async (memId) => {
    if (!memId) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`${API}/engagement/score/${memId}`);
      setMemberScore(response.data);
    } catch (error) {
      toast.error('Failed to fetch member engagement score');
    } finally {
      setLoading(false);
    }
  };

  const getLevelColor = (level) => {
    switch (level) {
      case 'Highly Engaged': return 'bg-green-500';
      case 'Engaged': return 'bg-blue-500';
      case 'Moderately Engaged': return 'bg-yellow-500';
      case 'Low Engagement': return 'bg-orange-500';
      case 'At Risk': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getLevelIcon = (level) => {
    switch (level) {
      case 'Highly Engaged': return <CheckCircle className="w-6 h-6 text-green-400" />;
      case 'Engaged': return <Activity className="w-6 h-6 text-blue-400" />;
      case 'Moderately Engaged': return <Zap className="w-6 h-6 text-yellow-400" />;
      case 'Low Engagement': return <AlertCircle className="w-6 h-6 text-orange-400" />;
      case 'At Risk': return <AlertCircle className="w-6 h-6 text-red-400" />;
      default: return <Activity className="w-6 h-6" />;
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
              <Activity className="w-8 h-8 text-blue-400" />
              Engagement Dashboard
            </h1>
            <p className="text-slate-400 mt-2">
              Monitor member engagement levels and activity patterns
            </p>
          </div>

          {/* Overview Summary Cards */}
          {overview && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="pb-2">
                  <CardDescription className="text-slate-400">Total Members</CardDescription>
                  <CardTitle className="text-3xl text-white">
                    {overview.summary.total_members}
                  </CardTitle>
                </CardHeader>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="pb-2">
                  <CardDescription className="text-slate-400">Members Analyzed</CardDescription>
                  <CardTitle className="text-3xl text-blue-400">
                    {overview.summary.members_analyzed}
                  </CardTitle>
                </CardHeader>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="pb-2">
                  <CardDescription className="text-slate-400">Avg Engagement Score</CardDescription>
                  <CardTitle className="text-3xl text-green-400">
                    {overview.summary.avg_engagement_score}%
                  </CardTitle>
                </CardHeader>
              </Card>
            </div>
          )}

          {/* Engagement Distribution Chart */}
          {overview && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white">Engagement Distribution</CardTitle>
                  <CardDescription className="text-slate-400">
                    Members grouped by engagement level
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={overview.by_level}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ level, count }) => `${level}: ${count}`}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="count"
                      >
                        {overview.by_level.map((entry, index) => (
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

              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white">Top Engaged Members</CardTitle>
                  <CardDescription className="text-slate-400">
                    Most active members this period
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {overview.top_engaged_members.slice(0, 5).map((member, idx) => (
                      <div
                        key={member.member_id}
                        className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold text-sm">
                            #{idx + 1}
                          </div>
                          <div>
                            <div className="text-white font-medium">{member.member_name}</div>
                            <div className="text-slate-400 text-xs">{member.email}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-green-400 font-bold">{member.score}</div>
                          <div className="text-slate-400 text-xs">score</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Individual Member Score Calculator */}
          <Card className="bg-slate-800 border-slate-700 mb-8">
            <CardHeader>
              <CardTitle className="text-white">Member Engagement Score</CardTitle>
              <CardDescription className="text-slate-400">
                Calculate detailed engagement score for individual members
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4 mb-6">
                <Input
                  placeholder="Enter Member ID"
                  value={memberId}
                  onChange={(e) => setMemberId(e.target.value)}
                  className="bg-slate-700 border-slate-600 text-white"
                />
                <Button
                  onClick={() => fetchMemberScore(memberId)}
                  disabled={!memberId || loading}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  Calculate Score
                </Button>
              </div>

              {memberScore && (
                <div className="space-y-6">
                  {/* Overall Score Card */}
                  <div className="p-6 bg-gradient-to-r from-slate-700 to-slate-800 rounded-lg border border-slate-600">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        {getLevelIcon(memberScore.level)}
                        <div>
                          <div className="text-2xl font-bold text-white">
                            {memberScore.engagement_score} / {memberScore.max_score}
                          </div>
                          <div className="text-slate-400">Engagement Score</div>
                        </div>
                      </div>
                      <Badge className={`${getLevelColor(memberScore.level)} text-white text-lg px-4 py-2`}>
                        {memberScore.level}
                      </Badge>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full bg-slate-700 rounded-full h-4">
                      <div 
                        className={`h-4 rounded-full ${
                          memberScore.level === 'Highly Engaged' ? 'bg-green-500' :
                          memberScore.level === 'Engaged' ? 'bg-blue-500' :
                          memberScore.level === 'Moderately Engaged' ? 'bg-yellow-500' :
                          memberScore.level === 'Low Engagement' ? 'bg-orange-500' :
                          'bg-red-500'
                        }`}
                        style={{ width: `${memberScore.percentage}%` }}
                      />
                    </div>
                    <div className="text-right text-slate-400 text-sm mt-1">
                      {memberScore.percentage}%
                    </div>
                  </div>

                  {/* Score Breakdown */}
                  <div>
                    <h3 className="text-white font-semibold mb-4">Score Breakdown</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {memberScore.factors.map((factor, idx) => (
                        <div key={idx} className="p-4 bg-slate-700/30 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <div className="text-white font-medium">{factor.factor}</div>
                            <div className="text-blue-400 font-bold">
                              {factor.score}/{factor.max_score}
                            </div>
                          </div>
                          <div className="w-full bg-slate-700 rounded-full h-2 mb-2">
                            <div 
                              className="h-2 rounded-full bg-blue-500"
                              style={{ width: `${(factor.score / factor.max_score) * 100}%` }}
                            />
                          </div>
                          <div className="text-slate-400 text-sm">{factor.details}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Engagement Level Guide */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Engagement Levels Explained</CardTitle>
              <CardDescription className="text-slate-400">
                Understanding engagement score ranges
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                <div className="text-center p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
                  <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-400" />
                  <div className="text-green-400 font-bold mb-1">Highly Engaged</div>
                  <div className="text-slate-300 text-sm">80-100%</div>
                  <div className="text-slate-400 text-xs mt-1">Excellent activity</div>
                </div>

                <div className="text-center p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                  <Activity className="w-8 h-8 mx-auto mb-2 text-blue-400" />
                  <div className="text-blue-400 font-bold mb-1">Engaged</div>
                  <div className="text-slate-300 text-sm">60-79%</div>
                  <div className="text-slate-400 text-xs mt-1">Good participation</div>
                </div>

                <div className="text-center p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                  <Zap className="w-8 h-8 mx-auto mb-2 text-yellow-400" />
                  <div className="text-yellow-400 font-bold mb-1">Moderate</div>
                  <div className="text-slate-300 text-sm">40-59%</div>
                  <div className="text-slate-400 text-xs mt-1">Average activity</div>
                </div>

                <div className="text-center p-4 bg-orange-500/10 border border-orange-500/30 rounded-lg">
                  <AlertCircle className="w-8 h-8 mx-auto mb-2 text-orange-400" />
                  <div className="text-orange-400 font-bold mb-1">Low</div>
                  <div className="text-slate-300 text-sm">20-39%</div>
                  <div className="text-slate-400 text-xs mt-1">Needs attention</div>
                </div>

                <div className="text-center p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                  <AlertCircle className="w-8 h-8 mx-auto mb-2 text-red-400" />
                  <div className="text-red-400 font-bold mb-1">At Risk</div>
                  <div className="text-slate-300 text-sm">0-19%</div>
                  <div className="text-slate-400 text-xs mt-1">Urgent intervention</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
