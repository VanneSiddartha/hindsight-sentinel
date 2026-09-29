import React from 'react';
import { AgentStep } from '../services/api';
import { Compass, Code, CheckCircle, ShieldAlert, Cpu, Brain, Sparkles } from 'lucide-react';

interface AgentActivityFeedProps {
  steps: AgentStep[];
  isExecuting?: boolean;
}

export default function AgentActivityFeed({ steps, isExecuting = false }: AgentActivityFeedProps) {
  const getAgentIcon = (name: string) => {
    switch (name) {
      case 'planner':
        return <Compass className="w-4 h-4 text-cyan-400" />;
      case 'coder':
        return <Code className="w-4 h-4 text-indigo-400" />;
      case 'tester':
        return <CheckCircle className="w-4 h-4 text-emerald-400" />;
      case 'security':
        return <ShieldAlert className="w-4 h-4 text-amber-400" />;
      default:
        return <Cpu className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return <span className="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded text-[10px] font-bold">SUCCESS</span>;
      case 'FAILED':
        return <span className="px-2 py-0.5 bg-red-500/20 text-red-400 border border-red-500/40 rounded text-[10px] font-bold">FAILED</span>;
      case 'WARNING':
        return <span className="px-2 py-0.5 bg-amber-500/20 text-amber-400 border border-amber-500/40 rounded text-[10px] font-bold">WARNING</span>;
      case 'SKIPPED':
        return <span className="px-2 py-0.5 bg-gray-700 text-gray-400 rounded text-[10px] font-bold">SKIPPED</span>;
      default:
        return null;
    }
  };

  if (!steps || steps.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 border border-dashed border-gray-800 rounded-xl text-center bg-gray-950/30 h-80">
        <Cpu className="w-10 h-10 text-gray-600 mb-3 animate-[pulse_3s_infinite]" />
        <h4 className="text-sm font-semibold text-gray-300">Pipeline Ready</h4>
        <p className="text-xs text-gray-500 mt-1 max-w-xs">
          Select or enter a task to trigger the autonomous 4-agent workflow.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {steps.map((step, idx) => {
        const isMemoryInfluenced = step.metadata?.memory_influenced;

        return (
          <div
            key={step.step_id || idx}
            className={`border rounded-xl p-4 shadow-sm transition ${
              isMemoryInfluenced
                ? 'bg-indigo-950/20 border-indigo-500/50 hover:border-indigo-400'
                : 'bg-gray-900/80 border-gray-800 hover:border-gray-700'
            }`}
          >
            <div className="flex items-center justify-between pb-2 border-b border-gray-800/80 mb-2">
              <div className="flex items-center space-x-2">
                <div className="p-1.5 bg-gray-800 rounded-lg border border-gray-700">
                  {getAgentIcon(step.agent_name)}
                </div>
                <span className="text-xs font-bold uppercase tracking-wider text-gray-200">
                  {step.agent_name} Agent
                </span>
                {isMemoryInfluenced && (
                  <span className="flex items-center space-x-1 px-2 py-0.5 bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 rounded text-[10px] font-bold">
                    <Brain className="w-3 h-3 text-indigo-400" />
                    <span>Hindsight Memory Influenced</span>
                  </span>
                )}
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-[11px] text-gray-500 font-mono">
                  {new Date(step.timestamp).toLocaleTimeString()}
                </span>
                {getStatusBadge(step.status)}
              </div>
            </div>

            <div className="space-y-2 text-xs">
              <div>
                <span className="text-gray-500 font-semibold uppercase text-[10px] block mb-0.5">Observation</span>
                <p className="text-gray-300 bg-gray-950/60 p-2 rounded border border-gray-800/60 leading-relaxed">
                  {step.observation}
                </p>
              </div>

              <div>
                <span className="text-gray-500 font-semibold uppercase text-[10px] block mb-0.5">Decision & Action</span>
                <pre className="text-gray-200 bg-gray-950 p-2.5 rounded border border-gray-800 font-mono text-[11px] whitespace-pre-wrap overflow-x-auto leading-relaxed text-indigo-300/90">
                  {step.decision}
                </pre>
              </div>

              {step.metadata?.diff && (
                <div>
                  <span className="text-gray-500 font-semibold uppercase text-[10px] block mb-0.5">Code Patch Diff</span>
                  <pre className="text-emerald-400 bg-[#090C15] p-2.5 rounded border border-gray-800/80 font-mono text-[11px] whitespace-pre-wrap overflow-x-auto">
                    {step.metadata.diff}
                  </pre>
                </div>
              )}

              {step.metadata?.test_output && (
                <div>
                  <span className="text-gray-500 font-semibold uppercase text-[10px] block mb-0.5">Test Suite Output</span>
                  <pre className={`p-2.5 rounded border font-mono text-[11px] whitespace-pre-wrap ${
                    step.status === 'FAILED'
                      ? 'bg-red-950/40 border-red-800/50 text-red-300'
                      : 'bg-emerald-950/30 border-emerald-800/40 text-emerald-300'
                  }`}>
                    {step.metadata.test_output}
                  </pre>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
