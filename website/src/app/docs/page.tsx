"use client";

import React from 'react';
import Link from 'next/link';
import { ChevronLeft, Database, Network, Cpu, Code2, Zap } from 'lucide-react';

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-[#050505] text-white selection:bg-blue-500/30 font-sans">
      {/* Sidebar / Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#050505]/80 backdrop-blur-xl border-b border-white/5 px-6 py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <ChevronLeft className="text-blue-500 group-hover:-translate-x-1 transition-transform" size={20} />
          <span className="font-black italic uppercase tracking-tighter text-sm">Wiki<span className="text-blue-500">Graph</span> Lab</span>
        </Link>
        <div className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/20">Technical Documentation v1.0</div>
      </nav>

      <div className="max-w-5xl mx-auto px-6 pt-32 pb-24">
        <header className="mb-16">
          <h1 className="text-5xl md:text-7xl font-black italic tracking-tighter uppercase mb-6">
            System <span className="text-blue-500">Architecture</span>
          </h1>
          <p className="text-xl text-white/40 max-w-3xl leading-relaxed">
            WikiGraph is engineered for massive-scale topological analysis of Wikipedia editions. It combines a high-performance Python parsing engine with Neo4j's Graph Data Science (GDS) suite.
          </p>
        </header>

        <div className="grid grid-cols-1 gap-16">
          {/* Section 1: Ingestion */}
          <section id="ingestion">
            <div className="flex items-center gap-4 mb-8">
              <div className="p-3 bg-blue-500/10 rounded-2xl border border-blue-500/20">
                <Database className="text-blue-500" size={24} />
              </div>
              <h2 className="text-2xl font-black uppercase italic tracking-tight">Data Ingestion Engine</h2>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-3xl p-8 space-y-6 leading-relaxed text-white/60">
              <p>
                The ingestion pipeline processes raw <code className="text-blue-400">pages-articles.xml.bz2</code> dumps using a parallelized <code className="text-blue-400">lxml</code>-based parser.
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li><span className="text-white font-bold">JIT Configuration:</span> Dynamically fetches namespace and redirect rules from the MediaWiki API to ensure 100% language agnosticism.</li>
                <li><span className="text-white font-bold">Parallel Parsing:</span> Multi-core processing with <code className="text-blue-400">rapidgzip</code> for near-instant decompression and streaming.</li>
                <li><span className="text-white font-bold">Semantic Cleaning:</span> Automatic detection of CJK languages for character-level tokenization and template stripping.</li>
              </ul>
            </div>
          </section>

          {/* Section 2: Graph Engine */}
          <section id="graph">
            <div className="flex items-center gap-4 mb-8">
              <div className="p-3 bg-purple-500/10 rounded-2xl border border-purple-500/20">
                <Network className="text-purple-500" size={24} />
              </div>
              <h2 className="text-2xl font-black uppercase italic tracking-tight">Neo4j GDS Integration</h2>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-3xl p-8 space-y-6 leading-relaxed text-white/60">
              <p>
                The graph model separates physical <code className="text-purple-400">Article</code> nodes from semantic <code className="text-purple-400">Concept</code> nodes (QIDs), enabling interlingual connections.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-black/40 rounded-2xl border border-white/5">
                  <h4 className="text-white font-bold text-sm mb-2 uppercase tracking-widest">Structural Algorithms</h4>
                  <p className="text-xs">PageRank, Betweenness Centrality, and Louvain Community Detection for topology mapping.</p>
                </div>
                <div className="p-4 bg-black/40 rounded-2xl border border-white/5">
                  <h4 className="text-white font-bold text-sm mb-2 uppercase tracking-widest">ML Readiness</h4>
                  <p className="text-xs">FastRP (Fast Random Projection) for node embeddings and PPR (Personalized PageRank) for recommendations.</p>
                </div>
              </div>
            </div>
          </section>

          {/* Section 3: Universal API */}
          <section id="api">
            <div className="flex items-center gap-4 mb-8">
              <div className="p-3 bg-green-500/10 rounded-2xl border border-green-500/20">
                <Code2 className="text-green-500" size={24} />
              </div>
              <h2 className="text-2xl font-black uppercase italic tracking-tight">Agnostic REST API</h2>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-3xl p-8 space-y-6 leading-relaxed text-white/60">
              <p>Built with FastAPI, the backend provides a unified interface for graph traversal and analytics.</p>
              <pre className="bg-black/60 p-6 rounded-2xl border border-white/5 overflow-x-auto font-mono text-xs text-blue-300">
{`# Dynamic Language Discovery
GET /graph/languages

# Multi-Algorithm Neighbor Ranking
POST /graph/weighted-neighbors
{
  "qid": "Q42",
  "weights": { "jaccard": 0.5, "adamic_adar": 1.5 }
}`}
              </pre>
            </div>
          </section>
        </div>

        <footer className="mt-24 pt-12 border-t border-white/5 text-center text-white/20 text-xs font-bold uppercase tracking-widest">
          WikiGraph Lab &bull; Documentation built with Next.js Static Export
        </footer>
      </div>
    </div>
  );
}
