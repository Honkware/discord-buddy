import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from steamship import Steamship
from steamship.cli.cli import deploy
from steamship.data.manifest import Manifest

from src.api import DiscordBuddy, DiscordBuddyConfig

if __name__ == "__main__":
    # Deploy the package
    try:
        deploy()
    except SystemExit as err:
        if err.code != 0:
            print("An error occurred during deployment:", err)
            exit(1)
        else:
            print("Deployment was successful.")

    # Load the manifest
    manifest = Manifest.load_manifest()

    # Create a Steamship client
    client = Steamship(workspace="discord-buddy")

    # Get configuration values from the user
    bot_name = input("Enter the bot name: ")
    bot_personality = input("Enter the bot's personality description: ")
    bot_token = input("Paste your bot token: ")
    use_gpt4 = input("Use GPT-4 instead of GPT-3.5? (yes/no): ").lower() == "yes"

    # Create the configuration dictionary
    config = {
        "bot_name": bot_name,
        "bot_personality": bot_personality,
        "bot_token": bot_token,
        "use_gpt4": use_gpt4,
    }

    # Use the package with the provided configuration
    bot = client.use(
        package_handle=manifest.handle,
        version=manifest.version,
        instance_handle=manifest.version.replace(".", "-"),
        config=config
    )

    # Wait for initialization
    bot.wait_for_init()

    # Ask the user whether to start or stop the bot
    action = input("Enter 'start' to start the bot or 'stop' to stop the bot: ")
    if action.lower() == "start":
        # Invoke the 'start' endpoint to start the bot
        bot.invoke("start")
    elif action.lower() == "stop":
        # Invoke the 'stop' endpoint to stop the bot
        bot.invoke("stop")
    else:
        print("Invalid action. Please enter 'start' or 'stop'.")