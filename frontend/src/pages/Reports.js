import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  FileText, 
  AlertCircle, 
  Calendar, 
  Download, 
  Users,
  TrendingUp,
  CheckCircle,
  XCircle,
  Clock,
  Award
} from 'lucide-react';
import { toast } from 'sonner';

export default function Reports() {
  const [incompleteDataReport, setIncompleteDataReport] = useState(null);
  const [birthdayReport, setBirthdayReport] = useState(null);
  const [anniversaryReport, setAnniversaryReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [birthdayDays, setBirthdayDays] = useState(30);
  const [anniversaryDays, setAnniversaryDays] = useState(30);
  const [priorityFilter, setPriorityFilter] = useState('all');
  
  const navigate = useNavigate();

  useEffect(() => {
    fetchIncompleteDataReport();
    fetchBirthdayReport(birthdayDays);
    fetchAnniversaryReport(anniversaryDays);
  }, []);

  const fetchIncompleteDataReport = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/reports/incomplete-data`);
      setIncompleteDataReport(response.data);
    } catch (error) {
      toast.error('Failed to fetch incomplete data report');
    } finally {
      setLoading(false);
    }
  };

  const fetchBirthdayReport = async (days) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/reports/birthdays?days_ahead=${days}`);
      setBirthdayReport(response.data);
    } catch (error) {
      toast.error('Failed to fetch birthday report');
    } finally {
      setLoading(false);
    }
  };

  const fetchAnniversaryReport = async (days) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/reports/anniversaries?days_ahead=${days}`);
      setAnniversaryReport(response.data);
    } catch (error) {
      toast.error('Failed to fetch anniversary report');
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'Critical': return 'bg-red-500';
      case 'High': return 'bg-orange-500';
      case 'Medium': return 'bg-yellow-500';
      case 'Low': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  const filteredMembers = incompleteDataReport?.members?.filter(member => {
    if (priorityFilter === 'all') return true;
    return member.priority === priorityFilter;
  }) || [];

  const exportToPDF = (reportType) => {
    toast.info('PDF export feature coming soon');
  };

  const exportToExcel = (reportType) => {
    toast.info('Excel export feature coming soon');
  };

  return (
    <div className="flex h-screen bg-slate-900">
      <Sidebar />
      
      <div className="flex-1 p-8 overflow-auto">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                  <FileText className="w-8 h-8 text-blue-400" />
                  Reports Library
                </h1>
                <p className="text-slate-400 mt-2">
                  Generate and analyze comprehensive member reports
                </p>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <Tabs defaultValue="incomplete" className="space-y-6">
            <TabsList className="bg-slate-800 border-slate-700">
              <TabsTrigger value="incomplete" className="data-[state=active]:bg-slate-700">
                <AlertCircle className="w-4 h-4 mr-2" />
                Incomplete Data
              </TabsTrigger>
              <TabsTrigger value="birthdays" className="data-[state=active]:bg-slate-700">
                <Calendar className="w-4 h-4 mr-2" />
                Birthdays
              </TabsTrigger>
              <TabsTrigger value="anniversaries" className="data-[state=active]:bg-slate-700">
                <Award className="w-4 h-4 mr-2" />
                Anniversaries
              </TabsTrigger>
            </TabsList>

            {/* Incomplete Data Tab */}
            <TabsContent value="incomplete" className="space-y-6">
              {/* Summary Cards */}
              {incompleteDataReport && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <Card className="bg-slate-800 border-slate-700">
                    <CardHeader className="pb-2">
                      <CardDescription className="text-slate-400">Total Members</CardDescription>
                      <CardTitle className="text-2xl text-white">
                        {incompleteDataReport.summary.total_members}
                      </CardTitle>
                    </CardHeader>
                  </Card>
                  
                  <Card className="bg-slate-800 border-slate-700">
                    <CardHeader className="pb-2">
                      <CardDescription className="text-slate-400">Incomplete Data</CardDescription>
                      <CardTitle className="text-2xl text-orange-400">
                        {incompleteDataReport.summary.members_with_incomplete_data}
                      </CardTitle>
                    </CardHeader>
                  </Card>
                  
                  <Card className="bg-slate-800 border-slate-700">
                    <CardHeader className="pb-2">
                      <CardDescription className="text-slate-400">Completion Rate</CardDescription>
                      <CardTitle className="text-2xl text-green-400">
                        {incompleteDataReport.summary.completion_rate}%
                      </CardTitle>
                    </CardHeader>
                  </Card>
                  
                  <Card className="bg-slate-800 border-slate-700">
                    <CardHeader className="pb-2">
                      <CardDescription className="text-slate-400">Critical Priority</CardDescription>
                      <CardTitle className="text-2xl text-red-400">
                        {incompleteDataReport.summary.by_priority.critical}
                      </CardTitle>
                    </CardHeader>
                  </Card>
                </div>
              )}

              {/* Filter and Export */}
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-white">Members with Incomplete Data</CardTitle>
                    <div className="flex items-center gap-4">
                      <Select value={priorityFilter} onValueChange={setPriorityFilter}>
                        <SelectTrigger className="w-40 bg-slate-700 border-slate-600 text-white">
                          <SelectValue placeholder="Filter Priority" />
                        </SelectTrigger>
                        <SelectContent className="bg-slate-800 border-slate-700">
                          <SelectItem value="all" className="text-white">All Priorities</SelectItem>
                          <SelectItem value="Critical" className="text-white">Critical</SelectItem>
                          <SelectItem value="High" className="text-white">High</SelectItem>
                          <SelectItem value="Medium" className="text-white">Medium</SelectItem>
                          <SelectItem value="Low" className="text-white">Low</SelectItem>
                        </SelectContent>
                      </Select>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => exportToPDF('incomplete')}
                        className="border-slate-600 text-slate-300"
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Export PDF
                      </Button>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => exportToExcel('incomplete')}
                        className="border-slate-600 text-slate-300"
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Export Excel
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-700">
                          <th className="text-left py-3 px-4 text-slate-400">Priority</th>
                          <th className="text-left py-3 px-4 text-slate-400">Member</th>
                          <th className="text-left py-3 px-4 text-slate-400">Contact</th>
                          <th className="text-left py-3 px-4 text-slate-400">Missing Fields</th>
                          <th className="text-left py-3 px-4 text-slate-400">Count</th>
                          <th className="text-left py-3 px-4 text-slate-400">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredMembers.map((member) => (
                          <tr key={member.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                            <td className="py-3 px-4">
                              <Badge className={`${getPriorityColor(member.priority)} text-white`}>
                                {member.priority}
                              </Badge>
                            </td>
                            <td className="py-3 px-4">
                              <div className="text-white font-medium">{member.full_name}</div>
                              <div className="text-slate-400 text-xs">{member.membership_status}</div>
                            </td>
                            <td className="py-3 px-4">
                              <div className="text-slate-300 text-xs">{member.email}</div>
                              <div className="text-slate-400 text-xs">{member.phone}</div>
                            </td>
                            <td className="py-3 px-4">
                              <div className="flex flex-wrap gap-1">
                                {member.missing_fields.slice(0, 3).map((field, idx) => (
                                  <span key={idx} className="text-xs bg-slate-700 text-slate-300 px-2 py-1 rounded">
                                    {field}
                                  </span>
                                ))}
                                {member.missing_fields.length > 3 && (
                                  <span className="text-xs text-slate-400">
                                    +{member.missing_fields.length - 3} more
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="py-3 px-4 text-white">{member.missing_count}</td>
                            <td className="py-3 px-4">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => navigate(`/members`)}
                                className="text-blue-400 hover:text-blue-300"
                              >
                                Edit Profile
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    
                    {filteredMembers.length === 0 && (
                      <div className="text-center py-12 text-slate-400">
                        <CheckCircle className="w-16 h-16 mx-auto mb-4 opacity-50" />
                        <p>No members with incomplete data found</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Birthdays Tab */}
            <TabsContent value="birthdays" className="space-y-6">
              {/* Summary Cards */}
              {birthdayReport && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <Card className="bg-slate-800 border-slate-700">
                    <CardHeader className="pb-2">
                      <CardDescription className="text-slate-400">Total Upcoming</CardDescription>
                      <CardTitle className="text-2xl text-white">
                        {birthdayReport.summary.total_upcoming}
                      </CardTitle>
                    </CardHeader>
                  </Card>
                  
                  <Card className="bg-slate-800 border-slate-700">
                    <CardHeader className="pb-2">
                      <CardDescription className="text-slate-400">This Week</CardDescription>
                      <CardTitle className="text-2xl text-blue-400">
                        {birthdayReport.summary.by_period.this_week}
                      </CardTitle>
                    </CardHeader>
                  </Card>
                  
                  <Card className="bg-slate-800 border-slate-700">
                    <CardHeader className="pb-2">
                      <CardDescription className="text-slate-400">Next Week</CardDescription>
                      <CardTitle className="text-2xl text-purple-400">
                        {birthdayReport.summary.by_period.next_week}
                      </CardTitle>
                    </CardHeader>
                  </Card>
                  
                  <Card className="bg-slate-800 border-slate-700">
                    <CardHeader className="pb-2">
                      <CardDescription className="text-slate-400">Later</CardDescription>
                      <CardTitle className="text-2xl text-green-400">
                        {birthdayReport.summary.by_period.later}
                      </CardTitle>
                    </CardHeader>
                  </Card>
                </div>
              )}

              {/* Birthday List */}
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-white flex items-center gap-2">
                        <Calendar className="w-5 h-5 text-blue-400" />
                        Upcoming Birthdays
                      </CardTitle>
                      <CardDescription className="text-slate-400 mt-1">
                        Members celebrating birthdays in the next {birthdayDays} days
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-4">
                      <Select 
                        value={birthdayDays.toString()} 
                        onValueChange={(value) => {
                          const days = parseInt(value);
                          setBirthdayDays(days);
                          fetchBirthdayReport(days);
                        }}
                      >
                        <SelectTrigger className="w-32 bg-slate-700 border-slate-600 text-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-slate-800 border-slate-700">
                          <SelectItem value="7" className="text-white">7 days</SelectItem>
                          <SelectItem value="14" className="text-white">14 days</SelectItem>
                          <SelectItem value="30" className="text-white">30 days</SelectItem>
                          <SelectItem value="60" className="text-white">60 days</SelectItem>
                          <SelectItem value="90" className="text-white">90 days</SelectItem>
                        </SelectContent>
                      </Select>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => exportToPDF('birthdays')}
                        className="border-slate-600 text-slate-300"
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Export
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {birthdayReport && birthdayReport.birthdays.all.length > 0 ? (
                    <div className="space-y-4">
                      {birthdayReport.birthdays.all.map((birthday) => (
                        <div
                          key={birthday.id}
                          className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 transition-colors"
                        >
                          <div className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold text-lg">
                              {birthday.first_name?.[0]}{birthday.last_name?.[0]}
                            </div>
                            <div>
                              <div className="text-white font-medium">{birthday.full_name}</div>
                              <div className="text-slate-400 text-sm">{birthday.email}</div>
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-6">
                            <div className="text-right">
                              <div className="text-white font-medium">{birthday.birthday_date}</div>
                              <div className="text-slate-400 text-sm">Turning {birthday.age_turning}</div>
                            </div>
                            
                            <Badge className="bg-blue-500 text-white">
                              {birthday.days_until === 0 ? 'Today!' : `${birthday.days_until} days`}
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12 text-slate-400">
                      <Calendar className="w-16 h-16 mx-auto mb-4 opacity-50" />
                      <p>No upcoming birthdays in the selected period</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Anniversaries Tab */}
            <TabsContent value="anniversaries" className="space-y-6">
              {/* Summary Cards */}
              {anniversaryReport && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <Card className="bg-slate-800 border-slate-700">
                    <CardHeader className="pb-2">
                      <CardDescription className="text-slate-400">Total Upcoming</CardDescription>
                      <CardTitle className="text-2xl text-white">
                        {anniversaryReport.summary.total_upcoming}
                      </CardTitle>
                    </CardHeader>
                  </Card>
                  
                  <Card className="bg-slate-800 border-slate-700">
                    <CardHeader className="pb-2">
                      <CardDescription className="text-slate-400">1 Year</CardDescription>
                      <CardTitle className="text-2xl text-blue-400">
                        {anniversaryReport.summary.by_milestone['1_year']}
                      </CardTitle>
                    </CardHeader>
                  </Card>
                  
                  <Card className="bg-slate-800 border-slate-700">
                    <CardHeader className="pb-2">
                      <CardDescription className="text-slate-400">5 Years</CardDescription>
                      <CardTitle className="text-2xl text-purple-400">
                        {anniversaryReport.summary.by_milestone['5_years']}
                      </CardTitle>
                    </CardHeader>
                  </Card>
                  
                  <Card className="bg-slate-800 border-slate-700">
                    <CardHeader className="pb-2">
                      <CardDescription className="text-slate-400">10+ Years</CardDescription>
                      <CardTitle className="text-2xl text-yellow-400">
                        {anniversaryReport.summary.by_milestone['10_plus_years']}
                      </CardTitle>
                    </CardHeader>
                  </Card>
                </div>
              )}

              {/* Anniversary List */}
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-white flex items-center gap-2">
                        <Award className="w-5 h-5 text-yellow-400" />
                        Membership Anniversaries
                      </CardTitle>
                      <CardDescription className="text-slate-400 mt-1">
                        Members celebrating milestones in the next {anniversaryDays} days
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-4">
                      <Select 
                        value={anniversaryDays.toString()} 
                        onValueChange={(value) => {
                          const days = parseInt(value);
                          setAnniversaryDays(days);
                          fetchAnniversaryReport(days);
                        }}
                      >
                        <SelectTrigger className="w-32 bg-slate-700 border-slate-600 text-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-slate-800 border-slate-700">
                          <SelectItem value="7" className="text-white">7 days</SelectItem>
                          <SelectItem value="14" className="text-white">14 days</SelectItem>
                          <SelectItem value="30" className="text-white">30 days</SelectItem>
                          <SelectItem value="60" className="text-white">60 days</SelectItem>
                          <SelectItem value="90" className="text-white">90 days</SelectItem>
                        </SelectContent>
                      </Select>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => exportToPDF('anniversaries')}
                        className="border-slate-600 text-slate-300"
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Export
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {anniversaryReport && anniversaryReport.anniversaries.all.length > 0 ? (
                    <div className="space-y-4">
                      {anniversaryReport.anniversaries.all.map((anniversary) => (
                        <div
                          key={anniversary.id}
                          className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 transition-colors"
                        >
                          <div className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-yellow-500 to-orange-500 flex items-center justify-center text-white font-bold text-lg">
                              {anniversary.first_name?.[0]}{anniversary.last_name?.[0]}
                            </div>
                            <div>
                              <div className="text-white font-medium">{anniversary.full_name}</div>
                              <div className="text-slate-400 text-sm">{anniversary.email}</div>
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-6">
                            <div className="text-right">
                              <div className="text-white font-medium">{anniversary.anniversary_date}</div>
                              <div className="text-slate-400 text-sm">Joined {anniversary.join_date?.split('T')[0]}</div>
                            </div>
                            
                            <Badge className="bg-yellow-500 text-slate-900 font-bold">
                              {anniversary.years_completing} {anniversary.years_completing === 1 ? 'Year' : 'Years'}
                            </Badge>
                            
                            <Badge className="bg-blue-500 text-white">
                              {anniversary.days_until === 0 ? 'Today!' : `${anniversary.days_until} days`}
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12 text-slate-400">
                      <Award className="w-16 h-16 mx-auto mb-4 opacity-50" />
                      <p>No upcoming anniversaries in the selected period</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
