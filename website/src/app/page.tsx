"use client";

import React from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { Zap, Globe, Database, Cpu, ChevronRight, BarChart3, Binary } from 'lucide-react';
import demoData from '../demo-data/demo-nebula.json';

// Use dynamic import for ForceGraph to avoid SSR issues
const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), { ssr: false });

export default function LandingPage() {
  const scrollToFeatures = () => {
    document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white selection:bg-blue-500/30">
      {/* 3D Hero Section */}
      <section className="relative h-screen flex flex-col items-center justify-center overflow-hidden border-b border-white/5">
        <div className="absolute inset-0 z-0 opacity-40">
          <ForceGraph3D
            graphData={demoData}
            backgroundColor="#050505"
            nodeLabel="name"
            nodeAutoColorBy="community"
            linkColor={() => "#ffffff22"}
            enablePointerInteraction={false}
            showNavInfo={false}
          />
        </div>
        
        <div className="relative z-10 text-center px-6 max-w-4xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 mb-6 backdrop-blur-md">
            <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
            <span className="text-[10px] font-bold uppercase tracking-widest text-blue-400">Universal Engine v1.0 Live</span>
          </div>
          
          <h1 className="text-6xl md:text-8xl font-black italic tracking-tighter mb-6 uppercase italic">
            Wiki<span className="text-blue-500">Graph</span> Lab
          </h1>
          
          <p className="text-xl text-white/40 max-w-2xl mx-auto mb-10 font-medium leading-relaxed">
            A high-performance research platform for visualizing the global topology of human knowledge through the lens of graph science.
          </p>
          
          <div className="flex flex-wrap gap-4 justify-center">
            <button 
              onClick={scrollToFeatures}
              className="px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white font-black rounded-2xl transition-all shadow-2xl shadow-blue-600/20 flex items-center gap-3 group uppercase text-sm italic"
            >
              Explore the Nebula
              <ChevronRight className="group-hover:translate-x-1 transition-transform" size={18} />
            </button>
            <Link 
              href="/docs"
              className="px-8 py-4 bg-white/5 hover:bg-white/10 border border-white/10 text-white font-bold rounded-2xl transition-all backdrop-blur-xl uppercase text-sm italic inline-flex items-center"
            >
              View Documentation
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

      {/* Case Study Section */}
      <section className="py-24 px-6 max-w-7xl mx-auto">
        <div className="flex items-center gap-4 mb-12">
          <div className="p-3 bg-white/5 rounded-2xl border border-white/10">
            <BarChart3 className="text-blue-500" size={32} />
          </div>
          <div>
            <h2 className="text-3xl font-black uppercase italic italic tracking-tight">Research <span className="text-blue-500">Case Studies</span></h2>
            <p className="text-white/20 text-[10px] font-bold uppercase tracking-[0.3em]">Scientific Insights from the Graph</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-white/5 border border-white/10 rounded-3xl p-8 hover:bg-white/[0.07] transition-all group">
            <div className="aspect-video bg-black/40 rounded-2xl mb-6 border border-white/5 flex items-center justify-center">
              <span className="text-white/10 font-bold uppercase tracking-widest">Visual: Bridge Mapping</span>
            </div>
            <h3 className="text-xl font-bold mb-3 uppercase tracking-tight italic italic text-blue-400">The "Bridge" Discovery</h3>
            <p className="text-white/40 leading-relaxed">
              Identifying articles that connect seemingly unrelated knowledge silos (e.g., Mathematics and Linguistics) using Betweenness Centrality.
            </p>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-3xl p-8 hover:bg-white/[0.07] transition-all group">
            <div className="aspect-video bg-black/40 rounded-2xl mb-6 border border-white/5 flex items-center justify-center">
              <span className="text-white/10 font-bold uppercase tracking-widest">Visual: Cross-Lingual Gap</span>
            </div>
            <h3 className="text-xl font-bold mb-3 uppercase tracking-tight italic italic text-blue-400">Cross-Lingual Disparity</h3>
            <p className="text-white/40 leading-relaxed">
              Quantifying the information gap between language editions by mapping identical concepts across independent topological graphs.
            </p>
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
