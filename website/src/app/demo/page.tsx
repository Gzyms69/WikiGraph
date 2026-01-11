"use client";

import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import dynamic from 'next/dynamic';
import { 
  ChevronLeft, Info, Zap, Globe, MousePointer2, Code2, 
  Layers, Sparkles, History, Copy, Check, Plus, 
  Maximize2, Compass, ChevronRight, Search, Share2 
} from 'lucide-react';
import { GraphService, Node, Link as GraphLink } from '../../utils/graphService';

// Dynamic Import (No SSR)
const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), { ssr: false });

export default function DemoPage() {
  // --- STATE ---
  const [nodes, setNodes] = useState<Node[]>([]);
  const [links, setLinks] = useState<GraphLink[]>([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [lens, setLens] = useState<'influence' | 'cluster'>('influence');
  const [isRotating, setIsRotating] = useState(true);
  const [dims, setDimensions] = useState({ w: 0, h: 0 }); // Explicit dimensions prevent 0x0 hydration
  
  const fgRef = useRef<any>();

  // --- 1. INITIALIZATION ---
  useEffect(() => {
    // Set Dimensions
    setDimensions({ w: window.innerWidth, h: window.innerHeight });
    window.addEventListener('resize', () => setDimensions({ w: window.innerWidth, h: window.innerHeight }));

    // Load Initial Graph
    const { nodes: initNodes, links: initLinks } = GraphService.getInitialGraph();
    setNodes(initNodes);
    setLinks(initLinks);
  }, []);

  // --- 2. INTERACTION HANDLERS ---
  
  // Focus & Select Node
  const focusNode = useCallback((node: any) => {
    if (!fgRef.current || !node) return;
    setIsRotating(false); // Stop rotation to let user inspect

    const distance = 120;
    const distRatio = 1 + distance / Math.hypot(node.x || 0, node.y || 0, node.z || 0);

    fgRef.current.cameraPosition(
      { x: (node.x || 0) * distRatio, y: (node.y || 0) * distRatio, z: (node.z || 0) * distRatio },
      node,
      1500
    );
    
    setSelectedNode(node);
  }, []);

  // Expand Network (The "Backend" Simulation)
  const expandNode = () => {
    if (!selectedNode) return;
    
    // Ask "Backend" for neighbors
    const newNeighbors = GraphService.getNeighbors(selectedNode.id, nodes);
    
    if (newNeighbors.length === 0) {
      alert("No new neighbors found in this demo dataset.");
      return;
    }

    // Update State
    setNodes(prev => {
      const nextNodes = [...prev, ...newNeighbors];
      // Recalculate links for ALL visible nodes
      const nextLinks = GraphService.getLinksForNodes(nextNodes);
      setLinks(nextLinks); // Batch update links
      return nextNodes;
    });
  };

  // Search
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const result = GraphService.search(searchQuery);
    if (result) {
      // If node is not in view, add it
      if (!nodes.find(n => n.id === result.id)) {
        setNodes(prev => {
          const nextNodes = [...prev, result];
          setLinks(GraphService.getLinksForNodes(nextNodes));
          return nextNodes;
        });
      }
      // Fly to it (small delay to allow render)
      setTimeout(() => {
        const graphNode = fgRef.current?.getGraphData().nodes.find((n: any) => n.id === result.id);
        if (graphNode) focusNode(graphNode);
      }, 100);
    } else {
      alert("Article not found in demo database.");
    }
  };

  // Memoize graph data to prevent jitter
  const graphData = useMemo(() => ({ nodes, links }), [nodes, links]);

  return (
    <div className="h-screen w-screen bg-[#050505] overflow-hidden relative font-sans text-white">
      
      {/* --- HUD: Header --- */}
      <nav className="absolute top-0 left-0 right-0 z-50 bg-[#050505]/80 backdrop-blur-md border-b border-white/5 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <a href="/WikiGraph/" className="flex items-center gap-2 group">
            <ChevronLeft className="text-blue-500 group-hover:-translate-x-1 transition-transform" size={20} />
            <span className="font-black italic uppercase tracking-tighter text-sm">Wiki<span className="text-blue-500">Graph</span> Lab</span>
          </a>
          <div className="h-4 w-px bg-white/10" />
          <div className="flex items-center gap-3">
            <button onClick={() => setLens('influence')} className={`px-3 py-1.5 rounded-full text-[9px] font-bold uppercase border transition-all ${lens === 'influence' ? 'bg-blue-600/20 border-blue-500/50 text-blue-400' : 'bg-white/5 border-white/10 text-white/40'}`}>Influence</button>
            <button onClick={() => setLens('cluster')} className={`px-3 py-1.5 rounded-full text-[9px] font-bold uppercase border transition-all ${lens === 'cluster' ? 'bg-purple-600/20 border-purple-500/50 text-purple-400' : 'bg-white/5 border-white/10 text-white/40'}`}>Clusters</button>
          </div>
        </div>
        <button onClick={() => setIsRotating(!isRotating)} className={`px-4 py-1.5 rounded-full text-[9px] font-bold uppercase border transition-all ${isRotating ? 'border-blue-500/30 text-blue-400' : 'border-white/10 text-white/20'}`}>
          {isRotating ? 'Orbiting' : 'Stationary'}
        </button>
      </nav>

      {/* --- THE GRAPH --- */}
      {dims.w > 0 && (
        <ForceGraph3D
          ref={fgRef}
          width={dims.w}
          height={dims.h}
          graphData={graphData}
          backgroundColor="#050505"
          nodeLabel="name"
          // Interaction
          enableNodeDrag={true}
          onNodeClick={focusNode}
          onNodeDragEnd={focusNode}
          // Visuals
          nodeVal={n => lens === 'influence' ? (n.val || 20) : 20}
          nodeAutoColorBy={lens === 'cluster' ? 'community' : 'lang'}
          nodeRelSize={4}
          linkOpacity={0.2}
          onEngineTick={() => {
            if (isRotating && fgRef.current) {
              const { x, y, z } = fgRef.current.cameraPosition();
              const angle = 0.001; // Slow rotation
              fgRef.current.cameraPosition({
                x: x * Math.cos(angle) - z * Math.sin(angle),
                y: y,
                z: x * Math.sin(angle) + z * Math.cos(angle)
              });
            }
          }}
        />
      )}

      {/* --- SIDEBAR UI --- */}
      <div className="absolute top-24 left-6 z-40 w-80 space-y-4 pointer-events-auto">
        {/* Search Bar */}
        <form onSubmit={handleSearch} className="relative group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-blue-500" size={18} />
          <input 
            type="text" 
            placeholder="Search (e.g. 'Physics')..." 
            className="w-full bg-black/80 border border-white/10 rounded-2xl py-4 pl-12 pr-4 backdrop-blur-xl focus:outline-none focus:border-blue-500/50 text-sm text-white shadow-2xl transition-all" 
            value={searchQuery} 
            onChange={(e) => setSearchQuery(e.target.value)} 
          />
        </form>

        {/* Info Panel */}
        <div className="bg-black/60 border border-white/5 rounded-[2.5rem] p-8 backdrop-blur-3xl shadow-3xl transition-all duration-300">
          {selectedNode ? (
            <div className="animate-in fade-in zoom-in-95 duration-300">
              <div className="flex items-center gap-2 mb-6">
                <Compass className="text-blue-500" size={18} />
                <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-blue-400">Analysis Mode</span>
              </div>
              
              <h3 className="text-3xl font-black italic uppercase tracking-tighter mb-4 leading-none">{selectedNode.name}</h3>
              <p className="text-sm text-white/40 leading-relaxed mb-8 italic">"{selectedNode.desc || "No description available."}"</p>
              
              <div className="grid grid-cols-2 gap-4 mb-8">
                <div className="bg-white/5 border border-white/5 rounded-2xl p-4 text-center">
                  <span className="block text-[9px] font-bold text-white/20 uppercase mb-1">Rank</span>
                  <span className="text-2xl font-black text-blue-400">{selectedNode.val ?? "?"}</span>
                </div>
                <div className="bg-white/5 border border-white/5 rounded-2xl p-4 text-center">
                  <span className="block text-[9px] font-bold text-white/20 uppercase mb-1">Group</span>
                  <span className="text-2xl font-black text-purple-400">#{selectedNode.community}</span>
                </div>
              </div>

              <div className="space-y-3 mb-6">
                <button 
                  onClick={expandNode} 
                  className="w-full flex items-center justify-between px-6 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-2xl font-black uppercase italic text-xs shadow-xl transition-all"
                >
                  <div className="flex items-center gap-2"><Plus size={16} /> Expand</div>
                  <span className="opacity-50 text-[10px]">FETCH NEIGHBORS</span>
                </button>
                
                <button 
                  onClick={() => focusNode(selectedNode)} 
                  className="w-full px-6 py-4 bg-white/5 hover:bg-white/10 border border-white/10 rounded-2xl font-bold uppercase italic text-xs text-white/60 transition-all"
                >
                  Refocus Camera
                </button>
              </div>

              <button onClick={() => setSelectedNode(null)} className="w-full text-white/10 hover:text-white/30 text-[9px] font-bold uppercase tracking-[0.4em]">
                Close Panel
              </button>
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

    </div>
  );
}