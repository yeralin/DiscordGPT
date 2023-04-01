# TelegramGPT
![Logo](./DiscordGPT.png)
## Simple Telegram bot tied with ChatGPT language model.

### Installation
1. Clone this repository:
`git clone https://github.com/yeralin/DiscordGPT.git`
2. Install the required dependencies (required python version >3.7):
`pip install -r requirements.txt`
3. Get OpenAI API key (`OPENAI_API_KEY`) and a Discord bot token (`DISCORD_TOKEN`)
4. Create a .env file in the root directory of the project and add the following:
```
OPENAI_API_KEY=<your-openai-api-key>
DISCORD_TOKEN=<your-discord-bot-token>
```
> Make sure to replace <your-openai-api-key> and <your-discord-bot-token> with your actual API key and token.

### Usage
To start the bot, run: `python bot.py`

Once the bot is running, you can interact with it by sending messages to it on Discord.

### How to get OpenAI API key
1. Go to the OpenAI website (https://openai.com/) and click on the "Get started for free" button.
2. Create an account by filling out the registration form.
3. Once you've created an account, you'll need to add a payment method to your account to get access to the API.
4. Once you have added a payment method, go to the "API Keys" tab in your OpenAI account dashboard.
5. Click on the "Create API Key" button and give your key a name.
6. Copy the API key that is generated and store it somewhere safe.
7. Store the API key under `.env` file as `OPENAI_API_KEY=<your-openai-api-key>`
> OpenAI offers a free trial with $200 in credits, so you won't be charged if you stay within that limit.
  
### How to get Discord Bot token
1. Go to the Discord Developer Portal.
2. Click the "New Application" button, and give your application a name.
3. Click on your application and go to the "Bot" tab in the left sidebar.
4. Click the "Add Bot" button to create a bot account for your application.
5. Scroll down to the "Token" section and click the "Copy" button to copy your bot token to the clipboard.
6. Save the token in a secure location and never share it with anyone.

### License

This project is licensed under the MIT License - see the LICENSE file for details.
