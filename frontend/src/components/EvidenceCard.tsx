import React from 'react';
import { History, AlertCircle, Lightbulb, CheckCircle2, XCircle, Sparkles } from 'lucide-react';
import { ExperienceModel } from '../services/api';

interface EvidenceItem {
  experience_id?: string;
  context?: string;
  outcome?: string;
  score?: number;
  reason?: string;
  description?: string;
  lesson?: string;
  root_cause?: string;
  future_applicability?: string;
}

interface EvidenceCardProps {
  evidence: EvidenceItem[];
  recalledExperiences?: EvidenceItem[];
  extractedExperience?: ExperienceModel;
  retentionStatus?: 'not_attempted' | 'remote' | 'local_only' | 'temporary';
}

export default function EvidenceCard({
  evidence,
  recalledExperiences = [],
  extractedExperience,
  retentionStatus = 'not_attempted',
}: EvidenceCardProps) {
  const evidenceById = new Map(
    evidence.flatMap((item) => item.experience_id ? [[item.experience_id, item] as const] : []),
  );
  const items = recalledExperiences.length > 0
    ? recalledExperiences.map((item) => ({
      ...(item.experience_id ? evidenceById.get(item.experience_id) : undefined),
      ...item,
    }))
    : evidence;

  return (
    <div className="space-y-4">
      {/* 1. Recalled Memories Section */}
      {items && items.length > 0 ? (
        items.map((item, idx) => (
          <div
            key={item.experience_id || idx}
            className={`border rounded-xl p-4 transition shadow-sm ${
              item.outcome === 'FAILURE'
                ? 'bg-red-950/20 border-red-800/50 hover:border-red-700/80'
                : 'bg-gray-900/80 border-gray-800 hover:border-gray-700'
            }`}
          >
            <div className="flex items-center justify-between pb-2 border-b border-gray-800 mb-2">
              <div className="flex items-center space-x-2">
                <span className="font-mono text-xs font-bold text-indigo-400">
                  [{item.experience_id}]
                </span>
                {item.outcome === 'FAILURE' ? (
                  <span className="flex items-center space-x-1 px-2 py-0.5 bg-red-500/20 text-red-400 border border-red-500/40 rounded text-[10px] font-bold">
                    <XCircle className="w-3 h-3" />
                    <span>PAST FAILURE</span>
                  </span>
                ) : (
                  <span className="flex items-center space-x-1 px-2 py-0.5 bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 rounded text-[10px] font-bold">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>SUCCESS</span>
                  </span>
                )}
              </div>

              {item.score !== undefined && (
                <span className="text-[10px] font-bold px-2 py-0.5 bg-indigo-500/20 text-indigo-300 rounded border border-indigo-500/30">
                  {(item.score * 100).toFixed(0)}% Match
                </span>
              )}
            </div>

            <div className="space-y-2 text-xs">
              <div>
                <span className="text-gray-500 text-[10px] font-semibold uppercase block">Incident Context</span>
                <p className="text-gray-200 font-medium">{item.context || item.description}</p>
              </div>

              {item.reason && (
                <div className="bg-gray-950/60 p-2.5 rounded border border-gray-800/80">
                  <span className="text-amber-400 text-[10px] font-bold uppercase flex items-center space-x-1 mb-1">
                    <AlertCircle className="w-3 h-3" />
                    <span>Match Rationale</span>
                  </span>
                  <p className="text-gray-300 text-[11px] leading-relaxed">{item.reason}</p>
                </div>
              )}

              {item.lesson && (
                <div className="bg-indigo-950/30 p-2.5 rounded border border-indigo-800/40">
                  <span className="text-indigo-400 text-[10px] font-bold uppercase flex items-center space-x-1 mb-1">
                    <Lightbulb className="w-3 h-3 text-amber-400" />
                    <span>Prior Experience Lesson</span>
                  </span>
                  <p className="text-indigo-200 text-[11px] leading-relaxed font-medium">{item.lesson}</p>
                </div>
              )}

              {item.root_cause && (
                <div className="rounded border border-red-900/50 bg-red-950/20 p-2.5">
                  <span className="mb-1 block text-[10px] font-bold uppercase text-red-300">Root Cause</span>
                  <p className="text-[11px] leading-relaxed text-gray-300">{item.root_cause}</p>
                </div>
              )}

              {item.future_applicability && (
                <div>
                  <span className="block text-[10px] font-semibold uppercase text-gray-500">Future Applicability</span>
                  <p className="mt-0.5 text-[11px] leading-relaxed text-gray-300">{item.future_applicability}</p>
                </div>
              )}
            </div>
          </div>
        ))
      ) : (
        <div className="flex flex-col items-center justify-center p-6 border border-dashed border-gray-800 rounded-xl text-center bg-gray-950/30">
          <History className="w-8 h-8 text-gray-600 mb-2" />
          <h4 className="text-xs font-semibold text-gray-300">No Matched Incidents</h4>
          <p className="text-[11px] text-gray-500 mt-0.5 max-w-xs">
            No relevant prior experiences were returned for this workflow.
          </p>
        </div>
      )}

      {/* 2. Post-Run Extracted Experience Card */}
      {extractedExperience && (
        <div className="bg-gradient-to-r from-indigo-950/80 via-purple-950/60 to-gray-900 border-2 border-indigo-500/70 rounded-xl p-4 shadow-xl animate-fade-in space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-indigo-800/60">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-amber-400 animate-pulse" />
              <span className="text-xs font-bold text-white uppercase tracking-wider">
              New Experience Captured
              </span>
            </div>
            <span className="px-2 py-0.5 bg-indigo-500/30 text-indigo-200 border border-indigo-400/50 rounded font-mono text-[10px] font-bold">
              {retentionStatus === 'remote'
                ? `Hindsight retained · source=${extractedExperience.source || 'workflow'}`
                : retentionStatus === 'local_only'
                  ? 'Metadata persisted locally · Hindsight not retained'
                  : retentionStatus === 'temporary'
                    ? 'Temporary in-memory only · not persistent'
                    : 'Retention was not attempted'}
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between text-gray-300 font-mono text-[11px]">
              <span>ID: <strong>[{extractedExperience.experience_id}]</strong></span>
              <span>Outcome: <strong className={extractedExperience.outcome === 'FAILURE' ? 'text-red-400' : 'text-emerald-400'}>{extractedExperience.outcome}</strong></span>
            </div>

            {extractedExperience.root_cause && (
              <div className={`p-2 rounded border ${
                extractedExperience.outcome === 'FAILURE'
                  ? 'bg-red-950/30 border-red-800/50'
                  : 'bg-gray-950/50 border-gray-800'
              }`}>
                <span className={`font-bold uppercase text-[10px] block mb-0.5 ${
                  extractedExperience.outcome === 'FAILURE' ? 'text-red-400' : 'text-gray-400'
                }`}>Root Cause</span>
                <p className={`text-[11px] ${
                  extractedExperience.outcome === 'FAILURE' ? 'text-red-200' : 'text-gray-300'
                }`}>{extractedExperience.root_cause}</p>
              </div>
            )}

            <div className="bg-indigo-950/60 p-2.5 rounded border border-indigo-700/60">
              <span className="text-amber-300 font-bold uppercase text-[10px] block mb-0.5">Lesson for Future Tasks</span>
              <p className="text-indigo-100 text-[11px] font-medium leading-relaxed">{extractedExperience.lesson}</p>
            </div>
          {extractedExperience.future_applicability && (
            <div className="rounded border border-gray-700 bg-gray-950/50 p-2.5">
              <span className="mb-0.5 block text-[10px] font-bold uppercase text-gray-400">Future Applicability</span>
              <p className="text-[11px] leading-relaxed text-gray-300">{extractedExperience.future_applicability}</p>
            </div>
          )}
          </div>
        </div>
      )}
    </div>
  );
}
