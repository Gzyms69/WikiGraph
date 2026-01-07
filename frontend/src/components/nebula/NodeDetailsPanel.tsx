import React from 'react';
import { X, Share2, Globe, Activity, ExternalLink, Layers } from 'lucide-react';
import { GraphNode } from '../../types/graph';

interface NodeDetailsPanelProps {
  node: GraphNode | null;
  onClose: () => void;
}

const NodeDetailsPanel: React.FC<NodeDetailsPanelProps> = ({ node, onClose }) => {
  if (!node) return null;

  const connectivity = Math.min((node.val / 20) * 100, 100);

  return (
    <div className="absolute top-28 right-8 z-20 w-80 animate-in slide-in-from-right-4 duration-300 pointer-events-auto">
      <div className="bg-black/60 border border-white/10 rounded-3xl p-6 backdrop-blur-xl shadow-2xl">
        <div className="flex justify-between items-start mb-4">
          <div className="flex gap-2 flex-wrap">
            <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded-lg text-[10px] font-black uppercase tracking-widest border border-blue-500/20">
              Entity
            </span>
            <span className="px-2 py-1 bg-white/5 text-white/40 rounded-lg text-[10px] font-black uppercase tracking-widest border border-white/5">
              {node.lang.toUpperCase()}
            </span>
            {node.community !== undefined && (
              <span className="px-2 py-1 bg-purple-500/20 text-purple-400 rounded-lg text-[10px] font-black uppercase tracking-widest border border-purple-500/20 flex items-center gap-1">
                <Layers size={10} />
                Cluster {node.community}
              </span>
            )}
          </div>
          <button 
            onClick={onClose} 
            className="text-white/20 hover:text-white transition-colors p-1 hover:bg-white/5 rounded-lg"
          >
            <X size={18} />
          </button>
        </div>
        
        <h2 className="text-2xl font-black text-white leading-tight mb-1">{node.name}</h2>
        <p className="text-white/30 text-xs font-mono mb-6 uppercase tracking-tighter">{node.qid}</p>

        <div className="space-y-4">
          <div className="p-4 bg-white/5 rounded-2xl border border-white/5">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Activity className="text-green-500" size={14} />
                <span className="text-[10px] font-bold text-white/60 uppercase tracking-widest">Connectivity</span>
              </div>
              <span className="text-[10px] font-mono text-green-500">{Math.round(connectivity)}%</span>
            </div>
            <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
              <div 
                className="h-full bg-green-500 rounded-full transition-all duration-500" 
                style={{ width: `${connectivity}%` }} 
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <button className="flex items-center justify-center gap-2 py-3 bg-white/5 hover:bg-white/10 border border-white/5 rounded-xl text-[10px] font-black uppercase tracking-widest text-white transition-all group">
              <Share2 size={14} className="group-hover:scale-110 transition-transform" />
              Expand
            </button>
            <a 
              href={`https://${node.lang}.wikipedia.org/wiki/${encodeURIComponent(node.name)}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 py-3 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/20 rounded-xl text-[10px] font-black uppercase tracking-widest text-blue-400 transition-all group"
            >
              <Globe size={14} className="group-hover:rotate-12 transition-transform" />
              Wiki
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NodeDetailsPanel;
