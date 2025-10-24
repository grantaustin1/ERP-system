import React from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, User, Phone, Mail, Clock, TrendingDown } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';

const RiskBadge = ({ level }) => {
  const config = {
    critical: { color: 'bg-red-500/20 text-red-400 border-red-500/50', label: 'Critical Risk' },
    high: { color: 'bg-orange-500/20 text-orange-400 border-orange-500/50', label: 'High Risk' },
    medium: { color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50', label: 'Medium Risk' }
  };
  
  const { color, label } = config[level] || config.medium;
  
  return (
    <Badge className={`${color} border`}>
      {label}
    </Badge>
  );
};

const AtRiskMemberCard = ({ member }) => {
  return (
    <div className="p-4 bg-slate-700/30 hover:bg-slate-700/50 rounded-lg transition-colors border border-slate-700/50 hover:border-slate-600">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-red-500 to-orange-600 flex items-center justify-center text-white font-semibold">
            {member.first_name?.charAt(0)}{member.last_name?.charAt(0)}
          </div>
          <div>
            <Link
              to={`/members/${member.id}`}
              className="text-white font-semibold hover:text-blue-400 transition-colors"
            >
              {member.full_name}
            </Link>
            <div className="flex items-center gap-2 mt-1">
              <RiskBadge level={member.risk_level} />
              <span className="text-xs text-slate-400">Score: {member.risk_score}</span>
            </div>
          </div>
        </div>
        <Link to={`/members/${member.id}`}>
          <Button size="sm" variant="outline" className="border-blue-500 text-blue-400 hover:bg-blue-500/10">
            View Profile
          </Button>
        </Link>
      </div>
      
      <div className="space-y-2 mb-3">
        {member.email && (
          <div className="flex items-center gap-2 text-sm">
            <Mail className="w-4 h-4 text-slate-400" />
            <span className="text-slate-300">{member.email}</span>
          </div>
        )}
        {member.phone && (
          <div className="flex items-center gap-2 text-sm">
            <Phone className="w-4 h-4 text-slate-400" />
            <span className="text-slate-300">{member.phone}</span>
          </div>
        )}
        {member.days_since_visit !== null && member.days_since_visit !== undefined && (
          <div className="flex items-center gap-2 text-sm">
            <Clock className="w-4 h-4 text-slate-400" />
            <span className="text-slate-300">
              Last visit: {member.days_since_visit} days ago
            </span>
          </div>
        )}
      </div>
      
      <div className="pt-3 border-t border-slate-700">
        <p className="text-xs text-slate-400 mb-2">Risk Factors:</p>
        <div className="flex flex-wrap gap-1.5">
          {member.risk_factors?.map((factor, index) => (
            <Badge
              key={index}
              variant="outline"
              className="text-xs border-slate-600 text-slate-300"
            >
              {factor}
            </Badge>
          ))}
        </div>
      </div>
    </div>
  );
};

const AtRiskMembersWidget = ({ data, loading = false }) => {
  if (loading) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            At-Risk Members
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 bg-slate-700/50 rounded"></div>
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
            <AlertTriangle className="w-5 h-5 text-green-400" />
            At-Risk Members
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <TrendingDown className="w-12 h-12 text-green-400 mx-auto mb-3 opacity-50" />
            <p className="text-slate-300 font-semibold">Great News!</p>
            <p className="text-slate-400 text-sm mt-1">No members currently at risk</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Show top 5 most at-risk members
  const topRiskMembers = data.members.slice(0, 5);

  return (
    <Card className="bg-gradient-to-br from-red-900/20 to-slate-800 border-slate-700">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-white flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            At-Risk Members
          </CardTitle>
          <div className="flex gap-2">
            <Badge className="bg-red-500/20 text-red-400 border-red-500/50 border">
              {data.critical} Critical
            </Badge>
            <Badge className="bg-orange-500/20 text-orange-400 border-orange-500/50 border">
              {data.high} High
            </Badge>
            <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/50 border">
              {data.medium} Medium
            </Badge>
          </div>
        </div>
        <p className="text-sm text-slate-400 mt-2">
          {data.total} members need attention • Showing top 5 highest risk
        </p>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {topRiskMembers.map((member) => (
            <AtRiskMemberCard key={member.id} member={member} />
          ))}
        </div>
        {data.total > 5 && (
          <div className="mt-4 text-center">
            <Link to="/retention">
              <Button variant="outline" className="border-slate-600 text-white hover:bg-slate-700">
                View All {data.total} At-Risk Members
              </Button>
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AtRiskMembersWidget;
