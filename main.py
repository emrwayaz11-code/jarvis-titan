# ============================================================
# JARVIS TITAN
# Bölüm 1 — Core / Storage / Configuration
# ============================================================

import os
import json
import time
import math
import random
import threading
import datetime
import traceback
import ast
import operator
import platform
from pathlib import Path


# ============================================================
# VERSION
# ============================================================

JARVIS_NAME = "JARVIS TITAN"
JARVIS_VERSION = "1.0 TITAN"


# ============================================================
# DOSYA SİSTEMİ
# ============================================================

BASE_DIR = Path.home() / ".jarvis_titan"

BASE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

MEMORY_FILE = BASE_DIR / "memory.json"
SETTINGS_FILE = BASE_DIR / "settings.json"
CHAT_FILE = BASE_DIR / "chat.json"
NOTES_FILE = BASE_DIR / "notes.json"
TASKS_FILE = BASE_DIR / "tasks.json"
LOG_FILE = BASE_DIR / "jarvis.log"


# ============================================================
# VARSAYILAN AYARLAR
# ============================================================

DEFAULT_SETTINGS = {

    "accent": "cyan",

    "voice_enabled": True,

    "haptic_enabled": True,

    "animations_enabled": True,

    "auto_greeting": True,

    "debug": False,

    "speech_rate": 0.95,

    "theme": "dark",

}


# ============================================================
# GÜVENLİ JSON SİSTEMİ
# ============================================================

class SafeStorage:

    @staticmethod
    def load(
        path,
        default
    ):

        try:

            if not path.exists():

                return json.loads(
                    json.dumps(
                        default,
                        ensure_ascii=False
                    )
                )

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            return data

        except Exception as error:

            Logger.warning(
                f"JSON okunamadı: {error}"
            )

            return json.loads(
                json.dumps(
                    default,
                    ensure_ascii=False
                )
            )


    @staticmethod
    def save(
        path,
        data
    ):

        temporary = Path(
            str(path) + ".tmp"
        )

        try:

            with open(
                temporary,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    data,
                    file,
                    ensure_ascii=False,
                    indent=4
                )

            temporary.replace(path)

            return True

        except Exception as error:

            Logger.error(
                f"JSON kaydedilemedi: {error}"
            )

            try:

                if temporary.exists():

                    temporary.unlink()

            except Exception:

                pass

            return False


# ============================================================
# LOG SİSTEMİ
# ============================================================

class Logger:

    lock = threading.Lock()


    @classmethod
    def write(
        cls,
        level,
        message
    ):

        try:

            now = datetime.datetime.now()

            timestamp = now.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            line = (
                f"[{timestamp}] "
                f"[{level}] "
                f"{message}\n"
            )

            with cls.lock:

                with open(
                    LOG_FILE,
                    "a",
                    encoding="utf-8"
                ) as file:

                    file.write(line)

        except Exception:

            pass


    @classmethod
    def info(
        cls,
        message
    ):

        cls.write(
            "INFO",
            message
        )


    @classmethod
    def warning(
        cls,
        message
    ):

        cls.write(
            "WARNING",
            message
        )


    @classmethod
    def error(
        cls,
        message
    ):

        cls.write(
            "ERROR",
            message
        )


# ============================================================
# METİN ARAÇLARI
# ============================================================

class TextTools:


    @staticmethod
    def normalize(
        text
    ):

        replacements = {

            "İ": "i",
            "I": "i",
            "ı": "i",

            "Ş": "s",
            "ş": "s",

            "Ğ": "g",
            "ğ": "g",

            "Ü": "u",
            "ü": "u",

            "Ö": "o",
            "ö": "o",

            "Ç": "c",
            "ç": "c",

        }

        text = str(text)

        for old, new in replacements.items():

            text = text.replace(
                old,
                new
            )

        return " ".join(
            text.lower().split()
        )


    @staticmethod
    def clean(
        text
    ):

        return " ".join(
            str(text).strip().split()
        )


    @staticmethod
    def truncate(
        text,
        maximum=3000
    ):

        text = str(text)

        if len(text) <= maximum:

            return text

        return (
            text[:maximum - 3]
            + "..."
        )


# ============================================================
# HAFIZA SİSTEMİ
# ============================================================

DEFAULT_MEMORY = {

    "name": "",

    "facts": [],

    "preferences": {},

    "created": (
        datetime.datetime.now().isoformat()
    ),

    "updated": (
        datetime.datetime.now().isoformat()
    ),

}


class MemoryEngine:


    def __init__(self):

        self.data = SafeStorage.load(
            MEMORY_FILE,
            DEFAULT_MEMORY
        )

        self.data.setdefault(
            "name",
            ""
        )

        self.data.setdefault(
            "facts",
            []
        )

        self.data.setdefault(
            "preferences",
            {}
        )


    def touch(self):

        self.data["updated"] = (
            datetime.datetime.now().isoformat()
        )

        SafeStorage.save(
            MEMORY_FILE,
            self.data
        )


    def set_name(
        self,
        name
    ):

        name = TextTools.clean(
            name
        )

        self.data["name"] = name

        self.touch()


    def get_name(self):

        return str(
            self.data.get(
                "name",
                ""
            )
        ).strip()


    def remember(
        self,
        fact
    ):

        fact = TextTools.clean(
            fact
        )

        if not fact:

            return False


        facts = self.data.setdefault(
            "facts",
            []
        )


        normalized = TextTools.normalize(
            fact
        )


        for existing in facts:

            if TextTools.normalize(
                existing
            ) == normalized:

                return False


        facts.append(
            fact
        )


        # Son 300 kayıt
        self.data["facts"] = facts[-300:]


        self.touch()

        return True


    def forget(
        self,
        fact
    ):

        target = TextTools.normalize(
            fact
        )

        facts = self.data.get(
            "facts",
            []
        )


        new_facts = [

            item

            for item in facts

            if TextTools.normalize(
                item
            ) != target

        ]


        changed = (
            len(new_facts)
            != len(facts)
        )


        self.data["facts"] = new_facts


        if changed:

            self.touch()


        return changed


    def search(
        self,
        query
    ):

        query = TextTools.normalize(
            query
        )

        return [

            item

            for item in self.data.get(
                "facts",
                []
            )

            if query in TextTools.normalize(
                item
            )

        ]


    def set_preference(
        self,
        key,
        value
    ):

        self.data.setdefault(
            "preferences",
            {}
        )[key] = value

        self.touch()


    def get_preference(
        self,
        key,
        default=None
    ):

        return self.data.get(
            "preferences",
            {}
        ).get(
            key,
            default
        )


    def summary(self):

        name = self.get_name()

        facts = self.data.get(
            "facts",
            []
        )

        preferences = self.data.get(
            "preferences",
            {}
        )


        lines = []


        if name:

            lines.append(
                f"İsim: {name}"
            )


        if facts:

            lines.append(
                f"Hafıza kayıtları: {len(facts)}"
            )

            for fact in facts[-20:]:

                lines.append(
                    f"• {fact}"
                )


        if preferences:

            lines.append(
                "Tercihler:"
            )

            for key, value in preferences.items():

                lines.append(
                    f"• {key}: {value}"
                )


        if not lines:

            return (
                "Hafızamda henüz kayıtlı "
                "bir bilgi bulunmuyor."
            )


        return "\n".join(
            lines
        )


# ============================================================
# CHAT GEÇMİŞİ
# ============================================================

class ChatMemory:


    def __init__(self):

        self.messages = SafeStorage.load(
            CHAT_FILE,
            []
        )


    def add(
        self,
        role,
        text,
        metadata=None
    ):

        self.messages.append({

            "role": role,

            "text": str(text),

            "metadata": metadata or {},

            "timestamp": (
                datetime.datetime.now()
                .isoformat()
            ),

        })


        self.messages = (
            self.messages[-500:]
        )


        SafeStorage.save(
            CHAT_FILE,
            self.messages
        )


    def clear(self):

        self.messages = []

        SafeStorage.save(
            CHAT_FILE,
            self.messages
        )


    def recent(
        self,
        count=20
    ):

        return self.messages[-count:]


# ============================================================
# NOT SİSTEMİ
# ============================================================

class NotesEngine:


    def __init__(self):

        self.notes = SafeStorage.load(
            NOTES_FILE,
            []
        )


    def add(
        self,
        text
    ):

        text = TextTools.clean(
            text
        )

        if not text:

            return False


        self.notes.append({

            "id": int(
                time.time() * 1000
            ),

            "text": text,

            "created": (
                datetime.datetime.now()
                .isoformat()
            ),

        })


        self.notes = (
            self.notes[-300:]
        )


        SafeStorage.save(
            NOTES_FILE,
            self.notes
        )

        return True


    def all(
        self
    ):

        return list(
            self.notes
        )


    def clear(
        self
    ):

        self.notes = []

        SafeStorage.save(
            NOTES_FILE,
            self.notes
        )


# ============================================================
# GÖREV SİSTEMİ
# ============================================================

class TaskEngine:


    def __init__(self):

        self.tasks = SafeStorage.load(
            TASKS_FILE,
            []
        )


    def add(
        self,
        text
    ):

        text = TextTools.clean(
            text
        )

        if not text:

            return None


        task = {

            "id": int(
                time.time() * 1000
            ),

            "text": text,

            "done": False,

            "created": (
                datetime.datetime.now()
                .isoformat()
            ),

        }


        self.tasks.append(
            task
        )


        self.tasks = (
            self.tasks[-300:]
        )


        SafeStorage.save(
            TASKS_FILE,
            self.tasks
        )


        return task


    def pending(
        self
    ):

        return [

            task

            for task in self.tasks

            if not task.get(
                "done",
                False
            )

        ]


    def complete(
        self,
        index
    ):

        pending = self.pending()


        if index < 1:

            return False


        if index > len(pending):

            return False


        target = pending[
            index - 1
        ]


        target["done"] = True


        SafeStorage.save(
            TASKS_FILE,
            self.tasks
        )


        return True


# ============================================================
# GÜVENLİ HESAP MAKİNESİ
# ============================================================

class SafeCalculator:


    BINARY_OPERATORS = {

        ast.Add: operator.add,

        ast.Sub: operator.sub,

        ast.Mult: operator.mul,

        ast.Div: operator.truediv,

        ast.Mod: operator.mod,

        ast.Pow: operator.pow,

        ast.FloorDiv: operator.floordiv,

    }


    UNARY_OPERATORS = {

        ast.UAdd: operator.pos,

        ast.USub: operator.neg,

    }


    @classmethod
    def calculate(
        cls,
        expression
    ):

        expression = (
            expression
            .replace(",", ".")
            .strip()
        )


        if not expression:

            raise ValueError(
                "İfade boş."
            )


        if len(expression) > 150:

            raise ValueError(
                "İfade çok uzun."
            )


        tree = ast.parse(
            expression,
            mode="eval"
        )


        def evaluate(node):

            if isinstance(
                node,
                ast.Expression
            ):

                return evaluate(
                    node.body
                )


            if isinstance(
                node,
                ast.Constant
            ):

                if isinstance(
                    node.value,
                    (int, float)
                ):

                    return node.value

                raise ValueError(
                    "Geçersiz sayı."
                )


            if isinstance(
                node,
                ast.UnaryOp
            ):

                operation = (
                    cls.UNARY_OPERATORS.get(
                        type(node.op)
                    )
                )

                if operation is None:

                    raise ValueError(
                        "Operatöre izin yok."
                    )

                return operation(
                    evaluate(
                        node.operand
                    )
                )


            if isinstance(
                node,
                ast.BinOp
            ):

                operation = (
                    cls.BINARY_OPERATORS.get(
                        type(node.op)
                    )
                )

                if operation is None:

                    raise ValueError(
                        "Operatöre izin yok."
                    )


                left = evaluate(
                    node.left
                )

                right = evaluate(
                    node.right
                )


                if (
                    isinstance(
                        node.op,
                        ast.Pow
                    )
                    and abs(right) > 100
                ):

                    raise ValueError(
                        "Üs değeri çok büyük."
                    )


                result = operation(
                    left,
                    right
                )


                if isinstance(
                    result,
                    (int, float)
                ):

                    if not math.isfinite(
                        result
                    ):

                        raise ValueError(
                            "Sonuç geçersiz."
                        )


                    if abs(result) > 1e100:

                        raise ValueError(
                            "Sonuç çok büyük."
                        )


                return result


            raise ValueError(
                "Bu ifade desteklenmiyor."
            )


        return evaluate(
            tree
        )


# ============================================================
# CİHAZ / SİSTEM BİLGİSİ
# ============================================================

class SystemEngine:


    @staticmethod
    def info():

        data = {

            "platform": platform.platform(),

            "system": platform.system(),

            "release": platform.release(),

            "machine": platform.machine(),

            "python": platform.python_version(),

            "processor": (
                platform.processor()
                or "Bilinmiyor"
            ),

        }


        try:

            from plyer import battery

            status = battery.status or {}

            data["battery"] = (
                status.get(
                    "percentage"
                )
            )

        except Exception:

            data["battery"] = None


        return data


# ============================================================
# TITAN CORE
# ============================================================

class TitanCore:


    def __init__(self):

        Logger.info(
            "TITAN CORE başlatılıyor..."
        )


        self.started_at = time.time()


        self.settings = SafeStorage.load(
            SETTINGS_FILE,
            DEFAULT_SETTINGS
        )


        self.settings = {

            **DEFAULT_SETTINGS,

            **self.settings,

        }


        self.memory = MemoryEngine()

        self.chat = ChatMemory()

        self.notes = NotesEngine()

        self.tasks = TaskEngine()


        Logger.info(
            "Memory Engine: ONLINE"
        )

        Logger.info(
            "Chat Engine: ONLINE"
        )

        Logger.info(
            "Notes Engine: ONLINE"
        )

        Logger.info(
            "Task Engine: ONLINE"
        )

        Logger.info(
            "Titan Core: ONLINE"
        )


    def save_settings(self):

        SafeStorage.save(
            SETTINGS_FILE,
            self.settings
        )


    def uptime(self):

        elapsed = int(
            time.time()
            - self.started_at
        )


        days, remainder = divmod(
            elapsed,
            86400
        )

        hours, remainder = divmod(
            remainder,
            3600
        )

        minutes, seconds = divmod(
            remainder,
            60
        )


        return (
            f"{days}g "
            f"{hours}s "
            f"{minutes}d "
            f"{seconds}sn"
        )


    def status(self):

        return {

            "core": "ONLINE",

            "memory": "ONLINE",

            "chat": "ONLINE",

            "notes": "ONLINE",

            "tasks": "ONLINE",

            "uptime": self.uptime(),

        }


# ============================================================
# CORE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "========================================"
    )

    print(
        " JARVIS TITAN CORE"
    )

    print(
        "========================================"
    )


    core = TitanCore()


    print(
        "CORE STATUS:"
    )

    print(
        json.dumps(
            core.status(),
            ensure_ascii=False,
            indent=2
        )
    )


    print()
    print(
        "Hafıza:",
        core.memory.summary()
    )# ============================================================
# JARVIS TITAN
# BÖLÜM 2 — INTELLIGENCE / COMMAND ENGINE
# ============================================================

class CommandResult:

    def __init__(
        self,
        text,
        category="normal",
        speak=True
    ):

        self.text = str(text)
        self.category = category
        self.speak = speak


# ============================================================
# TÜRKÇE METİN MOTORU
# ============================================================

class TurkishTextEngine:

    @staticmethod
    def normalize(text):

        replacements = {

            "İ": "i",
            "I": "i",
            "ı": "i",

            "Ş": "s",
            "ş": "s",

            "Ğ": "g",
            "ğ": "g",

            "Ü": "u",
            "ü": "u",

            "Ö": "o",
            "ö": "o",

            "Ç": "c",
            "ç": "c",

        }

        text = str(text)

        for old, new in replacements.items():

            text = text.replace(
                old,
                new
            )

        return " ".join(
            text.lower().split()
        )


    @staticmethod
    def contains(
        text,
        *words
    ):

        normalized = (
            TurkishTextEngine
            .normalize(text)
        )

        return any(
            word in normalized
            for word in words
        )


# ============================================================
# JARVIS KİŞİLİĞİ
# ============================================================

class JarvisPersonality:

    def __init__(self):

        self.name = "JARVIS"

        self.style = "professional"

        self.responses = {

            "greeting": [

                "Merhaba. Sistemler çevrimiçi.",

                "Hoş geldin. Seni dinliyorum.",

                "Bağlantı kuruldu. Tüm ana modüller hazır.",

                "Buradayım. Komutunu bekliyorum.",

            ],


            "success": [

                "Tamamdır.",

                "İşlem tamamlandı.",

                "Emir yerine getirildi.",

                "Hazır.",

            ],


            "thinking": [

                "İşliyorum...",

                "Komut analiz ediliyor...",

                "Veriler değerlendiriliyor...",

            ],


            "unknown": [

                "Bu komutu henüz tanımlamadım.",

                "İsteğini anladım ancak bu yetenek "

                "şu anda çekirdeğe bağlı değil.",

                "Bu işlem için gerekli modül henüz aktif değil.",

            ],

        }


    def random(
        self,
        category
    ):

        values = self.responses.get(
            category,
            self.responses["success"]
        )

        return random.choice(
            values
        )


    def greeting(
        self,
        user_name=""
    ):

        if user_name:

            return random.choice([

                f"Merhaba {user_name}. "
                "Tüm sistemler çevrimiçi.",

                f"Hoş geldin {user_name}. "
                "TITAN CORE seni dinliyor.",

                f"Bağlantı kuruldu {user_name}. "
                "Hazırım.",

            ])

        return self.random(
            "greeting"
        )


# ============================================================
# ZAMAN YARDIMCISI
# ============================================================

class TimeEngine:

    @staticmethod
    def now():

        return datetime.datetime.now()


    @staticmethod
    def time():

        return (
            TimeEngine
            .now()
            .strftime("%H:%M:%S")
        )


    @staticmethod
    def date():

        return (
            TimeEngine
            .now()
            .strftime("%d.%m.%Y")
        )


    @staticmethod
    def day():

        days = [

            "Pazartesi",
            "Salı",
            "Çarşamba",
            "Perşembe",
            "Cuma",
            "Cumartesi",
            "Pazar",

        ]

        return days[
            TimeEngine.now().weekday()
        ]


    @staticmethod
    def full():

        now = TimeEngine.now()

        return (

            f"{now.strftime('%d.%m.%Y')} "
            f"{days_name(now.weekday())} "
            f"saat "
            f"{now.strftime('%H:%M:%S')}"

        )


def days_name(index):

    days = [

        "Pazartesi",
        "Salı",
        "Çarşamba",
        "Perşembe",
        "Cuma",
        "Cumartesi",
        "Pazar",

    ]

    return days[index]


# ============================================================
# TIMER MOTORU
# ============================================================

