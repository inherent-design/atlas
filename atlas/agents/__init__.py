"""Agent implementations for Atlas."""

# Define explicit public exports
__all__ = [
    "AtlasAgent",
    "WorkerAgent",
    "RetrievalWorker",
    "AnalysisWorker",
    "DraftWorker",
    "ControllerAgent",
    "AgentRegistry",
    "register_agent",
    "create_agent",
    "get_registered_agents",
    "discover_agents",
]

from atlas.agents.base import AtlasAgent
from atlas.agents.worker import (
    WorkerAgent,
    RetrievalWorker,
    AnalysisWorker,
    DraftWorker,
)
from atlas.agents.controller import ControllerAgent
from atlas.agents.registry import (
    AgentRegistry,
    register_agent,
    create_agent,
    get_registered_agents,
    discover_agents,
)
