"""
Unit tests for template engine functionality.
"""
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

import pytest

from pythonweb_installer.templates.engine import (
    TemplateEngine,
    render_template_file,
    render_template_directory
)


class TestTemplateEngine:
    """Tests for template engine functionality."""

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

        # Create a nested template
        nested_dir = os.path.join(template_dir, "nested")
        os.makedirs(nested_dir, exist_ok=True)
        with open(os.path.join(nested_dir, "nested.tmpl"), "w") as f:
            f.write("Nested: {{ value }}")

        return template_dir

    def test_render_template_simple(self, template_dir):
        """Test rendering a simple template."""
        engine = TemplateEngine(template_dir)
        result = engine.render_template("simple.tmpl", {"name": "World"})

        assert result == "Hello, World!"

    def test_render_template_conditional_true(self, template_dir):
        """Test rendering a template with a true condition."""
        engine = TemplateEngine(template_dir)
        result = engine.render_template("conditional.tmpl", {"name": "World", "show_greeting": True})

        assert result == "Hello, World!"

    def test_render_template_conditional_false(self, template_dir):
        """Test rendering a template with a false condition."""
        engine = TemplateEngine(template_dir)
        result = engine.render_template("conditional.tmpl", {"name": "World", "show_greeting": False})

        assert result == "Goodbye, World!"

    def test_render_template_loop(self, template_dir):
        """Test rendering a template with a loop."""
        engine = TemplateEngine(template_dir)
        result = engine.render_template("loop.tmpl", {"items": ["one", "two", "three"]})

        assert result == "onetwothree"

    def test_render_template_include(self, template_dir):
        """Test rendering a template with an include."""
        engine = TemplateEngine(template_dir)
        result = engine.render_template("include.tmpl", {"name": "World"})

        assert result == "Hello, World!"

    def test_render_template_nested(self, template_dir):
        """Test rendering a nested template."""
        engine = TemplateEngine(template_dir)
        result = engine.render_template("nested/nested.tmpl", {"value": "test"})

        assert result == "Nested: test"

    def test_render_template_missing_variable(self, template_dir):
        """Test rendering a template with a missing variable."""
        engine = TemplateEngine(template_dir)
        result = engine.render_template("simple.tmpl", {})

        assert "{{ name }}" in result

    def test_render_template_not_found(self, template_dir):
        """Test rendering a non-existent template."""
        engine = TemplateEngine(template_dir)

        with pytest.raises(FileNotFoundError):
            engine.render_template("nonexistent.tmpl", {})

    def test_render_string(self, template_dir):
        """Test rendering a template string."""
        engine = TemplateEngine(template_dir)
        result = engine.render_string("Hello, {{ name }}!", {"name": "World"})

        assert result == "Hello, World!"

    def test_render_string_with_conditional(self, template_dir):
        """Test rendering a template string with conditionals."""
        engine = TemplateEngine(template_dir)
        template = "{% if show_greeting %}Hello{% else %}Goodbye{% endif %}, {{ name }}!"
        result = engine.render_string(template, {"name": "World", "show_greeting": True})

        assert result == "Hello, World!"

    def test_render_string_with_loop(self, template_dir):
        """Test rendering a template string with a loop."""
        engine = TemplateEngine(template_dir)
        template = "{% for item in items %}{{ item }}{% endfor %}"
        result = engine.render_string(template, {"items": ["A", "B", "C"]})

        assert result == "ABC"

    def test_render_template_file(self, template_dir, temp_dir):
        """Test rendering a template file to an output file."""
        template_path = os.path.join(template_dir, "simple.tmpl")
        output_path = os.path.join(temp_dir, "output.txt")

        success, message = render_template_file(template_path, output_path, {"name": "World"})

        assert success is True
        assert "Successfully rendered template" in message
        assert os.path.exists(output_path)

        with open(output_path, "r") as f:
            content = f.read()
            assert content == "Hello, World!"

    def test_render_template_file_not_found(self, temp_dir):
        """Test rendering a non-existent template file."""
        template_path = os.path.join(temp_dir, "nonexistent.tmpl")
        output_path = os.path.join(temp_dir, "output.txt")

        success, message = render_template_file(template_path, output_path, {})

        assert success is False
        assert "Template file not found" in message
        assert not os.path.exists(output_path)

    def test_render_template_file_output_dir_creation(self, template_dir, temp_dir):
        """Test rendering a template file with output directory creation."""
        template_path = os.path.join(template_dir, "simple.tmpl")
        output_dir = os.path.join(temp_dir, "nested", "output")
        output_path = os.path.join(output_dir, "output.txt")

        success, message = render_template_file(template_path, output_path, {"name": "World"})

        assert success is True
        assert "Successfully rendered template" in message
        assert os.path.exists(output_path)

    def test_render_template_directory(self, template_dir, temp_dir):
        """Test rendering a template directory."""
        output_dir = os.path.join(temp_dir, "output")

        success, results = render_template_directory(template_dir, output_dir, {"name": "World", "show_greeting": True, "items": ["A", "B"], "value": "test"})

        assert success is True
        assert len(results["rendered_files"]) > 0
        assert os.path.exists(os.path.join(output_dir, "simple"))
        assert os.path.exists(os.path.join(output_dir, "conditional"))
        assert os.path.exists(os.path.join(output_dir, "loop"))
        assert os.path.exists(os.path.join(output_dir, "include"))
        assert os.path.exists(os.path.join(output_dir, "nested", "nested"))

        # Check the content of the rendered files
        with open(os.path.join(output_dir, "simple"), "r") as f:
            assert f.read() == "Hello, World!"

    def test_render_template_directory_with_exclusions(self, template_dir, temp_dir):
        """Test rendering a template directory with exclusions."""
        output_dir = os.path.join(temp_dir, "output")

        success, results = render_template_directory(
            template_dir,
            output_dir,
            {"name": "World"},
            exclude_patterns=["*loop*", "nested*"]
        )

        assert success is True
        assert os.path.exists(os.path.join(output_dir, "simple"))
        assert os.path.exists(os.path.join(output_dir, "conditional"))
        assert os.path.exists(os.path.join(output_dir, "include"))
        assert not os.path.exists(os.path.join(output_dir, "loop"))
        assert not os.path.exists(os.path.join(output_dir, "nested", "nested"))

    def test_render_template_directory_not_found(self, temp_dir):
        """Test rendering a non-existent template directory."""
        template_dir = os.path.join(temp_dir, "nonexistent")
        output_dir = os.path.join(temp_dir, "output")

        success, results = render_template_directory(template_dir, output_dir, {})

        assert success is False
        assert "error" in results
        assert "Template directory not found" in results["error"]
