"use client";

import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import dynamic from 'next/dynamic';
import axios from 'axios';
import { Loader2 } from 'lucide-react';
import { GraphNode, GraphData } from '../types/graph';
import InitializationScreen from './nebula/InitializationScreen';
import SearchOverlay from './nebula/SearchOverlay';
import NebulaInfo from './nebula/NebulaInfo';
import NodeDetailsPanel from './nebula/NodeDetailsPanel';
import ControlDeck from './nebula/ControlDeck';
import SettingsPanel from './nebula/SettingsPanel';

const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), {
  ssr: false
});

const API_BASE = "http://localhost:8000";

const LANG_COLORS: Record<string, string> = {
  pl: "#dc143c", // Polish Red
  de: "#ffce00", // German Gold
  en: "#00247d", // Royal Blue
};

interface FlyParams {
  startTime: number;
  startPos: { x: number; y: number; z: number };
  offset: { x: number; y: number; z: number };
  node: GraphNode;
}

// Stable Community Color Generator
const getCommunityColor = (id?: number) => {
  if (id === undefined) return '#555555';
  const colors = [
    '#ff4500', '#2e8b57', '#4169e1', '#daa520', '#ff69b4', 
    '#00ffff', '#7fff00', '#ff00ff', '#1e90ff', '#ff1493'
  ];
  return colors[id % colors.length];
};

