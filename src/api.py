"""A package that allows quick creation of a Discord bot hosted on Steamship."""

from typing import Type, Optional, Dict, Any
import uuid
import asyncio
import threading
import concurrent.futures
from util import filter_blocks_for_prompt_length
from steamship.invocable import Config, post, PackageService
from steamship import SteamshipError, File, Block, Tag, PluginInstance
from steamship.data.tags.tag_constants import TagKind, RoleTag
from pydantic import Field
import discord
from discord.ext import commands

class DiscordBuddyConfig(Config):
    """Config object containing required parameters to initialize a MyPackage instance."""

    bot_name: str = Field(description='What the bot should call itself')
    bot_personality: str = Field(description='Complete the sentence, "The bot\'s personality is _." Writing a longer, more detailed description will yield less generic results.')
    bot_token: str = Field(description="The secret token for your Discord bot")
    use_gpt4: bool = Field(False, description="If True, use GPT-4 instead of GPT-3.5 to generate responses. GPT-4 creates better responses at higher cost and with longer wait times.")
    
class DiscordBuddy(PackageService):
    """Discord Buddy package. Stores individual chats in Steamship Files for chat history."""

    config: DiscordBuddyConfig
    gpt4: Optional[PluginInstance]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = "gpt-4" if self.config.use_gpt4 else "gpt-3.5-turbo"
        self.gpt4 = None
        intents = discord.Intents.default()
        self.bot = commands.Bot(command_prefix="", intents=intents)  # Use discord.ext.commands.Bot

        self.bot.add_listener(self.on_ready)
        self.bot.add_listener(self.on_message, 'on_message')

    async def on_ready(self):
        print(f'Logged in as {self.bot.user}')

    async def on_message(self, message: discord.Message):
        # Ignore messages sent by the bot itself
        if message.author == self.bot.user:
            return

        # Check if the message mentions the bot
        mentioned = self.bot.user in message.mentions
        is_reply = message.reference is not None
        is_reply_to_bot = is_reply and message.reference.resolved.author == self.bot.user
        if mentioned or is_reply_to_bot:
            # Extract the message content
            message_text = message.content

            # If the message is a reply, include the content of the replied-to message
            if is_reply:
                replied_to_message = await message.channel.fetch_message(message.reference.message_id)
                replied_to_author = replied_to_message.author.display_name
                message_text = f"{replied_to_author} said: {replied_to_message.content}\n{message.author.display_name} replied: {message_text}"

            # Process the message and generate a response
            chat_session_id = message.channel.id
            message_id = message.id
            try:
                response = self.prepare_response(message_text, chat_session_id, message_id)
            except SteamshipError as e:
                response = self.response_for_exception(e)
            await message.channel.send(response)
            
    def start_bot(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.bot.start(self.config.bot_token))
        loop.close()

    @post("start", public=True)
    def start(self) -> Dict[str, Any]:
        """Start the Discord bot."""
        print("Starting bot...")  # Debugging print statement

        # Start the bot in a new thread using a ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self.start_bot)
            print("Bot started in a new thread")

        return {"status": "Bot started"}


    @post("stop", public=True)
    def stop(self) -> Dict[str, Any]:
        """Stop the Discord bot."""
        self.bot.close()
        return {"status": "Bot stopped"}
    
    def get_gpt4(self) -> PluginInstance:
        if self.gpt4 is not None:
            return self.gpt4
        else:
            self.gpt4 = self.client.use_plugin("gpt-4", config={"model": self.model, "temperature": 0.8})
            return self.gpt4

    @classmethod
    def config_cls(cls) -> Type[Config]:
        """Return the Configuration class."""
        return DiscordBuddyConfig

    @post("answer", public=True)
    def answer(self, question: str, chat_session_id: Optional[str] = None) -> Dict[str, Any]:
        """Endpoint that implements the contract for Steamship embeddable chat widgets. This is a PUBLIC endpoint since these webhooks do not pass a token."""
        if not chat_session_id:
            chat_session_id = "default"
        
        message_id = str(uuid.uuid4())

        try:
            response = self.prepare_response(question, chat_session_id, message_id)
        except SteamshipError as e:
            response = self.response_for_exception(e)

        return {
            "answer": response,
            "sources": [],
            "is_plausible": True,
        }

    def prepare_response(self, message_text: str, chat_id: int, message_id: int) -> Optional[str]:
        """Use the LLM to prepare the next response by appending the user input to the file and then generating."""
        chat_file = self.get_file_for_chat(chat_id)

        if self.includes_message(chat_file, message_id):
            return None

        chat_file.append_block(
            text=message_text,
            tags=[Tag(kind=TagKind.ROLE, name=RoleTag.USER), Tag(kind="message_id", name=str(message_id))]
        )
        chat_file.refresh()
        # Limit total tokens passed to fit in context window
        max_tokens = self.max_tokens_for_model()
        retained_blocks = filter_blocks_for_prompt_length(max_tokens, chat_file.blocks)
        generate_task = self.get_gpt4().generate(
            input_file_id=chat_file.id,
            input_file_block_index_list=retained_blocks,
            append_output_to_file=True,
            output_file_id=chat_file.id
        )

        generate_task.wait()
        return generate_task.output.blocks[0].text

    def includes_message(self, file: File, message_id: int) -> bool:
        """Determine if the message ID has already been processed in this file by checking Block tags."""
        for block in file.blocks:
            for tag in block.tags:
                if tag.kind == "message_id" and tag.name == str(message_id):
                    return True
        return False

    def get_file_for_chat(self, chat_id: int) -> File:
        """Find the File associated with this chat id, or create it."""
        file_handle = str(chat_id)
        try:
            file = File.get(self.client, handle=file_handle)
        except:
            file = self.create_new_file_for_chat(file_handle)
        return file

    def create_new_file_for_chat(self, file_handle: str) -> File:
        """Create a new File for this chat id, beginning with the system prompt based on name and personality."""
        return File.create(
            self.client,
            handle=file_handle,
            blocks=[
                Block(
                    text=f"Your name is {self.config.bot_name}. Your personality is {self.config.bot_personality}.",
                    tags=[Tag(kind=TagKind.ROLE, name=RoleTag.SYSTEM)]
                    )
                ]
            )
        
    def response_for_exception(self, e: Optional[Exception]) -> str:
        if e is None:
            return "An unknown error happened. Please reach out to support@steamship.com or on our discord at https://steamship.com/discord"

        if "usage limit" in f"{e}":
            return "You have reached the introductory limit of Steamship. Visit https://steamship.com/account/plan to sign up for a plan."

        return f"An error happened while creating a response: {e}"

    def max_tokens_for_model(self) -> int:
        if self.config.use_gpt4:
            # Use 7800 instead of 8000 as buffer for different counting
            return 7800 - self.get_gpt4().config['max_tokens']
        else:
            # Use 4000 instead of 4097 as buffer for different counting
            return 4097 - self.get_gpt4().config['max_tokens']


