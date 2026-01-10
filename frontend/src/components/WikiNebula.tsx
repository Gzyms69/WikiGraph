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

// --- PROCEDURAL ENGINES ---

// 1. Color Engine: Consistent HSL from string
const getLangColor = (lang: string) => {
  if (!lang || lang === '??') return '#555555';
  let hash = 0;
  for (let i = 0; i < lang.length; i++) {
    hash = lang.charCodeAt(i) + ((hash << 5) - hash);
  }
  // Hue: Hash % 360, Sat: 70%, Light: 50%
  const h = Math.abs(hash % 360);
  return `hsl(${h}, 70%, 50%)`;
};

// 2. Layout Engine: Dynamic Spiral Assignment
const langPositionRegistry = new Map<string, {x: number, y: number, z: number}>();
const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));

const getLangCenter = (lang: string) => {
  if (!lang || lang === '??') return { x: 0, y: 0, z: 0 };
  
  if (!langPositionRegistry.has(lang)) {
    const index = langPositionRegistry.size + 1; // Start at 1
    const y = index * 20 - 200; // Vertical spiral
    const radius = 300;
    const theta = index * GOLDEN_ANGLE;
    
    const x = radius * Math.cos(theta);
    const z = radius * Math.sin(theta);
    
    langPositionRegistry.set(lang, { x, y, z });
  }
  
  return langPositionRegistry.get(lang)!;
};

// Stable Community Color Generator (Still useful for sub-clusters)
const getCommunityColor = (id?: number) => {
  if (id === undefined) return '#555555';
  const colors = [
    '#ff4500', '#2e8b57', '#4169e1', '#daa520', '#ff69b4', 
    '#00ffff', '#7fff00', '#ff00ff', '#1e90ff', '#ff1493'
  ];
  return colors[id % colors.length];
};

interface FlyParams {
  startTime: number;
  startPos: { x: number; y: number; z: number };
  offset: { x: number; y: number; z: number };
  node: GraphNode;
}

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
  
  // Default to browser locale or empty, NOT hardcoded 'pl'/'de'
  const [selectedLangs, setSelectedLangs] = useState<string[]>([]);

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
        
        // 1. Standard Forces
        fgRef.current.d3Force('charge').strength(-config.forceStrength);
        fgRef.current.d3Force('link').distance(config.forceDistance);

        // 2. Custom Force: Language Clustering
        // Pulls nodes gently towards their procedural language center
        fgRef.current.d3Force('lang_cluster', (alpha: number) => {
          for (const node of nodesRef.current) {
            const lang = (node as any).lang || 'unknown';
            const center = getLangCenter(lang);
            
            // Strength factor (0.05) determines how strictly they adhere to the cluster
            const strength = 0.05 * alpha; 
            
            if (node.x !== undefined) node.x += (center.x - node.x) * strength;
            if (node.y !== undefined) node.y += (center.y - node.y) * strength;
            if (node.z !== undefined) node.z += (center.z - node.z) * strength;
          }
        });
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
      const langParam = selectedLangs.length > 0 ? selectedLangs.join(",") : "";
      const url = langParam ? `${API_BASE}/graph/nebula?langs=${langParam}&limit=150` : `${API_BASE}/graph/nebula?limit=150`;
      
      const res = await axios.get(url);
      const nodes = res.data.nodes.map((n: any) => {
        const lang = n.lang || 'unknown';
        const center = getLangCenter(lang);
        return {
          ...n,
          langColor: getLangColor(lang),
          commColor: getCommunityColor(n.community),
          val: Math.max(Math.sqrt(n.val || 0) * 2, 2),
          // Procedural Spawn: Near dynamically assigned language center
          x: center.x + (Math.random() - 0.5) * 200,
          y: center.y + (Math.random() - 0.5) * 200,
          z: center.z + (Math.random() - 0.5) * 200
        };
      });
      setData({ nodes, links: res.data.links || [] });
      setIsInitialized(true);
      
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
      flyParamsRef.current = null;
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
      const neighborsRes = await axios.post(`${API_BASE}/graph/weighted-neighbors`, {
        qid,
        lang,
        limit: config.neighborLimit,
        weights: config.algorithmWeights
      });
      
      const center = getLangCenter(lang);
      const newNode: GraphNode = { 
        id: targetId,
        qid: qid,
        name: title || qid, 
        lang: lang, 
        val: 12, 
        color: getLangColor(lang),
        langColor: getLangColor(lang),
        commColor: getCommunityColor(0),
        // Spawn near its procedural language center
        x: center.x + (Math.random() - 0.5) * 50,
        y: center.y + (Math.random() - 0.5) * 50,
        z: center.z + (Math.random() - 0.5) * 50
      };

      const neighborNodes = neighborsRes.data.neighbors.map((nb: any) => {
        const nbLang = nb.lang || 'unknown';
        const nbCenter = getLangCenter(nbLang);
        return {
          id: (nb.lang && nb.lang !== '??') ? `${nb.lang}:${nb.qid}` : `concept:${nb.qid}`,
          qid: nb.qid,
          name: nb.title || nb.qid || 'Unknown',
          lang: nbLang,
          val: 5,
          color: '#333333',
          langColor: getLangColor(nbLang),
          commColor: '#333333',
          // Pull towards THEIR language center
          x: nbCenter.x + (Math.random() - 0.5) * 100,
          y: nbCenter.y + (Math.random() - 0.5) * 100,
          z: nbCenter.z + (Math.random() - 0.5) * 100
        };
      });

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

  // 4. Bulk Refresh Logic
  const handleBulkRefresh = async () => {
    const centers = data.nodes.filter(n => data.links.some(l => 
        (typeof l.source === 'string' ? l.source : l.source.id) === n.id
    ));

    if (centers.length === 0) return;
    
    setIsLoading(true);
    try {
        const batchSize = 5;
        const results: any = {};
        
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

        setData(prev => {
            const nodeMap = new Map(prev.nodes.map(n => [n.id, n]));
            const newLinks: any[] = [];

            centers.forEach(center => {
                const neighbors = results[center.qid] || [];
                neighbors.forEach((nb: any) => {
                    const id = (nb.lang && nb.lang !== '??') ? `${nb.lang}:${nb.qid}` : `concept:${nb.qid}`;
                    if (!nodeMap.has(id)) {
                        const nbLang = nb.lang || 'unknown';
                        const nbCenter = getLangCenter(nbLang);
                        nodeMap.set(id, {
                            id, qid: nb.qid, name: nb.title, lang: nbLang, val: 5,
                            color: '#333333', langColor: getLangColor(nbLang), commColor: '#333333',
                            // New neighbors respect dynamic language centers
                            x: nbCenter.x + (Math.random() - 0.5) * 50,
                            y: nbCenter.y + (Math.random() - 0.5) * 50,
                            z: nbCenter.z + (Math.random() - 0.5) * 50
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