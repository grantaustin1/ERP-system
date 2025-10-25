import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import SalesAutomationPanel from '@/components/SalesAutomationPanel';
import MemberSearchAutocomplete from '@/components/MemberSearchAutocomplete';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Users, 
  Plus, 
  Search,
  Phone,
  Mail,
  Building2,
  Star,
  Edit,
  Trash2,
  Eye,
  Filter
} from 'lucide-react';
import { toast } from 'sonner';

export default function LeadsContacts() {
  const [leads, setLeads] = useState([]);
  const [filteredLeads, setFilteredLeads] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sourceFilter, setSourceFilter] = useState('all');
  
  // Configuration data
  const [leadSources, setLeadSources] = useState([]);
  const [leadStatuses, setLeadStatuses] = useState([]);
  const [lossReasons, setLossReasons] = useState([]);
  
  // Create Lead Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [newLead, setNewLead] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    company: '',
    source: 'other',
    source_id: null,
    status_id: null,
    referred_by_member_id: null,
    notes: ''
  });
    notes: ''
  });
  
  // Detail Modal
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [selectedLead, setSelectedLead] = useState(null);
  const [leadDetails, setLeadDetails] = useState(null);

  useEffect(() => {
    fetchLeads();
    fetchConfigurations();
  }, []);

  useEffect(() => {
    filterLeads();
  }, [leads, searchQuery, statusFilter, sourceFilter]);

  const fetchConfigurations = async () => {
    try {
      const [sourcesRes, statusesRes, reasonsRes] = await Promise.all([
        axios.get(`${API}/sales/config/lead-sources`),
        axios.get(`${API}/sales/config/lead-statuses`),
        axios.get(`${API}/sales/config/loss-reasons`)
      ]);
      
      setLeadSources(sourcesRes.data.sources || []);
      setLeadStatuses(statusesRes.data.statuses || []);
      setLossReasons(reasonsRes.data.reasons || []);
    } catch (error) {
      console.error('Error fetching configurations:', error);
    }
  };

  const fetchLeads = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/sales/leads`);
      setLeads(response.data.leads);
    } catch (error) {
      toast.error('Failed to fetch leads');
    } finally {
      setLoading(false);
    }
  };

  const filterLeads = () => {
    let filtered = [...leads];
    
    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(lead => 
        `${lead.first_name} ${lead.last_name}`.toLowerCase().includes(searchQuery.toLowerCase()) ||
        lead.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        lead.phone?.includes(searchQuery) ||
        lead.company?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(lead => lead.status === statusFilter);
    }
    
    // Source filter
    if (sourceFilter !== 'all') {
      filtered = filtered.filter(lead => lead.source === sourceFilter);
    }
    
    setFilteredLeads(filtered);
  };

  const createLead = async () => {
    if (!newLead.first_name || !newLead.last_name) {
      toast.error('First name and last name are required');
      return;
    }
    
    if (!newLead.source_id) {
      toast.error('Please select a lead source');
      return;
    }
    
    if (!newLead.status_id) {
      toast.error('Please select a lead status');
      return;
    }
    
    try {
      const payload = {
        first_name: newLead.first_name,
        last_name: newLead.last_name,
        email: newLead.email || null,
        phone: newLead.phone || null,
        company: newLead.company || null,
        source: newLead.source, // Keep for backward compatibility
        source_id: newLead.source_id,
        status_id: newLead.status_id,
        referred_by_member_id: newLead.referred_by_member_id || null,
        notes: newLead.notes || null
      };
      
      const response = await axios.post(`${API}/sales/leads`, payload);
      toast.success('Lead created successfully');
      setCreateModalOpen(false);
      setNewLead({
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        company: '',
        source: 'other',
        source_id: null,
        status_id: null,
        referred_by_member_id: null,
        notes: ''
      });
      fetchLeads();
    } catch (error) {
      toast.error('Failed to create lead');
    }
  };

  const viewLeadDetails = async (lead) => {
    setSelectedLead(lead);
    setDetailModalOpen(true);
    
    try {
      const response = await axios.get(`${API}/sales/leads/${lead.id}`);
      setLeadDetails(response.data);
    } catch (error) {
      toast.error('Failed to fetch lead details');
    }
  };

  const updateLeadStatus = async (leadId, newStatus) => {
    try {
      await axios.put(`${API}/sales/leads/${leadId}?status=${newStatus}`);
      toast.success('Lead status updated');
      fetchLeads();
      if (selectedLead?.id === leadId) {
        viewLeadDetails({ id: leadId });
      }
    } catch (error) {
      toast.error('Failed to update lead');
    }
  };

  const deleteLead = async (leadId) => {
    if (!confirm('Are you sure you want to delete this lead?')) return;
    
    try {
      await axios.delete(`${API}/sales/leads/${leadId}`);
      toast.success('Lead deleted');
      fetchLeads();
      setDetailModalOpen(false);
    } catch (error) {
      toast.error('Failed to delete lead');
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      new: 'bg-blue-500',
      contacted: 'bg-cyan-500',
      qualified: 'bg-green-500',
      unqualified: 'bg-gray-500',
      converted: 'bg-purple-500'
    };
    return colors[status] || 'bg-gray-500';
  };

  const getSourceIcon = (source) => {
    switch(source) {
      case 'referral': return '🤝';
      case 'website': return '🌐';
      case 'walk_in': return '🚶';
      case 'social_media': return '📱';
      default: return '📋';
    }
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
                <Users className="w-8 h-8 text-blue-400" />
                Leads & Contacts
              </h1>
              <p className="text-slate-400 mt-2">
                Manage your prospects and contacts
              </p>
            </div>
            
            <Dialog open={createModalOpen} onOpenChange={setCreateModalOpen}>
              <DialogTrigger asChild>
                <Button className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="w-4 h-4 mr-2" />
                  Add New Lead
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Create New Lead</DialogTitle>
                  <DialogDescription className="text-slate-400">
                    Add a new prospect to your sales pipeline
                  </DialogDescription>
                </DialogHeader>
                
                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div>
                    <label className="text-sm text-slate-400 mb-1 block">First Name *</label>
                    <Input
                      value={newLead.first_name}
                      onChange={(e) => setNewLead({...newLead, first_name: e.target.value})}
                      className="bg-slate-700 border-slate-600 text-white"
                      placeholder="John"
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm text-slate-400 mb-1 block">Last Name *</label>
                    <Input
                      value={newLead.last_name}
                      onChange={(e) => setNewLead({...newLead, last_name: e.target.value})}
                      className="bg-slate-700 border-slate-600 text-white"
                      placeholder="Doe"
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm text-slate-400 mb-1 block">Email</label>
                    <Input
                      type="email"
                      value={newLead.email}
                      onChange={(e) => setNewLead({...newLead, email: e.target.value})}
                      className="bg-slate-700 border-slate-600 text-white"
                      placeholder="john@example.com"
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm text-slate-400 mb-1 block">Phone</label>
                    <Input
                      value={newLead.phone}
                      onChange={(e) => setNewLead({...newLead, phone: e.target.value})}
                      className="bg-slate-700 border-slate-600 text-white"
                      placeholder="+27 123 456 789"
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm text-slate-400 mb-1 block">Company</label>
                    <Input
                      value={newLead.company}
                      onChange={(e) => setNewLead({...newLead, company: e.target.value})}
                      className="bg-slate-700 border-slate-600 text-white"
                      placeholder="ABC Corp"
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm text-slate-400 mb-1 block">Lead Source *</label>
                    <Select 
                      value={newLead.source_id || ''} 
                      onValueChange={(value) => setNewLead({...newLead, source_id: value})}
                    >
                      <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                        <SelectValue placeholder="Select source..." />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        {leadSources.filter(s => s.is_active).map(source => (
                          <SelectItem key={source.id} value={source.id} className="text-white">
                            {source.icon && <span className="mr-2">{source.icon}</span>}
                            {source.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <label className="text-sm text-slate-400 mb-1 block">Lead Status *</label>
                    <Select 
                      value={newLead.status_id || ''} 
                      onValueChange={(value) => setNewLead({...newLead, status_id: value})}
                    >
                      <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                        <SelectValue placeholder="Select status..." />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        {leadStatuses.filter(s => s.is_active).map(status => (
                          <SelectItem key={status.id} value={status.id} className="text-white">
                            <div className="flex items-center gap-2">
                              <div 
                                className="w-3 h-3 rounded-full" 
                                style={{backgroundColor: status.color}}
                              />
                              {status.name}
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {/* Conditional Referral Field - Only show if source is "Referral" */}
                  {(() => {
                    const selectedSource = leadSources.find(s => s.id === newLead.source_id);
                    return selectedSource && selectedSource.name === "Referral" ? (
                      <div className="col-span-2">
                        <MemberSearchAutocomplete
                          value={newLead.referred_by_member_id}
                          onChange={(memberId) => setNewLead({...newLead, referred_by_member_id: memberId})}
                          label="Referring Member"
                          placeholder="Search for the member who referred this lead..."
                        />
                      </div>
                    ) : null;
                  })()}
                  
                  <div className="col-span-2">
                    <label className="text-sm text-slate-400 mb-1 block">Notes</label>
                    <textarea
                      value={newLead.notes}
                      onChange={(e) => setNewLead({...newLead, notes: e.target.value})}
                      className="w-full bg-slate-700 border-slate-600 text-white rounded-md p-2 min-h-20"
                      placeholder="Additional notes about this lead..."
                    />
                  </div>
                </div>
                
                <div className="flex justify-end gap-3 mt-6">
                  <Button
                    variant="outline"
                    onClick={() => setCreateModalOpen(false)}
                    className="border-slate-600 text-slate-300"
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={createLead}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    Create Lead
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {/* Filters and Search */}
          <Card className="bg-slate-800 border-slate-700 mb-6">
            <CardContent className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="md:col-span-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      placeholder="Search leads..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 bg-slate-700 border-slate-600 text-white"
                    />
                  </div>
                </div>
                
                <div>
                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                      <SelectValue placeholder="Filter by Status" />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-800 border-slate-700">
                      <SelectItem value="all" className="text-white">All Status</SelectItem>
                      <SelectItem value="new" className="text-white">New</SelectItem>
                      <SelectItem value="contacted" className="text-white">Contacted</SelectItem>
                      <SelectItem value="qualified" className="text-white">Qualified</SelectItem>
                      <SelectItem value="unqualified" className="text-white">Unqualified</SelectItem>
                      <SelectItem value="converted" className="text-white">Converted</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Select value={sourceFilter} onValueChange={setSourceFilter}>
                    <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                      <SelectValue placeholder="Filter by Source" />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-800 border-slate-700">
                      <SelectItem value="all" className="text-white">All Sources</SelectItem>
                      <SelectItem value="referral" className="text-white">Referral</SelectItem>
                      <SelectItem value="website" className="text-white">Website</SelectItem>
                      <SelectItem value="walk_in" className="text-white">Walk-in</SelectItem>
                      <SelectItem value="social_media" className="text-white">Social Media</SelectItem>
                      <SelectItem value="other" className="text-white">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="flex items-center gap-2 mt-4">
                <span className="text-slate-400 text-sm">
                  Showing {filteredLeads.length} of {leads.length} leads
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Sales Automation Panel */}
          <div className="mb-6">
            <SalesAutomationPanel />
          </div>

          {/* Leads List */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">All Leads</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left py-3 px-4 text-slate-400 font-medium">Name</th>
                      <th className="text-left py-3 px-4 text-slate-400 font-medium">Contact</th>
                      <th className="text-left py-3 px-4 text-slate-400 font-medium">Company</th>
                      <th className="text-left py-3 px-4 text-slate-400 font-medium">Source</th>
                      <th className="text-left py-3 px-4 text-slate-400 font-medium">Status</th>
                      <th className="text-left py-3 px-4 text-slate-400 font-medium">Score</th>
                      <th className="text-right py-3 px-4 text-slate-400 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredLeads.map((lead) => (
                      <tr key={lead.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                        <td className="py-3 px-4">
                          <div className="text-white font-medium">
                            {lead.first_name} {lead.last_name}
                          </div>
                          <div className="text-slate-400 text-xs">
                            Created {new Date(lead.created_at).toLocaleDateString()}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex flex-col gap-1">
                            {lead.email && (
                              <div className="flex items-center gap-2 text-slate-300 text-xs">
                                <Mail className="w-3 h-3" />
                                {lead.email}
                              </div>
                            )}
                            {lead.phone && (
                              <div className="flex items-center gap-2 text-slate-300 text-xs">
                                <Phone className="w-3 h-3" />
                                {lead.phone}
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2 text-slate-300">
                            {lead.company && (
                              <>
                                <Building2 className="w-4 h-4" />
                                {lead.company}
                              </>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2 text-slate-300">
                            <span>{getSourceIcon(lead.source)}</span>
                            <span className="capitalize">{lead.source.replace('_', ' ')}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <Badge className={`${getStatusColor(lead.status)} text-white`}>
                            {lead.status}
                          </Badge>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <Star className="w-4 h-4 text-yellow-400" />
                            <span className="text-white font-medium">{lead.lead_score}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => viewLeadDetails(lead)}
                              className="text-blue-400 hover:text-blue-300 hover:bg-slate-700"
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                
                {filteredLeads.length === 0 && (
                  <div className="text-center py-12 text-slate-400">
                    <Users className="w-16 h-16 mx-auto mb-4 opacity-50" />
                    <p>No leads found</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Lead Detail Modal */}
          <Dialog open={detailModalOpen} onOpenChange={setDetailModalOpen}>
            <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-4xl max-h-[90vh] overflow-y-auto">
              {leadDetails && (
                <>
                  <DialogHeader>
                    <div className="flex items-center justify-between">
                      <DialogTitle className="text-2xl">
                        {leadDetails.lead.first_name} {leadDetails.lead.last_name}
                      </DialogTitle>
                      <div className="flex items-center gap-2">
                        <Badge className={`${getStatusColor(leadDetails.lead.status)} text-white`}>
                          {leadDetails.lead.status}
                        </Badge>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteLead(leadDetails.lead.id)}
                          className="text-red-400 hover:text-red-300"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                    <DialogDescription className="text-slate-400">
                      Lead Score: {leadDetails.lead.lead_score}/100
                    </DialogDescription>
                  </DialogHeader>
                  
                  <div className="mt-6 space-y-6">
                    {/* Contact Information */}
                    <div>
                      <h3 className="text-white font-semibold mb-3">Contact Information</h3>
                      <div className="grid grid-cols-2 gap-4 bg-slate-700/30 p-4 rounded-lg">
                        {leadDetails.lead.email && (
                          <div>
                            <div className="text-slate-400 text-sm">Email</div>
                            <div className="text-white">{leadDetails.lead.email}</div>
                          </div>
                        )}
                        {leadDetails.lead.phone && (
                          <div>
                            <div className="text-slate-400 text-sm">Phone</div>
                            <div className="text-white">{leadDetails.lead.phone}</div>
                          </div>
                        )}
                        {leadDetails.lead.company && (
                          <div>
                            <div className="text-slate-400 text-sm">Company</div>
                            <div className="text-white">{leadDetails.lead.company}</div>
                          </div>
                        )}
                        <div>
                          <div className="text-slate-400 text-sm">Source</div>
                          <div className="text-white capitalize">{leadDetails.lead.source.replace('_', ' ')}</div>
                        </div>
                      </div>
                    </div>

                    {/* Change Status */}
                    <div>
                      <h3 className="text-white font-semibold mb-3">Update Status</h3>
                      <div className="flex gap-2">
                        {['new', 'contacted', 'qualified', 'unqualified', 'converted'].map((status) => (
                          <Button
                            key={status}
                            size="sm"
                            variant={leadDetails.lead.status === status ? "default" : "outline"}
                            onClick={() => updateLeadStatus(leadDetails.lead.id, status)}
                            className={leadDetails.lead.status === status 
                              ? `${getStatusColor(status)} text-white`
                              : "border-slate-600 text-slate-300"
                            }
                          >
                            {status}
                          </Button>
                        ))}
                      </div>
                    </div>

                    {/* Opportunities */}
                    {leadDetails.opportunities.length > 0 && (
                      <div>
                        <h3 className="text-white font-semibold mb-3">Opportunities ({leadDetails.opportunities.length})</h3>
                        <div className="space-y-2">
                          {leadDetails.opportunities.map((opp) => (
                            <div key={opp.id} className="bg-slate-700/30 p-3 rounded-lg">
                              <div className="flex items-center justify-between">
                                <div className="text-white font-medium">{opp.title}</div>
                                <div className="text-green-400 font-bold">R {opp.value.toLocaleString()}</div>
                              </div>
                              <div className="text-slate-400 text-sm mt-1">
                                Stage: {opp.stage.replace('_', ' ')} • {opp.probability}% probability
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Tasks */}
                    {leadDetails.tasks.length > 0 && (
                      <div>
                        <h3 className="text-white font-semibold mb-3">Tasks ({leadDetails.tasks.length})</h3>
                        <div className="space-y-2">
                          {leadDetails.tasks.map((task) => (
                            <div key={task.id} className="bg-slate-700/30 p-3 rounded-lg flex items-center justify-between">
                              <div>
                                <div className="text-white font-medium">{task.title}</div>
                                <div className="text-slate-400 text-sm">
                                  {task.task_type} • Due: {new Date(task.due_date).toLocaleDateString()}
                                </div>
                              </div>
                              <Badge className={task.status === 'completed' ? 'bg-green-500' : 'bg-orange-500'}>
                                {task.status}
                              </Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Notes */}
                    {leadDetails.lead.notes && (
                      <div>
                        <h3 className="text-white font-semibold mb-3">Notes</h3>
                        <div className="bg-slate-700/30 p-4 rounded-lg text-slate-300">
                          {leadDetails.lead.notes}
                        </div>
                      </div>
                    )}
                  </div>
                </>
              )}
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </div>
  );
}
