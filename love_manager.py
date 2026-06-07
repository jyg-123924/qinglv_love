"""我们的小屋 — 数据层，JSON 持久化与回收站。"""

import json
import os
import uuid
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DATA_FILE = os.path.join(DATA_DIR, "love_data.json")
TRASH_FILE = os.path.join(DATA_DIR, "trash.json")

DEFAULT_BUCKET_ITEMS = [
    "一起看日出", "一起看日落", "一起淋雨", "一起堆雪人", "一起放烟花",
    "一起坐摩天轮", "一起逛游乐园", "一起看电影", "一起K歌", "一起做饭",
    "一起洗碗", "一起逛超市", "一起养一盆植物", "一起拍情侣照", "一起穿情侣装",
    "一起写情书", "一起录一段视频", "一起做手工", "一起画画", "一起拼图",
    "一起去海边", "一起去爬山", "一起去露营", "一起去旅行", "一起坐高铁",
    "一起坐飞机", "一起骑单车", "一起散步", "一起跑步", "一起健身",
    "一起泡温泉", "一起游泳", "一起滑冰", "一起滑雪", "一起打羽毛球",
    "一起打游戏", "一起下象棋", "一起逛博物馆", "一起逛书店", "一起听演唱会",
    "一起过生日", "一起过情人节", "一起过圣诞节", "一起跨年", "一起许愿",
    "一起养宠物", "一起给宠物取名", "一起布置房间", "一起买家具", "一起贴墙纸",
    "一起种花", "一起摘草莓", "一起钓鱼", "一起烧烤", "一起野餐",
    "一起喝同一杯奶茶", "一起尝试新餐厅", "一起学做甜点", "一起包饺子", "一起火锅",
    "一起深夜聊天", "一起说晚安", "一起说早安", "一起赖床", "一起赖在沙发",
    "一起追剧", "一起追番", "一起读一本书", "一起学一门语言", "一起上课",
    "一起见家长", "一起见朋友", "一起参加婚礼", "一起拍全家福", "一起存共同相册",
    "一起制定计划", "一起完成目标", "一起存钱", "一起理财", "一起买房",
    "一起装修", "一起选窗帘", "一起选床单", "一起买礼物", "一起写愿望清单",
    "一起道歉", "一起和好", "一起拥抱", "一起牵手", "一起接吻",
    "一起说我爱你", "一起规划未来", "一起养孩子", "一起变老", "一起白头",
    "一起回忆初遇", "一起重走第一次约会路线", "一起拍100张合照", "一起录100条语音", "一起完成这份清单",
]


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _today_str() -> str:
    return date.today().isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


@dataclass
class PersonInfo:
    name: str = ""
    nickname: str = ""
    birthday: str = ""
    phone: str = ""
    bio: str = ""
    avatar: str = ""
    saved: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "PersonInfo":
        if not data:
            return cls()
        return cls(
            name=data.get("name", ""),
            nickname=data.get("nickname", ""),
            birthday=data.get("birthday", ""),
            phone=data.get("phone", ""),
            bio=data.get("bio", ""),
            avatar=data.get("avatar", ""),
            saved=data.get("saved", False),
        )

    @property
    def is_complete(self) -> bool:
        return self.saved and bool(self.name.strip())


@dataclass
class TrashItem:
    id: str
    item_type: str
    data: dict[str, Any]
    deleted_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "item_type": self.item_type,
            "data": self.data,
            "deleted_at": self.deleted_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "TrashItem":
        return cls(
            id=raw["id"],
            item_type=raw["item_type"],
            data=raw["data"],
            deleted_at=raw["deleted_at"],
        )


