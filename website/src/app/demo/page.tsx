"use client";

import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { ChevronLeft, Search, Info, Zap, Globe, MousePointer2, Code2, Play, Layers, Sparkles, History, Copy, Check } from 'lucide-react';
import demoData from '../../demo-data/demo-nebula.json';

const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), { ssr: false });

export default function DemoPage() {
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [hoverNode, setHoverNode] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewHistory, setViewHistory] = useState<any[]>([]);
  const [lens, setLens] = useState<'influence' | 'cluster'>('influence');
  const [isRotating, setIsRotating] = useState(true);
  const [copied, setCopied] = useState(false);
  
  const fgRef = useRef<any>();

  // Camera focus logic
  const focusNode = useCallback((node: any) => {
    if (!fgRef.current) return;
    const distance = 120;
    const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);
    fgRef.current.cameraPosition(
      { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
      node,
      2000
    );
    setSelectedNode(node);
    setViewHistory(prev => [node, ...prev.filter(n => n.id !== node.id)].slice(0, 5));
    setIsRotating(false);
  }, []);

  const walkPath = async () => {
    setIsRotating(false);
    const pathIds = ["en:Q9", "en:Q10", "en:Q2", "en:Q14", "en:Q5"];
    for (const id of pathIds) {
      const node = fgRef.current.getGraphData().nodes.find((n: any) => n.id === id);
      if (node) {
        focusNode(node);
        await new Promise(r => setTimeout(r, 2500));
      }
    }
  };

  const copyCypher = () => {
    if (!selectedNode) return;
    const query = `MATCH (n:Article {qid: '${selectedNode.id.split(':')[1]}', lang: '${selectedNode.lang}'}) RETURN n`;
    navigator.clipboard.writeText(query);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="h-screen w-screen bg-[#050505] overflow-hidden flex flex-col font-sans text-white selection:bg-blue-500/30">
      {/* Navigation HUD */}
      <nav className="z-50 bg-[#050505]/80 backdrop-blur-xl border-b border-white/5 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2 group">
            <ChevronLeft className="text-blue-500 group-hover:-translate-x-1 transition-transform" size={20} />
            <span className="font-black italic uppercase tracking-tighter text-sm">Wiki<span className="text-blue-500">Graph</span> Lab</span>
          </Link>
          <div className="h-4 w-px bg-white/10 hidden md:block" />
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setLens('influence')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-[9px] font-bold uppercase tracking-widest transition-all border ${
                lens === 'influence' ? 'bg-blue-600/20 border-blue-500/50 text-blue-400' : 'bg-white/5 border-white/10 text-white/40'
              }`}
            >
              <Zap size={12} /> Influence Lens
            </button>
            <button 
              onClick={() => setLens('cluster')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-[9px] font-bold uppercase tracking-widest transition-all border ${
                lens === 'cluster' ? 'bg-purple-600/20 border-purple-500/50 text-purple-400' : 'bg-white/5 border-white/10 text-white/40'
              }`}
            >
              <Layers size={12} /> Cluster Lens
            </button>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <button 
            onClick={walkPath}
            className="flex items-center gap-2 px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-full text-[9px] font-bold uppercase tracking-widest transition-all shadow-xl shadow-blue-600/20"
          >
            <Play size={10} fill="currentColor" /> Walk the Path
          </button>
          <button 
            onClick={() => setIsRotating(!isRotating)}
            className={`px-4 py-1.5 rounded-full text-[9px] font-bold uppercase tracking-widest transition-all border ${
              isRotating ? 'bg-white/10 border-white/20 text-white' : 'bg-white/5 border-white/10 text-white/20'
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
          onNodeClick={focusNode}
          onNodeHover={setHoverNode}
          showNavInfo={false}
          
          // Lens Logic
          nodeVal={n => lens === 'influence' ? n.val : 20}
          nodeAutoColorBy={lens === 'cluster' ? 'community' : 'lang'}
          
          // Visuals
          nodeRelSize={lens === 'influence' ? 1 : 6}
          linkOpacity={0.3}
          linkWidth={1}
          linkDirectionalParticles={2}
          linkDirectionalParticleWidth={link => {
            const active = selectedNode || hoverNode;
            if (!active) return 0;
            return (link.source as any).id === active.id || (link.target as any).id === active.id ? 2 : 0;
          }}

          // Physics Animation
          onEngineTick={() => {
            if (isRotating && fgRef.current) {
              const { x, y, z } = fgRef.current.cameraPosition();
              const angle = 0.002;
              const newX = x * Math.cos(angle) - z * Math.sin(angle);
              const newZ = x * Math.sin(angle) + z * Math.cos(angle);
              fgRef.current.cameraPosition({ x: newX, y: newZ });
            }
          }}
        />

        {/* Sidebar Controls */}
        <div className="absolute top-6 left-6 z-20 w-80 space-y-4">
          {/* Metadata & Researcher Box */}
          <div className="bg-black/40 border border-white/5 rounded-[2rem] p-6 backdrop-blur-2xl shadow-3xl">
            {selectedNode ? (
              <div className="animate-in fade-in slide-in-from-top-4 duration-500">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-2">
                    <Info className="text-blue-500" size={16} />
                    <span className="text-[10px] font-bold uppercase tracking-widest text-blue-400">Node Analyzer</span>
                  </div>
                  <span className="text-[10px] font-mono text-white/20 uppercase">{selectedNode.lang} Cluster</span>
                </div>
                
                <h3 className="text-2xl font-black italic uppercase tracking-tighter mb-4">{selectedNode.name}</h3>
                <p className="text-sm text-white/40 leading-relaxed mb-8 italic">"{selectedNode.desc}"</p>
                
                <div className="grid grid-cols-2 gap-4 mb-8">
                  <div className="bg-white/5 border border-white/5 rounded-2xl p-4">
                    <span className="block text-[9px] font-bold text-white/20 uppercase mb-1 tracking-widest italic">PageRank</span>
                    <span className="text-xl font-black text-blue-400">{selectedNode.val}%</span>
                  </div>
                  <div className="bg-white/5 border border-white/5 rounded-2xl p-4">
                    <span className="block text-[9px] font-bold text-white/20 uppercase mb-1 tracking-widest italic">Cluster</span>
                    <span className="text-xl font-black text-purple-400">#{selectedNode.community}</span>
                  </div>
                </div>

                {/* Researcher's Tool: Cypher Export */}
                <div className="space-y-3 pt-6 border-t border-white/5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Code2 className="text-white/20" size={12} />
                      <span className="text-[9px] font-bold text-white/20 uppercase tracking-widest">Cypher Query</span>
                    </div>
                    <button onClick={copyCypher} className="text-blue-500 hover:text-blue-400 transition-colors">
                      {copied ? <Check size={12} /> : <Copy size={12} />}
                    </button>
                  </div>
                  <div className="bg-black/60 rounded-xl p-4 font-mono text-[10px] text-blue-300 leading-relaxed break-all border border-white/5">
                    MATCH (n:Article {'{'}qid: '{selectedNode.id.split(':')[1]}', lang: '{selectedNode.lang}'{'}'}) RETURN n
                  </div>
                </div>

                <button 
                  onClick={() => setSelectedNode(null)}
                  className="w-full mt-8 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-[10px] font-bold uppercase tracking-widest transition-all"
                >
                  Deselect Node
                </button>
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="relative inline-block mb-6">
                  <MousePointer2 className="text-white/10 animate-bounce" size={40} />
                  <Sparkles className="absolute -top-2 -right-2 text-blue-500/20 animate-pulse" size={24} />
                </div>
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-white/20 leading-loose">
                  Interact with the nebula<br/>to analyze its structural data.
                </p>
              </div>
            )}
          </div>

          {/* History Panel */}
          {viewHistory.length > 0 && (
            <div className="bg-black/40 border border-white/5 rounded-[2rem] p-6 backdrop-blur-2xl">
              <div className="flex items-center gap-2 mb-4">
                <History className="text-blue-500" size={14} />
                <span className="text-[10px] font-bold uppercase tracking-widest text-white/40">Knowledge Trail</span>
              </div>
              <div className="space-y-2">
                {viewHistory.map(node => (
                  <button 
                    key={node.id}
                    onClick={() => focusNode(node)}
                    className="w-full text-left px-4 py-2 hover:bg-white/5 rounded-xl text-[10px] font-bold uppercase tracking-tighter transition-all flex items-center justify-between group"
                  >
                    <span>{node.name}</span>
                    <ChevronLeft className="opacity-0 group-hover:opacity-100 transition-opacity rotate-180" size={12} />
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Legend Overlay */}
        <div className="absolute bottom-6 right-6 z-20 flex flex-col items-end gap-2">
          <div className="bg-black/60 backdrop-blur-xl px-4 py-2 rounded-xl border border-white/5 flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-[#1e40af]" />
            <span className="text-[9px] font-bold uppercase tracking-widest text-white/40 italic">English Core</span>
          </div>
          <div className="bg-black/60 backdrop-blur-xl px-4 py-2 rounded-xl border border-white/5 flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-[#dc143c]" />
            <span className="text-[9px] font-bold uppercase tracking-widest text-white/40 italic">Interlingual Bridge</span>
          </div>
        </div>
      </div>
    </div>
  );
}