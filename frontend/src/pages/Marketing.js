import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import Sidebar from '@/components/Sidebar';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { MapPin, Users, TrendingUp, Building } from 'lucide-react';
import { toast } from 'sonner';
import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default marker icon
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

export default function Marketing() {
  const [distribution, setDistribution] = useState(null);
  const [loading, setLoading] = useState(true);
  const [mapCenter, setMapCenter] = useState([-26.2041, 28.0473]); // Johannesburg default

  useEffect(() => {
    fetchDistribution();
  }, []);

  const fetchDistribution = async () => {
    try {
      const response = await axios.get(`${API}/analytics/member-distribution`);
      setDistribution(response.data);
      
      // Set map center to first member if available
      if (response.data.members.length > 0) {
        const first = response.data.members[0];
        setMapCenter([first.latitude, first.longitude]);
      }
    } catch (error) {
      toast.error('Failed to fetch member distribution');
    } finally {
      setLoading(false);
    }
  };

  const calculateDensity = () => {
    if (!distribution || distribution.members.length === 0) return [];
    
    // Simple grid-based density calculation
    const gridSize = 0.05; // degrees
    const densityMap = {};
    
    distribution.members.forEach(member => {
      const gridLat = Math.floor(member.latitude / gridSize) * gridSize;
      const gridLon = Math.floor(member.longitude / gridSize) * gridSize;
      const key = `${gridLat},${gridLon}`;
      
      if (!densityMap[key]) {
        densityMap[key] = { lat: gridLat + gridSize/2, lon: gridLon + gridSize/2, count: 0 };
      }
      densityMap[key].count++;
    });
    
    return Object.values(densityMap);
  };

  const densityAreas = calculateDensity();

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-white mb-2" data-testid="marketing-title">Marketing Analytics</h1>
            <p className="text-slate-400">Member distribution and expansion opportunities</p>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-slate-400 text-sm">Total Members</p>
                    <p className="text-2xl font-bold text-white mt-1">
                      {distribution?.total_members || 0}
                    </p>
                  </div>
                  <Users className="w-8 h-8 text-blue-400" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-emerald-900/20 border-emerald-500">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-emerald-400 text-sm">Geo-Located</p>
                    <p className="text-2xl font-bold text-white mt-1">
                      {distribution?.geo_located_members || 0}
                    </p>
                  </div>
                  <MapPin className="w-8 h-8 text-emerald-400" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-blue-900/20 border-blue-500">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-blue-400 text-sm">Coverage Rate</p>
                    <p className="text-2xl font-bold text-white mt-1">
                      {distribution?.total_members > 0 
                        ? ((distribution?.geo_located_members / distribution?.total_members) * 100).toFixed(1)
                        : 0}%
                    </p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-blue-400" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-purple-900/20 border-purple-500">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-purple-400 text-sm">Density Areas</p>
                    <p className="text-2xl font-bold text-white mt-1">{densityAreas.length}</p>
                  </div>
                  <Building className="w-8 h-8 text-purple-400" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Info Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            <Card className="bg-blue-900/20 border-blue-500">
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <MapPin className="w-5 h-5 text-blue-400 mt-0.5" />
                  <div>
                    <h3 className="text-blue-200 font-semibold mb-1">Geographic Insights</h3>
                    <p className="text-blue-300 text-sm">
                      Member addresses are automatically geo-located using their home address. This enables heat map analysis, 
                      density visualization, and identification of underserved areas for potential gym expansion.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-emerald-900/20 border-emerald-500">
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <Building className="w-5 h-5 text-emerald-400 mt-0.5" />
                  <div>
                    <h3 className="text-emerald-200 font-semibold mb-1">Expansion Opportunities</h3>
                    <p className="text-emerald-300 text-sm">
                      Low-density areas (lighter colors) indicate potential opportunities for new gym locations. 
                      High-density clusters show where existing facilities are well-utilized.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Map */}
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg">
            <CardHeader>
              <CardTitle className="text-white">Member Distribution Map</CardTitle>
              <CardDescription className="text-slate-400">
                Geographic distribution of members with density visualization
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center text-slate-400 py-12">Loading map...</div>
              ) : distribution && distribution.geo_located_members > 0 ? (
                <div style={{ height: '600px', borderRadius: '8px', overflow: 'hidden' }}>
                  <MapContainer
                    center={mapCenter}
                    zoom={11}
                    style={{ height: '100%', width: '100%' }}
                  >
                    <TileLayer
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    
                    {/* Density circles */}
                    {densityAreas.map((area, idx) => {
                      const intensity = Math.min(area.count / 5, 1);
                      return (
                        <CircleMarker
                          key={idx}
                          center={[area.lat, area.lon]}
                          radius={Math.sqrt(area.count) * 5}
                          fillColor={`rgba(16, 185, 129, ${intensity})`}
                          color="#10b981"
                          weight={1}
                          fillOpacity={0.4}
                        >
                          <Popup>
                            <div className="text-slate-900">
                              <p className="font-semibold">Density Area</p>
                              <p className="text-sm">{area.count} member{area.count !== 1 ? 's' : ''} in this area</p>
                            </div>
                          </Popup>
                        </CircleMarker>
                      );
                    })}
                    
                    {/* Individual member markers */}
                    {distribution.members.map((member) => (
                      <Marker
                        key={member.id}
                        position={[member.latitude, member.longitude]}
                      >
                        <Popup>
                          <div className="text-slate-900">
                            <p className="font-semibold">{member.first_name} {member.last_name}</p>
                            <p className="text-sm">{member.address}</p>
                            <p className="text-xs mt-1">
                              <span className={`inline-block px-2 py-0.5 rounded ${
                                member.membership_status === 'active' ? 'bg-green-200' : 'bg-red-200'
                              }`}>
                                {member.membership_status}
                              </span>
                            </p>
                          </div>
                        </Popup>
                      </Marker>
                    ))}
                  </MapContainer>
                </div>
              ) : (
                <div className="text-center text-slate-400 py-12">
                  <MapPin className="w-16 h-16 mx-auto mb-4 text-slate-600" />
                  <p>No geo-located members yet</p>
                  <p className="text-sm mt-2">Member addresses will be automatically geo-located when added</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Legend */}
          {distribution && distribution.geo_located_members > 0 && (
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-lg mt-4">
              <CardContent className="pt-6">
                <div className="flex items-center gap-8">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 bg-emerald-500 rounded-full"></div>
                    <span className="text-slate-300 text-sm">Individual Members</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-emerald-500/40 rounded-full border-2 border-emerald-500"></div>
                    <span className="text-slate-300 text-sm">High Density Areas</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-emerald-500/10 rounded-full border-2 border-emerald-500"></div>
                    <span className="text-slate-300 text-sm">Low Density (Expansion Opportunity)</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
