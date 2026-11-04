// handlers/message.js — Handles all incoming user messages in Telegram Serverless
import { api } from 'sdk';
import { db, eq, desc, count } from 'sdk/db';
import { emotions, userStates, customFeelings } from '../schema.js';
import {
  isAuthorized,
  getSenderName,
  getPartnerInfo,
  USER_A_ID,
  USER_B_ID,
} from '../lib/config.js';
import {
  getMainReplyKeyboard,
  buildEmotionGrid,
  buildPartnerKeyboard,
} from '../lib/keyboards.js';

export default async function handleMessage(message, ctx) {
  const user = message.from;
  const chatId = message.chat.id;
  const text = (message.text || '').trim();

  // 1. Authorization check
  if (!user || !isAuthorized(user.id)) {
    const uid = user ? user.id : 'Unknown';
    const name = user ? user.first_name : 'Anonymous';
    await api.sendMessage({
      chat_id: chatId,
      text:
        `🔒 *TwoTone is an exclusive couple space.*\n\n` +
        `Your Telegram ID is: \`${uid}\`\nName: ${name}\n\n` +
        `Only authorized partners can access this bot.`,
      parse_mode: 'Markdown',
    });
    return;
  }

  // 2. /myid
  if (text === '/myid') {
    const status = isAuthorized(user.id)
      ? '✅ Authorized Partner'
      : '🔒 Not authorized';
    await api.sendMessage({
      chat_id: chatId,
      text:
        `🆔 *Your Telegram Identity*\n\n` +
        `• **User ID**: \`${user.id}\`\n` +
        `• **Name**: ${user.first_name}\n` +
        `• **Username**: @${user.username || 'none'}\n` +
        `• **Status**: ${status}`,
      parse_mode: 'Markdown',
      reply_markup: getMainReplyKeyboard(),
    });
    return;
  }

  // 3. /cancel
  if (text === '/cancel') {
    await db.delete(userStates).where(eq(userStates.userId, user.id)).run();
    await api.sendMessage({
      chat_id: chatId,
      text: '🤍 Cancelled. Take gentle care of yourself.',
      reply_markup: getMainReplyKeyboard(),
    });
    return;
  }

  // 4. /start
  if (text === '/start') {
    const senderName = getSenderName(user.id);
    const { partnerName } = getPartnerInfo(user.id);
    await db.delete(userStates).where(eq(userStates.userId, user.id)).run();

    await api.sendMessage({
      chat_id: chatId,
      text:
        `🤍 *Welcome to TwoTone, ${senderName}*\n\n` +
        `This is your shared, private haven with *${partnerName}*.\n\n` +
        `Whenever something is hard to voice directly—or whenever you feel ` +
        `love, fatigue, or sensitivity—tap **🌱 Share a Feeling** below.\n\n` +
        `Use the buttons at the bottom of your screen anytime.`,
      parse_mode: 'Markdown',
      reply_markup: getMainReplyKeyboard(),
    });
    return;
  }

  // 5. Help / Guide
  if (text === '❓ Guide' || text === '/help') {
    await api.sendMessage({
      chat_id: chatId,
      text:
        `🕊️ *TwoTone Guide*\n\n` +
        `TwoTone helps you communicate feelings without confrontation, defensiveness, ` +
        `or vulnerability fatigue.\n\n` +
        `✨ *How to Use:*\n` +
        `1. Tap **🌱 Share a Feeling** below.\n` +
        `2. Tap your emotion from the grid.\n` +
        `3. Tap what you need right now ➔ *Delivered instantly with care!*\n\n` +
        `✨ *Navigation:*\n` +
        `• **🌱 Share a Feeling** — Send an emotion card in 2 taps.\n` +
        `• **📖 Journal** — Review past feelings and mutual acknowledgments.\n` +
        `• **📊 Insights** — View emotional balance & counts.\n` +
        `• **✨ Custom Feelings** — Manage couple inside tags.\n` +
        `• \`/cancel\` — Reset any prompt.\n\n` +
        `_Everything you send is private, gentle, and delivered only to your partner._`,
      parse_mode: 'Markdown',
      reply_markup: getMainReplyKeyboard(),
    });
    return;
  }

  // 6. Share a Feeling
  if (text === '🌱 Share a Feeling' || text === '/feel') {
    await db.delete(userStates).where(eq(userStates.userId, user.id)).run();
    const cfs = await db.select().from(customFeelings).all();

    await api.sendMessage({
      chat_id: chatId,
      text:
        `🌱 *Step 1 of 2: How are you feeling right now?*\n\n` +
        `Tap the emotion that speaks to your current state:`,
      parse_mode: 'Markdown',
      reply_markup: buildEmotionGrid(cfs),
    });
    return;
  }

  // 7. Journal / History
  if (text === '📖 Journal' || text === '/history') {
    const list = await db
      .select()
      .from(emotions)
      .orderBy(desc(emotions.id))
      .limit(7)
      .all();

    if (!list || list.length === 0) {
      await api.sendMessage({
        chat_id: chatId,
        text:
          `📖 *Emotional Journal*\n\n` +
          `No feelings recorded yet. Whenever either of you shares a feeling ` +
          `using **🌱 Share a Feeling**, your shared history will be preserved here.`,
        parse_mode: 'Markdown',
        reply_markup: getMainReplyKeyboard(),
      });
      return;
    }

    const lines = ['📖 *Shared Emotional Timeline (Recent)*\n'];
    for (const e of list) {
      const senderName = getSenderName(e.senderId);
      const timeStr = (e.createdAt || '').slice(0, 16).replace('T', ' ');
      const status = e.reactionLabel
        ? `✅ *${e.reactionLabel}*`
        : `⏳ _Pending acknowledgment_`;
      const noteStr = e.note ? `  📝 _${e.note}_\n` : '';
      const replyStr = e.replyNote ? `  💬 _Reply: ${e.replyNote}_\n` : '';

      lines.push(
        `• *${timeStr}* — From *${senderName}*\n` +
          `  💭 ${e.emotionLabel}\n` +
          `  🎯 ${e.needLabel}\n` +
          `${noteStr}` +
          `  Status: ${status}\n` +
          `${replyStr}`
      );
    }

    await api.sendMessage({
      chat_id: chatId,
      text: lines.join('\n'),
      parse_mode: 'Markdown',
      reply_markup: getMainReplyKeyboard(),
    });
    return;
  }

  // 8. Insights / Stats
  if (text === '📊 Insights' || text === '/stats') {
    const all = await db.select().from(emotions).all();
    const total = all.length;
    const acked = all.filter((e) => e.acknowledgedAt).length;
    const pct = total > 0 ? Math.round((acked / total) * 100) : 0;

    await api.sendMessage({
      chat_id: chatId,
      text:
        `📊 *TwoTone Shared Insights*\n\n` +
        `• Total feelings shared: **${total}**\n` +
        `• Acknowledged with care: **${acked}** (${pct}%)\n\n` +
        `_Every feeling shared is an act of vulnerability and trust._ 🤍`,
      parse_mode: 'Markdown',
      reply_markup: getMainReplyKeyboard(),
    });
    return;
  }

  // 9. Custom Feelings management
  if (text === '✨ Custom Feelings' || text === '/list_feelings') {
    const cfs = await db.select().from(customFeelings).all();
    if (!cfs || cfs.length === 0) {
      await api.sendMessage({
        chat_id: chatId,
        text:
          `✨ *No custom feelings added yet.*\n\n` +
          `Use \`/add_feeling\` to create your first personal feeling tag!`,
        parse_mode: 'Markdown',
        reply_markup: getMainReplyKeyboard(),
      });
      return;
    }

    const inline_keyboard = cfs.map((cf) => [
      { text: `${cf.emoji} ${cf.feelingName}`, callback_data: 'noop' },
      { text: '🗑️ Delete', callback_data: `del_cf:${cf.id}` },
    ]);

    await api.sendMessage({
      chat_id: chatId,
      text: `✨ *Your Couple Custom Feelings:*\nTap 🗑️ to delete any tag:`,
      parse_mode: 'Markdown',
      reply_markup: { inline_keyboard },
    });
    return;
  }

  // 10. Add Feeling command
  if (text === '/add_feeling') {
    await db
      .insert(userStates)
      .values({
        userId: user.id,
        state: 'ADD_FEELING_NAME',
        data: {},
        updatedAt: new Date().toISOString(),
      })
      .onConflictDoUpdate({
        target: userStates.userId,
        set: { state: 'ADD_FEELING_NAME', data: {}, updatedAt: new Date().toISOString() },
      })
      .run();

    await api.sendMessage({
      chat_id: chatId,
      text:
        `✨ *Add a Couple Feeling*\n\n` +
        `Type the name of your custom feeling tag (e.g. _"Missing our morning tea"_ or _"Need silly banter"_):\n\n` +
        `Type \`/cancel\` to abort.`,
      parse_mode: 'Markdown',
    });
    return;
  }

  // 11. Check active user state
  const curState = await db
    .select()
    .from(userStates)
    .where(eq(userStates.userId, user.id))
    .get();

  if (curState) {
    // A. Attaching optional note to emotion
    if (curState.state === 'ATTACH_NOTE') {
      const feelData = curState.data || {};
      const { partnerId, senderName, partnerName } = getPartnerInfo(user.id);
      const note = text;

      // Log to database
      const inserted = await db
        .insert(emotions)
        .values({
          senderId: user.id,
          recipientId: partnerId,
          emotionKey: feelData.emotionKey || 'unknown',
          emotionLabel: feelData.emotionLabel || 'Feeling',
          needKey: feelData.needKey || 'no_reply',
          needLabel: feelData.needLabel || 'No words needed',
          note: note,
          createdAt: new Date().toISOString(),
        })
        .returning({ id: emotions.id });

      const logId = inserted[0]?.id;

      // Send Card to Partner
      const noteLine = note ? `\n📝 *Note*: _${note}_\n` : '';
      const cardText =
        `💌 *TwoTone Message*\n` +
        `From: *${senderName}*\n\n` +
        `💭 *Feeling*: ${feelData.emotionLabel}\n` +
        `🎯 *Need*: ${feelData.needLabel}` +
        `${noteLine}\n` +
        `_Take a gentle breath. No pressure to fix anything—just holding space for each other._`;

      try {
        const sent = await api.sendMessage({
          chat_id: partnerId,
          text: cardText,
          parse_mode: 'Markdown',
          reply_markup: buildPartnerKeyboard(logId),
        });
        await db
          .update(emotions)
          .set({ recipientMessageId: sent.message_id })
          .where(eq(emotions.id, logId))
          .run();
      } catch (err) {
        console.error('Failed to deliver card to partner:', err);
      }

      // Confirmation to Sender
      await api.sendMessage({
        chat_id: chatId,
        text:
          `🕊️ *Your feeling was delivered to ${partnerName} with care.*\n\n` +
          `• **Feeling**: ${feelData.emotionLabel}\n` +
          `• **Need**: ${feelData.needLabel}` +
          `${noteLine}\n` +
          `You will be notified when they acknowledge it 🤍.`,
        parse_mode: 'Markdown',
        reply_markup: getMainReplyKeyboard(),
      });

      await db.delete(userStates).where(eq(userStates.userId, user.id)).run();
      return;
    }

    // B. Replying gently to a partner's card
    if (curState.state === 'REPLY_NOTE') {
      const logId = curState.data?.logId;
      const { partnerId, senderName, partnerName } = getPartnerInfo(user.id);

      if (logId) {
        await db
          .update(emotions)
          .set({ replyNote: text })
          .where(eq(emotions.id, logId))
          .run();
      }

      // Deliver gentle reply to partner
      try {
        await api.sendMessage({
          chat_id: partnerId,
          text:
            `💌 *Gentle reply from ${senderName}:*\n\n` +
            `_${text}_\n\n` +
            `_Delivered with warmth._`,
          parse_mode: 'Markdown',
        });
      } catch (err) {
        console.error('Failed to deliver reply note:', err);
      }

      await api.sendMessage({
        chat_id: chatId,
        text: `🕊️ Delivered to ${partnerName}.`,
        reply_markup: getMainReplyKeyboard(),
      });

      await db.delete(userStates).where(eq(userStates.userId, user.id)).run();
      return;
    }

    // C. Add Custom Feeling: Name received
    if (curState.state === 'ADD_FEELING_NAME') {
      await db
        .update(userStates)
        .set({
          state: 'ADD_FEELING_EMOJI',
          data: { name: text },
          updatedAt: new Date().toISOString(),
        })
        .where(eq(userStates.userId, user.id))
        .run();

      await api.sendMessage({
        chat_id: chatId,
        text:
          `Great! Name: *${text}*\n\n` +
          `Now, send **one or two emojis** for this feeling (e.g. 🍵 or 🧸):`,
        parse_mode: 'Markdown',
      });
      return;
    }

    // D. Add Custom Feeling: Emoji received
    if (curState.state === 'ADD_FEELING_EMOJI') {
      const name = curState.data?.name || 'Custom Feeling';
      const emoji = text;
      const { partnerId, senderName } = getPartnerInfo(user.id);

      await db.insert(customFeelings).values({
        userId: user.id,
        feelingName: name,
        emoji: emoji,
        createdAt: new Date().toISOString(),
      }).run();

      await api.sendMessage({
        chat_id: chatId,
        text:
          `✨ *Saved to your couple catalog!*\n\n` +
          `${emoji} *${name}*\n\n` +
          `You can now pick this in **🌱 Share a Feeling**.`,
        parse_mode: 'Markdown',
        reply_markup: getMainReplyKeyboard(),
      });

      try {
        await api.sendMessage({
          chat_id: partnerId,
          text:
            `✨ *${senderName} added a new feeling to your couple catalog:*\n\n` +
            `${emoji} *${name}*`,
          parse_mode: 'Markdown',
        });
      } catch {}

      await db.delete(userStates).where(eq(userStates.userId, user.id)).run();
      return;
    }
  }

  // Default fallback for unrecognized text
  await api.sendMessage({
    chat_id: chatId,
    text: `Tap **🌱 Share a Feeling** below to send an emotion card.`,
    parse_mode: 'Markdown',
    reply_markup: getMainReplyKeyboard(),
  });
}