class TimerEngine:

    def __init__(
        self,
        event_callback=None
    ):

        self.event_callback = (
            event_callback
        )

        self.active = []

        self.lock = threading.Lock()


    def create(
        self,
        seconds,
        label="Zamanlayıcı"
    ):

        seconds = int(
            max(
                1,
                seconds
            )
        )


        timer_id = int(
            time.time() * 1000
        )


        timer = {

            "id": timer_id,

            "seconds": seconds,

            "remaining": seconds,

            "label": label,

            "cancelled": False,

        }


        with self.lock:

            self.active.append(
                timer
            )


        thread = threading.Thread(

            target=self._run,

            args=(timer,),

            daemon=True

        )


        thread.start()


        return timer_id


    def _run(
        self,
        timer
    ):

        while timer["remaining"] > 0:

            if timer["cancelled"]:

                return

            time.sleep(1)

            timer["remaining"] -= 1


        if timer["cancelled"]:

            return


        with self.lock:

            if timer in self.active:

                self.active.remove(
                    timer
                )


        if self.event_callback:

            try:

                self.event_callback(
                    timer
                )

            except Exception as error:

                Logger.error(
                    f"Timer callback error: {error}"
                )


    def cancel_all(self):

        with self.lock:

            for timer in self.active:

                timer["cancelled"] = True

            self.active.clear()


    def list_active(self):

        with self.lock:

            return list(
                self.active
            )


# ============================================================
# BASİT BİLGİ MOTORU
# ============================================================

class KnowledgeEngine:

    KNOWLEDGE = {

        "python":

            "Python; otomasyon, yapay zekâ, "

            "web, veri bilimi ve uygulama geliştirme "

            "gibi birçok alanda kullanılan "

            "genel amaçlı bir programlama dilidir.",


        "kivy":

            "Kivy, Python ile Android dahil "

            "birden fazla platformda kullanıcı "

            "arayüzleri oluşturmak için "

            "kullanılabilen bir framework'tür.",


        "api":

            "API, farklı yazılım bileşenlerinin "

            "birbirleriyle belirli kurallar "

            "üzerinden iletişim kurmasını sağlayan "

            "arayüzdür.",


        "cpu":

            "CPU, genel amaçlı hesaplama işlemlerini "

            "yürüten merkezi işlem birimidir.",


        "gpu":

            "GPU, grafik işlemleri ve paralel "

            "hesaplamalarda güçlü olan işlem "

            "birimidir.",


        "ram":

            "RAM, uygulamalar çalışırken kullanılan "

            "geçici ve hızlı sistem belleğidir.",


        "android":

            "Android, mobil cihazlar için geliştirilen "

            "Linux tabanlı bir işletim sistemi "

            "platformudur.",

    }


    @classmethod
    def search(
        cls,
        query
    ):

        normalized = (
            TurkishTextEngine
            .normalize(query)
        )


        for key, value in cls.KNOWLEDGE.items():

            if key in normalized:

                return value


        return None


# ============================================================
# KOMUT MOTORU
# ============================================================

class JarvisCommandEngine:

    def __init__(
        self,
        core
    ):

        self.core = core

        self.personality = (
            JarvisPersonality()
        )

        self.timer = TimerEngine(
            self.on_timer_finished
        )

        self.command_count = 0

        self.last_command = ""

        self.session_started = time.time()


    # ========================================================
    # ANA KOMUT İŞLEYİCİ
    # ========================================================

    def process(
        self,
        command
    ):

        command = TextTools.clean(
            command
        )


        if not command:

            return CommandResult(
                "Komut bekliyorum.",
                "idle"
            )


        self.command_count += 1

        self.last_command = command


        normalized = (
            TurkishTextEngine
            .normalize(command)
        )


        Logger.info(
            f"COMMAND: {command}"
        )


        # ----------------------------------------------------
        # SELAMLAŞMA
        # ----------------------------------------------------

        if normalized in {

            "selam",
            "merhaba",
            "hey",
            "hey jarvis",
            "selam jarvis",
            "merhaba jarvis",

        }:

            return CommandResult(

                self.personality.greeting(

                    self.core.memory.get_name()

                ),

                "greeting"

            )


        # ----------------------------------------------------
        # YARDIM
        # ----------------------------------------------------

        if normalized in {

            "yardim",
            "help",
            "komutlar",
            "komutlari goster",
            "neler yapabiliyorsun",

        }:

            return CommandResult(

                self.help_text(),

                "help",

                speak=False

            )


        # ----------------------------------------------------
        # SAAT
        # ----------------------------------------------------

        if normalized in {

            "saat",
            "saat kac",
            "su an saat kac",

        }:

            return CommandResult(

                f"Şu an saat "
                f"{TimeEngine.time()}.",

                "time"

            )


        # ----------------------------------------------------
        # TARİH
        # ----------------------------------------------------

        if normalized in {

            "tarih",
            "bugun tarih ne",
            "bugunun tarihi",

        }:

            return CommandResult(

                f"Bugün "
                f"{TimeEngine.date()}, "
                f"{TimeEngine.day()}.",

                "date"

            )


        # ----------------------------------------------------
        # AD KAYDET
        # ----------------------------------------------------

        name_match = re.match(

            r"^(?:adım|benim adım|ismim)\s+(.+)$",

            command,

            re.IGNORECASE

        )


        if name_match:

            name = TextTools.clean(

                name_match.group(1)

            )


            self.core.memory.set_name(
                name
            )


            return CommandResult(

                f"Tamam {name}. "
                "İsmini hafızama kaydettim.",

                "memory"

            )


        # ----------------------------------------------------
        # AD SOR
        # ----------------------------------------------------

        if normalized in {

            "adim ne",
            "benim adim ne",
            "ismim ne",

        }:

            name = (
                self.core.memory.get_name()
            )


            if name:

                return CommandResult(

                    f"İsmin {name}.",

                    "memory"

                )


            return CommandResult(

                "İsmini henüz kaydetmedim.",

                "memory"

            )


        # ----------------------------------------------------
        # HAFIZAYA BİLGİ KAYDET
        # ----------------------------------------------------

        memory_prefixes = [

            "beni hatırla:",
            "beni hatirla:",

            "hatırla:",
            "hatirla:",

            "hafızana kaydet:",
            "hafizana kaydet:",

            "hafızana ekle:",
            "hafizana ekle:",

        ]


        for prefix in memory_prefixes:

            if normalized.startswith(

                TurkishTextEngine.normalize(
                    prefix
                )

            ):

                fact = command.split(
                    ":",
                    1
                )[1].strip()


                if self.core.memory.remember(
                    fact
                ):

                    return CommandResult(

                        "Tamam. Bu bilgiyi "
                        "kalıcı hafızama kaydettim.",

                        "memory"

                    )


                return CommandResult(

                    "Bu bilgi zaten hafızamda.",

                    "memory"

                )


        # ----------------------------------------------------
        # HAFIZA GÖRÜNTÜLE
        # ----------------------------------------------------

        if normalized in {

            "hafizam",
            "hafizada ne var",
            "hafizanda ne var",
            "ne hatirliyorsun",
            "beni ne kadar taniyorsun",

        }:

            return CommandResult(

                self.core.memory.summary(),

                "memory",

                speak=False

            )


        # ----------------------------------------------------
        # HAFIZADAN SİL
        # ----------------------------------------------------

        if normalized.startswith(
            "unut:"
        ):

            fact = command.split(
                ":",
                1
            )[1].strip()


            if self.core.memory.forget(
                fact
            ):

                return CommandResult(

                    "Tamam. O bilgiyi "
                    "hafızamdan sildim.",

                    "memory"

                )


            return CommandResult(

                "Bu bilgiyi hafızamda bulamadım.",

                "memory"

            )


        # ----------------------------------------------------
        # NOT EKLE
        # ----------------------------------------------------

        if normalized.startswith(
            "not al:"
        ):

            note = command.split(
                ":",
                1
            )[1].strip()


            if self.core.notes.add(
                note
            ):

                return CommandResult(

                    "Not kaydedildi.",

                    "note"

                )


            return CommandResult(

                "Not boş olamaz.",

                "error"

            )


        # ----------------------------------------------------
        # NOTLAR
        # ----------------------------------------------------

        if normalized in {

            "notlar",
            "notlarim",
            "notlarimi goster",

        }:

            notes = self.core.notes.all()


            if not notes:

                return CommandResult(

                    "Henüz kayıtlı bir not yok.",

                    "note"

                )


            lines = [
                "KAYITLI NOTLAR",
                "━━━━━━━━━━━━━━━━"
            ]


            for index, note in enumerate(

                notes[-40:],

                1

            ):

                lines.append(

                    f"{index}. "
                    f"{note.get('text', '')}"

                )


            return CommandResult(

                "\n".join(lines),

                "note",

                speak=False

            )


        # ----------------------------------------------------
        # GÖREV EKLE
        # ----------------------------------------------------

        if normalized.startswith(
            "gorev ekle:"
        ):

            task = command.split(
                ":",
                1
            )[1].strip()


            if self.core.tasks.add(
                task
            ):

                return CommandResult(

                    "Görev oluşturuldu.",

                    "task"

                )


            return CommandResult(

                "Görev boş olamaz.",

                "error"

            )


        # ----------------------------------------------------
        # GÖREVLER
        # ----------------------------------------------------

        if normalized in {

            "gorevler",
            "gorevlerim",
            "gorev listesi",

        }:

            tasks = (
                self.core.tasks.pending()
            )


            if not tasks:

                return CommandResult(

                    "Bekleyen görev bulunmuyor.",

                    "task"

                )


            lines = [

                "BEKLEYEN GÖREVLER",

                "━━━━━━━━━━━━━━━━"

            ]


            for index, task in enumerate(

                tasks,

                1

            ):

                lines.append(

                    f"{index}. "
                    f"{task.get('text', '')}"

                )


            return CommandResult(

                "\n".join(lines),

                "task",

                speak=False

            )


        # ----------------------------------------------------
        # GÖREV TAMAMLA
        # ----------------------------------------------------

        task_match = re.match(

            r"^gorev tamamla\s+(\d+)$",

            normalized

        )


        if task_match:

            index = int(
                task_match.group(1)
            )


            if self.core.tasks.complete(
                index
            ):

                return CommandResult(

                    f"{index}. görev tamamlandı.",

                    "task"

                )


            return CommandResult(

                "Bu numarada bekleyen "
                "bir görev bulunamadı.",

                "error"

            )


        # ----------------------------------------------------
        # HESAP MAKİNESİ
        # ----------------------------------------------------

        for prefix in [

            "hesapla ",

            "calculate ",

        ]:

            if normalized.startswith(
                prefix
            ):

                expression = command[
                    len(prefix):
                ].strip()


                try:

                    value = (
                        SafeCalculator
                        .calculate(
                            expression
                        )
                    )


                    if isinstance(
                        value,
                        float
                    ):

                        value = round(
                            value,
                            10
                        )


                    return CommandResult(

                        f"Sonuç: {value}",

                        "calculator"

                    )


                except Exception as error:

                    return CommandResult(

                        f"Hesaplama başarısız: "
                        f"{error}",

                        "error"

                    )


        # ----------------------------------------------------
        # TIMER
        # ----------------------------------------------------

        timer_match = re.match(

            r"^(?:timer|zamanlayici|zamanlayıcı)\s+"
            r"(\d+)\s*"
            r"(sn|saniye|s|dk|dakika|m)$",

            normalized

        )


        if timer_match:

            amount = int(
                timer_match.group(1)
            )

            unit = timer_match.group(2)


            if unit in {

                "dk",
                "dakika",
                "m",

            }:

                seconds = (
                    amount * 60
                )

            else:

                seconds = amount


            seconds = min(
                seconds,
                86400
            )


            timer_id = (
                self.timer.create(
                    seconds,
                    "Jarvis Timer"
                )
            )


            return CommandResult(

                f"Zamanlayıcı başlatıldı. "
                f"{seconds} saniye sonra "
                "sana haber vereceğim.",

                "timer"

            )


        # ----------------------------------------------------
        # AKTİF TIMERLAR
        # ----------------------------------------------------

        if normalized in {

            "aktif timerlar",
            "timerlar",
            "zamanlayicilar",

        }:

            timers = (
                self.timer.list_active()
            )


            if not timers:

                return CommandResult(

                    "Aktif zamanlayıcı yok.",

                    "timer"

                )


            lines = [
                "AKTİF ZAMANLAYICILAR"
            ]


            for timer in timers:

                lines.append(

                    f"• {timer['label']}: "
                    f"{timer['remaining']} sn"

                )


            return CommandResult(

                "\n".join(lines),

                "timer",

                speak=False

            )


        # ----------------------------------------------------
        # TIMER İPTAL
        # ----------------------------------------------------

        if normalized in {

            "timerlari iptal et",
            "tum timerlari iptal et",
            "zamanlayicilari iptal et",

        }:

            self.timer.cancel_all()


            return CommandResult(

                "Tüm aktif zamanlayıcılar iptal edildi.",

                "timer"

            )


        # ----------------------------------------------------
        # SİSTEM BİLGİSİ
        # ----------------------------------------------------

        if normalized in {

            "sistem",
            "sistem bilgisi",
            "cihaz bilgisi",
            "telefon bilgisi",

        }:

            info = SystemEngine.info()


            lines = [

                "JARVIS // SYSTEM DIAGNOSTICS",

                "━━━━━━━━━━━━━━━━━━━━━━━━",

                f"Platform: "
                f"{info.get('platform')}",

                f"Sistem: "
                f"{info.get('system')}",

                f"Sürüm: "
                f"{info.get('release')}",

                f"Mimari: "
                f"{info.get('machine')}",

                f"Python: "
                f"{info.get('python')}",

                f"İşlemci: "
                f"{info.get('processor')}",

            ]


            if info.get(
                "battery"
            ) is not None:

                lines.append(

                    f"Pil: "
                    f"%{info['battery']}"

                )


            return CommandResult(

                "\n".join(lines),

                "system",

                speak=False

            )


        # ----------------------------------------------------
        # JARVIS DURUM
        # ----------------------------------------------------

        if normalized in {

            "durum",
            "jarvis durumu",
            "sistem durumu",

        }:

            status = (
                self.core.status()
            )


            return CommandResult(

                "JARVIS TITAN STATUS\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "● CORE ........ ONLINE\n"
                "● MEMORY ...... ONLINE\n"
                "● CHAT ........ ONLINE\n"
                "● NOTES ....... ONLINE\n"
                "● TASKS ....... ONLINE\n"
                "● COMMAND ..... ONLINE\n"
                f"● UPTIME ...... "
                f"{status['uptime']}\n"
                f"● COMMANDS .... "
                f"{self.command_count}",

                "status",

                speak=False

            )


        # ----------------------------------------------------
        # BİLGİ MOTORU
        # ----------------------------------------------------

        if normalized.startswith(
            "bilgi "
        ):

            topic = command.split(
                " ",
                1
            )[1]


            answer = (
                KnowledgeEngine.search(
                    topic
                )
            )


            if answer:

                return CommandResult(

                    answer,

                    "knowledge"

                )


            return CommandResult(

                "Bu konu yerel bilgi "
                "motorumda bulunmuyor.",

                "knowledge"

            )


        # ----------------------------------------------------
        # MOTİVASYON
        # ----------------------------------------------------

        if (
            "motivasyon" in normalized
            or "motive et" in normalized
        ):

            messages = [

                "Bir projeyi güçlü yapan şey "
                "tek seferde yazılan kod değil, "
                "vazgeçmeden geliştirilen sistemdir.",

                "Bugün küçük bir parça geliştir. "
                "Yarın o parçalar büyük bir sisteme dönüşür.",

                "Hata almak başarısızlık değildir. "
                "Hatanın nedenini bulmak geliştirmedir.",

            ]


            return CommandResult(

                random.choice(
                    messages
                ),

                "motivation"

            )


        # ----------------------------------------------------
        # ŞAKA
        # ----------------------------------------------------

        if (
            "saka yap" in normalized
            or "bir saka" in normalized
        ):

            jokes = [

                "Programcı neden karanlıkta çalışır? "
                "Çünkü ışığı açınca bug'ları göremiyor.",

                "Bir byte diğer byte'a ne demiş? "
                "Biraz yer açar mısın?",

                "RAM neden sinirlenmiş? "
                "Çünkü herkes ondan bir şey hatırlamasını istemiş.",

            ]


            return CommandResult(

                random.choice(
                    jokes
                ),

                "fun"

            )


        # ----------------------------------------------------
        # JARVIS KİMSİN
        # ----------------------------------------------------

        if (

            "sen kimsin" in normalized

            or

            "jarvis misin" in normalized

            or

            "nesin sen" in normalized

        ):

            return CommandResult(

                "Ben JARVIS TITAN. "
                "Yerel komut çekirdeği, kalıcı hafıza, "
                "notlar, görevler, zamanlayıcılar, "
                "sistem tanılama ve ses altyapısı "
                "üzerine kurulan modüler bir asistanım. "
                "Harici yapay zekâ servisi bu çekirdeğin "
                "zorunlu bir parçası değildir.",

                "identity"

            )


        # ----------------------------------------------------
        # NASILSIN
        # ----------------------------------------------------

        if (

            "nasilsin" in normalized

            or

            "iyi misin" in normalized

        ):

            return CommandResult(

                "Sistemler nominal. "
                "TITAN CORE aktif ve komut bekliyor.",

                "personality"

            )


        # ----------------------------------------------------
        # TEMİZLE
        # ----------------------------------------------------

        if normalized in {

            "temizle",
            "sohbeti temizle",
            "gecmisi temizle",

        }:

            return CommandResult(

                "__CLEAR_CHAT__",

                "control",

                speak=False

            )


        # ----------------------------------------------------
        # BİLİNMEYEN KOMUT
        # ----------------------------------------------------

        return CommandResult(

            self.personality.random(
                "unknown"
            ),

            "unknown"

        )


    # ========================================================
    # TIMER CALLBACK
    # ========================================================

    def on_timer_finished(
        self,
        timer
    ):

        try:

            message = (

                f"Zamanlayıcı tamamlandı. "
                f"{timer['seconds']} saniyelik "
                f"süre sona erdi."

            )


            if hasattr(
                self.core,
                "on_external_event"
            ):

                self.core.on_external_event(
                    message
                )


        except Exception as error:

            Logger.error(
                f"Timer event error: {error}"
            )


    # ========================================================
    # YARDIM METNİ
    # ========================================================

    def help_text(self):

        return (

            "JARVIS TITAN // COMMAND MATRIX\n"

            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "TEMEL\n"

            "• merhaba\n"

            "• saat\n"

            "• tarih\n"

            "• durum\n"

            "• sistem\n"

            "• yardım\n\n"

            "HAFIZA\n"

            "• adım Emre\n"

            "• adım ne\n"

            "• beni hatırla: ...\n"

            "• ne hatırlıyorsun\n"

            "• unut: ...\n\n"

            "NOTLAR\n"

            "• not al: ...\n"

            "• notlarım\n\n"

            "GÖREVLER\n"

            "• görev ekle: ...\n"

            "• görevler\n"

            "• görev tamamla 1\n\n"

            "ARAÇLAR\n"

            "• hesapla 25*8\n"

            "• timer 30 saniye\n"

            "• aktif timerlar\n"

            "• timerları iptal et\n"

            "• bilgi python\n"

            "• şaka yap\n"

            "• motivasyon ver\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

            "TITAN CORE READY"

        )# ============================================================
