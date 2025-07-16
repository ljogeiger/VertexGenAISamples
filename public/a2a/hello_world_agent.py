from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.auth.user import UnauthenticatedUser
from a2a.utils import new_agent_text_message
from google import genai
from google.genai import types


# --8<-- [start:HelloWorldAgent]
class HelloWorldAgent:
    """Hello World Agent."""

    async def invoke(self, context: RequestContext) -> str:
        user_input = context.get_user_input()
        user = context.call_context.user
        print(f"user: {user}")
        
        # Use Gemini API to determine response
        response_type = await self._determine_response_type(user_input)
        print(f"response_type: {response_type}")
        
        if response_type == "super" and user.is_authenticated:
            return "Super Hello World"
        elif response_type == "normal":
            return "Hello World"
        else: return "Invalid user input or user tried to use super hello world and is not authenticated"
    
    async def _determine_response_type(self, user_input: str) -> str:
        """Use Gemini API to determine whether to return 'super' or 'normal' response."""
        try:
            client = genai.Client(
                vertexai=True,
                project="sandbox-aiml",  # You may need to update this project ID
                location="global"
            )
            
            model = "gemini-2.0-flash"
            
            prompt = f"""
            Response either "super" or "normal" based on the user input. 
            You are determining whether to response with a Super Hello World or a normal Hello World.

            Use super hello world if the user feels really excited. 
            Use normal hello world if the user is just saying hello.

            Example:
            User input: "Hi!"
            Response: "super"

            User input: "hello"
            Response: "normal"

            User input: "{user_input}"
            
            Respond with only one word: either "super" or "normal"
            """
            
            generate_content_config = types.GenerateContentConfig(
                temperature=0.1,  # Low temperature for consistent responses
                max_output_tokens=10,
                response_modalities=["TEXT"],
                safety_settings=[
                    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
                    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
                    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
                    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF")
                ],
            )
            
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=generate_content_config,
            )
            
            result = str(response.text).strip().lower()
            if result == "super":
                return "super"
            else:
                return "normal"
                
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            # Fallback to normal response if API call fails
            return "normal"


# --8<-- [end:HelloWorldAgent]


# --8<-- [start:HelloWorldAgentExecutor_init]
class HelloWorldAgentExecutor(AgentExecutor):
    """Test AgentProxy Implementation."""

    def __init__(self):
        self.agent = HelloWorldAgent()

    # --8<-- [end:HelloWorldAgentExecutor_init]
    # --8<-- [start:HelloWorldAgentExecutor_execute]
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        print(f"user input: {context.get_user_input()}\n")
        # user input: give me a super hi
        print(f"task_id: {context.task_id}\ncontext_id: {context.context_id}, \ncall_context: {context.call_context}")
        # task_id: e71e549b-241b-4133-b726-edc08ea21720
        # context_id: ecdfd9ac-3806-41c7-89d5-bf9b440de78b, 
        # call_context: state={'headers': {'host': 'localhost:9999', 'accept-encoding': 'gzip, deflate', 'connection': 'keep-alive', 'user-agent': 'python-httpx/0.28.1', 'accept': 'text/event-stream', 'cache-control': 'no-store', 'content-length': '242', 'content-type': 'application/json'}} user=<a2a.auth.user.UnauthenticatedUser object at 0x10557bc50>

        result = await self.agent.invoke(context)
        await event_queue.enqueue_event(new_agent_text_message(result))

    # --8<-- [end:HelloWorldAgentExecutor_execute]

    # --8<-- [start:HelloWorldAgentExecutor_cancel]
    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception('cancel not supported')

    # --8<-- [end:HelloWorldAgentExecutor_cancel]