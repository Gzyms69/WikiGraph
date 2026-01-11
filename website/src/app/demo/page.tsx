"use client";

import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import dynamic from 'next/dynamic';
import { 
  ChevronLeft, Info, Zap, Globe, MousePointer2, Code2, 
  Layers, Sparkles, History, Copy, Check, Plus, 
  Maximize2, Compass, ChevronRight, Search, Share2, HelpCircle, X 
} from 'lucide-react';
import { GraphService, Node, Link as GraphLink } from '../../utils/graphService';

const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), { ssr: false });

export default function DemoPage() {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [links, setLinks] = useState<GraphLink[]>([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState<Node[]>([]);
  const [lens, setLens] = useState<'influence' | 'cluster'>('influence');
  const [isRotating, setIsRotating] = useState(true);
  const [dims, setDimensions] = useState({ w: 0, h: 0 });
  const [showWelcome, setShowWelcome] = useState(true);

  const fgRef = useRef<any>();

  // Init
  useEffect(() => {
    setDimensions({ w: window.innerWidth, h: window.innerHeight });
    const handleResize = () => setDimensions({ w: window.innerWidth, h: window.innerHeight });
    window.addEventListener('resize', handleResize);
    
    const { nodes: initNodes, links: initLinks } = GraphService.getInitialGraph();
    setNodes(initNodes);
    setLinks(initLinks);

    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Update forces when ref is ready
  useEffect(() => {
    if (fgRef.current) {
      // Stronger repulsion and longer links to keep nodes separate
      fgRef.current.d3Force('charge').strength(-400);
      fgRef.current.d3Force('link').distance(100);
    }
  }, [nodes]);

  // --- INTERACTION ---
  const focusNode = useCallback((node: any) => {
    if (!node) return;
    setIsRotating(false);
    
    if (fgRef.current) {
      const distance = 150;
      const distRatio = 1 + distance / Math.hypot(node.x || 0, node.y || 0, node.z || 0);
      fgRef.current.cameraPosition(
        { x: (node.x || 0) * distRatio, y: (node.y || 0) * distRatio, z: (node.z || 0) * distRatio },
        node,
        1500
      );
    }
    
    setSelectedNode(node);
  }, []);

  const expandNode = () => {
    if (!selectedNode) return;
    const newNeighbors = GraphService.getNeighbors(selectedNode.id, nodes);
    if (newNeighbors.length === 0) {
      alert("No new neighbors found in this demo dataset.");
      return;
    }
    setNodes(prev => {
      const nextNodes = [...prev, ...newNeighbors];
      setLinks(GraphService.getLinksForNodes(nextNodes));
      return nextNodes;
    });
  };

  const handleSearchInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setSearchQuery(val);
    setSuggestions(GraphService.getSuggestions(val));
  };

  const executeSearch = (queryOrNode: string | Node) => {
    let result: Node | undefined;
    
    if (typeof queryOrNode === 'string') {
      result = GraphService.search(queryOrNode);
    } else {
      result = queryOrNode;
    }

    if (result) {
      setSearchQuery(result.name);
      setSuggestions([]);

      if (!nodes.find(n => n.id === result!.id)) {
        setNodes(prev => {
          const nextNodes = [...prev, result!];
          setLinks(GraphService.getLinksForNodes(nextNodes));
          return nextNodes;
        });
      }
      setTimeout(() => {
        const graphNode = fgRef.current?.getGraphData().nodes.find((n: any) => n.id === result!.id);
        if (graphNode) focusNode(graphNode);
      }, 100);
    } else {
      alert("Not found.");
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    executeSearch(searchQuery);
  };

  const graphData = useMemo(() => ({ nodes, links }), [nodes, links]);

  return (
    <div className="h-screen w-screen bg-[#050505] overflow-hidden relative font-sans text-white">
      
      {/* HEADER */}
      <nav className="absolute top-0 left-0 right-0 z-50 bg-[#050505]/80 backdrop-blur-md border-b border-white/5 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <a href="/WikiGraph/" className="flex items-center gap-2 group">
            <ChevronLeft className="text-blue-500 group-hover:-translate-x-1 transition-transform" size={20} />
            <span className="font-black italic uppercase tracking-tighter text-sm">Wiki<span className="text-blue-500 text-glow">Graph</span> Lab</span>
          </a>
          <div className="h-4 w-px bg-white/10" />
          <div className="flex items-center gap-3">
            <button onClick={() => setLens('influence')} className={`px-3 py-1.5 rounded-full text-[9px] font-bold uppercase border transition-all ${lens === 'influence' ? 'bg-blue-600/20 border-blue-500/50 text-blue-400' : 'bg-white/5 border-white/10 text-white/40'}`}>Influence</button>
            <button onClick={() => setLens('cluster')} className={`px-3 py-1.5 rounded-full text-[9px] font-bold uppercase border transition-all ${lens === 'cluster' ? 'bg-purple-600/20 border-purple-500/50 text-purple-400' : 'bg-white/5 border-white/10 text-white/40'}`}>Clusters</button>
          </div>
        </div>
        <div className="flex items-center gap-4">
           <button onClick={() => setShowWelcome(true)} className="flex items-center gap-2 px-3 py-1.5 text-[9px] font-bold uppercase text-white/40 hover:text-white transition-colors">
            <HelpCircle size={14} /> Help
           </button>
           <button onClick={() => setIsRotating(!isRotating)} className={`px-4 py-1.5 rounded-full text-[9px] font-bold uppercase border transition-all ${isRotating ? 'border-blue-500/30 text-blue-400' : 'border-white/10 text-white/20'}`}>
            {isRotating ? 'Orbiting' : 'Stationary'}
          </button>
        </div>
      </nav>

      {/* GRAPH */}
      {dims.w > 0 && (
        <ForceGraph3D
          ref={fgRef}
          width={dims.w}
          height={dims.h}
          graphData={graphData}
          backgroundColor="#050505"
          nodeLabel="name"
          enableNodeDrag={true}
          onNodeClick={focusNode}
          onNodeDragEnd={focusNode}
          // SIZES VARY ACCORDING TO PAGERANK (importance)
          nodeVal={n => Math.pow(n.val / 10, 2.5)} 
          nodeAutoColorBy={lens === 'cluster' ? 'community' : 'lang'}
          nodeRelSize={1} // Base size adjusted for the power-scale nodeVal
          linkWidth={2}
          linkOpacity={0.5}
          onNodeHover={node => {
            if (fgRef.current) fgRef.current.renderer().domElement.style.cursor = node ? 'pointer' : 'default';
          }}
          onEngineTick={() => {
            if (isRotating && fgRef.current) {
              const { x, y, z } = fgRef.current.cameraPosition();
              const angle = 0.001;
              fgRef.current.cameraPosition({
                x: x * Math.cos(angle) - z * Math.sin(angle),
                y: y,
                z: x * Math.sin(angle) + z * Math.cos(angle)
              });
            }
          }}
        />
      )}

      {/* SIDEBAR */}
      <div className="absolute top-24 left-6 z-40 w-80 space-y-4 pointer-events-auto">
        <div className="relative group">
          <form onSubmit={handleSearchSubmit}>
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-blue-500" size={18} />
            <input 
              type="text" 
              placeholder="Search (e.g. 'History')..." 
              className="w-full bg-black/80 border border-white/10 rounded-2xl py-4 pl-12 pr-4 backdrop-blur-xl focus:outline-none focus:border-blue-500/50 text-sm text-white shadow-2xl transition-all" 
              value={searchQuery} 
              onChange={handleSearchInput} 
            />
          </form>
          {suggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-black/90 border border-white/10 rounded-xl overflow-hidden shadow-2xl animate-in fade-in slide-in-from-top-2">
              {suggestions.map(s => (
                <button 
                  key={s.id}
                  onClick={() => executeSearch(s)}
                  className="w-full text-left px-4 py-3 hover:bg-blue-600/20 hover:text-blue-300 text-xs font-bold uppercase tracking-wide border-b border-white/5 last:border-0 flex justify-between items-center group/item"
                >
                  {s.name}
                  <ChevronRight size={12} className="opacity-0 group-hover/item:opacity-100 transition-opacity" />
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="bg-black/60 border border-white/5 rounded-[2.5rem] p-8 backdrop-blur-3xl shadow-3xl transition-all duration-300">
          {selectedNode ? (
            <div className="animate-in fade-in zoom-in-95 duration-300">
              <div className="flex items-center gap-2 mb-6">
                <Compass className="text-blue-500" size={18} />
                <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-blue-400">Analysis Mode</span>
              </div>
              <h3 className="text-3xl font-black italic uppercase tracking-tighter mb-4 leading-none">{selectedNode.name}</h3>
              <p className="text-sm text-white/40 leading-relaxed mb-8 italic">"{selectedNode.desc || "No desc"}"</p>
              
              <div className="grid grid-cols-2 gap-4 mb-8">
                <div className="bg-white/5 border border-white/5 rounded-2xl p-4 text-center">
                  <span className="block text-[9px] font-bold text-white/20 uppercase mb-1">Rank</span>
                  <span className="text-2xl font-black text-blue-400">{selectedNode.val}%</span>
                </div>
                <div className="bg-white/5 border border-white/5 rounded-2xl p-4 text-center">
                  <span className="block text-[9px] font-bold text-white/20 uppercase mb-1">Group</span>
                  <span className="text-2xl font-black text-purple-400">#{selectedNode.community}</span>
                </div>
              </div>

              <div className="space-y-3 mb-6">
                <button onClick={expandNode} className="w-full flex items-center justify-between px-6 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-2xl font-black uppercase italic text-xs shadow-xl transition-all">
                  <div className="flex items-center gap-2"><Plus size={16} /> Expand</div>
                </button>
                <button onClick={() => setSelectedNode(null)} className="w-full text-white/10 hover:text-white/30 text-[9px] font-bold uppercase tracking-[0.4em]">
                  Close Panel
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 opacity-50">
              <MousePointer2 className="mx-auto text-white/20 mb-4 animate-bounce" size={32} />
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/40">Select a node</p>
            </div>
          )}
        </div>
      </div>
      
      {/* Legend */}
      <div className="absolute bottom-10 right-10 z-40 flex flex-col items-end gap-3 pointer-events-none">
        <div className="bg-black/40 backdrop-blur-md px-4 py-2 rounded-xl border border-white/5 flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.8)]" />
          <span className="text-[9px] font-bold uppercase tracking-widest text-white/40">High Influence</span>
        </div>
        <div className="bg-black/40 backdrop-blur-md px-4 py-2 rounded-xl border border-white/5 flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.8)]" />
          <span className="text-[9px] font-bold uppercase tracking-widest text-white/40">Cluster Core</span>
        </div>
      </div>

      {/* ONBOARDING MODAL */}
      {showWelcome && (
        <div className="absolute inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-500">
          <div className="bg-[#0a0a0a] border border-white/10 p-8 rounded-[2rem] max-w-lg w-full shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full blur-[100px] -translate-y-1/2 translate-x-1/2 pointer-events-none" />
            <div className="relative z-10">
              <div className="flex justify-between items-start mb-6">
                <div>
                   <h2 className="text-3xl font-black italic uppercase tracking-tighter text-white mb-2">Wiki<span className="text-blue-500 text-glow">Graph</span> Lab</h2>
                   <p className="text-sm text-white/50">Interactive 3D Knowledge Navigator</p>
                </div>
                <button onClick={() => setShowWelcome(false)} className="p-2 hover:bg-white/10 rounded-full transition-colors"><X size={20} className="text-white/40" /></button>
              </div>
              <div className="space-y-4 mb-8">
                <div className="flex gap-4 items-start">
                  <div className="p-3 bg-blue-500/10 rounded-xl text-blue-400"><MousePointer2 size={20} /></div>
                  <div>
                    <h4 className="text-sm font-bold uppercase tracking-wide text-white mb-1">Navigate & Interact</h4>
                    <p className="text-xs text-white/60 leading-relaxed">Drag background to rotate. Scroll to zoom. <span className="text-blue-400">Click or Drag nodes</span> to view details.</p>
                  </div>
                </div>
                <div className="flex gap-4 items-start">
                  <div className="p-3 bg-purple-500/10 rounded-xl text-purple-400"><Search size={20} /></div>
                  <div>
                    <h4 className="text-sm font-bold uppercase tracking-wide text-white mb-1">Search & Discover</h4>
                    <p className="text-xs text-white/60 leading-relaxed">Use the search bar to find topics like "Music" or "Physics".</p>
                  </div>
                </div>
                <div className="flex gap-4 items-start">
                  <div className="p-3 bg-green-500/10 rounded-xl text-green-400"><Plus size={20} /></div>
                  <div>
                    <h4 className="text-sm font-bold uppercase tracking-wide text-white mb-1">Expand Knowledge</h4>
                    <p className="text-xs text-white/60 leading-relaxed">Click the <span className="text-green-400">Expand</span> button in the panel to reveal hidden connections.</p>
                  </div>
                </div>
              </div>
              <button onClick={() => setShowWelcome(false)} className="w-full py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-black uppercase tracking-widest text-xs transition-all shadow-lg hover:shadow-blue-500/25">
                Start Exploring
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}