import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { X, Share2, Globe, Layers, Info, Loader2 } from 'lucide-react';
import { GraphNode, NodeMetrics } from '../../types/graph';
import AIInsightCard from './AIInsightCard';

interface NodeDetailsPanelProps {
  node: GraphNode | null;
  onClose: () => void;
}

const API_BASE = "http://localhost:8000/api/v1";

const METRIC_DEFINITIONS = {
  pagerank: {
    label: "Global Importance",
    desc: "Measures the global importance of a node based on the quality and quantity of links pointing to it.",
    formula: "PageRank (Iterative)"
  },
  triangle_count: {
    label: "Local Clustering",
    desc: "The number of triangles (3-node cliques) this node is part of. High values indicate a tight-knit community.",
    formula: "Count(Triangles)"
  },
  auth_score: {
    label: "Authority (HITS)",
    desc: "A measure of how valuable information this node holds, based on links from 'Hub' pages.",
    formula: "HITS Algorithm"
  },
  louvain_id: {
    label: "Community (Coarse)",
    desc: "The ID of the broad community this node belongs to, detected by the Louvain algorithm.",
    formula: "Louvain Modularity"
  },
  leiden_id: {
    label: "Community (Fine)",
    desc: "The ID of the fine-grained sub-community this node belongs to, detected by the Leiden algorithm.",
    formula: "Leiden Algorithm"
  },
  degree: {
    label: "Degree",
    desc: "Total number of direct connections. Incoming (In-degree) and Outgoing (Out-degree).",
    formula: "In-degree + Out-degree"
  }
};

const NodeDetailsPanel: React.FC<NodeDetailsPanelProps> = ({ node, onClose }) => {
  const [metrics, setMetrics] = useState<NodeMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!node) return;

    const fetchData = async () => {
      setIsLoading(true);
      try {
        // Fetch only metrics, which now includes degree data
        const metricsRes = await axios.get(`${API_BASE}/graph/metrics/${node.lang}/${node.qid}`);

        const newMetrics: NodeMetrics = {};

        if (metricsRes.data && metricsRes.data.metrics) {
          const m = metricsRes.data.metrics;
          newMetrics.pagerank = m.pagerank;
          newMetrics.triangle_count = m.triangle_count;
          newMetrics.auth_score = m.auth_score;
          newMetrics.louvain_id = m.louvain_id;
          newMetrics.leiden_id = m.leiden_id;
          newMetrics.degree = m.degree;
          newMetrics.in_degree = m.in_degree;
          newMetrics.out_degree = m.out_degree;
        }

        setMetrics(newMetrics);
      } catch (err) {
        console.error("Failed to fetch node details", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [node]);

  if (!node) return null;

  const renderMetric = (key: keyof NodeMetrics, value: number | undefined) => {
    const def = METRIC_DEFINITIONS[key as keyof typeof METRIC_DEFINITIONS];
    if (value === undefined || !def) return null;

    let displayValue = value.toString();
    if (key === 'pagerank') displayValue = value.toFixed(4);
    if (key === 'auth_score') displayValue = value.toExponential(2);
    if (['triangle_count', 'degree', 'louvain_id', 'leiden_id'].includes(key)) {
      displayValue = Math.round(value).toLocaleString();
    }

    return (
      <div className="flex flex-col p-3 bg-white/5 rounded-xl border border-white/5 relative group">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] font-bold text-white/50 uppercase tracking-widest">{def.label}</span>
          <div className="relative">
             <Info size={10} className="text-white/20 cursor-help" />
             <div className="absolute right-0 bottom-full mb-2 w-48 p-3 bg-gray-900 border border-white/10 rounded-xl shadow-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 text-[10px] text-white/80 leading-relaxed">
               <strong className="block text-white mb-1">{def.formula}</strong>
               {def.desc}
               {key === 'degree' && metrics?.in_degree !== undefined && (
                 <div className="mt-2 pt-2 border-t border-white/10 flex flex-col gap-1">
                    <div className="flex justify-between">
                      <span className="text-white/40">In-degree:</span>
                      <span className="text-blue-400 font-mono">{metrics.in_degree.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/40">Out-degree:</span>
                      <span className="text-blue-400 font-mono">{metrics.out_degree?.toLocaleString()}</span>
                    </div>
                 </div>
               )}
             </div>
          </div>
        </div>
        <span className="text-lg font-mono text-blue-400 font-medium">{displayValue}</span>
      </div>
    );
  };

  return (
    <div className="absolute top-28 right-8 z-20 w-96 animate-in slide-in-from-right-4 duration-300 pointer-events-auto">
      <div className="bg-black/60 border border-white/10 rounded-3xl p-6 backdrop-blur-xl shadow-2xl">
        <div className="flex justify-between items-start mb-4">
          <div className="flex gap-2 flex-wrap">
            <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded-lg text-[10px] font-black uppercase tracking-widest border border-blue-500/20">
              Entity
            </span>
            <span className="px-2 py-1 bg-white/5 text-white/40 rounded-lg text-[10px] font-black uppercase tracking-widest border border-white/5">
              {node.lang.toUpperCase()}
            </span>
            {metrics?.louvain_id !== undefined && (
              <span className="px-2 py-1 bg-purple-500/20 text-purple-400 rounded-lg text-[10px] font-black uppercase tracking-widest border border-purple-500/20 flex items-center gap-1">
                <Layers size={10} />
                Cluster {Math.round(metrics.louvain_id)}
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
        
        <h2 className="text-2xl font-black text-white leading-tight mb-1 break-words">{node.name}</h2>
        <p className="text-white/30 text-xs font-mono mb-6 uppercase tracking-tighter">{node.qid}</p>

        <div className="space-y-4">
          
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
               <Loader2 className="animate-spin text-blue-500" size={24} />
            </div>
          ) : (
             <div className="grid grid-cols-2 gap-2">
               {renderMetric('pagerank', metrics?.pagerank)}
               {renderMetric('auth_score', metrics?.auth_score)}
               {renderMetric('triangle_count', metrics?.triangle_count)}
               {renderMetric('degree', metrics?.degree)}
               {renderMetric('louvain_id', metrics?.louvain_id)}
               {renderMetric('leiden_id', metrics?.leiden_id)}
               
               {!metrics || Object.keys(metrics).length === 0 ? (
                  <div className="col-span-2 text-center py-4 text-white/30 text-xs font-mono uppercase tracking-[0.2em]">
                    No analytical metrics found
                  </div>
               ) : null}
             </div>
          )}

          <div className="grid grid-cols-2 gap-3 pt-2">
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

          <AIInsightCard node={node} apiBase={API_BASE} />
        </div>
      </div>
    </div>
  );
};

export default NodeDetailsPanel;
