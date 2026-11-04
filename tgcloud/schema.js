import { table, integer, text, json, index } from 'sdk/db';

export const emotions = table('emotions', {
  id:                 integer('id').primaryKey({ autoIncrement: true }),
  senderId:           integer('sender_id').notNull(),
  recipientId:        integer('recipient_id').notNull(),
  emotionKey:         text('emotion_key').notNull(),
  emotionLabel:       text('emotion_label').notNull(),
  needKey:            text('need_key').notNull(),
  needLabel:          text('need_label').notNull(),
  note:               text('note'),
  createdAt:          text('created_at').notNull(),
  acknowledgedAt:     text('acknowledged_at'),
  reactionKey:        text('reaction_key'),
  reactionLabel:      text('reaction_label'),
  replyNote:          text('reply_note'),
  recipientMessageId: integer('recipient_message_id'),
});

export const userStates = table('user_states', {
  userId:    integer('user_id').primaryKey(),
  state:     text('state').notNull(),
  data:      json('data'),
  updatedAt: text('updated_at').notNull(),
});

export const customFeelings = table('custom_feelings', {
  id:          integer('id').primaryKey({ autoIncrement: true }),
  userId:      integer('user_id').notNull(),
  feelingName: text('feeling_name').notNull(),
  emoji:       text('emoji').notNull(),
  createdAt:   text('created_at').notNull(),
});
