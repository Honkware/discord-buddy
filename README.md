# Discord Buddy Package 🤖

Create your very own AI-powered Discord buddy with a unique personality using the Discord Buddy package! Follow the simple steps below to get started.

## 🚀 Creating a Discord Buddy

### Step 1: Create a New Application

- Open Discord and go to the [Developer Portal](https://discord.com/developers/applications).
- Click the "**New Application**" button to create a new application.

### Step 2: Name Your Application

- Give the application a name (this does not have to be unique).
- Click "**Create**" to proceed.

### Step 3: Add a Bot to the Application

- In the application's settings, go to the "**Bot**" tab.
- Click the "**Add Bot**" button to create a bot for the application.

### Step 4: Set Intents for the Bot

- In the "**Bot**" tab, scroll down to the "**Privileged Gateway Intents**" section.
- Enable the "**Server Members Intent**" and "**Message Content Intent**" options.

### Step 5: Copy the Bot Token

- Copy the bot token by clicking the "**Copy**" button.
- Keep this token safe, as you'll need it later.

### Step 6: Customize Your Bot (Optional)

- Customize your bot's profile picture, username, and other settings as desired.

### Step 7: Generate the Invite Link

- Go to the "**OAuth2**" tab in the application's settings.
- In the "**Scopes**" section, select the "**bot**" option.
- In the "**Bot Permissions**" section, select the permissions you want to grant to the bot (e.g., "Send Messages").
- Copy the generated URL from the "**Scopes**" section. This is the invite link for your bot.

## 🎉 Deploying Your Discord Buddy

- Run the `deploy.py` script to deploy the Discord Buddy package. This script will prompt you for the necessary configuration values, such as the bot token, bot name, and bot personality.

## 🎮 Using Your Discord Buddy

- Use the invite link you generated earlier to invite your Discord Buddy to your server.
- Start a conversation with your Discord Buddy by mentioning it or replying to its messages.
