import React from 'react';
import { ShieldCheck, AlertTriangle, ShieldAlert } from 'lucide-react';

interface RiskBadgeProps {
  riskLevel: 'NORMAL' | 'CAUTION' | 'HIGH RISK';
  recommendedAction?: string;
  evidenceCount?: number;
}

export default function RiskBadge({ riskLevel, recommendedAction, evidenceCount = 0 }: RiskBadgeProps) {
  const recommendation = recommendedAction || 'No recommendation was returned by the backend.';

  if (riskLevel === 'HIGH RISK') {
    return (
      <div className="bg-red-950/60 border-2 border-red-500/80 rounded-xl p-5 shadow-2xl shadow-red-950/50 backdrop-blur transition-all duration-300">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center space-x-4">
            <div className="bg-red-500/20 border border-red-500 p-3 rounded-xl text-red-400 animate-pulse">
              <ShieldAlert className="w-8 h-8" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="px-3 py-1 bg-red-600 text-white font-extrabold rounded-full text-xs tracking-wider uppercase shadow">
                  HIGH RISK
                </span>
                <span className="text-xs text-red-300 font-semibold">
                  {evidenceCount} historical evidence item(s) returned
                </span>
              </div>
              <h2 className="text-lg font-bold text-red-100 mt-1">Historical evidence indicates elevated risk</h2>
              <p className="text-xs text-red-200/90 mt-0.5 max-w-2xl">
                {recommendation}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (riskLevel === 'CAUTION') {
    return (
      <div className="bg-amber-950/60 border-2 border-amber-500/80 rounded-xl p-5 shadow-xl shadow-amber-950/30 backdrop-blur transition-all duration-300">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center space-x-4">
            <div className="bg-amber-500/20 border border-amber-500 p-3 rounded-xl text-amber-400">
              <AlertTriangle className="w-8 h-8" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="px-3 py-1 bg-amber-500 text-slate-950 font-extrabold rounded-full text-xs tracking-wider uppercase shadow">
                  CAUTION
                </span>
                <span className="text-xs text-amber-300 font-semibold">
                  {evidenceCount} historical evidence item(s) returned
                </span>
              </div>
              <h2 className="text-lg font-bold text-amber-100 mt-1">Related historical experience requires review</h2>
              <p className="text-xs text-amber-200/90 mt-0.5 max-w-2xl">
                {recommendation}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // NORMAL (Default)
  return (
    <div className="bg-emerald-950/40 border border-emerald-500/50 rounded-xl p-5 shadow-lg shadow-emerald-950/20 backdrop-blur transition-all duration-300">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="bg-emerald-500/20 border border-emerald-500/40 p-3 rounded-xl text-emerald-400">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-3 py-1 bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 font-extrabold rounded-full text-xs tracking-wider uppercase">
                NORMAL
              </span>
            </div>
            <h2 className="text-lg font-bold text-emerald-100 mt-1">No known risk detected</h2>
            <p className="text-xs text-emerald-200/80 mt-0.5">
              {recommendation}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
