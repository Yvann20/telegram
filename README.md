# Meu Bot Telegram

Este é um bot do Telegram que permite encaminhar mensagens de um chat para outros grupos, preservando a formatação e emojis Premium. O bot é configurável e pode enviar mensagens em intervalos definidos pelo usuário.

## Funcionalidades

- **Encaminhamento de Mensagens**: O bot pode encaminhar mensagens de um chat específico para grupos em que você está.
- **Configuração de Intervalos**: Permite definir um intervalo em minutos para o encaminhamento das mensagens.
- **Formatação de Mensagens**: Suporta envio de mensagens formatadas em Markdown ou HTML.

## Requisitos

Para executar este bot, você precisará de:

- Python 3.x
- As seguintes bibliotecas:
  - `python-telegram-bot`
  - `telethon`

Você pode instalar as dependências usando o `pip`:

```bash
pip install python-telegram-bot telethon

Configuração

Antes de executar o bot, configure as credenciais no código:

API_ID = 'coloque seu id'  # Seu API ID
API_HASH = 'sua hash'  # Seu API Hash
BOT_TOKEN = 'coloque aqui'  # Token do bot
YOUR_PHONE = 'seu numero'  # Seu número do Telegram

Autenticação

O bot solicitará que você faça a autenticação usando seu número de telefone. Você receberá um código para autenticar o bot.

Comandos

/set_message_link <link>: Configura o link da mensagem que será encaminhada.

/set_interval <minutos>: Define o intervalo em minutos para o encaminhamento das mensagens.

/send_formatted_message: Envia uma mensagem de exemplo com formatação.


Execução

Para executar o bot, utilize o seguinte comando:

python bot.py

Após a execução, o bot estará em funcionamento e aguardará comandos.

Contribuições

Sinta-se à vontade para contribuir para este projeto. Faça um fork do repositório, faça suas alterações e envie um pull request!

Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.
