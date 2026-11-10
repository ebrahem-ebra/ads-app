import json
import sqlite3
import telebot
from telebot import types

# ==========================================
# إعدادات البوت الأساسية (ضع بياناتك هنا)
# ==========================================
BOT_TOKEN = "9102460711:AAHn8yFWl7pGukbLom9iTjJnL3MGViKIZ2Y"
ADMIN_ID = 8729075253  # ضع رقم الآيدي الخاص بحسابك هنا (أرقام فقط)
MINIAPP_LINK = "https://t.me/Coin_syria27Bot/Money"

bot = telebot.TeleBot(BOT_TOKEN)


# ==========================================
# إعداد قاعدة البيانات (SQLite)
# ==========================================
def init_db():
  conn = sqlite3.connect("bot_database.db")
  c = conn.cursor()
  c.execute("""CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    balance REAL DEFAULT 0.0,
                    ads_watched INTEGER DEFAULT 0
                )""")
  c.execute("""CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )""")
  c.execute(
      "INSERT OR IGNORE INTO settings (key, value) VALUES ('ad_reward',"
      " '0.002')"
  )
  c.execute(
      "INSERT OR IGNORE INTO settings (key, value) VALUES ('min_withdraw',"
      " '2.0')"
  )
  c.execute(
      "INSERT OR IGNORE INTO settings (key, value) VALUES ('maintenance',"
      " 'off')"
  )
  c.execute(
      "INSERT OR IGNORE INTO settings (key, value) VALUES ('maintenance_msg',"
      " '⏸ البوت في استراحة حالياً، سيعود للعمل غداً أو بعد قليل.')"
  )
  conn.commit()
  conn.close()


def get_setting(key):
  conn = sqlite3.connect("bot_database.db")
  c = conn.cursor()
  c.execute("SELECT value FROM settings WHERE key=?", (key,))
  res = c.fetchone()
  conn.close()
  return res[0] if res else None


def set_setting(key, value):
  conn = sqlite3.connect("bot_database.db")
  c = conn.cursor()
  c.execute(
      "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
  )
  conn.commit()
  conn.close()


def get_user(user_id):
  conn = sqlite3.connect("bot_database.db")
  c = conn.cursor()
  c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
  conn.commit()
  c.execute(
      "SELECT balance, ads_watched FROM users WHERE user_id=?", (user_id,)
  )
  user = c.fetchone()
  conn.close()
  return user


def add_balance(user_id, amount):
  conn = sqlite3.connect("bot_database.db")
  c = conn.cursor()
  c.execute(
      "UPDATE users SET balance = balance + ?, ads_watched = ads_watched + 1"
      " WHERE user_id=?",
      (amount, user_id),
  )
  conn.commit()
  conn.close()


def deduct_balance(user_id, amount):
  conn = sqlite3.connect("bot_database.db")
  c = conn.cursor()
  c.execute(
      "UPDATE users SET balance = balance - ? WHERE user_id=?",
      (amount, user_id),
  )
  conn.commit()
  conn.close()


# ==========================================
# القوائم والأزرار
# ==========================================
def main_menu(user_id):
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  btn_watch = types.KeyboardButton("🎬 مشاهدة إعلان والربح")
  btn_balance = types.KeyboardButton("💰 رصيدي")
  btn_withdraw = types.KeyboardButton("💸 سحب الأرباح")
  markup.add(btn_watch)
  markup.add(btn_balance, btn_withdraw)

  if user_id == ADMIN_ID:
    markup.add(types.KeyboardButton("⚙️ لوحة تحكم الأدمن"))
  return markup


def is_maintenance(user_id):
  if user_id == ADMIN_ID:
    return False
  return get_setting("maintenance") == "on"


# ==========================================
# أوامر البوت الأساسية
# ==========================================
@bot.message_handler(commands=["start"])
def send_welcome(message):
  user_id = message.from_user.id
  get_user(user_id)

  if is_maintenance(user_id):
    bot.send_message(user_id, get_setting("maintenance_msg"))
    return

  args = message.text.split()
  if len(args) > 1 and args[1] == "watched":
    reward = float(get_setting("ad_reward"))
    add_balance(user_id, reward)
    balance, _ = get_user(user_id)
    bot.send_message(
        user_id,
        f"✅ تم احتساب مشاهدة الإعلان بنجاح!\n➕ أضيف لرصيدك: *{reward}$*\n💰"
        f" رصيدك الحالي: *{balance:.4f}$*",
        parse_mode="Markdown",
        reply_markup=main_menu(user_id),
    )
    return

  reward = get_setting("ad_reward")
  min_w = get_setting("min_withdraw")
  welcome_text = (
      "👋 أهلاً بك في بوت الربح من مشاهدة الإعلانات!\n\n"
      f"💵 ربح الإعلان الواحد: *{reward}$*\n"
      f"🏦 الحد الأدنى للسحب: *{min_w}$*\n"
      "💳 طرق السحب: *شام كاش (ShamCash) - رصيد سيرياتيل*\n\n"
      "اضغط على زر (🎬 مشاهدة إعلان والربح) بالأسفل للبدء."
  )
  bot.send_message(
      user_id,
      welcome_text,
      parse_mode="Markdown",
      reply_markup=main_menu(user_id),
  )


