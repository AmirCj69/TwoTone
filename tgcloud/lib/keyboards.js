import { EMOTION_GRID, NEEDS_CATALOG } from './emotions.js';

export function getMainReplyKeyboard() {
  return {
    keyboard: [
      [{ text: '🌱 Share a Feeling' }],
      [{ text: '📖 Journal' }, { text: '📊 Insights' }],
      [{ text: '✨ Custom Feelings' }, { text: '❓ Guide' }],
    ],
    resize_keyboard: true,
  };
}

export function buildEmotionGrid(customFeelings = []) {
  const inline_keyboard = [];

  for (let i = 0; i < EMOTION_GRID.length; i += 2) {
    const row = [
      { text: EMOTION_GRID[i][1], callback_data: `emo:${EMOTION_GRID[i][0]}` },
    ];
    if (i + 1 < EMOTION_GRID.length) {
      row.push({
        text: EMOTION_GRID[i + 1][1],
        callback_data: `emo:${EMOTION_GRID[i + 1][0]}`,
      });
    }
    inline_keyboard.push(row);
  }

  if (customFeelings && customFeelings.length > 0) {
    let cfRow = [];
    for (const cf of customFeelings) {
      cfRow.push({
        text: `${cf.emoji} ${cf.feelingName}`,
        callback_data: `emo:custom_${cf.id}`,
      });
      if (cfRow.length === 2) {
        inline_keyboard.push(cfRow);
        cfRow = [];
      }
    }
    if (cfRow.length > 0) {
      inline_keyboard.push(cfRow);
    }
  }

  inline_keyboard.push([{ text: '❌ Cancel', callback_data: 'feel_cancel' }]);
  return { inline_keyboard };
}

export function buildNeedsKeyboard() {
  const inline_keyboard = NEEDS_CATALOG.map(([key, label]) => [
    { text: label, callback_data: `need_send:${key}` },
  ]);

  inline_keyboard.push([
    { text: '✍️ Add a note first', callback_data: 'need_add_note' },
  ]);

  inline_keyboard.push([
    { text: '🔙 Back', callback_data: 'back:to_emotions' },
    { text: '❌ Cancel', callback_data: 'feel_cancel' },
  ]);

  return { inline_keyboard };
}

export function buildPartnerKeyboard(logId) {
  return {
    inline_keyboard: [
      [
        { text: '🤍 I hear you', callback_data: `react:${logId}:ack_hear` },
        { text: '🫂 Sending a hug', callback_data: `react:${logId}:ack_hug` },
      ],
      [
        { text: '🕊️ Giving space', callback_data: `react:${logId}:ack_space` },
        { text: '⏳ Talk soon', callback_data: `react:${logId}:ack_soon` },
      ],
      [
        { text: '✨ Love you', callback_data: `react:${logId}:ack_love` },
        { text: '💬 Gentle Reply', callback_data: `reply:${logId}` },
      ],
    ],
  };
}
