"""
Template management functionality.
"""
import os
import re
import json
import logging
import shutil
import fnmatch
from typing import Dict, Any, List, Tuple, Optional, Set, Union

from pythonweb_installer.templates.engine import TemplateEngine

logger = logging.getLogger(__name__)


def discover_templates(
    base_dir: str,
    pattern: str = "*.tmpl",
    recursive: bool = True
) -> List[str]:
    """
    Discover template files in a directory.
    
    Args:
        base_dir: Base directory to search
        pattern: Glob pattern to match template files
        recursive: Whether to search recursively
        
    Returns:
        List[str]: List of discovered template paths
    """
    logger.info(f"Discovering templates in {base_dir} with pattern {pattern}")
    
    if not os.path.exists(base_dir):
        logger.error(f"Base directory not found: {base_dir}")
        return []
    
    templates = []
    
    if recursive:
        # Walk through the directory tree
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if fnmatch.fnmatch(file, pattern):
                    template_path = os.path.join(root, file)
                    templates.append(template_path)
    else:
        # Search only in the base directory
        for file in os.listdir(base_dir):
            file_path = os.path.join(base_dir, file)
            if os.path.isfile(file_path) and fnmatch.fnmatch(file, pattern):
                templates.append(file_path)
    
    logger.info(f"Discovered {len(templates)} templates")
    return templates


