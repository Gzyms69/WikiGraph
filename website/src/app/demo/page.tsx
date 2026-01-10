"use client";

import React, { useState, useRef, useCallback, useMemo } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { ChevronLeft, Search, Info, Zap, Globe, MousePointer2, Settings2, Sparkles, History } from 'lucide-react';
import demoData from '../../demo-data/demo-nebula.json';

const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), { ssr: false });

export default function DemoPage() {
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [hoverNode, setHoverNode] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewHistory, setViewHistory] = useState<any[]>([]);
  const [isRotating, setIsRotating] = useState(true);
  
  const fgRef = useRef<any>();

  // Determine neighbors for highlighting
  const neighbors = useMemo(() => {
    if (!selectedNode && !hoverNode) return new Set();
    const activeNode = selectedNode || hoverNode;
    const n = new Set();
    demoData.links.forEach(link => {
      if ((link.source as any).id === activeNode.id || link.source === activeNode.id) n.add(link.target);
      if ((link.target as any).id === activeNode.id || link.target === activeNode.id) n.add(link.source);
    });
    return n;
  }, [selectedNode, hoverNode]);

  const focusNode = useCallback((node: any) => {
    if (!fgRef.current) return;
    
    // Smooth camera transition
    const distance = 120;
    const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);

    fgRef.current.cameraPosition(
      { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
      node,
      2000
    );

    setSelectedNode(node);
    setViewHistory(prev => [node, ...prev.filter(n => n.id !== node.id)].slice(0, 5));
    setIsRotating(false); // Stop rotation when inspecting
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const node = demoData.nodes.find(n => n.name.toLowerCase().includes(searchQuery.toLowerCase()));
    if (node && fgRef.current) {
      const graphNode = fgRef.current.getGraphData().nodes.find((n: any) => n.id === node.id);
      if (graphNode) focusNode(graphNode);
    }
  };

  return (
    <div className="h-screen w-screen bg-[#050505] overflow-hidden flex flex-col font-sans text-white">
      {/* Interactive HUD Overlay */}
      <nav className="z-50 bg-[#050505]/80 backdrop-blur-xl border-b border-white/5 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2 group">
            <ChevronLeft className="text-blue-500 group-hover:-translate-x-1 transition-transform" size={20} />
            <span className="font-black italic uppercase tracking-tighter text-sm">Wiki<span className="text-blue-500">Graph</span> Lab</span>
          </Link>
          <div className="h-4 w-px bg-white/10 hidden md:block" />
          <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20">
            <Sparkles className="text-blue-400" size={12} />
            <span className="text-[9px] font-bold uppercase tracking-widest text-blue-400 italic">Interlingual Nebula Demo (English)</span>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <button 
            onClick={() => setIsRotating(!isRotating)}
            className={`px-4 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest transition-all border ${
              isRotating ? 'bg-blue-600/20 border-blue-500/50 text-blue-400' : 'bg-white/5 border-white/10 text-white/40'
            }`}
          >
            {isRotating ? 'Auto-Rotate ON' : 'Rotation Paused'}
          </button>
        </div>
      </nav>

      <div className="flex-1 relative">
        <ForceGraph3D
          ref={fgRef}
          graphData={demoData}
          backgroundColor="#050505"
          nodeLabel="name"
          nodeAutoColorBy="community"
          onNodeClick={focusNode}
          onNodeHover={setHoverNode}
          showNavInfo={false}
          
          // Interaction Styling
          nodeOpacity={1}
          nodeRelSize={6}
          linkOpacity={0.2}
          linkWidth={1}
          
          // Animation
          onEngineTick={() => {
            if (isRotating && fgRef.current) {
              const { x, y, z } = fgRef.current.cameraPosition();
              const angle = 0.002;
              const newX = x * Math.cos(angle) - z * Math.sin(angle);
              const newZ = x * Math.sin(angle) + z * Math.cos(angle);
              fgRef.current.cameraPosition({ x: newX, y, z: newZ });
            }
          }}

          // Spotlight Mode logic
          nodeThreeObjectExtend={true}
          linkDirectionalParticles={2}
          linkDirectionalParticleSpeed={0.005}
          linkDirectionalParticleWidth={link => {
            const activeNode = selectedNode || hoverNode;
            if (!activeNode) return 0;
            return (link.source as any).id === activeNode.id || (link.target as any).id === activeNode.id ? 2 : 0;
          }}
        />

        {/* HUD: Left Column */}
        <div className="absolute top-6 left-6 z-20 w-80 space-y-4">
          <form onSubmit={handleSearch} className="relative group shadow-2xl">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-blue-500 transition-colors" size={18} />
            <input 
              type="text"
              placeholder="Jump to Topic..."
              className="w-full bg-black/60 border border-white/10 rounded-2xl py-4 pl-12 pr-4 backdrop-blur-2xl focus:outline-none focus:border-blue-500/50 transition-all text-sm"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </form>

          {/* Metadata Panel */}
          <div className="bg-black/40 border border-white/5 rounded-[2rem] p-6 backdrop-blur-2xl shadow-2xl">
            {selectedNode ? (
              <div className="animate-in fade-in slide-in-from-top-4 duration-500">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-2">
                    <Info className="text-blue-500" size={16} />
                    <span className="text-[10px] font-bold uppercase tracking-widest text-blue-400">Knowledge Node</span>
                  </div>
                  <span className="text-[10px] font-mono text-white/20">ID: {selectedNode.id}</span>
                </div>
                
                <h3 className="text-2xl font-black italic uppercase tracking-tighter mb-4 leading-none">{selectedNode.name}</h3>
                <p className="text-sm text-white/40 leading-relaxed mb-8 italic">"{selectedNode.desc}"</p>
                
                <div className="grid grid-cols-2 gap-4 mb-8">
                  <div className="bg-white/5 border border-white/5 rounded-2xl p-4">
                    <span className="block text-[9px] font-bold text-white/20 uppercase mb-1 tracking-widest">PageRank</span>
                    <span className="text-lg font-black text-blue-400">{selectedNode.val}%</span>
                  </div>
                  <div className="bg-white/5 border border-white/5 rounded-2xl p-4">
                    <span className="block text-[9px] font-bold text-white/20 uppercase mb-1 tracking-widest">Community</span>
                    <span className="text-lg font-black text-purple-400">#{selectedNode.community}</span>
                  </div>
                </div>

                <button 
                  onClick={() => setSelectedNode(null)}
                  className="w-full py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-[10px] font-bold uppercase tracking-widest transition-all"
                >
                  Deselect Node
                </button>
              </div>
            ) : (
              <div className="text-center py-12">
                <MousePointer2 className="mx-auto text-white/10 mb-4 animate-bounce" size={32} />
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-white/20 leading-loose">
                  Select a node in the nebula<br/>to analyze its structural properties.
                </p>
              </div>
            )}
          </div>

          {/* History / Recent Panel */}
          {viewHistory.length > 0 && (
            <div className="bg-black/40 border border-white/5 rounded-[2rem] p-6 backdrop-blur-2xl shadow-2xl">
              <div className="flex items-center gap-2 mb-4">
                <History className="text-blue-500" size={14} />
                <span className="text-[10px] font-bold uppercase tracking-widest text-white/40">Recent History</span>
              </div>
              <div className="space-y-2">
                {viewHistory.map(node => (
                  <button 
                    key={node.id}
                    onClick={() => focusNode(node)}
                    className="w-full text-left px-4 py-2 hover:bg-white/5 rounded-xl text-[10px] font-bold uppercase tracking-tighter transition-all border border-transparent hover:border-white/5"
                  >
                    {node.name}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Interaction Guide HUD */}
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20 flex items-center gap-8 px-8 py-4 bg-black/60 backdrop-blur-xl rounded-full border border-white/10 text-[9px] font-bold uppercase tracking-[0.2em] text-white/40 shadow-3xl">
          <div className="flex items-center gap-2">
            <div className="w-1 h-1 rounded-full bg-blue-500" />
            Left-Click Node to Focus
          </div>
          <div className="h-3 w-px bg-white/10" />
          <div className="flex items-center gap-2">
            <div className="w-1 h-1 rounded-full bg-purple-500" />
            Scroll to Zoom Depth
          </div>
          <div className="h-3 w-px bg-white/10" />
          <div className="flex items-center gap-2">
            <div className="w-1 h-1 rounded-full bg-green-500" />
            Right-Click/Drag to Orbit
          </div>
        </div>
      </div>
    </div>
  );
}