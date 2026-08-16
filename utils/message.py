"""
utils/message.py
────────────────
Pre-rendered message constants for the entire bot.

All values are static constants generated at import time.

Integrates styling patterns from:
  - Moon-Userbot  : HTML bold/italic structure, code-block formatting
  - Dragon-Userbot: Clean <b>label:</b> <i>value</i> convention
  - CatUserBot    : Unicode font tables (smallcaps, cursive, fraktur,
                    gothic, bubbles, superscript) for decorative labels

Usage:
    from utils.message import Msg, font

    await message.edit(Msg.ERR_NO_GROUP_CALL)
    await message.edit(Msg.ERR_ADMIN_REQUIRED)
    styled = font.smallcaps("Hello World")
    styled = font.bold_cursive("Playing")
"""
import re
import html

from utils.custom_emojis import (
    CAT,
    CROWN,
    DOWNLOAD,
    DRAGON,
    ERROR,
    FIRE,
    FOLDER,
    GEAR,
    HEART,
    INFO,
    LOADING,
    LOCK,
    USER,
    MIC,
    NOTE,
    MOON,
    MUSIC,
    CHAT,
    LINK,
    ID,
    PIN,
    PARTY,
    ROCKET,
    SHIELD,
    SPARK,
    STAR,
    SEARCH,
    GRID,
    PUZZLE,
    SOLVE,
    PONG,
    SUCCESS,
    THUMBS_UP,
    WARNING,
    WARNING_BOLT,
    WAVE,
    CALENDAR,
    QUESTION,
)


# ─────────────────────────────────────────────────────────────────────────────
# Unicode font-style helpers  (ported from CatUserBot's helpers/fonts.py)
# ─────────────────────────────────────────────────────────────────────────────

_NORMAL = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

_SMALLCAPS = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ0123456789"
_BOLD_CURSIVE = "𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃0123456789"
_DOUBLE = "𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ𝕒𝕓𝕔𝕕𝕖𝕗𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝕧𝕨𝕩𝕪𝕫𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡"


def _translate(text: str, source: str, target) -> str:
    """Map each character in text through the font table."""
    out = []
    for ch in text:
        idx = source.find(ch)
        if idx >= 0:
            out.append(target[idx])
        else:
            out.append(ch)
    return "".join(out)


class _Font:
    """
    Lightweight font-style converter.

    Inspired by CatUserBot's helpers/fonts.py — provides Unicode
    "font" transformations that render distinctively in Telegram.
    """

    def smallcaps(self, text: str) -> str:
        """ᴀʙᴄᴅᴇꜰ — Small-caps style (upper & lower → phonetic IPA)"""
        return _translate(text, _NORMAL, _SMALLCAPS)

    def bold_cursive(self, text: str) -> str:
        """𝓑𝓸𝓵𝓭 𝓒𝓾𝓻𝓼𝓲𝓿𝓮 — Bold cursive/calligraphic style"""
        return _translate(text, _NORMAL, _BOLD_CURSIVE)

    def double(self, text: str) -> str:
        """𝔻𝕠𝕦𝕓𝕝𝕖 — Double-struck style"""
        return _translate(text, _NORMAL, _DOUBLE)


#: Singleton instance; import and call methods directly.
font = _Font()


# ─────────────────────────────────────────────────────────────────────────────
# Message constants
# ─────────────────────────────────────────────────────────────────────────────

