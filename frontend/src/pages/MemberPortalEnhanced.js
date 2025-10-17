import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { ArrowLeft, QrCode, FileText, Calendar, CreditCard, Users, UserPlus } from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export default function MemberPortalEnhanced() {
  const [member, setMember] = useState(null);
  const [membershipGroup, setMembershipGroup] = useState(null);
  const [groupMembers, setGroupMembers] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [paymentOption, setPaymentOption] = useState(null);
  const [loading, setLoading] = useState(true);
  const [memberId] = useState('demo-member-id'); // In production, from auth
  const navigate = useNavigate();

  useEffect(() => {
    // For demo purposes - in production, member would be authenticated
    toast.info('Member Portal - Demo Mode');
    fetchMemberData();
  }, []);

  const fetchMemberData = async () => {
    try {
      // In production, fetch real member data
      // const response = await axios.get(`${API}/api/members/${memberId}`);
      // setMember(response.data);
      
      // Demo data
      setMember({
        id: 'demo-member-id',
        first_name: 'John',
        last_name: 'Smith',
        email: 'john@example.com',
        phone: '+27123456789',
        membership_type_id: 'membership-1',
        membership_status: 'active',
        join_date: '2024-01-01',
        expiry_date: '2024-12-31',
        qr_code: 'data:image/png;base64,demo',
        is_primary_member: true,
        membership_group_id: 'group-1',
        selected_payment_option_id: 'payment-1'
      });

      // Demo membership group
      setMembershipGroup({
        id: 'group-1',
        group_name: 'Smith Family',
        max_members: 4,
        current_member_count: 3,
        primary_member_id: 'demo-member-id'
      });

      // Demo group members
      setGroupMembers([
        { id: 'demo-member-id', first_name: 'John', last_name: 'Smith', is_primary_member: true, membership_status: 'active' },
        { id: 'member-2', first_name: 'Jane', last_name: 'Smith', is_primary_member: false, membership_status: 'active' },
        { id: 'member-3', first_name: 'Jimmy', last_name: 'Smith', is_primary_member: false, membership_status: 'active' }
      ]);

      // Demo payment option
      setPaymentOption({
        payment_name: 'Monthly Budget Plan',
        installment_amount: 500.00,
        number_of_installments: 12,
        total_amount: 6000.00,
        payment_frequency: 'monthly',
        auto_renewal_enabled: true,
        auto_renewal_frequency: 'monthly'
      });

    } catch (error) {
      console.error('Failed to fetch member data:', error);
    } finally {
      setLoading(false);
    }
  };

  const isGroupMembership = membershipGroup && membershipGroup.max_members > 1;
  const canAddMembers = isGroupMembership && membershipGroup.current_member_count < membershipGroup.max_members;

  return (
    <div className="min-h-screen p-8" style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)' }}>
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <Button
            variant="outline"
            onClick={() => navigate('/login')}
            className="mb-4 border-slate-600 text-slate-300 hover:bg-slate-700"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Login
          </Button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">Member Portal</h1>
              <p className="text-slate-400">Welcome back, {member?.first_name}!</p>
            </div>
            {member?.is_primary_member && isGroupMembership && (
              <Badge variant="secondary" className="flex items-center gap-2">
                <Users className="w-4 h-4" />
                Primary Member
              </Badge>
            )}
          </div>
        </div>

        {/* Demo Notice */}
        <Card className="bg-blue-900/20 border-blue-500 mb-8">
          <CardContent className="pt-6">
            <p className="text-blue-200">
              <strong>Demo Mode:</strong> This is an enhanced demonstration of the member portal with family membership features. In production, members would log in to view their personal information.
            </p>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* QR Code Card */}
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <QrCode className="w-5 h-5" />
                Your QR Code
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col items-center space-y-4">
                <div className="bg-white p-4 rounded-lg">
                  <div className="w-48 h-48 bg-slate-200 flex items-center justify-center">
                    <p className="text-slate-600 text-sm text-center">QR Code<br />appears here<br />after login</p>
                  </div>
                </div>
                <p className="text-sm text-slate-400 text-center">
                  Show this QR code at the gym entrance
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Membership Details */}
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Calendar className="w-5 h-5" />
                Membership Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-slate-400 text-sm">Membership Type</p>
                <p className="text-white font-semibold">Premium Family Package</p>
              </div>
              <div>
                <p className="text-slate-400 text-sm">Status</p>
                <Badge className="mt-1 bg-green-600">Active</Badge>
              </div>
              <div>
                <p className="text-slate-400 text-sm">Join Date</p>
                <p className="text-white">January 1, 2024</p>
              </div>
              <div>
                <p className="text-slate-400 text-sm">Expiry Date</p>
                <p className="text-white">December 31, 2024</p>
              </div>
            </CardContent>
          </Card>

          {/* Payment Plan */}
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <CreditCard className="w-5 h-5" />
                Payment Plan
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {paymentOption ? (
                <>
                  <div>
                    <p className="text-slate-400 text-sm">Plan Name</p>
                    <p className="text-white font-semibold">{paymentOption.payment_name}</p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-sm">Payment Schedule</p>
                    <p className="text-white">
                      R{paymentOption.installment_amount.toFixed(2)} / {paymentOption.payment_frequency}
                    </p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-sm">Total Contract</p>
                    <p className="text-white font-bold">R{paymentOption.total_amount.toFixed(2)}</p>
                  </div>
                  {paymentOption.auto_renewal_enabled && (
                    <Badge variant="outline" className="text-blue-400 border-blue-400">
                      Auto-Renewal Active
                    </Badge>
                  )}
                </>
              ) : (
                <p className="text-slate-400 text-sm">Standard billing applies</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Family Members Section - Only for group memberships */}
        {isGroupMembership && (
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg mb-6">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Users className="w-5 h-5" />
                    Family Members
                  </CardTitle>
                  <CardDescription className="text-slate-400 mt-1">
                    {membershipGroup.group_name} - {membershipGroup.current_member_count} of {membershipGroup.max_members} members
                  </CardDescription>
                </div>
                {member?.is_primary_member && canAddMembers && (
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="sm" className="border-slate-600 text-slate-300">
                        <UserPlus className="w-4 h-4 mr-2" />
                        Add Member
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="bg-slate-800 border-slate-700 text-white">
                      <DialogHeader>
                        <DialogTitle>Add Family Member</DialogTitle>
                        <DialogDescription className="text-slate-400">
                          Contact gym staff to add additional family members to your membership.
                        </DialogDescription>
                      </DialogHeader>
                      <div className="py-4">
                        <div className="bg-blue-900/20 border border-blue-500 p-4 rounded-md">
                          <p className="text-blue-200 text-sm">
                            <strong>Note:</strong> Family members must be added by gym staff to ensure proper verification and QR code generation. 
                            Please visit the front desk or contact us at frontdesk@gym.com to add a new member.
                          </p>
                        </div>
                        <div className="mt-4 space-y-2">
                          <p className="text-white font-medium">Current Capacity:</p>
                          <div className="flex items-center gap-2">
                            <div className="flex-1 bg-slate-700 rounded-full h-2">
                              <div 
                                className="bg-green-500 h-2 rounded-full"
                                style={{ width: `${(membershipGroup.current_member_count / membershipGroup.max_members) * 100}%` }}
                              />
                            </div>
                            <span className="text-slate-400 text-sm">
                              {membershipGroup.current_member_count}/{membershipGroup.max_members}
                            </span>
                          </div>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {groupMembers.map((groupMember) => (
                  <Card key={groupMember.id} className="bg-slate-700/50 border-slate-600">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-white font-medium">
                            {groupMember.first_name} {groupMember.last_name}
                          </p>
                          <p className="text-slate-400 text-sm">
                            {groupMember.is_primary_member ? 'Primary Member' : 'Family Member'}
                          </p>
                        </div>
                        <Badge 
                          className={groupMember.membership_status === 'active' ? 'bg-green-600' : 'bg-gray-600'}
                        >
                          {groupMember.membership_status}
                        </Badge>
                      </div>
                      {groupMember.is_primary_member && (
                        <div className="mt-2 pt-2 border-t border-slate-600">
                          <p className="text-xs text-slate-400">Billing account owner</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>

              {!member?.is_primary_member && (
                <div className="mt-4 p-3 bg-slate-700/30 rounded-md border border-slate-600">
                  <p className="text-xs text-slate-400">
                    You are a family member on this account. The primary member ({groupMembers.find(m => m.is_primary_member)?.first_name}) manages billing and can add/remove members.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Recent Invoices */}
        <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Recent Invoices
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-slate-700/30 rounded-md">
                  <div>
                    <p className="text-white font-medium">Invoice #{1000 + i}</p>
                    <p className="text-slate-400 text-sm">Due: {new Date(2024, i, 1).toLocaleDateString()}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-white font-bold">R500.00</p>
                    <Badge className="mt-1 bg-green-600">Paid</Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
