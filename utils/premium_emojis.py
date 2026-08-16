"""Ryhavean Userbot — premium (custom) emoji reyestri.

Bu modul `emoji_utils` mənbəyindən gələn BÜTÜN premium emoji ID-lərini saxlayır
və həm bot, həm də userbot tərəfində istifadə olunur.

İstifadə:
    from utils.premium_emojis import pe, premiumize

    pe("🚀")            -> '<emoji id="6035191085452497972">🚀</emoji>'
    premiumize("Salam 🚀")  -> mətndəki bütün emojiləri premium teqlərə çevirir
"""

from __future__ import annotations

import re
import random
from typing import Dict, List, Optional

# ============================================================
# Premium Emoji ID xəritəsi
# ============================================================
PREMIUM_EMOJI_MAP: Dict[str, int] = {
    '👥': 4942888689131848546,
    '🎙️': 5408866986908201757,
    '🥰': 5235779074734968128,
    '🐺': 5442740582222941322,
    '♥️': 5379806980485421889,
    '🚀': 6035191085452497972,
    '🦅': 5413424754663122711,
    '🛑': 5852974782932323756,
    '⛔️': 5316653661105961462,
    '🪜': 5427083257470542447,
    '🌅': 5472089304937278565,
    '🔍': 5258274739041883702,
    '🆔': 5422388085121885096,
    '🌦️': 5391055925035415864,
    '🌡️': 5839411778722729805,
    '🌬️': 6332347924063717264,
    '💬': 5296258510684712098,
    '♻️': 5377584064326804458,
    '🗑': 5372825386591732174,
    '🎮': 5319247469165433798,
    '🌐': 5456446900901262114,
    '🌌': 5364181936707216367,
    '💾': 5373342633798167891,
    '📌': 5213035264397562073,
    '🔇': 5462990730253319917,
    '🏓': 5335035652981410865,
    '🎵': 5316710964559624097,
    '🎶': 5456126169923461016,
    '🎧': 5278779535683252020,
    '🎤': 5388657954599746804,
    '🎼': 5312546813377538792,
    '👢': 5465287910691455473,
    '⏳': 5212985021870123409,
    '▪': 5445164438426507058,
    '👮': 5962906687076569235,
    '💤': 5409073806763367479,
    '⏱': 5015045170496799920,
    '📝': 5215672443036772796,
    '😎': 5332377304448382437,
    '🥳': 5460929352109661725,
    '🤩': 5271815649939712712,
    '😻': 5203909786038443975,
    '🦄': 5312093732982510667,
    '🎷': 5467793203769933478,
    '🎸': 5471947489412128060,
    '🥁': 5852466430603169101,
    '🎨': 5431456208487716895,
    '📚': 5222444124698853913,
    '🛡': 5406935230877542714,
    '👤': 5346136537123801643,
    '🧬': 5438527189240787734,
    '✅': 5325538810275055890,
    '❌': 5436400368680450044,
    '⚠️': 5436308005408748533,
    'ℹ️': 6021618194228187816,
    '✔': 5350479625233395106,
    '❎': 4981202335737841455,
    '⛔': 5269770107340463723,
    '🚫': 5433834155785860591,
    '🆗': 5413737982333036649,
    '🆘': 5456626761246710338,
    '👏': 5843609817196794825,
    '🪨': 5253928829138785309,
    '🔢': 5287478403530767368,
    '🎱': 5136368178313561364,
    '🏳': 5467773141977670129,
    '❤️': 5465514676374746733,
    '💖': 5418341487194679878,
    '💕': 5195322046174748092,
    '💗': 5206256461679724808,
    '💞': 5292009027092378537,
    '💓': 5361857268478411449,
    '💝': 5290007284569627555,
    '💘': 5362051254971299115,
    '🧡': 5434147173002394272,
    '💛': 5345951651666615438,
    '💚': 5343881924106536026,
    '💙': 5206225752663548044,
    '💜': 5278747280478856642,
    '🖤': 5359359371333631914,
    '🤍': 5213148582814687024,
    '🤎': 5359732101480459887,
    '😀': 5821450070872035646,
    '🏹': 5206296361925878286,
    '💍': 5346076059689313891,
    '😍': 5465262274031659421,
    '😁': 6030394496041095796,
    '😂': 5456536919120813753,
    '🤣': 5850615733490290324,
    '😃': 5850343174865686224,
    '😄': 5204468157556733956,
    '😅': 5388650872198673917,
    '🙂': 5893406853437592859,
    '👻': 5359458146991481670,
    '💀': 5850424233783463073,
    '☠️': 5850176087752969770,
    '🤖': 5237689785425877860,
    '👽': 5188377706580342082,
    '👾': 5328150734506578613,
    '🇬🇪': 5350547232313599612,
    '⭐': 5341684837881235158,
    '🌟': 5343968167049839023,
    '✨': 5444957708765651221,
    '💫': 5469744063815102906,
    '🔥': 5212920133504212456,
    '💧': 5393512611968995988,
    '💦': 5850660345315594866,
    '☀️': 5458683354796806976,
    '🌙': 5474256979226541985,
    '⚡': 5877419533462933948,
    '❄️': 5364049247987578747,
    '🌈': 5350748331272334914,
    '☁️': 5983106326291554558,
    '💎': 5422555575961529062,
    '👑': 5271557007009128936,
    '🎁': 5420637379142625713,
    '🎉': 5391041468175495220,
    '🎊': 5204213715104184074,
    '🎈': 5388865049332823409,
    '💰': 5435999124245729290,
    '💵': 5291961954250794534,
    '💸': 5868527276122970322,
    '💳': 5240066289614987080,
    '🪙': 5467683093693354332,
    '📱': 5847950362685739628,
    '💻': 5852840084167987100,
    '⌨️': 5458569525278547985,
    '🖥️': 5334692506569288756,
    '🖱️': 5317059204802952215,
    '📷': 5197347179089392925,
    '📸': 5413628812854311979,
    '🎥': 6334554201519031929,
    '📹': 5375309569905938163,
    '📺': 5373330964372004748,
    '📡': 5413337163100083587,
    '🔋': 5248977066853943059,
    '🔌': 6332131440532129426,
    '📞': 5391192208642682468,
    '☎️': 5287324742485835162,
    '📧': 4970246557065544891,
    '📨': 5454113432284446338,
    '📩': 5472239203590888751,
    '📬': 5350421256627838238,
    '🏦': 5264895611517300926,
    '🎬': 6325351379388860506,
    '📰': 5434144690511290129,
    '🦠': 5296407803747903306,
    '💶': 5400320027758969855,
    '🌀': 5888999340818566791,
    '📐': 6334362276610443521,
    '🎴': 5341570699125355662,
    '🧠': 5319074132875295093,
    '💡': 5222253479690509955,
    '🏠': 5237952409791130101,
    '🔗': 5375129357373165375,
    '👁': 5156829295137522301,
    '🍴': 5866042019066942400,
    '📦': 5409380072291316349,
    '📛': 5215371279929976844,
    '🐙': 5267028539521114904,
    '🛰': 5467403607286502523,
    '📍': 5330088116944380969,
    '🏙': 5406686715479860449,
    '🌤': 5283075860188898177,
    '🐍': 5409076727341130651,
    '🔔': 5373136788900571050,
    '🔤': 5242615494439084286,
    '🧮': 5837157590907227857,
    '📮': 5235691513236706804,
    '➡️': 6037622221625626773,
    '⬅️': 6039539366177541657,
    '⬆️': 5963103826075456248,
    '⬇️': 6039802767931871481,
    '↗️': 5422706058730675684,
    '↘️': 6035353688619356485,
    '↙️': 5260260723329608328,
    '↖️': 5190779220611066696,
    '🔄': 6030657343744644592,
    '🔁': 5346269127059196142,
    '🔂': 5346269127059196142,
    '⚙️': 5393199882515277922,
    '🛠️': 5863945989127148135,
    '🔧': 5258023599419171861,
    '🔨': 5456312597273923475,
    '🔒': 5393302369024882368,
    '🔓': 5393302369024882368,
    '🔑': 5836690092306992715,
    '🗝️': 5836690092306992715,
    '📁': 5298853345241358103,
    '📂': 5298853345241358103,
    '📄': 5411334681842966198,
    '📃': 5370604433233177619,
    '📑': 5251632825521696687,
    '📊': 5028325978175177540,
    '📈': 5244837092042750681,
    '📉': 5301037284571759350,
    '🗂️': 5298853345241358103,
    '📋': 5197269100878907942,
    '✏️': 6273749645134925942,
    '🖊️': 5334673106202010226,
    '🖋️': 5389057773105328621,
    '📤': 5433614747381538714,
    '📖': 5319135825785529051,
    '🎭': 5276157818926300661,
    '🎌': 5431538972507522948,
    '🌍': 5465166522030764559,
    '🌎': 5465166522030764559,
    '🌏': 5465166522030764559,
    '🗺️': 5388916717789393938,
    '🧭': 5433825729060018456,
    '⏰': 5188377706580342082,
    '⏱️': 5195352914104694560,
    '⏲️': 5359535585251838264,
    '🕐': 5348236797606379943,
    '📅': 5265168676948035250,
    '📆': 5265168676948035250,
    '🗓️': 5265168676948035250,
    '🏳️\u200d🌈': 5850532823441607662,
    '🇦🇿': 5224542095963859210,
    '🇷🇺': 5398017006165305287,
}

