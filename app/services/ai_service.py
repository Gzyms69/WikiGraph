import logging
import abc
import asyncio
from typing import Optional, List
from app.core.config import settings
from app.models import Concept

logger = logging.getLogger(__name__)

# Graceful Degradation for missing dependency
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    logger.warning("google-generativeai not found. AI features will be limited to Mock provider.")

class AIProvider(abc.ABC):
    @abc.abstractmethod
    async def generate_insight(self, concept: Concept) -> str:
        pass

    @property
    @abc.abstractmethod
    def model_name(self) -> str:
        pass

class MockAIProvider(AIProvider):
    @property
    def model_name(self) -> str:
        return "Structural Mock"

    async def generate_insight(self, concept: Concept) -> str:
        logger.info(f"Mock AI generating insight for {concept.title} ({concept.qid})")
        
        neighbor_summary = ""
        if concept.neighbors:
            top_neighbors = [n.title for n in concept.neighbors[:5] if n.title]
            neighbor_summary = f" It is connected to {', '.join(top_neighbors)}."
            
        return (
            f"[MOCK INSIGHT] {concept.title} is a notable entity in the WikiGraph knowledge base. "
            f"Analysis of {len(concept.neighbors or [])} connections suggests it plays a structural role in the "
            f"{concept.lang.upper()} graph.{neighbor_summary}"
        )

class GeminiFlashProvider(AIProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini provider")
        genai.configure(api_key=api_key)
        # Updated to the latest recommended stable model for 2026
        self._model_id = 'gemini-2.5-flash'
        self.model = genai.GenerativeModel(self._model_id)

    @property
    def model_name(self) -> str:
        return f"Gemini {self._model_id.replace('gemini-', '').replace('-', ' ').title()}"

    def _compile_dossier(self, c: Concept) -> str:
        dossier = f"ENTITY IDENTITY:\n- Title: {c.title}\n- Wikidata ID: {c.qid}\n- Language: {c.lang.upper()} Wikipedia\n\n"
        
        # Metrics
        dossier += "GRAPH IMPORTANCE METRICS:\n"
        if c.pagerank is not None: dossier += f"- Global Importance (PageRank): {c.pagerank:.8f}\n"
        if c.auth_score is not None: dossier += f"- Authority Score (HITS): {c.auth_score:.8f}\n"
        if c.degree is not None: dossier += f"- Total Degree (Connectivity): {c.degree}\n"
        if c.in_degree is not None: dossier += f"- In-degree (Visibility): {c.in_degree}\n"
        if c.out_degree is not None: dossier += f"- Out-degree (Referencing): {c.out_degree}\n"
        dossier += "\n"

        # Topology
        dossier += "NEIGHBORHOOD TOPOLOGY:\n"
        if c.triangle_count is not None: dossier += f"- Local Clustering (Triangle Count): {c.triangle_count}\n"
        if c.louvain_id is not None: dossier += f"- Community Group (Broad): {c.louvain_id}\n"
        if c.leiden_id is not None: dossier += f"- Community Niche (Fine): {c.leiden_id}\n"
        dossier += "\n"

        # Similarities
        if c.similarities:
            dossier += "TOP CONTEXTUAL SIMILARITIES:\n"
            for metric, neighbors in c.similarities.items():
                label = "Adamic-Adar Index (Shared Context)" if metric == "adamic_adar" else "Jaccard Coefficient (Set Overlap)"
                items = [f"{n.score:.2f} with '{n.title}'" for n in neighbors if n.title]
                if items:
                    dossier += f"- {label}: {', '.join(items)}\n"
            dossier += "\n"

        # Infobox
        if c.infobox:
            dossier += "EXTRACTED KNOWLEDGE (INFOBOX):\n"
            for item in c.infobox[:8]: 
                if isinstance(item, dict):
                    # Assuming API v6 structure: {"key": "...", "value": "..."}
                    if 'key' in item and 'value' in item:
                        val = str(item['value']).replace('\n', ' ')
                        dossier += f"- Property '{item['key']}': {val}\n"
        
        return dossier

    async def generate_insight(self, concept: Concept) -> str:
        try:
            # 1. Compile the Dossier
            dossier = self._compile_dossier(concept)
            
            # 2. Construct the Analyst Prompt
            prompt = (
                f"You are a Senior Graph Intelligence Analyst. You are provided with an explicit structural dossier "
                f"of an entity from a massive knowledge graph.\n\n"
                f"{dossier}\n\n"
                f"TASK: Analyze the significance of this entity by synthesizing its mathematical metrics (Importance, Similarity, Topology) "
                f"with its real-world metadata.\n"
                f"INSTRUCTIONS:\n"
                f"1. Connect the metrics to the metadata (e.g., 'High PageRank confirms its central role in...').\n"
                f"2. Reference specific high-similarity entities to explain the context.\n"
                f"3. Output 3 to 5 concise sentences.\n"
                f"4. Do not invent facts outside the provided Dossier."
            )

            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            # Fallback to mock on quota error
            if "429" in str(e) or "ResourceExhausted" in str(e):
                logger.warning("Gemini Quota Exceeded (429). Falling back to Mock Insight.")
                mock = MockAIProvider()
                return await mock.generate_insight(concept)
            
            logger.error(f"Gemini API error: {e}")
            return "Unable to generate insight at this time due to an external API error."

class AIService:
    _provider: Optional[AIProvider] = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_provider(cls) -> AIProvider:
        if cls._provider is None:
            async with cls._lock:
                if cls._provider is None:
                    config = settings.get("ai", {})
                    provider_type = config.get("provider", "mock")
                    api_key = config.get("api_key", "")

                    if provider_type == "gemini":
                        if not HAS_GENAI:
                            logger.warning("Gemini provider requested but google-generativeai module missing. Falling back to Mock.")
                            cls._provider = MockAIProvider()
                        else:
                            try:
                                cls._provider = GeminiFlashProvider(api_key)
                                logger.info("Initialized Gemini Flash AI Provider")
                            except ValueError as e:
                                logger.warning(f"Failed to init Gemini Provider: {e}. Falling back to Mock.")
                                cls._provider = MockAIProvider()
                    else:
                        cls._provider = MockAIProvider()
                        logger.info("Initialized Mock AI Provider")
        
        return cls._provider

    @staticmethod
    async def analyze_node(concept: Concept) -> str:
        provider = await AIService.get_provider()
        return await provider.generate_insight(concept)

    @staticmethod
    async def get_model_name() -> str:
        provider = await AIService.get_provider()
        return provider.model_name
