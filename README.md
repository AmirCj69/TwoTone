# TwoTone 🤍
### *A gentle, private Telegram bot for couples to communicate emotions without defensiveness.*

---

## 🕊️ Overview

**TwoTone** is deployed and running directly on **Telegram's Native Serverless Cloud platform** (`tgcloud`). It runs 24/7 on Telegram's official V8 infrastructure without needing your computer on, a VPS, or any external servers.

---

## ✨ Features

1. **🔒 Private 1-on-1 Relay**
   - Strictly locked to **Amir** (`499080623`) and **Ghazal** (`634034210`).
   - Uninvited users are rejected automatically.
2. **📱 Always-On Bottom Navigation Bar**
   - `🌱 Share a Feeling` — Opens the emotion picker instantly.
   - `📖 Journal` — Reviews shared past feelings & responses.
   - `📊 Insights` — Shared emotional balance & statistics.
   - `✨ Custom Feelings` — Manage couple inside tags.
   - `❓ Guide` — Friendly help & guidance.
3. **🌱 Streamlined 2-Tap Emotion Delivery**
   - **Tap 1**: Pick your feeling from a visual 2-column grid (`🌫️ Unseen`, `🤍 Love you`, `🌊 Overwhelmed`, `🛋️ Cuddles`, etc.).
   - **Tap 2**: Tap what you need (`🕊️ No words needed`, `🫂 Warm hug`, `🌙 Talk tonight`, etc.) ➔ **Delivered instantly to your partner! 💌**
   - *(Optional note)*: If you want to type context, tap `[ ✍️ Add a note first ]`.
4. **🤍 1-Click Acknowledgments & Gentle Replies**
   - Partner receives a gentle card with 1-click reactions: `🤍 I hear you`, `🫂 Sending a hug`, `🕊️ Giving space`, `⏳ Talk soon`, `✨ Love you so much`.
   - Plus an optional `[ 💬 Gentle Reply ]` button.
   - Sender is instantly notified when their feeling is acknowledged.

---

## ☁️ Telegram Serverless Deployment Commands

The bot is already deployed and running live on Telegram Cloud!
If you ever want to edit code or push updates in the future:

1. **Deploy code to Telegram Cloud**:
   ```bash
   npx tgcloud push
   ```
2. **Apply database migrations**:
   ```bash
   npx tgcloud migrate --yes
   ```
3. **Check Cloud Webhook Status**:
   ```bash
   npx tgcloud webhook
   ```

---

## 🤍 Live Bot Details

- **Bot Username**: [@TWTone_bot](https://t.me/TWTone_bot)
- **Status**: Live 24/7 on Telegram's Serverless Cloud (`https://cloud.telegram.org/app7889785504/webhook`)
- **Partner A**: Amir (`499080623`)
- **Partner B**: Ghazal (`634034210`)
