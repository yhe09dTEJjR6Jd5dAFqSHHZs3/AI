from __future__ import annotations

import csv
import ctypes
import json
import os
import queue
import random
import sys
import threading
import time
import traceback
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable

try:
    import cv2
    import joblib
    import mss
    import numpy as np
    import win32api
    import win32con
    import win32gui
    from pynput import keyboard, mouse
    from sklearn.ensemble import ExtraTreesClassifier, ExtraTreesRegressor
    from sklearn.metrics import accuracy_score, balanced_accuracy_score
    from sklearn.model_selection import train_test_split
except ImportError as exc:
    missing = getattr(exc, "name", str(exc))
    raise SystemExit(
        f"缺少依赖：{missing}\n\n"
        "请在命令提示符中运行：\n"
        "python -m pip install -r requirements.txt"
    ) from exc

import tkinter as tk
from tkinter import filedialog, messagebox, ttk


APP_NAME = "通用鼠标游戏 AI（模仿学习原型）"
APP_VERSION = "1.0.0"
MODEL_VERSION = 1
FEATURE_WIDTH = 32
FEATURE_HEIGHT = 18
MAX_REVIEW_SAMPLES = 30000
ACTIONS = (
    "idle",
    "move",
    "left_down",
    "left_up",
    "right_down",
    "right_up",
    "middle_down",
    "middle_up",
)
ACTION_CN = {
    "idle": "静止",
    "move": "移动",
    "left_down": "左键按下",
    "left_up": "左键释放",
    "right_down": "右键按下",
    "right_up": "右键释放",
    "middle_down": "中键按下",
    "middle_up": "中键释放",
}

PALETTE = {
    "red": "#E53935",
    "orange": "#FB8C00",
    "yellow": "#FDD835",
    "green": "#43A047",
    "cyan": "#00ACC1",
    "blue": "#1E88E5",
    "purple": "#8E24AA",
    "black": "#151515",
    "white": "#FAFAFA",
    "gray": "#757575",
    "light_gray": "#E0E0E0",
}