# `.song` üçün təsadüfi premium emoji ID-ləri
SONG_PREMIUM_EMOJI_IDS: List[int] = [
    5244489483159609086,  # 🎵
    5411371652921435502,  # 🎶
    5363988860747400777,  # 🎧
]
SONG_EMOJI_CHAR: List[str] = ["🎵", "🎶", "🎧"]

# ============================================================
# Dinamik reyestr: PREMIUM_EMOJI_MAP + data/custom_emoji_ids.json
# ============================================================
_registry_cache: Optional[Dict[str, int]] = None
_pattern_cache: Optional["re.Pattern[str]"] = None


def _extra_registry() -> Dict[str, int]:
    """data/custom_emoji_ids.json faylındakı əlavə custom emojiləri oxuyur."""
    extra: Dict[str, int] = {}
    try:
        import json
        from pathlib import Path

        path = Path(__file__).resolve().parent.parent / "data" / "custom_emoji_ids.json"
        if not path.exists():
            return extra
        payload = json.loads(path.read_text(encoding="utf-8"))
        for pack in payload or []:
            for item in pack.get("items", []):
                emoji = item.get("emoji")
                doc_id = item.get("document_id")
                if emoji and doc_id is not None and emoji not in extra:
                    extra[emoji] = int(doc_id)
    except Exception:  # fayl pozulubsa sistem yenə işləməlidir
        return {}
    return extra