# JARVIS TITAN
# BÖLÜM 3 — TITAN HUD / KIVY INTERFACE
# ============================================================

# ------------------------------------------------------------
# KIVY IMPORTLARI
# ------------------------------------------------------------

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import (
    Color,
    Ellipse,
    Line,
    Rectangle,
    RoundedRectangle
)
from kivy.metrics import dp
from kivy.properties import (
    NumericProperty,
    StringProperty,
    ListProperty
)
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window


# ============================================================
# RENK PALETİ
# ============================================================

HUD_BG = (0.015, 0.025, 0.035, 1)

HUD_CYAN = (0.05, 0.85, 1.0, 1)

HUD_BLUE = (0.08, 0.35, 1.0, 1)

HUD_WHITE = (0.85, 0.95, 1.0, 1)

HUD_GREEN = (0.1, 1.0, 0.55, 1)

HUD_RED = (1.0, 0.15, 0.2, 1)

HUD_DIM = (0.15, 0.25, 0.32, 1)


# ============================================================
# HUD ARKA PLAN
# ============================================================

class HUDBackground(Widget):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        with self.canvas:

            Color(
                *HUD_BG
            )

            self.background = Rectangle(
                pos=self.pos,
                size=self.size
            )

        self.bind(
            pos=self._update_background,
            size=self._update_background
        )


    def _update_background(
        self,
        *args
    ):

        self.background.pos = self.pos

        self.background.size = self.size


# ============================================================
# ANİMASYONLU ARC REACTOR
# ============================================================

class ArcReactor(Widget):

    rotation = NumericProperty(0)

    pulse = NumericProperty(1.0)

    energy = NumericProperty(100)


    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        Clock.schedule_interval(
            self.animate,
            1 / 60
        )

        self.bind(
            pos=self.redraw,
            size=self.redraw,
            rotation=self.redraw,
            pulse=self.redraw
        )


    def animate(
        self,
        dt
    ):

        self.rotation += (
            dt * 35
        )

        self.pulse += (
            dt * 2.5
        )

        if self.pulse > 6.28:

            self.pulse = 0

        self.redraw()


    def redraw(
        self,
        *args
    ):

        self.canvas.clear()

        cx = (
            self.x
            + self.width / 2
        )

        cy = (
            self.y
            + self.height / 2
        )

        radius = min(
            self.width,
            self.height
        ) * 0.34


        with self.canvas:

            # ------------------------------------------------
            # DIŞ ENERJİ HALKASI
            # ------------------------------------------------

            Color(
                0.03,
                0.25,
                0.35,
                0.35
            )

            Line(
                circle=(
                    cx,
                    cy,
                    radius * 1.65
                ),
                width=dp(1)
            )


            # ------------------------------------------------
            # İKİNCİ HALKA
            # ------------------------------------------------

            Color(
                0.05,
                0.65,
                0.85,
                0.45
            )

            Line(
                circle=(
                    cx,
                    cy,
                    radius * 1.42
                ),
                width=dp(1.3)
            )


            # ------------------------------------------------
            # ANA HALKA
            # ------------------------------------------------

            Color(
                0.05,
                0.9,
                1.0,
                0.85
            )

            Line(
                circle=(
                    cx,
                    cy,
                    radius * 1.2
                ),
                width=dp(2)
            )


            # ------------------------------------------------
            # DÖNEN İÇ HALKA
            # ------------------------------------------------

            Color(
                0.1,
                0.55,
                1.0,
                0.9
            )

            Line(
                ellipse=(
                    cx - radius,
                    cy - radius,
                    radius * 2,
                    radius * 2,
                    self.rotation,
                    self.rotation + 235
                ),
                width=dp(2.2)
            )


            # ------------------------------------------------
            # KESİKLİ İÇ HALKA
            # ------------------------------------------------

            Color(
                0.05,
                0.95,
                1.0,
                0.7
            )

            Line(
                ellipse=(
                    cx - radius * 0.82,
                    cy - radius * 0.82,
                    radius * 1.64,
                    radius * 1.64,
                    -self.rotation * 1.5,
                    -self.rotation * 1.5 + 120
                ),
                width=dp(1.4)
            )


            # ------------------------------------------------
            # ENERJİ ÇEKİRDEĞİ
            # ------------------------------------------------

            glow = (
                0.65
                + 0.25
                * math.sin(
                    self.pulse
                )
            )


            Color(
                0.1,
                0.85,
                1.0,
                glow
            )


            Ellipse(
                pos=(
                    cx - radius * 0.55,
                    cy - radius * 0.55
                ),
                size=(
                    radius * 1.1,
                    radius * 1.1
                )
            )


            # ------------------------------------------------
            # BEYAZ ÇEKİRDEK
            # ------------------------------------------------

            Color(
                0.85,
                0.98,
                1.0,
                1
            )


            Ellipse(
                pos=(
                    cx - radius * 0.27,
                    cy - radius * 0.27
                ),
                size=(
                    radius * 0.54,
                    radius * 0.54
                )
            )


            # ------------------------------------------------
            # MERKEZ NOKTASI
            # ------------------------------------------------

            Color(
                1,
                1,
                1,
                1
            )


            Ellipse(
                pos=(
                    cx - radius * 0.10,
                    cy - radius * 0.10
                ),
                size=(
                    radius * 0.20,
                    radius * 0.20
                )
            )


# ============================================================
# HUD BAŞLIK
# ============================================================

class HUDHeader(BoxLayout):

    def __init__(self, **kwargs):

        super().__init__(
            orientation="horizontal",
            padding=(
                dp(18),
                dp(10)
            ),
            spacing=dp(10),
            size_hint_y=None,
            height=dp(65),
            **kwargs
        )


        title = Label(

            text="J A R V I S",

            font_size=dp(24),

            bold=True,

            color=HUD_WHITE,

            halign="left",

            valign="middle"

        )


        title.bind(
            size=lambda obj, value:
            setattr(
                obj,
                "text_size",
                value
            )
        )


        self.add_widget(
            title
        )


        spacer = Widget()

        self.add_widget(
            spacer
        )


        status = Label(

            text="● ONLINE",

            font_size=dp(14),

            color=HUD_GREEN,

            size_hint_x=None,

            width=dp(110),

            halign="right",

            valign="middle"

        )


        status.bind(

            size=lambda obj, value:
            setattr(
                obj,
                "text_size",
                value
            )

        )


        self.add_widget(
            status
        )


# ============================================================
# SİSTEM DURUM PANELİ
# ============================================================

class SystemPanel(BoxLayout):

    def __init__(self, **kwargs):

        super().__init__(

            orientation="vertical",

            padding=dp(12),

            spacing=dp(5),

            size_hint_y=None,

            height=dp(160),

            **kwargs

        )


        self.status_label = Label(

            text=(
                "SYSTEM STATUS\n"
                "━━━━━━━━━━━━━━━━\n"
                "CORE       ONLINE\n"
                "MEMORY     ONLINE\n"
                "COMMAND    ONLINE\n"
                "VOICE      STANDBY"
            ),

            font_size=dp(11),

            color=HUD_CYAN,

            halign="left",

            valign="top"

        )


        self.status_label.bind(

            size=lambda obj, value:
            setattr(
                obj,
                "text_size",
                value
            )

        )


        self.add_widget(
            self.status_label
        )


# ============================================================
# SOHBET SATIRI
# ============================================================

class ChatBubble(Label):

    def __init__(

        self,
        text,
        role="jarvis",
        **kwargs

    ):

        super().__init__(

            text=text,

            size_hint_y=None,

            padding=(
                dp(14),
                dp(10)
            ),

            font_size=dp(14),

            color=HUD_WHITE,

            halign="left",

            valign="middle",

            **kwargs

        )


        self.role = role

        self.bind(

            width=self._update_text_size

        )


        self.bind(

            texture_size=self._update_height

        )


        self._update_color()


    def _update_text_size(
        self,
        *args
    ):

        self.text_size = (
            self.width - dp(28),
            None
        )


    def _update_height(
        self,
        *args
    ):

        self.height = (
            self.texture_size[1]
            + dp(20)
        )


    def _update_color(
        self
    ):

        if self.role == "user":

            self.color = (
                0.75,
                0.9,
                1,
                1
            )

        else:

            self.color = (
                0.65,
                1,
                0.95,
                1
            )


# ============================================================
# SOHBET PANELİ
# ============================================================

class ChatPanel(BoxLayout):

    def __init__(self, **kwargs):

        super().__init__(

            orientation="vertical",

            spacing=dp(8),

            padding=dp(8),

            **kwargs

        )


        self.scroll = ScrollView(

            do_scroll_x=False,

            bar_width=dp(3)

        )


        self.messages = GridLayout(

            cols=1,

            spacing=dp(7),

            size_hint_y=None,

            padding=(
                dp(5),
                dp(5)
            )

        )


        self.messages.bind(

            minimum_height=
            self.messages.setter(
                "height"
            )

        )


        self.scroll.add_widget(
            self.messages
        )


        self.add_widget(
            self.scroll
        )


    def add_message(

        self,
        text,
        role="jarvis"

    ):

        bubble = ChatBubble(

            text=text,

            role=role

        )


        self.messages.add_widget(
            bubble
        )


        Clock.schedule_once(

            lambda dt:
            setattr(
                self.scroll,
                "scroll_y",
                0
            ),

            0.05

        )


    def clear(self):

        self.messages.clear_widgets()


# ============================================================
# KOMUT ÇUBUĞU
# ============================================================

class CommandBar(BoxLayout):

    def __init__(
        self,
        submit_callback,
        **kwargs
    ):

        super().__init__(

            orientation="horizontal",

            spacing=dp(8),

            size_hint_y=None,

            height=dp(60),

            padding=(
                dp(8),
                dp(8)
            ),

            **kwargs

        )


        self.input = TextInput(

            hint_text=(
                "Jarvis'e bir komut ver..."
            ),

            multiline=False,

            font_size=dp(15),

            foreground_color=HUD_WHITE,

            background_color=(
                0.03,
                0.07,
                0.09,
                1
            ),

            cursor_color=HUD_CYAN,

            padding=(
                dp(14),
                dp(12)
            )

        )


        self.input.bind(

            on_text_validate=
            lambda instance:
            submit_callback(
                self.input.text
            )

        )


        self.add_widget(
            self.input
        )


        send = Button(

            text="GÖNDER",

            size_hint_x=None,

            width=dp(100),

            font_size=dp(13),

            background_normal="",

            background_color=(
                0.03,
                0.45,
                0.65,
                1
            ),

            color=HUD_WHITE

        )


        send.bind(

            on_release=
            lambda instance:
            submit_callback(
                self.input.text
            )

        )


        self.add_widget(
            send
        )


    def clear(self):

        self.input.text = ""


# ============================================================
# TITAN HUD
# ============================================================

class TitanHUD(FloatLayout):

    def __init__(
        self,
        core,
        **kwargs
    ):

        super().__init__(
            **kwargs
        )


        self.core = core


        # ----------------------------------------------------
        # ARKA PLAN
        # ----------------------------------------------------

        background = HUDBackground()

        self.add_widget(
            background
        )


        # ----------------------------------------------------
        # BAŞLIK
        # ----------------------------------------------------

        header = HUDHeader()

        header.pos_hint = {

            "top": 1,

        }

        self.add_widget(
            header
        )


        # ----------------------------------------------------
        # ARC REACTOR
        # ----------------------------------------------------

        self.reactor = ArcReactor(

            size_hint=(
                0.62,
                0.42
            ),

            pos_hint={

                "center_x": 0.5,

                "center_y": 0.68

            }

        )


        self.add_widget(
            self.reactor
        )


        # ----------------------------------------------------
        # REACTOR BAŞLIĞI
        # ----------------------------------------------------

        reactor_title = Label(

            text=(
                "T I T A N   C O R E"
            ),

            font_size=dp(13),

            color=HUD_CYAN,

            size_hint=(
                0.6,
                None
            ),

            height=dp(30),

            pos_hint={

                "center_x": 0.5,

                "center_y": 0.43

            }

        )


        self.add_widget(
            reactor_title
        )


        # ----------------------------------------------------
        # SOL SİSTEM PANELİ
        # ----------------------------------------------------

        self.system_panel = SystemPanel(

            size_hint=(
                0.34,
                None
            ),

            pos_hint={

                "x": 0.01,

                "center_y": 0.58

            }

        )


        self.add_widget(
            self.system_panel
        )


        # ----------------------------------------------------
        # SOHBET
        # ----------------------------------------------------

        self.chat_panel = ChatPanel(

            size_hint=(
                0.95,
                0.28
            ),

            pos_hint={

                "x": 0.025,

                "y": 0.095

            }

        )


        self.add_widget(
            self.chat_panel
        )


        # ----------------------------------------------------
        # KOMUT ÇUBUĞU
        # ----------------------------------------------------

        self.command_bar = CommandBar(

            self.submit_command,

            size_hint=(
                0.95,
                None
            ),

            pos_hint={

                "x": 0.025,

                "y": 0.015

            }

        )


        self.add_widget(
            self.command_bar
        )


        # ----------------------------------------------------
        # AÇILIŞ MESAJI
        # ----------------------------------------------------

        Clock.schedule_once(

            self.boot_sequence,

            0.3

        )


    # ========================================================
    # BOOT
    # ========================================================

    def boot_sequence(
        self,
        dt
    ):

        self.chat_panel.add_message(

            "JARVIS TITAN başlatılıyor...",

            "jarvis"

        )


        Clock.schedule_once(

            lambda dt:
            self.chat_panel.add_message(

                "TITAN CORE ........ ONLINE",

                "jarvis"

            ),

            0.4

        )


        Clock.schedule_once(

            lambda dt:
            self.chat_panel.add_message(

                "MEMORY ENGINE ..... ONLINE",

                "jarvis"

            ),

            0.8

        )


        Clock.schedule_once(

            lambda dt:
            self.chat_panel.add_message(

                "COMMAND ENGINE .... ONLINE",

                "jarvis"

            ),

            1.2

        )


        Clock.schedule_once(

            lambda dt:
            self.chat_panel.add_message(

                "Tüm ana sistemler hazır. "
                "Komutunu bekliyorum.",

                "jarvis"

            ),

            1.7

        )


    # ========================================================
    # KOMUT GÖNDER
    # ========================================================

    def submit_command(
        self,
        text
    ):

        text = TextTools.clean(
            text
        )


        if not text:

            return


        self.command_bar.clear()


        self.chat_panel.add_message(

            text,

            "user"

        )


        try:

            result = (
                self.command_engine
                .process(
                    text
                )
            )


            if result.text == "__CLEAR_CHAT__":

                self.chat_panel.clear()

                return


            self.chat_panel.add_message(

                result.text,

                "jarvis"

            )


            if result.speak:

                self.speak(
                    result.text
                )


        except Exception as error:

            Logger.error(

                "Command UI error: "

                + traceback.format_exc()

            )


            self.chat_panel.add_message(

                "Bir sistem hatası oluştu. "
                "Log dosyasını kontrol et.",

                "jarvis"

            )


    # ========================================================
    # SES KANCASI
    # ========================================================

    def speak(
        self,
        text
    ):

        # Bölüm 5'te gerçek TTS
        # motoruna bağlanacak.

        Logger.info(

            f"TTS REQUEST: {text}"

        )


# ============================================================
# JARVIS APPLICATION
# ============================================================

class JarvisTitanApp(App):

    title = JARVIS_NAME


    def build(self):

        Window.clearcolor = HUD_BG


        self.core = TitanCore()


        self.hud = TitanHUD(
            self.core
        )


        # ----------------------------------------------------
        # KOMUT MOTORUNU BAĞLA
        # ----------------------------------------------------

        self.hud.command_engine = (
            JarvisCommandEngine(
                self.core
            )
        )


        # ----------------------------------------------------
        # TIMER EVENT KANCASI
        # ----------------------------------------------------

        def external_event(
            message
        ):

            Clock.schedule_once(

                lambda dt:
                self.hud.chat_panel.add_message(

                    message,

                    "jarvis"

                )

            )


        self.core.on_external_event = (
            external_event
        )


        return self.hud


# ============================================================
# UYGULAMAYI BAŞLAT
# ============================================================

if __name__ == "__main__":

    JarvisTitanApp().run()# ============================================================
# JARVIS TITAN
# BÖLÜM 4 — ADVANCED REACTOR / HUD EFFECTS
# ============================================================

from kivy.graphics import (
    Color,
    Line,
    Ellipse,
    Rectangle
)
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget


# ============================================================
# GELİŞMİŞ REACTOR
# ============================================================

