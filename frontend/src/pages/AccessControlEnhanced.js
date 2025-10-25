import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { 
  Scan, Fingerprint, ScanFace, UserCheck, UserX, Clock, 
  TrendingUp, Activity, BarChart3, MapPin, Shield, CheckCircle2, XCircle, Search, KeyRound
} from 'lucide-react';
import { toast } from 'sonner';

const ACCESS_METHODS = [
  { value: 'qr_code', label: 'QR Code', icon: Scan },
  { value: 'rfid', label: 'RFID Card', icon: Shield },
  { value: 'fingerprint', label: 'Fingerprint', icon: Fingerprint },
  { value: 'facial_recognition', label: 'Facial Recognition', icon: ScanFace },
  { value: 'manual_override', label: 'Manual Override', icon: UserCheck },
  { value: 'mobile_app', label: 'Mobile App', icon: Activity }
];

const LOCATIONS = [
  'Main Entrance',
  'Studio A',
  'Studio B',
  'Locker Room - Men',
  'Locker Room - Women',
  'Swimming Pool',
  'Gym Floor',
  'Cardio Zone',
  'Weight Room'
];

function AccessControlEnhanced() {
  const [activeTab, setActiveTab] = useState('check-in');
  const [members, setMembers] = useState([]);
  const [accessLogs, setAccessLogs] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCheckinDialog, setShowCheckinDialog] = useState(false);
  const [accessResult, setAccessResult] = useState(null);
  
  // Manual Override state
  const [showOverrideDialog, setShowOverrideDialog] = useState(false);
  const [overrideReasons, setOverrideReasons] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedMember, setSelectedMember] = useState(null);
  const [overrideForm, setOverrideForm] = useState({
    member_id: '',
    first_name: '',
    last_name: '',
    phone: '',
    email: '',
    reason_id: '',
    sub_reason_id: '',
    access_pin: '',
    location: 'Main Entrance',
    notes: ''
  });
  
  const [checkinForm, setCheckinForm] = useState({
    member_id: '',
    access_method: 'manual_override',
    location: 'Main Entrance',
    notes: ''
  });

  const [quickSearchQuery, setQuickSearchQuery] = useState('');

  const [logFilters, setLogFilters] = useState({
    status: '',
    location: '',
    limit: 100
  });

  const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8001' 
    : process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchMembers();
    fetchAccessLogs();
    fetchAnalytics();
  }, []);

  useEffect(() => {
    fetchAccessLogs();
  }, [logFilters]);

  const fetchMembers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/members`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setMembers(data);
      }
    } catch (error) {
      console.error('Failed to fetch members:', error);
    }
  };

  const fetchAccessLogs = async () => {
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      if (logFilters.status) params.append('status', logFilters.status);
      if (logFilters.location) params.append('location', logFilters.location);
      params.append('limit', logFilters.limit);

      const response = await fetch(`${API_URL}/api/access/logs?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setAccessLogs(data);
      }
    } catch (error) {
      console.error('Failed to fetch access logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/access/analytics`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    }
  };

  // Manual Override functions
  const fetchOverrideReasons = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/override-reasons/hierarchical`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setOverrideReasons(data);
      }
    } catch (error) {
      console.error('Failed to fetch override reasons:', error);
    }
  };

  const handleMemberSearch = async (query) => {
    setSearchQuery(query);
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/members/search?q=${encodeURIComponent(query)}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setSearchResults(data);
      }
    } catch (error) {
      console.error('Failed to search members:', error);
    }
  };

  const handleSelectMember = (member) => {
    setSelectedMember(member);
    setOverrideForm({
      ...overrideForm,
      member_id: member.id,
      first_name: member.first_name,
      last_name: member.last_name,
      phone: member.phone,
      email: member.email
    });
    setSearchResults([]);
    setSearchQuery(`${member.first_name} ${member.last_name}`);
  };

  const handleGrantOverride = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Validate
      if (!overrideForm.reason_id) {
        toast.error('Please select an override reason');
        return;
      }

      const selectedReason = overrideReasons.find(r => r.reason_id === overrideForm.reason_id);
      if (selectedReason?.sub_reasons?.length > 0 && !overrideForm.sub_reason_id) {
        toast.error('Please select a sub-reason');
        return;
      }

      if (selectedReason?.requires_pin && !overrideForm.access_pin && overrideForm.member_id) {
        toast.error('PIN is required for this override reason');
        return;
      }

      if (!overrideForm.member_id && (!overrideForm.first_name || !overrideForm.last_name)) {
        toast.error('Please search for a member or enter new prospect details');
        return;
      }

      const response = await fetch(`${API_URL}/api/access/override`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(overrideForm)
      });

      const result = await response.json();
      
      if (response.ok) {
        toast.success(result.is_new_prospect ? 'New prospect access granted!' : 'Access override granted!');
        setShowOverrideDialog(false);
        setOverrideForm({
          member_id: '',
          first_name: '',
          last_name: '',
          phone: '',
          email: '',
          reason_id: '',
          sub_reason_id: '',
          access_pin: '',
          location: 'Main Entrance',
          notes: ''
        });
        setSelectedMember(null);
        setSearchQuery('');
        setSearchResults([]);
        fetchAccessLogs();
      } else {
        toast.error(result.detail || 'Failed to grant override');
      }
    } catch (error) {
      console.error('Failed to grant override:', error);
      toast.error('Failed to grant override');
    }
  };

  const openOverrideDialog = () => {
    fetchOverrideReasons();
    setShowOverrideDialog(true);
  };

  const handleQuickCheckin = async (memberId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/access/quick-checkin?member_id=${memberId}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      const result = await response.json();
      setAccessResult(result);
      
      if (result.access === 'granted') {
        alert('✓ Access Granted!');
      } else {
        alert(`✗ Access Denied: ${result.reason}`);
      }
      
      await fetchAccessLogs();
      await fetchAnalytics();
    } catch (error) {
      console.error('Check-in failed:', error);
      alert('Check-in failed');
    }
  };

  const handleManualCheckin = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/access/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(checkinForm)
      });

      const result = await response.json();
      setAccessResult(result);
      
      if (result.access === 'granted') {
        alert('✓ Access Granted!');
        setShowCheckinDialog(false);
        resetCheckinForm();
      } else {
        alert(`✗ Access Denied: ${result.reason}`);
      }
      
      await fetchAccessLogs();
      await fetchAnalytics();
    } catch (error) {
      console.error('Check-in failed:', error);
      alert('Check-in failed');
    }
  };

  const resetCheckinForm = () => {
    setCheckinForm({
      member_id: '',
      access_method: 'manual_override',
      location: 'Main Entrance',
      notes: ''
    });
  };

  const getStatusBadge = (status) => {
    if (status === 'granted') {
      return <Badge className="bg-green-100 text-green-800"><CheckCircle2 className="h-3 w-3 mr-1" /> Granted</Badge>;
    }
    return <Badge className="bg-red-100 text-red-800"><XCircle className="h-3 w-3 mr-1" /> Denied</Badge>;
  };

  const getMethodIcon = (method) => {
    const methodObj = ACCESS_METHODS.find(m => m.value === method);
    if (methodObj) {
      const Icon = methodObj.icon;
      return <Icon className="h-4 w-4" />;
    }
    return <Activity className="h-4 w-4" />;
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Access Control & Check-ins</h1>
        <div className="flex gap-2">
          <Button onClick={openOverrideDialog} variant="outline">
            <KeyRound className="mr-2 h-4 w-4" /> Manual Override
          </Button>
          <Button onClick={() => setShowCheckinDialog(true)}>
            <UserCheck className="mr-2 h-4 w-4" /> Manual Check-in
          </Button>
        </div>
      </div>

      <Dialog open={showCheckinDialog} onOpenChange={setShowCheckinDialog}>
        <DialogContent>
            <DialogHeader>
              <DialogTitle>Manual Check-in</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleManualCheckin} className="space-y-4">
              <div>
                <Label htmlFor="member_id">Member *</Label>
                <Select 
                  value={checkinForm.member_id} 
                  onValueChange={(value) => setCheckinForm({ ...checkinForm, member_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select member" />
                  </SelectTrigger>
                  <SelectContent>
                    {members.map(member => (
                      <SelectItem key={member.id} value={member.id}>
                        {member.first_name} {member.last_name} - {member.email}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="access_method">Access Method *</Label>
                <Select 
                  value={checkinForm.access_method} 
                  onValueChange={(value) => setCheckinForm({ ...checkinForm, access_method: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ACCESS_METHODS.map(method => (
                      <SelectItem key={method.value} value={method.value}>
                        {method.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="location">Location</Label>
                <Select 
                  value={checkinForm.location} 
                  onValueChange={(value) => setCheckinForm({ ...checkinForm, location: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {LOCATIONS.map(location => (
                      <SelectItem key={location} value={location}>
                        {location}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="notes">Notes</Label>
                <Input
                  id="notes"
                  value={checkinForm.notes}
                  onChange={(e) => setCheckinForm({ ...checkinForm, notes: e.target.value })}
                  placeholder="Optional notes"
                />
              </div>

              <div className="flex justify-end space-x-2">
                <Button type="button" variant="outline" onClick={() => { setShowCheckinDialog(false); resetCheckinForm(); }}>
                  Cancel
                </Button>
                <Button type="submit">Check In</Button>
              </div>
            </form>
        </DialogContent>
      </Dialog>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="check-in">Quick Check-in</TabsTrigger>
          <TabsTrigger value="logs">Access Logs</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="check-in" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Quick Member Check-in</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex space-x-2">
                  <Input
                    placeholder="Search members by name or email..."
                    className="flex-1"
                    id="member-search"
                    value={quickSearchQuery}
                    onChange={(e) => setQuickSearchQuery(e.target.value)}
                  />
                  <Button variant="outline" onClick={() => setQuickSearchQuery('')}>
                    <Search className="h-4 w-4" />
                  </Button>
                </div>

                <div className="grid gap-3 max-h-[500px] overflow-y-auto">
                  {members
                    .filter(m => m.membership_status === 'active')
                    .filter(m => {
                      if (!quickSearchQuery) return true;
                      const query = quickSearchQuery.toLowerCase();
                      return (
                        m.first_name?.toLowerCase().includes(query) ||
                        m.last_name?.toLowerCase().includes(query) ||
                        m.email?.toLowerCase().includes(query) ||
                        m.phone?.toLowerCase().includes(query)
                      );
                    })
                    .slice(0, 20)
                    .map(member => (
                    <Card key={member.id} className="border-l-4 border-l-blue-500">
                      <CardContent className="py-3">
                        <div className="flex justify-between items-center">
                          <div>
                            <h4 className="font-semibold">
                              {member.first_name} {member.last_name}
                            </h4>
                            <p className="text-sm text-gray-600">{member.email}</p>
                            <p className="text-xs text-gray-500">
                              Status: <span className="font-medium">{member.membership_status}</span>
                            </p>
                          </div>
                          <Button onClick={() => handleQuickCheckin(member.id)}>
                            <UserCheck className="h-4 w-4 mr-2" /> Check In
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                  {members
                    .filter(m => m.membership_status === 'active')
                    .filter(m => {
                      if (!quickSearchQuery) return true;
                      const query = quickSearchQuery.toLowerCase();
                      return (
                        m.first_name?.toLowerCase().includes(query) ||
                        m.last_name?.toLowerCase().includes(query) ||
                        m.email?.toLowerCase().includes(query) ||
                        m.phone?.toLowerCase().includes(query)
                      );
                    }).length === 0 && quickSearchQuery && (
                    <div className="text-center py-8 text-gray-500">
                      <p>No members found matching "{quickSearchQuery}"</p>
                      <p className="text-sm mt-2">Try adjusting your search or use Manual Override</p>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Access Logs</CardTitle>
              <div className="flex space-x-2 mt-4">
                <Select value={logFilters.status} onValueChange={(value) => setLogFilters({ ...logFilters, status: value })}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="All statuses" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All statuses</SelectItem>
                    <SelectItem value="granted">Granted</SelectItem>
                    <SelectItem value="denied">Denied</SelectItem>
                  </SelectContent>
                </Select>

                <Select value={logFilters.location} onValueChange={(value) => setLogFilters({ ...logFilters, location: value })}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="All locations" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All locations</SelectItem>
                    {LOCATIONS.map(location => (
                      <SelectItem key={location} value={location}>{location}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Button variant="outline" onClick={fetchAccessLogs}>Refresh</Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Time</th>
                      <th className="text-left p-2">Member</th>
                      <th className="text-left p-2">Method</th>
                      <th className="text-left p-2">Location</th>
                      <th className="text-left p-2">Status</th>
                      <th className="text-left p-2">Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {accessLogs.map(log => (
                      <tr key={log.id} className="border-b hover:bg-gray-50">
                        <td className="p-2 text-sm">
                          <div className="flex items-center">
                            <Clock className="h-4 w-4 mr-2 text-gray-400" />
                            {new Date(log.timestamp).toLocaleString()}
                          </div>
                        </td>
                        <td className="p-2">
                          <div>
                            <div className="font-medium">{log.member_name}</div>
                            <div className="text-xs text-gray-500">{log.membership_type}</div>
                          </div>
                        </td>
                        <td className="p-2">
                          <div className="flex items-center space-x-2">
                            {getMethodIcon(log.access_method)}
                            <span className="text-sm">{log.access_method.replace('_', ' ')}</span>
                          </div>
                        </td>
                        <td className="p-2">
                          <div className="flex items-center">
                            <MapPin className="h-4 w-4 mr-2 text-gray-400" />
                            <span className="text-sm">{log.location || 'N/A'}</span>
                          </div>
                        </td>
                        <td className="p-2">{getStatusBadge(log.status)}</td>
                        <td className="p-2 text-sm text-gray-600">{log.reason || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {accessLogs.length === 0 && (
                  <div className="text-center py-12">
                    <p className="text-gray-600">No access logs found</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          {analytics && (
            <>
              <div className="grid gap-4 md:grid-cols-4">
                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600">Total Attempts</p>
                        <p className="text-2xl font-bold">{analytics.total_attempts}</p>
                      </div>
                      <Activity className="h-8 w-8 text-blue-500" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600">Access Granted</p>
                        <p className="text-2xl font-bold text-green-600">{analytics.granted_count}</p>
                      </div>
                      <CheckCircle2 className="h-8 w-8 text-green-500" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600">Access Denied</p>
                        <p className="text-2xl font-bold text-red-600">{analytics.denied_count}</p>
                      </div>
                      <XCircle className="h-8 w-8 text-red-500" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600">Success Rate</p>
                        <p className="text-2xl font-bold">{analytics.success_rate}%</p>
                      </div>
                      <TrendingUp className="h-8 w-8 text-purple-500" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Access by Method</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {analytics.access_by_method.map(item => (
                        <div key={item._id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                          <span className="capitalize">{item._id?.replace('_', ' ')}</span>
                          <Badge>{item.count}</Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Access by Location</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {analytics.access_by_location.map(item => (
                        <div key={item._id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                          <span>{item._id}</span>
                          <Badge>{item.count}</Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Denied Reasons</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {analytics.denied_reasons.map(item => (
                        <div key={item._id} className="flex justify-between items-center p-2 bg-red-50 rounded">
                          <span className="text-sm">{item._id}</span>
                          <Badge variant="destructive">{item.count}</Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Top Members (Check-ins)</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {analytics.top_members.map((item, index) => (
                        <div key={item._id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-gray-400">#{index + 1}</span>
                            <span>{item.member_name}</span>
                          </div>
                          <Badge variant="secondary">{item.check_in_count} check-ins</Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </>
          )}
        </TabsContent>
      </Tabs>

      {/* Manual Override Dialog */}
      <Dialog open={showOverrideDialog} onOpenChange={setShowOverrideDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <KeyRound className="h-5 w-5" />
              Manual Access Override
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            {/* Member Search */}
            <div className="space-y-2">
              <Label>Search Member (Name, Email, Phone, ID)</Label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  value={searchQuery}
                  onChange={(e) => handleMemberSearch(e.target.value)}
                  placeholder="Type to search..."
                  className="pl-10"
                />
              </div>
              {searchResults.length > 0 && (
                <div className="border rounded-md max-h-48 overflow-y-auto">
                  {searchResults.map((member) => (
                    <div
                      key={member.id}
                      onClick={() => handleSelectMember(member)}
                      className="p-3 hover:bg-gray-100 cursor-pointer border-b last:border-b-0"
                    >
                      <div className="font-medium">{member.first_name} {member.last_name}</div>
                      <div className="text-sm text-gray-500">{member.email} • {member.phone}</div>
                      <Badge variant={member.status_label === 'Active' ? 'default' : 'destructive'}>
                        {member.status_label}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Selected Member or New Prospect */}
            {selectedMember ? (
              <Card className="bg-blue-50">
                <CardContent className="p-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-bold">{selectedMember.first_name} {selectedMember.last_name}</div>
                      <div className="text-sm text-gray-600">{selectedMember.email}</div>
                      <div className="text-sm text-gray-600">{selectedMember.phone}</div>
                    </div>
                    <Badge variant={selectedMember.status_label === 'Active' ? 'default' : 'destructive'}>
                      {selectedMember.status_label}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card className="bg-yellow-50">
                <CardContent className="p-4">
                  <div className="text-sm font-medium mb-2">New Prospect - Enter Details:</div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label className="text-xs">First Name *</Label>
                      <Input
                        value={overrideForm.first_name}
                        onChange={(e) => setOverrideForm({...overrideForm, first_name: e.target.value})}
                        placeholder="First name"
                        size="sm"
                      />
                    </div>
                    <div>
                      <Label className="text-xs">Last Name *</Label>
                      <Input
                        value={overrideForm.last_name}
                        onChange={(e) => setOverrideForm({...overrideForm, last_name: e.target.value})}
                        placeholder="Last name"
                        size="sm"
                      />
                    </div>
                    <div>
                      <Label className="text-xs">Phone</Label>
                      <Input
                        value={overrideForm.phone}
                        onChange={(e) => setOverrideForm({...overrideForm, phone: e.target.value})}
                        placeholder="Phone"
                        size="sm"
                      />
                    </div>
                    <div>
                      <Label className="text-xs">Email</Label>
                      <Input
                        value={overrideForm.email}
                        onChange={(e) => setOverrideForm({...overrideForm, email: e.target.value})}
                        placeholder="Email"
                        size="sm"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Override Reason */}
            <div className="space-y-2">
              <Label>Override Reason *</Label>
              <Select 
                value={overrideForm.reason_id} 
                onValueChange={(value) => {
                  setOverrideForm({...overrideForm, reason_id: value, sub_reason_id: ''});
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select reason" />
                </SelectTrigger>
                <SelectContent>
                  {overrideReasons.map((reason) => (
                    <SelectItem key={reason.reason_id} value={reason.reason_id}>
                      {reason.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Sub-reason (conditional) */}
            {overrideForm.reason_id && overrideReasons.find(r => r.reason_id === overrideForm.reason_id)?.sub_reasons?.length > 0 && (
              <div className="space-y-2">
                <Label>Sub-Reason *</Label>
                <Select 
                  value={overrideForm.sub_reason_id} 
                  onValueChange={(value) => setOverrideForm({...overrideForm, sub_reason_id: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select sub-reason" />
                  </SelectTrigger>
                  <SelectContent>
                    {overrideReasons.find(r => r.reason_id === overrideForm.reason_id)?.sub_reasons?.map((subReason) => (
                      <SelectItem key={subReason.reason_id} value={subReason.reason_id}>
                        {subReason.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* PIN Input (conditional) */}
            {selectedMember && overrideReasons.find(r => r.reason_id === overrideForm.reason_id)?.requires_pin && (
              <div className="space-y-2">
                <Label>Member Access PIN (Card Number) *</Label>
                <Input
                  type="text"
                  value={overrideForm.access_pin}
                  onChange={(e) => setOverrideForm({...overrideForm, access_pin: e.target.value})}
                  placeholder="Enter member's access PIN"
                />
              </div>
            )}

            {/* Location */}
            <div className="space-y-2">
              <Label>Location</Label>
              <Select 
                value={overrideForm.location} 
                onValueChange={(value) => setOverrideForm({...overrideForm, location: value})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LOCATIONS.map((loc) => (
                    <SelectItem key={loc} value={loc}>{loc}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Notes */}
            <div className="space-y-2">
              <Label>Notes</Label>
              <Input
                value={overrideForm.notes}
                onChange={(e) => setOverrideForm({...overrideForm, notes: e.target.value})}
                placeholder="Optional notes..."
              />
            </div>

            {/* Grant Access Button */}
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setShowOverrideDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleGrantOverride} className="bg-green-600 hover:bg-green-700">
                <CheckCircle2 className="mr-2 h-4 w-4" />
                Grant Access
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default AccessControlEnhanced;
