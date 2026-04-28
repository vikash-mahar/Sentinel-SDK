import React, { useState, useEffect } from 'react';
import { Shield, Activity, Terminal, Zap, BrainCircuit, History } from 'lucide-react';

function App() {
  const [history, setHistory] = useState([]);
  const [mentorMsg, setMentorMsg] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch('./fixes_history.json');
        const data = await res.json();
        setHistory(data.reverse());

        const mentorRes = await fetch('./sentinel_mentor.txt');
        const text = await mentorRes.text();
        const lines = text.trim().split('\n');
        setMentorMsg(lines[lines.length - 1]);
      } catch (err) { console.log("Syncing logs..."); }
    };
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex min-h-screen bg-[#0f172a] text-slate-200 font-sans">
      
      {/* SIDEBAR */}
      <aside className="w-64 bg-[#020617] border-r border-slate-800 p-6 flex flex-col gap-8">
        <div className="flex items-center gap-3 text-xl font-bold tracking-tight">
          <Shield size={32} className="text-emerald-400" />
          <span>SENTINEL<span className="text-emerald-400">SDK</span></span>
        </div>
        
        <nav className="flex flex-col gap-2">
          <div className="flex items-center gap-3 p-3 bg-slate-800 text-emerald-400 rounded-lg cursor-pointer">
            <Activity size={20}/> Overview
          </div>
          {/* <div className="flex items-center gap-3 p-3 text-slate-400 hover:bg-slate-800 rounded-lg cursor-pointer transition-all">
            <Terminal size={20}/> Live Console
          </div>
          <div className="flex items-center gap-3 p-3 text-slate-400 hover:bg-slate-800 rounded-lg cursor-pointer transition-all">
            <History size={20}/> History
          </div> */}
        </nav>
      </aside>

      {/* MAIN CONTENT */}
      <main className="flex-1 p-8 overflow-y-auto">
        
        {/* TOP BAR */}
        <header className="flex justify-between items-center mb-10">
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
            System Status: <span className="text-emerald-400 font-bold">OPERATIONAL</span>
          </div>
          <div className="bg-slate-800 px-4 py-2 rounded-full text-xs font-medium border border-slate-700">
            Vikas Mahar (Admin)
          </div>
        </header>

        {/* MENTOR ADVICE CARD */}
        <section className="mb-8">
          <div className="bg-gradient-to-r from-slate-800 to-slate-900 p-6 rounded-2xl border-l-4 border-blue-400 shadow-xl flex items-center gap-6">
            <div className="bg-blue-500/10 p-4 rounded-xl">
              <BrainCircuit size={32} className="text-blue-400" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-blue-400 uppercase tracking-wider">AI Mentor Advice</h3>
              <p className="text-slate-300 mt-1 italic">"{mentorMsg || "No critical issues detected. System is healthy."}"</p>
            </div>
          </div>
        </section>

        {/* STATS GRID */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          {[
            { label: 'Total Auto-Fixes', val: history.length, icon: Zap, color: 'text-yellow-400' },
            { label: 'Uptime Rate', val: '99.98%', icon: Activity, color: 'text-emerald-400' },
            { label: 'Avg Patch Time', val: '0.8s', icon: Terminal, color: 'text-blue-400' }
          ].map((stat, i) => (
            <div key={i} className="bg-slate-800/50 p-6 rounded-2xl border border-slate-700 hover:border-slate-500 transition-colors">
              <div className="flex justify-between items-start mb-4">
                <span className="text-slate-400 text-sm font-medium">{stat.label}</span>
                <stat.icon size={20} className={stat.color} />
              </div>
              <div className="text-3xl font-bold text-white">{stat.val}</div>
            </div>
          ))}
        </div>

        {/* LOGS TABLE */}
        <section className="bg-slate-800/30 rounded-2xl border border-slate-700 overflow-hidden">
          <div className="p-6 border-b border-slate-700 bg-slate-800/50">
            <h2 className="text-lg font-semibold">Incident Patch History</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-slate-900/50 text-slate-400 text-xs uppercase">
                <tr>
                  <th className="px-6 py-4">Timestamp</th>
                  <th className="px-6 py-4">Target File</th>
                  <th className="px-6 py-4">Diagnosis</th>
                  <th className="px-6 py-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {history.map((fix, i) => (
                  <>
                  <tr key={i} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-6 py-4 text-sm text-slate-400">{fix.timestamp}</td>
                    <td className="px-6 py-4"><code className="text-xs bg-slate-900 px-2 py-1 rounded text-emerald-300 font-mono">{fix.file_fixed}</code></td>
                    <td className="px-6 py-4 text-sm max-w-xs truncate text-slate-300">{fix.error_detected}</td>
                    <td className="px-6 py-4">
                      <span className="bg-emerald-500/10 text-emerald-400 text-[10px] font-bold px-3 py-1 rounded-full border border-emerald-500/20">
                        PATCHED
                      </span>
                    </td>
                  </tr>

                  <tr>
                  <td colSpan="4" className="px-6 py-4 bg-slate-900/40">
                    <div className="grid grid-cols-2 gap-4 animate-in fade-in slide-in-from-top-2">
                      {/* Previous Code */}
                      <div>
                        <p className="text-[10px] text-slate-500 uppercase font-bold mb-2">Previous Code (Buggy)</p>
                        <pre className="p-4 bg-red-900/10 border border-red-500/20 rounded-lg text-xs font-mono text-red-300 overflow-auto max-h-60">
                          {fix.error_code || "// Original code not logged"}
                        </pre>
                      </div>
                      
                      {/* Corrected Code */}
                      <div>
                        <p className="text-[10px] text-slate-500 uppercase font-bold mb-2">Sentinel Patch (Fixed)</p>
                        <pre className="p-4 bg-emerald-900/10 border border-emerald-500/20 rounded-lg text-xs font-mono text-emerald-300 overflow-auto max-h-60">
                          {fix.corrected_code || "// Fixed code not logged"}
                        </pre>
                      </div>
                    </div>
                  </td>
                </tr>
                  </>
                  
                ))}
              </tbody>
            </table>
          </div>
        </section>

      </main>
    </div>
  );
}

export default App;