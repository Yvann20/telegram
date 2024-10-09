import time
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# Credenciais do bot e do Telegram pessoal
API_ID = 23129461  # Seu API ID (número inteiro)
API_HASH = 'b0c258c2960ea95cd0eb10aab621d3d2'  # Seu API Hash
BOT_TOKEN = '7319901594:AAEsqnyAmiM-kvRciDejjcYs53cUo94J2WE'  # Token do bot
YOUR_PHONE = '+5511914392234'  # Seu número do Telegram

client = TelegramClient('session_name', API_ID, API_HASH)

# Armazenar as configurações
settings = {
    'message_link': None,  # Link da mensagem a ser encaminhada
    'interval': 1,  # Intervalo padrão em minutos (pode ser ajustado pelo bot)
}

# Autenticação para enviar mensagens
async def authenticate():
    await client.start()
    if not await client.is_user_authorized():
        try:
            await client.send_code_request(YOUR_PHONE)
            code = input('Digite o código recebido: ')
            await client.sign_in(YOUR_PHONE, code)
        except SessionPasswordNeededError:
            password = input('Digite sua senha: ')
            await client.sign_in(YOUR_PHONE, password)

# Função para listar grupos em que a sua conta pessoal está presente
async def list_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_list = []
    async with client:
        me = await client.get_me()
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                participants = await client.get_participants(dialog.entity)
                if any(participant.id == me.id for participant in participants):
                    group_list.append(dialog.title)
    
    if group_list:
        await update.message.reply_text(f"Grupos em que você está:\n" + "\n".join(group_list))
    else:
        await update.message.reply_text("Você não está em nenhum grupo.")

# Função para encaminhar a mensagem preservando formatação e emojis Premium
async def forward_message_with_formatting(context: ContextTypes.DEFAULT_TYPE):
    async with client:
        if settings['message_link'] is None:
            print("Nenhum link de mensagem configurado para encaminhar.")
            return
        
        try:
            parts = settings['message_link'].split('/')
            chat = parts[-2]
            message_id = int(parts[-1])

            message = await client.get_messages(chat, ids=message_id)

            me = await client.get_me()
            async for dialog in client.iter_dialogs():
                if dialog.is_group:
                    participants = await client.get_participants(dialog.entity)
                    if any(participant.id == me.id for participant in participants):
                        await client.forward_messages(dialog.entity, message)
                        print(f"Mensagem encaminhada para: {dialog.title}")
        except Exception as e:
            print(f"Erro ao obter a mensagem: {e}")

# Comando para definir o link da mensagem a ser encaminhada
async def set_message_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = context.args[0] if context.args else None
    if link:
        settings['message_link'] = link
        await update.message.reply_text(f"Link da mensagem configurado: {link}")
    else:
        await update.message.reply_text("Por favor, forneça um link.")

# Comando para definir o intervalo
async def set_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        try:
            interval = int(context.args[0])
            settings['interval'] = interval
            await update.message.reply_text(f"Intervalo configurado para {interval} minutos.")
            context.application.job_queue.run_repeating(forward_message_with_formatting, interval=interval * 60, first=0)
        except ValueError:
            await update.message.reply_text("Por favor, forneça um número válido para o intervalo.")
    else:
        await update.message.reply_text("Por favor, forneça um intervalo em minutos.")

# Comando para enviar mensagem com formatação Markdown ou HTML
async def send_formatted_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "Aqui está a mensagem com **negrito**, _itálico_ e [um link](https://example.com)!"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        parse_mode='Markdown'
    )

# Função principal para configurar o bot
def main():
    client.loop.run_until_complete(authenticate())
    print("Bot autenticado e funcionando...")

    # Configuração do bot
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Adicionar comandos ao bot
    application.add_handler(CommandHandler("set_message_link", set_message_link))
    application.add_handler(CommandHandler("set_interval", set_interval))
    application.add_handler(CommandHandler("send_formatted_message", send_formatted_message))
    application.add_handler(CommandHandler("list_groups", list_groups))

    # Iniciar o job de envio repetido com intervalo configurável
    application.job_queue.run_repeating(forward_message_with_formatting, interval=settings['interval'] * 60, first=0)

    # Iniciar o bot
    application.run_polling()

if __name__ == '__main__':
    main()
