from fastapi import APIRouter, HTTPException
from app.database import db
import logging

# Configure router logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/shortest-path")
def shortest_path(start: str, end: str, lang: str = "pl"):
    """
    Finds the shortest path between two articles (by title) across the graph.
    Returns path with standardized lang:qid IDs.
    """
    query = """
    MATCH (start:Article {title: $start, lang: $lang})
    MATCH (end:Article {title: $end})
    MATCH p = shortestPath((start)-[:REPRESENTS|LINKS_TO*]-(end))
    RETURN [n in nodes(p) | {
        label: labels(n)[0], 
        title: n.title, 
        qid: n.qid, 
        lang: n.lang,
        id: CASE 
            WHEN 'Article' IN labels(n) THEN n.lang + ':' + n.qid 
            ELSE n.qid 
        END
    }] as path, length(p) as hops
    """
    
    with db.get_session() as session:
        result = session.run(query, start=start, end=end, lang=lang).single() 
        
    if not result:
        raise HTTPException(status_code=404, detail="Path not found or nodes do not exist")
        
    return result.data()

@router.get("/nebula")
def get_nebula_sample(langs: str = None, limit: int = 150):
    """
    Returns a sample of high-importance nodes with PageRank scores and Community IDs,
    including the links between them.
    Refactored to use GDS Mutate for stability.
    """
    lang_list = langs.split(",") if langs else []
    
    # 1. Setup Graph & Analytics (Mutate Phase)
    try:
        with db.get_session() as session:
            # Check if graph exists first to avoid unnecessary drops
            exists = session.run("CALL gds.graph.exists('wikigraph') YIELD exists").single()["exists"]
            
            # Always refresh for this demo to ensure properties are mutated
            if exists:
                session.run("CALL gds.graph.drop('wikigraph')")
            
            logger.info("Projecting 'wikigraph'...")
            session.run("""
                CALL gds.graph.project(
                    'wikigraph', 
                    ['Concept', 'Article'], 
                    {
                        LINKS_TO: {orientation:'UNDIRECTED'},
                        REPRESENTS: {orientation:'UNDIRECTED'}
                    }
                )
            """)
            
            logger.info("Running PageRank mutation...")
            session.run("CALL gds.pageRank.mutate('wikigraph', { mutateProperty: 'pagerank' })")
            
            logger.info("Running Louvain mutation...")
            session.run("CALL gds.louvain.mutate('wikigraph', { mutateProperty: 'community' })")

            # 2. Fetch Top Nodes
            logger.info(f"Fetching top {limit} nodes...")
            node_query = """
            CALL gds.graph.streamNodeProperty('wikigraph', 'pagerank')
            YIELD nodeId, propertyValue as pagerank
            ORDER BY pagerank DESC
            LIMIT $limit
            WITH nodeId, pagerank
            WITH nodeId, pagerank, gds.util.nodeProperty('wikigraph', nodeId, 'community') as community
            WITH gds.util.asNode(nodeId) as n, pagerank, community
            MATCH (n)<-[:REPRESENTS]-(a:Article)
            """
            
            if lang_list:
                node_query += " WHERE a.lang IN $langs "
                
            node_query += """
            RETURN n.qid as qid, 
                   a.lang + ':' + n.qid as id,
                   a.title as name, 
                   pagerank as val,
                   a.lang as lang,
                   coalesce(community, -1) as community
            """
            
            nodes = session.run(node_query, limit=limit, langs=lang_list).data()
            logger.info(f"Found {len(nodes)} nodes.")
            
            # 3. Fetch links between these nodes
            qids = [n['qid'] for n in nodes]
            links = []
            
            if qids:
                link_query = """
                MATCH (c1:Concept)-[:LINKS_TO]-(c2:Concept)
                WHERE c1.qid IN $qids AND c2.qid IN $qids
                RETURN c1.qid as source_qid, c2.qid as target_qid
                """
                raw_links = session.run(link_query, qids=qids).data()
                logger.info(f"Found {len(raw_links)} links.")
                
                qid_to_id = {n['qid']: n['id'] for n in nodes}
                seen = set()
                for rl in raw_links:
                    s = qid_to_id.get(rl['source_qid'])
                    t = qid_to_id.get(rl['target_qid'])
                    if s and t:
                        pair = tuple(sorted([s, t]))
                        if pair not in seen:
                            links.append({"source": s, "target": t})
                            seen.add(pair)
            
            return {"nodes": nodes, "links": links}

    except Exception as e:
        logger.error(f"Nebula Error: {str(e)}")
        # Return empty structure on failure so frontend doesn't crash
        print(f"Error generating nebula: {e}")
        return {"nodes": [], "links": []}

