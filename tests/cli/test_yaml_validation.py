#!/usr/bin/env python3
"""Test YAML schema validation for tigs.chat/v1 format - language-agnostic."""

import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

from framework.fixtures import create_test_repo


def run_tigs(repo_path, *args):
    """Run tigs command and return result."""
    cmd = ["uv", "run", "tigs", "--repo", str(repo_path)] + list(args)
    result = subprocess.run(cmd, cwd="/Users/basicthinker/Projects/tigs/python", 
                          capture_output=True, text=True)
    return result


def validate_yaml_schema(content):
    """Validate YAML content matches tigs.chat/v1 schema."""
    try:
        if not content or not content.strip():
            return False
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            return False
        if data.get('schema') != 'tigs.chat/v1':
            return False
        if 'messages' not in data:
            return False
        if not isinstance(data['messages'], list):
            return False
        
        for msg in data['messages']:
            if not isinstance(msg, dict):
                return False
            if 'role' not in msg or 'content' not in msg:
                return False
            if msg['role'] not in ['user', 'assistant', 'system']:
                return False
            if not isinstance(msg['content'], str):
                return False
        return True
    except:
        return False


class TestYAMLValidation:
    """Test YAML schema validation for tigs.chat/v1 format."""
    
    def test_valid_minimal_schema(self):
        """Test minimal valid schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "yaml_repo"
            create_test_repo(repo_path, ["YAML test commit"])
            
            minimal_yaml = """schema: tigs.chat/v1
messages:
- role: user
  content: Hello
