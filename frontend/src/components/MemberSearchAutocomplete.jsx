import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '@/App';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Search, X, User } from 'lucide-react';

export default function MemberSearchAutocomplete({ 
  value, 
  onChange, 
  label = "Search Member",
  placeholder = "Type to search members...",
  className = ""
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedMember, setSelectedMember] = useState(null);

  // Debounced search
  useEffect(() => {
    if (searchQuery.length < 2) {
      setSearchResults([]);
      setShowDropdown(false);
      return;
    }

    const timeoutId = setTimeout(async () => {
      setIsSearching(true);
      try {
        const response = await axios.get(`${API}/sales/members/search?q=${encodeURIComponent(searchQuery)}`);
        setSearchResults(response.data.members || []);
        setShowDropdown(true);
      } catch (error) {
        console.error('Member search error:', error);
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 300); // 300ms debounce

    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  // Load selected member details if value is provided
  useEffect(() => {
    if (value && !selectedMember) {
      // If we have a member ID but no selected member, try to fetch details
      const fetchMemberDetails = async () => {
        try {
          const response = await axios.get(`${API}/sales/members/search?q=${value}`);
          const member = response.data.members?.find(m => m.id === value);
          if (member) {
            setSelectedMember(member);
            setSearchQuery(`${member.first_name} ${member.last_name}`.trim());
          }
        } catch (error) {
          console.error('Error fetching member details:', error);
        }
      };
      fetchMemberDetails();
    }
  }, [value, selectedMember]);

  const handleSelectMember = (member) => {
    setSelectedMember(member);
    setSearchQuery(`${member.first_name} ${member.last_name}`.trim());
    setShowDropdown(false);
    onChange(member.id);
  };

  const handleClear = () => {
    setSelectedMember(null);
    setSearchQuery('');
    setSearchResults([]);
    setShowDropdown(false);
    onChange(null);
  };

  const handleInputChange = (e) => {
    const value = e.target.value;
    setSearchQuery(value);
    if (selectedMember) {
      setSelectedMember(null);
      onChange(null);
    }
  };

  return (
    <div className={`relative ${className}`}>
      {label && (
        <Label className="text-slate-300 text-sm mb-2 block">{label}</Label>
      )}
      
      <div className="relative">
        <div className="absolute left-3 top-1/2 -translate-y-1/2">
          <Search className="w-4 h-4 text-slate-400" />
        </div>
        
        <Input
          type="text"
          value={searchQuery}
          onChange={handleInputChange}
          onFocus={() => {
            if (searchResults.length > 0) {
              setShowDropdown(true);
            }
          }}
          placeholder={placeholder}
          className="pl-10 pr-10 bg-slate-700 border-slate-600 text-white"
        />
        
        {(searchQuery || selectedMember) && (
          <button
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
            type="button"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Selected Member Badge */}
      {selectedMember && (
        <div className="mt-2 p-2 bg-green-900/30 border border-green-500/30 rounded flex items-center gap-2">
          <User className="w-4 h-4 text-green-400" />
          <div className="flex-1">
            <p className="text-sm text-white font-medium">
              {selectedMember.first_name} {selectedMember.last_name}
            </p>
            <p className="text-xs text-slate-400">{selectedMember.email}</p>
          </div>
          <Badge className="bg-green-600">Selected</Badge>
        </div>
      )}

      {/* Search Dropdown */}
      {showDropdown && searchResults.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-slate-800 border border-slate-600 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {isSearching && (
            <div className="p-3 text-center text-slate-400 text-sm">
              Searching...
            </div>
          )}
          
          {!isSearching && searchResults.map((member) => (
            <button
              key={member.id}
              onClick={() => handleSelectMember(member)}
              className="w-full p-3 hover:bg-slate-700 text-left transition-colors border-b border-slate-700 last:border-b-0"
              type="button"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center">
                  <User className="w-5 h-5 text-slate-400" />
                </div>
                <div className="flex-1">
                  <p className="text-white font-medium text-sm">
                    {member.first_name} {member.last_name}
                  </p>
                  <p className="text-slate-400 text-xs">{member.email}</p>
                  {member.phone && (
                    <p className="text-slate-500 text-xs">{member.phone}</p>
                  )}
                </div>
                <div>
                  <Badge 
                    variant={member.membership_status === 'active' ? 'default' : 'secondary'}
                    className="text-xs"
                  >
                    {member.membership_status}
                  </Badge>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* No Results */}
      {showDropdown && !isSearching && searchResults.length === 0 && searchQuery.length >= 2 && (
        <div className="absolute z-50 w-full mt-1 bg-slate-800 border border-slate-600 rounded-lg shadow-lg p-4 text-center">
          <p className="text-slate-400 text-sm">No members found</p>
          <p className="text-slate-500 text-xs mt-1">Try a different search term</p>
        </div>
      )}

      {/* Minimum Characters Hint */}
      {searchQuery.length > 0 && searchQuery.length < 2 && (
        <p className="text-xs text-slate-500 mt-1">Type at least 2 characters to search</p>
      )}
    </div>
  );
}
