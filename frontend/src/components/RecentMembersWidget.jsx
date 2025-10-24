import React from 'react';
import { Link } from 'react-router-dom';
import { User, Mail, Phone, Calendar } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';

const RecentMembersList = ({ members, title, period }) => {
  if (!members || members.length === 0) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-slate-400 text-center py-4">
            No members added {period}
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-slate-800 border-slate-700">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-white flex items-center gap-2">
          <User className="w-5 h-5 text-blue-400" />
          {title}
        </CardTitle>
        <Badge variant="secondary" className="bg-blue-500/20 text-blue-400">
          {members.length} member{members.length !== 1 ? 's' : ''}
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="space-y-3 max-h-[400px] overflow-y-auto">
          {members.map((member) => (
            <Link
              key={member.id}
              to={`/members/${member.id}`}
              className="block p-3 bg-slate-700/30 hover:bg-slate-700/50 rounded-lg transition-colors border border-slate-700/50 hover:border-slate-600"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h4 className="text-white font-semibold flex items-center gap-2">
                    {member.full_name}
                    <Badge 
                      variant={
                        member.membership_status === 'active' ? 'default' : 
                        member.membership_status === 'prospect' ? 'secondary' : 
                        'destructive'
                      }
                      className="text-xs"
                    >
                      {member.membership_status}
                    </Badge>
                  </h4>
                  
                  {member.email && (
                    <div className="flex items-center gap-2 mt-1.5">
                      <Mail className="w-3.5 h-3.5 text-slate-400" />
                      <span className="text-sm text-slate-300">{member.email}</span>
                    </div>
                  )}
                  
                  {member.phone && (
                    <div className="flex items-center gap-2 mt-1">
                      <Phone className="w-3.5 h-3.5 text-slate-400" />
                      <span className="text-sm text-slate-300">{member.phone}</span>
                    </div>
                  )}
                  
                  {member.join_date && (
                    <div className="flex items-center gap-2 mt-1">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      <span className="text-xs text-slate-400">
                        Joined: {new Date(member.join_date).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                </div>
                
                <div className="ml-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold text-sm">
                    {member.first_name?.charAt(0)}{member.last_name?.charAt(0)}
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

const RecentMembersWidget = ({ todayMembers, yesterdayMembers }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <RecentMembersList 
        members={todayMembers} 
        title="People Added Today" 
        period="today"
      />
      <RecentMembersList 
        members={yesterdayMembers} 
        title="People Added Yesterday" 
        period="yesterday"
      />
    </div>
  );
};

export default RecentMembersWidget;