def validate_template(
    template_path: str,
    required_variables: Optional[List[str]] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate a template file.
    
    Args:
        template_path: Path to the template file
        required_variables: List of variables that must be present in the template
        
    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and validation results
    """
    logger.info(f"Validating template: {template_path}")
    
    if not os.path.exists(template_path):
        logger.error(f"Template file not found: {template_path}")
        return False, {"error": f"Template file not found: {template_path}"}
    
    try:
        # Read the template content
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Initialize results
        results = {
            "valid": True,
            "path": template_path,
            "variables": [],
            "conditionals": [],
            "loops": [],
            "includes": [],
            "missing_variables": []
        }
        
        # Find all variables
        var_pattern = r'\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}'
        variables = set(re.findall(var_pattern, template_content))
        results["variables"] = list(variables)
        
        # Find all conditionals
        if_pattern = r'\{\%\s*if\s+([a-zA-Z0-9_.-]+)\s*\%\}'
        conditionals = set(re.findall(if_pattern, template_content))
        results["conditionals"] = list(conditionals)
        
        # Find all loops
        for_pattern = r'\{\%\s*for\s+([a-zA-Z0-9_.-]+)\s+in\s+([a-zA-Z0-9_.-]+)\s*\%\}'
        loops = re.findall(for_pattern, template_content)
        results["loops"] = [{"item": item, "collection": collection} for item, collection in loops]
        
        # Find all includes
        include_pattern = r'\{\%\s*include\s+[\'"]([a-zA-Z0-9_.-/]+)[\'"]\s*\%\}'
        includes = set(re.findall(include_pattern, template_content))
        results["includes"] = list(includes)
        
        # Check for required variables
        if required_variables:
            missing_variables = [var for var in required_variables if var not in variables]
            results["missing_variables"] = missing_variables
            
            if missing_variables:
                results["valid"] = False
                logger.warning(f"Template {template_path} is missing required variables: {missing_variables}")
        
        # Check for balanced tags
        if_count = len(re.findall(r'\{\%\s*if\s+', template_content))
        endif_count = len(re.findall(r'\{\%\s*endif\s*\%\}', template_content))
        
        if if_count != endif_count:
            results["valid"] = False
            results["error"] = f"Unbalanced if/endif tags: {if_count} if tags, {endif_count} endif tags"
            logger.warning(f"Template {template_path} has unbalanced if/endif tags")
        
        for_count = len(re.findall(r'\{\%\s*for\s+', template_content))
        endfor_count = len(re.findall(r'\{\%\s*endfor\s*\%\}', template_content))
        
        if for_count != endfor_count:
            results["valid"] = False
            results["error"] = f"Unbalanced for/endfor tags: {for_count} for tags, {endfor_count} endfor tags"
            logger.warning(f"Template {template_path} has unbalanced for/endfor tags")
        
        # Check for includes that don't exist
        template_dir = os.path.dirname(template_path)
        for include in includes:
            include_path = os.path.join(template_dir, include)
            if not os.path.exists(include_path):
                results["valid"] = False
                if "include_errors" not in results:
                    results["include_errors"] = []
                results["include_errors"].append(f"Include not found: {include}")
                logger.warning(f"Template {template_path} includes non-existent file: {include}")
        
        logger.info(f"Template validation results: valid={results['valid']}")
        return results["valid"], results
    
    except Exception as e:
        logger.error(f"Failed to validate template {template_path}: {str(e)}")
        return False, {"error": f"Failed to validate template: {str(e)}"}


def validate_template_directory(
    template_dir: str,
    required_variables: Optional[List[str]] = None,
    pattern: str = "*.tmpl",
    recursive: bool = True
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate all templates in a directory.
    
    Args:
        template_dir: Path to the template directory
        required_variables: List of variables that must be present in all templates
        pattern: Glob pattern to match template files
        recursive: Whether to search recursively
        
    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and validation results
    """
    logger.info(f"Validating templates in directory: {template_dir}")
    
    if not os.path.exists(template_dir):
        logger.error(f"Template directory not found: {template_dir}")
        return False, {"error": f"Template directory not found: {template_dir}"}
    
    # Discover templates
    templates = discover_templates(template_dir, pattern, recursive)
    
    if not templates:
        logger.warning(f"No templates found in {template_dir} with pattern {pattern}")
        return True, {"valid": True, "templates": []}
    
    # Validate each template
    results = {
        "valid": True,
        "templates": []
    }
    
    for template_path in templates:
        valid, template_results = validate_template(template_path, required_variables)
        results["templates"].append(template_results)
        
        if not valid:
            results["valid"] = False
    
    logger.info(f"Template directory validation results: valid={results['valid']}, templates={len(results['templates'])}")
    return results["valid"], results


def create_template_context(
    context_file: Optional[str] = None,
    additional_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a template context from a file and/or additional context.
    
    Args:
        context_file: Path to a JSON context file
        additional_context: Additional context variables
        
    Returns:
        Dict[str, Any]: Combined template context
    """
    logger.info("Creating template context")
    
    context = {}
    
    # Load context from file if provided
    if context_file:
        if not os.path.exists(context_file):
            logger.warning(f"Context file not found: {context_file}")
        else:
            try:
                with open(context_file, 'r', encoding='utf-8') as f:
                    file_context = json.load(f)
                context.update(file_context)
                logger.info(f"Loaded {len(file_context)} variables from context file")
            except Exception as e:
                logger.error(f"Failed to load context file: {str(e)}")
    
    # Add additional context if provided
    if additional_context:
        context.update(additional_context)
        logger.info(f"Added {len(additional_context)} additional context variables")
    
    return context


def save_template_context(
    context: Dict[str, Any],
    output_file: str,
    overwrite: bool = False
) -> Tuple[bool, str]:
    """
    Save a template context to a JSON file.
    
    Args:
        context: Template context to save
        output_file: Path to the output file
        overwrite: Whether to overwrite an existing file
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
    logger.info(f"Saving template context to {output_file}")
    
    # Check if the output file already exists
    if os.path.exists(output_file) and not overwrite:
        logger.warning(f"Output file already exists: {output_file}")
        return False, f"Output file already exists: {output_file}"
    
    # Create the output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Write the context to the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(context, f, indent=2)
        
        logger.info(f"Successfully saved template context to {output_file}")
        return True, f"Successfully saved template context to {output_file}"
    except Exception as e:
        logger.error(f"Failed to save template context: {str(e)}")
        return False, f"Failed to save template context: {str(e)}"


def customize_template(
    template_path: str,
    output_path: str,
    context: Dict[str, Any],
    overwrite: bool = False
) -> Tuple[bool, str]:
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
    logger.info(f"Customizing template {template_path} to {output_path}")
    
    # Check if the template file exists
    if not os.path.exists(template_path):
        logger.error(f"Template file not found: {template_path}")
        return False, f"Template file not found: {template_path}"
    
    # Check if the output file already exists
    if os.path.exists(output_path) and not overwrite:
        logger.warning(f"Output file already exists: {output_path}")
        return False, f"Output file already exists: {output_path}"
    
    # Create the output directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Read the template content
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Create a template engine with the template directory
        template_dir = os.path.dirname(template_path)
        engine = TemplateEngine(template_dir)
        
        # Render the template
        rendered_content = engine.render_string(template_content, context)
        
        # Write the rendered content to the output file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered_content)
        
        logger.info(f"Successfully customized template to {output_path}")
        return True, f"Successfully customized template to {output_path}"
    except Exception as e:
        logger.error(f"Failed to customize template: {str(e)}")
        return False, f"Failed to customize template: {str(e)}"
