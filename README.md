# TelegramGPT
![Logo](./TelegramGPT.png)
## Simple Telegram bot tied with ChatGPT language model.

### Installation
1. Clone this repository:
`git clone https://github.com/yeralin/TelegramGPT.git`
2. Install the required dependencies (required python version >3.7):
`pip install -r requirements.txt`
3. Get OpenAI API key (`OPENAI_API_KEY`) and a Telegram bot token (`TELEGRAM_TOKEN`)
4. Create a .env file in the root directory of the project and add the following:
```
OPENAI_API_KEY=<your-openai-api-key>
TELEGRAM_TOKEN=<your-telegram-bot-token>
```
> Make sure to replace <your-openai-api-key> and <your-telegram-bot-token> with your actual API key and token.

### Usage
To start the bot, run: `python bot.py`

Once the bot is running, you can interact with it by sending messages to it on Telegram.

### Available commands:
* `/system <system-message>` - Sets the system message. If no message is provided, returns the current system message.
* All other messages will be interpreted as messages to the bot.
  
### How to get OpenAI API key
1. Go to the OpenAI website (https://openai.com/) and click on the "Get started for free" button.
2. Create an account by filling out the registration form.
3. Once you've created an account, you'll need to add a payment method to your account to get access to the API.
4. Once you have added a payment method, go to the "API Keys" tab in your OpenAI account dashboard.
5. Click on the "Create API Key" button and give your key a name.
6. Copy the API key that is generated and store it somewhere safe.
7. Store the API key under `.env` file as `OPENAI_API_KEY=<your-openai-api-key>`
> OpenAI offers a free trial with $200 in credits, so you won't be charged if you stay within that limit.
  
### How to get Telegram Bot token
1. Open the Telegram app and search for the BotFather bot.
2. Start a chat with the BotFather and type `/newbot` to create a new bot.
3. Follow the instructions from BotFather to provide a name and username for your bot.
4. Once you have successfully created the bot, BotFather will provide you with a token.
5. Store the token under `.env` file as `TELEGRAM_TOKEN=<your-telegram-bot-token>`

### License

This project is licensed under the MIT License - see the LICENSE file for details.
