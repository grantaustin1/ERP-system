import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BarChart3, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Bar, Line, Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const API = process.env.REACT_APP_BACKEND_URL || '';

const ChartSelector = ({ dateRange }) => {
  const [selectedChart, setSelectedChart] = useState('age-distribution');
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);

  const chartOptions = [
    { value: 'age-distribution', label: 'Age Distribution Analysis', type: 'bar' },
    { value: 'membership-duration', label: 'Average Membership Duration', type: 'bar' },
    { value: 'attendance-by-day', label: 'Attendance by Day of Week', type: 'bar' },
    { value: 'top-referrers', label: 'Top Referring Members', type: 'bar' },
    { value: 'member-sources', label: 'Member Acquisition Sources', type: 'pie' },
  ];

  useEffect(() => {
    fetchChartData(selectedChart);
  }, [selectedChart]);

  const fetchChartData = async (chartType) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/charts/${chartType}`);
      setChartData(response.data);
    } catch (error) {
      console.error(`Failed to fetch ${chartType} data:`, error);
    } finally {
      setLoading(false);
    }
  };

  const renderChart = () => {
    if (loading) {
      return (
        <div className="h-96 flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      );
    }

    if (!chartData || !chartData.data || chartData.data.length === 0) {
      return (
        <div className="h-96 flex flex-col items-center justify-center text-slate-400">
          <BarChart3 className="w-16 h-16 mb-4 opacity-50" />
          <p>No data available for this chart</p>
        </div>
      );
    }

    const currentChartOption = chartOptions.find(opt => opt.value === selectedChart);

    switch (selectedChart) {
      case 'age-distribution':
        return renderBarChart(
          chartData.data.map(d => d.category),
          chartData.data.map(d => d.value),
          'Members by Age Range',
          '#3b82f6'
        );

      case 'membership-duration':
        return renderBarChart(
          chartData.data.map(d => d.membership_type),
          chartData.data.map(d => d.average_duration_months),
          'Average Duration (Months)',
          '#8b5cf6'
        );

      case 'attendance-by-day':
        return renderBarChart(
          chartData.data.map(d => d.day),
          chartData.data.map(d => d.count),
          'Attendance Count',
          '#10b981'
        );

      case 'top-referrers':
        return renderBarChart(
          chartData.data.map(d => d.referrer_name),
          chartData.data.map(d => d.referral_count),
          'Referrals Made',
          '#f59e0b'
        );

      case 'member-sources':
        return renderPieChart(
          chartData.data.map(d => d.source),
          chartData.data.map(d => d.count)
        );

      default:
        return null;
    }
  };

  const renderBarChart = (labels, data, label, color) => {
    const config = {
      labels: labels,
      datasets: [
        {
          label: label,
          data: data,
          backgroundColor: color,
          borderColor: color,
          borderWidth: 1,
        },
      ],
    };

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          labels: {
            color: '#e2e8f0',
          },
        },
        tooltip: {
          backgroundColor: '#1e293b',
          titleColor: '#e2e8f0',
          bodyColor: '#e2e8f0',
        },
      },
      scales: {
        x: {
          ticks: {
            color: '#94a3b8',
          },
          grid: {
            color: '#334155',
          },
        },
        y: {
          ticks: {
            color: '#94a3b8',
          },
          grid: {
            color: '#334155',
          },
        },
      },
    };

    return (
      <div className="h-96">
        <Bar data={config} options={options} />
      </div>
    );
  };

  const renderPieChart = (labels, data) => {
    const colors = [
      '#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444',
      '#06b6d4', '#ec4899', '#14b8a6', '#f97316', '#6366f1'
    ];

    const config = {
      labels: labels,
      datasets: [
        {
          data: data,
          backgroundColor: colors.slice(0, data.length),
          borderColor: '#1e293b',
          borderWidth: 2,
        },
      ],
    };

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: {
            color: '#e2e8f0',
            padding: 15,
          },
        },
        tooltip: {
          backgroundColor: '#1e293b',
          titleColor: '#e2e8f0',
          bodyColor: '#e2e8f0',
        },
      },
    };

    return (
      <div className="h-96">
        <Pie data={config} options={options} />
      </div>
    );
  };

  const getChartDescription = () => {
    switch (selectedChart) {
      case 'age-distribution':
        return `Distribution of ${chartData?.total_members || 0} active members across age ranges`;
      case 'membership-duration':
        return `Average membership duration by membership type`;
      case 'attendance-by-day':
        return `Total attendance: ${chartData?.total_attendance || 0} visits in last 30 days`;
      case 'top-referrers':
        return `${chartData?.total_referrals || 0} total referrals from ${chartData?.total_referrers || 0} members`;
      case 'member-sources':
        return `Distribution of ${chartData?.total_members || 0} members by acquisition source`;
      default:
        return '';
    }
  };

  return (
    <Card className="bg-slate-800 border-slate-700">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-white flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-400" />
            Analytics & Charts
          </CardTitle>
          <div className="w-80">
            <Select value={selectedChart} onValueChange={setSelectedChart}>
              <SelectTrigger className="bg-slate-700/50 border-slate-600 text-white">
                <SelectValue placeholder="Select chart" />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-700">
                {chartOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value} className="text-white">
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        {chartData && (
          <p className="text-sm text-slate-400 mt-2">
            {getChartDescription()}
          </p>
        )}
      </CardHeader>
      <CardContent>
        {renderChart()}
      </CardContent>
    </Card>
  );
};

export default ChartSelector;
