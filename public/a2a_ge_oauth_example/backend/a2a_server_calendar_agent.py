import uvicorn
import logging
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, DatabaseTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)

from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor, A2aAgentExecutorConfig
from google.adk.runners import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService

import asyncpg
import sqlalchemy
import sqlalchemy.ext.asyncio
from google.cloud.alloydb.connector import AsyncConnector

from starlette.responses import JSONResponse
from starlette.routing import Route

# Import the root_agent from the calendar agent implementation
from calendar_agent.agent import root_agent
from calendar_agent import agent_tools
from starlette.middleware.base import BaseHTTPMiddleware

class TokenExtractorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
            agent_tools.oauth_token_var.set(token)
        response = await call_next(request)
        return response

async def create_sqlalchemy_engine(
    inst_uri: str,
    user: str,
    password: str,
    db: str
) -> tuple[sqlalchemy.ext.asyncio.engine.AsyncEngine, AsyncConnector]:
    """Creates a connection pool for an AlloyDB instance and returns the pool
    and the connector. Callers are responsible for closing the pool and the
    connector.
    """
    connector = AsyncConnector()

    async def get_conn() -> asyncpg.Connection:
        connect_kwargs = {
            "db": db,
            "ip_type": "PUBLIC",
            "enable_iam_auth": False,
            "user": user,
            "password": password,
        }
        return await connector.connect(
            inst_uri,
            "asyncpg",
            **connect_kwargs,
        )

    # create SQLAlchemy connection pool
    engine = sqlalchemy.ext.asyncio.create_async_engine(
        "postgresql+asyncpg://",
        async_creator=get_conn,
        execution_options={"isolation_level": "AUTOCOMMIT"},
    )

    # Test the database connection
    try:
        async with engine.begin() as conn:
            logger.info("✅ Successfully connected to the database.")
    except Exception as e:
        logger.error(f"❌ Failed to connect to the database or create table: {e}")
    return engine, connector

async def main():
    logger.info("Starting A2A Calendar Agent Server...")

    ALLOYDB_INSTANCE = os.environ.get('ALLOYDB_INSTANCE')
    ALLOYDB_PROJECT = os.environ.get('GOOGLE_CLOUD_PROJECT')
    
    # Check if AlloyDB configs are present
    if ALLOYDB_INSTANCE and ALLOYDB_PROJECT:
        logger.info("AlloyDB config detected. Connecting...")
        ALLOYDB_CLUSTER = os.environ.get('ALLOYDB_CLUSTER')
        ALLOYDB_REGION = os.environ.get('ALLOYDB_REGION')
        ALLOYDB_NAME = os.environ.get('ALLOYDB_NAME')
        ALLOYDB_USER = os.environ.get('ALLOYDB_USER')
        ALLOYDB_PASS = os.environ.get('ALLOYDB_PASS')
        
        instance_uri = f"projects/{ALLOYDB_PROJECT}/locations/{ALLOYDB_REGION}/clusters/{ALLOYDB_CLUSTER}/instances/{ALLOYDB_INSTANCE}"
        
        engine, connector = await create_sqlalchemy_engine(
            instance_uri,
            ALLOYDB_USER,
            ALLOYDB_PASS,
            ALLOYDB_NAME,
        )
        task_store = DatabaseTaskStore(engine)
        agent_tools.engine = engine
    else:
        logger.warning("AlloyDB config not fully specified. Using InMemoryTaskStore for local/reproducible dev.")
        task_store = InMemoryTaskStore()
        agent_tools.engine = None

    a2a_execution_config = A2aAgentExecutorConfig()

    runner = Runner(
        app_name="calendar_agent",
        agent=root_agent,
        artifact_service = InMemoryArtifactService(),
        session_service = InMemorySessionService(),
    )

    a2a_executor = A2aAgentExecutor(runner=runner)

    skill = AgentSkill(
        id='calendar_agent',
        name='Calendar Agent',
        description='Helps manage and schedule calendar events.',
        tags=['calendar', 'scheduling', 'events'],
        examples=['schedule a meeting', 'find free time', 'create event'],
    )

    from a2a.types import Security, AuthorizationCodeOAuthFlow, OAuthFlows

    oauth_flow = AuthorizationCodeOAuthFlow(
        authorizationUrl="https://accounts.google.com/o/oauth2/v2/auth",
        tokenUrl="https://oauth2.googleapis.com/token",
        scopes={
            "https://www.googleapis.com/auth/calendar": "Read and write access to Calendars",
            "https://www.googleapis.com/auth/calendar.events": "Read and write access to Events"
        }
    )

    public_agent_card = AgentCard(
        name='Calendar Agent',
        description='A smart agent for managing calendar events and scheduling.',
        url='https://a2a-calendar-backend.example.com/api/a2a', # This gets dynamic logic
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=AgentCapabilities(streaming=False),
        skills=[skill],
        supportsAuthenticatedExtendedCard=False,
        security=Security(authorizationCode=oauth_flow)
    )

    request_handler = DefaultRequestHandler(
        agent_executor=a2a_executor,
        task_store=task_store
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler
    )

    app = server.build()
    app.add_middleware(TokenExtractorMiddleware)

    async def health_check(request):
        return JSONResponse({"status": "ok"})

    app.add_route("/", health_check, methods=["GET"])

    logger.info("Server configured, starting uvicorn...")

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=9998,
        timeout_keep_alive=300,
        timeout_graceful_shutdown=300,
        access_log=True,
        log_level="info"
    )
    server_instance = uvicorn.Server(config)
    await server_instance.serve()

if __name__ == '__main__':
    # Use standard loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
