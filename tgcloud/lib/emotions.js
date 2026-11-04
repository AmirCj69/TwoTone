// Emotion and needs catalogs

export const EMOTION_GRID = [
  // Vulnerable
  ['unseen', '🌫️ Unseen', 'Unseen / Overlooked 🌫️'],
  ['fragile', '🫧 Sensitive', 'Fragile / Sensitive today 🫧'],
  ['insecure', '🥺 Reassurance', 'Craving reassurance 🥺'],
  ['distant', '🪟 Disconnected', 'Feeling disconnected 🪟'],
  // Affection
  ['missing', '💭 Missing you', 'Missing you deeply 💭'],
  ['tender_love', '🤍 Love you', 'Full of love for you 🤍'],
  ['grateful', '✨ Grateful', 'Deeply grateful for you ✨'],
  ['crush', '🦋 Butterflies', 'Crushing on you / Butterflies 🦋'],
  // Heavy & Friction
  ['overwhelmed', '🌊 Overwhelmed', 'Overwhelmed / Stressed 🌊'],
  ['stung', '🩹 Stung / Hurt', 'Something stung / hurt 🩹'],
  ['exhausted', '🪫 Low battery', 'Social / Emotional battery empty 🪫'],
  ['frustrated', '⚡ Frustrated', 'Frustrated (need decompression) ⚡'],
  // Comfort & Closeness
  ['cuddles', '🛋️ Cuddle craving', 'Cuddle craving 🛋️'],
  ['quiet_presence', '☕ Quiet presence', 'Want quiet presence next to me ☕'],
  ['longing', '🕯️ Longing', 'Longing for you 🕯️'],
  ['walk', '🌿 Fresh air', 'Want fresh air / a walk together 🌿'],
];

export const NEEDS_CATALOG = [
  ['no_reply', '🕊️ No words needed, just know'],
  ['hug_later', '🫂 Warm hug when we see each other'],
  ['talk_tonight', '🌙 Can we talk gently tonight?'],
  ['give_space', '🧘 A little quiet space for now'],
  ['reassurance', '💌 Words of comfort & reassurance'],
  ['listen_only', "👂 Just listen, don't fix anything"],
  ['distraction', '🎈 Make me laugh / distract me'],
  ['hold_hands', '🤝 Hold my hand / sit with me'],
];

export const QUICK_REACTIONS = [
  ['ack_hear', '🤍 I hear you'],
  ['ack_hug', '🫂 Sending a warm hug'],
  ['ack_space', '🕊️ Giving you space'],
  ['ack_soon', '⏳ On my way / Talk soon'],
  ['ack_love', '✨ Love you so much'],
];

export function findEmotionLabel(key) {
  const item = EMOTION_GRID.find(([k]) => k === key);
  return item ? item[2] : key;
}

export function findNeedLabel(key) {
  const item = NEEDS_CATALOG.find(([k]) => k === key);
  return item ? item[1] : key;
}

export function findReactionLabel(key) {
  const item = QUICK_REACTIONS.find(([k]) => k === key);
  return item ? item[1] : key;
}
