import React from 'react';
import { AlertTriangle, Phone, Home, Shield, MapPin, CreditCard } from 'lucide-react';

const MissingDataWarnings = ({ missingData }) => {
  if (!missingData || missingData.length === 0) {
    return null;
  }
  
  const getMissingDataConfig = (type) => {
    switch (type) {
      case 'phone':
        return { icon: Phone, label: 'Missing mobile phone number' };
      case 'additional_phone':
        return { icon: Home, label: 'Missing home/work phone' };
      case 'emergency_contact':
        return { icon: Shield, label: 'Missing emergency contact details' };
      case 'address':
        return { icon: MapPin, label: 'Missing home address' };
      case 'bank_details':
        return { icon: CreditCard, label: 'Missing bank account details' };
      default:
        return { icon: AlertTriangle, label: `Missing ${type}` };
    }
  };
  
  return (
    <div className="space-y-2">
      {missingData.map((dataType, index) => {
        const config = getMissingDataConfig(dataType);
        const Icon = config.icon;
        
        return (
          <div 
            key={index}
            className="flex items-center gap-2 px-3 py-2 bg-yellow-500/10 border border-yellow-500/30 rounded-lg"
          >
            <Icon className="w-4 h-4 text-yellow-500" />
            <span className="text-xs text-yellow-500">* {config.label}</span>
          </div>
        );
      })}
    </div>
  );
};

export default MissingDataWarnings;
