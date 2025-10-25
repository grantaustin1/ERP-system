import { useState } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { Send, Users, Mail, MessageSquare, CheckSquare } from 'lucide-react';

export default function AdminBroadcast() {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    subject: '',
    message: '',
    target_audience: 'all',
    channels: ['email', 'in_app']
  });

  const handleChannelToggle = (channel) => {
    const currentChannels = formData.channels;
    if (currentChannels.includes(channel)) {
      setFormData({
        ...formData,
        channels: currentChannels.filter(c => c !== channel)
      });
    } else {
      setFormData({
        ...formData,
        channels: [...currentChannels, channel]
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.subject || !formData.message) {
      toast.error('Please fill in subject and message');
      return;
    }
    
    if (formData.channels.length === 0) {
      toast.error('Please select at least one channel');
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.post(`${API}/notifications/broadcast`, formData);
      toast.success(response.data.message);
      
      // Reset form
      setFormData({
        subject: '',
        message: '',
        target_audience: 'all',
        channels: ['email', 'in_app']
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send broadcast');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 overflow-auto">
        <div className="p-8 max-w-4xl">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
              <Send className="w-8 h-8 text-blue-600" />
              Broadcast Message
            </h1>
            <p className="text-gray-600 mt-1">Send announcements to your members</p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Create Broadcast</CardTitle>
              <CardDescription>
                Send a message to all members or specific groups. Messages will be sent via selected channels.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Subject */}
                <div>
                  <Label htmlFor="subject">Subject *</Label>
                  <Input
                    id="subject"
                    value={formData.subject}
                    onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                    placeholder="e.g., New Class Schedule Available"
                    required
                  />
                </div>

                {/* Message */}
                <div>
                  <Label htmlFor="message">Message *</Label>
                  <Textarea
                    id="message"
                    value={formData.message}
                    onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                    placeholder="Enter your message here..."
                    rows={6}
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {formData.message.length} characters
                  </p>
                </div>

                {/* Target Audience */}
                <div>
                  <Label htmlFor="audience">Target Audience</Label>
                  <Select 
                    value={formData.target_audience} 
                    onValueChange={(value) => setFormData({ ...formData, target_audience: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Members</SelectItem>
                      <SelectItem value="active">Active Members Only</SelectItem>
                      <SelectItem value="inactive">Inactive Members</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Channels */}
                <div>
                  <Label>Delivery Channels *</Label>
                  <p className="text-xs text-gray-500 mb-3">Select where to send this message</p>
                  <div className="grid grid-cols-2 gap-3">
                    <div 
                      className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                        formData.channels.includes('email') 
                          ? 'border-blue-600 bg-blue-50' 
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => handleChannelToggle('email')}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <Mail className="w-5 h-5 text-blue-600" />
                        {formData.channels.includes('email') && (
                          <CheckSquare className="w-5 h-5 text-blue-600" />
                        )}
                      </div>
                      <div className="font-semibold">Email</div>
                      <div className="text-xs text-gray-600">Send via email</div>
                      <Badge className="mt-2 bg-yellow-100 text-yellow-800 text-xs">Mocked</Badge>
                    </div>

                    <div 
                      className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                        formData.channels.includes('sms') 
                          ? 'border-blue-600 bg-blue-50' 
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => handleChannelToggle('sms')}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <MessageSquare className="w-5 h-5 text-green-600" />
                        {formData.channels.includes('sms') && (
                          <CheckSquare className="w-5 h-5 text-blue-600" />
                        )}
                      </div>
                      <div className="font-semibold">SMS</div>
                      <div className="text-xs text-gray-600">Send via SMS</div>
                      <Badge className="mt-2 bg-yellow-100 text-yellow-800 text-xs">Mocked</Badge>
                    </div>

                    <div 
                      className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                        formData.channels.includes('whatsapp') 
                          ? 'border-blue-600 bg-blue-50' 
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => handleChannelToggle('whatsapp')}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <MessageSquare className="w-5 h-5 text-green-500" />
                        {formData.channels.includes('whatsapp') && (
                          <CheckSquare className="w-5 h-5 text-blue-600" />
                        )}
                      </div>
                      <div className="font-semibold">WhatsApp</div>
                      <div className="text-xs text-gray-600">Send via WhatsApp</div>
                      <Badge className="mt-2 bg-yellow-100 text-yellow-800 text-xs">Mocked</Badge>
                    </div>

                    <div 
                      className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                        formData.channels.includes('in_app') 
                          ? 'border-blue-600 bg-blue-50' 
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => handleChannelToggle('in_app')}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <Users className="w-5 h-5 text-purple-600" />
                        {formData.channels.includes('in_app') && (
                          <CheckSquare className="w-5 h-5 text-blue-600" />
                        )}
                      </div>
                      <div className="font-semibold">In-App</div>
                      <div className="text-xs text-gray-600">Portal notification</div>
                      <Badge className="mt-2 bg-green-100 text-green-800 text-xs">Live</Badge>
                    </div>
                  </div>
                </div>

                {/* Info Box */}
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="flex gap-3">
                    <div className="text-yellow-600 mt-0.5">ℹ️</div>
                    <div>
                      <div className="font-semibold text-yellow-800 mb-1">Mock Mode Active</div>
                      <div className="text-sm text-yellow-700">
                        Email, SMS, and WhatsApp notifications are currently mocked (logged but not sent). 
                        In-app notifications will be delivered to member portals. 
                        You can integrate real services later by providing API credentials.
                      </div>
                    </div>
                  </div>
                </div>

                {/* Submit Button */}
                <div className="flex gap-3 pt-4">
                  <Button 
                    type="submit" 
                    disabled={loading}
                    className="flex-1"
                  >
                    <Send className="w-4 h-4 mr-2" />
                    {loading ? 'Sending...' : 'Send Broadcast'}
                  </Button>
                  <Button 
                    type="button" 
                    variant="outline"
                    onClick={() => setFormData({
                      subject: '',
                      message: '',
                      target_audience: 'all',
                      channels: ['email', 'in_app']
                    })}
                  >
                    Clear
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Usage Tips */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="text-lg">Broadcasting Tips</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="text-blue-600 mt-0.5">•</span>
                  <span>Keep messages concise and action-oriented</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-600 mt-0.5">•</span>
                  <span>Use clear subject lines that indicate the message purpose</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-600 mt-0.5">•</span>
                  <span>Consider member preferences - they can opt out of certain notification types</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-600 mt-0.5">•</span>
                  <span>Use "Active Members Only" for time-sensitive promotions</span>
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
