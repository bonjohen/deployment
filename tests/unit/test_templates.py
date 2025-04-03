"""
Unit tests for the templates module.
"""
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

import pytest

import pythonweb_installer.templates as templates


class TestTemplates:
    """Tests for the templates module."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def template_file(self, temp_dir):
        """Create a template file."""
        template_path = os.path.join(temp_dir, "template.tmpl")
        with open(template_path, "w") as f:
            f.write("Hello, {{ name }}!")
        return template_path

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
            f.write("{% if show_greeting %}Hello{% else %}Goodbye{% endif %}, {{ name }}!")

        return template_dir

    @pytest.fixture
    def context_file(self, temp_dir):
        """Create a context file."""
        context_path = os.path.join(temp_dir, "context.json")
        context = {"name": "World", "show_greeting": True}

        with open(context_path, "w") as f:
            json.dump(context, f)

        return context_path

    def test_render_template(self, template_file):
        """Test rendering a template."""
        result = templates.render_template(template_file, {"name": "World"})

        assert result == "Hello, World!"

    def test_render_template_not_found(self, temp_dir):
        """Test rendering a non-existent template."""
        template_path = os.path.join(temp_dir, "nonexistent.tmpl")

        with pytest.raises(FileNotFoundError):
            templates.render_template(template_path, {})

    def test_render_template_to_file(self, template_file, temp_dir):
        """Test rendering a template to a file."""
        output_path = os.path.join(temp_dir, "output.txt")
        success, message = templates.render_template_to_file(template_file, output_path, {"name": "World"})

        assert success is True
        assert "Successfully rendered template" in message
        assert os.path.exists(output_path)

        with open(output_path, "r") as f:
            content = f.read()
            assert content == "Hello, World!"

    def test_render_directory(self, template_dir, temp_dir):
        """Test rendering a directory of templates."""
        output_dir = os.path.join(temp_dir, "output")
        success, results = templates.render_directory(template_dir, output_dir, {"name": "World", "show_greeting": True})

        assert success is True
        assert len(results["rendered_files"]) > 0
        assert os.path.exists(os.path.join(output_dir, "simple"))
        assert os.path.exists(os.path.join(output_dir, "conditional"))

        with open(os.path.join(output_dir, "simple"), "r") as f:
            content = f.read()
            assert content == "Hello, World!"

    def test_find_templates(self, template_dir):
        """Test finding templates."""
        template_list = templates.find_templates(template_dir, "*.tmpl")

        assert len(template_list) == 2
        assert any("simple.tmpl" in t for t in template_list)
        assert any("conditional.tmpl" in t for t in template_list)

    def test_validate_templates(self, template_dir):
        """Test validating templates."""
        valid, results = templates.validate_templates(template_dir, ["name"])

        assert valid is True
        assert "templates" in results
        assert len(results["templates"]) == 2

    def test_validate_templates_with_missing_variables(self, template_dir):
        """Test validating templates with missing variables."""
        valid, results = templates.validate_templates(template_dir, ["name", "age"])

        assert valid is False
        assert "templates" in results
        assert len(results["templates"]) == 2
        assert any("missing_variables" in t and "age" in t["missing_variables"] for t in results["templates"])

    def test_load_context(self, context_file):
        """Test loading a context."""
        context = templates.load_context(context_file)

        assert "name" in context
        assert context["name"] == "World"
        assert "show_greeting" in context
        assert context["show_greeting"] is True

    def test_load_context_with_additional(self, context_file):
        """Test loading a context with additional variables."""
        additional_context = {"age": 30}
        context = templates.load_context(context_file, additional_context)

        assert "name" in context
        assert "age" in context
        assert context["age"] == 30

    def test_save_context(self, temp_dir):
        """Test saving a context."""
        context = {"name": "World", "age": 30}
        output_path = os.path.join(temp_dir, "output.json")

        success, message = templates.save_context(context, output_path)

        assert success is True
        assert "Successfully saved template context" in message
        assert os.path.exists(output_path)

        with open(output_path, "r") as f:
            saved_context = json.load(f)
            assert saved_context == context

    def test_customize_template_file(self, template_file, temp_dir):
        """Test customizing a template file."""
        output_path = os.path.join(temp_dir, "output.txt")
        success, message = templates.customize_template_file(template_file, output_path, {"name": "World"})

        assert success is True
        assert "Successfully customized template" in message
        assert os.path.exists(output_path)

        with open(output_path, "r") as f:
            content = f.read()
            assert content == "Hello, World!"

    def test_validate_template_file(self, template_file):
        """Test validating a template file."""
        valid, results = templates.validate_template_file(template_file, ["name"])

        assert valid is True
        assert results["path"] == template_file
        assert "name" in results["variables"]

    def test_validate_template_file_with_missing_variables(self, template_file):
        """Test validating a template file with missing variables."""
        valid, results = templates.validate_template_file(template_file, ["name", "age"])

        assert valid is False
        assert results["path"] == template_file
        assert "missing_variables" in results
        assert "age" in results["missing_variables"]