class Msg:
    """
    Centralised message constant store.

    Naming convention (matches Moon-Userbot + Dragon-Userbot patterns):
      ERR_*    → error messages
      WARN_*   → warning / access-denied messages
      OK_*     → success confirmations
      INFO_*   → neutral informational messages

    Prefix labels use:
      • Telegram custom emoji tags for Premium emoji display
      • Unicode smallcaps label text (CatUserBot style) for non-premium fallback
      • HTML <b>/<i> wrapping (Dragon-Userbot / Moon-Userbot style)
      • Box-drawing/arrow characters for visual hierarchy
    """

    # ── Custom emoji labels backed by sticker pack ids ──────────────────────
    EMOJI_ERROR   = ERROR
    EMOJI_WARNING = WARNING
    EMOJI_SUCCESS = SUCCESS
    EMOJI_INFO    = INFO

    EMOJI_LOADING = LOADING
    EMOJI_PIN     = PIN
    EMOJI_ROCKET  = ROCKET
    EMOJI_GEAR    = GEAR
    EMOJI_FIRE    = FIRE
    EMOJI_SPARK   = SPARK
    EMOJI_MUSIC   = MUSIC
    EMOJI_MIC     = MIC
    EMOJI_SHIELD  = SHIELD
    EMOJI_LOCK    = LOCK
    EMOJI_CROWN   = CROWN
    EMOJI_DRAGON  = DRAGON
    EMOJI_MOON    = MOON
    EMOJI_CAT     = CAT
    EMOJI_THUMBS_UP = THUMBS_UP
    EMOJI_HEART   = HEART
    EMOJI_PARTY   = PARTY
    EMOJI_WARNING_BOLT = WARNING_BOLT
    EMOJI_FOLDER  = FOLDER
    EMOJI_DOWNLOAD = DOWNLOAD
    EMOJI_NOTE    = NOTE
    EMOJI_WAVE    = WAVE
    EMOJI_CALENDAR = CALENDAR
    EMOJI_QUESTION = QUESTION
    EMOJI_STAR    = STAR
    EMOJI_SEARCH  = SEARCH
    EMOJI_GRID    = GRID
    EMOJI_PUZZLE  = PUZZLE
    EMOJI_SOLVE   = SOLVE
    EMOJI_USER    = USER
    EMOJI_CHAT    = CHAT
    EMOJI_LINK    = LINK
    EMOJI_ID      = ID
    EMOJI_PONG    = PONG


    # ── Prefix labels (Unicode smallcaps label + emoji + box-draw) ───────────
    # Combine: Dragon-Userbot's <b>label:</b> <i>value</i> convention with
    # CatUserBot's Unicode font style for the label itself.
    _ERR_LABEL  = f"<b>{font.smallcaps('Xeta')}</b>"
    _WARN_LABEL = f"<b>{font.smallcaps('Xebardarliq')}</b>"
    _OK_LABEL   = f"<b>{font.smallcaps('Ugurlu')}</b>"
    _INFO_LABEL = f"<b>{font.smallcaps('Melumat')}</b>"

    ERROR_PREFIX   = f'{EMOJI_ERROR} {_ERR_LABEL}\n╰▸ '
    WARNING_PREFIX = f'{EMOJI_WARNING} {_WARN_LABEL}\n╰▸ '
    SUCCESS_PREFIX = f'{EMOJI_SUCCESS} {_OK_LABEL}\n╰▸ '
    INFO_PREFIX    = f'{EMOJI_INFO} {_INFO_LABEL}\n╰▸ '

    # ── Errors ───────────────────────────────────────────────────────────────
    ERR_ADMIN_REQUIRED        = f'{ERROR_PREFIX}Admin Səlahiyyətləri Tələb Olunur'
    ERR_REPLY_USER_OR_ID      = f'{ERROR_PREFIX}İstifadəçiyə Cavab Verin Və Ya İstifadəçi Adı/ID Daxil Edin'
    ERR_REPLY_USER_ID         = f'{ERROR_PREFIX}İstifadəçiyə Cavab Verin Və Ya İstifadəçi ID Daxil Edin'
    ERR_NO_INLINE_RESULTS     = f'{ERROR_PREFIX}Inline Nəticə Tapılmadı'
    ERR_NO_DATA               = f'{ERROR_PREFIX}Məlumat Tapılmadı'
    ERR_INVALID_COUNT         = f'{ERROR_PREFIX}Yanlış Say Nömrəsi'
    ERR_FILE_TOO_LARGE        = f'{ERROR_PREFIX}Fayl 2GB Limitini Aşır. Telegram Premium-a Keçin.'
    ERR_FILE_EXCEEDS_2GB      = f'{ERROR_PREFIX}Fayl 2GB Limitini Aşır'
    ERR_STICKER_ADD_FAILED    = f'{ERROR_PREFIX}Uğursuz Oldu. Sticker Əlavə Etmək Üçün @Stickers Botundan İstifadə Edin.'
    ERR_COUNT_1_100           = f'{ERROR_PREFIX}Say 1-100 Aralığında Olmalıdır'
    ERR_INVALID_COUNT_NUMBER  = f'{ERROR_PREFIX}Yanlış Say! Rəqəm Daxil Edin'
    ERR_CANT_FETCH_USER       = f'{ERROR_PREFIX}Entity-dən İstifadəçi Əldə Edilə Bilmədi'
    ERR_NO_GROUP_CALL         = f'{ERROR_PREFIX}Aktiv Qrup Zəngi Tapılmadı'
    ERR_QUOTE_FAILED          = f'{ERROR_PREFIX}Sitat Yaradılması Uğursuz Oldu'
    ERR_REPLY_PHOTO_OR_STICKER= f'{ERROR_PREFIX}İstənilən Şəkil Və Ya Stickerə Cavab Verin'
    ERR_REPLY_USER_MSG        = f"{ERROR_PREFIX}İstifadəçinin Mesajına Cavab Verin"
    ERR_REPLY_TO_QUOTE        = f'{ERROR_PREFIX}Sitat Yaratmaq Üçün Mesaja Cavab Verin'
    ERR_NO_TEXT_TO_QUOTE      = f'{ERROR_PREFIX}Sitat Üçün Mətn Tapılmadı'
    ERR_GET_USER_INFO_FAILED  = f'{ERROR_PREFIX}İstifadəçi Məlumatı Alına Bilmədi'
    ERR_GENERATE_QUOTE_FAILED = f'{ERROR_PREFIX}Sitat Yaradıla Bilmədi'
    ERR_QUOTE_RETRIES_FAILED  = f'{ERROR_PREFIX}Bir Neçə Cəhddən Sonra Uğursuz Oldu'
    ERR_START_CALL_FAILED     = f'{ERROR_PREFIX}Qrup Zəngi Başladıla Bilmədi'
    ERR_INVALID_CHAT_ID       = f'{ERROR_PREFIX}Yanlış Söhbət ID. Düzgün Tam Ədəd Daxil Edin.'
    ERR_NO_BLACKLIST          = f'{ERROR_PREFIX}Qara Siyahı Tapılmadı'
    ERR_REPLY_TO_STICKER      = f'{ERROR_PREFIX}İstənilən Stickerə Cavab Verin'
    ERR_STICKER_NO_NAME       = f'{ERROR_PREFIX}Stickerin Adı Yoxdur'
    ERR_UNSUPPORTED_FILE      = f'{ERROR_PREFIX}Dəstəklənməyən Fayl Növü'
    ERR_REPLY_PHOTO_STICKER   = f'{ERROR_PREFIX}Şəkil/GIF/Stickerə Cavab Verin'
    ERR_PURGE_REPLY           = f'{ERROR_PREFIX}Silməyə Başlamaq Üçün Mesaja Cavab Verin'
    ERR_REPLY_PURGE_USER      = f"{ERROR_PREFIX}Bütün Mesajlarını Silmək Üçün İstifadəçinin Mesajına Cavab Verin"
    ERR_DELETE_REPLY          = f'{ERROR_PREFIX}Silmək Üçün Mesaja Cavab Verin'
    ERR_UNKNOWN_STYLE         = f'{ERROR_PREFIX}Naməlum Stil. Stilləri Görmək Üçün [Prefix]Fonts İstifadə Edin'
    ERR_SPECIFY_USER          = f'{ERROR_PREFIX}Klonlamaq Üçün İstifadəçi Göstərin'
    ERR_CANT_CLONE_ADMIN      = f'{ERROR_PREFIX}Admin İstifadəçini Klonlamaq Olmaz'
    ERR_NO_CLONE_DATA         = f'{ERROR_PREFIX}Klon Məlumatı Tapılmadı'
    ERR_OWNER_ONLY            = f'{ERROR_PREFIX}Yalnız Sahibə Aid Əmr'
    ERR_PROVIDE_SPAM_TEXT     = f'{ERROR_PREFIX}Spam Üçün Bir Şey Daxil Edin'
    ERR_INVALID_DELAY         = f'{ERROR_PREFIX}Yanlış Gecikmə Dəyəri'
    ERR_GCAST_FLAG            = f'{ERROR_PREFIX}Gcast Bayrağını Daxil Edin'
    ERR_GCAST_USAGE           = f'{ERROR_PREFIX}İstifadə: [Prefix]Gcast [-All|-Pvt|-Grp] [Mesaj/Cavab]'
    ERR_SCHEDULE_FORMAT       = f'{ERROR_PREFIX}Yanlış Format! İstifadə Edin: [Prefix]Schedule <Hədəf> <HH:MM:SS> <MSG>'
    ERR_SCHEDULE_TIME         = f'{ERROR_PREFIX}Yanlış Vaxt! HH:MM:SS Və Ya HH:MM:SS:CC (24-Saatlıq) Formatından İstifadə Edin'
    ERR_SANGMATA_BLOCKED      = f'{ERROR_PREFIX}Bot Bloklanıb. @Sangmata_Beta_Bot Blokunu Açın Və Yenidən Cəhd Edin.'
    ERR_INVALID_CHANNEL       = f'{ERROR_PREFIX}Yanlış Kanal Və Ya Qrup'
    ERR_MMF_USAGE             = f'{ERROR_PREFIX}İstifadə: [Prefix]MMF <Mətn>'
    ERR_UNBAN_PERMISSION      = f'{ERROR_PREFIX}Blokdan Çıxarmaq Üçün İstifadəçiləri İdarəetmə İcazəsi Lazımdır'

    # ── Admin Action Errors ──────────────────────────────────────────────────
    ERR_CANT_BAN_ADMIN      = f'{ERROR_PREFIX}Bu Admini Bloklamaq Olmaz'
    ERR_CANT_KICK_ADMIN     = f'{ERROR_PREFIX}Bu Admini Çıxarmaq Olmaz'
    ERR_CANT_MUTE_ADMIN     = f'{ERROR_PREFIX}Bu Admini Susdurmaq Olmaz'
    ERR_CANT_UNMUTE_ADMIN   = f'{ERROR_PREFIX}Bu Adminin Səsini Açmaq Olmaz'
    ERR_CANT_VERIFY_ADMIN   = f'{ERROR_PREFIX}Admin Səlahiyyətləri Yoxlanıla Bilmədi'
    ERR_USER_ALREADY_ADMIN  = f'{ERROR_PREFIX}İstifadəçi Artıq Admindir Və Ya Yüksəldilə Bilməz'
    ERR_NO_ADMIN_RIGHTS_PIN = f'{ERROR_PREFIX}Sabitləmək Üçün Admin Hüquqları Lazımdır'
    ERR_NO_ADMIN_RIGHTS_UNPIN= f'{ERROR_PREFIX}Sabitliyi Ləğv Etmək Üçün Admin Hüquqları Lazımdır'
    ERR_NO_GRANT_PRIVILEGES = f'{ERROR_PREFIX}Verilməsi Üçün Səlahiyyət Yoxdur'
    ERR_REPLY_TO_PIN        = f'{ERROR_PREFIX}Sabitləmək Üçün Mesaja Cavab Verin'
    ERR_IMAGE_DOC_ONLY      = f'{ERROR_PREFIX}Sənəd Şəkil Növündə Olmalıdır'
    ERR_REPLY_IMAGE_DOC     = f'{ERROR_PREFIX}Şəkil/Sənədə Cavab Verin'
    ERR_PROVIDE_EVAL_CODE   = f'{ERROR_PREFIX}Qiymətləndirmək Üçün Kod Daxil Edin'
    ERR_GCAST_NOTHING       = f'{ERROR_PREFIX}Gcast Üçün Heç Nə Verilməyib'
    ERR_CANT_DM_SPAM_OWNER  = f'{ERROR_PREFIX}Sahibə DM Spam Göndərmək Olmaz'
    ERR_PRIVACY_HISTORY     = f'{ERROR_PREFIX}Tarixçə Əldə Edilə Bilmədi. İstifadəçinin Məxfilik Ayarı Aktiv Ola Bilər.'
    ERR_GROUP_ONLY          = f'{ERROR_PREFIX}Yalnız Qrup'
    ERR_INVALID_COMMAND     = f'{ERROR_PREFIX}Yanlış Əmr'
    ERR_INVALID_NUMBER      = f'{ERROR_PREFIX}Yanlış Rəqəm'
    ERR_NO_RESULTS          = f'{ERROR_PREFIX}Nəticə Tapılmadı'
    ERR_UNSUPPORTED_MEDIA   = f'{ERROR_PREFIX}Dəstəklənməyən Media Növü'

    # ── Warnings ─────────────────────────────────────────────────────────────
    WARN_NOT_AUTHORIZED    = f'{WARNING_PREFIX}İcazə Yoxdur'
    WARN_PRIVATE_RESTRICTED= f'{WARNING_PREFIX}Şəxsi Söhbət Məhdudlaşdırılıb'
    WARN_SESSION_NOT_FOUND = f'{WARNING_PREFIX}Sessiya Tapılmadı'
    WARN_RESTRICTED_DMS    = f'{WARNING_PREFIX}DM-lərdə Məhdudlaşdırılıb'
    WARN_CMD_NOT_FOUND     = f'{WARNING_PREFIX}Əmr Tapılmadı'
    WARN_VC_JOIN_FIRST     = f'{WARNING_PREFIX}İstifadəçiləri Dəvət Etməzdən Əvvəl Qrup Zənginə Qoşulun'
    WARN_NO_QUERY          = f'{WARNING_PREFIX}Sorğu Daxil Edilməyib'
    WARN_REACTIONS_DISABLED= f'{WARNING_PREFIX}Reaksiyalar Deaktivdir'

    # ── Success ───────────────────────────────────────────────────────────────
    OK_USERBOT_STOPPED      = f'{SUCCESS_PREFIX}Userbot Dayandırıldı'
    OK_USERBOT_REBOOTED     = f'{SUCCESS_PREFIX}Userbot Yenidən Başladıldı'
    OK_STICKER_KANGED       = f'{SUCCESS_PREFIX}Sticker Kopyalandı'
    OK_APPROVED_WHITELIST   = f'{SUCCESS_PREFIX}Təsdiqləndi Və Ağ Siyahıya Əlavə Edildi'
    OK_REMOVED_WHITELIST    = f'{SUCCESS_PREFIX}Ağ Siyahıdan Çıxarıldı Və Say Sıfırlandı'
    OK_ALL_WHITELIST_CLEARED= f'{SUCCESS_PREFIX}Bütün Ağ Siyahıdakı İstifadəçilər Çıxarıldı'
    OK_COUNTS_RESET         = f'{SUCCESS_PREFIX}Bütün Mesaj Sayları 0-a Sıfırlandı'
    OK_COUNT_RESET          = f'{SUCCESS_PREFIX}Mesaj Sayı 0-a Sıfırlandı'
    OK_PROFILE_REVERTED     = f'{SUCCESS_PREFIX}Profil Bərpa Edildi'
    OK_MSG_UNPINNED         = f'{SUCCESS_PREFIX}Mesajın Sabitliyi Ləğv Edildi'
    OK_GROUP_CALL_ENDED     = f'{SUCCESS_PREFIX}Qrup Zəngi Sona Çatdı'
    OK_MENTION_DISMISSED    = f'{SUCCESS_PREFIX}Qeyd Rədd Edildi'
    OK_ALIVE_RESET          = f'{SUCCESS_PREFIX}Alive Açarları Sıfırlandı (Emoji, Mətn)'
    OK_WELCOME_RESET        = f'{SUCCESS_PREFIX}Qarşılama Sıfırlandı'
    OK_SETTINGS_SAVED       = f'{SUCCESS_PREFIX}Ayarlar Yadda Saxlanıldı'
    OK_JOIN_REQUESTS_DONE   = f'{SUCCESS_PREFIX}Qoşulma Sorğuları Emal Edildi'
    OK_DM_SPAM_DONE         = f'{SUCCESS_PREFIX}DM Spam Tamamlandı'
    OK_MSG_PINNED           = f'{SUCCESS_PREFIX}Mesaj Sabitləndi'
    OK_ALL_MSGS_UNPINNED    = f'{SUCCESS_PREFIX}Bütün Mesajların Sabitliyi Ləğv Edildi'
    OK_LATEST_PIN_UNPINNED  = f'{SUCCESS_PREFIX}Son Sabitlənən Mesajın Sabitliyi Ləğv Edildi'
    OK_REACTION_UPDATED     = f'{SUCCESS_PREFIX}Reaksiya Yeniləndi'
    OK_REACTIONS_ENABLED    = f'{SUCCESS_PREFIX}Reaksiyalar Aktivdir'
    OK_SUDO_GRANTED         = f'{SUCCESS_PREFIX}Sudo Verildi'
    OK_SUDO_REVOKED         = f'{SUCCESS_PREFIX}Sudo Ləğv Edildi'
    OK_JOIN_REQUESTS_EMPTY  = f'{SUCCESS_PREFIX}Gözləyən Qoşulma Sorğusu Yoxdur'

    # ── Info ──────────────────────────────────────────────────────────────────
    INFO_BLACKLIST_EMPTY    = f'{INFO_PREFIX}Qara Siyahı Boşdur'
    INFO_NOT_IN_WHITELIST   = f'{INFO_PREFIX}Ağ Siyahıda Deyil'
    INFO_ALREADY_WHITELISTED= f'{INFO_PREFIX}Artıq Ağ Siyahıdadır'
    INFO_NO_COUNT           = f'{INFO_PREFIX}Bu Söhbət Üçün Say Tapılmadı'
    INFO_TAGALL_INACTIVE    = f'{INFO_PREFIX}Burada Aktiv Tagall Yoxdur'
    INFO_WORDLIST_EMPTY     = f'{INFO_PREFIX}Söz Siyahısı Artıq Boşdur'
    INFO_NOT_AFK            = f"{INFO_PREFIX}Siz AFK Deyildiniz"
    INFO_NO_BANNED_USERS    = f'{INFO_PREFIX}Bloklanmış İstifadəçi Tapılmadı'
    INFO_ALREADY_SUDOER     = f'{INFO_PREFIX}Artıq Sudoerdir'
    INFO_NOT_A_SUDOER       = f'{INFO_PREFIX}Sudoer Deyil'
    INFO_NO_SUDOERS         = f'{INFO_PREFIX}Sudoer Tapılmadı'
    INFO_NO_WHITELIST_USERS = f'{INFO_PREFIX}Çıxarılacaq Ağ Siyahıdakı İstifadəçi Yoxdur'
    INFO_NO_PENDING_JOIN_REQ= f'{INFO_PREFIX}Gözləyən Qoşulma Sorğusu Yoxdur'

    # ─────────────────────────────────────────────────────────────────────────
    # Composite / rich-text formatters
    # These follow Dragon-Userbot's <b>label:</b> <i>value</i> convention,
    # whilst using Unicode labels (CatUserBot style) for the label text.
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def afk_notify(afk_time: str, reason: str) -> str:
        """AFK auto-reply (Dragon-Userbot style)."""
        label_afk    = font.smallcaps("Mən Afkeyəm")
        label_reason = font.smallcaps("Sebeb")
        return (
            f"<b>{label_afk}</b> {afk_time}\n"
            f"<b>{label_reason}:</b> <i>{reason}</i>"
        )

    @staticmethod
    def afk_gone(reason: str) -> str:
        """Set-AFK confirmation (Dragon-Userbot style)."""
        label_going  = font.smallcaps("Afke Gedirem")
        label_reason = font.smallcaps("Sebeb")
        return (
            f"<b>{label_going}</b>\n"
            f"<b>{label_reason}:</b> <i>{reason}</i>"
        )

    @staticmethod
    def afk_return(afk_time: str) -> str:
        """Un-AFK confirmation."""
        label = font.smallcaps("Artiq Afk Deyil")
        label_was = font.smallcaps("Qeyri-aktivlik muddeti")
        return (
            f"<b>{label}</b>\n"
            f"<b>{label_was}:</b> <i>{afk_time}</i>"
        )

    @staticmethod
    def pong(latency_ms: float) -> str:
        """Ping result (Moon-Userbot style)."""
        label = font.smallcaps("Pong")
        return f"<b>{label}!</b> <code>{latency_ms:.0f}ms</code>"

    @staticmethod
    def banned(user: str, reason: str = "Səbəb göstərilməyib") -> str:
        """Ban confirmation (Dragon-Userbot style)."""
        label_banned = font.smallcaps("Bloklandi")
        label_reason = font.smallcaps("Sebeb")
        return (
            f"<b>{label_banned}:</b> {user}\n"
            f"<b>{label_reason}:</b> <i>{reason}</i>"
        )

    @staticmethod
    def unbanned(user: str) -> str:
        """Unban confirmation."""
        label = font.smallcaps("Blok Legv Edildi")
        return f"<b>{label}:</b> {user}"

    @staticmethod
    def muted(user: str, duration: str = "müddətsiz") -> str:
        """Mute confirmation (Dragon-Userbot style)."""
        label_muted = font.smallcaps("Susduruldu")
        label_dur   = font.smallcaps("Muddet")
        return (
            f"<b>{label_muted}:</b> {user}\n"
            f"<b>{label_dur}:</b> <i>{duration}</i>"
        )

    @staticmethod
    def unmuted(user: str) -> str:
        """Unmute confirmation."""
        label = font.smallcaps("Sesi Acildi")
        return f"<b>{label}:</b> {user}"

    @staticmethod
    def promoted(user: str, title: str = "") -> str:
        """Promote confirmation."""
        label = font.smallcaps("Yukseldildi")
        base  = f"<b>{label}:</b> {user}"
        return f"{base} — <i>{title}</i>" if title else base

    @staticmethod
    def demoted(user: str) -> str:
        """Demote confirmation."""
        label = font.smallcaps("Endirildi")
        return f"<b>{label}:</b> {user}"

    @staticmethod
    def kicked(user: str) -> str:
        """Kick confirmation."""
        label = font.smallcaps("Cixarildi")
        return f"<b>{label}:</b> {user}"

    @staticmethod
    def loading(action: str = "Emal olunur") -> str:
        """Inline loading status (Moon-Userbot style)."""
        label = font.smallcaps(action)
        return f'{Msg.EMOJI_LOADING} <i>{label}…</i>'
    @staticmethod
    def card(title: str, lines, emoji: str = PIN, footer: str = "") -> str:
        """Build a compact HTML status card with consistent spacing."""
        body_lines = []
        for line in lines:
            if line:
                body_lines.append(f"┃ {line}")
        if footer:
            body_lines.append(f"╰▸ {footer}")
        else:
            body_lines.append("╰━━━━━━━━━━━━━━━━━━━━╯")

        return "\n".join([
            f"{emoji} <b>{font.smallcaps(title)}</b>",
            *body_lines,
        ])

    @staticmethod
    def now_playing(title: str, artist: str = "", duration: str = "") -> str:
        """
        Now-playing card using cursive font for title
        (CatUserBot album/music display style).
        """
        t = font.bold_cursive(title[:40])
        parts = [f'{Msg.EMOJI_MUSIC} <b>{t}</b>']
        if artist:
            a = font.smallcaps(artist)
            parts.append(f'{Msg.EMOJI_MIC} <i>{a}</i>')
        if duration:
            parts.append(f'{Msg.EMOJI_LOADING} <code>{duration}</code>')
        return "\n".join(parts)

    @staticmethod
    def user_mention(name: str, user_id: int) -> str:
        """Hyperlink mention (CatUserBot format.py pattern)."""
        return f"<a href='tg://user?id={user_id}'>{name}</a>"

    @staticmethod
    def code_block(text: str) -> str:
        """Inline code block (Moon/Dragon style)."""
        return f"<code>{text}</code>"

    @staticmethod
    def section(title: str, body: str, emoji: str = PIN) -> str:
        """
        Section header block.
        Uses Gothic (CatUserBot style) for the title.

             📌 𝕊𝕖𝕔𝕥𝕚𝕠𝕟 𝕋𝕚𝕥𝕝𝕖
             ├ body line 1
             └ body line 2
        """
        styled_title = font.double(title)
        return f"{emoji} <b>{styled_title}</b>\n{body}"


def plain_text(text: str) -> str:
    """Convert a formatted message (HTML/Markdown) to plain text suitable for
    contexts that don't support formatting (callback_answer, inline results).

    This is intentionally conservative: strip HTML tags, remove Markdown
    emphasis and code markers, unescape HTML entities, and normalize spaces
    while preserving newlines.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)

    # Remove HTML tags
    out = re.sub(r'<[^>]+>', '', text)

    # Remove common Markdown/markup chars that affect formatting
    out = re.sub(r'[\*`_~]', '', out)

    # Unescape HTML entities (e.g. &amp; → &)
    out = html.unescape(out)

    # Normalize spaces but preserve newlines
    out = '\n'.join(re.sub(r'[ \t]+', ' ', line).strip() for line in out.splitlines())
    return out.strip()
