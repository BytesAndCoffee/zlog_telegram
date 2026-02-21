from datetime import timedelta
import pymysql as sql
from time import sleep
from zlog_telegram import ZlogTelegram
from dotenv import load_dotenv
import os
load_dotenv()

# Access environment variables
host = os.getenv('DB_HOST')
password = os.getenv('DB_PASSWORD')
token = os.getenv('TOKEN')
chat_id = os.getenv('CHAT_ID')
username = os.getenv('DB_USERNAME')


conn = sql.connect(
    host=host,
    user=username,
    password=password,
    db='znc',
    cursorclass=sql.cursors.DictCursor,
    ssl={'ca': '/etc/ssl/certs/ca-certificates.crt'}
)

tg_last = "SELECT tg_id FROM inbound_log ORDER BY id DESC LIMIT 1;"
with conn.cursor() as cur:
    cur.execute(tg_last)
    conn.commit()
    res = cur.fetchone()
    # print(res['tg_id'])
    tp = ZlogTelegram(token, chat_id, res['tg_id'])


try:
    with conn.cursor() as cur:
        while True:
            s = "SELECT * FROM push;"
            cur.execute(s)
            conn.commit()
            res = cur.fetchone()
            rep = tp.fetch()
            if rep is not None:
                for msg in rep:
                    if msg.text.startswith('context'):
                        tokens = msg.text.split()
                        s = '''SELECT * FROM logs WHERE id = %s;'''
                        cur.execute(s, (tokens[1],))
                        conn.commit()
                        res = cur.fetchone()
                        if res:
                            window = timedelta(minutes=10)
                            start_time = res['created_at'] - window
                            end_time = res['created_at']

                            s = '''SELECT * FROM logs WHERE (created_at BETWEEN %s AND %s) AND `window` = %s;'''
                            cur.execute(s, (start_time, end_time, res['window']))
                            conn.commit()
                            result = cur.fetchall()
                            msg = ''
                            for line in result:
                                msg += f"{line['nick']}: {line['message']} \n"
                            tp.push(msg)
                        else:
                            tp.push('no such message')
                    elif msg.text.startswith('reply'):
                        tokens = msg.text.split()
                        s = '''SELECT * FROM logs WHERE id = %s;'''
                        cur.execute(s, (tokens[1],))
                        conn.commit()
                        res = cur.fetchone()
                        if res:
                            s = '''INSERT INTO inbound (user, network, `window`, type, nick, message) VALUES (%s, %s, %s, %s, %s, %s);'''
                            cur.execute(s, (res['user'], res['network'], res['window'], 'msg', res['nick'], ' '.join(tokens[2:])))
                            s = '''INSERT INTO inbound_log (user, network, `window`, type, nick, message) VALUES (%s, %s, %s, %s, %s, %s);'''
                            cur.execute(s, (res['user'], res['network'], res['window'], 'msg', res['nick'], ' '.join(tokens[2:])))
                        else:
                            tp.push('no such message')
            if res:
                # print(res['id'])
                chat = (res['window'], res['nick'])
                if chat in tp.chats:
                    if chat != tp.active:
                        tp.active = chat
                    tp.push(f"{res['message']} \nreply: {res['id']}")
                else:
                    tp.add_chat(*chat)
                    tp.push(f"{res['message']} \nreply: {res['id']}")
                s = 'DELETE FROM push WHERE id={};'.format(res['id'])
                cur.execute(s)
                conn.commit()
            else:
                sleep(5)
finally:
    conn.close()

