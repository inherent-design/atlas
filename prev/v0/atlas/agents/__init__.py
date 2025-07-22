"""Agent implementations for Atlas."""

# Define explicit public exports
__all__ = [
    "AgentRegistry",
    "AnalysisWorker",
    "AtlasAgent",
    "ControllerAgent",
    "DraftWorker",
    "RetrievalWorker",
    "WorkerAgent",
    "create_agent",
    "discover_agents",
    "get_registered_agents",
    "register_agent",
]

from atlas.agents.base import AtlasAgent
from atlas.agents.controller import ControllerAgent
from atlas.agents.registry import (
    AgentRegistry,
    create_agent,
    discover_agents,
    get_registered_agents,
    register_agent,
)
from atlas.agents.worker import (
    AnalysisWorker,
    DraftWorker,
    RetrievalWorker,
    WorkerAgent,
)
