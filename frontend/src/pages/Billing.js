import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FileText, DollarSign, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

export default function Billing() {
  const [invoices, setInvoices] = useState([]);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState('cash');

  useEffect(() => {
    fetchInvoices();
    fetchMembers();
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

  const openPaymentDialog = (invoice) => {
    setSelectedInvoice(invoice);
    setPaymentDialogOpen(true);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'paid':
        return <CheckCircle className="w-5 h-5 text-emerald-400" />;
      case 'pending':
        return <Clock className="w-5 h-5 text-amber-400" />;
      case 'overdue':
        return <AlertCircle className="w-5 h-5 text-red-400" />;
      default:
        return <FileText className="w-5 h-5 text-slate-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'paid':
        return 'bg-emerald-900/20 border-emerald-500';
      case 'pending':
        return 'bg-amber-900/20 border-amber-500';
      case 'overdue':
        return 'bg-red-900/20 border-red-500';
      default:
        return 'bg-slate-800/50 border-slate-700';
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
            <h1 className="text-4xl font-bold text-white mb-2" data-testid="billing-title">Billing & Invoices</h1>
            <p className="text-slate-400">Manage payments and recurring billing</p>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-slate-400 text-sm">Total Invoices</p>
                    <p className="text-2xl font-bold text-white mt-1">{invoices.length}</p>
                  </div>
                  <FileText className="w-8 h-8 text-blue-400" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-emerald-900/20 border-emerald-500">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-emerald-400 text-sm">Paid</p>
                    <p className="text-2xl font-bold text-white mt-1">
                      {invoices.filter(inv => inv.status === 'paid').length}
                    </p>
                  </div>
                  <CheckCircle className="w-8 h-8 text-emerald-400" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-amber-900/20 border-amber-500">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-amber-400 text-sm">Pending</p>
                    <p className="text-2xl font-bold text-white mt-1">
                      {invoices.filter(inv => inv.status === 'pending').length}
                    </p>
                  </div>
                  <Clock className="w-8 h-8 text-amber-400" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-red-900/20 border-red-500">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-red-400 text-sm">Overdue</p>
                    <p className="text-2xl font-bold text-white mt-1">
                      {invoices.filter(inv => inv.status === 'overdue').length}
                    </p>
                  </div>
                  <AlertCircle className="w-8 h-8 text-red-400" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Invoices List */}
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
            <CardHeader>
              <CardTitle className="text-white">All Invoices</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center text-slate-400 py-8">Loading invoices...</div>
              ) : (
                <div className="space-y-3">
                  {invoices.map((invoice) => (
                    <div
                      key={invoice.id}
                      className={`p-4 rounded-lg border-2 ${getStatusColor(invoice.status)} hover:bg-slate-700/30 transition-all`}
                      data-testid={`invoice-${invoice.id}`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4 flex-1">
                          {getStatusIcon(invoice.status)}
                          <div className="flex-1">
                            <p className="text-white font-medium">{invoice.invoice_number}</p>
                            <p className="text-slate-400 text-sm">{getMemberName(invoice.member_id)}</p>
                            <p className="text-slate-500 text-xs mt-1">{invoice.description}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-6">
                          <div className="text-right">
                            <p className="text-white font-bold text-lg">R {invoice.amount.toFixed(2)}</p>
                            <p className="text-slate-400 text-xs">Due: {new Date(invoice.due_date).toLocaleDateString()}</p>
                            {invoice.paid_date && (
                              <p className="text-emerald-400 text-xs">Paid: {new Date(invoice.paid_date).toLocaleDateString()}</p>
                            )}
                          </div>
                          <div className="flex flex-col gap-2">
                            <Badge variant={invoice.status === 'paid' ? 'default' : invoice.status === 'overdue' ? 'destructive' : 'secondary'}>
                              {invoice.status}
                            </Badge>
                            {invoice.status !== 'paid' && (
                              <Button
                                size="sm"
                                onClick={() => openPaymentDialog(invoice)}
                                className="bg-gradient-to-r from-emerald-500 to-teal-600"
                                data-testid={`pay-invoice-${invoice.id}`}
                              >
                                <DollarSign className="w-4 h-4 mr-1" />
                                Pay
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Payment Dialog */}
          <Dialog open={paymentDialogOpen} onOpenChange={setPaymentDialogOpen}>
            <DialogContent className="bg-slate-800 border-slate-700 text-white">
              <DialogHeader>
                <DialogTitle>Process Payment</DialogTitle>
                <DialogDescription className="text-slate-400">
                  {selectedInvoice && `Invoice: ${selectedInvoice.invoice_number}`}
                </DialogDescription>
              </DialogHeader>
              {selectedInvoice && (
                <div className="space-y-4">
                  <div className="p-4 rounded-lg bg-slate-700/50">
                    <div className="flex justify-between mb-2">
                      <span className="text-slate-400">Member:</span>
                      <span className="text-white font-medium">{getMemberName(selectedInvoice.member_id)}</span>
                    </div>
                    <div className="flex justify-between mb-2">
                      <span className="text-slate-400">Amount:</span>
                      <span className="text-white font-bold text-lg">R {selectedInvoice.amount.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Description:</span>
                      <span className="text-white">{selectedInvoice.description}</span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-slate-200">Payment Method</label>
                    <Select value={paymentMethod} onValueChange={setPaymentMethod}>
                      <SelectTrigger className="bg-slate-700/50 border-slate-600" data-testid="payment-method-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        <SelectItem value="cash">Cash</SelectItem>
                        <SelectItem value="card">Card</SelectItem>
                        <SelectItem value="debit_order">Debit Order</SelectItem>
                        <SelectItem value="eft">EFT</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <Button
                    onClick={handlePayment}
                    className="w-full bg-gradient-to-r from-emerald-500 to-teal-600"
                    data-testid="confirm-payment-button"
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Confirm Payment
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
