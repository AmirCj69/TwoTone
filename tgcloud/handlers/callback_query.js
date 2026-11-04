// handlers/callback_query.js — Handles all inline button clicks in Telegram Serverless
import { api } from 'sdk';
import { db, eq } from 'sdk/db';
import { emotions, userStates, customFeelings } from '../schema.js';
import {
  isAuthorized,
  getSenderName,
  getPartnerInfo,
} from '../lib/config.js';
import {
  findEmotionLabel,
  findNeedLabel,
  findReactionLabel,
} from '../lib/emotions.js';
import {
  buildEmotionGrid,
  buildNeedsKeyboard,
  buildPartnerKeyboard,
} from '../lib/keyboards.js';

export default async function handleCallbackQuery(query, ctx) {
  const user = query.from;
  const data = query.data || '';
  const message = query.message;
  const chatId = message ? message.chat.id : user.id;
  const messageId = message ? message.message_id : null;

  if (!user || !isAuthorized(user.id)) {
    await api.answerCallbackQuery({
      callback_query_id: query.id,
      text: 'Unauthorized.',
      show_alert: true,
    });
    return;
  }

  // 1. Cancel
  if (data === 'feel_cancel') {
    await db.delete(userStates).where(eq(userStates.userId, user.id)).run();
    await api.answerCallbackQuery({ callback_query_id: query.id });
    if (messageId) {
      await api.editMessageText({
        chat_id: chatId,
        message_id: messageId,
        text: '🤍 Cancelled. Take gentle care of yourself.',
      });
    }
    return;
  }

  // 2. Select Emotion (Step 1 -> Step 2)
  if (data.startsWith('emo:')) {
    await api.answerCallbackQuery({ callback_query_id: query.id });
    const emoKey = data.split(':', 2)[1];

    let emoLabel = '';
    if (emoKey.startsWith('custom_')) {
      const cfId = parseInt(emoKey.replace('custom_', ''), 10);
      const cf = await db
        .select()
        .from(customFeelings)
        .where(eq(customFeelings.id, cfId))
        .get();
      emoLabel = cf ? `${cf.emoji} ${cf.feelingName}` : 'Custom Feeling';
    } else {
      emoLabel = findEmotionLabel(emoKey);
    }

    // Save selection in user states
    await db
      .insert(userStates)
      .values({
        userId: user.id,
        state: 'SELECT_NEED',
        data: { emotionKey: emoKey, emotionLabel: emoLabel },
        updatedAt: new Date().toISOString(),
      })
      .onConflictDoUpdate({
        target: userStates.userId,
        set: {
          state: 'SELECT_NEED',
          data: { emotionKey: emoKey, emotionLabel: emoLabel },
          updatedAt: new Date().toISOString(),
        },
      })
      .run();

    if (messageId) {
      await api.editMessageText({
        chat_id: chatId,
        message_id: messageId,
        text:
          `💌 *Step 2 of 2: What would help right now?*\n\n` +
          `Selected: *${emoLabel}*\n\n` +
          `Tap a need below to **send immediately** 🚀\n` +
          `_(or tap 'Add a note first' if you wish to type context)_:`,
        parse_mode: 'Markdown',
        reply_markup: buildNeedsKeyboard(),
      });
    }
    return;
  }

  // 3. Need selected -> 1-Tap Instant Dispatch!
  if (data.startsWith('need_send:')) {
    const needKey = data.split(':', 2)[1];
    const needLabel = findNeedLabel(needKey);

    // Retrieve emotion from user state
    const curState = await db
      .select()
      .from(userStates)
      .where(eq(userStates.userId, user.id))
      .get();
    const feelData = curState?.data || {};
    const emoLabel = feelData.emotionLabel || 'Feeling';
    const emoKey = feelData.emotionKey || 'unknown';

    const { partnerId, senderName, partnerName } = getPartnerInfo(user.id);

    // Insert into emotions log
    const inserted = await db
      .insert(emotions)
      .values({
        senderId: user.id,
        recipientId: partnerId,
        emotionKey: emoKey,
        emotionLabel: emoLabel,
        needKey: needKey,
        needLabel: needLabel,
        createdAt: new Date().toISOString(),
      })
      .returning({ id: emotions.id });

    const logId = inserted[0]?.id;

    // Send card to partner
    const cardText =
      `💌 *TwoTone Message*\n` +
      `From: *${senderName}*\n\n` +
      `💭 *Feeling*: ${emoLabel}\n` +
      `🎯 *Need*: ${needLabel}\n\n` +
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
      console.error('Failed to send card to partner:', err);
    }

    await api.answerCallbackQuery({
      callback_query_id: query.id,
      text: 'Delivered with care 🤍',
    });

    // Update sender's message to confirmation
    if (messageId) {
      await api.editMessageText({
        chat_id: chatId,
        message_id: messageId,
        text:
          `🕊️ *Your feeling was delivered to ${partnerName} with care.*\n\n` +
          `• **Feeling**: ${emoLabel}\n` +
          `• **Need**: ${needLabel}\n\n` +
          `You will be notified when they acknowledge it 🤍.`,
        parse_mode: 'Markdown',
      });
    }

    await db.delete(userStates).where(eq(userStates.userId, user.id)).run();
    return;
  }

  // 4. User wants to add a note first
  if (data === 'need_add_note') {
    await api.answerCallbackQuery({ callback_query_id: query.id });
    const curState = await db
      .select()
      .from(userStates)
      .where(eq(userStates.userId, user.id))
      .get();
    const feelData = curState?.data || {};

    await db
      .update(userStates)
      .set({
        state: 'ATTACH_NOTE',
        data: feelData,
        updatedAt: new Date().toISOString(),
      })
      .where(eq(userStates.userId, user.id))
      .run();

    const { partnerName } = getPartnerInfo(user.id);
    if (messageId) {
      await api.editMessageText({
        chat_id: chatId,
        message_id: messageId,
        text:
          `✍️ *Add a note for ${partnerName}:*\n\n` +
          `• **Feeling**: ${feelData.emotionLabel || 'Feeling'}\n\n` +
          `Type your message below and press send in Telegram.\n` +
          `Or tap **Send As Is** if you change your mind.`,
        parse_mode: 'Markdown',
        reply_markup: {
          inline_keyboard: [
            [{ text: '🚀 Send As Is (No Note)', callback_data: 'send_now' }],
            [
              { text: '🔙 Back to Needs', callback_data: 'back:to_needs' },
              { text: '❌ Cancel', callback_data: 'feel_cancel' },
            ],
          ],
        },
      });
    }
    return;
  }

  // 5. Send now without note
  if (data === 'send_now') {
    const curState = await db
      .select()
      .from(userStates)
      .where(eq(userStates.userId, user.id))
      .get();
    const feelData = curState?.data || {};
    const emoLabel = feelData.emotionLabel || 'Feeling';
    const emoKey = feelData.emotionKey || 'unknown';
    const needKey = feelData.needKey || 'no_reply';
    const needLabel = feelData.needLabel || 'No words needed';

    const { partnerId, senderName, partnerName } = getPartnerInfo(user.id);

    const inserted = await db
      .insert(emotions)
      .values({
        senderId: user.id,
        recipientId: partnerId,
        emotionKey: emoKey,
        emotionLabel: emoLabel,
        needKey: needKey,
        needLabel: needLabel,
        createdAt: new Date().toISOString(),
      })
      .returning({ id: emotions.id });

    const logId = inserted[0]?.id;

    const cardText =
      `💌 *TwoTone Message*\n` +
      `From: *${senderName}*\n\n` +
      `💭 *Feeling*: ${emoLabel}\n` +
      `🎯 *Need*: ${needLabel}\n\n` +
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
    } catch {}

    await api.answerCallbackQuery({
      callback_query_id: query.id,
      text: 'Delivered with care 🤍',
    });

    if (messageId) {
      await api.editMessageText({
        chat_id: chatId,
        message_id: messageId,
        text:
          `🕊️ *Your feeling was delivered to ${partnerName} with care.*\n\n` +
          `• **Feeling**: ${emoLabel}\n` +
          `• **Need**: ${needLabel}\n\n` +
          `You will be notified when they acknowledge it 🤍.`,
        parse_mode: 'Markdown',
      });
    }

    await db.delete(userStates).where(eq(userStates.userId, user.id)).run();
    return;
  }

  // 6. Back navigation
  if (data === 'back:to_emotions') {
    await api.answerCallbackQuery({ callback_query_id: query.id });
    const cfs = await db.select().from(customFeelings).all();
    if (messageId) {
      await api.editMessageText({
        chat_id: chatId,
        message_id: messageId,
        text:
          `🌱 *Step 1 of 2: How are you feeling right now?*\n\n` +
          `Tap the emotion that speaks to your current state:`,
        parse_mode: 'Markdown',
        reply_markup: buildEmotionGrid(cfs),
      });
    }
    return;
  }

  // 7. Reaction by Partner (Acknowledgment)
  if (data.startsWith('react:')) {
    const parts = data.split(':');
    const logId = parseInt(parts[1], 10);
    const reactionKey = parts[2];
    const reactionLabel = findReactionLabel(reactionKey);

    const entry = await db
      .select()
      .from(emotions)
      .where(eq(emotions.id, logId))
      .get();

    if (!entry) {
      await api.answerCallbackQuery({
        callback_query_id: query.id,
        text: 'Entry not found.',
        show_alert: true,
      });
      return;
    }

    if (user.id !== entry.recipientId) {
      await api.answerCallbackQuery({
        callback_query_id: query.id,
        text: 'Only the receiving partner can acknowledge this card.',
        show_alert: true,
      });
      return;
    }

    // Update in database
    await db
      .update(emotions)
      .set({
        acknowledgedAt: new Date().toISOString(),
        reactionKey: reactionKey,
        reactionLabel: reactionLabel,
      })
      .where(eq(emotions.id, logId))
      .run();

    await api.answerCallbackQuery({
      callback_query_id: query.id,
      text: `Sent: ${reactionLabel}`,
    });

    // Edit recipient's card to show acknowledgment
    const { senderName, partnerName } = getPartnerInfo(entry.senderId);
    const noteLine = entry.note ? `\n📝 *Note*: _${entry.note}_\n` : '';

    if (messageId) {
      await api.editMessageText({
        chat_id: chatId,
        message_id: messageId,
        text:
          `💌 *TwoTone Message*\n` +
          `From: *${senderName}*\n\n` +
          `💭 *Feeling*: ${entry.emotionLabel}\n` +
          `🎯 *Need*: ${entry.needLabel}` +
          `${noteLine}\n` +
          `✅ *You acknowledged this with*: ${reactionLabel}`,
        parse_mode: 'Markdown',
        reply_markup: {
          inline_keyboard: [
            [
              {
                text: '💬 Send Gentle Follow-up Note',
                callback_data: `reply:${logId}`,
              },
            ],
          ],
        },
      });
    }

    // Send warm instant notification to original sender
    try {
      await api.sendMessage({
        chat_id: entry.senderId,
        text:
          `🤍 *${partnerName} acknowledged your feeling*\n\n` +
          `• **Your feeling**: ${entry.emotionLabel}\n` +
          `• **Their response**: ${reactionLabel}\n\n` +
          `_You are held, heard, and cared for._`,
        parse_mode: 'Markdown',
      });
    } catch (err) {
      console.error('Failed to notify sender:', err);
    }
    return;
  }

  // 8. Partner wants to send a gentle reply
  if (data.startsWith('reply:')) {
    const logId = parseInt(data.split(':', 2)[1], 10);
    await api.answerCallbackQuery({ callback_query_id: query.id });

    await db
      .insert(userStates)
      .values({
        userId: user.id,
        state: 'REPLY_NOTE',
        data: { logId: logId },
        updatedAt: new Date().toISOString(),
      })
      .onConflictDoUpdate({
        target: userStates.userId,
        set: {
          state: 'REPLY_NOTE',
          data: { logId: logId },
          updatedAt: new Date().toISOString(),
        },
      })
      .run();

    await api.sendMessage({
      chat_id: chatId,
      text:
        `💬 *Send a gentle reply:*\n\n` +
        `Type your comforting thoughts or reassurance below and hit send.\n` +
        `Or type \`/cancel\` to skip.`,
      parse_mode: 'Markdown',
    });
    return;
  }

  // 9. Delete custom feeling
  if (data.startsWith('del_cf:')) {
    const cfId = parseInt(data.split(':', 2)[1], 10);
    await db.delete(customFeelings).where(eq(customFeelings.id, cfId)).run();
    await api.answerCallbackQuery({
      callback_query_id: query.id,
      text: 'Custom feeling deleted.',
      show_alert: true,
    });

    const cfs = await db.select().from(customFeelings).all();
    if (!cfs || cfs.length === 0) {
      if (messageId) {
        await api.editMessageText({
          chat_id: chatId,
          message_id: messageId,
          text: `✨ No custom feelings remaining. Use \`/add_feeling\` to create one!`,
          parse_mode: 'Markdown',
        });
      }
    } else {
      const inline_keyboard = cfs.map((cf) => [
        { text: `${cf.emoji} ${cf.feelingName}`, callback_data: 'noop' },
        { text: '🗑️ Delete', callback_data: `del_cf:${cf.id}` },
      ]);
      if (messageId) {
        await api.editMessageText({
          chat_id: chatId,
          message_id: messageId,
          text: `✨ *Your Couple Custom Feelings:*\nTap 🗑️ to delete any tag:`,
          parse_mode: 'Markdown',
          reply_markup: { inline_keyboard },
        });
      }
    }
    return;
  }

  await api.answerCallbackQuery({ callback_query_id: query.id });
}