@bot.message_handler(func=lambda m: m.text == "🎬 مشاهدة إعلان والربح")
def open_ad_menu(message):
  user_id = message.from_user.id
  if is_maintenance(user_id):
    bot.send_message(user_id, get_setting("maintenance_msg"))
    return

  markup = types.InlineKeyboardMarkup()
  markup.add(
      types.InlineKeyboardButton(
          "▶️ اضغط هنا لبدء الإعلان",
          url=MINIAPP_LINK,
      )
  )
  bot.send_message(
      user_id,
      "اضغط على الزر بالأسفل لفتح مشغل الإعلانات الرسمي والربح:",
      reply_markup=markup,
  )


@bot.message_handler(func=lambda m: m.text == "💰 رصيدي")
def show_balance(message):
  user_id = message.from_user.id
  if is_maintenance(user_id):
    bot.send_message(user_id, get_setting("maintenance_msg"))
    return

  balance, watched = get_user(user_id)
  min_w = float(get_setting("min_withdraw"))
  text = (
      f"👤 **معلومات حسابك:**\n\n"
      f"💰 الرصيد الحالي: *{balance:.4f}$*\n"
      f"🎬 الإعلانات المشاهدة: *{watched}*\n"
      f"🎯 الحد الأدنى للسحب: *{min_w}$*"
  )
  bot.send_message(user_id, text, parse_mode="Markdown")


# ==========================================
# نظام السحب (شام كاش + سيرياتيل)
# ==========================================
@bot.message_handler(func=lambda m: m.text == "💸 سحب الأرباح")
def withdraw_start(message):
  user_id = message.from_user.id
  if is_maintenance(user_id):
    bot.send_message(user_id, get_setting("maintenance_msg"))
    return

  balance, _ = get_user(user_id)
  min_w = float(get_setting("min_withdraw"))

  if balance < min_w:
    bot.send_message(
        user_id,
        f"⚠️ عذراً، رصيدك الحالي (*{balance:.4f}$*) أقل من الحد الأدنى للسحب"
        f" (*{min_w}$*).",
        parse_mode="Markdown",
    )
    return

  markup = types.InlineKeyboardMarkup(row_width=1)
  markup.add(
      types.InlineKeyboardButton(
          "💳 شام كاش (ShamCash)", callback_data="wd_shamcash"
      ),
      types.InlineKeyboardButton(
          "📱 رصيد سيرياتيل", callback_data="wd_syriatel"
      ),
  )
  bot.send_message(
      user_id,
      f"💰 رصيدك القابل للسحب: *{balance:.4f}$*\nاختر طريقة السحب المناسبة:",
      parse_mode="Markdown",
      reply_markup=markup,
  )


@bot.callback_query_handler(func=lambda call: call.data.startswith("wd_"))
def withdraw_method(call):
  method = (
      "شام كاش (ShamCash)"
      if call.data == "wd_shamcash"
      else "رصيد سيرياتيل"
  )
  prompt = (
      "أرسل عنوان محفظة شام كاش أو الباركود النصي الخاص بك:"
      if call.data == "wd_shamcash"
      else "أرسل رقم هاتف سيرياتيل الخاص بك:"
  )
  msg = bot.send_message(call.from_user.id, f"📝 اخترت: *{method}*\n{prompt}", parse_mode="Markdown")
  bot.register_next_step_handler(msg, process_withdraw, method)


def process_withdraw(message, method):
  user_id = message.from_user.id
  address = message.text
  balance, _ = get_user(user_id)
  min_w = float(get_setting("min_withdraw"))

  if balance < min_w:
    bot.send_message(user_id, "❌ رصيدك غير كافٍ.")
    return

  deduct_balance(user_id, balance)

  bot.send_message(
      user_id,
      "✅ تم إرسال طلب السحب بنجاح! سيتم مراجعته وتحويل المبلغ في أقرب وقت.",
  )

  admin_markup = types.InlineKeyboardMarkup()
  admin_markup.add(
      types.InlineKeyboardButton(
          "✅ تم الدفع", callback_data=f"approve_{user_id}_{balance:.4f}"
      ),
      types.InlineKeyboardButton(
          "❌ رفض وإرجاع الرصيد",
          callback_data=f"reject_{user_id}_{balance:.4f}",
      ),
  )
  admin_text = (
      "🔔 **طلب سحب جديد!**\n\n"
      f"👤 المستخدم: `{user_id}`\n"
      f"💵 المبلغ: *{balance:.4f}$*\n"
      f"🏦 الطريقة: *{method}*\n"
      f"📋 البيانات: `{address}`"
  )
  bot.send_message(
      ADMIN_ID, admin_text, parse_mode="Markdown", reply_markup=admin_markup
  )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith(("approve_", "reject_"))
)
def handle_admin_withdraw(call):
  if call.from_user.id != ADMIN_ID:
    return
  action, user_id, amount = call.data.split("_")
  user_id = int(user_id)
  amount = float(amount)

  if action == "approve":
    bot.edit_message_text(
        call.message.text + "\n\n✅ **الحالة: تم الدفع**",
        ADMIN_ID,
        call.message.message_id,
        parse_mode="Markdown",
    )
    bot.send_message(
        user_id,
        f"🎉 تمت الموافقة على طلب السحب الخاص بك بقيمة *{amount}$* وتم تحويل"
        " المبلغ بنجاح!",
        parse_mode="Markdown",
    )
  else:
    conn = sqlite3.connect("bot_database.db")
    c = conn.cursor()
    c.execute(
        "UPDATE users SET balance = balance + ? WHERE user_id=?",
        (amount, user_id),
    )
    conn.commit()
    conn.close()
    bot.edit_message_text(
        call.message.text + "\n\n❌ **الحالة: مرفوض (تم إرجاع الرصيد)**",
        ADMIN_ID,
        call.message.message_id,
        parse_mode="Markdown",
    )
    bot.send_message(
        user_id,
        f"⚠️ تم رفض طلب السحب الخاص بك بقيمة *{amount}$* وإعادة المبلغ إلى"
        " رصيدك في البوت.",
        parse_mode="Markdown",
    )


