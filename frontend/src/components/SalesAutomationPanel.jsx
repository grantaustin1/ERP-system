import { useState } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Zap, 
  Star, 
  UserCheck, 
  Clock,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Sparkles
} from 'lucide-react';
import { toast } from 'sonner';

export default function SalesAutomationPanel() {
  const [selectedLeadId, setSelectedLeadId] = useState('');
  const [assignmentStrategy, setAssignmentStrategy] = useState('round_robin');
  const [daysInactive, setDaysInactive] = useState(7);
  const [loading, setLoading] = useState(false);
  const [scoringResult, setScoringResult] = useState(null);
  const [assignmentResult, setAssignmentResult] = useState(null);
  const [followUpResult, setFollowUpResult] = useState(null);

  /**
   * Auto-Score Lead
   */
  const handleScoreLead = async () => {
    if (!selectedLeadId) {
      toast.error('Please select a lead first');
      return;
    }
    
    setLoading(true);
    setScoringResult(null);
    
    try {
      const response = await axios.post(`${API}/sales/automation/score-lead/${selectedLeadId}`);
      setScoringResult(response.data);
      toast.success(`Lead scored: ${response.data.new_score}/100`);
    } catch (error) {
      toast.error('Failed to score lead');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Auto-Assign Lead
   */
  const handleAutoAssign = async () => {
    if (!selectedLeadId) {
      toast.error('Please select a lead first');
      return;
    }
    
    setLoading(true);
    setAssignmentResult(null);
    
    try {
      const response = await axios.post(
        `${API}/sales/automation/auto-assign-lead/${selectedLeadId}?assignment_strategy=${assignmentStrategy}`
      );
      setAssignmentResult(response.data);
      toast.success(`Lead assigned to ${response.data.assigned_to}`);
    } catch (error) {
      toast.error('Failed to assign lead');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Create Follow-Up Tasks
   */
  const handleCreateFollowUpTasks = async () => {
    setLoading(true);
    setFollowUpResult(null);
    
    try {
      const response = await axios.post(
        `${API}/sales/automation/create-follow-up-tasks?days_inactive=${daysInactive}`
      );
      setFollowUpResult(response.data);
      toast.success(`Created ${response.data.tasks_created} follow-up tasks`);
    } catch (error) {
      toast.error('Failed to create follow-up tasks');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="bg-gradient-to-br from-purple-900/40 to-blue-900/40 border-purple-500/30">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-white">
          <Zap className="w-5 h-5 text-purple-400" />
          Sales Automation
        </CardTitle>
        <CardDescription className="text-slate-300">
          Automate lead scoring, assignment, and follow-ups
        </CardDescription>
      </CardHeader>
      
      <CardContent>
        <Tabs defaultValue="scoring" className="w-full">
          <TabsList className="grid w-full grid-cols-3 bg-slate-800/50">
            <TabsTrigger value="scoring" className="data-[state=active]:bg-purple-600">
              <Star className="w-4 h-4 mr-2" />
              Lead Scoring
            </TabsTrigger>
            <TabsTrigger value="assignment" className="data-[state=active]:bg-blue-600">
              <UserCheck className="w-4 h-4 mr-2" />
              Auto-Assign
            </TabsTrigger>
            <TabsTrigger value="followup" className="data-[state=active]:bg-green-600">
              <Clock className="w-4 h-4 mr-2" />
              Follow-Up
            </TabsTrigger>
          </TabsList>
          
          {/* Lead Scoring Tab */}
          <TabsContent value="scoring" className="space-y-4 mt-4">
            <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-yellow-400" />
                Automatic Lead Scoring
              </h3>
              <p className="text-xs text-slate-400 mb-4">
                Calculate lead quality score based on contact info, source, activity, and engagement (0-100)
              </p>
              
              <div className="space-y-3">
                <div>
                  <Label htmlFor="score-lead-id" className="text-slate-300 text-xs">
                    Select Lead (enter lead ID)
                  </Label>
                  <Input
                    id="score-lead-id"
                    value={selectedLeadId}
                    onChange={(e) => setSelectedLeadId(e.target.value)}
                    placeholder="Enter lead ID"
                    className="bg-slate-700 border-slate-600 text-white text-sm"
                  />
                </div>
                
                <Button 
                  onClick={handleScoreLead}
                  disabled={loading || !selectedLeadId}
                  className="w-full bg-purple-600 hover:bg-purple-700"
                  size="sm"
                >
                  {loading ? 'Scoring...' : 'Calculate Score'}
                </Button>
              </div>
              
              {scoringResult && (
                <div className="mt-4 p-3 bg-purple-900/30 border border-purple-500/30 rounded">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-white">Lead Score</span>
                    <Badge className="bg-purple-600 text-white text-lg px-3">
                      {scoringResult.new_score}/100
                    </Badge>
                  </div>
                  
                  <div className="space-y-1 mt-3">
                    <p className="text-xs font-medium text-slate-300 mb-1">Scoring Factors:</p>
                    {scoringResult.scoring_factors?.map((factor, index) => (
                      <div key={index} className="flex items-center gap-2 text-xs text-slate-400">
                        <CheckCircle2 className="w-3 h-3 text-green-400" />
                        {factor}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </TabsContent>
          
          {/* Auto-Assignment Tab */}
          <TabsContent value="assignment" className="space-y-4 mt-4">
            <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <UserCheck className="w-4 h-4 text-blue-400" />
                Auto-Assign Leads
              </h3>
              <p className="text-xs text-slate-400 mb-4">
                Automatically assign leads to team members based on workload or round-robin
              </p>
              
              <div className="space-y-3">
                <div>
                  <Label htmlFor="assign-lead-id" className="text-slate-300 text-xs">
                    Select Lead (enter lead ID)
                  </Label>
                  <Input
                    id="assign-lead-id"
                    value={selectedLeadId}
                    onChange={(e) => setSelectedLeadId(e.target.value)}
                    placeholder="Enter lead ID"
                    className="bg-slate-700 border-slate-600 text-white text-sm"
                  />
                </div>
                
                <div>
                  <Label htmlFor="strategy" className="text-slate-300 text-xs">
                    Assignment Strategy
                  </Label>
                  <Select value={assignmentStrategy} onValueChange={setAssignmentStrategy}>
                    <SelectTrigger className="bg-slate-700 border-slate-600 text-white text-sm">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-700 border-slate-600">
                      <SelectItem value="round_robin" className="text-white text-sm">
                        Round Robin (Equal distribution)
                      </SelectItem>
                      <SelectItem value="least_loaded" className="text-white text-sm">
                        Least Loaded (Fewest pending tasks)
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <Button 
                  onClick={handleAutoAssign}
                  disabled={loading || !selectedLeadId}
                  className="w-full bg-blue-600 hover:bg-blue-700"
                  size="sm"
                >
                  {loading ? 'Assigning...' : 'Auto-Assign Lead'}
                </Button>
              </div>
              
              {assignmentResult && (
                <div className="mt-4 p-3 bg-blue-900/30 border border-blue-500/30 rounded">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    <span className="text-sm font-medium text-white">Assignment Successful</span>
                  </div>
                  <p className="text-xs text-slate-300">
                    Lead assigned to: <span className="font-semibold">{assignmentResult.assigned_to}</span>
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    Strategy: {assignmentResult.strategy}
                  </p>
                </div>
              )}
            </div>
          </TabsContent>
          
          {/* Follow-Up Tasks Tab */}
          <TabsContent value="followup" className="space-y-4 mt-4">
            <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Clock className="w-4 h-4 text-green-400" />
                Automated Follow-Ups
              </h3>
              <p className="text-xs text-slate-400 mb-4">
                Automatically create follow-up tasks for leads that haven't been contacted recently
              </p>
              
              <div className="space-y-3">
                <div>
                  <Label htmlFor="days-inactive" className="text-slate-300 text-xs">
                    Days Inactive Threshold
                  </Label>
                  <Input
                    id="days-inactive"
                    type="number"
                    value={daysInactive}
                    onChange={(e) => setDaysInactive(parseInt(e.target.value) || 7)}
                    min="1"
                    max="90"
                    className="bg-slate-700 border-slate-600 text-white text-sm"
                  />
                  <p className="text-xs text-slate-400 mt-1">
                    Create tasks for leads not contacted in the last {daysInactive} days
                  </p>
                </div>
                
                <Button 
                  onClick={handleCreateFollowUpTasks}
                  disabled={loading}
                  className="w-full bg-green-600 hover:bg-green-700"
                  size="sm"
                >
                  {loading ? 'Creating Tasks...' : 'Create Follow-Up Tasks'}
                </Button>
              </div>
              
              {followUpResult && (
                <div className="mt-4 p-3 bg-green-900/30 border border-green-500/30 rounded">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    <span className="text-sm font-medium text-white">Tasks Created</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <p className="text-slate-400">Tasks Created:</p>
                      <p className="text-white font-semibold text-lg">{followUpResult.tasks_created}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">Leads Processed:</p>
                      <p className="text-white font-semibold text-lg">{followUpResult.leads_processed}</p>
                    </div>
                  </div>
                  <p className="text-xs text-slate-400 mt-2">
                    Threshold: {followUpResult.days_inactive_threshold} days
                  </p>
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
        
        {/* Info Box */}
        <div className="mt-4 p-3 bg-slate-800/30 border border-slate-700 rounded flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
          <p className="text-xs text-slate-400">
            <span className="font-semibold text-slate-300">Tip:</span> These automation features work with your existing leads. 
            Select a lead from the list above to use scoring and assignment features.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
