import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { FileText, DollarSign, CheckCircle, Clock, AlertCircle, Filter, Download, Search } from 'lucide-react';
import { toast } from 'sonner';

export default function BillingEnhanced() {
  const [invoices, setInvoices] = useState([]);
  const [members, setMembers] = useState([]);
  const [paymentReport, setPaymentReport] = useState([]);
  const [paymentSources, setPaymentSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [reportLoading, setReportLoading] = useState(false);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState('cash');

  // Filters for payment report
  const [filters, setFilters] = useState({
    member_id: '__all__',
    status: '__all__',
    payment_gateway: '',
    source: '__all__',
    start_date: '',
    end_date: ''
  });

  useEffect(() => {
    fetchInvoices();
    fetchMembers();
    fetchPaymentSources();
  }, []);

  const fetchInvoices = async () => {
    try {
      const response = await axios.get(`${API}/invoices`);
      setInvoices(response.data);
    } catch (error) {
      toast.error('Failed to fetch invoices');
    } finally {
      setLoading(false);
    }
  };

  const fetchMembers = async () => {
    try {
      const response = await axios.get(`${API}/members`);
      setMembers(response.data);
    } catch (error) {
      toast.error('Failed to fetch members');
    }
  };

  const fetchPaymentSources = async () => {
    try {
      const response = await axios.get(`${API}/payment-sources`);
      setPaymentSources(response.data);
    } catch (error) {
      console.error('Failed to fetch payment sources');
    }
  };

  const fetchPaymentReport = async () => {
    setReportLoading(true);
    try {
      const params = new URLSearchParams();
      Object.keys(filters).forEach(key => {
        if (filters[key] && filters[key] !== '__all__') {
          params.append(key, filters[key]);
        }
      });
      
      const response = await axios.get(`${API}/payment-report?${params.toString()}`);
      setPaymentReport(response.data.data || []);
      toast.success(`Loaded ${response.data.total_records} records`);
    } catch (error) {
      toast.error('Failed to fetch payment report');
    } finally {
      setReportLoading(false);
    }
  };

  const handlePayment = async () => {
    if (!selectedInvoice) return;

    try {
      await axios.post(`${API}/payments`, {
        invoice_id: selectedInvoice.id,
        member_id: selectedInvoice.member_id,
        amount: selectedInvoice.amount,
        payment_method: paymentMethod,
        reference: `PAY-${Date.now()}`
      });
      toast.success('Payment processed successfully!');
      setPaymentDialogOpen(false);
      setSelectedInvoice(null);
      fetchInvoices();
    } catch (error) {
      toast.error('Failed to process payment');
    }
  };

  const exportReport = () => {
    if (paymentReport.length === 0) {
      toast.error('No data to export');
      return;
    }

    // Create CSV content
    const headers = [
      'Member Name', 'Membership Number', 'Email', 'Phone', 'Membership Type',
      'Invoice Number', 'Amount', 'Status', 'Payment Gateway', 'Debt',
      'Due Date', 'Paid Date', 'Start Date', 'End Date', 'Contract Start', 'Contract End',
      'Source', 'Referred By', 'Sales Consultant'
    ];

    const rows = paymentReport.map(item => [
      item.member_name,
      item.membership_number,
      item.email,
      item.phone,
      item.membership_type,
      item.invoice_number,
      item.amount,
      item.status,
      item.payment_gateway || 'N/A',
      item.debt,
      item.due_date?.substring(0, 10) || '',
      item.paid_date?.substring(0, 10) || '',
      item.start_date?.substring(0, 10) || '',
      item.end_renewal_date?.substring(0, 10) || '',
      item.contract_start_date?.substring(0, 10) || '',
      item.contract_end_date?.substring(0, 10) || '',
      item.source || '',
      item.referred_by || '',
      item.sales_consultant_name || ''
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    // Download file
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `payment-report-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
    toast.success('Report exported successfully!');
  };

  const openPaymentDialog = (invoice) => {
    setSelectedInvoice(invoice);
    setPaymentDialogOpen(true);
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'paid':
        return <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/50">Paid</Badge>;
      case 'pending':
        return <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/50">Pending</Badge>;
      case 'overdue':
        return <Badge className="bg-red-500/20 text-red-400 border-red-500/50">Overdue</Badge>;
      case 'failed':
        return <Badge className="bg-red-500/20 text-red-400 border-red-500/50">Failed</Badge>;
      default:
        return <Badge variant="outline" className="border-slate-600 text-slate-400">{status}</Badge>;
    }
  };

  const getMemberName = (memberId) => {
    const member = members.find(m => m.id === memberId);
    return member ? `${member.first_name} ${member.last_name}` : 'Unknown';
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-white mb-2">Billing & Payments</h1>
            <p className="text-slate-400">Manage invoices, payments, and comprehensive financial reports</p>
          </div>

          <Tabs defaultValue="invoices" className="w-full">
            <TabsList className="bg-slate-800/50 border-slate-700">
              <TabsTrigger value="invoices" className="data-[state=active]:bg-emerald-500">
                <FileText className="w-4 h-4 mr-2" />
                Invoices
              </TabsTrigger>
              <TabsTrigger value="report" className="data-[state=active]:bg-emerald-500">
                <DollarSign className="w-4 h-4 mr-2" />
                Payment Report
              </TabsTrigger>
            </TabsList>

            {/* Invoices Tab */}
            <TabsContent value="invoices" className="mt-6">
              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
                <CardHeader>
                  <CardTitle className="text-white">All Invoices</CardTitle>
                  <CardDescription className="text-slate-400">View and manage member invoices</CardDescription>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div className="text-center py-8 text-slate-400">Loading invoices...</div>
                  ) : invoices.length === 0 ? (
                    <div className="text-center py-8 text-slate-400">No invoices found</div>
                  ) : (
                    <div className="space-y-3">
                      {invoices.map((invoice) => (
                        <div key={invoice.id} className="bg-slate-700/30 border border-slate-600 rounded-lg p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <h3 className="text-white font-semibold">{getMemberName(invoice.member_id)}</h3>
                                {getStatusBadge(invoice.status)}
                              </div>
                              <div className="grid grid-cols-2 gap-2 text-sm text-slate-400">
                                <div>Invoice: {invoice.invoice_number}</div>
                                <div>Amount: R {invoice.amount.toFixed(2)}</div>
                                <div>Due: {new Date(invoice.due_date).toLocaleDateString()}</div>
                                <div>{invoice.description}</div>
                              </div>
                            </div>
                            {invoice.status === 'pending' && (
                              <Button
                                size="sm"
                                className="bg-emerald-500 hover:bg-emerald-600"
                                onClick={() => openPaymentDialog(invoice)}
                              >
                                Record Payment
                              </Button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Payment Report Tab */}
            <TabsContent value="report" className="mt-6 space-y-4">
              {/* Filters Card */}
              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Filter className="w-5 h-5" />
                    Advanced Filters
                  </CardTitle>
                  <CardDescription className="text-slate-400">
                    Filter payment report by various criteria
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="space-y-2">
                      <Label>Member</Label>
                      <Select value={filters.member_id} onValueChange={(value) => setFilters({...filters, member_id: value})}>
                        <SelectTrigger className="bg-slate-700/50 border-slate-600">
                          <SelectValue placeholder="All members" />
                        </SelectTrigger>
                        <SelectContent className="bg-slate-800 border-slate-700">
                          <SelectItem value="__all__">All Members</SelectItem>
                          {members.map((member) => (
                            <SelectItem key={member.id} value={member.id}>
                              {member.first_name} {member.last_name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>Status</Label>
                      <Select value={filters.status} onValueChange={(value) => setFilters({...filters, status: value})}>
                        <SelectTrigger className="bg-slate-700/50 border-slate-600">
                          <SelectValue placeholder="All statuses" />
                        </SelectTrigger>
                        <SelectContent className="bg-slate-800 border-slate-700">
                          <SelectItem value="__all__">All Statuses</SelectItem>
                          <SelectItem value="paid">Paid</SelectItem>
                          <SelectItem value="pending">Pending</SelectItem>
                          <SelectItem value="overdue">Overdue</SelectItem>
                          <SelectItem value="failed">Failed</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>Source</Label>
                      <Select value={filters.source} onValueChange={(value) => setFilters({...filters, source: value})}>
                        <SelectTrigger className="bg-slate-700/50 border-slate-600">
                          <SelectValue placeholder="All sources" />
                        </SelectTrigger>
                        <SelectContent className="bg-slate-800 border-slate-700">
                          <SelectItem value="__all__">All Sources</SelectItem>
                          {paymentSources.map((source) => (
                            <SelectItem key={source.id} value={source.name}>
                              {source.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>Start Date</Label>
                      <Input
                        type="date"
                        value={filters.start_date}
                        onChange={(e) => setFilters({...filters, start_date: e.target.value})}
                        className="bg-slate-700/50 border-slate-600"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>End Date</Label>
                      <Input
                        type="date"
                        value={filters.end_date}
                        onChange={(e) => setFilters({...filters, end_date: e.target.value})}
                        className="bg-slate-700/50 border-slate-600"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Payment Gateway</Label>
                      <Input
                        value={filters.payment_gateway}
                        onChange={(e) => setFilters({...filters, payment_gateway: e.target.value})}
                        placeholder="e.g., Stripe, PayPal"
                        className="bg-slate-700/50 border-slate-600"
                      />
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      onClick={fetchPaymentReport}
                      className="bg-emerald-500 hover:bg-emerald-600"
                      disabled={reportLoading}
                    >
                      <Search className="w-4 h-4 mr-2" />
                      {reportLoading ? 'Loading...' : 'Generate Report'}
                    </Button>
                    <Button
                      onClick={exportReport}
                      variant="outline"
                      className="border-slate-600 hover:bg-slate-700"
                      disabled={paymentReport.length === 0}
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Export CSV
                    </Button>
                    <Button
                      onClick={() => setFilters({member_id: '__all__', status: '__all__', payment_gateway: '', source: '__all__', start_date: '', end_date: ''})}
                      variant="outline"
                      className="border-slate-600 hover:bg-slate-700"
                    >
                      Clear Filters
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Report Results */}
              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
                <CardHeader>
                  <CardTitle className="text-white">Payment Report Results</CardTitle>
                  <CardDescription className="text-slate-400">
                    {paymentReport.length > 0 ? `Showing ${paymentReport.length} records` : 'Click "Generate Report" to view results'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {reportLoading ? (
                    <div className="text-center py-8 text-slate-400">Loading report...</div>
                  ) : paymentReport.length === 0 ? (
                    <div className="text-center py-8 text-slate-400">No results. Apply filters and generate report.</div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead className="border-b border-slate-600">
                          <tr className="text-left text-slate-400">
                            <th className="p-2">Member</th>
                            <th className="p-2">Membership #</th>
                            <th className="p-2">Type</th>
                            <th className="p-2">Invoice</th>
                            <th className="p-2">Amount</th>
                            <th className="p-2">Status</th>
                            <th className="p-2">Debt</th>
                            <th className="p-2">Source</th>
                            <th className="p-2">Due Date</th>
                          </tr>
                        </thead>
                        <tbody>
                          {paymentReport.map((item, index) => (
                            <tr key={index} className="border-b border-slate-700/50 hover:bg-slate-700/20">
                              <td className="p-2 text-white">{item.member_name}</td>
                              <td className="p-2 text-slate-400">{item.membership_number}</td>
                              <td className="p-2 text-slate-400">{item.membership_type}</td>
                              <td className="p-2 text-slate-400">{item.invoice_number}</td>
                              <td className="p-2 text-white">R {item.amount.toFixed(2)}</td>
                              <td className="p-2">{getStatusBadge(item.status)}</td>
                              <td className="p-2">
                                {item.debt > 0 ? (
                                  <span className="text-red-400 font-semibold">R {item.debt.toFixed(2)}</span>
                                ) : (
                                  <span className="text-emerald-400">-</span>
                                )}
                              </td>
                              <td className="p-2 text-slate-400">{item.source || '-'}</td>
                              <td className="p-2 text-slate-400">
                                {item.due_date ? new Date(item.due_date).toLocaleDateString() : '-'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Payment Dialog */}
          <Dialog open={paymentDialogOpen} onOpenChange={setPaymentDialogOpen}>
            <DialogContent className="bg-slate-800 border-slate-700 text-white">
              <DialogHeader>
                <DialogTitle>Record Payment</DialogTitle>
                <DialogDescription className="text-slate-400">
                  Process payment for invoice {selectedInvoice?.invoice_number}
                </DialogDescription>
              </DialogHeader>
              {selectedInvoice && (
                <div className="space-y-4">
                  <div className="bg-slate-700/30 p-3 rounded-lg space-y-2">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Member:</span>
                      <span className="text-white">{getMemberName(selectedInvoice.member_id)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Amount:</span>
                      <span className="text-white font-semibold">R {selectedInvoice.amount.toFixed(2)}</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Payment Method</Label>
                    <Select value={paymentMethod} onValueChange={setPaymentMethod}>
                      <SelectTrigger className="bg-slate-700/50 border-slate-600">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        <SelectItem value="cash">Cash</SelectItem>
                        <SelectItem value="card">Card</SelectItem>
                        <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                        <SelectItem value="debit_order">Debit Order</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      onClick={handlePayment}
                      className="flex-1 bg-emerald-500 hover:bg-emerald-600"
                    >
                      Confirm Payment
                    </Button>
                    <Button
                      onClick={() => setPaymentDialogOpen(false)}
                      variant="outline"
                      className="border-slate-600 hover:bg-slate-700"
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </div>
  );
}
