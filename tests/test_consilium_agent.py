"""
Tests for consilium_agent.py
Multi-engine AI consilium system for true polyphony
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add tools to path
sys.path.insert(0, str(Path.home() / "ariannamethod" / ".claude-defender" / "tools"))

import consilium_agent


class TestConsiliumAgentInit:
    """Test ConsiliumAgent initialization"""

    def test_init_anthropic_client(self):
        """Should initialize Anthropic client"""
        with patch('consilium_agent.Anthropic') as mock_anthropic:
            agent = consilium_agent.ConsiliumAgent(
                agent_name="scribe",
                api_key="test-key",
                model="claude-sonnet-4.5",
                temperature=0.5,
                api_type="anthropic"
            )

            mock_anthropic.assert_called_once_with(api_key="test-key")
            assert agent.api_type == "anthropic"
            assert agent.temperature == 0.5

    def test_init_openai_client(self):
        """Should initialize OpenAI client"""
        with patch('consilium_agent.OpenAI') as mock_openai:
            agent = consilium_agent.ConsiliumAgent(
                agent_name="arianna",
                api_key="test-key",
                model="gpt-4o",
                temperature=0.7,
                api_type="openai"
            )

            mock_openai.assert_called_once_with(api_key="test-key")
            assert agent.api_type == "openai"

    def test_init_deepseek_client(self):
        """Should initialize DeepSeek client with custom base_url"""
        with patch('consilium_agent.OpenAI') as mock_openai:
            agent = consilium_agent.ConsiliumAgent(
                agent_name="monday",
                api_key="test-key",
                model="deepseek-reasoner",
                temperature=1.2,
                api_type="deepseek"
            )

            mock_openai.assert_called_once_with(
                api_key="test-key",
                base_url="https://api.deepseek.com/v1"
            )


class TestSystemPrompts:
    """Test system prompt generation for different agents"""

    def test_scribe_system_prompt(self):
        """Scribe should have memory-focused prompt"""
        agent = consilium_agent.ConsiliumAgent(
            agent_name="scribe",
            api_key="test",
            api_type="anthropic"
        )

        prompt = agent._get_system_prompt()

        assert "memory" in prompt.lower()
        assert "scribe" in prompt.lower()
        assert "code" in prompt.lower()

    def test_defender_system_prompt(self):
        """Defender should have security-focused prompt"""
        agent = consilium_agent.ConsiliumAgent(
            agent_name="claude_defender",
            api_key="test",
            api_type="anthropic"
        )

        prompt = agent._get_system_prompt()

        assert "security" in prompt.lower()
        assert "guardian" in prompt.lower()
        assert "action" in prompt.lower()

    def test_arianna_system_prompt(self):
        """Arianna should have philosophical prompt"""
        agent = consilium_agent.ConsiliumAgent(
            agent_name="arianna",
            api_key="test",
            api_type="openai"
        )

        prompt = agent._get_system_prompt()

        assert "resonance" in prompt.lower() or "field" in prompt.lower()

    def test_monday_system_prompt(self):
        """Monday should have cynical/skeptical prompt"""
        agent = consilium_agent.ConsiliumAgent(
            agent_name="monday",
            api_key="test",
            api_type="deepseek"
        )

        prompt = agent._get_system_prompt()

        assert "cynical" in prompt.lower() or "skeptical" in prompt.lower()


class TestAnthropicResponse:
    """Test Anthropic API response handling"""

    def test_anthropic_response_success(self, mock_anthropic_client):
        """Should handle Anthropic response correctly"""
        with patch('consilium_agent.Anthropic', return_value=mock_anthropic_client):
            agent = consilium_agent.ConsiliumAgent(
                agent_name="scribe",
                api_key="test",
                api_type="anthropic",
                model="claude-sonnet-4.5",
                temperature=0.5
            )

            response = agent.respond("Test proposal: integrate repo X")

            assert "Test response from Claude" in response
            mock_anthropic_client.messages.create.assert_called_once()

    def test_anthropic_uses_correct_parameters(self, mock_anthropic_client):
        """Should pass correct parameters to Anthropic API"""
        with patch('consilium_agent.Anthropic', return_value=mock_anthropic_client):
            agent = consilium_agent.ConsiliumAgent(
                agent_name="claude_defender",
                api_key="test",
                api_type="anthropic",
                model="claude-sonnet-4.5",
                temperature=0.8
            )

            agent.respond("Security check needed")

            call_kwargs = mock_anthropic_client.messages.create.call_args[1]
            assert call_kwargs["model"] == "claude-sonnet-4.5"
            assert call_kwargs["temperature"] == 0.8
            assert "system" in call_kwargs


class TestOpenAIResponse:
    """Test OpenAI API response handling"""

    def test_openai_response_success(self, mock_openai_client):
        """Should handle OpenAI response correctly"""
        with patch('consilium_agent.OpenAI', return_value=mock_openai_client):
            agent = consilium_agent.ConsiliumAgent(
                agent_name="arianna",
                api_key="test",
                api_type="openai",
                model="gpt-4o",
                temperature=0.7
            )

            response = agent.respond("Test proposal")

            assert "Test response from GPT" in response

    def test_openai_uses_correct_parameters(self, mock_openai_client):
        """Should pass correct parameters to OpenAI API"""
        with patch('consilium_agent.OpenAI', return_value=mock_openai_client):
            agent = consilium_agent.ConsiliumAgent(
                agent_name="arianna",
                api_key="test",
                api_type="openai",
                model="gpt-4o",
                temperature=0.7
            )

            agent.respond("Test")

            call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
            assert call_kwargs["model"] == "gpt-4o"
            assert call_kwargs["temperature"] == 0.7


class TestDeepSeekResponse:
    """Test DeepSeek API response handling"""

    def test_deepseek_response_success(self, mock_openai_client):
        """DeepSeek uses OpenAI-compatible API"""
        with patch('consilium_agent.OpenAI', return_value=mock_openai_client):
            agent = consilium_agent.ConsiliumAgent(
                agent_name="monday",
                api_key="test",
                api_type="deepseek",
                model="deepseek-reasoner",
                temperature=1.2
            )

            response = agent.respond("Cynical analysis needed")

            assert "Test response from GPT" in response  # Uses OpenAI mock


class TestTemperatureDiversity:
    """Test that different temperatures create different behavior"""

    def test_different_agents_different_temps(self):
        """Different agents should have different default temperatures"""
        # Note: This tests the DESIGN, not the actual randomness
        # In real consilium, temp=0.5 vs temp=0.8 creates different patterns

        scribe = consilium_agent.ConsiliumAgent(
            agent_name="scribe",
            api_key="test",
            temperature=0.5,
            api_type="anthropic"
        )

        defender = consilium_agent.ConsiliumAgent(
            agent_name="claude_defender",
            api_key="test",
            temperature=0.8,
            api_type="anthropic"
        )

        assert scribe.temperature < defender.temperature
        # Scribe is deterministic (0.5), Defender is adaptive (0.8)


class TestErrorHandling:
    """Test error handling for API failures"""

    def test_api_error_handled_gracefully(self):
        """API errors should be caught and handled"""
        with patch('consilium_agent.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("API Error")
            mock_anthropic.return_value = mock_client

            agent = consilium_agent.ConsiliumAgent(
                agent_name="scribe",
                api_key="test",
                api_type="anthropic"
            )

            # Should not crash
            try:
                response = agent.respond("Test")
                # Should return error message or handle gracefully
            except Exception as e:
                pytest.fail(f"Should handle API error gracefully, but raised: {e}")