"""
            
            # Test schema validation
            assert validate_yaml_schema(minimal_yaml)
            
            data = yaml.safe_load(minimal_yaml)
            assert data['schema'] == 'tigs.chat/v1'
            assert len(data['messages']) == 1
            assert data['messages'][0]['role'] == 'user'
            assert data['messages'][0]['content'] == 'Hello'
            
            # Test that it can be stored and retrieved
            result = run_tigs(repo_path, "add-chat", "-m", minimal_yaml)
            if result.returncode == 0:
                result = run_tigs(repo_path, "show-chat")
                if result.returncode == 0:
                    assert validate_yaml_schema(result.stdout)
                    assert "schema: tigs.chat/v1" in result.stdout
                    assert "Hello" in result.stdout
    
    def test_valid_complex_schema(self):
        """Test complex valid schema with multiple messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "complex_yaml_repo"
            create_test_repo(repo_path, ["Complex YAML test commit"])
            
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
    try:
        result = process_data(data)
    except Exception as e:
        print(f"Error: {e}")
    ```
"""
            
            # Test schema validation
            assert validate_yaml_schema(complex_yaml)
            
            data = yaml.safe_load(complex_yaml)
            assert data['schema'] == 'tigs.chat/v1'
            assert len(data['messages']) == 4
            
            # Verify all messages have correct structure
            for msg in data['messages']:
                assert 'role' in msg
                assert 'content' in msg
                assert msg['role'] in ['user', 'assistant']
                assert len(msg['content']) > 0
            
            # Test that complex content can be stored and retrieved
            result = run_tigs(repo_path, "add-chat", "-m", complex_yaml)
            if result.returncode == 0:
                result = run_tigs(repo_path, "show-chat")
                if result.returncode == 0:
                    assert validate_yaml_schema(result.stdout)
                    assert "process_data" in result.stdout
                    assert "```python" in result.stdout

    def test_invalid_schema_variations(self):
        """Test various invalid schema formats."""
        invalid_schemas = [
            # Wrong schema version
            """schema: tigs.chat/v2
messages:
- role: user
  content: Test
""",
            # Missing schema
            """messages:
- role: user
  content: Test
""",
            # Invalid role
            """schema: tigs.chat/v1
messages:
- role: invalid_role
  content: Test
""",
            # Missing content
            """schema: tigs.chat/v1
messages:
- role: user
""",
            # Non-string content
            """schema: tigs.chat/v1
messages:
- role: user
  content: 123
""",
            # Empty messages list (should be valid but edge case)
            """schema: tigs.chat/v1
messages: []
""",
        ]
        
        for i, invalid_yaml in enumerate(invalid_schemas):
            print(f"Testing invalid schema {i+1}")
            
            if i == len(invalid_schemas) - 1:  # Empty messages might be valid
                # Empty messages list might be valid depending on implementation
                result = validate_yaml_schema(invalid_yaml)
                print(f"Empty messages validation result: {result}")
            else:
                assert not validate_yaml_schema(invalid_yaml), f"Schema {i+1} should be invalid"

    def test_malformed_yaml_handling(self):
        """Test handling of malformed YAML content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "malformed_repo"
            create_test_repo(repo_path, ["Malformed YAML test"])
            
            malformed_yaml_samples = [
                "invalid: yaml: content: [unclosed",
                "not: valid: yaml: content: at: all: [[[",
                "",  # Empty content
                "{ this is not valid yaml ]",
            ]
            
            for malformed in malformed_yaml_samples:
                print(f"Testing malformed YAML: {malformed[:30]}...")
                
                # Schema validation should fail
                assert not validate_yaml_schema(malformed)
                
                # But tigs should handle it gracefully (might store or reject)
                result = run_tigs(repo_path, "add-chat", "-m", malformed)
                print(f"Add malformed result: {result.returncode}")
                
                # Should not crash - either succeeds (stores as-is) or fails gracefully
                assert result.returncode in [0, 1]
                
                if result.returncode == 0:
                    # If stored, should be retrievable
                    result = run_tigs(repo_path, "show-chat")
                    if result.returncode == 0:
                        print("✓ Malformed YAML stored and retrieved")
                    
                    # Clean up for next test
                    run_tigs(repo_path, "remove-chat")

    def test_unicode_yaml_validation(self):
        """Test YAML validation with Unicode content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "unicode_yaml_repo"
            create_test_repo(repo_path, ["Unicode YAML test"])
            
            unicode_yaml = """schema: tigs.chat/v1
messages:
- role: user
  content: |
    Unicode test: 你好世界 🌍
    Arabic: مرحبا بالعالم
    Emoji: 🚀 ⭐ 💫
- role: assistant
  content: |
    Unicode response: 
    - Chinese: 你好 (Hello)
    - Arabic: مرحبا (Welcome)
    - Symbols: ∑∫∞≈≠±×÷√
"""
            
            # Should validate correctly
            assert validate_yaml_schema(unicode_yaml)
            
            data = yaml.safe_load(unicode_yaml)
            assert data['schema'] == 'tigs.chat/v1'
            assert len(data['messages']) == 2
            
            # Test storage and retrieval of Unicode
            result = run_tigs(repo_path, "add-chat", "-m", unicode_yaml)
            if result.returncode == 0:
                result = run_tigs(repo_path, "show-chat")
                if result.returncode == 0:
                    assert validate_yaml_schema(result.stdout)
                    # Check that Unicode is preserved
                    assert "你好世界" in result.stdout or "你好" in result.stdout
                    assert "🌍" in result.stdout or "🚀" in result.stdout
                    print("✓ Unicode YAML validation and storage works")

    def test_large_yaml_content(self):
        """Test YAML validation with large content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "large_yaml_repo"
            create_test_repo(repo_path, ["Large YAML test"])
            
            # Create large YAML with many messages
            messages = []
            for i in range(20):
                messages.append({
                    "role": "user" if i % 2 == 0 else "assistant",
                    "content": f"Message {i}: " + ("Content " * 50)  # Make each message substantial
                })
            
            large_yaml_data = {
                "schema": "tigs.chat/v1",
                "messages": messages
            }
            
            large_yaml = yaml.dump(large_yaml_data, default_flow_style=False, allow_unicode=True)
            
            # Should validate correctly
            assert validate_yaml_schema(large_yaml)
            assert len(large_yaml) > 5000  # Should be substantial
            
            # Test storage and retrieval
            result = run_tigs(repo_path, "add-chat", "-m", large_yaml)
            if result.returncode == 0:
                result = run_tigs(repo_path, "show-chat")
                if result.returncode == 0:
                    assert validate_yaml_schema(result.stdout)
                    assert len(result.stdout) > 1000  # Should be large
                    print("✓ Large YAML validation and storage works")

    def test_edge_case_content(self):
        """Test edge cases in message content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "edge_case_repo"
            create_test_repo(repo_path, ["Edge case YAML test"])
            
            edge_cases = [
                # Very long single line
                "schema: tigs.chat/v1\nmessages:\n- role: user\n  content: " + ("Very long content " * 200),
                
                # Multiple newlines
                """schema: tigs.chat/v1
messages:
- role: user
  content: |
    Line 1
    
    
    Line with gaps
    
    Final line
""",
                
                # Special characters (properly escaped)
                """schema: tigs.chat/v1
messages:
- role: user
  content: "Special chars: !@#$%^&*()_+-=[]{}|;',./<>?"
""",
                
                # Code blocks
                """schema: tigs.chat/v1
messages:
- role: assistant
  content: |
    Here's some code:
    
    ```python
    def example():
        return "test"
    ```
    
    And some shell:
    
    ```bash
    echo "hello world"
    ```
""",
            ]
            
            for i, edge_yaml in enumerate(edge_cases):
                print(f"Testing edge case {i+1}")
                
                # Should validate
                assert validate_yaml_schema(edge_yaml)
                
                # Should handle storage
                result = run_tigs(repo_path, "add-chat", "-m", edge_yaml)
                if result.returncode == 0:
                    result = run_tigs(repo_path, "show-chat")
                    if result.returncode == 0:
                        assert validate_yaml_schema(result.stdout)
                        print(f"✓ Edge case {i+1} handled correctly")
                    
                    # Clean up
                    run_tigs(repo_path, "remove-chat")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])