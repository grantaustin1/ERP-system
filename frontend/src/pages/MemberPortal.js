import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API } from '@/App';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArrowLeft, QrCode, FileText, Calendar, CreditCard } from 'lucide-react';
import { toast } from 'sonner';

export default function MemberPortal() {
  const [member, setMember] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [memberId] = useState('demo-member-id'); // In production, this would come from auth
  const navigate = useNavigate();

  useEffect(() => {
    // For demo purposes - in production, member would be authenticated
    toast.info('Member Portal - Demo Mode');
    setLoading(false);
  }, []);

  return (
    <div className="min-h-screen p-8" style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)' }}>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <Button
            variant="outline"
            onClick={() => navigate('/login')}
            className="mb-4 border-slate-600 text-slate-300 hover:bg-slate-700"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Login
          </Button>
          <h1 className="text-4xl font-bold text-white mb-2">Member Portal</h1>
          <p className="text-slate-400">Access your membership information and QR code</p>
        </div>

        {/* Demo Notice */}
        <Card className="bg-blue-900/20 border-blue-500 mb-8">
          <CardContent className="pt-6">
            <p className="text-blue-200">
              <strong>Demo Mode:</strong> This is a demonstration of the member portal. In production, members would log in to view their personal QR code, invoices, and membership details.
            </p>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* QR Code Card */}
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <QrCode className="w-5 h-5" />
                Your QR Code
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col items-center space-y-4">
                <div className="bg-white p-4 rounded-lg">
                  <div className="w-48 h-48 bg-slate-200 flex items-center justify-center">
                    <p className="text-slate-600 text-sm text-center">QR Code<br />appears here<br />after login</p>
                  </div>
                </div>
                <p className="text-sm text-slate-400 text-center">
                  Show this QR code at the gym entrance for access
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Membership Details */}
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Calendar className="w-5 h-5" />
                Membership Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-slate-400 text-sm">Membership Type</p>
                <p className="text-white font-semibold">Premium Monthly</p>
              </div>
              <div>
                <p className="text-slate-400 text-sm">Status</p>
                <Badge className="mt-1">Active</Badge>
              </div>
              <div>
                <p className="text-slate-400 text-sm">Join Date</p>
                <p className="text-white">January 1, 2024</p>
              </div>
              <div>
                <p className="text-slate-400 text-sm">Expiry Date</p>
                <p className="text-white">December 31, 2024</p>
              </div>
            </CardContent>
          </Card>

          {/* Payment History */}
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg md:col-span-2">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <CreditCard className="w-5 h-5" />
                Payment History
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="p-3 rounded-lg bg-slate-700/30">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-white font-medium">Monthly Membership</p>
                      <p className="text-slate-400 text-sm">December 2024</p>
                    </div>
                    <div className="text-right">
                      <p className="text-white font-bold">R 599.00</p>
                      <Badge variant="default" className="mt-1">Paid</Badge>
                    </div>
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-slate-700/30">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-white font-medium">Monthly Membership</p>
                      <p className="text-slate-400 text-sm">November 2024</p>
                    </div>
                    <div className="text-right">
                      <p className="text-white font-bold">R 599.00</p>
                      <Badge variant="default" className="mt-1">Paid</Badge>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
