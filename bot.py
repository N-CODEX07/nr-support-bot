from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
from telegram.error import TelegramError, BadRequest, RetryAfter
import logging
import re
import asyncio

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define states for the conversation handler
MAIN_MENU, TECHNICAL_SUPPORT, BUG_REPORT, OTHER_TECHNICAL, PARTNERSHIP, SOMETHING_ELSE, DIRECT_CHAT = range(7)

# Bot configuration
BOT_TOKEN = "8019510227:AAFPcFFWVj2UoNf3VvYGynvzCl799N1YZbo"  # Your bot token
PERSONAL_ID = 7307638800  # Your Telegram ID
ADMIN_USERNAME = "@nilay_ok"  # Your Telegram username

# Dictionary to store user messages and forwarded message IDs
user_messages = {}

def escape_markdown_v2(text):
    """Escape special characters for MarkdownV2."""
    escape_chars = r'_*\[\]()~`>#+=|{}.!-'
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text

def get_keyboard(state):
    """Generate the appropriate keyboard based on the state."""
    if state == MAIN_MENU:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("Technical Support 🎟️", callback_data="technical_support")],
            [InlineKeyboardButton("Direct chat 🗣️", callback_data="direct_chat")],
            [InlineKeyboardButton("Partnership Request 🤝", callback_data="partnership")],
            [InlineKeyboardButton("Something Else ❓", callback_data="something_else")],
        ])
    elif state == TECHNICAL_SUPPORT:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("Bug Report 🐛", callback_data="bug_report")],
            [InlineKeyboardButton("Other Technical Issues 🖥️", callback_data="other_technical")],
        ])
    else:  # BUG_REPORT, OTHER_TECHNICAL, PARTNERSHIP, SOMETHING_ELSE, DIRECT_CHAT
        return InlineKeyboardMarkup([])  # No buttons for these states

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the /start command and display the main menu."""
    user = update.effective_user
    user_link = f"[{escape_markdown_v2(user.first_name)}](tg://user?id={user.id})"
    welcome_message = (
        f"GM 👋, thanks for reaching out\\!\n\n"
        f"If you have already read our FAQs and still need help, please select one of the options below\\.\n\n"
        f"A team member will aim to respond within a few hours, but during busy times, it might take longer\\.\n\n"
        f"\\(Stay safe frens \\- Don’t share your password or seed phrase with anyone\\)\n\n"
        f"Sent by: {user_link}"
    )

    # Initialize user data if not present
    if user.id not in user_messages:
        user_messages[user.id] = {
            "username": user.first_name,
            "user_id": user.id,
            "last_message": welcome_message,
        }

    # Initialize state history
    if "state_history" not in context.user_data:
        context.user_data["state_history"] = []
    context.user_data["state_history"].append(MAIN_MENU)

    try:
        # Send the welcome message to the user
        await update.message.reply_text(
            welcome_message,
            reply_markup=get_keyboard(MAIN_MENU),
            parse_mode="MarkdownV2"
        )

        # Forward the user's message to your personal ID
        forwarded = await context.bot.send_message(
            chat_id=PERSONAL_ID,
            text=f"New interaction from {user_link}:\n{welcome_message}",
            parse_mode="MarkdownV2"
        )

        # Update forwarded message ID
        user_messages[user.id]["forwarded_message_id"] = forwarded.message_id
    except TelegramError as e:
        logger.error(f"Error in start: {e}")
        await update.message.reply_text("An error occurred. Please try again later.", parse_mode="MarkdownV2")

    context.user_data["state"] = MAIN_MENU
    return MAIN_MENU

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle button clicks from the inline keyboard."""
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    user_link = f"[{escape_markdown_v2(user.first_name)}](tg://user?id={user.id})"
    data = query.data

    logger.info(f"Button clicked by {user.id}: {data}")  # Debug log

    # Initialize user data if not present
    if user.id not in user_messages:
        user_messages[user.id] = {
            "username": user.first_name,
            "user_id": user.id,
            "last_message": "",
        }

    # Initialize state history if not present
    if "state_history" not in context.user_data:
        context.user_data["state_history"] = []

    try:
        if data == "technical_support":
            message = (
                f"You have selected Technical Support 🎟️\n\n"
                f"Sorry to hear you are facing an issue\\. Are you looking to report a bug or do you need help with something else\\?\n\n"
                f"Sent by: {user_link}"
            )
            await query.message.reply_text(
                message,
                reply_markup=get_keyboard(TECHNICAL_SUPPORT),
                parse_mode="MarkdownV2"
            )
            forwarded = await context.bot獻.send_message(
                chat_id=PERSONAL_ID,
                text=f"Technical Support selected by {user_link}:\n{message}",
                parse_mode="MarkdownV2"
            )
            user_messages[user.id]["last_message"] = message
            user_messages[user.id]["forwarded_message_id"] = forwarded.message_id
            context.user_data["state"] = TECHNICAL_SUPPORT
            context.user_data["state_history"].append(TECHNICAL_SUPPORT)
            return TECHNICAL_SUPPORT

        elif data == "bug_report":
            message = (
                f"To report a bug, please:\n\n"
                f"1\\) Clearly describe the issue\n"
                f"2\\) Explain the steps needed to reproduce the issue\n"
                f"3\\) Share screenshots or any other relevant information\n"
                f"4\\) If applicable, share your public wallet address and/or transaction ID\n\n"
                f"A member of the team will respond as soon as possible\\.\n"
                f"Sent by: {user_link}"
            )
            await query.message.reply_text(
                message,
                reply_markup=get_keyboard(BUG_REPORT),
                parse_mode="MarkdownV2"
            )
            forwarded = await context.bot.send_message(
                chat_id=PERSONAL_ID,
                text=f"Bug Report selected by {user_link}:\n{message}",
                parse_mode="MarkdownV2"
            )
            user_messages[user.id]["last_message"] = message
            user_messages[user.id]["forwarded_message_id"] = forwarded.message_id
            context.user_data["state"] = BUG_REPORT
            context.user_data["state_history"].append(BUG_REPORT)
            return BUG_REPORT

        elif data == "other_technical":
            message = (
                f"You have selected Other Technical Question 🖥️\n\n"
                f"Please clearly describe the issue you are trying to resolve and share any relevant information or screenshots\\.\n\n"
                f"A member of the team will respond as soon as possible\\.\n"
                f"Sent by: {user_link}"
            )
            await query.message.reply_text(
                message,
                reply_markup=get_keyboard(OTHER_TECHNICAL),
                parse_mode="MarkdownV2"
            )
            forwarded = await context.bot.send_message(
                chat_id=PERSONAL_ID,
                text=f"Other Technical Issue selected by {user_link}:\n{message}",
                parse_mode="MarkdownV2"
            )
            user_messages[user.id]["last_message"] = message
            user_messages[user.id]["forwarded_message_id"] = forwarded.message_id
            context.user_data["state"] = OTHER_TECHNICAL
            context.user_data["state_history"].append(OTHER_TECHNICAL)
            return OTHER_TECHNICAL

        elif data == "partnership":
            message = (
                f"You have selected Partnership Request 🤝\n\n"
                f"Hey, we are excited that you want to collaborate with us\\!\n"
                f"To get started, please provide the following information:\n\n"
                f"1\\) Your name/alias\n"
                f"2\\) The organization you represent\n"
                f"3\\) The organization’s website address & social profiles\n"
                f"4\\) A detailed description of the proposed partnership\n"
                f"5\\) Anything else relevant\n\n"
                f"A member of the team will respond as soon as possible\\.\n"
                f"Sent by: {user_link}"
            )
            await query.message.reply_text(
                message,
                reply_markup=get_keyboard(PARTNERSHIP),
                parse_mode="MarkdownV2"
            )
            forwarded = await context.bot.send_message(
                chat_id=PERSONAL_ID,
                text=f"Partnership Request selected by {user_link}:\n{message}",
                parse_mode="MarkdownV2"
            )
            user_messages[user.id]["last_message"] = message
            user_messages[user.id]["forwarded_message_id"] = forwarded.message_id
            context.user_data["state"] = PARTNERSHIP
            context.user_data["state_history"].append(PARTNERSHIP)
            return PARTNERSHIP

        elif data == "something_else":
            message = (
                f"You have selected Something Else ❓\n\n"
                f"If you have already checked our FAQs and can’t find the answer you are looking for then please message the team below\\.\n\n"
                f"Please provide as much detail as possible, and if applicable, share screenshots so a team member can help you as quickly as possible\\.\n"
                f"Sent by: {user_link}"
            )
            await query.message.reply_text(
                message,
                reply_markup=get_keyboard(SOMETHING_ELSE),
                parse_mode="MarkdownV2"
            )
            forwarded = await context.bot.send_message(
                chat_id=PERSONAL_ID,
                text=f"Something Else selected by {user_link}:\n{message}",
                parse_mode="MarkdownV2"
            )
            user_messages[user.id]["last_message"] = message
            user_messages[user.id]["forwarded_message_id"] = forwarded.message_id
            context.user_data["state"] = SOMETHING_ELSE
            context.user_data["state_history"].append(SOMETHING_ELSE)
            return SOMETHING_ELSE

        elif data == "direct_chat":
            message = (
                f"You have selected Direct Chat 🗣️\n\n"
                f"Please send your message, and a team member will respond as soon as possible\\.\n"
                f"Sent by: {user_link}"
            )
            await query.message.reply_text(
                message,
                reply_markup=get_keyboard(DIRECT_CHAT),
                parse_mode="MarkdownV2"
            )
            forwarded = await context.bot.send_message(
                chat_id=PERSONAL_ID,
                text=f"Direct Chat selected by {user_link}:\n{message}",
                parse_mode="MarkdownV2"
            )
            user_messages[user.id]["last_message"] = message
            user_messages[user.id]["forwarded_message_id"] = forwarded.message_id
            context.user_data["state"] = DIRECT_CHAT
            context.user_data["state_history"].append(DIRECT_CHAT)
            return DIRECT_CHAT

    except TelegramError as e:
        logger.error(f"Error in button_callback: {e}")
        await query.message.reply_text("An error occurred. Please try again later.", parse_mode="MarkdownV2")
        context.user_data["state_history"].append(MAIN_MENU)
        return MAIN_MENU

    return MAIN_MENU

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user messages in different states."""
    user = update.effective_user
    user_link = f"[{escape_markdown_v2(user.first_name)}](tg://user?id={user.id})"
    state = context.user_data.get("state", MAIN_MENU)
    message_text = escape_markdown_v2(update.message.text)

    # Initialize user data if not present
    if user.id not in user_messages:
        user_messages[user.id] = {
            "username": user.first_name,
            "user_id": user.id,
            "last_message": message_text,
        }

    try:
        # Forward user message to your personal ID
        forwarded_message = f"Message from {user_link}:\n{message_text}"
        forwarded = await context.bot.send_message(
            chat_id=PERSONAL_ID,
            text=forwarded_message,
            parse_mode="MarkdownV2"
        )

        # Store the message and forwarded message ID
        user_messages[user.id]["last_message"] = message_text
        user_messages[user.id]["forwarded_message_id"] = forwarded.message_id

        # Respond to the user
        await update.message.reply_text(
            f"Thank you for your message, {user_link}\\! {escape_markdown_v2(ADMIN_USERNAME)} will respond soon\\.",
            reply_markup=get_keyboard(state),
            parse_mode="MarkdownV2"
        )
    except TelegramError as e:
        logger.error(f"Error in handle_user_message: {e}")
        await update.message.reply_text("An error occurred. Please try again later.", parse_mode="MarkdownV2")

    return state

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle replies from the admin to forward to the user."""
    if update.effective_chat.id != PERSONAL_ID:
        return

    # Check if the message is a reply to another message
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "Please reply to a user's message to send a response\\.",
            parse_mode="MarkdownV2"
        )
        return

    original_message = update.message.reply_to_message.text
    logger.info(f"Original message: {original_message}")  # Debug log

    # Try to extract user ID from the original message
    match = re.search(r'\[.*?\]\(tg://user\?id=(\d+)\)', original_message, re.IGNORECASE)
    if match:
        user_id = int(match.group(1))
    else:
        # Fallback: Check if the replied message ID matches a forwarded message
        replied_message_id = update.message.reply_to_message.message_id
        user_id = None
        for uid, data in user_messages.items():
            if data.get("forwarded_message_id") == replied_message_id:
                user_id = uid
                break
        if not user_id:
            await update.message.reply_text(
                f"Could not identify the user to reply to\\. Original message:\n{escape_markdown_v2(original_message)}\nEnsure you're replying to a forwarded user message\\.",
                parse_mode="MarkdownV2"
            )
            return

    reply_text = escape_markdown_v2(update.message.text)
    user_link = f"[{escape_markdown_v2(user_messages.get(user_id, {}).get('username', 'User'))}](tg://user?id={user_id})"

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"Response from {escape_markdown_v2(ADMIN_USERNAME)}:\n{reply_text}\n\nSent to: {user_link}",
            reply_markup=get_keyboard(context.user_data.get("state", MAIN_MENU)),
            parse_mode="MarkdownV2"
        )
        await update.message.reply_text(f"Reply sent to {user_link}\\.", parse_mode="MarkdownV2")
    except BadRequest as e:
        logger.error(f"BadRequest in handle_admin_reply: {e}")
        await update.message.reply_text(
            f"Failed to send reply to {user_link}\\. Error: User may have blocked the bot or is invalid\\.",
            parse_mode="MarkdownV2"
        )
    except RetryAfter as e:
        logger.error(f"RetryAfter in handle_admin_reply: {e}")
        await asyncio.sleep(e.retry_after)
        await context.bot.send_message(
            chat_id=user_id,
            text=f"Response from {escape_markdown_v2(ADMIN_USERNAME)}:\n{reply_text}\n\nSent to: {user_link}",
            reply_markup=get_keyboard(context.user_data.get("state", MAIN_MENU)),
            parse_mode="MarkdownV2"
        )
        await update.message.reply_text(f"Reply sent to {user_link} after retry\\.", parse_mode="MarkdownV2")
    except TelegramError as e:
        logger.error(f"Error in handle_admin_reply: {e}")
        await update.message.reply_text(
            f"Failed to send reply to {user_link}\\. Error: {escape_markdown_v2(str(e))}\\.",
            parse_mode="MarkdownV2"
        )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    user = update.effective_user
    user_link = f"[{escape_markdown_v2(user.first_name)}](tg://user?id={user.id})"
    try:
        await update.message.reply_text(
            f"Goodbye, {user_link}\\! Feel free to reach out again\\.",
            parse_mode="MarkdownV2"
        )
    except TelegramError as e:
        logger.error(f"Error in cancel: {e}")
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    try:
        application = Application.builder().token(BOT_TOKEN).build()

        # Define the conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                MAIN_MENU: [CallbackQueryHandler(button_callback)],
                TECHNICAL_SUPPORT: [CallbackQueryHandler(button_callback)],
                BUG_REPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message), CallbackQueryHandler(button_callback)],
                OTHER_TECHNICAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message), CallbackQueryHandler(button_callback)],
                PARTNERSHIP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message), CallbackQueryHandler(button_callback)],
                SOMETHING_ELSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message), CallbackQueryHandler(button_callback)],
                DIRECT_CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message), CallbackQueryHandler(button_callback)],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )

        # Add handlers
        application.add_handler(conv_handler)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Chat(PERSONAL_ID), handle_admin_reply))

        # Start the bot
        application.run_polling()
    except TelegramError as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == "__main__":
    main()