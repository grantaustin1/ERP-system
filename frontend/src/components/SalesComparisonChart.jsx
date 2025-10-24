import React from 'react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const SalesComparisonChart = ({ data, monthlyTarget, currentMonthName }) => {
  if (!data || data.length === 0) {
    return (
      <div className="w-full h-[400px] bg-slate-800 rounded-lg flex items-center justify-center">
        <span className="text-slate-400">No sales data available</span>
      </div>
    );
  }

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const date = new Date(label);
      return (
        <div className="bg-slate-700 border border-slate-600 rounded-lg p-3 shadow-lg">
          <p className="text-white font-semibold mb-2">
            {date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          </p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: R{entry.value ? entry.value.toFixed(0) : 0}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-[400px] bg-slate-800 rounded-lg p-4">
      <div className="mb-4">
        <h3 className="text-xl font-bold text-white">MEMBERSHIP SALES THIS MONTH</h3>
        <p className="text-sm text-slate-400">
          {currentMonthName} - Target: R{monthlyTarget?.toLocaleString() || '0'}
        </p>
      </div>
      
      <ResponsiveContainer width="100%" height="85%">
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis 
            dataKey="day" 
            stroke="#94a3b8"
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            stroke="#94a3b8"
            style={{ fontSize: '12px' }}
            tickFormatter={(value) => `R${(value / 1000).toFixed(0)}k`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="line"
          />
          
          {/* Target - Area */}
          <Area
            type="monotone"
            dataKey="Target"
            stroke="#888888"
            fill="#888888"
            fillOpacity={0.06}
            strokeWidth={1}
            name="Target"
          />
          
          {/* Previous Month - Line */}
          <Line
            type="monotone"
            dataKey="PrevMonthSales"
            stroke="#999999"
            strokeWidth={3}
            dot={false}
            name="Previous Month"
          />
          
          {/* Last Year - Line */}
          <Line
            type="monotone"
            dataKey="LastYearSales"
            stroke="#cccccc"
            strokeWidth={3}
            dot={false}
            name="Last Year"
          />
          
          {/* Current Month Sales - Line */}
          <Line
            type="monotone"
            dataKey="MonthSales"
            stroke="#8BD139"
            strokeWidth={5}
            dot={false}
            name="Membership Sales"
          />
        </LineChart>
      </ResponsiveContainer>
      
      <div className="mt-4 text-xs text-slate-400 text-center">
        Membership Sales This Month is updated hourly
      </div>
    </div>
  );
};

export default SalesComparisonChart;
