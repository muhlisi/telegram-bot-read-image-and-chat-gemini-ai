# Telegram Bot Read Text in an Image and can chat with you as Gemini AI

Telegram Bot that can read text in an image using **Google Vision** and you can chat with **Gemini AI** and save chat history using **PostgreSQL**, for each user.

## Prerequisites :
### Install module
Install python module
I am using [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
```
pip install python-telegram-bot pandas psycopg2 google-cloud-vision google-generativeai
```

### Get Google Gemini AI API
You can get the gemini ai API KEY at [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

### Get Google Vision API Key
You can read the setup here [https://cloud.google.com/vision/docs/setup](https://cloud.google.com/vision/docs/setup)
Google Vision need **Billing Activated** but its still free with condition, read it here [https://cloud.google.com/vision/pricing/](https://cloud.google.com/vision/pricing/)
To get your clientid json file, read here [https://daminion.net/docs/how-to-get-google-cloud-vision-api-key/](https://daminion.net/docs/how-to-get-google-cloud-vision-api-key/)
or watch [Youtube - Google Cloud Vision API For Image Annotation in Python](https://www.youtube.com/watch?v=1EBhUDAlrYU)

## Setup your database
Create database (I am using postgreSQL in here) or use existing database (you also need schema if you use postgreSQL), and create table :
```
-- my shema = telebot
-- table name = chat_session
CREATE TABLE telebot.chat_session (
	chat_id varchar NOT NULL,
	role varchar NOT NULL,
  parts varchar NOT NULL,
  timestamp timestamp NOT NULL
);
```

## References
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Youtube - Setup Gemini AI using Python](https://www.youtube.com/watch?v=CaxPa1FuHx4&t=2s)
- [Youtube - Google Cloud Vision API For Image Annotation in Python](https://www.youtube.com/watch?v=1EBhUDAlrYU)
- [Sample code conversationbot2.py](https://docs.python-telegram-bot.org/en/stable/examples.conversationbot2.html)
