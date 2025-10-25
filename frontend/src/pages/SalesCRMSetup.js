import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { 
  Settings, 
  Plus, 
  Edit, 
  Trash2,
  Users,
  GitBranch,
  XCircle,
  Check,
  GripVertical
} from 'lucide-react';
import { toast } from 'sonner';

export default function SalesCRMSetup() {
  const [activeTab, setActiveTab] = useState('sources');
  
  // Lead Sources state
  const [sources, setSources] = useState([]);
  const [showSourceDialog, setShowSourceDialog] = useState(false);
  const [editingSource, setEditingSource] = useState(null);
  const [sourceForm, setSourceForm] = useState({
    name: '',
    description: '',
    icon: '',
    is_active: true,
    display_order: 0
  });
  
  // Lead Statuses state
  const [statuses, setStatuses] = useState([]);
  const [showStatusDialog, setShowStatusDialog] = useState(false);
  const [editingStatus, setEditingStatus] = useState(null);
  const [statusForm, setStatusForm] = useState({
    name: '',
    description: '',
    category: 'prospect',
    color: '#3b82f6',
    workflow_sequence: 0,
    is_active: true,
    display_order: 0
  });
  
  // Loss Reasons state
  const [reasons, setReasons] = useState([]);
  const [showReasonDialog, setShowReasonDialog] = useState(false);
  const [editingReason, setEditingReason] = useState(null);
  const [reasonForm, setReasonForm] = useState({
    name: '',
    description: '',
    is_active: true,
    display_order: 0
  });
  
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    if (activeTab === 'sources') {
      fetchSources();
    } else if (activeTab === 'statuses') {
      fetchStatuses();
    } else if (activeTab === 'reasons') {
      fetchReasons();
    }
  }, [activeTab]);
  
  // ==================== LEAD SOURCES ====================
  
  const fetchSources = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/sales/config/lead-sources`);
      setSources(response.data.sources || []);
    } catch (error) {
      toast.error('Failed to fetch lead sources');
    } finally {
      setLoading(false);
    }
  };
  
  const handleSaveSource = async () => {
    try {
      if (editingSource) {
        await axios.put(`${API}/sales/config/lead-sources/${editingSource.id}`, sourceForm);
        toast.success('Lead source updated');
      } else {
        await axios.post(`${API}/sales/config/lead-sources`, sourceForm);
        toast.success('Lead source created');
      }
      
      setShowSourceDialog(false);
      resetSourceForm();
      fetchSources();
    } catch (error) {
      toast.error('Failed to save lead source');
    }
  };
  
  const handleDeleteSource = async (sourceId) => {
    if (!window.confirm('Are you sure you want to delete this lead source?')) {
      return;
    }
    
    try {
      await axios.delete(`${API}/sales/config/lead-sources/${sourceId}`);
      toast.success('Lead source deleted');
      fetchSources();
    } catch (error) {
      toast.error('Failed to delete lead source');
    }
  };
  
  const openEditSource = (source) => {
    setEditingSource(source);
    setSourceForm({
      name: source.name,
      description: source.description || '',
      icon: source.icon || '',
      is_active: source.is_active,
      display_order: source.display_order
    });
    setShowSourceDialog(true);
  };
  
  const resetSourceForm = () => {
    setEditingSource(null);
    setSourceForm({
      name: '',
      description: '',
      icon: '',
      is_active: true,
      display_order: 0
    });
  };
  
  // ==================== LEAD STATUSES ====================
  
  const fetchStatuses = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/sales/config/lead-statuses`);
      setStatuses(response.data.statuses || []);
    } catch (error) {
      toast.error('Failed to fetch lead statuses');
    } finally {
      setLoading(false);
    }
  };
  
  const handleSaveStatus = async () => {
    try {
      if (editingStatus) {
        await axios.put(`${API}/sales/config/lead-statuses/${editingStatus.id}`, statusForm);
        toast.success('Lead status updated');
      } else {
        await axios.post(`${API}/sales/config/lead-statuses`, statusForm);
        toast.success('Lead status created');
      }
      
      setShowStatusDialog(false);
      resetStatusForm();
      fetchStatuses();
    } catch (error) {
      toast.error('Failed to save lead status');
    }
  };
  
  const handleDeleteStatus = async (statusId) => {
    if (!window.confirm('Are you sure you want to delete this lead status?')) {
      return;
    }
    
    try {
      await axios.delete(`${API}/sales/config/lead-statuses/${statusId}`);
      toast.success('Lead status deleted');
      fetchStatuses();
    } catch (error) {
      toast.error('Failed to delete lead status');
    }
  };
  
  const openEditStatus = (status) => {
    setEditingStatus(status);
    setStatusForm({
      name: status.name,
      description: status.description || '',
      category: status.category,
      color: status.color,
      workflow_sequence: status.workflow_sequence,
      is_active: status.is_active,
      display_order: status.display_order
    });
    setShowStatusDialog(true);
  };
  
  const resetStatusForm = () => {
    setEditingStatus(null);
    setStatusForm({
      name: '',
      description: '',
      category: 'prospect',
      color: '#3b82f6',
      workflow_sequence: 0,
      is_active: true,
      display_order: 0
    });
  };
  
  // ==================== LOSS REASONS ====================
  
  const fetchReasons = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/sales/config/loss-reasons`);
      setReasons(response.data.reasons || []);
    } catch (error) {
      toast.error('Failed to fetch loss reasons');
    } finally {
      setLoading(false);
    }
  };
  
  const handleSaveReason = async () => {
    try {
      if (editingReason) {
        await axios.put(`${API}/sales/config/loss-reasons/${editingReason.id}`, reasonForm);
        toast.success('Loss reason updated');
      } else {
        await axios.post(`${API}/sales/config/loss-reasons`, reasonForm);
        toast.success('Loss reason created');
      }
      
      setShowReasonDialog(false);
      resetReasonForm();
      fetchReasons();
    } catch (error) {
      toast.error('Failed to save loss reason');
    }
  };
  
  const handleDeleteReason = async (reasonId) => {
    if (!window.confirm('Are you sure you want to delete this loss reason?')) {
      return;
    }
    
    try {
      await axios.delete(`${API}/sales/config/loss-reasons/${reasonId}`);
      toast.success('Loss reason deleted');
      fetchReasons();
    } catch (error) {
      toast.error('Failed to delete loss reason');
    }
  };
  
  const openEditReason = (reason) => {
    setEditingReason(reason);
    setReasonForm({
      name: reason.name,
      description: reason.description || '',
      is_active: reason.is_active,
      display_order: reason.display_order
    });
    setShowReasonDialog(true);
  };
  
  const resetReasonForm = () => {
    setEditingReason(null);
    setReasonForm({
      name: '',
      description: '',
      is_active: true,
      display_order: 0
    });
  };
  
  return (
    <div className="flex h-screen bg-slate-900">
      <Sidebar />
      
      <div className="flex-1 p-8 overflow-auto">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <Settings className="w-8 h-8 text-blue-400" />
              Sales CRM Setup
            </h1>
            <p className="text-slate-400 mt-2">
              Configure lead sources, statuses, and loss reasons for your sales pipeline
            </p>
          </div>
          
          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3 bg-slate-800">
              <TabsTrigger value="sources" className="data-[state=active]:bg-blue-600">
                <Source className="w-4 h-4 mr-2" />
                Lead Sources
              </TabsTrigger>
              <TabsTrigger value="statuses" className="data-[state=active]:bg-purple-600">
                <GitBranch className="w-4 h-4 mr-2" />
                Lead Statuses
              </TabsTrigger>
              <TabsTrigger value="reasons" className="data-[state=active]:bg-red-600">
                <XCircle className="w-4 h-4 mr-2" />
                Loss Reasons
              </TabsTrigger>
            </TabsList>
            
            {/* Lead Sources Tab */}
            <TabsContent value="sources" className="mt-6">
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-white">Lead Sources</CardTitle>
                    <CardDescription className="text-slate-400">
                      Manage where your leads come from
                    </CardDescription>
                  </div>
                  <Button 
                    onClick={() => {
                      resetSourceForm();
                      setShowSourceDialog(true);
                    }}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Add Source
                  </Button>
                </CardHeader>
                
                <CardContent>
                  {loading ? (
                    <div className="text-center text-slate-400 py-8">Loading...</div>
                  ) : sources.length === 0 ? (
                    <div className="text-center text-slate-400 py-8">No lead sources yet</div>
                  ) : (
                    <div className="space-y-3">
                      {sources.map((source) => (
                        <div 
                          key={source.id}
                          className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg border border-slate-600"
                        >
                          <div className="flex items-center gap-3">
                            <GripVertical className="w-5 h-5 text-slate-500" />
                            {source.icon && (
                              <span className="text-2xl">{source.icon}</span>
                            )}
                            <div>
                              <h3 className="text-white font-semibold">{source.name}</h3>
                              {source.description && (
                                <p className="text-sm text-slate-400">{source.description}</p>
                              )}
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <Badge variant={source.is_active ? 'default' : 'secondary'}>
                              {source.is_active ? 'Active' : 'Inactive'}
                            </Badge>
                            <Button 
                              size="sm"
                              variant="outline"
                              onClick={() => openEditSource(source)}
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button 
                              size="sm"
                              variant="outline"
                              onClick={() => handleDeleteSource(source.id)}
                              className="text-red-400"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
            
            {/* Lead Statuses Tab */}
            <TabsContent value="statuses" className="mt-6">
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-white">Lead Statuses</CardTitle>
                    <CardDescription className="text-slate-400">
                      Configure your sales workflow statuses
                    </CardDescription>
                  </div>
                  <Button 
                    onClick={() => {
                      resetStatusForm();
                      setShowStatusDialog(true);
                    }}
                    className="bg-purple-600 hover:bg-purple-700"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Add Status
                  </Button>
                </CardHeader>
                
                <CardContent>
                  {loading ? (
                    <div className="text-center text-slate-400 py-8">Loading...</div>
                  ) : statuses.length === 0 ? (
                    <div className="text-center text-slate-400 py-8">No lead statuses yet</div>
                  ) : (
                    <div className="space-y-3">
                      {statuses.map((status) => (
                        <div 
                          key={status.id}
                          className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg border border-slate-600"
                        >
                          <div className="flex items-center gap-3">
                            <GripVertical className="w-5 h-5 text-slate-500" />
                            <div
                              className="w-4 h-4 rounded-full"
                              style={{ backgroundColor: status.color }}
                            />
                            <div>
                              <h3 className="text-white font-semibold">{status.name}</h3>
                              <div className="flex items-center gap-2 mt-1">
                                {status.description && (
                                  <p className="text-sm text-slate-400">{status.description}</p>
                                )}
                                <Badge className="text-xs" variant="outline">
                                  {status.category}
                                </Badge>
                                <Badge className="text-xs" variant="outline">
                                  Seq: {status.workflow_sequence}
                                </Badge>
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <Badge variant={status.is_active ? 'default' : 'secondary'}>
                              {status.is_active ? 'Active' : 'Inactive'}
                            </Badge>
                            <Button 
                              size="sm"
                              variant="outline"
                              onClick={() => openEditStatus(status)}
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button 
                              size="sm"
                              variant="outline"
                              onClick={() => handleDeleteStatus(status.id)}
                              className="text-red-400"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
            
            {/* Loss Reasons Tab */}
            <TabsContent value="reasons" className="mt-6">
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-white">Loss Reasons</CardTitle>
                    <CardDescription className="text-slate-400">
                      Track why leads are lost
                    </CardDescription>
                  </div>
                  <Button 
                    onClick={() => {
                      resetReasonForm();
                      setShowReasonDialog(true);
                    }}
                    className="bg-red-600 hover:bg-red-700"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Add Reason
                  </Button>
                </CardHeader>
                
                <CardContent>
                  {loading ? (
                    <div className="text-center text-slate-400 py-8">Loading...</div>
                  ) : reasons.length === 0 ? (
                    <div className="text-center text-slate-400 py-8">No loss reasons yet</div>
                  ) : (
                    <div className="space-y-3">
                      {reasons.map((reason) => (
                        <div 
                          key={reason.id}
                          className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg border border-slate-600"
                        >
                          <div className="flex items-center gap-3">
                            <GripVertical className="w-5 h-5 text-slate-500" />
                            <div>
                              <h3 className="text-white font-semibold">{reason.name}</h3>
                              {reason.description && (
                                <p className="text-sm text-slate-400">{reason.description}</p>
                              )}
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <Badge variant={reason.is_active ? 'default' : 'secondary'}>
                              {reason.is_active ? 'Active' : 'Inactive'}
                            </Badge>
                            <Button 
                              size="sm"
                              variant="outline"
                              onClick={() => openEditReason(reason)}
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button 
                              size="sm"
                              variant="outline"
                              onClick={() => handleDeleteReason(reason.id)}
                              className="text-red-400"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
      
      {/* Lead Source Dialog */}
      <Dialog open={showSourceDialog} onOpenChange={setShowSourceDialog}>
        <DialogContent className="bg-slate-800 text-white">
          <DialogHeader>
            <DialogTitle>{editingSource ? 'Edit' : 'Create'} Lead Source</DialogTitle>
            <DialogDescription>Configure where your leads come from</DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="source-name">Name *</Label>
              <Input
                id="source-name"
                value={sourceForm.name}
                onChange={(e) => setSourceForm({...sourceForm, name: e.target.value})}
                className="bg-slate-700 border-slate-600 mt-1"
              />
            </div>
            
            <div>
              <Label htmlFor="source-desc">Description</Label>
              <Textarea
                id="source-desc"
                value={sourceForm.description}
                onChange={(e) => setSourceForm({...sourceForm, description: e.target.value})}
                className="bg-slate-700 border-slate-600 mt-1"
                rows={2}
              />
            </div>
            
            <div>
              <Label htmlFor="source-icon">Icon (emoji)</Label>
              <Input
                id="source-icon"
                value={sourceForm.icon}
                onChange={(e) => setSourceForm({...sourceForm, icon: e.target.value})}
                className="bg-slate-700 border-slate-600 mt-1"
                placeholder="📞"
              />
            </div>
            
            <div>
              <Label htmlFor="source-order">Display Order</Label>
              <Input
                id="source-order"
                type="number"
                value={sourceForm.display_order}
                onChange={(e) => setSourceForm({...sourceForm, display_order: parseInt(e.target.value) || 0})}
                className="bg-slate-700 border-slate-600 mt-1"
              />
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch
                id="source-active"
                checked={sourceForm.is_active}
                onCheckedChange={(checked) => setSourceForm({...sourceForm, is_active: checked})}
              />
              <Label htmlFor="source-active">Active</Label>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSourceDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveSource} className="bg-blue-600 hover:bg-blue-700">
              <Check className="w-4 h-4 mr-2" />
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Lead Status Dialog */}
      <Dialog open={showStatusDialog} onOpenChange={setShowStatusDialog}>
        <DialogContent className="bg-slate-800 text-white max-w-2xl">
          <DialogHeader>
            <DialogTitle>{editingStatus ? 'Edit' : 'Create'} Lead Status</DialogTitle>
            <DialogDescription>Configure a status in your sales workflow</DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="status-name">Name *</Label>
                <Input
                  id="status-name"
                  value={statusForm.name}
                  onChange={(e) => setStatusForm({...statusForm, name: e.target.value})}
                  className="bg-slate-700 border-slate-600 mt-1"
                />
              </div>
              
              <div>
                <Label htmlFor="status-category">Category *</Label>
                <select
                  id="status-category"
                  value={statusForm.category}
                  onChange={(e) => setStatusForm({...statusForm, category: e.target.value})}
                  className="w-full mt-1 bg-slate-700 border-slate-600 text-white rounded-md p-2"
                >
                  <option value="prospect">Prospect</option>
                  <option value="engaged">Engaged</option>
                  <option value="converted">Converted</option>
                  <option value="lost">Lost</option>
                </select>
              </div>
            </div>
            
            <div>
              <Label htmlFor="status-desc">Description</Label>
              <Textarea
                id="status-desc"
                value={statusForm.description}
                onChange={(e) => setStatusForm({...statusForm, description: e.target.value})}
                className="bg-slate-700 border-slate-600 mt-1"
                rows={2}
              />
            </div>
            
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="status-color">Color</Label>
                <Input
                  id="status-color"
                  type="color"
                  value={statusForm.color}
                  onChange={(e) => setStatusForm({...statusForm, color: e.target.value})}
                  className="bg-slate-700 border-slate-600 mt-1 h-10"
                />
              </div>
              
              <div>
                <Label htmlFor="status-sequence">Workflow Sequence *</Label>
                <Input
                  id="status-sequence"
                  type="number"
                  value={statusForm.workflow_sequence}
                  onChange={(e) => setStatusForm({...statusForm, workflow_sequence: parseInt(e.target.value) || 0})}
                  className="bg-slate-700 border-slate-600 mt-1"
                />
              </div>
              
              <div>
                <Label htmlFor="status-order">Display Order</Label>
                <Input
                  id="status-order"
                  type="number"
                  value={statusForm.display_order}
                  onChange={(e) => setStatusForm({...statusForm, display_order: parseInt(e.target.value) || 0})}
                  className="bg-slate-700 border-slate-600 mt-1"
                />
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch
                id="status-active"
                checked={statusForm.is_active}
                onCheckedChange={(checked) => setStatusForm({...statusForm, is_active: checked})}
              />
              <Label htmlFor="status-active">Active</Label>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowStatusDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveStatus} className="bg-purple-600 hover:bg-purple-700">
              <Check className="w-4 h-4 mr-2" />
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Loss Reason Dialog */}
      <Dialog open={showReasonDialog} onOpenChange={setShowReasonDialog}>
        <DialogContent className="bg-slate-800 text-white">
          <DialogHeader>
            <DialogTitle>{editingReason ? 'Edit' : 'Create'} Loss Reason</DialogTitle>
            <DialogDescription>Track why leads are lost</DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="reason-name">Name *</Label>
              <Input
                id="reason-name"
                value={reasonForm.name}
                onChange={(e) => setReasonForm({...reasonForm, name: e.target.value})}
                className="bg-slate-700 border-slate-600 mt-1"
              />
            </div>
            
            <div>
              <Label htmlFor="reason-desc">Description</Label>
              <Textarea
                id="reason-desc"
                value={reasonForm.description}
                onChange={(e) => setReasonForm({...reasonForm, description: e.target.value})}
                className="bg-slate-700 border-slate-600 mt-1"
                rows={2}
              />
            </div>
            
            <div>
              <Label htmlFor="reason-order">Display Order</Label>
              <Input
                id="reason-order"
                type="number"
                value={reasonForm.display_order}
                onChange={(e) => setReasonForm({...reasonForm, display_order: parseInt(e.target.value) || 0})}
                className="bg-slate-700 border-slate-600 mt-1"
              />
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch
                id="reason-active"
                checked={reasonForm.is_active}
                onCheckedChange={(checked) => setReasonForm({...reasonForm, is_active: checked})}
              />
              <Label htmlFor="reason-active">Active</Label>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowReasonDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveReason} className="bg-red-600 hover:bg-red-700">
              <Check className="w-4 h-4 mr-2" />
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
