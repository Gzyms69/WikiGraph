"use client";

import React from 'react';
import Link from 'next/link';
import { Zap, Globe, Database, Cpu, ChevronRight, BarChart3, Binary, Terminal, Play } from 'lucide-react';

export default function LandingPage() {
  const scrollToFeatures = () => {
    document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white selection:bg-blue-500/30">
      {/* Visual Background Pattern */}
      <div className="fixed inset-0 z-0 opacity-20 pointer-events-none" 
           style={{ backgroundImage: 'radial-gradient(#1e40af 0.5px, transparent 0.5px)', backgroundSize: '24px 24px' }} />

      {/* Hero Section */}
      <section className="relative h-screen flex flex-col items-center justify-center overflow-hidden border-b border-white/5 px-6">
        <div className="relative z-10 text-center max-w-4xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 mb-8 backdrop-blur-md">
            <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
            <span className="text-[10px] font-bold uppercase tracking-widest text-blue-400">Universal Engine v1.0 Live</span>
          </div>
          
          <h1 className="text-6xl md:text-9xl font-black italic tracking-tighter mb-8 uppercase italic leading-[0.8]">
            Wiki<span className="text-blue-500 text-glow">Graph</span> Lab
          </h1>
          
          <p className="text-xl md:text-2xl text-white/40 max-w-2xl mx-auto mb-12 font-medium leading-relaxed">
            The high-performance research platform for mapping the global topology of human knowledge across 300+ languages.
          </p>
          
          <div className="flex flex-wrap gap-4 justify-center">
            <Link 
              href="/demo"
              className="px-10 py-5 bg-blue-600 hover:bg-blue-500 text-white font-black rounded-2xl transition-all shadow-2xl shadow-blue-600/40 flex items-center gap-3 group uppercase text-sm italic scale-110"
            >
              <Play size={18} fill="currentColor" />
              Launch Nebula Demo
            </Link>
            <button 
              onClick={scrollToFeatures}
              className="px-10 py-5 bg-white/5 hover:bg-white/10 border border-white/10 text-white font-bold rounded-2xl transition-all backdrop-blur-xl uppercase text-sm italic"
            >
              Core Features
            </button>
            <Link 
              href="/docs"
              className="px-10 py-5 bg-white/5 hover:bg-white/10 border border-white/10 text-white font-bold rounded-2xl transition-all backdrop-blur-xl uppercase text-sm italic inline-flex items-center"
            >
              Documentation
            </Link>
          </div>
        </div>

        {/* Decorative elements */}
        <div className="absolute bottom-12 left-1/2 -translate-x-1/2 animate-bounce opacity-20">
          <ChevronRight size={32} className="rotate-90" />
        </div>
      </section>

      {/* Stats Grid */}
      <section id="features" className="relative z-10 py-32 px-6 border-b border-white/5 bg-[#050505]">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <FeatureCard 
              icon={<Database size={24} className="text-blue-500" />}
              title="Massive-Scale"
              desc="Ingest multi-terabyte Wikipedia XML dumps with parallel parsing and rapid decompression logic."
            />
            <FeatureCard 
              icon={<Binary size={24} className="text-purple-500" />}
              title="Graph GDS"
              desc="Native Neo4j Graph Data Science integration for PageRank, Betweenness, and FastRP embeddings."
            />
            <FeatureCard 
              icon={<Globe size={24} className="text-green-500" />}
              title="Agnostic Engine"
              desc="JIT configuration system supporting all 300+ Wikipedia language editions automatically."
            />
          </div>
        </div>
      </section>

      {/* Developer API Section */}
      <section className="relative z-10 py-32 px-6 bg-black border-b border-white/5">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-4 mb-16">
            <div className="p-3 bg-white/5 rounded-2xl border border-white/10">
              <Terminal className="text-blue-500" size={32} />
            </div>
            <div>
              <h2 className="text-4xl font-black uppercase italic italic tracking-tight">Researcher <span className="text-blue-500">Access</span></h2>
              <p className="text-white/20 text-[10px] font-bold uppercase tracking-[0.3em]">Direct Integration via REST API</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div className="space-y-8">
              <p className="text-xl text-white/40 leading-relaxed">
                Integrate WikiGraph insights directly into your research pipeline. Our agnostic API handles the complexities of multilingual parsing and graph traversal.
              </p>
              <ul className="space-y-6">
                <li className="flex items-start gap-4">
                  <div className="mt-1 p-1 bg-blue-500/20 rounded-lg"><Zap className="text-blue-500" size={18} /></div>
                  <div>
                    <h4 className="font-bold uppercase italic italic tracking-tight text-white/80">Language Discovery</h4>
                    <p className="text-sm text-white/40">Auto-discovery of available language clusters in the graph.</p>
                  </div>
                </li>
                <li className="flex items-start gap-4">
                  <div className="mt-1 p-1 bg-purple-500/20 rounded-lg"><Binary className="text-purple-500" size={18} /></div>
                  <div>
                    <h4 className="font-bold uppercase italic italic tracking-tight text-white/80">Ranked Neighbors</h4>
                    <p className="text-sm text-white/40">Weighted multi-algorithm ranking (Jaccard + Adamic Adar).</p>
                  </div>
                </li>
              </ul>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-[2.5rem] p-1 overflow-hidden shadow-3xl shadow-blue-500/5">
              <div className="bg-black/40 px-8 py-4 border-b border-white/5 flex items-center justify-between">
                <div className="flex gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500/20" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500/20" />
                  <div className="w-3 h-3 rounded-full bg-green-500/20" />
                </div>
                <span className="text-[10px] font-mono text-white/20 tracking-widest uppercase font-bold">Bash Terminal</span>
              </div>
              <pre className="p-10 font-mono text-sm text-blue-300 leading-loose overflow-x-auto bg-black/20">
                {`curl -X POST "https://api.wikigraph.lab/neighbors" \\
     -H "Content-Type: application/json" \\
     -d '{
       "qid": "Q42",
       "weights": {
         "jaccard": 1.0, 
         "pagerank": 0.5
       }
     }'`}
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-24 px-6 border-t border-white/5 text-center bg-black">
        <p className="text-white/10 text-xs font-bold uppercase tracking-[0.5em] mb-4">
          WikiGraph Lab &bull; Open Source Knowledge Graph Science
        </p>
        <div className="w-12 h-1 bg-blue-600 mx-auto rounded-full opacity-20" />
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, desc }: { icon: React.ReactNode, title: string, desc: string }) {
  return (
    <div className="p-10 bg-white/5 border border-white/10 rounded-[2.5rem] hover:bg-white/[0.07] transition-all group relative overflow-hidden">
      <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 blur-3xl -mr-16 -mt-16 group-hover:bg-blue-500/10 transition-all" />
      <div className="mb-8 inline-block p-5 bg-[#050505] rounded-2xl border border-white/10 group-hover:border-blue-500/30 transition-all shadow-xl relative z-10">
        {icon}
      </div>
      <h3 className="text-2xl font-bold mb-4 uppercase tracking-tight italic italic relative z-10">{title}</h3>
      <p className="text-white/30 text-sm leading-relaxed relative z-10">{desc}</p>
    </div>
  );
}
