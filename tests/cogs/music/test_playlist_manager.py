from unittest.mock import AsyncMock, MagicMock

import pytest
from discord import VoiceClient
from discord.ext.commands import CommandError, Context

from keion.cogs.music.voice_manager import VoiceManager


@pytest.fixture
def voice_manager():
    return VoiceManager()


@pytest.mark.asyncio
async def test_ensure_voice_no_voice():
    """Test ensure_voice when user is not in a voice channel."""
    vm = VoiceManager()

    # Mock context
    context = MagicMock(spec=Context)
    context.voice_client = None
    context.author.voice = None

    with pytest.raises(CommandError):
        await vm.ensure_voice(context)


@pytest.mark.asyncio
async def test_ensure_voice_different_channel():
    """Test ensure_voice when user is in different channel than bot."""
    vm = VoiceManager()

    # Mock context and voice states
    context = MagicMock(spec=Context)
    context.voice_client = MagicMock(spec=VoiceClient)
    context.author.voice = MagicMock()
    context.voice_client.channel = MagicMock()
    context.author.voice.channel = MagicMock()

    # Set different channels
    context.voice_client.channel.id = 1
    context.author.voice.channel.id = 2

    with pytest.raises(CommandError):
        await vm.ensure_voice(context)


@pytest.mark.asyncio
async def test_disconnect():
    """Test disconnecting from voice channel."""
    vm = VoiceManager()

    # Mock voice client
    voice_client = AsyncMock(spec=VoiceClient)
    guild_id = 123
    vm.voice_clients[guild_id] = voice_client

    await vm.disconnect(guild_id)

    voice_client.disconnect.assert_called_once()
    assert guild_id not in vm.voice_clients
