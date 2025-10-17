import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Switch } from '../components/ui/switch';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { useToast } from '../hooks/use-toast';
import { Plus, Play, Edit, Trash2, Power, PowerOff, Activity } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const TRIGGER_CATEGORIES = {
  bookings: {
    label: 'Bookings & Classes',
    triggers: [
      { value: 'booking_confirmed', label: 'Booking Confirmed', description: 'When a member confirms a booking' },
      { value: 'class_reminder', label: 'Class Reminder', description: 'Remind member about their class' },
      { value: 'waiting_list_added', label: 'Added to Waiting List', description: 'When member adds themselves to waiting list' },
      { value: 'waiting_list_to_booking', label: 'Moved from Waiting List', description: 'When member moves from waiting list to booking' },
    ]
  },
  management: {
    label: 'Management & Staff',
    triggers: [
      { value: 'member_joined', label: 'New Member Joined', description: 'When a new member registers' },
      { value: 'staff_notification_new_member', label: 'Staff: New Member Alert', description: 'Notify staff when a member joins' },
    ]
  },
  gamification: {
    label: 'Member Points & Gamification',
    triggers: [
      { value: 'member_attendance', label: 'Member Attendance', description: 'When a member checks in' },
      { value: 'achievement_recorded', label: 'Achievement Recorded', description: 'When a member achieves a milestone' },
      { value: 'attendance_streak_reminder', label: 'Attendance Streak Reminder', description: 'Remind about 6-day streak' },
      { value: 'attendance_streak_extended', label: 'Attendance Streak Extended', description: 'When streak is extended' },
      { value: 'points_milestone', label: 'Points Milestone Reached', description: 'When member reaches point threshold (e.g., 50 points)' },
    ]
  },
  payments: {
    label: 'Payment Management',
    triggers: [
      { value: 'payment_failed', label: 'Payment Failed', description: 'When a debit order or payment fails' },
      { value: 'payment_method_expiring', label: 'Payment Method Expiring', description: 'Before payment method expires' },
      { value: 'payment_received', label: 'Payment Received', description: 'When payment is successful' },
      { value: 'invoice_overdue', label: 'Invoice Overdue', description: 'When an invoice becomes overdue' },
      { value: 'product_purchased_app', label: 'Product Purchased (App)', description: 'When product is purchased in app' },
      { value: 'product_purchased_till', label: 'Product Purchased (Till)', description: 'When product is purchased at till' },
    ]
  },
  retention: {
    label: 'Retention & Engagement',
    triggers: [
      { value: 'member_inactive_10_days', label: 'Inactive 10 Days', description: 'Member has not attended in 10 days' },
      { value: 'member_inactive_14_days', label: 'Inactive 14 Days', description: 'Member has not attended in 14 days' },
      { value: 'new_member_no_attendance_7_days', label: 'New Member: No Attendance 7 Days', description: 'New member has not attended 7 days after joining' },
      { value: 'new_member_no_attendance_8_days', label: 'New Member: No Attendance 8 Days', description: 'New member has not attended 8 days after joining' },
    ]
  },
  sales_marketing: {
    label: 'Sales & Marketing',
    triggers: [
      { value: 'rejoin_prompt_3_months', label: '3 Month Re-join Prompt', description: 'Send re-join prompt after 3 months' },
      { value: 'birthday_promotion', label: 'Birthday Promotion', description: '5 Days for 5 friends birthday offer' },
      { value: 'appointment_attended', label: 'Appointment Attended', description: 'When member attends an appointment' },
      { value: 'email_opened', label: 'Email Opened', description: 'When marketing email is opened' },
      { value: 'referral_prompt', label: 'Referral Prompt', description: 'Send referral prompt 8 days after joining' },
    ]
  },
  member_journey: {
    label: 'The Member Journey',
    triggers: [
      { value: 'membership_expiring', label: 'Membership Expiring', description: 'When membership is about to expire' },
      { value: 'member_birthday', label: 'Member Birthday', description: 'On member\'s birthday' },
      { value: 'achievement_notification', label: 'Achievement Notification', description: 'When new achievement is recorded' },
      { value: 'welcome_new_member', label: 'Welcome New Member', description: 'Send welcome message when member joins' },
      { value: 'cancellation_requested', label: 'Cancellation Requested', description: 'When a member requests cancellation' },
    ]
  }
};