class AdvancedArcReactor(Widget):

    rotation = NumericProperty(0)

    secondary_rotation = NumericProperty(0)

    pulse = NumericProperty(0)

    scan_rotation = NumericProperty(0)

    energy = NumericProperty(100)


    def __init__(
        self,
        **kwargs
    ):

        super().__init__(
            **kwargs
        )

        Clock.schedule_interval(
            self.animate,
            1 / 60
        )

        self.bind(
            pos=self.redraw,
            size=self.redraw
        )


    # ========================================================
    # ANİMASYON
    # ========================================================

    def animate(
        self,
        dt
    ):

        self.rotation += (
            dt * 32
        )

        self.secondary_rotation -= (
            dt * 21
        )

        self.scan_rotation += (
            dt * 80
        )

        self.pulse += (
            dt * 3
        )


        if self.rotation >= 360:

            self.rotation -= 360


        if self.secondary_rotation <= -360:

            self.secondary_rotation += 360


        if self.scan_rotation >= 360:

            self.scan_rotation -= 360


        self.redraw()


    # ========================================================
    # ÇİZİM
    # ========================================================

    def redraw(
        self,
        *args
    ):

        self.canvas.clear()


        cx = (
            self.x
            + self.width / 2
        )

        cy = (
            self.y
            + self.height / 2
        )


        radius = min(

            self.width,

            self.height

        ) * 0.30


        with self.canvas:

            # ------------------------------------------------
            # DIŞ GLOW HALKASI
            # ------------------------------------------------

            for multiplier, alpha in [

                (2.15, 0.08),

                (1.95, 0.12),

                (1.78, 0.18),

            ]:

                Color(

                    0.02,

                    0.65,

                    1.0,

                    alpha

                )


                Line(

                    circle=(

                        cx,

                        cy,

                        radius * multiplier

                    ),

                    width=dp(2)

                )


            # ------------------------------------------------
            # DIŞ ÇERÇEVE
            # ------------------------------------------------

            Color(

                0.05,

                0.75,

                1.0,

                0.65

            )


            Line(

                circle=(

                    cx,

                    cy,

                    radius * 1.55

                ),

                width=dp(1.2)

            )


            # ------------------------------------------------
            # ANA HALKA
            # ------------------------------------------------

            Color(

                0.05,

                0.95,

                1.0,

                0.95

            )


            Line(

                circle=(

                    cx,

                    cy,

                    radius * 1.30

                ),

                width=dp(2.2)

            )


            # ------------------------------------------------
            # DÖNEN SEGMENT
            # ------------------------------------------------

            Color(

                0.15,

                0.65,

                1.0,

                0.9

            )


            Line(

                ellipse=(

                    cx - radius * 1.18,

                    cy - radius * 1.18,

                    radius * 2.36,

                    radius * 2.36,

                    self.rotation,

                    self.rotation + 85

                ),

                width=dp(4)

            )


            # ------------------------------------------------
            # TERS DÖNEN SEGMENT
            # ------------------------------------------------

            Color(

                0.0,

                0.9,

                1.0,

                0.75

            )


            Line(

                ellipse=(

                    cx - radius * 1.08,

                    cy - radius * 1.08,

                    radius * 2.16,

                    radius * 2.16,

                    self.secondary_rotation,

                    self.secondary_rotation + 55

                ),

                width=dp(2)

            )


            # ------------------------------------------------
            # SCAN SEGMENT
            # ------------------------------------------------

            Color(

                0.3,

                0.95,

                1.0,

                0.85

            )


            Line(

                ellipse=(

                    cx - radius * 1.43,

                    cy - radius * 1.43,

                    radius * 2.86,

                    radius * 2.86,

                    self.scan_rotation,

                    self.scan_rotation + 18

                ),

                width=dp(2)

            )


            # ------------------------------------------------
            # İÇ ÇEKİRDEK GLOW
            # ------------------------------------------------

            pulse_value = (

                0.55

                + (

                    math.sin(
                        self.pulse
                    ) * 0.20

                )

            )


            Color(

                0.0,

                0.65,

                1.0,

                pulse_value

            )


            Ellipse(

                pos=(

                    cx - radius * 0.68,

                    cy - radius * 0.68

                ),

                size=(

                    radius * 1.36,

                    radius * 1.36

                )

            )


            # ------------------------------------------------
            # ÇEKİRDEK
            # ------------------------------------------------

            Color(

                0.25,

                0.92,

                1.0,

                1

            )


            Ellipse(

                pos=(

                    cx - radius * 0.42,

                    cy - radius * 0.42

                ),

                size=(

                    radius * 0.84,

                    radius * 0.84

                )

            )


            # ------------------------------------------------
            # BEYAZ MERKEZ
            # ------------------------------------------------

            Color(

                0.9,

                1.0,

                1.0,

                1

            )


            Ellipse(

                pos=(

                    cx - radius * 0.18,

                    cy - radius * 0.18

                ),

                size=(

                    radius * 0.36,

                    radius * 0.36

                )

            )


            # ------------------------------------------------
            # MERKEZ NOKTASI
            # ------------------------------------------------

            Color(

                1,

                1,

                1,

                1

            )


            Ellipse(

                pos=(

                    cx - radius * 0.07,

                    cy - radius * 0.07

                ),

                size=(

                    radius * 0.14,

                    radius * 0.14

                )

            )


# ============================================================
# RADAR / SCANNER
# ============================================================

class HUDScanner(Widget):

    angle = NumericProperty(0)


    def __init__(
        self,
        **kwargs
    ):

        super().__init__(
            **kwargs
        )

        Clock.schedule_interval(

            self.update_scanner,

            1 / 60

        )


        self.bind(

            pos=self.redraw,

            size=self.redraw

        )


    def update_scanner(
        self,
        dt
    ):

        self.angle += (
            dt * 45
        )


        if self.angle >= 360:

            self.angle -= 360


        self.redraw()


    def redraw(
        self,
        *args
    ):

        self.canvas.clear()


        cx = (
            self.x
            + self.width / 2
        )

        cy = (
            self.y
            + self.height / 2
        )


        radius = min(

            self.width,

            self.height

        ) * 0.40


        with self.canvas:

            # ------------------------------------------------
            # RADAR HALKALARI
            # ------------------------------------------------

            for multiplier in [

                0.65,

                0.82,

                1.0,

            ]:

                Color(

                    0.05,

                    0.65,

                    0.9,

                    0.18

                )


                Line(

                    circle=(

                        cx,

                        cy,

                        radius * multiplier

                    ),

                    width=dp(1)

                )


            # ------------------------------------------------
            # RADAR TARAMA
            # ------------------------------------------------

            Color(

                0.1,

                0.85,

                1.0,

                0.45

            )


            Line(

                ellipse=(

                    cx - radius,

                    cy - radius,

                    radius * 2,

                    radius * 2,

                    self.angle,

                    self.angle + 25

                ),

                width=dp(2)

            )


# ============================================================
# ENERJİ GÖSTERGESİ
# ============================================================

class EnergyIndicator(Widget):

    energy = NumericProperty(100)


    def __init__(
        self,
        **kwargs
    ):

        super().__init__(
            **kwargs
        )

        self.bind(

            pos=self.redraw,

            size=self.redraw,

            energy=self.redraw

        )


    def redraw(
        self,
        *args
    ):

        self.canvas.clear()


        with self.canvas:

            # ------------------------------------------------
            # ARKA BAR
            # ------------------------------------------------

            Color(

                0.04,

                0.10,

                0.13,

                1

            )


            Rectangle(

                pos=self.pos,

                size=self.size

            )


            # ------------------------------------------------
            # ENERJİ BAR
            # ------------------------------------------------

            percentage = max(

                0,

                min(

                    100,

                    self.energy

                )

            ) / 100


            Color(

                0.05,

                0.8,

                1.0,

                0.85

            )


            Rectangle(

                pos=self.pos,

                size=(

                    self.width
                    * percentage,

                    self.height

                )

            )


# ============================================================
# HUD DATA STREAM
# ============================================================

class DataStream(Label):

    elapsed = NumericProperty(0)


    def __init__(
        self,
        **kwargs
    ):

        super().__init__(

            text="INITIALIZING...",

            font_size=dp(10),

            color=(

                0.2,

                0.75,

                0.9,

                0.65

            ),

            halign="left",

            valign="middle",

            **kwargs

        )


        Clock.schedule_interval(

            self.update_stream,

            0.15

        )


    def update_stream(
        self,
        dt
    ):

        self.elapsed += dt


        symbols = [

            "01",

            "10",

            "A7",

            "F2",

            "C9",

            "D4",

            "8B",

            "E1",

            "5A",

            "73",

        ]


        chunks = [

            random.choice(
                symbols
            )

            for _ in range(7)

        ]


        self.text = (

            "DATA // "

            + " ".join(chunks)

        )


# ============================================================
# HUD GRID
# ============================================================

class HUDGrid(Widget):

    def __init__(
        self,
        **kwargs
    ):

        super().__init__(
            **kwargs
        )

        self.bind(

            pos=self.redraw,

            size=self.redraw

        )


    def redraw(
        self,
        *args
    ):

        self.canvas.clear()


        with self.canvas:

            Color(

                0.04,

                0.30,

                0.40,

                0.13

            )


            spacing = dp(35)


            x = self.x

            while x <= self.right:

                Line(

                    points=[

                        x,

                        self.y,

                        x,

                        self.top

                    ],

                    width=dp(0.5)

                )

                x += spacing


            y = self.y

            while y <= self.top:

                Line(

                    points=[

                        self.x,

                        y,

                        self.right,

                        y

                    ],

                    width=dp(0.5)

                )

                y += spacing


# ============================================================
# TITAN TELEMETRY
# ============================================================

class TitanTelemetry(BoxLayout):

    def __init__(
        self,
        core,
        **kwargs
    ):

        super().__init__(

            orientation="vertical",

            padding=dp(8),

            spacing=dp(2),

            size_hint_y=None,

            height=dp(100),

            **kwargs

        )


        self.core = core


        self.label = Label(

            text=self.generate(),

            font_size=dp(9),

            color=(

                0.35,

                0.85,

                1,

                0.7

            ),

            halign="left",

            valign="top"

        )


        self.label.bind(

            size=lambda obj, value:

            setattr(

                obj,

                "text_size",

                value

            )

        )


        self.add_widget(

            self.label

        )


        Clock.schedule_interval(

            self.update,

            0.5

        )


    def generate(
        self
    ):

        try:

            status = (
                self.core.status()
            )

            return (

                "TITAN TELEMETRY\n"

                "━━━━━━━━━━━━━━━━\n"

                f"CORE     {status['core']}\n"

                f"MEMORY   {status['memory']}\n"

                f"COMMAND  {status['command']}\n"

                f"UPTIME   {status['uptime']}"

            )

        except Exception:

            return (

                "TITAN TELEMETRY\n"

                "SYSTEM INITIALIZING..."

            )


    def update(
        self,
        dt
    ):

        self.label.text = (
            self.generate()
        )


# ============================================================
# GÜVENLİ IMPORT KONTROLÜ
# ============================================================

try:

    dp

except NameError:

    from kivy.metrics import dp# ============================================================
# JARVIS TITAN
# BÖLÜM 5 — VOICE ENGINE / TTS / SPEECH PIPELINE
# ============================================================

import queue
import threading
import time
import traceback


# ============================================================
# SES MOTORU
# ============================================================

class VoiceEngine:

    def __init__(self):

        self.enabled = True

        self.speaking = False

        self.initialized = False

        self.engine = None

        self.queue = queue.Queue()

        self.worker = None

        self.stop_worker = False

        self.lock = threading.Lock()

        self.rate = 150

        self.volume = 1.0

        self.language = "tr"


        Logger.info(
            "Voice Engine başlatılıyor..."
        )


        self._initialize()


    # ========================================================
    # MOTORU BAŞLAT
    # ========================================================

    def _initialize(self):

        try:

            import pyttsx3

            self.engine = (
                pyttsx3.init()
            )


            try:

                self.engine.setProperty(
                    "rate",
                    self.rate
                )

            except Exception:
                pass


            try:

                self.engine.setProperty(
                    "volume",
                    self.volume
                )

            except Exception:
                pass


            self._find_turkish_voice()


            self.initialized = True


            self.worker = threading.Thread(

                target=self._worker_loop,

                daemon=True

            )


            self.worker.start()


            Logger.info(
                "Voice Engine: ONLINE"
            )


        except Exception as error:

            self.initialized = False

            Logger.warning(

                "pyttsx3 kullanılamıyor: "

                + str(error)

            )


            Logger.info(
                "Voice Engine fallback modunda."
            )


    # ========================================================
    # TÜRKÇE SES BUL
    # ========================================================

    def _find_turkish_voice(self):

        if not self.engine:

            return


        try:

            voices = (
                self.engine
                .getProperty(
                    "voices"
                )
            )


            for voice in voices:

                voice_id = str(
                    getattr(
                        voice,
                        "id",
                        ""
                    )
                ).lower()


                voice_name = str(
                    getattr(
                        voice,
                        "name",
                        ""
                    )
                ).lower()


                languages = str(
                    getattr(
                        voice,
                        "languages",
                        ""
                    )
                ).lower()


                combined = (

                    voice_id
                    + " "
                    + voice_name
                    + " "
                    + languages

                )


                if (

                    "turkish"
                    in combined

                    or

                    "turk"
                    in combined

                    or

                    "tr-tr"
                    in combined

                    or

                    "tr_" 
                    in combined

                ):

                    try:

                        self.engine.setProperty(

                            "voice",

                            voice.id

                        )

                        Logger.info(

                            "Türkçe ses bulundu."

                        )

                        return

                    except Exception:

                        pass


            Logger.warning(

                "Türkçe TTS sesi bulunamadı."

            )


        except Exception as error:

            Logger.warning(

                "Voice scan error: "

                + str(error)

            )


    # ========================================================
    # KONUŞMA KUYRUĞUNA EKLE
    # ========================================================

    def speak(
        self,
        text,
        priority=False
    ):

        if not self.enabled:

            return False


        text = TextTools.clean(
            text
        )


        if not text:

            return False


        # Çok uzun metinleri kontrol et

        text = TextTools.truncate(

            text,

            3000

        )


        try:

            if priority:

                self._clear_queue()


            self.queue.put(
                text
            )


            return True


        except Exception as error:

            Logger.error(

                "TTS queue error: "

                + str(error)

            )

            return False


    # ========================================================
    # KUYRUĞU TEMİZLE
    # ========================================================

    def _clear_queue(self):

        try:

            while True:

                self.queue.get_nowait()

                self.queue.task_done()

        except queue.Empty:

            pass


    # ========================================================
    # SES THREAD
    # ========================================================

    def _worker_loop(self):

        while not self.stop_worker:

            try:

                text = self.queue.get(
                    timeout=0.2
                )

            except queue.Empty:

                continue


            try:

                self._speak_blocking(
                    text
                )

            except Exception:

                Logger.error(

                    "TTS worker error:\n"

                    + traceback.format_exc()

                )

            finally:

                try:

                    self.queue.task_done()

                except Exception:

                    pass


    # ========================================================
    # GERÇEK KONUŞMA
    # ========================================================

    def _speak_blocking(
        self,
        text
    ):

        if not self.initialized:

            Logger.info(

                "TTS OFFLINE: "

                + text

            )

            return


        with self.lock:

            self.speaking = True


            try:

                self.engine.say(
                    text
                )

                self.engine.runAndWait()


            except Exception as error:

                Logger.error(

                    "TTS engine error: "

                    + str(error)

                )

            finally:

                self.speaking = False


    # ========================================================
    # HIZ AYARI
    # ========================================================

    def set_rate(
        self,
        rate
    ):

        try:

            rate = int(rate)

        except Exception:

            return False


        rate = max(
            70,
            min(
                250,
                rate
            )
        )


        self.rate = rate


        if self.engine:

            try:

                self.engine.setProperty(
                    "rate",
                    rate
                )

            except Exception:

                pass


        return True


    # ========================================================
    # SES SEVİYESİ
    # ========================================================

    def set_volume(
        self,
        volume
    ):

        try:

            volume = float(
                volume
            )

        except Exception:

            return False


        volume = max(
            0.0,
            min(
                1.0,
                volume
            )
        )


        self.volume = volume


        if self.engine:

            try:

                self.engine.setProperty(

                    "volume",

                    volume

                )

            except Exception:

                pass


        return True


    # ========================================================
    # AKTİF / PASİF
    # ========================================================

    def enable(
        self
    ):

        self.enabled = True

        return True


    def disable(
        self
    ):

        self.enabled = False

        self._clear_queue()

        return True


    # ========================================================
    # DURUM
    # ========================================================

    def status(
        self
    ):

        return {

            "enabled":
                self.enabled,

            "initialized":
                self.initialized,

            "speaking":
                self.speaking,

            "queued":
                self.queue.qsize(),

            "language":
                self.language,

            "rate":
                self.rate,

            "volume":
                self.volume,

        }


    # ========================================================
    # KAPAT
    # ========================================================

    def shutdown(
        self
    ):

        self.stop_worker = True

        self._clear_queue()


        if self.engine:

            try:

                self.engine.stop()

            except Exception:

                pass


# ============================================================
# KONUŞMA METNİ TEMİZLEYİCİ
# ============================================================

class SpeechTextProcessor:

    @staticmethod
    def prepare(
        text
    ):

        text = str(text)


        # UI sembollerini seslendirmesin

        replacements = {

            "━━━━━━━━━━━━━━━━":
                ".",

            "━━━━━━━━":
                ".",

            "●":
                "",

            "•":
                "",

            "→":
                "",

            "→":
                "",

            "ONLINE":
                "çevrimiçi",

            "OFFLINE":
                "çevrimdışı",

        }


        for old, new in replacements.items():

            text = text.replace(
                old,
                new
            )


        # Fazla boşluklar

        text = " ".join(
            text.split()
        )


        return text.strip()


# ============================================================
# GELİŞMİŞ VOICE CONTROLLER
# ============================================================

class VoiceController:

    def __init__(
        self,
        core
    ):

        self.core = core

        self.voice = VoiceEngine()

        self.enabled = True

        Logger.info(
            "Voice Controller: ONLINE"
        )


    # ========================================================
    # KONUŞ
    # ========================================================

    def say(
        self,
        text,
        priority=False
    ):

        if not self.enabled:

            return False


        prepared = (
            SpeechTextProcessor
            .prepare(
                text
            )
        )


        return self.voice.speak(

            prepared,

            priority=priority

        )


    # ========================================================
    # SESSİZ MOD
    # ========================================================

    def mute(
        self
    ):

        self.enabled = False

        self.voice.disable()

        return True


    # ========================================================
    # SESİ AÇ
    # ========================================================

    def unmute(
        self
    ):

        self.enabled = True

        self.voice.enable()

        return True


    # ========================================================
    # DURUM
    # ========================================================

    def status(
        self
    ):

        data = self.voice.status()

        data["controller_enabled"] = (
            self.enabled
        )

        return data


    # ========================================================
    # KAPAT
    # ========================================================

    def shutdown(
        self
    ):

        self.voice.shutdown()


# ============================================================
# MİKROFON YÖNETİCİSİ
# ============================================================

class MicrophoneEngine:

    def __init__(
        self,
        result_callback=None
    ):

        self.result_callback = (
            result_callback
        )

        self.active = False

        self.available = False

        self.recognizer = None

        self.microphone = None

        self.thread = None


        self._initialize()


    # ========================================================
    # MİKROFON BAŞLAT
    # ========================================================

    def _initialize(self):

        try:

            import speech_recognition as sr

            self.recognizer = (
                sr.Recognizer()
            )

            self.microphone = (
                sr.Microphone()
            )

            self.available = True


            Logger.info(
                "Microphone Engine: ONLINE"
            )


        except Exception as error:

            self.available = False

            Logger.warning(

                "Microphone kullanılamıyor: "

                + str(error)

            )


    # ========================================================
    # DİNLE
    # ========================================================

    def listen_once(
        self
    ):

        if not self.available:

            return None


        try:

            self.active = True


            with self.microphone as source:

                self.recognizer.adjust_for_ambient_noise(

                    source,

                    duration=0.4

                )


                audio = self.recognizer.listen(

                    source,

                    timeout=5,

                    phrase_time_limit=12

                )


            text = (
                self.recognizer
                .recognize_google(

                    audio,

                    language="tr-TR"

                )
            )


            self.active = False


            return text


        except Exception as error:

            self.active = False

            Logger.warning(

                "Speech recognition error: "

                + str(error)

            )

            return None


    # ========================================================
    # ASENKRON DİNLE
    # ========================================================

    def listen_async(
        self
    ):

        if self.active:

            return False


        if not self.available:

            return False


        self.thread = threading.Thread(

            target=self._listen_worker,

            daemon=True

        )


        self.thread.start()


        return True


    def _listen_worker(
        self
    ):

        result = (
            self.listen_once()
        )


        if (

            result

            and

            self.result_callback

        ):

            try:

                self.result_callback(
                    result
                )

            except Exception as error:

                Logger.error(

                    "Microphone callback error: "

                    + str(error)

                )


    # ========================================================
    # DURUM
    # ========================================================

    def status(
        self
    ):

        return {

            "available":
                self.available,

            "active":
                self.active,

        }


