import React from 'react';
import { Link } from 'react-router-dom';
import { Bell, Clock, User, Mail, Phone } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';

const RetentionAlertsWidget = ({ alerts7, alerts14, alerts28, loading = false }) => {
  if (loading) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Retention Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 bg-slate-700/50 rounded"></div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const renderMemberList = (data, days) => {
    if (!data || !data.members || data.members.length === 0) {
      return (
        <div className="text-center py-8">
          <Bell className="w-12 h-12 text-green-400 mx-auto mb-3 opacity-50" />
          <p className="text-slate-300">No alerts for {days} days</p>
          <p className="text-sm text-slate-400 mt-1">All members are active!</p>
        </div>
      );
    }

    return (
      <div className="space-y-3">
        <p className="text-sm text-slate-400 mb-3">
          {data.total} members haven't visited in {days}+ days
        </p>
        {data.members.slice(0, 5).map((member) => (
          <div
            key={member.id}
            className="p-3 bg-slate-700/30 hover:bg-slate-700/50 rounded-lg border border-slate-700/50 hover:border-slate-600 transition-colors"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-orange-500 to-red-600 flex items-center justify-center text-white font-semibold text-sm">
                  {member.first_name?.charAt(0)}{member.last_name?.charAt(0)}
                </div>
                <div>
                  <Link
                    to={`/members/${member.id}`}
                    className="text-white font-medium hover:text-blue-400 transition-colors"
                  >
                    {member.full_name}
                  </Link>
                  <div className="flex items-center gap-2 mt-1">
                    {member.days_since_visit ? (
                      <span className="text-xs text-orange-400 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {member.days_since_visit} days ago
                      </span>
                    ) : (
                      <span className="text-xs text-red-400">No visits recorded</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
            <div className="mt-2 space-y-1">
              {member.email && (
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <Mail className="w-3 h-3" />
                  {member.email}
                </div>
              )}
              {member.phone && (
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <Phone className="w-3 h-3" />
                  {member.phone}
                </div>
              )}
            </div>
          </div>
        ))}
        {data.total > 5 && (
          <p className="text-sm text-slate-400 text-center pt-2">
            + {data.total - 5} more members
          </p>
        )}
      </div>
    );
  };

  return (
    <Card className="bg-slate-800 border-slate-700">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Bell className="w-5 h-5 text-orange-400" />
          Retention Alerts
        </CardTitle>
        <p className="text-sm text-slate-400 mt-2">
          Members who haven't visited recently
        </p>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="7" className="w-full">
          <TabsList className="grid w-full grid-cols-3 bg-slate-700/50">
            <TabsTrigger value="7" className="data-[state=active]:bg-slate-600">
              7 Days
              {alerts7?.total > 0 && (
                <Badge className="ml-2 bg-red-500 text-white" variant="destructive">
                  {alerts7.total}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="14" className="data-[state=active]:bg-slate-600">
              14 Days
              {alerts14?.total > 0 && (
                <Badge className="ml-2 bg-orange-500 text-white">
                  {alerts14.total}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="28" className="data-[state=active]:bg-slate-600">
              28 Days
              {alerts28?.total > 0 && (
                <Badge className="ml-2 bg-yellow-500 text-white">
                  {alerts28.total}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="7" className="mt-4">
            {renderMemberList(alerts7, 7)}
          </TabsContent>
          
          <TabsContent value="14" className="mt-4">
            {renderMemberList(alerts14, 14)}
          </TabsContent>
          
          <TabsContent value="28" className="mt-4">
            {renderMemberList(alerts28, 28)}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default RetentionAlertsWidget;
