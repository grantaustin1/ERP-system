import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Switch } from '../components/ui/switch';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Plus, Play, Edit, Trash2, Power, Zap, Mail, MessageCircle, Users, CreditCard, Calendar, TrendingUp } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Predefined automation templates
const AUTOMATION_TEMPLATES = [
  {
    id: 'welcome_new_member',
    category: 'Member Onboarding',
    icon: Users,
    name: 'Welcome New Member',
    description: 'Send a welcome message when a member joins',
    trigger: 'member_joined',
    defaultAction: 'send_whatsapp',
    defaultMessage: 'Welcome to our gym, {member_name}! We\'re excited to have you join us. Your membership ID is {member_id}.',
    parameters: [
      { name: 'delay_minutes', label: 'Delay (minutes)', type: 'number', default: 5 }
    ]
  },
  {
    id: 'payment_failed_alert',
    category: 'Payment Management',
    icon: CreditCard,
    name: 'Payment Failed Alert',
    description: 'Notify member when their payment fails',
    trigger: 'payment_failed',
    defaultAction: 'send_whatsapp',
    defaultMessage: 'Hi {member_name}, your payment of R{amount} has failed. Please update your payment details to avoid service interruption.',
    parameters: [
      { name: 'delay_minutes', label: 'Delay (minutes)', type: 'number', default: 30 }
    ]
  },
  {
    id: 'payment_received_confirmation',
    category: 'Payment Management',
    icon: CreditCard,
    name: 'Payment Received',
    description: 'Confirm successful payment to member',
    trigger: 'payment_received',
    defaultAction: 'send_whatsapp',
    defaultMessage: 'Thank you {member_name}! We\'ve received your payment of R{amount}. Receipt: {invoice_number}',
    parameters: [
      { name: 'delay_minutes', label: 'Delay (minutes)', type: 'number', default: 5 }
    ]
  },
  {
    id: 'membership_expiring_reminder',
    category: 'Member Retention',
    icon: Calendar,
    name: 'Membership Expiring',
    description: 'Remind member their membership is expiring soon',
    trigger: 'membership_expiring',
    defaultAction: 'send_whatsapp',
    defaultMessage: 'Hi {member_name}, your membership expires in {days_until_expiry} days. Renew now to keep enjoying our facilities!',
    parameters: [
      { name: 'days_before', label: 'Days Before Expiry', type: 'number', default: 7 },
      { name: 'delay_minutes', label: 'Delay (minutes)', type: 'number', default: 0 }
    ]
  },
  {
    id: 'inactive_member_reminder',
    category: 'Member Retention',
    icon: TrendingUp,
    name: 'Inactive Member Reminder',
    description: 'Remind members who haven\'t visited recently',
    trigger: 'member_inactive_10_days',
    defaultAction: 'send_whatsapp',
    defaultMessage: 'Hey {member_name}! We miss you at the gym. It\'s been 10 days since your last visit. Come back and crush your goals!',
    parameters: [
      { name: 'inactive_days', label: 'Inactive Days', type: 'select', options: ['10', '14', '21', '30'], default: '10' },
      { name: 'delay_minutes', label: 'Delay (minutes)', type: 'number', default: 0 }
    ]
  },
  {
    id: 'class_booking_confirmation',
    category: 'Classes & Bookings',
    icon: Calendar,
    name: 'Class Booking Confirmed',
    description: 'Confirm class booking to member',
    trigger: 'booking_confirmed',
    defaultAction: 'send_whatsapp',
    defaultMessage: 'Hi {member_name}! Your booking for {class_name} on {booking_date} at {booking_time} is confirmed. See you there!',
    parameters: [
      { name: 'delay_minutes', label: 'Delay (minutes)', type: 'number', default: 2 }
    ]
  },
  {
    id: 'class_reminder',
    category: 'Classes & Bookings',
    icon: Calendar,
    name: 'Class Reminder',
    description: 'Remind member about their upcoming class',
    trigger: 'class_reminder',
    defaultAction: 'send_whatsapp',
    defaultMessage: 'Reminder: You have {class_name} starting in 2 hours at {booking_time}. Don\'t forget your water bottle!',
    parameters: [
      { name: 'hours_before', label: 'Hours Before Class', type: 'number', default: 2 }
    ]
  },
  {
    id: 'invoice_overdue_reminder',
    category: 'Payment Management',
    icon: CreditCard,
    name: 'Invoice Overdue',
    description: 'Notify member about overdue invoice',
    trigger: 'invoice_overdue',
    defaultAction: 'send_whatsapp',
    defaultMessage: 'Hi {member_name}, your invoice {invoice_number} for R{amount} is now overdue. Please make payment to avoid account suspension.',
    parameters: [
      { name: 'delay_minutes', label: 'Delay (minutes)', type: 'number', default: 60 }
    ]
  },
  {
    id: 'birthday_wishes',
    category: 'Member Engagement',
    icon: Users,
    name: 'Birthday Wishes',
    description: 'Send birthday wishes to member',
    trigger: 'member_birthday',
    defaultAction: 'send_whatsapp',
    defaultMessage: '🎉 Happy Birthday {member_name}! Enjoy a special birthday workout on us today. Have an amazing day!',
    parameters: [
      { name: 'time_of_day', label: 'Send Time', type: 'select', options: ['Morning (8am)', 'Afternoon (12pm)', 'Evening (6pm)'], default: 'Morning (8am)' }
    ]
  },
  {
    id: 'referral_prompt',
    category: 'Sales & Marketing',
    icon: TrendingUp,
    name: 'Referral Request',
    description: 'Ask happy members to refer friends',
    trigger: 'member_attendance',
    defaultAction: 'send_whatsapp',
    defaultMessage: 'Hey {member_name}! Loving your progress? Refer a friend and you both get 1 month free! Share your unique code: {referral_code}',
    parameters: [
      { name: 'after_checkins', label: 'After N Check-ins', type: 'number', default: 10 },
      { name: 'delay_minutes', label: 'Delay (minutes)', type: 'number', default: 0 }
    ]
  },
  {
    id: 'cancellation_retention',
    category: 'Member Retention',
    icon: Users,
    name: 'Cancellation Request Follow-up',
    description: 'Follow up with member who requested cancellation',
    trigger: 'cancellation_requested',
    defaultAction: 'send_whatsapp',
    defaultMessage: 'Hi {member_name}, we\'re sorry to see you go. Can we help with anything? Reply to this message and let\'s chat about your concerns.',
    parameters: [
      { name: 'delay_minutes', label: 'Delay (minutes)', type: 'number', default: 60 }
    ]
  },
  {
    id: 'new_member_no_show',
    category: 'Member Retention',
    icon: TrendingUp,
    name: 'New Member - No Visit',
    description: 'Follow up with new members who haven\'t visited',
    trigger: 'new_member_no_attendance_7_days',
    defaultAction: 'send_whatsapp',
    defaultMessage: 'Hi {member_name}! We haven\'t seen you yet. Need help getting started? Book a free orientation session with us!',
    parameters: [
      { name: 'days_after_join', label: 'Days After Joining', type: 'number', default: 7 }
    ]
  }
];