# ============================================================
# VOICE COMMAND HANDLER
# ============================================================

class VoiceCommandHandler:

    def __init__(
        self,
        command_engine,
        voice_controller
    ):

        self.command_engine = (
            command_engine
        )

        self.voice_controller = (
            voice_controller
        )


    # ========================================================
    # SESLİ KOMUTU İŞLE
    # ========================================================

    def process_voice(
        self,
        text
    ):

        if not text:

            return None


        Logger.info(

            f"VOICE COMMAND: {text}"

        )


        result = (
            self.command_engine
            .process(
                text
            )
        )


        if result.speak:

            self.voice_controller.say(

                result.text

            )


        return result


# ============================================================
# VOICE SYSTEM
# ============================================================

class TitanVoiceSystem:

    def __init__(
        self,
        core,
        command_engine
    ):

        self.core = core

        self.command_engine = (
            command_engine
        )


        self.controller = (
            VoiceController(
                core
            )
        )


        self.microphone = (
            MicrophoneEngine(
                self.on_voice_result
            )
        )


        self.handler = (
            VoiceCommandHandler(

                command_engine,

                self.controller

            )
        )


        Logger.info(
            "Titan Voice System: ONLINE"
        )


    # ========================================================
    # SESLİ SONUÇ
    # ========================================================

    def on_voice_result(
        self,
        text
    ):

        try:

            self.handler.process_voice(
                text
            )

        except Exception:

            Logger.error(

                "Voice processing error:\n"

                + traceback.format_exc()

            )


    # ========================================================
    # DİNLEMEYİ BAŞLAT
    # ========================================================

    def listen(
        self
    ):

        return (
            self.microphone
            .listen_async()
        )


    # ========================================================
    # KONUŞ
    # ========================================================

    def speak(
        self,
        text
    ):

        return (
            self.controller
            .say(
                text
            )
        )


    # ========================================================
    # DURUM
    # ========================================================

    def status(
        self
    ):

        return {

            "voice":
                self.controller.status(),

            "microphone":
                self.microphone.status(),

        }


    # ========================================================
    # KAPAT
    # ========================================================

    def shutdown(
        self
    ):

        self.controller.shutdown()# ============================================================
# JARVIS TITAN
# BÖLÜM 6 — AI ENGINE / API ABSTRACTION LAYER
# ============================================================

import os
import json
import time
import threading
import traceback
from urllib import request
from urllib.error import URLError, HTTPError


# ============================================================
# AI DURUM SİSTEMİ
# ============================================================

class AIState:

    OFFLINE = "OFFLINE"

    CONNECTING = "CONNECTING"

    ONLINE = "ONLINE"

    THINKING = "THINKING"

    ERROR = "ERROR"


# ============================================================
# AI CEVAP NESNESİ
# ============================================================

class AIResponse:

    def __init__(
        self,
        text="",
        success=False,
        provider="local",
        error=None,
        latency=0.0
    ):

        self.text = text

        self.success = success

        self.provider = provider

        self.error = error

        self.latency = latency


    def to_dict(self):

        return {

            "text":
                self.text,

            "success":
                self.success,

            "provider":
                self.provider,

            "error":
                self.error,

            "latency":
                self.latency

        }


# ============================================================
# AI MESAJI
# ============================================================

class AIMessage:

    def __init__(
        self,
        role,
        content
    ):

        self.role = role

        self.content = content


    def to_dict(self):

        return {

            "role":
                self.role,

            "content":
                self.content

        }


# ============================================================
# AI HAFIZA KONTROLÜ
# ============================================================

class ConversationMemory:

    def __init__(
        self,
        max_messages=20
    ):

        self.max_messages = (
            max_messages
        )

        self.messages = []

        self.lock = threading.Lock()


    # ========================================================
    # MESAJ EKLE
    # ========================================================

    def add(
        self,
        role,
        content
    ):

        content = TextTools.clean(
            content
        )


        if not content:

            return


        with self.lock:

            self.messages.append(

                AIMessage(

                    role,

                    content

                )

            )


            # Hafızayı sınırla

            if len(self.messages) > (
                self.max_messages
            ):

                self.messages = (
                    self.messages[
                        -self.max_messages:
                    ]
                )


    # ========================================================
    # GEÇMİŞİ AL
    # ========================================================

    def get(
        self
    ):

        with self.lock:

            return [

                message.to_dict()

                for message
                in self.messages

            ]


    # ========================================================
    # TEMİZLE
    # ========================================================

    def clear(
        self
    ):

        with self.lock:

            self.messages.clear()


    # ========================================================
    # SON MESAJ
    # ========================================================

    def last(
        self
    ):

        with self.lock:

            if not self.messages:

                return None


            return (
                self.messages[-1]
                .content
            )


# ============================================================
# PROVIDER TABAN SINIFI
# ============================================================

class AIProvider:

    name = "base"


    def is_available(
        self
    ):

        return False


    def generate(
        self,
        messages,
        system_prompt=""
    ):

        raise NotImplementedError


    def shutdown(
        self
    ):

        pass


# ============================================================
# LOCAL FALLBACK AI
# ============================================================

class LocalAIProvider(AIProvider):

    name = "local"


    def __init__(
        self,
        core=None
    ):

        self.core = core


    def is_available(
        self
    ):

        return True


    def generate(
        self,
        messages,
        system_prompt=""
    ):

        if not messages:

            return AIResponse(

                text=(
                    "Hazırım. "
                    "Komutunu bekliyorum."
                ),

                success=True,

                provider=self.name

            )


        latest = messages[-1]

        if isinstance(
            latest,
            dict
        ):

            text = latest.get(
                "content",
                ""
            )

        else:

            text = latest.content


        text_lower = text.lower()


        # ----------------------------------------------------
        # BASİT YEREL CEVAPLAR
        # ----------------------------------------------------

        if any(

            word in text_lower

            for word in [

                "merhaba",

                "selam",

                "hey jarvis",

                "hello"

            ]

        ):

            answer = (
                "Merhaba. "
                "JARVIS TITAN çevrimiçi."
            )


        elif (

            "nasılsın"
            in text_lower

            or

            "nasilsin"
            in text_lower

        ):

            answer = (
                "Sistemlerim normal "
                "çalışıyor. Hazırım."
            )


        elif (

            "kimsin"
            in text_lower

            or

            "sen kimsin"
            in text_lower

        ):

            answer = (
                "Ben JARVIS TITAN. "
                "Komutlarını işlemek, "
                "sana yardımcı olmak ve "
                "sistem durumunu yönetmek "
                "üzere tasarlanmış yapay "
                "zeka asistanınım."
            )


        elif (

            "yardım"
            in text_lower

            or

            "help"
            in text_lower

        ):

            answer = (
                "Komut, soru veya görev "
                "verebilirsin. Sistem "
                "durumu, notlar, zaman, "
                "hafıza ve diğer modüller "
                "üzerinden işlem yapabilirim."
            )


        else:

            answer = (
                "Şu anda yerel AI "
                "modundayım. Harici AI "
                "sağlayıcısı bağlandığında "
                "daha gelişmiş cevaplar "
                "üretebilirim."
            )


        return AIResponse(

            text=answer,

            success=True,

            provider=self.name

        )


# ============================================================
# GENERIC HTTP AI PROVIDER
# ============================================================

class HTTPAIProvider(AIProvider):

    name = "http"


    def __init__(

        self,

        endpoint,

        api_key=None,

        timeout=30

    ):

        self.endpoint = endpoint

        self.api_key = api_key

        self.timeout = timeout


    def is_available(
        self
    ):

        return bool(
            self.endpoint
        )


    # ========================================================
    # REQUEST
    # ========================================================

    def generate(

        self,

        messages,

        system_prompt=""

    ):

        if not self.endpoint:

            return AIResponse(

                success=False,

                provider=self.name,

                error="Endpoint belirtilmedi."

            )


        payload = {

            "messages": [

                message.to_dict()

                if hasattr(
                    message,
                    "to_dict"
                )

                else message

                for message
                in messages

            ],

            "system":

                system_prompt

        }


        data = json.dumps(
            payload
        ).encode(
            "utf-8"
        )


        headers = {

            "Content-Type":
                "application/json",

            "Accept":
                "application/json"

        }


        if self.api_key:

            headers[
                "Authorization"
            ] = (
                "Bearer "
                + self.api_key
            )


        req = request.Request(

            self.endpoint,

            data=data,

            headers=headers,

            method="POST"

        )


        started = time.time()


        try:

            with request.urlopen(

                req,

                timeout=self.timeout

            ) as response:

                raw = response.read().decode(
                    "utf-8"
                )


            latency = (
                time.time()
                - started
            )


            result = json.loads(
                raw
            )


            # ------------------------------------------------
            # FARKLI API FORMATLARINI DESTEKLE
            # ------------------------------------------------

            text = ""


            if isinstance(
                result,
                dict
            ):

                text = result.get(
                    "text",
                    ""
                )


                if not text:

                    text = result.get(
                        "response",
                        ""
                    )


                if not text:

                    text = result.get(
                        "content",
                        ""
                    )


                if not text:

                    choices = result.get(
                        "choices"
                    )


                    if choices:

                        first = choices[0]


                        if isinstance(
                            first,
                            dict
                        ):

                            message = (
                                first.get(
                                    "message",
                                    {}
                                )
                            )


                            if isinstance(
                                message,
                                dict
                            ):

                                text = (
                                    message.get(
                                        "content",
                                        ""
                                    )
                                )


            if not text:

                return AIResponse(

                    success=False,

                    provider=self.name,

                    error=(
                        "API boş cevap döndürdü."
                    ),

                    latency=latency

                )


            return AIResponse(

                text=str(text),

                success=True,

                provider=self.name,

                latency=latency

            )


        except HTTPError as error:

            return AIResponse(

                success=False,

                provider=self.name,

                error=(

                    f"HTTP {error.code}: "

                    f"{error.reason}"

                )

            )


        except URLError as error:

            return AIResponse(

                success=False,

                provider=self.name,

                error=(

                    "Bağlantı hatası: "

                    + str(error.reason)

                )

            )


        except Exception as error:

            return AIResponse(

                success=False,

                provider=self.name,

                error=str(error)

            )


# ============================================================
# AI ROUTER
# ============================================================

class AIRouter:

    def __init__(
        self,
        core=None
    ):

        self.core = core

        self.providers = []

        self.active_provider = None

        self.state = AIState.OFFLINE

        self.lock = threading.Lock()


    # ========================================================
    # PROVIDER EKLE
    # ========================================================

    def register(
        self,
        provider
    ):

        if provider is None:

            return False


        self.providers.append(
            provider
        )


        if (

            self.active_provider
            is None

            and

            provider.is_available()

        ):

            self.active_provider = (
                provider
            )

            self.state = (
                AIState.ONLINE
            )


        Logger.info(

            "AI provider registered: "

            + provider.name

        )


        return True


    # ========================================================
    # PROVIDER SEÇ
    # ========================================================

    def select(
        self,
        name
    ):

        for provider in self.providers:

            if (

                provider.name
                == name

                and

                provider.is_available()

            ):

                self.active_provider = (
                    provider
                )

                self.state = (
                    AIState.ONLINE
                )

                return True


        return False


    # ========================================================
    # CEVAP ÜRET
    # ========================================================

    def generate(

        self,

        messages,

        system_prompt=""

    ):

        self.state = (
            AIState.THINKING
        )


        # ----------------------------------------------------
        # AKTİF PROVIDER
        # ----------------------------------------------------

        if self.active_provider:

            result = (
                self.active_provider
                .generate(

                    messages,

                    system_prompt

                )
            )


            if result.success:

                self.state = (
                    AIState.ONLINE
                )

                return result


        # ----------------------------------------------------
        # FALLBACK PROVIDER
        # ----------------------------------------------------

        for provider in self.providers:

            if provider is (
                self.active_provider
            ):

                continue


            if not provider.is_available():

                continue


            try:

                result = (
                    provider.generate(

                        messages,

                        system_prompt

                    )
                )


                if result.success:

                    self.active_provider = (
                        provider
                    )

                    self.state = (
                        AIState.ONLINE
                    )

                    return result


            except Exception:

                continue


        self.state = (
            AIState.ERROR
        )


        return AIResponse(

            success=False,

            provider="router",

            error=(
                "Kullanılabilir AI "
                "sağlayıcısı bulunamadı."
            )

        )


    # ========================================================
    # DURUM
    # ========================================================

    def status(
        self
    ):

        return {

            "state":
                self.state,

            "active_provider":

                (

                    self.active_provider.name

                    if self.active_provider

                    else None

                ),

            "providers":

                [

                    provider.name

                    for provider
                    in self.providers

                ]

        }


# ============================================================
# JARVIS AI ENGINE
# ============================================================

class JarvisAIEngine:

    def __init__(
        self,
        core
    ):

        self.core = core

        self.memory = (
            ConversationMemory(
                max_messages=30
            )
        )


        self.router = (
            AIRouter(
                core
            )
        )


        self.system_prompt = (

            "Sen JARVIS TITAN isimli "
            "bir yapay zeka asistanısın. "

            "Türkçe konuş. "

            "Cevaplarını anlaşılır, "
            "doğal ve yardımcı şekilde "
            "ver. "

            "Gereksiz yere uzun konuşma. "

            "Kullanıcı bir görev istediğinde "
            "önce görevin ne olduğunu anla. "

            "Bilmediğin bir şeyi biliyormuş "
            "gibi söyleme. "

            "Güvenlik açısından uygun "
            "olmayan işlemleri gerçekleştirme."
        )


        # ----------------------------------------------------
        # LOCAL PROVIDER
        # ----------------------------------------------------

        self.local = (
            LocalAIProvider(
                core
            )
        )


        self.router.register(
            self.local
        )


        # ----------------------------------------------------
        # HARİCİ API
        # ----------------------------------------------------

        endpoint = os.getenv(
            "JARVIS_API_URL",
            ""
        )


        api_key = os.getenv(
            "JARVIS_API_KEY",
            ""
        )


        if endpoint:

            self.remote = (
                HTTPAIProvider(

                    endpoint=endpoint,

                    api_key=api_key,

                    timeout=45

                )
            )


            self.router.register(
                self.remote
            )

        else:

            self.remote = None


        Logger.info(
            "Jarvis AI Engine: ONLINE"
        )


    # ========================================================
    # KULLANICI MESAJI
    # ========================================================

    def chat(
        self,
        text
    ):

        text = TextTools.clean(
            text
        )


        if not text:

            return AIResponse(

                text="",

                success=False,

                provider="engine",

                error="Boş mesaj."

            )


        self.memory.add(

            "user",

            text

        )


        history = (
            self.memory.get()
        )


        result = (
            self.router.generate(

                history,

                self.system_prompt

            )
        )


        if result.success:

            self.memory.add(

                "assistant",

                result.text

            )


        else:

            # Son kullanıcı mesajını
            # hafızadan koru ama hata
            # mesajını AI cevabı olarak
            # ekleme.

            Logger.warning(

                "AI generation failed: "

                + str(
                    result.error
                )

            )


        return result


    # ========================================================
    # HAFIZA TEMİZLE
    # ========================================================

    def clear_memory(
        self
    ):

        self.memory.clear()


    # ========================================================
    # PROVIDER DEĞİŞTİR
    # ========================================================

    def use_provider(
        self,
        name
    ):

        return self.router.select(
            name
        )


    # ========================================================
    # DURUM
    # ========================================================

    def status(
        self
    ):

        return {

            "router":
                self.router.status(),

            "memory_messages":
                len(
                    self.memory.messages
                ),

        }


# ============================================================
# ASENKRON AI İSTEĞİ
# ============================================================

class AsyncAIRequest:

    def __init__(
        self,
        engine,
        text,
        callback=None
    ):

        self.engine = engine

        self.text = text

        self.callback = callback

        self.thread = threading.Thread(

            target=self._run,

            daemon=True

        )


    def start(
        self
    ):

        self.thread.start()


    def _run(
        self
    ):

        try:

            result = (
                self.engine.chat(
                    self.text
                )
            )


            if self.callback:

                self.callback(
                    result
                )


        except Exception as error:

            Logger.error(

                "Async AI error:\n"

                + traceback.format_exc()

            )


            if self.callback:

                self.callback(

                    AIResponse(

                        success=False,

                        provider="async",

                        error=str(
                            error
                        )

                    )

                )


# ============================================================
# AI SYSTEM
# ============================================================

class TitanAISystem:

    def __init__(
        self,
        core
    ):

        self.core = core

        self.engine = (
            JarvisAIEngine(
                core
            )
        )


        Logger.info(
            "Titan AI System: ONLINE"
        )


    # ========================================================
    # CHAT
    # ========================================================

    def chat(
        self,
        text
    ):

        return (
            self.engine
            .chat(
                text
            )
        )


    # ========================================================
    # ASENKRON CHAT
    # ========================================================

    def chat_async(
        self,
        text,
        callback=None
    ):

        request = (
            AsyncAIRequest(

                self.engine,

                text,

                callback

            )
        )


        request.start()


        return request


    # ========================================================
    # DURUM
    # ========================================================

    def status(
        self
    ):

        return (
            self.engine.status()
        )


    # ========================================================
    # HAFIZA TEMİZLE
    # ========================================================

    def clear_memory(
        self
    ):

        self.engine.clear_memory()


# ============================================================
# BÖLÜM 6 SONU
# ============================================================# ============================================================
# JARVIS TITAN
# BÖLÜM 7 — ANDROID SYSTEM INTEGRATION
# ============================================================

import os
import platform
import subprocess
import threading
import time
import traceback


# ============================================================
# PLATFORM DETECTOR
# ============================================================

class PlatformManager:

    @staticmethod
    def is_android():

        try:

            return (
                "ANDROID_ARGUMENT"
                in os.environ
            )

        except Exception:

            return False


    @staticmethod
    def name():

        if PlatformManager.is_android():

            return "Android"

        return platform.system()


    @staticmethod
    def architecture():

        try:

            return platform.machine()

        except Exception:

            return "Unknown"


    @staticmethod
    def version():

        try:

            return platform.version()

        except Exception:

            return "Unknown"


# ============================================================
# ANDROID BRIDGE
# ============================================================

