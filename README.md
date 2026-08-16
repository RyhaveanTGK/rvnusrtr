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
