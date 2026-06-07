"""我们的小屋 — 日常生活分享记录系统 Web 应用。"""

import calendar
import os
import socket
from datetime import date
from functools import wraps
from uuid import uuid4

from flask import Flask, flash, redirect, render_template, request, send_from_directory, url_for

from love_manager import LoveManager, UPLOAD_DIR

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "qinglv-love-dev-key")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
COUNTDOWN_TYPES = {"anniversary": "纪念日", "birthday": "生日", "event": "日程"}
manager = LoveManager()


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file_storage) -> str:
    if not file_storage or not file_storage.filename:
        raise ValueError("请选择图片文件")
    if not allowed_file(file_storage.filename):
        raise ValueError("仅支持 png/jpg/jpeg/gif/webp 格式")
    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid4().hex}.{ext}"
    file_storage.save(os.path.join(UPLOAD_DIR, filename))
    return filename


def form_who() -> str:
    return request.form.get("who", "1")


def require_unlocked(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not manager.is_unlocked():
            flash("请先完善双方情侣信息后再使用此功能", "error")
            return redirect(url_for("couple"))
        return view(*args, **kwargs)

    return wrapper


def handle_delete(delete_fn, item_id: str, endpoint: str):
    try:
        delete_fn(item_id)
        flash("已移入回收站", "success")
    except KeyError as e:
        flash(str(e), "error")
    return redirect(url_for(endpoint))


@app.context_processor
def inject_globals():
    summary = manager.couple_summary()
    return {
        "couple": summary,
        "unlocked": summary["unlocked"],
        "type_labels": manager.TYPE_LABELS,
        "countdown_types": COUNTDOWN_TYPES,
    }


@app.route("/")
def home():
    today = date.today()
    cal = calendar.Calendar(firstweekday=0)
    return render_template(
        "home.html",
        countdowns=manager.list_countdowns()[:3],
        activities=manager.list_activities(15),
        cal_data=manager.get_checkins(today.year, today.month),
        cal_year=today.year,
        cal_month=today.month,
        cal_weeks=cal.monthdatescalendar(today.year, today.month),
    )


@app.route("/couple", methods=["GET", "POST"])
def couple():
    if request.method == "POST":
        who = form_who()
        try:
            avatar = ""
            f = request.files.get("avatar")
            if f and f.filename:
                avatar = save_upload(f)
            info = {
                "name": request.form.get("name", ""),
                "nickname": request.form.get("nickname", ""),
                "birthday": request.form.get("birthday", ""),
                "phone": request.form.get("phone", ""),
                "bio": request.form.get("bio", ""),
            }
            if avatar:
                info["avatar"] = avatar
            elif manager.get_person(who).avatar:
                info["avatar"] = manager.get_person(who).avatar
            manager.save_person(who, info)
            flash("信息保存成功！", "success")
            if manager.is_unlocked():
                flash("双方信息已完善，所有功能已解锁！", "success")
        except (ValueError, PermissionError) as e:
            flash(str(e), "error")
        return redirect(url_for("couple"))
    return render_template("couple.html")


@app.route("/checkin", methods=["GET", "POST"])
@require_unlocked
def checkin():
    year = int(request.args.get("year", date.today().year))
    month = int(request.args.get("month", date.today().month))
    if request.method == "POST":
        try:
            result = manager.checkin(form_who())
            if result["checked"]:
                msg = "今天双方都打卡啦！爱的特效已触发~" if result["both_checked"] else "打卡成功，等待 TA 一起打卡吧~"
            else:
                msg = "已取消打卡"
            flash(msg, "success")
        except PermissionError as e:
            flash(str(e), "error")
        return redirect(url_for("checkin", year=year, month=month))

    cal = calendar.Calendar(firstweekday=0)
    prev_month, prev_year = (month - 1, year) if month > 1 else (12, year - 1)
    next_month, next_year = (month + 1, year) if month < 12 else (1, year + 1)
    return render_template(
        "checkin.html",
        year=year,
        month=month,
        weeks=cal.monthdatescalendar(year, month),
        data=manager.get_checkins(year, month),
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month,
    )


@app.route("/period", methods=["GET", "POST"])
@require_unlocked
def period():
    if request.method == "POST":
        try:
            manager.add_period(
                request.form.get("date", ""),
                request.form.get("note", ""),
                form_who(),
            )
            flash("例假记录已添加", "success")
        except (ValueError, PermissionError) as e:
            flash(str(e), "error")
        return redirect(url_for("period"))
    return render_template("period.html", records=manager.list_periods())


@app.route("/period/delete/<item_id>", methods=["POST"])
@require_unlocked
def delete_period(item_id):
    return handle_delete(manager.delete_period, item_id, "period")


@app.route("/messages", methods=["GET", "POST"])
@require_unlocked
def messages():
    if request.method == "POST":
        try:
            manager.add_message(
                request.form.get("content", ""),
                "",
                form_who(),
            )
            flash("留言已发布", "success")
        except (ValueError, PermissionError) as e:
            flash(str(e), "error")
        return redirect(url_for("messages"))
    return render_template("messages.html", items=manager.list_messages())


@app.route("/messages/delete/<item_id>", methods=["POST"])
@require_unlocked
def delete_message(item_id):
    return handle_delete(manager.delete_message, item_id, "messages")


@app.route("/album", methods=["GET", "POST"])
@require_unlocked
def album():
    if request.method == "POST":
        try:
            image = save_upload(request.files.get("image"))
            manager.add_album(image, request.form.get("description", ""), form_who())
            flash("照片已上传", "success")
        except (ValueError, PermissionError) as e:
            flash(str(e), "error")
        return redirect(url_for("album"))
    return render_template("album.html", items=manager.list_album())


@app.route("/album/delete/<item_id>", methods=["POST"])
@require_unlocked
def delete_album(item_id):
    return handle_delete(manager.delete_album, item_id, "album")


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/bucket", methods=["GET", "POST"])
@require_unlocked
def bucket():
    if request.method == "POST":
        action = request.form.get("action")
        item_id = request.form.get("item_id", "")
        try:
            if action == "toggle":
                manager.toggle_bucket(item_id, form_who())
            elif action == "note":
                manager.update_bucket_note(item_id, request.form.get("note", ""))
        except (KeyError, PermissionError) as e:
            flash(str(e), "error")
        return redirect(url_for("bucket"))
    return render_template(
        "bucket.html",
        items=manager.list_bucket(),
        stats=manager.bucket_stats(),
    )


@app.route("/countdown", methods=["GET", "POST"])
@require_unlocked
def countdown():
    if request.method == "POST":
        try:
            manager.add_countdown(
                request.form.get("title", ""),
                request.form.get("date", ""),
                request.form.get("type", "event"),
                form_who(),
            )
            flash("倒数日已添加", "success")
        except (ValueError, PermissionError) as e:
            flash(str(e), "error")
        return redirect(url_for("countdown"))
    return render_template("countdown.html", items=manager.list_countdowns())


@app.route("/countdown/delete/<item_id>", methods=["POST"])
@require_unlocked
def delete_countdown(item_id):
    return handle_delete(manager.delete_countdown, item_id, "countdown")


@app.route("/calculator")
def calculator_page():
    return render_template("calculator.html")


@app.route("/activity", methods=["POST"])
def log_activity():
    action = request.form.get("action", "")
    if action == "calculator":
        manager.log_activity(form_who(), "calculator")
    return "", 204


@app.route("/trash")
def trash():
    return render_template("trash.html", items=manager.list_trash())


@app.route("/trash/restore/<trash_id>", methods=["POST"])
def restore_trash(trash_id):
    try:
        manager.restore(trash_id)
        flash("已恢复", "success")
    except KeyError as e:
        flash(str(e), "error")
    return redirect(url_for("trash"))


@app.route("/trash/delete/<trash_id>", methods=["POST"])
def permanent_delete(trash_id):
    try:
        manager.permanent_delete(trash_id)
        flash("已彻底删除", "success")
    except KeyError as e:
        flash(str(e), "error")
    return redirect(url_for("trash"))


@app.route("/trash/empty-all", methods=["POST"])
def empty_trash_all():
    count = manager.empty_trash()
    flash(
        f"已清空回收站，共删除 {count} 项" if count else "回收站已经是空的",
        "success",
    )
    return redirect(url_for("trash"))


def _local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    ip = _local_ip()
    print("=" * 52)
    print("  我们的小屋 已启动")
    print(f"  本机访问: http://127.0.0.1:{port}")
    print(f"  手机访问: http://{ip}:{port}  (需同一 WiFi)")
    print("=" * 52)
    app.run(host="0.0.0.0", port=port, debug=True)
