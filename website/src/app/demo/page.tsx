"use client";

import React, { useState, useRef, useEffect, useMemo } from 'react';
import dynamic from 'next/dynamic';
import { ChevronLeft, Compass, Plus, Search } from 'lucide-react';
import masterPool from '../../demo-data/demo-nebula.json';

// Basic dynamic import
const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), { ssr: false });

export default function DemoPage() {
  const [nodes, setNodes] = useState<any[]>([]);
  const [links, setLinks] = useState<any[]>([]);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [debug, setDebug] = useState("Initializing...");
  
  const fgRef = useRef<any>();

  // --- 1. Load Data ---
  useEffect(() => {
    // Load simple initial set
    const seedIds = ["en:Q1", "en:Q9", "en:Q5", "en:Q13", "en:Q3"];
    const initialNodes = masterPool.nodes.filter(n => seedIds.includes(n.id));
    const initialLinks = masterPool.links.filter(l => 
      seedIds.includes((l.source as any).id || l.source) && 
      seedIds.includes((l.target as any).id || l.target)
    );
    setNodes(initialNodes);
    setLinks(initialLinks);
    setDebug("Data Loaded. Click a node.");
  }, []);

  // --- 2. Simple Interaction Handlers ---
  const handleNodeClick = (node: any) => {
    setDebug(`CLICKED: ${node.name}`);
    setSelectedNode(node);
    
    // Focus camera
    if (fgRef.current) {
      const distance = 160;
      const distRatio = 1 + distance / Math.hypot(node.x || 0, node.y || 0, node.z || 0);
      fgRef.current.cameraPosition(
        { x: (node.x || 0) * distRatio, y: (node.y || 0) * distRatio, z: (node.z || 0) * distRatio },
        node,
        1000
      );
    }
  };

  const graphData = useMemo(() => ({ nodes, links }), [nodes, links]);

  return (
    <div className="h-screen w-screen bg-[#050505] relative font-sans text-white overflow-hidden">
      
      {/* 3. Simple Header - Using <a> to avoid Next.js prefetch 404s */}
      <nav className="absolute top-0 left-0 w-full z-50 p-4 bg-black/50 border-b border-white/10 flex justify-between items-center backdrop-blur-md">
        <a href="/WikiGraph/" className="flex items-center gap-2 text-sm font-bold tracking-widest hover:text-blue-400 transition-colors">
          <ChevronLeft size={16} /> EXIT DEMO
        </a>
        <div className="text-xs font-mono text-blue-400">DEBUG: {debug}</div>
      </nav>

      {/* 4. The Graph - Bare Metal Configuration */}
      <div className="absolute inset-0 z-0">
        <ForceGraph3D
          ref={fgRef}
          graphData={graphData}
          backgroundColor="#050505"
          nodeLabel="name"
          // Standard Interaction
          enableNodeDrag={true}
          onNodeClick={handleNodeClick}
          // Visuals
          nodeRelSize={6}
          nodeVal={20}
          linkOpacity={0.5}
          onNodeHover={node => {
            if (fgRef.current) {
              fgRef.current.renderer().domElement.style.cursor = node ? 'pointer' : 'default';
            }
          }}
        />
      </div>

      {/* 5. The Menu - Hardcoded Visibility Check */}
      {selectedNode && (
        <div className="absolute top-20 left-6 z-40 w-80 bg-black/80 border border-white/20 p-6 rounded-3xl backdrop-blur-xl shadow-2xl">
          <div className="flex items-center gap-2 mb-4 text-blue-400">
            <Compass size={16} />
            <span className="text-xs font-bold uppercase tracking-widest">Selected Node</span>
          </div>
          <h2 className="text-2xl font-black mb-2">{selectedNode.name}</h2>
          <p className="text-sm text-white/60 mb-6 italic">{selectedNode.desc}</p>
          
          <button 
            onClick={() => setSelectedNode(null)}
            className="w-full py-3 bg-white/10 rounded-xl text-xs font-bold uppercase hover:bg-white/20 transition-colors"
          >
            Close Menu
          </button>
        </div>
      )}
    </div>
  );
}