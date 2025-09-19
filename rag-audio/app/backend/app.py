import logging
import os
from pathlib import Path

from aiohttp import web
from azure.core.credentials import AzureKeyCredential
from azure.identity import AzureDeveloperCliCredential, DefaultAzureCredential
from dotenv import load_dotenv

from ragtools import attach_rag_tools
from rtmt import RTMiddleTier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voicerag")

async def create_app():
    if not os.environ.get("RUNNING_IN_PRODUCTION"):
        logger.info("Running in development mode, loading from .env file")
        load_dotenv()

    llm_key = os.environ.get("AZURE_OPENAI_API_KEY")
    search_key = os.environ.get("AZURE_SEARCH_API_KEY")

    credential = None
    if not llm_key or not search_key:
        if tenant_id := os.environ.get("AZURE_TENANT_ID"):
            logger.info("Using AzureDeveloperCliCredential with tenant_id %s", tenant_id)
            credential = AzureDeveloperCliCredential(tenant_id=tenant_id, process_timeout=60)
        else:
            logger.info("Using DefaultAzureCredential")
            credential = DefaultAzureCredential()
    llm_credential = AzureKeyCredential(llm_key) if llm_key else credential
    search_credential = AzureKeyCredential(search_key) if search_key else credential
    
    app = web.Application()

    rtmt = RTMiddleTier(
        credentials=llm_credential,
        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        deployment=os.environ["AZURE_OPENAI_REALTIME_DEPLOYMENT"],
        voice_choice=os.environ.get("AZURE_OPENAI_REALTIME_VOICE_CHOICE") or "alloy"
        )
    rtmt.system_message = """
You are a concise voice assistant restricted to the topic: the AI Regulation Act in the Philippines.
Only answer questions if the answer is grounded in the knowledge base via the 'search' tool.

Rules (follow in order, every time):
1) Always use the 'search' tool first to look up relevant passages in the knowledge base.
2) If (and only if) the search returns grounding, use 'report_grounding' to cite the exact source(s).
3) Answer in one short sentence suitable for audio. Be direct, no filler.
4) If the answer is not explicitly in the knowledge base, say: "I don’t know based on the available AI Regulation Act sources."
5) Refuse out-of-scope queries (anything not about the AI Regulation Act in the Philippines) with: 
   "I can only answer questions about the AI Regulation Act in the Philippines based on the indexed data."
6) Never read file names, source names, URLs, IDs, or keys aloud. Do not speculate or rely on prior knowledge.

Scope examples (allowed):
- Definitions, scope, and intent of the AI Regulation Act in the Philippines
- Rights/obligations, governance structures, compliance, timelines, penalties, exemptions
- Risk categories, requirements for providers/deployers, enforcement and appeals
- Interplay with Philippine law and named agencies as reflected in the knowledge base

Out of scope (refuse):
- AI laws in other countries, general AI advice, implementation outside what’s in the indexed data
- Legal advice beyond summarizing the Act’s text in the knowledge base

Style:
- One sentence answers by default; if a list is needed, use up to three bullets, each under 10 words.
""".strip()

    attach_rag_tools(rtmt,
        credentials=search_credential,
        search_endpoint=os.environ.get("AZURE_SEARCH_ENDPOINT"),
        search_index=os.environ.get("AZURE_SEARCH_INDEX"),
        semantic_configuration=os.environ.get("AZURE_SEARCH_SEMANTIC_CONFIGURATION") or None,
        identifier_field=os.environ.get("AZURE_SEARCH_IDENTIFIER_FIELD") or "chunk_id",
        content_field=os.environ.get("AZURE_SEARCH_CONTENT_FIELD") or "chunk",
        embedding_field=os.environ.get("AZURE_SEARCH_EMBEDDING_FIELD") or "text_vector",
        title_field=os.environ.get("AZURE_SEARCH_TITLE_FIELD") or "title",
        use_vector_query=(os.getenv("AZURE_SEARCH_USE_VECTOR_QUERY", "true") == "true")
        )

    rtmt.attach_to_app(app, "/realtime")

    current_directory = Path(__file__).parent
    app.add_routes([web.get('/', lambda _: web.FileResponse(current_directory / 'static/index.html'))])
    app.router.add_static('/', path=current_directory / 'static', name='static')
    
    return app

if __name__ == "__main__":
    host = "localhost"
    port = 8765
    web.run_app(create_app(), host=host, port=port)
