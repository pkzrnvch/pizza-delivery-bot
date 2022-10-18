# Pizza delivery bot

This telegram bot was created to allow a pizzeria to collect orders. It works with [Elastic Path](https://www.elasticpath.com) e-commerce platform.

Supported functions:
- Show the list of all available pizzas and other products.
- Show description, picture, and price for a particular pizza.
- Add pizzas to cart.
- Remove pizzas from cart.
- Show cart overview (pizzas, their quantity and cost), cart total cost.
- Collect customer contact and location information and add it to Elastic Path CMS system.
- Calculate delivery cost, notify the worker responsible for deliveries.
- Collect payments for pizza.


## How to install
- Download project files and create virtual environment.
- Create an `.env` file in the project directory. Create a new telegram bot through a [BotFather](https://telegram.me/BotFather) and assign its token to `TG_BOT_TOKEN` variable.
- Set up a [Redis](https://redis.com/) account. After that, create a database, its host, port and password parameters can be found in configuration tab. Assign these values to `REDIS_DB_HOST`, `REDIS_DB_PORT`, `REDIS_DB_PASSWORD` variables respectively.
- Set up an [Elastic Path](https://www.elasticpath.com) account, create a store and add products. Set `ELASTIC_PATH_CLIENT_ID` and `ELASTIC_PATH_CLIENT_SECRET` environment variables.

Example of an `.env` file:
```
TG_BOT_TOKEN='Telegram bot token'
REDIS_DB_HOST='Redis database host'
REDIS_DB_PORT='Redis database port'
REDIS_DB_PASSWORD='Redis database password'
ELASTIC_PATH_CLIENT_ID='Your Elastic Path client ID'
ELASTIC_PATH_CLIENT_SECRET='Your Elastic Path client secret'
YANDEX_GEOCODER_KEY='Your Yandex geocoder key'
PAYMENT_PROVIDER_TOKEN='Your Telegram bot payment provider token'
```

Python3 should already be installed. Use pip (or pip3, in case of conflict with Python2) to install dependencies:
```
pip install -r requirements.txt
```

### Usage

To run the bots locally use the following commands from the project directory:
```
python bot.py
```

### Project Goals

The code is written for educational purposes on online-course for web-developers [Devman](https://dvmn.org).