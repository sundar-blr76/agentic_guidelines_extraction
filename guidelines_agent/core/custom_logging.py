import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.outputs import LLMResult

logger = logging.getLogger(__name__)

class ISTFormatter(logging.Formatter):
    """A custom logging formatter to display timestamps in IST."""
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, ZoneInfo("Asia/Kolkata"))
        if datefmt:
            s = dt.strftime(datefmt)
        else:
            s = dt.strftime('%Y-%m-%d %H:%M:%S,%f')[:-3] + " " + dt.tzname()
        return s

class CustomCallbackHandler(BaseCallbackHandler):
    """A custom callback handler to log AgentExecutor steps."""

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        logger.info(f"LLM Start: Prompts: {prompts}")

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        logger.info(f"LLM End: Response: {response.generations}")

    def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        logger.error(f"LLM Error: {error}", exc_info=True)

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        logger.info(f"Chain Start: Inputs: {inputs}")

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        logger.info(f"Chain End: Outputs: {outputs}")

    def on_chain_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        logger.error(f"Chain Error: {error}", exc_info=True)

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        logger.info(f"Tool Start: Input: {input_str}")

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        logger.info(f"Tool End: Output: {output}")

    def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        logger.error(f"Tool Error: {error}", exc_info=True)

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        logger.info(f"Agent Action: Tool={action.tool}, Input={action.tool_input}")

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        logger.info(f"Agent Finish: Output={finish.return_values}")
