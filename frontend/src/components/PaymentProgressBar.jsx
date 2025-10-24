import React from 'react';

const PaymentProgressBar = ({ paymentProgress }) => {
  if (!paymentProgress || paymentProgress.total === 0) {
    return (
      <div className="w-full bg-slate-700 rounded-full h-6 flex items-center justify-center">
        <span className="text-xs text-slate-400">No payment history</span>
      </div>
    );
  }
  
  const { paid_percentage, unpaid_percentage, remaining_percentage, paid, unpaid, remaining, total } = paymentProgress;
  
  return (
    <div className="space-y-2">
      <div className="w-full bg-slate-700 rounded-full h-6 flex overflow-hidden">
        {/* Paid section - Green */}
        {paid_percentage > 0 && (
          <div 
            className="bg-green-500 flex items-center justify-center transition-all duration-300"
            style={{ width: `${paid_percentage}%` }}
            title={`Paid: R${paid.toFixed(2)}`}
          >
            {paid_percentage > 15 && (
              <span className="text-xs font-semibold text-white">
                {paid_percentage.toFixed(0)}%
              </span>
            )}
          </div>
        )}
        
        {/* Unpaid section - Red */}
        {unpaid_percentage > 0 && (
          <div 
            className="bg-red-500 flex items-center justify-center transition-all duration-300"
            style={{ width: `${unpaid_percentage}%` }}
            title={`Unpaid: R${unpaid.toFixed(2)}`}
          >
            {unpaid_percentage > 15 && (
              <span className="text-xs font-semibold text-white">
                {unpaid_percentage.toFixed(0)}%
              </span>
            )}
          </div>
        )}
        
        {/* Remaining section - Amber */}
        {remaining_percentage > 0 && (
          <div 
            className="bg-amber-500 flex items-center justify-center transition-all duration-300"
            style={{ width: `${remaining_percentage}%` }}
            title={`Remaining: R${remaining.toFixed(2)}`}
          >
            {remaining_percentage > 15 && (
              <span className="text-xs font-semibold text-white">
                {remaining_percentage.toFixed(0)}%
              </span>
            )}
          </div>
        )}
      </div>
      
      {/* Legend */}
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-green-500 rounded"></div>
            <span className="text-slate-400">Paid: R{paid.toFixed(2)}</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-red-500 rounded"></div>
            <span className="text-slate-400">Unpaid: R{unpaid.toFixed(2)}</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-amber-500 rounded"></div>
            <span className="text-slate-400">Remaining: R{remaining.toFixed(2)}</span>
          </div>
        </div>
        <span className="text-slate-300 font-semibold">Total: R{total.toFixed(2)}</span>
      </div>
    </div>
  );
};

export default PaymentProgressBar;
