import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Package, Plus, Percent, Copy, Layers } from 'lucide-react';
import { toast } from 'sonner';

export default function PackageSetup() {
  const [baseMemberships, setBaseMemberships] = useState([]);
  const [durationTemplates, setDurationTemplates] = useState([]);
  const [variationTypes, setVariationTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [baseDialogOpen, setBaseDialogOpen] = useState(false);
  const [variationDialogOpen, setVariationDialogOpen] = useState(false);
  const [selectedBase, setSelectedBase] = useState(null);
  const [expandedBase, setExpandedBase] = useState(null);
  const [baseVariations, setBaseVariations] = useState({});

  const [baseForm, setBaseForm] = useState({
    name: '',
    description: '',
    price: '',
    billing_frequency: 'monthly',
    duration_template: '',
    payment_type: 'debit_order',
    features: '',
    peak_hours_only: false,
    multi_site_access: false
  });

  const [variationForm, setVariationForm] = useState({
    base_membership_id: '',
    variation_type: 'student',
    discount_percentage: '',
    description: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [basesRes, durationsRes, variationsRes] = await Promise.all([
        axios.get(`${API}/membership-types/base/list`),
        axios.get(`${API}/membership-types/templates/durations`),
        axios.get(`${API}/membership-types/templates/variations`)
      ]);
      
      setBaseMemberships(basesRes.data);
      setDurationTemplates(durationsRes.data);
      setVariationTypes(variationsRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const fetchVariations = async (baseId) => {
    try {
      const response = await axios.get(`${API}/membership-types/${baseId}/variations`);
      setBaseVariations(prev => ({ ...prev, [baseId]: response.data }));
    } catch (error) {
      console.error('Failed to fetch variations');
    }
  };

  const handleBaseMembershipSubmit = async (e) => {
    e.preventDefault();
    try {
      // Get selected duration template
      const template = durationTemplates.find(t => t.name === baseForm.duration_template);
      if (!template) {
        toast.error('Please select a duration');
        return;
      }

      const data = {
        name: baseForm.name,
        description: baseForm.description,
        price: parseFloat(baseForm.price),
        billing_frequency: baseForm.billing_frequency,
        duration_months: template.months,
        duration_days: template.days,
        payment_type: baseForm.payment_type,
        is_base_membership: true,
        features: baseForm.features.split('\n').filter(f => f.trim()),
        peak_hours_only: baseForm.peak_hours_only,
        multi_site_access: baseForm.multi_site_access
      };

      await axios.post(`${API}/membership-types`, data);
      toast.success('Base membership created!');
      setBaseDialogOpen(false);
      setBaseForm({
        name: '',
        description: '',
        price: '',
        billing_frequency: 'monthly',
        duration_template: '',
        payment_type: 'debit_order',
        features: '',
        peak_hours_only: false,
        multi_site_access: false
      });
      fetchData();
    } catch (error) {
      toast.error('Failed to create base membership');
    }
  };

  const handleVariationSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/membership-types/${variationForm.base_membership_id}/create-variation`, {
        variation_type: variationForm.variation_type,
        discount_percentage: parseFloat(variationForm.discount_percentage),
        description: variationForm.description
      });
      
      toast.success('Variation created successfully!');
      setVariationDialogOpen(false);
      setVariationForm({
        base_membership_id: '',
        variation_type: 'student',
        discount_percentage: '',
        description: ''
      });
      fetchData();
      if (expandedBase) {
        fetchVariations(expandedBase);
      }
    } catch (error) {
      toast.error('Failed to create variation');
    }
  };

  const toggleExpanded = async (baseId) => {
    if (expandedBase === baseId) {
      setExpandedBase(null);
    } else {
      setExpandedBase(baseId);
      if (!baseVariations[baseId]) {
        await fetchVariations(baseId);
      }
    }
  };

  const openVariationDialog = (base) => {
    setVariationForm({
      ...variationForm,
      base_membership_id: base.id
    });
    setSelectedBase(base);
    setVariationDialogOpen(true);
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-white mb-2" data-testid="package-setup-title">Package Setup</h1>
            <p className="text-slate-400">Create base memberships and managed variations with consistent naming</p>
          </div>

          {/* Info Card */}
          <Card className="bg-blue-900/20 border-blue-500 mb-8">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <Layers className="w-5 h-5 text-blue-400 mt-0.5" />
                <div>
                  <h3 className="text-blue-200 font-semibold mb-1">Structured Package Management</h3>
                  <p className="text-blue-300 text-sm">
                    Create <strong>base memberships</strong> for core packages (e.g., "Premium 12 Month"), then add 
                    <strong> variations</strong> with automatic naming (e.g., "Premium 12 Month - Student Discount"). 
                    This prevents membership proliferation and maintains consistent pricing structure.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Tabs defaultValue="base" className="w-full">
            <TabsList className="bg-slate-800/50 border-slate-700">
              <TabsTrigger value="base">
                <Package className="w-4 h-4 mr-2" />
                Base Memberships ({baseMemberships.length})
              </TabsTrigger>
              <TabsTrigger value="templates">
                <Copy className="w-4 h-4 mr-2" />
                Duration Templates
              </TabsTrigger>
            </TabsList>

            {/* Base Memberships Tab */}
            <TabsContent value="base" className="mt-6">
              <div className="flex justify-between items-center mb-6">
                <p className="text-slate-400">Create and manage base membership packages</p>
                <Dialog open={baseDialogOpen} onOpenChange={setBaseDialogOpen}>
                  <DialogTrigger asChild>
                    <Button className="bg-gradient-to-r from-emerald-500 to-teal-600" data-testid="create-base-button">
                      <Plus className="w-4 h-4 mr-2" />
                      Create Base Package
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-2xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                      <DialogTitle>Create Base Membership Package</DialogTitle>
                      <DialogDescription className="text-slate-400">
                        This will be the foundation for variations and discounts
                      </DialogDescription>
                    </DialogHeader>
                    <form onSubmit={handleBaseMembershipSubmit} className="space-y-4">
                      <div className="space-y-2">
                        <Label>Package Name</Label>
                        <Input
                          value={baseForm.name}
                          onChange={(e) => setBaseForm({ ...baseForm, name: e.target.value })}
                          placeholder="e.g., Premium, Basic, VIP"
                          required
                          className="bg-slate-700/50 border-slate-600"
                        />
                        <p className="text-xs text-slate-400">Use simple names - duration will be auto-appended</p>
                      </div>

                      <div className="space-y-2">
                        <Label>Duration</Label>
                        <Select
                          value={baseForm.duration_template}
                          onValueChange={(value) => setBaseForm({ ...baseForm, duration_template: value })}
                          required
                        >
                          <SelectTrigger className="bg-slate-700/50 border-slate-600">
                            <SelectValue placeholder="Select duration" />
                          </SelectTrigger>
                          <SelectContent className="bg-slate-800 border-slate-700">
                            {durationTemplates.map((template) => (
                              <SelectItem key={template.name} value={template.name}>
                                {template.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Base Price (R)</Label>
                          <Input
                            type="number"
                            step="0.01"
                            value={baseForm.price}
                            onChange={(e) => setBaseForm({ ...baseForm, price: e.target.value })}
                            placeholder="599.00"
                            required
                            className="bg-slate-700/50 border-slate-600"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Billing Frequency</Label>
                          <Select
                            value={baseForm.billing_frequency}
                            onValueChange={(value) => setBaseForm({ ...baseForm, billing_frequency: value })}
                          >
                            <SelectTrigger className="bg-slate-700/50 border-slate-600">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-slate-800 border-slate-700">
                              <SelectItem value="monthly">Monthly</SelectItem>
                              <SelectItem value="one-time">One-time</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label>Payment Type</Label>
                        <Select
                          value={baseForm.payment_type}
                          onValueChange={(value) => setBaseForm({ ...baseForm, payment_type: value })}
                        >
                          <SelectTrigger className="bg-slate-700/50 border-slate-600">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-slate-800 border-slate-700">
                            <SelectItem value="paid_upfront">Paid Upfront</SelectItem>
                            <SelectItem value="debit_order">Debit Order</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label>Description</Label>
                        <Input
                          value={baseForm.description}
                          onChange={(e) => setBaseForm({ ...baseForm, description: e.target.value })}
                          placeholder="Brief description"
                          required
                          className="bg-slate-700/50 border-slate-600"
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>Features (one per line)</Label>
                        <textarea
                          value={baseForm.features}
                          onChange={(e) => setBaseForm({ ...baseForm, features: e.target.value })}
                          placeholder="24/7 access\nAll equipment\nGroup classes"
                          rows={4}
                          className="w-full bg-slate-700/50 border-slate-600 rounded-md p-2 text-white border"
                        />
                      </div>

                      <Button type="submit" className="w-full bg-gradient-to-r from-emerald-500 to-teal-600">
                        Create Base Package
                      </Button>
                    </form>
                  </DialogContent>
                </Dialog>
              </div>

              {loading ? (
                <div className="text-center text-slate-400 py-12">Loading packages...</div>
              ) : (
                <div className="space-y-4">
                  {baseMemberships.map((base) => (
                    <Card key={base.id} className="bg-slate-800/50 border-slate-700" data-testid={`base-package-${base.id}`}>
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <CardTitle className="text-white text-xl">{base.name}</CardTitle>
                              <Badge className="bg-blue-500">Base Package</Badge>
                              <Badge>{base.payment_type === 'paid_upfront' ? 'Paid Upfront' : 'Debit Order'}</Badge>
                            </div>
                            <p className="text-slate-400 text-sm mb-3">{base.description}</p>
                            <div className="flex items-center gap-4">
                              <span className="text-emerald-400 font-bold text-2xl">R {base.price.toFixed(2)}</span>
                              <span className="text-slate-400 text-sm">•</span>
                              <span className="text-slate-400">
                                {base.duration_days > 0 
                                  ? `${base.duration_days} day${base.duration_days !== 1 ? 's' : ''}`
                                  : `${base.duration_months} month${base.duration_months !== 1 ? 's' : ''}`}
                              </span>
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => openVariationDialog(base)}
                              className="border-purple-500 text-purple-400 hover:bg-purple-500/10"
                              data-testid={`add-variation-${base.id}`}
                            >
                              <Percent className="w-4 h-4 mr-1" />
                              Add Variation
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => toggleExpanded(base.id)}
                              className="border-slate-600 text-slate-300"
                            >
                              {expandedBase === base.id ? 'Hide' : 'Show'} Variations
                            </Button>
                          </div>
                        </div>
                      </CardHeader>
                      
                      {expandedBase === base.id && (
                        <CardContent>
                          <div className="border-t border-slate-700 pt-4">
                            <h4 className="text-slate-300 font-semibold mb-3">Variations:</h4>
                            {baseVariations[base.id]?.length > 0 ? (
                              <div className="space-y-2">
                                {baseVariations[base.id].map((variation) => (
                                  <div key={variation.id} className="p-3 rounded-lg bg-slate-700/30 flex items-center justify-between">
                                    <div className="flex-1">
                                      <p className="text-white font-medium">{variation.name}</p>
                                      <p className="text-slate-400 text-sm">{variation.description}</p>
                                    </div>
                                    <div className="text-right">
                                      <p className="text-emerald-400 font-bold">R {variation.price.toFixed(2)}</p>
                                      <Badge variant="secondary" className="mt-1">
                                        {variation.discount_percentage}% off
                                      </Badge>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <p className="text-slate-400 text-sm">No variations yet. Click "Add Variation" to create discounted options.</p>
                            )}
                          </div>
                        </CardContent>
                      )}
                    </Card>
                  ))}
                  {baseMemberships.length === 0 && (
                    <div className="text-center text-slate-400 py-12">
                      <Package className="w-16 h-16 mx-auto mb-4 text-slate-600" />
                      <p>No base packages yet</p>
                      <p className="text-sm mt-2">Create your first base membership to get started</p>
                    </div>
                  )}
                </div>
              )}
            </TabsContent>

            {/* Duration Templates Tab */}
            <TabsContent value="templates" className="mt-6">
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white">Available Duration Templates</CardTitle>
                  <CardDescription className="text-slate-400">Predefined durations for consistent package creation</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 md:grid-cols-4 gap-3">
                    {durationTemplates.map((template) => (
                      <div key={template.name} className="p-3 rounded-lg bg-slate-700/30 border border-slate-600 text-center">
                        <p className="text-white font-semibold">{template.name}</p>
                        <p className="text-slate-400 text-xs mt-1">
                          {template.days > 0 ? `${template.days} days` : `${template.months} months`}
                        </p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-slate-800/50 border-slate-700 mt-6">
                <CardHeader>
                  <CardTitle className="text-white">Variation Types</CardTitle>
                  <CardDescription className="text-slate-400">Predefined discount categories</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {variationTypes.map((type) => (
                      <div key={type.value} className="p-3 rounded-lg bg-slate-700/30 border border-slate-600">
                        <p className="text-white font-semibold">{type.label}</p>
                        <p className="text-slate-400 text-xs mt-1">
                          Typical: {type.typical_discount}% discount
                        </p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Variation Dialog */}
          <Dialog open={variationDialogOpen} onOpenChange={setVariationDialogOpen}>
            <DialogContent className="bg-slate-800 border-slate-700 text-white">
              <DialogHeader>
                <DialogTitle>Create Package Variation</DialogTitle>
                <DialogDescription className="text-slate-400">
                  {selectedBase && `Add a discounted variation of "${selectedBase.name}"`}
                </DialogDescription>
              </DialogHeader>
              {selectedBase && (
                <form onSubmit={handleVariationSubmit} className="space-y-4">
                  <div className="p-3 rounded-lg bg-slate-700/50">
                    <p className="text-slate-400 text-sm">Base Package</p>
                    <p className="text-white font-semibold">{selectedBase.name}</p>
                    <p className="text-emerald-400 text-lg font-bold">R {selectedBase.price.toFixed(2)}</p>
                  </div>

                  <div className="space-y-2">
                    <Label>Variation Type</Label>
                    <Select
                      value={variationForm.variation_type}
                      onValueChange={(value) => {
                        const type = variationTypes.find(t => t.value === value);
                        setVariationForm({ 
                          ...variationForm, 
                          variation_type: value,
                          discount_percentage: type ? type.typical_discount.toString() : ''
                        });
                      }}
                    >
                      <SelectTrigger className="bg-slate-700/50 border-slate-600">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        {variationTypes.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label} (Typical: {type.typical_discount}%)
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Discount Percentage</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={variationForm.discount_percentage}
                      onChange={(e) => setVariationForm({ ...variationForm, discount_percentage: e.target.value })}
                      placeholder="15"
                      required
                      className="bg-slate-700/50 border-slate-600"
                    />
                  </div>

                  {variationForm.discount_percentage && (
                    <div className="p-3 rounded-lg bg-emerald-900/20 border border-emerald-500">
                      <p className="text-emerald-200 text-sm">New Price:</p>
                      <p className="text-emerald-400 text-2xl font-bold">
                        R {(selectedBase.price * (1 - parseFloat(variationForm.discount_percentage || 0) / 100)).toFixed(2)}
                      </p>
                      <p className="text-emerald-300 text-xs mt-1">
                        Savings: R {(selectedBase.price * (parseFloat(variationForm.discount_percentage || 0) / 100)).toFixed(2)}
                      </p>
                    </div>
                  )}

                  <div className="space-y-2">
                    <Label>Description (Optional)</Label>
                    <Input
                      value={variationForm.description}
                      onChange={(e) => setVariationForm({ ...variationForm, description: e.target.value })}
                      placeholder="Custom description"
                      className="bg-slate-700/50 border-slate-600"
                    />
                  </div>

                  <Button type="submit" className="w-full bg-gradient-to-r from-purple-500 to-pink-600">
                    <Percent className="w-4 h-4 mr-2" />
                    Create Variation
                  </Button>
                </form>
              )}
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </div>
  );
}
