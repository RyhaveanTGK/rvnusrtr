# Ryhavean Userbot — Render Deploy Təlimatı

Bütün sistem **tək server** üzərində işləyir: idarəedici bot və bütün
istifadəçilərin userbotları eyni prosesdə qalxır. Bütün məlumatlar
(**lisenziyalar, sessiyalar, parametrlər**) **MongoDB**-də saxlanılır və
server yenidən başlayanda oradan çəkilir.

---

## 1. Hazırlıq

| Lazımdır | Haradan |
|---|---|
| `API_ID`, `API_HASH` | https://my.telegram.org |
| `BOT_TOKEN` | https://t.me/BotFather |
| `MONGO_URI` | https://cloud.mongodb.com (pulsuz M0 klaster) |
| `OWNER_ID` | https://t.me/userinfobot |

MongoDB Atlas-da **Network Access → Add IP → 0.0.0.0/0** açılmalıdır.

---

## 2. Render-də qurulum (pulsuz servis)

1. Layihəni GitHub repozitoriyasına yükləyin.
2. https://render.com → **New → Blueprint** → repozitoriyanı seçin
   (`render.yaml` avtomatik oxunur).
   Alternativ: **New → Web Service**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`
   - Plan: **Free**
3. **Environment** bölməsinə dəyişənləri əlavə edin:
   `API_ID`, `API_HASH`, `BOT_TOKEN`, `MONGO_URI`, `OWNER_ID`, `BOT_ADMINS`.
4. **Deploy** düyməsinə basın. Loqlarda `Bot uğurla başladıldı!` görünməlidir.
5. Xidmət ünvanı: `https://<xidmet-adi>.onrender.com`

---

## 3. UptimeRobot ilə 7/24 işləmə

Render pulsuz planda 15 dəqiqə sorğu gəlməzsə xidməti yatızdırır.

1. https://uptimerobot.com saytında qeydiyyatdan keçin.
2. **Add New Monitor**:
   - Monitor Type: **HTTP(s)**
   - Friendly Name: `Ryhavean Userbot`
   - URL: `https://<xidmet-adi>.onrender.com/ping`
   - Monitoring Interval: **5 dəqiqə**
3. **Create Monitor** — bot artıq 7/24 aktiv qalır.

Yoxlama ünvanları:
- `/` — status səhifəsi
- `/ping` — `pong`
- `/health` — JSON vəziyyət (aktiv userbot sayı, işləmə müddəti)

---

## 4. İstifadə axını

1. Admin bota `/ver <istifadəçi_id>` yazır → istifadəçiyə **30 günlük** icazə verilir.
   (`/ver 123456789 60` — 60 günlük icazə)
2. İstifadəçi `/start` yazır. İcazəsi yoxdursa bot işləmir.
3. İcazəli istifadəçi `/login` yazır → nömrə → təsdiq kodu → (varsa) 2FA şifrəsi.
4. Userbot həmin serverdə işə düşür və rəsmi kanallara avtomatik qoşulur.

### Admin əmrləri
| Əmr | İzah |
|---|---|
| `/ver <id> [gün]` | İcazə verir (standart 30 gün) |
| `/unver <id>` | İcazəni ləğv edir və userbotu dayandırır |
| `/users` | Aktiv lisenziyaların siyahısı |

### İstifadəçi əmrləri
| Əmr | İzah |
|---|---|
| `/login` | Userbot qurulumu |
| `/logout` | Userbotu dayandırır, sessiyanı silir |
| `/mylicense` | Lisenziya müddətini göstərir |
| `/commands` | Bütün əmrlər |
| `/settings` | Parametrlər |
| `/status` | Vəziyyət |

---

## 5. Rəsmi linklər

- 📢 Yeniliklər Kanalı: https://t.me/ryhaveanupdates
- 💬 İcma Qrupu: https://t.me/RyhaveanTeam