// Flatten all triggers for backward compatibility
const TRIGGER_TYPES = Object.values(TRIGGER_CATEGORIES).flatMap(category => category.triggers);

const ACTION_TYPES = [
  { value: 'send_sms', label: 'Send SMS', icon: '📱' },
  { value: 'send_whatsapp', label: 'Send WhatsApp', icon: '💬' },
  { value: 'send_email', label: 'Send Email', icon: '📧' },
  { value: 'update_member_status', label: 'Update Member Status', icon: '👤' },
  { value: 'create_task', label: 'Create Task', icon: '✅' }
];

const CONDITION_FIELDS = {
  'member_joined': [
    { value: 'membership_type', label: 'Membership Type', type: 'text' },
    { value: 'join_date', label: 'Join Date', type: 'date' }
  ],
  'payment_failed': [
    { value: 'amount', label: 'Invoice Amount', type: 'number' },
    { value: 'failure_reason', label: 'Failure Reason', type: 'text' }
  ],
  'invoice_overdue': [
    { value: 'amount', label: 'Invoice Amount', type: 'number' },
    { value: 'days_overdue', label: 'Days Overdue', type: 'number' }
  ],
  'membership_expiring': [
    { value: 'days_until_expiry', label: 'Days Until Expiry', type: 'number' },
    { value: 'membership_type', label: 'Membership Type', type: 'text' }
  ],
  'member_inactive': [
    { value: 'days_inactive', label: 'Days Inactive', type: 'number' },
    { value: 'membership_type', label: 'Membership Type', type: 'text' }
  ],
  'cancellation_requested': [
    { value: 'cancellation_reason', label: 'Cancellation Reason', type: 'text' },
    { value: 'membership_type', label: 'Membership Type', type: 'text' }
  ]
};

const OPERATORS = [
  { value: '==', label: 'Equals', types: ['text', 'number', 'date'] },
  { value: '>', label: 'Greater Than', types: ['number', 'date'] },
  { value: '>=', label: 'Greater Than or Equal', types: ['number', 'date'] },
  { value: '<', label: 'Less Than', types: ['number', 'date'] },
  { value: '<=', label: 'Less Than or Equal', types: ['number', 'date'] },
  { value: 'contains', label: 'Contains', types: ['text'] }
];

