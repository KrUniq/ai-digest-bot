import tempfile
from datetime import datetime
from pathlib import Path

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from app.config import TOKEN, DEFAULT_MODE
from app.detection import detect_mode
from app.summarizer import summarize
from app.storage import init_db, make_cache_key, cache_get, cache_set, feedback_add


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("mode", DEFAULT_MODE)
    context.user_data.setdefault("auto_mode", True)

    await update.message.reply_text(
        "🤖 AI Summarizer (локально, Ollama)\n\n"
        "/mode travel | work | digest — вручную\n"
        "/auto on | off — авто-выбор режима (по умолчанию ON)\n"
        "/save — сохранить последний результат\n"
        "/like /dislike — оценить последний ответ\n"
        "/version — версия и состояние\n\n"
        "Новости/афиши/промо автоматически идут в digest."
    )



async def mode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        current = context.user_data.get("mode", DEFAULT_MODE)
        auto = context.user_data.get("auto_mode", True)
        await update.message.reply_text(
            f"Текущий режим: {current}\n"
            f"Auto-mode: {'ON' if auto else 'OFF'}\n"
            "Выбери: /mode travel | work | digest"
        )
        return

    m = context.args[0].lower()
    if m not in ("travel", "work", "digest"):
        await update.message.reply_text("Неверный режим. Доступно: travel, work, digest")
        return

    context.user_data["mode"] = m
    await update.message.reply_text(f"Режим установлен: {m}")


async def auto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        auto = context.user_data.get("auto_mode", True)
        await update.message.reply_text(
            f"Auto-mode сейчас: {'ON' if auto else 'OFF'}\nКоманда: /auto on или /auto off"
        )
        return

    v = context.args[0].lower()
    if v not in ("on", "off"):
        await update.message.reply_text("Нужно: /auto on или /auto off")
        return

    context.user_data["auto_mode"] = (v == "on")
    await update.message.reply_text(f"Auto-mode: {v.upper()}")


async def save_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    last = context.user_data.get("last_result")
    if not last:
        await update.message.reply_text("Пока нечего сохранять. Сначала пришли текст 🙂")
        return

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    mode = last.get("mode", "unknown")
    text = last.get("text", "")
    result = last.get("result", "")

    md = (
        f"# AI Summary\n\n"
        f"- Timestamp: {ts}\n"
        f"- Mode: {mode}\n\n"
        f"## Input\n\n{text}\n\n"
        f"## Output\n\n{result}\n"
    )

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / f"summary_{mode}_{ts}.md"
        p.write_text(md, encoding="utf-8")
        await update.message.reply_document(document=str(p), filename=p.name, caption=f"Saved ✅ (mode={mode})")


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    text = (msg.text or msg.caption or "").strip()

    # ignore album item without caption
    if (msg.media_group_id is not None) and len(text) < 20:
        return

    if len(text) < 20:
        if msg.photo or msg.video or msg.document or msg.animation:
            await msg.reply_text(
                "Похоже, это пост с медиа, но без текста/подписи (caption) или она слишком короткая.\n"
                "Скопируй текст поста и пришли сюда, либо перешли сообщение с подписью."
            )
            return
        await msg.reply_text("Пришли текст подлиннее.")
        return

    await msg.chat.send_action(action=ChatAction.TYPING)

    try:
        auto = context.user_data.get("auto_mode", True)
        mode = detect_mode(text) if auto else context.user_data.get("mode", DEFAULT_MODE)

        # CACHE
        key = make_cache_key(text, mode)
        cached = cache_get(key)
        if cached:
            result, model_used, _created_at = cached
        else:
            result, model_used = summarize(text, mode=mode)
            cache_set(key=key, mode=mode, model=model_used, text=text, result=result)

        context.user_data["last_result"] = {
            "mode": mode,
            "text": text,
            "result": result,
            "cache_key": key,
            "model_used": model_used,
        }

        await msg.reply_text(result[:3900])
    except Exception as e:
        await msg.reply_text(f"Ошибка: {e}")



APP_VERSION = "1.1.0"  # минимальный versioning

async def version_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode", DEFAULT_MODE)
    auto = context.user_data.get("auto_mode", True)

    last = context.user_data.get("last_result") or {}
    last_mode = last.get("mode")
    last_model = last.get("model_used")

    msg = (
        f"AI Digest v{APP_VERSION}\n"
        f"Auto-mode: {'ON' if auto else 'OFF'}\n"
        f"Default mode: {mode}\n"
    )
    if last_mode or last_model:
        msg += f"Last: mode={last_mode}, model={last_model}\n"

    await update.message.reply_text(msg)

async def like_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    last = context.user_data.get("last_result")
    if not last:
        await update.message.reply_text("Нет последнего результата, который можно оценить.")
        return

    key = last.get("cache_key")
    mode = last.get("mode")
    model = last.get("model_used")
    uid = update.effective_user.id if update.effective_user else 0

    feedback_add(key=key, telegram_user_id=uid, mode=mode, model=model, score=1)
    await update.message.reply_text("👍 принято")

async def dislike_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    last = context.user_data.get("last_result")
    if not last:
        await update.message.reply_text("Нет последнего результата, который можно оценить.")
        return

    key = last.get("cache_key")
    mode = last.get("mode")
    model = last.get("model_used")
    uid = update.effective_user.id if update.effective_user else 0

    feedback_add(key=key, telegram_user_id=uid, mode=mode, model=model, score=-1)
    await update.message.reply_text("👎 принято")


from telegram.request import HTTPXRequest

def build_app():
    request = HTTPXRequest(
        connect_timeout=30,
        read_timeout=30,
    )

    app = (
        Application.builder()
        .token(TOKEN)
        .request(request)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mode", mode_cmd))
    app.add_handler(CommandHandler("auto", auto_cmd))
    app.add_handler(CommandHandler("save", save_cmd))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, on_message))

    return app

