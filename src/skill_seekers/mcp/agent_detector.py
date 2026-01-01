"""
AI Coding Agent Detection and Configuration Module

This module provides functionality to detect installed AI coding agents
and generate appropriate MCP server configurations for each agent.

Supported agents:
- Claude Code (stdio)
- Cursor (HTTP)
- Windsurf (HTTP)
- VS Code + Cline extension (stdio)
- IntelliJ IDEA (HTTP)
"""

import json
import os
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


class AgentDetector:
    """Detects installed AI coding agents and generates their MCP configurations."""

    # Agent configuration templates
    AGENT_CONFIG = {
        "claude-code": {
            "name": "Claude Code",
            "transport": "stdio",
            "config_paths": {
                "Linux": "~/.config/claude-code/mcp.json",
                "Darwin": "~/Library/Application Support/Claude/mcp.json",
                "Windows": "~\\AppData\\Roaming\\Claude\\mcp.json"
            }
        },
        "cursor": {
            "name": "Cursor",
            "transport": "http",
            "config_paths": {
                "Linux": "~/.cursor/mcp_settings.json",
                "Darwin": "~/Library/Application Support/Cursor/mcp_settings.json",
                "Windows": "~\\AppData\\Roaming\\Cursor\\mcp_settings.json"
            }
        },
        "windsurf": {
            "name": "Windsurf",
            "transport": "http",
            "config_paths": {
                "Linux": "~/.windsurf/mcp_config.json",
                "Darwin": "~/Library/Application Support/Windsurf/mcp_config.json",
                "Windows": "~\\AppData\\Roaming\\Windsurf\\mcp_config.json"
            }
        },
        "vscode-cline": {
            "name": "VS Code + Cline",
            "transport": "stdio",
            "config_paths": {
                "Linux": "~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json",
                "Darwin": "~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json",
                "Windows": "~\\AppData\\Roaming\\Code\\User\\globalStorage\\saoudrizwan.claude-dev\\settings\\cline_mcp_settings.json"
            }
        },
        "intellij": {
            "name": "IntelliJ IDEA",
            "transport": "http",
            "config_paths": {
                "Linux": "~/.config/JetBrains/IntelliJIdea2024.3/mcp.xml",
                "Darwin": "~/Library/Application Support/JetBrains/IntelliJIdea2024.3/mcp.xml",
                "Windows": "~\\AppData\\Roaming\\JetBrains\\IntelliJIdea2024.3\\mcp.xml"
            }
        }
    }

    def __init__(self):
        """Initialize the agent detector."""
        self.system = platform.system()

    def detect_agents(self) -> List[Dict[str, str]]:
        """
        Detect installed AI coding agents on the system.

        Returns:
            List of detected agents with their config paths.
            Each dict contains: {'agent': str, 'name': str, 'config_path': str, 'transport': str}
        """
        detected = []

        for agent_id, config in self.AGENT_CONFIG.items():
            config_path = self._get_config_path(agent_id)
            if config_path:
                detected.append({
                    "agent": agent_id,
                    "name": config["name"],
                    "config_path": config_path,
                    "transport": config["transport"]
                })

        return detected

    def _get_config_path(self, agent_id: str) -> Optional[str]:
        """
        Get the configuration path for a specific agent.

        Args:
            agent_id: Agent identifier (e.g., 'claude-code', 'cursor')

        Returns:
            Expanded config path if the parent directory exists, None otherwise
        """
        if agent_id not in self.AGENT_CONFIG:
            return None

        config_paths = self.AGENT_CONFIG[agent_id]["config_paths"]
        if self.system not in config_paths:
            return None

        path = Path(config_paths[self.system]).expanduser()

        # Check if parent directory exists (agent is likely installed)
        parent = path.parent
        if parent.exists():
            return str(path)

        return None

    def get_transport_type(self, agent_id: str) -> Optional[str]:
        """
        Get the transport type for a specific agent.

        Args:
            agent_id: Agent identifier

        Returns:
            'stdio' or 'http', or None if agent not found
        """
        if agent_id not in self.AGENT_CONFIG:
            return None
        return self.AGENT_CONFIG[agent_id]["transport"]

    def generate_config(
        self,
        agent_id: str,
        server_command: str,
        http_port: Optional[int] = 3000
    ) -> Optional[str]:
        """
        Generate MCP configuration for a specific agent.

        Args:
            agent_id: Agent identifier
            server_command: Command to start the MCP server (e.g., 'skill-seekers mcp')
            http_port: Port for HTTP transport (default: 3000)

        Returns:
            Configuration string (JSON or XML) or None if agent not found
        """
        if agent_id not in self.AGENT_CONFIG:
            return None

        transport = self.AGENT_CONFIG[agent_id]["transport"]

        if agent_id == "intellij":
            return self._generate_intellij_config(server_command, http_port)
        elif transport == "stdio":
            return self._generate_stdio_config(server_command)
        else:  # http
            return self._generate_http_config(http_port)

    def _generate_stdio_config(self, server_command: str) -> str:
        """
        Generate stdio-based MCP configuration (JSON format).

        Args:
            server_command: Command to start the MCP server

        Returns:
            JSON configuration string
        """
        # Split command into program and args
        parts = server_command.split()
        command = parts[0] if parts else "skill-seekers"
        args = parts[1:] if len(parts) > 1 else ["mcp"]

        config = {
            "mcpServers": {
                "skill-seeker": {
                    "command": command,
                    "args": args
                }
            }
        }

        return json.dumps(config, indent=2)

    def _generate_http_config(self, http_port: int) -> str:
        """
        Generate HTTP-based MCP configuration (JSON format).

        Args:
            http_port: Port number for HTTP server

        Returns:
            JSON configuration string
        """
        config = {
            "mcpServers": {
                "skill-seeker": {
                    "url": f"http://localhost:{http_port}"
                }
            }
        }

        return json.dumps(config, indent=2)

    def _generate_intellij_config(self, server_command: str, http_port: int) -> str:
        """
        Generate IntelliJ IDEA MCP configuration (XML format).

        Args:
            server_command: Command to start the MCP server
            http_port: Port number for HTTP server

        Returns:
            XML configuration string
        """
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<application>
  <component name="MCPSettings">
    <servers>
      <server>
        <name>skill-seeker</name>
        <url>http://localhost:{http_port}</url>
        <enabled>true</enabled>
      </server>
    </servers>
  </component>