def registry() -> Dict[str, int]:
    """Bütün emoji -> premium ID xəritəsi (əl ilə yazılan + JSON dump)."""
    global _registry_cache
    if _registry_cache is None:
        merged = dict(_extra_registry())
        merged.update(PREMIUM_EMOJI_MAP)  # əl ilə seçilənlər üstündür
        # Variation selector-siz variantları da əlavə et (🎙 <-> 🎙️)
        for emoji, eid in list(merged.items()):
            bare = emoji.replace("\ufe0f", "")
            if bare and bare not in merged:
                merged[bare] = eid
            if not emoji.endswith("\ufe0f") and (emoji + "\ufe0f") not in merged:
                merged[emoji + "\ufe0f"] = eid
        _registry_cache = merged
    return _registry_cache


def _pattern() -> "re.Pattern[str]":
    global _pattern_cache
    if _pattern_cache is None:
        keys = sorted(registry().keys(), key=len, reverse=True)
        _pattern_cache = re.compile("|".join(re.escape(k) for k in keys)) if keys else re.compile(r"(?!x)x")
    return _pattern_cache


def register(emoji: str, document_id: int) -> None:
    """Runtime-da yeni premium emoji əlavə edir (məs. `.addemoji`)."""
    global _registry_cache, _pattern_cache
    PREMIUM_EMOJI_MAP[emoji] = int(document_id)
    _registry_cache = None
    _pattern_cache = None


# Artıq premium teq içində olan hissələri qorumaq üçün
_EXISTING_TAG_RE = re.compile(r"<emoji[^>]*>.*?</emoji>", re.S)
# HTML/markdown kod bloklarına toxunmuruq
_CODE_RE = re.compile(r"<pre.*?</pre>|<code.*?</code>|```.*?```|`[^`\n]+`", re.S)


def emoji_id(emoji: str) -> Optional[int]:
    """Verilmiş emoji üçün premium ID qaytarır (yoxdursa None)."""
    return registry().get(emoji)


def pe(emoji: str, fallback: Optional[str] = None) -> str:
    """Emojini Telegram premium emoji HTML teqinə çevirir."""
    visible = fallback if fallback is not None else emoji
    eid = registry().get(emoji)
    if eid is None:
        return visible
    return f'<emoji id="{eid}">{visible}</emoji>'


def random_song_emoji() -> str:
    """`.song` üçün təsadüfi premium musiqi emojisi."""
    idx = random.randrange(len(SONG_PREMIUM_EMOJI_IDS))
    return f'<emoji id="{SONG_PREMIUM_EMOJI_IDS[idx]}">{SONG_EMOJI_CHAR[idx]}</emoji>'


def _convert_chunk(chunk: str) -> str:
    reg = registry()

    def _sub(match: "re.Match[str]") -> str:
        ch = match.group(0)
        eid = reg.get(ch)
        return f'<emoji id="{eid}">{ch}</emoji>' if eid else ch

    return _pattern().sub(_sub, chunk)


def premiumize(text: str) -> str:
    """Mətndəki bütün adi emojiləri premium emoji teqlərinə çevirir.

    Toxunulmayan hissələr: artıq mövcud `<emoji>` teqləri, `<code>`/`<pre>`
    blokları və markdown kod parçaları.
    """
    if not text:
        return text
    protected = []
    for rx in (_EXISTING_TAG_RE, _CODE_RE):
        for m in rx.finditer(text):
            protected.append((m.start(), m.end()))
    protected.sort()

    # Üst-üstə düşən aralıqları birləşdir
    merged = []
    for start, end in protected:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    out: List[str] = []
    pos = 0
    for start, end in merged:
        out.append(_convert_chunk(text[pos:start]))
        out.append(text[start:end])
        pos = end
    out.append(_convert_chunk(text[pos:]))
    return "".join(out)


def available_emojis() -> List[str]:
    return sorted(registry().keys())
