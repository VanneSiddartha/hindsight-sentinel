import React, { useState } from 'react';
import Dashboard from './pages/Dashboard';
import ExperienceHistory from './pages/ExperienceHistory';
import { Shield, History, Activity } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'history'>('dashboard');

  return (
    <div className="min-h-screen bg-[#0B0F19] text-gray-100 flex flex-col font-sans">
      {/* Header / Navbar */}
      <header className="border-b border-gray-800 bg-[#111827]/90 backdrop-blur sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between shadow-md">
        <div className="flex items-center space-x-3">
          <div className="bg-indigo-600/20 p-2 rounded-lg border border-indigo-500/40 text-indigo-400">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-extrabold bg-gradient-to-r from-white via-gray-100 to-indigo-400 bg-clip-text text-transparent tracking-tight">
              AgentVault
            </h1>
            <p className="text-[11px] text-gray-400 font-medium">Shared experience and risk intelligence for AI agent teams.</p>
          </div>
        </div>

        <nav className="flex items-center space-x-1.5 bg-gray-950/80 p-1 rounded-lg border border-gray-800">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-md text-xs font-semibold transition ${
              activeTab === 'dashboard'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'text-gray-400 hover:text-white hover:bg-gray-800/80'
            }`}
          >
            <Activity className="w-4 h-4" />
            <span>AgentVault Dashboard</span>
          </button>

          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-md text-xs font-semibold transition ${
              activeTab === 'history'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'text-gray-400 hover:text-white hover:bg-gray-800/80'
            }`}
          >
            <History className="w-4 h-4" />
            <span>Experience History</span>
          </button>
        </nav>
      </header>

      {/* Main Content */}
      <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'history' && <ExperienceHistory />}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-4 px-6 text-center text-xs text-gray-500 bg-gray-950/50">
        AgentVault &bull; Powered by Vectorize Hindsight Experience Engine & Groq LLM
      </footer>
    </div>
  );
}
