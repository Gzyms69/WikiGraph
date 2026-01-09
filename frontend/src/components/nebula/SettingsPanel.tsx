import React from 'react';
import { X, Cpu, Zap, Activity, BarChart3, Sliders, Info, RefreshCw, AlertTriangle } from 'lucide-react';

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  config: {
    neighborLimit: number;
    forceStrength: number;
    forceDistance: number;
    algorithmWeights: Record<string, number>;
  };
  updateConfig: (key: string, val: any) => void;
  onBulkRefresh: () => void;
}

const SettingsPanel: React.FC<SettingsPanelProps> = ({ isOpen, onClose, config, updateConfig, onBulkRefresh }) => {
  if (!isOpen) return null;

  const algorithms = [
    { id: 'pagerank', name: 'PageRank', icon: <Cpu size={14} />, desc: 'Global importance' },
    { id: 'jaccard', name: 'Jaccard', icon: <Zap size={14} />, desc: 'Direct links' },
    { id: 'adamic_adar', name: 'Adamic-Adar', icon: <Activity size={14} />, desc: 'Shared context' },
  ];

  const handleWeightChange = (id: string, weight: number) => {
    updateConfig('algorithmWeights', { ...config.algorithmWeights, [id]: weight });
  };

  const activeAlgoCount = Object.values(config.algorithmWeights).filter(v => v > 0).length;

  return (
    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-[60] w-[420px] pointer-events-auto">
      <div className="bg-[#0a0a0a]/90 border border-white/10 backdrop-blur-3xl rounded-3xl shadow-[0_0_50px_rgba(0,0,0,0.8)] overflow-hidden flex flex-col max-h-[85vh]">
        
        {/* Header */}
        <div className="p-6 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/10 rounded-lg">
              <Sliders size={18} className="text-blue-400" />
            </div>
            <div>
              <h2 className="text-white font-bold tracking-tight">System Settings</h2>
              <p className="text-white/30 text-[10px] uppercase tracking-widest font-mono">Hybrid Intelligence Engine</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-full text-white/40 hover:text-white transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-8 overflow-y-auto">
          
          {/* Hybrid Ranking Config */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-white/50 uppercase tracking-widest">Weighted Hybrid Ranking</label>
              <div className="group relative">
                <Info size={14} className="text-white/20 cursor-help" />
                <div className="absolute bottom-full right-0 mb-2 w-56 p-2 bg-black border border-white/10 rounded-lg text-[10px] text-white/60 hidden group-hover:block backdrop-blur-xl z-50">
                  Combine multiple algorithms. Scores are normalized and blended based on your weights.
                </div>
              </div>
            </div>
            
            <div className="space-y-3">
              {algorithms.map((algo) => (
                <div key={algo.id} className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-1.5 rounded-lg ${config.algorithmWeights[algo.id] > 0 ? 'bg-blue-500/20 text-blue-400' : 'bg-white/5 text-white/20'}`}>
                        {algo.icon}
                      </div>
                      <div>
                        <div className="text-xs font-bold text-white/80">{algo.name}</div>
                        <div className="text-[10px] text-white/30">{algo.desc}</div>
                      </div>
                    </div>
                    <div className="text-xs font-mono text-blue-400">x{config.algorithmWeights[algo.id]?.toFixed(1)}</div>
                  </div>
                  <input 
                    type="range" min="0" max="5" step="0.5"
                    value={config.algorithmWeights[algo.id] || 0}
                    onChange={(e) => handleWeightChange(algo.id, parseFloat(e.target.value))}
                    className="w-full h-1 bg-white/5 rounded-lg appearance-none cursor-pointer accent-blue-500"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Graph Optimization */}
          <div className="space-y-6 pt-2">
             <div className="space-y-3">
              <div className="flex justify-between items-end">
                <label className="text-[10px] font-bold text-white/40 uppercase tracking-widest">Expansion Limit</label>
                <span className="text-xs font-mono text-blue-400 bg-blue-400/10 px-2 py-0.5 rounded">{config.neighborLimit} Nodes</span>
              </div>
              <input 
                type="range" min="5" max="50" step="5"
                value={config.neighborLimit}
                onChange={(e) => updateConfig('neighborLimit', parseInt(e.target.value))}
                className="w-full h-1.5 bg-white/5 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
            </div>

            <div className="space-y-3">
              <div className="flex justify-between items-end">
                <label className="text-[10px] font-bold text-white/40 uppercase tracking-widest">Charge Strength</label>
                <span className="text-xs font-mono text-amber-400 bg-amber-400/10 px-2 py-0.5 rounded">-{config.forceStrength}</span>
              </div>
              <input 
                type="range" min="30" max="300" step="10"
                value={config.forceStrength}
                onChange={(e) => updateConfig('forceStrength', parseInt(e.target.value))}
                className="w-full h-1.5 bg-white/5 rounded-lg appearance-none cursor-pointer accent-amber-500"
              />
            </div>
          </div>

          {/* Bulk Action */}
          <div className="pt-4">
            <button 
              onClick={onBulkRefresh}
              disabled={activeAlgoCount === 0}
              className={`w-full p-4 rounded-2xl flex items-center justify-center gap-3 transition-all border ${
                activeAlgoCount > 0 
                ? 'bg-amber-500/10 border-amber-500/20 text-amber-400 hover:bg-amber-500/20 shadow-lg shadow-amber-500/5' 
                : 'bg-white/5 border-white/5 text-white/20 cursor-not-allowed'
              }`}
            >
              <RefreshCw size={18} className={activeAlgoCount > 0 ? "animate-spin-slow" : ""} />
              <div className="text-left">
                <div className="text-xs font-bold uppercase tracking-tight">Regenerate Knowledge</div>
                <div className="text-[9px] opacity-60">Re-sync all nodes with current weights</div>
              </div>
            </button>
            <div className="mt-3 flex items-start gap-2 p-3 bg-red-500/5 border border-red-500/10 rounded-xl">
              <AlertTriangle size={14} className="text-red-400/60 mt-0.5 flex-shrink-0" />
              <p className="text-[9px] text-red-400/60 leading-relaxed italic">
                Caution: Regenerating large graphs performs multiple concurrent API calls. Some results may take time to stabilize.
              </p>
            </div>
          </div>

        </div>

        {/* Footer */}
        <div className="p-4 bg-white/[0.01] border-t border-white/5 text-center">
          <p className="text-[9px] text-white/10 uppercase tracking-[0.3em]">WikiGraph Core Engine v1.5.0</p>
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel;
