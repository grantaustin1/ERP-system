import { useState, useEffect } from 'react';
import axios from 'axios';
import Sidebar from '../components/Sidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Button } from '../components/ui/button';
import { useToast } from '../hooks/use-toast';
import {
  FileText,
  Download,
  Upload,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Ban,
  FileDown,
  FileUp,
  TrendingUp,
  TrendingDown,
  DollarSign
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export default function DebitOrderManagement() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('outgoing');
  
  // Data states
  const [outgoingFiles, setOutgoingFiles] = useState([]);
  const [incomingFiles, setIncomingFiles] = useState([]);
  const [stuckFiles, setStuckFiles] = useState([]);
  const [disallowedFiles, setDisallowedFiles] = useState([]);
  
  // Dialog states
  const [disallowDialogOpen, setDisallowDialogOpen] = useState(false);
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [disallowReason, setDisallowReason] = useState('');
  
  // Export states
  const [exportLoading, setExportLoading] = useState(false);

  useEffect(() => {
    fetchData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [outgoingRes, incomingRes, stuckRes, disallowedRes] = await Promise.all([
        axios.get(`${API}/api/eft/files/outgoing`),
        axios.get(`${API}/api/eft/files/incoming`),
        axios.get(`${API}/api/eft/files/stuck`),
        axios.get(`${API}/api/eft/transactions/disallowed`)
      ]);
      
      setOutgoingFiles(outgoingRes.data.files || []);
      setIncomingFiles(incomingRes.data.files || []);
      setStuckFiles(stuckRes.data.stuck_files || []);
      setDisallowedFiles(disallowedRes.data.transactions || []);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast({
        title: "Error",
        description: "Failed to fetch file data",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDisallowClick = (transaction) => {
    setSelectedTransaction(transaction);
    setDisallowDialogOpen(true);
  };

  const handleDisallowConfirm = async () => {
    if (!disallowReason.trim()) {
      toast({
        title: "Error",
        description: "Please provide a reason for disallowing",
        variant: "destructive"
      });
      return;
    }

    try {
      await axios.post(`${API}/api/eft/transactions/${selectedTransaction.id}/disallow`, {
        reason: disallowReason
      });
      
      toast({
        title: "Success",
        description: "Transaction disallowed successfully"
      });
      
      setDisallowDialogOpen(false);
      setDisallowReason('');
      setSelectedTransaction(null);
      fetchData();
    } catch (error) {
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to disallow transaction",
        variant: "destructive"
      });
    }
  };

  const handleNotifyStuckFiles = async () => {
    try {
      const response = await axios.post(`${API}/api/eft/files/stuck/notify`);
      toast({
        title: "Success",
        description: response.data.message
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to send notifications",
        variant: "destructive"
      });
    }
  };

  const handleExportReport = async (reportType) => {
    setExportLoading(true);
    try {
      let endpoint = '';
      let filename = '';
      
      switch(reportType) {
        case 'payments':
          endpoint = '/api/reports/payments/export';
          filename = 'payments_report.csv';
          break;
        case 'unpaid':
          endpoint = '/api/reports/unpaid/export';
          filename = 'unpaid_report.csv';
          break;
        case 'monthly':
          endpoint = '/api/reports/monthly-billing/export';
          filename = 'monthly_billing.csv';
          break;
        default:
          return;
      }
      
      const response = await axios.get(`${API}${endpoint}?format=csv`);
      
      // Create download link
      const blob = new Blob([response.data.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = response.data.filename || filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast({
        title: "Success",
        description: `Exported ${response.data.total_records} records`
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to export report",
        variant: "destructive"
      });
    } finally {
      setExportLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      generated: { color: 'bg-blue-500', icon: Clock, label: 'Generated' },
      submitted: { color: 'bg-yellow-500', icon: Upload, label: 'Submitted' },
      acknowledged: { color: 'bg-emerald-500', icon: CheckCircle, label: 'Acknowledged' },
      processed: { color: 'bg-green-500', icon: CheckCircle, label: 'Processed' },
      failed: { color: 'bg-red-500', icon: XCircle, label: 'Failed' },
      disallowed: { color: 'bg-orange-500', icon: Ban, label: 'Disallowed' }
    };
    
    const badge = badges[status] || badges.generated;
    const Icon = badge.icon;
    
    return (
      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium text-white ${badge.color}`}>
        <Icon className="w-3 h-3" />
        {badge.label}
      </span>
    );
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleString();
  };

  const formatAmount = (amount) => {
    return new Intl.NumberFormat('en-ZA', {
      style: 'currency',
      currency: 'ZAR'
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="flex min-h-screen bg-slate-900">
        <Sidebar />
        <div className="flex-1 p-8">
          <div className="text-center text-white">Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-slate-900">
      <Sidebar />
      
      <div className="flex-1 p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">💳 Debit Order Management</h1>
          <p className="text-slate-400">Monitor and manage EFT/DebiCheck file processing</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-4 gap-6 mb-8">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Outgoing Files</p>
                  <p className="text-3xl font-bold text-white mt-2">{outgoingFiles.length}</p>
                </div>
                <FileUp className="w-12 h-12 text-blue-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Incoming Files</p>
                  <p className="text-3xl font-bold text-white mt-2">{incomingFiles.length}</p>
                </div>
                <FileDown className="w-12 h-12 text-emerald-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Stuck Files</p>
                  <p className="text-3xl font-bold text-white mt-2">{stuckFiles.length}</p>
                </div>
                <AlertTriangle className="w-12 h-12 text-orange-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Disallowed</p>
                  <p className="text-3xl font-bold text-white mt-2">{disallowedFiles.length}</p>
                </div>
                <Ban className="w-12 h-12 text-red-400" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Export Reports Section */}
        <Card className="bg-slate-800/50 border-slate-700 mb-8">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Export Reports
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              <Button
                onClick={() => handleExportReport('payments')}
                disabled={exportLoading}
                className="bg-emerald-500 hover:bg-emerald-600"
              >
                <Download className="w-4 h-4 mr-2" />
                Payments Report
              </Button>
              <Button
                onClick={() => handleExportReport('unpaid')}
                disabled={exportLoading}
                className="bg-orange-500 hover:bg-orange-600"
              >
                <Download className="w-4 h-4 mr-2" />
                Unpaid Report
              </Button>
              <Button
                onClick={() => handleExportReport('monthly')}
                disabled={exportLoading}
                className="bg-blue-500 hover:bg-blue-600"
              >
                <Download className="w-4 h-4 mr-2" />
                Monthly Billing
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Tabs for File Management */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="p-6">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="bg-slate-700/50 mb-6">
                <TabsTrigger value="outgoing" className="data-[state=active]:bg-emerald-500">
                  <FileUp className="w-4 h-4 mr-2" />
                  Outgoing Files
                </TabsTrigger>
                <TabsTrigger value="incoming" className="data-[state=active]:bg-emerald-500">
                  <FileDown className="w-4 h-4 mr-2" />
                  Incoming Files
                </TabsTrigger>
                <TabsTrigger value="stuck" className="data-[state=active]:bg-emerald-500">
                  <AlertTriangle className="w-4 h-4 mr-2" />
                  Stuck Files ({stuckFiles.length})
                </TabsTrigger>
                <TabsTrigger value="disallowed" className="data-[state=active]:bg-emerald-500">
                  <Ban className="w-4 h-4 mr-2" />
                  Disallowed History
                </TabsTrigger>
              </TabsList>

              {/* Outgoing Files Tab */}
              <TabsContent value="outgoing">
                <div className="space-y-4">
                  {outgoingFiles.length === 0 ? (
                    <div className="text-center py-12">
                      <FileUp className="w-16 h-16 mx-auto text-slate-600 mb-4" />
                      <p className="text-slate-400">No outgoing files found</p>
                    </div>
                  ) : (
                    outgoingFiles.map(file => (
                      <Card key={file.id} className="bg-slate-700/50 border-slate-600">
                        <CardContent className="p-4">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <h4 className="text-white font-semibold">{file.file_name}</h4>
                                {getStatusBadge(file.status)}
                                {file.is_stuck && (
                                  <span className="text-orange-400 text-xs flex items-center gap-1">
                                    <AlertTriangle className="w-3 h-3" />
                                    Stuck
                                  </span>
                                )}
                              </div>
                              <div className="grid grid-cols-4 gap-4 text-sm">
                                <div>
                                  <p className="text-slate-400">Type</p>
                                  <p className="text-white capitalize">{file.transaction_type}</p>
                                </div>
                                <div>
                                  <p className="text-slate-400">Transactions</p>
                                  <p className="text-white">{file.total_transactions}</p>
                                </div>
                                <div>
                                  <p className="text-slate-400">Total Amount</p>
                                  <p className="text-white">{formatAmount(file.total_amount)}</p>
                                </div>
                                <div>
                                  <p className="text-slate-400">Generated</p>
                                  <p className="text-white text-xs">{formatDate(file.generated_at)}</p>
                                </div>
                              </div>
                            </div>
                            <div className="flex gap-2">
                              {file.status !== 'disallowed' && file.status !== 'processed' && (
                                <Button
                                  onClick={() => handleDisallowClick(file)}
                                  variant="destructive"
                                  size="sm"
                                >
                                  <Ban className="w-4 h-4 mr-2" />
                                  Disallow
                                </Button>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))
                  )}
                </div>
              </TabsContent>

              {/* Incoming Files Tab */}
              <TabsContent value="incoming">
                <div className="space-y-4">
                  {incomingFiles.length === 0 ? (
                    <div className="text-center py-12">
                      <FileDown className="w-16 h-16 mx-auto text-slate-600 mb-4" />
                      <p className="text-slate-400">No incoming files found</p>
                    </div>
                  ) : (
                    incomingFiles.map(file => (
                      <Card key={file.id} className="bg-slate-700/50 border-slate-600">
                        <CardContent className="p-4">
                          <div className="flex items-center gap-3 mb-2">
                            <h4 className="text-white font-semibold">{file.file_name}</h4>
                            {getStatusBadge(file.status)}
                          </div>
                          <div className="grid grid-cols-4 gap-4 text-sm">
                            <div>
                              <p className="text-slate-400">Response File</p>
                              <p className="text-white">{file.response_file || 'N/A'}</p>
                            </div>
                            <div>
                              <p className="text-slate-400">Processed</p>
                              <p className="text-white text-xs">{formatDate(file.processed_at)}</p>
                            </div>
                            <div>
                              <p className="text-slate-400">Notes</p>
                              <p className="text-white text-xs">{file.notes || 'None'}</p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))
                  )}
                </div>
              </TabsContent>

              {/* Stuck Files Tab */}
              <TabsContent value="stuck">
                <div className="space-y-4">
                  {stuckFiles.length > 0 && (
                    <div className="mb-4">
                      <Button
                        onClick={handleNotifyStuckFiles}
                        className="bg-orange-500 hover:bg-orange-600"
                      >
                        <AlertTriangle className="w-4 h-4 mr-2" />
                        Send Notifications
                      </Button>
                    </div>
                  )}
                  
                  {stuckFiles.length === 0 ? (
                    <div className="text-center py-12">
                      <CheckCircle className="w-16 h-16 mx-auto text-green-600 mb-4" />
                      <p className="text-slate-400">No stuck files - all processing normally!</p>
                    </div>
                  ) : (
                    stuckFiles.map(file => (
                      <Card key={file.id} className="bg-orange-500/10 border-orange-500/30">
                        <CardContent className="p-4">
                          <div className="flex items-center gap-3 mb-2">
                            <AlertTriangle className="w-5 h-5 text-orange-400" />
                            <h4 className="text-white font-semibold">{file.file_name}</h4>
                            {getStatusBadge(file.status)}
                          </div>
                          <p className="text-slate-300 text-sm mb-2">
                            Generated {formatDate(file.generated_at)} - No response received
                          </p>
                          <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                              <p className="text-slate-400">Transactions</p>
                              <p className="text-white">{file.total_transactions}</p>
                            </div>
                            <div>
                              <p className="text-slate-400">Amount</p>
                              <p className="text-white">{formatAmount(file.total_amount)}</p>
                            </div>
                            <div>
                              <p className="text-slate-400">Type</p>
                              <p className="text-white capitalize">{file.transaction_type}</p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))
                  )}
                </div>
              </TabsContent>

              {/* Disallowed History Tab */}
              <TabsContent value="disallowed">
                <div className="space-y-4">
                  {disallowedFiles.length === 0 ? (
                    <div className="text-center py-12">
                      <Ban className="w-16 h-16 mx-auto text-slate-600 mb-4" />
                      <p className="text-slate-400">No disallowed transactions</p>
                    </div>
                  ) : (
                    disallowedFiles.map(file => (
                      <Card key={file.id} className="bg-slate-700/50 border-slate-600">
                        <CardContent className="p-4">
                          <div className="flex items-center gap-3 mb-2">
                            <Ban className="w-5 h-5 text-red-400" />
                            <h4 className="text-white font-semibold">{file.file_name}</h4>
                            {getStatusBadge(file.status)}
                          </div>
                          <div className="grid grid-cols-4 gap-4 text-sm mt-3">
                            <div>
                              <p className="text-slate-400">Disallowed At</p>
                              <p className="text-white text-xs">{formatDate(file.disallowed_at)}</p>
                            </div>
                            <div>
                              <p className="text-slate-400">Reason</p>
                              <p className="text-white">{file.disallow_reason}</p>
                            </div>
                            <div>
                              <p className="text-slate-400">Transactions</p>
                              <p className="text-white">{file.total_transactions}</p>
                            </div>
                            <div>
                              <p className="text-slate-400">Amount</p>
                              <p className="text-white">{formatAmount(file.total_amount)}</p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))
                  )}
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>

      {/* Disallow Confirmation Dialog */}
      <Dialog open={disallowDialogOpen} onOpenChange={setDisallowDialogOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 text-white">
          <DialogHeader>
            <DialogTitle>Disallow Transaction Batch</DialogTitle>
            <DialogDescription className="text-slate-400">
              This will cancel the batch and prevent it from being processed. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          
          {selectedTransaction && (
            <div className="space-y-4 py-4">
              <div className="bg-slate-700/50 rounded-lg p-4 space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-400">File:</span>
                  <span className="text-white font-medium">{selectedTransaction.file_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Transactions:</span>
                  <span className="text-white">{selectedTransaction.total_transactions}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Amount:</span>
                  <span className="text-white">{formatAmount(selectedTransaction.total_amount)}</span>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Reason for Disallowing *</Label>
                <Textarea
                  value={disallowReason}
                  onChange={(e) => setDisallowReason(e.target.value)}
                  placeholder="Enter reason for disallowing this batch..."
                  className="bg-slate-700 border-slate-600 text-white"
                  rows={4}
                />
              </div>
            </div>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setDisallowDialogOpen(false);
                setDisallowReason('');
                setSelectedTransaction(null);
              }}
              className="border-slate-600 text-white hover:bg-slate-700"
            >
              Cancel
            </Button>
            <Button
              onClick={handleDisallowConfirm}
              className="bg-red-500 hover:bg-red-600"
            >
              <Ban className="w-4 h-4 mr-2" />
              Confirm Disallow
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
