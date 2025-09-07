"""Integration tests using real Claude Code logs via cligent."""

import subprocess
from pathlib import Path

import pytest
import yaml
from cligent import ChatParser

from tigs.cli import main


class TestCligentIntegration:
    """Test integration with real Claude Code logs."""
    
    def test_claude_logs_available(self, claude_logs):
        """Test that we can access real Claude Code logs."""
        if not claude_logs:
            pytest.skip("No Claude logs available in test environment")
        assert len(claude_logs) >= 1, "Need at least one accessible Claude Code log for testing"
        
        for log_id, info in claude_logs:
            assert info['accessible'] is True
            assert 'size' in info
            assert info['size'] > 0
            assert 'project' in info
    
    def test_parse_real_claude_log(self, claude_logs):
        """Test parsing a real Claude Code log."""
        if not claude_logs:
            pytest.skip("No Claude logs available in test environment")
        log_id, _ = claude_logs[0]
        parser = ChatParser()
        
        # Parse the log
        chat = parser.parse(log_id)
        assert len(chat.messages) > 0
        
        # Verify message structure
        first_message = chat.messages[0]
        assert hasattr(first_message, 'role')
        assert hasattr(first_message, 'content')
        assert first_message.role.value in ['user', 'assistant', 'system']
        assert isinstance(first_message.content, str)
        assert len(first_message.content) > 0
    
    def test_cligent_compose_yaml_format(self, claude_logs):
        """Test that cligent produces valid YAML in tigs.chat/v1 format."""
        if not claude_logs:
            pytest.skip("No Claude logs available in test environment")
        log_id, _ = claude_logs[0]
        parser = ChatParser()
        
        # Parse and select some messages
        chat = parser.parse(log_id)
        message_count = min(5, len(chat.messages))  # Select up to 5 messages
        parser.select(log_id, list(range(message_count)))
        
        # Compose YAML
        yaml_content = parser.compose()
        
        # Verify it's valid YAML
        data = yaml.safe_load(yaml_content)
        assert isinstance(data, dict)
        
        # Verify schema
        assert data.get('schema') == 'tigs.chat/v1'
        assert 'messages' in data
        assert isinstance(data['messages'], list)
        assert len(data['messages']) == message_count
        
        # Verify message structure
        for msg in data['messages']:
            assert isinstance(msg, dict)
            assert 'role' in msg
            assert 'content' in msg
            assert msg['role'] in ['user', 'assistant', 'system']
            assert isinstance(msg['content'], str)
    
    def test_store_real_claude_chat_in_git(self, runner, git_repo, claude_logs, git_notes_helper):
        """Test storing real Claude Code chat content in Git notes."""
        if not claude_logs:
            pytest.skip("No Claude logs available in test environment")
        log_id, _ = claude_logs[0]
        parser = ChatParser()
        
        # Parse and select first 3 messages
        chat = parser.parse(log_id)
        message_indices = list(range(min(3, len(chat.messages))))
        parser.select(log_id, message_indices)
        
        # Get YAML content
        yaml_content = parser.compose()
        
        # Store in Git notes using tigs
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", yaml_content])
        assert result.exit_code == 0
        commit_sha = result.output.split(":")[-1].strip()
        
        # Verify Git note was created with correct content
        assert git_notes_helper.verify_note_exists(git_repo, commit_sha)
        stored_content = git_notes_helper.get_note_content(git_repo, commit_sha)
        assert git_notes_helper.validate_yaml_schema(stored_content)
        
        # Verify we can retrieve the content (handle Git whitespace normalization)
        result = runner.invoke(main, ["--repo", str(git_repo), "show-chat"])
        assert result.exit_code == 0
        assert git_notes_helper.validate_yaml_schema(result.output)
        # Verify essential content from original YAML
        retrieved_data = yaml.safe_load(result.output)
        original_data = yaml.safe_load(yaml_content)
        assert retrieved_data['schema'] == original_data['schema']
        assert len(retrieved_data['messages']) == len(original_data['messages'])
        
        # Parse stored content and verify message count
        stored_data = yaml.safe_load(stored_content)
        assert len(stored_data['messages']) == len(message_indices)
    
    def test_multiple_claude_logs_workflow(self, runner, multi_commit_repo, claude_logs, git_notes_helper):
        """Test workflow with multiple Claude Code logs and commits."""
        if len(claude_logs) < 2:
            pytest.skip("Need at least 2 Claude Code logs for multi-log testing")
            
        git_repo, commits = multi_commit_repo
        parser = ChatParser()
        
        # Use first 2 logs and commits only (more reliable)
        stored_contents = []
        
        for i in range(2):
            log_id, _ = claude_logs[i]
            commit_sha = commits[i]
            
            # Use simple selection (first 2 messages)
            chat = parser.parse(log_id)
            if len(chat.messages) < 2:
                continue
                
            parser.clear_selection()
            parser.select(log_id, [0, 1])
            yaml_content = parser.compose()
            stored_contents.append((commit_sha, yaml_content))
            
            # Store to specific commit
            result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", commit_sha, "-m", yaml_content])
            assert result.exit_code == 0
            
            # Verify storage
            assert git_notes_helper.verify_note_exists(git_repo, commit_sha)
            stored_content = git_notes_helper.get_note_content(git_repo, commit_sha)
            assert git_notes_helper.validate_yaml_schema(stored_content)
        
        # Verify all stored chats are accessible
        for commit_sha, expected_content in stored_contents:
            result = runner.invoke(main, ["--repo", str(git_repo), "show-chat", commit_sha])
            assert result.exit_code == 0
            assert git_notes_helper.validate_yaml_schema(result.output)
    
    def test_large_claude_conversation(self, runner, git_repo, claude_logs, git_notes_helper):
        """Test handling large conversations from Claude Code logs."""
        if not claude_logs:
            pytest.skip("No Claude logs available in test environment")
        # Find the largest available log
        largest_log = max(claude_logs, key=lambda x: x[1]['size'])
        log_id, info = largest_log
        
        parser = ChatParser()
        chat = parser.parse(log_id)
        
        # Select a substantial portion of messages (up to 20)
        message_count = min(20, len(chat.messages))
        parser.select(log_id, list(range(message_count)))
        
        yaml_content = parser.compose()
        
        # Verify YAML is large and valid
        assert len(yaml_content) > 1000  # Should be substantial
        data = yaml.safe_load(yaml_content)
        assert len(data['messages']) == message_count
        
        # Store in Git
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", yaml_content])
        assert result.exit_code == 0
        commit_sha = result.output.split(":")[-1].strip()
        
        # Verify large content is stored and retrieved correctly
        stored_content = git_notes_helper.get_note_content(git_repo, commit_sha)
        assert git_notes_helper.validate_yaml_schema(stored_content)
        
        result = runner.invoke(main, ["--repo", str(git_repo), "show-chat"])
        assert result.exit_code == 0
        assert git_notes_helper.validate_yaml_schema(result.output)
        # Verify it's substantial content
        assert len(result.output) > 1000  # Should be substantial
    
    def test_claude_log_error_handling(self, runner, git_repo):
        """Test error handling with invalid log IDs."""
        parser = ChatParser()
        
        # Test with non-existent log ID
        try:
            chat = parser.parse("nonexistent-log-id")
            # If no exception, should have empty or minimal content
            assert len(chat.messages) == 0 or chat.messages is None
        except Exception:
            # Expected - should handle gracefully
            pass
        
        # Test storing invalid/empty content should still work
        empty_yaml = "schema: tigs.chat/v1\nmessages: []"
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", empty_yaml])
        assert result.exit_code == 0
        
        # Should be able to retrieve empty content
        result = runner.invoke(main, ["--repo", str(git_repo), "show-chat"])
        assert result.exit_code == 0
        assert result.output == empty_yaml
    
    def test_yaml_schema_compliance_with_real_data(self, claude_logs, git_notes_helper):
        """Test that all real Claude Code data complies with schema when processed."""
        if not claude_logs:
            pytest.skip("No Claude logs available in test environment")
        parser = ChatParser()
        
        for log_id, _ in claude_logs[:2]:  # Test first 2 logs
            chat = parser.parse(log_id)
            if len(chat.messages) == 0:
                continue
                
            # Test different message selection sizes
            for size in [1, min(3, len(chat.messages)), min(10, len(chat.messages))]:
                parser.clear_selection()
                parser.select(log_id, list(range(size)))
                yaml_content = parser.compose()
                
                # Verify schema compliance
                assert git_notes_helper.validate_yaml_schema(yaml_content)
                
                # Verify parseable
                data = yaml.safe_load(yaml_content)
                assert data['schema'] == 'tigs.chat/v1'
                assert len(data['messages']) == size
                
                # Verify all messages have required fields
                for msg in data['messages']:
                    assert 'role' in msg
                    assert 'content' in msg
                    assert isinstance(msg['content'], str)
                    assert msg['role'] in ['user', 'assistant', 'system']
    
    def test_cligent_selection_and_composition(self, claude_logs):
        """Test cligent selection and composition functionality."""
        if not claude_logs:
            pytest.skip("No Claude Code logs available")
            
        log_id, _ = claude_logs[0]
        parser = ChatParser()
        chat = parser.parse(log_id)
        
        if len(chat.messages) < 3:
            pytest.skip("Need at least 3 messages for selection testing")
        
        # Test selecting first 3 messages (more reliable)
        selected_indices = [0, 1, 2]
        parser.select(log_id, selected_indices)
        
        yaml_content = parser.compose()
        data = yaml.safe_load(yaml_content)
        
        # Should have exactly 3 messages
        assert len(data['messages']) == 3
        
        # Verify basic structure
        for msg in data['messages']:
            assert 'role' in msg
            assert 'content' in msg
            assert len(msg['content']) > 0
    
    @pytest.mark.parametrize("message_count", [1, 3, 10])
    def test_different_message_counts(self, claude_logs, message_count):
        """Test composition with different message counts."""
        if not claude_logs:
            pytest.skip("No Claude Code logs available")
            
        log_id, _ = claude_logs[0]
        parser = ChatParser()
        chat = parser.parse(log_id)
        
        if len(chat.messages) < message_count:
            pytest.skip(f"Need at least {message_count} messages")
        
        parser.select(log_id, list(range(message_count)))
        yaml_content = parser.compose()
        
        data = yaml.safe_load(yaml_content)
        assert data['schema'] == 'tigs.chat/v1'
        assert len(data['messages']) == message_count
        
        # Verify all messages are valid
        for msg in data['messages']:
            assert 'role' in msg
            assert 'content' in msg
            assert len(msg['content']) > 0