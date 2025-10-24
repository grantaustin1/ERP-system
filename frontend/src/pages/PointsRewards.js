import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Award, 
  TrendingUp, 
  Gift, 
  Star, 
  Trophy,
  Calendar,
  Plus,
  Minus
} from 'lucide-react';
import { toast } from 'sonner';

export default function PointsRewards() {
  const [leaderboard, setLeaderboard] = useState(null);
  const [selectedMember, setSelectedMember] = useState(null);
  const [memberBalance, setMemberBalance] = useState(null);
  const [memberTransactions, setMemberTransactions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [memberId, setMemberId] = useState('');

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  const fetchLeaderboard = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/engagement/points/leaderboard?limit=20`);
      setLeaderboard(response.data);
    } catch (error) {
      toast.error('Failed to fetch leaderboard');
    } finally {
      setLoading(false);
    }
  };

  const fetchMemberPoints = async (memId) => {
    if (!memId) return;
    
    setLoading(true);
    try {
      const [balanceRes, transactionsRes] = await Promise.all([
        axios.get(`${API}/engagement/points/balance/${memId}`),
        axios.get(`${API}/engagement/points/transactions/${memId}?limit=20`)
      ]);
      
      setMemberBalance(balanceRes.data);
      setMemberTransactions(transactionsRes.data);
      setSelectedMember(memId);
    } catch (error) {
      toast.error('Failed to fetch member points');
    } finally {
      setLoading(false);
    }
  };

  const getMedalIcon = (rank) => {
    if (rank === 1) return <Trophy className="w-6 h-6 text-yellow-400" />;
    if (rank === 2) return <Award className="w-6 h-6 text-slate-300" />;
    if (rank === 3) return <Award className="w-6 h-6 text-orange-400" />;
    return <Star className="w-5 h-5 text-slate-500" />;
  };

  const getTransactionIcon = (type) => {
    switch (type) {
      case 'earned': return <Plus className="w-4 h-4 text-green-400" />;
      case 'redeemed': return <Minus className="w-4 h-4 text-red-400" />;
      default: return <Gift className="w-4 h-4 text-blue-400" />;
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
              <Award className="w-8 h-8 text-yellow-400" />
              Points & Rewards
            </h1>
            <p className="text-slate-400 mt-2">
              Track member rewards and engagement points
            </p>
          </div>

          {/* Member Points Lookup */}
          <Card className="bg-slate-800 border-slate-700 mb-8">
            <CardHeader>
              <CardTitle className="text-white">Member Points Lookup</CardTitle>
              <CardDescription className="text-slate-400">
                Enter member ID to view their points balance and transaction history
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4">
                <Input
                  placeholder="Enter Member ID"
                  value={memberId}
                  onChange={(e) => setMemberId(e.target.value)}
                  className="bg-slate-700 border-slate-600 text-white"
                />
                <Button
                  onClick={() => fetchMemberPoints(memberId)}
                  disabled={!memberId || loading}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  Search
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Member Points Details */}
          {memberBalance && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
              <Card className="bg-gradient-to-br from-blue-600 to-blue-800 border-0">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Award className="w-5 h-5" />
                    Current Balance
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-4xl font-bold text-white">
                    {memberBalance.total_points.toLocaleString()}
                  </div>
                  <div className="text-blue-100 text-sm mt-1">points available</div>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-purple-600 to-purple-800 border-0">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <TrendingUp className="w-5 h-5" />
                    Lifetime Points
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-4xl font-bold text-white">
                    {memberBalance.lifetime_points.toLocaleString()}
                  </div>
                  <div className="text-purple-100 text-sm mt-1">earned total</div>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-green-600 to-green-800 border-0">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Gift className="w-5 h-5" />
                    Rewards Used
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-4xl font-bold text-white">
                    {(memberBalance.lifetime_points - memberBalance.total_points).toLocaleString()}
                  </div>
                  <div className="text-green-100 text-sm mt-1">points redeemed</div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Transaction History */}
          {memberTransactions && memberTransactions.transactions.length > 0 && (
            <Card className="bg-slate-800 border-slate-700 mb-8">
              <CardHeader>
                <CardTitle className="text-white">Transaction History</CardTitle>
                <CardDescription className="text-slate-400">
                  Recent points activity for selected member
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {memberTransactions.transactions.map((txn) => (
                    <div
                      key={txn.id}
                      className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center">
                          {getTransactionIcon(txn.transaction_type)}
                        </div>
                        <div>
                          <div className="text-white font-medium">{txn.reason}</div>
                          <div className="text-slate-400 text-sm flex items-center gap-2">
                            <Calendar className="w-3 h-3" />
                            {new Date(txn.created_at).toLocaleString()}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`text-lg font-bold ${
                          txn.transaction_type === 'earned' ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {txn.transaction_type === 'earned' ? '+' : '-'}{txn.points}
                        </div>
                        <Badge className={`${
                          txn.transaction_type === 'earned' ? 'bg-green-500' : 'bg-red-500'
                        } text-white text-xs`}>
                          {txn.transaction_type}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Leaderboard */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Trophy className="w-5 h-5 text-yellow-400" />
                    Points Leaderboard
                  </CardTitle>
                  <CardDescription className="text-slate-400 mt-1">
                    Top members by total points
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {leaderboard && leaderboard.leaderboard.length > 0 ? (
                <div className="space-y-3">
                  {leaderboard.leaderboard.map((member, idx) => (
                    <div
                      key={member.member_id}
                      className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 transition-colors"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                          {getMedalIcon(idx + 1)}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-white font-bold text-lg">#{idx + 1}</span>
                            <span className="text-white font-medium">{member.member_name}</span>
                          </div>
                          <div className="text-slate-400 text-sm">
                            {member.email} • {member.membership_type || 'No Type'}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-yellow-400">
                          {member.total_points.toLocaleString()}
                        </div>
                        <div className="text-slate-400 text-sm">
                          {member.lifetime_points.toLocaleString()} lifetime
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-slate-400">
                  <Trophy className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p>No leaderboard data available</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Points Earning Guide */}
          <Card className="bg-slate-800 border-slate-700 mt-8">
            <CardHeader>
              <CardTitle className="text-white">How to Earn Points</CardTitle>
              <CardDescription className="text-slate-400">
                Members automatically earn points through these activities
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="flex flex-col items-center text-center p-4 bg-slate-700/30 rounded-lg">
                  <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center mb-3">
                    <Award className="w-6 h-6 text-green-400" />
                  </div>
                  <div className="text-white font-semibold mb-1">Check-In Reward</div>
                  <div className="text-3xl font-bold text-green-400 mb-1">5</div>
                  <div className="text-slate-400 text-sm">points per visit</div>
                </div>

                <div className="flex flex-col items-center text-center p-4 bg-slate-700/30 rounded-lg">
                  <div className="w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center mb-3">
                    <Gift className="w-6 h-6 text-blue-400" />
                  </div>
                  <div className="text-white font-semibold mb-1">Payment Completed</div>
                  <div className="text-3xl font-bold text-blue-400 mb-1">10</div>
                  <div className="text-slate-400 text-sm">points per payment</div>
                </div>

                <div className="flex flex-col items-center text-center p-4 bg-slate-700/30 rounded-lg">
                  <div className="w-12 h-12 rounded-full bg-purple-500/20 flex items-center justify-center mb-3">
                    <Star className="w-6 h-6 text-purple-400" />
                  </div>
                  <div className="text-white font-semibold mb-1">More Coming Soon</div>
                  <div className="text-3xl font-bold text-purple-400 mb-1">?</div>
                  <div className="text-slate-400 text-sm">referrals, milestones</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
