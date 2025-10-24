import React from 'react';
import { AreaChart, Area, ResponsiveContainer, Tooltip } from 'recharts';

const KPISparkline = ({ data, dataKey, title, color = "#8BD139" }) => {
  if (!data || data.length === 0) {
    return (
      <div className="bg-slate-800 rounded-lg p-4">
        <h5 className="text-sm font-semibold text-slate-300 mb-2">{title}</h5>
        <div className="h-16 flex items-center justify-center text-slate-500 text-xs">
          No data available
        </div>
      </div>
    );
  }

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-700 border border-slate-600 rounded px-2 py-1 text-xs">
          <p className="text-white">{payload[0].value}</p>
        </div>
      );
    }
    return null;
  };

  // Get latest value and calculate trend
  const latestValue = data[data.length - 1]?.[dataKey] || 0;
  const previousValue = data[data.length - 2]?.[dataKey] || 0;
  const trend = previousValue > 0 ? ((latestValue - previousValue) / previousValue * 100).toFixed(1) : 0;
  const isPositive = trend >= 0;

  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <div className="flex items-center justify-between mb-2">
        <h5 className="text-sm font-semibold text-slate-300">{title}</h5>
        <div className="flex items-center gap-1">
          <span className="text-xl font-bold" style={{ color: color }}>
            {latestValue}
          </span>
          {trend !== 0 && (
            <span className={`text-xs ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
              {isPositive ? '↑' : '↓'}{Math.abs(trend)}%
            </span>
          )}
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={60}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id={`gradient-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.3}/>
              <stop offset="95%" stopColor={color} stopOpacity={0}/>
            </linearGradient>
          </defs>
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey={dataKey}
            stroke={color}
            fill={`url(#gradient-${dataKey})`}
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

const KPISparklines = ({ kpiData }) => {
  if (!kpiData || kpiData.length === 0) {
    return (
      <div className="bg-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4">Twelve Week KPIs</h3>
        <p className="text-slate-400">No KPI data available</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h3 className="text-lg font-bold text-white mb-6">Twelve Week KPIs</h3>
      
      <div className="space-y-4">
        <KPISparkline
          data={kpiData}
          dataKey="people_registered"
          title="People Registered"
          color="#3b82f6"
        />
        
        <KPISparkline
          data={kpiData}
          dataKey="memberships_started"
          title="Memberships Started"
          color="#8B5CF6"
        />
        
        <KPISparkline
          data={kpiData}
          dataKey="attendance"
          title="Attendance"
          color="#10b981"
        />
        
        <KPISparkline
          data={kpiData}
          dataKey="bookings"
          title="Bookings"
          color="#f59e0b"
        />
        
        <KPISparkline
          data={kpiData}
          dataKey="booking_attendance"
          title="Booking Attendance"
          color="#ef4444"
        />
        
        <KPISparkline
          data={kpiData}
          dataKey="product_sales"
          title="Product Sales (R)"
          color="#06b6d4"
        />
        
        <KPISparkline
          data={kpiData}
          dataKey="tasks"
          title="Tasks"
          color="#ec4899"
        />
      </div>
    </div>
  );
};

export default KPISparklines;
