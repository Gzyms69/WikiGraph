"use client";

import React, { useState, useRef, useCallback } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { Zap, Globe, Database, Cpu, ChevronRight, BarChart3, Binary, Search, Terminal, Info } from 'lucide-react';
import demoData from '../demo-data/demo-nebula.json';

// Use dynamic import for ForceGraph to avoid SSR issues
const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), { ssr: false });

export default function LandingPage() {
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const fgRef = useRef<any>();

  const scrollToFeatures = () => {
    document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleNodeClick = useCallback((node: any) => {
    const distance = 40;
    const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);

    fgRef.current.cameraPosition(
      { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
      node,
      3000
    );
    setSelectedNode(node);
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const node = demoData.nodes.find(n => n.name.toLowerCase().includes(searchQuery.toLowerCase()));
    if (node) {
      // Find the node in the actual simulation (need to match by ID)
      const graphNode = fgRef.current.getGraphData().nodes.find((n: any) => n.id === node.id);
      if (graphNode) handleNodeClick(graphNode);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white selection:bg-blue-500/30">
      {/* 3D Hero Section */}
      <section className="relative h-screen flex flex-col items-center justify-center overflow-hidden border-b border-white/5">
        <div className="absolute inset-0 z-0 opacity-60">
          <ForceGraph3D
            ref={fgRef}
            graphData={demoData}
            backgroundColor="#050505"
            nodeLabel="name"
            nodeAutoColorBy="community"
            linkColor={() => "#ffffff22"}
            onNodeClick={handleNodeClick}
            showNavInfo={false}
          />
        </div>
        
        {/* Floating Search / Info Panels */}
        <div className="absolute top-32 left-6 z-20 w-80 space-y-4 hidden md:block">
          <form onSubmit={handleSearch} className="relative group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-blue-500 transition-colors" size={18} />
            <input 
              type="text"
              placeholder="Search Knowledge Nebula..."
              className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 pr-4 backdrop-blur-xl focus:outline-none focus:border-blue-500/50 transition-all text-sm"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </form>

          {selectedNode && (
            <div className="bg-blue-600/10 border border-blue-500/30 rounded-3xl p-6 backdrop-blur-3xl animate-in fade-in slide-in-from-left-4 duration-500">
              <div className="flex items-center gap-2 mb-4">
                <Info className="text-blue-500" size={16} />
                <span className="text-[10px] font-bold uppercase tracking-widest text-blue-400">Node Metadata</span>
              </div>
              <h3 className="text-xl font-black italic uppercase tracking-tighter mb-2">{selectedNode.name}</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-white/40 uppercase font-bold">Language</span>
                  <span className="text-white font-mono bg-white/10 px-2 py-0.5 rounded uppercase">{selectedNode.lang}</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-white/40 uppercase font-bold">Importance</span>
                  <span className="text-blue-400 font-bold">{selectedNode.val}%</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-white/40 uppercase font-bold">Cluster ID</span>
                  <span className="text-purple-400 font-bold">#{selectedNode.community}</span>
                </div>
              </div>
              <button 
                onClick={() => setSelectedNode(null)}
                className="w-full mt-6 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-[10px] font-bold uppercase tracking-widest transition-all"
              >
                Clear Selection
              </button>
            </div>
          )}
        </div>
        
        <div className="relative z-10 text-center px-6 max-w-4xl pointer-events-none">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 mb-6 backdrop-blur-md">
            <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
            <span className="text-[10px] font-bold uppercase tracking-widest text-blue-400">Universal Engine v1.0 Live</span>
          </div>
          
          <h1 className="text-6xl md:text-8xl font-black italic tracking-tighter mb-6 uppercase italic">
            Wiki<span className="text-blue-500">Graph</span> Lab
          </h1>
          
          <p className="text-xl text-white/40 max-w-2xl mx-auto mb-10 font-medium leading-relaxed">
            Global topology of human knowledge through the lens of graph science. Interactive discovery across 300+ languages.
          </p>
          
          <div className="flex flex-wrap gap-4 justify-center pointer-events-auto">
            <button 
              onClick={scrollToFeatures}
              className="px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white font-black rounded-2xl transition-all shadow-2xl shadow-blue-600/20 flex items-center gap-3 group uppercase text-sm italic"
            >
              Explore Features
              <ChevronRight className="group-hover:translate-x-1 transition-transform" size={18} />
            </button>
            <Link 
              href="/docs"
              className="px-8 py-4 bg-white/5 hover:bg-white/10 border border-white/10 text-white font-bold rounded-2xl transition-all backdrop-blur-xl uppercase text-sm italic inline-flex items-center"
            >
              System Architecture
            </Link>
          </div>
        </div>
      </section>

      {/* Stats Grid */}
      <section id="features" className="py-24 px-6 border-b border-white/5 bg-gradient-to-b from-transparent to-white/[0.02]">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <FeatureCard 
              icon={<Database size={24} className="text-blue-500" />}
              title="Massive-Scale"
              desc="Optimized for ingestion of multi-terabyte Wikipedia XML dumps with parallel parsing logic."
            />
            <FeatureCard 
              icon={<Binary size={24} className="text-purple-500" />}
              title="Graph GDS"
              desc="Native Neo4j Graph Data Science integration for PageRank, Betweenness, and FastRP embeddings."
            />
            <FeatureCard 
              icon={<Globe size={24} className="text-green-500" />}
              title="Agnostic Engine"
              desc="JIT configuration system supporting all 300+ Wikipedia languages automatically."
            />
          </div>
        </div>
      </section>

      {/* Developer API Section */}
      <section className="py-24 px-6 bg-black border-b border-white/5">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-4 mb-12">
            <div className="p-3 bg-white/5 rounded-2xl border border-white/10">
              <Terminal className="text-blue-500" size={32} />
            </div>
            <div>
              <h2 className="text-3xl font-black uppercase italic italic tracking-tight">Researcher <span className="text-blue-500">Access</span></h2>
              <p className="text-white/20 text-[10px] font-bold uppercase tracking-[0.3em]">Direct Integration via REST API</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            <div className="space-y-6">
              <p className="text-white/40 leading-relaxed">
                Integrate WikiGraph insights directly into your research pipeline. Our agnostic API handles the complexities of multilingual parsing and graph traversal.
              </p>
              <ul className="space-y-4">
                <li className="flex items-start gap-3">
                  <Zap className="text-blue-500 mt-1" size={16} />
                  <span className="text-sm text-white/60 font-medium">Auto-discovery of available language editions.</span>
                </li>
                <li className="flex items-start gap-3">
                  <Zap className="text-blue-500 mt-1" size={16} />
                  <span className="text-sm text-white/60 font-medium">Weighted neighbor ranking across disparate subgraphs.</span>
                </li>
              </ul>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-3xl p-1 overflow-hidden">
              <div className="bg-black/40 px-6 py-3 border-b border-white/5 flex items-center justify-between">
                <div className="flex gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-500/20" />
                  <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/20" />
                  <div className="w-2.5 h-2.5 rounded-full bg-green-500/20" />
                </div>
                <span className="text-[10px] font-mono text-white/20 tracking-widest uppercase">Bash / cURL</span>
              </div>
              <pre className="p-8 font-mono text-xs text-blue-300 leading-loose overflow-x-auto">
                {`curl -X POST "http://localhost:8000/graph/weighted-neighbors" \\
     -H "Content-Type: application/json" \\
     -d '{
       "qid": "Q1",
       "weights": {"jaccard": 1.0, "pagerank": 0.5}
     }'`}
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-white/5 text-center">
        <p className="text-white/10 text-xs font-bold uppercase tracking-[0.5em]">
          WikiGraph Lab &bull; Open Source Knowledge Graph Science
        </p>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, desc }: { icon: React.ReactNode, title: string, desc: string }) {
  return (
    <div className="p-8 bg-white/5 border border-white/10 rounded-3xl hover:bg-white/[0.07] transition-all group">
      <div className="mb-6 inline-block p-4 bg-[#050505] rounded-2xl border border-white/10 group-hover:border-blue-500/30 transition-all shadow-xl">
        {icon}
      </div>
      <h3 className="text-lg font-bold mb-3 uppercase tracking-tight italic italic">{title}</h3>
      <p className="text-white/30 text-sm leading-relaxed">{desc}</p>
    </div>
  );
}
