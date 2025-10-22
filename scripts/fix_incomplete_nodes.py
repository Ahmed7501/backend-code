"""
Migration script to fix incomplete flow nodes in the database.
Run this once before deploying the strict validation changes.

Usage:
    python scripts/fix_incomplete_nodes.py

This script will:
1. Query all flows from database
2. Identify nodes with missing type, config, or required fields
3. Log all problematic nodes with details
4. Provide safe default values or mark for manual review
5. Update database with fixes
6. Generate report of changes
"""

import logging
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from src.shared.database import SessionLocal
from src.shared.models.bot_builder import BotFlow
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('node_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def fix_incomplete_nodes():
    """Fix nodes missing required fields."""
    db = SessionLocal()
    
    try:
        flows = db.query(BotFlow).all()
        fixed_count = 0
        error_count = 0
        flows_modified = 0
        
        logger.info(f"Starting migration for {len(flows)} flows")
        
        for flow in flows:
            if not flow.structure:
                logger.warning(f"Flow {flow.id}: Empty structure, skipping")
                continue
            
            modified = False
            flow_errors = []
            
            for idx, node in enumerate(flow.structure):
                node_fixes = []
                
                # Check and fix missing type
                if "type" not in node or not node.get("type"):
                    logger.warning(f"Flow {flow.id}, Node {idx}: Missing type, setting to 'send_message'")
                    node["type"] = "send_message"
                    node_fixes.append("added_type")
                    modified = True
                    fixed_count += 1
                
                # Check and fix missing config
                if "config" not in node or not node.get("config"):
                    logger.error(f"Flow {flow.id}, Node {idx}: Missing config - MANUAL REVIEW NEEDED")
                    flow_errors.append(f"Node {idx}: Missing config field")
                    error_count += 1
                    continue
                
                # Validate config based on type
                config = node["config"]
                node_type = node["type"]
                
                # Type-specific validation and fixes
                if node_type == "send_message":
                    if "message_type" not in config:
                        logger.warning(f"Flow {flow.id}, Node {idx}: Missing message_type, setting to 'text'")
                        config["message_type"] = "text"
                        node_fixes.append("added_message_type")
                        modified = True
                        fixed_count += 1
                    
                    if "content" not in config or not config.get("content"):
                        logger.warning(f"Flow {flow.id}, Node {idx}: Missing content, setting default")
                        config["content"] = {"text": ""}
                        node_fixes.append("added_content")
                        modified = True
                        fixed_count += 1
                    
                    if "next" not in config:
                        logger.warning(f"Flow {flow.id}, Node {idx}: Missing next, setting to None")
                        config["next"] = None
                        node_fixes.append("added_next")
                        modified = True
                        fixed_count += 1
                
                elif node_type == "wait":
                    if "duration" not in config:
                        logger.warning(f"Flow {flow.id}, Node {idx}: Missing duration, setting to 1")
                        config["duration"] = 1
                        node_fixes.append("added_duration")
                        modified = True
                        fixed_count += 1
                    
                    if "unit" not in config:
                        logger.warning(f"Flow {flow.id}, Node {idx}: Missing unit, setting to 'seconds'")
                        config["unit"] = "seconds"
                        node_fixes.append("added_unit")
                        modified = True
                        fixed_count += 1
                    
                    if "next" not in config:
                        logger.warning(f"Flow {flow.id}, Node {idx}: Missing next, setting to None")
                        config["next"] = None
                        node_fixes.append("added_next")
                        modified = True
                        fixed_count += 1
                
                elif node_type == "condition":
                    if "variable" not in config:
                        logger.error(f"Flow {flow.id}, Node {idx}: Missing variable - MANUAL REVIEW NEEDED")
                        flow_errors.append(f"Node {idx}: Missing variable field")
                        error_count += 1
                        continue
                    
                    if "operator" not in config:
                        logger.warning(f"Flow {flow.id}, Node {idx}: Missing operator, setting to '=='")
                        config["operator"] = "=="
                        node_fixes.append("added_operator")
                        modified = True
                        fixed_count += 1
                    
                    if "value" not in config:
                        logger.warning(f"Flow {flow.id}, Node {idx}: Missing value, setting to empty string")
                        config["value"] = ""
                        node_fixes.append("added_value")
                        modified = True
                        fixed_count += 1
                    
                    if "true_path" not in config:
                        logger.warning(f"Flow {flow.id}, Node {idx}: Missing true_path, setting to None")
                        config["true_path"] = None
                        node_fixes.append("added_true_path")
                        modified = True
                        fixed_count += 1
                    
                    if "false_path" not in config:
                        logger.warning(f"Flow {flow.id}, Node {idx}: Missing false_path, setting to None")
                        config["false_path"] = None
                        node_fixes.append("added_false_path")
                        modified = True
                        fixed_count += 1
                
                elif node_type == "webhook_action":
                    if "url" not in config:
                        logger.error(f"Flow {flow.id}, Node {idx}: Missing url - MANUAL REVIEW NEEDED")
                        flow_errors.append(f"Node {idx}: Missing url field")
                        error_count += 1
                        continue
                    
                    if "method" not in config:
                        logger.warning(f"Flow {flow.id}, Node {idx}: Missing method, setting to 'POST'")
                        config["method"] = "POST"
                        node_fixes.append("added_method")
                        modified = True
                        fixed_count += 1
                    
                    if "next" not in config:
                        logger.warning(f"Flow {flow.id}, Node {idx}: Missing next, setting to None")
                        config["next"] = None
                        node_fixes.append("added_next")
                        modified = True
                        fixed_count += 1
                
                elif node_type == "set_attribute":
                    if "attribute_key" not in config:
                        logger.error(f"Flow {flow.id}, Node {idx}: Missing attribute_key - MANUAL REVIEW NEEDED")
                        flow_errors.append(f"Node {idx}: Missing attribute_key field")
                        error_count += 1
                        continue
                    
                    if "attribute_value" not in config:
                        logger.warning(f"Flow {flow.id}, Node {idx}: Missing attribute_value, setting to empty string")
                        config["attribute_value"] = ""
                        node_fixes.append("added_attribute_value")
                        modified = True
                        fixed_count += 1
                    
                    if "next" not in config:
                        logger.warning(f"Flow {flow.id}, Node {idx}: Missing next, setting to None")
                        config["next"] = None
                        node_fixes.append("added_next")
                        modified = True
                        fixed_count += 1
                
                if node_fixes:
                    logger.info(f"Flow {flow.id}, Node {idx}: Applied fixes: {', '.join(node_fixes)}")
            
            if flow_errors:
                logger.error(f"Flow {flow.id}: Errors requiring manual review: {flow_errors}")
            
            if modified:
                db.commit()
                flows_modified += 1
                logger.info(f"Flow {flow.id}: Updated with fixes")
        
        logger.info(f"Migration complete:")
        logger.info(f"  - {fixed_count} fixes applied")
        logger.info(f"  - {error_count} errors need manual review")
        logger.info(f"  - {flows_modified} flows modified")
        
        # Generate summary report
        report = {
            "total_flows": len(flows),
            "flows_modified": flows_modified,
            "total_fixes": fixed_count,
            "errors_requiring_review": error_count,
            "status": "completed"
        }
        
        with open("migration_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info("Migration report saved to migration_report.json")
    
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        db.rollback()
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    try:
        fix_incomplete_nodes()
        logger.info("Migration completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        sys.exit(1)
