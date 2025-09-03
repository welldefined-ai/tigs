"""Tests for YAML schema validation and format compliance."""

import yaml
import pytest

from tigs.cli import main


class TestYAMLSchemaValidation:
    """Test YAML schema validation for tigs.chat/v1 format."""
    
    def test_valid_minimal_schema(self, git_notes_helper):
        """Test minimal valid schema."""
        minimal_yaml = """schema: tigs.chat/v1
messages:
- role: user
  content: Hello
"""
        assert git_notes_helper.validate_yaml_schema(minimal_yaml)
        
        data = yaml.safe_load(minimal_yaml)
        assert data['schema'] == 'tigs.chat/v1'
        assert len(data['messages']) == 1
        assert data['messages'][0]['role'] == 'user'
        assert data['messages'][0]['content'] == 'Hello'
    
    def test_valid_complex_schema(self, git_notes_helper):
        """Test complex valid schema with multiple messages."""
        complex_yaml = """schema: tigs.chat/v1
messages:
- role: user
  content: |
    Can you help me with a Python function?
    
    I need to process some data.
- role: assistant
  content: |
    I'd be happy to help! Here's a simple data processing function:
    
    ```python
    def process_data(data):
        return [item.strip().upper() for item in data if item.strip()]
    ```
- role: user
  content: Thanks! How do I handle errors?
- role: assistant
  content: |
    You can add error handling like this:
    
    ```python
    def process_data(data):
        try:
            return [item.strip().upper() for item in data if item.strip()]
        except AttributeError:
            return []
        except Exception as e:
            print(f"Error: {e}")
            return []
    ```
"""
        assert git_notes_helper.validate_yaml_schema(complex_yaml)
        
        data = yaml.safe_load(complex_yaml)
        assert len(data['messages']) == 4
        assert all(msg['role'] in ['user', 'assistant'] for msg in data['messages'])
        assert all(isinstance(msg['content'], str) for msg in data['messages'])
        assert all(len(msg['content']) > 0 for msg in data['messages'])
    
    def test_invalid_schema_missing_schema_field(self, git_notes_helper):
        """Test invalid schema missing schema field."""
        invalid_yaml = """messages:
- role: user
  content: Hello
"""
        assert not git_notes_helper.validate_yaml_schema(invalid_yaml)
    
    def test_invalid_schema_wrong_schema_version(self, git_notes_helper):
        """Test invalid schema with wrong version."""
        invalid_yaml = """schema: tigs.chat/v2
messages:
- role: user
  content: Hello
"""
        assert not git_notes_helper.validate_yaml_schema(invalid_yaml)
    
    def test_invalid_schema_missing_messages(self, git_notes_helper):
        """Test invalid schema missing messages field."""
        invalid_yaml = """schema: tigs.chat/v1
data:
- role: user
  content: Hello
"""
        assert not git_notes_helper.validate_yaml_schema(invalid_yaml)
    
    def test_invalid_schema_messages_not_list(self, git_notes_helper):
        """Test invalid schema where messages is not a list."""
        invalid_yaml = """schema: tigs.chat/v1
messages:
  role: user
  content: Hello
"""
        assert not git_notes_helper.validate_yaml_schema(invalid_yaml)
    
    def test_invalid_schema_message_missing_role(self, git_notes_helper):
        """Test invalid schema where message is missing role."""
        invalid_yaml = """schema: tigs.chat/v1
messages:
- content: Hello
"""
        assert not git_notes_helper.validate_yaml_schema(invalid_yaml)
    
    def test_invalid_schema_message_missing_content(self, git_notes_helper):
        """Test invalid schema where message is missing content."""
        invalid_yaml = """schema: tigs.chat/v1
messages:
- role: user
"""
        assert not git_notes_helper.validate_yaml_schema(invalid_yaml)
    
    def test_invalid_yaml_syntax(self, git_notes_helper):
        """Test invalid YAML syntax."""
        invalid_yaml = """schema: tigs.chat/v1
messages:
- role: user
  content: [unclosed bracket
"""
        assert not git_notes_helper.validate_yaml_schema(invalid_yaml)
    
    def test_schema_with_system_messages(self, git_notes_helper):
        """Test schema with system role messages."""
        system_yaml = """schema: tigs.chat/v1
messages:
- role: system
  content: You are a helpful assistant.
- role: user
  content: Hello
- role: assistant
  content: Hi there! How can I help you today?
"""
        assert git_notes_helper.validate_yaml_schema(system_yaml)
        
        data = yaml.safe_load(system_yaml)
        assert len(data['messages']) == 3
        assert data['messages'][0]['role'] == 'system'
    
    def test_schema_with_unicode_content(self, git_notes_helper):
        """Test schema validation with Unicode content."""
        unicode_yaml = """schema: tigs.chat/v1
messages:
- role: user
  content: |
    Hello in different languages:
    - Chinese: 你好
    - Arabic: مرحبا
    - Hindi: नमस्ते
    - Emoji: 👋🌍✨
- role: assistant
  content: |
    Great! Here are the pronunciations:
    - 你好 (nǐ hǎo)
    - مرحبا (marhaban)
    - नमस्ते (namaste)
    And some more emojis: 🗣️📚🎯
"""
        assert git_notes_helper.validate_yaml_schema(unicode_yaml)
        
        data = yaml.safe_load(unicode_yaml)
        assert "你好" in data['messages'][0]['content']
        assert "👋" in data['messages'][0]['content']
        assert "🗣️" in data['messages'][1]['content']
    
    def test_schema_with_empty_messages_list(self, git_notes_helper):
        """Test schema with empty messages list."""
        empty_messages_yaml = """schema: tigs.chat/v1
messages: []
"""
        # Empty messages should still be valid schema
        assert git_notes_helper.validate_yaml_schema(empty_messages_yaml)
        
        data = yaml.safe_load(empty_messages_yaml)
        assert len(data['messages']) == 0
    
    
    def test_store_and_retrieve_preserves_schema(self, runner, git_repo, git_notes_helper):
        """Test that storing and retrieving preserves YAML schema."""
        original_yaml = """schema: tigs.chat/v1
messages:
- role: user
  content: |
    Can you write a function to calculate fibonacci numbers?
- role: assistant
  content: |
    Here's a function to calculate fibonacci numbers:
    
    ```python
    def fibonacci(n):
        if n <= 1:
            return n
        return fibonacci(n-1) + fibonacci(n-2)
    ```
    
    This uses recursion. For better performance with large numbers,
    you might want to use dynamic programming or iteration.
- role: user
  content: Thanks! Can you show the iterative version?
- role: assistant
  content: |
    Sure! Here's the iterative version:
    
    ```python
    def fibonacci_iterative(n):
        if n <= 1:
            return n
        
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b
    ```
    
    This is much more efficient! 🚀
"""
        
        # Store the YAML
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", original_yaml])
        assert result.exit_code == 0
        commit_sha = result.output.split(":")[-1].strip()
        
        # Verify schema validation on stored content
        stored_content = git_notes_helper.get_note_content(git_repo, commit_sha)
        assert git_notes_helper.validate_yaml_schema(stored_content)
        
        # Verify content preservation (handle whitespace normalization)
        assert git_notes_helper.validate_yaml_schema(stored_content)
        assert "fibonacci numbers" in stored_content
        assert "fibonacci_iterative" in stored_content
        assert "🚀" in stored_content
        
        # Retrieve and verify
        result = runner.invoke(main, ["--repo", str(git_repo), "show-chat"])
        assert result.exit_code == 0
        assert git_notes_helper.validate_yaml_schema(result.output)
        assert "fibonacci numbers" in result.output
        assert "🚀" in result.output
    
    
    def test_schema_with_additional_fields(self, git_notes_helper):
        """Test schema validation with additional fields (forward compatibility)."""
        yaml_with_extra = """schema: tigs.chat/v1
metadata:
  created: 2024-01-01
messages:
- role: user
  content: Hello
  timestamp: 2024-01-01T12:00:00Z
"""
        assert git_notes_helper.validate_yaml_schema(yaml_with_extra)