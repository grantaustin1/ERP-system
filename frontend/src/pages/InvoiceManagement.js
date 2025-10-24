import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { FileText, Plus, Edit, Trash2, Eye, Download, Settings } from 'lucide-react';
import { toast } from 'sonner';
import { usePermissions } from '@/contexts/PermissionContext';
import PermissionGuard from '@/components/PermissionGuard';

export default function InvoiceManagement() {
  const { canCreate, canEdit, canDelete } = usePermissions();
  const [invoices, setInvoices] = useState([]);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  
  // Invoice form state
  const [formData, setFormData] = useState({
    member_id: '',
    description: '',
    due_date: '',
    notes: '',
    line_items: []
  });

  // Billing settings state
  const [billingSettings, setBillingSettings] = useState({
    auto_email_invoices: false,
    email_on_invoice_created: false,
    email_on_invoice_overdue: false,
    email_reminder_days_before_due: [7, 3, 1],
    default_tax_rate: 15.0,
    tax_enabled: true,
    tax_number: '',
    invoice_prefix: 'INV',
    company_name: '',
    company_address: '',
    company_phone: '',
    company_email: '',
    default_payment_terms_days: 30,
    auto_generate_membership_invoices: false,
    days_before_renewal_to_invoice: 5
  });

  // Single line item state for adding
  const [newLineItem, setNewLineItem] = useState({
    description: '',
    quantity: 1,
    unit_price: 0,
    discount_percent: 0,
    tax_percent: 15
  });

  useEffect(() => {
    fetchInvoices();
    fetchMembers();
    fetchBillingSettings();
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

  const fetchBillingSettings = async () => {
    try {
      const response = await axios.get(`${API}/billing/settings`);
      setBillingSettings(response.data);
    } catch (error) {
      console.error('Failed to fetch billing settings');
    }
  };

  const saveBillingSettings = async () => {
    try {
      await axios.post(`${API}/billing/settings`, billingSettings);
      toast.success('Billing settings saved successfully!');
      setSettingsDialogOpen(false);
    } catch (error) {
      toast.error('Failed to save billing settings');
    }
  };

  const addLineItem = () => {
    if (!newLineItem.description || newLineItem.unit_price <= 0) {
      toast.error('Please enter description and unit price');
      return;
    }

    setFormData({
      ...formData,
      line_items: [...formData.line_items, { ...newLineItem }]
    });

    // Reset line item form
    setNewLineItem({
      description: '',
      quantity: 1,
      unit_price: 0,
      discount_percent: 0,
      tax_percent: billingSettings.default_tax_rate || 15
    });
  };

  const removeLineItem = (index) => {
    setFormData({
      ...formData,
      line_items: formData.line_items.filter((_, i) => i !== index)
    });
  };

  const calculateLineItemTotal = (item) => {
    const subtotal = item.quantity * item.unit_price;
    const discount = subtotal * (item.discount_percent / 100);
    const subtotalAfterDiscount = subtotal - discount;
    const tax = subtotalAfterDiscount * (item.tax_percent / 100);
    return subtotalAfterDiscount + tax;
  };

  const calculateInvoiceTotal = () => {
    return formData.line_items.reduce((sum, item) => sum + calculateLineItemTotal(item), 0);
  };

  const handleCreateInvoice = async () => {
    if (!formData.member_id || !formData.description || !formData.due_date || formData.line_items.length === 0) {
      toast.error('Please fill all required fields and add at least one line item');
      return;
    }

    try {
      await axios.post(`${API}/invoices`, formData);
      toast.success('Invoice created successfully!');
      setCreateDialogOpen(false);
      resetForm();
      fetchInvoices();
    } catch (error) {
      toast.error('Failed to create invoice');
    }
  };

  const handleUpdateInvoice = async () => {
    if (!selectedInvoice) return;

    try {
      await axios.put(`${API}/invoices/${selectedInvoice.id}`, formData);
      toast.success('Invoice updated successfully!');
      setEditDialogOpen(false);
      resetForm();
      fetchInvoices();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update invoice');
    }
  };

  const handleVoidInvoice = async (invoiceId) => {
    if (!window.confirm('Are you sure you want to void this invoice?')) return;

    try {
      await axios.delete(`${API}/invoices/${invoiceId}?reason=Voided by user`);
      toast.success('Invoice voided successfully!');
      fetchInvoices();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to void invoice');
    }
  };

  const handleDownloadPDF = async (invoiceId, invoiceNumber) => {
    try {
      const response = await axios.get(`${API}/invoices/${invoiceId}/pdf`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `invoice_${invoiceNumber}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Invoice PDF downloaded!');
    } catch (error) {
      toast.error('Failed to generate PDF');
    }
  };

  const openEditDialog = (invoice) => {
    setSelectedInvoice(invoice);
    setFormData({
      member_id: invoice.member_id,
      description: invoice.description,
      due_date: invoice.due_date.substring(0, 10),
      notes: invoice.notes || '',
      line_items: invoice.line_items || []
    });
    setEditDialogOpen(true);
  };

  const resetForm = () => {
    setFormData({
      member_id: '',
      description: '',
      due_date: '',
      notes: '',
      line_items: []
    });
    setSelectedInvoice(null);
  };

  const getStatusBadge = (status) => {
    const badges = {
      paid: <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/50">Paid</Badge>,
      pending: <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/50">Pending</Badge>,
      overdue: <Badge className="bg-red-500/20 text-red-400 border-red-500/50">Overdue</Badge>,
      failed: <Badge className="bg-red-500/20 text-red-400 border-red-500/50">Failed</Badge>,
      void: <Badge className="bg-slate-500/20 text-slate-400 border-slate-500/50">Void</Badge>
    };
    return badges[status] || <Badge variant="outline">{status}</Badge>;
  };

  const getMemberName = (memberId) => {
    const member = members.find(m => m.id === memberId);
    return member ? `${member.first_name} ${member.last_name}` : 'Unknown';
  };

  return (
    <div className="flex min-h-screen bg-slate-950">
      <Sidebar />
      <div className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8 flex justify-between items-center">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">Invoice Management</h1>
              <p className="text-slate-400">Create, manage, and track invoices</p>
            </div>
            <div className="flex gap-3">
              <Dialog open={settingsDialogOpen} onOpenChange={setSettingsDialogOpen}>
                <DialogTrigger asChild>
                  <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800">
                    <Settings className="h-4 w-4 mr-2" />
                    Settings
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto bg-slate-900 border-slate-800">
                  <DialogHeader>
                    <DialogTitle className="text-white">Billing Settings</DialogTitle>
                    <DialogDescription className="text-slate-400">
                      Configure invoice settings and automation
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-6 py-4">
                    {/* Email Settings */}
                    <Card className="bg-slate-800/50 border-slate-700">
                      <CardHeader>
                        <CardTitle className="text-white text-lg">Email Automation</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="flex items-center justify-between">
                          <Label className="text-slate-300">Auto-email invoices</Label>
                          <input
                            type="checkbox"
                            checked={billingSettings.auto_email_invoices}
                            onChange={(e) => setBillingSettings({...billingSettings, auto_email_invoices: e.target.checked})}
                            className="w-4 h-4"
                          />
                        </div>
                        <div className="flex items-center justify-between">
                          <Label className="text-slate-300">Email when invoice created</Label>
                          <input
                            type="checkbox"
                            checked={billingSettings.email_on_invoice_created}
                            onChange={(e) => setBillingSettings({...billingSettings, email_on_invoice_created: e.target.checked})}
                            className="w-4 h-4"
                          />
                        </div>
                        <div className="flex items-center justify-between">
                          <Label className="text-slate-300">Email when invoice overdue</Label>
                          <input
                            type="checkbox"
                            checked={billingSettings.email_on_invoice_overdue}
                            onChange={(e) => setBillingSettings({...billingSettings, email_on_invoice_overdue: e.target.checked})}
                            className="w-4 h-4"
                          />
                        </div>
                      </CardContent>
                    </Card>

                    {/* Tax Settings */}
                    <Card className="bg-slate-800/50 border-slate-700">
                      <CardHeader>
                        <CardTitle className="text-white text-lg">Tax Configuration</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="flex items-center justify-between">
                          <Label className="text-slate-300">Tax enabled</Label>
                          <input
                            type="checkbox"
                            checked={billingSettings.tax_enabled}
                            onChange={(e) => setBillingSettings({...billingSettings, tax_enabled: e.target.checked})}
                            className="w-4 h-4"
                          />
                        </div>
                        <div>
                          <Label className="text-slate-300">Default tax rate (%)</Label>
                          <Input
                            type="number"
                            value={billingSettings.default_tax_rate}
                            onChange={(e) => setBillingSettings({...billingSettings, default_tax_rate: parseFloat(e.target.value)})}
                            className="bg-slate-800 border-slate-700 text-white mt-2"
                          />
                        </div>
                        <div>
                          <Label className="text-slate-300">Tax number</Label>
                          <Input
                            value={billingSettings.tax_number}
                            onChange={(e) => setBillingSettings({...billingSettings, tax_number: e.target.value})}
                            className="bg-slate-800 border-slate-700 text-white mt-2"
                            placeholder="Company VAT/Tax registration number"
                          />
                        </div>
                      </CardContent>
                    </Card>

                    {/* Company Details */}
                    <Card className="bg-slate-800/50 border-slate-700">
                      <CardHeader>
                        <CardTitle className="text-white text-lg">Company Information</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div>
                          <Label className="text-slate-300">Company name</Label>
                          <Input
                            value={billingSettings.company_name}
                            onChange={(e) => setBillingSettings({...billingSettings, company_name: e.target.value})}
                            className="bg-slate-800 border-slate-700 text-white mt-2"
                          />
                        </div>
                        <div>
                          <Label className="text-slate-300">Company address</Label>
                          <Textarea
                            value={billingSettings.company_address}
                            onChange={(e) => setBillingSettings({...billingSettings, company_address: e.target.value})}
                            className="bg-slate-800 border-slate-700 text-white mt-2"
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label className="text-slate-300">Company phone</Label>
                            <Input
                              value={billingSettings.company_phone}
                              onChange={(e) => setBillingSettings({...billingSettings, company_phone: e.target.value})}
                              className="bg-slate-800 border-slate-700 text-white mt-2"
                            />
                          </div>
                          <div>
                            <Label className="text-slate-300">Company email</Label>
                            <Input
                              value={billingSettings.company_email}
                              onChange={(e) => setBillingSettings({...billingSettings, company_email: e.target.value})}
                              className="bg-slate-800 border-slate-700 text-white mt-2"
                            />
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Button onClick={saveBillingSettings} className="w-full bg-blue-600 hover:bg-blue-700">
                      Save Settings
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>

              <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="bg-blue-600 hover:bg-blue-700">
                    <Plus className="h-4 w-4 mr-2" />
                    Create Invoice
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-slate-900 border-slate-800">
                  <DialogHeader>
                    <DialogTitle className="text-white">Create New Invoice</DialogTitle>
                    <DialogDescription className="text-slate-400">
                      Generate a new invoice with itemized billing
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-slate-300">Member *</Label>
                        <Select value={formData.member_id} onValueChange={(value) => setFormData({...formData, member_id: value})}>
                          <SelectTrigger className="bg-slate-800 border-slate-700 text-white">
                            <SelectValue placeholder="Select member" />
                          </SelectTrigger>
                          <SelectContent className="bg-slate-800 border-slate-700">
                            {members.map(member => (
                              <SelectItem key={member.id} value={member.id} className="text-white">
                                {member.first_name} {member.last_name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label className="text-slate-300">Due date *</Label>
                        <Input
                          type="date"
                          value={formData.due_date}
                          onChange={(e) => setFormData({...formData, due_date: e.target.value})}
                          className="bg-slate-800 border-slate-700 text-white"
                        />
                      </div>
                    </div>

                    <div>
                      <Label className="text-slate-300">Description *</Label>
                      <Input
                        value={formData.description}
                        onChange={(e) => setFormData({...formData, description: e.target.value})}
                        className="bg-slate-800 border-slate-700 text-white"
                        placeholder="e.g., Monthly membership fee"
                      />
                    </div>

                    {/* Line Items Section */}
                    <div className="space-y-3">
                      <Label className="text-white text-lg">Line Items *</Label>
                      
                      {/* Add line item form */}
                      <Card className="bg-slate-800/50 border-slate-700">
                        <CardContent className="pt-6">
                          <div className="grid grid-cols-6 gap-3 mb-3">
                            <div className="col-span-2">
                              <Label className="text-slate-300">Description</Label>
                              <Input
                                value={newLineItem.description}
                                onChange={(e) => setNewLineItem({...newLineItem, description: e.target.value})}
                                className="bg-slate-800 border-slate-700 text-white"
                                placeholder="Item description"
                              />
                            </div>
                            <div>
                              <Label className="text-slate-300">Qty</Label>
                              <Input
                                type="number"
                                value={newLineItem.quantity}
                                onChange={(e) => setNewLineItem({...newLineItem, quantity: parseFloat(e.target.value)})}
                                className="bg-slate-800 border-slate-700 text-white"
                              />
                            </div>
                            <div>
                              <Label className="text-slate-300">Price</Label>
                              <Input
                                type="number"
                                value={newLineItem.unit_price}
                                onChange={(e) => setNewLineItem({...newLineItem, unit_price: parseFloat(e.target.value)})}
                                className="bg-slate-800 border-slate-700 text-white"
                              />
                            </div>
                            <div>
                              <Label className="text-slate-300">Disc%</Label>
                              <Input
                                type="number"
                                value={newLineItem.discount_percent}
                                onChange={(e) => setNewLineItem({...newLineItem, discount_percent: parseFloat(e.target.value)})}
                                className="bg-slate-800 border-slate-700 text-white"
                              />
                            </div>
                            <div>
                              <Label className="text-slate-300">Tax%</Label>
                              <Input
                                type="number"
                                value={newLineItem.tax_percent}
                                onChange={(e) => setNewLineItem({...newLineItem, tax_percent: parseFloat(e.target.value)})}
                                className="bg-slate-800 border-slate-700 text-white"
                              />
                            </div>
                          </div>
                          <Button onClick={addLineItem} className="w-full bg-blue-600 hover:bg-blue-700">
                            Add Item
                          </Button>
                        </CardContent>
                      </Card>

                      {/* Display added line items */}
                      {formData.line_items.length > 0 && (
                        <div className="space-y-2">
                          {formData.line_items.map((item, index) => (
                            <Card key={index} className="bg-slate-800/30 border-slate-700">
                              <CardContent className="py-3 px-4">
                                <div className="flex justify-between items-center">
                                  <div className="flex-1">
                                    <p className="text-white font-medium">{item.description}</p>
                                    <p className="text-slate-400 text-sm">
                                      Qty: {item.quantity} × R{item.unit_price} | Disc: {item.discount_percent}% | Tax: {item.tax_percent}%
                                    </p>
                                  </div>
                                  <div className="flex items-center gap-4">
                                    <span className="text-white font-semibold">R{calculateLineItemTotal(item).toFixed(2)}</span>
                                    <Button
                                      size="sm"
                                      variant="destructive"
                                      onClick={() => removeLineItem(index)}
                                      className="h-8 w-8 p-0"
                                    >
                                      <Trash2 className="h-4 w-4" />
                                    </Button>
                                  </div>
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                          <div className="flex justify-end pt-3 border-t border-slate-700">
                            <div className="text-right">
                              <p className="text-slate-400 text-sm">Total Amount</p>
                              <p className="text-white text-2xl font-bold">R{calculateInvoiceTotal().toFixed(2)}</p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    <div>
                      <Label className="text-slate-300">Notes (optional)</Label>
                      <Textarea
                        value={formData.notes}
                        onChange={(e) => setFormData({...formData, notes: e.target.value})}
                        className="bg-slate-800 border-slate-700 text-white"
                        placeholder="Additional notes or payment instructions"
                      />
                    </div>

                    <Button onClick={handleCreateInvoice} className="w-full bg-blue-600 hover:bg-blue-700">
                      Create Invoice
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </div>

          {/* Invoices Table */}
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
              <CardTitle className="text-white">All Invoices</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <p className="text-slate-400">Loading invoices...</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-slate-800">
                        <th className="text-left py-3 px-4 text-slate-300 font-medium">Invoice #</th>
                        <th className="text-left py-3 px-4 text-slate-300 font-medium">Member</th>
                        <th className="text-left py-3 px-4 text-slate-300 font-medium">Description</th>
                        <th className="text-left py-3 px-4 text-slate-300 font-medium">Amount</th>
                        <th className="text-left py-3 px-4 text-slate-300 font-medium">Due Date</th>
                        <th className="text-left py-3 px-4 text-slate-300 font-medium">Status</th>
                        <th className="text-right py-3 px-4 text-slate-300 font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {invoices.map((invoice) => (
                        <tr key={invoice.id} className="border-b border-slate-800 hover:bg-slate-800/30">
                          <td className="py-3 px-4 text-slate-300">{invoice.invoice_number}</td>
                          <td className="py-3 px-4 text-slate-300">{getMemberName(invoice.member_id)}</td>
                          <td className="py-3 px-4 text-slate-300">{invoice.description}</td>
                          <td className="py-3 px-4 text-white font-medium">R{invoice.amount?.toFixed(2)}</td>
                          <td className="py-3 px-4 text-slate-300">
                            {new Date(invoice.due_date).toLocaleDateString()}
                          </td>
                          <td className="py-3 px-4">{getStatusBadge(invoice.status)}</td>
                          <td className="py-3 px-4">
                            <div className="flex justify-end gap-2">
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleDownloadPDF(invoice.id, invoice.invoice_number)}
                                className="h-8 w-8 p-0 text-slate-400 hover:text-white hover:bg-slate-800"
                              >
                                <Download className="h-4 w-4" />
                              </Button>
                              {invoice.status !== 'paid' && invoice.status !== 'void' && (
                                <>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => openEditDialog(invoice)}
                                    className="h-8 w-8 p-0 text-slate-400 hover:text-white hover:bg-slate-800"
                                  >
                                    <Edit className="h-4 w-4" />
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => handleVoidInvoice(invoice.id)}
                                    className="h-8 w-8 p-0 text-red-400 hover:text-red-300 hover:bg-red-900/20"
                                  >
                                    <Trash2 className="h-4 w-4" />
                                  </Button>
                                </>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {invoices.length === 0 && (
                    <p className="text-center py-8 text-slate-400">No invoices found</p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Edit Dialog */}
          <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-slate-900 border-slate-800">
              <DialogHeader>
                <DialogTitle className="text-white">Edit Invoice</DialogTitle>
                <DialogDescription className="text-slate-400">
                  Update invoice details and line items
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                {/* Same form as create but with handleUpdateInvoice */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-300">Member</Label>
                    <Input
                      value={getMemberName(formData.member_id)}
                      disabled
                      className="bg-slate-800 border-slate-700 text-slate-400"
                    />
                  </div>
                  <div>
                    <Label className="text-slate-300">Due date *</Label>
                    <Input
                      type="date"
                      value={formData.due_date}
                      onChange={(e) => setFormData({...formData, due_date: e.target.value})}
                      className="bg-slate-800 border-slate-700 text-white"
                    />
                  </div>
                </div>

                <div>
                  <Label className="text-slate-300">Description *</Label>
                  <Input
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    className="bg-slate-800 border-slate-700 text-white"
                  />
                </div>

                {/* Line items editing - same as create */}
                <div className="space-y-3">
                  <Label className="text-white text-lg">Line Items</Label>
                  {formData.line_items.map((item, index) => (
                    <Card key={index} className="bg-slate-800/30 border-slate-700">
                      <CardContent className="py-3 px-4">
                        <div className="flex justify-between items-center">
                          <div className="flex-1">
                            <p className="text-white font-medium">{item.description}</p>
                            <p className="text-slate-400 text-sm">
                              Qty: {item.quantity} × R{item.unit_price} | Disc: {item.discount_percent}% | Tax: {item.tax_percent}%
                            </p>
                          </div>
                          <div className="flex items-center gap-4">
                            <span className="text-white font-semibold">R{calculateLineItemTotal(item).toFixed(2)}</span>
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => removeLineItem(index)}
                              className="h-8 w-8 p-0"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                  {formData.line_items.length > 0 && (
                    <div className="flex justify-end pt-3 border-t border-slate-700">
                      <div className="text-right">
                        <p className="text-slate-400 text-sm">Total Amount</p>
                        <p className="text-white text-2xl font-bold">R{calculateInvoiceTotal().toFixed(2)}</p>
                      </div>
                    </div>
                  )}
                </div>

                <div>
                  <Label className="text-slate-300">Notes</Label>
                  <Textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({...formData, notes: e.target.value})}
                    className="bg-slate-800 border-slate-700 text-white"
                  />
                </div>

                <Button onClick={handleUpdateInvoice} className="w-full bg-blue-600 hover:bg-blue-700">
                  Update Invoice
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </div>
  );
}
