import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Workflow, 
  Plus, 
  Edit, 
  Trash2, 
  Play, 
  Power, 
  PowerOff,
  Zap,
  GitBranch,
  CheckCircle,
  XCircle,
  Settings,
  Mail,
  MessageSquare,
  Phone,
  UserCheck,
  CheckSquare,
  TrendingUp
} from 'lucide-react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  applyNodeChanges,
  applyEdgeChanges,
  MarkerType
} from 'reactflow';
import 'reactflow/dist/style.css';
import { toast } from 'sonner';

const TRIGGER_OBJECTS = [
  { value: 'lead', label: 'Lead', icon: UserCheck },
  { value: 'opportunity', label: 'Opportunity', icon: TrendingUp },
  { value: 'task', label: 'Task', icon: CheckSquare }
];

const TRIGGER_EVENTS = [
  { value: 'created', label: 'Created' },
  { value: 'updated', label: 'Updated' },
  { value: 'status_changed', label: 'Status Changed' }
];

const ACTION_TYPES = [
  { value: 'create_task', label: 'Create Task', icon: CheckSquare, color: 'blue' },
  { value: 'update_field', label: 'Update Field', icon: Edit, color: 'green' },
  { value: 'send_email', label: 'Send Email', icon: Mail, color: 'purple' },
  { value: 'send_sms', label: 'Send SMS', icon: Phone, color: 'orange' },
  { value: 'create_opportunity', label: 'Create Opportunity', icon: TrendingUp, color: 'emerald' }
];

