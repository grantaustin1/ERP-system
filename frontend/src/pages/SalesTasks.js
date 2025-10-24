import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
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
  CheckSquare, 
  Plus, 
  Calendar,
  Phone,
  Mail,
  Users as UsersIcon,
  AlertCircle,
  Check
} from 'lucide-react';
import { toast } from 'sonner';

export default function SalesTasks() {
  const [tasks, setTasks] = useState([]);
  const [leads, setLeads] = useState([]);
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');
  
  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    task_type: 'call',
    related_to_type: 'lead',
    related_to_id: '',
    due_date: '',
    priority: 'medium'
  });

  useEffect(() => {
    fetchTasks();
    fetchLeads();
    fetchOpportunities();
  }, []);

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/sales/tasks`);
      setTasks(response.data.tasks);
    } catch (error) {
      toast.error('Failed to fetch tasks');
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

  const fetchOpportunities = async () => {
    try {
      const response = await axios.get(`${API}/sales/opportunities`);
      setOpportunities(response.data.opportunities);
    } catch (error) {
      console.error('Failed to fetch opportunities');
    }
  };

  const createTask = async () => {
    if (!newTask.title || !newTask.related_to_id || !newTask.due_date) {
      toast.error('Title, related item, and due date are required');
      return;
    }
    
    try {
      await axios.post(`${API}/sales/tasks`, newTask);
      toast.success('Task created');
      setCreateModalOpen(false);
      setNewTask({
        title: '',
        description: '',
        task_type: 'call',
        related_to_type: 'lead',
        related_to_id: '',
        due_date: '',
        priority: 'medium'
      });
      fetchTasks();
    } catch (error) {
      toast.error('Failed to create task');
    }
  };

  const updateTaskStatus = async (taskId, newStatus) => {
    try {
      await axios.put(`${API}/sales/tasks/${taskId}?status=${newStatus}`);
      toast.success('Task updated');
      fetchTasks();
    } catch (error) {
      toast.error('Failed to update task');
    }
  };

  const deleteTask = async (taskId) => {
    if (!confirm('Are you sure you want to delete this task?')) return;
    
    try {
      await axios.delete(`${API}/sales/tasks/${taskId}`);
      toast.success('Task deleted');
      fetchTasks();
    } catch (error) {
      toast.error('Failed to delete task');
    }
  };

  const getPriorityColor = (priority) => {
    const colors = {
      high: 'bg-red-500',
      medium: 'bg-yellow-500',
      low: 'bg-blue-500'
    };
    return colors[priority] || 'bg-gray-500';
  };

  const getTypeIcon = (type) => {
    const icons = {
      call: <Phone className="w-4 h-4" />,
      email: <Mail className="w-4 h-4" />,
      meeting: <UsersIcon className="w-4 h-4" />,
      follow_up: <AlertCircle className="w-4 h-4" />
    };
    return icons[type] || <CheckSquare className="w-4 h-4" />;
  };

  const filteredTasks = tasks.filter(task => {
    if (statusFilter !== 'all' && task.status !== statusFilter) return false;
    if (priorityFilter !== 'all' && task.priority !== priorityFilter) return false;
    return true;
  });

  const isOverdue = (dueDate, status) => {
    if (status === 'completed') return false;
    return new Date(dueDate) < new Date();
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
                <CheckSquare className="w-8 h-8 text-orange-400" />
                Sales Tasks
              </h1>
              <p className="text-slate-400 mt-2">
                Manage follow-ups and activities
              </p>
            </div>
            
            <Dialog open={createModalOpen} onOpenChange={setCreateModalOpen}>
              <DialogTrigger asChild>
                <Button className="bg-orange-600 hover:bg-orange-700">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Task
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Create New Task</DialogTitle>
                  <DialogDescription className="text-slate-400">
                    Schedule a follow-up activity
                  </DialogDescription>
                </DialogHeader>
                
                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div className="col-span-2">
                    <label className="text-sm text-slate-400 mb-1 block">Task Title *</label>
                    <Input
                      value={newTask.title}
                      onChange={(e) => setNewTask({...newTask, title: e.target.value})}
                      className="bg-slate-700 border-slate-600 text-white"
                      placeholder="Follow up call"
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm text-slate-400 mb-1 block">Task Type</label>
                    <Select value={newTask.task_type} onValueChange={(value) => setNewTask({...newTask, task_type: value})}>
                      <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        <SelectItem value="call" className="text-white">Call</SelectItem>
                        <SelectItem value="email" className="text-white">Email</SelectItem>
                        <SelectItem value="meeting" className="text-white">Meeting</SelectItem>
                        <SelectItem value="follow_up" className="text-white">Follow-up</SelectItem>
                        <SelectItem value="other" className="text-white">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <label className="text-sm text-slate-400 mb-1 block">Priority</label>
                    <Select value={newTask.priority} onValueChange={(value) => setNewTask({...newTask, priority: value})}>
                      <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        <SelectItem value="low" className="text-white">Low</SelectItem>
                        <SelectItem value="medium" className="text-white">Medium</SelectItem>
                        <SelectItem value="high" className="text-white">High</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <label className="text-sm text-slate-400 mb-1 block">Related To</label>
                    <Select value={newTask.related_to_type} onValueChange={(value) => setNewTask({...newTask, related_to_type: value, related_to_id: ''})}>
                      <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        <SelectItem value="lead" className="text-white">Lead</SelectItem>
                        <SelectItem value="opportunity" className="text-white">Opportunity</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <label className="text-sm text-slate-400 mb-1 block">
                      {newTask.related_to_type === 'lead' ? 'Select Lead *' : 'Select Opportunity *'}
                    </label>
                    <Select value={newTask.related_to_id} onValueChange={(value) => setNewTask({...newTask, related_to_id: value})}>
                      <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                        <SelectValue placeholder={`Select ${newTask.related_to_type}`} />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        {newTask.related_to_type === 'lead' ? (
                          leads.map((lead) => (
                            <SelectItem key={lead.id} value={lead.id} className="text-white">
                              {lead.first_name} {lead.last_name}
                            </SelectItem>
                          ))
                        ) : (
                          opportunities.map((opp) => (
                            <SelectItem key={opp.id} value={opp.id} className="text-white">
                              {opp.title}
                            </SelectItem>
                          ))
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="col-span-2">
                    <label className="text-sm text-slate-400 mb-1 block">Due Date *</label>
                    <Input
                      type="datetime-local"
                      value={newTask.due_date}
                      onChange={(e) => setNewTask({...newTask, due_date: e.target.value})}
                      className="bg-slate-700 border-slate-600 text-white"
                    />
                  </div>
                  
                  <div className="col-span-2">
                    <label className="text-sm text-slate-400 mb-1 block">Description</label>
                    <textarea
                      value={newTask.description}
                      onChange={(e) => setNewTask({...newTask, description: e.target.value})}
                      className="w-full bg-slate-700 border-slate-600 text-white rounded-md p-2 min-h-20"
                      placeholder="Task details..."
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
                    onClick={createTask}
                    className="bg-orange-600 hover:bg-orange-700"
                  >
                    Create Task
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {/* Filters */}
          <Card className="bg-slate-800 border-slate-700 mb-6">
            <CardContent className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                      <SelectValue placeholder="Filter by Status" />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-800 border-slate-700">
                      <SelectItem value="all" className="text-white">All Status</SelectItem>
                      <SelectItem value="pending" className="text-white">Pending</SelectItem>
                      <SelectItem value="completed" className="text-white">Completed</SelectItem>
                      <SelectItem value="cancelled" className="text-white">Cancelled</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Select value={priorityFilter} onValueChange={setPriorityFilter}>
                    <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                      <SelectValue placeholder="Filter by Priority" />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-800 border-slate-700">
                      <SelectItem value="all" className="text-white">All Priorities</SelectItem>
                      <SelectItem value="high" className="text-white">High</SelectItem>
                      <SelectItem value="medium" className="text-white">Medium</SelectItem>
                      <SelectItem value="low" className="text-white">Low</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="flex items-center text-slate-400 text-sm">
                  Showing {filteredTasks.length} of {tasks.length} tasks
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Tasks List */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">All Tasks</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {filteredTasks.map((task) => (
                  <div
                    key={task.id}
                    className={`p-4 rounded-lg border-l-4 ${
                      isOverdue(task.due_date, task.status) ? 'border-red-500 bg-red-900/10' : 'border-slate-600'
                    } bg-slate-700/30 hover:bg-slate-700/50 transition-colors`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <div className={`w-8 h-8 rounded-full ${task.status === 'completed' ? 'bg-green-500' : 'bg-slate-600'} flex items-center justify-center`}>
                            {task.status === 'completed' ? (
                              <Check className="w-5 h-5 text-white" />
                            ) : (
                              getTypeIcon(task.task_type)
                            )}
                          </div>
                          <div>
                            <div className="text-white font-medium">{task.title}</div>
                            <div className="flex items-center gap-3 text-slate-400 text-sm mt-1">
                              <span className="capitalize">{task.task_type.replace('_', ' ')}</span>
                              <span>•</span>
                              <span>{task.related_to_name}</span>
                            </div>
                          </div>
                        </div>
                        
                        {task.description && (
                          <div className="text-slate-300 text-sm ml-11 mb-2">
                            {task.description}
                          </div>
                        )}
                        
                        <div className="flex items-center gap-3 ml-11">
                          <div className="flex items-center gap-2 text-slate-400 text-sm">
                            <Calendar className="w-4 h-4" />
                            {new Date(task.due_date).toLocaleString()}
                          </div>
                          
                          <Badge className={`${getPriorityColor(task.priority)} text-white`}>
                            {task.priority}
                          </Badge>
                          
                          <Badge className={task.status === 'completed' ? 'bg-green-500' : task.status === 'cancelled' ? 'bg-gray-500' : 'bg-orange-500'}>
                            {task.status}
                          </Badge>
                          
                          {isOverdue(task.due_date, task.status) && (
                            <Badge className="bg-red-500 text-white">
                              Overdue
                            </Badge>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {task.status === 'pending' && (
                          <Button
                            size="sm"
                            onClick={() => updateTaskStatus(task.id, 'completed')}
                            className="bg-green-600 hover:bg-green-700"
                          >
                            Mark Complete
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => deleteTask(task.id)}
                          className="text-red-400 hover:text-red-300 hover:bg-slate-700"
                        >
                          Delete
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
                
                {filteredTasks.length === 0 && (
                  <div className="text-center py-12 text-slate-400">
                    <CheckSquare className="w-16 h-16 mx-auto mb-4 opacity-50" />
                    <p>No tasks found</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