const WikiNebula = () => {
  const fgRef = useRef<any>();
  const nodesRef = useRef<GraphNode[]>([]);
  const pendingFocusRef = useRef<string | null>(null);
  const flyParamsRef = useRef<FlyParams | null>(null);
  
  const [data, setData] = useState<GraphData>({ nodes: [], links: [] });
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isSpawningNode, setIsSpawningNode] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [selectedLangs, setSelectedLangs] = useState<string[]>(['pl', 'de']);

  // UI & Visual States
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [isPhysicsPaused, setIsPhysicsPaused] = useState(false);
  const [autoRotate, setAutoRotate] = useState(false);
  const [colorByCommunity, setColorByCommunity] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Engine Configuration
  const [config, setConfig] = useState({
    neighborLimit: 15,
    forceStrength: 100,
    forceDistance: 100,
    algorithmWeights: {
      jaccard: 0.0,
      adamic_adar: 1.0,
      pagerank: 0.0
    } as Record<string, number>
  });
  
  // Spotlight State
  const neighbors = useMemo(() => {
    const set = new Set<string>();
    if (selectedNode) {
      data.links.forEach(link => {
        const s = typeof link.source === 'object' ? link.source.id : link.source;
        const t = typeof link.target === 'object' ? link.target.id : link.target;
        if (s === selectedNode.id) set.add(t);
        if (t === selectedNode.id) set.add(s);
      });
    }
    return set;
  }, [selectedNode, data.links]);

  useEffect(() => {
    nodesRef.current = data.nodes;
  }, [data.nodes]);

  // Handle Physics Toggle & Configuration
  useEffect(() => {
    if (fgRef.current) {
      if (isPhysicsPaused) {
        fgRef.current.pauseAnimation();
      } else {
        fgRef.current.resumeAnimation();
        // Dynamic Force Tuning
        fgRef.current.d3Force('charge').strength(-config.forceStrength);
        fgRef.current.d3Force('link').distance(config.forceDistance);
      }
    }
  }, [isPhysicsPaused, config.forceStrength, config.forceDistance]);

  // Handle Auto-Rotate Toggle
  useEffect(() => {
    if (fgRef.current) {
      const controls = fgRef.current.controls();
      if (controls) {
        controls.autoRotate = autoRotate;
        controls.autoRotateSpeed = 0.5;
      }
    }
  }, [autoRotate]);

  // 1. Initial Load
  const startNebula = async () => {
    setIsLoading(true);
    try {
      const langParam = selectedLangs.join(",");
      const res = await axios.get(`${API_BASE}/graph/nebula?langs=${langParam}&limit=150`);
      const nodes = res.data.nodes.map((n: any) => ({
        ...n,
        // Pre-calculate base colors
        langColor: LANG_COLORS[n.lang] || '#555555',
        commColor: getCommunityColor(n.community),
        // Use safer scaling: Min size 2
        val: Math.max(Math.sqrt(n.val || 0) * 2, 2),
        // Wider spawn area
        x: (Math.random() - 0.5) * 500,
        y: (Math.random() - 0.5) * 500,
        z: (Math.random() - 0.5) * 500
      }));
      setData({ nodes, links: res.data.links || [] });
      setIsInitialized(true);
      
      // Auto-zoom to fit ONLY on initial load
      if (fgRef.current) {
        setTimeout(() => {
            fgRef.current.zoomToFit(1000, 100); 
        }, 500);
      }
    } catch (err) {
      console.error("Failed to fetch nebula", err);
    } finally {
      setIsLoading(false);
    }
  };

  // 2. Search Handler
  const handleSearch = useCallback(async (q: string) => {
    if (q.length < 2) {
      setSearchResults([]);
      return;
    }
    setIsSearching(true);
    try {
      const res = await axios.get(`${API_BASE}/search/keyword?q=${q}&limit=5`);
      setSearchResults(res.data.results);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSearching(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => handleSearch(searchQuery), 300);
    return () => clearTimeout(timer);
  }, [searchQuery, handleSearch]);

  const handleResetCamera = () => {
    if (fgRef.current) {
      flyParamsRef.current = null; // Interrupt active fly
      fgRef.current.cameraPosition({ x: 0, y: 0, z: 600 }, { x: 0, y: 0, z: 0 }, 2000);
      setSelectedNode(null);
    }
  };

  const initCameraFly = (node: GraphNode) => {
    if (!fgRef.current) return;

    const camera = fgRef.current.camera();
    const startPos = { ...camera.position };

    const nodeX = node.x || 0;
    const nodeY = node.y || 0;
    const nodeZ = node.z || 0;

    let vx = startPos.x - nodeX;
    let vy = startPos.y - nodeY;
    let vz = startPos.z - nodeZ;

    const dist = Math.hypot(vx, vy, vz);
    if (dist < 1) { vx = 0; vy = 0; vz = 1; } 
    else { vx /= dist; vy /= dist; vz /= dist; }

    const targetDist = 150;
    const offset = { x: vx * targetDist, y: vy * targetDist, z: vz * targetDist };

    flyParamsRef.current = { startTime: Date.now(), startPos, offset, node };
  };

  // 3. Focus Logic
  const focusOnNode = async (qid: string, title: string, lang: string) => {
    // GUARD: Prevent multiple spawns
    if (isSpawningNode || isSearching) return;

    const targetId = `${lang}:${qid}`;
    let targetNode = nodesRef.current.find(n => n.id === targetId);

    if (targetNode) {
      setSelectedNode(targetNode);
      initCameraFly(targetNode);
      setSearchResults([]);
      setSearchQuery("");
      return;
    }

    setIsSpawningNode(title || qid);
    try {
      // DYNAMIC: Using WEIGHTED Hybrid Endpoint
      const neighborsRes = await axios.post(`${API_BASE}/graph/weighted-neighbors`, {
        qid,
        lang,
        limit: config.neighborLimit,
        weights: config.algorithmWeights
      });
      
      const newNode: GraphNode = { 
        id: targetId,
        qid: qid,
        name: title || qid, 
        lang: lang, 
        val: 12, 
        color: LANG_COLORS[lang] || '#555555', // Fallback
        langColor: LANG_COLORS[lang] || '#555555',
        commColor: getCommunityColor(0),
        x: (Math.random() - 0.5) * 50,
        y: (Math.random() - 0.5) * 50,
        z: (Math.random() - 0.5) * 50
      };

      const neighborNodes = neighborsRes.data.neighbors.map((nb: any) => ({
        id: (nb.lang && nb.lang !== '??') ? `${nb.lang}:${nb.qid}` : `concept:${nb.qid}`,
        qid: nb.qid,
        name: nb.title || nb.qid || 'Unknown',
        lang: nb.lang || '??',
        val: 5,
        color: '#333333',
        langColor: LANG_COLORS[nb.lang] || '#333333',
        commColor: '#333333',
        x: (Math.random() - 0.5) * 100,
        y: (Math.random() - 0.5) * 100,
        z: (Math.random() - 0.5) * 100
      }));

      const newLinks = neighborsRes.data.neighbors.map((nb: any) => ({
        source: targetId,
        target: (nb.lang && nb.lang !== '??') ? `${nb.lang}:${nb.qid}` : `concept:${nb.qid}`,
        color: '#ffffff11'
      }));

      pendingFocusRef.current = targetId;
      setSelectedNode(newNode);

      setData(prev => {
        const existingIds = new Set(prev.nodes.map(n => n.id));
        const filteredNewNodes = [newNode, ...neighborNodes].filter(n => !existingIds.has(n.id));
        return {
          nodes: [...prev.nodes, ...filteredNewNodes],
          links: [...prev.links, ...newLinks]
        };
      });

    } catch (err) {
      console.error(err);
    } finally {
      setIsSpawningNode(null);
      setSearchResults([]);
      setSearchQuery("");
    }
  };

  // 4. Bulk Refresh Logic (Stability Merge)
  const handleBulkRefresh = async () => {
    // 1. Identify all center nodes (nodes with neighbors)
    const centers = data.nodes.filter(n => data.links.some(l => 
        (typeof l.source === 'string' ? l.source : l.source.id) === n.id
    ));

    if (centers.length === 0) return;
    
    setIsLoading(true);
    try {
        const batchSize = 5;
        const results: any = {};
        
        // Chunk requests to avoid overloading
        for (let i = 0; i < centers.length; i += batchSize) {
            const chunk = centers.slice(i, i + batchSize);
            const res = await axios.post(`${API_BASE}/graph/bulk-weighted-neighbors`, {
                requests: chunk.map(c => ({
                    qid: c.qid,
                    lang: c.lang,
                    limit: config.neighborLimit,
                    weights: config.algorithmWeights
                }))
            });
            Object.assign(results, res.data.results);
        }

        // 2. Stability Merge: Preserve existing nodes' positions
        setData(prev => {
            const nodeMap = new Map(prev.nodes.map(n => [n.id, n]));
            const newLinks: any[] = [];

            centers.forEach(center => {
                const neighbors = results[center.qid] || [];
                neighbors.forEach((nb: any) => {
                    const id = (nb.lang && nb.lang !== '??') ? `${nb.lang}:${nb.qid}` : `concept:${nb.qid}`;
                    if (!nodeMap.has(id)) {
                        nodeMap.set(id, {
                            id, qid: nb.qid, name: nb.title, lang: nb.lang, val: 5,
                            color: '#333333', langColor: LANG_COLORS[nb.lang] || '#333333', commColor: '#333333',
                            x: (center.x || 0) + (Math.random() - 0.5) * 50,
                            y: (center.y || 0) + (Math.random() - 0.5) * 50,
                            z: (center.z || 0) + (Math.random() - 0.5) * 50
                        });
                    }
                    newLinks.push({ source: center.id, target: id, color: '#ffffff11' });
                });
            });

            return {
                nodes: Array.from(nodeMap.values()),
                links: newLinks
            };
        });

    } catch (err) {
        console.error("Bulk refresh failed", err);
    } finally {
        setIsLoading(false);
    }
  };

  const onEngineTick = () => {
    if (pendingFocusRef.current) {
      const target = nodesRef.current.find((n: any) => n.id === pendingFocusRef.current);
      if (target && target.x !== undefined && !isNaN(target.x) && (target.x !== 0 || target.y !== 0)) {
        initCameraFly(target);
        pendingFocusRef.current = null;
      }
    }

    if (flyParamsRef.current && fgRef.current) {
      const { startTime, startPos, offset, node } = flyParamsRef.current;
      const now = Date.now();
      const elapsed = now - startTime;
      const duration = 1500;
      
      if (elapsed >= duration) {
        const finalPos = { x: (node.x || 0) + offset.x, y: (node.y || 0) + offset.y, z: (node.z || 0) + offset.z };
        fgRef.current.cameraPosition(finalPos, node, 0);
        flyParamsRef.current = null;
      } else {
        const t = elapsed / duration;
        const ease = 1 - Math.pow(1 - t, 3);
        const currentTargetPos = { x: (node.x || 0) + offset.x, y: (node.y || 0) + offset.y, z: (node.z || 0) + offset.z };
        const interpolatedPos = {
          x: startPos.x + (currentTargetPos.x - startPos.x) * ease,
          y: startPos.y + (currentTargetPos.y - startPos.y) * ease,
          z: startPos.z + (currentTargetPos.z - startPos.z) * ease
        };
        fgRef.current.cameraPosition(interpolatedPos, node, 0);
      }
    }
  };

  const toggleLang = (l: string) => {
    setSelectedLangs(prev => prev.includes(l) ? prev.filter(x => x !== l) : [...prev, l]);
  };

  const updateConfig = (key: string, val: any) => {
    setConfig(prev => ({ ...prev, [key]: val }));
  };

  return (
    <div className="w-full h-screen bg-black overflow-hidden relative font-sans">
      
      {!isInitialized && (
        <InitializationScreen 
          isLoading={isLoading} 
          selectedLangs={selectedLangs} 
          toggleLang={toggleLang} 
          startNebula={startNebula} 
        />
      )}

      <ForceGraph3D
        ref={fgRef}
        graphData={data}
        backgroundColor="#000000"
        showNavInfo={false}
        nodeLabel={(node: any) => `${node.name || 'Unknown'} (${(node.lang || '??').toUpperCase()})`}
        nodeRelSize={1.5}
        nodeVal={(node: any) => node.val}
        
        // Robust Node Coloring
        nodeColor={(node: any) => {
          if (!node) return '#555555';
          if (selectedNode) {
            if (node.id === selectedNode.id) return '#ffffff'; 
            if (neighbors.has(node.id)) {
               return colorByCommunity 
                 ? (node.commColor || '#555555') 
                 : (node.langColor || '#555555');
            }
            return '#111111'; 
          }
          return colorByCommunity 
            ? (node.commColor || '#555555') 
            : (node.langColor || '#555555');
        }}
        
        // Temporarily simplified opacity for debugging
        nodeOpacity={1}

        linkWidth={(link: any) => {
          if (selectedNode) {
            const s = typeof link.source === 'object' ? link.source.id : link.source;
            const t = typeof link.target === 'object' ? link.target.id : link.target;
            return (s === selectedNode.id || t === selectedNode.id) ? 1.5 : 0.1;
          }
          return 0.5;
        }}

        linkOpacity={(link: any) => {
          if (selectedNode) {
            const s = typeof link.source === 'object' ? link.source.id : link.source;
            const t = typeof link.target === 'object' ? link.target.id : link.target;
            return (s === selectedNode.id || t === selectedNode.id) ? 0.6 : 0.05;
          }
          return 0.15;
        }}

        enableNodeDrag={false}
        onNodeClick={(node: any) => focusOnNode(node.qid, node.name, node.lang)}
        onEngineTick={onEngineTick}
      />
      
      {isInitialized && (
        <>
          <NebulaInfo selectedLangs={selectedLangs} activeNodeCount={data.nodes.length} />

          <SearchOverlay 
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            searchResults={searchResults}
            isSearching={isSearching}
            focusOnNode={focusOnNode}
          />

          <NodeDetailsPanel 
            node={selectedNode} 
            onClose={() => setSelectedNode(null)} 
          />

          <ControlDeck 
            isPhysicsPaused={isPhysicsPaused}
            setIsPhysicsPaused={setIsPhysicsPaused}
            autoRotate={autoRotate}
            setAutoRotate={setAutoRotate}
            colorByCommunity={colorByCommunity}
            setColorByCommunity={setColorByCommunity}
            onResetCamera={handleResetCamera}
            onOpenSettings={() => setShowSettings(true)}
          />

          <SettingsPanel 
            isOpen={showSettings}
            onClose={() => setShowSettings(false)}
            config={config}
            updateConfig={updateConfig}
            onBulkRefresh={handleBulkRefresh}
          />

          {/* Summoning Overlay */}
          {isSpawningNode && (
            <div className="absolute inset-0 z-50 pointer-events-none flex items-center justify-center">
              <div className="p-8 rounded-full bg-blue-500/5 border border-blue-500/20 backdrop-blur-3xl animate-pulse">
                <div className="flex flex-col items-center gap-4">
                  <Loader2 className="text-blue-400 animate-spin" size={32} />
                  <div className="text-center">
                    <p className="text-white/40 text-[10px] uppercase tracking-[0.4em] font-mono">Summoning Knowledge</p>
                    <p className="text-blue-400 font-bold text-lg tracking-tight">{isSpawningNode}</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {isLoading && (
        <div className="absolute inset-0 z-[100] bg-[#050505] flex flex-col items-center justify-center">
          <Loader2 className="text-blue-500 animate-spin mb-6" size={64} />
          <p className="text-white/20 font-mono text-[10px] uppercase tracking-[0.4em] animate-pulse">
            Synthesizing Knowledge Nebula...
          </p>
        </div>
      )}
    </div>
  );
};

export default WikiNebula;