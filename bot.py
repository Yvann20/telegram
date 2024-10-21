import os
from dotenv import load_dotenv
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
YOUR_PHONE = os.getenv('YOUR_PHONE')

client = TelegramClient('session_name', API_ID, API_HASH)

# Estados da conversação
LINK, INTERVAL, REFERRAL = range(3)

# Armazenar as configurações
settings = {
    'message_link': None,
    'referral_link': None,
    'user_id': None,
}

# Armazenar o job atual
current_job = None

# Estatísticas do bot
statistics = {
    'messages_sent': 0,
    'active_campaigns': 0,
}

# Agendador para tarefas automatizadas
scheduler = AsyncIOScheduler()

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

# Função para listar grupos onde o bot é administrador
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
        await update.message.reply_text(f"Grupos em que você está como administrador:\n" + "\n".join(group_list))
    else:
        await update.message.reply_text("Você não está como administrador em nenhum grupo.")

# Função para encaminhar a mensagem
async def forward_message_with_formatting(context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()  # Início da medição de tempo
    try:
        async with client:
            if settings['message_link'] is None:
                print("Nenhum link de mensagem configurado para encaminhar.")
                return

            parts = settings['message_link'].split('/')
            chat = parts[-2]
            message_id = int(parts[-1])

            message = await client.get_messages(chat, ids=message_id)

            me = await client.get_me()
            async for dialog in client.iter_dialogs():
                if dialog.is_group:
                    participants = await client.get_participants(dialog.entity)
                    if any(participant.id == me.id for participant in participants):
                        try:
                            await client.forward_messages(dialog.entity, message)
                            print(f"Mensagem encaminhada para: {dialog.title}")
                            statistics['messages_sent'] += 1
                        except Exception as e:
                            print(f"Erro ao encaminhar para {dialog.title}: {e}")
    except Exception as e:
        print(f"Erro ao obter a mensagem: {e}")
    finally:
        end_time = time.time()  # Fim da medição de tempo
        print(f"Duração total do job: {end_time - start_time:.2f} segundos")  # Log da duração total do job

# Função para iniciar a campanha
async def start_campaign(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global statistics
    statistics['active_campaigns'] += 1
    query = update.callback_query
    await query.answer()
    await query.message.reply_text('Envie o link da mensagem que deseja encaminhar:')
    print("Esperando o link da mensagem.")
    return LINK

# Função para definir o link da mensagem
async def set_message_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        print("Erro: update.message está None")
        return ConversationHandler.END

    print("Link recebido:", update.message.text)
    settings['message_link'] = update.message.text
    await update.message.reply_text(f"Link configurado: {settings['message_link']}\nAgora envie o intervalo em minutos:")
    print(" Esperando o intervalo.")
    return INTERVAL

# Função para definir o intervalo
async def set_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        print("Erro: update.message está None")
        return ConversationHandler.END

    print("Intervalo recebido:", update.message.text)

    # Remover o ponto final , se existir
    interval_text = update.message.text.strip().rstrip('.')
    
    try:
        interval = int(interval_text)
    except ValueError:
        await update.message.reply_text("Por favor, insira um número válido.")
        return INTERVAL

    global current_job
    if current_job is not None:
        current_job.schedule_removal()

    current_job = context.application.job_queue.run_repeating(
        forward_message_with_formatting, 
        interval=interval * 60, 
        first=0
    )

    await update.message.reply_text(f"SUCESSO... CONFIGURADO {interval} MINUTOS")
    print(f"Job de encaminhamento configurado para {interval} minutos.")
    return ConversationHandler.END

# Função para cancelar o encaminhamento da campanha
async def cancel_campaign(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_job, statistics
    if current_job is not None:
        current_job.schedule_removal()
        current_job = None
        settings['message_link'] = None
        statistics['active_campaigns'] -= 1
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("Encaminhamento de mensagens cancelado.")
        print("Encaminhamento de mensagens cancelado.")
    else:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("Nenhuma campanha ativa para cancelar.")
        print("Nenhuma campanha ativa para cancelar.")

    return ConversationHandler.END

# Função para cancelar a conversação
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operação cancelada.")
    return ConversationHandler.END

# Função para responder ao comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌊 CRIAR CAMPANHA", callback_data='create_campaign')],
        [InlineKeyboardButton("❌ CANCELAR CAMPANHA", callback_data='cancel_campaign')],
        [InlineKeyboardButton("📊 ESTATÍSTICAS DO BOT", callback_data='statistics')],
        [InlineKeyboardButton("🔗 LINK DE REFERÊNCIA", callback_data='referral')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Bem-vindo! Escolha uma ação:', reply_markup=reply_markup)

# Função para exibir estatísticas do bot
async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    stats_message = (
        "Estatísticas do Bot:\n"
        f"Mensagens enviadas: {statistics['messages_sent']}\n"
        f"Campanhas ativas: {statistics['active_campaigns']}\n"
    )
    await update.callback_query.message.reply_text(stats_message)

# Função ppara definir o link de referência
async def set_referral_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    settings['referral_link'] = f"https://t.me/MEIA_GIL_BOT?start=ref_{user_id}"
    await update.callback_query.message.reply_text(f"Seu link de referência: {settings['referral_link']}")

# Função principal para configurar o bot
def main():
    client.loop.run_until_complete(authenticate())
    print("BOT CONECTADO")

    # Configuração do bot
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Configurar o ConversationHandler para o fluxo da campanha
    campaign_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_campaign, pattern='create_campaign')],
        states={
            LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_message_link)],
            INTERVAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_interval)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Adicionar handlers ao bot
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list_groups", list_groups))
    application.add_handler(CallbackQueryHandler(show_statistics, pattern='statistics'))
    application.add_handler(CallbackQueryHandler(set_referral_link, pattern='referral'))
    application.add_handler(CallbackQueryHandler(cancel_campaign, pattern='cancel_campaign'))
    application .add_handler(campaign_handler)

    # Iniciar o bot
    application.run_polling()

if __name__ == '__main__':
    main()
