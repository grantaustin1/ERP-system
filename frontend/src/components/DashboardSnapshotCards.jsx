import React from 'react';
import { Users, UserPlus, Activity, TrendingUp, TrendingDown } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

const StatCard = ({ title, value, icon: Icon, className = "" }) => (
  <div className={`flex items-center justify-between ${className}`}>
    <div>
      <p className="text-sm text-slate-400">{title}</p>
      <p className="text-2xl font-bold text-white mt-1">{value}</p>
    </div>
    {Icon && (
      <div className="p-3 bg-slate-700/50 rounded-lg">
        <Icon className="w-6 h-6 text-blue-400" />
      </div>
    )}
  </div>
);

const GrowthIndicator = ({ value, label }) => {
  const isPositive = value >= 0;
  const Icon = isPositive ? TrendingUp : TrendingDown;
  const colorClass = isPositive ? 'text-green-400' : 'text-red-400';
  const bgClass = isPositive ? 'bg-green-500/10' : 'bg-red-500/10';
  
  return (
    <div className="flex items-center gap-2">
      <div className={`flex items-center gap-1 px-2 py-1 rounded ${bgClass}`}>
        <Icon className={`w-4 h-4 ${colorClass}`} />
        <span className={`text-sm font-semibold ${colorClass}`}>
          {value > 0 ? '+' : ''}{value}%
        </span>
      </div>
      <span className="text-xs text-slate-400">{label}</span>
    </div>
  );
};

const DashboardSnapshotCards = ({ snapshotData }) => {
  if (!snapshotData) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Loading...</CardTitle>
            </CardHeader>
            <CardContent className="animate-pulse">
              <div className="h-20 bg-slate-700/50 rounded"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const { today, yesterday, growth } = snapshotData;

  return (
    <div className="space-y-6">
      {/* Today vs Yesterday Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Today Card */}
        <Card className="bg-gradient-to-br from-blue-900/20 to-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-xl text-white flex items-center gap-2">
              <Users className="w-5 h-5 text-blue-400" />
              Today
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <StatCard 
              title="People Registered" 
              value={today.registered}
              icon={UserPlus}
            />
            <StatCard 
              title="Memberships Commenced" 
              value={today.commenced}
              icon={Users}
            />
            <StatCard 
              title="Member Attendance" 
              value={today.attendance}
              icon={Activity}
            />
          </CardContent>
        </Card>

        {/* Yesterday Card */}
        <Card className="bg-gradient-to-br from-purple-900/20 to-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-xl text-white flex items-center gap-2">
              <Users className="w-5 h-5 text-purple-400" />
              Yesterday
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <StatCard 
              title="People Registered" 
              value={yesterday.registered}
            />
            <StatCard 
              title="Memberships Commenced" 
              value={yesterday.commenced}
            />
            <StatCard 
              title="Member Attendance" 
              value={yesterday.attendance}
            />
          </CardContent>
        </Card>

        {/* Growth Card */}
        <Card className="bg-gradient-to-br from-emerald-900/20 to-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-xl text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              Growth (Last 30 Days)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-slate-400 mb-2">Memberships Sold</p>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-2xl font-bold text-white">{growth.memberships_sold_30d}</p>
                  <p className="text-xs text-slate-500">vs {growth.memberships_sold_last_year} last year</p>
                </div>
                <GrowthIndicator value={growth.memberships_growth} label="" />
              </div>
            </div>
            
            <div>
              <p className="text-sm text-slate-400 mb-2">Net Gain</p>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-2xl font-bold text-white">{growth.net_gain_30d}</p>
                  <p className="text-xs text-slate-500">vs {growth.net_gain_last_year} last year</p>
                </div>
                <GrowthIndicator value={growth.net_gain_growth} label="" />
              </div>
            </div>
            
            <div>
              <p className="text-sm text-slate-400 mb-2">Attendance</p>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-2xl font-bold text-white">{growth.attendance_30d}</p>
                  <p className="text-xs text-slate-500">vs {growth.attendance_last_year} last year</p>
                </div>
                <GrowthIndicator value={growth.attendance_growth} label="" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Additional Growth Metrics Summary */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">30-Day Performance Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-1">
              <p className="text-xs text-slate-400">Memberships Sold</p>
              <p className="text-lg font-semibold text-white">{growth.memberships_sold_30d}</p>
              <GrowthIndicator value={growth.memberships_growth} label="vs last year" />
            </div>
            <div className="space-y-1">
              <p className="text-xs text-slate-400">Memberships Expired</p>
              <p className="text-lg font-semibold text-white">{growth.memberships_expired_30d}</p>
              <GrowthIndicator value={growth.expired_growth} label="vs last year" />
            </div>
            <div className="space-y-1">
              <p className="text-xs text-slate-400">Net Gain</p>
              <p className="text-lg font-semibold text-white">{growth.net_gain_30d}</p>
              <GrowthIndicator value={growth.net_gain_growth} label="vs last year" />
            </div>
            <div className="space-y-1">
              <p className="text-xs text-slate-400">Total Attendance</p>
              <p className="text-lg font-semibold text-white">{growth.attendance_30d}</p>
              <GrowthIndicator value={growth.attendance_growth} label="vs last year" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DashboardSnapshotCards;
