import pandas as pd
import psycopg2

# for database
dbhost = "localhost"
dbase = "db_sibro"
dbuser = "sibro"
dbpass = "12345"

query_string = f"""
SELECT
    COUNT(*)
FROM
    telebot.chat_session
WHERE
    chat_id = '173723690'
"""

# connect to database
conn = psycopg2.connect(host=dbhost, database=dbase, user=dbuser, password=dbpass)

# read query by pandas
df = pd.read_sql_query(query_string, conn)

print(df['count'][0])