export default function Automations() {
  const [automations, setAutomations] = useState([]);
  const [executions, setExecutions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingAutomation, setEditingAutomation] = useState(null);
  const { toast } = useToast();

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    trigger_type: '',
    conditions: {},
    actions: [],
    enabled: true,
    test_mode: false
  });

  const [currentAction, setCurrentAction] = useState({
    type: '',
    delay_minutes: 0,
    message: '',
    subject: '',
    body: '',
    email: '',
    phone: '',
    status: '',
    task_title: '',
    task_description: '',
    assigned_to: ''
  });

  const [currentCondition, setCurrentCondition] = useState({
    field: '',
    operator: '',
    value: ''
  });

  const [conditionsList, setConditionsList] = useState([]);

  useEffect(() => {
    fetchAutomations();
    fetchExecutions();
  }, []);

  const fetchAutomations = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${BACKEND_URL}/api/automations`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAutomations(response.data);
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to fetch automations'
      });
    }
  };

  const fetchExecutions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${BACKEND_URL}/api/automation-executions?limit=50`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setExecutions(response.data);
    } catch (error) {
      console.error('Failed to fetch executions:', error);
    }
  };

  const handleCreateOrUpdate = async () => {
    if (!formData.name || !formData.trigger_type || formData.actions.length === 0) {
      toast({
        variant: 'destructive',
        title: 'Validation Error',
        description: 'Please fill in name, trigger type, and add at least one action'
      });
      return;
    }

    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      if (editingAutomation) {
        await axios.put(
          `${BACKEND_URL}/api/automations/${editingAutomation.id}`,
          formData,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        toast({ title: 'Success', description: 'Automation updated successfully' });
      } else {
        await axios.post(`${BACKEND_URL}/api/automations`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast({ title: 'Success', description: 'Automation created successfully' });
      }

      fetchAutomations();
      resetForm();
      setDialogOpen(false);
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to save automation'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleToggleAutomation = async (automationId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${BACKEND_URL}/api/automations/${automationId}/toggle`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast({ title: 'Success', description: response.data.message });
      fetchAutomations();
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to toggle automation'
      });
    }
  };

  const handleDeleteAutomation = async (automationId) => {
    if (!window.confirm('Are you sure you want to delete this automation?')) return;

    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${BACKEND_URL}/api/automations/${automationId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast({ title: 'Success', description: 'Automation deleted successfully' });
      fetchAutomations();
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to delete automation'
      });
    }
  };

  const handleEditAutomation = (automation) => {
    setEditingAutomation(automation);
    setFormData({
      name: automation.name,
      description: automation.description,
      trigger_type: automation.trigger_type,
      conditions: automation.conditions || {},
      actions: automation.actions || [],
      enabled: automation.enabled,
      test_mode: automation.test_mode || false
    });
    
    // Convert conditions object to array for UI
    const conditionsArray = Object.entries(automation.conditions || {}).map(([field, value]) => {
      if (typeof value === 'object' && value.operator) {
        return { field, operator: value.operator, value: value.value };
      }
      return { field, operator: '==', value };
    });
    setConditionsList(conditionsArray);
    
    setDialogOpen(true);
  };

  const handleTestAutomation = async (automationId) => {
    try {
      const token = localStorage.getItem('token');
      const testData = {
        member_id: 'test-member-id',
        member_name: 'Test Member',
        email: 'test@example.com',
        phone: '+1234567890'
      };
      
      const response = await axios.post(
        `${BACKEND_URL}/api/automations/test/${automationId}`,
        testData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast({
        title: response.data.success ? 'Test Successful' : 'Test Failed',
        description: response.data.message
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to test automation'
      });
    }
  };

  const addAction = () => {
    if (!currentAction.type) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Please select an action type'
      });
      return;
    }

    const newAction = { ...currentAction };
    setFormData({ ...formData, actions: [...formData.actions, newAction] });
    setCurrentAction({
      type: '',
      delay_minutes: 0,
      message: '',
      subject: '',
      body: '',
      email: '',
      phone: '',
      status: '',
      task_title: '',
      task_description: '',
      assigned_to: ''
    });
  };

  const removeAction = (index) => {
    const newActions = formData.actions.filter((_, i) => i !== index);
    setFormData({ ...formData, actions: newActions });
  };

  const addCondition = () => {
    if (!currentCondition.field || !currentCondition.operator || !currentCondition.value) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Please fill all condition fields'
      });
      return;
    }

    const newCondition = { ...currentCondition };
    const updatedConditions = [...conditionsList, newCondition];
    setConditionsList(updatedConditions);
    
    // Convert conditions array to object for backend
    const conditionsObj = {};
    updatedConditions.forEach(cond => {
      if (cond.operator === '==') {
        // Simple equality
        conditionsObj[cond.field] = cond.value;
      } else {
        // Complex operator
        conditionsObj[cond.field] = {
          operator: cond.operator,
          value: cond.value
        };
      }
    });
    
    setFormData({ ...formData, conditions: conditionsObj });
    setCurrentCondition({ field: '', operator: '', value: '' });
  };

  const removeCondition = (index) => {
    const updatedConditions = conditionsList.filter((_, i) => i !== index);
    setConditionsList(updatedConditions);
    
    // Convert back to object
    const conditionsObj = {};
    updatedConditions.forEach(cond => {
      if (cond.operator === '==') {
        conditionsObj[cond.field] = cond.value;
      } else {
        conditionsObj[cond.field] = {
          operator: cond.operator,
          value: cond.value
        };
      }
    });
    
    setFormData({ ...formData, conditions: conditionsObj });
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      trigger_type: '',
      conditions: {},
      actions: [],
      enabled: true
    });
    setCurrentAction({
      type: '',
      delay_minutes: 0,
      message: '',
      subject: '',
      body: '',
      email: '',
      phone: '',
      status: '',
      task_title: '',
      task_description: '',
      assigned_to: ''
    });
    setCurrentCondition({ field: '', operator: '', value: '' });
    setConditionsList([]);
    setEditingAutomation(null);
  };

  const getTriggerLabel = (triggerType) => {
    return TRIGGER_TYPES.find(t => t.value === triggerType)?.label || triggerType;
  };

  const getActionLabel = (actionType) => {
    return ACTION_TYPES.find(a => a.value === actionType)?.label || actionType;
  };

  const getFieldLabel = (field, triggerType) => {
    const fields = CONDITION_FIELDS[triggerType] || [];
    return fields.find(f => f.value === field)?.label || field;
  };

  const getOperatorLabel = (operator) => {
    return OPERATORS.find(op => op.value === operator)?.label || operator;
  };

  const getAvailableOperators = () => {
    if (!currentCondition.field || !formData.trigger_type) return [];
    
    const fields = CONDITION_FIELDS[formData.trigger_type] || [];
    const field = fields.find(f => f.value === currentCondition.field);
    if (!field) return OPERATORS;
    
    return OPERATORS.filter(op => op.types.includes(field.type));
  };

  const getFieldType = () => {
    if (!currentCondition.field || !formData.trigger_type) return 'text';
    
    const fields = CONDITION_FIELDS[formData.trigger_type] || [];
    const field = fields.find(f => f.value === currentCondition.field);
    return field?.type || 'text';
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Automation & Triggers</h1>
          <p className="text-gray-500 mt-1">Automate workflows with "If this, then do that" rules</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={resetForm}>
              <Plus className="mr-2 h-4 w-4" />
              Create Automation
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {editingAutomation ? 'Edit Automation' : 'Create New Automation'}
              </DialogTitle>
              <DialogDescription>
                Define triggers and actions to automate your gym workflows
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              {/* Basic Info */}
              <div className="space-y-2">
                <Label htmlFor="name">Automation Name</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Send SMS on Payment Failure"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe what this automation does"
                  rows={2}
                />
              </div>

              {/* Trigger Selection */}
              <div className="space-y-2">
                <Label htmlFor="trigger">Trigger (When this happens...)</Label>
                <Select
                  value={formData.trigger_type}
                  onValueChange={(value) => {
                    setFormData({ ...formData, trigger_type: value });
                    setConditionsList([]);
                    setCurrentCondition({ field: '', operator: '', value: '' });
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a trigger event" />
                  </SelectTrigger>
                  <SelectContent>
                    {TRIGGER_TYPES.map((trigger) => (
                      <SelectItem key={trigger.value} value={trigger.value}>
                        <div>
                          <div className="font-medium">{trigger.label}</div>
                          <div className="text-xs text-gray-500">{trigger.description}</div>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Conditions Builder */}
              {formData.trigger_type && (
                <div className="space-y-2">
                  <Label>Conditions (Optional - Only run if...)</Label>
                  <p className="text-xs text-gray-500 mb-2">
                    Add conditions to filter when this automation should run. All conditions must be true (AND logic).
                  </p>
                  
                  {/* Existing Conditions */}
                  {conditionsList.length > 0 && (
                    <div className="space-y-2 mb-4">
                      {conditionsList.map((condition, index) => (
                        <Card key={index}>
                          <CardContent className="p-3 flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <Badge variant="outline">
                                {getFieldLabel(condition.field, formData.trigger_type)}
                              </Badge>
                              <span className="text-sm text-gray-500">{getOperatorLabel(condition.operator)}</span>
                              <Badge variant="secondary">{condition.value}</Badge>
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => removeCondition(index)}
                            >
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}

                  {/* Add New Condition */}
                  <Card>
                    <CardContent className="p-4 space-y-3">
                      <div className="grid grid-cols-3 gap-2">
                        <div className="space-y-2">
                          <Label htmlFor="condition-field">Field</Label>
                          <Select
                            value={currentCondition.field}
                            onValueChange={(value) => setCurrentCondition({ ...currentCondition, field: value, operator: '', value: '' })}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select field" />
                            </SelectTrigger>
                            <SelectContent>
                              {(CONDITION_FIELDS[formData.trigger_type] || []).map((field) => (
                                <SelectItem key={field.value} value={field.value}>
                                  {field.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="condition-operator">Operator</Label>
                          <Select
                            value={currentCondition.operator}
                            onValueChange={(value) => setCurrentCondition({ ...currentCondition, operator: value })}
                            disabled={!currentCondition.field}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select operator" />
                            </SelectTrigger>
                            <SelectContent>
                              {getAvailableOperators().map((op) => (
                                <SelectItem key={op.value} value={op.value}>
                                  {op.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="condition-value">Value</Label>
                          <Input
                            id="condition-value"
                            type={getFieldType()}
                            value={currentCondition.value}
                            onChange={(e) => setCurrentCondition({ ...currentCondition, value: e.target.value })}
                            placeholder="Enter value"
                            disabled={!currentCondition.operator}
                          />
                        </div>
                      </div>

                      <Button onClick={addCondition} variant="outline" className="w-full" size="sm">
                        <Plus className="mr-2 h-4 w-4" />
                        Add Condition
                      </Button>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Actions */}
              <div className="space-y-2">
                <Label>Actions (Do this...)</Label>
                
                {/* Existing Actions */}
                {formData.actions.length > 0 && (
                  <div className="space-y-2 mb-4">
                    {formData.actions.map((action, index) => (
                      <Card key={index}>
                        <CardContent className="p-3 flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <span>{ACTION_TYPES.find(a => a.value === action.type)?.icon}</span>
                            <div>
                              <div className="font-medium">{getActionLabel(action.type)}</div>
                              {action.delay_minutes > 0 && (
                                <div className="text-xs text-gray-500">
                                  Delay: {action.delay_minutes} minutes
                                </div>
                              )}
                              {action.message && (
                                <div className="text-xs text-gray-500 truncate max-w-md">
                                  {action.message}
                                </div>
                              )}
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeAction(index)}
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}

                {/* Add New Action */}
                <Card>
                  <CardContent className="p-4 space-y-3">
                    <Select
                      value={currentAction.type}
                      onValueChange={(value) => setCurrentAction({ ...currentAction, type: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select action type" />
                      </SelectTrigger>
                      <SelectContent>
                        {ACTION_TYPES.map((action) => (
                          <SelectItem key={action.value} value={action.value}>
                            {action.icon} {action.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>

                    {currentAction.type && (
                      <>
                        <div className="space-y-2">
                          <Label htmlFor="delay">Delay (minutes)</Label>
                          <Input
                            id="delay"
                            type="number"
                            min="0"
                            value={currentAction.delay_minutes}
                            onChange={(e) =>
                              setCurrentAction({ ...currentAction, delay_minutes: parseInt(e.target.value) || 0 })
                            }
                            placeholder="0"
                          />
                        </div>

                        {/* SMS/WhatsApp Fields */}
                        {(currentAction.type === 'send_sms' || currentAction.type === 'send_whatsapp') && (
                          <>
                            <div className="space-y-2">
                              <Label htmlFor="phone">Phone (optional, uses member phone if empty)</Label>
                              <Input
                                id="phone"
                                value={currentAction.phone}
                                onChange={(e) => setCurrentAction({ ...currentAction, phone: e.target.value })}
                                placeholder="+1234567890"
                              />
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor="message">Message</Label>
                              <Textarea
                                id="message"
                                value={currentAction.message}
                                onChange={(e) => setCurrentAction({ ...currentAction, message: e.target.value })}
                                placeholder="Use {member_name}, {amount}, etc. for dynamic values"
                                rows={3}
                              />
                              <p className="text-xs text-gray-500">
                                Available variables: {'{member_name}'}, {'{email}'}, {'{phone}'}, {'{amount}'}, {'{invoice_number}'}
                              </p>
                            </div>
                          </>
                        )}

                        {/* Email Fields */}
                        {currentAction.type === 'send_email' && (
                          <>
                            <div className="space-y-2">
                              <Label htmlFor="email">Email (optional, uses member email if empty)</Label>
                              <Input
                                id="email"
                                value={currentAction.email}
                                onChange={(e) => setCurrentAction({ ...currentAction, email: e.target.value })}
                                placeholder="email@example.com"
                              />
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor="subject">Subject</Label>
                              <Input
                                id="subject"
                                value={currentAction.subject}
                                onChange={(e) => setCurrentAction({ ...currentAction, subject: e.target.value })}
                                placeholder="Email subject"
                              />
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor="body">Body</Label>
                              <Textarea
                                id="body"
                                value={currentAction.body}
                                onChange={(e) => setCurrentAction({ ...currentAction, body: e.target.value })}
                                placeholder="Email body with {member_name}, {amount}, etc."
                                rows={4}
                              />
                            </div>
                          </>
                        )}

                        {/* Update Status Fields */}
                        {currentAction.type === 'update_member_status' && (
                          <div className="space-y-2">
                            <Label htmlFor="status">New Status</Label>
                            <Select
                              value={currentAction.status}
                              onValueChange={(value) => setCurrentAction({ ...currentAction, status: value })}
                            >
                              <SelectTrigger>
                                <SelectValue placeholder="Select status" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="active">Active</SelectItem>
                                <SelectItem value="suspended">Suspended</SelectItem>
                                <SelectItem value="inactive">Inactive</SelectItem>
                                <SelectItem value="cancelled">Cancelled</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        )}

                        {/* Task Fields */}
                        {currentAction.type === 'create_task' && (
                          <>
                            <div className="space-y-2">
                              <Label htmlFor="task_title">Task Title</Label>
                              <Input
                                id="task_title"
                                value={currentAction.task_title}
                                onChange={(e) => setCurrentAction({ ...currentAction, task_title: e.target.value })}
                                placeholder="Follow up with member"
                              />
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor="task_description">Task Description</Label>
                              <Textarea
                                id="task_description"
                                value={currentAction.task_description}
                                onChange={(e) => setCurrentAction({ ...currentAction, task_description: e.target.value })}
                                placeholder="Task details with {member_name}, etc."
                                rows={2}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor="assigned_to">Assigned To (email)</Label>
                              <Input
                                id="assigned_to"
                                value={currentAction.assigned_to}
                                onChange={(e) => setCurrentAction({ ...currentAction, assigned_to: e.target.value })}
                                placeholder="staff@example.com"
                              />
                            </div>
                          </>
                        )}

                        <Button onClick={addAction} variant="outline" className="w-full">
                          <Plus className="mr-2 h-4 w-4" />
                          Add Action
                        </Button>
                      </>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Enabled Toggle */}
              <div className="flex items-center space-x-2">
                <Switch
                  id="enabled"
                  checked={formData.enabled}
                  onCheckedChange={(checked) => setFormData({ ...formData, enabled: checked })}
                />
                <Label htmlFor="enabled">Enable automation immediately</Label>
              </div>
            </div>

            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateOrUpdate} disabled={loading}>
                {loading ? 'Saving...' : editingAutomation ? 'Update' : 'Create'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <Tabs defaultValue="automations" className="space-y-4">
        <TabsList>
          <TabsTrigger value="automations">Automation Rules</TabsTrigger>
          <TabsTrigger value="executions">Execution History</TabsTrigger>
        </TabsList>

        <TabsContent value="automations" className="space-y-4">
          {automations.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Automations Yet</h3>
                <p className="text-gray-500 mb-4">
                  Create your first automation to start automating workflows
                </p>
                <Button onClick={() => setDialogOpen(true)}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Automation
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {automations.map((automation) => (
                <Card key={automation.id}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="space-y-1 flex-1">
                        <div className="flex items-center space-x-2">
                          <CardTitle>{automation.name}</CardTitle>
                          <Badge variant={automation.enabled ? 'default' : 'secondary'}>
                            {automation.enabled ? 'Enabled' : 'Disabled'}
                          </Badge>
                        </div>
                        <CardDescription>{automation.description}</CardDescription>
                      </div>
                      <div className="flex space-x-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleTestAutomation(automation.id)}
                          title="Test automation"
                        >
                          <Play className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleToggleAutomation(automation.id)}
                          title={automation.enabled ? 'Disable' : 'Enable'}
                        >
                          {automation.enabled ? (
                            <PowerOff className="h-4 w-4" />
                          ) : (
                            <Power className="h-4 w-4" />
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEditAutomation(automation)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteAutomation(automation.id)}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div>
                        <span className="text-sm font-medium">Trigger:</span>{' '}
                        <Badge variant="outline">{getTriggerLabel(automation.trigger_type)}</Badge>
                      </div>
                      
                      {/* Display Conditions */}
                      {automation.conditions && Object.keys(automation.conditions).length > 0 && (
                        <div>
                          <span className="text-sm font-medium">Conditions:</span>
                          <div className="flex flex-wrap gap-2 mt-1">
                            {Object.entries(automation.conditions).map(([field, value], index) => {
                              const displayValue = typeof value === 'object' 
                                ? `${getOperatorLabel(value.operator)} ${value.value}`
                                : `= ${value}`;
                              return (
                                <Badge key={index} variant="outline" className="bg-blue-50">
                                  {getFieldLabel(field, automation.trigger_type)}: {displayValue}
                                </Badge>
                              );
                            })}
                          </div>
                        </div>
                      )}
                      
                      <div>
                        <span className="text-sm font-medium">Actions ({automation.actions?.length || 0}):</span>
                        <div className="flex flex-wrap gap-2 mt-1">
                          {automation.actions?.map((action, index) => (
                            <Badge key={index} variant="secondary">
                              {ACTION_TYPES.find(a => a.value === action.type)?.icon}{' '}
                              {getActionLabel(action.type)}
                              {action.delay_minutes > 0 && ` (${action.delay_minutes}m delay)`}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div className="text-xs text-gray-500 flex items-center justify-between">
                        <span>Executed {automation.execution_count || 0} times</span>
                        {automation.last_triggered && (
                          <span>Last triggered: {new Date(automation.last_triggered).toLocaleString()}</span>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="executions" className="space-y-4">
          {executions.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Execution History</h3>
                <p className="text-gray-500">
                  Automation executions will appear here once triggered
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {executions.map((execution) => (
                <Card key={execution.id}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">{execution.automation_name}</div>
                        <div className="text-sm text-gray-500">
                          {new Date(execution.created_at).toLocaleString()}
                        </div>
                      </div>
                      <Badge
                        variant={
                          execution.status === 'completed'
                            ? 'default'
                            : execution.status === 'failed'
                            ? 'destructive'
                            : 'secondary'
                        }
                      >
                        {execution.status}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
