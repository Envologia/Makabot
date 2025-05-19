# handlers.py

from telegram import (
    Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import ContextTypes
from db import User, Like, SessionLocal
from config import UNIVERSITIES, REQUIRED_CHANNELS

(NAME, UNIVERSITY, AGE, GENDER, INTERESTS, BIO, PHOTO, SELECT_UNIS) = range(8)

def get_session():
    return SessionLocal()

async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception:
            return False
    return True

async def require_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🚨 To use **Unimatch Ethio**, you must join both channels:\n"
        "👉 [UniMatch Ethio](https://t.me/unimatch_ethio)\n"
        "👉 [UniMatch Confession](https://t.me/unimatch_confession)\n"
        "After joining, press /start again. 💌"
    )
    await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_membership(update, context):
        await require_channels(update, context)
        return
    user = update.effective_user
    session = get_session()
    db_user = session.query(User).filter_by(tg_id=user.id).first()
    if db_user and db_user.registered:
        await update.message.reply_text(
            "👋 Welcome back to **Unimatch Ethio**! Ready to find your campus match? 💘\n\n"
            "Use /browse to discover profiles, /profile to view/edit yours, /matches to chat with your matches.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "🎉 Welcome to **Unimatch Ethio** – Ethiopia's #1 University Dating Bot!\n\n"
            "Let's create your profile. What's your name? 😊",
            parse_mode="Markdown"
        )
        return NAME

