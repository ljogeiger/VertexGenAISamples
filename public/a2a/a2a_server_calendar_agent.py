import uvicorn
import logging
from dotenv import load_dotenv
import asyncio
import os

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
# from calendar_agent_executor import AdkAgentToA2AExecutor
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor, A2aAgentExecutorConfig
from google.adk.runners import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService

import asyncpg
import sqlalchemy
import sqlalchemy.ext.asyncio
from google.cloud.alloydb.connector import AsyncConnector

# Import the root_agent from the calendar agent implementation
from calendar_agent.agent import root_agent  # type: ignore[import]

load_dotenv()

async def create_sqlalchemy_engine(
    inst_uri: str,
    user: str,
    password: str,
    db: str
    ##refresh_strategy: str = "background",
) -> tuple[sqlalchemy.ext.asyncio.engine.AsyncEngine, AsyncConnector]:
    """Creates a connection pool for an AlloyDB instance and returns the pool
    and the connector. Callers are responsible for closing the pool and the
    connector.

    Args:
        instance_uri (str):
            The instance URI specifies the instance relative to the project,
            region, and cluster. For example:
            "projects/my-project/locations/us-central1/clusters/my-cluster/instances/my-instance"
        user (str):
            The database user name, e.g., postgres
        password (str):
            The database user's password, e.g., secret-password
        db (str):
            The name of the database, e.g., mydb
        refresh_strategy (Optional[str]):
            Refresh strategy for the AlloyDB Connector. Can be one of "lazy"
            or "background". For serverless environments use "lazy" to avoid
            errors resulting from CPU being throttled.
    """
    connector = AsyncConnector() ##refresh_strategy=refresh_strategy)

    async def get_conn() -> asyncpg.Connection:
        """Helper function to establish connection with conditional credentials."""
        ##https://github.com/googleapis/langchain-google-alloydb-pg-python/blob/main/src/langchain_google_alloydb_pg/engine.py
        connect_kwargs = {
            "db": db,
            "ip_type": "PUBLIC",
            "enable_iam_auth": False,
            "user": user, 
            "password": password,
        }

        # GRANT CONNECT ON DATABASE "agentorders" TO "admin@lolejniczak.altostrat.com";
        # GRANT USAGE ON SCHEMA "public" TO "admin@lolejniczak.altostrat.com";
        # GRANT SELECT ON ALL TABLES IN SCHEMA "public" TO "admin@lolejniczak.altostrat.com";
        # GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA "public" TO "admin@lolejniczak.altostrat.com";
        # GRANT ALL PRIVILEGES ON  SCHEMA "public" TO "admin@lolejniczak.altostrat.com";

        # Only add user and password to kwargs if they are not None.
        # This supports IAM-based authentication where no user/pass is provided.
        # if user:
        #     connect_kwargs["user"] = user
        # if password:
        #     connect_kwargs["password"] = password
            
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
        async with engine.connect() as conn:
            result = await conn.execute(sqlalchemy.text("SELECT 1"))
            if result.scalar_one() == 1:
                print("✅ Successfully connected to the database.")
            else:
                print("❌ DB connection test failed: Did not receive expected result.")
    except Exception as e:
        print(f"❌ Failed to connect to the database: {e}")
    return engine, connector

async def main():
    logger.info("Starting A2A Calendar Agent Server...")

    ALLOYDB_INSTANCE = os.environ['ALLOYDB_INSTANCE']
    ALLOYDB_CLUSTER = os.environ['ALLOYDB_CLUSTER']
    ALLOYDB_PROJECT = os.environ['GOOGLE_CLOUD_PROJECT']
    ALLOYDB_REGION = os.environ['ALLOYDB_REGION']
    ALLOYDB_NAME = os.environ['ALLOYDB_NAME']
    ALLOYDB_USER = os.environ['ALLOYDB_USER']
    ALLOYDB_PASS = os.environ['ALLOYDB_PASS']

    instance_uri = f"projects/{ALLOYDB_PROJECT}/locations/{ALLOYDB_REGION}/clusters/{ALLOYDB_CLUSTER}/instances/{ALLOYDB_INSTANCE}"

    # The await call is now inside an async function
    engine, connector = await create_sqlalchemy_engine(
        instance_uri,
        ALLOYDB_USER,
        ALLOYDB_PASS,
        ALLOYDB_NAME,
    )

    print(engine)

    alloydb_task_store = DatabaseTaskStore(engine)

    a2a_execution_config = A2aAgentExecutorConfig()

    runner = Runner(
        app_name="calendar_agent",
        agent=root_agent, 
        artifact_service = InMemoryArtifactService(),
        session_service = InMemorySessionService(),
    )

    a2a_executor = A2aAgentExecutor(runner=runner)

    # --8<-- [start:AgentSkill]
    skill = AgentSkill(
        id='calendar_agent',
        name='Calendar Agent',
        description='Helps manage and schedule calendar events.',
        tags=['calendar', 'scheduling', 'events'],
        examples=['schedule a meeting', 'find free time', 'create event'],
    )
    # --8<-- [end:AgentSkill]

    # --8<-- [start:AgentCard]
    public_agent_card = AgentCard(
        name='Calendar Agent',
        description='A smart agent for managing calendar events and scheduling.',
        url='https://sample-a2a-agent-305610648548.us-central1.run.app',
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
        supportsAuthenticatedExtendedCard=False,
    )
    # --8<-- [end:AgentCard]

    request_handler = DefaultRequestHandler(
        agent_executor=a2a_executor, # AdkAgentToA2AExecutor(name="calendar_agent", agent=root_agent),
        task_store=alloydb_task_store # InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
    )

    logger.info("Server configured, starting uvicorn...")

    # The uvicorn.run() function creates a new event loop, which causes a
    # RuntimeError when called from an already running async function.
    # The correct way is to create a uvicorn.Server and await its serve() method.
    config = uvicorn.Config(
        server.build(), 
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
    asyncio.run(main())