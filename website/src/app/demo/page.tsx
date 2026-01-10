"use client";

import React, { useState, useRef, useCallback, useEffect } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { ChevronLeft, Search, Info, Zap, Globe, MousePointer2 } from 'lucide-react';
import demoData from '../../demo-data/demo-nebula.json';

const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), { ssr: false });

export default function DemoPage() {
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const fgRef = useRef<any>();

  // Camera focus logic
  const focusNode = useCallback((node: any) => {
    const distance = 100;
    const distRatio = 1 + distance / Math.hypot(node.x || 0, node.y || 0, node.z || 0);

    fgRef.current.cameraPosition(
      { x: (node.x || 0) * distRatio, y: (node.y || 0) * distRatio, z: (node.z || 0) * distRatio },
      node,
      2000
    );
    setSelectedNode(node);
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
      {/* Header */}
      <nav className="z-50 bg-[#050505]/80 backdrop-blur-xl border-b border-white/5 px-6 py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <ChevronLeft className="text-blue-500 group-hover:-translate-x-1 transition-transform" size={20} />
          <span className="font-black italic uppercase tracking-tighter text-sm">Wiki<span className="text-blue-500">Graph</span> Lab</span>
        </Link>
        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20">
            <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
            <span className="text-[9px] font-bold uppercase tracking-widest text-blue-400 italic">Static Demo Environment</span>
          </div>
        </div>
      </nav>

      <div className="flex-1 relative">
        {/* 3D Nebula - Full Viewport */}
        <ForceGraph3D
          ref={fgRef}
          graphData={demoData}
          backgroundColor="#050505"
          nodeLabel="name"
          nodeAutoColorBy="community"
          linkColor={() => "#ffffff22"}
          onNodeClick={focusNode}
          showNavInfo={false}
        />

        {/* Sidebar Controls */}
        <div className="absolute top-6 left-6 z-20 w-80 space-y-4">
          {/* Search Box */}
          <form onSubmit={handleSearch} className="relative group shadow-2xl">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-blue-500 transition-colors" size={18} />
            <input 
              type="text"
              placeholder="Search Knowledge Nebula..."
              className="w-full bg-black/60 border border-white/10 rounded-2xl py-4 pl-12 pr-4 backdrop-blur-2xl focus:outline-none focus:border-blue-500/50 transition-all text-sm"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </form>

          {/* Discovery List - So users know what to search for */}
          <div className="bg-black/40 border border-white/5 rounded-3xl p-6 backdrop-blur-2xl">
            <div className="flex items-center gap-2 mb-4">
              <Globe className="text-blue-500" size={14} />
              <span className="text-[10px] font-bold uppercase tracking-widest text-white/40">Discoverable Topics</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {demoData.nodes.map(node => (
                <button 
                  key={node.id}
                  onClick={() => {
                    const gn = fgRef.current.getGraphData().nodes.find((n: any) => n.id === node.id);
                    if (gn) focusNode(gn);
                  }}
                  className="px-3 py-1.5 bg-white/5 hover:bg-blue-500/20 border border-white/5 rounded-lg text-[10px] font-bold uppercase tracking-tighter transition-all"
                >
                  {node.name}
                </button>
              ))}
            </div>
          </div>

          {/* Selected Node Metadata */}
          {selectedNode && (
            <div className="bg-blue-600/10 border border-blue-500/30 rounded-3xl p-6 backdrop-blur-3xl animate-in fade-in slide-in-from-left-4 duration-500">
              <div className="flex items-center gap-2 mb-4">
                <Info className="text-blue-500" size={16} />
                <span className="text-[10px] font-bold uppercase tracking-widest text-blue-400">Node Properties</span>
              </div>
              <h3 className="text-xl font-black italic uppercase tracking-tighter mb-2">{selectedNode.name}</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-white/40 uppercase font-bold">Language Cluster</span>
                  <span className="text-white font-mono bg-white/10 px-2 py-0.5 rounded uppercase">{selectedNode.lang}</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-white/40 uppercase font-bold">Relative Influence</span>
                  <span className="text-blue-400 font-bold">{selectedNode.val}%</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-white/40 uppercase font-bold">Community ID</span>
                  <span className="text-purple-400 font-bold">#{selectedNode.community}</span>
                </div>
              </div>
              <button 
                onClick={() => setSelectedNode(null)}
                className="w-full mt-6 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-[10px] font-bold uppercase tracking-widest transition-all"
              >
                Clear Focus
              </button>
            </div>
          )}
        </div>

        {/* Interaction Guide */}
        <div className="absolute bottom-6 left-6 z-20 flex items-center gap-6 px-6 py-3 bg-black/60 backdrop-blur-xl rounded-2xl border border-white/5 text-[10px] font-bold uppercase tracking-widest text-white/40">
          <div className="flex items-center gap-2">
            <MousePointer2 size={12} className="text-blue-500" /> Left-Click to Focus
          </div>
          <div className="flex items-center gap-2">
            <Zap size={12} className="text-purple-500" /> Scroll to Zoom
          </div>
          <div className="flex items-center gap-2">
            <Globe size={12} className="text-green-500" /> Drag to Rotate
          </div>
        </div>
      </div>
    </div>
  );
}
