# 🤖 Ryhavean Userbot

Pyrogram əsasında qurulmuş, tam Azərbaycan dilində işləyən güclü Telegram
userbot və idarəetmə sistemi.

- 📢 Yeniliklər Kanalı: https://t.me/ryhaveanupdates
- 💬 İcma Qrupu: https://t.me/RyhaveanTeam

---

## ✨ İmkanlar

### 🎵 Musiqi və Əyləncə
- Səsli söhbətdə musiqi yayımı (növbə dəstəyi ilə)
- YouTube-dan axtarış və səsləndirmə
- Audio/video formatlarının dəstəyi
- Növbə idarəetməsi: əlavə et, keç, dayandır

### 📁 Fayl İdarəetməsi
- Seçilmiş kanallardan avtomatik media yükləmə
- Fayl yükləmə/endirmə alətləri
- Video emalı və miniatür yaratma
- Telegram limitindən böyük fayl dəstəyi

### 🛠️ Faydalı Alətlər
- Söhbət statistikası və istifadəçi fəallığı
- Aktiv Telegram sessiyalarının idarəsi
- Ping / işləmə müddəti yoxlaması
- İstifadəçi və söhbət haqqında ətraflı məlumat

### 🎨 Fərdiləşdirmə
- Mətn şrift stilləri
- Stiker yaratma və idarəetmə
- Profil klonlama və bərpa
- Fərdi avtomatik cavablar

### 🔧 Admin Alətləri
- İstifadəçi təsdiqi və ağ siyahı
- Qabaqcıl spam qoruması
- Toplu mesaj silmə və moderasiya
- Söz zənciri / söz oyunu avtomatlaşdırması

### 💎 Premium Emoji
- 220-dən çox premium emoji İD-si həm bot, həm userbot üçün
- Bütün mesajlarda avtomatik tətbiq olunur

---

## 🔐 Lisenziya Sistemi

Bot hər kəs üçün açıq deyil:

1. Admin `/ver <istifadəçi_id>` yazır → istifadəçiyə **30 günlük** icazə verilir
   (`/ver <id> <gün>` ilə müddət dəyişdirilə bilər).
2. İcazəsi olmayan istifadəçi `/start` yazsa bot işləmir.
3. İcazəli istifadəçi `/login` ilə nömrə və təsdiq kodunu daxil edir.
4. Bütün userbotlar **eyni server** üzərində, hər istifadəçi üçün ayrıca
   klient kimi işləyir.
5. Bütün məlumatlar (lisenziya, sessiya, parametrlər) **MongoDB**-də saxlanılır
   və server yenidən başlayanda oradan çəkilir.

### Əsas əmrlər

| Əmr | İzah |
|---|---|
| `/start` | Başlanğıc (lisenziya tələb olunur) |
| `/login` | Userbot qurulumu (nömrə + kod + 2FA) |
| `/logout` | Userbotu dayandırır və sessiyanı silir |
| `/mylicense` | Lisenziya müddəti |
| `/commands` | Bütün əmrlər |
| `/settings` | Parametrlər paneli |
| `/status` | Vəziyyət məlumatı |
| `/ver <id> [gün]` | *(admin)* İcazə verir |
| `/unver <id>` | *(admin)* İcazəni ləğv edir |
| `/users` | *(admin)* Aktiv lisenziyalar |

Userbot prefiksləri: `.` `!` `?` `^` `_`

---

## 🚀 Quraşdırma

```bash
git clone <repo-ünvanı>
cd ryhavean-userbot
pip install -r requirements.txt
cp .env.example .env   # dəyərləri doldurun
python main.py
```

Render (pulsuz servis) və UptimeRobot ilə 7/24 işləmə üçün
**[DEPLOY.md](DEPLOY.md)** faylına baxın.

---

## 🌐 Keep-Alive Ünvanları

| Ünvan | Təyinat |
|---|---|
| `/` | Status səhifəsi |
| `/ping` | UptimeRobot üçün `pong` |
| `/health` | JSON vəziyyət məlumatı |

---

## 📄 Lisenziya

MIT — ətraflı üçün [LICENSE](LICENSE) faylına baxın.


## 🧩 Plagin sistemi (`.pinstall` / `.unpinstall`)

Hər istifadəçi öz plaginlərini quraşdıra bilər — plaginlər **MongoDB-də
istifadəçi ID-si üzrə ayrıca** saxlanılır və bir-birinə qarışmır.

| Əmr | İzah |
|-----|------|
| `.pinstall` | `.py` faylına **reply** edin — plagin dərhal (restartsız) işə düşür |
| `.unpinstall <ad>` | Plagini söndürüb bazadan silir |
| `.pluginlist` | Quraşdırılmış plaginlərin siyahısı |

Server yenidən başlayanda hər istifadəçinin plaginləri MongoDB-dən avtomatik
bərpa olunur (`user_plugins` kolleksiyası). Plagin ayarları isə
`plugin_configs` kolleksiyasında yenə hər istifadəçi üçün ayrıca saxlanılır
(`import db` → `await db.get_plugin_config(...)`).

Plagin nümunəsi: `example_plugins/auto_media_saver.py` — faylı Telegram-da
göndərib ona reply ilə `.pinstall` yazın.

## 🎵 `.song`

`.song <mahnı adı>` və ya audio/video faylına reply + `.song` — musiqi
@KeepMediaBot vasitəsilə endirilir və cari söhbətə göndərilir.

## ⏱ UptimeRobot ilə 7/24 aktiv qalmaq

1. Layihəni Render/Railway kimi bir yerdə yayımlayın.
2. [uptimerobot.com](https://uptimerobot.com) → **Add New Monitor** → *HTTP(s)*.
3. URL: `https://<layihə-ünvanınız>/ping` — interval **5 dəqiqə**.
4. `.env`-də `PING_URL=https://<layihə-ünvanınız>` yazsanız, bot əlavə olaraq
   özü də hər `PING_INTERVAL` saniyədən bir sorğu göndərir.

Yoxlama ünvanları: `/` (status səhifəsi), `/ping` (`pong`), `/health` (JSON).
