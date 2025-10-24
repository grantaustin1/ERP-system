import React from 'react';
import { Link } from 'react-router-dom';
import { Calendar, Clock, AlertCircle, User } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from './ui/table';

const ExpiringMembershipsTable = ({ data, period, loading = false }) => {
  const periodLabel = {
    30: 'Next 30 Days',
    60: 'Next 60 Days',
    90: 'Next 90 Days'
  };

  if (loading) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">
            Memberships Expiring in {periodLabel[period] || 'Next 30 Days'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-slate-700/50 rounded"></div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data || !data.members || data.members.length === 0) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Calendar className="w-5 h-5 text-green-400" />
            Memberships Expiring in {periodLabel[period] || 'Next 30 Days'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Calendar className="w-12 h-12 text-green-400 mx-auto mb-3 opacity-50" />
            <p className="text-slate-300">No memberships expiring in this period</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const getUrgencyColor = (days) => {
    if (days <= 7) return 'text-red-400';
    if (days <= 14) return 'text-orange-400';
    if (days <= 30) return 'text-yellow-400';
    return 'text-blue-400';
  };

  const getUrgencyBadge = (days) => {
    if (days <= 7) return <Badge className="bg-red-500/20 text-red-400 border-red-500/50 border">Urgent</Badge>;
    if (days <= 14) return <Badge className="bg-orange-500/20 text-orange-400 border-orange-500/50 border">Soon</Badge>;
    return <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/50 border">Upcoming</Badge>;
  };

  return (
    <Card className="bg-slate-800 border-slate-700">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-white flex items-center gap-2">
            <Calendar className="w-5 h-5 text-blue-400" />
            Memberships Expiring in {periodLabel[period] || 'Next 30 Days'}
          </CardTitle>
          <Badge variant="secondary" className="bg-blue-500/20 text-blue-400">
            {data.total} members
          </Badge>
        </div>
        <p className="text-sm text-slate-400 mt-2">
          Proactive renewal outreach opportunity
        </p>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="border-slate-700">
                <TableHead className="text-slate-300">Member</TableHead>
                <TableHead className="text-slate-300">Contact</TableHead>
                <TableHead className="text-slate-300">Expiry Date</TableHead>
                <TableHead className="text-slate-300">Days Left</TableHead>
                <TableHead className="text-slate-300">Last Visit</TableHead>
                <TableHead className="text-slate-300">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.members.map((member) => (
                <TableRow key={member.id} className="border-slate-700 hover:bg-slate-700/30">
                  <TableCell>
                    <Link
                      to={`/members/${member.id}`}
                      className="flex items-center gap-2 text-white hover:text-blue-400 transition-colors"
                    >
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-semibold">
                        {member.first_name?.charAt(0)}{member.last_name?.charAt(0)}
                      </div>
                      <span className="font-medium">{member.full_name}</span>
                    </Link>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      {member.email && (
                        <div className="text-sm text-slate-300">{member.email}</div>
                      )}
                      {member.phone && (
                        <div className="text-xs text-slate-400">{member.phone}</div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-slate-300">
                    {new Date(member.expiry_date).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <span className={`font-semibold ${getUrgencyColor(member.days_until_expiry)}`}>
                      {member.days_until_expiry} days
                    </span>
                  </TableCell>
                  <TableCell className="text-slate-400 text-sm">
                    {member.last_visit_date 
                      ? new Date(member.last_visit_date).toLocaleDateString()
                      : 'No visits'
                    }
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-col gap-1">
                      {getUrgencyBadge(member.days_until_expiry)}
                      {member.is_debtor && (
                        <Badge variant="destructive" className="text-xs">
                          Debtor
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
};

export default ExpiringMembershipsTable;
