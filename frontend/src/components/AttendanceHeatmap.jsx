import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Calendar, TrendingUp, Users } from 'lucide-react';
import { toast } from 'sonner';

export default function AttendanceHeatmap() {
  const [heatmapData, setHeatmapData] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [hoveredCell, setHoveredCell] = useState(null);

  useEffect(() => {
    // Set default date range (last 30 days)
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);
    
    setEndDate(end.toISOString().split('T')[0]);
    setStartDate(start.toISOString().split('T')[0]);
  }, []);

  useEffect(() => {
    if (startDate && endDate) {
      fetchHeatmapData();
    }
  }, [startDate, endDate]);

  const fetchHeatmapData = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/attendance/heatmap`, {
        params: {
          start_date: new Date(startDate).toISOString(),
          end_date: new Date(endDate).toISOString()
        }
      });
      
      setHeatmapData(response.data.heatmap);
      setStats(response.data.stats);
    } catch (error) {
      console.error('Failed to fetch heatmap data:', error);
      toast.error('Failed to load attendance heatmap');
    } finally {
      setLoading(false);
    }
  };

  const getColorIntensity = (count, maxCount) => {
    if (count === 0) return 'bg-slate-800';
    
    const intensity = (count / maxCount) * 100;
    
    if (intensity <= 10) return 'bg-blue-900/40';
    if (intensity <= 25) return 'bg-blue-800/60';
    if (intensity <= 50) return 'bg-blue-700/80';
    if (intensity <= 75) return 'bg-blue-600';
    return 'bg-blue-500';
  };

  const hours = Array.from({ length: 24 }, (_, i) => i);

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-white flex items-center gap-2">
              <Users className="w-5 h-5 text-blue-400" />
              Attendance by Day Heatmap
            </CardTitle>
            <CardDescription className="text-slate-400">
              Hourly attendance patterns by day of week
            </CardDescription>
          </div>
          
          {stats && (
            <div className="flex gap-4">
              <div className="text-right">
                <p className="text-slate-400 text-xs">Total Visits</p>
                <p className="text-white font-bold text-lg">{stats.total_visits.toLocaleString()}</p>
              </div>
              <div className="text-right">
                <p className="text-slate-400 text-xs">Peak Hour Count</p>
                <p className="text-white font-bold text-lg">{stats.max_hourly_count}</p>
              </div>
            </div>
          )}
        </div>
        
        {/* Date Range Selector */}
        <div className="flex gap-4 items-end mt-4">
          <div className="flex-1">
            <Label className="text-slate-300 text-xs">Start Date</Label>
            <Input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="bg-slate-700 border-slate-600 text-white mt-1"
            />
          </div>
          <div className="flex-1">
            <Label className="text-slate-300 text-xs">End Date</Label>
            <Input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="bg-slate-700 border-slate-600 text-white mt-1"
            />
          </div>
          <Button
            onClick={fetchHeatmapData}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <Calendar className="w-4 h-4 mr-2" />
            {loading ? 'Loading...' : 'Update'}
          </Button>
        </div>
      </CardHeader>
      
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        ) : (
          <>
            {/* Heatmap Grid */}
            <div className="overflow-x-auto">
              <div className="inline-block min-w-full">
                {/* Hour Labels */}
                <div className="flex mb-2">
                  <div className="w-24 flex-shrink-0"></div>
                  <div className="flex gap-1">
                    {hours.map(hour => (
                      <div
                        key={hour}
                        className="w-8 text-center text-xs text-slate-400"
                      >
                        {hour}
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* Heatmap Rows */}
                {heatmapData.map((dayData) => (
                  <div key={dayData.day} className="flex mb-1">
                    {/* Day Label */}
                    <div className="w-24 flex-shrink-0 text-sm text-slate-300 flex items-center font-medium">
                      {dayData.day}
                    </div>
                    
                    {/* Hour Cells */}
                    <div className="flex gap-1">
                      {hours.map(hour => {
                        const count = dayData[`hour_${hour}`];
                        const colorClass = getColorIntensity(count, stats?.max_hourly_count || 1);
                        
                        return (
                          <div
                            key={hour}
                            className={`w-8 h-8 ${colorClass} rounded border border-slate-700/50 cursor-pointer transition-all hover:scale-110 hover:border-blue-400 relative`}
                            onMouseEnter={() => setHoveredCell({ day: dayData.day, hour, count })}
                            onMouseLeave={() => setHoveredCell(null)}
                          >
                            {/* Tooltip */}
                            {hoveredCell?.day === dayData.day && hoveredCell?.hour === hour && (
                              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-900 text-white text-xs rounded shadow-lg whitespace-nowrap z-10 border border-slate-700">
                                <div className="font-medium">{dayData.day}</div>
                                <div className="text-slate-400">
                                  {hour}:00 - {hour + 1}:00
                                </div>
                                <div className="text-blue-400 font-bold">
                                  {count} visits
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Legend */}
            <div className="mt-6 flex items-center justify-between border-t border-slate-700 pt-4">
              <div className="text-sm text-slate-400">
                Hover over cells to see details
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-400">Less</span>
                <div className="flex gap-1">
                  <div className="w-6 h-6 bg-slate-800 rounded border border-slate-700"></div>
                  <div className="w-6 h-6 bg-blue-900/40 rounded border border-slate-700"></div>
                  <div className="w-6 h-6 bg-blue-800/60 rounded border border-slate-700"></div>
                  <div className="w-6 h-6 bg-blue-700/80 rounded border border-slate-700"></div>
                  <div className="w-6 h-6 bg-blue-600 rounded border border-slate-700"></div>
                  <div className="w-6 h-6 bg-blue-500 rounded border border-slate-700"></div>
                </div>
                <span className="text-sm text-slate-400">More</span>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
