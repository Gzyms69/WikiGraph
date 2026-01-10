"use client";

import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { 
  ChevronLeft, Info, Zap, Globe, MousePointer2, Code2, 
  Play, Layers, Sparkles, History, Copy, Check, Plus, 
  Maximize2, Compass, ChevronRight, Search 
} from 'lucide-react';
import masterPool from '../../demo-data/demo-nebula.json';

const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), { ssr: false });

export default function DemoPage() {
  const [nodes, setNodes] = useState<any[]>([]);
  const [links, setLinks] = useState<any[]>([]);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [viewHistory, setViewHistory] = useState<any[]>([]);
  const [lens, setLens] = useState<'influence' | 'cluster'>('influence');
  const [isRotating, setIsRotating] = useState(true);
  const [copied, setCopied] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  
  const fgRef = useRef<any>();

  // ID Helper
  const getId = (idOrObj: any) => typeof idOrObj === 'object' ? idOrObj.id : idOrObj;

  // --- Initial Seed ---
  useEffect(() => {
    const seedIds = ["en:Q1", "en:Q9", "en:Q5", "en:Q13", "en:Q3"];
    const initialNodes = masterPool.nodes.filter(n => seedIds.includes(n.id));
    const initialLinks = masterPool.links.filter(l => 
      seedIds.includes(getId(l.source)) && seedIds.includes(getId(l.target))
    );
    setNodes(initialNodes);
    setLinks(initialLinks);
  }, []);

  // --- Connectivity Scan ---
  // Finds all links in masterPool that connect a list of new nodes to visible nodes
  const findLinksForNodes = (newNodes: any[], currentNodes: any[]) => {
    const allIds = new Set([...currentNodes.map(n => n.id), ...newNodes.map(n => n.id)]);
    return masterPool.links.filter(l => {
      const sId = getId(l.source);
      const tId = getId(l.target);
      return allIds.has(sId) && allIds.has(tId);
    });
  };

  const expandNode = (targetNode: any) => {
    const targetId = getId(targetNode);
    
    // Find neighbors in master pool not currently visible
    const neighbors = masterPool.links
      .filter(l => getId(l.source) === targetId || getId(l.target) === targetId)
      .map(l => getId(l.source) === targetId ? getId(l.target) : getId(l.source));

    const nodesToAdd = masterPool.nodes
      .filter(n => neighbors.includes(n.id) && !nodes.find(v => v.id === n.id))
      .slice(0, 3);

    if (nodesToAdd.length === 0) return;

    setNodes(prevNodes => {
      const nextNodes = [...prevNodes, ...nodesToAdd];
      setLinks(findLinksForNodes(nodesToAdd, prevNodes));
      return nextNodes;
    });
  };

  const focusNode = useCallback((node: any) => {
    if (!fgRef.current || !node) return;
    
    // STOP rotation immediately to prevent fighting the camera animation
    setIsRotating(false);

    const distance = 150;
    const distRatio = 1 + distance / Math.hypot(node.x || 0, node.y || 0, node.z || 0);

    fgRef.current.cameraPosition(
      { x: (node.x || 0) * distRatio, y: (node.y || 0) * distRatio, z: (node.z || 0) * distRatio },
      node,
      2000
    );
    setSelectedNode(node);
    setViewHistory(prev => [node, ...prev.filter(n => n.id !== node.id)].slice(0, 5));
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const query = searchQuery.toLowerCase();
    const found = masterPool.nodes.find(n => n.name.toLowerCase().includes(query));
    
    if (found) {
      const isVisible = nodes.some(n => n.id === found.id);
      if (!isVisible) {
        setNodes(prev => {
          const next = [...prev, found];
          setLinks(findLinksForNodes([found], prev));
          return next;
        });
      }

      setTimeout(() => {
        const graphNode = fgRef.current.getGraphData().nodes.find((n: any) => n.id === found.id);
        if (graphNode) focusNode(graphNode);
      }, 300);
    }
  };

  const walkPath = async () => {
    setIsRotating(false);
    const pathIds = ["en:Q9", "en:Q10", "en:Q2", "en:Q16", "en:Q5"];
    for (const id of pathIds) {
      const nodeObj = masterPool.nodes.find(n => n.id === id);
      if (nodeObj && !nodes.some(n => n.id === id)) {
        setNodes(prev => {
          const next = [...prev, nodeObj];
          setLinks(findLinksForNodes([nodeObj], prev));
          return next;
        });
        await new Promise(r => setTimeout(r, 500));
      }
      
      const graphNode = fgRef.current.getGraphData().nodes.find((n: any) => n.id === id);
      if (graphNode) {
        focusNode(graphNode);
        await new Promise(r => setTimeout(r, 2500));
      }
    }
  };

  // --- Memoized Graph Data to prevent Jitter ---
  const graphData = useMemo(() => ({ nodes, links }), [nodes, links]);

  return (
    <div className="h-screen w-screen bg-[#050505] overflow-hidden flex flex-col font-sans text-white">
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
              className={`px-3 py-1.5 rounded-full text-[9px] font-bold uppercase tracking-widest transition-all border ${
                lens === 'influence' ? 'bg-blue-600/20 border-blue-500/50 text-blue-400' : 'bg-white/5 border-white/10 text-white/40'
              }`}
            >
              Influence Lens
            </button>
            <button 
              onClick={() => setLens('cluster')}
              className={`px-3 py-1.5 rounded-full text-[9px] font-bold uppercase tracking-widest transition-all border ${
                lens === 'cluster' ? 'bg-purple-600/20 border-purple-500/50 text-purple-400' : 'bg-white/5 border-white/10 text-white/40'
              }`}
            >
              Cluster Lens
            </button>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <button onClick={walkPath} className="px-4 py-1.5 bg-blue-600 text-white rounded-full text-[9px] font-bold uppercase tracking-widest shadow-xl">
            Storytelling Mode
          </button>
          <button 
            onClick={() => setIsRotating(!isRotating)}
            className="px-4 py-1.5 rounded-full text-[9px] font-bold uppercase tracking-widest border border-white/10 text-white/20"
          >
            {isRotating ? 'Auto-Rotate ON' : 'Paused'}
          </button>
        </div>
      </nav>

      <div className="flex-1 relative">
        <ForceGraph3D
          ref={fgRef}
          graphData={graphData}
          backgroundColor="#050505"
          nodeLabel="name"
          enableNodeDrag={false} // CRITICAL: Prevents clicks from being interpreted as drags
          onNodeClick={focusNode}
          onNodeHover={node => {
            if (fgRef.current) {
              fgRef.current.renderer().domElement.style.cursor = node ? 'pointer' : 'default';
            }
          }}
          onBackgroundClick={() => setSelectedNode(null)}
          nodeVal={n => lens === 'influence' ? (n.val || 20) : 20}
          nodeAutoColorBy={lens === 'cluster' ? 'community' : 'lang'}
          nodeRelSize={lens === 'influence' ? 1.5 : 6}
          linkOpacity={0.3}
          linkDirectionalParticles={selectedNode ? 4 : 0}
          linkDirectionalParticleWidth={2}
          onEngineTick={() => {
            if (isRotating && fgRef.current) {
              const { x, y, z } = fgRef.current.cameraPosition();
              const angle = 0.002;
              fgRef.current.cameraPosition({
                x: x * Math.cos(angle) - z * Math.sin(angle),
                y: y,
                z: x * Math.sin(angle) + z * Math.cos(angle)
              });
            }
          }}
        />

        {/* UI Overlay - Using pointer-events-none on parent and auto on children */}
        <div className="absolute inset-0 z-20 pointer-events-none flex flex-col p-6">
          <div className="w-80 space-y-4 pointer-events-auto">
            <form onSubmit={handleSearch} className="relative group">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20" size={18} />
              <input 
                type="text"
                placeholder="Search Knowledge (e.g. Linux)..."
                className="w-full bg-black/60 border border-white/10 rounded-2xl py-4 pl-12 pr-4 backdrop-blur-2xl focus:outline-none focus:border-blue-500/50 text-sm text-white"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </form>

            <div className="bg-black/40 border border-white/5 rounded-[2.5rem] p-8 backdrop-blur-3xl shadow-3xl">
              {selectedNode ? (
                <div className="animate-in fade-in zoom-in-95 duration-300">
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-2">
                      <Compass className="text-blue-500" size={18} />
                      <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-blue-400 font-mono">Node Analysis</span>
                    </div>
                  </div>
                  
                  <h3 className="text-3xl font-black italic uppercase tracking-tighter mb-4">{selectedNode.name}</h3>
                  <p className="text-sm text-white/40 leading-relaxed mb-8 italic">"{selectedNode.desc}"</p>
                  
                  <div className="grid grid-cols-2 gap-4 mb-8">
                    <div className="bg-white/5 border border-white/5 rounded-2xl p-4">
                      <span className="block text-[9px] font-bold text-white/20 uppercase mb-1">Influence</span>
                      <span className="text-2xl font-black text-blue-400">{selectedNode.val}%</span>
                    </div>
                    <div className="bg-white/5 border border-white/5 rounded-2xl p-4">
                      <span className="block text-[9px] font-bold text-white/20 uppercase mb-1">Cluster</span>
                      <span className="text-2xl font-black text-purple-400">#{selectedNode.community}</span>
                    </div>
                  </div>

                  <div className="space-y-3 mb-10">
                    <button 
                      onClick={() => expandNode(selectedNode)}
                      className="w-full flex items-center justify-between px-6 py-4 bg-blue-600 text-white rounded-2xl font-black uppercase italic text-xs shadow-xl"
                    >
                      <Plus size={16} /> Expand Cluster
                    </button>
                    <button 
                      onClick={() => focusNode(selectedNode)}
                      className="w-full px-6 py-4 bg-white/5 border border-white/10 rounded-2xl font-bold uppercase italic text-xs text-white/60"
                    >
                      Focus Camera
                    </button>
                  </div>

                  <div className="space-y-2 pt-6 border-t border-white/5">
                    <span className="text-[9px] font-bold text-white/20 uppercase tracking-widest">Cypher Fragment</span>
                    <div className="bg-black/60 rounded-xl p-4 font-mono text-[9px] text-blue-300 break-all border border-white/5">
                      MATCH (n:Article {'{'}qid: '{getId(selectedNode).split(':')[1]}', lang: '{selectedNode.lang}'{'}'}) RETURN n
                    </div>
                  </div>

                  <button 
                    onClick={() => setSelectedNode(null)}
                    className="w-full mt-8 text-white/10 hover:text-white/30 text-[9px] font-bold uppercase tracking-[0.4em]"
                  >
                    Dismiss
                  </button>
                </div>
              ) : (
                <div className="text-center py-12">
                  <MousePointer2 className="mx-auto text-white/10 mb-4 animate-bounce" size={40} />
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/20 leading-loose">
                    Select a knowledge node<br/>to begin exploration.
                  </p>
                </div>
              )}
            </div>

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
                      className="w-full text-left px-4 py-2 hover:bg-white/5 rounded-xl text-[10px] font-bold uppercase tracking-tighter flex items-center justify-between"
                    >
                      <span className="text-white/40">{node.name}</span>
                      <ChevronRight size={12} className="text-blue-500" />
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Legend */}
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 z-20 flex items-center gap-8 px-10 py-5 bg-[#050505]/80 backdrop-blur-2xl rounded-full border border-white/10 text-[9px] font-black uppercase tracking-[0.3em] text-white/20">
          <div className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-blue-500" /> Inspect</div>
          <div className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-purple-500" /> Zoom</div>
          <div className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-green-500" /> Orbit</div>
        </div>
      </div>
    </div>
  );
}