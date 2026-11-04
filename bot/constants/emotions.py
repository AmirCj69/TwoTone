"""Curated catalog of emotion categories, sub-emotions, actionable needs, and reactions."""

# Complete grid for fast 2-tap mood picking
EMOTION_GRID = [
    # Vulnerable
    ("unseen", "🌫️ Unseen", "Unseen / Overlooked 🌫️", "vulnerable"),
    ("fragile", "🫧 Sensitive", "Fragile / Sensitive today 🫧", "vulnerable"),
    ("insecure", "🥺 Reassurance", "Craving reassurance 🥺", "vulnerable"),
    ("distant", "🪟 Disconnected", "Feeling disconnected 🪟", "vulnerable"),
    # Affection
    ("missing", "💭 Missing you", "Missing you deeply 💭", "affection"),
    ("tender_love", "🤍 Love you", "Full of love for you 🤍", "affection"),
    ("grateful", "✨ Grateful", "Deeply grateful for you ✨", "affection"),
    ("crush", "🦋 Butterflies", "Crushing on you / Butterflies 🦋", "affection"),
    # Heavy & Friction
    ("overwhelmed", "🌊 Overwhelmed", "Overwhelmed / Stressed 🌊", "heavy"),
    ("stung", "🩹 Stung / Hurt", "Something stung / hurt 🩹", "heavy"),
    ("exhausted", "🪫 Low battery", "Social / Emotional battery empty 🪫", "heavy"),
    ("frustrated", "⚡ Frustrated", "Frustrated (need decompression) ⚡", "heavy"),
    # Comfort & Closeness
    ("cuddles", "🛋️ Cuddle craving", "Cuddle craving 🛋️", "comfort"),
    ("quiet_presence", "☕ Quiet presence", "Want quiet presence next to me ☕", "comfort"),
    ("longing", "🕯️ Longing", "Longing for you 🕯️", "vulnerable"),
    ("walk", "🌿 Fresh air", "Want fresh air / a walk together 🌿", "comfort"),
]

EMOTION_CATEGORIES = {
    "vulnerable": {
        "label": "🌱 Vulnerable & Tender",
        "items": [
            ("unseen", "Unseen / Overlooked 🌫️"),
            ("fragile", "Fragile / Sensitive today 🫧"),
            ("insecure", "Craving reassurance 🥺"),
            ("distant", "Feeling disconnected 🪟"),
            ("longing", "Longing for you 🕯️"),
        ],
    },
    "affection": {
        "label": "🤍 Warmth & Affection",
        "items": [
            ("missing", "Missing you deeply 💭"),
            ("tender_love", "Full of love for you 🤍"),
            ("grateful", "Deeply grateful for you ✨"),
            ("crush", "Crushing on you / Butterflies 🦋"),
        ],
    },
    "heavy": {
        "label": "🌧️ Heavy & Friction",
        "items": [
            ("overwhelmed", "Overwhelmed / Stressed 🌊"),
            ("stung", "Something stung / hurt 🩹"),
            ("frustrated", "Frustrated (need decompression) ⚡"),
            ("exhausted", "Social / Emotional battery empty 🪫"),
        ],
    },
    "comfort": {
        "label": "🛋️ Comfort & Closeness",
        "items": [
            ("cuddles", "Cuddle craving 🛋️"),
            ("quiet_presence", "Want quiet presence next to me ☕"),
            ("walk", "Want fresh air / a walk together 🌿"),
        ],
    },
}

NEEDS_CATALOG = [
    ("no_reply", "🕊️ No words needed, just know"),
    ("hug_later", "🫂 Warm hug when we see each other"),
    ("talk_tonight", "🌙 Can we talk gently tonight?"),
    ("give_space", "🧘 A little quiet space for now"),
    ("reassurance", "💌 Words of comfort & reassurance"),
    ("listen_only", "👂 Just listen, don't fix anything"),
    ("distraction", "🎈 Make me laugh / distract me"),
    ("hold_hands", "🤝 Hold my hand / sit with me"),
]

QUICK_REACTIONS = [
    ("ack_hear", "🤍 I hear you"),
    ("ack_hug", "🫂 Sending a warm hug"),
    ("ack_space", "🕊️ Giving you space"),
    ("ack_soon", "⏳ On my way / Talk soon"),
    ("ack_love", "✨ Love you so much"),
]


def find_emotion_label(emotion_key: str) -> str:
    """Find human-readable full emotion label by key."""
    for key, _, full_label, _ in EMOTION_GRID:
        if key == emotion_key:
            return full_label
    for category in EMOTION_CATEGORIES.values():
        for key, label in category["items"]:
            if key == emotion_key:
                return label
    return emotion_key


def find_need_label(need_key: str) -> str:
    """Find human-readable need label by key."""
    for key, label in NEEDS_CATALOG:
        if key == need_key:
            return label
    return need_key


def find_reaction_label(reaction_key: str) -> str:
    """Find human-readable reaction label by key."""
    for key, label in QUICK_REACTIONS:
        if key == reaction_key:
            return label
    return reaction_key