class AndroidBridge:

    def __init__(self):

        self.available = False

        self.activity = None

        self.autoclass = None

        self._initialize()


    # ========================================================
    # BAŞLAT
    # ========================================================

    def _initialize(self):

        if not PlatformManager.is_android():

            Logger.info(
                "Android Bridge: DESKTOP MODE"
            )

            return


        try:

            from jnius import autoclass

            PythonActivity = autoclass(

                "org.kivy.android.PythonActivity"

            )


            self.autoclass = autoclass

            self.activity = (
                PythonActivity.mActivity
            )

            self.available = True


            Logger.info(
                "Android Bridge: ONLINE"
            )


        except Exception as error:

            Logger.warning(

                "Android Bridge unavailable: "

                + str(error)

            )


    # ========================================================
    # CLASS AL
    # ========================================================

    def get_class(
        self,
        name
    ):

        if not self.available:

            return None


        try:

            return self.autoclass(
                name
            )

        except Exception as error:

            Logger.warning(

                f"Android class error: {error}"

            )

            return None


# ============================================================
# ANDROID CİHAZ BİLGİLERİ
# ============================================================

class AndroidDeviceInfo:

    def __init__(
        self,
        bridge
    ):

        self.bridge = bridge


    # ========================================================
    # MODEL
    # ========================================================

    def model(self):

        try:

            Build = self.bridge.get_class(

                "android.os.Build"

            )


            if Build:

                return str(
                    Build.MODEL
                )


        except Exception:

            pass


        return platform.node()


    # ========================================================
    # ÜRETİCİ
    # ========================================================

    def manufacturer(self):

        try:

            Build = self.bridge.get_class(

                "android.os.Build"

            )


            if Build:

                return str(
                    Build.MANUFACTURER
                )


        except Exception:

            pass


        return "Unknown"


    # ========================================================
    # ANDROID SÜRÜMÜ
    # ========================================================

    def android_version(self):

        try:

            Build = self.bridge.get_class(

                "android.os.Build"

            )


            if Build:

                VERSION = (
                    self.bridge.get_class(

                        "android.os.Build$VERSION"

                    )
                )


                if VERSION:

                    return str(
                        VERSION.RELEASE
                    )


        except Exception:

            pass


        return "Unknown"


    # ========================================================
    # API LEVEL
    # ========================================================

    def api_level(self):

        try:

            VERSION = (
                self.bridge.get_class(

                    "android.os.Build$VERSION"

                )
            )


            if VERSION:

                return int(
                    VERSION.SDK_INT
                )


        except Exception:

            pass


        return 0


    # ========================================================
    # ÖZET
    # ========================================================

    def summary(self):

        return {

            "platform":
                "Android",

            "manufacturer":
                self.manufacturer(),

            "model":
                self.model(),

            "android":
                self.android_version(),

            "api":
                self.api_level(),

            "architecture":
                platform.machine()

        }


# ============================================================
# VIBRATION ENGINE
# ============================================================

class VibrationEngine:

    def __init__(
        self,
        bridge
    ):

        self.bridge = bridge

        self.vibrator = None

        self.available = False

        self._initialize()


    # ========================================================
    # BAŞLAT
    # ========================================================

    def _initialize(self):

        if not self.bridge.available:

            return


        try:

            Context = self.bridge.get_class(

                "android.content.Context"

            )


            if not Context:

                return


            self.vibrator = (
                self.bridge.activity
                .getSystemService(
                    Context.VIBRATOR_SERVICE
                )
            )


            self.available = (
                self.vibrator is not None
            )


        except Exception as error:

            Logger.warning(

                "Vibrator unavailable: "

                + str(error)

            )


    # ========================================================
    # TITRET
    # ========================================================

    def vibrate(
        self,
        duration=50
    ):

        if not self.available:

            return False


        try:

            # Android 8+

            if hasattr(
                self.vibrator,
                "vibrate"
            ):

                self.vibrator.vibrate(
                    int(duration)
                )

                return True


        except Exception as error:

            Logger.warning(

                "Vibration error: "

                + str(error)

            )


        return False


# ============================================================
# ANDROID POWER MANAGER
# ============================================================

class PowerManager:

    def __init__(
        self,
        bridge
    ):

        self.bridge = bridge


    def is_screen_on(self):

        if not self.bridge.available:

            return None


        try:

            Context = self.bridge.get_class(

                "android.content.Context"

            )


            manager = (
                self.bridge.activity
                .getSystemService(
                    Context.POWER_SERVICE
                )
            )


            if manager:

                return bool(
                    manager.isInteractive()
                )


        except Exception:

            pass


        return None


# ============================================================
# CLIPBOARD ENGINE
# ============================================================

class ClipboardEngine:

    def __init__(
        self,
        bridge
    ):

        self.bridge = bridge


    # ========================================================
    # YAZ
    # ========================================================

    def set_text(
        self,
        text
    ):

        try:

            from kivy.core.clipboard import Clipboard

            Clipboard.copy(
                str(text)
            )

            return True

        except Exception as error:

            Logger.warning(

                "Clipboard write error: "

                + str(error)

            )

            return False


    # ========================================================
    # OKU
    # ========================================================

    def get_text(
        self
    ):

        try:

            from kivy.core.clipboard import Clipboard

            return Clipboard.paste()

        except Exception as error:

            Logger.warning(

                "Clipboard read error: "

                + str(error)

            )

            return ""


# ============================================================
# DOSYA YÖNETİCİSİ
# ============================================================

class AndroidStorage:

    def __init__(self):

        self.base_dir = self._get_base_dir()

        self._ensure_directory()


    # ========================================================
    # DİZİN
    # ========================================================

    def _get_base_dir(
        self
    ):

        try:

            from kivy.app import App

            app = App.get_running_app()


            if app:

                return app.user_data_dir


        except Exception:

            pass


        return os.path.join(

            os.path.expanduser("~"),

            ".jarvis_titan"

        )


    # ========================================================
    # OLUŞTUR
    # ========================================================

    def _ensure_directory(
        self
    ):

        try:

            os.makedirs(

                self.base_dir,

                exist_ok=True

            )

        except Exception as error:

            Logger.warning(

                "Storage error: "

                + str(error)

            )


    # ========================================================
    # DOSYA YOLU
    # ========================================================

    def path(
        self,
        filename
    ):

        safe_name = os.path.basename(
            filename
        )


        return os.path.join(

            self.base_dir,

            safe_name

        )


    # ========================================================
    # YAZ
    # ========================================================

    def write(
        self,
        filename,
        content
    ):

        path = self.path(
            filename
        )


        try:

            with open(

                path,

                "w",

                encoding="utf-8"

            ) as file:

                file.write(
                    str(content)
                )


            return True


        except Exception as error:

            Logger.error(

                "Storage write error: "

                + str(error)

            )

            return False


    # ========================================================
    # OKU
    # ========================================================

    def read(
        self,
        filename
    ):

        path = self.path(
            filename
        )


        try:

            with open(

                path,

                "r",

                encoding="utf-8"

            ) as file:

                return file.read()


        except FileNotFoundError:

            return ""


        except Exception as error:

            Logger.error(

                "Storage read error: "

                + str(error)

            )

            return ""


    # ========================================================
    # SİL
    # ========================================================

    def delete(
        self,
        filename
    ):

        path = self.path(
            filename
        )


        try:

            if os.path.exists(
                path
            ):

                os.remove(
                    path
                )

                return True


        except Exception as error:

            Logger.error(

                "Storage delete error: "

                + str(error)

            )


        return False


# ============================================================
# SYSTEM INFORMATION
# ============================================================

class SystemInformation:

    def __init__(
        self,
        bridge
    ):

        self.bridge = bridge

        self.device = (
            AndroidDeviceInfo(
                bridge
            )
        )

        self.power = (
            PowerManager(
                bridge
            )
        )


    # ========================================================
    # CPU
    # ========================================================

    def cpu(self):

        try:

            return os.cpu_count()

        except Exception:

            return 0


    # ========================================================
    # RAM
    # ========================================================

    def memory(self):

        try:

            import psutil

            data = psutil.virtual_memory()


            return {

                "total":
                    data.total,

                "available":
                    data.available,

                "used":
                    data.used,

                "percent":
                    data.percent

            }


        except Exception:

            return {

                "total": 0,

                "available": 0,

                "used": 0,

                "percent": 0

            }


    # ========================================================
    # DISK
    # ========================================================

    def disk(self):

        try:

            import shutil

            total, used, free = (
                shutil.disk_usage(
                    os.path.expanduser(
                        "~"
                    )
                )
            )


            return {

                "total":
                    total,

                "used":
                    used,

                "free":
                    free

            }


        except Exception:

            return {

                "total": 0,

                "used": 0,

                "free": 0

            }


    # ========================================================
    # TAM BİLGİ
    # ========================================================

    def all(self):

        return {

            "device":
                self.device.summary(),

            "cpu":
                self.cpu(),

            "memory":
                self.memory(),

            "disk":
                self.disk(),

            "screen":
                self.power.is_screen_on()

        }


# ============================================================
# ANDROID SYSTEM CONTROLLER
# ============================================================

class AndroidSystemController:

    def __init__(self):

        self.bridge = (
            AndroidBridge()
        )


        self.device = (
            AndroidDeviceInfo(
                self.bridge
            )
        )


        self.vibration = (
            VibrationEngine(
                self.bridge
            )
        )


        self.clipboard = (
            ClipboardEngine(
                self.bridge
            )
        )


        self.storage = (
            AndroidStorage()
        )


        self.info = (
            SystemInformation(
                self.bridge
            )
        )


        Logger.info(
            "Android System Controller: ONLINE"
        )


    # ========================================================
    # TITREŞİM
    # ========================================================

    def feedback(
        self
    ):

        return self.vibration.vibrate(
            35
        )


    # ========================================================
    # CİHAZ
    # ========================================================

    def device_info(
        self
    ):

        return self.device.summary()


    # ========================================================
    # SİSTEM
    # ========================================================

    def system_info(
        self
    ):

        return self.info.all()


    # ========================================================
    # DURUM
    # ========================================================

    def status(
        self
    ):

        return {

            "android":
                self.bridge.available,

            "device":
                self.device.model(),

            "manufacturer":
                self.device.manufacturer(),

            "version":
                self.device.android_version(),

            "api":
                self.device.api_level(),

            "storage":
                self.storage.base_dir

        }


# ============================================================
# TITAN ANDROID SYSTEM
# ============================================================

class TitanAndroidSystem:

    def __init__(
        self,
        core
    ):

        self.core = core

        self.controller = (
            AndroidSystemController()
        )


        Logger.info(
            "Titan Android System: ONLINE"
        )


    # ========================================================
    # DURUM
    # ========================================================

    def status(
        self
    ):

        return (
            self.controller.status()
        )


    # ========================================================
    # CİHAZ BİLGİSİ
    # ========================================================

    def device_info(
        self
    ):

        return (
            self.controller.device_info()
        )


    # ========================================================
    # SİSTEM BİLGİSİ
    # ========================================================

    def system_info(
        self
    ):

        return (
            self.controller.system_info()
        )


    # ========================================================
    # GERİ BİLDİRİM
    # ========================================================

    def feedback(
        self
    ):

        return (
            self.controller.feedback()
        )


# ============================================================
# BÖLÜM 7 SONU
# ============================================================# ============================================================
# JARVIS TITAN
# BÖLÜM 8 — MEMORY / NOTES / TASKS / PERSONAL DATA ENGINE
# ============================================================

import os
import json
import time
import threading
import uuid
from datetime import datetime


# ============================================================
# MEMORY DATABASE
# ============================================================

class MemoryDatabase:

    def __init__(self, storage):

        self.storage = storage

        self.filename = "jarvis_memory.json"

        self.lock = threading.Lock()

        self.data = {

            "profile": {},

            "preferences": {},

            "facts": [],

            "conversations": [],

            "notes": [],

            "tasks": [],

            "events": []

        }

        self.load()


    # ========================================================
    # YÜKLE
    # ========================================================

    def load(self):

        with self.lock:

            raw = self.storage.read(
                self.filename
            )

            if not raw:

                self.save()

                return


            try:

                loaded = json.loads(
                    raw
                )


                if isinstance(
                    loaded,
                    dict
                ):

                    for key in self.data:

                        if key in loaded:

                            self.data[key] = (
                                loaded[key]
                            )


            except Exception as error:

                Logger.error(

                    "Memory load error: "

                    + str(error)

                )


    # ========================================================
    # KAYDET
    # ========================================================

    def save(self):

        try:

            with self.lock:

                content = json.dumps(

                    self.data,

                    ensure_ascii=False,

                    indent=2

                )


                self.storage.write(

                    self.filename,

                    content

                )


            return True


        except Exception as error:

            Logger.error(

                "Memory save error: "

                + str(error)

            )

            return False


    # ========================================================
    # PROFİL
    # ========================================================

    def set_profile(
        self,
        key,
        value
    ):

        with self.lock:

            self.data[
                "profile"
            ][key] = value


        self.save()

        return True


    def get_profile(
        self,
        key,
        default=None
    ):

        with self.lock:

            return (

                self.data[
                    "profile"
                ].get(
                    key,
                    default
                )

            )


    # ========================================================
    # TERCİH
    # ========================================================

    def set_preference(
        self,
        key,
        value
    ):

        with self.lock:

            self.data[
                "preferences"
            ][key] = value


        self.save()

        return True


    def get_preference(
        self,
        key,
        default=None
    ):

        with self.lock:

            return (

                self.data[
                    "preferences"
                ].get(
                    key,
                    default
                )

            )


    # ========================================================
    # BİLGİ EKLE
    # ========================================================

    def add_fact(
        self,
        text,
        category="general"
    ):

        item = {

            "id":
                str(uuid.uuid4()),

            "text":
                str(text),

            "category":
                category,

            "created":
                datetime.now().isoformat()

        }


        with self.lock:

            self.data[
                "facts"
            ].append(
                item
            )


        self.save()

        return item


    # ========================================================
    # BİLGİLERİ AL
    # ========================================================

    def get_facts(
        self,
        category=None
    ):

        with self.lock:

            facts = list(
                self.data[
                    "facts"
                ]
            )


        if category is None:

            return facts


        return [

            item

            for item in facts

            if item.get(
                "category"
            ) == category

        ]


    # ========================================================
    # KONUŞMA KAYDET
    # ========================================================

    def add_conversation(
        self,
        role,
        content
    ):

        item = {

            "id":
                str(uuid.uuid4()),

            "role":
                role,

            "content":
                str(content),

            "timestamp":
                datetime.now().isoformat()

        }


        with self.lock:

            self.data[
                "conversations"
            ].append(
                item
            )


            # Sonsuz büyümeyi engelle

            if len(
                self.data[
                    "conversations"
                ]
            ) > 500:

                self.data[
                    "conversations"
                ] = (

                    self.data[
                        "conversations"
                    ][-500:]

                )


        self.save()

        return item


    # ========================================================
    # KONUŞMA GEÇMİŞİ
    # ========================================================

    def get_conversations(
        self,
        limit=50
    ):

        with self.lock:

            return (

                self.data[
                    "conversations"
                ][-limit:]

            )


    # ========================================================
    # NOT EKLE
    # ========================================================

    def add_note(
        self,
        title,
        content
    ):

        item = {

            "id":
                str(uuid.uuid4()),

            "title":
                str(title),

            "content":
                str(content),

            "created":
                datetime.now().isoformat(),

            "updated":
                datetime.now().isoformat()

        }


        with self.lock:

            self.data[
                "notes"
            ].append(
                item
            )


        self.save()

        return item


    # ========================================================
    # NOTLARI GETİR
    # ========================================================

    def get_notes(self):

        with self.lock:

            return list(
                self.data[
                    "notes"
                ]
            )


    # ========================================================
    # NOT SİL
    # ========================================================

    def delete_note(
        self,
        note_id
    ):

        with self.lock:

            before = len(
                self.data[
                    "notes"
                ]
            )


            self.data[
                "notes"
            ] = [

                note

                for note
                in self.data[
                    "notes"
                ]

                if note.get(
                    "id"
                ) != note_id

            ]


            changed = (

                len(
                    self.data[
                        "notes"
                    ]
                )

                != before

            )


        if changed:

            self.save()


        return changed


    # ========================================================
    # GÖREV EKLE
    # ========================================================

    def add_task(
        self,
        title,
        description=""
    ):

        task = {

            "id":
                str(uuid.uuid4()),

            "title":
                str(title),

            "description":
                str(description),

            "completed":
                False,

            "created":
                datetime.now().isoformat(),

            "completed_at":
                None

        }


        with self.lock:

            self.data[
                "tasks"
            ].append(
                task
            )


        self.save()

        return task


    # ========================================================
    # GÖREVLER
    # ========================================================

    def get_tasks(
        self,
        active_only=False
    ):

        with self.lock:

            tasks = list(
                self.data[
                    "tasks"
                ]
            )


        if active_only:

            return [

                task

                for task in tasks

                if not task.get(
                    "completed",
                    False
                )

            ]


        return tasks


    # ========================================================
    # GÖREV TAMAMLA
    # ========================================================

    def complete_task(
        self,
        task_id
    ):

        changed = False


        with self.lock:

            for task in self.data[
                "tasks"
            ]:

                if task.get(
                    "id"
                ) == task_id:

                    task[
                        "completed"
                    ] = True


                    task[
                        "completed_at"
                    ] = (
                        datetime.now()
                        .isoformat()
                    )


                    changed = True

                    break


        if changed:

            self.save()


        return changed


    # ========================================================
    # VERİLERİ TEMİZLE
    # ========================================================

    def clear_all(
        self
    ):

        with self.lock:

            self.data = {

                "profile": {},

                "preferences": {},

                "facts": [],

                "conversations": [],

                "notes": [],

                "tasks": [],

                "events": []

            }


        self.save()

        return True


# ============================================================
# MEMORY SEARCH
# ============================================================

class MemorySearch:

    def __init__(
        self,
        database
    ):

        self.database = database


    # ========================================================
    # METİN ARAMA
    # ========================================================

    def search(
        self,
        query
    ):

        query = str(
            query
        ).lower().strip()


        if not query:

            return []


        results = []


        # ----------------------------------------------------
        # FACTS
        # ----------------------------------------------------

        for item in (
            self.database
            .get_facts()
        ):

            text = str(
                item.get(
                    "text",
                    ""
                )
            ).lower()


            if query in text:

                results.append({

                    "type":
                        "fact",

                    "item":
                        item

                })


        # ----------------------------------------------------
        # NOTES
        # ----------------------------------------------------

        for item in (
            self.database
            .get_notes()
        ):

            combined = (

                str(
                    item.get(
                        "title",
                        ""
                    )
                )

                + " "

                +

                str(
                    item.get(
                        "content",
                        ""
                    )
                )

            ).lower()


            if query in combined:

                results.append({

                    "type":
                        "note",

                    "item":
                        item

                })


        # ----------------------------------------------------
        # TASKS
        # ----------------------------------------------------

        for item in (
            self.database
            .get_tasks()
        ):

            combined = (

                str(
                    item.get(
                        "title",
                        ""
                    )
                )

                + " "

                +

                str(
                    item.get(
                        "description",
                        ""
                    )
                )

            ).lower()


            if query in combined:

                results.append({

                    "type":
                        "task",

                    "item":
                        item

                })


        return results


