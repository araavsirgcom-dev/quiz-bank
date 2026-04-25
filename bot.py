# -*- coding: utf-8 -*-
import telebot
import json
import time
import threading
import random
import re

try:
    import requests
except ImportError:
    import subprocess
    subprocess.call(['pip', 'install', 'requests', '--break-system-packages'])
    import requests

# ══════════════════════════════════════
#         SETTINGS - YAHAN BADLO
# ══════════════════════════════════════
TOKEN    = '8642537837:AAFdvNHqy9_E07ygKcCCjJNn7RVXWL3lNE8'
CHAT_ID  = '-1003952438399'
GITHUB   = 'araavsirgcom-dev'
REPO     = 'quiz-bank'
BRANCH   = 'main'
# ══════════════════════════════════════

BASE_URL = f'https://raw.githubusercontent.com/{GITHUB}/{REPO}/{BRANCH}'

bot = telebot.TeleBot(TOKEN)

quiz_results        = {}
is_quiz_on          = False
current_correct_answer = None
quiz_lock           = threading.Lock()


# ──────────────────────────────────────
# GitHub se file fetch karo
# ──────────────────────────────────────
def fetch_file(path):
    url = f'{BASE_URL}/{path}'
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.text
        else:
            print(f'❌ Fetch failed: {url} → {r.status_code}')
            return None
    except Exception as e:
        print(f'❌ Network error: {e}')
        return None


# ──────────────────────────────────────
# menu.txt padho
# ──────────────────────────────────────
def read_menu():
    content = fetch_file('menu.txt')
    if not content:
        return []
    selections = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        if len(parts) == 2:
            try:
                selections.append((parts[0].lower(), int(parts[1])))
            except ValueError:
                pass
        elif len(parts) == 1:
            selections.append((parts[0].lower(), 0))
    return selections


# ──────────────────────────────────────
# Bank file se questions load karo
# ──────────────────────────────────────
def load_questions(subject, count):
    content = fetch_file(f'bank/{subject}.txt')
    if not content:
        return []
    questions = []
    for line in content.splitlines():
        line = line.strip()
        if not line or '|' not in line:
            continue
        parts = line.split('|')
        if len(parts) >= 6:
            questions.append({
                'question':    parts[0],
                'options':     [parts[1], parts[2], parts[3], parts[4]],
                'correct':     int(parts[5]),
                'explanation': parts[6] if len(parts) >= 7 else 'Sahi jawab!'
            })
    if count == 0 or count >= len(questions):
        return questions
    return random.sample(questions, count)


# ──────────────────────────────────────
# Hindi/English mix → vertical format
# ──────────────────────────────────────
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


# ──────────────────────────────────────
# Poll answer handler
# ──────────────────────────────────────
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


# ──────────────────────────────────────
# Quiz runner (thread mein chalta hai)
# ──────────────────────────────────────
def run_quiz():
    global is_quiz_on, quiz_results, current_correct_answer

    try:
        # Step 1 — GitHub se menu padho
        bot.send_message(CHAT_ID, '⏳ <b>GitHub se questions fetch ho rahe hain...</b>', parse_mode='HTML')
        selections = read_menu()

        if not selections:
            bot.send_message(CHAT_ID, '❌ <b>menu.txt khaali hai ya GitHub se connect nahi hua!</b>', parse_mode='HTML')
            return

        # Step 2 — Questions load karo
        all_q = []
        for subject, count in selections:
            qs = load_questions(subject, count)
            all_q.extend(qs)
            c = 'saare' if count == 0 else str(count)
            print(f'✅ {subject}.txt → {len(qs)} questions')

        if not all_q:
            bot.send_message(CHAT_ID, '❌ <b>Koi questions nahi mila! Bank files check karo.</b>', parse_mode='HTML')
            return

        total_q = len(all_q)

        # Step 3 — Intro message
        intro = (
            '📖 <b>UPSC/BPSC QUIZ SHURU HO RAHA HAI!</b>\n\n'
            '📍 <b>Total Questions:</b> ' + str(total_q) + '\n'
            '⏱️ <b>Har Question Ka Time:</b> 15 Seconds\n'
            '🏆 <b>Points:</b> Sirf Sahi Jawab Pe!\n\n'
            '👉 <i>Quiz 5 second mein shuru hoga...</i>'
        )
        bot.send_message(CHAT_ID, intro, parse_mode='HTML')
        time.sleep(5)

        # Step 4 — Questions bhejo
        for i, q in enumerate(all_q):
            current_correct_answer = int(q['correct'])
            question_text = fmt(q['question'])
            options       = [fmt(o)[:100] for o in q['options']]
            poll_q        = f'❓ Q{i+1}/{total_q}:\n\n{question_text}'[:300]
            footer        = '\n\n━━━━━━━━━━━━━━━\n© @dkstudio'

            bot.send_poll(
                chat_id             = CHAT_ID,
                question            = poll_q,
                options             = options,
                type                = 'quiz',
                correct_option_id   = current_correct_answer,
                explanation         = q.get('explanation', 'Sahi jawab chuniye!') + footer,
                is_anonymous        = False,
                open_period         = 15
            )
            time.sleep(17)

        # Step 5 — Result card
        is_quiz_on             = False
        current_correct_answer = None

        result = '🏁 <b>QUIZ KHATAM!</b> 🏁\n\n<b>📊 FINAL LEADERBOARD:</b>\n\n'

        if not quiz_results:
            result += '😴 Kisi ne koi jawab nahi diya!'
        else:
            sorted_res = sorted(quiz_results.items(), key=lambda x: x[1]['score'], reverse=True)
            medals = ['🥇', '🥈', '🥉']
            ranks  = ['1st Place', '2nd Place', '3rd Place']

            for i, (uid, data) in enumerate(sorted_res):
                medal = medals[i] if i < 3 else '👤'
                rank  = ranks[i]  if i < 3 else f'{i+1}th Place'
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
        bot.send_message(CHAT_ID, f'❌ Error aaya:\n<code>{e}</code>', parse_mode='HTML')

    finally:
        try:
            quiz_lock.release()
        except RuntimeError:
            pass


# ──────────────────────────────────────
# Commands
# ──────────────────────────────────────
@bot.message_handler(commands=['startquiz'])
def start_quiz(message):
    global is_quiz_on, quiz_results, current_correct_answer

    if not quiz_lock.acquire(blocking=False):
        bot.send_message(
            CHAT_ID,
            '⚠️ <b>Quiz pehle se chal rahi hai!</b>\n\nKhatam hone do, phir /startquiz dabao. 🙏',
            parse_mode='HTML'
        )
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
    state = '🟢 Chal rahi hai' if is_quiz_on else '🔴 Nahi chal rahi'
    bot.send_message(CHAT_ID, f'<b>Quiz Status:</b> {state}', parse_mode='HTML')


print('✅ Bot chal raha hai...')
bot.polling(none_stop=True)
