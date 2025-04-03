"""
Template rendering utility functions.
"""
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def render_template(template_name: str, context: Dict[str, Any]) -> str:
    """
    Render a template with the given context.
    
    Args:
        template_name: Template name
        context: Template context
        
    Returns:
        str: Rendered template
    """
    try:
        # Import Jinja2
        from jinja2 import Environment, FileSystemLoader, select_autoescape
        
        # Get the template directory
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        
        # Create the Jinja2 environment
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Get the template
        template = env.get_template(template_name)
        
        # Render the template
        return template.render(**context)
    
    except ImportError:
        logger.error("Jinja2 is not installed. Please install it with 'pip install jinja2'.")
        raise
    
    except Exception as e:
        logger.error(f"Failed to render template {template_name}: {str(e)}")
        raise
