"""
Template rendering for PythonWeb Installer.

This module provides high-level functions for template rendering and management.
"""
import os
import logging
from typing import Dict, Any, List, Tuple, Optional

from pythonweb_installer.templates.engine import (
    TemplateEngine,
    render_template_file,
    render_template_directory
)
from pythonweb_installer.templates.management import (
    discover_templates,
    validate_template,
    validate_template_directory,
    create_template_context,
    save_template_context,
    customize_template
)

logger = logging.getLogger(__name__)


def render_template(template_path: str, context: Dict[str, Any]) -> str:
    """
    Render a template with the given context.

    Args:
        template_path: Path to the template file
        context: Dictionary of variables to pass to the template

    Returns:
        str: Rendered template content
    """
    logger.info(f"Rendering template: {template_path}")

    # Check if the template file exists
    if not os.path.exists(template_path):
        logger.error(f"Template file not found: {template_path}")
        raise FileNotFoundError(f"Template file not found: {template_path}")

    # Create a template engine with the template directory
    template_dir = os.path.dirname(template_path)
    template_name = os.path.basename(template_path)
    engine = TemplateEngine(template_dir)

    # Render the template
    return engine.render_template(template_name, context)


def render_template_to_file(template_path: str, output_path: str, context: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Render a template to an output file.

    Args:
        template_path: Path to the template file
        output_path: Path to the output file
        context: Dictionary of variables to pass to the template

    Returns:
        Tuple[bool, str]: Success status and message
    """
    return render_template_file(template_path, output_path, context)


def render_directory(template_dir: str, output_dir: str, context: Dict[str, Any], exclude_patterns: Optional[List[str]] = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Render all templates in a directory to an output directory.

    Args:
        template_dir: Path to the template directory
        output_dir: Path to the output directory
        context: Dictionary of variables to pass to the templates
        exclude_patterns: List of glob patterns to exclude

    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and results
    """
    return render_template_directory(template_dir, output_dir, context, exclude_patterns)


def find_templates(base_dir: str, pattern: str = "*.tmpl", recursive: bool = True) -> List[str]:
    """
    Find template files in a directory.

    Args:
        base_dir: Base directory to search
        pattern: Glob pattern to match template files
        recursive: Whether to search recursively

    Returns:
        List[str]: List of discovered template paths
    """
    return discover_templates(base_dir, pattern, recursive)


def validate_templates(template_dir: str, required_variables: Optional[List[str]] = None, pattern: str = "*.tmpl") -> Tuple[bool, Dict[str, Any]]:
    """
    Validate all templates in a directory.

    Args:
        template_dir: Path to the template directory
        required_variables: List of variables that must be present in all templates
        pattern: Glob pattern to match template files

    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and validation results
    """
    return validate_template_directory(template_dir, required_variables, pattern)


def load_context(context_file: Optional[str] = None, additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Load a template context from a file and/or additional context.

    Args:
        context_file: Path to a JSON context file
        additional_context: Additional context variables

    Returns:
        Dict[str, Any]: Combined template context
    """
    return create_template_context(context_file, additional_context)


def save_context(context: Dict[str, Any], output_file: str, overwrite: bool = False) -> Tuple[bool, str]:
    """
    Save a template context to a JSON file.

    Args:
        context: Template context to save
        output_file: Path to the output file
        overwrite: Whether to overwrite an existing file

    Returns:
        Tuple[bool, str]: Success status and message
    """
    return save_template_context(context, output_file, overwrite)


def customize_template_file(template_path: str, output_path: str, context: Dict[str, Any], overwrite: bool = False) -> Tuple[bool, str]:
    """
    Customize a template with the given context and save it to a new file.

    Args:
        template_path: Path to the template file
        output_path: Path to the output file
        context: Dictionary of variables to use in rendering
        overwrite: Whether to overwrite an existing file

    Returns:
        Tuple[bool, str]: Success status and message
    """
    return customize_template(template_path, output_path, context, overwrite)


def validate_template_file(template_path: str, required_variables: Optional[List[str]] = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate a template file.

    Args:
        template_path: Path to the template file
        required_variables: List of variables that must be present in the template

    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and validation results
    """
    return validate_template(template_path, required_variables)