</application>"""
        return xml

    def get_all_config_paths(self) -> Dict[str, str]:
        """
        Get all possible configuration paths for the current system.

        Returns:
            Dict mapping agent_id to config_path
        """
        paths = {}
        for agent_id in self.AGENT_CONFIG:
            path = self._get_config_path(agent_id)
            if path:
                paths[agent_id] = path
        return paths

    def is_agent_installed(self, agent_id: str) -> bool:
        """
        Check if a specific agent is installed.

        Args:
            agent_id: Agent identifier

        Returns:
            True if agent appears to be installed, False otherwise
        """
        return self._get_config_path(agent_id) is not None

    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Dict with agent details or None if not found
        """
        if agent_id not in self.AGENT_CONFIG:
            return None

        config = self.AGENT_CONFIG[agent_id]
        config_path = self._get_config_path(agent_id)

        return {
            "agent": agent_id,
            "name": config["name"],
            "transport": config["transport"],
            "config_path": config_path,
            "installed": config_path is not None
        }


def detect_agents() -> List[Dict[str, str]]:
    """
    Convenience function to detect installed agents.

    Returns:
        List of detected agents
    """
    detector = AgentDetector()
    return detector.detect_agents()


def generate_config(
    agent_name: str,
    server_command: str = "skill-seekers mcp",
    http_port: int = 3000
) -> Optional[str]:
    """
    Convenience function to generate config for a specific agent.

    Args:
        agent_name: Agent identifier
        server_command: Command to start the MCP server
        http_port: Port for HTTP transport

    Returns:
        Configuration string or None
    """
    detector = AgentDetector()
    return detector.generate_config(agent_name, server_command, http_port)


def get_transport_type(agent_name: str) -> Optional[str]:
    """
    Convenience function to get transport type for an agent.

    Args:
        agent_name: Agent identifier

    Returns:
        'stdio' or 'http', or None
    """
    detector = AgentDetector()
    return detector.get_transport_type(agent_name)
