import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Cake, Mail, User } from 'lucide-react';

const BirthdayGallery = ({ birthdays }) => {
  if (!birthdays || birthdays.length === 0) {
    return (
      <div className="bg-slate-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Cake className="w-5 h-5 text-pink-400" />
            Birthdays Today
          </h3>
        </div>
        <p className="text-slate-400 text-center py-8">No birthdays today</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <Cake className="w-5 h-5 text-pink-400" />
          Birthdays Today
        </h3>
        <span className="text-sm text-slate-400">{birthdays.length} member{birthdays.length !== 1 ? 's' : ''}</span>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 max-h-[600px] overflow-y-auto">
        {birthdays.map((member, index) => (
          <Card 
            key={member.id || index}
            className="bg-slate-700/50 border-slate-600 hover:border-pink-400 transition-all cursor-pointer group"
          >
            <CardContent className="p-3">
              <div className="flex flex-col items-center text-center">
                {/* Member Photo */}
                <div className="w-20 h-20 rounded-full overflow-hidden bg-slate-600 mb-3 ring-2 ring-pink-400/50 group-hover:ring-pink-400">
                  {member.photo_url ? (
                    <img 
                      src={member.photo_url} 
                      alt={member.full_name}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="gray"><circle cx="12" cy="8" r="4"/><path d="M12 14c-6 0-8 4-8 4v2h16v-2s-2-4-8-4z"/></svg>';
                      }}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <User className="w-10 h-10 text-slate-400" />
                    </div>
                  )}
                </div>
                
                {/* Member Name */}
                <h4 className="text-sm font-semibold text-white mb-1 line-clamp-2">
                  {member.full_name}
                </h4>
                
                {/* Age */}
                <div className="flex items-center gap-1 text-pink-400 mb-2">
                  <Cake className="w-3 h-3" />
                  <span className="text-xs font-semibold">{member.age} years young</span>
                </div>
                
                {/* Membership Status Badge */}
                {member.membership_status && (
                  <div className={`px-2 py-0.5 rounded-full text-xs font-medium mb-2 ${
                    member.membership_status === 'active' 
                      ? 'bg-green-500/20 text-green-400'
                      : member.membership_status === 'expired'
                      ? 'bg-red-500/20 text-red-400'
                      : 'bg-gray-500/20 text-gray-400'
                  }`}>
                    {member.membership_status}
                  </div>
                )}
                
                {/* Email (if available) */}
                {member.email && (
                  <div className="flex items-center gap-1 text-xs text-slate-400 mt-1">
                    <Mail className="w-3 h-3" />
                    <span className="truncate max-w-[120px]">{member.email}</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default BirthdayGallery;
