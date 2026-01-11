"use client";

import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import dynamic from 'next/dynamic';
import { 
  ChevronLeft, Info, Zap, Globe, MousePointer2, Code2, 
  Layers, Sparkles, History, Copy, Check, Plus, 
  Maximize2, Compass, ChevronRight, Search, Share2, Bug 
} from 'lucide-react';
import { GraphService, Node, Link as GraphLink } from '../../utils/graphService';

const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), { ssr: false });

export default function DemoPage() {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [links, setLinks] = useState<GraphLink[]>([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [lens, setLens] = useState<'influence' | 'cluster'>('influence');
  const [isRotating, setIsRotating] = useState(true);
  const [dims, setDimensions] = useState({ w: 0, h: 0 });
  const [debugMsg, setDebugMsg] = useState("Init");

  const fgRef = useRef<any>();

  // Resize
  useEffect(() => {
    setDimensions({ w: window.innerWidth, h: window.innerHeight });
    window.addEventListener('resize', () => setDimensions({ w: window.innerWidth, h: window.innerHeight }));
    
    // Init Graph
    const { nodes: initNodes, links: initLinks } = GraphService.getInitialGraph();
    setNodes(initNodes);
    setLinks(initLinks);
    setDebugMsg("Graph Loaded. Nodes: " + initNodes.length);
  }, []);

  // --- DEBUG LOGGER ---
  const log = (msg: string, obj?: any) => {
    console.log(`[DemoDebug] ${msg}`, obj || '');
    setDebugMsg(`${msg} ${obj ? JSON.stringify(obj.id || 'obj') : ''}`);
  };

  // --- INTERACTION ---
  const focusNode = useCallback((node: any) => {
    log("CLICK EVENT FIRED:", node);
    
    if (!node) {
      log("Error: Node is null");
      return;
    }

    setIsRotating(false);
    
    // Camera Move
    if (fgRef.current) {
      const distance = 120;
      const distRatio = 1 + distance / Math.hypot(node.x || 0, node.y || 0, node.z || 0);
      fgRef.current.cameraPosition(
        { x: (node.x || 0) * distRatio, y: (node.y || 0) * distRatio, z: (node.z || 0) * distRatio },
        node,
        1500
      );
    }
    
    // STATE UPDATE
    log("Setting SelectedNode State...", node.name);
    setSelectedNode(node);
  }, []);

  // Manual Debug Trigger
  const forceSelectDebug = () => {
    const target = nodes[0];
    if (target) {
      log("Force Selecting:", target);
      focusNode(target);
    }
  };

  const expandNode = () => {
    if (!selectedNode) return;
    const newNeighbors = GraphService.getNeighbors(selectedNode.id, nodes);
    if (newNeighbors.length === 0) {
      alert("No new neighbors.");
      return;
    }
    setNodes(prev => {
      const nextNodes = [...prev, ...newNeighbors];
      setLinks(GraphService.getLinksForNodes(nextNodes));
      return nextNodes;
    });
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const result = GraphService.search(searchQuery);
    if (result) {
      if (!nodes.find(n => n.id === result.id)) {
        setNodes(prev => {
          const nextNodes = [...prev, result];
          setLinks(GraphService.getLinksForNodes(nextNodes));
          return nextNodes;
        });
      }
      setTimeout(() => {
        const graphNode = fgRef.current?.getGraphData().nodes.find((n: any) => n.id === result.id);
        if (graphNode) focusNode(graphNode);
      }, 100);
    } else {
      alert("Not found.");
    }
  };

  const graphData = useMemo(() => ({ nodes, links }), [nodes, links]);

  // RENDER LOG
  console.log("RENDER: SelectedNode is", selectedNode ? selectedNode.name : "NULL");

  return (
    <div className="h-screen w-screen bg-[#050505] overflow-hidden relative font-sans text-white">
      
      {/* HUD HEADER */}
      <nav className="absolute top-0 left-0 right-0 z-50 bg-[#050505]/80 backdrop-blur-md border-b border-white/5 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <a href="/WikiGraph/" className="flex items-center gap-2 group">
            <ChevronLeft className="text-blue-500" size={20} />
            <span className="font-bold text-sm">WikiGraph Lab</span>
          </a>
          <div className="h-4 w-px bg-white/10" />
          <div className="text-[10px] font-mono text-yellow-400 bg-yellow-400/10 px-2 py-1 rounded">
            DEBUG: {debugMsg}
          </div>
          <button onClick={forceSelectDebug} className="flex items-center gap-2 px-3 py-1 bg-red-500/20 text-red-400 text-xs font-bold rounded hover:bg-red-500/30">
            <Bug size={12} /> Force Select Node[0]
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
          nodeVal={20}
          nodeRelSize={4}
          onNodeHover={node => {
            if (fgRef.current) fgRef.current.renderer().domElement.style.cursor = node ? 'pointer' : 'default';
          }}
        />
      )}

      {/* SIDEBAR UI */}
      <div className="absolute top-24 left-6 z-40 w-80 space-y-4 pointer-events-auto">
        <form onSubmit={handleSearch} className="relative group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20" size={18} />
          <input 
            type="text" 
            placeholder="Search..." 
            className="w-full bg-black/80 border border-white/10 rounded-2xl py-4 pl-12 pr-4 text-sm text-white" 
            value={searchQuery} 
            onChange={(e) => setSearchQuery(e.target.value)} 
          />
        </form>

        <div className="bg-black/60 border border-white/5 rounded-[2.5rem] p-8 backdrop-blur-3xl shadow-3xl">
          {selectedNode ? (
            <div className="animate-in fade-in zoom-in-95 duration-300">
              <div className="flex items-center gap-2 mb-6">
                <Compass className="text-blue-500" size={18} />
                <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-blue-400">Analysis Mode</span>
              </div>
              <h3 className="text-3xl font-black italic uppercase tracking-tighter mb-4 leading-none">{selectedNode.name}</h3>
              <p className="text-sm text-white/40 leading-relaxed mb-8 italic">"{selectedNode.desc || "No desc"}"</p>
              
              <div className="space-y-3 mb-6">
                <button onClick={expandNode} className="w-full flex items-center justify-between px-6 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-2xl font-black uppercase italic text-xs shadow-xl">
                  <div className="flex items-center gap-2"><Plus size={16} /> Expand</div>
                </button>
                <button onClick={() => setSelectedNode(null)} className="w-full text-white/10 hover:text-white/30 text-[9px] font-bold uppercase tracking-[0.4em]">
                  Close Panel
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 opacity-50">
              <MousePointer2 className="mx-auto text-white/20 mb-4" size={32} />
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/40">Select a node</p>
            </div>
          )}
        </div>
      </div>

      {/* RAW STATE DEBUG OVERLAY (Top Right) */}
      <div className="absolute top-20 right-6 z-50 bg-black/80 border border-red-500/30 p-4 rounded text-xs font-mono text-red-300 pointer-events-none">
        <div>Current Selection:</div>
        <div className="text-white font-bold text-lg">{selectedNode ? selectedNode.name : "NULL"}</div>
        <div>Nodes Loaded: {nodes.length}</div>
      </div>

    </div>
  );
}