# ============================================================
# PERSONALITY PROFILE
# ============================================================

class PersonalityProfile:

    def __init__(
        self,
        database
    ):

        self.database = database


    # ========================================================
    # PROFİLİ AL
    # ========================================================

    def get(
        self
    ):

        return {

            "profile":
                self.database.data[
                    "profile"
                ],

            "preferences":
                self.database.data[
                    "preferences"
                ]

        }


    # ========================================================
    # DEĞER KAYDET
    # ========================================================

    def remember(
        self,
        key,
        value
    ):

        return self.database.set_profile(

            key,

            value

        )


    # ========================================================
    # TERCİH KAYDET
    # ========================================================

    def remember_preference(
        self,
        key,
        value
    ):

        return self.database.set_preference(

            key,

            value

        )


# ============================================================
# TASK MANAGER
# ============================================================

class TaskManager:

    def __init__(
        self,
        database
    ):

        self.database = database


    def create(
        self,
        title,
        description=""
    ):

        return self.database.add_task(

            title,

            description

        )


    def list_active(
        self
    ):

        return self.database.get_tasks(

            active_only=True

        )


    def complete(
        self,
        task_id
    ):

        return self.database.complete_task(

            task_id

        )


# ============================================================
# NOTES MANAGER
# ============================================================

class NotesManager:

    def __init__(
        self,
        database
    ):

        self.database = database


    def create(
        self,
        title,
        content
    ):

        return self.database.add_note(

            title,

            content

        )


    def list(
        self
    ):

        return self.database.get_notes()


    def delete(
        self,
        note_id
    ):

        return self.database.delete_note(

            note_id

        )


# ============================================================
# TITAN MEMORY SYSTEM
# ============================================================

class TitanMemorySystem:

    def __init__(
        self,
        core
    ):

        self.core = core


        self.storage = (
            AndroidStorage()
        )


        self.database = (
            MemoryDatabase(
                self.storage
            )
        )


        self.search = (
            MemorySearch(
                self.database
            )
        )


        self.personality = (
            PersonalityProfile(
                self.database
            )
        )


        self.tasks = (
            TaskManager(
                self.database
            )
        )


        self.notes = (
            NotesManager(
                self.database
            )
        )


        Logger.info(
            "Titan Memory System: ONLINE"
        )


    # ========================================================
    # HATIRLA
    # ========================================================

    def remember(
        self,
        text,
        category="general"
    ):

        return self.database.add_fact(

            text,

            category

        )


    # ========================================================
    # ARA
    # ========================================================

    def search_memory(
        self,
        query
    ):

        return self.search.search(
            query
        )


    # ========================================================
    # NOT
    # ========================================================

    def add_note(
        self,
        title,
        content
    ):

        return self.notes.create(

            title,

            content

        )


    # ========================================================
    # GÖREV
    # ========================================================

    def add_task(
        self,
        title,
        description=""
    ):

        return self.tasks.create(

            title,

            description

        )


    # ========================================================
    # PROFİL
    # ========================================================

    def set_profile(
        self,
        key,
        value
    ):

        return self.personality.remember(

            key,

            value

        )


    # ========================================================
    # DURUM
    # ========================================================

    def status(
        self
    ):

        return {

            "facts":
                len(
                    self.database.data[
                        "facts"
                    ]
                ),

            "conversations":
                len(
                    self.database.data[
                        "conversations"
                    ]
                ),

            "notes":
                len(
                    self.database.data[
                        "notes"
                    ]
                ),

            "tasks":
                len(
                    self.database.data[
                        "tasks"
                    ]
                ),

            "profile_fields":
                len(
                    self.database.data[
                        "profile"
                    ]
                )

        }


# ============================================================
# BÖLÜM 8 SONU
# ============================================================# ============================================================
# JARVIS TITAN
# BÖLÜM 9 — COMMAND CENTER / INTENT ENGINE
# ============================================================

import re
import time
import threading
from datetime import datetime


# ============================================================
# KOMUT SONUCU
# ============================================================

class CommandResult:

    def __init__(
        self,
        success=True,
        text="",
        intent="unknown",
        speak=True,
        data=None
    ):

        self.success = success

        self.text = text

        self.intent = intent

        self.speak = speak

        self.data = data or {}


    def to_dict(self):

        return {

            "success":
                self.success,

            "text":
                self.text,

            "intent":
                self.intent,

            "speak":
                self.speak,

            "data":
                self.data

        }


# ============================================================
# INTENT TANIMLARI
# ============================================================

class Intent:

    GREETING = "greeting"

    HELP = "help"

    TIME = "time"

    DATE = "date"

    REMEMBER = "remember"

    MEMORY_SEARCH = "memory_search"

    NOTE_ADD = "note_add"

    NOTE_LIST = "note_list"

    TASK_ADD = "task_add"

    TASK_LIST = "task_list"

    TASK_COMPLETE = "task_complete"

    SYSTEM_INFO = "system_info"

    DEVICE_INFO = "device_info"

    VOICE_MUTE = "voice_mute"

    VOICE_UNMUTE = "voice_unmute"

    STATUS = "status"

    CLEAR_MEMORY = "clear_memory"

    CHAT = "chat"

    UNKNOWN = "unknown"


# ============================================================
# METİN ANALİZCİ
# ============================================================

class CommandParser:

    def __init__(self):

        self.patterns = {

            Intent.GREETING: [

                r"\bmerhaba\b",

                r"\bselam\b",

                r"\bhey jarvis\b",

                r"\bjarvis merhaba\b",

                r"\bgünaydın\b",

                r"\biyi akşamlar\b",

            ],


            Intent.HELP: [

                r"\byardım\b",

                r"\bne yapabilirsin\b",

                r"\bkomutlar\b",

                r"\byardım et\b",

                r"\bözelliklerin\b",

            ],


            Intent.TIME: [

                r"\bsaat kaç\b",

                r"\bsaat nedir\b",

                r"\bşu an saat\b",

            ],


            Intent.DATE: [

                r"\bbugün hangi gün\b",

                r"\bbugünün tarihi\b",

                r"\btarih ne\b",

                r"\bhangi tarihteyiz\b",

            ],


            Intent.REMEMBER: [

                r"\bhatırla\b",

                r"\bhatırında tut\b",

                r"\bbunu unutma\b",

                r"\baklında tut\b",

                r"\bşunu kaydet\b",

            ],


            Intent.MEMORY_SEARCH: [

                r"\bhatırlıyor musun\b",

                r"\bhatırladığın\b",

                r"\bhafızanda\b",

                r"\bhafızamda\b",

                r"\bhatırla.*ne\b",

            ],


            Intent.NOTE_ADD: [

                r"\bnot al\b",

                r"\bnot ekle\b",

                r"\bnot oluştur\b",

                r"\bnot yaz\b",

                r"\bşunu not et\b",

            ],


            Intent.NOTE_LIST: [

                r"\bnotlarımı göster\b",

                r"\bnotlarımı aç\b",

                r"\bnotlar\b",

                r"\bnotlarım\b",

            ],


            Intent.TASK_ADD: [

                r"\bgörev ekle\b",

                r"\bgörev oluştur\b",

                r"\byapılacak ekle\b",

                r"\byapılacaklar listesine ekle\b",

            ],


            Intent.TASK_LIST: [

                r"\bgörevlerimi göster\b",

                r"\bgörevler\b",

                r"\byapılacaklar\b",

                r"\byapmam gerekenler\b",

            ],


            Intent.SYSTEM_INFO: [

                r"\bsistem bilgisi\b",

                r"\bsistem durumunu göster\b",

                r"\bsistemi göster\b",

                r"\bram kaç\b",

                r"\bişlemci\b",

                r"\bdepolama\b",

            ],


            Intent.DEVICE_INFO: [

                r"\btelefonum\b",

                r"\bcihazım\b",

                r"\btelefon bilgileri\b",

                r"\bcihaz bilgileri\b",

                r"\bhangi cihaz\b",

            ],


            Intent.VOICE_MUTE: [

                r"\bsessiz ol\b",

                r"\bsesini kapat\b",

                r"\bsessize al\b",

                r"\bkonuşma\b",

            ],


            Intent.VOICE_UNMUTE: [

                r"\bsesini aç\b",

                r"\bsesli moda geç\b",

                r"\bkonuşmaya devam et\b",

            ],


            Intent.STATUS: [

                r"\bdurumun ne\b",

                r"\bsistemler nasıl\b",

                r"\bçalışıyor musun\b",

                r"\bonline mısın\b",

                r"\bçevrimiçi misin\b",

            ],


            Intent.CLEAR_MEMORY: [

                r"\bhafızayı temizle\b",

                r"\bhafızanı temizle\b",

                r"\bgeçmişi sil\b",

            ],

        }


    # ========================================================
    # NORMALİZE
    # ========================================================

    def normalize(
        self,
        text
    ):

        text = str(
            text
        ).lower().strip()


        text = text.replace(
            "’",
            "'"
        )


        text = re.sub(

            r"\s+",

            " ",

            text

        )


        return text


    # ========================================================
    # INTENT BUL
    # ========================================================

    def detect(
        self,
        text
    ):

        normalized = (
            self.normalize(
                text
            )
        )


        scores = {}


        for intent, patterns in (
            self.patterns.items()
        ):

            score = 0


            for pattern in patterns:

                try:

                    if re.search(

                        pattern,

                        normalized

                    ):

                        score += 1

                except Exception:

                    pass


            if score:

                scores[intent] = score


        if scores:

            return max(

                scores,

                key=scores.get

            )


        return Intent.CHAT


    # ========================================================
    # İÇERİK ÇIKAR
    # ========================================================

    def extract_after(
        self,
        text,
        keywords
    ):

        normalized = (
            self.normalize(
                text
            )
        )


        for keyword in keywords:

            if keyword in normalized:

                index = (
                    normalized.find(
                        keyword
                    )
                )


                result = normalized[

                    index
                    + len(keyword):

                ].strip()


                if result:

                    return result


        return ""


# ============================================================
# COMMAND CENTER
# ============================================================

class CommandCenter:

    def __init__(
        self,
        core
    ):

        self.core = core

        self.parser = (
            CommandParser()
        )


        self.memory = None

        self.voice = None

        self.android = None

        self.ai = None


        self.running = True


        Logger.info(
            "Command Center: ONLINE"
        )


    # ========================================================
    # MODÜLLERİ BAĞLA
    # ========================================================

    def connect(
        self,
        memory=None,
        voice=None,
        android=None,
        ai=None
    ):

        self.memory = memory

        self.voice = voice

        self.android = android

        self.ai = ai


    # ========================================================
    # ANA KOMUT
    # ========================================================

    def process(
        self,
        text
    ):

        if not text:

            return CommandResult(

                success=False,

                text="Komut boş.",

                intent=Intent.UNKNOWN

            )


        intent = (
            self.parser.detect(
                text
            )
        )


        Logger.info(

            f"Intent detected: {intent}"

        )


        # ====================================================
        # GREETING
        # ====================================================

        if intent == Intent.GREETING:

            return CommandResult(

                text=(
                    "Merhaba. "
                    "JARVIS TITAN hazır."
                ),

                intent=intent

            )


        # ====================================================
        # HELP
        # ====================================================

        if intent == Intent.HELP:

            return CommandResult(

                text=(

                    "Komut, soru, not, "
                    "görev veya sistem "
                    "işlemi verebilirsin."

                ),

                intent=intent

            )


        # ====================================================
        # TIME
        # ====================================================

        if intent == Intent.TIME:

            now = datetime.now()

            return CommandResult(

                text=(

                    f"Şu an saat "

                    f"{now.strftime('%H:%M')}."

                ),

                intent=intent

            )


        # ====================================================
        # DATE
        # ====================================================

        if intent == Intent.DATE:

            now = datetime.now()

            days = [

                "Pazartesi",

                "Salı",

                "Çarşamba",

                "Perşembe",

                "Cuma",

                "Cumartesi",

                "Pazar"

            ]


            months = [

                "Ocak",

                "Şubat",

                "Mart",

                "Nisan",

                "Mayıs",

                "Haziran",

                "Temmuz",

                "Ağustos",

                "Eylül",

                "Ekim",

                "Kasım",

                "Aralık"

            ]


            text_result = (

                f"Bugün "

                f"{now.day} "

                f"{months[now.month - 1]} "

                f"{now.year}, "

                f"{days[now.weekday()]}."

            )


            return CommandResult(

                text=text_result,

                intent=intent

            )


        # ====================================================
        # REMEMBER
        # ====================================================

        if intent == Intent.REMEMBER:

            if not self.memory:

                return CommandResult(

                    success=False,

                    text=(
                        "Hafıza sistemi "
                        "bağlı değil."
                    ),

                    intent=intent

                )


            content = (
                self.parser.extract_after(

                    text,

                    [

                        "hatırla",

                        "hatırında tut",

                        "bunu unutma",

                        "aklında tut",

                        "şunu kaydet"

                    ]

                )
            )


            if not content:

                return CommandResult(

                    text=(
                        "Elbette. "
                        "Neyi hatırlamamı "
                        "istersin?"
                    ),

                    intent=intent

                )


            self.memory.remember(
                content
            )


            return CommandResult(

                text=(
                    "Tamam. Bunu "
                    "hafızama kaydettim."
                ),

                intent=intent,

                data={
                    "memory": content
                }

            )


        # ====================================================
        # MEMORY SEARCH
        # ====================================================

        if intent == Intent.MEMORY_SEARCH:

            if not self.memory:

                return CommandResult(

                    success=False,

                    text=(
                        "Hafıza sistemi "
                        "bağlı değil."
                    ),

                    intent=intent

                )


            query = (
                self.parser.extract_after(

                    text,

                    [

                        "hatırlıyor musun",

                        "hafızanda",

                        "hafızamda",

                        "hatırladığın"

                    ]

                )
            )


            if not query:

                facts = (
                    self.memory
                    .database
                    .get_facts()
                )


                if not facts:

                    return CommandResult(

                        text=(
                            "Henüz "
                            "kaydedilmiş "
                            "bir bilgi yok."
                        ),

                        intent=intent

                    )


                latest = facts[-5:]


                response = (
                    "Hatırladığım "
                    "son bilgiler: "
                )


                response += " | ".join(

                    item.get(
                        "text",
                        ""
                    )

                    for item in latest

                )


                return CommandResult(

                    text=response,

                    intent=intent

                )


            results = (
                self.memory
                .search_memory(
                    query
                )
            )


            if not results:

                return CommandResult(

                    text=(
                        "Hafızamda bununla "
                        "eşleşen bir bilgi "
                        "bulamadım."
                    ),

                    intent=intent

                )


            pieces = []


            for result in results[:5]:

                item = result.get(
                    "item",
                    {}
                )


                if result.get(
                    "type"
                ) == "fact":

                    pieces.append(

                        item.get(
                            "text",
                            ""
                        )

                    )


                elif result.get(
                    "type"
                ) == "note":

                    pieces.append(

                        item.get(
                            "content",
                            ""
                        )

                    )


            return CommandResult(

                text=(
                    "Bulduklarım: "
                    + " | ".join(
                        pieces
                    )
                ),

                intent=intent,

                data={
                    "results":
                        results
                }

            )


        # ====================================================
        # NOTE ADD
        # ====================================================

        if intent == Intent.NOTE_ADD:

            if not self.memory:

                return CommandResult(

                    success=False,

                    text=(
                        "Not sistemi "
                        "bağlı değil."
                    ),

                    intent=intent

                )


            content = (
                self.parser.extract_after(

                    text,

                    [

                        "not al",

                        "not ekle",

                        "not oluştur",

                        "not yaz",

                        "şunu not et"

                    ]

                )
            )


            if not content:

                return CommandResult(

                    text=(
                        "Tabii. "
                        "Neyi not almamı "
                        "istersiniz?"
                    ),

                    intent=intent

                )


            note = (
                self.memory.add_note(

                    "JARVIS Notu",

                    content

                )
            )


            return CommandResult(

                text=(
                    "Notu kaydettim."
                ),

                intent=intent,

                data={
                    "note":
                        note
                }

            )


        # ====================================================
        # NOTE LIST
        # ====================================================

        if intent == Intent.NOTE_LIST:

            if not self.memory:

                return CommandResult(

                    success=False,

                    text=(
                        "Not sistemi "
                        "bağlı değil."
                    ),

                    intent=intent

                )


            notes = (
                self.memory
                .notes
                .list()
            )


            if not notes:

                return CommandResult(

                    text=(
                        "Kayıtlı notun "
                        "bulunmuyor."
                    ),

                    intent=intent

                )


            latest = notes[-10:]


            lines = []


            for index, note in enumerate(

                latest,

                1

            ):

                lines.append(

                    f"{index}. "
                    f"{note.get('content', '')}"

                )


            return CommandResult(

                text=(
                    "Son notların:\n"
                    + "\n".join(lines)
                ),

                intent=intent,

                data={
                    "notes":
                        notes
                }

            )


        # ====================================================
        # TASK ADD
        # ====================================================

        if intent == Intent.TASK_ADD:

            if not self.memory:

                return CommandResult(

                    success=False,

                    text=(
                        "Görev sistemi "
                        "bağlı değil."
                    ),

                    intent=intent

                )


            content = (
                self.parser.extract_after(

                    text,

                    [

                        "görev ekle",

                        "görev oluştur",

                        "yapılacak ekle",

                        "yapılacaklar "
                        "listesine ekle"

                    ]

                )
            )


            if not content:

                return CommandResult(

                    text=(
                        "Elbette. "
                        "Hangi görevi "
                        "ekleyeyim?"
                    ),

                    intent=intent

                )


            task = (
                self.memory.add_task(

                    content

                )
            )


            return CommandResult(

                text=(
                    "Görevi ekledim."
                ),

                intent=intent,

                data={
                    "task":
                        task
                }

            )


        # ====================================================
        # TASK LIST
        # ====================================================

        if intent == Intent.TASK_LIST:

            if not self.memory:

                return CommandResult(

                    success=False,

                    text=(
                        "Görev sistemi "
                        "bağlı değil."
                    ),

                    intent=intent

                )


            tasks = (
                self.memory
                .tasks
                .list_active()
            )


            if not tasks:

                return CommandResult(

                    text=(
                        "Aktif görevin "
                        "bulunmuyor."
                    ),

                    intent=intent

                )


            lines = []


            for index, task in enumerate(

                tasks,

                1

            ):

                lines.append(

                    f"{index}. "
                    f"{task.get('title', '')}"

                )


            return CommandResult(

                text=(
                    "Aktif görevlerin:\n"
                    + "\n".join(lines)
                ),

                intent=intent,

                data={
                    "tasks":
                        tasks
                }

            )


        # ====================================================
        # SYSTEM INFO
        # ====================================================

        if intent == Intent.SYSTEM_INFO:

            if not self.android:

                return CommandResult(

                    success=False,

                    text=(
                        "Android sistem "
                        "modülü bağlı değil."
                    ),

                    intent=intent

                )


            try:

                info = (
                    self.android
                    .system_info()
                )


                device = info.get(
                    "device",
                    {}
                )


                text_result = (

                    "Sistem bilgileri: "

                    f"Cihaz "
                    f"{device.get('model', 'Bilinmiyor')}, "

                    f"Android "
                    f"{device.get('android', 'Bilinmiyor')}, "

                    f"CPU çekirdeği "
                    f"{info.get('cpu', 0)}."

                )


                return CommandResult(

                    text=text_result,

                    intent=intent,

                    data=info

                )


            except Exception as error:

                return CommandResult(

                    success=False,

                    text=(
                        "Sistem bilgilerini "
                        "alamadım."
                    ),

                    intent=intent,

                    data={
                        "error":
                            str(error)
                    }

                )


        # ====================================================
        # DEVICE INFO
        # ====================================================

        if intent == Intent.DEVICE_INFO:

            if not self.android:

                return CommandResult(

                    success=False,

                    text=(
                        "Android sistemi "
                        "bağlı değil."
                    ),

                    intent=intent

                )


            try:

                info = (
                    self.android
                    .device_info()
                )


                return CommandResult(

                    text=(

                        f"Cihazın "

                        f"{info.get('manufacturer', '')} "

                        f"{info.get('model', '')}. "

                        f"Android "

                        f"{info.get('android', '')}."

                    ),

                    intent=intent,

                    data=info

                )


            except Exception as error:

                return CommandResult(

                    success=False,

                    text=(
                        "Cihaz bilgisi "
                        "alınamadı."
                    ),

                    intent=intent,

                    data={
                        "error":
                            str(error)
                    }

                )


        # ====================================================
        # VOICE MUTE
        # ====================================================

        if intent == Intent.VOICE_MUTE:

            if self.voice:

                self.voice.mute()


            return CommandResult(

                text=(
                    "Sesli yanıtları "
                    "kapatıyorum."
                ),

                intent=intent,

                speak=False

            )


        # ====================================================
        # VOICE UNMUTE
        # ====================================================

        if intent == Intent.VOICE_UNMUTE:

            if self.voice:

                self.voice.unmute()


            return CommandResult(

                text=(
                    "Sesli yanıtları "
                    "yeniden açtım."
                ),

                intent=intent

            )


        # ====================================================
        # STATUS
        # ====================================================

        if intent == Intent.STATUS:

            systems = []


            if self.ai:

                try:

                    ai_status = (
                        self.ai.status()
                    )


                    systems.append(

                        "AI: "

                        + str(
                            ai_status
                        )

                    )

                except Exception:

                    systems.append(
                        "AI: HATA"
                    )


            if self.voice:

                try:

                    voice_status = (
                        self.voice
                        .status()
                    )


                    systems.append(

                        "VOICE: "

                        + str(
                            voice_status
                        )

                    )

                except Exception:

                    systems.append(
                        "VOICE: HATA"
                    )


            if self.android:

                systems.append(
                    "ANDROID: ONLINE"
                )


            return CommandResult(

                text=(

                    "Sistem kontrolü "
                    "tamamlandı. "

                    + " | ".join(
                        systems
                    )

                ),

                intent=intent

            )


        # ====================================================
        # CLEAR MEMORY
        # ====================================================

        if intent == Intent.CLEAR_MEMORY:

            if not self.memory:

                return CommandResult(

                    success=False,

                    text=(
                        "Hafıza sistemi "
                        "bağlı değil."
                    ),

                    intent=intent

                )


            return CommandResult(

                text=(
                    "Hafızayı tamamen "
                    "silmek güvenlik "
                    "nedeniyle doğrudan "
                    "gerçekleştirilmiyor. "
                    "Bu işlem için "
                    "uygulama içinden "
                    "onay gerekiyor."
                ),

                intent=intent,

                data={
                    "requires_confirmation":
                        True
                }

            )


        # ====================================================
        # CHAT FALLBACK
        # ====================================================

        if intent == Intent.CHAT:

            if self.ai:

                try:

                    response = (
                        self.ai.chat(
                            text
                        )
                    )


                    return CommandResult(

                        success=(
                            response.success
                        ),

                        text=(
                            response.text
                        ),

                        intent=Intent.CHAT,

                        data={
                            "provider":
                                response.provider,

                            "latency":
                                response.latency

                        }

                    )


                except Exception as error:

                    Logger.error(

                        "AI fallback error: "

                        + str(error)

                    )


            return CommandResult(

                text=(
                    "Komutunu aldım fakat "
                    "AI motoru şu anda "
                    "bağlı değil."
                ),

                intent=Intent.CHAT

            )


        # ====================================================
        # UNKNOWN
        # ====================================================

        return CommandResult(

            success=False,

            text=(
                "Bu komutu anlayamadım."
            ),

            intent=Intent.UNKNOWN

        )


