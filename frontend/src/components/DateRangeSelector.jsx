import React, { useState, useEffect } from 'react';
import { Calendar } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Input } from './ui/input';
import { Label } from './ui/label';

const DateRangeSelector = ({ onRangeChange, initialRange = 'last_30_days' }) => {
  const [selectedPeriod, setSelectedPeriod] = useState(initialRange);
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');

  // Calculate date ranges based on selected period
  const getDateRange = (period) => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    
    switch (period) {
      case 'today':
        return {
          start: today.toISOString().split('T')[0],
          end: today.toISOString().split('T')[0],
          label: 'Today'
        };
      
      case 'yesterday':
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        return {
          start: yesterday.toISOString().split('T')[0],
          end: yesterday.toISOString().split('T')[0],
          label: 'Yesterday'
        };
      
      case 'this_week':
        const startOfWeek = new Date(today);
        startOfWeek.setDate(today.getDate() - today.getDay());
        return {
          start: startOfWeek.toISOString().split('T')[0],
          end: today.toISOString().split('T')[0],
          label: 'This Week'
        };
      
      case 'last_week':
        const lastWeekStart = new Date(today);
        lastWeekStart.setDate(today.getDate() - today.getDay() - 7);
        const lastWeekEnd = new Date(lastWeekStart);
        lastWeekEnd.setDate(lastWeekStart.getDate() + 6);
        return {
          start: lastWeekStart.toISOString().split('T')[0],
          end: lastWeekEnd.toISOString().split('T')[0],
          label: 'Last Week'
        };
      
      case 'last_7_days':
        const last7 = new Date(today);
        last7.setDate(today.getDate() - 7);
        return {
          start: last7.toISOString().split('T')[0],
          end: today.toISOString().split('T')[0],
          label: 'Last 7 Days'
        };
      
      case 'last_14_days':
        const last14 = new Date(today);
        last14.setDate(today.getDate() - 14);
        return {
          start: last14.toISOString().split('T')[0],
          end: today.toISOString().split('T')[0],
          label: 'Last 14 Days'
        };
      
      case 'last_30_days':
        const last30 = new Date(today);
        last30.setDate(today.getDate() - 30);
        return {
          start: last30.toISOString().split('T')[0],
          end: today.toISOString().split('T')[0],
          label: 'Last 30 Days'
        };
      
      case 'this_month':
        const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
        return {
          start: monthStart.toISOString().split('T')[0],
          end: today.toISOString().split('T')[0],
          label: 'This Month'
        };
      
      case 'last_month':
        const lastMonthStart = new Date(now.getFullYear(), now.getMonth() - 1, 1);
        const lastMonthEnd = new Date(now.getFullYear(), now.getMonth(), 0);
        return {
          start: lastMonthStart.toISOString().split('T')[0],
          end: lastMonthEnd.toISOString().split('T')[0],
          label: 'Last Month'
        };
      
      case 'this_quarter':
        const quarterStart = new Date(now.getFullYear(), Math.floor(now.getMonth() / 3) * 3, 1);
        return {
          start: quarterStart.toISOString().split('T')[0],
          end: today.toISOString().split('T')[0],
          label: 'This Quarter'
        };
      
      case 'ytd':
        const yearStart = new Date(now.getFullYear(), 0, 1);
        return {
          start: yearStart.toISOString().split('T')[0],
          end: today.toISOString().split('T')[0],
          label: 'Year to Date'
        };
      
      case 'last_year':
        const lastYearStart = new Date(now.getFullYear() - 1, 0, 1);
        const lastYearEnd = new Date(now.getFullYear() - 1, 11, 31);
        return {
          start: lastYearStart.toISOString().split('T')[0],
          end: lastYearEnd.toISOString().split('T')[0],
          label: String(now.getFullYear() - 1)
        };
      
      case 'custom':
        return {
          start: customStart,
          end: customEnd,
          label: 'Custom Range'
        };
      
      default:
        return getDateRange('last_30_days');
    }
  };

  // Handle period change
  const handlePeriodChange = (value) => {
    setSelectedPeriod(value);
    if (value !== 'custom') {
      const range = getDateRange(value);
      onRangeChange(range);
    }
  };

  // Handle custom date changes
  useEffect(() => {
    if (selectedPeriod === 'custom' && customStart && customEnd) {
      onRangeChange({
        start: customStart,
        end: customEnd,
        label: 'Custom Range'
      });
    }
  }, [customStart, customEnd, selectedPeriod]);

  // Initialize with default range
  useEffect(() => {
    const range = getDateRange(initialRange);
    onRangeChange(range);
  }, []);

  return (
    <div className="flex flex-wrap items-end gap-4">
      <div className="flex-1 min-w-[200px]">
        <Label className="text-slate-300 mb-2">Period</Label>
        <Select value={selectedPeriod} onValueChange={handlePeriodChange}>
          <SelectTrigger className="bg-slate-700/50 border-slate-600 text-white">
            <SelectValue placeholder="Select period" />
          </SelectTrigger>
          <SelectContent className="bg-slate-800 border-slate-700">
            <SelectItem value="today" className="text-white">Today</SelectItem>
            <SelectItem value="yesterday" className="text-white">Yesterday</SelectItem>
            <SelectItem value="this_week" className="text-white">This Week</SelectItem>
            <SelectItem value="last_week" className="text-white">Last Week</SelectItem>
            <SelectItem value="last_7_days" className="text-white">Last 7 Days</SelectItem>
            <SelectItem value="last_14_days" className="text-white">Last 14 Days</SelectItem>
            <SelectItem value="last_30_days" className="text-white">Last 30 Days</SelectItem>
            <SelectItem value="this_month" className="text-white">This Month</SelectItem>
            <SelectItem value="last_month" className="text-white">Last Month</SelectItem>
            <SelectItem value="this_quarter" className="text-white">This Quarter</SelectItem>
            <SelectItem value="ytd" className="text-white">Year to Date</SelectItem>
            <SelectItem value="last_year" className="text-white">{new Date().getFullYear() - 1}</SelectItem>
            <SelectItem value="custom" className="text-white">Custom Range</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {selectedPeriod === 'custom' && (
        <>
          <div className="flex-1 min-w-[140px]">
            <Label className="text-slate-300 mb-2">Start Date</Label>
            <Input
              type="date"
              value={customStart}
              onChange={(e) => setCustomStart(e.target.value)}
              className="bg-slate-700/50 border-slate-600 text-white"
            />
          </div>
          <div className="flex-1 min-w-[140px]">
            <Label className="text-slate-300 mb-2">End Date</Label>
            <Input
              type="date"
              value={customEnd}
              onChange={(e) => setCustomEnd(e.target.value)}
              className="bg-slate-700/50 border-slate-600 text-white"
            />
          </div>
        </>
      )}
    </div>
  );
};

export default DateRangeSelector;