async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_membership(update, context):
        await require_channels(update, context)
        return
    context.user_data['name'] = update.message.text
    keyboard = [UNIVERSITIES[i:i+2] for i in range(0, len(UNIVERSITIES), 2)]
    keyboard.append(["Other"])
    await update.message.reply_text(
        "🏫 Which university do you attend? Please select from the list:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return UNIVERSITY

async def register_university(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_membership(update, context):
        await require_channels(update, context)
        return
    if update.message.text not in UNIVERSITIES and update.message.text != "Other":
        await update.message.reply_text("❗️Please select a university from the list.")
        return UNIVERSITY
    context.user_data['university'] = update.message.text
    age_buttons = [[str(i)] for i in range(18, 31)]
    await update.message.reply_text("🎂 How old are you?", reply_markup=ReplyKeyboardMarkup(age_buttons, one_time_keyboard=True, resize_keyboard=True))
    return AGE

async def register_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_membership(update, context):
        await require_channels(update, context)
        return
    try:
        age = int(update.message.text)
        if age < 18 or age > 30:
            await update.message.reply_text("🔞 Please select your age using the buttons (18-30).")
            return AGE
        context.user_data['age'] = age
    except ValueError:
        await update.message.reply_text("🔢 Please select your age using the buttons.")
        return AGE
    await update.message.reply_text(
        "🚻 What's your gender?",
        reply_markup=ReplyKeyboardMarkup([["Male"], ["Female"]], one_time_keyboard=True, resize_keyboard=True)
    )
    return GENDER

def build_uni_keyboard(selected_unis, all_unis):
    keyboard = []
    for uni in all_unis:
        checked = "✔️ " if uni in selected_unis else ""
        keyboard.append([InlineKeyboardButton(f"{checked}{uni}", callback_data=uni)])
    keyboard.append([InlineKeyboardButton("✅ Done", callback_data="__done__")])
    return InlineKeyboardMarkup(keyboard)

async def register_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_membership(update, context):
        await require_channels(update, context)
        return
    gender = update.message.text
    if gender not in ["Male", "Female"]:
        await update.message.reply_text("❗️Please select Male or Female.")
        return GENDER
    context.user_data['gender'] = gender
    context.user_data['looking_for'] = "Female" if gender == "Male" else "Male"
    context.user_data['selected_unis'] = []
    await update.message.reply_text(
        "🏫 **Select all universities you are interested in for matches.**\n"
        "Tap to select/deselect. Press ✅ Done when finished.",
        reply_markup=build_uni_keyboard([], UNIVERSITIES + ["All Universities"]),
        parse_mode="Markdown"
    )
    return SELECT_UNIS

async def uni_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selected_unis = context.user_data.get('selected_unis', [])
    uni = query.data

    if uni == "__done__":
        if not selected_unis:
            await query.edit_message_text("❗️Please select at least one university.")
            await query.message.reply_text(
                "🏫 **Select all universities you are interested in for matches.**\n"
                "Tap to select/deselect. Press ✅ Done when finished.",
                reply_markup=build_uni_keyboard(selected_unis, UNIVERSITIES + ["All Universities"]),
                parse_mode="Markdown"
            )
            return SELECT_UNIS
        context.user_data['looking_for_unis'] = selected_unis
        await query.edit_message_text(
            f"Selected universities: {', '.join(selected_unis)}"
        )
        await query.message.reply_text("🎯 What are your interests? (comma separated)")
        return INTERESTS

    # Toggle selection
    if uni in selected_unis:
        selected_unis.remove(uni)
    else:
        if uni == "All Universities":
            selected_unis = ["All Universities"]
        else:
            selected_unis = [u for u in selected_unis if u != "All Universities"]
            selected_unis.append(uni)
    context.user_data['selected_unis'] = selected_unis

    await query.edit_message_reply_markup(reply_markup=build_uni_keyboard(selected_unis, UNIVERSITIES + ["All Universities"]))
    return SELECT_UNIS

async def register_interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['interests'] = update.message.text
    await update.message.reply_text("📝 Write a short bio about yourself.")
    return BIO

async def register_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['bio'] = update.message.text
    await update.message.reply_text("📸 Send a profile photo (photo is required).")
    return PHOTO

async def register_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❗️Photo is required. Please send a profile photo.")
        return PHOTO
    context.user_data['photo_file_id'] = update.message.photo[-1].file_id
    user = update.effective_user
    session = get_session()
    db_user = session.query(User).filter_by(tg_id=user.id).first()
    if not db_user:
        db_user = User(tg_id=user.id)
        session.add(db_user)
    db_user.name = context.user_data['name']
    db_user.university = context.user_data['university']
    db_user.age = context.user_data['age']
    db_user.gender = context.user_data['gender']
    db_user.interests = context.user_data['interests']
    db_user.bio = context.user_data['bio']
    db_user.looking_for = context.user_data['looking_for']
    db_user.photo_file_id = context.user_data['photo_file_id']
    db_user.registered = True
    db_user.match_universities = ",".join(context.user_data['looking_for_unis'])
    session.commit()
    await update.message.reply_text(
        "✅ **Profile created!** Use /browse to find matches. Good luck! 🍀",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return -1  # ConversationHandler.END

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    session = get_session()
    db_user = session.query(User).filter_by(tg_id=user.id).first()
    if not db_user or not db_user.registered:
        await update.message.reply_text("❗️You need to register first. Use /start.")
        return
    text = (
        f"👤 **Your Profile**\n"
        f"Name: {db_user.name}\n"
        f"University: {db_user.university}\n"
        f"Age: {db_user.age}\n"
        f"Gender: {db_user.gender}\n"
        f"Interests: {db_user.interests}\n"
        f"Bio: {db_user.bio}\n"
        f"Interested in: {db_user.match_universities}\n"
    )
    await update.message.reply_photo(
        photo=db_user.photo_file_id,
        caption=text,
        parse_mode="Markdown"
    )

async def browse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    session = get_session()
    db_user = session.query(User).filter_by(tg_id=user.id).first()
    if not db_user or not db_user.registered:
        await update.message.reply_text("❗️You need to register first. Use /start.")
        return

    # Get universities the user is interested in
    user_unis = db_user.match_universities.split(",")
    # Exclude already liked/skipped users
    liked_ids = [like.to_user_id for like in session.query(Like).filter_by(from_user_id=db_user.id)]
    match_query = session.query(User).filter(
        User.id != db_user.id,
        User.gender == db_user.looking_for,
        User.registered == True,
        ~User.id.in_(liked_ids)
    )
    if "All Universities" not in user_unis:
        match_query = match_query.filter(User.university.in_(user_unis))
    candidate = match_query.first()
    if not candidate:
        await update.message.reply_text("😕 No more profiles match your criteria right now. Please check back later!")
        return

    context.user_data['browse_user_id'] = candidate.id
    text = (
        f"✨ **Profile Preview**\n"
        f"Name: {candidate.name}\n"
        f"University: {candidate.university}\n"
        f"Age: {candidate.age}\n"
        f"Gender: {candidate.gender}\n"
        f"Interests: {candidate.interests}\n"
        f"Bio: {candidate.bio}\n"
    )
    keyboard = ReplyKeyboardMarkup([["👍 Like", "⏭️ Skip"]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_photo(
        photo=candidate.photo_file_id,
        caption=text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def browse_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_membership(update, context):
        await require_channels(update, context)
        return
    user = update.effective_user
    session = get_session()
    db_user = session.query(User).filter_by(tg_id=user.id).first()
    target_id = context.user_data.get('browse_user_id')
    if not target_id:
        await update.message.reply_text("❗️No profile selected. Use /browse.")
        return

    if update.message.text.startswith("👍"):
        like = Like(from_user_id=db_user.id, to_user_id=target_id)
        session.add(like)
        liked_user = session.query(User).filter_by(id=target_id).first()

        # Notify the liked user immediately, even if not a match
        try:
            await context.bot.send_message(
                chat_id=liked_user.tg_id,
                text=(
                    f"💌 **Someone just liked your profile on Unimatch Ethio!**\n"
                    "Browse profiles to see if you like them back and get a match!"
                ),
                parse_mode="Markdown"
            )
        except Exception:
            pass

        # Check for mutual like (match)
        mutual = session.query(Like).filter_by(from_user_id=target_id, to_user_id=db_user.id).first()
        if mutual:
            like.matched = True
            mutual.matched = True
            session.commit()
            await update.message.reply_text(
                f"🎉 **It's a match!** You and {liked_user.name} liked each other! Start a conversation now. 🥳",
                parse_mode="Markdown"
            )
            try:
                await context.bot.send_message(
                    chat_id=liked_user.tg_id,
                    text=(
                        f"🎉 **It's a match!** You and {db_user.name} liked each other! "
                        "Start a conversation now. 🥳"
                    ),
                    parse_mode="Markdown"
                )
            except Exception:
                pass
        else:
            session.commit()
            await update.message.reply_text("👍 Liked! Use /browse to see more profiles.")
    else:
        await update.message.reply_text("⏭️ Skipped. Use /browse to see more profiles.")

async def matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    session = get_session()
    db_user = session.query(User).filter_by(tg_id=user.id).first()
    if not db_user:
        await update.message.reply_text("❗️You need to register first. Use /start.")
        return

    likes = session.query(Like).filter_by(from_user_id=db_user.id, matched=True).all()
    match_ids = [like.to_user_id for like in likes]
    matches = session.query(User).filter(User.id.in_(match_ids)).all()

    if not matches:
        await update.message.reply_text("💔 You have no matches yet. Keep browsing and liking!")
        return

    buttons = [
        [InlineKeyboardButton(f"{m.name} ({m.university})", callback_data=f"chatwith_{m.tg_id}")]
        for m in matches
    ]
    await update.message.reply_text(
        "💑 **Your matches:**\nTap a name to start chatting anonymously.",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )

async def start_chat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if not data.startswith("chatwith_"):
        return
    target_tg_id = int(data.split("_")[1])
    user = update.effective_user
    session = get_session()
    db_user = session.query(User).filter_by(tg_id=user.id).first()
    target_user = session.query(User).filter_by(tg_id=target_tg_id).first()
    if not target_user:
        await query.edit_message_text("❗️User not found.")
        return
    db_user.chatting_with = target_user.tg_id
    target_user.chatting_with = db_user.tg_id
    session.commit()
    await query.edit_message_text(
        f"🗨️ You are now chatting anonymously with **{target_user.name}**.\n"
        "Send a message and I'll deliver it!\nSend /stopchat to end this chat."
    )

async def relay_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    session = get_session()
    db_user = session.query(User).filter_by(tg_id=user.id).first()
    if not db_user or not db_user.chatting_with:
        return
    target_user = session.query(User).filter_by(tg_id=db_user.chatting_with).first()
    if not target_user or target_user.chatting_with != user.id:
        await update.message.reply_text("❗️Chat session expired. Use /matches to start again.")
        db_user.chatting_with = None
        session.commit()
        return
    # Relay the message
    if update.message.text:
        await context.bot.send_message(
            chat_id=target_user.tg_id,
            text=f"💬 Anonymous message from your match:\n\n{update.message.text}"
        )
    elif update.message.photo:
        await context.bot.send_photo(
            chat_id=target_user.tg_id,
            photo=update.message.photo[-1].file_id,
            caption="📷 Anonymous photo from your match"
        )

async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    session = get_session()
    db_user = session.query(User).filter_by(tg_id=user.id).first()
    if db_user and db_user.chatting_with:
        target_user = session.query(User).filter_by(tg_id=db_user.chatting_with).first()
        if target_user:
            target_user.chatting_with = None
            await context.bot.send_message(
                chat_id=target_user.tg_id,
                text="🔕 Your match has left the chat. Use /matches to start a new chat."
            )
        db_user.chatting_with = None
        session.commit()
        await update.message.reply_text("🔕 You have left the chat. Use /matches to chat again.")
    else:
        await update.message.reply_text("❗️You are not in a chat session.")
