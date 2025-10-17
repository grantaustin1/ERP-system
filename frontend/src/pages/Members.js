import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { UserPlus, Ban, CheckCircle, QrCode } from 'lucide-react';
import { toast } from 'sonner';

export default function Members() {
  const [members, setMembers] = useState([]);
  const [membershipTypes, setMembershipTypes] = useState([]);
  const [paymentOptions, setPaymentOptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [qrDialogOpen, setQrDialogOpen] = useState(false);
  const [selectedMember, setSelectedMember] = useState(null);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    home_phone: '',
    work_phone: '',
    membership_type_id: '',
    selected_payment_option_id: '',
    address: '',
    bank_account_number: '',
    bank_name: '',
    bank_branch_code: '',
    account_holder_name: '',
    id_number: '',
    id_type: 'id',
    emergency_contact: '',
    notes: ''
  });

  useEffect(() => {
    fetchMembers();
    fetchMembershipTypes();
  }, []);

  const fetchMembers = async () => {
    try {
      const response = await axios.get(`${API}/members`);
      setMembers(response.data);
    } catch (error) {
      toast.error('Failed to fetch members');
    } finally {
      setLoading(false);
    }
  };

  const fetchMembershipTypes = async () => {
    try {
      const response = await axios.get(`${API}/membership-types`);
      setMembershipTypes(response.data);
    } catch (error) {
      toast.error('Failed to fetch membership types');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/members`, formData);
      toast.success('Member added successfully!');
      setDialogOpen(false);
      setFormData({
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        home_phone: '',
        work_phone: '',
        membership_type_id: '',
        address: '',
        bank_account_number: '',
        bank_name: '',
        bank_branch_code: '',
        account_holder_name: '',
        id_number: '',
        id_type: 'id',
        emergency_contact: '',
        notes: ''
      });
      fetchMembers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add member');
    }
  };

  const blockMember = async (memberId) => {
    try {
      await axios.put(`${API}/members/${memberId}/block`);
      toast.success('Member blocked successfully');
      fetchMembers();
    } catch (error) {
      toast.error('Failed to block member');
    }
  };

  const unblockMember = async (memberId) => {
    try {
      await axios.put(`${API}/members/${memberId}/unblock`);
      toast.success('Member unblocked successfully');
      fetchMembers();
    } catch (error) {
      toast.error('Failed to unblock member');
    }
  };

  const showQRCode = (member) => {
    setSelectedMember(member);
    setQrDialogOpen(true);
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2" data-testid="members-title">Members</h1>
              <p className="text-slate-400">Manage gym members and memberships</p>
            </div>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700" data-testid="add-member-button">
                  <UserPlus className="w-4 h-4 mr-2" />
                  Add Member
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Add New Member</DialogTitle>
                  <DialogDescription className="text-slate-400">
                    Create a new member profile
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  {/* Personal Information */}
                  <div className="border-b border-slate-600 pb-3">
                    <h3 className="text-white font-semibold mb-3">Personal Information</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="first_name">First Name</Label>
                        <Input
                          id="first_name"
                          data-testid="first-name-input"
                          value={formData.first_name}
                          onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                          required
                          className="bg-slate-700/50 border-slate-600"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="last_name">Last Name</Label>
                        <Input
                          id="last_name"
                          data-testid="last-name-input"
                          value={formData.last_name}
                          onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                          required
                          className="bg-slate-700/50 border-slate-600"
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 mt-3">
                      <div className="space-y-2">
                        <Label htmlFor="id_type">ID Type</Label>
                        <Select
                          value={formData.id_type}
                          onValueChange={(value) => setFormData({ ...formData, id_type: value })}
                        >
                          <SelectTrigger className="bg-slate-700/50 border-slate-600">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-slate-800 border-slate-700">
                            <SelectItem value="id">ID Number</SelectItem>
                            <SelectItem value="passport">Passport</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="id_number">ID/Passport Number</Label>
                        <Input
                          id="id_number"
                          value={formData.id_number}
                          onChange={(e) => setFormData({ ...formData, id_number: e.target.value })}
                          className="bg-slate-700/50 border-slate-600"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Contact Information */}
                  <div className="border-b border-slate-600 pb-3">
                    <h3 className="text-white font-semibold mb-3">Contact Information</h3>
                    <div className="space-y-3">
                      <div className="space-y-2">
                        <Label htmlFor="email">Email</Label>
                        <Input
                          id="email"
                          type="email"
                          data-testid="member-email-input"
                          value={formData.email}
                          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                          required
                          className="bg-slate-700/50 border-slate-600"
                        />
                      </div>
                      <div className="grid grid-cols-3 gap-3">
                        <div className="space-y-2">
                          <Label htmlFor="phone">Mobile</Label>
                          <Input
                            id="phone"
                            data-testid="phone-input"
                            value={formData.phone}
                            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                            required
                            className="bg-slate-700/50 border-slate-600"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="home_phone">Home Phone</Label>
                          <Input
                            id="home_phone"
                            value={formData.home_phone}
                            onChange={(e) => setFormData({ ...formData, home_phone: e.target.value })}
                            className="bg-slate-700/50 border-slate-600"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="work_phone">Work Phone</Label>
                          <Input
                            id="work_phone"
                            value={formData.work_phone}
                            onChange={(e) => setFormData({ ...formData, work_phone: e.target.value })}
                            className="bg-slate-700/50 border-slate-600"
                          />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="address">Home Address (will be geo-located for marketing)</Label>
                        <Input
                          id="address"
                          value={formData.address}
                          onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                          placeholder="Full street address, city, postal code"
                          className="bg-slate-700/50 border-slate-600"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="emergency_contact">Emergency Contact</Label>
                        <Input
                          id="emergency_contact"
                          value={formData.emergency_contact}
                          onChange={(e) => setFormData({ ...formData, emergency_contact: e.target.value })}
                          className="bg-slate-700/50 border-slate-600"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Banking Details */}
                  <div className="border-b border-slate-600 pb-3">
                    <h3 className="text-white font-semibold mb-3">Banking Details</h3>
                    <div className="space-y-3">
                      <div className="space-y-2">
                        <Label htmlFor="account_holder_name">Account Holder Name</Label>
                        <Input
                          id="account_holder_name"
                          value={formData.account_holder_name}
                          onChange={(e) => setFormData({ ...formData, account_holder_name: e.target.value })}
                          className="bg-slate-700/50 border-slate-600"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-2">
                          <Label htmlFor="bank_name">Bank Name</Label>
                          <Input
                            id="bank_name"
                            value={formData.bank_name}
                            onChange={(e) => setFormData({ ...formData, bank_name: e.target.value })}
                            placeholder="e.g. FNB, Standard Bank"
                            className="bg-slate-700/50 border-slate-600"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="bank_branch_code">Branch Code</Label>
                          <Input
                            id="bank_branch_code"
                            value={formData.bank_branch_code}
                            onChange={(e) => setFormData({ ...formData, bank_branch_code: e.target.value })}
                            className="bg-slate-700/50 border-slate-600"
                          />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="bank_account_number">Account Number</Label>
                        <Input
                          id="bank_account_number"
                          value={formData.bank_account_number}
                          onChange={(e) => setFormData({ ...formData, bank_account_number: e.target.value })}
                          className="bg-slate-700/50 border-slate-600"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Membership */}
                  <div className="border-b border-slate-600 pb-3">
                    <h3 className="text-white font-semibold mb-3">Membership</h3>
                    <div className="space-y-2">
                      <Label htmlFor="membership_type">Membership Type</Label>
                      <Select
                        value={formData.membership_type_id}
                        onValueChange={(value) => setFormData({ ...formData, membership_type_id: value })}
                        required
                      >
                        <SelectTrigger className="bg-slate-700/50 border-slate-600" data-testid="membership-type-select">
                          <SelectValue placeholder="Select membership type" />
                        </SelectTrigger>
                        <SelectContent className="bg-slate-800 border-slate-700">
                          {membershipTypes.map((type) => (
                            <SelectItem key={type.id} value={type.id}>
                              {type.name} - R{type.price}/{type.billing_frequency}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {/* Notes */}
                  <div className="space-y-2">
                    <Label htmlFor="notes">Notes</Label>
                    <textarea
                      id="notes"
                      value={formData.notes}
                      onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                      rows={2}
                      className="w-full bg-slate-700/50 border-slate-600 rounded-md p-2 text-white border"
                    />
                  </div>

                  <Button type="submit" className="w-full bg-gradient-to-r from-emerald-500 to-teal-600" data-testid="submit-member-button">
                    Create Member
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          {loading ? (
            <div className="text-center text-slate-400 py-12">Loading members...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {members.map((member) => (
                <Card key={member.id} className="bg-slate-800/50 border-slate-700 backdrop-blur-lg hover:bg-slate-800/70 transition-all" data-testid={`member-card-${member.id}`}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-white text-lg">
                          {member.first_name} {member.last_name}
                        </CardTitle>
                        <p className="text-sm text-slate-400 mt-1">{member.email}</p>
                        <p className="text-sm text-slate-400">{member.phone}</p>
                      </div>
                      <div className="flex gap-2">
                        <Badge variant={member.membership_status === 'active' ? 'default' : 'destructive'}>
                          {member.membership_status}
                        </Badge>
                        {member.is_debtor && <Badge variant="destructive">Debtor</Badge>}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Join Date:</span>
                        <span className="text-white">{new Date(member.join_date).toLocaleDateString()}</span>
                      </div>
                      {member.expiry_date && (
                        <div className="flex justify-between">
                          <span className="text-slate-400">Expiry Date:</span>
                          <span className="text-white">{new Date(member.expiry_date).toLocaleDateString()}</span>
                        </div>
                      )}
                    </div>
                    <div className="flex gap-2 mt-4">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => showQRCode(member)}
                        className="flex-1 border-emerald-500 text-emerald-400 hover:bg-emerald-500/10"
                        data-testid={`view-qr-${member.id}`}
                      >
                        <QrCode className="w-4 h-4 mr-1" />
                        QR
                      </Button>
                      {member.is_debtor ? (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => unblockMember(member.id)}
                          className="flex-1 border-emerald-500 text-emerald-400 hover:bg-emerald-500/10"
                          data-testid={`unblock-${member.id}`}
                        >
                          <CheckCircle className="w-4 h-4 mr-1" />
                          Unblock
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => blockMember(member.id)}
                          className="flex-1 border-red-500 text-red-400 hover:bg-red-500/10"
                          data-testid={`block-${member.id}`}
                        >
                          <Ban className="w-4 h-4 mr-1" />
                          Block
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* QR Code Dialog */}
          <Dialog open={qrDialogOpen} onOpenChange={setQrDialogOpen}>
            <DialogContent className="bg-slate-800 border-slate-700 text-white">
              <DialogHeader>
                <DialogTitle>Member QR Code</DialogTitle>
                <DialogDescription className="text-slate-400">
                  {selectedMember && `${selectedMember.first_name} ${selectedMember.last_name}`}
                </DialogDescription>
              </DialogHeader>
              {selectedMember && (
                <div className="flex flex-col items-center space-y-4">
                  <div className="bg-white p-4 rounded-lg">
                    <img
                      src={`data:image/png;base64,${selectedMember.qr_code}`}
                      alt="Member QR Code"
                      className="w-64 h-64"
                    />
                  </div>
                  <p className="text-sm text-slate-400 text-center">
                    Use this QR code for gym access
                  </p>
                </div>
              )}
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </div>
  );
}