def set_dpi_awareness() -> None:
    """Avoid coordinate scaling mismatches on high-DPI Windows displays."""
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def atomic_json_dump(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    temp.replace(path)


def safe_imwrite(path: Path, image: np.ndarray, quality: int = 82) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise RuntimeError(f"图像编码失败：{path.name}")
    encoded.tofile(str(path))


def safe_imread(path: Path) -> np.ndarray | None:
    try:
        data = np.fromfile(str(path), dtype=np.uint8)
        if data.size == 0:
            return None
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        return None


@dataclass(frozen=True)
class WindowInfo:
    hwnd: int
    title: str

    @property
    def display(self) -> str:
        clean = " ".join(self.title.split())
        if len(clean) > 74:
            clean = clean[:71] + "..."
        return f"{clean}  [HWND {self.hwnd}]"


@dataclass(frozen=True)
class ClientRect:
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    def contains(self, x: int, y: int) -> bool:
        return self.left <= x < self.right and self.top <= y < self.bottom

    def normalize(self, x: int, y: int) -> tuple[float, float]:
        nx = (x - self.left) / max(1, self.width - 1)
        ny = (y - self.top) / max(1, self.height - 1)
        return clamp(nx, 0.0, 1.0), clamp(ny, 0.0, 1.0)

    def denormalize(self, nx: float, ny: float) -> tuple[int, int]:
        x = self.left + round(clamp(nx, 0.0, 1.0) * max(1, self.width - 1))
        y = self.top + round(clamp(ny, 0.0, 1.0) * max(1, self.height - 1))
        return int(x), int(y)


def enumerate_windows() -> list[WindowInfo]:
    windows: list[WindowInfo] = []

    def callback(hwnd: int, _: Any) -> bool:
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return True
            if win32gui.IsIconic(hwnd):
                return True
            title = win32gui.GetWindowText(hwnd).strip()
            if not title:
                return True
            client = get_client_rect(hwnd)
            if client.width < 120 or client.height < 80:
                return True
            windows.append(WindowInfo(hwnd=hwnd, title=title))
        except Exception:
            pass
        return True

    win32gui.EnumWindows(callback, None)
    windows.sort(key=lambda item: item.title.casefold())
    return windows


def get_client_rect(hwnd: int) -> ClientRect:
    if not win32gui.IsWindow(hwnd):
        raise RuntimeError("所选窗口已关闭。")
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    screen_left, screen_top = win32gui.ClientToScreen(hwnd, (left, top))
    screen_right, screen_bottom = win32gui.ClientToScreen(hwnd, (right, bottom))
    width = int(screen_right - screen_left)
    height = int(screen_bottom - screen_top)
    if width <= 0 or height <= 0:
        raise RuntimeError("窗口客户区尺寸无效，窗口可能已最小化。")
    return ClientRect(int(screen_left), int(screen_top), width, height)


def bring_window_to_front(hwnd: int) -> None:
    try:
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        # Windows can reject focus stealing. The loop will wait until the user clicks it.
        pass


def capture_client(sct: mss.mss, rect: ClientRect) -> np.ndarray:
    shot = sct.grab(
        {"left": rect.left, "top": rect.top, "width": rect.width, "height": rect.height}
    )
    bgra = np.asarray(shot, dtype=np.uint8)
    return cv2.cvtColor(bgra, cv2.COLOR_BGRA2BGR)


def preprocess_gray(image_bgr: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    return cv2.resize(gray, (FEATURE_WIDTH, FEATURE_HEIGHT), interpolation=cv2.INTER_AREA)


def make_feature(
    gray: np.ndarray,
    prev_gray: np.ndarray | None,
    x_norm: float,
    y_norm: float,
    left_down: bool,
    right_down: bool,
    middle_down: bool,
) -> np.ndarray:
    current = gray.astype(np.float32) / 255.0
    if prev_gray is None:
        diff = np.zeros_like(current, dtype=np.float32)
    else:
        diff = cv2.absdiff(gray, prev_gray).astype(np.float32) / 255.0
    state = np.asarray(
        [x_norm, y_norm, float(left_down), float(right_down), float(middle_down)],
        dtype=np.float32,
    )
    return np.concatenate((current.ravel(), diff.ravel(), state))


class EscWatcher:
    def __init__(self, stop_event: threading.Event):
        self.stop_event = stop_event
        self.listener: keyboard.Listener | None = None

    def start(self) -> None:
        def on_press(key: keyboard.Key | keyboard.KeyCode) -> bool | None:
            if key == keyboard.Key.esc:
                self.stop_event.set()
                return False
            return None

        self.listener = keyboard.Listener(on_press=on_press)
        self.listener.daemon = True
        self.listener.start()

    def stop(self) -> None:
        if self.listener is not None:
            try:
                self.listener.stop()
            except Exception:
                pass
            self.listener = None


class LearningRecorder:
    def __init__(
        self,
        hwnd: int,
        output_root: Path,
        fps: int,
        stop_event: threading.Event,
        status: Callable[[str], None],
        progress: Callable[[float], None],
    ) -> None:
        self.hwnd = hwnd
        self.output_root = output_root
        self.fps = fps
        self.stop_event = stop_event
        self.status = status
        self.progress = progress
        self.state_lock = threading.Lock()
        self.mouse_pos = tuple(win32api.GetCursorPos())
        self.buttons = {"left": False, "right": False, "middle": False}
        self.events: queue.Queue[dict[str, Any]] = queue.Queue()
        self.mouse_listener: mouse.Listener | None = None
        self.esc = EscWatcher(stop_event)
        self.session_dir: Path | None = None
        self.sample_count = 0
        self.frame_count = 0

    @staticmethod
    def _button_name(button: mouse.Button) -> str | None:
        if button == mouse.Button.left:
            return "left"
        if button == mouse.Button.right:
            return "right"
        if button == mouse.Button.middle:
            return "middle"
        return None

    def _on_move(self, x: int, y: int) -> None:
        with self.state_lock:
            self.mouse_pos = (int(x), int(y))

    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        name = self._button_name(button)
        if name is None:
            return
        with self.state_lock:
            self.mouse_pos = (int(x), int(y))
            self.buttons[name] = bool(pressed)
            snapshot = dict(self.buttons)
        try:
            rect = get_client_rect(self.hwnd)
            inside = rect.contains(int(x), int(y))
        except Exception:
            inside = False
        # Keep releases even if the cursor left the window, to avoid learning stuck buttons.
        if inside or not pressed:
            self.events.put(
                {
                    "timestamp": time.time(),
                    "action": f"{name}_{'down' if pressed else 'up'}",
                    "x": int(x),
                    "y": int(y),
                    "buttons": snapshot,
                }
            )

    def _start_listeners(self) -> None:
        self.mouse_listener = mouse.Listener(on_move=self._on_move, on_click=self._on_click)
        self.mouse_listener.daemon = True
        self.mouse_listener.start()
        self.esc.start()

    def _stop_listeners(self) -> None:
        self.esc.stop()
        if self.mouse_listener is not None:
            try:
                self.mouse_listener.stop()
            except Exception:
                pass
            self.mouse_listener = None

    def run(self) -> dict[str, Any]:
        session_dir = self.output_root / "sessions" / f"session_{now_stamp()}"
        frames_dir = session_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=False)
        self.session_dir = session_dir
        action_path = session_dir / "actions.jsonl"
        initial_rect = get_client_rect(self.hwnd)
        manifest = {
            "app": APP_NAME,
            "app_version": APP_VERSION,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "window_title": win32gui.GetWindowText(self.hwnd),
            "hwnd_at_recording": self.hwnd,
            "fps": self.fps,
            "initial_client_size": [initial_rect.width, initial_rect.height],
            "feature_size": [FEATURE_WIDTH, FEATURE_HEIGHT],
            "actions": list(ACTIONS),
            "status": "recording",
        }
        atomic_json_dump(session_dir / "manifest.json", manifest)

        self._start_listeners()
        bring_window_to_front(self.hwnd)
        self.status("学习中：请用鼠标玩游戏；按 ESC 结束。")
        last_norm: tuple[float, float] | None = None
        period = 1.0 / max(1, self.fps)
        next_tick = time.perf_counter()
        last_status = 0.0

        try:
            with action_path.open("w", encoding="utf-8", buffering=1) as action_file:
                with mss.mss() as sct:
                    while not self.stop_event.is_set():
                        tick_start = time.perf_counter()
                        try:
                            rect = get_client_rect(self.hwnd)
                        except Exception as exc:
                            raise RuntimeError(str(exc)) from exc

                        if win32gui.GetForegroundWindow() != self.hwnd:
                            if time.time() - last_status > 1.0:
                                self.status("学习暂停：请点击所选游戏窗口，ESC 可结束。")
                                last_status = time.time()
                            time.sleep(0.1)
                            next_tick = time.perf_counter()
                            continue

                        frame = capture_client(sct, rect)
                        frame_name = f"{self.frame_count:07d}.jpg"
                        frame_path = frames_dir / frame_name
                        safe_imwrite(frame_path, frame)
                        self.frame_count += 1

                        with self.state_lock:
                            x, y = self.mouse_pos
                            buttons = dict(self.buttons)
                        nx, ny = rect.normalize(int(x), int(y))

                        drained: list[dict[str, Any]] = []
                        while True:
                            try:
                                drained.append(self.events.get_nowait())
                            except queue.Empty:
                                break

                        rows: list[dict[str, Any]] = []
                        for event in drained:
                            ex, ey = rect.normalize(event["x"], event["y"])
                            event_buttons = event["buttons"]
                            rows.append(
                                self._make_row(
                                    frame_name,
                                    event["timestamp"],
                                    event["action"],
                                    ex,
                                    ey,
                                    event_buttons,
                                    rect,
                                )
                            )

                        if not rows:
                            moved = False
                            if last_norm is not None:
                                moved = abs(nx - last_norm[0]) + abs(ny - last_norm[1]) >= 0.006
                            action = "move" if moved else "idle"
                            rows.append(
                                self._make_row(
                                    frame_name,
                                    time.time(),
                                    action,
                                    nx,
                                    ny,
                                    buttons,
                                    rect,
                                )
                            )
                        last_norm = (nx, ny)

                        for row in rows:
                            row["sample_id"] = self.sample_count
                            action_file.write(json.dumps(row, ensure_ascii=False) + "\n")
                            self.sample_count += 1

                        if time.time() - last_status > 1.0:
                            self.status(
                                f"学习中：{self.frame_count} 帧，{self.sample_count} 条动作样本；ESC 结束。"
                            )
                            last_status = time.time()
                            self.progress((self.frame_count % 100) / 100.0)

                        next_tick += period
                        sleep_for = next_tick - time.perf_counter()
                        if sleep_for > 0:
                            time.sleep(sleep_for)
                        elif tick_start - next_tick > 2 * period:
                            next_tick = time.perf_counter()
        finally:
            self._stop_listeners()
            manifest["ended_at"] = datetime.now().isoformat(timespec="seconds")
            manifest["frames"] = self.frame_count
            manifest["samples"] = self.sample_count
            manifest["status"] = "complete" if self.sample_count else "empty"
            atomic_json_dump(session_dir / "manifest.json", manifest)

        return {
            "session_dir": str(session_dir),
            "frames": self.frame_count,
            "samples": self.sample_count,
        }

    def _make_row(
        self,
        frame_name: str,
        timestamp: float,
        action: str,
        x_norm: float,
        y_norm: float,
        buttons: dict[str, bool],
        rect: ClientRect,
    ) -> dict[str, Any]:
        return {
            "sample_id": self.sample_count,
            "timestamp": round(float(timestamp), 6),
            "frame": f"frames/{frame_name}",
            "action": action,
            "x_norm": round(float(x_norm), 6),
            "y_norm": round(float(y_norm), 6),
            "left_down": bool(buttons.get("left", False)),
            "right_down": bool(buttons.get("right", False)),
            "middle_down": bool(buttons.get("middle", False)),
            "client_width": rect.width,
            "client_height": rect.height,
        }


class DatasetReviewer:
    def __init__(
        self,
        output_root: Path,
        stop_event: threading.Event,
        status: Callable[[str], None],
        progress: Callable[[float], None],
    ) -> None:
        self.output_root = output_root
        self.stop_event = stop_event
        self.status = status
        self.progress = progress
        self.esc = EscWatcher(stop_event)

    def run(self) -> dict[str, Any]:
        self.esc.start()
        try:
            refs = self._collect_refs()
            if not refs:
                raise RuntimeError("没有找到学习数据。请先点击“学习”并完成至少一段演示。")
            if len(refs) > MAX_REVIEW_SAMPLES:
                indices = np.linspace(0, len(refs) - 1, MAX_REVIEW_SAMPLES, dtype=int)
                refs = [refs[int(i)] for i in indices]
                self.status(f"数据较多，已均匀抽取 {MAX_REVIEW_SAMPLES} 条样本进行复习。")

            X, actions, targets, preview_items, invalid = self._build_features(refs)
            if self.stop_event.is_set():
                raise InterruptedError("复习已由 ESC 停止。")
            if len(actions) < 20:
                raise RuntimeError(f"有效样本只有 {len(actions)} 条，建议至少学习 20 条。")

            counts = Counter(actions)
            self.status("复习中：训练动作分类模型……")
            classifier, metrics = self._train_classifier(X, np.asarray(actions, dtype=object))
            if self.stop_event.is_set():
                raise InterruptedError("复习已由 ESC 停止。")

            reg_mask = np.asarray([a != "idle" for a in actions], dtype=bool)
            regressor: ExtraTreesRegressor | None = None
            if int(reg_mask.sum()) >= 10:
                self.status("复习中：训练鼠标位置模型……")
                regressor = self._train_regressor(X[reg_mask], targets[reg_mask])
            if self.stop_event.is_set():
                raise InterruptedError("复习已由 ESC 停止。")

            model_dir = self.output_root / "model"
            review_dir = self.output_root / "review"
            model_dir.mkdir(parents=True, exist_ok=True)
            review_dir.mkdir(parents=True, exist_ok=True)
            stamp = now_stamp()
            model_path = model_dir / "game_ai_model.joblib"
            model_data = {
                "model_version": MODEL_VERSION,
                "app_version": APP_VERSION,
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "feature_width": FEATURE_WIDTH,
                "feature_height": FEATURE_HEIGHT,
                "classifier": classifier,
                "regressor": regressor,
                "action_counts": dict(counts),
                "metrics": metrics,
                "samples": len(actions),
            }
            joblib.dump(model_data, model_path, compress=3)

            report = {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "samples_found": len(refs),
                "samples_used": len(actions),
                "invalid_samples": invalid,
                "action_distribution": dict(counts),
                "metrics": metrics,
                "model_path": str(model_path),
                "notes": [
                    "复习阶段使用低分辨率画面、画面变化和鼠标状态训练模仿学习模型。",
                    "模型只适用于与学习阶段相近的窗口尺寸、游戏版本、场景和操作逻辑。",
                ],
            }
            report_path = review_dir / f"report_{stamp}.json"
            atomic_json_dump(report_path, report)
            self._write_distribution(review_dir / f"action_distribution_{stamp}.csv", counts)
            contact_path = review_dir / f"contact_sheet_{stamp}.jpg"
            self._write_contact_sheet(contact_path, preview_items)
            self.progress(1.0)
            return {
                "samples": len(actions),
                "invalid": invalid,
                "counts": dict(counts),
                "metrics": metrics,
                "model_path": str(model_path),
                "report_path": str(report_path),
                "contact_path": str(contact_path),
            }
        finally:
            self.esc.stop()

    def _collect_refs(self) -> list[tuple[Path, dict[str, Any]]]:
        sessions_dir = self.output_root / "sessions"
        if not sessions_dir.exists():
            return []
        refs: list[tuple[Path, dict[str, Any]]] = []
        session_paths = sorted(p for p in sessions_dir.glob("session_*") if p.is_dir())
        total_sessions = max(1, len(session_paths))
        for index, session_dir in enumerate(session_paths):
            if self.stop_event.is_set():
                break
            action_path = session_dir / "actions.jsonl"
            if not action_path.exists():
                continue
            self.status(f"复习中：读取第 {index + 1}/{total_sessions} 个学习会话……")
            try:
                with action_path.open("r", encoding="utf-8") as fh:
                    for line in fh:
                        try:
                            row = json.loads(line)
                            if row.get("action") in ACTIONS and row.get("frame"):
                                refs.append((session_dir, row))
                        except (json.JSONDecodeError, TypeError):
                            continue
            except OSError:
                continue
            self.progress(0.1 * (index + 1) / total_sessions)
        return refs

    def _build_features(
        self, refs: list[tuple[Path, dict[str, Any]]]
    ) -> tuple[np.ndarray, list[str], np.ndarray, list[tuple[Path, str]], int]:
        features: list[np.ndarray] = []
        actions: list[str] = []
        targets: list[tuple[float, float]] = []
        preview: list[tuple[Path, str]] = []
        invalid = 0
        prev_by_session: dict[Path, np.ndarray] = {}
        last_frame_by_session: dict[Path, Path] = {}
        base_cache: dict[tuple[Path, Path], tuple[np.ndarray, np.ndarray | None]] = {}
        total = max(1, len(refs))

        for idx, (session_dir, row) in enumerate(refs):
            if self.stop_event.is_set():
                break
            frame_path = session_dir / str(row["frame"])
            cache_key = (session_dir, frame_path)
            cached = base_cache.get(cache_key)
            if cached is None:
                image = safe_imread(frame_path)
                if image is None:
                    invalid += 1
                    continue
                gray = preprocess_gray(image)
                prev_gray = prev_by_session.get(session_dir)
                cached = (gray, prev_gray)
                base_cache.clear()  # one-frame cache is enough for duplicate event rows
                base_cache[cache_key] = cached
                if last_frame_by_session.get(session_dir) != frame_path:
                    prev_by_session[session_dir] = gray
                    last_frame_by_session[session_dir] = frame_path
            gray, prev_gray = cached
            try:
                x_norm = clamp(float(row.get("x_norm", 0.5)), 0.0, 1.0)
                y_norm = clamp(float(row.get("y_norm", 0.5)), 0.0, 1.0)
                feature = make_feature(
                    gray,
                    prev_gray,
                    x_norm,
                    y_norm,
                    bool(row.get("left_down", False)),
                    bool(row.get("right_down", False)),
                    bool(row.get("middle_down", False)),
                )
                features.append(feature)
                actions.append(str(row["action"]))
                targets.append((x_norm, y_norm))
                if len(preview) < 18 and (idx % max(1, total // 18) == 0):
                    preview.append((frame_path, str(row["action"])))
            except Exception:
                invalid += 1

            if idx % 100 == 0 or idx + 1 == total:
                self.status(f"复习中：提取视觉特征 {idx + 1}/{total}……")
                self.progress(0.1 + 0.35 * (idx + 1) / total)

        if not features:
            return (
                np.empty((0, FEATURE_WIDTH * FEATURE_HEIGHT * 2 + 5), dtype=np.float32),
                [],
                np.empty((0, 2), dtype=np.float32),
                preview,
                invalid,
            )
        return (
            np.vstack(features).astype(np.float32, copy=False),
            actions,
            np.asarray(targets, dtype=np.float32),
            preview,
            invalid,
        )

    def _train_classifier(
        self, X: np.ndarray, y: np.ndarray
    ) -> tuple[ExtraTreesClassifier, dict[str, Any]]:
        counts = Counter(y.tolist())
        can_stratify = len(counts) > 1 and min(counts.values()) >= 2 and len(y) >= 50
        if len(y) >= 50:
            X_train, X_test, y_train, y_test = train_test_split(
                X,
                y,
                test_size=0.15,
                random_state=42,
                stratify=y if can_stratify else None,
            )
        else:
            X_train, X_test, y_train, y_test = X, X, y, y

        model = ExtraTreesClassifier(
            n_estimators=0,
            max_depth=26,
            min_samples_leaf=2,
            max_features="sqrt",
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
            warm_start=True,
        )
        total_trees = 160
        step = 20
        for tree_count in range(step, total_trees + 1, step):
            if self.stop_event.is_set():
                break
            model.set_params(n_estimators=tree_count)
            model.fit(X_train, y_train)
            self.status(f"复习中：动作模型 {tree_count}/{total_trees} 棵树……")
            self.progress(0.45 + 0.30 * tree_count / total_trees)

        if not hasattr(model, "classes_"):
            raise InterruptedError("复习已由 ESC 停止。")
        pred = model.predict(X_test)
        metrics = {
            "validation_samples": int(len(y_test)),
            "accuracy": round(float(accuracy_score(y_test, pred)), 4),
            "balanced_accuracy": round(float(balanced_accuracy_score(y_test, pred)), 4),
        }
        return model, metrics

    def _train_regressor(self, X: np.ndarray, y: np.ndarray) -> ExtraTreesRegressor:
        model = ExtraTreesRegressor(
            n_estimators=0,
            max_depth=26,
            min_samples_leaf=2,
            max_features=0.7,
            random_state=43,
            n_jobs=-1,
            warm_start=True,
        )
        total_trees = 140
        step = 20
        for tree_count in range(step, total_trees + 1, step):
            if self.stop_event.is_set():
                break
            model.set_params(n_estimators=tree_count)
            model.fit(X, y)
            self.status(f"复习中：位置模型 {tree_count}/{total_trees} 棵树……")
            self.progress(0.75 + 0.20 * tree_count / total_trees)
        if not hasattr(model, "estimators_"):
            raise InterruptedError("复习已由 ESC 停止。")
        return model

    @staticmethod
    def _write_distribution(path: Path, counts: Counter[str]) -> None:
        with path.open("w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["action", "action_cn", "count"])
            for action in ACTIONS:
                writer.writerow([action, ACTION_CN[action], counts.get(action, 0)])

    @staticmethod
    def _write_contact_sheet(path: Path, items: list[tuple[Path, str]]) -> None:
        if not items:
            return
        thumbs: list[np.ndarray] = []
        for frame_path, action in items[:12]:
            image = safe_imread(frame_path)
            if image is None:
                continue
            thumb = cv2.resize(image, (320, 180), interpolation=cv2.INTER_AREA)
            cv2.rectangle(thumb, (0, 0), (320, 28), (0, 0, 0), thickness=-1)
            cv2.putText(
                thumb,
                action,
                (8, 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
            thumbs.append(thumb)
        if not thumbs:
            return
        while len(thumbs) % 3:
            thumbs.append(np.zeros_like(thumbs[0]))
        rows = [np.hstack(thumbs[i : i + 3]) for i in range(0, len(thumbs), 3)]
        sheet = np.vstack(rows)
        safe_imwrite(path, sheet, quality=88)


class MouseExecutor:
    FLAG_MAP = {
        "left_down": win32con.MOUSEEVENTF_LEFTDOWN,
        "left_up": win32con.MOUSEEVENTF_LEFTUP,
        "right_down": win32con.MOUSEEVENTF_RIGHTDOWN,
        "right_up": win32con.MOUSEEVENTF_RIGHTUP,
        "middle_down": win32con.MOUSEEVENTF_MIDDLEDOWN,
        "middle_up": win32con.MOUSEEVENTF_MIDDLEUP,
    }

    def __init__(self) -> None:
        self.down = {"left": False, "right": False, "middle": False}
        self.down_since = {"left": 0.0, "right": 0.0, "middle": 0.0}

    def move_to(self, x: int, y: int) -> None:
        win32api.SetCursorPos((int(x), int(y)))

    def perform(self, action: str) -> bool:
        if action not in self.FLAG_MAP:
            return False
        name, edge = action.split("_", 1)
        desired_down = edge == "down"
        if self.down[name] == desired_down:
            return False
        win32api.mouse_event(self.FLAG_MAP[action], 0, 0, 0, 0)
        self.down[name] = desired_down
        self.down_since[name] = time.time() if desired_down else 0.0
        return True

    def release_expired(self, max_hold_seconds: float = 1.6) -> None:
        now = time.time()
        for name in ("left", "right", "middle"):
            if self.down[name] and now - self.down_since[name] > max_hold_seconds:
                self.perform(f"{name}_up")

    def release_all(self) -> None:
        for name in ("left", "right", "middle"):
            if self.down[name]:
                try:
                    self.perform(f"{name}_up")
                except Exception:
                    pass


class AutoPlayer:
    def __init__(
        self,
        hwnd: int,
        output_root: Path,
        fps: int,
        confidence: float,
        stop_event: threading.Event,
        status: Callable[[str], None],
        progress: Callable[[float], None],
    ) -> None:
        self.hwnd = hwnd
        self.output_root = output_root
        self.fps = fps
        self.confidence = confidence
        self.stop_event = stop_event
        self.status = status
        self.progress = progress
        self.esc = EscWatcher(stop_event)
        self.executor = MouseExecutor()

    def run(self) -> dict[str, Any]:
        model_path = self.output_root / "model" / "game_ai_model.joblib"
        if not model_path.exists():
            raise RuntimeError("没有找到模型。请先完成“学习”，再点击“复习”。")
        model_data = joblib.load(model_path)
        if int(model_data.get("model_version", -1)) != MODEL_VERSION:
            raise RuntimeError("模型版本不兼容，请重新点击“复习”生成模型。")
        classifier: ExtraTreesClassifier = model_data["classifier"]
        regressor: ExtraTreesRegressor | None = model_data.get("regressor")

        run_dir = self.output_root / "runs" / f"run_{now_stamp()}"
        run_dir.mkdir(parents=True, exist_ok=False)
        log_path = run_dir / "actions.jsonl"
        self.esc.start()
        bring_window_to_front(self.hwnd)
        period = 1.0 / max(1, self.fps)
        prev_gray: np.ndarray | None = None
        action_count = 0
        frame_count = 0
        last_transition = 0.0
        last_status = 0.0
        next_tick = time.perf_counter()
        self.status("AI 运行中：只会操作所选窗口；按 ESC 立即停止。")

        try:
            with log_path.open("w", encoding="utf-8", buffering=1) as log_file:
                with mss.mss() as sct:
                    while not self.stop_event.is_set():
                        rect = get_client_rect(self.hwnd)
                        if win32gui.GetForegroundWindow() != self.hwnd:
                            self.executor.release_all()
                            if time.time() - last_status > 1.0:
                                self.status("AI 已暂停：请点击所选游戏窗口；ESC 可结束。")
                                last_status = time.time()
                            time.sleep(0.1)
                            prev_gray = None
                            next_tick = time.perf_counter()
                            continue

                        frame = capture_client(sct, rect)
                        gray = preprocess_gray(frame)
                        cursor_x, cursor_y = win32api.GetCursorPos()
                        nx, ny = rect.normalize(cursor_x, cursor_y)
                        feature = make_feature(
                            gray,
                            prev_gray,
                            nx,
                            ny,
                            self.executor.down["left"],
                            self.executor.down["right"],
                            self.executor.down["middle"],
                        ).reshape(1, -1)
                        prev_gray = gray

                        probabilities = classifier.predict_proba(feature)[0]
                        class_index = int(np.argmax(probabilities))
                        action = str(classifier.classes_[class_index])
                        probability = float(probabilities[class_index])

                        target_x, target_y = cursor_x, cursor_y
                        if regressor is not None and action != "idle":
                            target = regressor.predict(feature)[0]
                            target_x, target_y = rect.denormalize(float(target[0]), float(target[1]))

                        performed = False
                        if action == "move":
                            self.executor.move_to(target_x, target_y)
                            performed = True
                        elif action.endswith("_down") or action.endswith("_up"):
                            # Transition actions require confidence and a small debounce interval.
                            if probability >= self.confidence and time.time() - last_transition >= 0.07:
                                self.executor.move_to(target_x, target_y)
                                performed = self.executor.perform(action)
                                if performed:
                                    last_transition = time.time()
                        self.executor.release_expired()

                        row = {
                            "timestamp": round(time.time(), 6),
                            "frame_index": frame_count,
                            "action": action,
                            "probability": round(probability, 5),
                            "performed": performed,
                            "x_norm": round(rect.normalize(target_x, target_y)[0], 6),
                            "y_norm": round(rect.normalize(target_x, target_y)[1], 6),
                        }
                        log_file.write(json.dumps(row, ensure_ascii=False) + "\n")
                        frame_count += 1
                        if performed:
                            action_count += 1

                        if time.time() - last_status > 1.0:
                            self.status(
                                f"AI 运行中：预测 {ACTION_CN.get(action, action)} "
                                f"({probability:.0%})，已执行 {action_count} 次；ESC 结束。"
                            )
                            self.progress((frame_count % 100) / 100.0)
                            last_status = time.time()

                        next_tick += period
                        sleep_for = next_tick - time.perf_counter()
                        if sleep_for > 0:
                            time.sleep(sleep_for)
                        else:
                            next_tick = time.perf_counter()
        finally:
            self.executor.release_all()
            self.esc.stop()
            atomic_json_dump(
                run_dir / "summary.json",
                {
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                    "frames": frame_count,
                    "performed_actions": action_count,
                    "fps": self.fps,
                    "confidence": self.confidence,
                    "stopped_by_user": self.stop_event.is_set(),
                },
            )

        return {
            "run_dir": str(run_dir),
            "frames": frame_count,
            "actions": action_count,
        }


class GameAIApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("920x700")
        self.root.minsize(820, 620)
        self.root.configure(bg=PALETTE["black"])
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.windows: list[WindowInfo] = []
        self.window_by_display: dict[str, WindowInfo] = {}
        self.active_thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.mode: str | None = None

        self.window_var = tk.StringVar()
        self.folder_var = tk.StringVar()
        self.fps_var = tk.IntVar(value=8)
        self.confidence_var = tk.DoubleVar(value=0.45)
        self.status_var = tk.StringVar(value="请选择窗口和数据文件夹。")
        self.progress_var = tk.DoubleVar(value=0.0)

        self._configure_style()
        self._build_ui()
        self.refresh_windows()
        self._log(f"{APP_NAME} v{APP_VERSION}")
        self._log("安全停止键：ESC。AI 只在所选窗口位于前台时操作鼠标。")

    def _configure_style(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Game.TCombobox",
            fieldbackground=PALETTE["white"],
            background=PALETTE["light_gray"],
            foreground=PALETTE["black"],
            padding=7,
        )
        style.configure(
            "Game.Horizontal.TProgressbar",
            troughcolor="#303030",
            background=PALETTE["yellow"],
            bordercolor="#303030",
            lightcolor=PALETTE["yellow"],
            darkcolor=PALETTE["orange"],
        )

    def _build_ui(self) -> None:
        top = tk.Frame(self.root, bg=PALETTE["black"])
        top.pack(fill="x")
        for name in ("red", "orange", "yellow", "green", "cyan", "blue", "purple", "black", "white", "gray"):
            tk.Frame(top, bg=PALETTE[name], height=10).pack(side="left", fill="x", expand=True)

        header = tk.Frame(self.root, bg=PALETTE["black"], padx=22, pady=16)
        header.pack(fill="x")
        tk.Label(
            header,
            text=APP_NAME,
            bg=PALETTE["black"],
            fg=PALETTE["white"],
            font=("Microsoft YaHei UI", 20, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Windows 11 · 选择窗口 · 指定目录 · 学习 → 复习 → AI运行",
            bg=PALETTE["black"],
            fg=PALETTE["light_gray"],
            font=("Microsoft YaHei UI", 10),
        ).pack(anchor="w", pady=(4, 0))

        setup = tk.Frame(self.root, bg="#262626", padx=18, pady=16, highlightthickness=1, highlightbackground=PALETTE["gray"])
        setup.pack(fill="x", padx=22, pady=(0, 12))

        tk.Label(setup, text="目标窗口", bg="#262626", fg=PALETTE["yellow"], font=("Microsoft YaHei UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.window_combo = ttk.Combobox(setup, textvariable=self.window_var, state="readonly", style="Game.TCombobox")
        self.window_combo.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        self.refresh_button = self._make_button(setup, "刷新窗口", PALETTE["cyan"], self.refresh_windows, width=11)
        self.refresh_button.grid(row=0, column=2, pady=5)

        tk.Label(setup, text="数据文件夹", bg="#262626", fg=PALETTE["yellow"], font=("Microsoft YaHei UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        self.folder_entry = tk.Entry(setup, textvariable=self.folder_var, bg=PALETTE["white"], fg=PALETTE["black"], relief="flat", font=("Microsoft YaHei UI", 10))
        self.folder_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=5, ipady=7)
        self.folder_button = self._make_button(setup, "选择文件夹", PALETTE["blue"], self.choose_folder, width=11)
        self.folder_button.grid(row=1, column=2, pady=5)

        options = tk.Frame(setup, bg="#262626")
        options.grid(row=2, column=1, sticky="w", padx=10, pady=(8, 0))
        tk.Label(options, text="FPS", bg="#262626", fg=PALETTE["white"], font=("Microsoft YaHei UI", 9)).pack(side="left")
        tk.Spinbox(options, from_=4, to=20, textvariable=self.fps_var, width=5, bg=PALETTE["white"], relief="flat").pack(side="left", padx=(6, 18), ipady=3)
        tk.Label(options, text="按键置信度", bg="#262626", fg=PALETTE["white"], font=("Microsoft YaHei UI", 9)).pack(side="left")
        tk.Scale(
            options,
            from_=0.20,
            to=0.90,
            resolution=0.05,
            orient="horizontal",
            variable=self.confidence_var,
            length=180,
            bg="#262626",
            fg=PALETTE["white"],
            troughcolor=PALETTE["gray"],
            highlightthickness=0,
            activebackground=PALETTE["orange"],
        ).pack(side="left", padx=6)
        setup.columnconfigure(1, weight=1)

        controls = tk.Frame(self.root, bg=PALETTE["black"], padx=22, pady=5)
        controls.pack(fill="x")
        self.learn_button = self._make_button(controls, "① 学习", PALETTE["green"], self.start_learning, width=15, height=2)
        self.review_button = self._make_button(controls, "② 复习", PALETTE["orange"], self.start_review, width=15, height=2)
        self.train_button = self._make_button(controls, "③ 训练 / AI运行", PALETTE["red"], self.start_training, width=17, height=2)
        self.stop_button = self._make_button(controls, "ESC / 停止", PALETTE["purple"], self.request_stop, width=15, height=2)
        self.learn_button.pack(side="left", expand=True, padx=5)
        self.review_button.pack(side="left", expand=True, padx=5)
        self.train_button.pack(side="left", expand=True, padx=5)
        self.stop_button.pack(side="left", expand=True, padx=5)
        self.stop_button.configure(state="disabled")

        status_frame = tk.Frame(self.root, bg="#262626", padx=18, pady=12, highlightthickness=1, highlightbackground=PALETTE["gray"])
        status_frame.pack(fill="x", padx=22, pady=12)
        tk.Label(status_frame, textvariable=self.status_var, bg="#262626", fg=PALETTE["yellow"], anchor="w", font=("Microsoft YaHei UI", 10, "bold"), wraplength=830).pack(fill="x")
        ttk.Progressbar(status_frame, variable=self.progress_var, maximum=1.0, style="Game.Horizontal.TProgressbar").pack(fill="x", pady=(10, 0))

        notes = tk.Frame(self.root, bg=PALETTE["white"], padx=16, pady=12)
        notes.pack(fill="x", padx=22, pady=(0, 12))
        note_text = (
            "使用顺序：学习时亲自玩游戏并按 ESC 结束；复习会整理数据并生成模型；训练阶段由 AI 操作鼠标。\n"
            "重要：窗口必须在前台且不可最小化。不要用于带反作弊系统、金融操作或任何禁止自动化的场景。"
        )
        tk.Label(notes, text=note_text, bg=PALETTE["white"], fg=PALETTE["black"], justify="left", anchor="w", font=("Microsoft YaHei UI", 9), wraplength=840).pack(fill="x")

        log_frame = tk.Frame(self.root, bg=PALETTE["gray"], padx=1, pady=1)
        log_frame.pack(fill="both", expand=True, padx=22, pady=(0, 18))
        self.log_text = tk.Text(
            log_frame,
            bg="#111111",
            fg=PALETTE["light_gray"],
            insertbackground=PALETTE["white"],
            relief="flat",
            font=("Consolas", 9),
            wrap="word",
            state="disabled",
            height=9,
        )
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

    @staticmethod
    def _make_button(
        parent: tk.Widget,
        text: str,
        color: str,
        command: Callable[[], None],
        width: int,
        height: int = 1,
    ) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg=PALETTE["white"] if color not in (PALETTE["yellow"], PALETTE["white"]) else PALETTE["black"],
            activebackground=color,
            activeforeground=PALETTE["white"],
            relief="flat",
            cursor="hand2",
            font=("Microsoft YaHei UI", 10, "bold"),
            width=width,
            height=height,
            padx=8,
            pady=5,
        )

    def refresh_windows(self) -> None:
        try:
            self.windows = enumerate_windows()
            self.window_by_display = {item.display: item for item in self.windows}
            values = list(self.window_by_display)
            self.window_combo["values"] = values
            current = self.window_var.get()
            if current not in self.window_by_display:
                self.window_var.set(values[0] if values else "")
            self._log(f"已发现 {len(values)} 个可选窗口。")
        except Exception as exc:
            self._show_error("刷新窗口失败", exc)

    def choose_folder(self) -> None:
        selected = filedialog.askdirectory(title="选择 AI 数据文件夹")
        if selected:
            self.folder_var.set(str(Path(selected).resolve()))
            self._log(f"数据文件夹：{self.folder_var.get()}")

    def start_learning(self) -> None:
        context = self._validate_context(needs_model=False)
        if context is None:
            return
        hwnd, root = context
        self._start_worker(
            "学习",
            lambda: LearningRecorder(
                hwnd,
                root,
                self._validated_fps(),
                self.stop_event,
                self._set_status_threadsafe,
                self._set_progress_threadsafe,
            ).run(),
        )

    def start_review(self) -> None:
        root = self._validate_folder()
        if root is None:
            return
        self._start_worker(
            "复习",
            lambda: DatasetReviewer(
                root,
                self.stop_event,
                self._set_status_threadsafe,
                self._set_progress_threadsafe,
            ).run(),
        )

    def start_training(self) -> None:
        context = self._validate_context(needs_model=True)
        if context is None:
            return
        hwnd, root = context
        confidence = clamp(float(self.confidence_var.get()), 0.2, 0.9)
        self._start_worker(
            "训练 / AI运行",
            lambda: AutoPlayer(
                hwnd,
                root,
                self._validated_fps(),
                confidence,
                self.stop_event,
                self._set_status_threadsafe,
                self._set_progress_threadsafe,
            ).run(),
        )

    def _validate_context(self, needs_model: bool) -> tuple[int, Path] | None:
        selected = self.window_by_display.get(self.window_var.get())
        if selected is None or not win32gui.IsWindow(selected.hwnd):
            messagebox.showwarning("请选择窗口", "请先选择一个仍在运行的目标窗口。")
            return None
        root = self._validate_folder()
        if root is None:
            return None
        if needs_model and not (root / "model" / "game_ai_model.joblib").exists():
            messagebox.showwarning("缺少模型", "请先完成学习，再点击复习生成模型。")
            return None
        return selected.hwnd, root

    def _validate_folder(self) -> Path | None:
        raw = self.folder_var.get().strip()
        if not raw:
            messagebox.showwarning("请选择文件夹", "所有生成文件都会保存到你指定的文件夹，请先选择。")
            return None
        root = Path(raw).expanduser()
        try:
            root.mkdir(parents=True, exist_ok=True)
            test_path = root / ".game_ai_write_test"
            test_path.write_text("ok", encoding="utf-8")
            test_path.unlink(missing_ok=True)
            return root.resolve()
        except Exception as exc:
            messagebox.showerror("文件夹不可写", f"无法写入所选文件夹：\n{exc}")
            return None

    def _validated_fps(self) -> int:
        try:
            return int(clamp(int(self.fps_var.get()), 4, 20))
        except Exception:
            return 8

    def _start_worker(self, mode: str, target: Callable[[], dict[str, Any]]) -> None:
        if self.active_thread and self.active_thread.is_alive():
            messagebox.showinfo("任务正在运行", "请先按 ESC 或点击停止。")
            return
        self.mode = mode
        self.stop_event = threading.Event()
        self._set_busy(True)
        self.progress_var.set(0.0)
        self.status_var.set(f"正在启动{mode}……")
        self._log(f"开始：{mode}")

        def worker() -> None:
            try:
                result = target()
                self.root.after(0, lambda: self._finish_success(mode, result))
            except InterruptedError as exc:
                message = str(exc)
                self.root.after(0, lambda m=message: self._finish_stopped(mode, m))
            except Exception as exc:
                details = traceback.format_exc()
                self.root.after(0, lambda e=exc, d=details: self._finish_error(mode, e, d))

        self.active_thread = threading.Thread(target=worker, name=f"GameAI-{mode}", daemon=True)
        self.active_thread.start()

    def request_stop(self) -> None:
        if self.active_thread and self.active_thread.is_alive():
            self.stop_event.set()
            self.status_var.set("正在安全停止并释放鼠标按键……")
            self._log("收到停止请求。")

    def _finish_success(self, mode: str, result: dict[str, Any]) -> None:
        self._set_busy(False)
        self.progress_var.set(1.0)
        if mode == "学习":
            text = f"学习结束：{result.get('frames', 0)} 帧，{result.get('samples', 0)} 条样本。"
        elif mode == "复习":
            metrics = result.get("metrics", {})
            text = (
                f"复习完成：使用 {result.get('samples', 0)} 条样本；"
                f"平衡准确率 {metrics.get('balanced_accuracy', 0):.1%}。"
            )
        else:
            text = f"AI运行结束：处理 {result.get('frames', 0)} 帧，执行 {result.get('actions', 0)} 次动作。"
        self.status_var.set(text)
        self._log(text)
        for key in ("session_dir", "model_path", "report_path", "run_dir"):
            if result.get(key):
                self._log(f"{key}: {result[key]}")
        self.mode = None

    def _finish_stopped(self, mode: str, message: str) -> None:
        self._set_busy(False)
        self.status_var.set(message or f"{mode}已停止。")
        self._log(message or f"{mode}已停止。")
        self.mode = None

    def _finish_error(self, mode: str, exc: Exception, details: str) -> None:
        self._set_busy(False)
        self.status_var.set(f"{mode}失败：{exc}")
        self._log(f"错误：{exc}\n{details}")
        messagebox.showerror(f"{mode}失败", str(exc))
        self.mode = None

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        for widget in (
            self.learn_button,
            self.review_button,
            self.train_button,
            self.refresh_button,
            self.folder_button,
            self.folder_entry,
        ):
            try:
                widget.configure(state=state)
            except tk.TclError:
                pass
        self.window_combo.configure(state="disabled" if busy else "readonly")
        self.stop_button.configure(state="normal" if busy else "disabled")

    def _set_status_threadsafe(self, text: str) -> None:
        self.root.after(0, lambda: self.status_var.set(text))

    def _set_progress_threadsafe(self, value: float) -> None:
        self.root.after(0, lambda: self.progress_var.set(clamp(float(value), 0.0, 1.0)))

    def _log(self, text: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{timestamp}] {text}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _show_error(self, title: str, exc: Exception) -> None:
        self._log(f"{title}: {exc}")
        messagebox.showerror(title, str(exc))

    def _on_close(self) -> None:
        if self.active_thread and self.active_thread.is_alive():
            self.request_stop()
            self.root.after(250, self._wait_then_close)
        else:
            self.root.destroy()

    def _wait_then_close(self) -> None:
        if self.active_thread and self.active_thread.is_alive():
            self.root.after(250, self._wait_then_close)
        else:
            self.root.destroy()


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("此程序仅支持 Windows 11/Windows 10。")
    set_dpi_awareness()
    root = tk.Tk()
    GameAIApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
