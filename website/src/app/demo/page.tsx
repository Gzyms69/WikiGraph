"use client";

import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { 
  ChevronLeft, Info, Zap, Globe, MousePointer2, Code2, 
  Layers, Sparkles, History, Copy, Check, Plus, 
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
  const [dims, setDimensions] = useState({ w: 0, h: 0 });
  
  const fgRef = useRef<any>();

  // Resize handler
  useEffect(() => {
    setDimensions({ w: window.innerWidth, h: window.innerHeight });
    const handleResize = () => setDimensions({ w: window.innerWidth, h: window.innerHeight });
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const getId = (idOrObj: any) => typeof idOrObj === 'object' ? idOrObj.id : idOrObj;

  useEffect(() => {
    const seedIds = ["en:Q1", "en:Q9", "en:Q5", "en:Q13", "en:Q3"];
    const initialNodes = masterPool.nodes.filter(n => seedIds.includes(n.id));
    const initialLinks = masterPool.links.filter(l => 
      seedIds.includes(getId(l.source)) && seedIds.includes(getId(l.target))
    );
    setNodes(initialNodes);
    setLinks(initialLinks);
  }, []);

  const findLinksForNodes = (newNodes: any[], currentNodes: any[]) => {
    const allVisibleIds = new Set([...currentNodes.map(n => n.id), ...newNodes.map(n => n.id)]);
    return masterPool.links.filter(l => {
      const sId = getId(l.source);
      const tId = getId(l.target);
      return allVisibleIds.has(sId) && allVisibleIds.has(tId);
    });
  };

  const expandNode = (targetNode: any) => {
    const targetId = getId(targetNode);
    const neighbors = masterPool.links
      .filter(l => getId(l.source) === targetId || getId(l.target) === targetId)
      .map(l => getId(l.source) === targetId ? getId(l.target) : getId(l.source));

    const nodesToAdd = masterPool.nodes
      .filter(n => neighbors.includes(n.id) && !nodes.find(v => v.id === n.id))
      .slice(0, 3);

    if (nodesToAdd.length === 0) return;

    setNodes(prev => {
      const next = [...prev, ...nodesToAdd];
      setLinks(findLinksForNodes(nodesToAdd, prev));
      return next;
    });
  };

  const focusNode = useCallback((node: any) => {
    if (!fgRef.current || !node) return;
    
    console.log("ACTIVATE MENU:", node);
    setIsRotating(false);

    const distance = 160;
    const distRatio = 1 + distance / Math.hypot(node.x || 0, node.y || 0, node.z || 0);

    fgRef.current.cameraPosition(
      { x: (node.x || 0) * distRatio, y: (node.y || 0) * distRatio, z: (node.z || 0) * distRatio },
      node,
      1500
    );
    
    setSelectedNode(node);
    setViewHistory(prev => [node, ...prev.filter(n => n.id !== node.id)].slice(0, 5));
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const query = searchQuery.toLowerCase();
    const found = masterPool.nodes.find(n => n.name.toLowerCase().includes(query));
    
    if (found) {
      if (!nodes.some(n => n.id === found.id)) {
        setNodes(prev => {
          const next = [...prev, found];
          setLinks(findLinksForNodes([found], prev));
          return next;
        });
      }
      setTimeout(() => {
        const graphNode = fgRef.current?.getGraphData().nodes.find((n: any) => n.id === found.id);
        if (graphNode) focusNode(graphNode);
      }, 200);
    }
  };

  const copyCypher = () => {
    if (!selectedNode) return;
    const qid = getId(selectedNode).split(':')[1];
    const query = `MATCH (n:Article {qid: '${qid}', lang: '${selectedNode.lang}'}) RETURN n`;
    navigator.clipboard.writeText(query);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const graphData = useMemo(() => ({ nodes, links }), [nodes, links]);

  return (
    <div className="h-screen w-screen bg-[#050505] overflow-hidden relative font-sans text-white">
      {/* Top HUD */}
      <nav className="absolute top-0 left-0 right-0 z-50 bg-[#050505]/80 backdrop-blur-md border-b border-white/5 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2 group">
            <ChevronLeft className="text-blue-500 group-hover:-translate-x-1 transition-transform" size={20} />
            <span className="font-black italic uppercase tracking-tighter text-sm">Wiki<span className="text-blue-500 text-glow">Graph</span> Lab</span>
          </Link>
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

      {/* GRAPH CONTAINER */}
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
          // Changed from onNodeDragStart (invalid) to onNodeDragEnd (valid)
          // This ensures that when you finish dragging a node, the menu opens
          onNodeDragEnd={focusNode}
          onNodeHover={node => {
            if (fgRef.current) fgRef.current.renderer().domElement.style.cursor = node ? 'pointer' : 'default';
          }}
          // Intentionally removed onBackgroundClick to prevent accidental menu closing
          nodeVal={n => lens === 'influence' ? (n.val || 20) : 20}
          nodeAutoColorBy={lens === 'cluster' ? 'community' : 'lang'}
          nodeRelSize={lens === 'influence' ? 6 : 4} 
          linkOpacity={0.3}
          linkDirectionalParticles={selectedNode ? 4 : 0}
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
      )}

      {/* Sidebar Interface */}
      <div className="absolute top-24 left-6 z-40 w-80 space-y-4 pointer-events-auto border-2 border-transparent hover:border-blue-500/20 transition-colors">
        <form onSubmit={handleSearch} className="relative group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-blue-500" size={18} />
          <input type="text" placeholder="Find Article..." className="w-full bg-black/80 border border-white/10 rounded-2xl py-4 pl-12 pr-4 backdrop-blur-xl focus:outline-none focus:border-blue-500/50 text-sm text-white shadow-2xl" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
        </form>

        <div className="bg-black/60 border border-white/5 rounded-[2.5rem] p-8 backdrop-blur-3xl shadow-3xl transition-all duration-300">
          {selectedNode ? (
            <div className="animate-in fade-in zoom-in-95 duration-300">
              <div className="flex items-center gap-2 mb-6"><Compass className="text-blue-500" size={18} /><span className="text-[10px] font-bold uppercase tracking-[0.3em] text-blue-400">Analysis Mode</span></div>
              <h3 className="text-3xl font-black italic uppercase tracking-tighter mb-4 leading-none">{selectedNode.name}</h3>
              <p className="text-sm text-white/40 leading-relaxed mb-8 italic">"{selectedNode.desc}"</p>
              <div className="grid grid-cols-2 gap-4 mb-8">
                <div className="bg-white/5 border border-white/5 rounded-2xl p-4 text-center"><span className="block text-[9px] font-bold text-white/20 uppercase mb-1">Rank</span><span className="text-2xl font-black text-blue-400">{selectedNode.val}%</span></div>
                <div className="bg-white/5 border border-white/5 rounded-2xl p-4 text-center"><span className="block text-[9px] font-bold text-white/20 uppercase mb-1">Group</span><span className="text-2xl font-black text-purple-400">#{selectedNode.community}</span></div>
              </div>
              <div className="space-y-3 mb-10">
                <button onClick={() => expandNode(selectedNode)} className="w-full flex items-center justify-between px-6 py-4 bg-blue-600 text-white rounded-2xl font-black uppercase italic text-xs shadow-xl">
                  <Plus size={16} /> Expand Knowledge
                </button>
                <button onClick={() => focusNode(selectedNode)} className="w-full px-6 py-4 bg-white/5 border border-white/10 rounded-2xl font-bold uppercase italic text-xs text-white/60">
                  Refocus Camera
                </button>
              </div>
              <div className="space-y-2 pt-6 border-t border-white/5 text-left">
                <div className="flex items-center justify-between mb-2"><span className="text-[9px] font-bold text-white/20 uppercase tracking-widest">Cypher Query</span><button onClick={copyCypher} className="text-blue-500 hover:text-blue-400">{copied ? <Check size={12} /> : <Copy size={12} />}</button></div>
                <div className="bg-black/60 rounded-xl p-4 font-mono text-[9px] text-blue-300 break-all border border-white/5">MATCH (n:Article {'{'}qid: '{getId(selectedNode).split(':')[1]}', lang: '{selectedNode.lang}'{'}'}) RETURN n</div>
              </div>
              <button onClick={() => setSelectedNode(null)} className="w-full mt-8 text-white/10 hover:text-white/30 text-[9px] font-bold uppercase tracking-[0.4em]">Deselect</button>
            </div>
          ) : (
            <div className="text-center py-12"><MousePointer2 className="mx-auto text-white/5 mb-4 animate-pulse" size={48} /><p className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/20 leading-loose">Select a node to begin<br/>the analysis sequence.</p></div>
          )}
        </div>

        {viewHistory.length > 0 && (
          <div className="bg-black/60 border border-white/5 rounded-[2rem] p-6 backdrop-blur-3xl shadow-xl">
            <div className="flex items-center gap-2 mb-4 text-white/20"><History size={14} /><span className="text-[9px] font-bold uppercase tracking-[0.2em]">Research Trail</span></div>
            <div className="space-y-2">{viewHistory.map(node => (
              <button key={node.id} onClick={() => focusNode(node)} className="w-full text-left px-4 py-2 hover:bg-white/5 rounded-xl text-[10px] font-bold uppercase tracking-tighter flex items-center justify-between group">
                <span className="text-white/40 group-hover:text-white/80">{node.name}</span>
                <ChevronRight size={12} className="text-blue-500 opacity-0 group-hover:opacity-100" />
              </button>
            ))}</div>
          </div>
        )}
      </div>

      {/* HUD: Legend */}
      <div className="absolute bottom-10 right-10 z-40 flex flex-col items-end gap-3">
        <div className="bg-black/80 backdrop-blur-xl px-4 py-2 rounded-xl border border-white/5 flex items-center gap-3 shadow-2xl">
          <div className="w-1.5 h-1.5 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]" />
          <span className="text-[9px] font-bold uppercase tracking-widest text-white/40 italic">Neural Connector</span>
        </div>
        <div className="bg-black/80 backdrop-blur-xl px-4 py-2 rounded-xl border border-white/5 flex items-center gap-3 shadow-2xl">
          <div className="w-1.5 h-1.5 rounded-full bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.5)]" />
          <span className="text-[9px] font-bold uppercase tracking-widest text-white/40 italic">Semantic Cluster</span>
        </div>
      </div>
    </div>
  );
}