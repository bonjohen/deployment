"""
Template engine functionality.
"""
import os
import re
import logging
import shutil
from typing import Dict, Any, List, Tuple, Optional, Set, Union

logger = logging.getLogger(__name__)


class TemplateEngine:
    """
    Template engine for rendering templates with variable substitution and conditional logic.
    """

    # Regex patterns for template syntax
    VAR_PATTERN = r'\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}'
    IF_START_PATTERN = r'\{\%\s*if\s+([a-zA-Z0-9_.-]+)\s*\%\}'
    IF_ELSE_PATTERN = r'\{\%\s*else\s*\%\}'
    IF_END_PATTERN = r'\{\%\s*endif\s*\%\}'
    FOR_START_PATTERN = r'\{\%\s*for\s+([a-zA-Z0-9_.-]+)\s+in\s+([a-zA-Z0-9_.-]+)\s*\%\}'
    FOR_END_PATTERN = r'\{\%\s*endfor\s*\%\}'
    INCLUDE_PATTERN = r'\{\%\s*include\s+[\'"]([a-zA-Z0-9_.-/]+)[\'"]\s*\%\}'

    def __init__(self, template_dir: str):
        """
        Initialize the template engine.

        Args:
            template_dir: Directory containing template files
        """
        self.template_dir = template_dir
        self.templates_cache = {}

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a template with the given context.

        Args:
            template_name: Name of the template file
            context: Dictionary of variables to use in rendering

        Returns:
            str: Rendered template content
        """
        logger.info(f"Rendering template: {template_name}")

        # Load the template content
        template_content = self._load_template(template_name)

        # Process includes first
        template_content = self._process_includes(template_content, context)

        # Process conditionals
        template_content = self._process_conditionals(template_content, context)

        # Process loops
        template_content = self._process_loops(template_content, context)

        # Process variables
        template_content = self._process_variables(template_content, context)

        return template_content

    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """
        Render a template string with the given context.

        Args:
            template_string: Template content as a string
            context: Dictionary of variables to use in rendering

        Returns:
            str: Rendered template content
        """
        logger.info("Rendering template string")

        # Process includes first
        template_content = self._process_includes(template_string, context)

        # Process conditionals
        template_content = self._process_conditionals(template_content, context)

        # Process loops
        template_content = self._process_loops(template_content, context)

        # Process variables
        template_content = self._process_variables(template_content, context)

        return template_content

    def _load_template(self, template_name: str) -> str:
        """
        Load a template from the template directory.

        Args:
            template_name: Name of the template file

        Returns:
            str: Template content

        Raises:
            FileNotFoundError: If the template file doesn't exist
        """
        # Check if template is in cache
        if template_name in self.templates_cache:
            return self.templates_cache[template_name]

        # Construct the template path
        template_path = os.path.join(self.template_dir, template_name)

        # Check if the template file exists
        if not os.path.exists(template_path):
            logger.error(f"Template file not found: {template_path}")
            raise FileNotFoundError(f"Template file not found: {template_path}")

        # Read the template content
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()

            # Cache the template content
            self.templates_cache[template_name] = template_content

            return template_content
        except Exception as e:
            logger.error(f"Failed to load template {template_name}: {str(e)}")
            raise

    def _process_variables(self, content: str, context: Dict[str, Any]) -> str:
        """
        Replace variables in the template with their values from the context.

        Args:
            content: Template content
            context: Dictionary of variables

        Returns:
            str: Processed content with variables replaced
        """
        def replace_var(match):
            var_name = match.group(1)
            if var_name in context:
                return str(context[var_name])
            else:
                logger.warning(f"Variable not found in context: {var_name}")
                return f"{{{{ {var_name} }}}}"  # Keep the variable as is

        return re.sub(self.VAR_PATTERN, replace_var, content)

    def _process_conditionals(self, content: str, context: Dict[str, Any]) -> str:
        """
        Process conditional blocks in the template.

        Args:
            content: Template content
            context: Dictionary of variables

        Returns:
            str: Processed content with conditionals evaluated
        """
        # Find all if blocks
        if_blocks = []
        start_pos = 0

        while True:
            # Find the start of an if block
            if_match = re.search(self.IF_START_PATTERN, content[start_pos:])
            if not if_match:
                break

            if_start = start_pos + if_match.start()
            var_name = if_match.group(1)

            # Find the corresponding endif
            nesting_level = 1
            end_pos = if_start + len(if_match.group(0))
            else_pos = None

            while nesting_level > 0 and end_pos < len(content):
                # Check for nested if
                nested_if = re.search(self.IF_START_PATTERN, content[end_pos:])
                nested_if_pos = end_pos + nested_if.start() if nested_if else len(content)

                # Check for else
                else_match = re.search(self.IF_ELSE_PATTERN, content[end_pos:])
                else_match_pos = end_pos + else_match.start() if else_match else len(content)

                # Check for endif
                endif_match = re.search(self.IF_END_PATTERN, content[end_pos:])
                endif_match_pos = end_pos + endif_match.start() if endif_match else len(content)

                # Find the closest match
                min_pos = min(nested_if_pos, else_match_pos, endif_match_pos)

                if min_pos == nested_if_pos and nested_if:
                    # Found a nested if
                    nesting_level += 1
                    end_pos = min_pos + len(nested_if.group(0))
                elif min_pos == else_match_pos and else_match and nesting_level == 1:
                    # Found an else for the current if
                    else_pos = min_pos
                    end_pos = min_pos + len(else_match.group(0))
                elif min_pos == endif_match_pos and endif_match:
                    # Found an endif
                    nesting_level -= 1
                    if nesting_level == 0:
                        endif_pos = min_pos
                        end_pos = min_pos + len(endif_match.group(0))
                        if_blocks.append((if_start, endif_pos + len(endif_match.group(0)), var_name, else_pos))
                    else:
                        end_pos = min_pos + len(endif_match.group(0))
                else:
                    # No match found, break to avoid infinite loop
                    break

            start_pos = end_pos

        # Process if blocks from the end to avoid position shifts
        for if_start, if_end, var_name, else_pos in sorted(if_blocks, key=lambda x: x[0], reverse=True):
            # Check if the condition is true
            condition_value = bool(context.get(var_name, False))

            if else_pos is not None:
                # If-else block
                if_block = content[if_start:else_pos]
                else_block = content[else_pos:if_end]

                # Extract the content without the tags
                if_content = if_block[if_block.find('%}') + 2:]
                else_content = else_block[else_block.find('%}') + 2:else_block.rfind('{%')]

                # Replace the entire if-else block with the appropriate content
                if condition_value:
                    content = content[:if_start] + if_content + content[if_end:]
                else:
                    content = content[:if_start] + else_content + content[if_end:]
            else:
                # If block without else
                if_block = content[if_start:if_end]

                # Extract the content without the tags
                if_content = if_block[if_block.find('%}') + 2:if_block.rfind('{%')]

                # Replace the entire if block with the content or empty string
                if condition_value:
                    content = content[:if_start] + if_content + content[if_end:]
                else:
                    content = content[:if_start] + content[if_end:]

        return content

    def _process_loops(self, content: str, context: Dict[str, Any]) -> str:
        """
        Process loop blocks in the template.

        Args:
            content: Template content
            context: Dictionary of variables

        Returns:
            str: Processed content with loops expanded
        """
        # Find all for blocks
        for_blocks = []
        start_pos = 0

        while True:
            # Find the start of a for block
            for_match = re.search(self.FOR_START_PATTERN, content[start_pos:])
            if not for_match:
                break

            for_start = start_pos + for_match.start()
            item_var = for_match.group(1)
            collection_var = for_match.group(2)

            # Find the corresponding endfor
            nesting_level = 1
            end_pos = for_start + len(for_match.group(0))

            while nesting_level > 0 and end_pos < len(content):
                # Check for nested for
                nested_for = re.search(self.FOR_START_PATTERN, content[end_pos:])
                nested_for_pos = end_pos + nested_for.start() if nested_for else len(content)

                # Check for endfor
                endfor_match = re.search(self.FOR_END_PATTERN, content[end_pos:])
                endfor_match_pos = end_pos + endfor_match.start() if endfor_match else len(content)

                # Find the closest match
                min_pos = min(nested_for_pos, endfor_match_pos)

                if min_pos == nested_for_pos and nested_for:
                    # Found a nested for
                    nesting_level += 1
                    end_pos = min_pos + len(nested_for.group(0))
                elif min_pos == endfor_match_pos and endfor_match:
                    # Found an endfor
                    nesting_level -= 1
                    if nesting_level == 0:
                        endfor_pos = min_pos
                        end_pos = min_pos + len(endfor_match.group(0))
                        for_blocks.append((for_start, endfor_pos + len(endfor_match.group(0)), item_var, collection_var))
                    else:
                        end_pos = min_pos + len(endfor_match.group(0))
                else:
                    # No match found, break to avoid infinite loop
                    break

            start_pos = end_pos

        # Process for blocks from the end to avoid position shifts
        for for_start, for_end, item_var, collection_var in sorted(for_blocks, key=lambda x: x[0], reverse=True):
            # Get the collection from the context
            collection = context.get(collection_var, [])
            if not collection:
                # Empty collection, remove the for block
                content = content[:for_start] + content[for_end:]
                continue

            # Extract the for block content
            for_block = content[for_start:for_end]
            for_content = for_block[for_block.find('%}') + 2:for_block.rfind('{%')].strip()

            # Generate the expanded content
            expanded_content = []
            for item in collection:
                # Create a new context with the loop variable
                loop_context = context.copy()
                loop_context[item_var] = item

                # Render the loop content with the loop context
                item_content = self._process_variables(for_content, loop_context)
                expanded_content.append(item_content)

            # Replace the for block with the expanded content
            content = content[:for_start] + ''.join(expanded_content) + content[for_end:]

        return content

    def _process_includes(self, content: str, context: Dict[str, Any]) -> str:
        """
        Process include directives in the template.

        Args:
            content: Template content
            context: Dictionary of variables

        Returns:
            str: Processed content with includes expanded
        """
        def replace_include(match):
            include_template = match.group(1)
            try:
                include_content = self._load_template(include_template)
                return include_content
            except FileNotFoundError:
                logger.warning(f"Include template not found: {include_template}")
                return f"{{% include '{include_template}' %}}"

        return re.sub(self.INCLUDE_PATTERN, replace_include, content)


def render_template_file(template_path: str, output_path: str, context: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Render a template file to an output file.

    Args:
        template_path: Path to the template file
        output_path: Path to the output file
        context: Dictionary of variables to use in rendering

    Returns:
        Tuple[bool, str]: Success status and message
    """
    logger.info(f"Rendering template file: {template_path} to {output_path}")

    # Check if the template file exists
    if not os.path.exists(template_path):
        logger.error(f"Template file not found: {template_path}")
        return False, f"Template file not found: {template_path}"

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

        logger.info(f"Successfully rendered template to {output_path}")
        return True, f"Successfully rendered template to {output_path}"
    except Exception as e:
        logger.error(f"Failed to render template: {str(e)}")
        return False, f"Failed to render template: {str(e)}"


