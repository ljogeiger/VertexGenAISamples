from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue, EventConsumer

from google.adk import Runner, Agent
from google.adk.memory.base_memory_service import BaseMemoryService
from google.adk.artifacts.base_artifact_service import BaseArtifactService
from google.adk.sessions.base_session_service import BaseSessionService
from google.adk.sessions import InMemorySessionService, Session

import uuid
from a2a.types import Task, TaskState



class AdkAgentToA2AExecutor(AgentExecutor):
    _runner: Runner;

    def __init__(
        self,
        name: str,
        agent: Agent,
        session_service: BaseSessionService = InMemorySessionService(),
        artifact_service: BaseArtifactService | None = None,
        memory_service: BaseMemoryService | None = None,
    ):
        self._runner = Runner(
            app_name=name,
            agent=agent,
            session_service=session_service,
            artifact_service=artifact_service,
            memory_service=memory_service,
        )
        self._name = name
        self._user_id = 'remote_agent'

    def new_task(message):
        # Use existing contextId if present, else generate a new one
        context_id = getattr(message, "contextId", None) or str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        return Task(
            id=task_id,
            contextId=context_id,
            status=TaskState.submitted,  # or TaskState.working if that's your default
            input=message,
            history=[],
            artifacts=[]
        )

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        query = context.get_user_input()
        task = context.current_task
        # This agent always produces Task objects. If this request does
        # not have current task, create a new one and use it.
        if not task:
            if not context.message:
                return

            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(event_queue, task.id, task.contextId)
        session_id = task.contextId
        session = await self._runner.session_service.get_session(
            app_name=self._name,
            user_id=self._user_id,
            session_id=session_id,
        )
        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self._name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )
        content = types.Content(
            role='user', parts=[types.Part.from_text(text=query)]
        )

        # Working status
        await updater.start_work()
 	 
        # To record partial text chunks
        full_response_text = ""

        async for event in self._runner.run_async(
            user_id=self._user_id, session_id=session.id, new_message=content
        ):
            if event.partial and event.content and event.content.parts and event.content.parts[0].text:
                full_response_text += event.content.parts[0].text
        
            # Check if this event marks the final response.
            if event.is_final_response():

                # 1. Check if it has text parts.
                if event.content and event.content.parts and event.content.parts[0].text:
                    final_text = full_response_text + (event.content.parts[0].text if not event.partial else "")
                    await updater.add_artifact(
                    [Part(root=TextPart(text=final_text))], name='response'
                    )
                    await updater.complete()

                # 2. If there's function response. Normally LLM summarises it and adds to text parts. If not, we simply include the function response.
                elif event.actions and event.actions.skip_summarization and event.get_function_responses():
                    response_data = event.get_function_responses()
                    await updater.add_artifact(
                    [Part(root=TextPart(text=str(response_data[0].response)))], name='response'
                    )
                    await updater.complete()

                # 3. In special case of long running tools, we mark the task as working.
                elif hasattr(event, 'long_running_tool_ids') and event.long_running_tool_ids:
                    await updater.update_status(
                    TaskState.working,
                    new_agent_text_message("waiting for tools in background", task.contextId, task.id),
                    final=True,
                    )
                    break;


    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise ServerError(error=UnsupportedOperationError())

    

