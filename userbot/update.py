"""`.update` — kodu git-dən yeniləyib botu yenidən başladır.

Əvvəlki versiya sadəcə `git pull --ff-only` çağırırdı və server-də repo
"detached HEAD" vəziyyətində olduqda bu xəta ilə dayanırdı:

    You are not currently on a branch.
    Please specify which branch you want to merge with.

Yeni versiya:
  • cari branch-i müəyyən edir; branch yoxdursa (detached HEAD) origin-in
    default branch-inə (main/master) avtomatik keçir;
  • upstream qurulmayıbsa özü qurur;
  • yerli dəyişikliklər varsa `git stash` edir (və ya `.update force` ilə
    tamamilə sıfırlayır);
  • requirements.txt dəyişibsə asılılıqları yenidən qurur;
  • sonda prosesi yenidən başladır.
"""

import hashlib
import logging
import os
import sys

from pyrogram import Client, filters

from tools import *

logger = logging.getLogger("userbot.update")

REQUIREMENTS = os.path.join(os.getcwd(), "requirements.txt")

FALLBACK_BRANCHES = ("main", "master")


def _requirements_hash():
    try:
        with open(REQUIREMENTS, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except FileNotFoundError:
        return None


async def _git(cmd: str):
    out, err, code, _ = await run_cmd(f"git {cmd}")
    return (out or "").strip(), (err or "").strip(), code


async def _current_branch():
    """Cari branch adı; detached HEAD-də None."""
    out, _, code = await _git("rev-parse --abbrev-ref HEAD")
    if code != 0 or not out or out == "HEAD":
        return None
    return out


async def _default_remote_branch():
    """origin/HEAD -> hansı branch-ə baxır; tapılmasa main/master yoxlanır."""
    out, _, code = await _git("symbolic-ref --quiet refs/remotes/origin/HEAD")
    if code == 0 and out:
        return out.rsplit("/", 1)[-1]

    # origin/HEAD qurulmayıbsa, uzaqdan soruşaq
    out, _, code = await _git("remote show origin")
    if code == 0:
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("HEAD branch:"):
                name = line.split(":", 1)[1].strip()
                if name and name != "(unknown)":
                    return name

    for candidate in FALLBACK_BRANCHES:
        _, _, code = await _git(f"rev-parse --verify --quiet refs/remotes/origin/{candidate}")
        if code == 0:
            return candidate
    return None


async def _has_local_changes():
    out, _, code = await _git("status --porcelain")
    return code == 0 and bool(out)


@Client.on_message(filters.command("update", prefixes=HARDCODED_PREFIXES) & filters.me)
async def update_handler(client, message):
    """Ən son kodu çəkir, asılılıqları yeniləyir və botu yenidən başladır."""
    args = (get_arg(message) or "").strip().lower()
    force = args in ("force", "hard", "-f")

    status = await edit_or_reply(message, "🔄 <b>Yenilənir...</b>\n┃ Repozitoriya yoxlanılır...")

    # 0) Ümumiyyətlə git repo-dur?
    _, _, code = await _git("rev-parse --is-inside-work-tree")
    if code != 0:
        await status.edit_text(styled_error(
            "Bu qovluq git repozitoriyası deyil — <code>.update</code> istifadə edilə bilməz."
        ))
        return

    before = _requirements_hash()

    # 1) Uzaqdan bütün yenilikləri çək
    await status.edit_text("🔄 <b>Yenilənir...</b>\n┃ <code>git fetch</code> icra olunur...")
    out, err, code = await _git("fetch --all --prune --tags")
    if code != 0:
        await status.edit_text(styled_error(f"git fetch uğursuz oldu:\n<code>{(err or out)[-500:]}</code>"))
        return

    # 2) Branch-i müəyyən et (detached HEAD problemi burada həll olunur)
    branch = await _current_branch()
    detached = branch is None
    if detached:
        branch = await _default_remote_branch()
        if not branch:
            await status.edit_text(styled_error(
                "Branch tapılmadı. Repozitoriyada uzaq branch yoxdur "
                "(<code>git remote -v</code> yoxlayın)."
            ))
            return
        await status.edit_text(
            f"⚠️ <b>Branch-də deyildiniz (detached HEAD).</b>\n"
            f"┃ <code>{branch}</code> branch-inə keçilir..."
        )
        _, err, code = await _git(f"checkout -B {branch} origin/{branch}")
        if code != 0:
            await status.edit_text(styled_error(f"Branch dəyişdirilmədi:\n<code>{err[-400:]}</code>"))
            return

    # 3) Uzaq branch mövcuddurmu?
    _, _, code = await _git(f"rev-parse --verify --quiet refs/remotes/origin/{branch}")
    if code != 0:
        await status.edit_text(styled_error(
            f"<code>origin/{branch}</code> tapılmadı. Branch silinib və ya adı dəyişib."
        ))
        return

    # 4) Yerli dəyişikliklər
    stashed = False
    if await _has_local_changes():
        if force:
            await _git("reset --hard")
            await _git("clean -fd")
        else:
            await status.edit_text("📦 <b>Yerli dəyişikliklər saxlanılır (stash)...</b>")
            _, _, code = await _git('stash push -u -m "ryhavean-auto-update"')
            stashed = code == 0

    # 5) Fərq varmı?
    local, _, _ = await _git("rev-parse HEAD")
    remote, _, _ = await _git(f"rev-parse origin/{branch}")
    if local and local == remote and not detached:
        if stashed:
            await _git("stash pop")
        await status.edit_text(f"✅ <b>Artıq ən son versiyadır.</b>\n┃ Branch: <code>{branch}</code>")
        return

    # 6) Yenilə — fast-forward alınmasa sərt sinxronlaşma
    await status.edit_text(f"⬇️ <b>Kod çəkilir...</b>\n┃ Branch: <code>{branch}</code>")
    out, err, code = await _git(f"merge --ff-only origin/{branch}")
    if code != 0:
        logger.warning("[UPDATE] ff-only merge alınmadı: %s", err or out)
        await status.edit_text("♻️ <b>Fast-forward mümkün olmadı — sərt sinxronlaşma...</b>")
        _, err, code = await _git(f"reset --hard origin/{branch}")
        if code != 0:
            await status.edit_text(styled_error(f"Yeniləmə alınmadı:\n<code>{err[-500:]}</code>"))
            return

    # upstream-i qur ki, gələcəkdə adi `git pull` da işləsin
    await _git(f"branch --set-upstream-to=origin/{branch} {branch}")

    if stashed:
        _, err, code = await _git("stash pop")
        if code != 0:
            logger.warning("[UPDATE] stash pop konflikt verdi: %s", err)

    # 7) Asılılıqlar dəyişibsə pip install
    if _requirements_hash() != before:
        await status.edit_text("📦 <b>Asılılıqlar dəyişdi — yenidən quraşdırılır...</b>")
        _, pip_err, pip_code, _ = await run_cmd(
            f'"{sys.executable}" -m pip install --no-input -r "{REQUIREMENTS}"'
        )
        if pip_code != 0:
            await status.edit_text(styled_error(f"pip install uğursuz oldu:\n<code>{pip_err[-500:]}</code>"))
            return

    short, _, _ = await _git("log -1 --pretty=format:%h%x20%s")
    await status.edit_text(
        f"♻️ <b>Yeniləmə tətbiq edildi.</b>\n"
        f"┃ Branch: <code>{branch}</code>\n"
        f"┃ Commit: <code>{short[:80]}</code>\n"
        f"┃ Yenidən başladılır..."
    )
    logger.info("[UPDATE] Update pulled (%s); re-executing process.", branch)
    os.execv(sys.executable, [sys.executable, *sys.argv])
