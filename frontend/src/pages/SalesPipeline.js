import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Target, 
  Plus, 
  DollarSign,
  User,
  Building2,
  Calendar,
  Percent,
  TrendingUp
} from 'lucide-react';
import { toast } from 'sonner';

export default function SalesPipeline() {
  const [pipeline, setPipeline] = useState(null);
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(false);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [newOpp, setNewOpp] = useState({
    title: '',
    contact_id: '',
    value: '',
    stage: 'new_lead',
    probability: '10',
    expected_close_date: '',
    notes: ''
  });

  useEffect(() => {
    fetchPipeline();
    fetchLeads();
  }, []);

  const fetchPipeline = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/sales/pipeline`);
      setPipeline(response.data);
    } catch (error) {
      toast.error('Failed to fetch pipeline');
    } finally {
      setLoading(false);
    }
  };

  const fetchLeads = async () => {
    try {
      const response = await axios.get(`${API}/sales/leads`);
      setLeads(response.data.leads);
    } catch (error) {
      console.error('Failed to fetch leads');
    }
  };

  const createOpportunity = async () => {
    if (!newOpp.title || !newOpp.contact_id || !newOpp.value) {
      toast.error('Title, contact, and value are required');
      return;
    }
    
    try {
      await axios.post(`${API}/sales/opportunities`, {
        ...newOpp,
        value: parseFloat(newOpp.value),
        probability: parseInt(newOpp.probability)
      });
      toast.success('Opportunity created');
      setCreateModalOpen(false);
      setNewOpp({
        title: '',
        contact_id: '',
        value: '',
        stage: 'new_lead',
        probability: '10',
        expected_close_date: '',
        notes: ''
      });
      fetchPipeline();
    } catch (error) {
      toast.error('Failed to create opportunity');
    }
  };

  const moveOpportunity = async (oppId, newStage) => {
    try {
      await axios.put(`${API}/sales/opportunities/${oppId}?stage=${newStage}`);
      toast.success('Opportunity moved');
      fetchPipeline();
    } catch (error) {
      toast.error('Failed to move opportunity');
    }
  };

  const getStageColor = (stage) => {
    const colors = {
      new_lead: 'border-blue-500',
      contacted: 'border-cyan-500',
      qualified: 'border-green-500',
      proposal: 'border-yellow-500',
      negotiation: 'border-orange-500',
      closed_won: 'border-emerald-500',
      closed_lost: 'border-red-500'
    };
    return colors[stage] || 'border-gray-500';
  };

  const stageNames = {
    new_lead: 'New Lead',
    contacted: 'Contacted',
    qualified: 'Qualified',
    proposal: 'Proposal',
    negotiation: 'Negotiation',
    closed_won: 'Closed Won',
    closed_lost: 'Closed Lost'
  };

  return (
    <div className="flex h-screen bg-slate-900">
      <Sidebar />
      
      <div className="flex-1 p-8 overflow-auto">
        <div className="max-w-[1800px] mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                <Target className="w-8 h-8 text-green-400" />
                Sales Pipeline
              </h1>
              <p className="text-slate-400 mt-2">
                Manage opportunities through sales stages
              </p>
            </div>
            
            <Dialog open={createModalOpen} onOpenChange={setCreateModalOpen}>
              <DialogTrigger asChild>
                <Button className="bg-green-600 hover:bg-green-700">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Opportunity
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Create New Opportunity</DialogTitle>
                  <DialogDescription className="text-slate-400">
                    Add a new sales opportunity to the pipeline
                  </DialogDescription>
                </DialogHeader>
                
                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div className="col-span-2">
                    <label className="text-sm text-slate-400 mb-1 block">Opportunity Title *</label>
                    <Input
                      value={newOpp.title}
                      onChange={(e) => setNewOpp({...newOpp, title: e.target.value})}
                      className="bg-slate-700 border-slate-600 text-white"
                      placeholder="Premium Membership Package"
                    />
                  </div>
                  
                  <div className="col-span-2">
                    <label className="text-sm text-slate-400 mb-1 block">Contact/Lead *</label>
                    <Select value={newOpp.contact_id} onValueChange={(value) => setNewOpp({...newOpp, contact_id: value})}>
                      <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                        <SelectValue placeholder="Select a contact" />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        {leads.map((lead) => (
                          <SelectItem key={lead.id} value={lead.id} className="text-white">
                            {lead.first_name} {lead.last_name} {lead.company && `- ${lead.company}`}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <label className="text-sm text-slate-400 mb-1 block">Value (ZAR) *</label>
                    <Input
                      type="number"
                      value={newOpp.value}
                      onChange={(e) => setNewOpp({...newOpp, value: e.target.value})}
                      className="bg-slate-700 border-slate-600 text-white"
                      placeholder="5000"
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm text-slate-400 mb-1 block">Probability (%)</label>
                    <Input
                      type="number"
                      value={newOpp.probability}
                      onChange={(e) => setNewOpp({...newOpp, probability: e.target.value})}
                      className="bg-slate-700 border-slate-600 text-white"
                      placeholder="10"
                      min="0"
                      max="100"
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm text-slate-400 mb-1 block">Stage</label>
                    <Select value={newOpp.stage} onValueChange={(value) => setNewOpp({...newOpp, stage: value})}>
                      <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        {Object.entries(stageNames).map(([value, label]) => (
                          <SelectItem key={value} value={value} className="text-white">{label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <label className="text-sm text-slate-400 mb-1 block">Expected Close Date</label>
                    <Input
                      type="date"
                      value={newOpp.expected_close_date}
                      onChange={(e) => setNewOpp({...newOpp, expected_close_date: e.target.value})}
                      className="bg-slate-700 border-slate-600 text-white"
                    />
                  </div>
                  
                  <div className="col-span-2">
                    <label className="text-sm text-slate-400 mb-1 block">Notes</label>
                    <textarea
                      value={newOpp.notes}
                      onChange={(e) => setNewOpp({...newOpp, notes: e.target.value})}
                      className="w-full bg-slate-700 border-slate-600 text-white rounded-md p-2 min-h-20"
                      placeholder="Additional notes..."
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
                    onClick={createOpportunity}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    Create Opportunity
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {/* Pipeline Summary */}
          {pipeline && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <Card className="bg-slate-800 border-slate-700">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-slate-400 text-sm">Total Opportunities</div>
                      <div className="text-3xl font-bold text-white mt-1">
                        {pipeline.summary.total_opportunities}
                      </div>
                    </div>
                    <Target className="w-12 h-12 text-green-400 opacity-50" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-slate-400 text-sm">Total Pipeline Value</div>
                      <div className="text-3xl font-bold text-green-400 mt-1">
                        R {pipeline.summary.total_pipeline_value.toLocaleString()}
                      </div>
                    </div>
                    <DollarSign className="w-12 h-12 text-green-400 opacity-50" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-slate-400 text-sm">Closed Won</div>
                      <div className="text-3xl font-bold text-emerald-400 mt-1">
                        {pipeline.pipeline.closed_won.count}
                      </div>
                    </div>
                    <TrendingUp className="w-12 h-12 text-emerald-400 opacity-50" />
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Kanban Board */}
          {pipeline && (
            <div className="overflow-x-auto pb-6">
              <div className="flex gap-4 min-w-max">
                {Object.entries(pipeline.pipeline).map(([stage, data]) => (
                  <div key={stage} className="w-80 flex-shrink-0">
                    <Card className={`bg-slate-800 border-l-4 ${getStageColor(stage)} border-slate-700`}>
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-white text-sm">
                            {stageNames[stage]}
                          </CardTitle>
                          <Badge className="bg-slate-700 text-white">
                            {data.count}
                          </Badge>
                        </div>
                        <div className="text-green-400 font-bold text-sm">
                          R {data.total_value.toLocaleString()}
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-3 max-h-[600px] overflow-y-auto">
                        {data.opportunities.map((opp) => (
                          <Card key={opp.id} className="bg-slate-700 border-slate-600 hover:bg-slate-600 transition-colors cursor-move">
                            <CardContent className="p-4">
                              <div className="text-white font-medium mb-2">{opp.title}</div>
                              
                              <div className="flex items-center gap-2 text-slate-300 text-sm mb-2">
                                <User className="w-3 h-3" />
                                {opp.contact_name}
                              </div>
                              
                              {opp.contact_company && (
                                <div className="flex items-center gap-2 text-slate-400 text-xs mb-2">
                                  <Building2 className="w-3 h-3" />
                                  {opp.contact_company}
                                </div>
                              )}
                              
                              <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-600">
                                <div className="flex items-center gap-2">
                                  <DollarSign className="w-4 h-4 text-green-400" />
                                  <span className="text-green-400 font-bold">
                                    R {opp.value.toLocaleString()}
                                  </span>
                                </div>
                                <div className="flex items-center gap-1 text-slate-400 text-xs">
                                  <Percent className="w-3 h-3" />
                                  {opp.probability}%
                                </div>
                              </div>
                              
                              {opp.expected_close_date && (
                                <div className="flex items-center gap-2 text-slate-400 text-xs mt-2">
                                  <Calendar className="w-3 h-3" />
                                  {new Date(opp.expected_close_date).toLocaleDateString()}
                                </div>
                              )}
                              
                              {/* Quick Stage Change */}
                              <div className="mt-3 pt-3 border-t border-slate-600">
                                <Select 
                                  value={opp.stage} 
                                  onValueChange={(value) => moveOpportunity(opp.id, value)}
                                >
                                  <SelectTrigger className="h-7 text-xs bg-slate-600 border-slate-500 text-white">
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent className="bg-slate-800 border-slate-700">
                                    {Object.entries(stageNames).map(([value, label]) => (
                                      <SelectItem key={value} value={value} className="text-white text-xs">
                                        {label}
                                      </SelectItem>
                                    ))}
                                  </SelectContent>
                                </Select>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                        
                        {data.count === 0 && (
                          <div className="text-center py-8 text-slate-500 text-sm">
                            No opportunities
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
