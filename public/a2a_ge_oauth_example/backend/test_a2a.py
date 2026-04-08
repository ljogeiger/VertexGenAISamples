from a2a.types import AgentCard, Security, AuthorizationCodeOAuthFlow
from pydantic import BaseModel

security = Security(
    authorizationCode=AuthorizationCodeOAuthFlow(
        authorizationUrl="https://accounts.google.com/o/oauth2/v2/auth",
        tokenUrl="https://oauth2.googleapis.com/token",
        scopes={
            "https://www.googleapis.com/auth/calendar": "Access calendar",
            "https://www.googleapis.com/auth/calendar.events": "Access events"
        }
    )
)

card = AgentCard(
    name="Test",
    description="Test",
    url="http://test",
    version="1.0",
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    security=security
)

print(card.model_dump_json())
