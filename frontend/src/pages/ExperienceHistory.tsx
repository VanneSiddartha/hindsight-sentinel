import React, { useEffect, useState } from 'react';
import { ApiRequestError, fetchExperiences, ExperienceModel } from '../services/api';
import { History, Search, Tag, ChevronRight, Brain, Database } from 'lucide-react';
import ExperienceDetail from './ExperienceDetail';

export default function ExperienceHistory() {
  const [experiences, setExperiences] = useState<ExperienceModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedExp, setSelectedExp] = useState<ExperienceModel | null>(null);
  const [error, setError] = useState('');
  const [sourceFilter, setSourceFilter] = useState<'all' | 'workflow' | 'demo'>('all');

  const loadExperiences = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await fetchExperiences();
      setExperiences(data);
    } catch (err) {
      setError(err instanceof ApiRequestError
        ? err.message
        : 'Could not load experience history due to an unexpected frontend error.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadExperiences();
  }, []);

  const filtered = experiences.filter((e) => {
    const isWorkflow = e.source === 'workflow' || e.source === 'agent_run';
    const isDemo = e.source === 'demo' || e.source === 'seed';
    const matchesSource = sourceFilter === 'all' ||
      (sourceFilter === 'workflow' && isWorkflow) ||
      (sourceFilter === 'demo' && isDemo);
    return matchesSource && (
      e.context.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.service_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.lesson.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  if (selectedExp) {
    return <ExperienceDetail experience={selectedExp} onBack={() => setSelectedExp(null)} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-gray-800">
        <div>
          <h2 className="text-xl font-bold flex items-center space-x-2 text-gray-100">
            <History className="w-5 h-5 text-indigo-400" />
            <span>Experience Memory Vault</span>
          </h2>
          <p className="text-xs text-gray-400 mt-1">
            Persisted workflow experiences and demo examples; remote Hindsight status is shown per experience
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={loadExperiences}
            disabled={loading}
            className="px-3 py-1.5 bg-gray-900 hover:bg-gray-800 text-xs font-semibold text-indigo-300 border border-gray-800 rounded-lg transition"
          >
            {loading ? 'Loading…' : 'Refresh Vault'}
          </button>
          <div className="relative w-full md:w-64">
            <Search className="w-4 h-4 absolute left-3 top-3 text-gray-500" />
            <input
              type="text"
              placeholder="Search experiences..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-gray-900 border border-gray-800 rounded-lg text-xs text-gray-200 focus:outline-none focus:border-indigo-500 transition"
            />
          </div>
          <select
            aria-label="Filter experiences by source"
            value={sourceFilter}
            onChange={(event) => setSourceFilter(event.target.value as 'all' | 'workflow' | 'demo')}
            className="rounded-lg border border-gray-800 bg-gray-900 px-3 py-2 text-xs text-gray-200 focus:border-indigo-500 focus:outline-none"
          >
            <option value="all">All Experiences</option>
            <option value="workflow">My Workflow Experiences</option>
            <option value="demo">Demo Experiences</option>
          </select>
        </div>
      </div>

      {error ? (
        <div role="alert" className="rounded-xl border border-red-800/60 bg-red-950/30 p-5 text-xs text-red-200">
          <p>{error}</p>
          <button onClick={loadExperiences} className="mt-3 font-semibold text-red-100 underline underline-offset-2">
            Try again
          </button>
        </div>
      ) : loading ? (
        <div className="text-center py-12 text-gray-500 text-xs">Loading experience vault...</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12 border border-dashed border-gray-800 rounded-xl bg-gray-950/40">
          <History className="w-10 h-10 text-gray-600 mx-auto mb-2" />
          <p className="text-sm font-semibold text-gray-400">No experiences found</p>
          <p className="text-xs text-gray-600 mt-1">Run a workflow or seed memories to populate vault.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((exp) => (
            <div
              key={exp.experience_id}
              onClick={() => setSelectedExp(exp)}
              className={`border p-4 rounded-xl cursor-pointer transition flex flex-col justify-between group shadow-sm ${
                exp.source === 'workflow' || exp.source === 'agent_run'
                  ? 'bg-gradient-to-r from-indigo-950/40 via-purple-950/20 to-gray-900/90 border-indigo-500/60 hover:border-indigo-400'
                  : 'bg-gray-900/60 border-gray-800 hover:border-gray-700'
              }`}
            >
              <div>
                <div className="flex items-center justify-between pb-2 border-b border-gray-800/60 mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs font-bold text-indigo-400">
                      [{exp.experience_id}]
                    </span>
                    {exp.source === 'workflow' || exp.source === 'agent_run' ? (
                      <span className="flex items-center space-x-1 px-2 py-0.5 bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 rounded text-[10px] font-bold">
                        <Brain className="w-3 h-3 text-indigo-400" />
                        <span>WORKFLOW</span>
                      </span>
                    ) : (
                      <span className="flex items-center space-x-1 px-2 py-0.5 bg-gray-800 text-gray-400 border border-gray-700 rounded text-[10px] font-bold">
                        <Database className="w-3 h-3" />
                        <span>DEMO</span>
                      </span>
                    )}
                  </div>

                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      exp.outcome === 'FAILURE'
                        ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                        : exp.outcome === 'SUCCESS'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    }`}
                  >
                    {exp.outcome}
                  </span>
                </div>

                <h3 className="font-bold text-sm text-gray-200 group-hover:text-indigo-300 transition">
                  {exp.context}
                </h3>
                <p className="text-xs text-gray-400 mt-1 line-clamp-2">{exp.lesson}</p>
              </div>

              <div className="mt-4 pt-2 border-t border-gray-800/60 flex items-center justify-between text-[11px] text-gray-500">
                <div className="flex items-center space-x-1">
                  <Tag className="w-3 h-3 text-gray-600" />
                  <span>{exp.service_name}</span>
                  {exp.workflow_id && <span className="font-mono">· {exp.workflow_id}</span>}
                </div>
                <div className="flex items-center text-indigo-400 font-medium group-hover:translate-x-1 transition-transform">
                  <span>View Details</span>
                  <ChevronRight className="w-4 h-4 ml-0.5" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
