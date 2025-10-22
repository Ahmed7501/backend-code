"""
Flow structure normalization utilities.
Ensures legacy flow data has required fields before validation.
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class FlowNormalizer:
    """Normalizes flow structures to ensure required fields exist."""
    
    @classmethod
    def normalize_flow_structure(cls, flow_structure: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize a flow structure by ensuring all nodes have required fields.
        This is for backward compatibility with legacy data.
        """
        if not flow_structure:
            return flow_structure
        
        normalized = []
        for idx, node in enumerate(flow_structure):
            normalized_node = cls._normalize_node(node, idx)
            normalized.append(normalized_node)
        
        return normalized
    
    @classmethod
    def _normalize_node(cls, node: Dict[str, Any], node_index: int) -> Dict[str, Any]:
        """Normalize a single node by adding missing required fields."""
        normalized = node.copy()
        
        # Ensure 'type' field exists
        if "type" not in normalized or not normalized.get("type"):
            logger.warning(f"Node {node_index}: Missing 'type', defaulting to 'send_message'")
            normalized["type"] = "send_message"
        
        # Ensure 'config' field exists
        if "config" not in normalized:
            logger.warning(f"Node {node_index}: Missing 'config', adding empty dict")
            normalized["config"] = {}
        
        # Normalize config based on node type
        node_type = normalized["type"]
        config = normalized["config"]
        
        if node_type == "send_message":
            if "message_type" not in config:
                config["message_type"] = "text"
            if "content" not in config:
                config["content"] = {"text": ""}
            if "next" not in config:
                config["next"] = None
        
        elif node_type == "wait":
            if "duration" not in config:
                config["duration"] = 1
            if "unit" not in config:
                config["unit"] = "seconds"
            if "next" not in config:
                config["next"] = None
        
        elif node_type == "condition":
            if "variable" not in config:
                config["variable"] = "state.variable"
            if "operator" not in config:
                config["operator"] = "=="
            if "value" not in config:
                config["value"] = ""
            if "true_path" not in config:
                config["true_path"] = None
            if "false_path" not in config:
                config["false_path"] = None
        
        elif node_type == "webhook_action":
            if "url" not in config:
                config["url"] = "https://example.com/webhook"
            if "method" not in config:
                config["method"] = "POST"
            if "next" not in config:
                config["next"] = None
        
        elif node_type == "set_attribute":
            if "attribute_key" not in config:
                config["attribute_key"] = "default_key"
            if "attribute_value" not in config:
                config["attribute_value"] = ""
            if "next" not in config:
                config["next"] = None
        
        return normalized
