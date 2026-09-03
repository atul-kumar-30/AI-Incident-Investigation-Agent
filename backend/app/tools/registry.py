from typing import Dict, Optional
from app.tools.base import BaseTool

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def get_all_tools(self) -> Dict[str, BaseTool]:
        return self._tools

registry = ToolRegistry()

# Register default tools
from app.tools.incident_context import IncidentContextAnalyzer
from app.agents.investigation.tools.log_search import LogSearchTool
from app.agents.investigation.tools.code_search import CodeSearchTool
from app.agents.investigation.tools.recent_changes import RecentChangesTool
from app.agents.investigation.tools.docs_search import DocsSearchTool

registry.register(IncidentContextAnalyzer())
registry.register(LogSearchTool())
registry.register(CodeSearchTool())
registry.register(RecentChangesTool())
registry.register(DocsSearchTool())
