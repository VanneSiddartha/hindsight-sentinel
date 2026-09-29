import React from 'react';
import { ExperienceModel } from '../services/api';
import { ArrowLeft, History, Tag, AlertTriangle, Lightbulb, CheckCircle2, Shield } from 'lucide-react';

interface ExperienceDetailProps {
  experience: ExperienceModel;
  onBack: () => void;
}

export default function ExperienceDetail({ experience, onBack }: ExperienceDetailProps) {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <button
        onClick={onBack}
        className="flex items-center space-x-2 px-3 py-1.5 bg-gray-900 border border-gray-800 hover:border-gray-700 text-gray-300 rounded-lg text-xs font-semibold transition"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Vault</span>
      </button>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-gray-800">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <span className="font-mono text-xs font-bold text-indigo-400">
                [{experience.experience_id}]
              </span>
              <span className="text-xs text-gray-500">&bull; {experience.service_name}</span>
            </div>
            <h2 className="text-xl font-bold text-gray-100">{experience.context}</h2>
          </div>

          <span
            className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
              experience.outcome === 'FAILURE'
                ? 'bg-red-500/20 text-red-400 border border-red-500/40'
                : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
            }`}
          >
            {experience.outcome}
          </span>
        </div>

        {/* Detailed Fields Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
          <div className="space-y-1">
            <span className="text-gray-500 font-semibold uppercase text-[10px] block">Agents Involved</span>
            <div className="flex flex-wrap gap-1.5">
              {experience.agents_involved.map((agent) => (
                <span key={agent} className="px-2 py-0.5 bg-gray-800 text-indigo-300 rounded font-mono text-[11px]">
                  {agent}
                </span>
              ))}
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-gray-500 font-semibold uppercase text-[10px] block">Tags</span>
            <div className="flex flex-wrap gap-1.5">
              {experience.tags.map((tag) => (
                <span key={tag} className="px-2 py-0.5 bg-indigo-950 text-indigo-300 border border-indigo-800/40 rounded text-[11px]">
                  #{tag}
                </span>
              ))}
            </div>
          </div>

          <div className="space-y-1 md:col-span-2">
            <span className="text-gray-500 font-semibold uppercase text-[10px] block">Original Decision</span>
            <p className="text-gray-300 bg-gray-950 p-3 rounded border border-gray-800 font-mono text-[11px]">
              {experience.decision}
            </p>
          </div>

          <div className="space-y-1 md:col-span-2">
            <span className="text-gray-500 font-semibold uppercase text-[10px] block">Action Taken</span>
            <p className="text-gray-300 bg-gray-950 p-3 rounded border border-gray-800 font-mono text-[11px]">
              {experience.action}
            </p>
          </div>

          {experience.root_cause && (
            <div className="space-y-1 md:col-span-2 bg-red-950/20 p-4 rounded-xl border border-red-800/40">
              <span className="text-red-400 font-bold uppercase text-[10px] flex items-center space-x-1 mb-1">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Root Cause Analysis</span>
              </span>
              <p className="text-red-200 text-xs leading-relaxed">{experience.root_cause}</p>
            </div>
          )}

          <div className="space-y-1 md:col-span-2 bg-indigo-950/30 p-4 rounded-xl border border-indigo-800/50">
            <span className="text-indigo-400 font-bold uppercase text-[10px] flex items-center space-x-1 mb-1">
              <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
              <span>Lesson Learned</span>
            </span>
            <p className="text-indigo-100 text-xs font-medium leading-relaxed">{experience.lesson}</p>
          </div>

          <div className="space-y-1 md:col-span-2">
            <span className="text-gray-500 font-semibold uppercase text-[10px] block">Future Applicability</span>
            <p className="text-gray-400 bg-gray-950 p-3 rounded border border-gray-800 text-xs">
              {experience.future_applicability}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