export default function WorkflowAutomation() {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showBuilderDialog, setShowBuilderDialog] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  
  // Workflow form state
  const [workflowName, setWorkflowName] = useState('');
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [triggerObject, setTriggerObject] = useState('lead');
  const [triggerEvent, setTriggerEvent] = useState('created');
  const [conditions, setConditions] = useState({});
  const [actions, setActions] = useState([]);
  
  // React Flow state
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  
  useEffect(() => {
    fetchWorkflows();
  }, []);
  
  const fetchWorkflows = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/sales/workflows`);
      setWorkflows(response.data.workflows || []);
    } catch (error) {
      toast.error('Failed to fetch workflows');
    } finally {
      setLoading(false);
    }
  };
  
  const handleCreateWorkflow = async () => {
    if (!workflowName || !triggerObject || !triggerEvent) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    try {
      await axios.post(`${API}/sales/workflows`, {
        name: workflowName,
        trigger_object: triggerObject,
        trigger_event: triggerEvent,
        conditions,
        actions
      });
      
      toast.success('Workflow created successfully');
      setShowCreateDialog(false);
      resetForm();
      fetchWorkflows();
    } catch (error) {
      toast.error('Failed to create workflow');
    }
  };
  
  const handleToggleWorkflow = async (workflowId, currentStatus) => {
    try {
      await axios.put(`${API}/sales/workflows/${workflowId}`, {
        is_active: !currentStatus
      });
      
      toast.success(currentStatus ? 'Workflow deactivated' : 'Workflow activated');
      fetchWorkflows();
    } catch (error) {
      toast.error('Failed to toggle workflow');
    }
  };
  
  const handleDeleteWorkflow = async (workflowId) => {
    if (!window.confirm('Are you sure you want to delete this workflow?')) {
      return;
    }
    
    try {
      await axios.delete(`${API}/sales/workflows/${workflowId}`);
      toast.success('Workflow deleted successfully');
      fetchWorkflows();
    } catch (error) {
      toast.error('Failed to delete workflow');
    }
  };
  
  const resetForm = () => {
    setWorkflowName('');
    setWorkflowDescription('');
    setTriggerObject('lead');
    setTriggerEvent('created');
    setConditions({});
    setActions([]);
  };
  
  const addAction = () => {
    setActions([...actions, { type: 'create_task', params: {} }]);
  };
  
  const removeAction = (index) => {
    setActions(actions.filter((_, i) => i !== index));
  };
  
  const updateAction = (index, field, value) => {
    const newActions = [...actions];
    if (field === 'type') {
      newActions[index] = { type: value, params: {} };
    } else {
      newActions[index].params[field] = value;
    }
    setActions(newActions);
  };
  
  const openVisualBuilder = (workflow) => {
    setSelectedWorkflow(workflow);
    
    // Build nodes from workflow data
    const triggerNode = {
      id: 'trigger',
      type: 'input',
      data: { label: `${workflow.trigger_object} ${workflow.trigger_event}` },
      position: { x: 250, y: 50 }
    };
    
    const conditionNode = workflow.conditions && Object.keys(workflow.conditions).length > 0 ? {
      id: 'condition',
      type: 'default',
      data: { 
        label: `Conditions: ${Object.entries(workflow.conditions).map(([k, v]) => `${k}=${v}`).join(', ')}`
      },
      position: { x: 250, y: 150 }
    } : null;
    
    const actionNodes = (workflow.actions || []).map((action, index) => ({
      id: `action-${index}`,
      type: 'output',
      data: { label: `${action.type}` },
      position: { x: 100 + index * 200, y: conditionNode ? 300 : 200 }
    }));
    
    const flowNodes = [triggerNode];
    if (conditionNode) flowNodes.push(conditionNode);
    flowNodes.push(...actionNodes);
    
    // Build edges
    const flowEdges = [];
    if (conditionNode) {
      flowEdges.push({
        id: 'e-trigger-condition',
        source: 'trigger',
        target: 'condition',
        type: 'smoothstep',
        markerEnd: { type: MarkerType.ArrowClosed }
      });
      
      actionNodes.forEach((node) => {
        flowEdges.push({
          id: `e-condition-${node.id}`,
          source: 'condition',
          target: node.id,
          type: 'smoothstep',
          markerEnd: { type: MarkerType.ArrowClosed }
        });
      });
    } else {
      actionNodes.forEach((node) => {
        flowEdges.push({
          id: `e-trigger-${node.id}`,
          source: 'trigger',
          target: node.id,
          type: 'smoothstep',
          markerEnd: { type: MarkerType.ArrowClosed }
        });
      });
    }
    
    setNodes(flowNodes);
    setEdges(flowEdges);
    setShowBuilderDialog(true);
  };
  
  const onNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );
  
  const onEdgesChange = useCallback(
    (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );
  
  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    []
  );
  
  const getActionIcon = (type) => {
    const action = ACTION_TYPES.find(a => a.value === type);
    return action ? action.icon : Zap;
  };
  
  const getActionColor = (type) => {
    const action = ACTION_TYPES.find(a => a.value === type);
    return action ? action.color : 'gray';
  };
  
  return (
    <div className="flex h-screen bg-slate-900">
      <Sidebar />
      
      <div className="flex-1 p-8 overflow-auto">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                <Workflow className="w-8 h-8 text-purple-400" />
                Workflow Automation
              </h1>
              <p className="text-slate-400 mt-2">
                Automate your sales processes with visual workflows
              </p>
            </div>
            
            <Button 
              onClick={() => setShowCreateDialog(true)}
              className="bg-purple-600 hover:bg-purple-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Workflow
            </Button>
          </div>
          
          {/* Workflows List */}
          {loading ? (
            <div className="text-center text-slate-400 py-12">Loading workflows...</div>
          ) : workflows.length === 0 ? (
            <Card className="bg-slate-800 border-slate-700">
              <CardContent className="p-12 text-center">
                <Workflow className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">No workflows yet</h3>
                <p className="text-slate-400 mb-6">
                  Create your first workflow to automate sales processes
                </p>
                <Button 
                  onClick={() => setShowCreateDialog(true)}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create First Workflow
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {workflows.map((workflow) => (
                <Card key={workflow.id} className="bg-slate-800 border-slate-700">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-white flex items-center gap-2">
                          <GitBranch className="w-5 h-5 text-purple-400" />
                          {workflow.name}
                        </CardTitle>
                        <CardDescription className="text-slate-400 mt-1">
                          Trigger: {workflow.trigger_object} {workflow.trigger_event}
                        </CardDescription>
                      </div>
                      
                      <Badge variant={workflow.is_active ? 'default' : 'secondary'}>
                        {workflow.is_active ? (
                          <><CheckCircle className="w-3 h-3 mr-1" /> Active</>
                        ) : (
                          <><XCircle className="w-3 h-3 mr-1" /> Inactive</>
                        )}
                      </Badge>
                    </div>
                  </CardHeader>
                  
                  <CardContent>
                    {/* Conditions */}
                    {workflow.conditions && Object.keys(workflow.conditions).length > 0 && (
                      <div className="mb-4 p-3 bg-slate-700 rounded-lg">
                        <p className="text-sm text-slate-300 font-medium mb-2">Conditions:</p>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(workflow.conditions).map(([key, value]) => (
                            <Badge key={key} variant="outline" className="text-xs">
                              {key}: {value}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Actions */}
                    <div className="mb-4">
                      <p className="text-sm text-slate-300 font-medium mb-2">Actions ({workflow.actions?.length || 0}):</p>
                      <div className="flex flex-wrap gap-2">
                        {workflow.actions?.map((action, index) => {
                          const Icon = getActionIcon(action.type);
                          const color = getActionColor(action.type);
                          return (
                            <Badge 
                              key={index} 
                              className={`bg-${color}-600 hover:bg-${color}-700 text-white`}
                            >
                              <Icon className="w-3 h-3 mr-1" />
                              {action.type.replace('_', ' ')}
                            </Badge>
                          );
                        })}
                      </div>
                    </div>
                    
                    {/* Action Buttons */}
                    <div className="flex gap-2 pt-4 border-t border-slate-700">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => openVisualBuilder(workflow)}
                        className="flex-1"
                      >
                        <Play className="w-3 h-3 mr-1" />
                        View
                      </Button>
                      
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleToggleWorkflow(workflow.id, workflow.is_active)}
                        className={workflow.is_active ? 'text-orange-400' : 'text-green-400'}
                      >
                        {workflow.is_active ? (
                          <><PowerOff className="w-3 h-3 mr-1" /> Deactivate</>
                        ) : (
                          <><Power className="w-3 h-3 mr-1" /> Activate</>
                        )}
                      </Button>
                      
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDeleteWorkflow(workflow.id)}
                        className="text-red-400"
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
      
      {/* Create Workflow Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto bg-slate-800 text-white">
          <DialogHeader>
            <DialogTitle>Create New Workflow</DialogTitle>
            <DialogDescription>Define the trigger, conditions, and actions for your workflow</DialogDescription>
          </DialogHeader>
          
          <div className="space-y-6 py-4">
            {/* Basic Info */}
            <div className="space-y-4">
              <div>
                <Label htmlFor="name">Workflow Name *</Label>
                <Input
                  id="name"
                  value={workflowName}
                  onChange={(e) => setWorkflowName(e.target.value)}
                  placeholder="e.g., Auto-create task when lead is qualified"
                  className="bg-slate-700 border-slate-600 mt-1"
                />
              </div>
              
              <div>
                <Label htmlFor="description">Description (optional)</Label>
                <Textarea
                  id="description"
                  value={workflowDescription}
                  onChange={(e) => setWorkflowDescription(e.target.value)}
                  placeholder="Describe what this workflow does..."
                  className="bg-slate-700 border-slate-600 mt-1"
                  rows={2}
                />
              </div>
            </div>
            
            {/* Trigger */}
            <div className="space-y-4 p-4 bg-slate-700 rounded-lg">
              <h3 className="font-semibold flex items-center gap-2">
                <Zap className="w-4 h-4 text-yellow-400" />
                Trigger
              </h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="trigger-object">Trigger Object *</Label>
                  <Select value={triggerObject} onValueChange={setTriggerObject}>
                    <SelectTrigger className="bg-slate-600 border-slate-500 mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-700 border-slate-600">
                      {TRIGGER_OBJECTS.map(obj => (
                        <SelectItem key={obj.value} value={obj.value}>
                          {obj.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label htmlFor="trigger-event">Trigger Event *</Label>
                  <Select value={triggerEvent} onValueChange={setTriggerEvent}>
                    <SelectTrigger className="bg-slate-600 border-slate-500 mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-700 border-slate-600">
                      {TRIGGER_EVENTS.map(event => (
                        <SelectItem key={event.value} value={event.value}>
                          {event.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
            
            {/* Actions */}
            <div className="space-y-4 p-4 bg-slate-700 rounded-lg">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold flex items-center gap-2">
                  <Settings className="w-4 h-4 text-blue-400" />
                  Actions
                </h3>
                <Button size="sm" onClick={addAction} variant="outline">
                  <Plus className="w-3 h-3 mr-1" />
                  Add Action
                </Button>
              </div>
              
              {actions.length === 0 ? (
                <p className="text-sm text-slate-400 text-center py-4">
                  No actions yet. Click "Add Action" to get started.
                </p>
              ) : (
                <div className="space-y-3">
                  {actions.map((action, index) => (
                    <div key={index} className="p-3 bg-slate-600 rounded border border-slate-500">
                      <div className="flex items-start gap-3">
                        <div className="flex-1 space-y-3">
                          <Select 
                            value={action.type} 
                            onValueChange={(value) => updateAction(index, 'type', value)}
                          >
                            <SelectTrigger className="bg-slate-700 border-slate-500">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-slate-700 border-slate-600">
                              {ACTION_TYPES.map(type => (
                                <SelectItem key={type.value} value={type.value}>
                                  {type.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          
                          {/* Action-specific fields */}
                          {action.type === 'create_task' && (
                            <>
                              <Input
                                placeholder="Task title"
                                value={action.params.title || ''}
                                onChange={(e) => updateAction(index, 'title', e.target.value)}
                                className="bg-slate-700 border-slate-500"
                              />
                              <Input
                                placeholder="Task description"
                                value={action.params.description || ''}
                                onChange={(e) => updateAction(index, 'description', e.target.value)}
                                className="bg-slate-700 border-slate-500"
                              />
                            </>
                          )}
                          
                          {action.type === 'update_field' && (
                            <>
                              <Input
                                placeholder="Field name"
                                value={action.params.field || ''}
                                onChange={(e) => updateAction(index, 'field', e.target.value)}
                                className="bg-slate-700 border-slate-500"
                              />
                              <Input
                                placeholder="New value"
                                value={action.params.value || ''}
                                onChange={(e) => updateAction(index, 'value', e.target.value)}
                                className="bg-slate-700 border-slate-500"
                              />
                            </>
                          )}
                          
                          {action.type === 'create_opportunity' && (
                            <>
                              <Input
                                placeholder="Opportunity title"
                                value={action.params.title || ''}
                                onChange={(e) => updateAction(index, 'title', e.target.value)}
                                className="bg-slate-700 border-slate-500"
                              />
                              <Input
                                type="number"
                                placeholder="Value (amount)"
                                value={action.params.value || ''}
                                onChange={(e) => updateAction(index, 'value', e.target.value)}
                                className="bg-slate-700 border-slate-500"
                              />
                            </>
                          )}
                        </div>
                        
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => removeAction(index)}
                          className="text-red-400"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateWorkflow} className="bg-purple-600 hover:bg-purple-700">
              Create Workflow
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Visual Builder Dialog */}
      <Dialog open={showBuilderDialog} onOpenChange={setShowBuilderDialog}>
        <DialogContent className="max-w-6xl max-h-[90vh] bg-slate-800 text-white">
          <DialogHeader>
            <DialogTitle>Workflow Visual Builder</DialogTitle>
            <DialogDescription>
              {selectedWorkflow?.name}
            </DialogDescription>
          </DialogHeader>
          
          <div className="h-[500px] bg-slate-900 rounded-lg border border-slate-700">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              fitView
            >
              <Background color="#475569" gap={16} />
              <Controls />
              <MiniMap 
                nodeColor="#6366f1"
                maskColor="rgba(0, 0, 0, 0.8)"
              />
            </ReactFlow>
          </div>
          
          <DialogFooter>
            <Button onClick={() => setShowBuilderDialog(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
