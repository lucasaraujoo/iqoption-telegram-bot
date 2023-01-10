# iqoption-telegram-bot

This is an automation signals bot for the iqoption platform, with Telegram integration, written in Python. With it, you can send trading signals directly from your mobile phone through Telegram, without having to be stuck in front of a computer.

## Features
1. Send real-time trading signals directly from your Telegram
2. Real-time automatic entries
3. Customizable configuration, through config.txt file
4. Trend and News Analysis
5. Direct integration with iqoption account
6. Binary and Digital options
7. Logs
8. Signal insertion at runtime
9. Use of Thread for better optimization and precision in entries

## Installation
To install and start using the bot, follow the following steps:

1. Clone the repository to your computer.
2. Enter the repository folder: `cd iqoption-telegram-bot`
3. Install dependencies: `pip install -r requirements.txt`
4. Create a bot on Telegram using BotFather and note down your access token
5. Edit the `config.txt` file in the root of the repository and add the following environment variables:

```
TELEGRAM_TOKEN=your_token
TELEGRAM_ID=your_id
```

6. Run the bot: `python AutoBot24h.py` and `Inclusor_Sinais.py`

## Usage
Once the bot is running, you can send commands to it through Telegram.

## Contributing
This is an open-source project and contributions are always welcome! If you find a bug or have an idea for a new feature, create a new issue or submit a pull request.

