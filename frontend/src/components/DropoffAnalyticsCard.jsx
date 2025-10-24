import React from 'react';
import { TrendingDown, AlertCircle, BarChart3 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';

const DropoffAnalyticsCard = ({ data, loading = false }) => {
  if (loading) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Dropoff Analytics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-3">
            <div className="h-24 bg-slate-700/50 rounded"></div>
            <div className="h-32 bg-slate-700/50 rounded"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data || data.members_analyzed === 0) {
    return (
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <TrendingDown className="w-5 h-5 text-blue-400" />
            Dropoff Analytics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <BarChart3 className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400">Not enough data to analyze dropoff patterns</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const distribution = data.distribution || {};
  const total = Object.values(distribution).reduce((sum, val) => sum + val, 0);

  const getPercentage = (value) => {
    return total > 0 ? Math.round((value / total) * 100) : 0;
  };

  const distributionData = [
    { label: '0-7 days', value: distribution['0-7_days'] || 0, color: 'bg-red-500' },
    { label: '8-14 days', value: distribution['8-14_days'] || 0, color: 'bg-orange-500' },
    { label: '15-30 days', value: distribution['15-30_days'] || 0, color: 'bg-yellow-500' },
    { label: '31-60 days', value: distribution['31-60_days'] || 0, color: 'bg-blue-500' },
    { label: '60+ days', value: distribution['60+_days'] || 0, color: 'bg-purple-500' }
  ];

  return (
    <Card className="bg-gradient-to-br from-purple-900/20 to-slate-800 border-slate-700">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <TrendingDown className="w-5 h-5 text-purple-400" />
          Attendance Before Dropoff Analytics
        </CardTitle>
        <p className="text-sm text-slate-400 mt-2">
          Analysis of {data.members_analyzed} cancelled memberships (last 90 days)
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Key Insight */}
        <div className="p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-6 h-6 text-purple-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-white font-semibold mb-1">Key Insight</p>
              <p className="text-sm text-slate-300">
                On average, members are inactive for{' '}
                <span className="font-bold text-purple-400">
                  {data.average_days_inactive_before_cancel} days
                </span>{' '}
                before cancelling.
              </p>
              <p className="text-xs text-slate-400 mt-2">
                💡 {data.recommendation}
              </p>
            </div>
          </div>
        </div>

        {/* Distribution Chart */}
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-white">
            Inactive Period Distribution
          </h4>
          {distributionData.map((item) => {
            const percentage = getPercentage(item.value);
            return (
              <div key={item.label} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-300">{item.label}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-slate-400">{item.value} members</span>
                    <Badge variant="secondary" className="bg-slate-700 text-white text-xs">
                      {percentage}%
                    </Badge>
                  </div>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
                  <div
                    className={`${item.color} h-full rounded-full transition-all duration-500`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>

        {/* Stats Summary */}
        <div className="grid grid-cols-3 gap-4 pt-4 border-t border-slate-700">
          <div className="text-center">
            <p className="text-2xl font-bold text-white">{data.total_cancelled_members}</p>
            <p className="text-xs text-slate-400 mt-1">Total Cancelled</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-purple-400">{data.members_analyzed}</p>
            <p className="text-xs text-slate-400 mt-1">Analyzed</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-orange-400">
              {data.average_days_inactive_before_cancel}
            </p>
            <p className="text-xs text-slate-400 mt-1">Avg Days Inactive</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default DropoffAnalyticsCard;
