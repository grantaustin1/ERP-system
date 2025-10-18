import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { 
  Scan, Fingerprint, ScanFace, UserCheck, UserX, Clock, 
  TrendingUp, Activity, BarChart3, MapPin, Shield, CheckCircle2, XCircle 
} from 'lucide-react';

export default function AccessControl() {
  const [accessLogs, setAccessLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scanDialogOpen, setScanDialogOpen] = useState(false);
  const [accessResult, setAccessResult] = useState(null);
  const [manualMemberId, setManualMemberId] = useState('');

  useEffect(() => {
    fetchAccessLogs();
  }, []);

  const fetchAccessLogs = async () => {
    try {
      const response = await axios.get(`${API}/access/logs?limit=50`);
      setAccessLogs(response.data);
    } catch (error) {
      toast.error('Failed to fetch access logs');
    } finally {
      setLoading(false);
    }
  };

  const validateAccess = async (memberId, method) => {
    try {
      const response = await axios.post(`${API}/access/validate`, {
        member_id: memberId,
        access_method: method
      });
      setAccessResult(response.data);
      fetchAccessLogs();
      if (response.data.access === 'granted') {
        toast.success('Access Granted!');
      } else {
        toast.error(`Access Denied: ${response.data.reason}`);
      }
    } catch (error) {
      toast.error('Failed to validate access');
    }
  };

  const handleManualEntry = async () => {
    if (!manualMemberId.trim()) {
      toast.error('Please enter a member ID');
      return;
    }
    await validateAccess(manualMemberId, 'manual_entry');
    setManualMemberId('');
  };

  const simulateBiometric = async (type) => {
    // In a real implementation, this would integrate with actual biometric hardware
    const memberId = prompt(`Enter Member ID for ${type} scan:`);
    if (memberId) {
      await validateAccess(memberId, type);
    }
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-white mb-2" data-testid="access-control-title">Access Control</h1>
            <p className="text-slate-400">Monitor and control gym access in real-time</p>
          </div>

          {/* Access Methods */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg hover:bg-slate-800/70 transition-all cursor-pointer" onClick={() => setScanDialogOpen(true)} data-testid="qr-scan-card">
              <CardContent className="pt-6 text-center">
                <div className="w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center mb-4">
                  <Scan className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-white font-semibold">QR Code Scan</h3>
                <p className="text-slate-400 text-sm mt-1">Scan member QR code</p>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg hover:bg-slate-800/70 transition-all cursor-pointer" onClick={() => simulateBiometric('fingerprint')} data-testid="fingerprint-card">
              <CardContent className="pt-6 text-center">
                <div className="w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center mb-4">
                  <Fingerprint className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-white font-semibold">Fingerprint</h3>
                <p className="text-slate-400 text-sm mt-1">Scan fingerprint</p>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg hover:bg-slate-800/70 transition-all cursor-pointer" onClick={() => simulateBiometric('facial_recognition')} data-testid="facial-recognition-card">
              <CardContent className="pt-6 text-center">
                <div className="w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center mb-4">
                  <ScanFace className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-white font-semibold">Facial Recognition</h3>
                <p className="text-slate-400 text-sm mt-1">Scan face</p>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
              <CardContent className="pt-6">
                <div className="flex gap-2">
                  <Input
                    placeholder="Member ID"
                    value={manualMemberId}
                    onChange={(e) => setManualMemberId(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleManualEntry()}
                    className="bg-slate-700/50 border-slate-600 text-white"
                    data-testid="manual-member-id-input"
                  />
                  <Button onClick={handleManualEntry} className="bg-gradient-to-r from-amber-500 to-orange-600" data-testid="manual-entry-button">
                    Enter
                  </Button>
                </div>
                <p className="text-slate-400 text-sm mt-2 text-center">Manual Entry</p>
              </CardContent>
            </Card>
          </div>

          {/* Access Result */}
          {accessResult && (
            <Card className={`mb-8 border-2 ${accessResult.access === 'granted' ? 'bg-emerald-900/20 border-emerald-500' : 'bg-red-900/20 border-red-500'}`}>
              <CardHeader>
                <div className="flex items-center gap-4">
                  {accessResult.access === 'granted' ? (
                    <UserCheck className="w-12 h-12 text-emerald-400" />
                  ) : (
                    <UserX className="w-12 h-12 text-red-400" />
                  )}
                  <div className="flex-1">
                    <CardTitle className={accessResult.access === 'granted' ? 'text-emerald-400' : 'text-red-400'}>
                      {accessResult.access === 'granted' ? 'ACCESS GRANTED' : 'ACCESS DENIED'}
                    </CardTitle>
                    {accessResult.member && (
                      <p className="text-white mt-1">
                        {accessResult.member.first_name} {accessResult.member.last_name}
                      </p>
                    )}
                    {accessResult.reason && (
                      <p className="text-slate-400 text-sm mt-1">{accessResult.reason}</p>
                    )}
                  </div>
                </div>
              </CardHeader>
            </Card>
          )}

          {/* Access Logs */}
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
            <CardHeader>
              <CardTitle className="text-white">Recent Access Logs</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center text-slate-400 py-8">Loading logs...</div>
              ) : (
                <div className="space-y-3">
                  {accessLogs.map((log) => (
                    <div key={log.id} className="flex items-center justify-between p-3 rounded-lg bg-slate-700/30 hover:bg-slate-700/50 transition-colors" data-testid={`access-log-${log.id}`}>
                      <div className="flex items-center gap-4 flex-1">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${log.status === 'granted' ? 'bg-emerald-500/20' : 'bg-red-500/20'}`}>
                          {log.status === 'granted' ? (
                            <UserCheck className="w-5 h-5 text-emerald-400" />
                          ) : (
                            <UserX className="w-5 h-5 text-red-400" />
                          )}
                        </div>
                        <div className="flex-1">
                          <p className="text-white font-medium">{log.member_name}</p>
                          <p className="text-slate-400 text-sm">{log.access_method.replace('_', ' ')}</p>
                          {log.reason && <p className="text-slate-500 text-xs mt-1">{log.reason}</p>}
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <Badge variant={log.status === 'granted' ? 'default' : 'destructive'}>
                          {log.status}
                        </Badge>
                        <div className="text-right">
                          <p className="text-slate-400 text-sm flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            {new Date(log.timestamp).toLocaleTimeString()}
                          </p>
                          <p className="text-slate-500 text-xs">{new Date(log.timestamp).toLocaleDateString()}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* QR Scanner Dialog */}
          <Dialog open={scanDialogOpen} onOpenChange={setScanDialogOpen}>
            <DialogContent className="bg-slate-800 border-slate-700 text-white">
              <DialogHeader>
                <DialogTitle>Scan QR Code</DialogTitle>
                <DialogDescription className="text-slate-400">
                  For this demo, enter Member ID manually
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <Input
                  placeholder="Enter Member ID from QR"
                  value={manualMemberId}
                  onChange={(e) => setManualMemberId(e.target.value)}
                  className="bg-slate-700/50 border-slate-600 text-white"
                  data-testid="qr-member-id-input"
                />
                <Button
                  onClick={() => {
                    validateAccess(manualMemberId, 'qr_code');
                    setScanDialogOpen(false);
                    setManualMemberId('');
                  }}
                  className="w-full bg-gradient-to-r from-emerald-500 to-teal-600"
                  data-testid="validate-qr-button"
                >
                  Validate Access
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </div>
  );
}
