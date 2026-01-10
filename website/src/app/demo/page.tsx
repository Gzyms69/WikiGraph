"use client";

import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { 
  ChevronLeft, Info, Zap, Globe, MousePointer2, Code2, 
  Play, Layers, Sparkles, History, Copy, Check, Plus, 
  Maximize2, Share2, Compass 
} from 'lucide-react';
import masterPool from '../../demo-data/demo-nebula.json';

const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), { ssr: false });

export default function DemoPage() {
  // --- Graph State ---
  const [nodes, setNodes] = useState<any[]>([]);
  const [links, setLinks] = useState<any[]>([]);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [hoverNode, setHoverNode] = useState<any>(null);
  const [viewHistory, setViewHistory] = useState<any[]>([]);
  const [lens, setLens] = useState<'influence' | 'cluster'>('influence');
  const [isRotating, setIsRotating] = useState(true);
  const [copied, setCopied] = useState(false);
  
  const fgRef = useRef<any>();

  // --- Initialize with Seed Data ---
  useEffect(() => {
    const seedIds = ["en:Q1", "en:Q9", "en:Q5", "en:Q13", "en:Q3"];
    const initialNodes = masterPool.nodes.filter(n => seedIds.includes(n.id));
    const initialLinks = masterPool.links.filter(l => seedIds.includes(l.source) && seedIds.includes(l.target));
    setNodes(initialNodes);
    setLinks(initialLinks);
  }, []);

  // --- Exploration Logic ---
  const expandNode = (targetNode: any) => {
    const targetId = targetNode.id;
    
    // Find neighbors in master pool not currently visible
    const potentialLinks = masterPool.links.filter(l => 
      (l.source === targetId || l.target === targetId)
    );
    
    const newLinkData: any[] = [];
    const newNodeData: any[] = [];
    
    potentialLinks.forEach(link => {
      const neighborId = link.source === targetId ? link.target : link.source;
      const alreadyVisible = nodes.some(n => n.id === neighborId);
      
      if (!alreadyVisible) {
        const neighborNode = masterPool.nodes.find(n => n.id === neighborId);
        if (neighborNode) newNodeData.push(neighborNode);
      }
      
      // Add the link if it's not already visible
      const linkExists = links.some(l => 
        (l.source === link.source && l.target === link.target) ||
        (l.source === link.target && l.target === link.source)
      );
      if (!linkExists) newLinkData.push(link);
    });

    if (newNodeData.length === 0 && newLinkData.length === 0) return;

    // Limit expansion to 3 nodes at a time for visual clarity
    const slicedNewNodes = newNodeData.slice(0, 3);
    const slicedIds = new Set(slicedNewNodes.map(n => n.id));
    
    // Only keep links connected to the nodes we are adding
    const validNewLinks = newLinkData.filter(l => 
      slicedIds.has(l.source) || slicedIds.has(l.target) || 
      (nodes.some(n => n.id === l.source) && nodes.some(n => n.id === l.target))
    );

    setNodes(prev => [...prev, ...slicedNewNodes]);
    setLinks(prev => [...prev, ...validNewLinks]);
  };

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
    const pathIds = ["en:Q9", "en:Q10", "en:Q2", "en:Q16", "en:Q5"];
    for (const id of pathIds) {
      const nodeInMaster = masterPool.nodes.find(n => n.id === id);
      // Ensure node is visible
      setNodes(prev => prev.some(n => n.id === id) ? prev : [...prev, nodeInMaster]);
      
      // Give time for simulation to update
      await new Promise(r => setTimeout(r, 100));
      
      const graphNode = fgRef.current.getGraphData().nodes.find((n: any) => n.id === id);
      if (graphNode) {
        focusNode(graphNode);
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
            <span className="font-black italic uppercase tracking-tighter text-sm">Wiki<span className="text-blue-500 text-glow">Graph</span> Lab</span>
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
            <Play size={10} fill="currentColor" /> Storytelling Mode
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
          graphData={{ nodes, links }}
          backgroundColor="#050505"
          nodeLabel="name"
          onNodeClick={focusNode}
          onNodeHover={setHoverNode}
          showNavInfo={false}
          
          // Lens Logic
          nodeVal={n => lens === 'influence' ? (n.val || 20) : 20}
          nodeAutoColorBy={lens === 'cluster' ? 'community' : 'lang'}
          
          // Visuals
          nodeRelSize={lens === 'influence' ? 1 : 6}
          linkOpacity={0.3}
          linkWidth={1}
          linkDirectionalParticles={2}
          linkDirectionalParticleSpeed={0.005}
          linkDirectionalParticleWidth={link => {
            const active = selectedNode || hoverNode;
            if (!active) return 0;
            const sId = (link.source as any).id || link.source;
            const tId = (link.target as any).id || link.target;
            return sId === active.id || tId === active.id ? 2 : 0;
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

        {/* Action Panel (The "Menu") */}
        <div className="absolute top-6 left-6 z-20 w-80 space-y-4">
          <div className="bg-black/40 border border-white/5 rounded-[2.5rem] p-8 backdrop-blur-3xl shadow-[0_0_50px_-12px_rgba(59,130,246,0.2)]">
            {selectedNode ? (
              <div className="animate-in fade-in zoom-in-95 duration-500">
                <div className="flex items-center justify-between mb-8">
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-blue-500/20 rounded-xl">
                      <Compass className="text-blue-500" size={18} />
                    </div>
                    <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-blue-400">Node Navigator</span>
                  </div>
                  <span className="text-[10px] font-mono text-white/20 uppercase tracking-tighter italic">{selectedNode.lang} edition</span>
                </div>
                
                <h3 className="text-3xl font-black italic uppercase tracking-tighter mb-4 leading-[0.9]">{selectedNode.name}</h3>
                <p className="text-sm text-white/40 leading-relaxed mb-10 italic">"{selectedNode.desc}"</p>
                
                {/* Metrics */}
                <div className="grid grid-cols-2 gap-4 mb-10">
                  <div className="bg-white/5 border border-white/5 rounded-2xl p-4">
                    <span className="block text-[9px] font-bold text-white/20 uppercase mb-1 tracking-widest italic">PageRank</span>
                    <span className="text-2xl font-black text-blue-400">{(selectedNode.val || 20)}%</span>
                  </div>
                  <div className="bg-white/5 border border-white/5 rounded-2xl p-4">
                    <span className="block text-[9px] font-bold text-white/20 uppercase mb-1 tracking-widest italic">Cluster</span>
                    <span className="text-2xl font-black text-purple-400">#{selectedNode.community}</span>
                  </div>
                </div>

                {/* Primary Actions */}
                <div className="space-y-3 mb-10">
                  <button 
                    onClick={() => expandNode(selectedNode)}
                    className="w-full flex items-center justify-between px-6 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-2xl font-black uppercase italic text-xs transition-all shadow-xl shadow-blue-600/20 group"
                  >
                    <div className="flex items-center gap-3">
                      <Plus size={16} />
                      Expand Knowledge
                    </div>
                    <ChevronRight size={14} className="group-hover:translate-x-1 transition-transform" />
                  </button>
                  <button 
                    onClick={() => focusNode(selectedNode)}
                    className="w-full flex items-center justify-between px-6 py-4 bg-white/5 hover:bg-white/10 border border-white/10 rounded-2xl font-bold uppercase italic text-xs transition-all"
                  >
                    <div className="flex items-center gap-3 text-white/60">
                      <Maximize2 size={16} />
                      Focus Camera
                    </div>
                  </button>
                </div>

                {/* Developer Tool */}
                <div className="space-y-3 pt-8 border-t border-white/5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Code2 className="text-white/20" size={14} />
                      <span className="text-[10px] font-bold text-white/20 uppercase tracking-widest">Cypher Query</span>
                    </div>
                    <button onClick={copyCypher} className="text-blue-500 hover:text-blue-400 transition-colors p-1 bg-blue-500/10 rounded-lg">
                      {copied ? <Check size={12} /> : <Copy size={12} />}
                    </button>
                  </div>
                  <div className="bg-black/60 rounded-xl p-5 font-mono text-[10px] text-blue-300 leading-relaxed break-all border border-white/5 shadow-inner italic">
                    MATCH (n:Article {'{'}qid: '{selectedNode.id.split(':')[1]}', lang: '{selectedNode.lang}'{'}'}) RETURN n
                  </div>
                </div>

                <button 
                  onClick={() => setSelectedNode(null)}
                  className="w-full mt-10 py-3 text-white/20 hover:text-white/40 text-[9px] font-bold uppercase tracking-[0.4em] transition-all"
                >
                  &mdash; Dismiss Analysis &mdash;
                </button>
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="relative inline-block mb-8">
                  <MousePointer2 className="text-white/10 animate-bounce" size={48} />
                  <Sparkles className="absolute -top-2 -right-2 text-blue-500/30 animate-pulse" size={32} />
                </div>
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-white/20 leading-loose">
                  Navigate the Knowledge Nebula.<br/>
                  Select a node to begin<br/>the expansion protocol.
                </p>
              </div>
            )}
          </div>

          {/* Knowledge Trail */}
          {viewHistory.length > 0 && (
            <div className="bg-black/40 border border-white/5 rounded-[2rem] p-6 backdrop-blur-2xl">
              <div className="flex items-center gap-2 mb-4 text-white/20">
                <History size={14} />
                <span className="text-[9px] font-bold uppercase tracking-[0.2em]">Research Trail</span>
              </div>
              <div className="space-y-2">
                {viewHistory.map(node => (
                  <button 
                    key={node.id}
                    onClick={() => focusNode(node)}
                    className="w-full text-left px-4 py-2 hover:bg-white/5 rounded-xl text-[10px] font-bold uppercase tracking-tighter transition-all flex items-center justify-between group"
                  >
                    <span className="text-white/40 group-hover:text-white/80">{node.name}</span>
                    <ChevronLeft className="opacity-0 group-hover:opacity-100 transition-opacity rotate-180 text-blue-500" size={12} />
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Interaction Guide HUD */}
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 z-20 flex items-center gap-8 px-10 py-5 bg-[#050505]/80 backdrop-blur-2xl rounded-full border border-white/10 text-[9px] font-black uppercase tracking-[0.3em] text-white/20 shadow-3xl">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]" />
            L-Click to Inspect
          </div>
          <div className="h-4 w-px bg-white/10" />
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.5)]" />
            Scroll to Zoom
          </div>
          <div className="h-4 w-px bg-white/10" />
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)]" />
            R-Click to Orbit
          </div>
        </div>
      </div>
    </div>
  );
}