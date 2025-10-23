import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Badge } from '../components/ui/badge';
import { Switch } from '../components/ui/switch';
import { useToast } from '../hooks/use-toast';
import { Plus, Edit, Trash2, DollarSign, Users, Calendar, CreditCard } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export default function PackageSetupEnhanced() {
  const [baseMemberships, setBaseMemberships] = useState([]);
  const [selectedBase, setSelectedBase] = useState(null);
  const [variations, setVariations] = useState([]);
  const [paymentOptions, setPaymentOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  // Dialog states
  const [baseDialogOpen, setBaseDialogOpen] = useState(false);
  const [variationDialogOpen, setVariationDialogOpen] = useState(false);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);

  // Forms
  const [baseForm, setBaseForm] = useState({
    name: '',
    description: '',
    price: '',
    duration_months: 12,
    max_members: 1,
    features: [],
    peak_hours_only: false,
    multi_site_access: false
  });

  const [variationForm, setVariationForm] = useState({
    base_membership_id: '',
    variation_type: '',
    discount_percentage: '',
    description: ''
  });

  const [paymentForm, setPaymentForm] = useState({
    membership_type_id: '',
    payment_name: '',
    payment_type: 'single',
    payment_frequency: 'one-time',
    installment_amount: '',
    number_of_installments: 1,
    auto_renewal_enabled: false,
    auto_renewal_frequency: 'monthly',
    auto_renewal_price: '',
    description: '',
    is_default: false,
    // Levy configuration
    levy_enabled: false,
    levy_frequency_type: 'none',
    levy_amount: '',
    levy_custom_schedule: [],
    levy_rollover_enabled: true
  });

  const variationTypes = [
    { value: 'student', label: 'Student Discount' },
    { value: 'corporate', label: 'Corporate Discount' },
    { value: 'senior', label: 'Senior Discount' },
    { value: 'family', label: 'Family Package' },
    { value: 'promo', label: 'Promotional' }
  ];

  const paymentFrequencies = [
    { value: 'one-time', label: 'One-time Payment' },
    { value: 'monthly', label: 'Monthly' },
    { value: 'quarterly', label: 'Quarterly' },
    { value: 'bi-annual', label: 'Bi-annual (6 months)' },
    { value: 'annual', label: 'Annual' }
  ];

  useEffect(() => {
    fetchBaseMemberships();
  }, []);

  useEffect(() => {
    if (selectedBase) {
      fetchVariations(selectedBase.id);
    }
  }, [selectedBase]);

  const fetchBaseMemberships = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/api/membership-types`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const bases = response.data.filter(m => m.is_base_membership);
      setBaseMemberships(bases);
    } catch (error) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to fetch memberships' });
    }
  };

  const fetchVariations = async (baseId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/api/membership-types/${baseId}/variations`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setVariations(response.data);
    } catch (error) {
      console.error('Failed to fetch variations:', error);
    }
  };

  const fetchPaymentOptions = async (membershipTypeId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/api/payment-options/${membershipTypeId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPaymentOptions(response.data);
    } catch (error) {
      console.error('Failed to fetch payment options:', error);
    }
  };

  const handleCreateBaseMembership = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const data = {
        ...baseForm,
        price: parseFloat(baseForm.price),
        duration_days: 0,
        billing_frequency: 'monthly',
        payment_type: 'debit_order',
        is_base_membership: true,
        levy_enabled: false,
        levy_frequency: 'annual',
        levy_timing: 'anniversary',
        levy_amount_type: 'fixed',
        levy_amount: 0.0,
        levy_payment_method: 'debit_order'
      };

      await axios.post(`${API}/api/membership-types`, data, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast({ title: 'Success', description: 'Base membership created' });
      fetchBaseMemberships();
      setBaseDialogOpen(false);
      resetBaseForm();
    } catch (error) {
      toast({ variant: 'destructive', title: 'Error', description: error.response?.data?.detail || 'Failed to create membership' });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateVariation = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');

      await axios.post(
        `${API}/api/membership-types/${variationForm.base_membership_id}/create-variation`,
        {
          variation_type: variationForm.variation_type,
          discount_percentage: parseFloat(variationForm.discount_percentage),
          description: variationForm.description
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast({ title: 'Success', description: 'Variation created successfully' });
      fetchVariations(variationForm.base_membership_id);
      setVariationDialogOpen(false);
      resetVariationForm();
    } catch (error) {
      toast({ variant: 'destructive', title: 'Error', description: error.response?.data?.detail || 'Failed to create variation' });
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePaymentOption = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');

      const data = {
        ...paymentForm,
        installment_amount: parseFloat(paymentForm.installment_amount),
        number_of_installments: parseInt(paymentForm.number_of_installments),
        auto_renewal_price: paymentForm.auto_renewal_price ? parseFloat(paymentForm.auto_renewal_price) : null,
        display_order: 0
      };

      await axios.post(`${API}/api/payment-options`, data, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast({ title: 'Success', description: 'Payment option created successfully' });
      fetchPaymentOptions(paymentForm.membership_type_id);
      setPaymentDialogOpen(false);
      resetPaymentForm();
    } catch (error) {
      toast({ variant: 'destructive', title: 'Error', description: error.response?.data?.detail || 'Failed to create payment option' });
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePaymentOption = async (optionId, membershipTypeId) => {
    if (!window.confirm('Are you sure you want to delete this payment option?')) return;

    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/api/payment-options/${optionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast({ title: 'Success', description: 'Payment option deleted' });
      fetchPaymentOptions(membershipTypeId);
    } catch (error) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to delete payment option' });
    }
  };

  const resetBaseForm = () => {
    setBaseForm({
      name: '',
      description: '',
      price: '',
      duration_months: 12,
      max_members: 1,
      features: [],
      peak_hours_only: false,
      multi_site_access: false
    });
  };

  const resetVariationForm = () => {
    setVariationForm({
      base_membership_id: '',
      variation_type: '',
      discount_percentage: '',
      description: ''
    });
  };

  const resetPaymentForm = () => {
    setPaymentForm({
      membership_type_id: '',
      payment_name: '',
      payment_type: 'single',
      payment_frequency: 'one-time',
      installment_amount: '',
      number_of_installments: 1,
      auto_renewal_enabled: false,
      auto_renewal_frequency: 'monthly',
      auto_renewal_price: '',
      description: '',
      is_default: false,
      // Levy configuration
      levy_enabled: false,
      levy_frequency_type: 'none',
      levy_amount: '',
      levy_custom_schedule: [],
      levy_rollover_enabled: true
    });
  };

  const handleSelectMembershipForPayment = async (membership) => {
    setPaymentForm({ ...paymentForm, membership_type_id: membership.id });
    await fetchPaymentOptions(membership.id);
  };

  const calculateTotalAmount = () => {
    const installment = parseFloat(paymentForm.installment_amount) || 0;
    const installments = parseInt(paymentForm.number_of_installments) || 1;
    return (installment * installments).toFixed(2);
  };

  const addCustomLevyDate = () => {
    setPaymentForm({
      ...paymentForm,
      levy_custom_schedule: [
        ...(paymentForm.levy_custom_schedule || []),
        { month: 1, day: 1, amount: '' }
      ]
    });
  };

  const updateCustomLevyDate = (index, field, value) => {
    const schedule = [...(paymentForm.levy_custom_schedule || [])];
    schedule[index] = { ...schedule[index], [field]: value };
    setPaymentForm({ ...paymentForm, levy_custom_schedule: schedule });
  };

  const removeCustomLevyDate = (index) => {
    const schedule = [...(paymentForm.levy_custom_schedule || [])];
    schedule.splice(index, 1);
    setPaymentForm({ ...paymentForm, levy_custom_schedule: schedule });
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Enhanced Package Setup</h1>
          <p className="text-gray-500 mt-1">Create base memberships, variations, and flexible payment options</p>
        </div>
      </div>

      <Tabs defaultValue="structure" className="space-y-4">
        <TabsList>
          <TabsTrigger value="structure">Membership Structure</TabsTrigger>
          <TabsTrigger value="payments">Payment Options</TabsTrigger>
        </TabsList>

        {/* MEMBERSHIP STRUCTURE TAB */}
        <TabsContent value="structure" className="space-y-4">
          <div className="flex gap-4">
            <Dialog open={baseDialogOpen} onOpenChange={setBaseDialogOpen}>
              <DialogTrigger asChild>
                <Button onClick={resetBaseForm}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Base Membership
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Create Base Membership</DialogTitle>
                  <DialogDescription>Define a new base membership package</DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Membership Name</Label>
                      <Input
                        value={baseForm.name}
                        onChange={(e) => setBaseForm({ ...baseForm, name: e.target.value })}
                        placeholder="e.g., Premium Gym Access"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Base Price (R)</Label>
                      <Input
                        type="number"
                        value={baseForm.price}
                        onChange={(e) => setBaseForm({ ...baseForm, price: e.target.value })}
                        placeholder="500.00"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Description</Label>
                    <Input
                      value={baseForm.description}
                      onChange={(e) => setBaseForm({ ...baseForm, description: e.target.value })}
                      placeholder="Full gym access with all amenities"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Duration (Months)</Label>
                      <Input
                        type="number"
                        value={baseForm.duration_months}
                        onChange={(e) => setBaseForm({ ...baseForm, duration_months: parseInt(e.target.value) })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Max Members per Membership</Label>
                      <Input
                        type="number"
                        min="1"
                        value={baseForm.max_members}
                        onChange={(e) => setBaseForm({ ...baseForm, max_members: parseInt(e.target.value) })}
                      />
                      <p className="text-xs text-gray-500">1 = Individual, 2+ = Family/Group</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      <Switch
                        checked={baseForm.peak_hours_only}
                        onCheckedChange={(checked) => setBaseForm({ ...baseForm, peak_hours_only: checked })}
                      />
                      <Label>Peak Hours Only</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Switch
                        checked={baseForm.multi_site_access}
                        onCheckedChange={(checked) => setBaseForm({ ...baseForm, multi_site_access: checked })}
                      />
                      <Label>Multi-Site Access</Label>
                    </div>
                  </div>
                </div>
                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setBaseDialogOpen(false)}>Cancel</Button>
                  <Button onClick={handleCreateBaseMembership} disabled={loading}>
                    {loading ? 'Creating...' : 'Create'}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {/* BASE MEMBERSHIPS LIST */}
          <div className="grid gap-4">
            {baseMemberships.map((base) => (
              <Card key={base.id} className="border-2">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="flex items-center gap-2">
                        {base.name}
                        {base.max_members > 1 && (
                          <Badge variant="secondary">
                            <Users className="h-3 w-3 mr-1" />
                            Up to {base.max_members} members
                          </Badge>
                        )}
                      </CardTitle>
                      <CardDescription>{base.description}</CardDescription>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold">R{base.price}</div>
                      <div className="text-sm text-gray-500">{base.duration_months} months</div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Add Variation Button */}
                    <Dialog open={variationDialogOpen} onOpenChange={setVariationDialogOpen}>
                      <DialogTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setVariationForm({ ...variationForm, base_membership_id: base.id });
                            setSelectedBase(base);
                          }}
                        >
                          <Plus className="mr-2 h-4 w-4" />
                          Add Variation
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Create Membership Variation</DialogTitle>
                          <DialogDescription>Add a discounted variation to {base.name}</DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4 py-4">
                          <div className="space-y-2">
                            <Label>Variation Type</Label>
                            <Select
                              value={variationForm.variation_type}
                              onValueChange={(value) => setVariationForm({ ...variationForm, variation_type: value })}
                            >
                              <SelectTrigger>
                                <SelectValue placeholder="Select type" />
                              </SelectTrigger>
                              <SelectContent>
                                {variationTypes.map((type) => (
                                  <SelectItem key={type.value} value={type.value}>
                                    {type.label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>

                          <div className="space-y-2">
                            <Label>Discount Percentage (%)</Label>
                            <Input
                              type="number"
                              min="0"
                              max="100"
                              value={variationForm.discount_percentage}
                              onChange={(e) => setVariationForm({ ...variationForm, discount_percentage: e.target.value })}
                              placeholder="10"
                            />
                          </div>

                          <div className="space-y-2">
                            <Label>Description (Optional)</Label>
                            <Input
                              value={variationForm.description}
                              onChange={(e) => setVariationForm({ ...variationForm, description: e.target.value })}
                              placeholder="Student discount for university students"
                            />
                          </div>
                        </div>
                        <div className="flex justify-end space-x-2">
                          <Button variant="outline" onClick={() => setVariationDialogOpen(false)}>Cancel</Button>
                          <Button onClick={handleCreateVariation} disabled={loading}>
                            {loading ? 'Creating...' : 'Create Variation'}
                          </Button>
                        </div>
                      </DialogContent>
                    </Dialog>

                    {/* Variations List */}
                    {variations.filter(v => v.base_membership_id === base.id).length > 0 && (
                      <div className="space-y-2">
                        <h4 className="font-medium text-sm">Variations:</h4>
                        <div className="grid gap-2">
                          {variations.filter(v => v.base_membership_id === base.id).map((variation) => (
                            <Card key={variation.id} className="border">
                              <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <div className="font-medium">{variation.name}</div>
                                    <div className="text-sm text-gray-500">{variation.description}</div>
                                  </div>
                                  <div className="text-right">
                                    <div className="font-bold text-lg">R{variation.price.toFixed(2)}</div>
                                    <Badge variant="secondary">{variation.discount_percentage}% off</Badge>
                                  </div>
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* PAYMENT OPTIONS TAB */}
        <TabsContent value="payments" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Payment Options Management</CardTitle>
              <CardDescription>
                Create multiple payment plans for each membership variation
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Select Membership */}
              <div className="space-y-2">
                <Label>Select Membership to Manage Payment Options</Label>
                <div className="grid gap-2">
                  {baseMemberships.map((base) => (
                    <div key={base.id} className="space-y-2">
                      <Button
                        variant={paymentForm.membership_type_id === base.id ? "default" : "outline"}
                        className="w-full justify-start"
                        onClick={() => handleSelectMembershipForPayment(base)}
                      >
                        {base.name} - R{base.price}
                      </Button>
                      
                      {/* Variations */}
                      {variations.filter(v => v.base_membership_id === base.id).map((variation) => (
                        <Button
                          key={variation.id}
                          variant={paymentForm.membership_type_id === variation.id ? "default" : "outline"}
                          className="w-full justify-start ml-8"
                          onClick={() => handleSelectMembershipForPayment(variation)}
                        >
                          {variation.name} - R{variation.price.toFixed(2)}
                        </Button>
                      ))}
                    </div>
                  ))}
                </div>
              </div>

              {/* Payment Options for Selected Membership */}
              {paymentForm.membership_type_id && (
                <div className="space-y-4 border-t pt-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium">Payment Options</h3>
                    <Dialog open={paymentDialogOpen} onOpenChange={setPaymentDialogOpen}>
                      <DialogTrigger asChild>
                        <Button onClick={resetPaymentForm}>
                          <Plus className="mr-2 h-4 w-4" />
                          Add Payment Option
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                        <DialogHeader>
                          <DialogTitle>Create Payment Option</DialogTitle>
                          <DialogDescription>
                            Define a payment plan for this membership
                          </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4 py-4">
                          <div className="space-y-2">
                            <Label>Payment Option Name</Label>
                            <Input
                              value={paymentForm.payment_name}
                              onChange={(e) => setPaymentForm({ ...paymentForm, payment_name: e.target.value })}
                              placeholder="e.g., Monthly Budget Plan, Upfront Saver"
                            />
                          </div>

                          <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                              <Label>Payment Type</Label>
                              <Select
                                value={paymentForm.payment_type}
                                onValueChange={(value) => setPaymentForm({ 
                                  ...paymentForm, 
                                  payment_type: value,
                                  payment_frequency: value === 'single' ? 'one-time' : 'monthly',
                                  number_of_installments: value === 'single' ? 1 : 12
                                })}
                              >
                                <SelectTrigger>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="single">Single Payment</SelectItem>
                                  <SelectItem value="recurring">Recurring Payments</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>

                            {paymentForm.payment_type === 'recurring' && (
                              <div className="space-y-2">
                                <Label>Payment Frequency</Label>
                                <Select
                                  value={paymentForm.payment_frequency}
                                  onValueChange={(value) => setPaymentForm({ ...paymentForm, payment_frequency: value })}
                                >
                                  <SelectTrigger>
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    {paymentFrequencies.filter(f => f.value !== 'one-time').map((freq) => (
                                      <SelectItem key={freq.value} value={freq.value}>
                                        {freq.label}
                                      </SelectItem>
                                    ))}
                                  </SelectContent>
                                </Select>
                              </div>
                            )}
                          </div>

                          <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                              <Label>Installment Amount (R)</Label>
                              <Input
                                type="number"
                                value={paymentForm.installment_amount}
                                onChange={(e) => setPaymentForm({ ...paymentForm, installment_amount: e.target.value })}
                                placeholder="500.00"
                              />
                            </div>
                            <div className="space-y-2">
                              <Label>Number of Installments</Label>
                              <Input
                                type="number"
                                min="1"
                                value={paymentForm.number_of_installments}
                                onChange={(e) => setPaymentForm({ ...paymentForm, number_of_installments: e.target.value })}
                                placeholder="12"
                              />
                            </div>
                          </div>

                          <div className="p-4 bg-gray-50 rounded-md">
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-medium">Total Amount:</span>
                              <span className="text-lg font-bold">R{calculateTotalAmount()}</span>
                            </div>
                          </div>

                          {/* Auto-Renewal Section */}
                          <div className="space-y-4 border-t pt-4">
                            <div className="flex items-center space-x-2">
                              <Switch
                                checked={paymentForm.auto_renewal_enabled}
                                onCheckedChange={(checked) => setPaymentForm({ ...paymentForm, auto_renewal_enabled: checked })}
                              />
                              <Label>Enable Auto-Renewal</Label>
                            </div>

                            {paymentForm.auto_renewal_enabled && (
                              <div className="space-y-4 ml-6">
                                <div className="space-y-2">
                                  <Label>Auto-Renewal Frequency</Label>
                                  <Select
                                    value={paymentForm.auto_renewal_frequency}
                                    onValueChange={(value) => setPaymentForm({ ...paymentForm, auto_renewal_frequency: value })}
                                  >
                                    <SelectTrigger>
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      <SelectItem value="monthly">Month-to-Month</SelectItem>
                                      <SelectItem value="same_frequency">Same Frequency (Restart Contract)</SelectItem>
                                    </SelectContent>
                                  </Select>
                                  <p className="text-xs text-gray-500">
                                    {paymentForm.auto_renewal_frequency === 'monthly' 
                                      ? 'After contract ends, continue on month-to-month basis'
                                      : 'After contract ends, restart for the same duration'}
                                  </p>
                                </div>

                                <div className="space-y-2">
                                  <Label>Auto-Renewal Price (Optional)</Label>
                                  <Input
                                    type="number"
                                    value={paymentForm.auto_renewal_price}
                                    onChange={(e) => setPaymentForm({ ...paymentForm, auto_renewal_price: e.target.value })}
                                    placeholder="Leave blank to use same price"
                                  />
                                  <p className="text-xs text-gray-500">
                                    Leave blank to continue at {paymentForm.installment_amount || 'same'} per period
                                  </p>
                                </div>
                              </div>
                            )}
                          </div>

                          <div className="space-y-2">
                            <Label>Description (Optional)</Label>
                            <Input
                              value={paymentForm.description}
                              onChange={(e) => setPaymentForm({ ...paymentForm, description: e.target.value })}
                              placeholder="Additional details about this payment option"
                            />
                          </div>

                          <div className="flex items-center space-x-2">
                            <Switch
                              checked={paymentForm.is_default}
                              onCheckedChange={(checked) => setPaymentForm({ ...paymentForm, is_default: checked })}
                            />
                            <Label>Set as Default Option</Label>
                          </div>

                          <div className="flex items-center space-x-2">
                            <Switch
                              checked={paymentForm.is_levy}
                              onCheckedChange={(checked) => setPaymentForm({ ...paymentForm, is_levy: checked })}
                            />
                            <Label>Is Levy</Label>
                          </div>
                        </div>
                        <div className="flex justify-end space-x-2">
                          <Button variant="outline" onClick={() => setPaymentDialogOpen(false)}>Cancel</Button>
                          <Button onClick={handleCreatePaymentOption} disabled={loading}>
                            {loading ? 'Creating...' : 'Create Payment Option'}
                          </Button>
                        </div>
                      </DialogContent>
                    </Dialog>
                  </div>

                  {/* Payment Options List */}
                  {paymentOptions.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <CreditCard className="h-12 w-12 mx-auto mb-2 text-gray-400" />
                      <p>No payment options created yet</p>
                      <p className="text-sm">Create flexible payment plans for members to choose from</p>
                    </div>
                  ) : (
                    <div className="grid gap-4">
                      {paymentOptions.map((option) => (
                        <Card key={option.id} className="border-2">
                          <CardContent className="p-4">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                  <h4 className="font-bold">{option.payment_name}</h4>
                                  {option.is_default && <Badge>Default</Badge>}
                                </div>
                                
                                <div className="space-y-1 text-sm">
                                  <div className="flex items-center gap-2">
                                    <DollarSign className="h-4 w-4 text-gray-500" />
                                    <span>
                                      R{option.installment_amount.toFixed(2)} × {option.number_of_installments} installments
                                      = <strong>R{option.total_amount.toFixed(2)}</strong>
                                    </span>
                                  </div>
                                  
                                  <div className="flex items-center gap-2">
                                    <Calendar className="h-4 w-4 text-gray-500" />
                                    <span className="capitalize">
                                      {option.payment_type === 'single' ? 'One-time payment' : `${option.payment_frequency} payments`}
                                    </span>
                                  </div>

                                  {option.auto_renewal_enabled && (
                                    <div className="flex items-center gap-2 text-blue-600">
                                      <Badge variant="outline" className="border-blue-600">
                                        Auto-Renewal: {option.auto_renewal_frequency === 'monthly' ? 'Month-to-Month' : 'Same Duration'}
                                      </Badge>
                                      {option.auto_renewal_price && (
                                        <span>@ R{option.auto_renewal_price.toFixed(2)}</span>
                                      )}
                                    </div>
                                  )}

                                  {option.description && (
                                    <p className="text-gray-500 italic">{option.description}</p>
                                  )}
                                </div>
                              </div>
                              
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDeletePaymentOption(option.id, option.membership_type_id)}
                              >
                                <Trash2 className="h-4 w-4 text-red-500" />
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
