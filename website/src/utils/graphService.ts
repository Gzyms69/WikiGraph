import masterPool from '../demo-data/demo-nebula.json';

// Types for our graph data
export interface Node {
  id: string;
  name: string;
  val: number; // Influence Rank
  community: number; // Cluster ID
  lang: string;
  desc?: string; // Description
  // Physical coords (optional, for forcing layout)
  x?: number;
  y?: number;
  z?: number;
}

export interface Link {
  source: string | Node;
  target: string | Node;
}

export class GraphService {
  // 1. Initial Seed: Returns a small, interesting subset to start with
  static getInitialGraph() {
    // Start with a few major hubs to make the graph look interesting immediately
    const seedIds = ["en:Q1", "en:Q9", "en:Q5", "en:Q13", "en:Q3"]; // Universe, Earth, Computing, Biology, Physics
    
    // Find these nodes
    const nodes = masterPool.nodes.filter(n => seedIds.includes(n.id));
    
    // Find links ONLY between these specific nodes (closed world)
    const links = masterPool.links.filter(l => {
      const s = typeof l.source === 'object' ? (l.source as any).id : l.source;
      const t = typeof l.target === 'object' ? (l.target as any).id : l.target;
      return seedIds.includes(s) && seedIds.includes(t);
    });

    return { nodes, links };
  }

  // 2. Expand: Finds neighbors of a specific node
  static getNeighbors(nodeId: string, currentNodes: Node[]) {
    const existingIds = new Set(currentNodes.map(n => n.id));
    
    // Find all links connected to this node in the Master Pool
    const relevantLinks = masterPool.links.filter(l => {
      const s = typeof l.source === 'object' ? (l.source as any).id : l.source;
      const t = typeof l.target === 'object' ? (l.target as any).id : l.target;
      return s === nodeId || t === nodeId;
    });

    // Identify the neighbor IDs
    const neighborIds = new Set<string>();
    relevantLinks.forEach(l => {
      const s = typeof l.source === 'object' ? (l.source as any).id : l.source;
      const t = typeof l.target === 'object' ? (l.target as any).id : l.target;
      neighborIds.add(s === nodeId ? t : s);
    });

    // Filter out nodes we already have
    const newNeighborIds = Array.from(neighborIds).filter(id => !existingIds.has(id));

    // Get the actual node objects, limited to 5 to prevent explosion
    const newNodes = masterPool.nodes
      .filter(n => newNeighborIds.includes(n.id))
      .slice(0, 5);

    return newNodes;
  }

  // 3. Re-Link: Ensures all visible nodes are connected if a link exists in Master Pool
  static getLinksForNodes(nodes: Node[]) {
    const nodeIds = new Set(nodes.map(n => n.id));
    return masterPool.links.filter(l => {
      const s = typeof l.source === 'object' ? (l.source as any).id : l.source;
      const t = typeof l.target === 'object' ? (l.target as any).id : l.target;
      return nodeIds.has(s) && nodeIds.has(t);
    });
  }

  // 4. Search: Simple substring match
  static search(query: string) {
    const q = query.toLowerCase();
    return masterPool.nodes.find(n => n.name.toLowerCase().includes(q));
  }

  // 5. Suggestions: Returns list of matching nodes
  static getSuggestions(query: string): Node[] {
    if (!query || query.length < 2) return [];
    const q = query.toLowerCase();
    return masterPool.nodes
      .filter(n => n.name.toLowerCase().includes(q))
      .slice(0, 5); // Limit to 5 suggestions
  }
}