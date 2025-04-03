"""
Unit tests for template management functionality.
"""
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

import pytest

from pythonweb_installer.templates.management import (
    discover_templates,
    validate_template,
    validate_template_directory,
    create_template_context,
    save_template_context,
    customize_template
)


class TestTemplateManagement:
    """Tests for template management functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def template_dir(self, temp_dir):
        """Create a directory with template files."""
        template_dir = os.path.join(temp_dir, "templates")
        os.makedirs(template_dir, exist_ok=True)
        
        # Create a simple template
        with open(os.path.join(template_dir, "simple.tmpl"), "w") as f:
            f.write("Hello, {{ name }}!")
        
        # Create a template with conditionals
        with open(os.path.join(template_dir, "conditional.tmpl"), "w") as f:
            f.write("{% if show_greeting %}Hello, {{ name }}!{% else %}Goodbye, {{ name }}!{% endif %}")
        
        # Create a template with loops
        with open(os.path.join(template_dir, "loop.tmpl"), "w") as f:
            f.write("{% for item in items %}{{ item }}\n{% endfor %}")
        
        # Create a template with includes
        with open(os.path.join(template_dir, "include.tmpl"), "w") as f:
            f.write("{% include 'simple.tmpl' %}")
        
        # Create a template with unbalanced tags
        with open(os.path.join(template_dir, "unbalanced.tmpl"), "w") as f:
            f.write("{% if condition %}Content{% endif %}{% if another %}More")
        
        # Create a nested template
        nested_dir = os.path.join(template_dir, "nested")
        os.makedirs(nested_dir, exist_ok=True)
        with open(os.path.join(nested_dir, "nested.tmpl"), "w") as f:
            f.write("Nested: {{ value }}")
        
        # Create a non-template file
        with open(os.path.join(template_dir, "not_template.txt"), "w") as f:
            f.write("This is not a template")
        
        return template_dir
    
    @pytest.fixture
    def context_file(self, temp_dir):
        """Create a context file."""
        context_file = os.path.join(temp_dir, "context.json")
        context = {
            "name": "World",
            "show_greeting": True,
            "items": ["one", "two", "three"],
            "value": "test"
        }
        
        with open(context_file, "w") as f:
            json.dump(context, f)
        
        return context_file
    
    def test_discover_templates_recursive(self, template_dir):
        """Test discovering templates recursively."""
        templates = discover_templates(template_dir, "*.tmpl", recursive=True)
        
        assert len(templates) == 6  # 5 templates + 1 nested template
        assert any("simple.tmpl" in t for t in templates)
        assert any("conditional.tmpl" in t for t in templates)
        assert any("loop.tmpl" in t for t in templates)
        assert any("include.tmpl" in t for t in templates)
        assert any("unbalanced.tmpl" in t for t in templates)
        assert any("nested.tmpl" in t for t in templates)
    
    def test_discover_templates_non_recursive(self, template_dir):
        """Test discovering templates non-recursively."""
        templates = discover_templates(template_dir, "*.tmpl", recursive=False)
        
        assert len(templates) == 5  # 5 templates in the root directory
        assert any("simple.tmpl" in t for t in templates)
        assert any("conditional.tmpl" in t for t in templates)
        assert any("loop.tmpl" in t for t in templates)
        assert any("include.tmpl" in t for t in templates)
        assert any("unbalanced.tmpl" in t for t in templates)
        assert not any("nested.tmpl" in t for t in templates)
    
    def test_discover_templates_with_pattern(self, template_dir):
        """Test discovering templates with a specific pattern."""
        templates = discover_templates(template_dir, "*loop*.tmpl")
        
        assert len(templates) == 1
        assert "loop.tmpl" in templates[0]
    
    def test_discover_templates_directory_not_found(self, temp_dir):
        """Test discovering templates in a non-existent directory."""
        nonexistent_dir = os.path.join(temp_dir, "nonexistent")
        templates = discover_templates(nonexistent_dir)
        
        assert len(templates) == 0
    
    def test_validate_template_valid(self, template_dir):
        """Test validating a valid template."""
        template_path = os.path.join(template_dir, "simple.tmpl")
        valid, results = validate_template(template_path)
        
        assert valid is True
        assert results["path"] == template_path
        assert "name" in results["variables"]
        assert len(results["conditionals"]) == 0
        assert len(results["loops"]) == 0
        assert len(results["includes"]) == 0
    
    def test_validate_template_with_required_variables(self, template_dir):
        """Test validating a template with required variables."""
        template_path = os.path.join(template_dir, "simple.tmpl")
        valid, results = validate_template(template_path, required_variables=["name", "age"])
        
        assert valid is False
        assert "age" in results["missing_variables"]
    
    def test_validate_template_with_conditionals(self, template_dir):
        """Test validating a template with conditionals."""
        template_path = os.path.join(template_dir, "conditional.tmpl")
        valid, results = validate_template(template_path)
        
        assert valid is True
        assert "name" in results["variables"]
        assert "show_greeting" in results["conditionals"]
    
    def test_validate_template_with_loops(self, template_dir):
        """Test validating a template with loops."""
        template_path = os.path.join(template_dir, "loop.tmpl")
        valid, results = validate_template(template_path)
        
        assert valid is True
        assert len(results["loops"]) == 1
        assert results["loops"][0]["item"] == "item"
        assert results["loops"][0]["collection"] == "items"
    
    def test_validate_template_with_includes(self, template_dir):
        """Test validating a template with includes."""
        template_path = os.path.join(template_dir, "include.tmpl")
        valid, results = validate_template(template_path)
        
        assert valid is True
        assert "simple.tmpl" in results["includes"]
    
    def test_validate_template_unbalanced_tags(self, template_dir):
        """Test validating a template with unbalanced tags."""
        template_path = os.path.join(template_dir, "unbalanced.tmpl")
        valid, results = validate_template(template_path)
        
        assert valid is False
        assert "error" in results
        assert "Unbalanced if/endif tags" in results["error"]
    
    def test_validate_template_not_found(self, temp_dir):
        """Test validating a non-existent template."""
        template_path = os.path.join(temp_dir, "nonexistent.tmpl")
        valid, results = validate_template(template_path)
        
        assert valid is False
        assert "error" in results
        assert "Template file not found" in results["error"]
    
    def test_validate_template_directory(self, template_dir):
        """Test validating a template directory."""
        valid, results = validate_template_directory(template_dir)
        
        assert valid is False  # Because of the unbalanced template
        assert "templates" in results
        assert len(results["templates"]) == 6  # 5 templates + 1 nested template
    
    def test_validate_template_directory_with_pattern(self, template_dir):
        """Test validating a template directory with a specific pattern."""
        valid, results = validate_template_directory(template_dir, pattern="*simple*.tmpl")
        
        assert valid is True
        assert "templates" in results
        assert len(results["templates"]) == 1
    
    def test_validate_template_directory_with_required_variables(self, template_dir):
        """Test validating a template directory with required variables."""
        valid, results = validate_template_directory(template_dir, required_variables=["name", "age"])
        
        assert valid is False
        assert "templates" in results
        assert all("age" in t.get("missing_variables", []) for t in results["templates"] if "missing_variables" in t)
    
    def test_validate_template_directory_not_found(self, temp_dir):
        """Test validating a non-existent template directory."""
        nonexistent_dir = os.path.join(temp_dir, "nonexistent")
        valid, results = validate_template_directory(nonexistent_dir)
        
        assert valid is False
        assert "error" in results
        assert "Template directory not found" in results["error"]
    
    def test_create_template_context_empty(self):
        """Test creating an empty template context."""
        context = create_template_context()
        
        assert context == {}
    
    def test_create_template_context_from_file(self, context_file):
        """Test creating a template context from a file."""
        context = create_template_context(context_file)
        
        assert "name" in context
        assert context["name"] == "World"
        assert "show_greeting" in context
        assert "items" in context
        assert "value" in context
    
    def test_create_template_context_with_additional(self, context_file):
        """Test creating a template context with additional variables."""
        additional_context = {"age": 30, "location": "Earth"}
        context = create_template_context(context_file, additional_context)
        
        assert "name" in context
        assert "age" in context
        assert context["age"] == 30
        assert "location" in context
    
    def test_create_template_context_file_not_found(self, temp_dir):
        """Test creating a template context with a non-existent file."""
        nonexistent_file = os.path.join(temp_dir, "nonexistent.json")
        context = create_template_context(nonexistent_file)
        
        assert context == {}
    
    def test_save_template_context(self, temp_dir):
        """Test saving a template context."""
        context = {"name": "World", "age": 30}
        output_file = os.path.join(temp_dir, "output.json")
        
        success, message = save_template_context(context, output_file)
        
        assert success is True
        assert "Successfully saved template context" in message
        assert os.path.exists(output_file)
        
        # Verify the content
        with open(output_file, "r") as f:
            saved_context = json.load(f)
            assert saved_context == context
    
    def test_save_template_context_with_directory_creation(self, temp_dir):
        """Test saving a template context with directory creation."""
        context = {"name": "World"}
        output_dir = os.path.join(temp_dir, "nested", "output")
        output_file = os.path.join(output_dir, "context.json")
        
        success, message = save_template_context(context, output_file)
        
        assert success is True
        assert "Successfully saved template context" in message
        assert os.path.exists(output_file)
    
    def test_save_template_context_already_exists(self, temp_dir):
        """Test saving a template context to an existing file."""
        context = {"name": "World"}
        output_file = os.path.join(temp_dir, "context.json")
        
        # Create the file first
        with open(output_file, "w") as f:
            json.dump({"existing": "data"}, f)
        
        # Try to save without overwrite
        success, message = save_template_context(context, output_file, overwrite=False)
        
        assert success is False
        assert "Output file already exists" in message
        
        # Try to save with overwrite
        success, message = save_template_context(context, output_file, overwrite=True)
        
        assert success is True
        assert "Successfully saved template context" in message
        
        # Verify the content was overwritten
        with open(output_file, "r") as f:
            saved_context = json.load(f)
            assert saved_context == context
    
    def test_customize_template(self, template_dir, temp_dir):
        """Test customizing a template."""
        template_path = os.path.join(template_dir, "simple.tmpl")
        output_path = os.path.join(temp_dir, "output.txt")
        context = {"name": "World"}
        
        success, message = customize_template(template_path, output_path, context)
        
        assert success is True
        assert "Successfully customized template" in message
        assert os.path.exists(output_path)
        
        # Verify the content
        with open(output_path, "r") as f:
            content = f.read()
            assert content == "Hello, World!"
    
    def test_customize_template_with_directory_creation(self, template_dir, temp_dir):
        """Test customizing a template with directory creation."""
        template_path = os.path.join(template_dir, "simple.tmpl")
        output_dir = os.path.join(temp_dir, "nested", "output")
        output_path = os.path.join(output_dir, "output.txt")
        context = {"name": "World"}
        
        success, message = customize_template(template_path, output_path, context)
        
        assert success is True
        assert "Successfully customized template" in message
        assert os.path.exists(output_path)
    
    def test_customize_template_already_exists(self, template_dir, temp_dir):
        """Test customizing a template to an existing file."""
        template_path = os.path.join(template_dir, "simple.tmpl")
        output_path = os.path.join(temp_dir, "output.txt")
        context = {"name": "World"}
        
        # Create the file first
        with open(output_path, "w") as f:
            f.write("Existing content")
        
        # Try to customize without overwrite
        success, message = customize_template(template_path, output_path, context, overwrite=False)
        
        assert success is False
        assert "Output file already exists" in message
        
        # Try to customize with overwrite
        success, message = customize_template(template_path, output_path, context, overwrite=True)
        
        assert success is True
        assert "Successfully customized template" in message
        
        # Verify the content was overwritten
        with open(output_path, "r") as f:
            content = f.read()
            assert content == "Hello, World!"
    
    def test_customize_template_not_found(self, temp_dir):
        """Test customizing a non-existent template."""
        template_path = os.path.join(temp_dir, "nonexistent.tmpl")
        output_path = os.path.join(temp_dir, "output.txt")
        
        success, message = customize_template(template_path, output_path, {})
        
        assert success is False
        assert "Template file not found" in message
