# -*- coding: utf-8 -*-
import telebot
import json
import time
import threading
import random
import re
from datetime import datetime

try:
    import requests
except ImportError:
    import subprocess
    subprocess.call(['pip', 'install', 'requests', '--break-system-packages'])
    import requests

# ══════════════════════════════════════
#         SETTINGS
# ══════════════════════════════════════
TOKEN   = '8642537837:AAFdvNHqy9_E07ygKcCCjJNn7RVXWL3lNE8'
CHAT_ID = '-1003952438399'
GITHUB  = 'araavsirgcom-dev'
REPO    = 'quiz-bank'
BRANCH  = 'main'
# ══════════════════════════════════════

BASE_URL = f'https://raw.githubusercontent.com/{GITHUB}/{REPO}/{BRANCH}'

bot = telebot.TeleBot(TOKEN)

quiz_results           = {}
is_quiz_on             = False
current_correct_answer = None
quiz_lock              = threading.Lock()


def fetch_file(path):
    url = f'{BASE_URL}/{path}'
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.text
        print(f'Fetch failed: {path} -> {r.status_code}')
        return None
    except Exception as e:
        print(f'Network error: {e}')
        return None


def read_menu():
    content = fetch_file('menu.txt')
    if not content:
        return []

    today      = datetime.now().weekday()  # 5=Sat, 6=Sun
    is_weekend = today in [5, 6]

    selections   = []
    weekend_mode = False

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # WEEKEND keyword
        if line.upper() == 'WEEKEND':
            weekend_mode = True
            continue

        parts   = line.split()
        subject = parts[0].lower()

        if len(parts) == 1:
            selections.append({'subject': subject, 'mode': 'all', 'start': 0, 'end': 0, 'count': 0})

        elif len(parts) == 2:
            param = parts[1]
            if '-' in param:
                try:
                    s, e = param.split('-')
                    selections.append({'subject': subject, 'mode': 'range',
                                       'start': int(s), 'end': int(e), 'count': 0})
                except:
                    pass
            else:
                try:
                    count = int(param)
                    mode  = 'random' if count > 0 else 'all'
                    selections.append({'subject': subject, 'mode': mode,
                                       'start': 0, 'end': 0, 'count': count})
                except:
                    pass

        elif len(parts) == 3 and parts[1].lower() == 'random':
            try:
                count = int(parts[2])
                selections.append({'subject': subject, 'mode': 'random',
                                   'start': 0, 'end': 0, 'count': count})
            except:
                pass

    # Weekend mode — sab random ho jaata hai
    if weekend_mode and is_weekend:
        for s in selections:
            s['mode']  = 'random'
            if s['count'] == 0:
                s['count'] = 10

    return selections


