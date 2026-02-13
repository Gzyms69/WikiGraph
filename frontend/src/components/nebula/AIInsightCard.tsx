import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Sparkles, RefreshCw, AlertCircle, Bot } from 'lucide-react';
import { GraphNode } from '../../types/graph';

interface AIInsightCardProps {
  node: GraphNode;
  apiBase: string;
}

interface InsightState {
  status: 'idle' | 'loading' | 'success' | 'error';
  text: string | null;
  provider?: string;
  model?: string;
}

// Global cache to persist insights during the session
const insightCache = new Map<string, InsightState>();

const AIInsightCard: React.FC<AIInsightCardProps> = ({ node, apiBase }) => {
  const [state, setState] = useState<InsightState>({ status: 'idle', text: null });

  // Handle node changes and cache lookup
  useEffect(() => {
    const cacheKey = `${node.lang}:${node.qid}`;
    const cached = insightCache.get(cacheKey);
    
    if (cached) {
      setState(cached);
    } else {
      setState({ status: 'idle', text: null });
    }
  }, [node.qid, node.lang]);

  const fetchInsight = async () => {
    const cacheKey = `${node.lang}:${node.qid}`;
    setState({ status: 'loading', text: null });
    
    try {
      const res = await axios.post(`${apiBase}/ai/analyze/${node.lang}/${node.qid}`);
      const newState: InsightState = {
        status: 'success',
        text: res.data.insight,
        provider: res.data.provider,
        model: res.data.model
      };
      
      // Save to cache
      insightCache.set(cacheKey, newState);
      setState(newState);
    } catch (err) {
      console.error(err);
      setState({ status: 'error', text: 'Failed to generate insight.' });
    }
  };

  if (state.status === 'idle') {
    return (
      <button
        onClick={fetchInsight}
        className="w-full flex items-center justify-center gap-2 py-3 mt-4 bg-gradient-to-r from-purple-500/20 to-blue-500/20 hover:from-purple-500/30 hover:to-blue-500/30 border border-purple-500/30 rounded-xl text-[10px] font-black uppercase tracking-widest text-purple-300 transition-all group"
      >
        <Sparkles size={14} className="group-hover:scale-110 transition-transform" />
        Analyze with AI
      </button>
    );
  }

  return (
    <div className="mt-4 p-4 bg-purple-900/10 border border-purple-500/20 rounded-xl animate-in fade-in slide-in-from-bottom-2">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 text-purple-400">
          <Bot size={14} />
          <span className="text-[10px] font-black uppercase tracking-widest">
            {state.model || 'AI Insight'}
          </span>
        </div>
        {state.status === 'success' && (
          <button onClick={fetchInsight} className="text-purple-400/50 hover:text-purple-300 transition-colors">
            <RefreshCw size={12} />
          </button>
        )}
      </div>

      {state.status === 'loading' && (
        <div className="space-y-2 animate-pulse">
          <div className="h-2 bg-purple-500/20 rounded w-3/4"></div>
          <div className="h-2 bg-purple-500/20 rounded w-full"></div>
          <div className="h-2 bg-purple-500/20 rounded w-5/6"></div>
        </div>
      )}

      {state.status === 'error' && (
        <div className="flex items-center gap-2 text-red-400 text-xs">
          <AlertCircle size={14} />
          <span>Connection failed. Is the backend running?</span>
          <button onClick={fetchInsight} className="underline hover:text-red-300 ml-2">Retry</button>
        </div>
      )}

      {state.status === 'success' && (
        <div className="text-sm text-purple-100/90 leading-relaxed font-light">
          {state.text}
        </div>
      )}
    </div>
  );
};

export default AIInsightCard;