class LoveManager:
    """情侣生活记录管理器。"""

    def __init__(
        self,
        data_file: str = DATA_FILE,
        trash_file: str = TRASH_FILE,
    ) -> None:
        self.data_file = data_file
        self.trash_file = trash_file
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        self._data: dict[str, Any] = {}
        self._trash: dict[str, TrashItem] = {}
        self._load()
        self._load_trash()
        self._ensure_bucket_list()
        self._normalize_bucket_list()
        self._backfill_activities()

    def _default_data(self) -> dict[str, Any]:
        return {
            "couple": {
                "person1": PersonInfo().to_dict(),
                "person2": PersonInfo().to_dict(),
            },
            "checkins": {},
            "period_records": [],
            "messages": [],
            "album": [],
            "bucket_list": [],
            "countdowns": [],
            "activities": [],
        }

    def _load(self) -> None:
        if not os.path.exists(self.data_file):
            self._data = self._default_data()
            self._save()
            return
        with open(self.data_file, "r", encoding="utf-8") as f:
            self._data = json.load(f)
        for key in self._default_data():
            self._data.setdefault(key, deepcopy(self._default_data()[key]))

    def _load_trash(self) -> None:
        if not os.path.exists(self.trash_file):
            self._save_trash()
            return
        with open(self.trash_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self._trash = {item["id"]: TrashItem.from_dict(item) for item in raw}

    def _save(self) -> None:
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def _save_trash(self) -> None:
        data = [t.to_dict() for t in self._trash.values()]
        with open(self.trash_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _ensure_bucket_list(self) -> None:
        if self._data["bucket_list"]:
            return
        self._data["bucket_list"] = [
            {
                "id": _new_id(),
                "title": title,
                "done": False,
                "done_at": "",
                "note": "",
            }
            for title in DEFAULT_BUCKET_ITEMS
        ]
        self._save()

    def _normalize_bucket_list(self) -> None:
        items = self._data["bucket_list"]
        if len(items) > 100:
            self._data["bucket_list"] = items[:100]
            self._save()

    def _backfill_activities(self) -> None:
        """确保 activities 字段存在。"""
        self._data.setdefault("activities", [])

    def _move_to_trash(self, item_type: str, item: dict[str, Any]) -> None:
        trash_id = item.get("id", _new_id())
        self._trash[trash_id] = TrashItem(
            id=trash_id,
            item_type=item_type,
            data=deepcopy(item),
            deleted_at=_now_iso(),
        )
        self._save_trash()

    # ---------- 解锁逻辑 ----------

    def get_person(self, who: str) -> PersonInfo:
        key = "person1" if who == "1" else "person2"
        return PersonInfo.from_dict(self._data["couple"].get(key))

    def save_person(self, who: str, info: dict[str, Any]) -> PersonInfo:
        key = "person1" if who == "1" else "person2"
        name = info.get("name", "").strip()
        if not name:
            raise ValueError("姓名不能为空")
        current = PersonInfo.from_dict(self._data["couple"].get(key))
        current.name = name
        current.nickname = info.get("nickname", "").strip()
        current.birthday = info.get("birthday", "").strip()
        current.phone = info.get("phone", "").strip()
        current.bio = info.get("bio", "").strip()
        if info.get("avatar"):
            current.avatar = info["avatar"]
        current.saved = True
        self._data["couple"][key] = current.to_dict()
        self._save()
        return current

    def is_unlocked(self) -> bool:
        p1 = self.get_person("1")
        p2 = self.get_person("2")
        return p1.is_complete and p2.is_complete

    def couple_summary(self) -> dict[str, Any]:
        p1 = self.get_person("1")
        p2 = self.get_person("2")
        return {
            "person1": p1.to_dict(),
            "person2": p2.to_dict(),
            "unlocked": self.is_unlocked(),
            "person1_name": p1.name or "TA",
            "person2_name": p2.name or "TA",
        }

    def person_name(self, who: str) -> str:
        return self.couple_summary()["person1_name" if who == "1" else "person2_name"]

    # ---------- 动态记录 ----------

    def log_activity(self, who: str, action: str, detail: str = "") -> dict[str, Any]:
        """记录一条动态。"""
        item = {
            "id": _new_id(),
            "who": who,
            "action": action,
            "detail": detail,
            "created_at": _now_iso(),
        }
        self._data.setdefault("activities", []).insert(0, item)
        self._save()
        return item

    def list_activities(self, limit: int = 15) -> list[dict[str, Any]]:
        """获取最近的动态记录，每条带上 who_name。"""
        activities = self._data.get("activities", [])
        result = []
        action_texts = {
            "checkin": "打卡了",
            "uncheckin": "取消了打卡",
            "message": "写了留言",
            "album": "上传了照片",
            "countdown": "添加了倒数日",
            "bucket_done": "完成了一件事",
            "bucket_undone": "取消完成一件事",
            "period": "记录了例假",
            "calculator": "使用了计算器",
        }
        for act in activities[:limit]:
            result.append({
                **act,
                "who_name": self.person_name(act.get("who", "1")),
                "text": action_texts.get(act.get("action", ""), "进行了操作"),
            })
        return result

    # ---------- 打卡 ----------

    def checkin(self, who: str) -> dict[str, Any]:
        if not self.is_unlocked():
            raise PermissionError("请先完善双方情侣信息")
        today = _today_str()
        day = self._data["checkins"].setdefault(
            today, {"person1": False, "person2": False}
        )
        key = "person1" if who == "1" else "person2"
        day[key] = not day[key]
        checked = day[key]
        if not day["person1"] and not day["person2"]:
            self._data["checkins"].pop(today, None)
            day = {"person1": False, "person2": False}
        self._save()
        both = day["person1"] and day["person2"]
        return {
            "date": today,
            "checkin": day,
            "both_checked": both,
            "checked": checked,
        }

    def get_checkins(self, year: int, month: int) -> dict[str, Any]:
        prefix = f"{year:04d}-{month:02d}-"
        result = {}
        for d, info in self._data["checkins"].items():
            if d.startswith(prefix):
                result[d] = {
                    **info,
                    "both": info.get("person1") and info.get("person2"),
                }
        today = _today_str()
        today_info = self._data["checkins"].get(
            today, {"person1": False, "person2": False}
        )
        return {
            "days": result,
            "today": today,
            "today_info": today_info,
            "today_both": today_info.get("person1") and today_info.get("person2"),
        }

    # ---------- 例假记录 ----------

    def add_period(self, record_date: str, note: str = "", who: str = "1") -> dict[str, Any]:
        if not self.is_unlocked():
            raise PermissionError("请先完善双方情侣信息")
        item = {
            "id": _new_id(),
            "date": record_date,
            "note": note.strip(),
            "created_at": _now_iso(),
        }
        self._data["period_records"].append(item)
        self._data["period_records"].sort(key=lambda x: x["date"], reverse=True)
        self._save()
        self.log_activity(who, "period", record_date)
        return item

    def list_periods(self) -> list[dict[str, Any]]:
        return list(self._data["period_records"])

    def delete_period(self, item_id: str) -> dict[str, Any]:
        for i, item in enumerate(self._data["period_records"]):
            if item["id"] == item_id:
                removed = self._data["period_records"].pop(i)
                self._move_to_trash("period", removed)
                self._save()
                return removed
        raise KeyError("记录不存在")

    # ---------- 留言 ----------

    def add_message(self, content: str, description: str, author: str) -> dict[str, Any]:
        if not self.is_unlocked():
            raise PermissionError("请先完善双方情侣信息")
        content = content.strip()
        if not content:
            raise ValueError("留言内容不能为空")
        item = {
            "id": _new_id(),
            "content": content,
            "description": description.strip(),
            "author": author,
            "created_at": _now_iso(),
        }
        self._data["messages"].insert(0, item)
        self._save()
        return item

    def list_messages(self) -> list[dict[str, Any]]:
        return list(self._data["messages"])

    def delete_message(self, item_id: str) -> dict[str, Any]:
        for i, item in enumerate(self._data["messages"]):
            if item["id"] == item_id:
                removed = self._data["messages"].pop(i)
                self._move_to_trash("message", removed)
                self._save()
                return removed
        raise KeyError("留言不存在")

    # ---------- 相册 ----------

    def add_album(self, image: str, description: str, who: str = "1") -> dict[str, Any]:
        if not self.is_unlocked():
            raise PermissionError("请先完善双方情侣信息")
        if not image:
            raise ValueError("请上传图片")
        item = {
            "id": _new_id(),
            "image": image,
            "description": description.strip(),
            "created_at": _now_iso(),
        }
        self._data["album"].insert(0, item)
        self._save()
        self.log_activity(who, "album", description[:50] if description else "")
        return item

    def list_album(self) -> list[dict[str, Any]]:
        return list(self._data["album"])

    def delete_album(self, item_id: str) -> dict[str, Any]:
        for i, item in enumerate(self._data["album"]):
            if item["id"] == item_id:
                removed = self._data["album"].pop(i)
                self._move_to_trash("album", removed)
                self._save()
                return removed
        raise KeyError("照片不存在")

    # ---------- 一百件事 ----------

    def list_bucket(self) -> list[dict[str, Any]]:
        return list(self._data["bucket_list"])

    def toggle_bucket(self, item_id: str, who: str = "1") -> dict[str, Any]:
        if not self.is_unlocked():
            raise PermissionError("请先完善双方情侣信息")
        for item in self._data["bucket_list"]:
            if item["id"] == item_id:
                item["done"] = not item["done"]
                item["done_at"] = _now_iso() if item["done"] else ""
                self._save()
                action = "bucket_done" if item["done"] else "bucket_undone"
                self.log_activity(who, action, item["title"])
                return item
        raise KeyError("项目不存在")

    def update_bucket_note(self, item_id: str, note: str) -> dict[str, Any]:
        for item in self._data["bucket_list"]:
            if item["id"] == item_id:
                item["note"] = note.strip()
                self._save()
                return item
        raise KeyError("项目不存在")

    def bucket_stats(self) -> dict[str, int]:
        items = self._data["bucket_list"]
        done = sum(1 for x in items if x["done"])
        return {"total": len(items), "done": done, "left": len(items) - done}

    # ---------- 倒数日 ----------

    def add_countdown(
        self, title: str, target_date: str, event_type: str, who: str = "1"
    ) -> dict[str, Any]:
        if not self.is_unlocked():
            raise PermissionError("请先完善双方情侣信息")
        title = title.strip()
        if not title:
            raise ValueError("标题不能为空")
        if not target_date:
            raise ValueError("日期不能为空")
        item = {
            "id": _new_id(),
            "title": title,
            "date": target_date,
            "type": event_type,
            "created_at": _now_iso(),
        }
        self._data["countdowns"].append(item)
        self._data["countdowns"].sort(key=lambda x: x["date"])
        self._save()
        self.log_activity(who, "countdown", title)
        return item

    def list_countdowns(self) -> list[dict[str, Any]]:
        today = date.today()
        result = []
        for item in self._data["countdowns"]:
            try:
                target = date.fromisoformat(item["date"])
                delta = (target - today).days
            except ValueError:
                delta = 0
            enriched = {**item, "days_left": delta}
            result.append(enriched)
        result.sort(key=lambda x: abs(x["days_left"]))
        return result

    def delete_countdown(self, item_id: str) -> dict[str, Any]:
        for i, item in enumerate(self._data["countdowns"]):
            if item["id"] == item_id:
                removed = self._data["countdowns"].pop(i)
                self._move_to_trash("countdown", removed)
                self._save()
                return removed
        raise KeyError("倒数日不存在")

    # ---------- 回收站 ----------

    def list_trash(self) -> list[TrashItem]:
        return sorted(
            self._trash.values(),
            key=lambda t: t.deleted_at,
            reverse=True,
        )

    def restore(self, trash_id: str) -> TrashItem:
        trashed = self._trash.pop(trash_id, None)
        if trashed is None:
            raise KeyError("回收站中未找到该项目")
        item = trashed.data
        mapping = {
            "period": "period_records",
            "message": "messages",
            "album": "album",
            "countdown": "countdowns",
        }
        key = mapping.get(trashed.item_type)
        if key:
            self._data[key].insert(0, item)
            self._save()
        self._save_trash()
        return trashed

    def permanent_delete(self, trash_id: str) -> TrashItem:
        trashed = self._trash.pop(trash_id, None)
        if trashed is None:
            raise KeyError("回收站中未找到该项目")
        self._delete_trash_files(trashed)
        self._save_trash()
        return trashed

    def _delete_trash_files(self, trashed: TrashItem) -> None:
        if trashed.item_type == "album" and trashed.data.get("image"):
            path = os.path.join(UPLOAD_DIR, trashed.data["image"])
            if os.path.isfile(path):
                os.remove(path)

    def empty_trash(self) -> int:
        count = len(self._trash)
        for trashed in list(self._trash.values()):
            self._delete_trash_files(trashed)
        self._trash.clear()
        self._save_trash()
        return count

    TYPE_LABELS = {
        "period": "例假记录",
        "message": "留言",
        "album": "相册",
        "countdown": "倒数日",
    }
