"""
Flow builder helper utilities for validation and testing.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class FlowValidationError(Exception):
    """Exception raised when flow validation fails."""
    pass


class FlowValidator:
    """Validator for flow structures."""
    
    SUPPORTED_NODE_TYPES = {"send_message", "wait", "condition", "webhook_action", "set_attribute"}
    SUPPORTED_MESSAGE_TYPES = {"text", "template", "media", "interactive"}
    SUPPORTED_CONDITION_OPERATORS = {"==", "!=", ">", "<", ">=", "<=", "contains", "starts_with", "ends_with"}
    SUPPORTED_WAIT_UNITS = {"seconds", "minutes", "hours", "days"}
    SUPPORTED_HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH"}
    
    @classmethod
    def validate_flow_structure(cls, flow_structure: List[Dict[str, Any]]) -> List[str]:
        """Validate flow structure and return list of errors."""
        errors = []
        
        if not flow_structure:
            errors.append("Flow structure cannot be empty")
            return errors
        
        # Check for circular dependencies
        circular_errors = cls._check_circular_dependencies(flow_structure)
        errors.extend(circular_errors)
        
        # Validate each node
        for i, node in enumerate(flow_structure):
            node_errors = cls._validate_node(node, i)
            errors.extend(node_errors)
        
        return errors
    
    @classmethod
    def _check_circular_dependencies(cls, flow_structure: List[Dict[str, Any]]) -> List[str]:
        """Check for circular dependencies in flow structure."""
        errors = []
        visited = set()
        recursion_stack = set()
        
        def dfs(node_index: int):
            if node_index in recursion_stack:
                errors.append(f"Circular dependency detected involving node {node_index}")
                return
            if node_index in visited:
                return
            
            visited.add(node_index)
            recursion_stack.add(node_index)
            
            if node_index < len(flow_structure):
                node = flow_structure[node_index]
                next_nodes = cls._get_next_nodes(node)
                for next_node in next_nodes:
                    if next_node is not None:
                        dfs(next_node)
            
            recursion_stack.remove(node_index)
        
        # Start DFS from each unvisited node
        for i in range(len(flow_structure)):
            if i not in visited:
                dfs(i)
        
        return errors
    
    @classmethod
    def _get_next_nodes(cls, node: Dict[str, Any]) -> List[Optional[int]]:
        """Get next node indices from a node."""
        next_nodes = []
        
        # Direct next node
        if "next" in node:
            next_nodes.append(node["next"])
        
        # Condition node paths
        if node.get("type") == "condition" and "config" in node:
            config = node["config"]
            if "true_path" in config:
                next_nodes.append(config["true_path"])
            if "false_path" in config:
                next_nodes.append(config["false_path"])
        
        return next_nodes
    
    @classmethod
    def _validate_node(cls, node: Dict[str, Any], node_index: int) -> List[str]:
        """Validate a single node."""
        errors = []
        
        # Strict validation - no auto-fixing
        if "type" not in node or not node.get("type"):
            errors.append(f"Node {node_index}: Missing required 'type' field")
            return errors
        
        node_type = node["type"]
        if node_type not in cls.SUPPORTED_NODE_TYPES:
            errors.append(f"Node {node_index}: Unsupported node type '{node_type}'")
            return errors
        
        # Check config field
        if "config" not in node:
            errors.append(f"Node {node_index}: Missing 'config' field")
            return errors
        
        config = node["config"]
        
        # Validate based on node type
        if node_type == "send_message":
            errors.extend(cls._validate_send_message_node(config, node_index))
        elif node_type == "wait":
            errors.extend(cls._validate_wait_node(config, node_index))
        elif node_type == "condition":
            errors.extend(cls._validate_condition_node(config, node_index))
        elif node_type == "webhook_action":
            errors.extend(cls._validate_webhook_action_node(config, node_index))
        elif node_type == "set_attribute":
            errors.extend(cls._validate_set_attribute_node(config, node_index))
        
        return errors
    
    @classmethod
    def _validate_send_message_node(cls, config: Dict[str, Any], node_index: int) -> List[str]:
        """Validate send_message node configuration."""
        errors = []
        
        if "message_type" not in config:
            errors.append(f"Node {node_index}: Missing 'message_type' in config")
        elif config["message_type"] not in cls.SUPPORTED_MESSAGE_TYPES:
            errors.append(f"Node {node_index}: Unsupported message type '{config['message_type']}'")
        
        if "content" not in config:
            errors.append(f"Node {node_index}: Missing 'content' in config")
        
        if "next" not in config:
            errors.append(f"Node {node_index}: Missing 'next' field in config")
        
        return errors
    
    @classmethod
    def _validate_wait_node(cls, config: Dict[str, Any], node_index: int) -> List[str]:
        """Validate wait node configuration."""
        errors = []
        
        if "duration" not in config:
            errors.append(f"Node {node_index}: Missing 'duration' in config")
        elif not isinstance(config["duration"], (int, float)) or config["duration"] <= 0:
            errors.append(f"Node {node_index}: 'duration' must be a positive number")
        
        if "unit" not in config:
            errors.append(f"Node {node_index}: Missing 'unit' in config")
        elif config["unit"] not in cls.SUPPORTED_WAIT_UNITS:
            errors.append(f"Node {node_index}: Unsupported wait unit '{config['unit']}'")
        
        if "next" not in config:
            errors.append(f"Node {node_index}: Missing 'next' field in config")
        
        return errors
    
    @classmethod
    def _validate_condition_node(cls, config: Dict[str, Any], node_index: int) -> List[str]:
        """Validate condition node configuration."""
        errors = []
        
        if "variable" not in config:
            errors.append(f"Node {node_index}: Missing 'variable' in config")
        
        if "operator" not in config:
            errors.append(f"Node {node_index}: Missing 'operator' in config")
        elif config["operator"] not in cls.SUPPORTED_CONDITION_OPERATORS:
            errors.append(f"Node {node_index}: Unsupported operator '{config['operator']}'")
        
        if "value" not in config:
            errors.append(f"Node {node_index}: Missing 'value' in config")
        
        if "true_path" not in config:
            errors.append(f"Node {node_index}: Missing 'true_path' in config")
        
        if "false_path" not in config:
            errors.append(f"Node {node_index}: Missing 'false_path' in config")
        
        return errors
    
    @classmethod
    def _validate_webhook_action_node(cls, config: Dict[str, Any], node_index: int) -> List[str]:
        """Validate webhook_action node configuration."""
        errors = []
        
        if "url" not in config:
            errors.append(f"Node {node_index}: Missing 'url' in config")
        elif not isinstance(config["url"], str) or not config["url"].startswith(("http://", "https://")):
            errors.append(f"Node {node_index}: 'url' must be a valid HTTP/HTTPS URL")
        
        if "method" not in config:
            errors.append(f"Node {node_index}: Missing 'method' in config")
        elif config["method"] not in cls.SUPPORTED_HTTP_METHODS:
            errors.append(f"Node {node_index}: Unsupported HTTP method '{config['method']}'")
        
        if "next" not in config:
            errors.append(f"Node {node_index}: Missing 'next' field in config")
        
        return errors

    @classmethod
    def _validate_set_attribute_node(cls, config: Dict[str, Any], node_index: int) -> List[str]:
        """Validate set_attribute node configuration."""
        errors = []
        
        if "attribute_key" not in config:
            errors.append(f"Node {node_index}: Missing 'attribute_key' in config")
        elif not isinstance(config["attribute_key"], str) or not config["attribute_key"].strip():
            errors.append(f"Node {node_index}: 'attribute_key' must be a non-empty string")
        
        if "attribute_value" not in config:
            errors.append(f"Node {node_index}: Missing 'attribute_value' in config")
        elif not isinstance(config["attribute_value"], str):
            errors.append(f"Node {node_index}: 'attribute_value' must be a string")
        
        if "value_type" in config:
            supported_types = {"string", "number", "boolean", "json"}
            if config["value_type"] not in supported_types:
                errors.append(f"Node {node_index}: Unsupported value_type '{config['value_type']}'. Must be one of: {supported_types}")
        
        if "next" not in config:
            errors.append(f"Node {node_index}: Missing 'next' field in config")
        elif not isinstance(config["next"], int) or config["next"] < 0:
            errors.append(f"Node {node_index}: 'next' must be a non-negative integer")
        
        return errors


class FlowTester:
    """Flow testing utilities."""
    
    @classmethod
    def create_test_flow(cls) -> List[Dict[str, Any]]:
        """Create a simple test flow for validation."""
        return [
            {
                "type": "send_message",
                "config": {
                    "message_type": "text",
                    "content": {"text": "Hello! Welcome to our bot."},
                    "next": 1
                }
            },
            {
                "type": "wait",
                "config": {
                    "duration": 5,
                    "unit": "seconds",
                    "next": 2
                }
            },
            {
                "type": "condition",
                "config": {
                    "variable": "state.user_response",
                    "operator": "==",
                    "value": "yes",
                    "true_path": 3,
                    "false_path": 4
                }
            },
            {
                "type": "send_message",
                "config": {
                    "message_type": "text",
                    "content": {"text": "Great! You said yes."},
                    "next": None
                }
            },
            {
                "type": "send_message",
                "config": {
                    "message_type": "text",
                    "content": {"text": "You said no. That's okay too!"},
                    "next": None
                }
            }
        ]
    
    @classmethod
    def validate_test_flow(cls) -> List[str]:
        """Validate the test flow."""
        test_flow = cls.create_test_flow()
        return FlowValidator.validate_flow_structure(test_flow)


class FlowAnalyzer:
    """Flow analysis utilities."""
    
    @classmethod
    def analyze_flow_complexity(cls, flow_structure: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze flow complexity metrics."""
        total_nodes = len(flow_structure)
        node_types = {}
        condition_nodes = 0
        wait_nodes = 0
        max_depth = 0
        
        for node in flow_structure:
            node_type = node.get("type", "unknown")
            node_types[node_type] = node_types.get(node_type, 0) + 1
            
            if node_type == "condition":
                condition_nodes += 1
            elif node_type == "wait":
                wait_nodes += 1
        
        # Calculate maximum depth (simplified)
        max_depth = cls._calculate_max_depth(flow_structure)
        
        return {
            "total_nodes": total_nodes,
            "node_types": node_types,
            "condition_nodes": condition_nodes,
            "wait_nodes": wait_nodes,
            "max_depth": max_depth,
            "complexity_score": cls._calculate_complexity_score(
                total_nodes, condition_nodes, wait_nodes, max_depth
            )
        }
    
    @classmethod
    def _calculate_max_depth(cls, flow_structure: List[Dict[str, Any]]) -> int:
        """Calculate maximum depth of the flow."""
        if not flow_structure:
            return 0
        
        visited = set()
        
        def dfs(node_index: int, depth: int) -> int:
            if node_index in visited or node_index >= len(flow_structure):
                return depth
            
            visited.add(node_index)
            max_depth = depth
            
            node = flow_structure[node_index]
            next_nodes = FlowValidator._get_next_nodes(node)
            
            for next_node in next_nodes:
                if next_node is not None:
                    max_depth = max(max_depth, dfs(next_node, depth + 1))
            
            return max_depth
        
        return dfs(0, 1)
    
    @classmethod
    def _calculate_complexity_score(
        cls,
        total_nodes: int,
        condition_nodes: int,
        wait_nodes: int,
        max_depth: int
    ) -> float:
        """Calculate a complexity score for the flow."""
        # Simple complexity scoring algorithm
        base_score = total_nodes * 1.0
        condition_penalty = condition_nodes * 2.0  # Conditions add complexity
        wait_penalty = wait_nodes * 1.5  # Waits add temporal complexity
        depth_penalty = max_depth * 0.5  # Depth adds nesting complexity
        
        return base_score + condition_penalty + wait_penalty + depth_penalty
