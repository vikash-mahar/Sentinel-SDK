import React, { useState, useEffect } from 'react';
import { Shield, Activity, Terminal, Zap, BrainCircuit, History, Search, AlertTriangle, CheckCircle, Bug, Loader2 } from 'lucide-react';

function App() {
  const [history, setHistory] = useState([]);
  const [mentorMsg, setMentorMsg] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [scanResults, setScanResults] = useState([]);
  const [results, setResults] = useState([]);

  // Fetch History and Mentor Data
  const fetchData = async () => {
    try {
      const res = await fetch('./fixes_history.json');
      const data = await res.json();
      setHistory(data.reverse());

      const mentorRes = await fetch('./sentinel_mentor.txt');
      const text = await mentorRes.text();
      const lines = text.trim().split('\n');
      setMentorMsg(lines[lines.length - 1]);
      
      // Fetch scan results if they exist
      const scanRes = await fetch('./scan_results.json');
      if (scanRes.ok) {
        const scanData = await scanRes.json();
        setScanResults(scanData);
      }
    } catch (err) { console.log("Syncing logs..."); }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  // New Trigger for Predictive Scan
  const triggerScan = async () => {
    setIsScanning(true);
    setResults([]); 
    try {
        const response = await fetch('http://localhost:3000/api/sentinel/scan', { method: 'POST' });
        if (response.ok) {
            setTimeout(async () => {
                const dataRes = await fetch(`/scan_results.json?t=${Date.now()}`);
                const data = await dataRes.json();
                
                // FIX: Structure handle karo
                const issues = Array.isArray(data) ? data : (data.vulnerabilities || []);
                setResults(issues);
                
                // FIX: Scanning yahan band karo data aane ke baad
                setIsScanning(false); 
            }, 2000);
        } else {
            setIsScanning(false);
        }
    } catch (err) {
        console.error("Scan failed", err);
        setIsScanning(false);
    }
    // Yahan finally mat lagao jo setIsScanning ko reset kare
};

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
          <div className="flex items-center gap-3 p-3 text-slate-400 hover:bg-slate-800 rounded-lg cursor-pointer transition-all" onClick={triggerScan}>
            <Search size={20}/> Vulnerability Scan
          </div>
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

        {/* PRE-EMPTIVE SCAN SECTION */}
        <section className="mb-8">
          <div className="bg-[#1e293b] border border-slate-700 rounded-2xl p-6 shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-xl font-bold flex items-center gap-2">
                  <Search className="text-blue-400" size={24} /> 
                  Pre-Emptive Vulnerability Scanner
                </h2>
                <p className="text-slate-400 text-sm">Detecting potential crashes before they reach production.</p>
              </div>
              <button 
                onClick={triggerScan}
                disabled={isScanning}
                className={`flex items-center gap-2 px-6 py-2 rounded-xl font-bold transition-all ${
                  isScanning ? 'bg-slate-700 text-slate-500' : 'bg-blue-600 hover:bg-blue-500 shadow-lg shadow-blue-900/20'
                }`}
              >
                {isScanning ? <Loader2 className="animate-spin" size={18} /> : <Zap size={18} fill="currentColor" />}
                {isScanning ? "Scanning Code..." : "Start Deep Scan"}
              </button>
            </div>

            {scanResults.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {scanResults.map((bug, i) => (
                  <div key={i} className={`p-4 rounded-xl border-l-4 ${
                    bug.priority === 'HIGH' ? 'bg-red-500/5 border-red-500' : 'bg-yellow-500/5 border-yellow-500'
                  }`}>
                    <div className="flex justify-between items-start">
                      <span className={`text-[10px] font-black px-2 py-0.5 rounded ${
                        bug.priority === 'HIGH' ? 'bg-red-500' : 'bg-yellow-500'
                      }`}>
                        {bug.priority}
                      </span>
                      <span className="text-slate-500 text-xs font-mono">Line: {bug.line}</span>
                    </div>
                    <h4 className="font-semibold mt-2 text-slate-200">{bug.issue}</h4>
                    <div className="mt-3 flex items-start gap-2 bg-slate-900/50 p-2 rounded-lg">
                      <CheckCircle size={14} className="text-emerald-500 mt-1" />
                      <p className="text-xs text-slate-400"><span className="text-emerald-500 font-bold">Fix:</span> {bug.fix}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-10 border-2 border-dashed border-slate-800 rounded-xl">
                <Bug className="mx-auto text-slate-700 mb-2" size={40} />
                <p className="text-slate-500 text-sm">No vulnerabilities detected. Click 'Start Deep Scan' to analyze.</p>
              </div>
            )}
          </div>
        </section>

        {/* MENTOR ADVICE CARD */}
        <section className="mb-8">
          <div className="bg-gradient-to-r from-slate-800 to-slate-900 p-6 rounded-2xl border-l-4 border-emerald-400 shadow-xl flex items-center gap-6">
            <div className="bg-emerald-500/10 p-4 rounded-xl">
              <BrainCircuit size={32} className="text-emerald-400" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-emerald-400 uppercase tracking-wider">AI Mentor Advice</h3>
              <p className="text-slate-300 mt-1 italic">"{mentorMsg || "No critical issues detected. System is healthy."}"</p>
            </div>
          </div>
        </section>

        {/* STATS GRID */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          {[
            { label: 'Total Auto-Fixes', val: history.length, icon: Zap, color: 'text-yellow-400' },
            { label: 'Uptime Rate', val: '99.98%', icon: Activity, color: 'text-emerald-400' },
            { label: 'Potential Bugs Found', val: scanResults.length, icon: Bug, color: 'text-red-400' }
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
          <div className="p-6 border-b border-slate-700 bg-slate-800/50 flex justify-between items-center">
            <h2 className="text-lg font-semibold">Incident Patch History</h2>
            <History className="text-slate-500" size={20} />
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
                  <React.Fragment key={i}>
                    <tr className="hover:bg-slate-800/40 transition-colors">
                      <td className="px-6 py-4 text-sm text-slate-400">{fix.timestamp}</td>
                      <td className="px-6 py-4"><code className="text-xs bg-slate-900 px-2 py-1 rounded text-emerald-300 font-mono">{fix.file_fixed}</code></td>
                      <td className="px-6 py-4 text-sm max-w-xs truncate text-slate-300">{fix.issue}</td>
                      <td className="px-6 py-4">
                        <span className="bg-emerald-500/10 text-emerald-400 text-[10px] font-bold px-3 py-1 rounded-full border border-emerald-500/20">
                          {fix.status || "PATCHED"}
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td colSpan="4" className="px-6 py-4 bg-slate-900/40">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <p className="text-[10px] text-slate-500 uppercase font-bold mb-2 tracking-widest">Previous Code</p>
                            <pre className="p-4 bg-red-900/10 border border-red-500/20 rounded-lg text-xs font-mono text-red-300 overflow-auto max-h-40">
                              {fix.previous_code || "// Not logged"}
                            </pre>
                          </div>
                          <div>
                            <p className="text-[10px] text-slate-500 uppercase font-bold mb-2 tracking-widest">Sentinel Patch</p>
                            <pre className="p-4 bg-emerald-900/10 border border-emerald-500/20 rounded-lg text-xs font-mono text-emerald-300 overflow-auto max-h-40">
                              {fix.fixed_code || "// Not logged"}
                            </pre>
                          </div>
                        </div>
                      </td>
                    </tr>
                  </React.Fragment>
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