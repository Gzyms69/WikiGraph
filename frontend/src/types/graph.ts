export interface GraphNode {
  id: string; 
  qid: string;
  name: string;
  val: number;
  lang: string;
  community?: number;
  color?: string;
  x?: number;
  y?: number;
  z?: number;
}

export interface GraphData {
  nodes: GraphNode[];
  links: any[];
}
