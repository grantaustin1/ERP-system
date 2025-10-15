import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { UserX, Plus, CheckCircle, XCircle, Clock, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';

export default function Cancellations() {
  const [requests, setRequests] = useState([]);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [approvalDialogOpen, setApprovalDialogOpen] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [approvalLevel, setApprovalLevel] = useState('staff');
  
  const [formData, setFormData] = useState({
    member_id: '',
    reason: '',
    request_source: 'staff'
  });

  const [approvalForm, setApprovalForm] = useState({
    action: 'approve',
    comments: '',
    rejection_reason: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [reqRes, memRes] = await Promise.all([
        axios.get(`${API}/cancellations`),
        axios.get(`${API}/members`)
      ]);
      setRequests(reqRes.data);
      setMembers(memRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/cancellations`, formData);
      toast.success('Cancellation request created!');
      setDialogOpen(false);
      setFormData({
        member_id: '',
        reason: '',
        request_source: 'staff'
      });
      fetchData();
    } catch (error) {
      toast.error('Failed to create request');
    }
  };

  const handleApproval = async () => {
    if (!selectedRequest) return;

    try {
      const endpoint = approvalLevel === 'staff' 
        ? '/cancellations/approve-staff'
        : approvalLevel === 'manager'
        ? '/cancellations/approve-manager'
        : '/cancellations/approve-admin';

      await axios.post(`${API}${endpoint}`, {
        request_id: selectedRequest.id,
        action: approvalForm.action,
        comments: approvalForm.comments,
        rejection_reason: approvalForm.rejection_reason
      });

      toast.success(approvalForm.action === 'approve' ? 'Request approved!' : 'Request rejected');
      setApprovalDialogOpen(false);
      setSelectedRequest(null);
      setApprovalForm({
        action: 'approve',
        comments: '',
        rejection_reason: ''
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to process approval');
    }
  };

  const openApprovalDialog = (request, level) => {
    setSelectedRequest(request);
    setApprovalLevel(level);
    setApprovalDialogOpen(true);
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: { variant: 'secondary', label: 'Pending Staff' },
      staff_approved: { variant: 'default', label: 'Staff Approved' },
      manager_approved: { variant: 'default', label: 'Manager Approved' },
      admin_approved: { variant: 'default', label: 'Admin Approved' },
      completed: { variant: 'default', label: 'Completed' },
      rejected: { variant: 'destructive', label: 'Rejected' }
    };
    const config = badges[status] || badges.pending;
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const getMemberName = (memberId) => {
    const member = members.find(m => m.id === memberId);
    return member ? `${member.first_name} ${member.last_name}` : 'Unknown';
  };

  const pendingRequests = requests.filter(r => r.status === 'pending');
  const staffApprovedRequests = requests.filter(r => r.status === 'staff_approved');
  const managerApprovedRequests = requests.filter(r => r.status === 'manager_approved');
  const completedRequests = requests.filter(r => ['completed', 'rejected'].includes(r.status));

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2" data-testid="cancellations-title">Cancellation Requests</h1>
              <p className="text-slate-400">Multi-level approval workflow for membership cancellations</p>
            </div>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-gradient-to-r from-red-500 to-orange-600" data-testid="create-cancellation-button">
                  <Plus className="w-4 h-4 mr-2" />
                  New Cancellation Request
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-slate-800 border-slate-700 text-white">
                <DialogHeader>
                  <DialogTitle>Create Cancellation Request</DialogTitle>
                  <DialogDescription className="text-slate-400">
                    Submit a membership cancellation request
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label>Member</Label>
                    <Select
                      value={formData.member_id}
                      onValueChange={(value) => setFormData({ ...formData, member_id: value })}
                      required
                    >
                      <SelectTrigger className="bg-slate-700/50 border-slate-600">
                        <SelectValue placeholder="Select member" />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        {members.filter(m => m.membership_status === 'active').map((member) => (
                          <SelectItem key={member.id} value={member.id}>
                            {member.first_name} {member.last_name} - {member.email}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Request Source</Label>
                    <Select
                      value={formData.request_source}
                      onValueChange={(value) => setFormData({ ...formData, request_source: value })}
                    >
                      <SelectTrigger className="bg-slate-700/50 border-slate-600">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        <SelectItem value="staff">Staff (In-person)</SelectItem>
                        <SelectItem value="email">Email</SelectItem>
                        <SelectItem value="mobile_app">Mobile App</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Reason for Cancellation</Label>
                    <textarea
                      value={formData.reason}
                      onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                      placeholder="Please provide reason for cancellation..."
                      rows={4}
                      required
                      className="w-full bg-slate-700/50 border-slate-600 rounded-md p-2 text-white border"
                    />
                  </div>
                  <Button type="submit" className="w-full bg-gradient-to-r from-red-500 to-orange-600">
                    Submit Request
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          {/* Approval Workflow Visual */}
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg mb-8">
            <CardHeader>
              <CardTitle className="text-white">Approval Workflow</CardTitle>
              <CardDescription className="text-slate-400">3-Level authorization process</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="text-center">
                  <div className="w-16 h-16 rounded-full bg-blue-500/20 border-2 border-blue-500 flex items-center justify-center mx-auto mb-2">
                    <span className="text-blue-400 font-bold">1</span>
                  </div>
                  <p className="text-white font-semibold">Staff Review</p>
                  <p className="text-slate-400 text-sm">Reception/Staff</p>
                </div>
                <ArrowRight className="text-slate-600" />
                <div className="text-center">
                  <div className="w-16 h-16 rounded-full bg-emerald-500/20 border-2 border-emerald-500 flex items-center justify-center mx-auto mb-2">
                    <span className="text-emerald-400 font-bold">2</span>
                  </div>
                  <p className="text-white font-semibold">Manager Approval</p>
                  <p className="text-slate-400 text-sm">Line Manager</p>
                </div>
                <ArrowRight className="text-slate-600" />
                <div className="text-center">
                  <div className="w-16 h-16 rounded-full bg-purple-500/20 border-2 border-purple-500 flex items-center justify-center mx-auto mb-2">
                    <span className="text-purple-400 font-bold">3</span>
                  </div>
                  <p className="text-white font-semibold">Admin Approval</p>
                  <p className="text-slate-400 text-sm">Head Office</p>
                </div>
                <ArrowRight className="text-slate-600" />
                <div className="text-center">
                  <div className="w-16 h-16 rounded-full bg-green-500/20 border-2 border-green-500 flex items-center justify-center mx-auto mb-2">
                    <CheckCircle className="text-green-400" />
                  </div>
                  <p className="text-white font-semibold">Completed</p>
                  <p className="text-slate-400 text-sm">Membership Cancelled</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Tabs defaultValue="pending" className="w-full">
            <TabsList className="bg-slate-800/50 border-slate-700">
              <TabsTrigger value="pending">
                Pending Staff ({pendingRequests.length})
              </TabsTrigger>
              <TabsTrigger value="staff_approved">
                Staff Approved ({staffApprovedRequests.length})
              </TabsTrigger>
              <TabsTrigger value="manager_approved">
                Manager Approved ({managerApprovedRequests.length})
              </TabsTrigger>
              <TabsTrigger value="completed">
                Completed ({completedRequests.length})
              </TabsTrigger>
            </TabsList>

            {/* Pending Staff Tab */}
            <TabsContent value="pending" className="mt-6">
              <div className="space-y-4">
                {pendingRequests.map((request) => (
                  <Card key={request.id} className="bg-slate-800/50 border-slate-700">
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-white font-semibold">{request.member_name}</h3>
                            {getStatusBadge(request.status)}
                            <Badge variant="outline">{request.request_source}</Badge>
                          </div>
                          <p className="text-slate-400 text-sm mb-2">Membership: {request.membership_type}</p>
                          <p className="text-slate-300 text-sm mb-2"><strong>Reason:</strong> {request.reason}</p>
                          <p className="text-slate-500 text-xs">Requested by: {request.requested_by} on {new Date(request.created_at).toLocaleString()}</p>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => openApprovalDialog(request, 'staff')}
                            className="bg-gradient-to-r from-emerald-500 to-teal-600"
                            data-testid={`approve-staff-${request.id}`}
                          >
                            <CheckCircle className="w-4 h-4 mr-1" />
                            Review
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                {pendingRequests.length === 0 && (
                  <p className="text-center text-slate-400 py-8">No pending requests</p>
                )}
              </div>
            </TabsContent>

            {/* Staff Approved Tab */}
            <TabsContent value="staff_approved" className="mt-6">
              <div className="space-y-4">
                {staffApprovedRequests.map((request) => (
                  <Card key={request.id} className="bg-slate-800/50 border-slate-700">
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-white font-semibold">{request.member_name}</h3>
                            {getStatusBadge(request.status)}
                          </div>
                          <p className="text-slate-400 text-sm mb-2">Membership: {request.membership_type}</p>
                          <p className="text-slate-300 text-sm mb-2"><strong>Reason:</strong> {request.reason}</p>
                          {request.staff_approval && (
                            <div className="bg-emerald-900/20 p-2 rounded mt-2">
                              <p className="text-emerald-300 text-xs">
                                ✓ Staff approved by {request.staff_approval.approved_by}
                              </p>
                              {request.staff_approval.comments && (
                                <p className="text-slate-400 text-xs mt-1">{request.staff_approval.comments}</p>
                              )}
                            </div>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => openApprovalDialog(request, 'manager')}
                            className="bg-gradient-to-r from-emerald-500 to-teal-600"
                            data-testid={`approve-manager-${request.id}`}
                          >
                            <CheckCircle className="w-4 h-4 mr-1" />
                            Manager Review
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                {staffApprovedRequests.length === 0 && (
                  <p className="text-center text-slate-400 py-8">No requests pending manager approval</p>
                )}
              </div>
            </TabsContent>

            {/* Manager Approved Tab */}
            <TabsContent value="manager_approved" className="mt-6">
              <div className="space-y-4">
                {managerApprovedRequests.map((request) => (
                  <Card key={request.id} className="bg-slate-800/50 border-slate-700">
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-white font-semibold">{request.member_name}</h3>
                            {getStatusBadge(request.status)}
                          </div>
                          <p className="text-slate-400 text-sm mb-2">Membership: {request.membership_type}</p>
                          <p className="text-slate-300 text-sm mb-2"><strong>Reason:</strong> {request.reason}</p>
                          {request.manager_approval && (
                            <div className="bg-emerald-900/20 p-2 rounded mt-2">
                              <p className="text-emerald-300 text-xs">
                                ✓ Manager approved by {request.manager_approval.approved_by}
                              </p>
                            </div>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => openApprovalDialog(request, 'admin')}
                            className="bg-gradient-to-r from-purple-500 to-pink-600"
                            data-testid={`approve-admin-${request.id}`}
                          >
                            <CheckCircle className="w-4 h-4 mr-1" />
                            Admin Review
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                {managerApprovedRequests.length === 0 && (
                  <p className="text-center text-slate-400 py-8">No requests pending admin approval</p>
                )}
              </div>
            </TabsContent>

            {/* Completed Tab */}
            <TabsContent value="completed" className="mt-6">
              <div className="space-y-4">
                {completedRequests.map((request) => (
                  <Card key={request.id} className="bg-slate-800/50 border-slate-700">
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-white font-semibold">{request.member_name}</h3>
                            {getStatusBadge(request.status)}
                          </div>
                          <p className="text-slate-400 text-sm mb-2">Membership: {request.membership_type}</p>
                          <p className="text-slate-300 text-sm mb-2"><strong>Reason:</strong> {request.reason}</p>
                          {request.status === 'rejected' && request.rejection_reason && (
                            <div className="bg-red-900/20 p-2 rounded mt-2">
                              <p className="text-red-300 text-xs">
                                ✗ Rejected: {request.rejection_reason}
                              </p>
                            </div>
                          )}
                          {request.status === 'completed' && (
                            <p className="text-green-400 text-sm mt-2">
                              ✓ Cancellation completed on {new Date(request.completed_at).toLocaleString()}
                            </p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                {completedRequests.length === 0 && (
                  <p className="text-center text-slate-400 py-8">No completed requests</p>
                )}
              </div>
            </TabsContent>
          </Tabs>

          {/* Approval Dialog */}
          <Dialog open={approvalDialogOpen} onOpenChange={setApprovalDialogOpen}>
            <DialogContent className="bg-slate-800 border-slate-700 text-white">
              <DialogHeader>
                <DialogTitle>
                  {approvalLevel === 'staff' ? 'Staff Review' : approvalLevel === 'manager' ? 'Manager Approval' : 'Admin Final Approval'}
                </DialogTitle>
                <DialogDescription className="text-slate-400">
                  {selectedRequest && `Review cancellation request for ${selectedRequest.member_name}`}
                </DialogDescription>
              </DialogHeader>
              {selectedRequest && (
                <div className="space-y-4">
                  <div className="p-4 rounded-lg bg-slate-700/50">
                    <p className="text-slate-400 text-sm mb-1">Member</p>
                    <p className="text-white font-semibold">{selectedRequest.member_name}</p>
                    <p className="text-slate-400 text-sm mt-2 mb-1">Reason</p>
                    <p className="text-white">{selectedRequest.reason}</p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Action</Label>
                    <Select
                      value={approvalForm.action}
                      onValueChange={(value) => setApprovalForm({ ...approvalForm, action: value })}
                    >
                      <SelectTrigger className="bg-slate-700/50 border-slate-600">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        <SelectItem value="approve">Approve</SelectItem>
                        <SelectItem value="reject">Reject</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {approvalForm.action === 'approve' ? (
                    <div className="space-y-2">
                      <Label>Comments (Optional)</Label>
                      <textarea
                        value={approvalForm.comments}
                        onChange={(e) => setApprovalForm({ ...approvalForm, comments: e.target.value })}
                        placeholder="Add any comments..."
                        rows={3}
                        className="w-full bg-slate-700/50 border-slate-600 rounded-md p-2 text-white border"
                      />
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <Label>Rejection Reason</Label>
                      <textarea
                        value={approvalForm.rejection_reason}
                        onChange={(e) => setApprovalForm({ ...approvalForm, rejection_reason: e.target.value })}
                        placeholder="Reason for rejection..."
                        rows={3}
                        required
                        className="w-full bg-slate-700/50 border-slate-600 rounded-md p-2 text-white border"
                      />
                    </div>
                  )}

                  <Button
                    onClick={handleApproval}
                    className={`w-full ${approvalForm.action === 'approve' ? 'bg-gradient-to-r from-emerald-500 to-teal-600' : 'bg-gradient-to-r from-red-500 to-orange-600'}`}
                  >
                    {approvalForm.action === 'approve' ? <CheckCircle className="w-4 h-4 mr-2" /> : <XCircle className="w-4 h-4 mr-2" />}
                    {approvalForm.action === 'approve' ? 'Approve' : 'Reject'}
                  </Button>
                </div>
              )}
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </div>
  );
}
