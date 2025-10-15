import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DollarSign, FileText, CheckCircle, Clock, AlertCircle, Calendar } from 'lucide-react';
import { toast } from 'sonner';

export default function Levies() {
  const [levies, setLevies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLevies();
  }, []);

  const fetchLevies = async () => {
    try {
      const response = await axios.get(`${API}/levies`);
      setLevies(response.data);
    } catch (error) {
      toast.error('Failed to fetch levies');
    } finally {
      setLoading(false);
    }
  };

  const generateLevyInvoice = async (levyId) => {
    try {
      await axios.post(`${API}/levies/${levyId}/generate-invoice`);
      toast.success('Levy invoice generated successfully!');
      fetchLevies();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate invoice');
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: { variant: 'secondary', label: 'Pending', icon: Clock },
      paid: { variant: 'default', label: 'Paid', icon: CheckCircle },
      overdue: { variant: 'destructive', label: 'Overdue', icon: AlertCircle }
    };
    const config = badges[status] || badges.pending;
    const Icon = config.icon;
    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className="w-3 h-3" />
        {config.label}
      </Badge>
    );
  };

  const pendingLevies = levies.filter(l => l.status === 'pending');
  const paidLevies = levies.filter(l => l.status === 'paid');
  const overdueLevies = levies.filter(l => {
    if (l.status !== 'pending') return false;
    const dueDate = new Date(l.due_date);
    return dueDate < new Date();
  });

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-white mb-2" data-testid="levies-title">Levy Management</h1>
            <p className="text-slate-400">Manage annual and bi-annual levy charges - billed separately from membership fees</p>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-slate-400 text-sm">Total Levies</p>
                    <p className="text-2xl font-bold text-white mt-1">{levies.length}</p>
                  </div>
                  <Calendar className="w-8 h-8 text-blue-400" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-amber-900/20 border-amber-500">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-amber-400 text-sm">Pending</p>
                    <p className="text-2xl font-bold text-white mt-1">{pendingLevies.length}</p>
                  </div>
                  <Clock className="w-8 h-8 text-amber-400" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-red-900/20 border-red-500">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-red-400 text-sm">Overdue</p>
                    <p className="text-2xl font-bold text-white mt-1">{overdueLevies.length}</p>
                  </div>
                  <AlertCircle className="w-8 h-8 text-red-400" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-emerald-900/20 border-emerald-500">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-emerald-400 text-sm">Paid</p>
                    <p className="text-2xl font-bold text-white mt-1">{paidLevies.length}</p>
                  </div>
                  <CheckCircle className="w-8 h-8 text-emerald-400" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Info Card */}
          <Card className="bg-blue-900/20 border-blue-500 mb-8">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <DollarSign className="w-5 h-5 text-blue-400 mt-0.5" />
                <div>
                  <h3 className="text-blue-200 font-semibold mb-1">Separate Billing for Better Success Rates</h3>
                  <p className="text-blue-300 text-sm">
                    Levies are intentionally billed separately from regular membership fees. This approach reduces payment failures 
                    and improves collection rates by avoiding higher combined amounts that often result in declined transactions.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Tabs defaultValue="pending" className="w-full">
            <TabsList className="bg-slate-800/50 border-slate-700">
              <TabsTrigger value="pending">
                Pending ({pendingLevies.length})
              </TabsTrigger>
              <TabsTrigger value="overdue">
                Overdue ({overdueLevies.length})
              </TabsTrigger>
              <TabsTrigger value="paid">
                Paid ({paidLevies.length})
              </TabsTrigger>
            </TabsList>

            {/* Pending Levies Tab */}
            <TabsContent value="pending" className="mt-6">
              <div className="space-y-4">
                {pendingLevies.map((levy) => (
                  <Card key={levy.id} className="bg-slate-800/50 border-slate-700" data-testid={`levy-${levy.id}`}>
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-white font-semibold">{levy.member_name}</h3>
                            {getStatusBadge(levy.status)}
                            <Badge className="bg-amber-500">{levy.levy_type}</Badge>
                          </div>
                          <div className="space-y-1">
                            <p className="text-slate-400 text-sm">
                              Amount: <span className="text-white font-bold">R {levy.amount.toFixed(2)}</span>
                            </p>
                            <p className="text-slate-400 text-sm">
                              Due Date: <span className="text-white">{new Date(levy.due_date).toLocaleDateString()}</span>
                            </p>
                            {levy.invoice_id && (
                              <p className="text-emerald-400 text-sm">
                                ✓ Invoice generated: {levy.invoice_id.substring(0, 8)}...
                              </p>
                            )}
                          </div>
                        </div>
                        <div className="flex flex-col gap-2">
                          {!levy.invoice_id ? (
                            <Button
                              size="sm"
                              onClick={() => generateLevyInvoice(levy.id)}
                              className="bg-gradient-to-r from-amber-500 to-orange-600"
                              data-testid={`generate-invoice-${levy.id}`}
                            >
                              <FileText className="w-4 h-4 mr-1" />
                              Generate Invoice
                            </Button>
                          ) : (
                            <Button
                              size="sm"
                              variant="outline"
                              className="border-emerald-500 text-emerald-400"
                              disabled
                            >
                              Invoice Created
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                {pendingLevies.length === 0 && (
                  <p className="text-center text-slate-400 py-8">No pending levies</p>
                )}
              </div>
            </TabsContent>

            {/* Overdue Levies Tab */}
            <TabsContent value="overdue" className="mt-6">
              <div className="space-y-4">
                {overdueLevies.map((levy) => (
                  <Card key={levy.id} className="bg-red-900/10 border-red-500/50">
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-white font-semibold">{levy.member_name}</h3>
                            <Badge variant="destructive">Overdue</Badge>
                            <Badge className="bg-amber-500">{levy.levy_type}</Badge>
                          </div>
                          <div className="space-y-1">
                            <p className="text-slate-400 text-sm">
                              Amount: <span className="text-white font-bold">R {levy.amount.toFixed(2)}</span>
                            </p>
                            <p className="text-red-400 text-sm">
                              ⚠️ Due Date: <span className="font-medium">{new Date(levy.due_date).toLocaleDateString()}</span>
                            </p>
                          </div>
                        </div>
                        <div className="flex flex-col gap-2">
                          {!levy.invoice_id && (
                            <Button
                              size="sm"
                              onClick={() => generateLevyInvoice(levy.id)}
                              className="bg-gradient-to-r from-red-500 to-orange-600"
                            >
                              <FileText className="w-4 h-4 mr-1" />
                              Generate Invoice
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                {overdueLevies.length === 0 && (
                  <p className="text-center text-slate-400 py-8">No overdue levies</p>
                )}
              </div>
            </TabsContent>

            {/* Paid Levies Tab */}
            <TabsContent value="paid" className="mt-6">
              <div className="space-y-4">
                {paidLevies.map((levy) => (
                  <Card key={levy.id} className="bg-slate-800/50 border-slate-700">
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-white font-semibold">{levy.member_name}</h3>
                            {getStatusBadge(levy.status)}
                            <Badge className="bg-amber-500">{levy.levy_type}</Badge>
                          </div>
                          <div className="space-y-1">
                            <p className="text-slate-400 text-sm">
                              Amount: <span className="text-white font-bold">R {levy.amount.toFixed(2)}</span>
                            </p>
                            <p className="text-emerald-400 text-sm">
                              ✓ Paid on: {levy.paid_date ? new Date(levy.paid_date).toLocaleDateString() : 'N/A'}
                            </p>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                {paidLevies.length === 0 && (
                  <p className="text-center text-slate-400 py-8">No paid levies</p>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
