import logging, subprocess

from typing import Any
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
)

import google.auth.transport.requests

def getToken():
  creds, _ = google.auth.default()
  auth_req = google.auth.transport.requests.Request()
  creds.refresh(auth_req)
  return creds.token

async def main() -> None:
    PUBLIC_AGENT_CARD_PATH = '/.well-known/agent.json'
    EXTENDED_AGENT_CARD_PATH = '/agent/authenticatedExtendedCard'

    # Configure logging to show INFO level messages
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)  # Get a logger instance

    # --8<-- [start:A2ACardResolver]
    # base_url = 'http://localhost:9998'
    base_url = 'https://sample-a2a-agent-305610648548.us-central1.run.app'


    # Configure longer timeouts for complex agent operations
    timeout_config = httpx.Timeout(
        connect=30.0,  # Connection timeout
        read=300.0,    # Read timeout (5 minutes for complex operations)
        write=30.0,    # Write timeout
        pool=30.0      # Pool timeout
    )
    
    async with httpx.AsyncClient(timeout=timeout_config) as httpx_client:
        # Initialize A2ACardResolver
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
            # agent_card_path uses default, extended_agent_card_path also uses default
        )
        # --8<-- [end:A2ACardResolver]

        # Fetch Public Agent Card and Initialize Client
        final_agent_card_to_use: AgentCard | None = None

        try:
            logger.info(
                f'Attempting to fetch public agent card from: {base_url}{PUBLIC_AGENT_CARD_PATH}'
            )
            
            _public_card = (
                await resolver.get_agent_card()
            )  # Fetches from default public path
            logger.info('Successfully fetched public agent card:')
            logger.info(
                _public_card.model_dump_json(indent=2, exclude_none=True)
            )
            final_agent_card_to_use = _public_card
            logger.info(
                '\nUsing PUBLIC agent card for client initialization (default).'
            )

            if _public_card.supportsAuthenticatedExtendedCard:
                try:
                    logger.info(
                        f'\nPublic card supports authenticated extended card. Attempting to fetch from: {base_url}{EXTENDED_AGENT_CARD_PATH}'
                    )
                    auth_headers_dict = {
                        'Authorization': 'Bearer dummy-token-for-extended-card'  # Add your token here
                    }
                    _extended_card = await resolver.get_agent_card(
                        relative_card_path=EXTENDED_AGENT_CARD_PATH,
                        http_kwargs={'headers': auth_headers_dict},
                    )
                    logger.info(
                        'Successfully fetched authenticated extended agent card:'
                    )
                    logger.info(
                        _extended_card.model_dump_json(
                            indent=2, exclude_none=True
                        )
                    )
                    final_agent_card_to_use = (
                        _extended_card  # Update to use the extended card
                    )
                    logger.info(
                        '\nUsing AUTHENTICATED EXTENDED agent card for client initialization.'
                    )
                except Exception as e_extended:
                    logger.warning(
                        f'Failed to fetch extended agent card: {e_extended}. Will proceed with public card.',
                        exc_info=True,
                    )
            elif (
                _public_card
            ):  # supportsAuthenticatedExtendedCard is False or None
                logger.info(
                    '\nPublic card does not indicate support for an extended card. Using public card.'
                )

        except Exception as e:
            logger.error(
                f'Critical error fetching public agent card: {e}', exc_info=True
            )
            raise RuntimeError(
                'Failed to fetch the public agent card. Cannot continue.'
            ) from e

        # --8<-- [start:send_message]
        client = A2AClient(
            httpx_client=httpx_client, agent_card=final_agent_card_to_use
        )
        logger.info('A2AClient initialized.')

        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [
                    {'kind': 'text', 'text': 'Hello, please schedule an event for tomorrow at 10-10:30am called test for me. '}
                ],
                'messageId': uuid4().hex,
            },
        }
        request = SendMessageRequest(
            id=str(uuid4()), params=MessageSendParams(**send_message_payload)
        )

        logger.info("Sending message request...")
        logger.info(f"Request payload: {send_message_payload}")
        
        try:
            response = await client.send_message(request)
            logger.info("Successfully received response")
            print(response.model_dump(mode='json', exclude_none=True))
        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)
            raise
        # --8<-- [end:send_message]

        task_id = response.root.result.id
        context_id = response.root.result.contextId

        send_message_payload_2: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [
                    {'kind': 'text', 'text': 'yes'}
                    ],
                'messageId': uuid4().hex,
                # 'taskId': task_id,
                'contextId': context_id,
            },
        }

        request_2 = SendMessageRequest(
            id=str(uuid4()), params=MessageSendParams(**send_message_payload_2)
        )
        response_2 = await client.send_message(request_2)
        print(response_2.model_dump(mode='json', exclude_none=True))

        # --8<-- [start:send_message_streaming]

        # streaming_request = SendStreamingMessageRequest(
        #     id=str(uuid4()), params=MessageSendParams(**send_message_payload)
        # )

        # stream_response = client.send_message_streaming(streaming_request)

        # async for chunk in stream_response:
        #     print(chunk.model_dump(mode='json', exclude_none=True))
        # --8<-- [end:send_message_streaming]


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())