const ACTION_CHANNELS = [
  { value: 'send_whatsapp', label: 'WhatsApp', icon: MessageCircle, color: 'bg-green-500' },
  { value: 'send_sms', label: 'SMS', icon: MessageCircle, color: 'bg-blue-500' },
  { value: 'send_email', label: 'Email', icon: Mail, color: 'bg-purple-500' }
];

function AutomationsGeneric() {
  const [automations, setAutomations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editingAutomation, setEditingAutomation] = useState(null);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [notificationTemplates, setNotificationTemplates] = useState([]);
  const [useTemplate, setUseTemplate] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    template_id: '',
    action_type: 'send_whatsapp',
    message: '',
    test_mode: false,
    parameters: {}
  });

  useEffect(() => {
    fetchAutomations();
    fetchNotificationTemplates();
  }, []);

  useEffect(() => {
    if (selectedTemplate) {
      setFormData({
        ...formData,
        name: selectedTemplate.name,
        description: selectedTemplate.description,
        action_type: selectedTemplate.defaultAction,
        message: selectedTemplate.defaultMessage,
        parameters: selectedTemplate.parameters.reduce((acc, param) => ({
          ...acc,
          [param.name]: param.default
        }), {})
      });
    }
  }, [selectedTemplate]);

  const fetchAutomations = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/automations`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setAutomations(data);
      }
    } catch (error) {
      console.error('Failed to fetch automations:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchNotificationTemplates = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/notification-templates`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setNotificationTemplates(data.templates || []);
      }
    } catch (error) {
      console.error('Failed to fetch notification templates:', error);
    }
  };

  const handleTemplateSelect = (templateId) => {
    const template = AUTOMATION_TEMPLATES.find(t => t.id === templateId);
    setSelectedTemplate(template);
  };

  const handleCreateAutomation = async (e) => {
    e.preventDefault();
    
    if (!selectedTemplate) {
      alert('Please select an automation template');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      
      // Build actions array based on template and form data
      const actions = [{
        type: formData.action_type,
        delay_minutes: parseInt(formData.parameters.delay_minutes || 0),
        message: formData.message
      }];

      const automationData = {
        name: formData.name,
        description: formData.description,
        trigger_type: selectedTemplate.trigger,
        conditions: formData.parameters,
        actions: actions,
        test_mode: formData.test_mode
      };

      const url = editingAutomation 
        ? `${BACKEND_URL}/api/automations/${editingAutomation.id}`
        : `${BACKEND_URL}/api/automations`;
      
      const method = editingAutomation ? 'PATCH' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(automationData)
      });

      if (response.ok) {
        await fetchAutomations();
        setShowDialog(false);
        resetForm();
        alert(editingAutomation ? 'Automation updated!' : 'Automation created!');
      } else {
        const error = await response.json();
        alert(`Failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error saving automation:', error);
      alert('Failed to save automation');
    }
  };

  const handleDeleteAutomation = async (id) => {
    if (!window.confirm('Delete this automation?')) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/automations/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        await fetchAutomations();
        alert('Automation deleted!');
      }
    } catch (error) {
      console.error('Error deleting automation:', error);
      alert('Failed to delete automation');
    }
  };

  const handleToggleAutomation = async (automation) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/automations/${automation.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ enabled: !automation.enabled })
      });

      if (response.ok) {
        await fetchAutomations();
      }
    } catch (error) {
      console.error('Error toggling automation:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      template_id: '',
      action_type: 'send_whatsapp',
      message: '',
      test_mode: false,
      parameters: {}
    });
    setSelectedTemplate(null);
    setEditingAutomation(null);
  };

  const openEditDialog = (automation) => {
    setEditingAutomation(automation);
    // Find matching template
    const template = AUTOMATION_TEMPLATES.find(t => t.trigger === automation.trigger_type);
    setSelectedTemplate(template);
    
    setFormData({
      name: automation.name,
      description: automation.description,
      action_type: automation.actions[0]?.type || 'send_whatsapp',
      message: automation.actions[0]?.message || '',
      test_mode: automation.test_mode,
      parameters: automation.conditions || {}
    });
    setShowDialog(true);
  };

  // Group templates by category
  const groupedTemplates = AUTOMATION_TEMPLATES.reduce((acc, template) => {
    if (!acc[template.category]) {
      acc[template.category] = [];
    }
    acc[template.category].push(template);
    return acc;
  }, {});

  const getActionChannel = (actionType) => {
    return ACTION_CHANNELS.find(ch => ch.value === actionType);
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Automations</h1>
          <p className="text-gray-600 mt-1">Set up automated workflows for your gym</p>
        </div>
        <Dialog open={showDialog} onOpenChange={(open) => { setShowDialog(open); if (!open) resetForm(); }}>
          <Button onClick={() => setShowDialog(true)}>
            <Plus className="mr-2 h-4 w-4" /> Create Automation
          </Button>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingAutomation ? 'Edit Automation' : 'Create New Automation'}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreateAutomation} className="space-y-6">
              {/* Template Selection */}
              <div>
                <Label>Select Automation Template *</Label>
                <Select 
                  value={selectedTemplate?.id || ''} 
                  onValueChange={handleTemplateSelect}
                  disabled={!!editingAutomation}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Choose an automation template..." />
                  </SelectTrigger>
                  <SelectContent>
                    {AUTOMATION_TEMPLATES.map(template => (
                      <SelectItem key={template.id} value={template.id}>
                        <div className="flex flex-col">
                          <span className="font-medium">{template.name}</span>
                          <span className="text-xs text-gray-500">{template.category} - {template.description}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {selectedTemplate && (
                <>
                  {/* Template Preview */}
                  <Card className="bg-blue-50 border-blue-200">
                    <CardHeader>
                      <div className="flex items-center space-x-3">
                        {React.createElement(selectedTemplate.icon, { className: "h-6 w-6 text-blue-600" })}
                        <div>
                          <CardTitle className="text-lg">{selectedTemplate.name}</CardTitle>
                          <CardDescription>{selectedTemplate.description}</CardDescription>
                        </div>
                      </div>
                    </CardHeader>
                  </Card>

                  {/* Name (editable) */}
                  <div>
                    <Label htmlFor="name">Automation Name *</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      required
                    />
                  </div>

                  {/* Channel Selection */}
                  <div>
                    <Label>Communication Channel *</Label>
                    <Select 
                      value={formData.action_type} 
                      onValueChange={(value) => setFormData({ ...formData, action_type: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {ACTION_CHANNELS.map(channel => (
                          <SelectItem key={channel.value} value={channel.value}>
                            <div className="flex items-center space-x-2">
                              {React.createElement(channel.icon, { className: "h-4 w-4" })}
                              <span>{channel.label}</span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Message Template */}
                  <div>
                    <Label htmlFor="message">Message Template *</Label>
                    <Textarea
                      id="message"
                      value={formData.message}
                      onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                      rows={4}
                      required
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Available variables: {'{member_name}'}, {'{member_id}'}, {'{amount}'}, {'{invoice_number}'}, {'{class_name}'}, {'{booking_date}'}
                    </p>
                  </div>

                  {/* Template Parameters */}
                  {selectedTemplate.parameters.map(param => (
                    <div key={param.name}>
                      <Label htmlFor={param.name}>{param.label}</Label>
                      {param.type === 'number' ? (
                        <Input
                          id={param.name}
                          type="number"
                          value={formData.parameters[param.name] || param.default}
                          onChange={(e) => setFormData({
                            ...formData,
                            parameters: { ...formData.parameters, [param.name]: e.target.value }
                          })}
                        />
                      ) : param.type === 'select' ? (
                        <Select
                          value={formData.parameters[param.name] || param.default}
                          onValueChange={(value) => setFormData({
                            ...formData,
                            parameters: { ...formData.parameters, [param.name]: value }
                          })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {param.options.map(option => (
                              <SelectItem key={option} value={option}>{option}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      ) : (
                        <Input
                          id={param.name}
                          value={formData.parameters[param.name] || param.default}
                          onChange={(e) => setFormData({
                            ...formData,
                            parameters: { ...formData.parameters, [param.name]: e.target.value }
                          })}
                        />
                      )}
                    </div>
                  ))}

                  {/* Test Mode Toggle */}
                  <div className="flex items-center justify-between p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex-1">
                      <Label htmlFor="test_mode" className="font-semibold">Test Mode</Label>
                      <p className="text-sm text-gray-600">Enable to test this automation without triggering real actions</p>
                    </div>
                    <Switch
                      id="test_mode"
                      checked={formData.test_mode}
                      onCheckedChange={(checked) => setFormData({ ...formData, test_mode: checked })}
                    />
                  </div>

                  <div className="flex justify-end space-x-2 pt-4">
                    <Button type="button" variant="outline" onClick={() => { setShowDialog(false); resetForm(); }}>
                      Cancel
                    </Button>
                    <Button type="submit">
                      {editingAutomation ? 'Update Automation' : 'Create Automation'}
                    </Button>
                  </div>
                </>
              )}
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Active Automations */}
      <div className="space-y-4">
        {automations.length === 0 ? (
          <Card>
            <CardContent className="text-center py-12">
              <Zap className="h-12 w-12 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-600">No automations created yet. Click "Create Automation" to get started!</p>
            </CardContent>
          </Card>
        ) : (
          automations.map(automation => {
            const template = AUTOMATION_TEMPLATES.find(t => t.trigger === automation.trigger_type);
            const channel = getActionChannel(automation.actions[0]?.type);
            const TemplateIcon = template?.icon || Zap;

            return (
              <Card key={automation.id} className={`border-l-4 ${automation.enabled ? 'border-l-green-500' : 'border-l-gray-300'}`}>
                <CardContent className="py-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4 flex-1">
                      <div className={`p-3 rounded-lg ${automation.enabled ? 'bg-green-100' : 'bg-gray-100'}`}>
                        <TemplateIcon className={`h-6 w-6 ${automation.enabled ? 'text-green-600' : 'text-gray-400'}`} />
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <h3 className="font-semibold text-lg">{automation.name}</h3>
                          {automation.test_mode && (
                            <Badge className="bg-yellow-100 text-yellow-800">🧪 Test Mode</Badge>
                          )}
                          {automation.enabled ? (
                            <Badge className="bg-green-100 text-green-800">Active</Badge>
                          ) : (
                            <Badge variant="secondary">Inactive</Badge>
                          )}
                        </div>
                        
                        <p className="text-sm text-gray-600 mb-3">{automation.description}</p>
                        
                        <div className="flex items-center space-x-4 text-sm">
                          <div className="flex items-center space-x-2">
                            <span className="text-gray-500">Trigger:</span>
                            <Badge variant="outline">{template?.name || automation.trigger_type}</Badge>
                          </div>
                          
                          {channel && (
                            <div className="flex items-center space-x-2">
                              <span className="text-gray-500">Channel:</span>
                              <div className="flex items-center space-x-1">
                                {React.createElement(channel.icon, { className: "h-4 w-4" })}
                                <span>{channel.label}</span>
                              </div>
                            </div>
                          )}
                          
                          <div className="flex items-center space-x-2">
                            <span className="text-gray-500">Executions:</span>
                            <span className="font-medium">{automation.execution_count || 0}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Button
                        size="sm"
                        variant={automation.enabled ? "default" : "outline"}
                        onClick={() => handleToggleAutomation(automation)}
                      >
                        {automation.enabled ? (
                          <><Power className="h-4 w-4 mr-1" /> Enabled</>
                        ) : (
                          <><Power className="h-4 w-4 mr-1" /> Disabled</>
                        )}
                      </Button>
                      
                      <Button size="sm" variant="outline" onClick={() => openEditDialog(automation)}>
                        <Edit className="h-4 w-4" />
                      </Button>
                      
                      <Button size="sm" variant="outline" onClick={() => handleDeleteAutomation(automation.id)}>
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
}

export default AutomationsGeneric;
