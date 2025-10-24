import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API } from '@/App';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Search, Users, Calendar, FileText, Loader2 } from 'lucide-react';

export default function GlobalSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const searchRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    const delaySearch = setTimeout(() => {
      if (query.length >= 2) {
        performSearch();
      } else {
        setResults(null);
      }
    }, 300);

    return () => clearTimeout(delaySearch);
  }, [query]);

  const performSearch = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/engagement/search?query=${encodeURIComponent(query)}`);
      setResults(response.data);
      setIsOpen(true);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleResultClick = (result) => {
    if (result.type === 'member') {
      navigate('/members');
    } else if (result.type === 'class') {
      navigate('/classes');
    } else if (result.type === 'invoice') {
      navigate('/invoices');
    }
    setIsOpen(false);
    setQuery('');
  };

  const getResultIcon = (type) => {
    switch (type) {
      case 'member': return <Users className="w-4 h-4 text-blue-400" />;
      case 'class': return <Calendar className="w-4 h-4 text-purple-400" />;
      case 'invoice': return <FileText className="w-4 h-4 text-green-400" />;
      default: return <Search className="w-4 h-4" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'frozen': return 'bg-blue-500';
      case 'paid': return 'bg-green-500';
      case 'overdue': return 'bg-red-500';
      case 'pending': return 'bg-yellow-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div ref={searchRef} className="relative w-full max-w-md">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
        <Input
          type="text"
          placeholder="Search members, classes, invoices..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query.length >= 2 && setIsOpen(true)}
          className="pl-10 pr-10 bg-slate-800 border-slate-700 text-white placeholder:text-slate-400"
        />
        {loading && (
          <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400 animate-spin" />
        )}
      </div>

      {isOpen && results && results.total_results > 0 && (
        <Card className="absolute top-full mt-2 w-full max-h-96 overflow-auto bg-slate-800 border-slate-700 shadow-xl z-50">
          <CardContent className="p-2">
            {/* Members */}
            {results.results.members.length > 0 && (
              <div className="mb-3">
                <div className="text-xs text-slate-400 font-semibold mb-2 px-2">MEMBERS ({results.results.members.length})</div>
                {results.results.members.map((member) => (
                  <button
                    key={member.id}
                    onClick={() => handleResultClick(member)}
                    className="w-full flex items-center gap-3 p-2 hover:bg-slate-700 rounded-lg transition-colors text-left"
                  >
                    {getResultIcon('member')}
                    <div className="flex-1 min-w-0">
                      <div className="text-white font-medium truncate">{member.name}</div>
                      <div className="text-slate-400 text-xs truncate">{member.email}</div>
                    </div>
                    <Badge className={`${getStatusColor(member.status)} text-white text-xs`}>
                      {member.status}
                    </Badge>
                  </button>
                ))}
              </div>
            )}

            {/* Classes */}
            {results.results.classes.length > 0 && (
              <div className="mb-3">
                <div className="text-xs text-slate-400 font-semibold mb-2 px-2">CLASSES ({results.results.classes.length})</div>
                {results.results.classes.map((classItem) => (
                  <button
                    key={classItem.id}
                    onClick={() => handleResultClick(classItem)}
                    className="w-full flex items-center gap-3 p-2 hover:bg-slate-700 rounded-lg transition-colors text-left"
                  >
                    {getResultIcon('class')}
                    <div className="flex-1 min-w-0">
                      <div className="text-white font-medium truncate">{classItem.name}</div>
                      <div className="text-slate-400 text-xs truncate">
                        Instructor: {classItem.instructor} • {classItem.date}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}

            {/* Invoices */}
            {results.results.invoices.length > 0 && (
              <div>
                <div className="text-xs text-slate-400 font-semibold mb-2 px-2">INVOICES ({results.results.invoices.length})</div>
                {results.results.invoices.map((invoice) => (
                  <button
                    key={invoice.id}
                    onClick={() => handleResultClick(invoice)}
                    className="w-full flex items-center gap-3 p-2 hover:bg-slate-700 rounded-lg transition-colors text-left"
                  >
                    {getResultIcon('invoice')}
                    <div className="flex-1 min-w-0">
                      <div className="text-white font-medium truncate">Invoice #{invoice.invoice_number}</div>
                      <div className="text-slate-400 text-xs truncate">
                        R {invoice.amount?.toLocaleString()} • Due: {invoice.due_date}
                      </div>
                    </div>
                    <Badge className={`${getStatusColor(invoice.status)} text-white text-xs`}>
                      {invoice.status}
                    </Badge>
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {isOpen && results && results.total_results === 0 && query.length >= 2 && (
        <Card className="absolute top-full mt-2 w-full bg-slate-800 border-slate-700 shadow-xl z-50">
          <CardContent className="p-4 text-center">
            <Search className="w-8 h-8 mx-auto mb-2 text-slate-500" />
            <p className="text-slate-400 text-sm">No results found for "{query}"</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