# ==========================================
# لوحة تحكم الأدمن
# ==========================================
@bot.message_handler(
    func=lambda m: m.text == "⚙️ لوحة تحكم الأدمن"
    and m.from_user.id == ADMIN_ID
)
def admin_panel(message):
  maint = get_setting("maintenance")
  reward = get_setting("ad_reward")
  status_text = (
      "🔴 متوقف (وضع الاستراحة)" if maint == "on" else "🟢 يعمل بشكل طبيعي"
  )

  markup = types.InlineKeyboardMarkup(row_width=1)
  markup.add(
      types.InlineKeyboardButton(
          f"💵 تغيير مكافأة الإعلان (الحالي: {reward}$)",
          callback_data="set_reward",
      ),
      types.InlineKeyboardButton(
          "⏸ تفعيل وضع الاستراحة (قبل إغلاق الهاتف)",
          callback_data="maint_on",
      ),
      types.InlineKeyboardButton(
          "▶️ تشغيل البوت وإشعار الجميع بالعودة", callback_data="maint_off"
      ),
      types.InlineKeyboardButton(
          "📢 إرسال إشعار عودة الإنترنت للجميع", callback_data="broadcast_back"
      ),
  )
  bot.send_message(
      ADMIN_ID,
      f"⚙️ **لوحة التحكم**\nحالة البوت: {status_text}",
      parse_mode="Markdown",
      reply_markup=markup,
  )


@bot.callback_query_handler(
    func=lambda call: call.data
    in ["set_reward", "maint_on", "maint_off", "broadcast_back"]
)
def admin_actions(call):
  if call.from_user.id != ADMIN_ID:
    return

  if call.data == "set_reward":
    msg = bot.send_message(
        ADMIN_ID, "أرسل السعر الجديد لمشاهدة الإعلان بالدولار (مثال: 0.003):"
    )
    bot.register_next_step_handler(msg, save_new_reward)

  elif call.data == "maint_on":
    set_setting("maintenance", "on")
    bot.answer_callback_query(call.id, "تم تفعيل وضع الاستراحة!")
    bot.send_message(
        ADMIN_ID,
        "⏸ تم تفعيل وضع الاستراحة. أي مستخدم سيحاول استخدام البوت الآن ستظهر"
        " له رسالة التوقف المؤقت.",
    )

  elif call.data == "maint_off":
    set_setting("maintenance", "off")
    bot.answer_callback_query(call.id, "تم تشغيل البوت!")
    send_broadcast("✅ عاد البوت للعمل الآن! يمكنك متابعة مشاهدة الإعلانات والربح.")

  elif call.data == "broadcast_back":
    send_broadcast(
        "⚡ عاد الاتصال بالإنترنت والبوت يعمل الآن بكامل طاقته! ابدأ الربح."
    )


def save_new_reward(message):
  try:
    val = float(message.text)
    set_setting("ad_reward", str(val))
    bot.send_message(ADMIN_ID, f"✅ تم تحديث مكافأة الإعلان إلى *{val}$*", parse_mode="Markdown")
  except:
    bot.send_message(ADMIN_ID, "❌ رقم غير صحيح.")


def send_broadcast(text):
  conn = sqlite3.connect("bot_database.db")
  c = conn.cursor()
  c.execute("SELECT user_id FROM users")
  users = c.fetchall()
  conn.close()

  count = 0
  for u in users:
    try:
      bot.send_message(u[0], text)
      count += 1
    except:
      pass
  bot.send_message(ADMIN_ID, f"📢 تم إرسال الإشعار إلى {count} مستخدم.")


init_db()
print("البوت يعمل الآن...")
bot.infinity_polling()
