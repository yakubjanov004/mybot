# MyBot

This repository contains a Telegram bot used by clients and company staff such as admins and call‑center operators. The project is organized into multiple modules under the `handlers/`, `database/`, and `keyboards/` folders.

## Support Chat Workflow

The bot includes a support chat feature that allows call‑center operators (and admins) to communicate with clients through the bot. A typical flow works as follows:

1. **Operator starts a chat**
   - From the call‑center menu operators choose the **"💬 Chat"** option after selecting a client, or they can send the command `chat`/`чат`.
   - The bot creates a chat session and shows inline buttons from `support_chat_buttons.py`.
   - The main actions are:
     - **✍️ Javob yozish** (`chat:reply`) – begin chatting with the chosen client.
     - **❌ Chatni yopish** (`chat:close`) – end the current session (the bot asks for confirmation via `chat:close_confirm`).

2. **Client replies**
   - Clients simply type messages in the bot chat. Every incoming message from one side is immediately forwarded to the other side so that both participants see updates in real time.
   - Clients do not need special commands; they just send text or media while the chat is active.

3. **Ending the conversation**
   - Operators can finish the session with the **❌ Chatni yopish** button and confirm to close.
   - Once closed, no further forwarding occurs until a new chat is started.

This mechanism lets the call‑center handle client issues directly within Telegram while keeping a record of messages in the `chat_sessions` and `chat_messages` tables.
