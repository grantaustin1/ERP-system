import React from 'react';
import { TrendingUp, TrendingDown, Minus, Users } from 'lucide-react';

const RetentionIndicator = ({ retention }) => {
  if (!retention) return null;
  
  const { status, percentage_change, current_month_visits, previous_month_visits } = retention;
  
  const getStatusConfig = () => {
    switch (status) {
      case 'good':
        return {
          bgColor: 'bg-green-500/20',
          textColor: 'text-green-400',
          borderColor: 'border-green-500/50',
          icon: TrendingUp,
          label: 'GOOD'
        };
      case 'consistent':
        return {
          bgColor: 'bg-gray-500/20',
          textColor: 'text-gray-400',
          borderColor: 'border-gray-500/50',
          icon: Minus,
          label: 'CONSISTENT'
        };
      case 'alert':
        return {
          bgColor: 'bg-orange-500/20',
          textColor: 'text-orange-400',
          borderColor: 'border-orange-500/50',
          icon: TrendingDown,
          label: 'ALERT'
        };
      case 'critical':
        return {
          bgColor: 'bg-red-500/20',
          textColor: 'text-red-400',
          borderColor: 'border-red-500/50',
          icon: TrendingDown,
          label: 'ALERT'
        };
      case 'collating':
      default:
        return {
          bgColor: 'bg-blue-500/20',
          textColor: 'text-blue-400',
          borderColor: 'border-blue-500/50',
          icon: Users,
          label: 'COLLATING'
        };
    }
  };
  
  const config = getStatusConfig();
  const Icon = config.icon;
  
  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border ${config.bgColor} ${config.borderColor}`}>
      <Icon className={`w-4 h-4 ${config.textColor}`} />
      <div className="flex items-center gap-1">
        <span className={`text-xs font-semibold ${config.textColor}`}>
          {config.label}
        </span>
        {status !== 'collating' && percentage_change !== 0 && (
          <span className={`text-xs font-bold ${config.textColor}`}>
            {percentage_change > 0 ? '+' : ''}{percentage_change}%
          </span>
        )}
      </div>
      <span className="text-xs text-gray-400">
        {current_month_visits} visits this month
      </span>
    </div>
  );
};

export default RetentionIndicator;