@router.get("/neighbors")
def get_neighbors(qid: str, lang: str = "pl", limit: int = 15):
    """
    Get 1-hop neighbors of a Concept, ranked by Jaccard Similarity (Semantic Relevance).
    This heavily penalizes 'super-hubs' (Dates, Years) that share few common neighbors 
    relative to their massive degree.
    """
    query = """
    MATCH (c:Concept {qid: $qid})
    WITH c, COUNT { (c)-[:LINKS_TO]-() } as c_degree
    
    MATCH (c)-[:LINKS_TO]-(neighbor:Concept)
    MATCH (neighbor)<-[:REPRESENTS]-(a:Article)
    
    // 1. Hard Filters for obvious noise
    WHERE NOT a.title =~ '^\\d+$' 
      AND NOT a.title =~ '^\\d+ .*'
      AND NOT a.title STARTS WITH 'List of'
      AND NOT a.title STARTS WITH 'Lista '
      AND NOT a.title STARTS WITH 'Kategoria:'
      AND NOT a.title STARTS WITH 'Category:'
      AND NOT a.title CONTAINS 'Biografien'
    
    // 2. Jaccard Similarity Calculation
    // Intersection: Count of nodes connected to BOTH c and neighbor
    MATCH (c)-[:LINKS_TO]-(common)-[:LINKS_TO]-(neighbor)
    WITH c, c_degree, neighbor, a, count(common) as intersection
    
    // Union: c_degree + n_degree - intersection
    WITH neighbor, a, intersection, c_degree, COUNT { (neighbor)-[:LINKS_TO]-() } as n_degree
    WITH neighbor, a, intersection, (c_degree + n_degree - intersection) as union_size
    
    WITH neighbor, a, 
         CASE WHEN union_size > 0 
              THEN (1.0 * intersection / union_size) 
              ELSE 0.0 
         END as score
    
    ORDER BY score DESC, CASE WHEN a.lang = $lang THEN 1 ELSE 2 END, size(a.title) DESC
    
    // 3. Return best article per neighbor
    WITH neighbor, score, collect(a) as articles
    WITH neighbor, score, articles[0] as article
    
    RETURN neighbor.qid as qid, 
           article.title as title, 
           article.lang as lang,
           'LINKS_TO' as type,
           score
    LIMIT $limit
    """
    with db.get_session() as session:
        results = session.run(query, qid=qid, lang=lang, limit=limit).data()
    return {"center": qid, "neighbors": results}

@router.get("/recommendations")
def get_recommendations(title: str, lang: str = "pl", limit: int = 5):
    """
    Personalized PageRank recommendations.
    """
    find_id_query = """
    MATCH (a:Article {title: $title, lang: $lang})-[:REPRESENTS]->(c:Concept)
    RETURN id(c) as nodeId
    """
    ppr_query = """
    CALL gds.pageRank.stream('wikigraph', { sourceNodes: [$sourceNodeId] })
    YIELD nodeId, score
    RETURN gds.util.asNode(nodeId).qid as qid, score
    ORDER BY score DESC
    LIMIT $limit
    """
    with db.get_session() as session:
        node_record = session.run(find_id_query, title=title, lang=lang).single()
        if not node_record:
            raise HTTPException(status_code=404, detail="Article not found")
        source_id = node_record["nodeId"]
        results = session.run(ppr_query, sourceNodeId=source_id, limit=limit + 1).data()
    recommendations = [r for r in results if r["qid"] != results[0]["qid"]]
    return {"seed": title, "recommendations": recommendations[:limit]}
