import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Send, MessageSquare, Mail, MessageCircle, Bell, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const UnifiedMessagingDialog = ({ open, onOpenChange, selectedMembers = [], onSuccess }) => {
  const [messageType, setMessageType] = useState('sms');
  const [subject, setSubject] = useState('');
  const [messageBody, setMessageBody] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [templates, setTemplates] = useState([]);
  const [isMarketing, setIsMarketing] = useState(false);
  const [saveAsTemplate, setSaveAsTemplate] = useState(false);
  const [templateName, setTemplateName] = useState('');
  const [showOnCheckin, setShowOnCheckin] = useState(false);
  const [smsCredits, setSmsCredits] = useState(null);
  const [sending, setSending] = useState(false);
  const [loadingTemplates, setLoadingTemplates] = useState(false);

  const messageTypeConfig = {
    sms: { icon: MessageSquare, label: 'SMS', color: 'text-green-400', requiresSubject: false },
    email: { icon: Mail, label: 'Email', color: 'text-blue-400', requiresSubject: true },
    whatsapp: { icon: MessageCircle, label: 'WhatsApp', color: 'text-green-500', requiresSubject: false },
    push: { icon: Bell, label: 'Push Notification', color: 'text-purple-400', requiresSubject: true }
  };

  const config = messageTypeConfig[messageType];
  const Icon = config.icon;

  // Calculate SMS character count
  const smsCharCount = messageType === 'sms' ? 1500 - messageBody.length : null;
  const smsMessages = messageType === 'sms' ? Math.ceil(messageBody.length / 153) : null;

  useEffect(() => {
    if (open) {
      fetchSmsCredits();
      fetchTemplates();
    }
  }, [open, messageType]);

  const fetchSmsCredits = async () => {
    try {
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
      const response = await fetch(`${backendUrl}/api/messaging/sms-credits`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSmsCredits(data);
      }
    } catch (error) {
      console.error('Failed to fetch SMS credits:', error);
    }
  };

  const fetchTemplates = async () => {
    try {
      setLoadingTemplates(true);
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
      const response = await fetch(
        `${backendUrl}/api/messaging/templates/dropdown?message_type=${messageType}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      }
    } catch (error) {
      console.error('Failed to fetch templates:', error);
      toast.error('Failed to load templates');
    } finally {
      setLoadingTemplates(false);
    }
  };

  const handleTemplateSelect = (templateId) => {
    setSelectedTemplate(templateId);
    if (templateId === 'none' || !templateId) {
      setSubject('');
      setMessageBody('');
      return;
    }
    const template = templates.find(t => t.value === templateId);
    if (template) {
      setSubject(template.subject || '');
      setMessageBody(template.message || '');
    }
  };

  const handleSend = async () => {
    // Validation
    if (!messageBody.trim()) {
      toast.error('Message body is required');
      return;
    }

    if (config.requiresSubject && !subject.trim()) {
      toast.error('Subject is required for ' + config.label);
      return;
    }

    if (selectedMembers.length === 0) {
      toast.error('No recipients selected');
      return;
    }

    // Check SMS credits
    if (messageType === 'sms' && smsCredits) {
      const requiredCredits = selectedMembers.length * (smsMessages || 1);
      if (requiredCredits > smsCredits.credits_available) {
        toast.error(`Insufficient SMS credits. Need ${requiredCredits}, have ${smsCredits.credits_available}`);
        return;
      }
    }

    setSending(true);

    try {
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
      
      const payload = {
        member_ids: selectedMembers.map(m => typeof m === 'string' ? m : m.id),
        message_type: messageType,
        subject: subject,
        message_body: messageBody,
        is_marketing: isMarketing,
        save_as_template: saveAsTemplate,
        template_name: saveAsTemplate ? templateName : '',
        show_on_checkin: showOnCheckin
      };

      const response = await fetch(`${backendUrl}/api/messaging/send-unified`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        const result = await response.json();
        toast.success(result.message || `Successfully sent ${result.sent_count} messages`);
        
        // Reset form
        setSubject('');
        setMessageBody('');
        setSelectedTemplate('');
        setSaveAsTemplate(false);
        setTemplateName('');
        
        onOpenChange(false);
        if (onSuccess) onSuccess();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to send messages');
      }
    } catch (error) {
      console.error('Failed to send messages:', error);
      toast.error('Failed to send messages');
    } finally {
      setSending(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Icon className={`w-5 h-5 ${config.color}`} />
            Send {config.label}
          </DialogTitle>
          <DialogDescription className="text-slate-400">
            Compose and send {config.label.toLowerCase()} messages to {selectedMembers.length} member{selectedMembers.length !== 1 ? 's' : ''}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Message Type Selector */}
          <div className="flex gap-2">
            {Object.entries(messageTypeConfig).map(([type, typeConfig]) => {
              const TypeIcon = typeConfig.icon;
              return (
                <Button
                  key={type}
                  variant={messageType === type ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setMessageType(type)}
                  className="flex-1"
                >
                  <TypeIcon className="w-4 h-4 mr-1" />
                  {typeConfig.label}
                </Button>
              );
            })}
          </div>

          {/* SMS Credits Display */}
          {messageType === 'sms' && smsCredits && (
            <div className="bg-slate-700 rounded-lg p-3 flex items-center justify-between">
              <div>
                <span className="text-sm text-slate-400">Available Credits:</span>
                <span className="text-lg font-bold text-green-400 ml-2">
                  {smsCredits.credits_available}
                </span>
              </div>
              <div className="text-xs text-slate-400">
                This message: {selectedMembers.length * (smsMessages || 1)} credits
              </div>
            </div>
          )}

          {/* Template Selector */}
          <div>
            <Label>Message Template (Optional)</Label>
            <Select value={selectedTemplate} onValueChange={handleTemplateSelect} disabled={loadingTemplates}>
              <SelectTrigger className="bg-slate-700 border-slate-600">
                <SelectValue placeholder={loadingTemplates ? "Loading templates..." : "Choose a template"} />
              </SelectTrigger>
              <SelectContent className="bg-slate-700 border-slate-600">
                <SelectItem value="none">No template</SelectItem>
                {templates.map(template => (
                  <SelectItem key={template.value} value={template.value}>
                    {template.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Subject (for email and push) */}
          {config.requiresSubject && (
            <div>
              <Label>Subject *</Label>
              <Input
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Enter subject"
                className="bg-slate-700 border-slate-600"
              />
            </div>
          )}

          {/* Message Body */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <Label>Message *</Label>
              {messageType === 'sms' && (
                <span className="text-xs text-slate-400">
                  {smsCharCount} chars / {smsMessages} SMS
                </span>
              )}
            </div>
            <Textarea
              value={messageBody}
              onChange={(e) => setMessageBody(e.target.value)}
              placeholder="Enter your message. Use {first_name}, {last_name}, {email} for personalization"
              rows={6}
              maxLength={messageType === 'sms' ? 1500 : undefined}
              className="bg-slate-700 border-slate-600"
            />
            <p className="text-xs text-slate-500 mt-1">
              Available variables: {'{first_name}'}, {'{last_name}'}, {'{email}'}
            </p>
          </div>

          {/* Options */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Checkbox 
                id="marketing" 
                checked={isMarketing}
                onCheckedChange={setIsMarketing}
              />
              <Label htmlFor="marketing" className="text-sm cursor-pointer">
                This is a marketing message
              </Label>
            </div>

            {messageType === 'push' && (
              <div className="flex items-center space-x-2">
                <Checkbox 
                  id="checkin" 
                  checked={showOnCheckin}
                  onCheckedChange={setShowOnCheckin}
                />
                <Label htmlFor="checkin" className="text-sm cursor-pointer">
                  Show on check-in screen
                </Label>
              </div>
            )}

            <div className="flex items-center space-x-2">
              <Checkbox 
                id="saveTemplate" 
                checked={saveAsTemplate}
                onCheckedChange={setSaveAsTemplate}
              />
              <Label htmlFor="saveTemplate" className="text-sm cursor-pointer">
                Save as new template
              </Label>
            </div>

            {saveAsTemplate && (
              <Input
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
                placeholder="Template name"
                className="bg-slate-700 border-slate-600 ml-6"
              />
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2 pt-4">
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="flex-1"
              disabled={sending}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSend}
              className="flex-1 bg-emerald-600 hover:bg-emerald-700"
              disabled={sending}
            >
              {sending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Sending...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Send {config.label}
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default UnifiedMessagingDialog;
