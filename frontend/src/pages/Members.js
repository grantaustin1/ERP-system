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
import { UserPlus, Ban, CheckCircle, QrCode, Shield, AlertCircle, Search, Filter, X } from 'lucide-react';
import { toast } from 'sonner';

export default function Members() {
  const [members, setMembers] = useState([]);
  const [membershipTypes, setMembershipTypes] = useState([]);
  const [paymentOptions, setPaymentOptions] = useState([]);
  const [paymentSources, setPaymentSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [qrDialogOpen, setQrDialogOpen] = useState(false);
  const [selectedMember, setSelectedMember] = useState(null);
  const [avsVerifying, setAvsVerifying] = useState(false);
  const [avsResult, setAvsResult] = useState(null);
  // Search and filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [debtorFilter, setDebtorFilter] = useState('all');
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    home_phone: '',
    work_phone: '',
    membership_type_id: '',
    selected_payment_option_id: '',
    source: '',
    referred_by: '',
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
    fetchPaymentSources();
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
      console.error('Failed to fetch membership types:', error);
    }
  };

  const fetchPaymentSources = async () => {
    try {
      const response = await axios.get(`${API}/payment-sources`);
      setPaymentSources(response.data);
    } catch (error) {
      console.error('Failed to fetch payment sources:', error);
    }
  };

  const fetchPaymentOptions = async (membershipTypeId) => {
    try {
      const response = await axios.get(`${API}/payment-options/${membershipTypeId}`);
      setPaymentOptions(response.data);
    } catch (error) {
      console.error('Failed to fetch payment options:', error);
      setPaymentOptions([]);
    }
  };

  const handleMembershipTypeChange = (value) => {
    setFormData({ ...formData, membership_type_id: value, selected_payment_option_id: '' });
    fetchPaymentOptions(value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    console.log('handleSubmit called', formData);
    try {
      const response = await axios.post(`${API}/members`, formData);
      console.log('Member created successfully:', response.data);
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
        selected_payment_option_id: '',
        source: '',
        referred_by: '',
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
      setPaymentOptions([]);
      fetchMembers();
    } catch (error) {
      console.error('Error creating member:', error, error.response);
      // Handle duplicate error specially
      if (error.response?.status === 409 && error.response?.data?.detail?.duplicates) {
        const duplicates = error.response.data.detail.duplicates;
        let message = 'Duplicate member detected: ';
        const dupFields = duplicates.map(dup => {
          return `${dup.field}: ${dup.value} (existing: ${dup.existing_member.name})`;
        }).join(', ');
        message += dupFields;
        toast.error(message);
      } else {
        const errorMsg = error.response?.data?.detail || 'Failed to add member';
        toast.error(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
      }
    }
  };

  const handleAvsVerification = async () => {
    // Validate required fields
    if (!formData.bank_account_number || !formData.bank_branch_code || !formData.id_number) {
      toast.error('Please fill in banking details and ID number before verification');
      return;
    }

    setAvsVerifying(true);
    setAvsResult(null);

    try {
      // Determine bank identifier from branch code (simplified)
      const branchCode = formData.bank_branch_code;
      let bankIdentifier = '21'; // Default to Nedbank
      
      if (branchCode) {
        const branch = parseInt(branchCode);
        if (branch >= 100000 && branch <= 199999) bankIdentifier = '21'; // Nedbank
        else if (branch >= 200000 && branch <= 299999) bankIdentifier = '05'; // FNB
        else if (branch >= 0 && branch <= 99999) bankIdentifier = '18'; // Standard Bank
        else if ((branch >= 630000 && branch <= 659999) || (branch >= 300000 && branch <= 349999)) bankIdentifier = '16'; // Absa
        else if (branch >= 470000 && branch <= 470999) bankIdentifier = '34'; // Capitec
      }

      const verificationRequest = {
        bank_identifier: bankIdentifier,
        account_number: formData.bank_account_number,
        sort_code: formData.bank_branch_code,
        identity_number: formData.id_number,
        identity_type: formData.id_type === 'id' ? 'SID' : 'SPP',
        initials: formData.first_name ? formData.first_name.charAt(0) : null,
        last_name: formData.last_name,
        email_id: formData.email,
        cell_number: formData.phone,
        customer_reference: `${formData.first_name} ${formData.last_name}`
      };

      const response = await axios.post(`${API}/avs/verify`, verificationRequest);
      
      if (response.data.success) {
        setAvsResult(response.data.result);
        
        // Check if verification was successful
        const result = response.data.result;
        if (result.account_exists === 'Y' && result.identification_number_matched === 'Y') {
          toast.success('Account verified successfully! ✓');
        } else if (result.account_exists === 'N') {
          toast.error('Account not found at the bank');
        } else if (result.identification_number_matched === 'N') {
          toast.error('ID number does not match bank records');
        } else {
          toast.warning('Verification completed with some unverified fields');
        }
      }
    } catch (error) {
      console.error('AVS verification error:', error);
      toast.error(error.response?.data?.detail || 'Account verification failed');
    } finally {
      setAvsVerifying(false);
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

  // Search and filter logic
  const filteredMembers = members.filter((member) => {
    // Search query filter (name, email, phone, ID)
    const searchLower = searchQuery.toLowerCase();
    const matchesSearch = 
      searchQuery === '' ||
      member.first_name?.toLowerCase().includes(searchLower) ||
      member.last_name?.toLowerCase().includes(searchLower) ||
      member.email?.toLowerCase().includes(searchLower) ||
      member.phone?.toLowerCase().includes(searchLower) ||
      member.id_number?.toLowerCase().includes(searchLower);

    // Status filter
    const matchesStatus = 
      statusFilter === 'all' ||
      member.membership_status === statusFilter;

    // Membership type filter
    const matchesType = 
      typeFilter === 'all' ||
      member.membership_type_id === typeFilter;

    // Debtor filter
    const matchesDebtor = 
      debtorFilter === 'all' ||
      (debtorFilter === 'yes' && member.is_debtor) ||
      (debtorFilter === 'no' && !member.is_debtor);

    return matchesSearch && matchesStatus && matchesType && matchesDebtor;
  });

  const clearFilters = () => {
    setSearchQuery('');
    setStatusFilter('all');
    setTypeFilter('all');
    setDebtorFilter('all');
  };

  const hasActiveFilters = searchQuery !== '' || statusFilter !== 'all' || typeFilter !== 'all' || debtorFilter !== 'all';

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
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-2">
                          <Label htmlFor="source">How did you hear about us?</Label>
                          <Select 
                            value={formData.source} 
                            onValueChange={(value) => setFormData({ ...formData, source: value })}
                          >
                            <SelectTrigger className="bg-slate-700/50 border-slate-600">
                              <SelectValue placeholder="Select source..." />
                            </SelectTrigger>
                            <SelectContent className="bg-slate-800 border-slate-700">
                              {paymentSources.map((source) => (
                                <SelectItem key={source.id} value={source.name}>
                                  {source.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="referred_by">Referred By (if applicable)</Label>
                          <Input
                            id="referred_by"
                            value={formData.referred_by}
                            onChange={(e) => setFormData({ ...formData, referred_by: e.target.value })}
                            placeholder="Name of referrer"
                            className="bg-slate-700/50 border-slate-600"
                          />
                        </div>
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

                      {/* AVS Verification Button */}
                      <div className="pt-2">
                        <Button
                          type="button"
                          onClick={handleAvsVerification}
                          disabled={avsVerifying || !formData.bank_account_number || !formData.bank_branch_code || !formData.id_number}
                          className="w-full bg-blue-600 hover:bg-blue-700"
                        >
                          <Shield className="w-4 h-4 mr-2" />
                          {avsVerifying ? 'Verifying...' : 'Verify Account with AVS'}
                        </Button>
                      </div>

                      {/* AVS Verification Result */}
                      {avsResult && (
                        <div className="mt-3 p-3 bg-slate-700/50 rounded border border-slate-600">
                          <div className="flex items-center gap-2 mb-2">
                            {avsResult.account_exists === 'Y' && avsResult.identification_number_matched === 'Y' ? (
                              <CheckCircle className="w-5 h-5 text-green-500" />
                            ) : (
                              <AlertCircle className="w-5 h-5 text-yellow-500" />
                            )}
                            <span className="font-semibold text-white">
                              {avsResult.account_exists === 'Y' && avsResult.identification_number_matched === 'Y' 
                                ? 'Verification Successful' 
                                : 'Verification Completed'}
                            </span>
                          </div>
                          <div className="text-sm space-y-1 text-slate-300">
                            <div>Account Exists: <span className={avsResult.account_exists === 'Y' ? 'text-green-400' : 'text-red-400'}>{avsResult.account_exists === 'Y' ? '✓ Yes' : '✗ No'}</span></div>
                            <div>ID Match: <span className={avsResult.identification_number_matched === 'Y' ? 'text-green-400' : avsResult.identification_number_matched === 'N' ? 'text-red-400' : 'text-yellow-400'}>{avsResult.identification_number_matched === 'Y' ? '✓ Yes' : avsResult.identification_number_matched === 'N' ? '✗ No' : '- Not Verified'}</span></div>
                            <div>Name Match: <span className={avsResult.last_name_matched === 'Y' ? 'text-green-400' : avsResult.last_name_matched === 'N' ? 'text-red-400' : 'text-yellow-400'}>{avsResult.last_name_matched === 'Y' ? '✓ Yes' : avsResult.last_name_matched === 'N' ? '✗ No' : '- Not Verified'}</span></div>
                            <div>Account Active: <span className={avsResult.account_active === 'Y' ? 'text-green-400' : 'text-red-400'}>{avsResult.account_active === 'Y' ? '✓ Yes' : '✗ No'}</span></div>
                            <div>Can Accept Debits: <span className={avsResult.can_debit_account === 'Y' ? 'text-green-400' : 'text-red-400'}>{avsResult.can_debit_account === 'Y' ? '✓ Yes' : '✗ No'}</span></div>
                            {avsResult.mock_mode && (
                              <div className="mt-2 text-xs text-blue-400 bg-blue-500/10 px-2 py-1 rounded">
                                🧪 Mock Mode: Using test data
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Membership */}
                  <div className="border-b border-slate-600 pb-3">
                    <h3 className="text-white font-semibold mb-3">Membership</h3>
                    <div className="space-y-3">
                      <div className="space-y-2">
                        <Label htmlFor="membership_type">Membership Type</Label>
                        <Select
                          value={formData.membership_type_id}
                          onValueChange={handleMembershipTypeChange}
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

                      {/* Payment Options */}
                      {formData.membership_type_id && paymentOptions.length > 0 && (
                        <div className="space-y-2 mt-3 border-t border-slate-600 pt-3">
                          <Label htmlFor="payment_option">Payment Plan</Label>
                          <Select
                            value={formData.selected_payment_option_id}
                            onValueChange={(value) => setFormData({ ...formData, selected_payment_option_id: value })}
                          >
                            <SelectTrigger className="bg-slate-700/50 border-slate-600">
                              <SelectValue placeholder="Select payment plan (optional)" />
                            </SelectTrigger>
                            <SelectContent className="bg-slate-800 border-slate-700">
                              {paymentOptions.map((option) => (
                                <SelectItem key={option.id} value={option.id}>
                                  <div className="flex flex-col">
                                    <span className="font-medium">{option.payment_name}</span>
                                    <span className="text-xs text-slate-400">
                                      R{option.installment_amount.toFixed(2)} × {option.number_of_installments} = R{option.total_amount.toFixed(2)}
                                      {option.is_default && ' (Recommended)'}
                                    </span>
                                  </div>
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <p className="text-xs text-slate-400 mt-1">
                            {paymentOptions.length} payment plan{paymentOptions.length > 1 ? 's' : ''} available for this membership
                          </p>
                        </div>
                      )}

                      {formData.membership_type_id && paymentOptions.length === 0 && (
                        <div className="mt-3 p-3 bg-slate-700/30 rounded-md border border-slate-600">
                          <p className="text-xs text-slate-400">
                            No payment plans configured for this membership. Member will use default billing.
                          </p>
                        </div>
                      )}
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

          {/* Search and Filter Section */}
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg mb-6">
            <CardContent className="p-6">
              <div className="space-y-4">
                {/* Search Bar */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5" />
                  <Input
                    type="text"
                    placeholder="Search by name, email, phone, or ID number..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 bg-slate-700/50 border-slate-600 text-white placeholder-slate-400 h-12"
                  />
                  {searchQuery && (
                    <button
                      onClick={() => setSearchQuery('')}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-white"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  )}
                </div>

                {/* Filters */}
                <div className="flex flex-wrap gap-3 items-center">
                  <div className="flex items-center gap-2">
                    <Filter className="w-4 h-4 text-slate-400" />
                    <span className="text-sm text-slate-400">Filters:</span>
                  </div>

                  {/* Status Filter */}
                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-[160px] bg-slate-700/50 border-slate-600 text-white">
                      <SelectValue placeholder="All Status" />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-800 border-slate-700">
                      <SelectItem value="all" className="text-white">All Status</SelectItem>
                      <SelectItem value="active" className="text-white">Active</SelectItem>
                      <SelectItem value="inactive" className="text-white">Inactive</SelectItem>
                      <SelectItem value="expired" className="text-white">Expired</SelectItem>
                    </SelectContent>
                  </Select>

                  {/* Membership Type Filter */}
                  <Select value={typeFilter} onValueChange={setTypeFilter}>
                    <SelectTrigger className="w-[180px] bg-slate-700/50 border-slate-600 text-white">
                      <SelectValue placeholder="All Types" />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-800 border-slate-700">
                      <SelectItem value="all" className="text-white">All Types</SelectItem>
                      {membershipTypes.map((type) => (
                        <SelectItem key={type.id} value={type.id} className="text-white">
                          {type.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  {/* Debtor Filter */}
                  <Select value={debtorFilter} onValueChange={setDebtorFilter}>
                    <SelectTrigger className="w-[160px] bg-slate-700/50 border-slate-600 text-white">
                      <SelectValue placeholder="All Members" />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-800 border-slate-700">
                      <SelectItem value="all" className="text-white">All Members</SelectItem>
                      <SelectItem value="yes" className="text-white">Debtors Only</SelectItem>
                      <SelectItem value="no" className="text-white">Non-Debtors</SelectItem>
                    </SelectContent>
                  </Select>

                  {/* Clear Filters Button */}
                  {hasActiveFilters && (
                    <Button
                      onClick={clearFilters}
                      variant="outline"
                      size="sm"
                      className="ml-auto border-slate-600 text-slate-300 hover:bg-slate-700"
                    >
                      <X className="w-4 h-4 mr-2" />
                      Clear Filters
                    </Button>
                  )}
                </div>

                {/* Results Count */}
                <div className="flex items-center justify-between pt-2 border-t border-slate-700">
                  <p className="text-sm text-slate-400">
                    Showing <span className="text-white font-semibold">{filteredMembers.length}</span> of{' '}
                    <span className="text-white font-semibold">{members.length}</span> members
                  </p>
                  {hasActiveFilters && (
                    <Badge variant="outline" className="border-emerald-500/50 text-emerald-400">
                      <Filter className="w-3 h-3 mr-1" />
                      Filtered
                    </Badge>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {loading ? (
            <div className="text-center text-slate-400 py-12">Loading members...</div>
          ) : filteredMembers.length === 0 ? (
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="text-center py-12">
                <Search className="w-16 h-16 mx-auto text-slate-600 mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">No members found</h3>
                <p className="text-slate-400 mb-4">
                  {hasActiveFilters 
                    ? 'Try adjusting your search or filters' 
                    : 'Start by adding your first member'}
                </p>
                {hasActiveFilters && (
                  <Button onClick={clearFilters} variant="outline" className="border-slate-600">
                    Clear Filters
                  </Button>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredMembers.map((member) => (
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
