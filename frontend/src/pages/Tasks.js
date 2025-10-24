import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { Plus, CheckCircle2, Clock, AlertCircle, XCircle, Pause, FileText, MessageSquare } from 'lucide-react';
import { toast } from 'sonner';

export default function Tasks() {
  const [tasks, setTasks] = useState([]);
  const [taskTypes, setTaskTypes] = useState([]);
  const [members, setMembers] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [stats, setStats] = useState({});
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    task_type_id: '',
    priority: 'medium',
    assigned_to_user_id: '',
    assigned_to_department: '',
    related_member_id: '',
    due_date: ''
  });

  useEffect(() => {
    fetchTasks();
    fetchTaskTypes();
    fetchMembers();
    fetchUsers();
    fetchStats();
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await axios.get(`${API}/tasks`);
      setTasks(response.data);
    } catch (error) {
      console.error('Error fetching tasks:', error);
      toast.error('Failed to fetch tasks');
    } finally {
      setLoading(false);
    }
  };

  const fetchTaskTypes = async () => {
    try {
      const response = await axios.get(`${API}/task-types`);
      setTaskTypes(response.data);
    } catch (error) {
      console.error('Error fetching task types:', error);
    }
  };

  const fetchMembers = async () => {
    try {
      const response = await axios.get(`${API}/members`);
      setMembers(response.data);
    } catch (error) {
      console.error('Error fetching members:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users/list`);
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/tasks/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/tasks`, formData);
      toast.success('Task created successfully');
      setDialogOpen(false);
      setFormData({
        title: '',
        description: '',
        task_type_id: '',
        priority: 'medium',
        assigned_to_user_id: '',
        assigned_to_department: '',
        related_member_id: '',
        due_date: ''
      });
      fetchTasks();
      fetchStats();
    } catch (error) {
      console.error('Error creating task:', error);
      toast.error('Failed to create task');
    }
  };

  const handleStatusChange = async (taskId, newStatus) => {
    try {
      await axios.put(`${API}/tasks/${taskId}`, { status: newStatus });
      toast.success('Task status updated');
      fetchTasks();
      fetchStats();
      if (selectedTask && selectedTask.task_id === taskId) {
        setSelectedTask({ ...selectedTask, status: newStatus });
      }
    } catch (error) {
      console.error('Error updating task:', error);
      toast.error('Failed to update task');
    }
  };

  const openTaskDetail = async (task) => {
    setSelectedTask(task);
    setDetailDialogOpen(true);
    try {
      const response = await axios.get(`${API}/tasks/${task.task_id}/comments`);
      setComments(response.data);
    } catch (error) {
      console.error('Error fetching comments:', error);
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim()) return;
    try {
      await axios.post(`${API}/tasks/${selectedTask.task_id}/comments`, {
        content: newComment
      });
      toast.success('Comment added');
      setNewComment('');
      const response = await axios.get(`${API}/tasks/${selectedTask.task_id}/comments`);
      setComments(response.data);
      fetchTasks();
    } catch (error) {
      console.error('Error adding comment:', error);
      toast.error('Failed to add comment');
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      pending: 'secondary',
      in_progress: 'default',
      completed: 'default',
      cancelled: 'destructive',
      on_hold: 'secondary',
      needs_review: 'secondary'
    };
    return variants[status] || 'secondary';
  };

  const getPriorityBadge = (priority) => {
    const variants = {
      low: 'secondary',
      medium: 'default',
      high: 'default',
      urgent: 'destructive'
    };
    return variants[priority] || 'default';
  };

  const getStatusIcon = (status) => {
    const icons = {
      pending: Clock,
      in_progress: AlertCircle,
      completed: CheckCircle2,
      cancelled: XCircle,
      on_hold: Pause,
      needs_review: FileText
    };
    const Icon = icons[status] || Clock;
    return <Icon className="w-4 h-4" />;
  };

  const isOverdue = (dueDate, status) => {
    if (!dueDate || status === 'completed' || status === 'cancelled') return false;
    return new Date(dueDate) < new Date();
  };

  const myTasks = tasks.filter(t => t.assigned_to_user_id === JSON.parse(localStorage.getItem('user'))?.id);
  const allTasks = tasks;

  const renderTaskCard = (task) => (
    <Card 
      key={task.task_id}
      className={`bg-slate-800/50 border-slate-700 hover:bg-slate-800/70 transition-all cursor-pointer ${
        isOverdue(task.due_date, task.status) ? 'border-red-500' : ''
      }`}
      onClick={() => openTaskDetail(task)}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-white text-lg flex items-center gap-2">
              {getStatusIcon(task.status)}
              {task.title}
              {isOverdue(task.due_date, task.status) && (
                <Badge variant="destructive" className="text-xs">OVERDUE</Badge>
              )}
            </CardTitle>
            <p className="text-sm text-slate-400 mt-1">{task.task_type_name}</p>
          </div>
          <div className="flex flex-col gap-2">
            <Badge variant={getPriorityBadge(task.priority)}>
              {task.priority.toUpperCase()}
            </Badge>
            <Badge variant={getStatusBadge(task.status)}>
              {task.status.replace('_', ' ').toUpperCase()}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 text-sm">
          {task.description && (
            <div className="text-slate-300">{task.description.substring(0, 100)}...</div>
          )}
          {task.assigned_to_user_name && (
            <div className="flex items-center gap-2">
              <span className="text-slate-400">Assigned to:</span>
              <span className="text-white">{task.assigned_to_user_name}</span>
            </div>
          )}
          {task.assigned_to_department && (
            <div className="flex items-center gap-2">
              <span className="text-slate-400">Department:</span>
              <span className="text-white">{task.assigned_to_department}</span>
            </div>
          )}
          {task.related_member_name && (
            <div className="flex items-center gap-2">
              <span className="text-slate-400">Member:</span>
              <span className="text-white">{task.related_member_name}</span>
            </div>
          )}
          {task.due_date && (
            <div className="flex items-center gap-2">
              <span className="text-slate-400">Due:</span>
              <span className={isOverdue(task.due_date, task.status) ? 'text-red-400 font-semibold' : 'text-white'}>
                {new Date(task.due_date).toLocaleDateString()}
              </span>
            </div>
          )}
          {task.comment_count > 0 && (
            <div className="flex items-center gap-2 text-emerald-400">
              <MessageSquare className="w-4 h-4" />
              <span>{task.comment_count} comments</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <Sidebar />
      <div className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">Tasks</h1>
              <p className="text-slate-400">Manage and track team tasks</p>
            </div>
            <Button onClick={() => setDialogOpen(true)} className="bg-emerald-500 hover:bg-emerald-600">
              <Plus className="w-4 h-4 mr-2" />
              Create Task
            </Button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-6 gap-4 mb-8">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-white">{stats.total || 0}</div>
                <div className="text-xs text-slate-400">Total Tasks</div>
              </CardContent>
            </Card>
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-yellow-400">{stats.pending || 0}</div>
                <div className="text-xs text-slate-400">Pending</div>
              </CardContent>
            </Card>
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-blue-400">{stats.in_progress || 0}</div>
                <div className="text-xs text-slate-400">In Progress</div>
              </CardContent>
            </Card>
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-green-400">{stats.completed || 0}</div>
                <div className="text-xs text-slate-400">Completed</div>
              </CardContent>
            </Card>
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-purple-400">{stats.my_tasks || 0}</div>
                <div className="text-xs text-slate-400">My Tasks</div>
              </CardContent>
            </Card>
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-red-400">{stats.my_overdue || 0}</div>
                <div className="text-xs text-slate-400">My Overdue</div>
              </CardContent>
            </Card>
          </div>

          {/* Tabs */}
          <Tabs defaultValue="all" className="space-y-6">
            <TabsList className="grid w-full grid-cols-3 bg-slate-800">
              <TabsTrigger value="all">All Tasks</TabsTrigger>
              <TabsTrigger value="my">My Tasks</TabsTrigger>
              <TabsTrigger value="assigned">Assigned by Me</TabsTrigger>
            </TabsList>

            <TabsContent value="all" className="space-y-4">
              {loading ? (
                <div className="text-center text-slate-400 py-8">Loading...</div>
              ) : allTasks.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {allTasks.map(renderTaskCard)}
                </div>
              ) : (
                <div className="text-center text-slate-400 py-8">No tasks found</div>
              )}
            </TabsContent>

            <TabsContent value="my" className="space-y-4">
              {myTasks.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {myTasks.map(renderTaskCard)}
                </div>
              ) : (
                <div className="text-center text-slate-400 py-8">No tasks assigned to you</div>
              )}
            </TabsContent>

            <TabsContent value="assigned" className="space-y-4">
              {tasks.filter(t => t.created_by === JSON.parse(localStorage.getItem('user'))?.id).length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {tasks.filter(t => t.created_by === JSON.parse(localStorage.getItem('user'))?.id).map(renderTaskCard)}
                </div>
              ) : (
                <div className="text-center text-slate-400 py-8">No tasks assigned by you</div>
              )}
            </TabsContent>
          </Tabs>

          {/* Create Task Dialog */}
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create New Task</DialogTitle>
                <DialogDescription className="text-slate-400">
                  Create a task and assign it to a team member or department
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2 space-y-2">
                    <Label>Title *</Label>
                    <Input
                      value={formData.title}
                      onChange={(e) => setFormData({...formData, title: e.target.value})}
                      className="bg-slate-700 border-slate-600"
                      required
                    />
                  </div>
                  <div className="col-span-2 space-y-2">
                    <Label>Description</Label>
                    <Textarea
                      value={formData.description}
                      onChange={(e) => setFormData({...formData, description: e.target.value})}
                      className="bg-slate-700 border-slate-600"
                      rows={3}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Task Type *</Label>
                    <Select value={formData.task_type_id} onValueChange={(value) => setFormData({...formData, task_type_id: value})} required>
                      <SelectTrigger className="bg-slate-700 border-slate-600">
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        {taskTypes.map((type) => (
                          <SelectItem key={type.type_id} value={type.type_id}>{type.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Priority</Label>
                    <Select value={formData.priority} onValueChange={(value) => setFormData({...formData, priority: value})}>
                      <SelectTrigger className="bg-slate-700 border-slate-600">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="urgent">Urgent</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Assign to User</Label>
                    <Select value={formData.assigned_to_user_id} onValueChange={(value) => setFormData({...formData, assigned_to_user_id: value})}>
                      <SelectTrigger className="bg-slate-700 border-slate-600">
                        <SelectValue placeholder="Select user" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">None</SelectItem>
                        {users.map((user) => (
                          <SelectItem key={user.id} value={user.id}>{user.full_name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Assign to Department</Label>
                    <Input
                      value={formData.assigned_to_department}
                      onChange={(e) => setFormData({...formData, assigned_to_department: e.target.value})}
                      placeholder="e.g., Sales, Admin"
                      className="bg-slate-700 border-slate-600"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Related Member</Label>
                    <Select value={formData.related_member_id} onValueChange={(value) => setFormData({...formData, related_member_id: value})}>
                      <SelectTrigger className="bg-slate-700 border-slate-600">
                        <SelectValue placeholder="Select member" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">None</SelectItem>
                        {members.slice(0, 50).map((member) => (
                          <SelectItem key={member.id} value={member.id}>
                            {member.first_name} {member.last_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Due Date</Label>
                    <Input
                      type="date"
                      value={formData.due_date}
                      onChange={(e) => setFormData({...formData, due_date: e.target.value})}
                      className="bg-slate-700 border-slate-600"
                    />
                  </div>
                </div>
                <div className="flex gap-2 justify-end">
                  <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" className="bg-emerald-500 hover:bg-emerald-600">
                    Create Task
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>

          {/* Task Detail Dialog */}
          <Dialog open={detailDialogOpen} onOpenChange={setDetailDialogOpen}>
            <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-3xl max-h-[90vh] overflow-y-auto">
              {selectedTask && (
                <>
                  <DialogHeader>
                    <DialogTitle className="text-2xl flex items-center gap-2">
                      {getStatusIcon(selectedTask.status)}
                      {selectedTask.title}
                    </DialogTitle>
                    <DialogDescription className="text-slate-400">
                      {selectedTask.task_type_name}
                    </DialogDescription>
                  </DialogHeader>

                  <div className="space-y-4">
                    {/* Status & Priority */}
                    <div className="flex gap-4">
                      <div className="flex-1 space-y-2">
                        <Label>Status</Label>
                        <Select 
                          value={selectedTask.status} 
                          onValueChange={(value) => handleStatusChange(selectedTask.task_id, value)}
                        >
                          <SelectTrigger className="bg-slate-700 border-slate-600">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="pending">Pending</SelectItem>
                            <SelectItem value="in_progress">In Progress</SelectItem>
                            <SelectItem value="completed">Completed</SelectItem>
                            <SelectItem value="on_hold">On Hold</SelectItem>
                            <SelectItem value="needs_review">Needs Review</SelectItem>
                            <SelectItem value="cancelled">Cancelled</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="flex-1 space-y-2">
                        <Label>Priority</Label>
                        <Badge variant={getPriorityBadge(selectedTask.priority)} className="text-lg py-2 px-4">
                          {selectedTask.priority.toUpperCase()}
                        </Badge>
                      </div>
                    </div>

                    {/* Description */}
                    {selectedTask.description && (
                      <div className="space-y-2">
                        <Label>Description</Label>
                        <div className="text-slate-300 whitespace-pre-wrap bg-slate-700/50 p-3 rounded">
                          {selectedTask.description}
                        </div>
                      </div>
                    )}

                    {/* Details */}
                    <div className="grid grid-cols-2 gap-4">
                      {selectedTask.assigned_to_user_name && (
                        <div className="space-y-1">
                          <Label className="text-slate-400">Assigned To</Label>
                          <div className="text-white">{selectedTask.assigned_to_user_name}</div>
                        </div>
                      )}
                      {selectedTask.assigned_to_department && (
                        <div className="space-y-1">
                          <Label className="text-slate-400">Department</Label>
                          <div className="text-white">{selectedTask.assigned_to_department}</div>
                        </div>
                      )}
                      {selectedTask.related_member_name && (
                        <div className="space-y-1">
                          <Label className="text-slate-400">Related Member</Label>
                          <div className="text-white">{selectedTask.related_member_name}</div>
                        </div>
                      )}
                      {selectedTask.due_date && (
                        <div className="space-y-1">
                          <Label className="text-slate-400">Due Date</Label>
                          <div className={isOverdue(selectedTask.due_date, selectedTask.status) ? 'text-red-400 font-semibold' : 'text-white'}>
                            {new Date(selectedTask.due_date).toLocaleDateString()}
                            {isOverdue(selectedTask.due_date, selectedTask.status) && (
                              <Badge variant="destructive" className="ml-2">OVERDUE</Badge>
                            )}
                          </div>
                        </div>
                      )}
                      <div className="space-y-1">
                        <Label className="text-slate-400">Created By</Label>
                        <div className="text-white">{selectedTask.created_by_name}</div>
                      </div>
                      <div className="space-y-1">
                        <Label className="text-slate-400">Created At</Label>
                        <div className="text-white">{new Date(selectedTask.created_at).toLocaleString()}</div>
                      </div>
                    </div>

                    {/* Comments */}
                    <div className="space-y-3">
                      <Label>Comments ({comments.length})</Label>
                      <div className="space-y-2">
                        <Textarea
                          value={newComment}
                          onChange={(e) => setNewComment(e.target.value)}
                          placeholder="Add a comment..."
                          className="bg-slate-700 border-slate-600"
                          rows={3}
                        />
                        <Button onClick={handleAddComment} size="sm">
                          <MessageSquare className="w-4 h-4 mr-1" />
                          Add Comment
                        </Button>
                      </div>
                      <div className="space-y-2 max-h-64 overflow-y-auto">
                        {comments.map((comment) => (
                          <Card key={comment.comment_id} className="bg-slate-700/50 border-slate-600">
                            <CardContent className="p-3">
                              <div className="text-xs text-slate-400 mb-1">
                                {comment.created_by_name} • {new Date(comment.created_at).toLocaleString()}
                              </div>
                              <div className="text-white whitespace-pre-wrap">{comment.content}</div>
                            </CardContent>
                          </Card>
                        ))}
                        {comments.length === 0 && (
                          <div className="text-center text-slate-400 py-4">No comments yet</div>
                        )}
                      </div>
                    </div>
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