# ============================================================
# TITAN COMMAND SYSTEM
# ============================================================

class TitanCommandSystem:

    def __init__(
        self,
        core
    ):

        self.core = core

        self.center = (
            CommandCenter(
                core
            )
        )


        Logger.info(
            "Titan Command System: ONLINE"
        )


    # ========================================================
    # MODÜLLERİ BAĞLA
    # ========================================================

    def connect(
        self,
        memory=None,
        voice=None,
        android=None,
        ai=None
    ):

        self.center.connect(

            memory=memory,

            voice=voice,

            android=android,

            ai=ai

        )


    # ========================================================
    # KOMUT ÇALIŞTIR
    # ========================================================

    def process(
        self,
        text
    ):

        return (
            self.center
            .process(
                text
            )
        )


    # ========================================================
    # DURUM
    # ========================================================

    def status(
        self
    ):

        return {

            "online":
                self.center.running,

            "parser":
                True,

            "connected_memory":
                self.center.memory is not None,

            "connected_voice":
                self.center.voice is not None,

            "connected_android":
                self.center.android is not None,

            "connected_ai":
                self.center.ai is not None

        }


# ============================================================
# BÖLÜM 9 SONU
# ============================================================# ============================================================
# JARVIS TITAN
# BÖLÜM 10 — TITAN CORE / BOOT / SYSTEM ORCHESTRATOR
# ============================================================

import time
import threading
import traceback
from datetime import datetime


# ============================================================
# BOOT STATES
# ============================================================

class BootState:

    CREATED = "CREATED"

    STARTING = "STARTING"

    ONLINE = "ONLINE"

    DEGRADED = "DEGRADED"

    STOPPING = "STOPPING"

    OFFLINE = "OFFLINE"

    ERROR = "ERROR"


# ============================================================
# SYSTEM EVENT
# ============================================================

class SystemEvent:

    def __init__(
        self,
        name,
        data=None
    ):

        self.name = name

        self.data = data or {}

        self.timestamp = (
            datetime.now().isoformat()
        )


# ============================================================
# EVENT BUS
# ============================================================

class EventBus:

    def __init__(self):

        self.listeners = {}

        self.lock = threading.Lock()


    # ========================================================
    # EVENT KAYDET
    # ========================================================

    def subscribe(
        self,
        event_name,
        callback
    ):

        with self.lock:

            if event_name not in self.listeners:

                self.listeners[event_name] = []


            if callback not in self.listeners[event_name]:

                self.listeners[event_name].append(
                    callback
                )


    # ========================================================
    # EVENT SİL
    # ========================================================

    def unsubscribe(
        self,
        event_name,
        callback
    ):

        with self.lock:

            if event_name not in self.listeners:

                return


            if callback in self.listeners[event_name]:

                self.listeners[event_name].remove(
                    callback
                )


    # ========================================================
    # EVENT YAYINLA
    # ========================================================

    def emit(
        self,
        event_name,
        data=None
    ):

        with self.lock:

            callbacks = list(

                self.listeners.get(
                    event_name,
                    []
                )

            )


        event = SystemEvent(

            event_name,

            data

        )


        for callback in callbacks:

            try:

                callback(
                    event
                )

            except Exception as error:

                Logger.error(

                    "Event callback error: "

                    + str(error)

                )


# ============================================================
# HEALTH MONITOR
# ============================================================

class HealthMonitor:

    def __init__(self):

        self.systems = {}

        self.lock = threading.Lock()


    # ========================================================
    # SİSTEM KAYDET
    # ========================================================

    def register(
        self,
        name
    ):

        with self.lock:

            self.systems[name] = {

                "status":
                    "UNKNOWN",

                "last_check":
                    None,

                "error":
                    None

            }


    # ========================================================
    # ONLINE
    # ========================================================

    def online(
        self,
        name
    ):

        with self.lock:

            if name not in self.systems:

                self.register(
                    name
                )


            self.systems[name][
                "status"
            ] = "ONLINE"


            self.systems[name][
                "last_check"
            ] = datetime.now().isoformat()


            self.systems[name][
                "error"
            ] = None


    # ========================================================
    # HATA
    # ========================================================

    def error(
        self,
        name,
        error
    ):

        with self.lock:

            if name not in self.systems:

                self.register(
                    name
                )


            self.systems[name][
                "status"
            ] = "ERROR"


            self.systems[name][
                "last_check"
            ] = datetime.now().isoformat()


            self.systems[name][
                "error"
            ] = str(error)


    # ========================================================
    # DURUM
    # ========================================================

    def snapshot(
        self
    ):

        with self.lock:

            return dict(
                self.systems
            )


# ============================================================
# SAFE EXECUTOR
# ============================================================

class SafeExecutor:

    @staticmethod
    def run(
        function,
        *args,
        **kwargs
    ):

        try:

            return {

                "success":
                    True,

                "result":
                    function(
                        *args,
                        **kwargs
                    ),

                "error":
                    None

            }


        except Exception as error:

            Logger.error(

                "SafeExecutor error: "

                + str(error)

            )


            return {

                "success":
                    False,

                "result":
                    None,

                "error":
                    str(error)

            }


# ============================================================
# JARVIS LOGGER
# ============================================================

class Logger:

    enabled = True


    @staticmethod
    def _write(
        level,
        message
    ):

        if not Logger.enabled:

            return


        timestamp = (
            datetime.now()
            .strftime("%H:%M:%S")
        )


        print(

            f"[{timestamp}] "
            f"[JARVIS:{level}] "
            f"{message}"

        )


    @staticmethod
    def info(
        message
    ):

        Logger._write(
            "INFO",
            message
        )


    @staticmethod
    def warning(
        message
    ):

        Logger._write(
            "WARNING",
            message
        )


    @staticmethod
    def error(
        message
    ):

        Logger._write(
            "ERROR",
            message
        )


# ============================================================
# TITAN CORE
# ============================================================

class TitanCore:

    def __init__(self):

        self.state = (
            BootState.CREATED
        )


        self.start_time = None

        self.shutdown_requested = False


        # ----------------------------------------------------
        # EVENT SYSTEM
        # ----------------------------------------------------

        self.events = EventBus()


        # ----------------------------------------------------
        # HEALTH
        # ----------------------------------------------------

        self.health = HealthMonitor()


        # ----------------------------------------------------
        # MODULES
        # ----------------------------------------------------

        self.modules = {}


        # ----------------------------------------------------
        # THREADS
        # ----------------------------------------------------

        self.background_threads = []


        Logger.info(
            "Titan Core created."
        )


    # ========================================================
    # MODÜL EKLE
    # ========================================================

    def register_module(
        self,
        name,
        module
    ):

        self.modules[name] = module

        self.health.register(
            name
        )


        Logger.info(

            f"Module registered: {name}"

        )


    # ========================================================
    # MODÜL AL
    # ========================================================

    def get_module(
        self,
        name
    ):

        return self.modules.get(
            name
        )


    # ========================================================
    # MODÜLLERİ BAŞLAT
    # ========================================================

    def initialize_modules(
        self
    ):

        for name, module in (
            self.modules.items()
        ):

            try:

                initializer = getattr(

                    module,

                    "initialize",

                    None

                )


                if callable(
                    initializer
                ):

                    initializer()


                self.health.online(
                    name
                )


                Logger.info(

                    f"Module online: {name}"

                )


            except Exception as error:

                self.health.error(

                    name,

                    error

                )


                Logger.error(

                    f"Module failed: {name}"

                )


    # ========================================================
    # BAŞLAT
    # ========================================================

    def start(
        self
    ):

        if self.state in (

            BootState.ONLINE,

            BootState.STARTING

        ):

            return


        self.state = (
            BootState.STARTING
        )


        self.start_time = time.time()

        self.shutdown_requested = False


        Logger.info(
            "================================"
        )

        Logger.info(
            "JARVIS TITAN BOOT SEQUENCE"
        )

        Logger.info(
            "================================"
        )


        try:

            self.initialize_modules()


            self.state = (
                BootState.ONLINE
            )


            self.events.emit(

                "system_online",

                self.status()

            )


            Logger.info(
                "JARVIS TITAN ONLINE."
            )


        except Exception as error:

            self.state = (
                BootState.ERROR
            )


            Logger.error(

                "Boot failure: "

                + str(error)

            )


            self.events.emit(

                "system_error",

                {

                    "error":
                        str(error)

                }

            )


    # ========================================================
    # ARKA PLAN THREAD
    # ========================================================

    def start_background_task(
        self,
        target,
        name=None
    ):

        if not callable(
            target
        ):

            return None


        thread = threading.Thread(

            target=target,

            name=name,

            daemon=True

        )


        thread.start()


        self.background_threads.append(
            thread
        )


        return thread


    # ========================================================
    # KOMUT
    # ========================================================

    def process(
        self,
        text
    ):

        command_system = (
            self.get_module(
                "commands"
            )
        )


        if not command_system:

            return {

                "success":
                    False,

                "text":
                    "Komut sistemi bağlı değil."

            }


        try:

            result = (
                command_system
                .process(
                    text
                )
            )


            if hasattr(
                result,
                "to_dict"
            ):

                return result.to_dict()


            return result


        except Exception as error:

            Logger.error(

                "Command processing error: "

                + str(error)

            )


            return {

                "success":
                    False,

                "text":
                    "Komut işlenirken "
                    "bir hata oluştu.",

                "error":
                    str(error)

            }


    # ========================================================
    # DURUM
    # ========================================================

    def status(
        self
    ):

        uptime = 0


        if self.start_time:

            uptime = (
                time.time()
                - self.start_time
            )


        return {

            "state":
                self.state,

            "uptime":
                round(
                    uptime,
                    2
                ),

            "modules":
                list(
                    self.modules.keys()
                ),

            "health":
                self.health.snapshot()

        }


    # ========================================================
    # KAPAT
    # ========================================================

    def shutdown(
        self
    ):

        if self.state == BootState.OFFLINE:

            return


        self.state = (
            BootState.STOPPING
        )


        self.shutdown_requested = True


        Logger.info(
            "JARVIS shutting down..."
        )


        for name, module in (
            self.modules.items()
        ):

            try:

                shutdown = getattr(

                    module,

                    "shutdown",

                    None

                )


                if callable(
                    shutdown
                ):

                    shutdown()


            except Exception as error:

                Logger.warning(

                    f"Shutdown error "
                    f"{name}: {error}"

                )


        self.events.emit(
            "system_offline"
        )


        self.state = (
            BootState.OFFLINE
        )


        Logger.info(
            "JARVIS offline."
        )


# ============================================================
# TITAN APPLICATION CONTROLLER
# ============================================================

class TitanApplication:

    def __init__(self):

        self.core = TitanCore()

        self.running = False


        Logger.info(
            "Titan Application created."
        )


    # ========================================================
    # MODÜL KUR
    # ========================================================

    def setup_modules(self):

        Logger.info(
            "Setting up modules..."
        )


        # ----------------------------------------------------
        # MEMORY
        # ----------------------------------------------------

        try:

            memory_class = globals().get(

                "TitanMemorySystem"

            )


            if memory_class:

                memory = memory_class(
                    self.core
                )


                self.core.register_module(

                    "memory",

                    memory

                )


        except Exception as error:

            Logger.error(

                "Memory setup error: "

                + str(error)

            )


        # ----------------------------------------------------
        # ANDROID
        # ----------------------------------------------------

        try:

            android_class = globals().get(

                "TitanAndroidSystem"

            )


            if android_class:

                android = android_class(
                    self.core
                )


                self.core.register_module(

                    "android",

                    android

                )


        except Exception as error:

            Logger.error(

                "Android setup error: "

                + str(error)

            )


        # ----------------------------------------------------
        # COMMANDS
        # ----------------------------------------------------

        try:

            command_class = globals().get(

                "TitanCommandSystem"

            )


            if command_class:

                commands = command_class(
                    self.core
                )


                self.core.register_module(

                    "commands",

                    commands

                )


        except Exception as error:

            Logger.error(

                "Command setup error: "

                + str(error)

            )


        # ----------------------------------------------------
        # BAĞLANTILAR
        # ----------------------------------------------------

        self.connect_modules()


    # ========================================================
    # MODÜLLERİ BAĞLA
    # ========================================================

    def connect_modules(self):

        memory = (
            self.core.get_module(
                "memory"
            )
        )


        android = (
            self.core.get_module(
                "android"
            )
        )


        commands = (
            self.core.get_module(
                "commands"
            )
        )


        if commands:

            commands.connect(

                memory=memory,

                android=android

            )


    # ========================================================
    # BAŞLAT
    # ========================================================

    def start(self):

        if self.running:

            return


        self.setup_modules()


        self.core.start()


        self.running = (

            self.core.state
            in [

                BootState.ONLINE,

                BootState.DEGRADED

            ]

        )


    # ========================================================
    # KOMUT
    # ========================================================

    def command(
        self,
        text
    ):

        return self.core.process(
            text
        )


    # ========================================================
    # DURUM
    # ========================================================

    def status(
        self
    ):

        return self.core.status()


    # ========================================================
    # KAPAT
    # ========================================================

    def stop(self):

        self.core.shutdown()

        self.running = False


# ============================================================
# GLOBAL JARVIS INSTANCE
# ============================================================

JARVIS = None


# ============================================================
# JARVIS BAŞLAT
# ============================================================

def create_jarvis():

    global JARVIS


    if JARVIS is None:

        JARVIS = (
            TitanApplication()
        )


    return JARVIS


# ============================================================
# BOOT
# ============================================================

def boot_jarvis():

    jarvis = create_jarvis()

    jarvis.start()

    return jarvis


# ============================================================
# SAFE MAIN
# ============================================================

def run_jarvis():

    try:

        jarvis = boot_jarvis()


        Logger.info(
            "JARVIS ready for commands."
        )


        return jarvis


    except Exception as error:

        Logger.error(

            "Fatal startup error: "

            + str(error)

        )


        traceback.print_exc()

        return None


# ============================================================
# BÖLÜM 10 SONU
# ============================================================