def load_questions(sel):
    subject = sel['subject']
    mode    = sel['mode']
    start   = sel.get('start', 0)
    end     = sel.get('end', 0)
    count   = sel.get('count', 0)

    content = fetch_file(f'bank/{subject}.txt')
    if not content:
        return []

    all_q   = []
    skipped = 0

    for line_num, line in enumerate(content.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split('|')
        if len(parts) < 6:
            skipped += 1
            continue
        try:
            correct_idx = int(parts[5].strip())
        except ValueError:
            skipped += 1
            continue
        if correct_idx not in [0, 1, 2, 3]:
            skipped += 1
            continue

        all_q.append({
            'question':    parts[0].strip(),
            'options':     [parts[1].strip(), parts[2].strip(),
                            parts[3].strip(), parts[4].strip()],
            'correct':     correct_idx,
            'explanation': parts[6].strip() if len(parts) >= 7 else 'Sahi jawab!'
        })

    if not all_q:
        return []

    if mode == 'range':
        s        = max(0, start - 1)
        e        = min(len(all_q), end)
        selected = all_q[s:e]
        print(f'{subject}.txt -> Range Q{start}-Q{end} -> {len(selected)} questions')

    elif mode == 'random':
        n        = min(count, len(all_q)) if count > 0 else len(all_q)
        selected = random.sample(all_q, n)
        print(f'{subject}.txt -> Random {n} questions')

    else:
        selected = all_q
        print(f'{subject}.txt -> All {len(selected)} questions')

    return selected


def fmt(text):
    hindi = re.compile(r'[\u0900-\u097F]+')
    words = text.split()
    lines, cur, cur_type = [], [], None
    for w in words:
        t = 'h' if hindi.search(w) else 'e'
        if cur_type is None or t == cur_type:
            cur.append(w)
        else:
            lines.append(' '.join(cur))
            cur = [w]
        cur_type = t
    if cur:
        lines.append(' '.join(cur))
    return '\n'.join(lines)


@bot.poll_answer_handler()
def handle_poll_answer(poll_answer):
    global quiz_results, current_correct_answer
    if not is_quiz_on or current_correct_answer is None:
        return
    uid   = poll_answer.user.id
    uname = poll_answer.user.first_name
    if uid not in quiz_results:
        quiz_results[uid] = {'name': uname, 'score': 0, 'incorrect': 0}
    if poll_answer.option_ids == [current_correct_answer]:
        quiz_results[uid]['score'] += 1
    else:
        quiz_results[uid]['incorrect'] += 1


def run_quiz():
    global is_quiz_on, quiz_results, current_correct_answer

    try:
        bot.send_message(CHAT_ID,
            '⏳ <b>GitHub se questions fetch ho rahe hain...</b>',
            parse_mode='HTML')

        selections = read_menu()
        if not selections:
            bot.send_message(CHAT_ID,
                '❌ <b>menu.txt khaali hai ya GitHub connect nahi hua!</b>',
                parse_mode='HTML')
            return

        all_q = []
        for sel in selections:
            qs = load_questions(sel)
            all_q.extend(qs)

        if not all_q:
            bot.send_message(CHAT_ID,
                '❌ <b>Koi valid question nahi mila!</b>',
                parse_mode='HTML')
            return

        total_q    = len(all_q)
        today      = datetime.now().weekday()
        is_weekend = today in [5, 6]
        day_tag    = '🎲 <b>WEEKEND RANDOM MIX!</b>' if is_weekend else '📅 <b>DAILY QUIZ</b>'

        intro = (
            f'📖 {day_tag}\n\n'
            '<b>UPSC / BPSC / MPPCS QUIZ</b>\n\n'
            f'📍 <b>Total Questions:</b> {total_q}\n'
            '⏱️ <b>Har Question Ka Time:</b> 15 Seconds\n'
            '🏆 <b>Points:</b> Sirf Sahi Jawab Pe!\n\n'
            '👉 <i>Quiz 5 second mein shuru hoga...</i>'
        )
        bot.send_message(CHAT_ID, intro, parse_mode='HTML')
        time.sleep(5)

        for i, q in enumerate(all_q):
            current_correct_answer = q['correct']
            question_text = fmt(q['question'])
            options       = [fmt(o)[:100] for o in q['options']]
            poll_q        = f'❓ Q{i+1}/{total_q}:\n\n{question_text}'[:300]
            footer        = '\n\n━━━━━━━━━━━━━━━\n© @dkstudio'

            bot.send_poll(
                chat_id           = CHAT_ID,
                question          = poll_q,
                options           = options,
                type              = 'quiz',
                correct_option_id = current_correct_answer,
                explanation       = q.get('explanation', 'Sahi jawab!') + footer,
                is_anonymous      = False,
                open_period       = 15
            )
            time.sleep(17)

        is_quiz_on             = False
        current_correct_answer = None

        result = '🏁 <b>QUIZ KHATAM!</b> 🏁\n\n<b>📊 FINAL LEADERBOARD:</b>\n\n'

        if not quiz_results:
            result += '😴 Kisi ne koi jawab nahi diya!'
        else:
            sorted_res = sorted(
                quiz_results.items(),
                key=lambda x: x[1]['score'],
                reverse=True
            )
            medals = ['🥇', '🥈', '🥉']
            ranks  = ['1st Place', '2nd Place', '3rd Place']

            for i, (uid, data) in enumerate(sorted_res):
                medal     = medals[i] if i < 3 else '👤'
                rank      = ranks[i]  if i < 3 else f'{i+1}th Place'
                correct   = data['score']
                incorrect = data['incorrect']
                attempted = correct + incorrect
                result += (
                    f'{medal} <b>{data["name"]}</b>  <i>{rank}</i>\n'
                    f'   ✅ Sahi: <b>{correct}/{total_q}</b>\n'
                    f'   ❌ Galat: {incorrect}\n'
                    f'   📝 Attempt: {attempted}/{total_q}\n'
                    f'──────────────────────\n'
                )

        result += '\n© @dkstudio'
        bot.send_message(CHAT_ID, result, parse_mode='HTML')

    except Exception as e:
        is_quiz_on = False
        bot.send_message(CHAT_ID,
            f'❌ Error aaya:\n<code>{e}</code>',
            parse_mode='HTML')

    finally:
        try:
            quiz_lock.release()
        except RuntimeError:
            pass


@bot.message_handler(commands=['startquiz'])
def start_quiz(message):
    global is_quiz_on, quiz_results, current_correct_answer

    if not quiz_lock.acquire(blocking=False):
        bot.send_message(CHAT_ID,
            '⚠️ <b>Quiz pehle se chal rahi hai!</b>\n\nKhatam hone do phir /startquiz dabao.',
            parse_mode='HTML')
        return

    quiz_results           = {}
    current_correct_answer = None
    is_quiz_on             = True

    t = threading.Thread(target=run_quiz)
    t.daemon = True
    t.start()


@bot.message_handler(commands=['stopquiz'])
def stop_quiz(message):
    global is_quiz_on
    if is_quiz_on:
        is_quiz_on = False
        bot.send_message(CHAT_ID, '🛑 <b>Quiz rok di gayi!</b>', parse_mode='HTML')
    else:
        bot.send_message(CHAT_ID, 'ℹ️ Abhi koi quiz nahi chal rahi.', parse_mode='HTML')


@bot.message_handler(commands=['status'])
def status(message):
    state      = '🟢 Chal rahi hai' if is_quiz_on else '🔴 Nahi chal rahi'
    today      = datetime.now().weekday()
    day        = '🎲 Weekend' if today in [5, 6] else '📅 Weekday'
    bot.send_message(CHAT_ID,
        f'<b>Quiz Status:</b> {state}\n<b>Aaj:</b> {day}',
        parse_mode='HTML')


@bot.message_handler(commands=['help'])
def help_cmd(message):
    help_text = (
        '<b>📚 QUIZ BOT — HELP</b>\n\n'
        '<b>Commands:</b>\n'
        '/startquiz — Quiz shuru karo\n'
        '/stopquiz  — Quiz band karo\n'
        '/status    — Bot status\n'
        '/help      — Yeh message\n\n'
        '<b>menu.txt ke formats:</b>\n\n'
        '<code>history 10</code>\n'
        '→ history se 10 random questions\n\n'
        '<code>history 0</code>\n'
        '→ history ke saare questions\n\n'
        '<code>history 25-50</code>\n'
        '→ history ke Q25 se Q50 tak\n\n'
        '<code>WEEKEND</code>\n'
        '→ Saturday/Sunday ko auto random mix\n\n'
        '<b>Available subjects:</b>\n'
        'history, polity, geography\n'
        'bihar, economy, science\n'
        'current_affairs, mppcs_2026'
    )
    bot.send_message(CHAT_ID, help_text, parse_mode='HTML')


print('Bot chal raha hai...')
bot.polling(none_stop=True)
