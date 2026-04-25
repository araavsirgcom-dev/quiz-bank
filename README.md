# 📚 Quiz Bank — UPSC/BPSC Telegram Bot

> Sab kuch GitHub pe manage karo — Bot automatically fetch karega!

---

## 🗂️ Repository Structure

```
quiz-bank/
├── menu.txt              ← 👈 Yahi control karta hai quiz ko
├── README.md             ← Yeh guide
└── bank/
    ├── history.txt       ← Modern/Ancient History
    ├── polity.txt        ← Indian Polity
    ├── geography.txt     ← Geography
    ├── bihar.txt         ← Bihar Special
    ├── economy.txt       ← Economy
    ├── science.txt       ← Science & Tech
    └── current_affairs.txt ← Current Affairs
```

---

## 📝 menu.txt — Quiz Control File

Yahan likho **kaunsi file se kitne questions** chahiye:

```
# Yeh ek example hai
history 10
polity 5
bihar 5
current_affairs 8
```

### Rules:
| Likhne ka tarika | Matlab |
|---|---|
| `history 10` | history.txt se 10 random questions |
| `polity 0` | polity.txt se SAARE questions |
| `current_affairs 5` | current_affairs.txt se 5 random questions |
| `# Yeh comment hai` | Yeh line ignore hogi |

> ✅ Jitni files chahiye utni likho — bot sab mix karke quiz banayega!

---

## ➕ Naye Questions Kaise Add Karein?

### Format (HAR LINE EK QUESTION):
```
Question|Option A|Option B|Option C|Option D|Correct Index|Explanation
```

### Correct Index:
| Index | Matlab |
|---|---|
| `0` | Option A sahi hai |
| `1` | Option B sahi hai |
| `2` | Option C sahi hai |
| `3` | Option D sahi hai |

### Example:
```
1857 ki kranti ka karan?|Namak kar|Charbi wale kartoose|Bhoomi kar|Jaati bhed|1|Enfield rifle ke charbi wale kartoose 1857 ki kranti ka tatkalik karan the.
```

### Hindi + English dono mein:
```
गांधीजी का जन्म कब हुआ? / When was Gandhiji born?|1867|1869|1871|1875|1|Mahatma Gandhi ka janm 2 October 1869 ko Porbandar mein hua tha.
```

---

## 📱 GitHub Pe Questions Add Karne Ka Tarika

### Phone/PC se:
1. GitHub.com pe `quiz-bank` repo mein jao
2. `bank/` folder mein jis file mein add karna hai use open karo
   - Jaise: `bank/history.txt`
3. **Pencil icon** (Edit) pe click karo
4. File ke **neeche** naya question paste karo
5. **Commit changes** pe click karo — ho gaya! ✅

### menu.txt change karna ho to:
1. `menu.txt` file open karo
2. Pencil icon pe click karo
3. Jo subject aur kitne questions chahiye woh likho
4. **Commit changes** — Bot next `/startquiz` pe automatically naya mix lega! ✅

---

## 🤖 Bot Commands

| Command | Kaam |
|---|---|
| `/startquiz` | Quiz shuru karo (GitHub se auto fetch hoga) |
| `/stopquiz` | Chal rahi quiz band karo |
| `/status` | Check karo quiz chal rahi hai ya nahi |

---

## ⚙️ Termux Setup (Ek Baar Karo)

```bash
pip install pyTelegramBotAPI requests --break-system-packages
```

```bash
pkill -f python
PYTHONIOENCODING=utf-8 LANG=en_US.UTF-8 nohup python bot.py &
```

### Bot restart karna ho:
```bash
pkill -f python && PYTHONIOENCODING=utf-8 LANG=en_US.UTF-8 nohup python bot.py &
```

---

## 💡 Daily Quiz Tips

- Roz `menu.txt` edit karo — alag mix rakho
- Naye questions `bank/` files mein add karte raho
- Questions kabhi delete mat karo — sirf `menu.txt` se control karo

---

## ❗ Common Errors aur Fix

| Error | Fix |
|---|---|
| `GitHub se connect nahi hua` | Internet check karo, repo Public hai na check karo |
| `Koi questions nahi mila` | `menu.txt` mein subject ka naam aur `bank/` file ka naam same hona chahiye |
| `409 Conflict` | `pkill -f python` karo phir restart karo |
| `Quiz baar baar start ho rahi` | Pehli quiz khatam hone do, phir `/startquiz` dabao |

---

*© @dkstudio*
