import { useState, useEffect } from 'react';
import axios from 'axios';
import Sidebar from '../components/Sidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { useToast } from '../hooks/use-toast';
import {
  Activity,
  CheckCircle,
  AlertCircle,
  Download,
  RefreshCw,
  TrendingUp,
  DollarSign,
  Clock,
  FileText
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL || '';

export default function TransactionReconciliation() {
  const [loading, setLoading] = useState(true);
  const [fetching, setFetching] = useState(false);
  const [reconciling, setReconciling] = useState(false);
  const [ftiTransactions, setFtiTransactions] = useState([]);
  const [ptiTransactions, setPtiTransactions] = useState([]);
  const [reconciliationHistory, setReconciliationHistory] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const { toast } = useToast();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [ftiRes, ptiRes, historyRes] = await Promise.all([
        axios.get(`${API}/api/ti/fti/transactions?limit=50`),
        axios.get(`${API}/api/ti/pti/transactions?limit=20`),
        axios.get(`${API}/api/ti/reconciliation/history?limit=10`)
      ]);

      setFtiTransactions(ftiRes.data.transactions || []);
      setPtiTransactions(ptiRes.data.transactions || []);
      setReconciliationHistory(historyRes.data.results || []);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast({
        title: "Error",
        description: "Failed to fetch transaction data",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFetchFti = async () => {
    setFetching(true);
    try {
      const response = await axios.post(`${API}/api/ti/fti/fetch`);
      toast({
        title: "Success",
        description: response.data.message || "FTI transactions fetched"
      });
      await fetchData();
    } catch (error) {
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to fetch FTI",
        variant: "destructive"
      });
    } finally {
      setFetching(false);
    }
  };

  const handleReconcile = async () => {
    setReconciling(true);
    try {
      const response = await axios.post(`${API}/api/ti/fti/reconcile`);
      const recon = response.data.reconciliation;
      
      toast({
        title: "Reconciliation Complete",
        description: `Matched ${recon.matched_count} of ${recon.total_transactions} transactions (${recon.match_rate.toFixed(1)}%)`
      });
      
      await fetchData();
    } catch (error) {
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Reconciliation failed",
        variant: "destructive"
      });
    } finally {
      setReconciling(false);
    }
  };

  const handleFetchPti = async () => {
    try {
      const response = await axios.post(`${API}/api/ti/pti/fetch`);
      toast({
        title: "Success",
        description: `Fetched ${response.data.new_transactions} new provisional transactions`
      });
      await fetchData();
    } catch (error) {
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to fetch PTI",
        variant: "destructive"
      });
    }
  };

  const handleViewReport = async (reportId) => {
    try {
      const response = await axios.get(`${API}/api/ti/reconciliation/report/${reportId}`);
      setSelectedReport(response.data.report);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load report",
        variant: "destructive"
      });
    }
  };

  const getMatchConfidenceBadge = (confidence) => {
    const colors = {
      high: "bg-green-500/20 text-green-300 border-green-500/50",
      medium: "bg-yellow-500/20 text-yellow-300 border-yellow-500/50",
      low: "bg-orange-500/20 text-orange-300 border-orange-500/50"
    };
    return colors[confidence] || colors.low;
  };

  // Calculate summary stats
  const unreconciledCount = ftiTransactions.filter(t => !t.is_reconciled).length;
  const reconciledCount = ftiTransactions.filter(t => t.is_reconciled).length;
  const totalFtiAmount = ftiTransactions
    .filter(t => !t.is_debit && t.amount > 0)
    .reduce((sum, t) => sum + t.amount, 0);

  if (loading) {
    return (
      <div className="flex h-screen bg-gradient-to-br from-slate-900 to-slate-800">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-8">
          <div className="flex items-center justify-center h-full">
            <RefreshCw className="w-8 h-8 animate-spin text-emerald-500" />
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-900 to-slate-800">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">Transaction Reconciliation</h1>
              <p className="text-slate-400">Automated payment reconciliation & real-time tracking</p>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={handleFetchFti}
                disabled={fetching}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {fetching ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Download className="w-4 h-4 mr-2" />}
                Fetch FTI
              </Button>
              <Button
                onClick={handleReconcile}
                disabled={reconciling || unreconciledCount === 0}
                className="bg-emerald-600 hover:bg-emerald-700"
              >
                {reconciling ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle className="w-4 h-4 mr-2" />}
                Reconcile Now
              </Button>
            </div>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-400">Total Transactions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-white">{ftiTransactions.length}</div>
                <p className="text-xs text-slate-400 mt-1">FTI records</p>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-400">Unreconciled</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-orange-400">{unreconciledCount}</div>
                <p className="text-xs text-slate-400 mt-1">Need matching</p>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-400">Reconciled</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-400">{reconciledCount}</div>
                <p className="text-xs text-slate-400 mt-1">Matched to invoices</p>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-400">Total Amount</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-emerald-400">R{totalFtiAmount.toFixed(2)}</div>
                <p className="text-xs text-slate-400 mt-1">Credits received</p>
              </CardContent>
            </Card>
          </div>

          {/* Main Content Tabs */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Transaction Management</CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="fti" className="w-full">
                <TabsList className="grid w-full grid-cols-3 bg-slate-700/50">
                  <TabsTrigger value="fti">FTI Transactions</TabsTrigger>
                  <TabsTrigger value="pti">PTI (Real-time)</TabsTrigger>
                  <TabsTrigger value="history">Reconciliation History</TabsTrigger>
                </TabsList>

                <TabsContent value="fti" className="mt-4">
                  <div className="space-y-3">
                    {ftiTransactions.length === 0 ? (
                      <div className="text-center py-12">
                        <FileText className="w-16 h-16 mx-auto text-slate-600 mb-4" />
                        <p className="text-slate-400">No FTI transactions. Click "Fetch FTI" to retrieve transactions.</p>
                      </div>
                    ) : (
                      ftiTransactions.map((transaction) => (
                        <div
                          key={transaction.id}
                          className={`p-4 rounded-lg border ${
                            transaction.is_reconciled
                              ? 'bg-green-500/5 border-green-500/30'
                              : 'bg-slate-700/50 border-slate-600'
                          }`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <span className="text-white font-semibold">{transaction.description}</span>
                                {transaction.is_reconciled && (
                                  <Badge className={getMatchConfidenceBadge(transaction.match_confidence)}>
                                    {transaction.match_confidence}
                                  </Badge>
                                )}
                              </div>
                              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                                <div className="text-slate-400">
                                  Date: <span className="text-slate-300">{transaction.date} {transaction.time}</span>
                                </div>
                                <div className="text-slate-400">
                                  Reference: <span className="text-slate-300">{transaction.reference}</span>
                                </div>
                                <div className="text-slate-400">
                                  Type: <span className="text-slate-300">{transaction.transaction_type_name}</span>
                                </div>
                                <div className="text-slate-400">
                                  Channel: <span className="text-slate-300">{transaction.channel_name}</span>
                                </div>
                                {transaction.is_reconciled && (
                                  <>
                                    <div className="text-slate-400">
                                      Invoice: <span className="text-green-400">{transaction.matched_invoice_id}</span>
                                    </div>
                                    <div className="text-slate-400">
                                      Match: <span className="text-slate-300">{transaction.match_reason}</span>
                                    </div>
                                  </>
                                )}
                              </div>
                            </div>
                            <div className="text-right">
                              <div className={`text-xl font-bold ${transaction.is_debit ? 'text-red-400' : 'text-green-400'}`}>
                                {transaction.is_debit ? '-' : '+'}R{Math.abs(transaction.amount).toFixed(2)}
                              </div>
                              <div className="text-sm text-slate-400">
                                {transaction.is_reconciled ? (
                                  <span className="text-green-400">✓ Reconciled</span>
                                ) : (
                                  <span className="text-orange-400">⚠ Pending</span>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </TabsContent>

                <TabsContent value="pti" className="mt-4">
                  <div className="mb-4 flex justify-end">
                    <Button onClick={handleFetchPti} size="sm" className="bg-blue-600 hover:bg-blue-700">
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Refresh PTI
                    </Button>
                  </div>
                  <div className="space-y-3">
                    {ptiTransactions.length === 0 ? (
                      <div className="text-center py-12">
                        <Clock className="w-16 h-16 mx-auto text-slate-600 mb-4" />
                        <p className="text-slate-400">No provisional transactions. Enable PTI in settings to track real-time payments.</p>
                      </div>
                    ) : (
                      ptiTransactions.map((transaction) => (
                        <div
                          key={transaction.id}
                          className="p-4 rounded-lg border bg-blue-500/5 border-blue-500/30"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <span className="text-white font-semibold">{transaction.description}</span>
                                <Badge className="bg-blue-500/20 text-blue-300 border-blue-500/50">
                                  Provisional
                                </Badge>
                              </div>
                              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                                <div className="text-slate-400">
                                  Date: <span className="text-slate-300">{transaction.date} {transaction.time}</span>
                                </div>
                                <div className="text-slate-400">
                                  Reference: <span className="text-slate-300">{transaction.reference}</span>
                                </div>
                                <div className="text-slate-400">
                                  Type: <span className="text-slate-300">{transaction.transaction_type_name}</span>
                                </div>
                                <div className="text-slate-400">
                                  Channel: <span className="text-slate-300">{transaction.channel_name}</span>
                                </div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-xl font-bold text-blue-400">
                                +R{transaction.amount.toFixed(2)}
                              </div>
                              <div className="text-sm text-blue-400">Pending confirmation</div>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </TabsContent>

                <TabsContent value="history" className="mt-4">
                  <div className="space-y-3">
                    {reconciliationHistory.length === 0 ? (
                      <div className="text-center py-12">
                        <FileText className="w-16 h-16 mx-auto text-slate-600 mb-4" />
                        <p className="text-slate-400">No reconciliation history. Run your first reconciliation to see results here.</p>
                      </div>
                    ) : (
                      reconciliationHistory.map((result) => (
                        <div
                          key={result.id}
                          className="p-4 rounded-lg border bg-slate-700/50 border-slate-600 hover:border-emerald-500/50 cursor-pointer transition-colors"
                          onClick={() => handleViewReport(result.id)}
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div>
                              <div className="text-white font-semibold mb-1">
                                Reconciliation - {new Date(result.reconciliation_date).toLocaleDateString()}
                              </div>
                              <div className="text-sm text-slate-400">
                                {new Date(result.reconciliation_date).toLocaleTimeString()}
                              </div>
                            </div>
                            <Badge className="bg-emerald-500/20 text-emerald-300 border-emerald-500/50">
                              {result.match_rate.toFixed(1)}% matched
                            </Badge>
                          </div>
                          <div className="grid grid-cols-4 gap-4 text-sm">
                            <div>
                              <div className="text-slate-400">Total</div>
                              <div className="text-white font-semibold">{result.total_transactions}</div>
                            </div>
                            <div>
                              <div className="text-slate-400">Matched</div>
                              <div className="text-green-400 font-semibold">{result.matched_count}</div>
                            </div>
                            <div>
                              <div className="text-slate-400">Unmatched</div>
                              <div className="text-orange-400 font-semibold">{result.unmatched_count}</div>
                            </div>
                            <div>
                              <div className="text-slate-400">Amount</div>
                              <div className="text-emerald-400 font-semibold">R{result.total_matched_amount.toFixed(2)}</div>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Report Modal */}
          {selectedReport && (
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-white">Reconciliation Report</CardTitle>
                  <Button
                    onClick={() => setSelectedReport(null)}
                    variant="ghost"
                    size="sm"
                    className="text-slate-400"
                  >
                    Close
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <pre className="bg-slate-900 p-4 rounded-lg text-sm text-slate-300 overflow-x-auto">
                  {selectedReport.report_text}
                </pre>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}