def render_template_directory(
    template_dir: str,
    output_dir: str,
    context: Dict[str, Any],
    exclude_patterns: Optional[List[str]] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Render all templates in a directory to an output directory.

    Args:
        template_dir: Path to the template directory
        output_dir: Path to the output directory
        context: Dictionary of variables to use in rendering
        exclude_patterns: List of glob patterns to exclude

    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and results
    """
    logger.info(f"Rendering template directory: {template_dir} to {output_dir}")

    # Check if the template directory exists
    if not os.path.exists(template_dir):
        logger.error(f"Template directory not found: {template_dir}")
        return False, {"error": f"Template directory not found: {template_dir}"}

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Initialize the template engine
    engine = TemplateEngine(template_dir)

    # Initialize results
    results = {
        "success": True,
        "rendered_files": [],
        "copied_files": [],
        "failed_files": []
    }

    # Compile exclude patterns
    exclude_regexes = []
    if exclude_patterns:
        for pattern in exclude_patterns:
            # Convert glob pattern to regex
            regex_pattern = pattern.replace('.', r'\.').replace('*', r'.*').replace('?', r'.')
            exclude_regexes.append(re.compile(regex_pattern))

    # Walk through the template directory
    for root, dirs, files in os.walk(template_dir):
        # Create the corresponding output directory
        rel_path = os.path.relpath(root, template_dir)
        if rel_path == '.':
            rel_path = ''

        output_subdir = os.path.join(output_dir, rel_path)
        os.makedirs(output_subdir, exist_ok=True)

        # Process each file
        for file in files:
            # Check if the file should be excluded
            file_path = os.path.join(rel_path, file)
            if any(regex.match(file_path) for regex in exclude_regexes):
                logger.info(f"Skipping excluded file: {file_path}")
                continue

            # Determine if the file is a template or should be copied as-is
            template_path = os.path.join(root, file)
            output_path = os.path.join(output_subdir, file)

            if file.endswith(('.tmpl', '.template', '.j2', '.jinja', '.jinja2')):
                # Render the template
                output_path = output_path.rsplit('.', 1)[0]  # Remove the template extension
                success, message = render_template_file(template_path, output_path, context)

                if success:
                    results["rendered_files"].append({
                        "template_path": template_path,
                        "output_path": output_path
                    })
                else:
                    results["success"] = False
                    results["failed_files"].append({
                        "template_path": template_path,
                        "output_path": output_path,
                        "error": message
                    })
            else:
                # Copy the file as-is
                try:
                    shutil.copy2(template_path, output_path)
                    results["copied_files"].append({
                        "source_path": template_path,
                        "output_path": output_path
                    })
                except Exception as e:
                    results["success"] = False
                    results["failed_files"].append({
                        "source_path": template_path,
                        "output_path": output_path,
                        "error": str(e)
                    })

    # Log the results
    logger.info(f"Rendered {len(results['rendered_files'])} templates, copied {len(results['copied_files'])} files, failed {len(results['failed_files'])} files")

    return results["success"], results
