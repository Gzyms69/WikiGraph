export interface NodeMetrics {
  pagerank?: number;
  triangle_count?: number;
  auth_score?: number;
  louvain_id?: number;
  leiden_id?: number;
  degree?: number;
  in_degree?: number;
  out_degree?: number;
}

export interface GraphNode {
  id: string; 
  qid: string;
  name: string;
  val: number;
  lang: string;
  community?: number;
  color?: string;
  langColor?: string;
  commColor?: string;
  x?: number;
  y?: number;
  z?: number;
  // Dynamic fields
  metrics?: NodeMetrics;
  description?: string;
}

export interface GraphData {
  nodes: GraphNode[];
  links: any[];
}
