"use client";

import React, { useRef, useEffect, useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import axios from 'axios';
import { Search, Globe, Zap, Loader2, CheckCircle2, ChevronRight, Activity } from 'lucide-react';

const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), {
  ssr: false
});

const API_BASE = "http://localhost:8000";

const LANG_COLORS: Record<string, string> = {
  pl: "#dc143c", // Polish Red
  de: "#ffce00", // German Gold
  en: "#00247d", // Royal Blue
};

interface GraphNode {
  id: string; 
  qid: string;
  name: string;
  val: number;
  lang: string;
  color?: string;
  x?: number;
  y?: number;
  z?: number;
}

interface GraphData {
  nodes: GraphNode[];
  links: any[];
}

const WikiNebula = () => {
  const fgRef = useRef<any>();
  const nodesRef = useRef<GraphNode[]>([]);
  const pendingFocusRef = useRef<string | null>(null);
  
  const [data, setData] = useState<GraphData>({ nodes: [], links: [] });
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [selectedLangs, setSelectedLangs] = useState<string[]>(['pl', 'de']);

  useEffect(() => {
    nodesRef.current = data.nodes;
  }, [data.nodes]);

  // 1. Initial Load
  const startNebula = async () => {
    setIsLoading(true);
    try {
      const langParam = selectedLangs.join(",");
      const res = await axios.get(`${API_BASE}/graph/nebula?langs=${langParam}&limit=150`);
      const nodes = res.data.nodes.map((n: any) => ({
        ...n,
        color: LANG_COLORS[n.lang] || '#555555',
        val: Math.sqrt(n.val) * 2
      }));
      setData({ nodes, links: [] });
      setIsInitialized(true);
    } catch (err) {
      console.error("Failed to fetch nebula", err);
    } finally {
      setIsLoading(false);
    }
  };

  // 2. Search Handler
  const handleSearch = useCallback(async (q: string) => {
    if (q.length < 2) {
      setSearchResults([]);
      return;
    }
    setIsSearching(true);
    try {
      const res = await axios.get(`${API_BASE}/search/keyword?q=${q}&limit=5`);
      setSearchResults(res.data.results);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSearching(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => handleSearch(searchQuery), 300);
    return () => clearTimeout(timer);
  }, [searchQuery, handleSearch]);

  const performCameraFly = (node: any) => {
    if (!fgRef.current) return;
    const distance = 120;
    const distRatio = 1 + distance/Math.hypot(node.x || 0, node.y || 0, node.z || 1);
    fgRef.current.cameraPosition(
      { x: (node.x || 0) * distRatio, y: (node.y || 0) * distRatio, z: (node.z || 0) * distRatio },
      node,
      2000
    );
  };

  // 3. Fly-to and Expand
  const focusOnNode = async (qid: string, title: string, lang: string) => {
    const targetId = `${lang}:${qid}`;
    let targetNode = nodesRef.current.find(n => n.id === targetId);

    if (!targetNode) {
      setIsSearching(true);
      try {
        const neighborsRes = await axios.get(`${API_BASE}/graph/neighbors?qid=${qid}&limit=15`);
        
        const newNode: GraphNode = { 
          id: targetId,
          qid: qid,
          name: title, 
          lang: lang, 
          val: 12, 
          color: LANG_COLORS[lang] || '#555555',
          x: (Math.random() - 0.5) * 100,
          y: (Math.random() - 0.5) * 100,
          z: (Math.random() - 0.5) * 100
        };

        const neighborNodes = neighborsRes.data.neighbors.map((nb: any) => ({
          id: `concept:${nb.qid}`,
          qid: nb.qid,
          name: nb.qid,
          lang: '??',
          val: 5,
          color: '#333333',
          x: (Math.random() - 0.5) * 200,
          y: (Math.random() - 0.5) * 200,
          z: (Math.random() - 0.5) * 200
        }));

        const newLinks = neighborsRes.data.neighbors.map((nb: any) => ({
          source: targetId,
          target: `concept:${nb.qid}`,
          color: '#ffffff11'
        }));

        pendingFocusRef.current = targetId;

        setData(prev => {
          const existingIds = new Set(prev.nodes.map(n => n.id));
          const filteredNewNodes = [newNode, ...neighborNodes].filter(n => !existingIds.has(n.id));
          return {
            nodes: [...prev.nodes, ...filteredNewNodes],
            links: [...prev.links, ...newLinks]
          };
        });

      } catch (err) {
        console.error(err);
      } finally {
        setIsSearching(false);
      }
    } else {
      performCameraFly(targetNode);
    }
    
    setSearchResults([]);
    setSearchQuery("");
  };

  const onEngineTick = () => {
    if (pendingFocusRef.current) {
      const target = nodesRef.current.find((n: any) => n.id === pendingFocusRef.current);
      if (target && typeof target.x === 'number' && Math.abs(target.x) > 1) {
        performCameraFly(target);
        pendingFocusRef.current = null;
      }
    }
  };

  const toggleLang = (l: string) => {
    setSelectedLangs(prev => prev.includes(l) ? prev.filter(x => x !== l) : [...prev, l]);
  };

  return (
    <div className="w-full h-screen bg-black overflow-hidden relative font-sans">
      
      {!isInitialized && (
        <div className="absolute inset-0 z-50 bg-[#050505] flex items-center justify-center p-6">
          <div className="max-w-md w-full bg-white/5 border border-white/10 rounded-3xl p-8 backdrop-blur-3xl shadow-2xl">
            <div className="flex items-center gap-4 mb-8">
              <div className="p-3 bg-blue-600 rounded-2xl shadow-xl shadow-blue-600/20">
                <Zap className="text-white" size={32} />
              </div>
              <div>
                <h2 className="text-3xl font-black text-white tracking-tight italic uppercase">WikiGraph <span className="text-blue-500">Lab</span></h2>
                <p className="text-white/20 text-[9px] font-bold uppercase tracking-[0.3em] mt-2">Initialization Protocol</p>
              </div>
            </div>

            <div className="space-y-6">
              <div className="space-y-2">
                <label className="text-white/30 text-[10px] font-bold uppercase tracking-widest ml-1">Knowledge Clusters</label>
                <div className="grid grid-cols-2 gap-3">
                  {['pl', 'de'].map(l => (
                    <button 
                      key={l}
                      onClick={() => toggleLang(l)}
                      className={`flex items-center justify-between p-4 rounded-2xl border transition-all duration-300 ${
                        selectedLangs.includes(l) 
                        ? 'bg-white/10 border-blue-500/50 scale-[1.02]' 
                        : 'bg-white/5 border-white/5 hover:bg-white/10'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${l === 'pl' ? 'bg-[#dc143c]' : 'bg-[#ffce00]'}`} />
                        <span className="text-white font-bold uppercase tracking-tighter text-xs">{l === 'pl' ? 'Polish' : 'German'}</span>
                      </div>
                      {selectedLangs.includes(l) && <CheckCircle2 className="text-blue-500" size={16} />}
                    </button>
                  ))}
                </div>
              </div>

              <button 
                disabled={selectedLangs.length === 0 || isLoading}
                onClick={startNebula}
                className="w-full py-5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-black rounded-2xl transition-all shadow-2xl shadow-blue-600/20 flex items-center justify-center gap-3 group"
              >
                {isLoading ? <Loader2 className="animate-spin" size={20} /> : (
                  <>
                    SYNTHESIZE NEBULA
                    <ChevronRight className="group-hover:translate-x-1 transition-transform" size={20} />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      <ForceGraph3D
        ref={fgRef}
        graphData={data}
        backgroundColor="#000000"
        showNavInfo={false}
        nodeLabel={(node: any) => `${node.name} (${node.lang.toUpperCase()})`}
        nodeRelSize={1.5}
        nodeVal={(node: any) => node.val}
        nodeColor={(node: any) => node.color}
        linkOpacity={0.15}
        enableNodeDrag={false}
        onNodeClick={(node: any) => focusOnNode(node.qid, node.name, node.lang)}
        onEngineTick={onEngineTick}
      />
      
      {isInitialized && (
        <>
          <div className="absolute top-8 left-8 z-20 pointer-events-none">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500 rounded-lg shadow-lg shadow-blue-500/20">
                <Zap className="text-white" size={24} />
              </div>
              <div>
                <h1 className="text-2xl font-black tracking-tight text-white italic leading-none">
                  WIKIGRAPH <span className="text-blue-400">LAB</span>
                </h1>
                <div className="flex gap-2 items-center mt-2">
                  {selectedLangs.map(l => (
                    <span key={l} className="flex items-center gap-1 px-2 py-0.5 bg-white/5 rounded border border-white/10 text-[8px] font-black text-white/40 uppercase tracking-widest">
                      <div className={`w-1.5 h-1.5 rounded-full ${l === 'pl' ? 'bg-[#dc143c]' : 'bg-[#ffce00]'}`} />
                      {l}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="absolute top-8 right-8 z-30 w-80">
            <div className="relative group">
              <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
                {isSearching ? <Loader2 className="text-blue-400 animate-spin" size={18} /> : <Search className="text-white/30" size={18} />}
              </div>
              <input
                type="text"
                className="w-full bg-black/40 border border-white/10 rounded-2xl py-4 pl-12 pr-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:bg-white/10 transition-all backdrop-blur-xl"
                placeholder="Search the nebula..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              
              {searchResults.length > 0 && (
                <div className="absolute top-full mt-2 w-full bg-black/90 border border-white/10 rounded-2xl overflow-hidden backdrop-blur-2xl shadow-2xl animate-in zoom-in-95 duration-200">
                  {searchResults.map((res, i) => (
                    <button
                      key={i}
                      onClick={() => focusOnNode(res.qid, res.title, res.lang)}
                      className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-white/5 transition-colors border-b border-white/5 last:border-0 group/item"
                    >
                      <div>
                        <span className="text-white/90 font-bold block group-hover/item:text-blue-400 transition-colors text-sm">{res.title}</span>
                        <span className="text-white/20 text-[9px] uppercase font-mono tracking-tighter">{res.qid}</span>
                      </div>
                      <div className="flex items-center gap-1.5 px-2 py-1 bg-white/5 rounded-lg border border-white/5">
                        <div className={`w-2 h-2 rounded-sm ${res.lang === 'pl' ? 'bg-[#dc143c]' : 'bg-[#ffce00]'}`} />
                        <span className="text-[9px] text-white/50 font-black uppercase tracking-tighter">{res.lang}</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="absolute bottom-8 left-8 flex gap-4 pointer-events-none">
            <div className="px-4 py-2 bg-black/40 border border-white/10 rounded-full backdrop-blur-md flex items-center gap-2 shadow-2xl shadow-black">
              <Activity className="text-green-500" size={14} />
              <span className="text-[9px] text-white/60 font-bold uppercase tracking-widest">
                Active Nodes: {data.nodes.length.toLocaleString()}
              </span>
            </div>
          </div>
        </>
      )}

      {isLoading && (
        <div className="absolute inset-0 z-[100] bg-[#050505] flex flex-col items-center justify-center">
          <Loader2 className="text-blue-500 animate-spin mb-6" size={64} />
          <p className="text-white/20 font-mono text-[10px] uppercase tracking-[0.4em] animate-pulse">
            Synthesizing Knowledge Nebula...
          </p>
        </div>
      )}
    </div>
  );
};

export default WikiNebula;