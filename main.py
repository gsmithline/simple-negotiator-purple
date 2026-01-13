"""
Simple Negotiator Purple Agent - A2A Server

A simple aspiration-based negotiation agent for testing the Meta-Game
Negotiation Assessor on AgentBeats.
"""
import argparse
import json
import logging
import os
from typing import Any

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCard,
    AgentCapabilities,
    AgentSkill,
    Part,
    TaskState,
    TextPart,
)
from a2a.utils import new_agent_text_message, new_task
import uvicorn

from negotiator import AspirationNegotiator, handle_negotiation_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simple_negotiator")


class SimpleNegotiatorExecutor(AgentExecutor):
    """Executor for the simple negotiator agent."""

    def __init__(self):
        self.negotiator = AspirationNegotiator(keep_fraction=0.85, accept_slack=0.05)

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Handle incoming negotiation requests."""
        try:
            # Get the message text from context
            message_text = context.get_user_input()
            logger.info(f"Received message: {message_text[:500]}...")

            # Create task and updater
            msg = context.message
            if msg:
                task = new_task(msg)
                await event_queue.enqueue_event(task)
            else:
                # Return simple response without task
                response = handle_negotiation_message(message_text, self.negotiator)
                response_text = json.dumps(response, indent=2)
                logger.info(f"Sending response: {response_text}")
                return

            updater = TaskUpdater(event_queue, task.id, task.context_id)

            # Process the negotiation message
            response = handle_negotiation_message(message_text, self.negotiator)
            response_text = json.dumps(response, indent=2)

            logger.info(f"Sending response: {response_text}")

            # Send the response
            await updater.update_status(
                TaskState.completed,
                new_agent_text_message(response_text, context_id=context.context_id),
            )

        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            error_response = {"error": str(e), "action": "WALK"}
            if 'updater' in locals():
                await updater.update_status(
                    TaskState.completed,
                    new_agent_text_message(json.dumps(error_response), context_id=context.context_id),
                )


def create_agent_card(url: str) -> AgentCard:
    """Create the agent card for the simple negotiator."""
    skill = AgentSkill(
        id="negotiation",
        name="Aspiration-Based Negotiation",
        description=(
            "A simple aspiration-based negotiator that aims to keep approximately "
            "85% of total value while accepting offers that meet BATNA or are within "
            "5% of a reasonable counteroffer."
        ),
        tags=["negotiation", "bargaining", "aspiration", "purple-agent"],
        examples=[
            "Negotiate item allocations in a bargaining game",
            "Accept or reject offers based on BATNA comparison",
        ],
    )

    return AgentCard(
        name="Simple Aspiration Negotiator",
        version="1.0.0",
        description=(
            "A simple purple agent for the Meta-Game Negotiation Assessor. "
            "Uses an aspiration-based strategy to negotiate item allocations "
            "in OpenSpiel bargaining games."
        ),
        url=url,
        preferred_transport="JSONRPC",
        protocol_version="0.3.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[skill],
    )


def main():
    parser = argparse.ArgumentParser(description="Simple Negotiator A2A Agent")
    parser.add_argument("--host", type=str, default=os.environ.get("HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("AGENT_PORT", os.environ.get("PORT", "8080"))))
    parser.add_argument("--card-url", type=str, default=None)
    args = parser.parse_args()

    host = args.host
    port = args.port
    base_url = args.card_url or os.environ.get("AGENT_URL", f"http://{host}:{port}/")

    logger.info(f"Starting Simple Negotiator on {host}:{port}")
    logger.info(f"Agent URL: {base_url}")

    executor = SimpleNegotiatorExecutor()
    agent_card = create_agent_card(base_url)

    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    uvicorn_config = uvicorn.Config(
        server.build(),
        host=host,
        port=port,
        log_level="info",
    )
    uvicorn_server = uvicorn.Server(uvicorn_config)
    uvicorn_server.run()


if __name__ == "__main__":
    main()
