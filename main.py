import os
import ast
import sys
import json
import time
import math
import uuid
import random
import hashlib
import threading
import queue
import multiprocessing
import traceback
import statistics
import sqlite3
import zlib
import base64
import io
import tokenize
import tempfile
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path
from collections import deque,Counter,defaultdict,OrderedDict
import tkinter as tk
from tkinter import ttk
import ctypes
from ctypes import wintypes
APP_NAME="UniversalGameAI"
FORMAT_VERSION=6
FEATURE_W=64
FEATURE_H=36
PREVIEW_W=320
PREVIEW_H=180
FEATURE_CHANNELS=5
PIXELS=FEATURE_W*FEATURE_H
FEATURE_LEN=PIXELS*FEATURE_CHANNELS
COARSE_W=16
COARSE_H=9
COARSE_LEN=COARSE_W*COARSE_H*FEATURE_CHANNELS
SQUARED_DIFF=tuple(value*value for value in range(-255,256))
FEATURE_ALGORITHM_VERSION=4
ACTION_ALGORITHM_VERSION=6
DATABASE_SCHEMA_VERSION=7
MODEL_SCHEMA_VERSION=1
MAX_SAMPLES=1500
MAX_PROTOTYPES=320
SUPPORTED_BUTTONS={"left","right","middle"}
SUPPORTED_KINDS={"no_op","click","double_click","long_press","drag","scroll_v","scroll_h","move","hover"}
BASIC_SAFE_FAMILIES={"no_op","click|left","move","hover"}
REPEAT_POLICIES={"one_shot","repeatable","hold_until_change","rate_limited"}
MODE_IDLE="IDLE"
MODE_STARTING="STARTING"
MODE_RUNNING="RUNNING"
MODE_STOPPING="STOPPING"
MODE_STATES={MODE_IDLE,MODE_STARTING,MODE_RUNNING,MODE_STOPPING}
ASK_CANVAS_W=672
ASK_CANVAS_H=378
ASK_PREVIEW_W=640
ASK_PREVIEW_H=360
ASK_PREVIEW_X=16
ASK_PREVIEW_Y=9
CAPTURE_RETRY_DELAYS=(2.0,10.0,60.0)
INPUT_EXTRA_INFO=0x5547414932303236
TITLE_RULE_MODES={"none","contains","prefix","exact"}
WINDOW_RULE_VERSION=2
CAPTURE_BACKEND_VERSION=2
RECOVERY_BACKUP_LIMIT=1024*1024*1024
MIN_FREE_DISK=256*1024*1024
class VersionedThresholdConfig:
    version=2
    required_sessions=2
    review_min_holdout=150
    review_min_accepted=150
    ordinary_min_positive=20
    ordinary_min_sessions=2
    basic_safe_min_positive=12
    basic_safe_min_consistency=0.95
    dangerous_min_positive=50
    dangerous_min_negative=50
    dangerous_min_sessions=4
    capture_min_holdout=20
    capture_min_accuracy=0.80
    capture_max_errors=0
    scene_min_holdout=10
    scene_min_accuracy=0.75
    scene_max_errors=0
    minimum_coverage=0.80
    maximum_error_upper_95=0.02
    minimum_overall_accuracy=0.80
    maximum_dangerous_false=0
    maximum_uncovered_false_accept=0
    candidate_full_limit=18
    content_aspect_tolerance=0.015
    @classmethod
    def snapshot(cls):
        return {key:value for key,value in vars(cls).items() if not key.startswith("_") and isinstance(value,(int,float,str,bool))}
def current_build_hash():
    try:
        return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    except Exception:
        return ""
def compatibility_signature():
    return {"format_version":FORMAT_VERSION,"model_schema_version":MODEL_SCHEMA_VERSION,"feature_algorithm_version":FEATURE_ALGORITHM_VERSION,"action_algorithm_version":ACTION_ALGORITHM_VERSION,"feature_size":[FEATURE_W,FEATURE_H,FEATURE_CHANNELS],"coarse_size":[COARSE_W,COARSE_H,FEATURE_CHANNELS],"window_rule_version":WINDOW_RULE_VERSION,"capture_backend_version":CAPTURE_BACKEND_VERSION,"thresholds":VersionedThresholdConfig.snapshot()}
def compatibility_signature_from_item(item):
    if not isinstance(item,dict):
        return None
    direct=item.get("compatibility_signature")
    if isinstance(direct,dict):
        return direct
    snapshot=item.get("algorithm_snapshot")
    if not isinstance(snapshot,dict):
        return None
    nested=snapshot.get("compatibility_signature")
    if isinstance(nested,dict):
        return nested
    legacy={key:snapshot.get(key) for key in ("format_version","feature_algorithm_version","action_algorithm_version","feature_size","coarse_size","window_rule_version","capture_backend_version","thresholds")}
    legacy["model_schema_version"]=MODEL_SCHEMA_VERSION
    return legacy
def normalized_compatibility_signature(value):
    if not isinstance(value,dict):
        return None
    result=dict(value)
    result["model_schema_version"]=safe_int(result.get("model_schema_version",MODEL_SCHEMA_VERSION),MODEL_SCHEMA_VERSION)
    thresholds=dict(result.get("thresholds")) if isinstance(result.get("thresholds"),dict) else {}
    legacy_defaults={"required_sessions":2,"capture_min_holdout":20,"capture_min_accuracy":0.80,"capture_max_errors":0,"scene_min_holdout":10,"scene_min_accuracy":0.75,"scene_max_errors":0,"maximum_dangerous_false":0,"maximum_uncovered_false_accept":0}
    for key,default in legacy_defaults.items():
        thresholds.setdefault(key,default)
    current=VersionedThresholdConfig.snapshot()
    comparable=dict(thresholds)
    comparable["version"]=current["version"]
    if comparable==current:
        thresholds=current
    result["thresholds"]=thresholds
    return result
def algorithm_snapshot():
    return {"compatibility_signature":compatibility_signature(),"source_build_hash":current_build_hash()}
def evaluate_validation_thresholds(split_complete,session_count,holdout_count,accepted,coverage,overall_accuracy,error_upper_95,dangerous_false,uncovered_false_accept):
    enough=bool(split_complete and int(session_count)>=VersionedThresholdConfig.required_sessions and int(holdout_count)>=VersionedThresholdConfig.review_min_holdout and int(accepted)>=VersionedThresholdConfig.review_min_accepted)
    global_pass=bool(float(coverage)>=VersionedThresholdConfig.minimum_coverage and float(overall_accuracy)>=VersionedThresholdConfig.minimum_overall_accuracy and float(error_upper_95)<=VersionedThresholdConfig.maximum_error_upper_95 and int(dangerous_false)<=VersionedThresholdConfig.maximum_dangerous_false and int(uncovered_false_accept)<=VersionedThresholdConfig.maximum_uncovered_false_accept)
    return enough,global_pass
def own_injected_event(flags,extra_info,mask):
    return bool(int(flags)&int(mask) and int(extra_info)==INPUT_EXTRA_INFO)
def normalized_rect(rect,container):
    x,y,w,h=[float(value) for value in rect]
    cx,cy,cw,ch=[float(value) for value in container]
    if min(cw,ch,w,h)<=0:
        raise ValueError("矩形尺寸无效")
    left=max(0.0,min(1.0,(x-cx)/cw)); top=max(0.0,min(1.0,(y-cy)/ch)); right=max(left,min(1.0,(x+w-cx)/cw)); bottom=max(top,min(1.0,(y+h-cy)/ch))
    if right-left<0.02 or bottom-top<0.02:
        raise ValueError("内容区域过小")
    return [round(left,8),round(top,8),round(right-left,8),round(bottom-top,8)]
def apply_normalized_rect(container,norm):
    cx,cy,cw,ch=[int(value) for value in container]
    if not isinstance(norm,(list,tuple)) or len(norm)!=4:
        norm=[0.0,0.0,1.0,1.0]
    left=max(0.0,min(1.0,safe_float(norm[0],0.0))); top=max(0.0,min(1.0,safe_float(norm[1],0.0))); width=max(0.02,min(1.0-left,safe_float(norm[2],1.0))); height=max(0.02,min(1.0-top,safe_float(norm[3],1.0)))
    x=cx+round(left*cw); y=cy+round(top*ch); right=cx+round((left+width)*cw); bottom=cy+round((top+height)*ch)
    return x,y,max(2,right-x),max(2,bottom-y)
def visual_perceptual_hash(feature):
    source=feature_bytes(feature)
    plane=source[:PIXELS]
    values=[]
    for oy in range(8):
        sy=min(FEATURE_H-1,(2*oy+1)*FEATURE_H//16)
        row=[]
        for ox in range(9):
            sx=min(FEATURE_W-1,(2*ox+1)*FEATURE_W//18)
            row.append(plane[sy*FEATURE_W+sx])
        values.extend(1 if row[index+1]>=row[index] else 0 for index in range(8))
    value=0
    for bit in values:
        value=(value<<1)|bit
    return format(value,"016x")
def visual_scene_key(item):
    feature=feature_bytes(item.get("f"))
    plane=feature[:PIXELS]
    mean=sum(plane)/max(1,len(plane))
    edges=feature[3*PIXELS:4*PIXELS]
    edge_mean=sum(edges)/max(1,len(edges))
    context=temporal_from_context(item.get("context",{}))
    motion=sum(context.get("recent_frame_deltas",[]))/max(1,len(context.get("recent_frame_deltas",[])))
    return "L"+str(min(5,int(mean//43)))+"|E"+str(min(5,int(edge_mean//43)))+"|M"+str(min(5,int(motion//120)))
class TaskAgentPolicy:
    def __init__(self,profile):
        self.profile=dict(profile) if isinstance(profile,dict) else {}
        self.allowed=set(str(value) for value in self.profile.get("allowed_families",[]))
        self.max_failures=max(1,safe_int(self.profile.get("max_consecutive_failures",3),3,1,20))
        self.failures=0
        self.history=deque(maxlen=128)
    def allowed_action(self,action):
        family=action_family_key(action)
        return bool(family and family in self.allowed)
    def state_hash(self,feature):
        return visual_perceptual_hash(feature)
    def classify(self,feature):
        value=self.state_hash(feature)
        if value in set(self.profile.get("success_states",[])):
            return "success",safe_float(self.profile.get("success_reward",1.0),1.0)
        if value in set(self.profile.get("failure_states",[])):
            return "failure",safe_float(self.profile.get("failure_reward",-1.0),-1.0)
        return "neutral",0.0
    def register(self,before,action,after,changed):
        before_hash=self.state_hash(before); after_hash=self.state_hash(after) if after is not None else ""
        state,reward=self.classify(after if after is not None else before)
        if state=="failure" or not changed:
            self.failures+=1
        else:
            self.failures=0
        self.history.append({"before":before_hash,"action":action_signature(action),"after":after_hash,"state":state,"reward":reward,"changed":bool(changed)})
        return {"state":state,"reward":reward,"failures":self.failures,"stop":self.failures>=self.max_failures}
    def sequence_penalty(self,history,cluster_id,sequence_model):
        if not isinstance(sequence_model,dict):
            return 0.0
        values=[str(value) for value in history] if isinstance(history,(list,tuple,deque)) else [str(history)]
        choices={}
        depth=0
        for size in range(min(4,len(values)),0,-1):
            key=str(size)+"|"+"|".join(values[-size:])
            candidate=sequence_model.get(key,{})
            if isinstance(candidate,dict) and candidate:
                choices=candidate
                depth=size
                break
        if not choices:
            choices=sequence_model.get(str(values[-1] if values else "<START>"),{})
        if not isinstance(choices,dict) or not choices:
            return 0.0
        total=sum(max(0.0,safe_float(value,0.0)) for value in choices.values())
        probability=max(0.0,safe_float(choices.get(str(cluster_id),0.0),0.0))/max(1e-9,total)
        return (1.0-probability)*(18.0+depth*3.0)
def profile_checksum(profile):
    value=dict(profile) if isinstance(profile,dict) else {}
    value.pop("updated",None)
    return hashlib.sha256(canonical_bytes(value)).hexdigest()
def model_binding_from_samples(samples):
    paths=set(); classes=set(); norms=set(); aspects=[]; dpis=[]; methods=set()
    for item in samples:
        context=item.get("context",{}) if isinstance(item,dict) else {}
        path=os.path.normcase(str(context.get("process_path","")))
        window_class=str(context.get("window_class",""))
        norm=context.get("content_rect_norm")
        aspect=context.get("content_aspect")
        dpi=context.get("dpi")
        method=str(item.get("capture_method") or context.get("capture_method") or "")
        if path:
            paths.add(path)
        if window_class:
            classes.add(window_class)
        if isinstance(norm,(list,tuple)) and len(norm)==4:
            norms.add(tuple(round(safe_float(value,0.0),6) for value in norm))
        if finite_number(aspect) and float(aspect)>0:
            aspects.append(float(aspect))
        if finite_number(dpi) and int(dpi)>0:
            dpis.append(int(dpi))
        if method:
            methods.add(method)
    return {"process_paths":sorted(paths),"window_classes":sorted(classes),"content_rect_norms":[list(value) for value in sorted(norms)],"content_aspect_min":min(aspects) if aspects else 0.0,"content_aspect_max":max(aspects) if aspects else 0.0,"dpi_min":min(dpis) if dpis else 0,"dpi_max":max(dpis) if dpis else 0,"capture_methods":sorted(methods),"window_rule_version":WINDOW_RULE_VERSION,"capture_backend_version":CAPTURE_BACKEND_VERSION}
class ThreadLocalSQLite:
    def __init__(self,path,read_only=False):
        self.path=Path(path)
        self.read_only=bool(read_only)
        self.lock=threading.RLock()
        self.connections={}
    def _new(self):
        if self.read_only:
            connection=sqlite3.connect("file:"+self.path.as_posix()+"?mode=ro",uri=True,timeout=1.0,check_same_thread=False)
        else:
            connection=sqlite3.connect(str(self.path),timeout=3.0,check_same_thread=False)
        connection.row_factory=sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=3000")
        if not self.read_only:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=NORMAL")
            connection.execute("PRAGMA temp_store=MEMORY")
        return connection
    def current(self):
        key=threading.get_ident()
        with self.lock:
            connection=self.connections.get(key)
            if connection is None:
                connection=self._new()
                self.connections[key]=connection
            return connection
    def execute(self,*args,**kwargs):
        return self.current().execute(*args,**kwargs)
    def executemany(self,*args,**kwargs):
        return self.current().executemany(*args,**kwargs)
    def commit(self):
        return self.current().commit()
    def rollback(self):
        return self.current().rollback()
    def __enter__(self):
        self.current().__enter__()
        return self
    def __exit__(self,exc_type,exc_value,exc_traceback):
        return self.current().__exit__(exc_type,exc_value,exc_traceback)
    def close_current_thread(self):
        key=threading.get_ident()
        with self.lock:
            connection=self.connections.pop(key,None)
        if connection is None:
            return False
        try:
            connection.close()
            return True
        except Exception:
            return False
    def connection_count(self):
        with self.lock:
            return len(self.connections)
    def close(self):
        with self.lock:
            values=list(self.connections.values())
            self.connections.clear()
        for connection in values:
            try:
                connection.close()
            except Exception:
                pass
class POINT(ctypes.Structure):
    _fields_=[("x",wintypes.LONG),("y",wintypes.LONG)]
class RECT(ctypes.Structure):
    _fields_=[("left",wintypes.LONG),("top",wintypes.LONG),("right",wintypes.LONG),("bottom",wintypes.LONG)]
class MSG(ctypes.Structure):
    _fields_=[("hwnd",wintypes.HWND),("message",wintypes.UINT),("wParam",wintypes.WPARAM),("lParam",wintypes.LPARAM),("time",wintypes.DWORD),("pt",POINT)]
class BITMAPINFOHEADER(ctypes.Structure):
    _fields_=[("biSize",wintypes.DWORD),("biWidth",wintypes.LONG),("biHeight",wintypes.LONG),("biPlanes",wintypes.WORD),("biBitCount",wintypes.WORD),("biCompression",wintypes.DWORD),("biSizeImage",wintypes.DWORD),("biXPelsPerMeter",wintypes.LONG),("biYPelsPerMeter",wintypes.LONG),("biClrUsed",wintypes.DWORD),("biClrImportant",wintypes.DWORD)]
class BITMAPINFO(ctypes.Structure):
    _fields_=[("bmiHeader",BITMAPINFOHEADER),("bmiColors",wintypes.DWORD*3)]
ULONG_PTR=ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p)==8 else ctypes.c_ulong
class MOUSEINPUT(ctypes.Structure):
    _fields_=[("dx",wintypes.LONG),("dy",wintypes.LONG),("mouseData",wintypes.DWORD),("dwFlags",wintypes.DWORD),("time",wintypes.DWORD),("dwExtraInfo",ULONG_PTR)]
class INPUTUNION(ctypes.Union):
    _fields_=[("mi",MOUSEINPUT)]
class INPUT(ctypes.Structure):
    _anonymous_=("u",)
    _fields_=[("type",wintypes.DWORD),("u",INPUTUNION)]
class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_=[("pt",POINT),("mouseData",wintypes.DWORD),("flags",wintypes.DWORD),("time",wintypes.DWORD),("dwExtraInfo",ULONG_PTR)]
class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_=[("vkCode",wintypes.DWORD),("scanCode",wintypes.DWORD),("flags",wintypes.DWORD),("time",wintypes.DWORD),("dwExtraInfo",ULONG_PTR)]
class SID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_=[("Sid",ctypes.c_void_p),("Attributes",wintypes.DWORD)]
class TOKEN_MANDATORY_LABEL(ctypes.Structure):
    _fields_=[("Label",SID_AND_ATTRIBUTES)]
class GUID(ctypes.Structure):
    _fields_=[("Data1",ctypes.c_uint32),("Data2",ctypes.c_uint16),("Data3",ctypes.c_uint16),("Data4",ctypes.c_ubyte*8)]
class FILETIME(ctypes.Structure):
    _fields_=[("dwLowDateTime",wintypes.DWORD),("dwHighDateTime",wintypes.DWORD)]
class SIZEINT32(ctypes.Structure):
    _fields_=[("Width",ctypes.c_int32),("Height",ctypes.c_int32)]
class DXGI_SAMPLE_DESC(ctypes.Structure):
    _fields_=[("Count",ctypes.c_uint32),("Quality",ctypes.c_uint32)]
class D3D11_TEXTURE2D_DESC(ctypes.Structure):
    _fields_=[("Width",ctypes.c_uint32),("Height",ctypes.c_uint32),("MipLevels",ctypes.c_uint32),("ArraySize",ctypes.c_uint32),("Format",ctypes.c_uint32),("SampleDesc",DXGI_SAMPLE_DESC),("Usage",ctypes.c_uint32),("BindFlags",ctypes.c_uint32),("CPUAccessFlags",ctypes.c_uint32),("MiscFlags",ctypes.c_uint32)]
class D3D11_MAPPED_SUBRESOURCE(ctypes.Structure):
    _fields_=[("pData",ctypes.c_void_p),("RowPitch",ctypes.c_uint32),("DepthPitch",ctypes.c_uint32)]
def guid(value):
    item=uuid.UUID(str(value))
    data=item.bytes_le
    return GUID(int.from_bytes(data[0:4],"little"),int.from_bytes(data[4:6],"little"),int.from_bytes(data[6:8],"little"),(ctypes.c_ubyte*8).from_buffer_copy(data[8:16]))
class TargetUnavailable(RuntimeError):
    pass
class CaptureUnavailable(RuntimeError):
    pass
class InputStopped(RuntimeError):
    pass
class ModeResult:
    def __init__(self,status,summary,details=None):
        value=str(status)
        if value not in {"completed","stopped","failed"}:
            raise ValueError("模式结果状态无效")
        self.status=value
        self.summary=str(summary)
        self.details=dict(details) if isinstance(details,dict) else {}
class ModeLifecycle:
    def __init__(self):
        self.lock=threading.RLock()
        self.state=MODE_IDLE
        self.name=None
        self.stop_event=None
        self.requested_status="stopped"
        self.reason=""
    def begin(self,name):
        with self.lock:
            if self.state!=MODE_IDLE:
                raise RuntimeError("当前已有操作正在运行，请先停止")
            self.state=MODE_STARTING
            self.name=str(name)
            self.stop_event=threading.Event()
            self.requested_status="completed"
            self.reason=""
            return self.stop_event
    def mark_running(self):
        with self.lock:
            if self.state==MODE_STARTING:
                self.state=MODE_RUNNING
            return self.state
    def request_stop(self,status="stopped",reason=""):
        priority={"completed":0,"stopped":1,"failed":2}
        with self.lock:
            if self.state==MODE_IDLE:
                return False
            value=str(status) if str(status) in priority else "stopped"
            if priority[value]>=priority.get(self.requested_status,0):
                self.requested_status=value
                if reason:
                    self.reason=str(reason)
            elif reason and not self.reason:
                self.reason=str(reason)
            self.state=MODE_STOPPING
            if self.stop_event is not None:
                self.stop_event.set()
            return True
    def mark_stopping(self,status=None,reason=""):
        return self.request_stop(status or self.requested_status,reason)
    def finish(self):
        with self.lock:
            self.state=MODE_IDLE
            self.name=None
            self.stop_event=None
            self.requested_status="stopped"
            self.reason=""
    def snapshot(self):
        with self.lock:
            return self.state,self.name,self.stop_event,self.requested_status,self.reason
class StrictInputIsolation:
    def __init__(self,stop_event):
        self.stop_event=stop_event
        self.lock=threading.Lock()
        self.kind=""
        self.stamp=0.0
    def signal(self,kind,stamp=None):
        with self.lock:
            if not self.kind:
                self.kind=str(kind)
                self.stamp=float(time.monotonic() if stamp is None else stamp)
            if self.stop_event is not None:
                self.stop_event.set()
    def tripped(self):
        with self.lock:
            return bool(self.kind)
    def can_automate(self):
        return not self.tripped() and self.stop_event is not None and not self.stop_event.is_set()
class PreviewCoordinateMapper:
    canvas_width=ASK_CANVAS_W
    canvas_height=ASK_CANVAS_H
    preview_width=ASK_PREVIEW_W
    preview_height=ASK_PREVIEW_H
    offset_x=ASK_PREVIEW_X
    offset_y=ASK_PREVIEW_Y
    @classmethod
    def to_normalized(cls,x,y):
        px=float(x)
        py=float(y)
        if px<cls.offset_x or py<cls.offset_y or px>cls.offset_x+cls.preview_width-1 or py>cls.offset_y+cls.preview_height-1:
            return None
        return [(px-cls.offset_x)/max(1,cls.preview_width-1),(py-cls.offset_y)/max(1,cls.preview_height-1)]
    @classmethod
    def to_canvas(cls,point):
        return [cls.offset_x+max(0.0,min(1.0,float(point[0])))*(cls.preview_width-1),cls.offset_y+max(0.0,min(1.0,float(point[1])))*(cls.preview_height-1)]
class ResourceShutdownBarrier:
    def __init__(self,label,timeout=4.0):
        self.label=str(label)
        self.timeout=max(0.5,float(timeout))
        self.entries=[]
        self.deadline=None
        self.forced=[]
        self.errors=[]
        self.lock=threading.RLock()
    def add(self,name,stopper,alive,forcer=None):
        with self.lock:
            self.entries.append({"name":str(name),"stop":stopper,"alive":alive,"force":forcer})
    def request_stop(self):
        with self.lock:
            if self.deadline is None:
                self.deadline=time.monotonic()+self.timeout
            entries=list(self.entries)
        for entry in entries:
            try:
                entry["stop"](0.0)
            except Exception as error:
                self.errors.append(entry["name"]+"："+str(error))
    def poll(self):
        self.request_stop()
        now=time.monotonic()
        with self.lock:
            entries=list(self.entries)
        remaining=[]
        for entry in entries:
            alive=True
            try:
                alive=bool(entry["alive"]())
            except Exception as error:
                self.errors.append(entry["name"]+"状态："+str(error))
            if alive:
                try:
                    entry["stop"](0.0)
                except Exception as error:
                    self.errors.append(entry["name"]+"停止："+str(error))
                try:
                    alive=bool(entry["alive"]())
                except Exception:
                    alive=True
            if alive and self.deadline is not None and now>=self.deadline and entry.get("force") is not None:
                try:
                    entry["force"]()
                    self.forced.append(entry["name"])
                except Exception as error:
                    self.errors.append(entry["name"]+"强制停止："+str(error))
                try:
                    alive=bool(entry["alive"]())
                except Exception:
                    alive=True
            if alive:
                remaining.append(entry)
        with self.lock:
            self.entries=remaining
        return not remaining
    def pending_names(self):
        with self.lock:
            return [entry["name"] for entry in self.entries]
def finite_number(value):
    try:
        return math.isfinite(float(value))
    except Exception:
        return False
def safe_int(value,default=0,minimum=None,maximum=None):
    try:
        number=int(value)
    except (TypeError,ValueError,OverflowError):
        number=int(default)
    if minimum is not None:
        number=max(int(minimum),number)
    if maximum is not None:
        number=min(int(maximum),number)
    return number
def safe_float(value,default=0.0,minimum=None,maximum=None):
    try:
        number=float(value)
        if not math.isfinite(number):
            raise ValueError("非有限数")
    except (TypeError,ValueError,OverflowError):
        number=float(default)
    if minimum is not None:
        number=max(float(minimum),number)
    if maximum is not None:
        number=min(float(maximum),number)
    return number
def bounded_decompress(data,maximum):
    raw=bytes(data)
    limit=max(1,safe_int(maximum,1,1,268435456))
    decoder=zlib.decompressobj()
    result=decoder.decompress(raw,limit+1)
    if len(result)>limit or decoder.unconsumed_tail or not decoder.eof:
        raise ValueError("压缩数据超过安全上限或已损坏")
    tail=decoder.flush()
    if tail:
        result+=tail
    if len(result)>limit:
        raise ValueError("压缩数据超过安全上限")
    return result
def canonical_bytes(data):
    return json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
def add_checksum(data):
    result=dict(data)
    result.pop("checksum",None)
    result["checksum"]=hashlib.sha256(canonical_bytes(result)).hexdigest()
    return result
def verify_checksum(data):
    if not isinstance(data,dict) or not isinstance(data.get("checksum"),str):
        return False
    expected=data.get("checksum")
    item=dict(data)
    item.pop("checksum",None)
    return hashlib.sha256(canonical_bytes(item)).hexdigest()==expected
class LightweightLogger:
    def __init__(self,path):
        self.path=Path(path)
        self.lock=threading.RLock()
    def write(self,code,error=None,thread_name=None,mode=None,game_id=None,window_identity=None,details=None):
        exception_type=type(error).__name__ if isinstance(error,BaseException) else ""
        message=str(error) if error is not None else ""
        stack=""
        if isinstance(error,BaseException):
            stack="".join(traceback.format_exception(type(error),error,error.__traceback__))[-6000:]
        record={"time":time.time(),"code":str(code),"thread":str(thread_name or threading.current_thread().name),"mode":str(mode or ""),"game_id":str(game_id or ""),"window_identity":window_identity if isinstance(window_identity,dict) else {},"exception_type":exception_type,"message":message[:2000],"stack":stack,"details":details if isinstance(details,dict) else {}}
        try:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            line=json.dumps(record,ensure_ascii=False,separators=(",",":"))+"\n"
            with self.lock,self.path.open("a",encoding="utf-8") as handle:
                handle.write(line)
            return True
        except Exception:
            return False
def binomial_error_upper(errors,total,confidence=0.95):
    n=max(0,int(total))
    k=max(0,min(n,int(errors)))
    if n<1:
        return 1.0
    if k==0:
        return 1.0-(1.0-float(confidence))**(1.0/n)
    z=1.6448536269514722 if confidence<=0.95 else 1.959963984540054
    phat=k/n
    denominator=1.0+z*z/n
    center=(phat+z*z/(2.0*n))/denominator
    radius=z*math.sqrt(phat*(1.0-phat)/n+z*z/(4.0*n*n))/denominator
    return min(1.0,center+radius)
def checksum_set(samples):
    return {str(item.get("checksum","")) for item in samples if str(item.get("checksum",""))}
def assert_disjoint_checksums(train,holdout):
    overlap=checksum_set(train)&checksum_set(holdout)
    if overlap:
        raise RuntimeError("训练集与留出集checksum发生重叠："+str(len(overlap)))
    return True
def quantile(values,q):
    if not values:
        return 0.0
    ordered=sorted(float(x) for x in values)
    if len(ordered)==1:
        return ordered[0]
    pos=(len(ordered)-1)*q
    low=int(math.floor(pos))
    high=int(math.ceil(pos))
    if low==high:
        return ordered[low]
    part=pos-low
    return ordered[low]*(1.0-part)+ordered[high]*part
def path_length(path):
    total=0.0
    for a,b in zip(path,path[1:]):
        total+=math.hypot(float(b[0])-float(a[0]),float(b[1])-float(a[1]))
    return total
def direction_changes(path):
    if len(path)<3:
        return 0
    changes=0
    previous=None
    for a,b in zip(path,path[1:]):
        dx=float(b[0])-float(a[0])
        dy=float(b[1])-float(a[1])
        if abs(dx)+abs(dy)<0.002:
            continue
        angle=math.atan2(dy,dx)
        if previous is not None:
            delta=abs((angle-previous+math.pi)%(2*math.pi)-math.pi)
            if delta>math.radians(35):
                changes+=1
        previous=angle
    return changes
def resample_path(path,count=16):
    clean=[]
    for point in path or []:
        if isinstance(point,(list,tuple)) and len(point)>=2 and finite_number(point[0]) and finite_number(point[1]):
            clean.append([max(0.0,min(1.0,float(point[0]))),max(0.0,min(1.0,float(point[1])))])
    if not clean:
        return []
    if len(clean)==1:
        return [[round(clean[0][0],5),round(clean[0][1],5)] for _ in range(count)]
    distances=[0.0]
    for a,b in zip(clean,clean[1:]):
        distances.append(distances[-1]+math.hypot(b[0]-a[0],b[1]-a[1]))
    total=distances[-1]
    if total<1e-9:
        return [[round(clean[0][0],5),round(clean[0][1],5)] for _ in range(count)]
    result=[]
    segment=0
    for index in range(count):
        target=total*index/(count-1)
        while segment+1<len(distances) and distances[segment+1]<target:
            segment+=1
        if segment+1>=len(clean):
            point=clean[-1]
        else:
            span=max(1e-9,distances[segment+1]-distances[segment])
            ratio=(target-distances[segment])/span
            point=[clean[segment][0]+(clean[segment+1][0]-clean[segment][0])*ratio,clean[segment][1]+(clean[segment+1][1]-clean[segment][1])*ratio]
        result.append([round(point[0],5),round(point[1],5)])
    return result
def normalize_action(action):
    try:
        if not isinstance(action,dict):
            return None
        kind=str(action.get("kind",""))
        if kind not in SUPPORTED_KINDS:
            return None
        result={"kind":kind}
        if kind=="no_op":
            result["duration"]=round(max(0.05,min(3.0,float(action.get("duration",0.35)))),3)
            return result
        if kind in {"scroll_v","scroll_h"}:
            delta=int(action.get("delta",0))
            if delta==0:
                return None
            result["delta"]=max(-960,min(960,delta))
            point=resample_path(action.get("path") or [[0.5,0.5]],16)
            if not point:
                return None
            result["path"]=point
            result["duration"]=round(max(0.03,min(1.0,float(action.get("duration",0.08)))),3)
            return result
        path=resample_path(action.get("path"),16)
        if not path:
            return None
        result["path"]=path
        result["duration"]=round(max(0.03,min(3.0,float(action.get("duration",0.1)))),3)
        if kind in {"click","double_click","long_press","drag"}:
            button=str(action.get("button","left"))
            if button not in SUPPORTED_BUTTONS:
                return None
            result["button"]=button
        return result
    except (TypeError,ValueError,OverflowError):
        return None
def action_family_key(action):
    item=normalize_action(action)
    if not item:
        return ""
    kind=item["kind"]
    if kind in {"click","double_click","long_press","drag"}:
        return kind+"|"+item.get("button","left")
    if kind in {"scroll_v","scroll_h"}:
        return kind+"|"+str(1 if item["delta"]>0 else -1)
    return kind
def _main_direction(path):
    if not path or len(path)<2:
        return 0.0
    dx=float(path[-1][0])-float(path[0][0])
    dy=float(path[-1][1])-float(path[0][1])
    return math.atan2(dy,dx) if abs(dx)+abs(dy)>1e-9 else 0.0
def _path_rms(a,b):
    first=resample_path(a,16)
    second=resample_path(b,16)
    if not first or not second:
        return float("inf")
    return math.sqrt(sum((x[0]-y[0])**2+(x[1]-y[1])**2 for x,y in zip(first,second))/len(first))
def action_geometry_distance(first,second):
    a=normalize_action(first)
    b=normalize_action(second)
    if not a or not b or action_family_key(a)!=action_family_key(b):
        return float("inf")
    kind=a["kind"]
    duration_gap=abs(float(a.get("duration",0.1))-float(b.get("duration",0.1)))/3.0
    if kind=="no_op":
        return duration_gap
    if kind in {"scroll_v","scroll_h"}:
        pa=a["path"][-1]
        pb=b["path"][-1]
        point_gap=math.hypot(pa[0]-pb[0],pa[1]-pb[1])
        tier_a=min(8,max(1,round(abs(a["delta"])/120)))
        tier_b=min(8,max(1,round(abs(b["delta"])/120)))
        return 0.55*point_gap+0.35*abs(tier_a-tier_b)/7.0+0.10*duration_gap
    pa=a["path"]
    pb=b["path"]
    end_gap=math.hypot(pa[-1][0]-pb[-1][0],pa[-1][1]-pb[-1][1])
    if kind in {"click","double_click","long_press","hover"}:
        return 0.92*end_gap+0.08*duration_gap
    start_gap=math.hypot(pa[0][0]-pb[0][0],pa[0][1]-pb[0][1])
    path_gap=_path_rms(pa,pb)
    length_gap=abs(path_length(pa)-path_length(pb))
    angle_gap=abs((_main_direction(pa)-_main_direction(pb)+math.pi)%(2*math.pi)-math.pi)/math.pi
    if kind=="drag":
        return 0.24*start_gap+0.30*end_gap+0.25*path_gap+0.11*length_gap+0.07*angle_gap+0.03*duration_gap
    if kind=="move":
        return 0.18*start_gap+0.28*end_gap+0.32*path_gap+0.12*length_gap+0.08*angle_gap+0.02*duration_gap
    return end_gap
def action_cluster_limit(action):
    kind=normalize_action(action)["kind"]
    return {"no_op":0.22,"click":0.075,"double_click":0.085,"long_press":0.09,"hover":0.085,"drag":0.16,"move":0.18,"scroll_v":0.16,"scroll_h":0.16}.get(kind,0.1)
def action_signature(action):
    item=normalize_action(action)
    if not item:
        return ""
    kind=item["kind"]
    family=action_family_key(item)
    if kind=="no_op":
        return family
    if kind in {"scroll_v","scroll_h"}:
        point=item["path"][-1]
        tier=min(8,max(1,round(abs(item["delta"])/120)))
        return "|".join([family,str(tier),str(int(round(point[0]*12))),str(int(round(point[1]*8)))])
    path=item["path"]
    end=path[-1]
    if kind in {"click","double_click","long_press","hover"}:
        return "|".join([family,str(int(round(end[0]*20))),str(int(round(end[1]*12)))])
    start=path[0]
    direction=int(round(((_main_direction(path)+math.pi)/(2*math.pi))*8))%8
    return "|".join([family,str(int(round(start[0]*12))),str(int(round(start[1]*8))),str(int(round(end[0]*12))),str(int(round(end[1]*8))),str(direction)])
def feature_valid(feature):
    if isinstance(feature,(bytes,bytearray)):
        return len(feature)==FEATURE_LEN
    return isinstance(feature,(list,tuple)) and len(feature)==FEATURE_LEN and all(finite_number(value) for value in feature)
def feature_bytes(feature):
    if not feature_valid(feature):
        raise RuntimeError("特征尺寸无效")
    if isinstance(feature,bytes):
        return feature
    return bytes(int(max(0,min(255,round(float(value))))) for value in feature)
def gray_valid(gray):
    return isinstance(gray,(bytes,bytearray,list,tuple)) and len(gray)==PIXELS
def gray_bytes(gray):
    if not gray_valid(gray):
        return None
    if isinstance(gray,bytes):
        return gray
    return bytes(int(max(0,min(255,round(float(value))))) for value in gray)
def rgb_valid(rgb):
    return isinstance(rgb,(bytes,bytearray,list,tuple)) and len(rgb)==PIXELS*3
def rgb_bytes(rgb):
    if not rgb_valid(rgb):
        return None
    if isinstance(rgb,bytes):
        return rgb
    return bytes(int(max(0,min(255,round(float(value))))) for value in rgb)
def _pool_channel(source,offset,src_w,src_h,out_w,out_h):
    result=[]
    for oy in range(out_h):
        y0=oy*src_h//out_h
        y1=max(y0+1,(oy+1)*src_h//out_h)
        for ox in range(out_w):
            x0=ox*src_w//out_w
            x1=max(x0+1,(ox+1)*src_w//out_w)
            total=0
            count=0
            for y in range(y0,min(src_h,y1)):
                row=offset+y*src_w
                for x in range(x0,min(src_w,x1)):
                    total+=source[row+x]
                    count+=1
            result.append(round(total/max(1,count)))
    return result
def coarse_feature(feature):
    source=feature_bytes(feature)
    result=[]
    for channel in range(FEATURE_CHANNELS):
        result.extend(_pool_channel(source,channel*PIXELS,FEATURE_W,FEATURE_H,COARSE_W,COARSE_H))
    return bytes(result)
def coarse_distance(a,b):
    if not isinstance(a,(bytes,bytearray)) or not isinstance(b,(bytes,bytearray)) or len(a)!=len(b) or not a:
        return float("inf")
    return sum((int(x)-int(y))**2 for x,y in zip(a,b))/len(a)
def feature_distance(a,b):
    if not feature_valid(a) or not feature_valid(b):
        return float("inf")
    first=memoryview(feature_bytes(a))
    second=memoryview(feature_bytes(b))
    weights=(0.30,0.19,0.19,0.22,0.10)
    total=0.0
    for channel,weight in enumerate(weights):
        offset=channel*PIXELS
        value=0
        for index in range(offset,offset+PIXELS):
            value+=SQUARED_DIFF[int(first[index])-int(second[index])+255]
        total+=weight*value/PIXELS
    return total
def visual_distance(a,b):
    if not feature_valid(a) or not feature_valid(b):
        return float("inf")
    first=memoryview(feature_bytes(a))
    second=memoryview(feature_bytes(b))
    weights=(0.34,0.22,0.22,0.22)
    total=0.0
    for channel,weight in enumerate(weights):
        offset=channel*PIXELS
        value=0
        for index in range(offset,offset+PIXELS):
            value+=SQUARED_DIFF[int(first[index])-int(second[index])+255]
        total+=weight*value/PIXELS
    return total
def runtime_feature_distance(feature,prototype):
    if not feature_valid(feature) or not isinstance(prototype,dict):
        return float("inf")
    first=memoryview(feature_bytes(feature))
    second=prototype.get("feature_view")
    if not isinstance(second,memoryview) or len(second)!=FEATURE_LEN:
        if not feature_valid(prototype.get("f")):
            return float("inf")
        second=memoryview(feature_bytes(prototype["f"]))
    offsets=prototype.get("channel_offsets",(0,PIXELS,PIXELS*2,PIXELS*3,PIXELS*4))
    weights=(0.30,0.19,0.19,0.22,0.10)
    total=0.0
    for offset,weight in zip(offsets,weights):
        value=0
        for index in range(int(offset),int(offset)+PIXELS):
            value+=SQUARED_DIFF[int(first[index])-int(second[index])+255]
        total+=weight*value/PIXELS
    return total
def upgrade_feature(feature,version):
    try:
        raw=bytes(feature)
        if int(version)==FEATURE_ALGORITHM_VERSION and len(raw)==FEATURE_LEN:
            return raw
        if int(version)==3 and len(raw)==48*27*3:
            old_w=48
            old_h=27
            old_pixels=old_w*old_h
            channels=[]
            for channel in range(3):
                source=raw[channel*old_pixels:(channel+1)*old_pixels]
                expanded=[]
                for y in range(FEATURE_H):
                    sy=min(old_h-1,int((y+0.5)*old_h/FEATURE_H))
                    for x in range(FEATURE_W):
                        sx=min(old_w-1,int((x+0.5)*old_w/FEATURE_W))
                        expanded.append(source[sy*old_w+sx])
                channels.append(bytes(expanded))
            return channels[0]+bytes([128])*PIXELS+bytes([128])*PIXELS+channels[1]+channels[2]
    except Exception:
        return None
    return None
def upgrade_gray_image(gray,width=None,height=None):
    try:
        raw=bytes(gray)
        if len(raw)==PIXELS:
            return raw
        if width is None or height is None:
            if len(raw)==48*27:
                width,height=48,27
            else:
                return None
        result=[]
        for y in range(FEATURE_H):
            sy=min(int(height)-1,int((y+0.5)*int(height)/FEATURE_H))
            for x in range(FEATURE_W):
                sx=min(int(width)-1,int((x+0.5)*int(width)/FEATURE_W))
                result.append(raw[sy*int(width)+sx])
        return bytes(result)
    except Exception:
        return None
def preview_rgb_valid(rgb):
    return isinstance(rgb,(bytes,bytearray,list,tuple)) and len(rgb)==PREVIEW_W*PREVIEW_H*3
def preview_rgb_bytes(rgb):
    if not preview_rgb_valid(rgb):
        return None
    if isinstance(rgb,bytes):
        return rgb
    return bytes(int(max(0,min(255,round(float(value))))) for value in rgb)
def resize_rgb(rgb,src_w,src_h,out_w,out_h):
    source=bytes(rgb)
    if len(source)!=int(src_w)*int(src_h)*3 or min(int(src_w),int(src_h),int(out_w),int(out_h))<1:
        raise CaptureUnavailable("RGB画面尺寸无效")
    result=bytearray(int(out_w)*int(out_h)*3)
    for oy in range(int(out_h)):
        sy=min(int(src_h)-1,(2*oy+1)*int(src_h)//(2*int(out_h)))
        for ox in range(int(out_w)):
            sx=min(int(src_w)-1,(2*ox+1)*int(src_w)//(2*int(out_w)))
            source_index=(sy*int(src_w)+sx)*3
            target_index=(oy*int(out_w)+ox)*3
            result[target_index:target_index+3]=source[source_index:source_index+3]
    return bytes(result)
def temporal_from_context(context):
    source=context if isinstance(context,dict) else {}
    raw_deltas=source.get("recent_frame_deltas",[])
    if not isinstance(raw_deltas,(list,tuple)):
        raw_deltas=[]
    deltas=[]
    for value in raw_deltas[:4]:
        if finite_number(value):
            deltas.append(safe_float(value,0.0,0.0,5000.0))
    raw_actions=source.get("recent_actions",[])
    if not isinstance(raw_actions,(list,tuple)):
        raw_actions=[]
    actions=[]
    for value in raw_actions[:4]:
        try:
            text=str(value)
        except Exception:
            text=""
        if text:
            actions.append(text)
    cursor=source.get("cursor")
    if not isinstance(cursor,(list,tuple)) or len(cursor)<2 or not finite_number(cursor[0]) or not finite_number(cursor[1]):
        cursor=None
    else:
        cursor=[safe_float(cursor[0],0.0,0.0,1.0),safe_float(cursor[1],0.0,0.0,1.0)]
    size=source.get("window_size")
    if not isinstance(size,(list,tuple)) or len(size)<2 or not finite_number(size[0]) or not finite_number(size[1]):
        size=None
    else:
        size=[safe_int(size[0],1,1,100000),safe_int(size[1],1,1,100000)]
    recent_count=safe_int(source.get("recent_frame_count",0),0,0,1000)
    dpi=safe_int(source.get("dpi",0),0,0,10000)
    state_duration=safe_float(source.get("state_duration",0.0),0.0,0.0,60.0)
    return {"recent_frame_count":recent_count,"recent_frame_deltas":deltas,"recent_actions":actions,"previous_action_changed_frame":bool(source.get("previous_action_changed_frame",True)),"state_duration":state_duration,"cursor":cursor,"window_size":size,"dpi":dpi,"capture_method":str(source.get("capture_method","unknown")),"complete":bool(recent_count>=3 and len(deltas)>=2 and len(actions)>=2 and cursor is not None and size is not None)}
def temporal_distance(first,second):
    a=temporal_from_context(first)
    b=temporal_from_context(second)
    if not a.get("complete") or not b.get("complete"):
        return 1.0
    length=max(len(a["recent_frame_deltas"]),len(b["recent_frame_deltas"]),1)
    da=list(a["recent_frame_deltas"])+[0.0]*length
    db=list(b["recent_frame_deltas"])+[0.0]*length
    frame_gap=sum(min(1.0,abs(da[index]-db[index])/300.0) for index in range(length))/length
    actions_a=a["recent_actions"][-4:]
    actions_b=b["recent_actions"][-4:]
    action_length=max(len(actions_a),len(actions_b),1)
    action_gap=sum(1.0 for index in range(1,action_length+1) if (actions_a[-index] if index<=len(actions_a) else "")!=(actions_b[-index] if index<=len(actions_b) else ""))/action_length
    cursor_gap=math.hypot(a["cursor"][0]-b["cursor"][0],a["cursor"][1]-b["cursor"][1])/math.sqrt(2.0)
    duration_gap=min(1.0,abs(a["state_duration"]-b["state_duration"])/5.0)
    change_gap=0.0 if a["previous_action_changed_frame"]==b["previous_action_changed_frame"] else 1.0
    size_gap=0.0 if a["window_size"]==b["window_size"] else 1.0
    dpi_gap=min(1.0,abs(a["dpi"]-b["dpi"])/96.0)
    backend_gap=0.0 if a["capture_method"]==b["capture_method"] else 1.0
    return 0.25*frame_gap+0.25*action_gap+0.12*cursor_gap+0.10*duration_gap+0.08*change_gap+0.07*size_gap+0.05*dpi_gap+0.08*backend_gap
class CaptureProcessWorker:
    def __init__(self,bridge,key):
        self.bridge=bridge
        self.key=key
        self.lock=threading.RLock()
        self.retired=False
        self.timed_out=False
        self.started=time.monotonic()
        context=multiprocessing.get_context("spawn")
        self.connection,child=context.Pipe(duplex=True)
        self.process=context.Process(target=_capture_process_main,args=(child,),name="UniversalGameAI-Capture-"+str(key[1]),daemon=True)
        self.process.start()
        child.close()
    def request(self,command,timeout):
        with self.lock:
            if self.retired or not self.process.is_alive():
                raise CaptureUnavailable(str(self.key[1])+"采集进程不可用")
            try:
                self.connection.send(dict(command))
            except Exception as error:
                self.retired=True
                self.terminate()
                raise CaptureUnavailable(str(self.key[1])+"采集进程通信失败："+str(error))
            startup_grace=2.4 if time.monotonic()-self.started<3.0 else 0.0
            wait=max(0.08,float(timeout)+startup_grace)
            if not self.connection.poll(wait):
                self.timed_out=True
                self.retired=True
                self.terminate()
                raise CaptureUnavailable(str(self.key[1])+"采集超时，该采集后端已因超时禁用")
            try:
                ok,value=self.connection.recv()
            except Exception as error:
                self.retired=True
                self.terminate()
                raise CaptureUnavailable(str(self.key[1])+"采集进程异常退出："+str(error))
            if ok:
                return value
            raise CaptureUnavailable(str(value))
    def terminate(self,timeout=0.2):
        self.retired=True
        wait=max(0.0,float(timeout))
        try:
            if self.process.is_alive():
                self.process.terminate()
                if wait>0:
                    self.process.join(wait)
            if self.process.is_alive() and hasattr(self.process,"kill"):
                self.process.kill()
                if wait>0:
                    self.process.join(wait)
        except Exception:
            pass
        stopped=not self.process.is_alive()
        if stopped:
            try:
                self.connection.close()
            except Exception:
                pass
        return stopped
    def stop(self,timeout=1.0):
        with self.lock:
            if not self.retired:
                try:
                    self.connection.send(None)
                except Exception:
                    pass
            self.retired=True
            wait=max(0.0,float(timeout))
            if wait>0:
                try:
                    self.process.join(wait)
                except Exception:
                    pass
            stopped=not self.process.is_alive()
            if stopped:
                try:
                    self.connection.close()
                except Exception:
                    pass
            return stopped
class WindowsGraphicsCapture:
    def __init__(self,bridge):
        self.bridge=bridge
        self.lock=threading.RLock()
        self.sessions={}
        self.available=False
        self.error="未初始化"
        self.combase=ctypes.WinDLL("combase",use_last_error=True)
        self.d3d11=ctypes.WinDLL("d3d11",use_last_error=True)
        self.combase.RoInitialize.argtypes=[ctypes.c_uint32]
        self.combase.RoInitialize.restype=ctypes.c_long
        self.combase.RoUninitialize.argtypes=[]
        self.combase.RoUninitialize.restype=None
        self.combase.WindowsCreateString.argtypes=[wintypes.LPCWSTR,ctypes.c_uint32,ctypes.POINTER(ctypes.c_void_p)]
        self.combase.WindowsCreateString.restype=ctypes.c_long
        self.combase.WindowsDeleteString.argtypes=[ctypes.c_void_p]
        self.combase.WindowsDeleteString.restype=ctypes.c_long
        self.combase.RoGetActivationFactory.argtypes=[ctypes.c_void_p,ctypes.POINTER(GUID),ctypes.POINTER(ctypes.c_void_p)]
        self.combase.RoGetActivationFactory.restype=ctypes.c_long
        self.d3d11.D3D11CreateDevice.argtypes=[ctypes.c_void_p,ctypes.c_uint32,wintypes.HMODULE,ctypes.c_uint32,ctypes.POINTER(ctypes.c_uint32),ctypes.c_uint32,ctypes.c_uint32,ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_uint32),ctypes.POINTER(ctypes.c_void_p)]
        self.d3d11.D3D11CreateDevice.restype=ctypes.c_long
        self.d3d11.CreateDirect3D11DeviceFromDXGIDevice.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_void_p)]
        self.d3d11.CreateDirect3D11DeviceFromDXGIDevice.restype=ctypes.c_long
    def _check(self,hr,label):
        value=int(hr)
        if value<0:
            raise CaptureUnavailable(label+"失败，HRESULT=0x"+format(value&0xffffffff,"08X"))
    def _call(self,obj,index,restype,argtypes,*args):
        pointer=ctypes.c_void_p(int(obj.value if isinstance(obj,ctypes.c_void_p) else obj))
        vtable=ctypes.cast(pointer,ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        function=ctypes.WINFUNCTYPE(restype,ctypes.c_void_p,*argtypes)(vtable[index])
        return function(pointer,*args)
    def _query(self,obj,iid):
        result=ctypes.c_void_p()
        self._check(self._call(obj,0,ctypes.c_long,[ctypes.POINTER(GUID),ctypes.POINTER(ctypes.c_void_p)],ctypes.byref(iid),ctypes.byref(result)),"QueryInterface")
        return result
    def _release(self,obj):
        if obj and int(obj.value if isinstance(obj,ctypes.c_void_p) else obj):
            try:
                self._call(obj,2,ctypes.c_ulong,[])
            except Exception:
                pass
    def _close(self,obj):
        if not obj:
            return
        closable=None
        try:
            closable=self._query(obj,guid("30D5A829-7FA4-4026-83BB-D75BAE4EA99E"))
            self._check(self._call(closable,6,ctypes.c_long,[]),"关闭Windows Graphics Capture对象")
        except Exception:
            pass
        finally:
            self._release(closable)
    def _factory(self,class_name,iid):
        handle=ctypes.c_void_p()
        self._check(self.combase.WindowsCreateString(class_name,len(class_name),ctypes.byref(handle)),"创建WinRT类名")
        result=ctypes.c_void_p()
        try:
            self._check(self.combase.RoGetActivationFactory(handle,ctypes.byref(iid),ctypes.byref(result)),"获取WinRT激活工厂")
            return result
        finally:
            self.combase.WindowsDeleteString(handle)
    def _dispose_session(self,item):
        if not item:
            return
        for key in ("session","pool"):
            self._close(item.get(key))
        for key in ("staging","session","pool","capture_item","winrt_device","context","device"):
            self._release(item.get(key))
        if item.get("ro_initialized"):
            try:
                self.combase.RoUninitialize()
            except Exception:
                pass
    def _create_device(self):
        levels=(ctypes.c_uint32*4)(0xB100,0xB000,0xA100,0xA000)
        device=ctypes.c_void_p()
        context=ctypes.c_void_p()
        selected=ctypes.c_uint32()
        hr=self.d3d11.D3D11CreateDevice(None,1,None,0x20,levels,len(levels),7,ctypes.byref(device),ctypes.byref(selected),ctypes.byref(context))
        if int(hr)<0:
            hr=self.d3d11.D3D11CreateDevice(None,5,None,0x20,levels,len(levels),7,ctypes.byref(device),ctypes.byref(selected),ctypes.byref(context))
        self._check(hr,"创建D3D11设备")
        dxgi=self._query(device,guid("54EC77FA-1377-44E6-8C32-88FD5F44C84C"))
        winrt_device=ctypes.c_void_p()
        try:
            self._check(self.d3d11.CreateDirect3D11DeviceFromDXGIDevice(dxgi,ctypes.byref(winrt_device)),"创建WinRT Direct3D设备")
        finally:
            self._release(dxgi)
        return device,context,winrt_device
    def _create_session(self,hwnd,geometry):
        hr=self.combase.RoInitialize(1)
        ro_initialized=int(hr)>=0
        if int(hr)<0 and (int(hr)&0xffffffff)!=0x80010106:
            self._check(hr,"初始化WinRT")
        device=context=winrt_device=item_factory=capture_item=pool_factory=pool=session=None
        success=False
        try:
            device,context,winrt_device=self._create_device()
            item_factory=self._factory("Windows.Graphics.Capture.GraphicsCaptureItem",guid("3628E81B-3CAC-4C60-B7F4-23CE0E0C3356"))
            capture_item=ctypes.c_void_p()
            item_iid=guid("79C3F95B-31F7-4EC2-A464-632EF5D30760")
            self._check(self._call(item_factory,3,ctypes.c_long,[wintypes.HWND,ctypes.POINTER(GUID),ctypes.POINTER(ctypes.c_void_p)],wintypes.HWND(hwnd),ctypes.byref(item_iid),ctypes.byref(capture_item)),"为窗口创建GraphicsCaptureItem")
            item_size=SIZEINT32()
            self._check(self._call(capture_item,7,ctypes.c_long,[ctypes.POINTER(SIZEINT32)],ctypes.byref(item_size)),"读取GraphicsCaptureItem尺寸")
            if item_size.Width<2 or item_size.Height<2:
                raise CaptureUnavailable("Windows Graphics Capture返回无效尺寸")
            pool_factory=self._factory("Windows.Graphics.Capture.Direct3D11CaptureFramePool",guid("589B103F-6BBC-5DF5-A991-02E28B3B66D5"))
            pool=ctypes.c_void_p()
            size=SIZEINT32(item_size.Width,item_size.Height)
            self._check(self._call(pool_factory,6,ctypes.c_long,[ctypes.c_void_p,ctypes.c_int32,ctypes.c_int32,SIZEINT32,ctypes.POINTER(ctypes.c_void_p)],winrt_device,87,3,size,ctypes.byref(pool)),"创建自由线程捕获帧池")
            session=ctypes.c_void_p()
            self._check(self._call(pool,10,ctypes.c_long,[ctypes.c_void_p,ctypes.POINTER(ctypes.c_void_p)],capture_item,ctypes.byref(session)),"创建窗口捕获会话")
            session2=None
            try:
                session2=self._query(session,guid("2C39AE40-7D2E-5044-804E-8B6799D4CF9E"))
                self._check(self._call(session2,7,ctypes.c_long,[ctypes.c_ubyte],0),"关闭捕获光标")
            except Exception:
                pass
            finally:
                self._release(session2)
            session3=None
            try:
                session3=self._query(session,guid("F2CDD966-22AE-5EA1-9596-3A289344C3BE"))
                self._check(self._call(session3,7,ctypes.c_long,[ctypes.c_ubyte],0),"关闭捕获边框")
            except Exception:
                pass
            finally:
                self._release(session3)
            self._check(self._call(session,6,ctypes.c_long,[]),"启动Windows Graphics Capture")
            result={"thread":threading.get_ident(),"hwnd":int(hwnd),"geometry":tuple(geometry),"item_size":(int(item_size.Width),int(item_size.Height)),"device":device,"context":context,"winrt_device":winrt_device,"capture_item":capture_item,"pool":pool,"session":session,"started":time.time(),"ro_initialized":ro_initialized}
            device=context=winrt_device=capture_item=pool=session=None
            self.available=True
            self.error="可用"
            success=True
            return result
        except Exception as error:
            self.error=str(error)
            raise
        finally:
            self._release(item_factory)
            self._release(pool_factory)
            for obj in (session,pool,capture_item,winrt_device,context,device):
                self._release(obj)
            if ro_initialized and not success:
                try:
                    self.combase.RoUninitialize()
                except Exception:
                    pass
    def _session(self,hwnd,geometry):
        key=(threading.get_ident(),int(hwnd))
        with self.lock:
            item=self.sessions.get(key)
            if item and tuple(item.get("geometry",()))!=tuple(geometry):
                self._dispose_session(item)
                item=None
                self.sessions.pop(key,None)
            if item is None:
                item=self._create_session(hwnd,geometry)
                self.sessions[key]=item
            return item
    def _sample_bgra(self,pointer,row_pitch,width,height,crop,out_w,out_h):
        left,top,crop_w,crop_h=crop
        raw=ctypes.cast(pointer,ctypes.POINTER(ctypes.c_ubyte))
        result=bytearray(int(out_w)*int(out_h)*3)
        for oy in range(int(out_h)):
            sy=min(height-1,top+(2*oy+1)*crop_h//(2*int(out_h)))
            for ox in range(int(out_w)):
                sx=min(width-1,left+(2*ox+1)*crop_w//(2*int(out_w)))
                index=sy*row_pitch+sx*4
                position=(oy*int(out_w)+ox)*3
                result[position]=raw[index+2]
                result[position+1]=raw[index+1]
                result[position+2]=raw[index]
        return bytes(result)
    def capture(self,hwnd,client_rect,out_w=FEATURE_W,out_h=FEATURE_H):
        window_rect=self.bridge.window_rect(hwnd)
        geometry=tuple(client_rect)+tuple(window_rect)
        item=self._session(hwnd,geometry)
        frame=None
        deadline=time.monotonic()+0.45
        while time.monotonic()<deadline:
            candidate=ctypes.c_void_p()
            self._check(self._call(item["pool"],7,ctypes.c_long,[ctypes.POINTER(ctypes.c_void_p)],ctypes.byref(candidate)),"读取Windows Graphics Capture帧")
            if candidate.value:
                if frame is not None:
                    self._close(frame)
                    self._release(frame)
                frame=candidate
                time.sleep(0.002)
                continue
            if frame is not None:
                break
            time.sleep(0.008)
        if frame is None:
            raise CaptureUnavailable("Windows Graphics Capture暂未返回画面")
        surface=access=texture=None
        mapped=False
        staging=None
        try:
            surface=ctypes.c_void_p()
            self._check(self._call(frame,6,ctypes.c_long,[ctypes.POINTER(ctypes.c_void_p)],ctypes.byref(surface)),"读取捕获帧表面")
            access=self._query(surface,guid("A9B3D012-3DF2-4EE3-B8D1-8695F457D3C1"))
            texture=ctypes.c_void_p()
            texture_iid=guid("6F15AAF2-D208-4E89-9AB4-489535D34F9C")
            self._check(self._call(access,3,ctypes.c_long,[ctypes.POINTER(GUID),ctypes.POINTER(ctypes.c_void_p)],ctypes.byref(texture_iid),ctypes.byref(texture)),"获取D3D11纹理")
            desc=D3D11_TEXTURE2D_DESC()
            self._call(texture,10,None,[ctypes.POINTER(D3D11_TEXTURE2D_DESC)],ctypes.byref(desc))
            staging_key=(int(desc.Width),int(desc.Height),int(desc.Format))
            if item.get("staging_key")!=staging_key or not item.get("staging"):
                self._release(item.get("staging"))
                staging_desc=D3D11_TEXTURE2D_DESC(desc.Width,desc.Height,1,1,desc.Format,DXGI_SAMPLE_DESC(1,0),3,0,0x20000,0)
                created=ctypes.c_void_p()
                self._check(self._call(item["device"],5,ctypes.c_long,[ctypes.POINTER(D3D11_TEXTURE2D_DESC),ctypes.c_void_p,ctypes.POINTER(ctypes.c_void_p)],ctypes.byref(staging_desc),None,ctypes.byref(created)),"创建CPU可读捕获纹理")
                item["staging"]=created
                item["staging_key"]=staging_key
            staging=item["staging"]
            self._call(item["context"],47,None,[ctypes.c_void_p,ctypes.c_void_p],staging,texture)
            mapped_resource=D3D11_MAPPED_SUBRESOURCE()
            self._check(self._call(item["context"],14,ctypes.c_long,[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_uint32,ctypes.POINTER(D3D11_MAPPED_SUBRESOURCE)],staging,0,1,0,ctypes.byref(mapped_resource)),"映射捕获纹理")
            mapped=True
            cx,cy,cw,ch=client_rect
            wx,wy,ww,wh=window_rect
            scale_x=float(desc.Width)/max(1,ww)
            scale_y=float(desc.Height)/max(1,wh)
            left=max(0,min(int(desc.Width)-1,round((cx-wx)*scale_x)))
            top=max(0,min(int(desc.Height)-1,round((cy-wy)*scale_y)))
            crop_w=max(1,min(int(desc.Width)-left,round(cw*scale_x)))
            crop_h=max(1,min(int(desc.Height)-top,round(ch*scale_y)))
            return self._sample_bgra(mapped_resource.pData,int(mapped_resource.RowPitch),int(desc.Width),int(desc.Height),(left,top,crop_w,crop_h),int(out_w),int(out_h))
        finally:
            if mapped:
                try:
                    self._call(item["context"],15,None,[ctypes.c_void_p,ctypes.c_uint32],staging,0)
                except Exception:
                    pass
            for obj in (texture,access,surface):
                self._release(obj)
            self._close(frame)
            self._release(frame)
    def release_thread(self,thread_id=None):
        wanted=threading.get_ident() if thread_id is None else int(thread_id)
        with self.lock:
            keys=[key for key in self.sessions if key[0]==wanted]
            items=[self.sessions.pop(key) for key in keys]
        for item in items:
            self._dispose_session(item)
    def close(self):
        with self.lock:
            items=list(self.sessions.values())
            self.sessions.clear()
        for item in items:
            self._dispose_session(item)
class WinBridge:
    def __init__(self):
        if os.name!="nt":
            raise RuntimeError("本程序仅支持Windows 11")
        version=sys.getwindowsversion()
        if int(version.major)!=10 or int(version.build)<22000:
            raise RuntimeError("本程序仅支持Windows 11（系统内部版本22000或更高）")
        self.user32=ctypes.WinDLL("user32",use_last_error=True)
        self.gdi32=ctypes.WinDLL("gdi32",use_last_error=True)
        self.kernel32=ctypes.WinDLL("kernel32",use_last_error=True)
        self.advapi32=ctypes.WinDLL("advapi32",use_last_error=True)
        self._bind()
        self._bind_extra()
        self.previous_frames={}
        self.frame_lock=threading.RLock()
        self.held=set()
        self.input_lock=threading.RLock()
        self.input_blocked=True
        self.input_stop_event=None
        self.capture_health={}
        self.capture_reports={}
        self.calibrations={}
        self.capture_task_lock=threading.RLock()
        self.capture_processes={}
        self.capture_disabled={}
        self.gdi_resources={}
        self.wgc_lock=threading.RLock()
        self.wgc=None
        self.wgc_error="尚未初始化"
    def get_wgc(self):
        with self.wgc_lock:
            if self.wgc is not None:
                return self.wgc
            try:
                self.wgc=WindowsGraphicsCapture(self)
                self.wgc_error=""
                return self.wgc
            except Exception as error:
                self.wgc_error=str(error)
                raise CaptureUnavailable("Windows Graphics Capture不可用，已降级："+self.wgc_error)
    def wgc_status(self):
        with self.wgc_lock:
            if self.wgc is not None:
                return "可用"
            return "未初始化" if self.wgc_error=="尚未初始化" else "不可用，已降级："+self.wgc_error
    def _bind(self):
        self.WNDENUMPROC=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
        self.CHILDENUMPROC=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
        self.HOOKPROC=ctypes.WINFUNCTYPE(wintypes.LPARAM,ctypes.c_int,wintypes.WPARAM,wintypes.LPARAM)
        self.user32.EnumWindows.argtypes=[self.WNDENUMPROC,wintypes.LPARAM]
        self.user32.EnumWindows.restype=wintypes.BOOL
        self.user32.EnumChildWindows.argtypes=[wintypes.HWND,self.CHILDENUMPROC,wintypes.LPARAM]
        self.user32.EnumChildWindows.restype=wintypes.BOOL
        self.user32.IsWindow.argtypes=[wintypes.HWND]
        self.user32.IsWindow.restype=wintypes.BOOL
        self.user32.IsWindowVisible.argtypes=[wintypes.HWND]
        self.user32.IsWindowVisible.restype=wintypes.BOOL
        self.user32.IsIconic.argtypes=[wintypes.HWND]
        self.user32.IsIconic.restype=wintypes.BOOL
        self.user32.GetForegroundWindow.argtypes=[]
        self.user32.GetForegroundWindow.restype=wintypes.HWND
        self.user32.GetWindowTextLengthW.argtypes=[wintypes.HWND]
        self.user32.GetWindowTextLengthW.restype=ctypes.c_int
        self.user32.GetWindowTextW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
        self.user32.GetWindowTextW.restype=ctypes.c_int
        self.user32.GetClassNameW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
        self.user32.GetClassNameW.restype=ctypes.c_int
        self.user32.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
        self.user32.GetWindowThreadProcessId.restype=wintypes.DWORD
        self.user32.GetClientRect.argtypes=[wintypes.HWND,ctypes.POINTER(RECT)]
        self.user32.GetClientRect.restype=wintypes.BOOL
        self.user32.ClientToScreen.argtypes=[wintypes.HWND,ctypes.POINTER(POINT)]
        self.user32.ClientToScreen.restype=wintypes.BOOL
        self.user32.GetWindowRect.argtypes=[wintypes.HWND,ctypes.POINTER(RECT)]
        self.user32.GetWindowRect.restype=wintypes.BOOL
        if hasattr(self.user32,"GetDpiForWindow"):
            self.user32.GetDpiForWindow.argtypes=[wintypes.HWND]
            self.user32.GetDpiForWindow.restype=wintypes.UINT
        self.user32.GetCursorPos.argtypes=[ctypes.POINTER(POINT)]
        self.user32.GetCursorPos.restype=wintypes.BOOL
        self.user32.GetAsyncKeyState.argtypes=[ctypes.c_int]
        self.user32.GetAsyncKeyState.restype=wintypes.SHORT
        self.user32.SetForegroundWindow.argtypes=[wintypes.HWND]
        self.user32.SetForegroundWindow.restype=wintypes.BOOL
        self.user32.SendInput.argtypes=[wintypes.UINT,ctypes.POINTER(INPUT),ctypes.c_int]
        self.user32.SendInput.restype=wintypes.UINT
        self.user32.GetSystemMetrics.argtypes=[ctypes.c_int]
        self.user32.GetSystemMetrics.restype=ctypes.c_int
        self.user32.GetDC.argtypes=[wintypes.HWND]
        self.user32.GetDC.restype=wintypes.HDC
        self.user32.ReleaseDC.argtypes=[wintypes.HWND,wintypes.HDC]
        self.user32.ReleaseDC.restype=ctypes.c_int
        self.user32.PrintWindow.argtypes=[wintypes.HWND,wintypes.HDC,wintypes.UINT]
        self.user32.PrintWindow.restype=wintypes.BOOL
        self.user32.SetWindowsHookExW.argtypes=[ctypes.c_int,self.HOOKPROC,wintypes.HINSTANCE,wintypes.DWORD]
        self.user32.SetWindowsHookExW.restype=wintypes.HHOOK
        self.user32.CallNextHookEx.argtypes=[wintypes.HHOOK,ctypes.c_int,wintypes.WPARAM,wintypes.LPARAM]
        self.user32.CallNextHookEx.restype=wintypes.LPARAM
        self.user32.UnhookWindowsHookEx.argtypes=[wintypes.HHOOK]
        self.user32.UnhookWindowsHookEx.restype=wintypes.BOOL
        self.user32.GetMessageW.argtypes=[ctypes.POINTER(MSG),wintypes.HWND,wintypes.UINT,wintypes.UINT]
        self.user32.GetMessageW.restype=wintypes.BOOL
        self.user32.TranslateMessage.argtypes=[ctypes.POINTER(MSG)]
        self.user32.TranslateMessage.restype=wintypes.BOOL
        self.user32.DispatchMessageW.argtypes=[ctypes.POINTER(MSG)]
        self.user32.DispatchMessageW.restype=wintypes.LPARAM
        self.user32.PostThreadMessageW.argtypes=[wintypes.DWORD,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
        self.user32.PostThreadMessageW.restype=wintypes.BOOL
        self.kernel32.GetCurrentThreadId.argtypes=[]
        self.kernel32.GetCurrentThreadId.restype=wintypes.DWORD
        self.kernel32.GetModuleHandleW.argtypes=[wintypes.LPCWSTR]
        self.kernel32.GetModuleHandleW.restype=wintypes.HMODULE
        self.gdi32.CreateCompatibleDC.argtypes=[wintypes.HDC]
        self.gdi32.CreateCompatibleDC.restype=wintypes.HDC
        self.gdi32.DeleteDC.argtypes=[wintypes.HDC]
        self.gdi32.DeleteDC.restype=wintypes.BOOL
        self.gdi32.CreateDIBSection.argtypes=[wintypes.HDC,ctypes.POINTER(BITMAPINFO),wintypes.UINT,ctypes.POINTER(ctypes.c_void_p),wintypes.HANDLE,wintypes.DWORD]
        self.gdi32.CreateDIBSection.restype=wintypes.HBITMAP
        self.gdi32.SelectObject.argtypes=[wintypes.HDC,wintypes.HGDIOBJ]
        self.gdi32.SelectObject.restype=wintypes.HGDIOBJ
        self.gdi32.DeleteObject.argtypes=[wintypes.HGDIOBJ]
        self.gdi32.DeleteObject.restype=wintypes.BOOL
        self.gdi32.SetStretchBltMode.argtypes=[wintypes.HDC,ctypes.c_int]
        self.gdi32.SetStretchBltMode.restype=ctypes.c_int
        self.gdi32.StretchBlt.argtypes=[wintypes.HDC,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,wintypes.HDC,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,wintypes.DWORD]
        self.gdi32.StretchBlt.restype=wintypes.BOOL
    def _bind_extra(self):
        self.user32.WindowFromPoint.argtypes=[POINT]
        self.user32.WindowFromPoint.restype=wintypes.HWND
        self.user32.GetAncestor.argtypes=[wintypes.HWND,wintypes.UINT]
        self.user32.GetAncestor.restype=wintypes.HWND
        self.user32.GetClipCursor.argtypes=[ctypes.POINTER(RECT)]
        self.user32.GetClipCursor.restype=wintypes.BOOL
        self.user32.ClipCursor.argtypes=[ctypes.POINTER(RECT)]
        self.user32.ClipCursor.restype=wintypes.BOOL
        self.kernel32.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
        self.kernel32.OpenProcess.restype=wintypes.HANDLE
        self.kernel32.GetCurrentProcess.argtypes=[]
        self.kernel32.GetCurrentProcess.restype=wintypes.HANDLE
        self.kernel32.CloseHandle.argtypes=[wintypes.HANDLE]
        self.kernel32.CloseHandle.restype=wintypes.BOOL
        self.kernel32.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
        self.kernel32.QueryFullProcessImageNameW.restype=wintypes.BOOL
        self.kernel32.GetProcessTimes.argtypes=[wintypes.HANDLE,ctypes.POINTER(FILETIME),ctypes.POINTER(FILETIME),ctypes.POINTER(FILETIME),ctypes.POINTER(FILETIME)]
        self.kernel32.GetProcessTimes.restype=wintypes.BOOL
        self.advapi32.OpenProcessToken.argtypes=[wintypes.HANDLE,wintypes.DWORD,ctypes.POINTER(wintypes.HANDLE)]
        self.advapi32.OpenProcessToken.restype=wintypes.BOOL
        self.advapi32.GetTokenInformation.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD)]
        self.advapi32.GetTokenInformation.restype=wintypes.BOOL
        self.advapi32.GetSidSubAuthorityCount.argtypes=[ctypes.c_void_p]
        self.advapi32.GetSidSubAuthorityCount.restype=ctypes.POINTER(ctypes.c_ubyte)
        self.advapi32.GetSidSubAuthority.argtypes=[ctypes.c_void_p,wintypes.DWORD]
        self.advapi32.GetSidSubAuthority.restype=ctypes.POINTER(wintypes.DWORD)
    def _token_integrity(self,process_handle):
        token=wintypes.HANDLE()
        if not self.advapi32.OpenProcessToken(process_handle,0x0008,ctypes.byref(token)):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            needed=wintypes.DWORD()
            self.advapi32.GetTokenInformation(token,25,None,0,ctypes.byref(needed))
            if needed.value<ctypes.sizeof(TOKEN_MANDATORY_LABEL):
                raise RuntimeError("无法读取进程完整性级别")
            buffer=ctypes.create_string_buffer(needed.value)
            if not self.advapi32.GetTokenInformation(token,25,buffer,needed.value,ctypes.byref(needed)):
                raise ctypes.WinError(ctypes.get_last_error())
            label=ctypes.cast(buffer,ctypes.POINTER(TOKEN_MANDATORY_LABEL)).contents
            count=int(self.advapi32.GetSidSubAuthorityCount(label.Label.Sid).contents.value)
            if count<1:
                raise RuntimeError("进程完整性SID无效")
            return int(self.advapi32.GetSidSubAuthority(label.Label.Sid,count-1).contents.value)
        finally:
            self.kernel32.CloseHandle(token)
    def _open_process_query(self,pid):
        handle=self.kernel32.OpenProcess(0x1000,False,int(pid))
        if not handle:
            raise TargetUnavailable("无法读取目标进程身份，拒绝自动输入")
        return handle
    def process_identity_for_pid(self,pid):
        handle=self._open_process_query(pid)
        try:
            size=wintypes.DWORD(32768)
            buffer=ctypes.create_unicode_buffer(size.value)
            if not self.kernel32.QueryFullProcessImageNameW(handle,0,buffer,ctypes.byref(size)):
                raise ctypes.WinError(ctypes.get_last_error())
            path=os.path.normcase(os.path.abspath(buffer.value))
            if not path:
                raise TargetUnavailable("目标进程可执行文件路径为空")
            created=FILETIME()
            exited=FILETIME()
            kernel=FILETIME()
            user=FILETIME()
            if not self.kernel32.GetProcessTimes(handle,ctypes.byref(created),ctypes.byref(exited),ctypes.byref(kernel),ctypes.byref(user)):
                raise ctypes.WinError(ctypes.get_last_error())
            creation=(int(created.dwHighDateTime)<<32)|int(created.dwLowDateTime)
            integrity=self._token_integrity(handle)
            return {"path":path,"created":creation,"integrity":integrity}
        finally:
            self.kernel32.CloseHandle(handle)
    def process_path_for_pid(self,pid):
        return self.process_identity_for_pid(pid)["path"]
    def process_creation_for_pid(self,pid):
        return self.process_identity_for_pid(pid)["created"]
    def integrity_for_pid(self,pid):
        return self.process_identity_for_pid(pid)["integrity"]
    def current_integrity(self):
        return self._token_integrity(self.kernel32.GetCurrentProcess())
    def validate_uipi(self,target):
        target_level=self.integrity_for_pid(int(target.get("pid",0)))
        current_level=self.current_integrity()
        if target_level>current_level:
            raise TargetUnavailable("目标程序完整性级别高于本程序；请以相同权限运行，否则拒绝训练")
        expected=target.get("integrity")
        if expected is not None and int(expected)!=target_level:
            raise TargetUnavailable("目标程序完整性级别已变化，拒绝自动输入")
        return target_level
    def allow_input(self,stop_event=None):
        with self.input_lock:
            self.input_stop_event=stop_event
            self.input_blocked=False
    def block_input(self):
        with self.input_lock:
            self.input_blocked=True
            self.release_all_buttons()
    def input_allowed(self):
        with self.input_lock:
            return not self.input_blocked and not (self.input_stop_event and self.input_stop_event.is_set())
    def validate_action_point(self,target,x,y,expected_rect=(),expected_dpi=0):
        rect=self.validate_target(target,True)
        dpi=self.dpi_for_window(int(target["hwnd"]))
        if len(expected_rect)==4 and (max(abs(int(rect[index])-int(expected_rect[index])) for index in range(4))>2 or expected_dpi and abs(int(dpi)-int(expected_dpi))>1):
            raise TargetUnavailable("窗口客户区几何或DPI已变化，放弃当前动作并重新识别")
        if not (rect[0]<=int(x)<rect[0]+rect[2] and rect[1]<=int(y)<rect[1]+rect[3]):
            raise TargetUnavailable("动作坐标超出客户区")
        hit=int(self.user32.WindowFromPoint(POINT(int(x),int(y))) or 0)
        target_root=int(self.user32.GetAncestor(wintypes.HWND(int(target["hwnd"])),2) or int(target["hwnd"]))
        hit_root=int(self.user32.GetAncestor(wintypes.HWND(hit),2) or hit)
        if not hit or hit_root!=target_root:
            raise TargetUnavailable("点击点被其他顶层窗口覆盖，拒绝自动输入")
        self.validate_uipi(target)
        return rect
    def clip_to_client(self,rect):
        previous=RECT()
        if not self.user32.GetClipCursor(ctypes.byref(previous)):
            raise ctypes.WinError(ctypes.get_last_error())
        current=RECT(int(rect[0]),int(rect[1]),int(rect[0]+rect[2]),int(rect[1]+rect[3]))
        if not self.user32.ClipCursor(ctypes.byref(current)):
            raise ctypes.WinError(ctypes.get_last_error())
        return previous
    def restore_clip(self,previous):
        try:
            self.user32.ClipCursor(ctypes.byref(previous) if previous is not None else None)
        except Exception:
            pass
    def _dispose_gdi_resource(self,item):
        if not item:
            return
        try:
            if item.get("memory") and item.get("old"):
                self.gdi32.SelectObject(item["memory"],item["old"])
        except Exception:
            pass
        try:
            if item.get("bitmap"):
                self.gdi32.DeleteObject(item["bitmap"])
        except Exception:
            pass
        try:
            if item.get("memory"):
                self.gdi32.DeleteDC(item["memory"])
        except Exception:
            pass
        try:
            if item.get("source"):
                self.user32.ReleaseDC(wintypes.HWND(int(item.get("source_hwnd",0))),item["source"])
        except Exception:
            pass
    def release_capture_thread_resources(self,thread_id=None):
        wanted=threading.get_ident() if thread_id is None else int(thread_id)
        with self.capture_task_lock:
            keys=[key for key in self.gdi_resources if key[0]==wanted]
            items=[self.gdi_resources.pop(key) for key in keys]
        for item in items:
            self._dispose_gdi_resource(item)
        with self.wgc_lock:
            wgc=self.wgc
        if wgc is not None:
            try:
                wgc.release_thread(wanted)
            except Exception:
                pass
    def _gdi_resource(self,kind,source_hwnd,width,height):
        key=(threading.get_ident(),str(kind),int(source_hwnd),int(width),int(height))
        stale=[]
        with self.capture_task_lock:
            item=self.gdi_resources.get(key)
            if item:
                return item
            stale_keys=[existing for existing in self.gdi_resources if existing[:3]==key[:3] and existing!=key]
            stale=[self.gdi_resources.pop(existing) for existing in stale_keys]
        for old in stale:
            self._dispose_gdi_resource(old)
        source=self.user32.GetDC(wintypes.HWND(int(source_hwnd)))
        if not source:
            raise ctypes.WinError(ctypes.get_last_error())
        memory=bitmap=old=bits=None
        try:
            memory,bitmap,old,bits=self._make_dib(source,int(width),int(height))
            item={"source":source,"source_hwnd":int(source_hwnd),"memory":memory,"bitmap":bitmap,"old":old,"bits":bits,"width":int(width),"height":int(height)}
            source=memory=bitmap=old=bits=None
            with self.capture_task_lock:
                previous=self.gdi_resources.get(key)
                if previous:
                    self._dispose_gdi_resource(item)
                    return previous
                self.gdi_resources[key]=item
            return item
        finally:
            if source:
                self.user32.ReleaseDC(wintypes.HWND(int(source_hwnd)),source)
            if memory and old:
                self.gdi32.SelectObject(memory,old)
            if bitmap:
                self.gdi32.DeleteObject(bitmap)
            if memory:
                self.gdi32.DeleteDC(memory)
    def _capture_identity_key(self,target):
        item={"hwnd":safe_int(target.get("hwnd",0),0),"pid":safe_int(target.get("pid",0),0),"class":str(target.get("class","")),"thread":safe_int(target.get("window_thread_id",0),0),"path":os.path.normcase(str(target.get("process_path",""))),"created":safe_int(target.get("process_created",0),0),"content_rect_norm":[round(safe_float(value,0.0),6) for value in target.get("content_rect_norm",[0,0,1,1])[:4]],"window_rule_version":WINDOW_RULE_VERSION}
        return hashlib.sha256(canonical_bytes(item)).hexdigest()
    def _circuit_allows(self,key):
        with self.capture_task_lock:
            state=self.capture_disabled.get(tuple(key))
        if not state:
            return True,""
        remaining=float(state.get("next_probe",0.0))-time.monotonic()
        if remaining<=0:
            return True,"冷却结束，允许探测"
        return False,str(state.get("reason","超时"))+"，约"+str(round(remaining,1))+"秒后重试"
    def _record_backend_timeout(self,key,reason):
        with self.capture_task_lock:
            previous=dict(self.capture_disabled.get(tuple(key),{}))
            failures=safe_int(previous.get("failures",0),0)+1
            delay=0.0 if failures<2 else CAPTURE_RETRY_DELAYS[min(len(CAPTURE_RETRY_DELAYS)-1,failures-2)]
            state={"failures":failures,"next_probe":time.monotonic()+delay,"reason":str(reason),"updated":time.time()}
            self.capture_disabled[tuple(key)]=state
            return dict(state)
    def _record_backend_success(self,key):
        with self.capture_task_lock:
            self.capture_disabled.pop(tuple(key),None)
    def reset_capture_backends(self,target=None):
        identity=self._capture_identity_key(target) if isinstance(target,dict) else None
        with self.capture_task_lock:
            keys=[key for key in self.capture_disabled if identity is None or key[0]==identity]
            for key in keys:
                self.capture_disabled.pop(key,None)
            worker_items=[(key,worker) for key,worker in self.capture_processes.items() if identity is None or key[0]==identity]
        for key,worker in worker_items:
            try:
                stopped=worker.terminate(0.05)
            except Exception:
                stopped=False
            if stopped:
                with self.capture_task_lock:
                    if self.capture_processes.get(key) is worker:
                        self.capture_processes.pop(key,None)
        return len(keys)
    def stop_capture_processes(self,timeout=0.0,force=False):
        with self.capture_task_lock:
            items=list(self.capture_processes.items())
        alive=[]
        for key,worker in items:
            try:
                stopped=worker.terminate(timeout) if force else worker.stop(timeout)
            except Exception:
                stopped=False
            if stopped:
                with self.capture_task_lock:
                    if self.capture_processes.get(key) is worker:
                        self.capture_processes.pop(key,None)
            else:
                alive.append(str(key[1]))
        return alive
    def live_capture_processes(self):
        with self.capture_task_lock:
            return [str(key[1]) for key,worker in self.capture_processes.items() if worker.process.is_alive()]
    def _isolated_capture(self,key,command,timeout=0.55):
        backend_key=(str(key[0]),str(key[1]))
        allowed,reason=self._circuit_allows(backend_key)
        if not allowed:
            raise CaptureUnavailable(str(key[1])+"采集后端冷却中："+reason)
        with self.capture_task_lock:
            worker=self.capture_processes.get(backend_key)
        if worker is not None and (worker.retired or not worker.process.is_alive()):
            if worker.process.is_alive():
                worker.terminate(0.05)
            if worker.process.is_alive():
                raise CaptureUnavailable(str(key[1])+"旧采集进程正在退出，请稍后重试")
            with self.capture_task_lock:
                if self.capture_processes.get(backend_key) is worker:
                    self.capture_processes.pop(backend_key,None)
            worker=None
        if worker is None:
            created=CaptureProcessWorker(self,backend_key)
            with self.capture_task_lock:
                current=self.capture_processes.get(backend_key)
                if current is None:
                    self.capture_processes[backend_key]=created
                    worker=created
                else:
                    worker=current
            if worker is not created:
                created.terminate(0.05)
        try:
            value=worker.request(command,timeout)
            self._record_backend_success(backend_key)
            return value
        except CaptureUnavailable as error:
            if worker.timed_out:
                state=self._record_backend_timeout(backend_key,str(error))
                if not worker.process.is_alive():
                    with self.capture_task_lock:
                        if self.capture_processes.get(backend_key) is worker:
                            self.capture_processes.pop(backend_key,None)
                self.capture_reports[safe_int(command.get("hwnd",0),0)]=str(key[1])+"超时第"+str(state["failures"])+"次；"+("进入冷却" if state.get("next_probe",0)>time.monotonic() else "下次允许立即重试")
            elif worker.retired and not worker.process.is_alive():
                with self.capture_task_lock:
                    if self.capture_processes.get(backend_key) is worker:
                        self.capture_processes.pop(backend_key,None)
            raise error
    def abort_capture_processes(self):
        with self.capture_task_lock:
            items=list(self.capture_processes.items())
        stopped=True
        for key,worker in items:
            try:
                done=worker.terminate(0.2)
            except Exception:
                done=False
            stopped=done and stopped
            if done:
                with self.capture_task_lock:
                    if self.capture_processes.get(key) is worker:
                        self.capture_processes.pop(key,None)
        return stopped and not self.live_capture_processes()
    def valid(self,hwnd):
        return bool(hwnd and self.user32.IsWindow(wintypes.HWND(hwnd)))
    def class_name(self,hwnd):
        buffer=ctypes.create_unicode_buffer(512)
        if not self.user32.GetClassNameW(wintypes.HWND(hwnd),buffer,512):
            raise ctypes.WinError(ctypes.get_last_error())
        return buffer.value
    def window_thread_pid(self,hwnd):
        value=wintypes.DWORD()
        thread_id=self.user32.GetWindowThreadProcessId(wintypes.HWND(hwnd),ctypes.byref(value))
        if not thread_id:
            raise ctypes.WinError(ctypes.get_last_error())
        return int(thread_id),int(value.value)
    def pid(self,hwnd):
        return self.window_thread_pid(hwnd)[1]
    def window_title(self,hwnd):
        length=self.user32.GetWindowTextLengthW(wintypes.HWND(hwnd))
        buffer=ctypes.create_unicode_buffer(max(1,length+1))
        self.user32.GetWindowTextW(wintypes.HWND(hwnd),buffer,len(buffer))
        return buffer.value
    def target_identity(self,target):
        item=dict(target) if isinstance(target,dict) else {"hwnd":int(target)}
        hwnd=int(item.get("hwnd",0))
        if not self.valid(hwnd):
            raise TargetUnavailable("目标窗口已关闭或句柄无效")
        thread_id,pid=self.window_thread_pid(hwnd)
        rect=self.client_rect(hwnd)
        process=self.process_identity_for_pid(pid)
        dpi=self.dpi_for_window(hwnd)
        item.update({"hwnd":hwnd,"pid":pid,"class":self.class_name(hwnd),"title":self.window_title(hwnd),"window_thread_id":thread_id,"process_path":process["path"],"process_created":process["created"],"integrity":process["integrity"],"selected_rect":list(rect),"client_size":[int(rect[2]),int(rect[3])],"selected_dpi":dpi,"dpi":dpi})
        rule=item.get("title_rule")
        if not isinstance(rule,dict) or str(rule.get("mode","none")) not in TITLE_RULE_MODES:
            item["title_rule"]={"mode":"none","value":""}
        norm=item.get("content_rect_norm")
        if not isinstance(norm,(list,tuple)) or len(norm)!=4:
            item["content_rect_norm"]=[0.0,0.0,1.0,1.0]
        content=apply_normalized_rect(rect,item["content_rect_norm"])
        item["content_aspect"]=round(content[2]/max(1,content[3]),8)
        item["window_rule_version"]=WINDOW_RULE_VERSION
        return item
    def enum_windows(self):
        result=[]
        own_pid=os.getpid()
        def callback(hwnd,lparam):
            if not self.user32.IsWindowVisible(hwnd):
                return True
            length=self.user32.GetWindowTextLengthW(hwnd)
            if length<=0:
                return True
            title_buffer=ctypes.create_unicode_buffer(length+1)
            self.user32.GetWindowTextW(hwnd,title_buffer,length+1)
            title=title_buffer.value.strip()
            if not title:
                return True
            pid=self.pid(hwnd)
            if pid==own_pid:
                return True
            result.append({"hwnd":int(hwnd),"title":title,"class":self.class_name(hwnd),"pid":pid,"minimized":bool(self.user32.IsIconic(hwnd))})
            return True
        cb=self.WNDENUMPROC(callback)
        if not self.user32.EnumWindows(cb,0):
            raise ctypes.WinError(ctypes.get_last_error())
        result.sort(key=lambda item:(item["minimized"],item["title"].casefold()))
        return result
    def client_rect(self,hwnd):
        if not self.valid(hwnd):
            raise TargetUnavailable("目标窗口已关闭或句柄无效")
        if self.user32.IsIconic(wintypes.HWND(hwnd)):
            raise TargetUnavailable("目标窗口已最小化")
        rect=RECT()
        if not self.user32.GetClientRect(wintypes.HWND(hwnd),ctypes.byref(rect)):
            raise ctypes.WinError(ctypes.get_last_error())
        first=POINT(rect.left,rect.top)
        second=POINT(rect.right,rect.bottom)
        if not self.user32.ClientToScreen(wintypes.HWND(hwnd),ctypes.byref(first)):
            raise ctypes.WinError(ctypes.get_last_error())
        if not self.user32.ClientToScreen(wintypes.HWND(hwnd),ctypes.byref(second)):
            raise ctypes.WinError(ctypes.get_last_error())
        width=int(second.x-first.x)
        height=int(second.y-first.y)
        if width<2 or height<2:
            raise TargetUnavailable("目标窗口客户区尺寸无效")
        return int(first.x),int(first.y),width,height
    def visible_child_regions(self,hwnd):
        client=self.client_rect(hwnd)
        cx,cy,cw,ch=client
        result=[]
        def callback(child,lparam):
            try:
                if not self.user32.IsWindowVisible(child) or self.user32.IsIconic(child):
                    return True
                rect=RECT()
                if not self.user32.GetWindowRect(child,ctypes.byref(rect)):
                    return True
                left=max(cx,int(rect.left)); top=max(cy,int(rect.top)); right=min(cx+cw,int(rect.right)); bottom=min(cy+ch,int(rect.bottom))
                width=right-left; height=bottom-top
                if width>=FEATURE_W and height>=FEATURE_H:
                    result.append({"hwnd":int(child),"rect":(left,top,width,height),"area":width*height,"class":self.class_name(child)})
            except Exception:
                pass
            return True
        proc=self.CHILDENUMPROC(callback)
        self.user32.EnumChildWindows(wintypes.HWND(int(hwnd)),proc,0)
        result.sort(key=lambda item:item["area"],reverse=True)
        return result
    def auto_content_region(self,target):
        client=self.client_rect(int(target["hwnd"]))
        children=self.visible_child_regions(int(target["hwnd"]))
        minimum=client[2]*client[3]*0.30
        chosen=next((item for item in children if item["area"]>=minimum),None)
        rect=chosen["rect"] if chosen else client
        return {"rect":rect,"norm":normalized_rect(rect,client),"source":"largest_visible_child" if chosen else "full_client","child_class":str(chosen.get("class","")) if chosen else ""}
    def content_rect(self,target):
        client=self.client_rect(int(target["hwnd"]))
        rect=apply_normalized_rect(client,target.get("content_rect_norm",[0.0,0.0,1.0,1.0]))
        expected=safe_float(target.get("content_aspect",rect[2]/max(1,rect[3])),rect[2]/max(1,rect[3]))
        actual=rect[2]/max(1,rect[3])
        if expected>0 and abs(actual/expected-1.0)>VersionedThresholdConfig.content_aspect_tolerance:
            raise TargetUnavailable("内容区域宽高比已变化，已暂停并要求重新校准")
        return rect
    def window_rect(self,hwnd):
        if not self.valid(hwnd):
            raise TargetUnavailable("目标窗口已关闭或句柄无效")
        rect=RECT()
        if not self.user32.GetWindowRect(wintypes.HWND(hwnd),ctypes.byref(rect)):
            raise ctypes.WinError(ctypes.get_last_error())
        width=int(rect.right-rect.left)
        height=int(rect.bottom-rect.top)
        if width<2 or height<2:
            raise TargetUnavailable("目标窗口尺寸无效")
        return int(rect.left),int(rect.top),width,height
    def dpi_for_window(self,hwnd):
        try:
            if hasattr(self.user32,"GetDpiForWindow"):
                value=int(self.user32.GetDpiForWindow(wintypes.HWND(hwnd)))
                if value>0:
                    return value
        except Exception:
            pass
        return 96
    def foreground_hwnd(self):
        return int(self.user32.GetForegroundWindow() or 0)
    def request_foreground(self,hwnd):
        if not self.valid(hwnd):
            return False
        result=bool(self.user32.SetForegroundWindow(wintypes.HWND(hwnd)))
        return result and self.foreground_hwnd()==int(hwnd)
    def validate_target_identity(self,target,require_foreground=True):
        if not isinstance(target,dict):
            raise TargetUnavailable("目标窗口身份信息无效")
        hwnd=safe_int(target.get("hwnd",0),0)
        if not self.valid(hwnd):
            raise TargetUnavailable("目标窗口已关闭或句柄无效")
        current_thread,current_pid=self.window_thread_pid(hwnd)
        if current_pid!=safe_int(target.get("pid",-1),-1):
            raise TargetUnavailable("目标窗口PID已变化，窗口句柄可能被复用")
        current_class=self.class_name(hwnd)
        if current_class!=str(target.get("class","")):
            raise TargetUnavailable("目标窗口类名已变化，窗口身份不确定")
        if "window_thread_id" in target and current_thread!=safe_int(target.get("window_thread_id",-1),-1):
            raise TargetUnavailable("目标窗口所属线程已变化，拒绝继续操作")
        process=None
        if any(key in target for key in ("process_path","process_created","integrity")):
            process=self.process_identity_for_pid(current_pid)
        if "process_path" in target and os.path.normcase(str(target.get("process_path","")))!=process["path"]:
            raise TargetUnavailable("目标进程可执行文件路径已变化，拒绝继续操作")
        if "process_created" in target and process["created"]!=safe_int(target.get("process_created",-1),-1):
            raise TargetUnavailable("目标进程创建时间已变化，PID可能已被复用")
        if "integrity" in target and process["integrity"]!=safe_int(target.get("integrity",-1),-1):
            raise TargetUnavailable("目标进程完整性级别已变化，拒绝继续操作")
        if self.user32.IsIconic(wintypes.HWND(hwnd)):
            raise TargetUnavailable("目标窗口已最小化")
        if require_foreground and self.foreground_hwnd()!=hwnd:
            raise TargetUnavailable("目标窗口失去焦点，等待恢复")
        rule=target.get("title_rule")
        if isinstance(rule,dict):
            mode=str(rule.get("mode","none")); value=str(rule.get("value","")); title=self.window_title(hwnd)
            if mode=="exact" and title!=value:
                raise TargetUnavailable("目标窗口标题不再符合精确规则")
            if mode=="contains" and value and value not in title:
                raise TargetUnavailable("目标窗口标题不再符合包含规则")
            if mode=="prefix" and value and not title.startswith(value):
                raise TargetUnavailable("目标窗口标题不再符合前缀规则")
        return self.client_rect(hwnd),self.dpi_for_window(hwnd)
    def validate_target(self,target,require_foreground=True):
        client,dpi=self.validate_target_identity(target,require_foreground)
        expected_size=target.get("client_size")
        if isinstance(expected_size,(list,tuple)) and len(expected_size)>=2 and [int(client[2]),int(client[3])]!=[safe_int(expected_size[0],-1),safe_int(expected_size[1],-1)]:
            raise TargetUnavailable("目标窗口客户区尺寸已变化，已暂停并要求重新校准内容区域")
        expected_dpi=target.get("selected_dpi",target.get("dpi"))
        if expected_dpi is not None and int(dpi)!=safe_int(expected_dpi,-1):
            raise TargetUnavailable("目标窗口DPI已变化，已暂停并要求重新校准")
        return self.content_rect(target)
    def cursor(self):
        point=POINT()
        if not self.user32.GetCursorPos(ctypes.byref(point)):
            raise ctypes.WinError(ctypes.get_last_error())
        return int(point.x),int(point.y)
    def key_down(self,vk):
        return bool(self.user32.GetAsyncKeyState(vk)&0x8000)
    def _make_dib(self,reference_dc,width,height):
        memory=self.gdi32.CreateCompatibleDC(reference_dc)
        if not memory:
            raise ctypes.WinError(ctypes.get_last_error())
        info=BITMAPINFO()
        info.bmiHeader.biSize=ctypes.sizeof(BITMAPINFOHEADER)
        info.bmiHeader.biWidth=width
        info.bmiHeader.biHeight=-height
        info.bmiHeader.biPlanes=1
        info.bmiHeader.biBitCount=32
        info.bmiHeader.biCompression=0
        bits=ctypes.c_void_p()
        bitmap=self.gdi32.CreateDIBSection(reference_dc,ctypes.byref(info),0,ctypes.byref(bits),None,0)
        if not bitmap:
            self.gdi32.DeleteDC(memory)
            raise ctypes.WinError(ctypes.get_last_error())
        old=self.gdi32.SelectObject(memory,bitmap)
        return memory,bitmap,old,bits
    def _rgb_from_raw(self,raw,width,height,out_w=PREVIEW_W,out_h=PREVIEW_H,crop=None):
        left,top,crop_w,crop_h=(0,0,int(width),int(height)) if not isinstance(crop,(list,tuple)) or len(crop)!=4 else [int(value) for value in crop]
        left=max(0,min(int(width)-1,left)); top=max(0,min(int(height)-1,top)); crop_w=max(1,min(int(width)-left,crop_w)); crop_h=max(1,min(int(height)-top,crop_h))
        result=bytearray(int(out_w)*int(out_h)*3)
        for oy in range(int(out_h)):
            sy=min(int(height)-1,top+(2*oy+1)*crop_h//(2*int(out_h)))
            for ox in range(int(out_w)):
                sx=min(int(width)-1,left+(2*ox+1)*crop_w//(2*int(out_w)))
                index=(sy*int(width)+sx)*4
                position=(oy*int(out_w)+ox)*3
                result[position]=raw[index+2]
                result[position+1]=raw[index+1]
                result[position+2]=raw[index]
        return bytes(result)
    def _capture_print(self,hwnd,width,height,out_w=FEATURE_W,out_h=FEATURE_H,crop=None):
        key_kind="print|"+str(int(hwnd))
        item=self._gdi_resource(key_kind,0,int(width),int(height))
        ctypes.memset(item["bits"],0,int(width)*int(height)*4)
        if not self.user32.PrintWindow(wintypes.HWND(hwnd),item["memory"],3):
            raise CaptureUnavailable("PrintWindow采集失败")
        raw=(ctypes.c_ubyte*(int(width)*int(height)*4)).from_address(int(item["bits"].value))
        return self._rgb_from_raw(raw,int(width),int(height),int(out_w),int(out_h),crop)
    def _capture_dc(self,source_hwnd,sx,sy,width,height,out_w=FEATURE_W,out_h=FEATURE_H):
        key_kind="dc|"+str(int(source_hwnd))
        item=self._gdi_resource(key_kind,int(source_hwnd),int(out_w),int(out_h))
        self.gdi32.SetStretchBltMode(item["memory"],4)
        if not self.gdi32.StretchBlt(item["memory"],0,0,int(out_w),int(out_h),item["source"],int(sx),int(sy),int(width),int(height),0x00CC0020):
            raise CaptureUnavailable("窗口DC采集失败")
        raw=(ctypes.c_ubyte*(int(out_w)*int(out_h)*4)).from_address(int(item["bits"].value))
        return self._rgb_from_raw(raw,int(out_w),int(out_h),int(out_w),int(out_h))
    def _rgb_to_gray(self,rgb):
        source=rgb_bytes(rgb)
        if source is None:
            return None
        return bytes((source[index]*77+source[index+1]*150+source[index+2]*29)>>8 for index in range(0,len(source),3))
    def _quality(self,rgb):
        try:
            source=bytes(rgb)
        except Exception:
            source=b""
        if not source or len(source)%3:
            return {"mean":0.0,"std":0.0,"spread":0,"black":True,"black_frame":True,"solid":True,"flat_frame":True,"low_information":False,"valid":False,"protected_or_black":True,"histogram":[0]*16}
        count=0
        mean=0.0
        m2=0.0
        minimum=255
        maximum=0
        histogram=[0]*16
        for index in range(0,len(source),3):
            value=(source[index]*77+source[index+1]*150+source[index+2]*29)>>8
            count+=1
            delta=value-mean
            mean+=delta/count
            m2+=delta*(value-mean)
            if value<minimum:
                minimum=value
            if value>maximum:
                maximum=value
            histogram[min(15,value>>4)]+=1
        variance=m2/max(1,count)
        std=math.sqrt(max(0.0,variance))
        spread=maximum-minimum
        black=bool(maximum<12 or mean<3.0 or mean<9.0 and spread<10 and std<3.0)
        solid=bool(std<0.9 or spread<3)
        flat=bool(not black and solid)
        return {"mean":mean,"std":std,"spread":spread,"black":black,"black_frame":black,"solid":solid,"flat_frame":flat,"low_information":flat,"valid":True,"protected_or_black":black,"histogram":histogram}
    def feature_from_rgb(self,rgb,previous_rgb=None):
        source=rgb_bytes(rgb)
        if source is None:
            raise CaptureUnavailable("RGB画面尺寸无效")
        previous=rgb_bytes(previous_rgb)
        luminance=bytearray(PIXELS)
        chroma_b=bytearray(PIXELS)
        chroma_r=bytearray(PIXELS)
        motion=bytearray(PIXELS)
        for pixel in range(PIXELS):
            index=pixel*3
            r=source[index]
            g=source[index+1]
            b=source[index+2]
            luminance[pixel]=(r*77+g*150+b*29)>>8
            chroma_b[pixel]=max(0,min(255,128+((-43*r-85*g+128*b)>>8)))
            chroma_r[pixel]=max(0,min(255,128+((128*r-107*g-21*b)>>8)))
            if previous is not None:
                motion[pixel]=(abs(r-previous[index])+abs(g-previous[index+1])+abs(b-previous[index+2]))//3
        edges=bytearray(PIXELS)
        for y in range(FEATURE_H):
            for x in range(FEATURE_W):
                index=y*FEATURE_W+x
                right=luminance[index+1] if x+1<FEATURE_W else luminance[index]
                down=luminance[index+FEATURE_W] if y+1<FEATURE_H else luminance[index]
                edges[index]=min(255,abs(int(right)-int(luminance[index]))+abs(int(down)-int(luminance[index])))
        return bytes(luminance)+bytes(chroma_b)+bytes(chroma_r)+bytes(edges)+bytes(motion)
    def feature_from_gray(self,gray,previous_gray=None):
        current=gray_bytes(gray)
        previous=gray_bytes(previous_gray)
        if current is None:
            raise CaptureUnavailable("灰度画面尺寸无效")
        rgb=bytes(value for pixel in current for value in (pixel,pixel,pixel))
        previous_rgb=bytes(value for pixel in previous for value in (pixel,pixel,pixel)) if previous is not None else None
        return self.feature_from_rgb(rgb,previous_rgb)
    def _features(self,rgb,key):
        now=time.monotonic()
        with self.frame_lock:
            history=self.previous_frames.setdefault(int(key),deque(maxlen=12))
            previous=None
            for stamp,item in reversed(history):
                if stamp<=now-0.1:
                    previous=item
                    break
            history.append((now,rgb_bytes(rgb)))
        return self.feature_from_rgb(rgb,previous)
    def reset_frame_history(self,hwnd=None):
        with self.frame_lock:
            if hwnd is None:
                self.previous_frames.clear()
            else:
                self.previous_frames.pop(int(hwnd),None)
    def _health(self,hwnd,method,rgb):
        now=time.monotonic()
        digest=hashlib.sha256(rgb).digest()
        key=(int(hwnd),str(method),len(rgb))
        previous=self.capture_health.get(key)
        if previous and previous["digest"]==digest:
            unchanged_since=previous["unchanged_since"]
        else:
            unchanged_since=now
        stale=now-unchanged_since>4.0
        self.capture_health[key]={"digest":digest,"unchanged_since":unchanged_since,"last":now,"stale":stale}
        return stale
    def calibration_identity_matches(self,target,calibration,rect=None):
        try:
            if not isinstance(target,dict) or not isinstance(calibration,dict) or not calibration.get("dynamic_passed"):
                return False
            current_rect=tuple(rect) if isinstance(rect,(list,tuple)) and len(rect)==4 else self.validate_target(target,False)
            hwnd=safe_int(target.get("hwnd",0),0)
            current_thread,current_pid=self.window_thread_pid(hwnd)
            process=self.process_identity_for_pid(current_pid)
            norm=[round(safe_float(value,0.0),6) for value in target.get("content_rect_norm",[0,0,1,1])[:4]]
            saved_norm=[round(safe_float(value,0.0),6) for value in calibration.get("validated_content_rect_norm",[0,0,1,1])[:4]]
            return bool(calibration.get("validated_backend") and safe_int(calibration.get("validated_pid",-1),-1)==current_pid and str(calibration.get("validated_class",""))==self.class_name(hwnd) and str(calibration.get("validated_process_path",""))==process["path"] and safe_int(calibration.get("validated_process_created",-1),-1)==process["created"] and safe_int(calibration.get("validated_window_thread_id",-1),-1)==current_thread and safe_int(calibration.get("validated_integrity",-1),-1)==process["integrity"] and safe_int(calibration.get("validated_dpi",0),0)==self.dpi_for_window(hwnd) and list(calibration.get("validated_rect",[0,0,0,0]))[2:4]==[int(current_rect[2]),int(current_rect[3])] and norm==saved_norm and safe_int(calibration.get("capture_backend_version",0),0)==CAPTURE_BACKEND_VERSION)
        except Exception:
            return False
    def capture_gray(self,target,require_foreground_for_desktop=True,validation_mode=False,need_preview=False):
        rect=self.validate_target(target,False)
        client=self.client_rect(int(target["hwnd"]))
        hwnd=safe_int(target["hwnd"],0)
        x,y,width,height=rect
        if width<FEATURE_W or height<FEATURE_H:
            raise CaptureUnavailable("内容区域尺寸异常，拒绝采集")
        out_w=PREVIEW_W if need_preview else FEATURE_W
        out_h=PREVIEW_H if need_preview else FEATURE_H
        attempts=[]
        candidates=[]
        calibration=self.calibrations.get(hwnd,{})
        validated_method=str(calibration.get("validated_backend",""))
        validated_methods=set(str(value) for value in calibration.get("validated_backends",[]) if str(value))
        if validated_method:
            validated_methods.add(validated_method)
        identity_key=self._capture_identity_key(target)
        if validated_method:
            allowed,_=self._circuit_allows((identity_key,validated_method))
            if not allowed:
                alternatives=[]
                for name in validated_methods:
                    if name==validated_method:
                        continue
                    candidate_allowed,_=self._circuit_allows((identity_key,name))
                    if candidate_allowed:
                        alternatives.append(name)
                if alternatives:
                    validated_method=sorted(alternatives)[0]
                    calibration["validated_backend"]=validated_method
                    self.calibrations[hwnd]=calibration
        backend_names=["Windows Graphics Capture","PrintWindow客户区","窗口DC"]
        if not require_foreground_for_desktop or self.foreground_hwnd()==hwnd:
            backend_names.append("前台桌面裁剪")
        else:
            attempts.append("前台桌面裁剪被跳过：目标窗口不在前台")
        if validated_method:
            backend_names.sort(key=lambda name:0 if name==validated_method else 1)
        identity_valid=self.calibration_identity_matches(target,calibration,rect)
        need_comparison=bool(validation_mode)
        offset_x=x-client[0]; offset_y=y-client[1]
        for priority,name in enumerate(backend_names):
            allowed,reason=self._circuit_allows((identity_key,name))
            if not allowed:
                attempts.append(name+"已跳过："+reason)
                continue
            try:
                command={"backend":name,"hwnd":hwnd,"rect":list(rect),"client_rect":list(client),"content_offset":[offset_x,offset_y],"out_w":out_w,"out_h":out_h}
                raw=self._isolated_capture((identity_key,name),command,0.55)
                rgb=bytes(raw)
                expected=int(out_w)*int(out_h)*3
                if len(rgb)!=expected:
                    raise CaptureUnavailable("返回画面尺寸无效")
                preview=rgb if need_preview else None
                model_rgb=resize_rgb(rgb,out_w,out_h,FEATURE_W,FEATURE_H) if (out_w,out_h)!=(FEATURE_W,FEATURE_H) else rgb
                quality=self._quality(rgb)
                stale=self._health(hwnd,name,model_rgb)
                backend_validated=bool(validation_mode or identity_valid and name in validated_methods)
                backend_changed=bool(validated_method and (name not in validated_methods or not identity_valid))
                candidate={"rgb":model_rgb,"gray":self._rgb_to_gray(model_rgb),"preview_rgb":preview,"preview_width":out_w if preview is not None else 0,"preview_height":out_h if preview is not None else 0,"method":name,"quality":quality,"priority":priority,"stale":stale,"stable_frame":bool(stale and not quality.get("black_frame")),"capture_valid":bool(quality["valid"]),"backend_validated":backend_validated,"backend_changed":backend_changed,"static_feature":self.feature_from_rgb(model_rgb,None)}
                candidates.append(candidate)
                if len(candidates)==1:
                    need_comparison=bool(validation_mode or quality.get("black_frame") or quality.get("flat_frame") or stale)
                if not need_comparison and backend_validated and not backend_changed:
                    break
                if need_comparison and len(candidates)>=2 and not validation_mode:
                    break
            except Exception as error:
                attempts.append(name+"失败："+str(error))
        if not candidates:
            self.capture_reports[hwnd]="采集失败："+"；".join(attempts)
            raise CaptureUnavailable("无法采集目标内容区域："+"；".join(attempts))
        chosen=next((item for item in candidates if item["method"]==validated_method and identity_valid),None)
        if chosen is None:
            chosen=min(candidates,key=lambda item:(not item["capture_valid"],bool(item["quality"].get("black_frame")),item["priority"]))
        protected=False
        frozen=False
        comparison_threshold=max(260.0,safe_float(calibration.get("significant_change",60.0),60.0)*4.0)
        for other in candidates:
            if other is chosen or not other.get("capture_valid"):
                continue
            gap=visual_distance(chosen["static_feature"],other["static_feature"])
            information_mismatch=bool(chosen["quality"].get("black_frame")!=other["quality"].get("black_frame") or chosen["quality"].get("flat_frame")!=other["quality"].get("flat_frame"))
            if information_mismatch and gap>comparison_threshold:
                protected=True
            if chosen.get("stale") and not other.get("stale") and gap>max(20.0,safe_float(calibration.get("freeze_change",1.5),1.5)*8.0):
                frozen=True
        is_black=bool(chosen["quality"].get("black_frame",chosen["quality"].get("black")))
        usable=bool(chosen.get("capture_valid") and chosen.get("backend_validated") and not chosen.get("backend_changed") and not protected and not frozen and not is_black)
        result=dict(chosen)
        result.pop("static_feature",None)
        result.update({"usable_for_learning":usable,"usable_for_training":usable,"usable_for_teaching":usable,"protected_or_black":bool(protected or is_black),"black_frame":is_black,"stable_frame":bool(chosen.get("stable_frame") and not frozen),"capture_frozen":frozen,"frozen_backend":frozen})
        if validation_mode:
            result["validation_candidates"]=[{"method":item["method"],"rgb":item["rgb"],"quality":dict(item["quality"]),"stale":bool(item.get("stale"))} for item in candidates]
        wgc_note="；WGC不可用，已降级" if any(str(value).startswith("Windows Graphics Capture失败") for value in attempts) else ""
        if usable:
            mode="合法静态画面" if result.get("stable_frame") else ("低纹理画面" if result["quality"].get("flat_frame") else "画面有效")
            self.capture_reports[hwnd]="当前采集："+result["method"]+"；"+mode+"；内容区域已隔离；后端已验收"+wgc_note
        else:
            reasons=[]
            if is_black:
                reasons.append("检测到全黑或极暗画面，自动输入已锁定")
            if not result.get("backend_validated"):
                reasons.append("后端未验收")
            if result.get("backend_changed"):
                reasons.append("后端或窗口身份变化")
            if protected:
                reasons.append("不同后端结果显著不一致，疑似受保护画面")
            if frozen:
                reasons.append("当前后端冻结但其他后端仍变化")
            if not result.get("capture_valid"):
                reasons.append("画面数据无效")
            self.capture_reports[hwnd]="采集仅可预览，拒绝自动处理："+"、".join(reasons or attempts or ["未知原因"])
        return result
    def capture(self,target,require_foreground_for_desktop=True):
        item=self.capture_gray(target,require_foreground_for_desktop,False,False)
        item["f"]=self._features(item["rgb"],int(target["hwnd"]))
        item["motion_valid"]=True
        item["rect"]=self.validate_target(target,False)
        item["dpi"]=self.dpi_for_window(int(target["hwnd"]))
        return item
    def capture_status(self,hwnd):
        return self.capture_reports.get(int(hwnd),"尚未完成动态采集验收；未验收后端只能预览，不能学习或训练")
    def calibration_for(self,target):
        hwnd=int(target.get("hwnd",0)) if isinstance(target,dict) else int(target or 0)
        defaults={"noise":4.0,"visual_cluster":420.0,"significant_change":60.0,"post_action_change":45.0,"freeze_change":1.5,"freeze_frames":30,"confirm_frames":3,"duplicate":3.0,"fps":10.0,"input_delay":0.24,"validated_backend":"","dynamic_passed":False,"static_passed":False,"backend_thresholds":{}}
        result=dict(defaults)
        result.update(self.calibrations.get(hwnd,{}))
        method=str(result.get("validated_backend",""))
        thresholds=result.get("backend_thresholds",{})
        if method and isinstance(thresholds,dict) and isinstance(thresholds.get(method),dict):
            result.update(thresholds[method])
        return result
    def calibrate(self,target,duration=1.8,stop_event=None,progress=None):
        hwnd=safe_int(target["hwnd"],0)
        rect=self.validate_target(target,False)
        integrity=self.validate_uipi(target)
        with self.frame_lock:
            for key in [key for key in self.capture_health if key[0]==hwnd]:
                self.capture_health.pop(key,None)
        actual_duration=safe_float(duration,1.8,0.75,3.0)
        deadline=time.monotonic()+actual_duration
        records=defaultdict(list)
        previous_by_method={}
        black_frames=0
        invalid_frames=0
        while time.monotonic()<deadline:
            if stop_event is not None and stop_event.is_set():
                raise InputStopped("窗口采集验收已取消")
            self.validate_target(target,False)
            try:
                captured=self.capture_gray(target,True,True,False)
            except CaptureUnavailable:
                invalid_frames+=1
                if stop_event is not None and stop_event.wait(0.06):
                    raise InputStopped("窗口采集验收已取消")
                continue
            candidates=captured.get("validation_candidates")
            if not isinstance(candidates,list):
                candidates=[{"method":captured.get("method"),"rgb":captured.get("rgb"),"quality":captured.get("quality",{}),"stale":captured.get("stale")}]
            stamp=time.monotonic()
            for candidate in candidates:
                quality=candidate.get("quality",{}) if isinstance(candidate,dict) else {}
                if not quality.get("valid"):
                    invalid_frames+=1
                    continue
                if quality.get("black_frame",quality.get("black")):
                    black_frames+=1
                    continue
                method=str(candidate.get("method",""))
                rgb=rgb_bytes(candidate.get("rgb"))
                if not method or rgb is None:
                    invalid_frames+=1
                    continue
                feature=self.feature_from_rgb(rgb,previous_by_method.get(method))
                previous_by_method[method]=rgb
                records[method].append({"feature":feature,"stamp":stamp,"quality":quality,"stale":bool(candidate.get("stale"))})
            if progress:
                progress(min(1.0,1.0-max(0.0,deadline-time.monotonic())/actual_duration))
            if stop_event is not None and stop_event.wait(0.05):
                raise InputStopped("窗口采集验收已取消")
            time.sleep(0.0)
        minimum_nonblack=3 if actual_duration<1.2 else 4
        eligible={}
        for method,items in records.items():
            features=[item["feature"] for item in items]
            changes=[visual_distance(a,b) for a,b in zip(features,features[1:])]
            unique=len({hashlib.sha256(bytes(feature[:PIXELS])).digest() for feature in features})
            trusted_change=bool(len(items)>=3 and unique>=2 and changes and max(changes)>=1.0)
            if len(items)>=minimum_nonblack or trusted_change:
                eligible[method]={"items":items,"changes":changes,"unique":unique,"trusted_change":trusted_change}
        if not eligible:
            total_nonblack=sum(len(items) for items in records.values())
            raise CaptureUnavailable("采集验收未获得足够非黑帧或可信画面变化；非黑帧"+str(total_nonblack)+"，黑帧"+str(black_frames)+"，无效帧"+str(invalid_frames)+"；自动输入保持锁定")
        previous=self.calibrations.get(hwnd,{})
        previous_method=str(previous.get("validated_backend",""))
        method=previous_method if previous_method in eligible else max(eligible,key=lambda name:(len(eligible[name]["items"]),eligible[name]["unique"],name))
        selected=eligible[method]["items"]
        features=[record["feature"] for record in selected]
        stamps=[record["stamp"] for record in selected]
        changes=eligible[method]["changes"]
        unique=eligible[method]["unique"]
        dynamic=bool(eligible[method]["trusted_change"])
        observed_noise=max(0.35,quantile(changes,0.5) if changes else 0.35)
        previous_thresholds={}
        if isinstance(previous.get("backend_thresholds"),dict) and isinstance(previous.get("backend_thresholds",{}).get(method),dict):
            previous_thresholds=dict(previous["backend_thresholds"][method])
        if actual_duration<1.2 and finite_number(previous_thresholds.get("noise")):
            noise=max(0.35,0.7*safe_float(previous_thresholds.get("noise"),observed_noise)+0.3*observed_noise)
        else:
            noise=observed_noise
        fps=(len(stamps)-1)/max(0.01,stamps[-1]-stamps[0]) if len(stamps)>1 else safe_float(previous_thresholds.get("fps",8.0),8.0,1.0,120.0)
        rect=self.validate_target(target,False)
        dpi=self.dpi_for_window(hwnd)
        thresholds={"noise":noise,"visual_cluster":max(70.0,min(1400.0,noise*9.0+120.0)),"significant_change":max(16.0,min(260.0,noise*4.5+18.0)),"post_action_change":max(12.0,min(220.0,noise*3.2+14.0)),"freeze_change":max(0.35,noise*0.22),"freeze_frames":max(18,min(80,round(fps*3.0))),"confirm_frames":3 if fps>=12 else 4,"duplicate":max(1.0,min(18.0,noise*0.65)),"fps":fps,"input_delay":max(0.16,min(0.55,3.0/max(5.0,fps)))}
        backend_thresholds=dict(previous.get("backend_thresholds",{})) if isinstance(previous.get("backend_thresholds",{}),dict) else {}
        for backend,data in eligible.items():
            backend_changes=data["changes"]
            backend_noise=max(0.35,quantile(backend_changes,0.5) if backend_changes else noise)
            backend_thresholds[backend]={"noise":backend_noise,"visual_cluster":max(70.0,min(1400.0,backend_noise*9.0+120.0)),"significant_change":max(16.0,min(260.0,backend_noise*4.5+18.0)),"post_action_change":max(12.0,min(220.0,backend_noise*3.2+14.0)),"freeze_change":max(0.35,backend_noise*0.22),"freeze_frames":thresholds["freeze_frames"],"confirm_frames":thresholds["confirm_frames"],"duplicate":max(1.0,min(18.0,backend_noise*0.65)),"fps":fps,"input_delay":thresholds["input_delay"]}
        thread_id,pid=self.window_thread_pid(hwnd)
        process=self.process_identity_for_pid(pid)
        result=dict(thresholds)
        result.update({"method":method,"validated_backend":method,"validated_backends":sorted(eligible),"dynamic_passed":True,"static_passed":not dynamic,"calibration_mode":"dynamic" if dynamic else "stable","validated_at":time.time(),"validated_rect":list(rect),"validated_content_rect_norm":[round(safe_float(value,0.0),6) for value in target.get("content_rect_norm",[0,0,1,1])[:4]],"capture_backend_version":CAPTURE_BACKEND_VERSION,"validated_dpi":dpi,"validated_pid":pid,"validated_class":str(target["class"]),"validated_process_path":process["path"],"validated_process_created":process["created"],"validated_window_thread_id":thread_id,"validated_integrity":process["integrity"],"integrity":process["integrity"],"nonblack_frames":len(selected),"black_frames":black_frames,"trusted_change":dynamic,"backend_thresholds":backend_thresholds})
        self.calibrations[hwnd]=result
        mode="动态校准" if dynamic else "稳定性校准"
        self.capture_reports[hwnd]="当前采集："+method+"；"+mode+"通过；非黑帧"+str(len(selected))+"；帧率"+str(round(fps,1))+"fps；后端已验收"
        return dict(result)
    def _send(self,flags,data=0,dx=0,dy=0,require_allowed=False):
        if require_allowed and not self.input_allowed():
            raise InputStopped("停止标志已设置，拒绝新的鼠标输入")
        item=INPUT()
        item.type=0
        item.mi=MOUSEINPUT(int(dx),int(dy),ctypes.c_ulong(int(data)&0xffffffff).value,int(flags),0,ULONG_PTR(INPUT_EXTRA_INFO))
        if require_allowed and not self.input_allowed():
            raise InputStopped("停止标志已设置，拒绝新的鼠标输入")
        if self.user32.SendInput(1,ctypes.byref(item),ctypes.sizeof(INPUT))!=1:
            raise ctypes.WinError(ctypes.get_last_error())
    def move_cursor(self,x,y):
        if not self.input_allowed():
            raise InputStopped("停止标志已设置，拒绝鼠标移动")
        left=self.user32.GetSystemMetrics(76)
        top=self.user32.GetSystemMetrics(77)
        width=self.user32.GetSystemMetrics(78)
        height=self.user32.GetSystemMetrics(79)
        nx=round((int(x)-left)*65535/max(1,width-1))
        ny=round((int(y)-top)*65535/max(1,height-1))
        self._send(0x0001|0x8000|0x4000,0,nx,ny,True)
    def button(self,button,down):
        flags={"left":(0x0002,0x0004),"right":(0x0008,0x0010),"middle":(0x0020,0x0040)}
        if button not in flags:
            raise RuntimeError("不支持的鼠标按钮")
        with self.input_lock:
            if down and not self.input_allowed():
                raise InputStopped("停止标志已设置，拒绝新的鼠标按下事件")
            self._send(flags[button][0 if down else 1],require_allowed=bool(down))
            if down:
                self.held.add(button)
            else:
                self.held.discard(button)
    def wheel(self,delta,horizontal=False):
        with self.input_lock:
            if not self.input_allowed():
                raise InputStopped("停止标志已设置，拒绝滚轮事件")
            self._send(0x01000 if horizontal else 0x0800,int(delta),require_allowed=True)
    def close(self):
        self.block_input()
        processes_stopped=self.abort_capture_processes()
        with self.wgc_lock:
            wgc=self.wgc
            self.wgc=None
        if wgc is not None:
            try:
                wgc.close()
            except Exception:
                pass
        with self.capture_task_lock:
            items=list(self.gdi_resources.values())
            self.gdi_resources.clear()
        for item in items:
            self._dispose_gdi_resource(item)
        return processes_stopped
    def release_all_buttons(self):
        with self.input_lock:
            for button in list(self.held):
                try:
                    flags={"left":0x0004,"right":0x0010,"middle":0x0040}
                    self._send(flags[button])
                except Exception:
                    pass
                self.held.discard(button)
            for flag in (0x0004,0x0010,0x0040):
                try:
                    self._send(flag)
                except Exception:
                    pass
def _capture_process_main(connection):
    bridge=None
    try:
        bridge=WinBridge()
        while True:
            try:
                command=connection.recv()
            except EOFError:
                break
            if command is None:
                break
            try:
                backend=str(command.get("backend",""))
                hwnd=safe_int(command.get("hwnd",0),0)
                rect=command.get("rect")
                if not isinstance(rect,(list,tuple)) or len(rect)!=4:
                    raise CaptureUnavailable("采集进程收到无效客户区")
                x,y,width,height=[safe_int(value,0) for value in rect]
                out_w=safe_int(command.get("out_w",FEATURE_W),FEATURE_W,1,PREVIEW_W)
                out_h=safe_int(command.get("out_h",FEATURE_H),FEATURE_H,1,PREVIEW_H)
                if backend=="Windows Graphics Capture":
                    result=bridge.get_wgc().capture(hwnd,(x,y,width,height),out_w,out_h)
                elif backend=="PrintWindow客户区":
                    client_rect=command.get("client_rect",rect); cx,cy,cw,ch=[safe_int(value,0) for value in client_rect]; offset=command.get("content_offset",[x-cx,y-cy]); ox,oy=[safe_int(value,0) for value in offset[:2]]
                    result=bridge._capture_print(hwnd,cw,ch,out_w,out_h,(ox,oy,width,height))
                elif backend=="窗口DC":
                    client_rect=command.get("client_rect",rect); cx,cy,cw,ch=[safe_int(value,0) for value in client_rect]; offset=command.get("content_offset",[x-cx,y-cy]); ox,oy=[safe_int(value,0) for value in offset[:2]]
                    result=bridge._capture_dc(hwnd,ox,oy,width,height,out_w,out_h)
                elif backend=="前台桌面裁剪":
                    result=bridge._capture_dc(0,x,y,width,height,out_w,out_h)
                else:
                    raise CaptureUnavailable("未知采集后端")
                connection.send((True,bytes(result)))
            except BaseException as error:
                try:
                    connection.send((False,str(error)))
                except Exception:
                    break
    finally:
        if bridge is not None:
            try:
                bridge.close()
            except Exception:
                pass
        try:
            connection.close()
        except Exception:
            pass
class KeyboardMonitor:
    def __init__(self,bridge,on_escape=None,on_other=None):
        self.bridge=bridge
        self.events=queue.Queue(maxsize=2048)
        self.escape_event=threading.Event()
        self.other_event=threading.Event()
        self.thread=None
        self.thread_id=0
        self.hook=None
        self.callback=None
        self.ready=threading.Event()
        self.error=None
        self.escape_down=False
        self.pressed_non_escape=set()
        self.key_lock=threading.RLock()
        self.non_escape_count=0
    def start(self):
        self.thread=threading.Thread(target=self._run,name="UniversalGameAI-KeyboardHook",daemon=True)
        self.thread.start()
        if not self.ready.wait(2.0):
            raise RuntimeError("键盘监听器启动超时")
        if self.error:
            raise RuntimeError(self.error)
        if not self.hook:
            raise RuntimeError("无法安装键盘监听器")
        return self
    def _put(self,event):
        try:
            self.events.put_nowait(event)
        except queue.Full:
            pass
    def _run(self):
        try:
            self.thread_id=int(self.bridge.kernel32.GetCurrentThreadId())
            def callback(code,wparam,lparam):
                if code>=0 and int(wparam) in {0x0100,0x0101,0x0104,0x0105}:
                    data=ctypes.cast(lparam,ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                    injected=bool(int(data.flags)&0x12)
                    if own_injected_event(data.flags,data.dwExtraInfo,0x12):
                        return self.bridge.user32.CallNextHookEx(self.hook,code,wparam,lparam)
                    vk=int(data.vkCode)
                    is_escape=vk==0x1B
                    down=int(wparam) in {0x0100,0x0104}
                    wall_time=time.time()
                    monotonic_time=time.monotonic()
                    stamp=monotonic_time
                    if is_escape:
                        first=down and not self.escape_down
                        self.escape_down=down
                        if first:
                            self.escape_event.set()
                            self._put({"kind":"escape","down":True,"time":stamp,"wall_time":wall_time,"monotonic_time":monotonic_time,"injected":injected})
                    else:
                        with self.key_lock:
                            first=down and vk not in self.pressed_non_escape
                            if down:
                                self.pressed_non_escape.add(vk)
                            else:
                                self.pressed_non_escape.discard(vk)
                            active=bool(self.pressed_non_escape)
                        if down:
                            if first:
                                self.non_escape_count+=1
                            self.other_event.set()
                            self._put({"kind":"other","down":True,"time":stamp,"wall_time":wall_time,"monotonic_time":monotonic_time,"vk":vk,"injected":injected})
                        else:
                            self._put({"kind":"other","down":False,"time":stamp,"wall_time":wall_time,"monotonic_time":monotonic_time,"vk":vk,"injected":injected})
                            if not active:
                                self.other_event.clear()
                return self.bridge.user32.CallNextHookEx(self.hook,code,wparam,lparam)
            self.callback=self.bridge.HOOKPROC(callback)
            module=self.bridge.kernel32.GetModuleHandleW(None)
            self.hook=self.bridge.user32.SetWindowsHookExW(13,self.callback,module,0)
            if not self.hook:
                raise ctypes.WinError(ctypes.get_last_error())
            self.ready.set()
            message=MSG()
            while self.bridge.user32.GetMessageW(ctypes.byref(message),None,0,0)>0:
                self.bridge.user32.TranslateMessage(ctypes.byref(message))
                self.bridge.user32.DispatchMessageW(ctypes.byref(message))
        except Exception:
            self.error=traceback.format_exc()
            self.ready.set()
        finally:
            if self.hook:
                try:
                    self.bridge.user32.UnhookWindowsHookEx(self.hook)
                except Exception:
                    pass
                self.hook=None
    def drain(self):
        result=[]
        while True:
            try:
                result.append(self.events.get_nowait())
            except queue.Empty:
                break
        if not any(item.get("kind")=="other" and item.get("down") for item in result):
            self.other_event.clear()
        if not any(item.get("kind")=="escape" for item in result):
            self.escape_event.clear()
        return result
    def all_released(self):
        with self.key_lock:
            return not self.pressed_non_escape
    def stop(self,timeout=1.0):
        if self.thread_id:
            try:
                self.bridge.user32.PostThreadMessageW(self.thread_id,0x0012,0,0)
            except Exception:
                pass
        if self.thread and self.thread.is_alive() and self.thread is not threading.current_thread() and timeout>0:
            self.thread.join(max(0.0,float(timeout)))
        return not bool(self.thread and self.thread.is_alive())
    def alive(self):
        return bool(self.thread and self.thread.is_alive())
class MouseMonitor:
    def __init__(self,bridge,on_input=None):
        self.bridge=bridge
        self.events=queue.Queue(maxsize=6000)
        self.input_event=threading.Event()
        self.state_lock=threading.RLock()
        self.held=set()
        self.thread=None
        self.thread_id=0
        self.hook=None
        self.callback=None
        self.ready=threading.Event()
        self.error=None
        self.last_move=0.0
        self.last_input_time=0.0
        self.generation=0
        self.dropped_events=0
    def start(self):
        self.thread=threading.Thread(target=self._run,name="UniversalGameAI-MouseHook",daemon=True)
        self.thread.start()
        if not self.ready.wait(2.0):
            raise RuntimeError("鼠标监听器启动超时")
        if self.error:
            raise RuntimeError(self.error)
        if not self.hook:
            raise RuntimeError("无法安装鼠标监听器")
        return self
    def _put(self,event):
        try:
            self.events.put_nowait(event)
            return True
        except queue.Full:
            with self.state_lock:
                self.dropped_events+=1
                self.generation+=1
                self.held.clear()
            self.input_event.set()
            return False
    def _run(self):
        try:
            self.thread_id=int(self.bridge.kernel32.GetCurrentThreadId())
            messages={0x0200:"move",0x0201:"left_down",0x0202:"left_up",0x0204:"right_down",0x0205:"right_up",0x0207:"middle_down",0x0208:"middle_up",0x020A:"wheel",0x020E:"hwheel"}
            def callback(code,wparam,lparam):
                if code>=0 and int(wparam) in messages:
                    data=ctypes.cast(lparam,ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                    injected=bool(int(data.flags)&0x00000003)
                    if own_injected_event(data.flags,data.dwExtraInfo,0x00000003):
                        return self.bridge.user32.CallNextHookEx(self.hook,code,wparam,lparam)
                    wall_time=time.time()
                    monotonic_time=time.monotonic()
                    kind=messages[int(wparam)]
                    with self.state_lock:
                        should_emit=kind!="move" or monotonic_time-self.last_move>=0.018
                        if should_emit and kind=="move":
                            self.last_move=monotonic_time
                    if should_emit:
                        event={"type":kind,"x":int(data.pt.x),"y":int(data.pt.y),"time":monotonic_time,"wall_time":wall_time,"monotonic_time":monotonic_time,"injected":injected,"extra_info":int(data.dwExtraInfo)}
                        if kind in {"wheel","hwheel"}:
                            raw=(int(data.mouseData)>>16)&0xffff
                            event["delta"]=raw-0x10000 if raw&0x8000 else raw
                        with self.state_lock:
                            if kind.endswith("_down"):
                                self.held.add(kind.split("_",1)[0])
                            elif kind.endswith("_up"):
                                self.held.discard(kind.split("_",1)[0])
                            self.last_input_time=monotonic_time
                            self.generation+=1
                            event["generation"]=self.generation
                        self.input_event.set()
                        self._put(event)
                return self.bridge.user32.CallNextHookEx(self.hook,code,wparam,lparam)
            self.callback=self.bridge.HOOKPROC(callback)
            module=self.bridge.kernel32.GetModuleHandleW(None)
            self.hook=self.bridge.user32.SetWindowsHookExW(14,self.callback,module,0)
            if not self.hook:
                raise ctypes.WinError(ctypes.get_last_error())
            self.ready.set()
            message=MSG()
            while self.bridge.user32.GetMessageW(ctypes.byref(message),None,0,0)>0:
                self.bridge.user32.TranslateMessage(ctypes.byref(message))
                self.bridge.user32.DispatchMessageW(ctypes.byref(message))
        except Exception:
            self.error=traceback.format_exc()
            self.ready.set()
        finally:
            if self.hook:
                try:
                    self.bridge.user32.UnhookWindowsHookEx(self.hook)
                except Exception:
                    pass
                self.hook=None
    def drain(self):
        result=[]
        while True:
            try:
                result.append(self.events.get_nowait())
            except queue.Empty:
                break
        if self.events.empty():
            self.input_event.clear()
        return result
    def snapshot(self):
        with self.state_lock:
            return {"held":frozenset(self.held),"last_input_time":self.last_input_time,"generation":self.generation,"dropped_events":self.dropped_events}
    def all_released(self):
        with self.state_lock:
            return not self.held
    def stable_for(self,seconds):
        with self.state_lock:
            return not self.held and time.monotonic()-self.last_input_time>=max(0.0,float(seconds))
    def stop(self,timeout=1.0):
        if self.thread_id:
            try:
                self.bridge.user32.PostThreadMessageW(self.thread_id,0x0012,0,0)
            except Exception:
                pass
        if self.thread and self.thread.is_alive() and self.thread is not threading.current_thread() and timeout>0:
            self.thread.join(max(0.0,float(timeout)))
        return not bool(self.thread and self.thread.is_alive())
    def alive(self):
        return bool(self.thread and self.thread.is_alive())
class FrameBuffer:
    def __init__(self,bridge,target,hz=20.0,seconds=2.0,motion_interval=0.1,purpose=None,on_geometry=None):
        self.bridge=bridge
        self.target=target if isinstance(target,dict) else dict(target)
        self.base_interval=1.0/max(5.0,float(hz))
        self.interval=self.base_interval
        self.motion_interval=max(0.05,min(0.25,float(motion_interval)))
        self.purpose=str(purpose or "")
        self.need_preview=self.purpose=="teaching"
        self.preview_interval=1.0/11.0
        self.preview_active=threading.Event()
        if self.need_preview:
            self.preview_active.set()
        self.frames=deque(maxlen=max(12,int(float(hz)*float(seconds))+4))
        self.lock=threading.RLock()
        self.condition=threading.Condition(self.lock)
        self.sequence=0
        self.stop_event=threading.Event()
        self.thread=None
        self.last_error=""
        self.last_preview=None
        self.on_geometry=on_geometry
        self.pending_geometry=None
        self.geometry_since=0.0
        self.resume_confirmations=0
    def set_preview_active(self,active):
        if active:
            self.preview_active.set()
        else:
            self.preview_active.clear()
    def start(self):
        self.bridge.reset_frame_history(self.target.get("hwnd"))
        self.stop_event.clear()
        self.thread=threading.Thread(target=self._run,name="UniversalGameAI-FrameBuffer",daemon=True)
        self.thread.start()
        return self
    def _geometry_ready(self):
        rect,dpi=self.bridge.validate_target_identity(self.target,False)
        expected=self.target.get("client_size")
        expected_dpi=self.target.get("selected_dpi",self.target.get("dpi"))
        changed=bool(isinstance(expected,(list,tuple)) and len(expected)>=2 and [int(rect[2]),int(rect[3])]!=[safe_int(expected[0],-1),safe_int(expected[1],-1)] or expected_dpi is not None and int(dpi)!=safe_int(expected_dpi,-1))
        if not changed:
            self.pending_geometry=None
            self.geometry_since=0.0
            return True
        self.bridge.block_input()
        geometry=(int(rect[2]),int(rect[3]),int(dpi))
        now=time.monotonic()
        if geometry!=self.pending_geometry:
            self.pending_geometry=geometry
            self.geometry_since=now
            with self.condition:
                self.frames.clear()
                self.sequence+=1
                self.last_error="窗口尺寸或DPI变化，等待几何稳定后重新校准"
                self.condition.notify_all()
            return False
        if now-self.geometry_since<0.75:
            return False
        self.target["selected_rect"]=list(rect)
        self.target["client_size"]=[int(rect[2]),int(rect[3])]
        self.target["selected_dpi"]=int(dpi)
        self.target["dpi"]=int(dpi)
        self.bridge.calibrations.pop(int(self.target["hwnd"]),None)
        self.bridge.reset_capture_backends(self.target)
        self.bridge.reset_frame_history(self.target.get("hwnd"))
        calibration=self.bridge.calibrate(self.target,1.2,self.stop_event)
        with self.condition:
            self.frames.clear()
            self.sequence+=1
            self.last_error="窗口几何已稳定，重新校准完成，等待连续有效帧"
            self.condition.notify_all()
        self.resume_confirmations=max(3,int(calibration.get("confirm_frames",3)))
        self.pending_geometry=None
        self.geometry_since=0.0
        if self.on_geometry:
            self.on_geometry(self.target,calibration)
        return False
    def _run(self):
        thread_id=threading.get_ident()
        next_time=time.monotonic()
        next_preview=0.0
        try:
            while not self.stop_event.is_set():
                try:
                    if not self._geometry_ready():
                        self.stop_event.wait(0.05)
                        continue
                    now=time.monotonic()
                    preview_due=bool(self.need_preview and self.preview_active.is_set() and now>=next_preview)
                    captured=self.bridge.capture_gray(self.target,True,False,preview_due)
                    if preview_due:
                        next_preview=now+self.preview_interval
                        preview=preview_rgb_bytes(captured.get("preview_rgb"))
                        if preview is not None:
                            self.last_preview=(preview,safe_int(captured.get("preview_width",PREVIEW_W),PREVIEW_W),safe_int(captured.get("preview_height",PREVIEW_H),PREVIEW_H))
                    stamp=time.monotonic()
                    wall_time=time.time()
                    rgb=captured["rgb"]
                    gray=captured["gray"]
                    with self.lock:
                        previous=None
                        previous_feature=None
                        for old_frame in reversed(self.frames):
                            if previous_feature is None:
                                previous_feature=old_frame.get("f")
                            if old_frame["time"]<=stamp-self.motion_interval:
                                previous=old_frame["rgb"]
                                break
                    feature=self.bridge.feature_from_rgb(rgb,previous)
                    if previous_feature is not None:
                        change=visual_distance(previous_feature,feature)
                        noise=float(self.bridge.calibration_for(self.target).get("noise",4.0))
                        self.interval=min(0.2,self.base_interval*2.5) if change<=max(1.0,noise*1.5) else self.base_interval
                    rect=self.bridge.validate_target(self.target,False)
                    preview_rgb=captured.get("preview_rgb")
                    preview_width=captured.get("preview_width",0)
                    preview_height=captured.get("preview_height",0)
                    if preview_rgb is None and self.last_preview is not None:
                        preview_rgb,preview_width,preview_height=self.last_preview
                    confirmed=self.resume_confirmations<=0
                    if captured.get("capture_valid") and captured.get("backend_validated") and self.resume_confirmations>0:
                        self.resume_confirmations-=1
                    frame={"time":stamp,"wall_time":wall_time,"monotonic_time":stamp,"f":feature,"coarse":coarse_feature(feature),"gray":gray,"rgb":rgb,"preview_rgb":preview_rgb,"preview_width":preview_width,"preview_height":preview_height,"method":captured["method"],"quality":captured["quality"],"motion_valid":previous is not None,"rect":rect,"dpi":self.bridge.dpi_for_window(int(self.target["hwnd"])),"capture_valid":bool(captured.get("capture_valid")),"backend_validated":bool(captured.get("backend_validated")),"usable_for_learning":bool(captured.get("usable_for_learning") and confirmed),"usable_for_training":bool(captured.get("usable_for_training") and confirmed),"usable_for_teaching":bool(captured.get("usable_for_teaching") and confirmed),"stale":bool(captured.get("stale")),"stable_frame":bool(captured.get("stable_frame")),"black_frame":bool(captured.get("black_frame")),"protected_or_black":bool(captured.get("protected_or_black")),"capture_frozen":bool(captured.get("capture_frozen")),"frozen_backend":bool(captured.get("frozen_backend")),"backend_changed":bool(captured.get("backend_changed"))}
                    with self.condition:
                        self.frames.append(frame)
                        self.sequence+=1
                        self.last_error="" if frame.get("usable_for_"+self.purpose,frame["capture_valid"]) else "画面无效、黑屏、冻结、受保护、后端未验收或正在重新确认"
                        self.condition.notify_all()
                except InputStopped:
                    break
                except Exception as error:
                    with self.condition:
                        self.last_error=str(error)
                        self.condition.notify_all()
                next_time=max(next_time+self.interval,time.monotonic())
                self.stop_event.wait(max(0.001,next_time-time.monotonic()))
        finally:
            try:
                self.bridge.release_capture_thread_resources(thread_id)
            except Exception:
                pass
    def latest(self,before=None,max_age=0.6,purpose=None):
        now=time.monotonic()
        with self.lock:
            candidates=list(self.frames)
        if before is not None:
            candidates=[frame for frame in candidates if frame["time"]<=float(before)]
        if not candidates:
            return None
        frame=candidates[-1]
        reference=float(before) if before is not None else now
        if reference-frame["time"]>max_age:
            return None
        if purpose and not frame.get("usable_for_"+str(purpose)):
            return None
        return dict(frame)
    def latest_after(self,stamp,max_wait_age=0.8):
        with self.lock:
            for frame in reversed(self.frames):
                if frame["time"]>float(stamp):
                    return dict(frame)
        if time.monotonic()-float(stamp)>max_wait_age:
            return None
        return None
    def snapshot(self,seconds=1.5):
        cutoff=time.monotonic()-max(0.1,float(seconds))
        with self.lock:
            return [dict(frame) for frame in self.frames if frame["time"]>=cutoff]
    def stop(self,wait=True,timeout=1.0):
        self.stop_event.set()
        with self.condition:
            self.condition.notify_all()
        if wait and self.thread and self.thread.is_alive() and self.thread is not threading.current_thread() and timeout>0:
            self.thread.join(max(0.0,float(timeout)))
        return not bool(self.thread and self.thread.is_alive())
    def wait_for_usable(self,purpose,timeout=3.0,external_stop=None):
        deadline=time.monotonic()+max(0.1,float(timeout))
        with self.condition:
            seen=self.sequence
        while time.monotonic()<deadline:
            if self.bridge.key_down(0x1B):
                if external_stop is not None:
                    external_stop.set()
                self.bridge.block_input()
                raise InputStopped("初始化期间收到ESC停止请求")
            if external_stop is not None and external_stop.is_set():
                raise InputStopped("初始化期间收到停止请求")
            frame=self.latest(None,1.0,purpose)
            if frame is not None:
                return frame
            if not self.thread or not self.thread.is_alive():
                raise CaptureUnavailable(self.last_error or "画面线程已停止")
            remaining=max(0.0,deadline-time.monotonic())
            with self.condition:
                while self.sequence==seen and not self.stop_event.is_set() and remaining>0:
                    self.condition.wait(min(0.2,remaining))
                    remaining=max(0.0,deadline-time.monotonic())
                seen=self.sequence
        raise CaptureUnavailable("未在限定时间内获得可用于"+str(purpose)+"的已验收画面："+(self.last_error or "未知原因"))
    def alive(self):
        return bool(self.thread and self.thread.is_alive())
class ModeSession:
    def __init__(self,app,target):
        self.app=app
        self.target=target if isinstance(target,dict) else dict(target)
        self.barrier=ResourceShutdownBarrier("模式资源",4.0)
        self.frame_buffer=None
        self.mouse_monitor=None
        self.keyboard_monitor=None
    def _geometry_updated(self,target,calibration):
        try:
            self.app.store.save_capture_calibration(target,calibration)
        except Exception:
            pass
        self.app.set_status("窗口尺寸或DPI变化后已自动重新校准，正在连续确认画面")
    def start_frames(self,hz,seconds,motion_interval,purpose):
        buffer=FrameBuffer(self.app.api,self.target,hz,seconds,motion_interval,purpose,self._geometry_updated)
        self.barrier.add("FrameBuffer",lambda timeout:buffer.stop(False,timeout),buffer.alive)
        buffer.start()
        buffer.wait_for_usable(purpose,4.0,self.app.stop_event)
        self.frame_buffer=buffer
        return buffer
    def start_keyboard(self,on_other=None):
        monitor=KeyboardMonitor(self.app.api)
        self.barrier.add("KeyboardHook",monitor.stop,monitor.alive)
        monitor.start()
        self.keyboard_monitor=monitor
        return monitor
    def start_mouse(self,on_input=None):
        monitor=MouseMonitor(self.app.api)
        self.barrier.add("MouseHook",monitor.stop,monitor.alive)
        monitor.start()
        self.mouse_monitor=monitor
        return monitor
    def add_resource(self,name,resource,stopper=None,alive=None,forcer=None):
        stop=stopper or resource.stop
        check=alive or resource.alive
        self.barrier.add(name,stop,check,forcer)
        return resource
    def request_stop(self):
        self.barrier.request_stop()
        self.app.api.block_input()
    def close(self,timeout=0.0):
        self.request_stop()
        done=self.barrier.poll()
        if timeout>0 and not done:
            deadline=time.monotonic()+float(timeout)
            while time.monotonic()<deadline and not done:
                time.sleep(0.02)
                done=self.barrier.poll()
        if done and self.app.active_session is self:
            self.app.active_session=None
        return done
    def pending_names(self):
        return self.barrier.pending_names()
    def __enter__(self):
        self.app.active_session=self
        return self
    def __exit__(self,exc_type,exc_value,exc_traceback):
        self.close(0.0)
        return False
class AskQuestionProducer:
    def __init__(self,app,frame_buffer,prototypes,historical,sources,game_id,model_version):
        self.app=app
        self.frame_buffer=frame_buffer
        self.prototypes=list(prototypes)
        self.historical=list(historical)
        self.sources=list(sources)
        self.game_id=str(game_id)
        self.model_version=str(model_version)
        self.requests=queue.Queue(maxsize=1)
        self.results=queue.Queue(maxsize=2)
        self.stop_event=threading.Event()
        self.thread=None
        self.counter=0
    def start(self):
        self.thread=threading.Thread(target=self._run,name="UniversalGameAI-TeachingQuestions",daemon=True)
        self.thread.start()
        return self
    def request(self,recent_actions,state_since):
        payload={"recent_actions":list(recent_actions)[-4:],"state_since":float(state_since)}
        try:
            while True:
                self.requests.get_nowait()
        except queue.Empty:
            pass
        try:
            self.requests.put_nowait(payload)
        except queue.Full:
            pass
    def _put_result(self,value):
        try:
            while self.results.qsize()>=1:
                self.results.get_nowait()
        except queue.Empty:
            pass
        try:
            self.results.put_nowait(value)
        except queue.Full:
            pass
    def _select_frame(self,payload):
        frames=self.frame_buffer.snapshot(1.8)
        usable=[frame for frame in frames if frame.get("usable_for_teaching")]
        if not usable:
            raise CaptureUnavailable(self.frame_buffer.last_error or "没有可用于请教的画面")
        selected=usable[-1]
        selected_ranked=[]
        selected_priority=float("inf")
        candidates=usable[-28:]
        if not self.prototypes:
            return selected,[]
        for candidate_frame in candidates:
            if self.stop_event.is_set() or self.app.should_stop():
                raise InputStopped("请教题目生成已停止")
            temporal=self.app.build_temporal_context(self.frame_buffer,candidate_frame,payload["recent_actions"],payload["state_since"])
            temporal["previous_action_changed_frame"]=True
            ranked=self.app.rank_action_candidates(candidate_frame["f"],self.prototypes,"",18,temporal,candidate_frame.get("coarse"))
            if not ranked:
                priority=-2.0
            else:
                decision=self.app.evaluate_action_candidates(ranked)
                gap=(ranked[1]["score"]-ranked[0]["score"])/max(1.0,ranked[0]["score"]) if len(ranked)>1 else 10.0
                priority=gap-3.0 if decision.get("ambiguous") else gap-1.0 if not decision.get("accepted") else gap
            if priority<selected_priority:
                selected_priority=priority
                selected=candidate_frame
                selected_ranked=ranked
        return selected,selected_ranked
    def _make_choices(self,question_frame,ranked):
        choices=[]
        signatures=set()
        for item in ranked[:4]:
            action=normalize_action(item["a"])
            signature=action_signature(action)
            if signature and signature not in signatures:
                signatures.add(signature)
                choices.append({"a":action,"repeat_policy":str(item["proto"].get("repeat_policy","one_shot")),"cluster_id":item["cluster_id"]})
            if len(choices)>=3:
                break
        if not choices and self.historical:
            query=question_frame.get("coarse")
            if not isinstance(query,(bytes,bytearray)) or len(query)!=COARSE_LEN:
                query=coarse_feature(question_frame["f"])
            rough=sorted((coarse_distance(query,item["coarse"]),item) for item in self.historical)[:20]
            exact=sorted((feature_distance(question_frame["f"],item["f"]),item) for _,item in rough)
            for _,item in exact:
                signature=action_signature(item["a"])
                if signature and signature not in signatures:
                    signatures.add(signature)
                    choices.append({"a":item["a"],"repeat_policy":item.get("repeat_policy","one_shot"),"cluster_id":item["cluster_id"]})
                if len(choices)>=2:
                    break
        seed_text=self.game_id+"|"+self.model_version+"|"+str(self.counter)
        generator=random.Random(int(hashlib.sha256(seed_text.encode("utf-8","replace")).hexdigest()[:16],16))
        distractors=list(self.sources)
        generator.shuffle(distractors)
        for entry in distractors:
            signature=action_signature(entry["a"])
            if signature and signature not in signatures:
                signatures.add(signature)
                choices.append(dict(entry))
            if len(choices)>=4:
                break
        generator.shuffle(choices)
        choices=choices[:4]
        candidates=[{"cluster_id":entry.get("cluster_id",""),"canonical_action_signature":action_signature(entry["a"]),"a":entry["a"]} for entry in choices]
        return choices,candidates
    def _run(self):
        while not self.stop_event.is_set():
            try:
                payload=self.requests.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                frame,ranked=self._select_frame(payload)
                choices,candidates=self._make_choices(frame,ranked)
                self.counter+=1
                self._put_result({"frame":frame,"choices":choices,"candidates":candidates,"error":""})
            except InputStopped:
                break
            except Exception as error:
                self._put_result({"frame":None,"choices":[],"candidates":[],"error":str(error)})
    def get_result(self,timeout=0.0):
        try:
            return self.results.get(timeout=max(0.0,float(timeout)))
        except queue.Empty:
            return None
    def stop(self,timeout=1.0):
        self.stop_event.set()
        if self.thread and self.thread.is_alive() and self.thread is not threading.current_thread() and timeout>0:
            self.thread.join(max(0.0,float(timeout)))
        return not bool(self.thread and self.thread.is_alive())
    def alive(self):
        return bool(self.thread and self.thread.is_alive())
class BoundedLRU:
    def __init__(self,capacity=50000):
        self.capacity=max(1,int(capacity))
        self.data=OrderedDict()
        self.hits=0
        self.misses=0
    def get(self,key,default=None):
        if key not in self.data:
            self.misses+=1
            return default
        value=self.data.pop(key)
        self.data[key]=value
        self.hits+=1
        return value
    def __setitem__(self,key,value):
        if key in self.data:
            self.data.pop(key)
        self.data[key]=value
        while len(self.data)>self.capacity:
            self.data.popitem(last=False)
    def clear(self):
        self.data.clear()
    def __len__(self):
        return len(self.data)
def compact_checksum_key(item):
    value=str(item.get("checksum") or item.get("created") or id(item)).encode("utf-8","replace")
    return int.from_bytes(hashlib.blake2b(value,digest_size=8).digest(),"big")
def action_runtime_metadata(action):
    item=normalize_action(action)
    if not item:
        return {"action":None,"family":"","dangerous":True,"strictness":(9.0,999,0.0),"cooldown":9.0}
    kind=item["kind"]
    button=item.get("button")
    dangerous=kind in {"double_click","long_press","drag"} or button in {"right","middle"}
    if dangerous:
        strictness=(1.35,4,0.78)
    elif kind in {"scroll_v","scroll_h"}:
        strictness=(1.2,3,0.80)
    elif kind in {"move","hover"}:
        strictness=(1.0,2,0.84)
    elif kind=="no_op":
        strictness=(1.0,1,0.88)
    else:
        strictness=(1.0,2,0.84)
    cooldown={"click":0.8,"double_click":1.5,"long_press":2.0,"drag":1.2,"scroll_v":0.8,"scroll_h":1.0,"move":0.45,"hover":1.0,"no_op":0.25}.get(kind,1.0)
    return {"action":item,"family":action_family_key(item),"dangerous":dangerous,"strictness":strictness,"cooldown":cooldown}
def coarse_bucket_key(value):
    raw=bytes(value) if isinstance(value,(bytes,bytearray)) and len(value)==COARSE_LEN else b""
    if not raw:
        return ()
    plane=COARSE_W*COARSE_H
    return tuple(min(7,max(0,round(sum(raw[index*plane:(index+1)*plane])/plane/36.0))) for index in range(FEATURE_CHANNELS))
def window_descriptor_score(descriptor,candidate):
    if not isinstance(descriptor,dict) or not isinstance(candidate,dict):
        return -1
    score=0
    if os.path.normcase(str(descriptor.get("process_path",""))) and os.path.normcase(str(descriptor.get("process_path","")))==os.path.normcase(str(candidate.get("process_path",""))):
        score+=8
    if str(descriptor.get("class","")) and str(descriptor.get("class",""))==str(candidate.get("class","")):
        score+=5
    rule=descriptor.get("title_rule",{})
    title=str(candidate.get("title",""))
    if isinstance(rule,dict):
        mode=str(rule.get("mode","")); value=str(rule.get("value",""))
        if mode=="exact" and title==value:
            score+=4
        elif mode=="prefix" and title.startswith(value):
            score+=3
        elif mode=="contains" and value and value in title:
            score+=2
    size=descriptor.get("client_size")
    if isinstance(size,(list,tuple)) and len(size)>=2 and list(size[:2])==list(candidate.get("client_size",[])[:2]):
        score+=2
    if safe_int(descriptor.get("dpi",0),0)>0 and safe_int(descriptor.get("dpi",0),0)==safe_int(candidate.get("dpi",0),0):
        score+=1
    if safe_int(descriptor.get("integrity",-1),-1)>=0 and safe_int(descriptor.get("integrity",-1),-1)==safe_int(candidate.get("integrity",-2),-2):
        score+=1
    return score
class ReviewProcessStore:
    def __init__(self,payload):
        self.samples=list(payload.get("samples",[]))
        self.stats=dict(payload.get("stats",{}))
        self.rejections=list(payload.get("rejections",[]))
        self.saved=[]
        self.profile=dict(payload.get("profile",{}))
    def load_game_profile(self,gid):
        return dict(self.profile)
    def load_samples(self,gid):
        return list(self.samples),dict(self.stats)
    def load_rejections(self,gid,limit=500):
        return list(self.rejections[:int(limit)])
    def save_model(self,gid,model,complete=True):
        self.saved.append((str(gid),dict(model),bool(complete)))
        return True
class ReviewProcessLifecycle:
    def mark_running(self):
        return MODE_RUNNING
    def snapshot(self):
        return MODE_RUNNING,"复习",None,"completed",""
class ReviewProcessApi:
    def key_down(self,key):
        return False
    def block_input(self):
        return None
    def release_all_buttons(self):
        return None
def review_process_send(connection,kind,payload):
    try:
        connection.send((str(kind),payload))
        return True
    except Exception:
        return False
def review_process_main(connection,stop_event,payload):
    try:
        app=object.__new__(App)
        app.selected_game=dict(payload["game"])
        app.store=ReviewProcessStore(payload)
        app.stop_event=stop_event
        app.review_distance_cache=BoundedLRU(payload.get("cache_capacity",50000))
        app.candidate_cache=BoundedLRU(64)
        app.active_model_runtime=None
        app.review_controller=ReviewController(app)
        app.lifecycle=ReviewProcessLifecycle()
        app.mode_state=MODE_STARTING
        app.api=ReviewProcessApi()
        app.set_progress=lambda value:review_process_send(connection,"progress",float(value))
        app.set_status=lambda value:review_process_send(connection,"status",str(value))
        result=App._review_worker_impl(app)
        review_process_send(connection,"result",{"status":result.status,"summary":result.summary,"details":result.details,"models":app.store.saved})
    except InputStopped as error:
        saved=app.store.saved if "app" in locals() else []
        review_process_send(connection,"result",{"status":"stopped","summary":"复习已停止","details":{"reason":str(error)},"models":saved})
    except BaseException:
        saved=app.store.saved if "app" in locals() else []
        review_process_send(connection,"error",{"traceback":traceback.format_exc(),"models":saved})
    finally:
        try:
            connection.close()
        except Exception:
            pass
class ReviewProcessWorker:
    def __init__(self,payload):
        context=multiprocessing.get_context("spawn")
        self.connection,child=context.Pipe(duplex=False)
        self.stop_event=context.Event()
        self.process=context.Process(target=review_process_main,args=(child,self.stop_event,dict(payload)),name="UniversalGameAI-OfflineReview",daemon=True)
        self.process.start()
        child.close()
    def request_stop(self):
        self.stop_event.set()
    def receive(self,timeout=0.0):
        if self.connection.poll(max(0.0,float(timeout))):
            return self.connection.recv()
        return None
    def alive(self):
        return bool(self.process.is_alive())
    def terminate(self,timeout=0.3):
        self.stop_event.set()
        try:
            if self.process.is_alive():
                self.process.terminate()
                self.process.join(max(0.0,float(timeout)))
            if self.process.is_alive() and hasattr(self.process,"kill"):
                self.process.kill()
                self.process.join(max(0.0,float(timeout)))
        except Exception:
            pass
        return not self.process.is_alive()
    def close(self,timeout=0.2):
        self.stop_event.set()
        try:
            self.process.join(max(0.0,float(timeout)))
        except Exception:
            pass
        stopped=not self.process.is_alive()
        if stopped:
            try:
                self.connection.close()
            except Exception:
                pass
        return stopped
class LearningInputEventConverter:
    def convert(self,event,rect):
        if not isinstance(event,dict) or len(rect)!=4:
            return None
        item=dict(event)
        if not all(key in item for key in ("x","y","time","type")):
            return None
        rx,ry,rw,rh=rect
        item["inside"]=bool(rx<=int(item["x"])<rx+rw and ry<=int(item["y"])<ry+rh)
        if item["inside"]:
            item["point"]=[max(0.0,min(1.0,(int(item["x"])-rx)/max(1,rw-1))),max(0.0,min(1.0,(int(item["y"])-ry)/max(1,rh-1)))]
        return item
class ClickMerger:
    def merge(self,first,second,maximum_gap=0.32):
        if not first or not second or float(second.get("time",0))-float(first.get("time",0))>float(maximum_gap):
            return None
        return {"kind":"double_click","button":str(first.get("button","left")),"path":[list(first.get("point",[0.5,0.5]))],"duration":max(0.06,float(second.get("time",0))-float(first.get("time",0)))}
class NegativeSampleSampler:
    def due(self,last_time,now,motion_time):
        return float(now)-float(last_time)>0.9 and float(now)-float(motion_time)>0.35
class SessionSubmitter:
    def __init__(self,store,gid,session_id):
        self.store=store; self.gid=str(gid); self.session_id=str(session_id)
    def flush(self):
        return self.store.sample_write_barrier()
class ReviewDataFilter:
    def valid(self,sample):
        action=normalize_action(sample.get("a")); context=sample.get("context",{}); temporal=temporal_from_context(context); calibration=context.get("calibration",{}) if isinstance(context,dict) else {}
        return bool(feature_valid(sample.get("f")) and action and temporal.get("complete") and str(sample.get("capture_method","unknown")) not in {"","unknown","legacy"} and calibration.get("dynamic_passed"))
class ReviewSessionSplitter:
    def split(self,controller,valid):
        return controller._split_by_family_backend(valid)
class ReviewActionClusterer:
    def cluster(self,app,samples):
        return app._cluster_action_samples(samples)
class ReviewVisualClusterer:
    def cluster(self,app,*args):
        return app._cluster_action_group(*args)
class ReviewThresholdBuilder:
    def dangerous(self,action):
        return action_runtime_metadata(action)["dangerous"]
class ReviewValidator:
    def authorize(self,row,dangerous):
        minimum=VersionedThresholdConfig.dangerous_min_positive if dangerous else VersionedThresholdConfig.ordinary_min_positive
        sessions=VersionedThresholdConfig.dangerous_min_sessions if dangerous else VersionedThresholdConfig.ordinary_min_sessions
        return bool(row.get("total",0)>=minimum and row.get("independent_sessions",0)>=sessions and row.get("errors",0)==0 and row.get("false_positive",0)==0 and row.get("coverage",0.0)>=VersionedThresholdConfig.minimum_coverage and (not dangerous or row.get("negative_total",0)>=VersionedThresholdConfig.dangerous_min_negative))
class BasicSafeAuthorizer:
    def authorize(self,family,support,consistency,sessions,nonambiguous,rejection_clear):
        return bool(str(family) in BASIC_SAFE_FAMILIES and int(support)>=VersionedThresholdConfig.basic_safe_min_positive and float(consistency)>=VersionedThresholdConfig.basic_safe_min_consistency and int(sessions)>=1 and bool(nonambiguous) and bool(rejection_clear))
class TrainingInterferenceDetector:
    def tripped(self,mouse_event,keyboard_event):
        return bool(mouse_event.is_set() or keyboard_event.is_set())
class TrainingFrameGate:
    def usable(self,frame,backend):
        return bool(frame and frame.get("usable_for_training") and not frame.get("black_frame") and not frame.get("capture_frozen") and frame.get("method")==backend)
class TrainingCandidateConfirmer:
    def confirmed(self,count,required):
        return int(count)>=int(required)
class TrainingActionAuthorizer:
    def authorized(self,proto):
        return bool(proto.get("authorized",False) and not proto.get("ambiguous",False))
class TrainingPostActionVerifier:
    def changed(self,before,after,threshold):
        return bool(after is not None and visual_distance(before,after["f"])>=float(threshold))
class AskRenderer:
    def action_text(self,app,action):
        return app.action_text(action)
class AskQuestionStateMachine:
    def __init__(self):
        self.state="loading"
    def set(self,value):
        self.state=str(value)
class AskActionEditor:
    def normalize(self,action):
        return normalize_action(action)
class AskSubmitController:
    def submit(self,queue_object,value):
        queue_object.put(value)
class LearningController:
    def __init__(self,app):
        self.app=app
        self.converter=LearningInputEventConverter()
        self.click_merger=ClickMerger()
        self.negative_sampler=NegativeSampleSampler()
    def convert_event(self,event,rect):
        return self.converter.convert(event,rect)
    def merge_clicks(self,first,button,point,start_time,end_time):
        second={"time":float(start_time),"button":str(button),"point":list(point)}
        merged=self.click_merger.merge(first,second,0.42)
        if merged is not None:
            merged["duration"]=max(0.06,float(end_time)-float(first.get("time",start_time)))
        return merged
    def negative_due(self,last_time,now,motion_time):
        return self.negative_sampler.due(last_time,now,motion_time)
    def submit(self,store,gid,session_id):
        return SessionSubmitter(store,gid,session_id).flush()
    def run(self):
        return self._run_impl()
    def _run_impl(self):
        app=self.app
        self=app
        game=self.require_game()
        target=self.require_window(False)
        hwnd=target["hwnd"]
        session_id="learn|"+uuid.uuid4().hex
        self.store.begin_learning_session(game["id"],session_id)
        calibration=self.ensure_capture_calibration(target,"学习")
        if not self.api.request_foreground(hwnd):
            self.set_status("无法自动切换到目标窗口，学习将等待目标窗口成为前台")
        self.wait_escape_release()
        keyboard_state={"generation":0,"last_time":0.0}
        strict_violation=False
        invalid_marked=False
        invalid_reason=""
        isolation=StrictInputIsolation(self.stop_event)
        learned=0
        discarded=0
        duplicates=0
        invalid_frames=0
        keyboard_discarded=0
        keyboard_count=0
        recent_actions=deque(["<START>","<START>"],maxlen=4)
        last_action_signature=""
        last_action_time=0.0
        last_action_feature=None
        last_action_changed=True
        state_since=time.monotonic()
        with ModeSession(self,target) as session:
            frame_buffer=session.start_frames(20.0,2.0,0.1,"learning")
            keyboard=session.start_keyboard()
            monitor=session.start_mouse()
            mouse_drop_baseline=monitor.snapshot()["dropped_events"]
            self.lifecycle.mark_running()
            self.mode_state=MODE_RUNNING
            active={}
            pending_click={}
            last_negative=0.0
            last_motion_time=0.0
            motion=None
            last_cursor=None
            hover_start=0.0
            hover_point=None
            last_update=0.0
            def drain_keyboard_events():
                nonlocal keyboard_count,strict_violation,invalid_marked,invalid_reason
                events=[event for event in keyboard.drain() if event.get("kind")=="other" and event.get("down")]
                if events:
                    strict_violation=True
                    invalid_reason="non_escape_keyboard_input"
                    keyboard_count+=len(events)
                    keyboard_state["generation"]=safe_int(keyboard_state["generation"],0)+1
                    keyboard_state["last_time"]=safe_float(events[0].get("time"),time.monotonic())
                    if not invalid_marked:
                        self.store.invalidate_learning_session(game["id"],session_id,"non_escape_keyboard_input")
                        invalid_marked=True
                    isolation.signal("keyboard",keyboard_state["last_time"])
                    self.request_mode_stop("stopped","学习检测到非ESC键盘输入，整段session无效")
                    self.mode_state=MODE_STOPPING
                    self.api.block_input()
                    self.api.release_all_buttons()
                return events
            def paused(now=None):
                drain_keyboard_events()
                return strict_violation or keyboard.other_event.is_set()
            def capture_safe(stamp=None):
                nonlocal invalid_frames
                frame=frame_buffer.latest(stamp,0.75,"learning")
                if frame is None:
                    invalid_frames+=1
                return frame
            def save(frame,action,source,weight=1.0,cursor_point=None):
                nonlocal learned,duplicates,last_action_signature,last_action_time,last_action_feature,last_action_changed,keyboard_discarded,state_since,invalid_frames
                if frame is None or not frame.get("usable_for_learning"):
                    return False
                clean_action=normalize_action(action)
                if not clean_action:
                    return False
                if frame.get("quality",{}).get("low_information") and clean_action.get("kind") not in {"no_op","click","double_click"}:
                    return False
                action=clean_action
                if paused():
                    keyboard_discarded+=1
                    return False
                generation=int(keyboard_state["generation"])
                temporal=self.build_temporal_context(frame_buffer,frame,recent_actions,state_since,cursor_point or ((action.get("path") or [None])[-1] if isinstance(action,dict) else None))
                if not temporal_from_context({**temporal,"previous_action_changed_frame":last_action_changed}).get("complete"):
                    invalid_frames+=1
                    return False
                context=self.sample_context(last_action_signature,last_action_time,last_action_changed,frame.get("motion_valid",False),session_id,frame.get("method","unknown"),"one_shot",temporal)
                saved=self.store.append_sample(game["id"],frame["f"],action,source,context,frame.get("gray"),weight)
                if saved and (generation!=int(keyboard_state["generation"]) or paused()):
                    keyboard_discarded+=1
                    return False
                if saved:
                    learned+=1
                    signature=action_signature(action)
                    recent_actions.append(signature)
                    last_action_signature=signature
                    last_action_time=time.monotonic()
                    changed=True if last_action_feature is None else visual_distance(last_action_feature,frame["f"])>float(calibration.get("significant_change",60.0))
                    last_action_changed=changed
                    if changed:
                        state_since=time.monotonic()
                    last_action_feature=frame["f"]
                else:
                    duplicates+=1
                return saved
            def save_click(button,item):
                save(item["frame"],{"kind":"click","button":button,"path":[item["point"]],"duration":item["duration"]},"learn",1.0,item["point"])
            def flush_pending(now,force=False):
                for button,item in list(pending_click.items()):
                    if force or now-item["time"]>0.42:
                        if not self.should_stop() and not paused(now):
                            save_click(button,item)
                        pending_click.pop(button,None)
            while not self.should_stop():
                now=time.monotonic()
                mouse_snapshot=monitor.snapshot()
                if mouse_snapshot["dropped_events"]>mouse_drop_baseline:
                    strict_violation=True
                    invalid_reason="mouse_event_queue_overflow"
                    if not invalid_marked:
                        self.store.invalidate_learning_session(game["id"],session_id,invalid_reason)
                        invalid_marked=True
                    isolation.signal("mouse_queue_overflow",now)
                    self.request_mode_stop("stopped","鼠标事件队列溢出，整段session无效")
                    self.mode_state=MODE_STOPPING
                    self.api.block_input()
                    self.api.release_all_buttons()
                    active.clear()
                    pending_click.clear()
                    motion=None
                    last_cursor=None
                    hover_point=None
                    hover_start=0.0
                    self.set_status("鼠标事件队列溢出，学习立即停止且整段session将被标记无效")
                    break
                keyboard_events=drain_keyboard_events()
                if keyboard_events:
                    active.clear()
                    pending_click.clear()
                    motion=None
                    last_cursor=None
                    hover_point=None
                    hover_start=0.0
                    monitor.drain()
                    self.set_status("检测到非ESC键盘输入，学习立即停止且整段session将被标记无效")
                    break
                if paused(now):
                    active.clear()
                    pending_click.clear()
                    motion=None
                    self.api.release_all_buttons()
                    self.set_status("检测到非ESC键盘输入，学习立即停止且整段session将被标记无效")
                    break
                try:
                    rect=self.api.validate_target(target,True)
                    focused=True
                except TargetUnavailable:
                    focused=False
                    active.clear()
                    pending_click.clear()
                    motion=None
                    last_cursor=None
                    hover_point=None
                    hover_start=0.0
                    self.api.release_all_buttons()
                    self.set_status("目标窗口失去焦点，等待恢复；已释放全部鼠标键")
                events=monitor.drain()
                if not focused:
                    time.sleep(0.05)
                    continue
                for raw_event in events:
                    event=self.learning_controller.convert_event(raw_event,rect)
                    if event is None:
                        continue
                    if paused(event["time"]) or self.should_stop():
                        break
                    etype=event["type"]
                    x=event["x"]
                    y=event["y"]
                    event_time=event["time"]
                    inside=event["inside"]
                    if etype.endswith("_down"):
                        button=etype.split("_")[0]
                        if button in SUPPORTED_BUTTONS and inside:
                            frame=capture_safe(event_time)
                            if frame is not None:
                                point=self.normalize_point(x,y,rect)
                                active[button]={"frame":frame,"path":[point],"start":event_time,"outside":False,"last":point}
                        motion=None
                        last_cursor=None
                        hover_point=None
                        hover_start=0.0
                    elif etype=="move":
                        last_motion_time=event_time
                        if active:
                            for item in active.values():
                                if not inside:
                                    item["outside"]=True
                                else:
                                    point=self.normalize_point(x,y,rect)
                                    if abs(point[0]-item["last"][0])+abs(point[1]-item["last"][1])>=0.004:
                                        item["path"].append(point)
                                        item["last"]=point
                            if not inside:
                                last_cursor=None
                                hover_point=None
                                hover_start=0.0
                        else:
                            if not inside:
                                last_cursor=None
                                hover_point=None
                                hover_start=0.0
                                if motion is not None:
                                    motion["outside"]=True
                                continue
                            point=self.normalize_point(x,y,rect)
                            if last_cursor is None:
                                last_cursor=point
                                hover_point=point
                                hover_start=event_time
                                continue
                            distance=math.hypot(point[0]-last_cursor[0],point[1]-last_cursor[1])
                            if motion is None and distance>=0.012:
                                frame=capture_safe(event_time)
                                if frame is not None:
                                    motion={"frame":frame,"path":[last_cursor,point],"start":event_time,"last":point,"outside":False}
                            elif motion is not None and math.hypot(point[0]-motion["last"][0],point[1]-motion["last"][1])>=0.006:
                                motion["path"].append(point)
                                motion["last"]=point
                            last_cursor=point
                            hover_point=point
                            hover_start=event_time
                    elif etype.endswith("_up"):
                        button=etype.split("_")[0]
                        if button in active:
                            item=active.pop(button)
                            if not inside:
                                item["outside"]=True
                            if item["outside"]:
                                discarded+=1
                                continue
                            point=self.normalize_point(x,y,rect)
                            item["path"].append(point)
                            duration=max(0.03,min(3.0,event_time-item["start"]))
                            length=path_length(item["path"])
                            if length>0.045:
                                save(item["frame"],{"kind":"drag","button":button,"path":item["path"],"duration":duration},"learn",1.4,point)
                            elif duration>=0.48:
                                save(item["frame"],{"kind":"long_press","button":button,"path":[point],"duration":duration},"learn",1.2,point)
                            else:
                                previous=pending_click.get(button)
                                if previous:
                                    click_gap=item["start"]-previous["time"]
                                    close=math.hypot(point[0]-previous["point"][0],point[1]-previous["point"][1])<=0.035
                                    merged=self.learning_controller.merge_clicks(previous,button,point,item["start"],event_time) if close else None
                                    if merged is not None:
                                        pending_click.pop(button,None)
                                        save(previous["frame"],merged,"learn",1.3,previous["point"])
                                        continue
                                    save_click(button,previous)
                                pending_click[button]={"frame":item["frame"],"point":point,"duration":duration,"time":event_time}
                    elif etype in {"wheel","hwheel"} and inside and not active:
                        frame=capture_safe(event_time)
                        point=self.normalize_point(x,y,rect)
                        if frame is not None:
                            save(frame,{"kind":"scroll_h" if etype=="hwheel" else "scroll_v","delta":event.get("delta",0),"path":[point],"duration":0.08},"learn",1.2,point)
                flush_pending(now)
                try:
                    polled_x,polled_y=self.api.cursor()
                    polled_inside=self.inside(polled_x,polled_y,rect)
                except Exception:
                    polled_inside=False
                if not polled_inside:
                    last_cursor=None
                    hover_point=None
                    hover_start=0.0
                    if motion is not None:
                        motion["outside"]=True
                    for item in active.values():
                        item["outside"]=True
                if motion is not None and now-last_motion_time>0.22:
                    if not motion["outside"] and path_length(motion["path"])>0.06:
                        save(motion["frame"],{"kind":"move","path":motion["path"],"duration":max(0.05,min(2.0,now-motion["start"]))},"learn",1.0,motion["path"][-1])
                    elif motion["outside"]:
                        discarded+=1
                    motion=None
                    last_cursor=None
                if not active and hover_point is not None and now-hover_start>0.85 and now-last_action_time>0.7:
                    try:
                        current_x,current_y=self.api.cursor()
                        current_inside=self.inside(current_x,current_y,rect)
                    except Exception:
                        current_inside=False
                    if current_inside:
                        current_point=self.normalize_point(current_x,current_y,rect)
                        if math.hypot(current_point[0]-hover_point[0],current_point[1]-hover_point[1])<=0.02:
                            frame=capture_safe(now)
                            if frame is not None:
                                save(frame,{"kind":"hover","path":[current_point],"duration":0.85},"learn",1.0,current_point)
                            hover_start=now+1.5
                        else:
                            hover_point=current_point
                            hover_start=now
                if not active and not pending_click and self.learning_controller.negative_due(last_negative,now,last_motion_time):
                    frame=capture_safe(now)
                    if frame is not None:
                        cursor_point=self.normalize_point(polled_x,polled_y,rect) if polled_inside else None
                        save(frame,{"kind":"no_op","duration":0.45},"negative",0.6,cursor_point)
                    last_negative=now
                if now-last_update>0.45:
                    self.set_status("学习中：有效"+str(learned)+"  重复"+str(duplicates)+"  越界废弃"+str(discarded)+"  无效画面"+str(invalid_frames)+"  非ESC键"+str(keyboard_count)+"  键盘关联废弃"+str(keyboard_discarded))
                    last_update=now
                time.sleep(0.012)
        self.learning_controller.submit(self.store,game["id"],session_id)
        if strict_violation:
            reason=invalid_reason or "input_safety_violation"
            removed=self.store.discard_session(game["id"],session_id,reason)
            keyboard_discarded=max(keyboard_discarded,removed)
            if reason=="mouse_event_queue_overflow":
                return ModeResult("stopped","学习因鼠标事件队列溢出而严格停止；整段session已作废并删除"+str(removed)+"个样本",{"invalid_session":session_id,"dropped_mouse_events":monitor.snapshot()["dropped_events"]-mouse_drop_baseline})
            return ModeResult("stopped","学习因检测到非ESC键盘输入而严格停止；整段session已作废并删除"+str(removed)+"个样本",{"invalid_session":session_id,"keyboard_events":keyboard_count})
        self.store.validate_learning_session(game["id"],session_id)
        summary="学习已停止：有效"+str(learned)+"，重复或配额抑制"+str(duplicates)+"，越界废弃"+str(discarded)+"，无效画面"+str(invalid_frames)
        return ModeResult("stopped" if self.stop_event and self.stop_event.is_set() else "completed",summary)
class ReviewController:
    def __init__(self,app):
        self.app=app
    def session_of(self,item):
        return str(item.get("session_id") or item.get("context",{}).get("session_id") or "legacy")
    def method_of(self,item):
        return str(item.get("capture_method") or item.get("context",{}).get("capture_method") or "unknown")
    def stratum_of(self,item):
        return (action_family_key(item["a"]),self.method_of(item))
    def decorrelate(self,valid):
        result=[]
        previous={}
        removed=0
        ordered=sorted(valid,key=lambda item:(self.session_of(item),float(item.get("created",0.0)),str(item.get("checksum",""))))
        for index,item in enumerate(ordered):
            if index%32==0 and self.app.should_stop():
                raise InputStopped("复习已停止")
            key=(self.session_of(item),action_signature(item["a"]),self.method_of(item))
            old=previous.get(key)
            keep=True
            if old is not None:
                gap=float(item.get("created",0.0))-float(old.get("created",0.0))
                if 0.0<=gap<0.75 and coarse_distance(item.get("coarse"),old.get("coarse"))<=5.0:
                    threshold=max(2.0,safe_float(item.get("context",{}).get("duplicate_threshold",3.0),3.0)*1.5)
                    if feature_distance(item["f"],old["f"])<=threshold:
                        keep=False
            if keep:
                result.append(item)
                previous[key]=item
            else:
                removed+=1
        return result,removed
    def split(self,valid):
        return ReviewSessionSplitter().split(self,valid)
    def _split_by_family_backend(self,valid):
        session_groups=defaultdict(list)
        for item in valid:
            session_groups[self.session_of(item)].append(item)
        sessions=sorted(session_groups,key=lambda key:hashlib.sha256(key.encode("utf-8","replace")).hexdigest())
        totals=Counter(self.stratum_of(item) for item in valid)
        if len(sessions)<2:
            return list(valid),[],{"complete":False,"mode":"session_family_backend_visual_group","holdout_sessions":[],"reason":"只有一个完整学习session，只能生成临时模型","strata":len(totals),"session_count":len(sessions),"visual_group_intersection":[]}
        parent={session:session for session in sessions}
        def find(value):
            while parent[value]!=value:
                parent[value]=parent[parent[value]]
                value=parent[value]
            return value
        def union(first,second):
            a=find(first); b=find(second)
            if a!=b:
                parent[max(a,b)]=min(a,b)
        hash_sessions=defaultdict(set)
        for item in valid:
            hash_sessions[visual_perceptual_hash(item["f"])].add(self.session_of(item))
        for sessions_for_hash in hash_sessions.values():
            ordered_sessions=sorted(sessions_for_hash)
            for session in ordered_sessions[1:]:
                union(ordered_sessions[0],session)
        hash_values=sorted(hash_sessions)
        comparisons=0
        for first_index,first_hash in enumerate(hash_values):
            first_sessions=sorted(hash_sessions[first_hash])
            for second_hash in hash_values[first_index+1:]:
                comparisons+=1
                if comparisons%2048==0 and self.app.should_stop():
                    raise InputStopped("复习已停止")
                if bin(int(first_hash,16)^int(second_hash,16)).count("1")<=4:
                    second_sessions=sorted(hash_sessions[second_hash])
                    if first_sessions and second_sessions:
                        union(first_sessions[0],second_sessions[0])
        group_sessions=defaultdict(set)
        for session in sessions:
            group_sessions[find(session)].add(session)
        groups=sorted(group_sessions,key=lambda key:hashlib.sha256("|".join(sorted(group_sessions[key])).encode("utf-8","replace")).hexdigest())
        group_items={group:[item for session in group_sessions[group] for item in session_groups[session]] for group in groups}
        group_counts={group:Counter(self.stratum_of(item) for item in items) for group,items in group_items.items()}
        group_sizes={group:len(items) for group,items in group_items.items()}
        target=max(VersionedThresholdConfig.review_min_holdout,round(len(valid)*0.25))
        best=None
        best_score=None
        def consider(chosen):
            nonlocal best,best_score
            if not chosen or len(chosen)>=len(groups):
                return
            hold_counts=Counter(); hold_count=0
            for group in chosen:
                hold_counts.update(group_counts[group]); hold_count+=group_sizes[group]
            shared=sum(1 for key,total in totals.items() if 0<hold_counts[key]<total)
            missing=sum(1 for key,total in totals.items() if hold_counts[key] in {0,total})
            complete=shared>0 and all(hold_counts[key]<totals[key] for key in totals)
            score=(0 if complete else 1,missing,0 if hold_count>=VersionedThresholdConfig.review_min_holdout else 1,abs(hold_count-target),len(chosen))
            if best_score is None or score<best_score:
                best=set(chosen); best_score=score
        count=len(groups)
        if count<=16:
            for mask in range(1,(1<<count)-1):
                consider({groups[index] for index in range(count) if mask&(1<<index)})
        else:
            generator=random.Random(int(hashlib.sha256("|".join(groups).encode("utf-8","replace")).hexdigest()[:16],16))
            for order in (groups,sorted(groups,key=lambda value:group_sizes[value]),sorted(groups,key=lambda value:group_sizes[value],reverse=True)):
                for length in range(1,min(len(order),16)+1):
                    consider(set(order[:length]))
            for _ in range(5000):
                consider({group for group in groups if generator.random()<0.25})
        if not best:
            return list(valid),[],{"complete":False,"mode":"session_family_backend_visual_group","holdout_sessions":[],"reason":"无法建立视觉组与session级留出集","strata":len(totals),"session_count":len(sessions),"visual_group_count":len(groups),"visual_group_intersection":[]}
        hold_sessions=set().union(*(group_sessions[group] for group in best))
        train=[item for item in valid if self.session_of(item) not in hold_sessions]
        holdout=[item for item in valid if self.session_of(item) in hold_sessions]
        assert_disjoint_checksums(train,holdout)
        train_sessions={self.session_of(item) for item in train}; holdout_sessions={self.session_of(item) for item in holdout}
        visual_intersection=sorted({visual_perceptual_hash(item["f"]) for item in train}&{visual_perceptual_hash(item["f"]) for item in holdout})
        if train_sessions&holdout_sessions or visual_intersection:
            raise RuntimeError("训练集与留出集session或视觉近重复组发生重叠")
        hold_counts=Counter(self.stratum_of(item) for item in holdout)
        complete=bool(train and holdout and not any(hold_counts[key]>=totals[key] for key in totals) and any(0<hold_counts[key]<totals[key] for key in totals))
        reason="" if complete else "视觉组划分无法为动作族与采集后端保留训练数据"
        return train,holdout,{"complete":complete,"mode":"session_family_backend_visual_group","holdout_sessions":sorted(holdout_sessions),"reason":reason,"strata":len(totals),"session_count":len(sessions),"visual_group_count":len(groups),"training_sessions":sorted(train_sessions),"session_intersection":[],"visual_group_intersection":visual_intersection}
    def map_holdout(self,holdout,clusters):
        by_family=defaultdict(list)
        for cluster in clusters:
            by_family[action_family_key(cluster["a"])].append(cluster)
        uncovered=0
        for item in holdout:
            candidates=by_family.get(action_family_key(item["a"]),[])
            if not candidates:
                item["_action_cluster"]=None
                item["_uncovered_action"]=True
                uncovered+=1
                continue
            ranked=sorted((action_geometry_distance(item["a"],cluster["a"]),cluster) for cluster in candidates)
            distance,cluster=ranked[0]
            if distance>action_cluster_limit(cluster["a"]):
                item["_action_cluster"]=None
                item["_uncovered_action"]=True
                uncovered+=1
                continue
            item["_action_cluster"]=cluster["id"]
            item["_cluster_action"]=cluster["a"]
            item["_action_support"]=len(cluster["members"])
            item["_canonical_action_signature"]=cluster["canonical_action_signature"]
            item["_uncovered_action"]=False
        return uncovered
    def run(self):
        return self.app._run_review_process()
    def _run_impl(self):
        app=self.app
        self=app
        game=self.require_game()
        samples,stats=self.store.load_samples(game["id"])
        valid=[]
        for index,sample in enumerate(samples):
            if index%64==0 and self.should_stop():
                raise InputStopped("复习已停止")
            action=normalize_action(sample.get("a"))
            context=sample.get("context",{})
            temporal=temporal_from_context(context)
            calibration=context.get("calibration",{}) if isinstance(context,dict) else {}
            if feature_valid(sample.get("f")) and action and temporal.get("complete") and str(sample.get("capture_method","unknown")) not in {"","unknown","legacy"} and calibration.get("dynamic_passed"):
                item=dict(sample)
                item["a"]=action
                valid.append(item)
        if not valid:
            raise RuntimeError("没有同时具备已验收采集后端和完整短时序上下文的学习数据；数据不足时只允许请教")
        self.wait_escape_release()
        self.review_distance_cache=BoundedLRU(50000)
        decorrelated,decorrelated_removed=self.review_controller.decorrelate(valid)
        if not decorrelated:
            raise RuntimeError("连续帧去相关后没有独立样本")
        train,holdout,split_info=self.review_controller.split(decorrelated)
        assert_disjoint_checksums(train,holdout)
        train_checksums=sorted(checksum_set(train))
        holdout_checksums=sorted(checksum_set(holdout))
        if set(train_checksums)&set(holdout_checksums):
            raise RuntimeError("训练集与留出集checksum交集非空")
        self.lifecycle.mark_running()
        self.mode_state=MODE_RUNNING
        action_clusters=self._cluster_action_samples(train)
        uncovered_actions=self.review_controller.map_holdout(holdout,action_clusters)
        if self.should_stop():
            raise InputStopped("复习已停止")
        holdout_sessions=set(split_info.get("holdout_sessions",[]))
        cluster_map={cluster["id"]:cluster for cluster in action_clusters}
        groups=defaultdict(list)
        for sample in train:
            groups[sample["_action_cluster"]].append(sample)
        ordered=sorted(groups.items(),key=lambda item:(normalize_action(cluster_map[item[0]]["a"])["kind"]=="no_op",-len(item[1])))
        prototypes=[]
        processed=0
        try:
            for cluster_id,items in ordered:
                if self.should_stop():
                    raise InputStopped("复习已停止")
                cluster=cluster_map[cluster_id]
                def progress(local,total_local,count):
                    self.set_progress(78*(processed+local)/max(1,len(train)))
                    self.set_status("复习中：仅使用训练集生成动作簇和短时序原型；"+str(processed+local)+"/"+str(len(train)))
                prototypes.extend(self._cluster_action_group(cluster_id,cluster["a"],len(items),items,progress,cluster.get("repeat_policy","one_shot"),cluster.get("max_rate",3.0)))
                processed+=len(items)
                prototypes=self._limit_prototypes(prototypes,MAX_PROTOTYPES)
                cache_used=len(self.review_distance_cache)
                self.set_status("复习阶段：动作簇"+str(len(prototypes))+"；距离缓存"+str(cache_used)+"/"+str(self.review_distance_cache.capacity)+"；剩余样本约"+str(max(0,len(train)-processed)))
                self.review_distance_cache.clear()
        except InputStopped:
            if prototypes:
                partial={"created":time.time(),"samples":len(decorrelated),"training_samples":len(train),"invalid_samples":stats["invalid"],"prototypes":prototypes,"capture_backends":sorted({str(item.get("capture_method")) for item in train}),"validation":{"status":"stopped","training_checksums":train_checksums,"holdout_checksums":holdout_checksums},"sequence_model":{},"model_binding":model_binding_from_samples(train),"safety_profile_checksum":profile_checksum(self.store.load_game_profile(game["id"])),"stopped":True}
                self.store.save_model(game["id"],partial,False)
            raise
        operations=0
        for index,proto in enumerate(prototypes):
            conflicting=[]
            for other in prototypes:
                operations+=1
                if operations%64==0 and self.should_stop():
                    raise InputStopped("复习已停止")
                if other["id"]!=proto["id"] and other.get("cluster_id")!=proto.get("cluster_id"):
                    conflicting.append(other)
            nearest=float("inf")
            temporal_nearest=1.0
            if conflicting:
                rough=sorted((coarse_distance(proto["coarse"],other["coarse"]),other) for other in conflicting)[:20]
                distances=[]
                for _,other in rough:
                    operations+=1
                    if operations%32==0 and self.should_stop():
                        raise InputStopped("复习已停止")
                    distances.append((feature_distance(proto["f"],other["f"]),temporal_distance(proto.get("temporal",{}),other.get("temporal",{}))))
                nearest,temporal_nearest=min(distances,key=lambda item:item[0])
            proto["nearest_conflicting_distance"]=None if math.isinf(nearest) else round(nearest,6)
            intra=float(proto.get("intra_threshold",proto["threshold"]))
            visual_close=not math.isinf(nearest) and nearest<=max(1e-6,intra*0.20)
            temporal_close=temporal_nearest<=max(float(proto.get("temporal_threshold",0.25)),0.25)
            proto["ambiguous"]=bool(visual_close and temporal_close)
            proto["threshold"]=round(max(0.001,intra if math.isinf(nearest) else min(intra,max(0.001,nearest*0.62))),6)
            proto["minimum_second_candidate_gap"]=round(max(10.0,float(proto["threshold"])*0.15,0.0 if math.isinf(nearest) else nearest*0.10),6)
            proto["channel_stats"]={"mean":sum(proto["f"])/len(proto["f"]),"minimum":min(proto["f"]),"maximum":max(proto["f"])}
            if index%12==0:
                self.set_progress(78+7*(index+1)/max(1,len(prototypes)))
        rejections=self.store.load_rejections(game["id"],500)
        rejection_constraints=0
        for proto_index,proto in enumerate(prototypes):
            matching=[]
            for rejection_index,rejection in enumerate(rejections):
                if (proto_index*max(1,len(rejections))+rejection_index)%64==0 and self.should_stop():
                    raise InputStopped("复习已停止")
                candidate_actions=[normalize_action(item.get("a")) for item in rejection.get("candidates",[]) if isinstance(item,dict)]
                if any(action and action_family_key(action)==action_family_key(proto["a"]) and action_geometry_distance(action,proto["a"])<=action_cluster_limit(proto["a"])*1.25 for action in candidate_actions):
                    matching.append((coarse_distance(proto["coarse"],rejection["coarse"]),rejection))
            if matching:
                nearest_rejected=min(feature_distance(proto["f"],rejection["f"]) for _,rejection in sorted(matching,key=lambda item:item[0])[:8])
                proto["nearest_rejected_distance"]=round(nearest_rejected,6)
                proto["threshold"]=round(max(0.001,min(float(proto["threshold"]),nearest_rejected*0.72)),6)
                rejection_constraints+=1
            else:
                proto["nearest_rejected_distance"]=None
        basic_cluster_rows={}
        basic_by_signature=defaultdict(lambda:{"support":0,"sessions":set(),"clusters":[],"consistent":0,"total":0})
        for cluster in action_clusters:
            cluster_id=str(cluster["id"])
            members=list(groups.get(cluster_id,[]))
            family=action_family_key(cluster["a"])
            signature=str(cluster.get("canonical_action_signature") or action_signature(cluster["a"]))
            sessions={self.review_controller.session_of(item) for item in members}
            limit=max(1e-9,action_cluster_limit(cluster["a"])*0.65)
            consistent=sum(1 for item in members if action_geometry_distance(item["a"],cluster["a"])<=limit)
            consistency=consistent/max(1,len(members))
            cluster_prototypes=[proto for proto in prototypes if str(proto.get("cluster_id"))==cluster_id]
            rejection_clear=all(proto.get("nearest_rejected_distance") is None or float(proto.get("nearest_rejected_distance"))>float(proto.get("threshold",0.0))*1.10 for proto in cluster_prototypes)
            nonambiguous=bool(cluster_prototypes and all(not proto.get("ambiguous") for proto in cluster_prototypes))
            passed=BasicSafeAuthorizer().authorize(family,len(members),consistency,len(sessions),nonambiguous,rejection_clear)
            row={"family":family,"signature":signature,"support":len(members),"sessions":sorted(sessions),"consistency":consistency,"nonambiguous":nonambiguous,"rejection_clear":rejection_clear,"passed":passed}
            basic_cluster_rows[cluster_id]=row
            aggregate=basic_by_signature[signature]
            aggregate["support"]+=len(members)
            aggregate["sessions"].update(sessions)
            aggregate["clusters"].append(cluster_id)
            aggregate["consistent"]+=consistent
            aggregate["total"]+=len(members)
        errors=0
        accepted=0
        correct=0
        by_action=defaultdict(lambda:{"total":0,"accepted":0,"correct":0,"errors":0,"unrecognized":0,"negative_total":0,"false_positive":0})
        by_method=defaultdict(lambda:{"total":0,"accepted":0,"correct":0,"errors":0})
        by_scene=defaultdict(lambda:{"total":0,"accepted":0,"correct":0,"errors":0})
        action_sessions=defaultdict(set)
        dangerous_false=0
        uncovered_rejected=0
        uncovered_false_accept=0
        covered_holdout=0
        dangerous_signatures={cluster["canonical_action_signature"] for cluster in action_clusters if cluster["a"]["kind"] in {"double_click","long_press","drag"} or cluster["a"].get("button") in {"right","middle"}}
        for index,sample in enumerate(holdout):
            if index%8==0 and self.should_stop():
                raise InputStopped("复习已停止")
            ranked=self.rank_action_candidates(sample["f"],prototypes,str(sample.get("context",{}).get("previous_action","")),16,sample.get("context",{}),sample.get("coarse"))
            decision=self.evaluate_action_candidates(ranked)
            expected=sample.get("_action_cluster")
            canonical=sample.get("_canonical_action_signature") or action_signature(sample["a"])
            method=str(sample.get("capture_method") or sample.get("context",{}).get("capture_method") or "unknown")
            scene=visual_scene_key(sample)
            arow=by_action[canonical]
            mrow=by_method[method]
            srow=by_scene[scene]
            action_sessions[canonical].add(self.review_controller.session_of(sample))
            arow["total"]+=1
            mrow["total"]+=1
            srow["total"]+=1
            predicted_signature=""
            if expected is not None:
                covered_holdout+=1
            if decision.get("accepted"):
                accepted+=1
                arow["accepted"]+=1
                mrow["accepted"]+=1
                srow["accepted"]+=1
                predicted=decision["best"]
                predicted_signature=str(predicted.get("canonical_action_signature") or action_signature(predicted["a"]))
                if expected is not None and predicted["cluster_id"]==expected:
                    correct+=1
                    arow["correct"]+=1
                    mrow["correct"]+=1
                    srow["correct"]+=1
                else:
                    errors+=1
                    arow["errors"]+=1
                    mrow["errors"]+=1
                    srow["errors"]+=1
                    if expected is None:
                        uncovered_false_accept+=1
                    predicted_action=normalize_action(predicted["a"])
                    if predicted_action["kind"] in {"double_click","long_press","drag"} or predicted_action.get("button") in {"right","middle"}:
                        dangerous_false+=1
            else:
                arow["unrecognized"]+=1
                if expected is None:
                    uncovered_rejected+=1
                    correct+=1
                    arow["correct"]+=1
                    mrow["correct"]+=1
                    srow["correct"]+=1
            for signature in dangerous_signatures:
                if canonical!=signature:
                    by_action[signature]["negative_total"]+=1
                    if predicted_signature==signature:
                        by_action[signature]["false_positive"]+=1
            if index%5==0:
                self.set_progress(85+13*(index+1)/max(1,len(holdout)))
        holdout_count=len(holdout)
        coverage=accepted/covered_holdout if covered_holdout else 0.0
        accepted_error_rate=errors/accepted if accepted else None
        error_upper_95=binomial_error_upper(errors,accepted,0.95)
        overall_accuracy=correct/holdout_count if holdout_count else 0.0
        dangerous_false_rate=dangerous_false/max(1,holdout_count)
        per_action={}
        action_rules_pass=True
        authorized_clusters=set()
        train_signatures={str(item.get("_canonical_action_signature",action_signature(item["a"]))) for item in train}
        for signature in sorted(train_signatures|set(by_action)):
            row=dict(by_action[signature])
            row["recall"]=row["correct"]/row["total"] if row["total"] else 0.0
            row["coverage"]=row["accepted"]/row["total"] if row["total"] else 0.0
            row["accepted_error_rate"]=row["errors"]/row["accepted"] if row["accepted"] else None
            row["error_upper_95"]=binomial_error_upper(row["errors"],row["accepted"],0.95)
            row["independent_sessions"]=len(action_sessions.get(signature,set()))
            action=next((cluster["a"] for cluster in action_clusters if cluster["canonical_action_signature"]==signature),{"kind":"no_op"})
            dangerous=action["kind"] in {"double_click","long_press","drag"} or action.get("button") in {"right","middle"}
            row["dangerous"]=dangerous
            row_pass=ReviewValidator().authorize(row,dangerous)
            basic_row=basic_by_signature.get(signature)
            basic_pass=bool(not dangerous and basic_row and any(basic_cluster_rows.get(cluster_id,{}).get("passed") for cluster_id in basic_row["clusters"]))
            row["basic_training_support"]=int(basic_row["support"]) if basic_row else 0
            row["basic_training_sessions"]=len(basic_row["sessions"]) if basic_row else 0
            row["basic_training_consistency"]=(basic_row["consistent"]/max(1,basic_row["total"])) if basic_row else 0.0
            row["basic_safe_passed"]=basic_pass
            row["passed"]=bool(row_pass)
            row["authorized"]=bool(row_pass or basic_pass)
            for cluster in action_clusters:
                if cluster["canonical_action_signature"]==signature and (row_pass or basic_cluster_rows.get(str(cluster["id"]),{}).get("passed")):
                    authorized_clusters.add(cluster["id"])
            per_action[signature]=row
        train_methods=sorted({str(item.get("capture_method")) for item in train})
        per_method={}
        method_rules_pass=True
        for method in sorted(set(train_methods)|set(by_method)):
            row=dict(by_method[method])
            row["accuracy"]=row["correct"]/row["total"] if row["total"] else 0.0
            row["coverage"]=row["accepted"]/row["total"] if row["total"] else 0.0
            row["accepted_error_rate"]=row["errors"]/row["accepted"] if row["accepted"] else None
            row["error_upper_95"]=binomial_error_upper(row["errors"],row["accepted"],0.95)
            row["passed"]=bool(row["total"]>=VersionedThresholdConfig.capture_min_holdout and row["errors"]<=VersionedThresholdConfig.capture_max_errors and row["accuracy"]>=VersionedThresholdConfig.capture_min_accuracy)
            method_rules_pass=method_rules_pass and row["passed"]
            per_method[method]=row
        per_scene={}
        scene_rules_pass=True
        for scene,row_value in sorted(by_scene.items()):
            row=dict(row_value)
            row["accuracy"]=row["correct"]/row["total"] if row["total"] else 0.0
            row["coverage"]=row["accepted"]/row["total"] if row["total"] else 0.0
            row["error_upper_95"]=binomial_error_upper(row["errors"],row["accepted"],0.95)
            row["passed"]=bool(row["total"]>=VersionedThresholdConfig.scene_min_holdout and row["errors"]<=VersionedThresholdConfig.scene_max_errors and row["accuracy"]>=VersionedThresholdConfig.scene_min_accuracy)
            scene_rules_pass=scene_rules_pass and row["passed"]
            per_scene[scene]=row
        full_authorized_clusters=set()
        for signature,row in per_action.items():
            if row.get("passed"):
                full_authorized_clusters.update(cluster["id"] for cluster in action_clusters if cluster["canonical_action_signature"]==signature)
        for proto in prototypes:
            cluster_id=str(proto.get("cluster_id"))
            basic_safe=bool(basic_cluster_rows.get(cluster_id,{}).get("passed"))
            full_safe=bool(cluster_id in full_authorized_clusters)
            proto["authorized"]=bool((full_safe or basic_safe) and not proto.get("ambiguous"))
            proto["authorization_level"]="full" if full_safe else "basic_safe" if basic_safe else "none"
            runtime=action_runtime_metadata(proto.get("a"))
            proto["strictness"]=runtime["strictness"]
            proto["cooldown"]=runtime["cooldown"]
            proto["dangerous"]=runtime["dangerous"]
        authorized_prototypes=sum(1 for proto in prototypes if proto.get("authorized"))
        full_authorized_prototypes=sum(1 for proto in prototypes if proto.get("authorized") and proto.get("authorization_level")=="full")
        basic_safe_prototypes=sum(1 for proto in prototypes if proto.get("authorized") and proto.get("authorization_level")=="basic_safe")
        enough,global_pass=evaluate_validation_thresholds(split_info.get("complete"),split_info.get("session_count",0),holdout_count,accepted,coverage,overall_accuracy,error_upper_95,dangerous_false,uncovered_false_accept)
        enough=bool(enough and train_methods)
        action_rules_pass=full_authorized_prototypes>0
        passed=bool(enough and global_pass and action_rules_pass and method_rules_pass and scene_rules_pass and prototypes)
        basic_available=bool(basic_safe_prototypes>0 and train_methods)
        validation_status="passed" if passed else "basic_safe" if basic_available else "insufficient" if not enough or not action_rules_pass or not method_rules_pass else "failed"
        validation={"status":validation_status,"split":str(split_info.get("mode","unknown")),"split_complete":bool(split_info.get("complete")),"split_reason":str(split_info.get("reason","")),"strata":int(split_info.get("strata",0)),"session_count":int(split_info.get("session_count",0)),"holdout_sessions":sorted(holdout_sessions),"required_sessions":VersionedThresholdConfig.required_sessions,"minimum_holdout":VersionedThresholdConfig.review_min_holdout,"minimum_accepted":VersionedThresholdConfig.review_min_accepted,"minimum_ordinary_action_holdout":VersionedThresholdConfig.ordinary_min_positive,"minimum_ordinary_sessions":VersionedThresholdConfig.ordinary_min_sessions,"minimum_dangerous_positive":VersionedThresholdConfig.dangerous_min_positive,"minimum_dangerous_negative":VersionedThresholdConfig.dangerous_min_negative,"minimum_dangerous_sessions":VersionedThresholdConfig.dangerous_min_sessions,"minimum_coverage":VersionedThresholdConfig.minimum_coverage,"maximum_error_upper_95":VersionedThresholdConfig.maximum_error_upper_95,"minimum_overall_accuracy":VersionedThresholdConfig.minimum_overall_accuracy,"maximum_dangerous_false":VersionedThresholdConfig.maximum_dangerous_false,"maximum_uncovered_false_accept":VersionedThresholdConfig.maximum_uncovered_false_accept,"capture_min_holdout":VersionedThresholdConfig.capture_min_holdout,"capture_min_accuracy":VersionedThresholdConfig.capture_min_accuracy,"capture_max_errors":VersionedThresholdConfig.capture_max_errors,"scene_min_holdout":VersionedThresholdConfig.scene_min_holdout,"scene_min_accuracy":VersionedThresholdConfig.scene_min_accuracy,"scene_max_errors":VersionedThresholdConfig.scene_max_errors,"holdout":holdout_count,"accepted":accepted,"errors":errors,"correct":correct,"coverage":coverage,"reject_rate":1.0-coverage,"accepted_error_rate":accepted_error_rate,"error_upper_95":error_upper_95,"overall_accuracy":overall_accuracy,"dangerous_false":dangerous_false,"dangerous_false_rate":dangerous_false_rate,"uncovered_actions":uncovered_actions,"uncovered_rejected":uncovered_rejected,"uncovered_false_accept":uncovered_false_accept,"covered_holdout":covered_holdout,"authorized_prototypes":authorized_prototypes,"full_authorized_prototypes":full_authorized_prototypes,"basic_safe_prototypes":basic_safe_prototypes,"authorized_families":sorted({action_family_key(proto["a"]) for proto in prototypes if proto.get("authorized")}),"basic_safe_authorized_families":sorted({action_family_key(proto["a"]) for proto in prototypes if proto.get("authorization_level")=="basic_safe" and proto.get("authorized")}),"basic_cluster_validation":basic_cluster_rows,"decorrelated_removed":decorrelated_removed,"per_action":per_action,"per_capture_method":per_method,"per_scene":per_scene,"visual_group_intersection":list(split_info.get("visual_group_intersection",[])),"ambiguous_prototypes":sum(1 for proto in prototypes if proto.get("ambiguous")),"training_checksums":train_checksums,"holdout_checksums":holdout_checksums,"checksum_intersection":[]}
        sequence_counts=defaultdict(Counter)
        for session in sorted({self.review_controller.session_of(item) for item in train}):
            ordered_session=sorted((item for item in train if self.review_controller.session_of(item)==session),key=lambda item:float(item.get("created",0.0)))
            history=deque(["<START>","<START>","<START>","<START>"],maxlen=4)
            for item in ordered_session:
                cluster_id=str(item.get("_action_cluster") or "")
                if cluster_id:
                    for size in range(1,5):
                        sequence_counts[str(size)+"|"+"|".join(list(history)[-size:])][cluster_id]+=1
                    signature=str(item.get("_canonical_action_signature") or action_signature(item["a"]))
                    sequence_counts[history[-1]][cluster_id]+=1
                    history.append(signature)
        sequence_model={key:dict(value) for key,value in sequence_counts.items()}
        profile=self.store.load_game_profile(game["id"])
        binding=model_binding_from_samples(train)
        model={"created":time.time(),"samples":len(decorrelated),"training_samples":len(train),"holdout_samples":len(holdout),"invalid_samples":stats["invalid"],"action_clusters":len(action_clusters),"rejection_constraints":rejection_constraints,"prototypes":prototypes,"capture_backends":train_methods,"validation":validation,"training_checksums":train_checksums,"holdout_checksums":holdout_checksums,"sequence_model":sequence_model,"model_binding":binding,"safety_profile_checksum":profile_checksum(profile),"stopped":False}
        if not prototypes:
            raise RuntimeError("复习未生成可用原型")
        self.store.save_model(game["id"],model,validation_status=="passed")
        self.review_distance_cache.clear()
        self.set_progress(100)
        label="通过完整独立验收" if validation_status=="passed" else "已生成基础安全模型，可训练已授权的普通安全动作" if validation_status=="basic_safe" else "验证不足，仅保存不可训练临时模型" if validation_status=="insufficient" else "验证失败，仅保存不可训练临时模型"
        error_text="无可计算值" if accepted_error_rate is None else str(round(accepted_error_rate*100,2))+"%"
        lines=["复习完成，"+label+"：原型"+str(len(prototypes))+"，独立session留出"+str(holdout_count)+"，接受"+str(accepted)+"，覆盖率"+str(round(coverage*100,2))+"%，接受错误率"+error_text+"，95%错误率上界"+str(round(error_upper_95*100,2))+"%，未覆盖动作"+str(uncovered_actions)+"，连续帧去相关移除"+str(decorrelated_removed)+("；留出失败原因："+str(split_info.get("reason")) if split_info.get("reason") else ""),"各动作独立留出验证："]
        for signature,row in sorted(per_action.items()):
            lines.append(signature+"：独立留出正例"+str(row["total"])+"，负例"+str(row["negative_total"])+"，接受"+str(row["accepted"])+"，错误"+str(row["errors"])+"，危险误触"+str(row["false_positive"])+"，训练支持"+str(row.get("basic_training_support",0))+"，一致率"+str(round(float(row.get("basic_training_consistency",0.0))*100,2))+"%，"+("完整授权" if row["passed"] else "基础安全授权" if row.get("basic_safe_passed") else "未授权"))
        lines.append("各采集后端独立验证：")
        for method,row in sorted(per_method.items()):
            lines.append(method+"：留出"+str(row["total"])+"，覆盖率"+str(round(row["coverage"]*100,2))+"%，错误"+str(row["errors"])+"，"+("通过" if row["passed"] else "未通过"))
        lines.append("各视觉场景分层验证：")
        for scene,row in sorted(per_scene.items()):
            lines.append(scene+"：留出"+str(row["total"])+"，准确率"+str(round(row["accuracy"]*100,2))+"%，错误"+str(row["errors"])+"，"+("通过" if row["passed"] else "未通过"))
        return ModeResult("completed","\n".join(lines),{"validation":validation_status})
class TrainingController:
    def __init__(self,app):
        self.app=app
        self.interference_detector=TrainingInterferenceDetector()
        self.frame_gate=TrainingFrameGate()
        self.confirmer=TrainingCandidateConfirmer()
        self.authorizer=TrainingActionAuthorizer()
        self.post_verifier=TrainingPostActionVerifier()
    def interference(self,mouse_event,keyboard_event):
        return self.interference_detector.tripped(mouse_event,keyboard_event)
    def usable_frame(self,frame,backend):
        return self.frame_gate.usable(frame,backend)
    def confirmed(self,count,required):
        return self.confirmer.confirmed(count,required)
    def authorized(self,proto):
        return self.authorizer.authorized(proto)
    def changed(self,before,after,threshold):
        return self.post_verifier.changed(before,after,threshold)
    def run(self):
        return self._run_impl()
    def _run_impl(self):
        app=self.app
        self=app
        game=self.require_game()
        target=self.require_window(False)
        model=self.store.load_trainable_model(game["id"])
        self.validate_model_binding(model,target)
        profile=self.store.load_game_profile(game["id"])
        agent_policy=TaskAgentPolicy(profile)
        if not agent_policy.allowed:
            raise RuntimeError("当前游戏未配置任何自动动作白名单，请先打开“任务与安全”")
        self.active_model_runtime=model
        prototypes=[proto for proto in model["prototypes"] if self.training_controller.authorized(proto) and agent_policy.allowed_action(proto.get("a"))]
        if not prototypes:
            raise RuntimeError("当前模型与任务白名单没有共同的已授权动作")
        allowed_backends={method for proto in prototypes for method in proto.get("capture_methods",[])} or set(model.get("capture_backends",[]))
        calibration=self.ensure_capture_calibration(target,"训练")
        validated_backend=str(calibration.get("validated_backend",""))
        if validated_backend not in allowed_backends:
            raise RuntimeError("当前采集后端未被当前可训练模型授权；请用该后端重新学习并复习")
        self.api.request_foreground(target["hwnd"])
        self.wait_escape_release()
        isolation=StrictInputIsolation(self.stop_event)
        mouse_interrupt=None
        keyboard_interrupt=None
        actions=0
        keyboard_count=0
        mouse_count=0
        recent_actions=deque(["<START>","<START>"],maxlen=4)
        candidate_id=None
        candidate_count=0
        candidate_frame_stamp=0.0
        last_action_signature=""
        last_cluster_id=""
        last_action_time=0.0
        last_action_feature=None
        state_unlocked=True
        no_change_count=0
        previous_feature=None
        previous_frame_stamp=0.0
        state_since=time.monotonic()
        action_hits=defaultdict(deque)
        with ModeSession(self,target) as session:
            frame_buffer=session.start_frames(max(8.0,float(calibration.get("fps",15.0))),2.5,0.1,"training")
            keyboard=session.start_keyboard()
            mouse=session.start_mouse()
            self.lifecycle.mark_running()
            self.mode_state=MODE_RUNNING
            keyboard_interrupt=keyboard.other_event
            mouse_interrupt=mouse.input_event
            def execute_profile_restart(frame):
                nonlocal actions
                restart=normalize_action(profile.get("restart_action"))
                if not restart:
                    return False
                if not agent_policy.allowed_action(restart):
                    raise InputStopped("重新开始动作不在安全白名单")
                if not self.training_controller.usable_frame(frame,validated_backend) or frame.get("method") not in allowed_backends:
                    raise InputStopped("重新开始前画面或采集后端不可用")
                if mouse_interrupt.is_set() or keyboard_interrupt.is_set() or not keyboard.all_released() or not mouse.stable_for(0.45):
                    raise InputStopped("重新开始前检测到人工输入")
                self.api.validate_target(target,True)
                self.api.validate_uipi(target)
                try:
                    if restart.get("kind")!="no_op":
                        self.api.allow_input(self.stop_event)
                        self.set_input_status("允许执行一次已配置的重新开始动作")
                    self.execute_action(target,restart,frame,mouse_interrupt,keyboard,keyboard_interrupt)
                    actions+=1
                    recent_actions.append(action_signature(restart))
                    return True
                finally:
                    self.api.block_input()
                    self.api.release_all_buttons()
            while not self.should_stop():
                key_events=[event for event in keyboard.drain() if event.get("kind")=="other" and event.get("down")]
                mouse_events=mouse.drain()
                if self.training_controller.interference(mouse_interrupt,keyboard_interrupt) or key_events or mouse_events:
                    keyboard_count+=len(key_events)
                    mouse_count+=len(mouse_events)
                    if key_events or keyboard_interrupt.is_set():
                        isolation.signal("keyboard",key_events[0].get("time") if key_events else time.monotonic())
                        reason="检测到非ESC键盘输入，训练立即停止"
                        self.set_input_status("因键盘输入锁定")
                    else:
                        isolation.signal("mouse",mouse_events[0].get("time") if mouse_events else time.monotonic())
                        reason="检测到物理或其他程序注入的鼠标输入，训练立即停止"
                        self.set_input_status("因人工鼠标输入锁定")
                    self.request_mode_stop("stopped",reason)
                    self.mode_state=MODE_STOPPING
                    self.api.block_input()
                    self.api.release_all_buttons()
                    self.set_status(reason+"；不会自动恢复")
                    break
                self.api.block_input()
                self.set_input_status("等待连续确认")
                try:
                    self.api.validate_target(target,True)
                except TargetUnavailable as error:
                    candidate_id=None
                    candidate_count=0
                    self.set_confidence("训练置信度：0%")
                    self.set_input_status("目标窗口不可用，已锁定")
                    self.set_status("目标窗口失去焦点，等待恢复；"+str(error))
                    time.sleep(0.08)
                    continue
                captured=frame_buffer.latest(None,0.8)
                if not self.training_controller.usable_frame(captured,validated_backend):
                    self.set_input_status("检测到黑屏，已锁定" if captured and captured.get("black_frame") else "画面不可用，已锁定")
                    self.set_status("采集画面不可用于训练；等待已验收、非受保护黑屏且后端未冻结的最新帧；"+(frame_buffer.last_error or "尚无画面"))
                    time.sleep(0.08)
                    continue
                current_validated_backend=str(self.api.calibration_for(target).get("validated_backend",validated_backend))
                if current_validated_backend!=validated_backend:
                    if current_validated_backend in allowed_backends:
                        validated_backend=current_validated_backend
                        candidate_id=None
                        candidate_count=0
                        candidate_frame_stamp=0.0
                        self.set_input_status("采集后端切换，等待连续确认")
                        self.set_status("原采集后端已熔断，已切换到剩余已验证后端："+validated_backend)
                        time.sleep(0.1)
                        continue
                    self.set_status("替代采集后端未在模型中验证，拒绝自动动作")
                    time.sleep(0.1)
                    continue
                if captured.get("method")!=validated_backend or captured.get("method") not in allowed_backends:
                    self.set_status("采集后端变化或未在模型中验证，拒绝自动动作；请重新学习和复习")
                    time.sleep(0.1)
                    continue
                feature=captured["f"]
                current_state,current_reward=agent_policy.classify(feature)
                if current_state=="success":
                    self.request_mode_stop("completed","检测到已定义的成功状态，训练完成")
                    break
                if current_state=="failure":
                    outcome=agent_policy.register(feature,{"kind":"no_op","duration":0.1},feature,False)
                    if outcome["stop"]:
                        self.request_mode_stop("stopped","失败状态连续出现达到安全上限"+str(agent_policy.max_failures)+"次，已自动停机")
                        break
                    try:
                        if execute_profile_restart(captured):
                            self.set_status("检测到失败或死亡状态，已执行白名单内的重新开始动作")
                            time.sleep(max(0.1,float(calibration.get("input_delay",0.24))))
                            continue
                    except InputStopped as error:
                        self.request_mode_stop("stopped","失败状态回滚无法安全执行："+str(error))
                        break
                    self.set_status("检测到失败或死亡状态，但未配置重新开始动作；保持锁定")
                    time.sleep(0.12)
                    continue
                if captured["time"]!=previous_frame_stamp:
                    if previous_feature is not None and visual_distance(previous_feature,feature)>float(calibration.get("significant_change",60.0)):
                        state_since=time.monotonic()
                    previous_feature=feature
                    previous_frame_stamp=captured["time"]
                significant=last_action_feature is not None and visual_distance(last_action_feature,feature)>float(calibration.get("significant_change",60.0))
                if significant:
                    state_unlocked=True
                    no_change_count=0
                    state_since=time.monotonic()
                temporal=self.build_temporal_context(frame_buffer,captured,recent_actions,state_since)
                if not temporal_from_context({**temporal,"previous_action_changed_frame":significant}).get("complete"):
                    self.set_status("等待至少3帧短时序上下文")
                    time.sleep(0.05)
                    continue
                temporal["previous_action_changed_frame"]=bool(significant)
                ranked=self.rank_action_candidates(feature,prototypes,last_action_signature,VersionedThresholdConfig.candidate_full_limit,temporal,captured.get("coarse"))
                decision=self.evaluate_action_candidates(ranked)
                if not decision.get("accepted"):
                    candidate_id=None
                    candidate_count=0
                    self.set_input_status("等待连续确认")
                    self.set_confidence("训练置信度："+str(round(float(decision.get("confidence",0.0))*100,1))+"%")
                    suffix="；安全探索仅保持等待，不产生鼠标输入" if profile.get("exploration_enabled") else "；不执行动作并等待请教"
                    self.set_status("训练中："+str(decision.get("reason","识别不确定"))+suffix)
                    time.sleep(0.12)
                    continue
                best=decision["best"]
                cluster_id=best["cluster_id"]
                if candidate_id==cluster_id:
                    if captured["time"]==candidate_frame_stamp:
                        time.sleep(0.025)
                        continue
                    candidate_count+=1
                else:
                    candidate_id=cluster_id
                    candidate_count=1
                candidate_frame_stamp=captured["time"]
                confirmations=max(3,int(calibration.get("confirm_frames",3)))
                self.set_confidence("训练置信度："+str(round(decision["confidence"]*100,1))+"%  连续确认"+str(candidate_count)+"/"+str(confirmations))
                if not self.training_controller.confirmed(candidate_count,confirmations):
                    time.sleep(0.05)
                    continue
                action=normalize_action(best["a"])
                canonical=action_signature(action)
                proto=best["proto"]
                if not self.training_controller.authorized(proto):
                    self.set_status("动作原型未通过独立留出授权，拒绝动作")
                    time.sleep(0.1)
                    continue
                if not agent_policy.allowed_action(action):
                    self.set_status("动作不在当前游戏安全白名单中，拒绝动作："+self.action_text(action))
                    time.sleep(0.1)
                    continue
                if captured["method"] not in proto.get("capture_methods",frozenset()):
                    self.set_status("当前原型未在该采集后端训练，拒绝动作")
                    time.sleep(0.1)
                    continue
                repeat_policy=str(proto.get("repeat_policy","one_shot"))
                max_rate=max(0.25,min(12.0,float(proto.get("max_rate",3.0))))
                if repeat_policy in {"one_shot","hold_until_change"} and last_cluster_id==cluster_id and not state_unlocked:
                    self.set_status("等待画面变化：该动作策略为"+repeat_policy)
                    time.sleep(0.1)
                    continue
                minimum_gap=max(self.action_cooldown(action) if repeat_policy=="one_shot" else 0.0,1.0/max_rate if repeat_policy in {"rate_limited","repeatable"} else 0.0)
                if time.monotonic()-last_action_time<minimum_gap:
                    time.sleep(0.03)
                    continue
                now=time.monotonic()
                hits=action_hits[cluster_id]
                while hits and now-hits[0]>1.0:
                    hits.popleft()
                if len(hits)>=max(1,int(math.ceil(max_rate))):
                    self.set_status("动作专属频率限制中："+self.action_text(action))
                    time.sleep(0.05)
                    continue
                fresh=frame_buffer.latest(None,0.35)
                try:
                    self.api.validate_target(target,True)
                    self.api.validate_uipi(target)
                    if not self.training_controller.usable_frame(fresh,validated_backend) or fresh.get("method") not in allowed_backends or fresh.get("method") not in proto.get("capture_methods",frozenset()):
                        raise InputStopped("动作前最后一帧或采集后端不可用")
                    if keyboard_interrupt.is_set() or not keyboard.all_released():
                        raise InputStopped("检测到键盘输入")
                    if mouse_interrupt.is_set() or not mouse.stable_for(0.45):
                        raise InputStopped("检测到人工鼠标干扰")
                    fresh_temporal=self.build_temporal_context(frame_buffer,fresh,recent_actions,state_since)
                    fresh_temporal["previous_action_changed_frame"]=bool(significant)
                    fresh_ranked=self.rank_action_candidates(fresh["f"],prototypes,last_action_signature,VersionedThresholdConfig.candidate_full_limit,fresh_temporal,fresh.get("coarse"))
                    fresh_decision=self.evaluate_action_candidates(fresh_ranked)
                    if not fresh_decision.get("accepted") or fresh_decision.get("best",{}).get("cluster_id")!=cluster_id:
                        raise InputStopped("动作前模型判断已变化")
                    if not self.training_controller.confirmed(candidate_count,confirmations):
                        raise InputStopped("动作前连续帧确认不足")
                    before=fresh["f"]
                    needs_input=action.get("kind")!="no_op"
                    if needs_input:
                        self.set_input_status("允许执行单个动作")
                        self.api.allow_input(self.stop_event)
                    else:
                        self.set_input_status("已锁定")
                    self.set_status("训练中："+self.action_text(action)+"；全部安全条件已通过；采集="+fresh["method"])
                    self.execute_action(target,action,fresh,mouse_interrupt,keyboard,keyboard_interrupt)
                except InputStopped:
                    if mouse_interrupt.is_set() or keyboard_interrupt.is_set() or not keyboard.all_released():
                        kind="mouse" if mouse_interrupt.is_set() else "keyboard"
                        isolation.signal(kind,time.monotonic())
                        reason="检测到物理或其他程序注入的鼠标输入，训练立即停止" if kind=="mouse" else "检测到非ESC键盘输入，训练立即停止"
                        self.request_mode_stop("stopped",reason)
                        self.mode_state=MODE_STOPPING
                        self.api.block_input()
                        self.api.release_all_buttons()
                        self.set_status(reason+"；不会自动恢复")
                    raise
                except TargetUnavailable as error:
                    candidate_id=None
                    candidate_count=0
                    self.set_status(str(error))
                    self.set_input_status("目标身份变化，已锁定")
                    continue
                finally:
                    self.api.block_input()
                    if not mouse_interrupt.is_set() and not keyboard_interrupt.is_set() and keyboard.all_released():
                        self.set_input_status("已锁定")
                action_end=time.monotonic()
                actions+=1
                hits.append(action_end)
                recent_actions.append(canonical)
                last_action_signature=canonical
                last_cluster_id=cluster_id
                last_action_time=action_end
                last_action_feature=before
                state_unlocked=repeat_policy in {"repeatable","rate_limited"}
                candidate_count=0
                delay=float(calibration.get("input_delay",0.24))
                deadline=time.monotonic()+delay
                while time.monotonic()<deadline and not self.should_stop():
                    time.sleep(0.02)
                after=None
                wait_end=time.monotonic()+max(0.35,delay*2.0)
                while time.monotonic()<wait_end and not self.should_stop():
                    candidate_after=frame_buffer.latest_after(action_end)
                    if self.training_controller.usable_frame(candidate_after,validated_backend):
                        after=candidate_after
                        break
                    time.sleep(0.025)
                changed=self.training_controller.changed(before,after,float(calibration.get("post_action_change",45.0)))
                outcome=agent_policy.register(before,action,after["f"] if after is not None else None,changed)
                if changed:
                    no_change_count=0
                    state_unlocked=True
                    state_since=time.monotonic()
                else:
                    no_change_count+=1
                    if repeat_policy in {"one_shot","hold_until_change"} and no_change_count>=2:
                        state_unlocked=False
                        self.set_status("动作后未出现预期画面变化，暂停并等待请教")
                if outcome["state"]=="success":
                    self.request_mode_stop("completed","检测到已定义的成功状态，训练完成")
                    break
                if outcome["stop"]:
                    self.request_mode_stop("stopped","连续失败或无变化达到安全上限"+str(agent_policy.max_failures)+"次，已自动停机")
                    break
                if outcome["state"]=="failure" and profile.get("restart_action") and not self.should_stop():
                    restart_frame=after or frame_buffer.latest(None,0.35)
                    try:
                        if execute_profile_restart(restart_frame):
                            self.set_status("检测到失败状态，已执行白名单内的重新开始动作")
                    except InputStopped as error:
                        self.request_mode_stop("stopped","失败状态回滚无法安全执行："+str(error))
                        break
                time.sleep(0.05)
        requested=self.lifecycle.snapshot()[3]
        final_status=requested if requested in {"completed","stopped","failed"} else ("stopped" if self.stop_event and self.stop_event.is_set() else "completed")
        summary=("训练完成" if final_status=="completed" else "训练已停止")+"，AI执行"+str(actions)+"个鼠标动作；检测到非ESC键盘输入"+str(keyboard_count)+"次，人工或外部注入鼠标输入"+str(mouse_count)+"次"
        return ModeResult(final_status,summary,{"strict_input_violation":isolation.kind,"task_history":list(agent_policy.history)})
class TeachingController:
    def __init__(self,app):
        self.app=app
    def run(self):
        app=self.app
        game=app.require_game()
        target=app.require_window(False)
        samples,stats=app.store.load_samples(game["id"])
        try:
            model=app.store.load_model(game["id"])
        except Exception:
            model=None
        app.active_model_runtime=model
        prototypes=[item for item in (model.get("prototypes",[]) if model else []) if feature_valid(item.get("f")) and normalize_action(item.get("a"))]
        historical=[]
        for index,item in enumerate(samples):
            if index%64==0 and app.should_stop():
                raise InputStopped("请教初始化已停止")
            action=normalize_action(item.get("a"))
            if feature_valid(item.get("f")) and action:
                historical.append({"id":str(item.get("checksum",uuid.uuid4().hex)),"f":item["f"],"coarse":item.get("coarse") if isinstance(item.get("coarse"),(bytes,bytearray)) and len(item.get("coarse"))==COARSE_LEN else coarse_feature(item["f"]),"a":action,"cluster_id":"history|"+action_signature(action),"canonical_action_signature":action_signature(action),"repeat_policy":str(item.get("repeat_policy","one_shot")),"source":"sample"})
        calibration=app.ensure_capture_calibration(target,"请教")
        session_id="teach|"+uuid.uuid4().hex
        app.store.begin_learning_session(game["id"],session_id)
        sources=[]
        for proto in prototypes:
            sources.append({"a":normalize_action(proto["a"]),"repeat_policy":str(proto.get("repeat_policy","one_shot")),"cluster_id":str(proto.get("cluster_id",""))})
        for item in historical:
            sources.append({"a":item["a"],"repeat_policy":item.get("repeat_policy","one_shot"),"cluster_id":item["cluster_id"]})
        sources.extend({"a":action,"repeat_policy":"one_shot","cluster_id":"basic|"+action_signature(action)} for action in app.basic_actions())
        unique=[]
        seen=set()
        for entry in sources:
            signature=action_signature(entry["a"])
            if signature and signature not in seen:
                seen.add(signature)
                unique.append(entry)
        with ModeSession(app,target) as session:
            buffer=session.start_frames(max(12.0,float(calibration.get("fps",15.0))),2.5,0.1,"teaching")
            model_version=str((model or {}).get("saved",(model or {}).get("created","none")))
            producer=AskQuestionProducer(app,buffer,prototypes,historical,unique,game["id"],model_version).start()
            session.add_resource("TeachingQuestionProducer",producer)
            app.ask_session_id=session_id
            app.ask_buffer=buffer
            app.ask_producer=producer
            app.ask_counts={"saved":0,"duplicates":0,"skipped":0,"rejected":0,"ocr":0}
            answer_queue=queue.Queue()
            app.ask_answer_queue=answer_queue
            producer.request(deque(["<START>","<START>"],maxlen=4),time.monotonic())
            initial=None
            deadline=time.monotonic()+5.0
            while initial is None and time.monotonic()<deadline and not app.should_stop():
                packet=producer.get_result(0.15)
                if packet and not packet.get("error") and packet.get("frame") is not None:
                    initial=packet
                elif packet and packet.get("error"):
                    app.set_status("请教初始化等待画面："+str(packet["error"]))
                    producer.request(deque(["<START>","<START>"],maxlen=4),time.monotonic())
            if app.should_stop():
                raise InputStopped("请教初始化已停止")
            if initial is None:
                raise CaptureUnavailable("请教初始化未在限定时间内生成第一道题")
            created=threading.Event()
            app.ui(lambda:app._create_ask_window({"game":game,"target":target,"buffer":buffer,"producer":producer,"packet":initial,"created":created}))
            while not created.wait(0.05):
                if app.should_stop():
                    raise InputStopped("请教初始化已停止")
            while not app.should_stop():
                try:
                    command=answer_queue.get(timeout=0.05)
                except queue.Empty:
                    continue
                callback=command.get("callback")
                try:
                    kind=str(command.get("kind",""))
                    frame=command.get("frame") or {}
                    entry=command.get("entry") or {}
                    recent_actions=command.get("recent_actions") or ["<START>","<START>"]
                    state_since=safe_float(command.get("state_since"),time.monotonic())
                    if kind=="skip":
                        app.ask_counts["skipped"]+=1
                        result={"saved":False,"action":None}
                    else:
                        if not frame.get("usable_for_teaching"):
                            raise CaptureUnavailable("当前画面不可用于请教")
                        temporal=app.build_temporal_context(buffer,frame,recent_actions,state_since)
                        temporal["previous_action_changed_frame"]=True
                        policy=str(entry.get("repeat_policy","one_shot"))
                        context=app.sample_context(recent_actions[-1] if recent_actions else "",0,True,frame.get("motion_valid",False),session_id,frame.get("method","unknown"),policy,temporal)
                        if kind in {"choose","custom"}:
                            action=normalize_action(entry.get("a"))
                            if not action:
                                raise RuntimeError("请教动作无效")
                            source="teach_live_custom" if kind=="custom" else "teach_live"
                            weight=3.5 if kind=="custom" else 3.0
                            saved=app.store.append_sample(game["id"],frame["f"],action,source,context,frame.get("gray"),weight)
                            app.ask_counts["saved" if saved else "duplicates"]+=1
                            result={"saved":saved,"action":action}
                        elif kind=="reject":
                            app.store.append_rejection(game["id"],frame["f"],command.get("candidates") or [],"teach_live_reject",frame.get("gray"),context)
                            app.ask_counts["rejected"]+=1
                            result={"saved":False,"action":None}
                        else:
                            raise RuntimeError("未知请教命令")
                    if callback:
                        app.ui(lambda callback=callback,result=result:callback(result,None))
                except Exception as error:
                    message="请教数据库或题目处理失败："+str(error)
                    if callback:
                        app.ui(lambda callback=callback,message=message:callback(None,message))
                    app.request_mode_stop("failed",message)
                    break
        status=app.lifecycle.snapshot()[3]
        if status=="failed":
            app.store.invalidate_learning_session(game["id"],session_id,app.lifecycle.snapshot()[4] or "teaching_failed")
        else:
            app.store.validate_learning_session(game["id"],session_id)
        counts=app.ask_counts if isinstance(app.ask_counts,dict) else {"saved":0,"duplicates":0,"skipped":0,"rejected":0,"ocr":0}
        summary="请教已结束：已保存"+str(counts.get("saved",0))+"，重复未保存"+str(counts.get("duplicates",0))+"，跳过"+str(counts.get("skipped",0))+"，拒绝记录"+str(counts.get("rejected",0))+"，OCR语义"+str(counts.get("ocr",0))+"；模型需要复习"
        if status=="failed":
            return ModeResult("failed",app.lifecycle.snapshot()[4] or summary)
        return ModeResult(status if status in {"completed","stopped"} else "stopped",summary,{"samples":stats.get("valid",0)})
    def create_window(self,prepared):
        app=self.app
        self=app
        created=prepared.get("created")
        try:
            if self.mode!="请教" or self.stop_event is None or self.stop_event.is_set() or self.closing:
                return
            game=prepared["game"]
            target=prepared["target"]
            buffer=prepared["buffer"]
            producer=prepared["producer"]
            initial=prepared["packet"]
            self.lifecycle.mark_running()
            self.mode_state=MODE_RUNNING
            self.api.block_input()
            self.set_input_status("已锁定")
            self.status.set("请教已开始：题目由后台线程生成；ESC或“停止”结束")
            win=tk.Toplevel(self.root)
            self.ask_window=win
            win.title("请教")
            win.geometry("780x780")
            win.minsize(700,700)
            win.transient(self.root)
            win.bind("<Unmap>",lambda event:buffer.set_preview_active(False))
            win.bind("<Map>",lambda event:buffer.set_preview_active(True))
            win.bind("<FocusOut>",lambda event:buffer.set_preview_active(False))
            win.bind("<FocusIn>",lambda event:buffer.set_preview_active(True))
            frame=ttk.Frame(win,padding=16)
            frame.pack(fill="both",expand=True)
            ttk.Label(frame,text="请选择当前画面中AI应该执行的鼠标动作",font=("Microsoft YaHei UI",14,"bold")).pack(anchor="w")
            ttk.Label(frame,text="候选排序在后台线程完成；请教窗口在前台时不要求游戏窗口也在前台。",wraplength=730).pack(anchor="w",pady=(4,10))
            canvas=tk.Canvas(frame,width=ASK_CANVAS_W,height=ASK_CANVAS_H,bg="black",highlightthickness=1,highlightbackground="#777777")
            canvas.pack()
            preview_info=tk.StringVar(value="等待彩色教学预览")
            ttk.Label(frame,textvariable=preview_info,wraplength=730).pack(anchor="w",fill="x",pady=(6,0))
            choice_frame=ttk.Frame(frame)
            choice_frame.pack(fill="both",expand=True,pady=(10,0))
            answer_buttons=[]
            state={"frame":None,"choices":[],"candidates":[],"image":None,"locked":False,"recent_actions":deque(["<START>","<START>"],maxlen=4),"state_since":time.monotonic(),"waiting":False}
            def schedule(delay,callback):
                if self.ask_window is None:
                    return
                holder={"id":None}
                def wrapped():
                    self.ask_after_ids.discard(holder["id"])
                    if self.ask_window is not None:
                        callback()
                holder["id"]=win.after(delay,wrapped)
                self.ask_after_ids.add(holder["id"])
            def set_locked(value):
                state["locked"]=bool(value)
                for index,button in enumerate(answer_buttons):
                    button.configure(state="normal" if not value and index<len(state["choices"]) else "disabled")
                skip_button.configure(state="disabled" if value else "normal")
                reject_button.configure(state="disabled" if value else "normal")
                custom_button.configure(state="disabled" if value else "normal")
                ocr_button.configure(state="disabled" if value else "normal")
            def render(packet):
                question_frame=packet["frame"]
                choices=packet["choices"]
                preview=preview_rgb_bytes(question_frame.get("preview_rgb")) or bytes(PREVIEW_W*PREVIEW_H*3)
                ppm=b"P6\n"+str(PREVIEW_W).encode("ascii")+b" "+str(PREVIEW_H).encode("ascii")+b"\n255\n"+preview
                image=tk.PhotoImage(data=base64.b64encode(ppm).decode("ascii"),format="PPM")
                scaled=image.zoom(2,2)
                state["image"]=(image,scaled)
                canvas.delete("all")
                canvas.create_image(ASK_PREVIEW_X,ASK_PREVIEW_Y,image=scaled,anchor="nw")
                colors=("#00ffff","#ffff00","#ff66ff","#66ff66")
                for index,entry in enumerate(choices[:4]):
                    action=normalize_action(entry.get("a"))
                    if not action or action["kind"]=="no_op":
                        continue
                    points=[]
                    for point in action.get("path") or []:
                        cx,cy=PreviewCoordinateMapper.to_canvas(point)
                        points.extend([cx,cy])
                    color=colors[index%len(colors)]
                    if len(points)>=4:
                        canvas.create_line(*points,fill=color,width=3,arrow="last")
                    if len(points)>=2:
                        canvas.create_oval(points[-2]-6,points[-1]-6,points[-2]+6,points[-1]+6,outline=color,width=3)
                        canvas.create_text(points[-2]+10,points[-1]-10,text=chr(65+index),fill=color,font=("Microsoft YaHei UI",12,"bold"),anchor="sw")
                latest=buffer.latest(None,2.0)
                is_latest=bool(latest and abs(float(latest["time"])-float(question_frame.get("time",0)))<0.05)
                warnings=[]
                if question_frame.get("protected_or_black"):
                    warnings.append("黑屏/受保护画面")
                if question_frame.get("stale"):
                    warnings.append("长时间重复")
                if question_frame.get("backend_changed"):
                    warnings.append("采集后端变化")
                if not question_frame.get("backend_validated"):
                    warnings.append("后端未验收")
                if not question_frame.get("capture_valid"):
                    warnings.append("画面无效")
                stamp=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(float(question_frame.get("wall_time",time.time()))))
                preview_info.set("采集时间："+stamp+"  后端："+str(question_frame.get("method","未知"))+"  最新帧："+("是" if is_latest else "否")+"  质量告警："+("、".join(warnings) if warnings else "无"))
            def apply_packet(packet):
                if self.ask_window is None:
                    return
                state["waiting"]=False
                state["frame"]=packet["frame"]
                state["choices"]=packet["choices"]
                state["candidates"]=packet["candidates"]
                render(packet)
                for index,button in enumerate(answer_buttons):
                    if index<len(state["choices"]):
                        button.configure(text=chr(65+index)+". "+self.action_text(state["choices"][index]["a"]))
                    else:
                        button.configure(text=chr(65+index)+". 无可用答案")
                set_locked(False)
            def poll_question():
                if self.ask_window is None or self.stop_event is None or self.stop_event.is_set():
                    return
                packet=producer.get_result(0.0)
                if packet is None:
                    schedule(45,poll_question)
                    return
                if packet.get("error"):
                    self.status.set("请教等待可用画面："+str(packet["error"]))
                    producer.request(state["recent_actions"],state["state_since"])
                    schedule(160,poll_question)
                    return
                apply_packet(packet)
            def request_question():
                if self.ask_window is None or state["waiting"]:
                    return
                state["waiting"]=True
                set_locked(True)
                producer.request(state["recent_actions"],state["state_since"])
                schedule(20,poll_question)
            def finish_answer(result,error):
                if self.ask_window is None:
                    return
                if error:
                    self._fail_active_mode(error)
                    return
                if result and result.get("saved") and result.get("action"):
                    state["recent_actions"].append(action_signature(result["action"]))
                    state["state_since"]=time.monotonic()
                counts=self.ask_counts or {}
                self.status.set("请教中：已保存"+str(counts.get("saved",0))+"，重复未保存"+str(counts.get("duplicates",0))+"，跳过"+str(counts.get("skipped",0))+"，拒绝记录"+str(counts.get("rejected",0))+"；模型需要复习")
                schedule(100,request_question)
            def queue_answer(kind,entry=None,candidates=None):
                if state["locked"] or self.ask_answer_queue is None:
                    return
                set_locked(True)
                command={"kind":kind,"frame":state["frame"],"entry":entry or {},"candidates":candidates or [],"recent_actions":list(state["recent_actions"]),"state_since":state["state_since"],"callback":finish_answer}
                self.ask_answer_queue.put(command)
            def choose(index):
                if index<len(state["choices"]):
                    queue_answer("choose",state["choices"][index])
            def skip():
                queue_answer("skip")
            def reject():
                queue_answer("reject",{},state["candidates"])
            def ocr_teach():
                if state["locked"] or state["frame"] is None:
                    return
                set_locked(True)
                def reopen_actions():
                    if self.ask_window is not None:
                        try:
                            set_locked(False)
                        except Exception:
                            pass
                try:
                    self.open_ocr_teaching_dialog(win,game,buffer,state["frame"],reopen_actions)
                except Exception as error:
                    set_locked(False)
                    self.show_error("OCR请教无法启动："+str(error))
            def custom():
                if state["locked"] or state["image"] is None:
                    return
                set_locked(True)
                dialog=tk.Toplevel(win)
                dialog_state={"closed":False}
                dialog.title("自定义鼠标动作")
                dialog.geometry("760x650")
                dialog.transient(win)
                dialog.grab_set()
                controls=ttk.Frame(dialog,padding=10)
                controls.pack(fill="x")
                kind_var=tk.StringVar(value="click")
                button_var=tk.StringVar(value="left")
                duration_var=tk.StringVar(value="0.12")
                delta_var=tk.StringVar(value="120")
                policy_var=tk.StringVar(value="one_shot")
                fields=[("动作",kind_var,["click","double_click","long_press","drag","scroll_v","scroll_h","move","hover","no_op"]),("按钮",button_var,["left","right","middle"]),("重复策略",policy_var,["one_shot","repeatable","hold_until_change","rate_limited"])]
                for column,(label,var,values) in enumerate(fields):
                    ttk.Label(controls,text=label).grid(row=0,column=column,sticky="w",padx=4)
                    ttk.Combobox(controls,textvariable=var,values=values,state="readonly",width=18).grid(row=1,column=column,padx=4)
                ttk.Label(controls,text="持续秒").grid(row=2,column=0,sticky="w",padx=4,pady=(8,0))
                ttk.Entry(controls,textvariable=duration_var,width=20).grid(row=3,column=0,padx=4,sticky="w")
                ttk.Label(controls,text="滚轮增量").grid(row=2,column=1,sticky="w",padx=4,pady=(8,0))
                ttk.Entry(controls,textvariable=delta_var,width=20).grid(row=3,column=1,padx=4,sticky="w")
                ttk.Label(dialog,text="只能在640×360游戏预览区域内单击或拖动；边框区域会被拒绝。",wraplength=720).pack(pady=(0,8))
                custom_canvas=tk.Canvas(dialog,width=ASK_CANVAS_W,height=ASK_CANVAS_H,bg="black",highlightthickness=1,highlightbackground="#777777")
                custom_canvas.pack()
                custom_canvas.create_image(ASK_PREVIEW_X,ASK_PREVIEW_Y,image=state["image"][1],anchor="nw")
                path_state={"start":None,"end":None,"line":None}
                error_var=tk.StringVar()
                ttk.Label(dialog,textvariable=error_var).pack()
                def draw_path():
                    if path_state["line"]:
                        custom_canvas.delete(path_state["line"])
                        path_state["line"]=None
                    if path_state["start"] is not None and path_state["end"] is not None:
                        sx,sy=PreviewCoordinateMapper.to_canvas(path_state["start"])
                        ex,ey=PreviewCoordinateMapper.to_canvas(path_state["end"])
                        path_state["line"]=custom_canvas.create_line(sx,sy,ex,ey,width=3,arrow="last")
                def press(event):
                    point=PreviewCoordinateMapper.to_normalized(event.x,event.y)
                    if point is None:
                        error_var.set("点击位于预览边框，已拒绝；请在游戏画面内操作")
                        return
                    error_var.set("")
                    path_state["start"]=point
                    path_state["end"]=list(point)
                    draw_path()
                def motion_event(event):
                    if path_state["start"] is None:
                        return
                    point=PreviewCoordinateMapper.to_normalized(event.x,event.y)
                    if point is None:
                        error_var.set("拖动越出游戏画面，当前坐标未记录")
                        return
                    error_var.set("")
                    path_state["end"]=point
                    draw_path()
                def release(event):
                    motion_event(event)
                def cancel():
                    if self.close_dialog(dialog,dialog_state):
                        set_locked(False)
                def submit():
                    try:
                        kind=kind_var.get()
                        duration=float(duration_var.get())
                        if kind=="no_op":
                            raw={"kind":kind,"duration":duration}
                        else:
                            if path_state["end"] is None:
                                raise ValueError("请先在游戏预览区域内选择位置")
                            if kind in {"scroll_v","scroll_h"}:
                                raw={"kind":kind,"delta":int(delta_var.get()),"path":[path_state["end"]],"duration":duration}
                            elif kind in {"click","double_click","long_press"}:
                                raw={"kind":kind,"button":button_var.get(),"path":[path_state["end"]],"duration":duration}
                            elif kind=="drag":
                                raw={"kind":kind,"button":button_var.get(),"path":[path_state["start"],path_state["end"]],"duration":duration}
                            else:
                                raw={"kind":kind,"path":[path_state["start"],path_state["end"]],"duration":duration}
                        action=normalize_action(raw)
                        if not action:
                            raise ValueError("动作参数无效")
                        self.close_dialog(dialog,dialog_state)
                        state["locked"]=False
                        queue_answer("custom",{"a":action,"repeat_policy":policy_var.get()})
                    except Exception as error:
                        error_var.set(str(error))
                custom_canvas.bind("<ButtonPress-1>",press)
                custom_canvas.bind("<B1-Motion>",motion_event)
                custom_canvas.bind("<ButtonRelease-1>",release)
                actions_frame=ttk.Frame(dialog,padding=10)
                actions_frame.pack()
                ttk.Button(actions_frame,text="确认",command=submit).pack(side="left",padx=6)
                ttk.Button(actions_frame,text="取消",command=cancel).pack(side="left",padx=6)
                dialog.protocol("WM_DELETE_WINDOW",cancel)
                dialog.bind("<Escape>",lambda event:cancel())
            for index in range(4):
                button=ttk.Button(choice_frame,text=chr(65+index),command=lambda position=index:choose(position))
                button.pack(fill="x",pady=3,ipady=6)
                answer_buttons.append(button)
            tools=ttk.Frame(frame)
            tools.pack(fill="x",pady=(8,0))
            skip_button=ttk.Button(tools,text="跳过此题",command=skip)
            skip_button.pack(side="left",padx=(0,6))
            reject_button=ttk.Button(tools,text="都不正确",command=reject)
            reject_button.pack(side="left",padx=6)
            custom_button=ttk.Button(tools,text="自定义动作",command=custom)
            custom_button.pack(side="left",padx=6)
            ocr_button=ttk.Button(tools,text="OCR数字语义",command=ocr_teach)
            ocr_button.pack(side="left",padx=6)
            ttk.Button(tools,text="结束请教",command=lambda:self.close_ask(reason="completed")).pack(side="right")
            win.protocol("WM_DELETE_WINDOW",lambda:self.close_ask(reason="stopped"))
            self.ask_escape_armed=not self.api.key_down(0x1B)
            def poll_escape():
                if self.ask_window is None:
                    return
                down=self.api.key_down(0x1B)
                if not down:
                    self.ask_escape_armed=True
                elif self.ask_escape_armed:
                    self.close_ask(reason="stopped")
                    return
                schedule(45,poll_escape)
            apply_packet(initial)
            poll_escape()
            win.wait_visibility()
            win.focus_force()
        except Exception as error:
            self._fail_active_mode("请教界面创建失败："+str(error))
        finally:
            if created is not None:
                created.set()
class DataStore:
    def __init__(self,base=None):
        local=os.environ.get("LOCALAPPDATA")
        self.base=Path(base) if base is not None else (Path(local) if local else Path.home()/"AppData"/"Local")/APP_NAME
        self.base.mkdir(parents=True,exist_ok=True)
        usage=shutil.disk_usage(self.base)
        if int(usage.free)<MIN_FREE_DISK:
            raise RuntimeError("剩余磁盘空间不足256MB，拒绝启动以避免数据库损坏")
        self.db_path=self.base/"universal_game_ai.db"
        self.logger=LightweightLogger(self.base/"runtime_errors.jsonl")
        self.lock=threading.RLock()
        self.pending_lock=threading.RLock()
        self.writer_condition=threading.Condition(self.pending_lock)
        self.model_cache={}
        self.closed=False
        self.closing=False
        self.read_only=False
        self.read_only_reason=""
        self.corrupt_backup=None
        self.invalid_rows=defaultdict(int)
        self.pending_samples=[]
        self.writer_inflight=0
        self.blocked_game_ids=set()
        self.blocked_sessions=set()
        self.pending_event=threading.Event()
        self.writer_stop=threading.Event()
        self.writer_error=None
        self.writer_before_commit=None
        self.writer_error_callback=None
        self.writer_thread=None
        self.writer_db=None
        self.db=ThreadLocalSQLite(self.db_path,False)
        try:
            result=self.db.execute("PRAGMA quick_check").fetchone()
            if not result or str(result[0]).lower()!="ok":
                raise RuntimeError(str(result[0]) if result else "quick_check无结果")
        except Exception as error:
            try:
                self.db.close()
            except Exception:
                pass
            self.corrupt_backup=self.create_recovery_backup("quick_check_failed")
            self.db=ThreadLocalSQLite(self.db_path,True)
            self.read_only=True
            self.read_only_reason="数据库quick_check失败，已只读打开；恢复备份："+str(self.corrupt_backup)+"；"+str(error)
            return
        self._initialize_schema()
        self._migrate_legacy()
        self.writer_thread=threading.Thread(target=self._writer_loop,name="UniversalGameAI-SampleWriter",daemon=True)
        self.writer_thread.start()
    def set_writer_error_callback(self,callback):
        self.writer_error_callback=callback
    def _notify_writer_error(self,value):
        if value:
            self.logger.write("SAMPLE_WRITER_ERROR_STATE",details={"writer_error":str(value)})
        callback=self.writer_error_callback
        if callback is not None:
            try:
                callback(value)
            except Exception as error:
                self.logger.write("SAMPLE_WRITER_CALLBACK_FAILED",error)
    def _ensure_writable(self):
        if self.read_only:
            raise RuntimeError(self.read_only_reason or "数据库处于只读恢复模式")
    def create_recovery_backup(self,reason="manual"):
        stamp=time.strftime("%Y%m%d_%H%M%S")
        folder=self.base/("recovery_"+stamp+"_"+str(reason).replace(" ","_"))
        folder.mkdir(parents=True,exist_ok=True)
        for suffix in ("","-wal","-shm"):
            source=Path(str(self.db_path)+suffix)
            if source.exists():
                shutil.copy2(source,folder/source.name)
        self._trim_recovery_backups()
        return folder
    def _trim_recovery_backups(self):
        folders=sorted((item for item in self.base.glob("recovery_*") if item.is_dir()),key=lambda item:item.stat().st_mtime,reverse=True)
        total=0
        for folder in folders:
            size=sum(path.stat().st_size for path in folder.rglob("*") if path.is_file())
            total+=size
            if total>RECOVERY_BACKUP_LIMIT:
                shutil.rmtree(folder,ignore_errors=True)
    def light_checkpoint(self):
        self.sample_write_barrier()
        with self.lock:
            try:
                self.db.execute("PRAGMA wal_checkpoint(PASSIVE)")
                self.db.execute("PRAGMA optimize")
            except Exception as error:
                self.logger.write("DATABASE_LIGHT_CHECKPOINT_FAILED",error)
    def default_game_profile(self):
        return {"goal":"模仿已学习的鼠标操作并在不确定时停止","allowed_families":["no_op","click|left","move","hover","scroll_v|1","scroll_v|-1"],"max_consecutive_failures":3,"exploration_enabled":False,"restart_action":None,"success_states":[],"failure_states":[],"success_reward":1.0,"failure_reward":-1.0,"step_penalty":-0.01,"updated":0.0}
    def load_game_profile(self,gid):
        profile=self.default_game_profile()
        try:
            with self.lock:
                row=self.db.execute("SELECT payload,checksum FROM game_profiles WHERE game_id=?",(str(gid),)).fetchone()
            if row:
                raw=str(row["payload"])
                if hashlib.sha256(raw.encode("utf-8")).hexdigest()==str(row["checksum"]):
                    value=json.loads(raw)
                    if isinstance(value,dict):
                        profile.update(value)
        except Exception as error:
            self.logger.write("GAME_PROFILE_LOAD_FAILED",error,game_id=gid)
        return profile
    def save_game_profile(self,gid,profile):
        self._ensure_writable()
        value=self.default_game_profile()
        if isinstance(profile,dict):
            value.update(profile)
        value["goal"]=str(value.get("goal","")).strip()[:2000] or "模仿已学习的鼠标操作并在不确定时停止"
        value["allowed_families"]=sorted({str(item) for item in value.get("allowed_families",[]) if str(item)})
        value["success_states"]=sorted({str(item) for item in value.get("success_states",[]) if str(item)})
        value["failure_states"]=sorted({str(item) for item in value.get("failure_states",[]) if str(item)})
        value["max_consecutive_failures"]=safe_int(value.get("max_consecutive_failures",3),3,1,20)
        value["exploration_enabled"]=bool(value.get("exploration_enabled",False))
        value["restart_action"]=normalize_action(value.get("restart_action")) if value.get("restart_action") else None
        value["updated"]=time.time()
        raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))
        checksum=hashlib.sha256(raw.encode("utf-8")).hexdigest()
        with self.lock,self.db:
            self.db.execute("INSERT OR REPLACE INTO game_profiles(game_id,updated,payload,checksum) VALUES(?,?,?,?)",(str(gid),value["updated"],raw,checksum))
            self.db.execute("UPDATE games SET needs_review=1 WHERE id=?",(str(gid),))
        self.model_cache.pop(str(gid),None)
        return value
    def quarantine_corrupt_row(self,table_name,row_id,game_id,reason,payload=""):
        if self.read_only:
            return
        try:
            with self.lock,self.db:
                self.db.execute("INSERT OR IGNORE INTO corrupt_rows(source_table,source_id,game_id,created,reason,payload) VALUES(?,?,?,?,?,?)",(str(table_name),safe_int(row_id,0),str(game_id),time.time(),str(reason)[:2000],str(payload)[:16000]))
        except Exception as error:
            self.logger.write("CORRUPT_ROW_QUARANTINE_FAILED",error,game_id=game_id,details={"table":str(table_name),"row_id":safe_int(row_id,0)})
    @contextmanager
    def critical_transaction(self):
        self._ensure_writable()
        with self.lock:
            self.db.execute("PRAGMA synchronous=FULL")
            self.db.execute("BEGIN IMMEDIATE")
            try:
                yield
                self.db.commit()
            except Exception as error:
                self.db.rollback()
                self.logger.write("DATABASE_CRITICAL_TRANSACTION_FAILED",error)
                raise
            finally:
                self.db.execute("PRAGMA synchronous=NORMAL")
    def close_current_thread(self):
        return self.db.close_current_thread() if self.db is not None else False
    def connection_count(self):
        return self.db.connection_count() if self.db is not None else 0
    def log_error(self,code,error=None,mode=None,game_id=None,window_identity=None,details=None):
        return self.logger.write(code,error,mode=mode,game_id=game_id,window_identity=window_identity,details=details)
    def begin_learning_session(self,gid,session_id,started=None):
        self._ensure_writable()
        game_id=str(gid)
        sid=str(session_id)
        stamp=float(time.time() if started is None else started)
        with self.pending_lock:
            self.blocked_sessions.discard((game_id,sid))
        with self.critical_transaction():
            if not self.db.execute("SELECT 1 FROM games WHERE id=?",(game_id,)).fetchone():
                raise RuntimeError("游戏不存在")
            self.db.execute("INSERT INTO learning_sessions(game_id,session_id,status,started,finished,invalid_reason) VALUES(?,?,'staging',?,NULL,'') ON CONFLICT(game_id,session_id) DO UPDATE SET status='staging',started=excluded.started,finished=NULL,invalid_reason=''",(game_id,sid,stamp))
        return sid
    def learning_session_status(self,gid,session_id):
        with self.lock:
            row=self.db.execute("SELECT status,started,finished,invalid_reason FROM learning_sessions WHERE game_id=? AND session_id=?",(str(gid),str(session_id))).fetchone()
        return dict(row) if row else None
    def invalidate_learning_session(self,gid,session_id,reason="invalid",finished=None):
        self._ensure_writable()
        game_id=str(gid)
        sid=str(session_id)
        stamp=float(time.time() if finished is None else finished)
        with self.pending_lock:
            self.blocked_sessions.add((game_id,sid))
        with self.critical_transaction():
            cursor=self.db.execute("UPDATE learning_sessions SET status='invalid',finished=?,invalid_reason=? WHERE game_id=? AND session_id=?",(stamp,str(reason)[:2000],game_id,sid))
            if int(cursor.rowcount or 0)==0:
                self.db.execute("INSERT INTO learning_sessions(game_id,session_id,status,started,finished,invalid_reason) VALUES(?,?,'invalid',?,?,?)",(game_id,sid,stamp,stamp,str(reason)[:2000]))
        return True
    def validate_learning_session(self,gid,session_id,finished=None):
        game_id=str(gid)
        sid=str(session_id)
        with self.pending_lock:
            self.blocked_sessions.add((game_id,sid))
            self.writer_condition.notify_all()
        self.sample_write_barrier()
        stamp=float(time.time() if finished is None else finished)
        with self.critical_transaction():
            row=self.db.execute("SELECT status FROM learning_sessions WHERE game_id=? AND session_id=?",(game_id,sid)).fetchone()
            if not row:
                raise RuntimeError("学习session不存在")
            if str(row["status"])=="invalid":
                raise RuntimeError("无效学习session不能提交为valid")
            self.db.execute("UPDATE learning_sessions SET status='valid',finished=?,invalid_reason='' WHERE game_id=? AND session_id=?",(stamp,game_id,sid))
        return True
    def _ensure_sample_session(self,gid,session_id,created):
        game_id=str(gid)
        sid=str(session_id)
        with self.lock:
            row=self.db.execute("SELECT status FROM learning_sessions WHERE game_id=? AND session_id=?",(game_id,sid)).fetchone()
            if row:
                if str(row["status"])=="invalid":
                    raise RuntimeError("无效session拒绝接收样本")
                return str(row["status"])
            if sid.startswith("learn|"):
                raise RuntimeError("学习session未进入staging状态")
            with self.db:
                self.db.execute("INSERT INTO learning_sessions(game_id,session_id,status,started,finished,invalid_reason) VALUES(?,?,'valid',?,?,'automatic_non_learning_session')",(game_id,sid,float(created),float(created)))
            return "valid"
    def _raise_writer_error(self):
        with self.pending_lock:
            error=self.writer_error
        if error:
            raise RuntimeError("样本批量写入失败："+str(error))
    def _flush_pending(self,connection):
        self._ensure_writable()
        with self.pending_lock:
            if not self.pending_samples:
                self.pending_event.clear()
                self.writer_condition.notify_all()
                return 0
            batch=self.pending_samples
            self.pending_samples=[]
            self.writer_inflight+=1
            self.pending_event.clear()
            rows=[item["row"] for item in batch]
            review_games=sorted({item["gid"] for item in batch if item.get("mark_review")})
        last_error=None
        success=False
        recovered=False
        try:
            hook=self.writer_before_commit
            if hook is not None:
                hook(batch)
            for attempt in range(5):
                try:
                    with connection:
                        connection.executemany("INSERT OR IGNORE INTO samples(game_id,created,kind,action_signature,action_family,repeat_policy,feature_algorithm_version,action_algorithm_version,feature,coarse,action,source,session_id,capture_method,context,thumbnail,weight,fingerprint) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",rows)
                        for gid in review_games:
                            connection.execute("UPDATE games SET needs_review=1 WHERE id=?",(gid,))
                    success=True
                    break
                except sqlite3.OperationalError as error:
                    last_error=error
                    text_error=str(error).lower()
                    if "locked" not in text_error and "busy" not in text_error:
                        break
                    if self.writer_stop.wait(min(1.2,0.05*(2**attempt))):
                        break
                except Exception as error:
                    last_error=error
                    break
        finally:
            with self.pending_lock:
                self.writer_inflight=max(0,self.writer_inflight-1)
                if success:
                    recovered=self.writer_error is not None
                    self.writer_error=None
                else:
                    self.pending_samples=batch+self.pending_samples
                    self.pending_event.set()
                    self.writer_error="".join(traceback.format_exception_only(type(last_error),last_error)).strip() if last_error is not None else "未知写入错误"
                self.writer_condition.notify_all()
        if success:
            if recovered:
                self._notify_writer_error(None)
            return len(batch)
        error_text=self.writer_error or "未知写入错误"
        self.logger.write("SAMPLE_WRITER_COMMIT_FAILED",last_error,details={"batch_size":len(batch),"writer_error":error_text})
        self._notify_writer_error(error_text)
        raise RuntimeError(error_text)
    def flush_samples(self,timeout=5.0):
        if self.read_only:
            with self.pending_lock:
                if self.pending_samples or self.writer_inflight:
                    self._ensure_writable()
            return 0
        deadline=time.monotonic()+max(0.1,float(timeout))
        with self.pending_lock:
            initial=len(self.pending_samples)+self.writer_inflight
            if self.pending_samples:
                self.pending_event.set()
            while True:
                empty=not self.pending_samples and self.writer_inflight==0
                if empty and not self.writer_error:
                    return initial
                if self.writer_thread is not None and not self.writer_thread.is_alive():
                    detail="；最后错误："+str(self.writer_error) if self.writer_error else ""
                    raise RuntimeError("样本写线程已停止，写入屏障无法完成"+detail)
                remaining=deadline-time.monotonic()
                if remaining<=0:
                    detail="，最后错误"+str(self.writer_error) if self.writer_error else ""
                    raise RuntimeError("样本写线程在限定时间内未完成提交，待处理"+str(len(self.pending_samples))+"，提交中"+str(self.writer_inflight)+detail)
                if self.pending_samples:
                    self.pending_event.set()
                self.writer_condition.wait(min(0.2,remaining))
    def sample_write_barrier(self,timeout=5.0):
        return self.flush_samples(timeout)
    def _writer_loop(self):
        connection=sqlite3.connect(str(self.db_path),timeout=3.0,check_same_thread=False)
        connection.row_factory=sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        connection.execute("PRAGMA busy_timeout=3000")
        self.writer_db=connection
        try:
            while True:
                self.pending_event.wait(0.35)
                with self.pending_lock:
                    empty=not self.pending_samples
                    stopping=self.writer_stop.is_set()
                if stopping and empty:
                    break
                if empty:
                    continue
                try:
                    self._flush_pending(connection)
                except Exception:
                    if self.writer_stop.wait(0.8):
                        with self.pending_lock:
                            if not self.pending_samples:
                                break
            with self.pending_lock:
                pending=bool(self.pending_samples)
            if pending:
                try:
                    self._flush_pending(connection)
                except Exception as error:
                    self.logger.write("SAMPLE_WRITER_FINAL_FLUSH_FAILED",error)
        except Exception as error:
            with self.pending_lock:
                if not self.writer_error:
                    self.writer_error=str(error)
                self.writer_condition.notify_all()
            self.logger.write("SAMPLE_WRITER_THREAD_FAILED",error)
            self._notify_writer_error(self.writer_error)
        finally:
            try:
                connection.close()
            except Exception as error:
                self.logger.write("SAMPLE_WRITER_CONNECTION_CLOSE_FAILED",error)
            self.writer_db=None
            with self.pending_lock:
                self.writer_condition.notify_all()
    def _table_exists(self,name):
        return bool(self.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(str(name),)).fetchone())
    def _columns(self,name):
        if not self._table_exists(name):
            return set()
        return {str(row[1]) for row in self.db.execute("PRAGMA table_info("+str(name)+")")}
    def _create_latest_schema(self):
        self.db.execute("CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS config_backups(id INTEGER PRIMARY KEY AUTOINCREMENT,created REAL NOT NULL,payload TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS games(id TEXT PRIMARY KEY,name TEXT NOT NULL COLLATE NOCASE UNIQUE,created REAL NOT NULL,needs_review INTEGER NOT NULL DEFAULT 0,last_review REAL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS learning_sessions(game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,session_id TEXT NOT NULL,status TEXT NOT NULL CHECK(status IN ('staging','valid','invalid')),started REAL NOT NULL,finished REAL,invalid_reason TEXT NOT NULL DEFAULT '',PRIMARY KEY(game_id,session_id))")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_learning_sessions_game_status ON learning_sessions(game_id,status,started)")
        self.db.execute("CREATE TABLE IF NOT EXISTS samples(id INTEGER PRIMARY KEY AUTOINCREMENT,game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,created REAL NOT NULL,kind TEXT NOT NULL,action_signature TEXT NOT NULL,action_family TEXT NOT NULL,repeat_policy TEXT NOT NULL,feature_algorithm_version INTEGER NOT NULL,action_algorithm_version INTEGER NOT NULL,feature BLOB NOT NULL,coarse BLOB NOT NULL,action TEXT NOT NULL,source TEXT NOT NULL,session_id TEXT NOT NULL,capture_method TEXT NOT NULL,context TEXT NOT NULL,thumbnail BLOB,weight REAL NOT NULL DEFAULT 1.0,fingerprint TEXT NOT NULL,UNIQUE(game_id,fingerprint))")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_samples_game_kind_created ON samples(game_id,kind,created)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_samples_game_session ON samples(game_id,session_id)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_samples_game_action ON samples(game_id,action_signature)")
        self.db.execute("CREATE TABLE IF NOT EXISTS models(game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,slot TEXT NOT NULL,saved REAL NOT NULL,created REAL NOT NULL,prototype_count INTEGER NOT NULL,validation TEXT NOT NULL,payload BLOB NOT NULL,checksum TEXT NOT NULL,PRIMARY KEY(game_id,slot))")
        self.db.execute("CREATE TABLE IF NOT EXISTS model_backups(id INTEGER PRIMARY KEY AUTOINCREMENT,game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,created REAL NOT NULL,prototype_count INTEGER NOT NULL,validation TEXT NOT NULL,payload BLOB NOT NULL,checksum TEXT NOT NULL)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_model_backups_game_created ON model_backups(game_id,created DESC)")
        self.db.execute("CREATE TABLE IF NOT EXISTS rejections(id INTEGER PRIMARY KEY AUTOINCREMENT,game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,created REAL NOT NULL,feature_algorithm_version INTEGER NOT NULL,feature BLOB NOT NULL,coarse BLOB NOT NULL,thumbnail BLOB,candidates TEXT NOT NULL,source TEXT NOT NULL,session_id TEXT NOT NULL,capture_method TEXT NOT NULL)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_rejections_game_created ON rejections(game_id,created DESC)")
        self.db.execute("CREATE TABLE IF NOT EXISTS capture_calibrations(identity_key TEXT NOT NULL,backend TEXT NOT NULL,saved REAL NOT NULL,payload TEXT NOT NULL,checksum TEXT NOT NULL,PRIMARY KEY(identity_key,backend))")
        self.db.execute("CREATE TABLE IF NOT EXISTS game_profiles(game_id TEXT PRIMARY KEY REFERENCES games(id) ON DELETE CASCADE,updated REAL NOT NULL,payload TEXT NOT NULL,checksum TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS corrupt_rows(id INTEGER PRIMARY KEY AUTOINCREMENT,source_table TEXT NOT NULL,source_id INTEGER NOT NULL,game_id TEXT NOT NULL,created REAL NOT NULL,reason TEXT NOT NULL,payload TEXT NOT NULL,UNIQUE(source_table,source_id))")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_capture_calibrations_saved ON capture_calibrations(saved DESC)")
    def _initialize_schema(self):
        with self.lock:
            self.db.execute("CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
            row=self.db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
            if row:
                try:
                    version=int(row[0])
                except Exception:
                    raise RuntimeError("数据库schema_version无效")
            elif self._table_exists("games") or self._table_exists("samples"):
                version=1
                with self.db:
                    self.db.execute("INSERT INTO meta(key,value) VALUES('schema_version','1')")
            else:
                version=0
            if version>DATABASE_SCHEMA_VERSION:
                raise RuntimeError("数据库版本"+str(version)+"高于程序支持的版本"+str(DATABASE_SCHEMA_VERSION)+"，请升级程序后再打开")
            if version==0:
                with self.db:
                    self._create_latest_schema()
                    self.db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version',?)",(str(DATABASE_SCHEMA_VERSION),))
                return
            while version<DATABASE_SCHEMA_VERSION:
                self.db.execute("BEGIN IMMEDIATE")
                try:
                    if version==1:
                        sample_columns=self._columns("samples")
                        additions=[("action_family","TEXT NOT NULL DEFAULT ''"),("repeat_policy","TEXT NOT NULL DEFAULT 'one_shot'"),("feature_algorithm_version","INTEGER NOT NULL DEFAULT 3"),("action_algorithm_version","INTEGER NOT NULL DEFAULT 4"),("session_id","TEXT NOT NULL DEFAULT 'legacy'"),("capture_method","TEXT NOT NULL DEFAULT 'legacy'")]
                        for name,declaration in additions:
                            if name not in sample_columns:
                                self.db.execute("ALTER TABLE samples ADD COLUMN "+name+" "+declaration)
                        rejection_columns=self._columns("rejections")
                        additions=[("feature_algorithm_version","INTEGER NOT NULL DEFAULT 3"),("session_id","TEXT NOT NULL DEFAULT 'legacy'"),("capture_method","TEXT NOT NULL DEFAULT 'legacy'")]
                        for name,declaration in additions:
                            if name not in rejection_columns:
                                self.db.execute("ALTER TABLE rejections ADD COLUMN "+name+" "+declaration)
                        version=2
                    elif version==2:
                        self._create_latest_schema()
                        self.db.execute("UPDATE samples SET action_family=kind WHERE action_family='' OR action_family IS NULL")
                        version=3
                    elif version==3:
                        self.db.execute("DROP TABLE IF EXISTS model_backups_v4")
                        self.db.execute("CREATE TABLE model_backups_v4(id INTEGER PRIMARY KEY AUTOINCREMENT,game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,created REAL NOT NULL,prototype_count INTEGER NOT NULL,validation TEXT NOT NULL,payload BLOB NOT NULL,checksum TEXT NOT NULL)")
                        if self._table_exists("model_backups"):
                            self.db.execute("INSERT INTO model_backups_v4(id,game_id,created,prototype_count,validation,payload,checksum) SELECT b.id,b.game_id,b.created,b.prototype_count,b.validation,b.payload,b.checksum FROM model_backups b JOIN games g ON g.id=b.game_id")
                            self.db.execute("DROP TABLE model_backups")
                        self.db.execute("ALTER TABLE model_backups_v4 RENAME TO model_backups")
                        self.db.execute("CREATE INDEX IF NOT EXISTS idx_model_backups_game_created ON model_backups(game_id,created DESC)")
                        version=4
                    elif version==4:
                        self.db.execute("CREATE TABLE IF NOT EXISTS capture_calibrations(identity_key TEXT NOT NULL,backend TEXT NOT NULL,saved REAL NOT NULL,payload TEXT NOT NULL,checksum TEXT NOT NULL,PRIMARY KEY(identity_key,backend))")
                        self.db.execute("CREATE INDEX IF NOT EXISTS idx_capture_calibrations_saved ON capture_calibrations(saved DESC)")
                        version=5
                    elif version==5:
                        self.db.execute("CREATE TABLE IF NOT EXISTS game_profiles(game_id TEXT PRIMARY KEY REFERENCES games(id) ON DELETE CASCADE,updated REAL NOT NULL,payload TEXT NOT NULL,checksum TEXT NOT NULL)")
                        self.db.execute("CREATE TABLE IF NOT EXISTS corrupt_rows(id INTEGER PRIMARY KEY AUTOINCREMENT,source_table TEXT NOT NULL,source_id INTEGER NOT NULL,game_id TEXT NOT NULL,created REAL NOT NULL,reason TEXT NOT NULL,payload TEXT NOT NULL,UNIQUE(source_table,source_id))")
                        version=6
                    elif version==6:
                        self.db.execute("CREATE TABLE IF NOT EXISTS learning_sessions(game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,session_id TEXT NOT NULL,status TEXT NOT NULL CHECK(status IN ('staging','valid','invalid')),started REAL NOT NULL,finished REAL,invalid_reason TEXT NOT NULL DEFAULT '',PRIMARY KEY(game_id,session_id))")
                        self.db.execute("CREATE INDEX IF NOT EXISTS idx_learning_sessions_game_status ON learning_sessions(game_id,status,started)")
                        self.db.execute("INSERT OR IGNORE INTO learning_sessions(game_id,session_id,status,started,finished,invalid_reason) SELECT game_id,session_id,'valid',MIN(created),MAX(created),'legacy_migration' FROM samples GROUP BY game_id,session_id")
                        version=7
                    else:
                        raise RuntimeError("没有从数据库版本"+str(version)+"开始的迁移路径")
                    self.db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version',?)",(str(version),))
                    self.db.commit()
                except Exception:
                    self.db.rollback()
                    raise
            with self.db:
                self._create_latest_schema()
    def _legacy_read_json(self,path,default=None):
        try:
            if path.stat().st_size>64*1024*1024:
                return default
            with path.open("r",encoding="utf-8") as stream:
                return json.load(stream)
        except Exception:
            return default
    def _migrate_legacy(self):
        with self.lock:
            row=self.db.execute("SELECT value FROM meta WHERE key='legacy_migrated'").fetchone()
            if row:
                return
        config_path=self.base/"config.json"
        backup_path=config_path.with_suffix(".json.bak")
        legacy_dirs=[self.base/name for name in ("samples","models","backups","temp")]
        legacy_present=config_path.exists() or backup_path.exists() or any(folder.exists() and any(folder.iterdir()) for folder in legacy_dirs)
        if not legacy_present:
            with self.lock,self.db:
                self.db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('legacy_migrated','1')")
            return
        config=self._legacy_read_json(config_path,None)
        if not isinstance(config,dict):
            config=self._legacy_read_json(backup_path,None)
        if not isinstance(config,dict) or not isinstance(config.get("games"),list):
            raise RuntimeError("旧配置损坏，迁移事务未开始，旧文件已保留")
        games=[]
        game_ids=set()
        legacy_invalid=0
        for game in config.get("games",[]):
            try:
                if not isinstance(game,dict) or not game.get("id") or not str(game.get("name","")).strip():
                    raise ValueError("invalid game")
                gid=str(game["id"])
                if gid in game_ids:
                    raise ValueError("duplicate game")
                game_ids.add(gid)
                games.append((gid,str(game["name"]).strip(),safe_float(game.get("created",time.time()),time.time()),1 if game.get("needs_review") else 0,game.get("last_review")))
            except Exception:
                legacy_invalid+=1
        if not games:
            raise RuntimeError("旧配置没有可迁移的有效游戏，旧文件已保留")
        sample_rows=[]
        samples_dir=self.base/"samples"
        if samples_dir.exists():
            for path in sorted(samples_dir.glob("*.jsonl")):
                gid=path.stem
                if gid not in game_ids:
                    legacy_invalid+=1
                    continue
                with path.open("r",encoding="utf-8") as stream:
                    for line_number,line in enumerate(stream,1):
                        try:
                            item=json.loads(line)
                            action=normalize_action(item.get("a"))
                            feature=upgrade_feature(item.get("f"),item.get("feature_algorithm_version",3))
                            if not action or not feature_valid(feature):
                                raise ValueError("schema")
                            context=item.get("context") if isinstance(item.get("context"),dict) else {}
                            source=str(item.get("source","legacy"))
                            session_id=str(context.get("session_id") or "legacy-"+path.stem)
                            capture_method=str(context.get("capture_method") or "legacy")
                            thumbnail=upgrade_gray_image(item.get("thumbnail")) if item.get("thumbnail") is not None else None
                            sample_rows.append((gid,float(item.get("created",time.time())),feature,action,source,context,thumbnail,float(item.get("weight",1.0)),session_id,capture_method))
                        except Exception:
                            legacy_invalid+=1
                            continue
        model_rows=[]
        for folder_name in ("models","backups"):
            folder=self.base/folder_name
            if not folder.exists():
                continue
            for path in sorted(folder.glob("*.json")):
                if path.name.endswith(".partial.json"):
                    continue
                raw=self._legacy_read_json(path,None)
                if not isinstance(raw,dict):
                    legacy_invalid+=1
                    continue
                gid=str(raw.get("game_id",path.stem.split(".")[0]))
                if gid not in game_ids:
                    legacy_invalid+=1
                    continue
                complete=bool(raw.get("complete",True))
                upgraded=self._upgrade_model(raw,gid,complete)
                if not upgraded or not self._model_valid(upgraded,gid,complete):
                    legacy_invalid+=1
                    continue
                model_rows.append((folder_name,gid,upgraded,complete))
        selected=str(config.get("selected_game")) if config.get("selected_game") in game_ids else (games[0][0] if games else None)
        with self.lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                for row in games:
                    self.db.execute("INSERT OR IGNORE INTO games(id,name,created,needs_review,last_review) VALUES(?,?,?,?,?)",row)
                if selected:
                    self.db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('selected_game',?)",(selected,))
                for gid,created,feature,action,source,context,thumbnail,weight,session_id,capture_method in sample_rows:
                    fbytes=feature_bytes(feature)
                    signature=action_signature(action)
                    fingerprint=self._sample_fingerprint(fbytes,action)
                    self.db.execute("INSERT OR IGNORE INTO samples(game_id,created,kind,action_signature,action_family,repeat_policy,feature_algorithm_version,action_algorithm_version,feature,coarse,action,source,session_id,capture_method,context,thumbnail,weight,fingerprint) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(gid,created,action["kind"],signature,action_family_key(action),str(context.get("repeat_policy","one_shot")),FEATURE_ALGORITHM_VERSION,ACTION_ALGORITHM_VERSION,sqlite3.Binary(zlib.compress(fbytes,6)),sqlite3.Binary(coarse_feature(fbytes)),json.dumps(action,ensure_ascii=False,separators=(",",":")),source,session_id,capture_method,json.dumps(context,ensure_ascii=False,separators=(",",":")),sqlite3.Binary(zlib.compress(thumbnail,6)) if gray_valid(thumbnail) else None,max(0.1,min(10.0,weight)),fingerprint))
                for folder_name,gid,model,complete in model_rows:
                    payload=self._pack_model(model)
                    checksum=hashlib.sha256(payload).hexdigest()
                    validation=json.dumps(model.get("validation",{}),ensure_ascii=False,separators=(",",":"))
                    if folder_name=="backups":
                        self.db.execute("INSERT INTO model_backups(game_id,created,prototype_count,validation,payload,checksum) VALUES(?,?,?,?,?,?)",(gid,float(model.get("saved",model.get("created",time.time()))),len(model["prototypes"]),validation,sqlite3.Binary(payload),checksum))
                    else:
                        slot="complete" if complete else "partial"
                        self.db.execute("INSERT OR REPLACE INTO models(game_id,slot,saved,created,prototype_count,validation,payload,checksum) VALUES(?,?,?,?,?,?,?,?)",(gid,slot,float(model.get("saved",time.time())),float(model.get("created",time.time())),len(model["prototypes"]),validation,sqlite3.Binary(payload),checksum))
                self.db.execute("INSERT OR IGNORE INTO learning_sessions(game_id,session_id,status,started,finished,invalid_reason) SELECT game_id,session_id,'valid',MIN(created),MAX(created),'legacy_file_migration' FROM samples GROUP BY game_id,session_id")
                self.db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('legacy_migrated','1')")
                self.db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('legacy_invalid_rows',?)",(str(legacy_invalid),))
                self.db.commit()
            except Exception:
                self.db.rollback()
                raise
        for path in (config_path,backup_path):
            try:
                path.unlink()
            except Exception:
                pass
        for folder in legacy_dirs:
            if folder.exists():
                for child in list(folder.iterdir()):
                    try:
                        child.unlink()
                    except Exception:
                        pass
                try:
                    folder.rmdir()
                except Exception:
                    pass
    def _config_snapshot(self):
        games=[dict(row) for row in self.db.execute("SELECT id,name,created,needs_review,last_review FROM games ORDER BY created,id")]
        row=self.db.execute("SELECT value FROM meta WHERE key='selected_game'").fetchone()
        return {"format_version":FORMAT_VERSION,"games":games,"selected_game":row[0] if row else None}
    def data_version_signature(self):
        values=[]
        for suffix in ("","-wal","-shm"):
            path=Path(str(self.db_path)+suffix)
            try:
                stat=path.stat()
                values.append((suffix,int(stat.st_mtime_ns),int(stat.st_size)))
            except FileNotFoundError:
                values.append((suffix,0,0))
            except Exception as error:
                self.logger.write("DATABASE_VERSION_STAT_FAILED",error,details={"path":str(path)})
                values.append((suffix,-1,-1))
        with self.pending_lock:
            values.append(("writer",len(self.pending_samples),self.writer_inflight,str(self.writer_error or "")))
        return tuple(values)
    def games(self):
        with self.lock:
            rows=self.db.execute("SELECT id,name,created,needs_review,last_review FROM games ORDER BY created,id").fetchall()
        return [{"id":row["id"],"name":row["name"],"created":row["created"],"needs_review":bool(row["needs_review"]),"last_review":row["last_review"]} for row in rows]
    def selected_game(self):
        with self.lock:
            row=self.db.execute("SELECT value FROM meta WHERE key='selected_game'").fetchone()
        if not row:
            return None
        return next((game for game in self.games() if game["id"]==row[0]),None)
    def replace_games(self,games,selected):
        cleaned=[]
        names=set()
        for item in games:
            if not isinstance(item,dict) or not item.get("id") or not str(item.get("name","")).strip():
                continue
            name=str(item["name"]).strip()
            if name.casefold() in names:
                raise RuntimeError("游戏名称重复")
            names.add(name.casefold())
            cleaned.append({"id":str(item["id"]),"name":name,"created":float(item.get("created",time.time())),"needs_review":1 if item.get("needs_review") else 0,"last_review":item.get("last_review")})
        keep={item["id"] for item in cleaned}
        if selected not in keep:
            raise RuntimeError("所选游戏不存在")
        with self.lock:
            existing={str(row[0]) for row in self.db.execute("SELECT id FROM games")}
        deleting=existing-keep
        with self.pending_lock:
            self.blocked_game_ids.update(deleting)
            removed_pending=[item for item in self.pending_samples if item.get("gid") in deleting]
            self.pending_samples=[item for item in self.pending_samples if item.get("gid") not in deleting]
            if not self.pending_samples:
                self.pending_event.clear()
                if self.writer_inflight==0 and self.writer_error:
                    self.writer_error=None
                    self._notify_writer_error(None)
            self.writer_condition.notify_all()
        try:
            self.sample_write_barrier()
            with self.critical_transaction():
                self.db.execute("INSERT INTO config_backups(created,payload) VALUES(?,?)",(time.time(),json.dumps(self._config_snapshot(),ensure_ascii=False,separators=(",",":"))))
                self.db.execute("DELETE FROM config_backups WHERE id NOT IN (SELECT id FROM config_backups ORDER BY id DESC LIMIT 5)")
                for gid in deleting:
                    self.db.execute("DELETE FROM games WHERE id=?",(gid,))
                    self.model_cache.pop(gid,None)
                for item in cleaned:
                    self.db.execute("INSERT INTO games(id,name,created,needs_review,last_review) VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,created=excluded.created,needs_review=excluded.needs_review,last_review=excluded.last_review",(item["id"],item["name"],item["created"],item["needs_review"],item["last_review"]))
                self.db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('selected_game',?)",(selected,))
            return {"deleted_games":sorted(deleting),"discarded_pending_samples":len(removed_pending)}
        finally:
            with self.pending_lock:
                self.blocked_game_ids.difference_update(deleting)
                self.writer_condition.notify_all()
    def delete_game(self,gid):
        game_id=str(gid)
        with self.pending_lock:
            self.blocked_game_ids.add(game_id)
            before=len(self.pending_samples)
            self.pending_samples=[item for item in self.pending_samples if item.get("gid")!=game_id]
            removed=before-len(self.pending_samples)
            if not self.pending_samples:
                self.pending_event.clear()
                if self.writer_inflight==0 and self.writer_error:
                    self.writer_error=None
                    self._notify_writer_error(None)
            self.writer_condition.notify_all()
        try:
            self.sample_write_barrier()
            with self.critical_transaction():
                row=self.db.execute("SELECT 1 FROM games WHERE id=?",(game_id,)).fetchone()
                if not row:
                    return False
                self.db.execute("DELETE FROM games WHERE id=?",(game_id,))
                selected=self.db.execute("SELECT value FROM meta WHERE key='selected_game'").fetchone()
                if selected and str(selected[0])==game_id:
                    self.db.execute("DELETE FROM meta WHERE key='selected_game'")
            self.model_cache.pop(game_id,None)
            return True
        finally:
            with self.pending_lock:
                self.blocked_game_ids.discard(game_id)
                self.writer_condition.notify_all()
    def update_game(self,gid,**changes):
        allowed={"name","created","needs_review","last_review"}
        fields=[]
        values=[]
        for key,value in changes.items():
            if key in allowed:
                fields.append(key+"=?")
                values.append(1 if key=="needs_review" and value else 0 if key=="needs_review" else value)
        if not fields:
            return
        values.append(gid)
        with self.critical_transaction():
            self.db.execute("UPDATE games SET "+",".join(fields)+" WHERE id=?",values)
    def _sample_fingerprint(self,feature,action,context=None):
        temporal=temporal_from_context(context or {})
        identity={"action":normalize_action(action),"temporal":temporal}
        return hashlib.sha256(feature_bytes(feature)+b"\0"+canonical_bytes(identity)).hexdigest()
    def _near_duplicate(self,gid,feature,signature,threshold,context=None):
        with self.lock:
            rows=self.db.execute("SELECT feature,coarse,feature_algorithm_version,context FROM samples WHERE game_id=? AND action_signature=? ORDER BY created DESC,id DESC LIMIT 36",(gid,signature)).fetchall()
        with self.pending_lock:
            pending=[item for item in self.pending_samples if item["gid"]==gid and item["signature"]==signature][-36:]
        query=feature_bytes(feature)
        query_coarse=coarse_feature(query)
        query_context=context if isinstance(context,dict) else {}
        for item in pending:
            try:
                if temporal_distance(query_context,item["context"])<=0.08 and coarse_distance(query_coarse,item["coarse"])<=max(2.0,float(threshold)*2.5) and feature_distance(query,item["feature"])<=float(threshold):
                    return True
            except Exception as error:
                self.logger.write("PENDING_DUPLICATE_COMPARE_FAILED",error,game_id=gid)
        for row in rows:
            try:
                candidate=upgrade_feature(bounded_decompress(row["feature"],FEATURE_LEN*2),row["feature_algorithm_version"])
                candidate_context=json.loads(row["context"])
                candidate_coarse=bytes(row["coarse"]) if row["coarse"] is not None and len(row["coarse"])==COARSE_LEN else coarse_feature(candidate)
                if candidate is None or not isinstance(candidate_context,dict):
                    continue
                if temporal_distance(query_context,candidate_context)>0.08:
                    continue
                if coarse_distance(query_coarse,candidate_coarse)<=max(2.0,float(threshold)*2.5) and feature_distance(query,candidate)<=float(threshold):
                    return True
            except Exception:
                continue
        return False
    def _insert_sample(self,gid,feature,action,source,context,thumbnail,weight,enforce_quota,mark_review,created=None):
        self._ensure_writable()
        self._raise_writer_error()
        clean=normalize_action(action)
        if not clean or not feature_valid(feature):
            raise RuntimeError("拒绝保存无效样本")
        fbytes=feature_bytes(feature)
        coarse=coarse_feature(fbytes)
        signature=action_signature(clean)
        context=dict(context) if isinstance(context,dict) else {}
        session_id=str(context.get("session_id") or "unspecified")
        capture_method=str(context.get("capture_method") or "unknown")
        repeat_policy=str(context.get("repeat_policy","one_shot"))
        if repeat_policy not in REPEAT_POLICIES:
            repeat_policy="one_shot"
        duplicate_threshold=float(context.get("duplicate_threshold",3.0)) if finite_number(context.get("duplicate_threshold",3.0)) else 3.0
        fingerprint=self._sample_fingerprint(fbytes,clean,context)
        kind=clean["kind"]
        created_value=float(time.time() if created is None else created)
        self._ensure_sample_session(gid,session_id,created_value)
        with self.pending_lock:
            if str(gid) in self.blocked_game_ids or (str(gid),session_id) in self.blocked_sessions:
                raise RuntimeError("游戏或session正在作废，拒绝接收样本")
            pending_duplicate=any(item["gid"]==gid and item["fingerprint"]==fingerprint for item in self.pending_samples)
            pending_noops=sum(1 for item in self.pending_samples if item["gid"]==gid and item["kind"]=="no_op")
            pending_actions=sum(1 for item in self.pending_samples if item["gid"]==gid and item["kind"]!="no_op")
            pending_count=sum(1 for item in self.pending_samples if item["gid"]==gid)
        with self.lock:
            if not self.db.execute("SELECT 1 FROM games WHERE id=?",(gid,)).fetchone():
                raise RuntimeError("游戏不存在")
            persisted_duplicate=bool(self.db.execute("SELECT 1 FROM samples WHERE game_id=? AND fingerprint=?",(gid,fingerprint)).fetchone())
            count_row=self.db.execute("SELECT COUNT(*) AS total,SUM(CASE WHEN kind='no_op' THEN 1 ELSE 0 END) AS noops,SUM(CASE WHEN kind!='no_op' THEN 1 ELSE 0 END) AS actions FROM samples WHERE game_id=?",(gid,)).fetchone()
        if pending_duplicate or persisted_duplicate:
            return False
        if enforce_quota and kind=="no_op" and int(count_row["noops"] or 0)+pending_noops>=max(1,(int(count_row["actions"] or 0)+pending_actions)//3):
            return False
        if enforce_quota and self._near_duplicate(gid,fbytes,signature,duplicate_threshold,context):
            return False
        row=(gid,created_value,kind,signature,action_family_key(clean),repeat_policy,FEATURE_ALGORITHM_VERSION,ACTION_ALGORITHM_VERSION,sqlite3.Binary(zlib.compress(fbytes,6)),sqlite3.Binary(coarse),json.dumps(clean,ensure_ascii=False,separators=(",",":")),str(source),session_id,capture_method,json.dumps(context,ensure_ascii=False,separators=(",",":")),sqlite3.Binary(zlib.compress(gray_bytes(thumbnail),6)) if gray_valid(thumbnail) else None,float(max(0.1,min(10.0,weight))),fingerprint)
        with self.pending_lock:
            if str(gid) in self.blocked_game_ids or (str(gid),session_id) in self.blocked_sessions:
                raise RuntimeError("游戏或session正在作废，拒绝接收样本")
            if any(item["gid"]==gid and item["fingerprint"]==fingerprint for item in self.pending_samples):
                return False
            self.pending_samples.append({"row":row,"gid":gid,"signature":signature,"coarse":coarse,"feature":fbytes,"context":context,"kind":kind,"fingerprint":fingerprint,"session_id":session_id,"created":created_value,"mark_review":bool(mark_review)})
            if len(self.pending_samples)>=12:
                self.pending_event.set()
            count=int(count_row["total"] or 0)+pending_count+1
            self.writer_condition.notify_all()
        if count>MAX_SAMPLES+16:
            self.sample_write_barrier()
            self.compact_samples(gid,MAX_SAMPLES)
        return True
    def discard_session(self,gid,session_id,reason="discarded"):
        game_id=str(gid)
        sid=str(session_id)
        self.invalidate_learning_session(game_id,sid,reason)
        self.sample_write_barrier()
        with self.pending_lock:
            before=len(self.pending_samples)
            self.pending_samples=[item for item in self.pending_samples if not (item["gid"]==game_id and item["session_id"]==sid)]
            pending_removed=before-len(self.pending_samples)
            self.writer_condition.notify_all()
        with self.critical_transaction():
            cursor=self.db.execute("DELETE FROM samples WHERE game_id=? AND session_id=?",(game_id,sid))
            removed=pending_removed+max(0,int(cursor.rowcount or 0))
            if removed:
                self.db.execute("UPDATE games SET needs_review=1 WHERE id=?",(game_id,))
        self.model_cache.pop(game_id,None)
        return removed
    def discard_session_window(self,gid,session_id,start_time,end_time):
        game_id=str(gid)
        sid=str(session_id)
        self.invalidate_learning_session(game_id,sid,"discarded_window")
        self.sample_write_barrier()
        with self.pending_lock:
            before=len(self.pending_samples)
            self.pending_samples=[item for item in self.pending_samples if not (item["gid"]==game_id and item["session_id"]==sid and float(start_time)<=item["created"]<=float(end_time))]
            pending_removed=before-len(self.pending_samples)
            self.writer_condition.notify_all()
        with self.critical_transaction():
            cursor=self.db.execute("DELETE FROM samples WHERE game_id=? AND session_id=? AND created BETWEEN ? AND ?",(game_id,sid,float(start_time),float(end_time)))
            removed=pending_removed+max(0,int(cursor.rowcount or 0))
            if removed:
                self.db.execute("UPDATE games SET needs_review=1 WHERE id=?",(game_id,))
        self.model_cache.pop(game_id,None)
        return removed
    def append_sample(self,gid,feature,action,source,context=None,thumbnail=None,weight=1.0):
        return self._insert_sample(gid,feature,action,source,context or {},thumbnail,weight,True,True)
    def append_rejection(self,gid,feature,candidates,source="teach_reject",thumbnail=None,context=None):
        self._ensure_writable()
        if not feature_valid(feature):
            raise RuntimeError("拒绝记录的特征无效")
        candidate_data=[]
        for item in candidates or []:
            action=normalize_action(item.get("a") if isinstance(item,dict) else item)
            if action:
                candidate_data.append({"cluster_id":str(item.get("cluster_id",item.get("action_signature",""))) if isinstance(item,dict) else "","canonical_action_signature":action_signature(action),"a":action})
        context=dict(context) if isinstance(context,dict) else {}
        with self.lock,self.db:
            self.db.execute("INSERT INTO rejections(game_id,created,feature_algorithm_version,feature,coarse,thumbnail,candidates,source,session_id,capture_method) VALUES(?,?,?,?,?,?,?,?,?,?)",(gid,time.time(),FEATURE_ALGORITHM_VERSION,sqlite3.Binary(zlib.compress(feature_bytes(feature),6)),sqlite3.Binary(coarse_feature(feature)),sqlite3.Binary(zlib.compress(gray_bytes(thumbnail),6)) if gray_valid(thumbnail) else None,json.dumps(candidate_data,ensure_ascii=False,separators=(",",":")),str(source),str(context.get("session_id") or "unspecified"),str(context.get("capture_method") or "unknown")))
            self.db.execute("UPDATE games SET needs_review=1 WHERE id=?",(gid,))
    def load_samples(self,gid,limit=MAX_SAMPLES):
        self.sample_write_barrier()
        with self.lock:
            rows=self.db.execute("SELECT s.id,s.created,s.feature_algorithm_version,s.action_algorithm_version,s.feature,s.coarse,s.action,s.source,s.session_id,s.capture_method,s.context,s.thumbnail,s.weight,s.fingerprint,s.repeat_policy FROM samples s JOIN learning_sessions ls ON ls.game_id=s.game_id AND ls.session_id=s.session_id WHERE s.game_id=? AND ls.status='valid' ORDER BY s.created DESC,s.id DESC LIMIT ?",(gid,int(limit))).fetchall()
        result=[]
        invalid=0
        for row in reversed(rows):
            try:
                feature=upgrade_feature(bounded_decompress(row["feature"],FEATURE_LEN*2),row["feature_algorithm_version"])
                action=normalize_action(json.loads(row["action"]))
                coarse=bytes(row["coarse"]) if row["coarse"] is not None and len(row["coarse"])==COARSE_LEN else coarse_feature(feature)
                if not feature_valid(feature) or len(coarse)!=COARSE_LEN or not action:
                    raise ValueError("样本特征、粗特征或动作无效")
                thumbnail=bounded_decompress(row["thumbnail"],PIXELS*4) if row["thumbnail"] is not None else None
                thumbnail=upgrade_gray_image(thumbnail) if thumbnail is not None else None
                context=json.loads(row["context"])
                if not isinstance(context,dict):
                    context={}
                context.update({"session_id":row["session_id"],"capture_method":row["capture_method"],"repeat_policy":row["repeat_policy"]})
                result.append({"format_version":FORMAT_VERSION,"feature_width":FEATURE_W,"feature_height":FEATURE_H,"feature_algorithm_version":FEATURE_ALGORITHM_VERSION,"action_algorithm_version":ACTION_ALGORITHM_VERSION,"created":row["created"],"game_id":gid,"f":feature,"coarse":coarse,"a":action,"source":row["source"],"session_id":row["session_id"],"capture_method":row["capture_method"],"repeat_policy":row["repeat_policy"],"context":context,"thumbnail":thumbnail,"weight":row["weight"],"checksum":row["fingerprint"]})
            except Exception as error:
                invalid+=1
                self.quarantine_corrupt_row("samples",row["id"],gid,error,row["fingerprint"])
        self.invalid_rows[str(gid)]=max(self.invalid_rows.get(str(gid),0),invalid)
        return result,{"valid":len(result),"invalid":invalid,"total":len(rows)}
    def load_rejections(self,gid,limit=500):
        with self.lock:
            rows=self.db.execute("SELECT id,created,feature_algorithm_version,feature,coarse,thumbnail,candidates,source,session_id,capture_method FROM rejections WHERE game_id=? ORDER BY created DESC,id DESC LIMIT ?",(gid,int(limit))).fetchall()
        result=[]
        invalid=0
        for row in rows:
            try:
                feature=upgrade_feature(bounded_decompress(row["feature"],FEATURE_LEN*2),row["feature_algorithm_version"])
                coarse=bytes(row["coarse"]) if row["coarse"] is not None and len(row["coarse"])==COARSE_LEN else coarse_feature(feature)
                candidates=json.loads(row["candidates"])
                thumbnail=bounded_decompress(row["thumbnail"],PIXELS*4) if row["thumbnail"] is not None else None
                thumbnail=upgrade_gray_image(thumbnail) if thumbnail is not None else None
                if not feature_valid(feature) or len(coarse)!=COARSE_LEN or not isinstance(candidates,list):
                    raise ValueError("拒绝记录特征或候选无效")
                result.append({"created":row["created"],"f":feature,"coarse":coarse,"thumbnail":thumbnail,"candidates":candidates,"source":row["source"],"session_id":row["session_id"],"capture_method":row["capture_method"]})
            except Exception as error:
                invalid+=1
                self.quarantine_corrupt_row("rejections",row["id"],gid,error,str(row["source"]))
        self.invalid_rows["rejections:"+str(gid)]=max(self.invalid_rows.get("rejections:"+str(gid),0),invalid)
        return result
    def sample_stats(self,gid):
        self.sample_write_barrier()
        with self.lock:
            total_row=self.db.execute("SELECT COUNT(*) AS total,COALESCE(SUM(length(feature)+length(coarse)+length(action)+length(context)+COALESCE(length(thumbnail),0)),0) AS bytes FROM samples WHERE game_id=?",(gid,)).fetchone()
            valid_row=self.db.execute("SELECT COUNT(*) AS valid FROM samples s JOIN learning_sessions ls ON ls.game_id=s.game_id AND ls.session_id=s.session_id WHERE s.game_id=? AND ls.status='valid' AND s.feature_algorithm_version IN (3,?)",(gid,FEATURE_ALGORITHM_VERSION)).fetchone()
            session_row=self.db.execute("SELECT COUNT(*) AS sessions FROM learning_sessions WHERE game_id=? AND status='valid'",(gid,)).fetchone()
            family_rows=self.db.execute("SELECT s.action_family,COUNT(*) AS count FROM samples s JOIN learning_sessions ls ON ls.game_id=s.game_id AND ls.session_id=s.session_id WHERE s.game_id=? AND ls.status='valid' AND s.feature_algorithm_version IN (3,?) GROUP BY s.action_family",(gid,FEATURE_ALGORITHM_VERSION)).fetchall()
        total=safe_int(total_row["total"] or 0,0,0)
        sql_valid=safe_int(valid_row["valid"] or 0,0,0,total)
        observed=safe_int(self.invalid_rows.get(str(gid),0),0,0,total)
        valid=max(0,min(sql_valid,total-observed))
        families={str(row["action_family"]):safe_int(row["count"],0,0) for row in family_rows if str(row["action_family"])}
        return {"valid":valid,"invalid":total-valid,"total":total,"bytes":safe_int(total_row["bytes"] or 0,0,0),"sessions":safe_int(session_row["sessions"] or 0,0,0),"families":families}
    def _select_diverse(self,rows,count):
        if count<=0:
            return []
        if len(rows)<=count:
            return list(rows)
        ordered=sorted(rows,key=lambda row:(safe_float(row["weight"],1.0),safe_float(row["created"],0.0)),reverse=True)
        selected=[ordered.pop(0)]
        while ordered and len(selected)<count:
            candidates=ordered if len(ordered)<=180 else ordered[:180]
            best=max(candidates,key=lambda row:(min(coarse_distance(row["coarse"],chosen["coarse"]) for chosen in selected),safe_float(row["weight"],1.0),safe_float(row["created"],0.0)))
            selected.append(best)
            ordered.remove(best)
        return selected
    def compact_samples(self,gid,keep=MAX_SAMPLES):
        self.sample_write_barrier()
        keep=max(1,safe_int(keep,MAX_SAMPLES,1,MAX_SAMPLES))
        with self.lock:
            rows=self.db.execute("SELECT id,kind,action_signature,action_family,capture_method,coarse,weight,created FROM samples WHERE game_id=?",(gid,)).fetchall()
        if len(rows)<=keep:
            return {"kept":len(rows),"removed":0,"invalid":0}
        signature_groups=defaultdict(list)
        family_groups=defaultdict(set)
        invalid_row_count=0
        for row in rows:
            signature=str(row["action_signature"] or "")
            if not signature:
                invalid_row_count+=1
                continue
            signature_groups[signature].append(row)
            family_groups[str(row["action_family"] or row["kind"] or "unknown")].add(signature)
        def signature_info(signature):
            group=signature_groups[signature]
            kinds={str(row["kind"]) for row in group}
            family=str(group[0]["action_family"] or group[0]["kind"])
            dangerous=bool(kinds&{"double_click","long_press","drag"} or family.endswith("|right") or family.endswith("|middle"))
            return {"support":len(group),"latest":max(safe_float(row["created"],0.0) for row in group),"weight":max(safe_float(row["weight"],1.0) for row in group),"backends":len({str(row["capture_method"]) for row in group}),"family":family,"dangerous":dangerous,"noop":"no_op" in kinds}
        infos={signature:signature_info(signature) for signature in signature_groups}
        def geometry_distance(first,second):
            a=str(first).split("|")
            b=str(second).split("|")
            total=0.0
            count=0
            for x,y in zip(a,b):
                try:
                    total+=abs(float(x)-float(y))
                    count+=1
                except Exception:
                    if x!=y:
                        total+=1.0
                        count+=1
            return total/max(1,count)
        selected=[]
        remaining_signatures=set(signature_groups)
        dangerous=[sig for sig in remaining_signatures if infos[sig]["dangerous"] and not infos[sig]["noop"]]
        ordinary=[sig for sig in remaining_signatures if not infos[sig]["dangerous"] and not infos[sig]["noop"]]
        def best_signature(pool):
            if not pool:
                return None
            return max(pool,key=lambda sig:(infos[sig]["support"],infos[sig]["latest"],min((geometry_distance(sig,chosen) for chosen in selected if infos[chosen]["family"]==infos[sig]["family"]),default=9999.0),infos[sig]["backends"],infos[sig]["weight"],sig))
        if keep>=2 and dangerous and ordinary:
            for pool in (dangerous,ordinary):
                chosen=best_signature(pool)
                selected.append(chosen)
                remaining_signatures.discard(chosen)
        elif dangerous or ordinary:
            chosen=best_signature(dangerous or ordinary)
            selected.append(chosen)
            remaining_signatures.discard(chosen)
        noop_limit=max(1,min(keep//10,25))
        while remaining_signatures and len(selected)<keep:
            action_pool=[sig for sig in remaining_signatures if not infos[sig]["noop"]]
            noop_selected=sum(1 for sig in selected if infos[sig]["noop"])
            pool=action_pool if action_pool else ([sig for sig in remaining_signatures if infos[sig]["noop"] and noop_selected<noop_limit] or list(remaining_signatures))
            chosen=best_signature(pool)
            if chosen is None:
                break
            selected.append(chosen)
            remaining_signatures.discard(chosen)
        targets={signature:1 for signature in selected[:keep]}
        remaining=max(0,keep-len(targets))
        family_order=sorted({infos[sig]["family"] for sig in targets},key=lambda family:sum(len(signature_groups[sig]) for sig in targets if infos[sig]["family"]==family),reverse=True)
        while remaining>0:
            progressed=False
            for family in family_order:
                candidates=[]
                for signature in targets:
                    if infos[signature]["family"]!=family or targets[signature]>=len(signature_groups[signature]):
                        continue
                    if infos[signature]["noop"] and targets[signature]>=noop_limit:
                        continue
                    candidates.append(signature)
                if not candidates:
                    continue
                signature=max(candidates,key=lambda sig:((len(signature_groups[sig])-targets[sig])/(targets[sig]+1),infos[sig]["support"],infos[sig]["latest"],infos[sig]["backends"]))
                targets[signature]+=1
                remaining-=1
                progressed=True
                if remaining<=0:
                    break
            if not progressed:
                break
        chosen=[]
        for signature,count in targets.items():
            chosen.extend(self._select_diverse(signature_groups[signature],count))
        keep_ids={safe_int(row["id"],0,1) for row in chosen}
        if len(keep_ids)>keep:
            raise RuntimeError("样本压缩未满足硬上限")
        with self.lock,self.db:
            placeholders=",".join("?" for _ in keep_ids)
            if keep_ids:
                self.db.execute("DELETE FROM samples WHERE game_id=? AND id NOT IN ("+placeholders+")",[gid]+list(keep_ids))
            else:
                self.db.execute("DELETE FROM samples WHERE game_id=?",(gid,))
            final_count=safe_int(self.db.execute("SELECT COUNT(*) FROM samples WHERE game_id=?",(gid,)).fetchone()[0],0,0)
        if final_count>keep:
            raise RuntimeError("样本压缩未满足硬上限")
        return {"kept":final_count,"removed":len(rows)-final_count,"invalid":invalid_row_count}
    def clear_game_data(self,gid):
        self.sample_write_barrier()
        with self.lock,self.db:
            self.db.execute("DELETE FROM samples WHERE game_id=?",(gid,))
            self.db.execute("DELETE FROM learning_sessions WHERE game_id=?",(gid,))
            self.db.execute("DELETE FROM models WHERE game_id=?",(gid,))
            self.db.execute("DELETE FROM model_backups WHERE game_id=?",(gid,))
            self.db.execute("DELETE FROM rejections WHERE game_id=?",(gid,))
            self.db.execute("UPDATE games SET needs_review=0,last_review=NULL WHERE id=?",(gid,))
        self.model_cache.pop(gid,None)
    def save_window_descriptor(self,target):
        self._ensure_writable()
        rule=dict(target.get("title_rule") or {"mode":"none","value":""})
        if str(rule.get("mode","none")) not in TITLE_RULE_MODES:
            rule={"mode":"none","value":""}
        descriptor={"process_path":os.path.normcase(str(target.get("process_path",""))),"class":str(target.get("class","")),"title_rule":rule,"client_size":list(target.get("client_size",[]))[:2],"dpi":safe_int(target.get("selected_dpi",target.get("dpi",0)),0),"integrity":safe_int(target.get("integrity",-1),-1),"content_rect_norm":[round(safe_float(value,0.0),8) for value in target.get("content_rect_norm",[0,0,1,1])[:4]],"content_aspect":safe_float(target.get("content_aspect",0.0),0.0),"content_source":str(target.get("content_source","manual")),"window_rule_version":WINDOW_RULE_VERSION,"saved":time.time()}
        with self.lock,self.db:
            self.db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('last_window_descriptor',?)",(json.dumps(descriptor,ensure_ascii=False,separators=(",",":")),))
        return descriptor
    def load_window_descriptor(self):
        try:
            with self.lock:
                row=self.db.execute("SELECT value FROM meta WHERE key='last_window_descriptor'").fetchone()
            value=json.loads(row[0]) if row else None
            return value if isinstance(value,dict) else None
        except Exception as error:
            self.logger.write("WINDOW_DESCRIPTOR_LOAD_FAILED",error)
            return None
    def _calibration_identity_key(self,target):
        if not isinstance(target,dict):
            return ""
        raw_size=target.get("client_size")
        if not isinstance(raw_size,(list,tuple)):
            raw_size=[0,0]
        payload={"process_path":os.path.normcase(str(target.get("process_path",""))),"class":str(target.get("class","")),"client_size":[safe_int(value,0,0) for value in list(raw_size)[:2]],"dpi":safe_int(target.get("selected_dpi",target.get("dpi",0)),0,0),"content_rect_norm":[round(safe_float(value,0.0),6) for value in target.get("content_rect_norm",[0,0,1,1])[:4]],"window_rule_version":WINDOW_RULE_VERSION,"capture_backend_version":CAPTURE_BACKEND_VERSION}
        while len(payload["client_size"])<2:
            payload["client_size"].append(0)
        if not payload["process_path"] or not payload["class"] or payload["client_size"]==[0,0] or payload["dpi"]<=0:
            return ""
        return hashlib.sha256(canonical_bytes(payload)).hexdigest()
    def save_capture_calibration(self,target,calibration):
        identity_key=self._calibration_identity_key(target)
        backend=str(calibration.get("validated_backend","")) if isinstance(calibration,dict) else ""
        if not identity_key or not backend:
            return False
        payload={"format_version":FORMAT_VERSION,"saved":time.time(),"identity_key":identity_key,"backend":backend,"calibration":dict(calibration)}
        payload=add_checksum(payload)
        text=json.dumps(payload,ensure_ascii=False,separators=(",",":"),sort_keys=True)
        with self.lock,self.db:
            self.db.execute("INSERT INTO capture_calibrations(identity_key,backend,saved,payload,checksum) VALUES(?,?,?,?,?) ON CONFLICT(identity_key,backend) DO UPDATE SET saved=excluded.saved,payload=excluded.payload,checksum=excluded.checksum",(identity_key,backend,payload["saved"],text,payload["checksum"]))
        return True
    def load_capture_calibration(self,target):
        identity_key=self._calibration_identity_key(target)
        if not identity_key:
            return None
        with self.lock:
            rows=self.db.execute("SELECT backend,payload,checksum FROM capture_calibrations WHERE identity_key=? ORDER BY saved DESC",(identity_key,)).fetchall()
        for row in rows:
            try:
                payload=json.loads(row["payload"])
                if not isinstance(payload,dict) or payload.get("checksum")!=row["checksum"] or not verify_checksum(payload) or payload.get("identity_key")!=identity_key:
                    continue
                calibration=payload.get("calibration")
                if not isinstance(calibration,dict) or str(calibration.get("validated_backend",""))!=str(row["backend"]):
                    continue
                result=dict(calibration)
                result["dynamic_passed"]=False
                result["cache_loaded"]=True
                return result
            except Exception as error:
                self.logger.write("CAPTURE_CALIBRATION_LOAD_FAILED",error,window_identity=target,details={"identity_key":identity_key,"backend":str(row["backend"])})
                continue
        return None
    def _pack_model(self,model):
        item=dict(model)
        packed=[]
        for proto in item.get("prototypes",[]):
            entry=dict(proto)
            entry["f_blob"]=base64.b64encode(zlib.compress(feature_bytes(entry.pop("f")),6)).decode("ascii")
            coarse=entry.pop("coarse",None)
            entry["coarse_blob"]=base64.b64encode(bytes(coarse) if isinstance(coarse,(bytes,bytearray)) else coarse_feature(zlib.decompress(base64.b64decode(entry["f_blob"])))).decode("ascii")
            packed.append(entry)
        item["prototypes"]=packed
        return zlib.compress(canonical_bytes(item),9)
    def _unpack_model(self,payload):
        item=json.loads(bounded_decompress(payload,32*1024*1024).decode("utf-8"))
        unpacked=[]
        for proto in item.get("prototypes",[]):
            entry=dict(proto)
            entry["f"]=bounded_decompress(base64.b64decode(entry.pop("f_blob"),validate=True),FEATURE_LEN*2)
            entry["coarse"]=base64.b64decode(entry.pop("coarse_blob"),validate=True)
            unpacked.append(entry)
        item["prototypes"]=unpacked
        return item
    def _upgrade_model(self,item,gid,complete):
        try:
            if not isinstance(item,dict) or str(item.get("game_id",gid))!=gid:
                return None
            if normalized_compatibility_signature(compatibility_signature_from_item(item))!=compatibility_signature():
                return None
            if int(item.get("format_version",0))!=FORMAT_VERSION or int(item.get("action_algorithm_version",0))!=ACTION_ALGORITHM_VERSION:
                return None
            upgraded=[]
            for proto in item.get("prototypes",[]):
                if not isinstance(proto,dict):
                    return None
                action=normalize_action(proto.get("a"))
                feature=upgrade_feature(proto.get("f"),int(item.get("feature_algorithm_version",FEATURE_ALGORITHM_VERSION)))
                if not action or feature is None:
                    return None
                entry=dict(proto)
                entry["f"]=feature
                entry["coarse"]=coarse_feature(feature)
                entry["temporal"]=temporal_from_context(entry.get("temporal",{}))
                upgraded.append(entry)
            result=dict(item)
            result.update({"format_version":FORMAT_VERSION,"model_schema_version":MODEL_SCHEMA_VERSION,"feature_width":FEATURE_W,"feature_height":FEATURE_H,"feature_algorithm_version":FEATURE_ALGORITHM_VERSION,"action_algorithm_version":ACTION_ALGORITHM_VERSION,"game_id":gid,"complete":bool(complete),"compatibility_signature":compatibility_signature(),"source_build_hash":str(item.get("source_build_hash") or item.get("algorithm_snapshot",{}).get("build_hash") or item.get("algorithm_snapshot",{}).get("source_build_hash") or ""),"algorithm_snapshot":algorithm_snapshot(),"prototypes":upgraded})
            return result
        except Exception:
            return None
    def _model_valid(self,item,gid,complete=True):
        try:
            if not isinstance(item,dict) or item.get("format_version")!=FORMAT_VERSION or item.get("feature_width")!=FEATURE_W or item.get("feature_height")!=FEATURE_H or item.get("feature_algorithm_version")!=FEATURE_ALGORITHM_VERSION or item.get("action_algorithm_version")!=ACTION_ALGORITHM_VERSION or item.get("game_id")!=gid or bool(item.get("complete"))!=bool(complete) or normalized_compatibility_signature(compatibility_signature_from_item(item))!=compatibility_signature():
                return False
            binding=item.get("model_binding")
            if not isinstance(binding,dict) or binding.get("window_rule_version")!=WINDOW_RULE_VERSION or binding.get("capture_backend_version")!=CAPTURE_BACKEND_VERSION or not binding.get("process_paths") or not binding.get("window_classes") or not binding.get("content_rect_norms") or not finite_number(binding.get("content_aspect_min")) or not finite_number(binding.get("content_aspect_max")) or float(binding.get("content_aspect_min",0))<=0 or float(binding.get("content_aspect_max",0))<=0 or safe_int(binding.get("dpi_min",0),0)<=0 or safe_int(binding.get("dpi_max",0),0)<=0 or not binding.get("capture_methods"):
                return False
            if not isinstance(item.get("sequence_model"),dict) or len(str(item.get("safety_profile_checksum","")))!=64:
                return False
            prototypes=item.get("prototypes")
            if not isinstance(prototypes,list) or not prototypes or len(prototypes)>MAX_PROTOTYPES:
                return False
            for proto in prototypes:
                if not isinstance(proto,dict):
                    return False
                temporal=temporal_from_context(proto.get("temporal",{}))
                if not str(proto.get("id","")) or not str(proto.get("cluster_id","")) or not str(proto.get("canonical_action_signature","")) or not feature_valid(proto.get("f")) or not isinstance(proto.get("coarse"),(bytes,bytearray)) or len(proto.get("coarse"))!=COARSE_LEN or not normalize_action(proto.get("a")) or not finite_number(proto.get("threshold")) or float(proto.get("threshold"))<=0 or int(proto.get("support",0))<=0 or not temporal.get("complete") or not finite_number(proto.get("temporal_threshold",0)) or float(proto.get("temporal_threshold",0))<=0:
                    return False
                conflict=proto.get("nearest_conflicting_distance")
                if conflict is not None and (not finite_number(conflict) or float(conflict)<0):
                    return False
                rejected=proto.get("nearest_rejected_distance")
                if rejected is not None and (not finite_number(rejected) or float(rejected)<0):
                    return False
                if not finite_number(proto.get("minimum_second_candidate_gap",0)) or str(proto.get("repeat_policy","one_shot")) not in REPEAT_POLICIES or not finite_number(proto.get("max_rate",1.0)) or float(proto.get("max_rate",1.0))<=0:
                    return False
            validation=item.get("validation")
            if complete and not any(bool(proto.get("authorized",False)) for proto in prototypes):
                return False
            return isinstance(validation,dict) and isinstance(item.get("capture_backends"),list) and bool(item.get("capture_backends"))
        except Exception:
            return False
    def save_model(self,gid,model,complete=True):
        item=dict(model)
        item.update({"format_version":FORMAT_VERSION,"model_schema_version":MODEL_SCHEMA_VERSION,"feature_width":FEATURE_W,"feature_height":FEATURE_H,"feature_algorithm_version":FEATURE_ALGORITHM_VERSION,"action_algorithm_version":ACTION_ALGORITHM_VERSION,"game_id":gid,"complete":bool(complete),"compatibility_signature":compatibility_signature(),"source_build_hash":current_build_hash(),"algorithm_snapshot":algorithm_snapshot(),"saved":time.time()})
        clean_prototypes=[]
        for proto in item.get("prototypes",[]):
            entry=dict(proto)
            runtime=action_runtime_metadata(entry.get("a"))
            action=runtime["action"]
            if action:
                entry["a"]=action
                entry["canonical_action_signature"]=str(entry.get("canonical_action_signature") or action_signature(action))
                entry["cluster_id"]=str(entry.get("cluster_id") or "action|"+runtime["family"]+"|"+hashlib.sha256(canonical_bytes(action)).hexdigest()[:20])
            if "coarse" not in entry and feature_valid(entry.get("f")):
                entry["coarse"]=coarse_feature(entry["f"])
            entry["repeat_policy"]=str(entry.get("repeat_policy","one_shot")) if str(entry.get("repeat_policy","one_shot")) in REPEAT_POLICIES else "one_shot"
            entry["max_rate"]=float(entry.get("max_rate",3.0)) if finite_number(entry.get("max_rate",3.0)) else 3.0
            entry["capture_methods"]=sorted({str(value) for value in entry.get("capture_methods",[])})
            entry["authorized"]=bool(entry.get("authorized",False))
            clean_prototypes.append(entry)
        item["prototypes"]=clean_prototypes
        if not self._model_valid(item,gid,complete):
            raise RuntimeError("模型完整schema校验失败")
        payload=self._pack_model(item)
        checksum=hashlib.sha256(payload).hexdigest()
        slot="complete" if complete else "partial"
        validation=json.dumps(item.get("validation",{}),ensure_ascii=False,separators=(",",":"))
        with self.critical_transaction():
            if complete:
                old=self.db.execute("SELECT saved,prototype_count,validation,payload,checksum FROM models WHERE game_id=? AND slot='complete'",(gid,)).fetchone()
                if old:
                    self.db.execute("INSERT INTO model_backups(game_id,created,prototype_count,validation,payload,checksum) VALUES(?,?,?,?,?,?)",(gid,old["saved"],old["prototype_count"],old["validation"],old["payload"],old["checksum"]))
                    self.db.execute("DELETE FROM model_backups WHERE game_id=? AND id NOT IN (SELECT id FROM model_backups WHERE game_id=? ORDER BY id DESC LIMIT 5)",(gid,gid))
            self.db.execute("INSERT INTO models(game_id,slot,saved,created,prototype_count,validation,payload,checksum) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(game_id,slot) DO UPDATE SET saved=excluded.saved,created=excluded.created,prototype_count=excluded.prototype_count,validation=excluded.validation,payload=excluded.payload,checksum=excluded.checksum",(gid,slot,item["saved"],float(item.get("created",time.time())),len(item["prototypes"]),validation,sqlite3.Binary(payload),checksum))
            if complete:
                self.db.execute("DELETE FROM models WHERE game_id=? AND slot='partial'",(gid,))
                self.db.execute("UPDATE games SET needs_review=0,last_review=? WHERE id=?",(float(item.get("created",time.time())),gid))
            elif str(item.get("validation",{}).get("status",""))=="basic_safe":
                self.db.execute("UPDATE games SET needs_review=0,last_review=? WHERE id=?",(float(item.get("created",time.time())),gid))
        if complete:
            self.model_cache[gid]=self._prepare_model_runtime(item)
    def _prepare_model_runtime(self,item):
        model=dict(item)
        prototypes=[]
        backend_index=defaultdict(list)
        bucket_index=defaultdict(list)
        for index,proto in enumerate(model.get("prototypes",[])):
            entry=dict(proto)
            runtime=action_runtime_metadata(entry.get("a"))
            entry["a"]=runtime["action"]
            entry["action_family"]=runtime["family"]
            entry["feature_view"]=memoryview(entry["f"]).toreadonly()
            entry["channel_offsets"]=(0,PIXELS,PIXELS*2,PIXELS*3,PIXELS*4)
            entry["dangerous"]=runtime["dangerous"]
            entry["strictness"]=runtime["strictness"]
            entry["cooldown"]=runtime["cooldown"]
            entry["capture_methods"]=frozenset(str(value) for value in entry.get("capture_methods",[]))
            entry["temporal_cached"]=temporal_from_context(entry.get("temporal",{}))
            entry["coarse_bucket"]=coarse_bucket_key(entry.get("coarse"))
            prototypes.append(entry)
            for backend in entry["capture_methods"] or frozenset({"unknown"}):
                backend_index[backend].append(index)
                bucket_index[(backend,entry["coarse_bucket"])].append(index)
        model["prototypes"]=prototypes
        model["runtime_index"]={"backend":dict(backend_index),"bucket":dict(bucket_index)}
        model["runtime_token"]=hashlib.sha256((str(model.get("saved",0))+"|"+str(len(prototypes))).encode()).hexdigest()[:16]
        return model
    def _row_model(self,row,gid,complete):
        try:
            if not row or hashlib.sha256(row["payload"]).hexdigest()!=row["checksum"]:
                return None
            item=self._unpack_model(row["payload"])
            item=self._upgrade_model(item,gid,complete)
            return item if self._model_valid(item,gid,complete) else None
        except Exception:
            return None
    def load_model(self,gid):
        cached=self.model_cache.get(gid)
        if cached is not None and self._model_valid(cached,gid,True):
            return cached
        with self.lock:
            row=self.db.execute("SELECT payload,checksum FROM models WHERE game_id=? AND slot='complete'",(gid,)).fetchone()
        item=self._row_model(row,gid,True)
        if item:
            item=self._prepare_model_runtime(item)
            self.model_cache[gid]=item
            return item
        with self.lock:
            backups=self.db.execute("SELECT id,created,prototype_count,validation,payload,checksum FROM model_backups WHERE game_id=? ORDER BY id DESC",(gid,)).fetchall()
        for backup in backups:
            recovered=self._row_model(backup,gid,True)
            if recovered:
                payload=self._pack_model(recovered)
                checksum=hashlib.sha256(payload).hexdigest()
                if not self.read_only:
                    with self.critical_transaction():
                        self.db.execute("INSERT OR REPLACE INTO models(game_id,slot,saved,created,prototype_count,validation,payload,checksum) VALUES(?,?,?,?,?,?,?,?)",(gid,"complete",float(recovered.get("saved",backup["created"])),float(recovered.get("created",backup["created"])),len(recovered["prototypes"]),json.dumps(recovered.get("validation",{}),ensure_ascii=False,separators=(",",":")),sqlite3.Binary(payload),checksum))
                recovered=self._prepare_model_runtime(recovered)
                self.model_cache[gid]=recovered
                return recovered
        if row:
            raise RuntimeError("模型版本、游戏ID、特征尺寸、算法版本或原型schema校验失败，且无法从数据库备份恢复")
        return None
    def load_trainable_model(self,gid):
        with self.lock:
            rows=self.db.execute("SELECT slot,saved,payload,checksum FROM models WHERE game_id=? ORDER BY saved DESC",(gid,)).fetchall()
        invalid_complete=False
        for row in rows:
            complete=str(row["slot"])=="complete"
            item=self._row_model(row,gid,complete)
            if item is None:
                invalid_complete=invalid_complete or complete
                continue
            status=str(item.get("validation",{}).get("status",""))
            authorized=[proto for proto in item.get("prototypes",[]) if bool(proto.get("authorized")) and not bool(proto.get("ambiguous"))]
            if complete and status=="passed" and authorized:
                return self._prepare_model_runtime(item)
            if not complete and status=="basic_safe":
                safe=[proto for proto in authorized if action_family_key(proto.get("a")) in BASIC_SAFE_FAMILIES]
                if safe:
                    item=dict(item)
                    item["prototypes"]=safe
                    item["capture_backends"]=sorted({method for proto in safe for method in proto.get("capture_methods",[])}) or list(item.get("capture_backends",[]))
                    return self._prepare_model_runtime(item)
        complete=self.load_model(gid)
        if complete is not None:
            return complete
        if invalid_complete:
            raise RuntimeError("完整模型损坏且没有可训练的基础安全模型")
        return None
    def model_metadata(self,gid):
        with self.lock:
            rows=self.db.execute("SELECT slot,saved,created,prototype_count,validation FROM models WHERE game_id=? ORDER BY saved DESC",(gid,)).fetchall()
        if not rows:
            return None
        parsed=[]
        for row in rows:
            try:
                validation=json.loads(row["validation"])
            except Exception:
                validation={"status":"invalid"}
            parsed.append({"slot":row["slot"],"saved":row["saved"],"created":row["created"],"prototype_count":row["prototype_count"],"validation":validation})
        latest=dict(parsed[0])
        trainable=next((dict(item) for item in parsed if str(item.get("validation",{}).get("status","")) in {"passed","basic_safe"} and safe_int(item.get("validation",{}).get("authorized_prototypes",0),0)>0),None)
        latest["trainable"]=trainable
        return latest
    def restore_model_backup(self,gid):
        with self.lock:
            backups=self.db.execute("SELECT id,created,prototype_count,validation,payload,checksum FROM model_backups WHERE game_id=? ORDER BY id DESC",(gid,)).fetchall()
        for backup in backups:
            item=self._row_model(backup,gid,True)
            if item:
                payload=self._pack_model(item)
                checksum=hashlib.sha256(payload).hexdigest()
                with self.lock,self.db:
                    self.db.execute("INSERT OR REPLACE INTO models(game_id,slot,saved,created,prototype_count,validation,payload,checksum) VALUES(?,?,?,?,?,?,?,?)",(gid,"complete",float(item.get("saved",backup["created"])),float(item.get("created",backup["created"])),len(item["prototypes"]),json.dumps(item.get("validation",{}),ensure_ascii=False,separators=(",",":")),sqlite3.Binary(payload),checksum))
                self.model_cache[gid]=item
                return True
        raise RuntimeError("没有通过完整版本、游戏ID、特征尺寸、算法版本和原型schema校验的模型备份")
    def integrity_check(self):
        self.sample_write_barrier()
        with self.lock:
            row=self.db.execute("PRAGMA quick_check").fetchone()
        return bool(row and str(row[0]).lower()=="ok")
    def emergency_checkpoint(self,reason="forced_exit"):
        with self.pending_lock:
            pending_count=len(self.pending_samples)
            inflight=self.writer_inflight
            writer_error=self.writer_error
        record={"created":time.time(),"reason":str(reason),"pending_samples":pending_count,"writer_inflight":inflight,"writer_error":writer_error,"read_only":self.read_only}
        try:
            path=self.base/"recovery.log"
            with path.open("a",encoding="utf-8") as handle:
                handle.write(json.dumps(record,ensure_ascii=False,separators=(",",":"))+"\n")
        except Exception:
            pass
        try:
            if self.db is not None and not self.read_only:
                with self.lock:
                    self.db.execute("PRAGMA wal_checkpoint(FULL)")
        except Exception:
            pass
        return record
    def close(self,timeout=4.0):
        if self.closed:
            return True
        self.closing=True
        if not self.read_only:
            try:
                self.sample_write_barrier(max(0.5,float(timeout)))
            except Exception as error:
                self.logger.write("DATABASE_CLOSE_BARRIER_FAILED",error)
                return False
        self.writer_stop.set()
        self.pending_event.set()
        thread=self.writer_thread
        if thread and thread.is_alive() and thread is not threading.current_thread() and timeout>0:
            thread.join(max(0.0,float(timeout)))
        stopped=not bool(thread and thread.is_alive())
        if not stopped:
            return False
        try:
            if not self.read_only:
                self.db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        except Exception as error:
            self.logger.write("DATABASE_FINAL_CHECKPOINT_FAILED",error)
        try:
            self.db.close()
        except Exception as error:
            self.logger.write("DATABASE_CONNECTION_CLOSE_FAILED",error)
        self.closed=True
        return True
class App:
    def __init__(self,root):
        self.root=root
        self.api=WinBridge()
        self.store=DataStore()
        self.selected_game=self.store.selected_game()
        self.selected_window=None
        self.window_recommendation=self.store.load_window_descriptor()
        self.lifecycle=ModeLifecycle()
        self.mode=None
        self.mode_state=MODE_IDLE
        self.stop_event=None
        self.mode_thread=None
        self.active_session=None
        self.review_process=None
        self.pending_mode_result=None
        self.pending_mode_error=None
        self.mode_shutdown_deadline=None
        self.mode_shutdown_forced=[]
        self.mode_stop_lock=threading.RLock()
        self.mode_stop_started=False
        self.mode_shutdown_polling=False
        self.controls=[]
        self.control_buttons={}
        self.stop_button=None
        self.ask_window=None
        self.ask_buffer=None
        self.ask_producer=None
        self.ask_answer_queue=None
        self.ask_after_ids=set()
        self.ask_escape_armed=False
        self.global_escape_armed=True
        self.ask_session_id=None
        self.ask_counts=None
        self.error_recent={}
        self.result_modal=None
        self.result_modal_widget=None
        self.ui_queue=queue.Queue(maxsize=512)
        self.ui_lock=threading.RLock()
        self.ui_latest={}
        self.ui_scheduled=set()
        self.background_lock=threading.RLock()
        self.background_generations=defaultdict(int)
        self.background_threads=set()
        self.refresh_signature=None
        self.closing=False
        self.shutdown_started=False
        self.shutdown_deadline=None
        self.review_distance_cache=BoundedLRU(50000)
        self.candidate_cache=BoundedLRU(64)
        self.storage_fault=bool(self.store.read_only)
        self.training_ready=False
        self.flow_text=tk.StringVar(value="1. 游戏：未完成\n2. 窗口：未完成\n3. 学习数据：不足\n4. 模型：不可训练")
        self.active_model_runtime=None
        self.learning_controller=LearningController(self)
        self.review_controller=ReviewController(self)
        self.training_controller=TrainingController(self)
        self.teaching_controller=TeachingController(self)
        self.status=tk.StringVar(value="就绪")
        self.game_text=tk.StringVar(value="未选择")
        self.window_text=tk.StringVar(value="未选择")
        self.window_detail=tk.StringVar(value="PID：-  类名：-  客户区：-")
        self.capture_text=tk.StringVar(value="采集方式：未检测")
        self.sample_text=tk.StringVar(value="样本：有效0  废弃0  数据0 KB")
        self.model_text=tk.StringVar(value="模型：无  需要复习：否")
        self.confidence_text=tk.StringVar(value="训练置信度：-")
        self.input_text=tk.StringVar(value="自动输入：已锁定")
        self.progress_value=tk.DoubleVar(value=0.0)
        self.root.report_callback_exception=self.tk_exception
        self.store.set_writer_error_callback(self._writer_status_changed)
        self._build()
        self._refresh_all()
        self._apply_storage_controls()
        if self.store.read_only:
            self.status.set(self.store.read_only_reason)
        self.root.protocol("WM_DELETE_WINDOW",self.close)
        self.root.after(25,self.process_ui_queue)
        self.root.after(35,self.poll_global_escape)
        self.root.after(1200,self.periodic_refresh)
    def _writer_status_changed(self,error):
        def apply():
            self.storage_fault=bool(error) or bool(self.store.read_only)
            if error:
                self.status.set("样本写入失败，学习与请教已锁定："+str(error))
                if self.mode in {"学习","请教"}:
                    self.request_mode_stop("failed","样本写入失败")
            else:
                self.status.set("样本写入线程已恢复")
            self._apply_storage_controls()
        self.ui(apply,"writer_status")
    def _apply_storage_controls(self):
        self._update_control_availability()
    def _update_control_availability(self):
        running=self.mode_state!=MODE_IDLE
        blocked=bool(self.storage_fault or self.store.read_only)
        for name,button in self.control_buttons.items():
            try:
                if name=="停止":
                    button.configure(state="normal" if running else "disabled")
                elif running:
                    button.configure(state="disabled")
                elif name in {"学习","复习","请教"} and blocked:
                    button.configure(state="disabled")
                elif name=="训练" and not self.training_ready:
                    button.configure(state="disabled")
                else:
                    button.configure(state="normal")
            except Exception:
                pass
    def _forced_exit(self,reason,exit_function=os._exit):
        self.api.block_input()
        self.api.release_all_buttons()
        try:
            if self.review_process is not None:
                self.review_process.terminate(0.2)
        except Exception:
            pass
        try:
            self.api.stop_capture_processes(0.0,True)
        except Exception:
            pass
        try:
            self.store.emergency_checkpoint(reason)
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass
        exit_function(2)
    def _build(self):
        self.root.title("通用游戏AI")
        self.root.geometry("860x760")
        self.root.minsize(760,680)
        self.root.option_add("*Font",("Microsoft YaHei UI",10))
        outer=ttk.Frame(self.root,padding=18)
        outer.pack(fill="both",expand=True)
        ttk.Label(outer,text="通用游戏AI控制面板",font=("Microsoft YaHei UI",18,"bold")).pack(anchor="w",pady=(0,12))
        flow=ttk.LabelFrame(outer,text="规定流程",padding=12)
        flow.pack(fill="x",pady=(0,12))
        primary=ttk.Frame(flow)
        primary.pack(fill="x")
        primary_specs=[("游戏",self.open_game_dialog),("选择窗口",self.open_window_dialog),("学习",self.start_learning),("复习",self.start_review),("训练",self.start_training),("请教",self.start_ask)]
        for index,(name,command) in enumerate(primary_specs):
            button=ttk.Button(primary,text=name,command=command)
            self.control_buttons[name]=button
            self.controls.append(button)
            button.grid(row=index//3,column=index%3,sticky="nsew",padx=6,pady=6,ipady=12)
        for column in range(3):
            primary.columnconfigure(column,weight=1)
        ttk.Label(flow,textvariable=self.flow_text,justify="left",wraplength=780).pack(anchor="w",fill="x",pady=(8,0))
        stop_frame=ttk.Frame(outer)
        stop_frame.pack(fill="x",pady=(0,12))
        self.stop_button=ttk.Button(stop_frame,text="停止",command=self.request_stop,state="disabled")
        self.control_buttons["停止"]=self.stop_button
        self.stop_button.pack(fill="x",ipady=8)
        info=ttk.LabelFrame(outer,text="当前状态",padding=12)
        info.pack(fill="x",pady=(0,12))
        labels=[("当前游戏：",self.game_text),("目标窗口：",self.window_text),("窗口身份：",self.window_detail),("采集兼容性：",self.capture_text),("输入权限：",self.input_text),("数据统计：",self.sample_text),("模型状态：",self.model_text),("识别状态：",self.confidence_text)]
        for row,(name,value) in enumerate(labels):
            ttk.Label(info,text=name).grid(row=row,column=0,sticky="nw",pady=2)
            ttk.Label(info,textvariable=value,wraplength=680).grid(row=row,column=1,sticky="nw",pady=2)
        info.columnconfigure(1,weight=1)
        advanced_header=ttk.Frame(outer)
        advanced_header.pack(fill="x")
        self.advanced_visible=tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_header,text="高级设置",variable=self.advanced_visible,command=self._toggle_advanced).pack(anchor="w")
        self.advanced_frame=ttk.Frame(outer)
        advanced_specs=[("任务与安全",self.open_task_dialog),("重新测试采集后端",self.retest_capture_backends),("数据清理",self.open_data_dialog)]
        for index,(name,command) in enumerate(advanced_specs):
            button=ttk.Button(self.advanced_frame,text=name,command=command)
            self.control_buttons[name]=button
            self.controls.append(button)
            button.grid(row=0,column=index,sticky="nsew",padx=6,pady=6,ipady=8)
            self.advanced_frame.columnconfigure(index,weight=1)
        self.progress_bar=ttk.Progressbar(outer,variable=self.progress_value,maximum=100)
        self.progress_bar.pack(fill="x",pady=(12,8))
        bottom=ttk.Frame(outer)
        bottom.pack(fill="x")
        ttk.Label(bottom,text="状态：").pack(side="left")
        ttk.Label(bottom,textvariable=self.status,wraplength=620).pack(side="left",fill="x",expand=True)
        ttk.Label(bottom,text="ESC或“停止”结束").pack(side="right")
    def _toggle_advanced(self):
        if self.advanced_visible.get():
            self.advanced_frame.pack(fill="x",pady=(0,8),before=self.progress_bar)
        else:
            self.advanced_frame.pack_forget()
    def tk_exception(self,exc_type,exc_value,exc_traceback):
        self.show_error("".join(traceback.format_exception(exc_type,exc_value,exc_traceback)))
    def ui(self,callback,key=None):
        if self.shutdown_started:
            return
        if threading.current_thread() is threading.main_thread():
            try:
                callback()
            except Exception as error:
                self.store.log_error("UI_CALLBACK_FAILED",error,mode=self.mode)
                if not self.closing:
                    self.show_error(traceback.format_exc())
            return
        if key is None:
            try:
                self.ui_queue.put_nowait(("call",callback))
            except queue.Full:
                self.store.log_error("UI_QUEUE_FULL",details={"kind":"call"})
            return
        token=str(key)
        with self.ui_lock:
            self.ui_latest[token]=callback
            if token in self.ui_scheduled:
                return
            self.ui_scheduled.add(token)
        try:
            self.ui_queue.put_nowait(("latest",token))
        except queue.Full:
            with self.ui_lock:
                self.ui_scheduled.discard(token)
            self.store.log_error("UI_QUEUE_FULL",details={"kind":"latest","key":token})
    def close_dialog(self,win,state=None):
        if isinstance(state,dict):
            if state.get("closed"):
                return False
            state["closed"]=True
            for key in state.get("background_keys",[]):
                with self.background_lock:
                    self.background_generations[str(key)]+=1
        try:
            win.grab_release()
        except Exception:
            pass
        try:
            win.destroy()
        except Exception:
            pass
        return True
    def run_background(self,key,task,apply=None,on_error=None):
        token=str(key)
        with self.background_lock:
            if self.closing or self.shutdown_started:
                return None
            self.background_generations[token]+=1
            generation=self.background_generations[token]
        def current_generation():
            with self.background_lock:
                return generation==self.background_generations.get(token,0)
        def worker():
            try:
                result=task()
                def finish():
                    if current_generation() and not self.closing and not self.shutdown_started and apply is not None:
                        apply(result)
                self.ui(finish,"background:"+token)
            except Exception as error:
                self.store.log_error("BACKGROUND_TASK_FAILED",error,mode=self.mode,details={"task":token,"generation":generation})
                def fail(error=error):
                    if current_generation() and not self.closing and not self.shutdown_started and on_error is not None:
                        on_error(error)
                self.ui(fail,"background_error:"+token)
            finally:
                self.store.close_current_thread()
                current=threading.current_thread()
                with self.background_lock:
                    self.background_threads.discard(current)
        thread=threading.Thread(target=worker,name="UniversalGameAI-Background-"+token,daemon=True)
        with self.background_lock:
            self.background_threads.add(thread)
        thread.start()
        return generation
    def process_ui_queue(self):
        try:
            for _ in range(200):
                try:
                    kind,payload=self.ui_queue.get_nowait()
                except queue.Empty:
                    break
                callback=None
                if kind=="call":
                    callback=payload
                elif kind=="latest":
                    with self.ui_lock:
                        callback=self.ui_latest.pop(payload,None)
                        self.ui_scheduled.discard(payload)
                if callback is not None and not self.shutdown_started:
                    try:
                        callback()
                    except Exception as error:
                        self.store.log_error("UI_QUEUE_CALLBACK_FAILED",error,mode=self.mode)
                        self.show_error(traceback.format_exc())
        finally:
            if not self.shutdown_started:
                try:
                    self.root.after(25,self.process_ui_queue)
                except Exception as error:
                    self.store.log_error("UI_QUEUE_RESCHEDULE_FAILED",error,mode=self.mode)
    def _begin_mode_stopping(self,result,error=None):
        if self.shutdown_started or self.closing and self.mode_state==MODE_IDLE:
            return
        if result is None:
            result=ModeResult("failed",str(self.mode or "模式")+"失败")
        priority={"completed":0,"stopped":1,"failed":2}
        _,_,_,requested,reason=self.lifecycle.snapshot()
        effective=result.status
        if priority.get(requested,1)>priority.get(effective,0):
            effective=requested
        if effective!=result.status:
            summary=reason or (str(self.mode or "模式")+("失败" if effective=="failed" else "已停止"))
            result=ModeResult(effective,summary,dict(result.details))
        self.pending_mode_result=result
        self.pending_mode_error=error
        self.request_mode_stop(result.status,result.summary if result.status=="failed" else reason or result.summary)
        self.mode_shutdown_deadline=time.monotonic()+5.0
        self.status.set(str(self.mode or "模式")+"正在停止资源，控制按钮保持禁用")
        if not self.mode_shutdown_polling:
            self.mode_shutdown_polling=True
            self.root.after(25,self._poll_mode_shutdown)
    def _poll_mode_shutdown(self):
        if self.mode_state!=MODE_STOPPING:
            return
        self.api.block_input()
        self.api.release_all_buttons()
        session_done=True
        pending=[]
        if self.active_session is not None:
            session_done=self.active_session.close(0.0)
            if not session_done:
                pending.extend(self.active_session.pending_names())
        deadline_reached=bool(self.mode_shutdown_deadline is not None and time.monotonic()>=self.mode_shutdown_deadline)
        if self.review_process is not None:
            self.review_process.request_stop()
            if deadline_reached and self.review_process.alive():
                self.review_process.terminate(0.2)
                self.mode_shutdown_forced.append("OfflineReviewProcess")
            if self.review_process.alive():
                pending.append("OfflineReviewProcess")
        capture_pending=self.api.stop_capture_processes(0.0,False)
        if deadline_reached and capture_pending:
            forced=self.api.stop_capture_processes(0.0,True)
            self.mode_shutdown_forced.extend(name for name in capture_pending if name not in self.mode_shutdown_forced)
            capture_pending=forced
        thread_alive=bool(self.mode_thread and self.mode_thread.is_alive())
        if thread_alive:
            pending.append("模式线程")
        pending.extend("CaptureProcess:"+name for name in capture_pending)
        if deadline_reached and thread_alive and (self.review_process is None or not self.review_process.alive()):
            self._forced_exit("模式停止超过5秒，Python模式线程未退出")
            return
        if pending or not session_done:
            suffix="；已到关闭期限并执行强制停止："+"、".join(self.mode_shutdown_forced) if self.mode_shutdown_forced else ""
            self.status.set("STOPPING：等待资源退出："+"、".join(sorted(set(pending)))+suffix)
            self.root.after(50,self._poll_mode_shutdown)
            return
        result=self.pending_mode_result or ModeResult("failed",str(self.mode or "模式")+"失败")
        error=self.pending_mode_error
        name=str(self.mode or "模式")
        if self.mode_shutdown_forced:
            result.details["forced_processes"]=list(dict.fromkeys(self.mode_shutdown_forced))
            result.summary+="；已强制停止："+"、".join(result.details["forced_processes"])
        self.mode_thread=None
        self.active_session=None
        self.review_process=None
        self.ask_buffer=None
        self.ask_producer=None
        self.ask_answer_queue=None
        self.ask_session_id=None
        self.ask_counts=None
        self.stop_event=None
        self.mode=None
        self.mode_state=MODE_IDLE
        self.lifecycle.finish()
        self.pending_mode_result=None
        self.pending_mode_error=None
        self.mode_shutdown_deadline=None
        self.mode_stop_started=False
        self.mode_shutdown_polling=False
        self.set_controls(False)
        self.progress_value.set(0)
        self.status.set(result.summary)
        self._refresh_all()
        if self.closing:
            self._poll_shutdown()
            return
        if result.status=="failed":
            self.show_info(name+"失败",error or result.summary)
        elif error:
            self.show_info(name+"失败",error)
        else:
            title=name+("已完成" if result.status=="completed" else "已停止")
            self.show_info(title,result.summary)
    def _destroy_ask_window(self):
        win=self.ask_window
        self.ask_window=None
        if win is not None:
            for after_id in list(self.ask_after_ids):
                try:
                    win.after_cancel(after_id)
                except Exception:
                    pass
            self.ask_after_ids.clear()
            try:
                win.destroy()
            except Exception:
                pass
    def _fail_active_mode(self,message):
        self.request_mode_stop("failed",str(message))
    def retest_capture_backends(self):
        self.start_worker("重测采集",self.retest_capture_worker,True)
    def retest_capture_worker(self):
        target=self.require_window(False)
        self.api.reset_capture_backends(target)
        self.api.calibrations.pop(int(target["hwnd"]),None)
        result=self.ensure_capture_calibration(target,"重新测试采集后端")
        self.lifecycle.mark_running()
        self.mode_state=MODE_RUNNING
        return ModeResult("completed","采集后端重新测试完成："+str(result.get("validated_backend","未知")),{"validated_backends":list(result.get("validated_backends",[]))})
    def poll_global_escape(self):
        if self.shutdown_started:
            return
        try:
            down=self.api.key_down(0x1B)
            if not down:
                self.global_escape_armed=True
            elif self.mode_state!=MODE_IDLE and self.global_escape_armed:
                self.global_escape_armed=False
                self._keyboard_escape()
        except Exception:
            pass
        if not self.shutdown_started:
            try:
                self.root.after(35,self.poll_global_escape)
            except Exception:
                pass
    def set_status(self,text):
        self.ui(lambda:self.status.set(str(text)),"status")
    def set_confidence(self,text):
        self.ui(lambda:self.confidence_text.set(str(text)),"confidence")
    def set_input_status(self,text):
        value=str(text)
        if not value.startswith("自动输入："):
            value="自动输入："+value
        self.ui(lambda:self.input_text.set(value),"input_status")
    def lock_input(self,reason="已锁定"):
        self.api.block_input()
        self.set_input_status(reason)
    def set_progress(self,value):
        self.ui(lambda:self.progress_value.set(max(0.0,min(100.0,float(value)))),"progress")
    def _show_result_modal(self,title,text):
        if self.result_modal is not None:
            try:
                if self.result_modal.winfo_exists():
                    self.result_modal.title(str(title))
                    if self.result_modal_widget is not None:
                        self.result_modal_widget.configure(state="normal")
                        self.result_modal_widget.insert("end","\n\n"+str(text))
                        self.result_modal_widget.configure(state="disabled")
                        self.result_modal_widget.see("end")
                    self.result_modal.lift()
                    return
            except Exception:
                self.result_modal=None
                self.result_modal_widget=None
        previous_grab=None
        try:
            previous_grab=self.root.grab_current()
        except Exception:
            previous_grab=None
        win=tk.Toplevel(self.root)
        self.result_modal=win
        win.title(str(title))
        win.geometry("720x420")
        win.minsize(520,320)
        win.transient(self.root)
        frame=ttk.Frame(win,padding=14)
        frame.pack(fill="both",expand=True)
        ttk.Label(frame,text=str(title),font=("Microsoft YaHei UI",14,"bold")).pack(anchor="w",pady=(0,8))
        body=ttk.Frame(frame)
        body.pack(fill="both",expand=True)
        widget=tk.Text(body,wrap="word",font=("Microsoft YaHei UI",10),relief="solid",borderwidth=1)
        self.result_modal_widget=widget
        scroll=ttk.Scrollbar(body,orient="vertical",command=widget.yview)
        widget.configure(yscrollcommand=scroll.set)
        widget.pack(side="left",fill="both",expand=True)
        scroll.pack(side="right",fill="y")
        widget.insert("1.0",str(text))
        widget.configure(state="disabled")
        closed={"closed":False}
        def confirm():
            if closed["closed"]:
                return
            self.result_modal=None
            self.result_modal_widget=None
            self.close_dialog(win,closed)
            if previous_grab is not None:
                try:
                    if previous_grab.winfo_exists():
                        previous_grab.grab_set()
                except Exception:
                    pass
        ttk.Button(frame,text="确认",command=confirm).pack(pady=(12,0),ipadx=28)
        win.bind("<Return>",lambda event:confirm())
        win.protocol("WM_DELETE_WINDOW",confirm)
        win.bind("<Escape>",lambda event:confirm())
        win.wait_visibility()
        win.grab_set()
        win.focus_force()
        win.wait_window()
    def show_error(self,text):
        if threading.current_thread() is not threading.main_thread():
            self.ui(lambda:self.show_error(text))
            return
        message=str(text).strip() or "未知错误"
        digest=hashlib.sha256(message.encode("utf-8","replace")).hexdigest()
        now=time.monotonic()
        self.error_recent={key:value for key,value in self.error_recent.items() if now-value<6.0}
        if digest in self.error_recent:
            return
        self.error_recent[digest]=now
        self._show_result_modal("报错信息",message)
    def show_info(self,title,text):
        if threading.current_thread() is not threading.main_thread():
            self.ui(lambda:self.show_info(title,text))
            return
        if self.shutdown_started:
            return
        self._show_result_modal(str(title),str(text))
    def prompt_text(self,title,label,initial=""):
        result={"value":None}
        state={"closed":False}
        win=tk.Toplevel(self.root)
        win.title(title)
        win.geometry("440x190")
        win.resizable(False,False)
        win.transient(self.root)
        win.grab_set()
        frame=ttk.Frame(win,padding=18)
        frame.pack(fill="both",expand=True)
        ttk.Label(frame,text=label).pack(anchor="w")
        value=tk.StringVar(value=initial)
        entry=ttk.Entry(frame,textvariable=value)
        entry.pack(fill="x",pady=12)
        error=tk.StringVar()
        ttk.Label(frame,textvariable=error).pack(anchor="w")
        buttons=ttk.Frame(frame)
        buttons.pack(side="bottom")
        def confirm():
            content=value.get().strip()
            if not content:
                error.set("名称不能为空")
                return
            if len(content)>80:
                error.set("名称不能超过80个字符")
                return
            result["value"]=content
            self.close_dialog(win,state)
        def cancel():
            self.close_dialog(win,state)
        ttk.Button(buttons,text="确认",command=confirm).pack(side="left",padx=6)
        ttk.Button(buttons,text="取消",command=cancel).pack(side="left",padx=6)
        entry.bind("<Return>",lambda event:confirm())
        entry.bind("<Escape>",lambda event:cancel())
        win.protocol("WM_DELETE_WINDOW",cancel)
        entry.focus_set()
        win.wait_window()
        return result["value"]
    def confirm_dialog(self,title,text):
        result={"value":False}
        state={"closed":False}
        win=tk.Toplevel(self.root)
        win.title(title)
        win.geometry("500x210")
        win.resizable(False,False)
        win.transient(self.root)
        win.grab_set()
        frame=ttk.Frame(win,padding=20)
        frame.pack(fill="both",expand=True)
        ttk.Label(frame,text=text,wraplength=450,justify="left").pack(fill="x",expand=True)
        buttons=ttk.Frame(frame)
        buttons.pack(side="bottom")
        def confirm():
            result["value"]=True
            self.close_dialog(win,state)
        def cancel():
            self.close_dialog(win,state)
        ttk.Button(buttons,text="确认",command=confirm).pack(side="left",padx=6)
        ttk.Button(buttons,text="取消",command=cancel).pack(side="left",padx=6)
        win.protocol("WM_DELETE_WINDOW",cancel)
        win.bind("<Escape>",lambda event:cancel())
        win.wait_window()
        return result["value"]
    def _window_state_signature(self,window):
        if not isinstance(window,dict):
            return None
        hwnd=safe_int(window.get("hwnd",0),0)
        if not hwnd:
            return (0,False,False,None,None)
        try:
            exists=bool(self.api.user32.IsWindow(hwnd))
            minimized=bool(self.api.user32.IsIconic(hwnd)) if exists else False
            foreground=int(self.api.user32.GetForegroundWindow() or 0)==hwnd if exists else False
            client=self.api.client_rect(hwnd) if exists and not minimized else None
            dpi=self.api.dpi_for_window(hwnd) if exists else 0
            return (hwnd,exists,minimized,foreground,tuple(client) if client else None,dpi)
        except Exception as error:
            return (hwnd,False,False,False,None,0,type(error).__name__,str(error))
    def _collect_refresh_snapshot(self,game,window,force):
        signature=(self.store.data_version_signature(),self._window_state_signature(window),str(game.get("id","")) if isinstance(game,dict) else "")
        if not force and signature==self.refresh_signature:
            return {"unchanged":True,"signature":signature}
        game_ready=isinstance(game,dict)
        window_ready=False
        result={"unchanged":False,"signature":signature,"game_text":game.get("name","未选择") if game_ready else "未选择","window_text":"未选择","window_detail":"PID：-  类名：-  客户区：-  游戏区域：-","capture_text":"采集方式：未检测","sample_text":"样本：有效0  废弃0  session 0  数据0 KB","model_text":"模型：无  需要复习：否","training_ready":False,"flow_text":""}
        if isinstance(window,dict):
            result["window_text"]=window.get("title","未命名窗口")
            try:
                content=self.api.validate_target(window,False)
                client=self.api.client_rect(window["hwnd"])
                dpi=self.api.dpi_for_window(window["hwnd"])
                path=str(window.get("process_path","-"))
                rule=window.get("title_rule",{"mode":"none"})
                result["window_detail"]="PID："+str(window["pid"])+"  TID："+str(window.get("window_thread_id","-"))+"  类名："+window["class"]+"  客户区："+str(client[2])+"×"+str(client[3])+"  游戏区域："+str(content[2])+"×"+str(content[3])+"  DPI："+str(dpi)+"  标题规则："+str(rule.get("mode","none"))+"  路径："+path
                result["capture_text"]=self.api.capture_status(window["hwnd"])
                window_ready=True
            except Exception as error:
                result["window_detail"]="PID："+str(window.get("pid","-"))+"  类名："+str(window.get("class","-"))+"  "+str(error)
                result["capture_text"]="采集方式：等待目标窗口恢复"
        valid=0
        sessions=0
        model_state="不可训练"
        missing=[]
        if isinstance(game,dict):
            gid=str(game["id"])
            try:
                stats=self.store.sample_stats(gid)
                valid=int(stats["valid"])
                sessions=int(stats.get("sessions",0))
                families=dict(stats.get("families",{}))
                result["sample_text"]="样本：有效"+str(valid)+"  废弃"+str(stats["invalid"])+"  session "+str(sessions)+"  数据"+str(round(stats["bytes"]/1024,1))+" KB"
                metadata=self.store.model_metadata(gid)
                needs=bool(next((item.get("needs_review") for item in self.store.games() if item["id"]==gid),False))
                if metadata:
                    created=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(metadata.get("created",0)))
                    validation=metadata.get("validation",{})
                    trainable_metadata=metadata.get("trainable") if isinstance(metadata.get("trainable"),dict) else None
                    trainable_validation=trainable_metadata.get("validation",{}) if trainable_metadata else {}
                    holdout=int(validation.get("holdout",0) or 0)
                    accepted=int(validation.get("accepted",0) or 0)
                    coverage=float(validation.get("coverage",0.0) or 0.0)
                    reject_rate=float(validation.get("reject_rate",1.0-coverage) if validation.get("reject_rate") is not None else 1.0-coverage)
                    overall=float(validation.get("overall_accuracy",0.0) or 0.0)
                    error_upper=float(validation.get("error_upper_95",1.0) or 1.0)
                    accepted_error=validation.get("accepted_error_rate")
                    status=str(validation.get("status","insufficient"))
                    authorized=sorted(str(value) for value in validation.get("authorized_families",[]) if str(value))
                    error_text="接受样本错误率无法计算（验证不足）" if accepted_error is None else "接受样本错误率"+str(round(float(accepted_error)*100,2))+"%"
                    detail="留出"+str(holdout)+" 接受"+str(accepted)+" 覆盖"+str(round(coverage*100,1))+"% 总体正确"+str(round(overall*100,1))+"% 95%上界"+str(round(error_upper*100,2))+"% 拒识"+str(round(reject_rate*100,1))+"%"
                    model_kind="完整模型" if status=="passed" and metadata.get("slot")=="complete" else "基础安全模型" if status=="basic_safe" else "不可训练临时模型"
                    retained_status=str(trainable_validation.get("status",""))
                    retained_authorized=sorted(str(value) for value in trainable_validation.get("authorized_families",[]) if str(value))
                    retained_text="" if trainable_metadata is None or trainable_metadata.get("saved")==metadata.get("saved") else "  已保留可训练模型："+retained_status+"，授权动作："+("、".join(retained_authorized) if retained_authorized else "已授权动作")
                    result["model_text"]=model_kind+"："+str(metadata.get("prototype_count",0))+"个原型  最近复习："+created+"  "+error_text+"  "+detail+"  授权动作："+("、".join(authorized) if authorized else "无")+"  需要复习："+("是" if needs else "否")+retained_text
                    result["training_ready"]=bool(trainable_metadata is not None and retained_status in {"passed","basic_safe"} and int(trainable_validation.get("authorized_prototypes",0) or 0)>0 and not needs)
                    model_state=("可训练（完整授权："+("、".join(retained_authorized) if retained_authorized else "已授权动作")+"）" if retained_status=="passed" else "可训练（仅基础安全动作："+("、".join(retained_authorized) if retained_authorized else "已授权动作")+"）") if result["training_ready"] else "不可训练"
                    session_count=int(validation.get("session_count",sessions) or sessions)
                    if status!="passed":
                        if session_count<VersionedThresholdConfig.required_sessions:
                            missing.append("第二个独立学习 session" if session_count==1 else "独立学习 session "+str(VersionedThresholdConfig.required_sessions-session_count)+" 个")
                        if holdout<VersionedThresholdConfig.review_min_holdout:
                            missing.append("有效留出样本 "+str(VersionedThresholdConfig.review_min_holdout-holdout)+" 个")
                        if accepted<VersionedThresholdConfig.review_min_accepted:
                            missing.append("接受样本 "+str(VersionedThresholdConfig.review_min_accepted-accepted)+" 个")
                        if coverage<VersionedThresholdConfig.minimum_coverage:
                            missing.append("覆盖率还差 "+str(round((VersionedThresholdConfig.minimum_coverage-coverage)*100,1))+" 个百分点")
                        if error_upper>VersionedThresholdConfig.maximum_error_upper_95:
                            missing.append("95%错误率上界需降至 "+str(round(VersionedThresholdConfig.maximum_error_upper_95*100,1))+"%")
                    if not result["training_ready"]:
                        best_basic=max((safe_int(families.get(family,0),0,0) for family in BASIC_SAFE_FAMILIES),default=0)
                        if best_basic<VersionedThresholdConfig.basic_safe_min_positive:
                            left_count=safe_int(families.get("click|left",0),0,0)
                            missing.insert(0,"普通左键样本 "+str(max(0,VersionedThresholdConfig.basic_safe_min_positive-left_count))+" 个，或其他基础安全动作达到"+str(VersionedThresholdConfig.basic_safe_min_positive)+"个高一致样本")
                else:
                    result["model_text"]="模型：无  需要复习："+("是" if needs else "否")
                    if valid<=0:
                        missing.append("有效学习样本")
                    else:
                        missing.append("完成一次复习")
            except Exception as error:
                result["sample_text"]="数据统计失败"
                result["model_text"]=str(error)
                missing.append("修复数据统计错误")
                self.store.log_error("CONTROL_PANEL_STATS_FAILED",error,game_id=gid)
        if not game_ready:
            missing.append("选择或新建游戏")
        if not window_ready:
            missing.append("选择并确认窗口与游戏区域")
        result["training_ready"]=bool(result.get("training_ready") and game_ready and window_ready)
        learning_state="可复习（有效"+str(valid)+"，独立session "+str(sessions)+"）" if valid>0 else "不足"
        extra="；还需要："+"；".join(dict.fromkeys(missing)) if missing else ""
        result["flow_text"]="1. 游戏："+("已完成" if game_ready else "未完成")+"\n2. 窗口："+("已完成" if window_ready else "未完成")+"\n3. 学习数据："+learning_state+"\n4. 模型："+model_state+extra
        return result
    def _apply_refresh_snapshot(self,result):
        if not isinstance(result,dict) or result.get("unchanged"):
            return
        self.refresh_signature=result.get("signature")
        self.game_text.set(result["game_text"])
        self.window_text.set(result["window_text"])
        self.window_detail.set(result["window_detail"])
        self.capture_text.set(result["capture_text"])
        self.sample_text.set(result["sample_text"])
        self.model_text.set(result["model_text"])
        self.flow_text.set(str(result.get("flow_text","")))
        self.training_ready=bool(result.get("training_ready"))
        self._update_control_availability()
    def refresh_all_async(self,force=False):
        game=dict(self.selected_game) if isinstance(self.selected_game,dict) else None
        window=dict(self.selected_window) if isinstance(self.selected_window,dict) else None
        if force:
            self.sample_text.set("样本：正在读取")
            self.model_text.set("模型：正在读取")
        self.run_background("control_panel_refresh",lambda:self._collect_refresh_snapshot(game,window,bool(force)),self._apply_refresh_snapshot)
    def _refresh_all(self):
        self.refresh_all_async(True)
    def refresh_data_stats(self):
        self.refresh_all_async(True)
    def periodic_refresh(self):
        try:
            if not self.mode and not self.closing:
                self.refresh_all_async(False)
        finally:
            if not self.shutdown_started:
                try:
                    self.root.after(1200,self.periodic_refresh)
                except Exception as error:
                    self.store.log_error("PERIODIC_REFRESH_RESCHEDULE_FAILED",error)
    def open_game_dialog(self):
        if self.mode:
            self.show_error("请先停止当前模式")
            return
        working_games=[dict(item) for item in self.store.games()]
        original_selected=self.selected_game["id"] if self.selected_game else None
        working_selected=original_selected
        win=tk.Toplevel(self.root)
        win.title("游戏")
        win.geometry("540x450")
        win.transient(self.root)
        win.grab_set()
        state={"closed":False}
        frame=ttk.Frame(win,padding=16)
        frame.pack(fill="both",expand=True)
        ttk.Label(frame,text="选择、新建、编辑或删除游戏名称",font=("Microsoft YaHei UI",13,"bold")).pack(anchor="w",pady=(0,10))
        ttk.Label(frame,text="所有修改仅保存在本对话框的临时副本中；只有点击总“确认”才一次性写入数据库。",wraplength=500).pack(anchor="w",pady=(0,8))
        list_frame=ttk.Frame(frame)
        list_frame.pack(fill="both",expand=True)
        box=tk.Listbox(list_frame,exportselection=False,font=("Microsoft YaHei UI",11))
        scroll=ttk.Scrollbar(list_frame,orient="vertical",command=box.yview)
        box.configure(yscrollcommand=scroll.set)
        box.pack(side="left",fill="both",expand=True)
        scroll.pack(side="right",fill="y")
        def refresh(target=None):
            nonlocal working_selected
            box.delete(0,"end")
            for game in working_games:
                suffix="  [需要复习]" if game.get("needs_review") else ""
                box.insert("end",game["name"]+suffix)
            wanted=target if target is not None else working_selected
            if wanted is not None:
                for index,game in enumerate(working_games):
                    if game["id"]==wanted:
                        box.selection_set(index)
                        box.see(index)
                        working_selected=wanted
                        return
            working_selected=None
        def current_index():
            selection=box.curselection()
            return selection[0] if selection else None
        def add_game():
            nonlocal working_selected
            name=self.prompt_text("新建游戏","输入游戏名称")
            if name is None:
                return
            if any(item["name"].casefold()==name.casefold() for item in working_games):
                self.show_error("游戏名称已存在")
                return
            game={"id":uuid.uuid4().hex,"name":name,"created":time.time(),"needs_review":False,"last_review":None}
            working_games.append(game)
            working_selected=game["id"]
            refresh(working_selected)
        def edit_game():
            index=current_index()
            if index is None:
                self.show_error("请先选择一个游戏")
                return
            name=self.prompt_text("编辑游戏","修改游戏名称",working_games[index]["name"])
            if name is None:
                return
            if any(position!=index and item["name"].casefold()==name.casefold() for position,item in enumerate(working_games)):
                self.show_error("游戏名称已存在")
                return
            working_games[index]["name"]=name
            refresh(working_games[index]["id"])
        def delete_game():
            nonlocal working_selected
            index=current_index()
            if index is None:
                self.show_error("请先选择一个游戏")
                return
            item=dict(working_games[index])
            if not self.confirm_dialog("标记删除游戏","确认将“"+item["name"]+"”加入待删除列表吗？只有随后点击总“确认”才会删除游戏、样本、模型和备份；点击“取消”不会写数据库。"):
                return
            working_games.pop(index)
            box.selection_clear(0,"end")
            if item["id"]==original_selected or item["id"]==working_selected:
                working_selected=None
            elif working_games:
                working_selected=working_games[min(index,len(working_games)-1)]["id"]
            refresh(working_selected)
        def confirm():
            nonlocal working_selected
            selection=box.curselection()
            if not selection:
                self.show_error("请重新选择一个仍存在的游戏；删除当前游戏后不能提交无效选择")
                return
            chosen=working_games[selection[0]]
            working_selected=chosen["id"]
            result=self.store.replace_games(working_games,working_selected)
            self.selected_game=dict(chosen)
            self._refresh_all()
            deleted=len(result.get("deleted_games",[])) if isinstance(result,dict) else 0
            self.status.set("已提交游戏列表并选择："+chosen["name"]+("；已删除"+str(deleted)+"个游戏及其全部数据" if deleted else ""))
            self.close_dialog(win,state)
        def cancel():
            self.close_dialog(win,state)
        tools=ttk.Frame(frame)
        tools.pack(fill="x",pady=10)
        ttk.Button(tools,text="新建",command=add_game).pack(side="left",padx=(0,6))
        ttk.Button(tools,text="编辑",command=edit_game).pack(side="left",padx=6)
        ttk.Button(tools,text="删除",command=delete_game).pack(side="left",padx=6)
        actions=ttk.Frame(frame)
        actions.pack(fill="x")
        ttk.Button(actions,text="确认",command=confirm).pack(side="right",padx=(6,0))
        ttk.Button(actions,text="取消",command=cancel).pack(side="right")
        box.bind("<Double-Button-1>",lambda event:confirm())
        win.protocol("WM_DELETE_WINDOW",cancel)
        win.bind("<Escape>",lambda event:cancel())
        refresh()
        win.wait_visibility()
        box.focus_set()
    def open_window_dialog(self):
        if self.mode:
            self.show_error("请先停止当前模式")
            return
        win=tk.Toplevel(self.root)
        win.title("选择窗口")
        win.geometry("1200x760")
        win.minsize(1040,680)
        win.transient(self.root)
        win.grab_set()
        state={"closed":False,"background_keys":["window_dialog_enumeration","window_dialog_preview"],"norm":[0.0,0.0,1.0,1.0],"auto":None,"client":None,"target_key":None,"start":None,"rect_id":None,"image":None}
        frame=ttk.Frame(win,padding=16)
        frame.pack(fill="both",expand=True)
        ttk.Label(frame,text="选择雷电模拟器窗口或其他窗口，并在同一界面确认游戏区域",font=("Microsoft YaHei UI",13,"bold")).pack(anchor="w",pady=(0,6))
        ttk.Label(frame,text="默认自动选择最大可见游戏子窗口。也可选择整个客户区或在右侧预览中手动拖框；点击一次总“确认”同时保存窗口身份和区域。",wraplength=1140).pack(anchor="w",pady=(0,10))
        body=ttk.Frame(frame)
        body.pack(fill="both",expand=True)
        body.columnconfigure(0,weight=5)
        body.columnconfigure(1,weight=4)
        body.rowconfigure(0,weight=1)
        left=ttk.Frame(body)
        left.grid(row=0,column=0,sticky="nsew",padx=(0,10))
        right=ttk.LabelFrame(body,text="游戏渲染区域",padding=10)
        right.grid(row=0,column=1,sticky="nsew")
        list_frame=ttk.Frame(left)
        list_frame.pack(fill="both",expand=True)
        box=tk.Listbox(list_frame,exportselection=False,font=("Microsoft YaHei UI",9))
        scroll=ttk.Scrollbar(list_frame,orient="vertical",command=box.yview)
        box.configure(yscrollcommand=scroll.set)
        box.pack(side="left",fill="both",expand=True)
        scroll.pack(side="right",fill="y")
        rule_frame=ttk.LabelFrame(left,text="可选标题规则",padding=8)
        rule_frame.pack(fill="x",pady=(8,0))
        rule_label=tk.StringVar(value="不检查")
        rule_value=tk.StringVar(value="")
        mode_map={"不检查":"none","包含":"contains","前缀":"prefix","精确":"exact"}
        combo=ttk.Combobox(rule_frame,textvariable=rule_label,values=list(mode_map),state="readonly",width=10)
        combo.pack(side="left")
        entry=ttk.Entry(rule_frame,textvariable=rule_value)
        entry.pack(side="left",fill="x",expand=True,padx=(8,0))
        status=tk.StringVar(value="请选择窗口")
        ttk.Label(left,textvariable=status,wraplength=620).pack(anchor="w",fill="x",pady=(8,2))
        preview_status=tk.StringVar(value="选择窗口后自动读取预览")
        ttk.Label(right,textvariable=preview_status,wraplength=620).pack(anchor="w",fill="x",pady=(0,8))
        canvas_w=640
        canvas_h=360
        canvas=tk.Canvas(right,width=canvas_w,height=canvas_h,bg="black",highlightthickness=1,highlightbackground="#777777")
        canvas.pack(fill="both",expand=False)
        placeholder=bytes(PREVIEW_W*PREVIEW_H*3)
        ppm=b"P6\n"+str(PREVIEW_W).encode("ascii")+b" "+str(PREVIEW_H).encode("ascii")+b"\n255\n"+placeholder
        image=tk.PhotoImage(data=base64.b64encode(ppm).decode("ascii"),format="PPM")
        scaled=image.zoom(2,2)
        image_id=canvas.create_image(0,0,image=scaled,anchor="nw")
        state["image"]=(image,scaled)
        region_mode=tk.StringVar(value="auto")
        region_info=tk.StringVar(value="区域：未选择")
        options=ttk.Frame(right)
        options.pack(fill="x",pady=(8,0))
        ttk.Radiobutton(options,text="自动区域",value="auto",variable=region_mode).pack(side="left")
        ttk.Radiobutton(options,text="整个客户区",value="full",variable=region_mode).pack(side="left",padx=8)
        ttk.Radiobutton(options,text="手动调整",value="manual",variable=region_mode).pack(side="left")
        ttk.Label(right,textvariable=region_info,wraplength=620).pack(anchor="w",fill="x",pady=(6,0))
        windows=[]
        widgets={"refresh":None}
        def selected_item():
            selection=box.curselection()
            if not selection or selection[0]>=len(windows):
                return None
            return dict(windows[selection[0]])
        def redraw():
            if state["rect_id"] is not None:
                try:
                    canvas.delete(state["rect_id"])
                except Exception:
                    pass
            norm=list(state.get("norm") or [0.0,0.0,1.0,1.0])
            x,y,w,h=norm
            state["rect_id"]=canvas.create_rectangle(x*canvas_w,y*canvas_h,(x+w)*canvas_w,(y+h)*canvas_h,outline="#00ffff",width=3)
            client=state.get("client")
            if client:
                rect=apply_normalized_rect(client,norm)
                region_info.set("区域："+str(rect[2])+"×"+str(rect[3])+"；归一化："+",".join(str(round(value,4)) for value in norm)+"；模式："+{"auto":"自动区域","full":"整个客户区","manual":"手动调整"}.get(region_mode.get(),"手动调整"))
            else:
                region_info.set("区域：未选择")
        def apply_region_mode(*args):
            if state.get("client") is None:
                return
            mode=region_mode.get()
            if mode=="auto" and isinstance(state.get("auto"),dict):
                state["norm"]=list(state["auto"]["norm"])
            elif mode=="full":
                state["norm"]=[0.0,0.0,1.0,1.0]
            redraw()
        region_mode.trace_add("write",apply_region_mode)
        def load_preview(snapshot):
            temporary=dict(snapshot)
            temporary["content_rect_norm"]=[0.0,0.0,1.0,1.0]
            temporary["content_aspect"]=snapshot["selected_rect"][2]/max(1,snapshot["selected_rect"][3])
            captured=self.api.capture_gray(temporary,False,True,True)
            rgb=preview_rgb_bytes(captured.get("preview_rgb"))
            if rgb is None:
                raise CaptureUnavailable("预览截图尺寸无效")
            return {"key":snapshot["_preview_key"],"rgb":rgb}
        def apply_preview(result):
            if state["closed"] or not win.winfo_exists() or result.get("key")!=state.get("target_key"):
                return
            rgb=result["rgb"]
            ppm_value=b"P6\n"+str(PREVIEW_W).encode("ascii")+b" "+str(PREVIEW_H).encode("ascii")+b"\n255\n"+rgb
            loaded=tk.PhotoImage(data=base64.b64encode(ppm_value).decode("ascii"),format="PPM")
            loaded_scaled=loaded.zoom(2,2)
            canvas.itemconfigure(image_id,image=loaded_scaled)
            state["image"]=(loaded,loaded_scaled)
            preview_status.set("预览读取完成；青色框内是学习、复习、训练和请教使用的唯一区域")
        def preview_failed(error):
            if state["closed"] or not win.winfo_exists():
                return
            preview_status.set("预览告警："+str(error)+"；仍可使用自动区域、整个客户区或手动调整")
        def prepare_selection(event=None):
            item=selected_item()
            if item is None:
                return
            existing=item.get("title_rule") if isinstance(item.get("title_rule"),dict) else None
            if self.selected_window and item.get("hwnd")==self.selected_window.get("hwnd"):
                existing=self.selected_window.get("title_rule")
            if not isinstance(existing,dict):
                existing={"mode":"none","value":""}
            reverse={value:key for key,value in mode_map.items()}
            rule_label.set(reverse.get(str(existing.get("mode","none")),"不检查"))
            rule_value.set(str(existing.get("value","")))
            try:
                identity=self.api.target_identity(item)
                client=self.api.client_rect(identity["hwnd"])
                auto=self.api.auto_content_region(identity)
                key=str(identity.get("hwnd"))+"|"+str(identity.get("pid"))+"|"+str(identity.get("process_created"))
                state["client"]=client
                state["auto"]=auto
                state["target_key"]=key
                state["norm"]=list(auto["norm"])
                region_mode.set("auto")
                status.set("进程路径："+str(identity.get("process_path","读取失败")))
                preview_status.set("正在后台读取预览…")
                redraw()
                snapshot=dict(identity)
                snapshot["selected_rect"]=list(client)
                snapshot["_preview_key"]=key
                self.run_background("window_dialog_preview",lambda snapshot=snapshot:load_preview(snapshot),apply_preview,preview_failed)
            except Exception as error:
                state["client"]=None
                state["auto"]=None
                state["target_key"]=None
                status.set("窗口身份或区域读取失败："+str(error))
                preview_status.set("无法读取预览")
                redraw()
        def load_windows():
            hydrated=[]
            for item in self.api.enum_windows():
                candidate=dict(item)
                try:
                    candidate=self.api.target_identity(candidate)
                except Exception as error:
                    candidate["identity_error"]=str(error)
                    self.store.log_error("WINDOW_IDENTITY_READ_FAILED",error,window_identity={key:candidate.get(key) for key in ("hwnd","pid","class","title")})
                hydrated.append(candidate)
            return hydrated
        def apply_windows(hydrated):
            nonlocal windows
            if state["closed"] or not win.winfo_exists():
                return
            windows=list(hydrated)
            box.delete(0,"end")
            selected_index=None
            scored=[window_descriptor_score(self.window_recommendation,item) for item in windows]
            recommended=None
            if scored and max(scored)>=8 and scored.count(max(scored))==1:
                recommended=scored.index(max(scored))
            for index,item in enumerate(windows):
                prefix=("[推荐] " if index==recommended else "")+("[最小化] " if item.get("minimized") else "")
                path=str(item.get("process_path","路径读取失败"))
                box.insert("end",prefix+str(item.get("title",""))+"  [PID "+str(item.get("pid","-"))+"]  ["+str(item.get("class",""))+"]  "+path)
                if self.selected_window and item.get("hwnd")==self.selected_window.get("hwnd") and item.get("pid")==self.selected_window.get("pid") and item.get("class")==self.selected_window.get("class"):
                    selected_index=index
            if selected_index is None:
                selected_index=recommended
            if selected_index is not None:
                box.selection_set(selected_index)
                box.see(selected_index)
                prepare_selection()
            status.set("已读取"+str(len(windows))+"个可见窗口")
            if widgets["refresh"] is not None:
                widgets["refresh"].configure(state="normal")
        def refresh_error(error):
            if state["closed"] or not win.winfo_exists():
                return
            status.set("窗口读取失败："+str(error))
            if widgets["refresh"] is not None:
                widgets["refresh"].configure(state="normal")
            self.show_error(str(error))
        def refresh():
            if state["closed"]:
                return
            status.set("正在后台读取窗口和进程完整身份…")
            box.delete(0,"end")
            box.insert("end","正在读取…")
            if widgets["refresh"] is not None:
                widgets["refresh"].configure(state="disabled")
            self.run_background("window_dialog_enumeration",load_windows,apply_windows,refresh_error)
        def press(event):
            if state.get("client") is None:
                return
            region_mode.set("manual")
            state["start"]=(max(0,min(canvas_w,event.x)),max(0,min(canvas_h,event.y)))
        def drag(event):
            if state.get("start") is None:
                return
            x0,y0=state["start"]
            x1=max(0,min(canvas_w,event.x))
            y1=max(0,min(canvas_h,event.y))
            left=min(x0,x1)/canvas_w
            top=min(y0,y1)/canvas_h
            width=abs(x1-x0)/canvas_w
            height=abs(y1-y0)/canvas_h
            if width>=0.02 and height>=0.02:
                state["norm"]=[left,top,width,height]
                redraw()
        def release(event):
            drag(event)
            state["start"]=None
        def confirm():
            item=selected_item()
            if item is None:
                self.show_error("请先选择一个窗口")
                return
            try:
                item=self.api.target_identity(item)
                client=self.api.client_rect(item["hwnd"])
                key=str(item.get("hwnd"))+"|"+str(item.get("pid"))+"|"+str(item.get("process_created"))
                if key!=state.get("target_key"):
                    raise RuntimeError("窗口选择已变化，请等待区域信息刷新后再确认")
                rect=apply_normalized_rect(client,state["norm"])
                if rect[2]<FEATURE_W or rect[3]<FEATURE_H:
                    raise RuntimeError("游戏区域过小")
                item["integrity"]=self.api.validate_uipi(item)
                item["selected_rect"]=list(client)
                item["client_size"]=[int(client[2]),int(client[3])]
                item["selected_dpi"]=self.api.dpi_for_window(item["hwnd"])
                title_mode=mode_map.get(rule_label.get(),"none")
                title_value=rule_value.get().strip()
                if title_mode!="none" and not title_value:
                    raise RuntimeError("标题规则不是“不检查”时必须填写匹配文本")
                item["title_rule"]={"mode":title_mode,"value":title_value}
                source_mode=region_mode.get()
                auto=state.get("auto") or {}
                item.update({"content_rect_norm":[round(value,8) for value in state["norm"]],"content_aspect":round(rect[2]/max(1,rect[3]),8),"content_source":auto.get("source","auto") if source_mode=="auto" else "full_client" if source_mode=="full" else "manual","content_child_class":auto.get("child_class","") if source_mode=="auto" else "","window_rule_version":WINDOW_RULE_VERSION})
                item=self.api.target_identity(item)
                self.api.validate_target(item,False)
            except Exception as error:
                self.show_error(str(error))
                return
            previous=self.selected_window
            self.selected_window=item
            if not previous or any(previous.get(key)!=item.get(key) for key in ("hwnd","pid","class","process_created","content_rect_norm")):
                self.api.calibrations.pop(int(item["hwnd"]),None)
            self.window_recommendation=self.store.save_window_descriptor(item)
            self.api.reset_capture_backends(item)
            self.api.reset_frame_history(item["hwnd"])
            self._refresh_all()
            self.status.set("一次确认已保存窗口身份和游戏内容区域："+item["title"]+"；区域模式="+source_mode+"；标题规则="+item["title_rule"]["mode"])
            self.close_dialog(win,state)
        def cancel():
            self.close_dialog(win,state)
        canvas.bind("<Button-1>",press)
        canvas.bind("<B1-Motion>",drag)
        canvas.bind("<ButtonRelease-1>",release)
        tools=ttk.Frame(frame)
        tools.pack(fill="x",pady=(10,0))
        widgets["refresh"]=ttk.Button(tools,text="刷新",command=refresh)
        widgets["refresh"].pack(side="left")
        ttk.Button(tools,text="确认",command=confirm).pack(side="right",padx=(6,0))
        ttk.Button(tools,text="取消",command=cancel).pack(side="right")
        box.bind("<<ListboxSelect>>",prepare_selection)
        box.bind("<Double-Button-1>",lambda event:confirm())
        win.protocol("WM_DELETE_WINDOW",cancel)
        win.bind("<Escape>",lambda event:cancel())
        refresh()
        win.wait_visibility()
        box.focus_set()
    def select_content_region(self,target,parent=None):
        client=self.api.client_rect(int(target["hwnd"]))
        auto=self.api.auto_content_region(target)
        temporary=dict(target)
        temporary["content_rect_norm"]=[0.0,0.0,1.0,1.0]
        temporary["content_aspect"]=client[2]/max(1,client[3])
        preview=bytes(PREVIEW_W*PREVIEW_H*3)
        win=tk.Toplevel(parent or self.root)
        win.title("确认游戏渲染区域")
        win.geometry("760x560")
        win.transient(parent or self.root)
        frame=ttk.Frame(win,padding=14)
        frame.pack(fill="both",expand=True)
        ttk.Label(frame,text="框选真正的游戏渲染区域",font=("Microsoft YaHei UI",13,"bold")).pack(anchor="w")
        preview_status=tk.StringVar(value="学习、预览、坐标归一化、点击校验和截图全部使用此区域；区域外工具栏永远不允许自动点击。正在后台读取预览…")
        ttk.Label(frame,textvariable=preview_status,wraplength=720).pack(anchor="w",pady=(4,8))
        canvas_w=640
        canvas_h=360
        canvas=tk.Canvas(frame,width=canvas_w,height=canvas_h,bg="black",highlightthickness=1,highlightbackground="#777777")
        canvas.pack()
        ppm=b"P6\n"+str(PREVIEW_W).encode("ascii")+b" "+str(PREVIEW_H).encode("ascii")+b"\n255\n"+preview
        image=tk.PhotoImage(data=base64.b64encode(ppm).decode("ascii"),format="PPM")
        scaled=image.zoom(2,2)
        image_id=canvas.create_image(0,0,image=scaled,anchor="nw")
        state={"norm":list(auto["norm"]),"start":None,"rect_id":None,"result":None,"image":(image,scaled),"closed":False,"background_keys":["content_region_preview"]}
        info=tk.StringVar()
        ttk.Label(frame,textvariable=info).pack(anchor="w",pady=(6,0))
        def redraw():
            if state["rect_id"] is not None:
                canvas.delete(state["rect_id"])
            x,y,w,h=state["norm"]
            state["rect_id"]=canvas.create_rectangle(x*canvas_w,y*canvas_h,(x+w)*canvas_w,(y+h)*canvas_h,outline="#00ffff",width=3)
            rect=apply_normalized_rect(client,state["norm"])
            info.set("游戏区域："+str(rect[2])+"×"+str(rect[3])+"  归一化："+",".join(str(round(value,4)) for value in state["norm"]))
        def press(event):
            state["start"]=(max(0,min(canvas_w,event.x)),max(0,min(canvas_h,event.y)))
        def drag(event):
            if state["start"] is None:
                return
            x0,y0=state["start"]
            x1=max(0,min(canvas_w,event.x)); y1=max(0,min(canvas_h,event.y))
            left=min(x0,x1)/canvas_w; top=min(y0,y1)/canvas_h; width=abs(x1-x0)/canvas_w; height=abs(y1-y0)/canvas_h
            if width>=0.02 and height>=0.02:
                state["norm"]=[left,top,width,height]
                redraw()
        def release(event):
            drag(event)
            state["start"]=None
        def set_auto():
            state["norm"]=list(auto["norm"])
            redraw()
        def set_full():
            state["norm"]=[0.0,0.0,1.0,1.0]
            redraw()
        def load_preview():
            captured=self.api.capture_gray(temporary,False,True,True)
            rgb=preview_rgb_bytes(captured.get("preview_rgb"))
            if rgb is None:
                raise CaptureUnavailable("预览截图尺寸无效")
            return rgb
        def apply_preview(rgb):
            if state["closed"] or not win.winfo_exists():
                return
            ppm_value=b"P6\n"+str(PREVIEW_W).encode("ascii")+b" "+str(PREVIEW_H).encode("ascii")+b"\n255\n"+rgb
            loaded=tk.PhotoImage(data=base64.b64encode(ppm_value).decode("ascii"),format="PPM")
            loaded_scaled=loaded.zoom(2,2)
            canvas.itemconfigure(image_id,image=loaded_scaled)
            state["image"]=(loaded,loaded_scaled)
            preview_status.set("学习、预览、坐标归一化、点击校验和截图全部使用此区域；区域外工具栏永远不允许自动点击。预览读取完成。")
        def preview_failed(error):
            if state["closed"] or not win.winfo_exists():
                return
            preview_status.set("学习、预览、坐标归一化、点击校验和截图全部使用此区域；区域外工具栏永远不允许自动点击。预览告警："+str(error))
        def confirm():
            rect=apply_normalized_rect(client,state["norm"])
            if rect[2]<FEATURE_W or rect[3]<FEATURE_H:
                self.show_error("游戏区域过小")
                return
            state["result"]={"content_rect_norm":[round(value,8) for value in state["norm"]],"content_aspect":round(rect[2]/max(1,rect[3]),8),"content_source":"manual" if state["norm"]!=auto["norm"] else auto["source"],"content_child_class":auto.get("child_class",""),"window_rule_version":WINDOW_RULE_VERSION}
            self.close_dialog(win,state)
        def cancel():
            self.close_dialog(win,state)
        canvas.bind("<Button-1>",press)
        canvas.bind("<B1-Motion>",drag)
        canvas.bind("<ButtonRelease-1>",release)
        tools=ttk.Frame(frame)
        tools.pack(fill="x",pady=(10,0))
        ttk.Button(tools,text="自动最大可见子窗口",command=set_auto).pack(side="left")
        ttk.Button(tools,text="整个客户区",command=set_full).pack(side="left",padx=6)
        ttk.Button(tools,text="确认",command=confirm).pack(side="right",padx=(6,0))
        ttk.Button(tools,text="取消",command=cancel).pack(side="right")
        win.protocol("WM_DELETE_WINDOW",cancel)
        win.bind("<Escape>",lambda event:cancel())
        redraw()
        self.run_background("content_region_preview",load_preview,apply_preview,preview_failed)
        win.wait_visibility()
        win.grab_set()
        win.focus_force()
        win.wait_window()
        return state["result"]
    def require_game(self):
        if not self.selected_game:
            raise RuntimeError("请先点击“游戏”按钮选择或新建游戏")
        return self.selected_game
    def require_window(self,foreground=False):
        if not self.selected_window:
            raise RuntimeError("请先点击“选择窗口”按钮选择目标窗口")
        self.api.validate_target_identity(self.selected_window,foreground)
        return self.selected_window
    def ensure_capture_calibration(self,target,purpose):
        target_identity=self.api.target_identity(target)
        target.update(target_identity)
        if self.selected_window is target or self.selected_window and int(self.selected_window.get("hwnd",0))==int(target.get("hwnd",0)):
            self.selected_window.update(target_identity)
        calibration=self.api.calibration_for(target)
        identity_valid=self.api.calibration_identity_matches(target,calibration)
        if not identity_valid:
            cached=self.store.load_capture_calibration(target)
            if cached:
                self.api.calibrations[int(target["hwnd"])]=cached
                calibration=self.api.calibration_for(target)
                self.set_status(str(purpose)+"开始前已载入校准缓存，正在重新验证窗口身份和采集后端")
        duration=0.9 if calibration.get("cache_loaded") or identity_valid else 1.8
        self.set_status(str(purpose)+"开始前正在验收采集后端；黑屏只暂停验收，合法静态画面允许通过")
        def progress(value):
            self.set_progress(max(0.0,min(8.0,float(value)*8.0)))
        while not self.should_stop():
            try:
                result=self.api.calibrate(target,duration,self.stop_event,progress)
                self.store.save_capture_calibration(target,result)
                return result
            except InputStopped:
                raise
            except CaptureUnavailable as error:
                text=str(error)
                if "非黑帧" not in text and "黑帧" not in text:
                    raise
                self.lock_input("检测到黑屏，等待画面恢复")
                self.set_status(str(purpose)+"验收暂停："+text)
                if self.stop_event is not None and self.stop_event.wait(0.2):
                    raise InputStopped("采集验收已停止")
                duration=3.0
        raise InputStopped("采集验收已停止")
    def set_controls(self,running):
        self._update_control_availability()
    def start_worker(self,name,target,needs_window=False):
        if self.mode_state!=MODE_IDLE or self.closing:
            self.show_error("当前已有操作正在运行，请先停止")
            return
        try:
            self.require_game()
            if self.storage_fault and name in {"学习","复习","请教"}:
                raise RuntimeError(self.store.read_only_reason or self.store.writer_error or "样本存储故障，相关模式已锁定")
            if needs_window:
                self.require_window(False)
            stop_event=self.lifecycle.begin(name)
        except Exception as error:
            self.show_error(str(error))
            return
        self.mode=str(name)
        self.mode_state=MODE_STARTING
        self.stop_event=stop_event
        self.pending_mode_result=None
        self.pending_mode_error=None
        self.mode_shutdown_deadline=None
        self.mode_shutdown_forced=[]
        self.mode_stop_started=False
        self.mode_shutdown_polling=False
        self.api.block_input()
        self.set_input_status("已锁定")
        self.set_controls(True)
        self.progress_value.set(0)
        self.status.set(name+"正在初始化，按ESC或点击“停止”可立即中止")
        self.mode_thread=threading.Thread(target=self.worker_entry,args=(name,target),name="UniversalGameAI-"+name,daemon=True)
        self.mode_thread.start()
    def worker_entry(self,name,target):
        result=None
        error=None
        try:
            value=target()
            if isinstance(value,ModeResult):
                result=value
            else:
                stopped=bool(self.stop_event and self.stop_event.is_set())
                requested=self.lifecycle.snapshot()[3]
                status=requested if stopped and requested in {"completed","stopped","failed"} else "completed"
                result=ModeResult(status,str(value if value is not None else name+"已结束"))
        except InputStopped as stopped_error:
            requested=self.lifecycle.snapshot()[3]
            status=requested if requested in {"failed","stopped"} else "stopped"
            result=ModeResult(status,name+("失败" if status=="failed" else "已停止"),{"reason":str(stopped_error)})
        except (TargetUnavailable,CaptureUnavailable) as stopped_error:
            result=ModeResult("stopped",name+"已停止：目标窗口或安全采集条件不可用",{"reason":str(stopped_error)})
        except Exception as worker_error:
            error=traceback.format_exc()
            game_id=str(self.selected_game.get("id","")) if isinstance(self.selected_game,dict) else ""
            window_identity={key:self.selected_window.get(key) for key in ("hwnd","pid","class","process_path","process_created") if isinstance(self.selected_window,dict) and key in self.selected_window}
            self.store.log_error("MODE_WORKER_FAILED",worker_error,mode=name,game_id=game_id,window_identity=window_identity)
            result=ModeResult("failed",name+"失败")
        finally:
            self.api.block_input()
            self.set_input_status("已锁定")
            self.store.close_current_thread()
        self.ui(lambda:self._begin_mode_stopping(result,error),"mode_result")
    def request_mode_stop(self,status="stopped",reason=""):
        if self.mode_state==MODE_IDLE:
            return False
        with self.mode_stop_lock:
            first=not self.mode_stop_started
            self.mode_stop_started=True
            self.lifecycle.request_stop(status,reason)
            self.mode_state=MODE_STOPPING
            event=self.stop_event
            if event is not None:
                event.set()
        self.api.block_input()
        self.api.release_all_buttons()
        review=self.review_process
        if review is not None:
            try:
                review.request_stop()
            except Exception:
                pass
        session=self.active_session
        if session is not None:
            try:
                session.request_stop()
            except Exception:
                pass
        def apply_ui():
            self._destroy_ask_window()
            self.set_input_status("已锁定："+(str(reason) if reason else "停止请求"))
            self.status.set("正在停止，已阻止新的鼠标按下并释放全部鼠标键"+("；"+str(reason) if reason else ""))
        self.ui(apply_ui)
        return first
    def request_stop(self):
        self.request_mode_stop("stopped","用户请求停止")
    def _keyboard_escape(self,event=None):
        self.request_mode_stop("stopped","ESC停止")
    def wait_escape_release(self):
        while self.api.key_down(0x1B) and self.stop_event and not self.stop_event.is_set():
            time.sleep(0.04)
    def should_stop(self):
        if self.stop_event is None or self.stop_event.is_set():
            self.api.block_input()
            return True
        if self.api.key_down(0x1B):
            self.request_mode_stop("stopped","ESC停止")
            return True
        return False
    def inside(self,x,y,rect):
        rx,ry,rw,rh=rect
        return rx<=x<rx+rw and ry<=y<ry+rh
    def normalize_point(self,x,y,rect):
        rx,ry,rw,rh=rect
        return [max(0.0,min(1.0,(x-rx)/max(1,rw-1))),max(0.0,min(1.0,(y-ry)/max(1,rh-1)))]
    def point_to_screen(self,point,rect):
        x,y,width,height=rect
        return x+round(max(0.0,min(1.0,float(point[0])))*max(1,width-1)),y+round(max(0.0,min(1.0,float(point[1])))*max(1,height-1))
    def sample_context(self,last_signature,last_time,last_changed,motion_valid=True,session_id="",capture_method="unknown",repeat_policy="one_shot",temporal=None):
        calibration=self.api.calibration_for(self.selected_window.get("hwnd") if self.selected_window else 0)
        target=self.selected_window or {}
        content=self.api.validate_target(target,False) if target else (0,0,1,1)
        result={"previous_action":last_signature or "","seconds_since_previous":round(max(0.0,min(60.0,time.monotonic()-last_time)) if last_time else 60.0,3),"previous_action_changed_frame":bool(last_changed),"motion_channel_valid":bool(motion_valid),"session_id":str(session_id or "unspecified"),"capture_method":str(capture_method or "unknown"),"repeat_policy":repeat_policy if repeat_policy in REPEAT_POLICIES else "one_shot","duplicate_threshold":float(calibration.get("duplicate",3.0)),"calibration":dict(calibration),"process_path":os.path.normcase(str(target.get("process_path",""))),"window_class":str(target.get("class","")),"content_rect_norm":[round(safe_float(value,0.0),6) for value in target.get("content_rect_norm",[0,0,1,1])[:4]],"content_aspect":content[2]/max(1,content[3]),"window_rule_version":WINDOW_RULE_VERSION,"capture_backend_version":CAPTURE_BACKEND_VERSION}
        if isinstance(temporal,dict):
            result.update(temporal)
        return result
    def build_temporal_context(self,frame_buffer,frame,recent_actions,state_since,cursor_point=None):
        frames=[item for item in frame_buffer.snapshot(1.5) if item.get("capture_valid") and item.get("backend_validated") and item["time"]<=float(frame["time"])+0.001 and item.get("method")==frame.get("method")]
        frames=frames[-5:]
        deltas=[round(visual_distance(first["f"],second["f"]),6) for first,second in zip(frames,frames[1:])]
        if cursor_point is None:
            try:
                x,y=self.api.cursor()
                rect=tuple(frame.get("rect",()))
                cursor_point=self.normalize_point(x,y,rect) if len(rect)==4 and self.inside(x,y,rect) else None
            except Exception:
                cursor_point=None
        rect=tuple(frame.get("rect",()))
        actions=list(recent_actions)[-4:]
        while len(actions)<2:
            actions.insert(0,"<START>")
        return {"recent_frame_count":len(frames),"recent_frame_deltas":deltas,"recent_actions":actions,"state_duration":round(max(0.0,min(60.0,time.monotonic()-float(state_since))),3),"cursor":cursor_point,"window_size":[int(rect[2]),int(rect[3])] if len(rect)==4 else None,"dpi":int(frame.get("dpi",0)),"capture_method":str(frame.get("method","unknown"))}
    def start_learning(self):
        self.start_worker("学习",self.learning_controller.run,True)
    def learning_worker(self):
        return self.learning_controller.run()
    def _learning_worker_impl(self):
        return self.learning_controller._run_impl()
    def _run_review_process(self):
        game=self.require_game()
        self.store.sample_write_barrier()
        samples,stats=self.store.load_samples(game["id"])
        rejections=self.store.load_rejections(game["id"],500)
        worker=ReviewProcessWorker({"game":game,"samples":samples,"stats":stats,"rejections":rejections,"profile":self.store.load_game_profile(game["id"]),"cache_capacity":50000})
        self.review_process=worker
        packet=None
        try:
            while True:
                if self.should_stop():
                    worker.request_stop()
                message=worker.receive(0.08)
                if message is not None:
                    kind,payload=message
                    if kind=="progress":
                        self.set_progress(payload)
                    elif kind=="status":
                        self.set_status(payload)
                    elif kind in {"result","error"}:
                        packet=(kind,payload)
                        break
                if not worker.alive():
                    message=worker.receive(0.0)
                    if message is not None:
                        packet=message
                    break
            if packet is None:
                if self.stop_event is not None and self.stop_event.is_set():
                    raise InputStopped("复习子进程已停止")
                raise RuntimeError("复习子进程异常退出且未返回结果")
            kind,payload=packet
            for gid,model,complete in payload.get("models",[]):
                self.store.save_model(gid,model,complete)
            if kind=="error":
                raise RuntimeError(payload.get("traceback","复习子进程失败"))
            return ModeResult(payload.get("status","failed"),payload.get("summary","复习结束"),payload.get("details",{}))
        finally:
            worker.request_stop()
            worker.close(0.2)
            if self.review_process is worker:
                self.review_process=None
    def _prototype_medoid(self,members):
        if len(members)==1:
            return members[0]
        pool=members if len(members)<=32 else [members[round(index*(len(members)-1)/31)] for index in range(32)]
        comparisons=members if len(members)<=80 else [members[round(index*(len(members)-1)/79)] for index in range(80)]
        for item in pool+comparisons:
            if not isinstance(item.get("coarse"),(bytes,bytearray)) or len(item.get("coarse"))!=COARSE_LEN:
                item["coarse"]=coarse_feature(item["f"])
        coarse_scores=[]
        for candidate in pool:
            total=sum(coarse_distance(candidate["coarse"],other["coarse"]) for other in comparisons)
            coarse_scores.append((total,candidate))
        candidates=[item for _,item in sorted(coarse_scores,key=lambda pair:pair[0])[:min(12,len(coarse_scores))]]
        best=candidates[0]
        best_total=float("inf")
        operations=0
        cache=self.review_distance_cache
        for candidate in candidates:
            total=0.0
            candidate_key=compact_checksum_key(candidate)
            for other in comparisons:
                operations+=1
                if operations%32==0 and self.should_stop():
                    raise InputStopped("复习已停止")
                other_key=compact_checksum_key(other)
                key=(candidate_key,other_key) if candidate_key<=other_key else (other_key,candidate_key)
                distance=cache.get(key)
                if distance is None:
                    distance=feature_distance(candidate["f"],other["f"])
                    cache[key]=distance
                total+=distance
            if total<best_total:
                best_total=total
                best=candidate
        return best
    def _action_medoid(self,members):
        if len(members)==1:
            return members[0]
        candidates=members if len(members)<=36 else [members[round(index*(len(members)-1)/35)] for index in range(36)]
        comparisons=members if len(members)<=96 else [members[round(index*(len(members)-1)/95)] for index in range(96)]
        best=candidates[0]
        best_total=float("inf")
        operations=0
        for candidate in candidates:
            total=0.0
            for other in comparisons:
                operations+=1
                if operations%32==0 and self.should_stop():
                    raise InputStopped("复习已停止")
                total+=action_geometry_distance(candidate["a"],other["a"])*float(other.get("weight",1.0))
            if total<best_total:
                best_total=total
                best=candidate
        return best
    def _cluster_action_samples(self,samples):
        families=defaultdict(list)
        for index,sample in enumerate(samples):
            if index%64==0 and self.should_stop():
                raise InputStopped("复习已停止")
            family=action_family_key(sample["a"])
            if family:
                families[family].append(sample)
        clusters=[]
        operations=0
        for family,items in sorted(families.items()):
            if self.should_stop():
                raise InputStopped("复习已停止")
            local=[]
            for item in sorted(items,key=lambda value:str(value.get("checksum",""))):
                if self.should_stop():
                    raise InputStopped("复习已停止")
                if not local:
                    local.append({"family":family,"members":[item],"medoid":item})
                    continue
                distances=[]
                for cluster in local:
                    operations+=1
                    if operations%32==0 and self.should_stop():
                        raise InputStopped("复习已停止")
                    distances.append(action_geometry_distance(item["a"],cluster["medoid"]["a"]))
                best_index=min(range(len(distances)),key=lambda index:distances[index])
                if distances[best_index]<=action_cluster_limit(item["a"]):
                    cluster=local[best_index]
                    cluster["members"].append(item)
                    if len(cluster["members"])<=48 or len(cluster["members"])%8==0:
                        cluster["medoid"]=self._action_medoid(cluster["members"])
                else:
                    local.append({"family":family,"members":[item],"medoid":item})
            changed=True
            while changed and len(local)>1:
                changed=False
                for first in range(len(local)):
                    if changed:
                        break
                    for second in range(first+1,len(local)):
                        operations+=1
                        if operations%16==0 and self.should_stop():
                            raise InputStopped("复习已停止")
                        limit=min(action_cluster_limit(local[first]["medoid"]["a"]),action_cluster_limit(local[second]["medoid"]["a"]))*0.82
                        if action_geometry_distance(local[first]["medoid"]["a"],local[second]["medoid"]["a"])<=limit:
                            local[first]["members"].extend(local[second]["members"])
                            local[first]["medoid"]=self._action_medoid(local[first]["members"])
                            local.pop(second)
                            changed=True
                            break
            for index,cluster in enumerate(local):
                if self.should_stop():
                    raise InputStopped("复习已停止")
                action=normalize_action(cluster["medoid"]["a"])
                canonical=action_signature(action)
                token=hashlib.sha256(canonical_bytes({"family":family,"action":action,"index":index})).hexdigest()[:20]
                cluster_id="action|"+family+"|"+token
                intervals=[]
                learned_policies=[]
                for member_index,member in enumerate(cluster["members"]):
                    if member_index%32==0 and self.should_stop():
                        raise InputStopped("复习已停止")
                    context=member.get("context",{}) if isinstance(member.get("context"),dict) else {}
                    if context.get("previous_action")==canonical and not context.get("previous_action_changed_frame",True) and finite_number(context.get("seconds_since_previous")) and float(context.get("seconds_since_previous"))<=1.5:
                        intervals.append(max(0.05,float(context.get("seconds_since_previous"))))
                    policy=str(context.get("repeat_policy","one_shot"))
                    if policy in REPEAT_POLICIES:
                        learned_policies.append(policy)
                kind=action["kind"]
                if learned_policies and Counter(learned_policies).most_common(1)[0][0]!="one_shot":
                    repeat_policy=Counter(learned_policies).most_common(1)[0][0]
                elif kind=="no_op":
                    repeat_policy="repeatable"
                elif kind in {"scroll_v","scroll_h","move","hover"}:
                    repeat_policy="rate_limited"
                elif len(intervals)>=2:
                    repeat_policy="rate_limited"
                else:
                    repeat_policy="one_shot"
                max_rate=max(0.25,min(12.0,1.0/max(0.08,quantile(intervals,0.25)))) if intervals else ({"scroll_v":6.0,"scroll_h":5.0,"move":8.0,"hover":2.0,"no_op":4.0}.get(kind,3.0))
                cluster.update({"id":cluster_id,"a":action,"canonical_action_signature":canonical,"repeat_policy":repeat_policy,"max_rate":max_rate})
                for member in cluster["members"]:
                    member["_action_cluster"]=cluster_id
                    member["_cluster_action"]=action
                    member["_action_support"]=len(cluster["members"])
                    member["_canonical_action_signature"]=canonical
                clusters.append(cluster)
        return clusters
    def _cluster_action_group(self,cluster_id,action,action_support,items,progress_callback,repeat_policy="one_shot",max_rate=3.0):
        clusters=[]
        max_clusters=max(1,min(28,int(math.sqrt(len(items)))+3))
        calibrated=[]
        for item in items:
            context=item.get("context",{}) if isinstance(item.get("context"),dict) else {}
            calibration=context.get("calibration",{}) if isinstance(context.get("calibration"),dict) else {}
            if finite_number(calibration.get("visual_cluster")):
                calibrated.append(float(calibration["visual_cluster"]))
        visual_threshold=statistics.median(calibrated) if calibrated else 420.0
        for index,item in enumerate(items):
            if self.should_stop():
                raise InputStopped("复习已停止")
            if not clusters:
                clusters.append([item])
            else:
                medoids=[cluster[0] for cluster in clusters]
                distances=[feature_distance(item["f"],medoid["f"]) for medoid in medoids]
                best_index=min(range(len(distances)),key=lambda position:distances[position])
                if distances[best_index]>visual_threshold and len(clusters)<max_clusters:
                    clusters.append([item])
                else:
                    clusters[best_index].append(item)
            if index%15==0:
                progress_callback(index,len(items),len(clusters))
        result=[]
        canonical=action_signature(action)
        for cluster_index,cluster in enumerate(clusters):
            if self.should_stop():
                raise InputStopped("复习已停止")
            medoid=self._prototype_medoid(cluster)
            distances=[]
            temporal_distances=[]
            temporal=temporal_from_context(medoid.get("context",{}))
            for item_index,item in enumerate(cluster):
                if item_index%32==0 and self.should_stop():
                    raise InputStopped("复习已停止")
                distances.append(feature_distance(item["f"],medoid["f"]))
                temporal_distances.append(temporal_distance(item.get("context",{}),temporal))
            mean=statistics.fmean(distances) if distances else 0.0
            std=statistics.pstdev(distances) if len(distances)>1 else 0.0
            limit95=quantile(distances,0.95)
            limit99=quantile(distances,0.99)
            threshold_value=max(1.0,min(1800.0,max(limit99,mean+2.58*std)+max(8.0,std*0.35)))
            temporal_threshold=max(0.12,min(0.42,quantile(temporal_distances,0.95)+0.05))
            previous=Counter(str(item.get("context",{}).get("previous_action","")) for item in cluster)
            previous.pop("",None)
            prev=previous.most_common(1)[0][0] if previous else ""
            methods=sorted({str(item.get("capture_method") or item.get("context",{}).get("capture_method") or "unknown") for item in cluster})
            result.append({"id":uuid.uuid4().hex,"cluster_id":cluster_id,"canonical_action_signature":canonical,"f":feature_bytes(medoid["f"]),"coarse":bytes(medoid.get("coarse")) if isinstance(medoid.get("coarse"),(bytes,bytearray)) and len(medoid.get("coarse"))==COARSE_LEN else coarse_feature(medoid["f"]),"a":normalize_action(action),"support":len(cluster),"action_support":int(action_support),"mean_distance":round(mean,6),"std_distance":round(std,6),"limit95":round(limit95,6),"limit99":round(limit99,6),"intra_threshold":round(threshold_value,6),"threshold":round(threshold_value,6),"temporal":temporal,"temporal_threshold":round(temporal_threshold,6),"capture_methods":methods,"previous_action":prev,"repeat_policy":repeat_policy if repeat_policy in REPEAT_POLICIES else "one_shot","max_rate":max(0.25,min(12.0,float(max_rate))),"ambiguous":False,"created_from_sample_checksum":medoid.get("checksum","")})
        return result
    def rank_action_candidates(self,feature,prototypes,last_action_signature="",full_limit=8,temporal_context=None,query_coarse=None):
        if not feature_valid(feature):
            return []
        query_temporal=temporal_from_context(temporal_context or {})
        if not isinstance(query_coarse,(bytes,bytearray)) or len(query_coarse)!=COARSE_LEN:
            query_coarse=coarse_feature(feature)
        backend=str(query_temporal.get("capture_method","unknown"))
        digest=hashlib.blake2b(feature_bytes(feature),digest_size=8).digest()
        cache_key=(id(prototypes),len(prototypes),digest,backend,str(last_action_signature),coarse_bucket_key(query_coarse))
        cached=self.candidate_cache.get(cache_key)
        if cached is not None:
            return cached
        runtime_model=getattr(self,"active_model_runtime",None)
        runtime_index=runtime_model.get("runtime_index",{}) if isinstance(runtime_model,dict) and runtime_model.get("prototypes") is prototypes else {}
        backend_indices=runtime_index.get("backend",{}).get(backend) if isinstance(runtime_index,dict) else None
        source_indices=list(backend_indices) if backend_indices is not None else list(range(len(prototypes)))
        bucket_indices=set(runtime_index.get("bucket",{}).get((backend,coarse_bucket_key(query_coarse)),[])) if isinstance(runtime_index,dict) else set()
        eligible=[]
        for position,index in enumerate(source_indices):
            proto=prototypes[index]
            if position%64==0 and self.stop_event is not None and self.should_stop():
                return []
            if "authorized" in proto and not proto.get("authorized"):
                continue
            methods=proto.get("capture_methods",frozenset())
            if not isinstance(methods,frozenset):
                methods=frozenset(str(value) for value in methods)
                proto["capture_methods"]=methods
            if methods and backend not in methods:
                continue
            if index in bucket_indices:
                proto["bucket_priority"]=0
            else:
                proto["bucket_priority"]=1
            eligible.append(proto)
        coarse_rank=[]
        best_per_cluster={}
        for proto in eligible:
            pc=proto.get("coarse")
            if not isinstance(pc,(bytes,bytearray)) or len(pc)!=COARSE_LEN:
                pc=coarse_feature(proto["f"]); proto["coarse"]=pc
            distance=coarse_distance(query_coarse,pc)
            coarse_rank.append((int(proto.get("bucket_priority",1)),distance,proto))
            cluster_id=str(proto.get("cluster_id",proto.get("action_signature","")))
            if cluster_id and (cluster_id not in best_per_cluster or distance<best_per_cluster[cluster_id][0]):
                best_per_cluster[cluster_id]=(distance,proto)
        coarse_rank.sort(key=lambda item:(item[0],item[1]))
        exact_limit=max(12,min(VersionedThresholdConfig.candidate_full_limit,int(full_limit) if int(full_limit)>0 else VersionedThresholdConfig.candidate_full_limit))
        selected=[]
        selected_ids=set()
        for priority,distance,proto in coarse_rank:
            if proto["id"] not in selected_ids:
                selected.append(proto); selected_ids.add(proto["id"])
            if len(selected)>=exact_limit:
                break
        if len(selected)<exact_limit:
            for distance,proto in sorted(best_per_cluster.values(),key=lambda item:item[0]):
                if proto["id"] not in selected_ids:
                    selected.append(proto); selected_ids.add(proto["id"])
                if len(selected)>=exact_limit:
                    break
        grouped=defaultdict(list)
        for proto in selected:
            raw=runtime_feature_distance(feature,proto)
            expected=str(proto.get("previous_action",""))
            penalty=min(120.0,raw*0.08+18.0) if expected and last_action_signature and expected!=last_action_signature else 0.0
            proto_temporal=proto.get("temporal_cached") or temporal_from_context(proto.get("temporal",{}))
            proto["temporal_cached"]=proto_temporal
            tdistance=temporal_distance(query_temporal,proto_temporal)
            temporal_penalty=tdistance*max(40.0,float(proto.get("threshold",100.0))*0.35)
            cluster_id=str(proto.get("cluster_id",proto.get("action_signature","")))
            sequence_model=runtime_model.get("sequence_model",{}) if isinstance(runtime_model,dict) else {}
            sequence_penalty=TaskAgentPolicy({}).sequence_penalty(query_temporal.get("recent_actions",[last_action_signature]),cluster_id,sequence_model)
            if cluster_id:
                grouped[cluster_id].append((raw+penalty+temporal_penalty+sequence_penalty,raw,tdistance,proto))
        result=[]
        for cluster_id,items in grouped.items():
            items.sort(key=lambda item:item[0])
            best_score,best_distance,best_temporal,best_proto=items[0]
            vote_score=best_score if len(items)==1 else 0.88*best_score+0.12*items[1][0]
            action=best_proto.get("a") if normalize_action(best_proto.get("a")) else normalize_action(best_proto["a"])
            result.append({"cluster_id":cluster_id,"canonical_action_signature":str(best_proto.get("canonical_action_signature") or action_signature(action)),"score":vote_score,"best_score":best_score,"distance":best_distance,"temporal_distance":best_temporal,"proto":best_proto,"a":action,"support":max(int(item[3].get("action_support",item[3].get("support",0))) for item in items),"prototype_votes":len(items)})
        result.sort(key=lambda item:item["score"])
        self.candidate_cache[cache_key]=result
        return result
    def evaluate_action_candidates(self,ranked):
        if not ranked:
            return {"accepted":False,"confidence":0.0,"reason":"没有候选或停止请求"}
        best=ranked[0]
        second=ranked[1] if len(ranked)>1 else None
        proto=best["proto"]
        strict_multiplier,min_support,margin_ratio=tuple(proto.get("strictness") or self.action_strictness(best["a"]))
        threshold=float(proto["threshold"])/strict_multiplier
        second_score=second["score"] if second else float("inf")
        margin=second_score-best["score"]
        required_gap=max(float(proto.get("minimum_second_candidate_gap",16.0)),best["score"]*0.12)
        margin_ok=math.isinf(second_score) or best["score"]<second_score*margin_ratio and margin>required_gap
        support=int(best.get("support",0))
        rejected_distance=proto.get("nearest_rejected_distance")
        rejection_ok=rejected_distance is None or best["distance"]<float(rejected_distance)*0.65
        temporal_ok=float(best.get("temporal_distance",1.0))<=float(proto.get("temporal_threshold",0.0))
        query_backend=str((proto.get("temporal_cached") or temporal_from_context(proto.get("temporal",{}))).get("capture_method","unknown"))
        ambiguous=bool(proto.get("ambiguous",False))
        authorized=bool(proto.get("authorized",True))
        accepted=authorized and not ambiguous and best["distance"]<threshold and margin_ok and support>=min_support and rejection_ok and temporal_ok
        confidence=max(0.0,min(1.0,1.0-best["distance"]/max(1.0,threshold)))*(1.0-min(1.0,float(best.get("temporal_distance",1.0))))
        if not authorized:
            reason="动作簇未通过独立session验证，拒绝执行"
        elif ambiguous:
            reason="视觉与短时序状态仍对应不同动作，必须请教"
        elif not temporal_ok:
            reason="最近3至5帧、最近动作、状态时长或鼠标位置不匹配"
        else:
            reason="未达到动作阈值、差距或支持数要求"
        return {"accepted":accepted,"best":best,"second":second,"threshold":threshold,"margin":margin,"required_gap":required_gap,"support":support,"min_support":min_support,"confidence":confidence,"margin_ok":margin_ok,"rejection_ok":rejection_ok,"temporal_ok":temporal_ok,"ambiguous":ambiguous,"authorized":authorized,"reason":reason,"nearest_rejected_distance":rejected_distance,"query_backend":query_backend}
    def open_task_dialog(self):
        try:
            game=self.require_game()
            if self.mode_state!=MODE_IDLE:
                raise RuntimeError("请先停止当前模式")
        except Exception as error:
            self.show_error(str(error))
            return
        profile=self.store.load_game_profile(game["id"])
        win=tk.Toplevel(self.root)
        state={"closed":False}
        win.title("任务目标与安全边界")
        win.geometry("760x700")
        win.minsize(700,620)
        frame=ttk.Frame(win,padding=16)
        frame.pack(fill="both",expand=True)
        ttk.Label(frame,text="该系统是按游戏配置的任务型模仿智能体，不保证适用于所有游戏。未进入白名单的动作永远不会自动执行。",wraplength=710).pack(anchor="w",fill="x",pady=(0,10))
        ttk.Label(frame,text="游戏目标或奖励说明").pack(anchor="w")
        goal=tk.Text(frame,height=4,wrap="word")
        goal.pack(fill="x",pady=(4,10))
        goal.insert("1.0",str(profile.get("goal","")))
        allowed_frame=ttk.LabelFrame(frame,text="自动动作白名单",padding=10)
        allowed_frame.pack(fill="x")
        families=[("等待","no_op"),("左键单击","click|left"),("左键双击","double_click|left"),("左键长按","long_press|left"),("左键拖动","drag|left"),("右键单击","click|right"),("中键单击","click|middle"),("移动","move"),("悬停","hover"),("向上滚轮","scroll_v|1"),("向下滚轮","scroll_v|-1"),("横向正滚轮","scroll_h|1"),("横向负滚轮","scroll_h|-1")]
        variables={family:tk.BooleanVar(value=family in set(profile.get("allowed_families",[]))) for _,family in families}
        for index,(label,family) in enumerate(families):
            ttk.Checkbutton(allowed_frame,text=label,variable=variables[family]).grid(row=index//3,column=index%3,sticky="w",padx=6,pady=3)
        safety=ttk.LabelFrame(frame,text="失败停机与回滚",padding=10)
        safety.pack(fill="x",pady=(10,0))
        ttk.Label(safety,text="连续失败或动作后无变化达到").grid(row=0,column=0,sticky="w")
        max_failures=tk.IntVar(value=safe_int(profile.get("max_consecutive_failures",3),3,1,20))
        ttk.Spinbox(safety,from_=1,to=20,textvariable=max_failures,width=6).grid(row=0,column=1,sticky="w")
        ttk.Label(safety,text="次后自动停机").grid(row=0,column=2,sticky="w")
        exploration=tk.BooleanVar(value=bool(profile.get("exploration_enabled",False)))
        ttk.Checkbutton(safety,text="不确定时允许安全探索（仅等待，不产生鼠标输入）",variable=exploration).grid(row=1,column=0,columnspan=3,sticky="w",pady=(6,0))
        restart=normalize_action(profile.get("restart_action"))
        restart_enabled=tk.BooleanVar(value=bool(restart))
        ttk.Checkbutton(safety,text="失败状态后执行一次左键单击重新开始",variable=restart_enabled).grid(row=2,column=0,columnspan=3,sticky="w",pady=(6,0))
        restart_x=tk.StringVar(value=str(round((restart or {"path":[[0.5,0.5]]})["path"][-1][0],4)))
        restart_y=tk.StringVar(value=str(round((restart or {"path":[[0.5,0.5]]})["path"][-1][1],4)))
        ttk.Label(safety,text="归一化X").grid(row=3,column=0,sticky="e",pady=(4,0))
        ttk.Entry(safety,textvariable=restart_x,width=10).grid(row=3,column=1,sticky="w",pady=(4,0))
        ttk.Label(safety,text="Y").grid(row=3,column=1,sticky="e",pady=(4,0))
        ttk.Entry(safety,textvariable=restart_y,width=10).grid(row=3,column=2,sticky="w",pady=(4,0))
        state_frame=ttk.LabelFrame(frame,text="成功、失败状态",padding=10)
        state_frame.pack(fill="both",expand=True,pady=(10,0))
        success_states=set(str(value) for value in profile.get("success_states",[]))
        failure_states=set(str(value) for value in profile.get("failure_states",[]))
        state_text=tk.StringVar()
        feedback=tk.StringVar(value="选择目标窗口后，可把当前内容区域画面记录为成功或失败状态")
        def refresh_state_text():
            state_text.set("成功状态："+str(len(success_states))+"个    失败状态："+str(len(failure_states))+"个")
        def record_state(kind):
            try:
                target=self.require_window(False)
                packet=self.api.capture(target,False)
                value=visual_perceptual_hash(packet["f"])
                if kind=="success":
                    success_states.add(value)
                    failure_states.discard(value)
                    feedback.set("已记录成功状态："+value)
                else:
                    failure_states.add(value)
                    success_states.discard(value)
                    feedback.set("已记录失败状态："+value)
                refresh_state_text()
            except Exception as error:
                feedback.set("记录失败："+str(error))
        ttk.Label(state_frame,textvariable=state_text).pack(anchor="w")
        button_row=ttk.Frame(state_frame)
        button_row.pack(fill="x",pady=(6,0))
        ttk.Button(button_row,text="记录当前画面为成功",command=lambda:record_state("success")).pack(side="left",padx=(0,6))
        ttk.Button(button_row,text="记录当前画面为失败",command=lambda:record_state("failure")).pack(side="left",padx=(0,6))
        ttk.Button(button_row,text="清空成功状态",command=lambda:(success_states.clear(),refresh_state_text(),feedback.set("已清空成功状态"))).pack(side="left",padx=(0,6))
        ttk.Button(button_row,text="清空失败状态",command=lambda:(failure_states.clear(),refresh_state_text(),feedback.set("已清空失败状态"))).pack(side="left")
        ttk.Label(state_frame,textvariable=feedback,wraplength=690).pack(anchor="w",fill="x",pady=(8,0))
        refresh_state_text()
        def save():
            try:
                allowed=sorted(family for family,variable in variables.items() if variable.get())
                if not allowed:
                    raise RuntimeError("至少选择一个安全动作；建议保留“等待”")
                restart_action=None
                if restart_enabled.get():
                    x=safe_float(restart_x.get(),0.5,0.0,1.0)
                    y=safe_float(restart_y.get(),0.5,0.0,1.0)
                    restart_action=normalize_action({"kind":"click","button":"left","path":[[x,y]],"duration":0.08})
                    if action_family_key(restart_action) not in allowed:
                        raise RuntimeError("启用重新开始动作时，必须把“左键单击”加入白名单")
                value=dict(profile)
                value.update({"goal":goal.get("1.0","end").strip(),"allowed_families":allowed,"max_consecutive_failures":safe_int(max_failures.get(),3,1,20),"exploration_enabled":bool(exploration.get()),"restart_action":restart_action,"success_states":sorted(success_states),"failure_states":sorted(failure_states)})
                self.store.save_game_profile(game["id"],value)
                self._refresh_all()
                self.close_dialog(win,state)
                self.show_info("任务与安全","配置已保存。安全配置或状态定义改变后，必须重新复习才能训练。")
            except Exception as error:
                feedback.set("无法保存："+str(error))
        actions=ttk.Frame(frame)
        actions.pack(fill="x",pady=(12,0))
        ttk.Button(actions,text="取消",command=lambda:self.close_dialog(win,state)).pack(side="right")
        ttk.Button(actions,text="确认",command=save).pack(side="right",padx=(0,8))
        win.transient(self.root)
        win.protocol("WM_DELETE_WINDOW",lambda:self.close_dialog(win,state))
        win.bind("<Escape>",lambda event:self.close_dialog(win,state))
        win.wait_visibility()
        win.grab_set()
        win.focus_force()
    def validate_model_binding(self,model,target):
        if not isinstance(model,dict):
            raise RuntimeError("模型不存在或格式无效")
        binding=model.get("model_binding")
        if not isinstance(binding,dict):
            raise RuntimeError("模型缺少不可变窗口绑定快照，请重新复习")
        current=self.api.target_identity(target)
        target.update(current)
        rect=self.api.validate_target(target,False)
        errors=[]
        path=os.path.normcase(str(current.get("process_path","")))
        stored_paths={os.path.normcase(str(value)) for value in binding.get("process_paths",[])}
        if path not in stored_paths:
            errors.append("可执行文件路径改变")
        if str(current.get("class","")) not in {str(value) for value in binding.get("window_classes",[])}:
            errors.append("窗口类改变")
        norm=[round(safe_float(value,0.0),6) for value in current.get("content_rect_norm",[])[:4]]
        norms=[[round(safe_float(value,0.0),6) for value in item[:4]] for item in binding.get("content_rect_norms",[]) if isinstance(item,(list,tuple)) and len(item)==4]
        if not norms or not any(max(abs(norm[index]-item[index]) for index in range(4))<=0.0005 for item in norms):
            errors.append("内容区域定义改变")
        aspect=rect[2]/max(1,rect[3])
        low=safe_float(binding.get("content_aspect_min",0.0),0.0)
        high=safe_float(binding.get("content_aspect_max",0.0),0.0)
        tolerance=VersionedThresholdConfig.content_aspect_tolerance
        if low<=0 or high<=0 or aspect<low*(1.0-tolerance) or aspect>high*(1.0+tolerance):
            errors.append("内容区域宽高比改变")
        dpi=safe_int(current.get("dpi",current.get("selected_dpi",0)),0)
        if dpi<safe_int(binding.get("dpi_min",0),0) or dpi>safe_int(binding.get("dpi_max",0),0):
            errors.append("DPI超出训练范围")
        if binding.get("window_rule_version")!=WINDOW_RULE_VERSION or binding.get("capture_backend_version")!=CAPTURE_BACKEND_VERSION:
            errors.append("窗口规则或采集后端版本改变")
        profile=self.store.load_game_profile(self.require_game()["id"])
        if str(model.get("safety_profile_checksum",""))!=profile_checksum(profile):
            errors.append("任务目标或安全白名单改变")
        if errors:
            raise RuntimeError("模型与当前窗口/任务绑定不一致："+"、".join(errors)+"；请重新学习或复习")
        return True
    def start_review(self):
        try:
            self.require_game()
            self.store.light_checkpoint()
        except Exception as error:
            self.show_error(str(error))
            return
        self.start_worker("复习",self.review_controller.run,False)
    def _limit_prototypes(self,prototypes,limit):
        limit=int(limit)
        if len(prototypes)<=limit:
            return list(prototypes)
        groups=defaultdict(list)
        for proto in prototypes:
            groups[str(proto.get("cluster_id",""))].append(proto)
        if len(groups)>limit:
            raise RuntimeError("动作簇数量"+str(len(groups))+"超过原型上限"+str(limit)+"，拒绝生成模型")
        def danger(item):
            action=normalize_action(item.get("a")) or {"kind":"no_op"}
            return 1 if action["kind"] in {"double_click","long_press","drag"} or action.get("button") in {"right","middle"} else 0
        chosen=[]
        remaining=[]
        for items in groups.values():
            ordered=sorted(items,key=lambda item:(danger(item),int(item.get("support",0)),int(item.get("action_support",0))),reverse=True)
            chosen.append(ordered[0])
            remaining.extend(ordered[1:])
        remaining.sort(key=lambda item:(danger(item),int(item.get("support",0)),int(item.get("action_support",0))),reverse=True)
        chosen.extend(remaining[:limit-len(chosen)])
        if len(chosen)>limit:
            raise RuntimeError("原型限制执行失败")
        return chosen
    def _split_review_samples(self,valid):
        return self.review_controller.split(valid)
    def _review_worker_impl(self):
        return self.review_controller._run_impl()
    def review_worker(self):
        return self.review_controller.run()
    def action_text(self,action):
        item=normalize_action(action) or {"kind":"no_op","duration":0.3}
        kind=item["kind"]
        names={"left":"左键","right":"右键","middle":"中键"}
        if kind=="no_op":
            return "不操作，等待"+str(item.get("duration",0.3))+"秒"
        if kind in {"scroll_v","scroll_h"}:
            direction="向上" if item["delta"]>0 else "向下"
            if kind=="scroll_h":
                direction="向右" if item["delta"]>0 else "向左"
            return ("水平滚轮" if kind=="scroll_h" else "垂直滚轮")+direction
        point=item["path"][-1]
        position="("+str(int(round(point[0]*100)))+"%, "+str(int(round(point[1]*100)))+"%)"
        if kind=="move":
            return "无按键移动到"+position
        if kind=="hover":
            return "悬停于"+position
        label={"click":"单击","double_click":"双击","long_press":"长按","drag":"拖动"}.get(kind,kind)
        return names.get(item.get("button"),"左键")+label+" "+position
    def action_cooldown(self,action):
        return action_runtime_metadata(action)["cooldown"]
    def action_strictness(self,action):
        return action_runtime_metadata(action)["strictness"]
    def execute_action(self,target,action,expected_frame=None,mouse_interrupt=None,keyboard_monitor=None,keyboard_interrupt=None):
        item=normalize_action(action)
        if not item:
            raise RuntimeError("模型包含无效动作")
        expected_rect=tuple(expected_frame.get("rect",())) if isinstance(expected_frame,dict) else ()
        expected_dpi=int(expected_frame.get("dpi",0)) if isinstance(expected_frame,dict) and finite_number(expected_frame.get("dpi",0)) else 0
        needs_input=item.get("kind")!="no_op"
        def stop_check():
            if mouse_interrupt is not None and mouse_interrupt.is_set():
                self.api.block_input()
                raise InputStopped("检测到人工鼠标干扰")
            if keyboard_interrupt is not None and keyboard_interrupt.is_set():
                self.api.block_input()
                raise InputStopped("检测到键盘输入")
            if keyboard_monitor is not None and not keyboard_monitor.all_released():
                self.api.block_input()
                raise InputStopped("检测到键盘输入")
            if self.should_stop() or needs_input and not self.api.input_allowed():
                self.api.block_input()
                raise InputStopped("已停止或输入权限已锁定，拒绝剩余动作")
        def geometry(point=None):
            stop_check()
            rect=self.api.validate_target(target,True)
            dpi=self.api.dpi_for_window(int(target["hwnd"]))
            if len(expected_rect)==4 and (max(abs(int(rect[index])-int(expected_rect[index])) for index in range(4))>2 or expected_dpi and abs(dpi-expected_dpi)>1):
                raise TargetUnavailable("窗口客户区几何或DPI已变化，放弃当前动作并重新识别")
            self.api.validate_uipi(target)
            if point is not None:
                x,y=self.point_to_screen(point,rect)
                self.api.validate_action_point(target,x,y,expected_rect,expected_dpi)
            return rect
        def sleep_checked(duration):
            deadline=time.monotonic()+max(0.0,float(duration))
            while time.monotonic()<deadline:
                stop_check()
                time.sleep(min(0.008,max(0.001,deadline-time.monotonic())))
        kind=item["kind"]
        if kind=="no_op":
            deadline=time.monotonic()+item.get("duration",0.35)
            while time.monotonic()<deadline:
                geometry()
                sleep_checked(min(0.02,deadline-time.monotonic()))
            return
        path=item.get("path") or [[0.5,0.5]]*16
        current_point=path[0]
        def move_to(point):
            nonlocal current_point
            stop_check()
            rect=geometry()
            x,y=self.point_to_screen(point,rect)
            self.api.validate_action_point(target,x,y,expected_rect,expected_dpi)
            self.api.move_cursor(x,y)
            self.api.validate_action_point(target,x,y,expected_rect,expected_dpi)
            current_point=point
        move_to(path[0])
        if kind=="move":
            for point in path[1:]:
                move_to(point)
                sleep_checked(max(0.004,item["duration"]/max(1,len(path)-1)))
            return
        if kind=="hover":
            deadline=time.monotonic()+item["duration"]
            while time.monotonic()<deadline:
                geometry(current_point)
                sleep_checked(min(0.02,deadline-time.monotonic()))
            return
        if kind in {"scroll_v","scroll_h"}:
            geometry(current_point)
            stop_check()
            self.api.wheel(item["delta"],kind=="scroll_h")
            geometry(current_point)
            return
        button=item["button"]
        if kind=="double_click":
            for iteration in range(2):
                stop_check()
                geometry(current_point)
                self.api.button(button,True)
                try:
                    sleep_checked(0.045)
                finally:
                    self.api.button(button,False)
                if iteration==0:
                    stop_check()
                    sleep_checked(0.09)
                    stop_check()
            return
        clip=None
        pressed=False
        try:
            if kind=="drag":
                clip=self.api.clip_to_client(geometry(current_point))
            stop_check()
            geometry(current_point)
            self.api.button(button,True)
            pressed=True
            if kind=="drag":
                step_time=item["duration"]/max(1,len(path)-1)
                for point in path[1:]:
                    move_to(point)
                    deadline=time.monotonic()+step_time
                    while time.monotonic()<deadline:
                        geometry(current_point)
                        sleep_checked(min(0.012,deadline-time.monotonic()))
            else:
                hold=item["duration"] if kind=="long_press" else min(0.13,item["duration"])
                deadline=time.monotonic()+hold
                while time.monotonic()<deadline:
                    geometry(current_point)
                    sleep_checked(min(0.01,deadline-time.monotonic()))
        finally:
            if pressed:
                try:
                    self.api.button(button,False)
                except Exception:
                    self.api.release_all_buttons()
            if clip is not None:
                self.api.restore_clip(clip)
    def start_training(self):
        try:
            game=self.require_game()
            target=self.require_window(False)
            model=self.store.load_trainable_model(game["id"])
            if not model or not model.get("prototypes"):
                raise RuntimeError("没有已授权动作的可训练模型，请先完成学习和复习；普通左键单击、移动、悬停、等待可在单次高重复一致学习后获得基础安全授权")
            if str(model.get("validation",{}).get("status","")) not in {"passed","basic_safe"}:
                raise RuntimeError("模型没有通过完整验收，也没有获得基础安全动作授权")
            current=next((item for item in self.store.games() if item["id"]==game["id"]),{})
            if current.get("needs_review"):
                raise RuntimeError("模型需要复习：请先点击“复习”完成离线优化")
            self.validate_model_binding(model,target)
        except Exception as error:
            self.show_error(str(error))
            return
        self.start_worker("训练",self.training_controller.run,True)
    def training_worker(self):
        return self.training_controller.run()
    def _training_worker_impl(self):
        return self.training_controller._run_impl()
    def basic_actions(self):
        result=[]
        for y in (0.18,0.35,0.5,0.68,0.84):
            for x in (0.16,0.32,0.5,0.68,0.84):
                result.append(normalize_action({"kind":"click","button":"left","path":[[x,y]],"duration":0.08}))
        result.extend([normalize_action({"kind":"double_click","button":"left","path":[[0.5,0.5]],"duration":0.16}),normalize_action({"kind":"drag","button":"left","path":[[0.25,0.5],[0.75,0.5]],"duration":0.45}),normalize_action({"kind":"drag","button":"left","path":[[0.5,0.75],[0.5,0.25]],"duration":0.45}),normalize_action({"kind":"no_op","duration":0.4}),normalize_action({"kind":"scroll_v","delta":120,"path":[[0.5,0.5]],"duration":0.08}),normalize_action({"kind":"scroll_v","delta":-120,"path":[[0.5,0.5]],"duration":0.08})])
        return result
    def start_ask(self):
        self.start_worker("请教",self.teaching_controller.run,True)
    def _create_ask_window(self,prepared):
        return self.teaching_controller.create_window(prepared)
    def close_ask(self,show_summary=True,wait_buffer=True,reason="completed"):
        if self.mode!="请教" and self.ask_window is None:
            return
        status="completed" if str(reason)=="completed" else "stopped"
        text="用户结束请教" if status=="completed" else "请教已停止"
        self.request_mode_stop(status,text)
    def open_data_dialog(self):
        if self.mode:
            self.show_error("请先停止当前模式")
            return
        try:
            game=self.require_game()
        except Exception as error:
            self.show_error(str(error))
            return
        win=tk.Toplevel(self.root)
        state={"closed":False,"background_keys":["data_dialog_refresh"]}
        win.title("数据清理")
        win.geometry("560x300")
        win.transient(self.root)
        win.grab_set()
        frame=ttk.Frame(win,padding=18)
        frame.pack(fill="both",expand=True)
        text=tk.StringVar()
        ttk.Label(frame,text="当前游戏数据维护",font=("Microsoft YaHei UI",13,"bold")).pack(anchor="w",pady=(0,10))
        ttk.Label(frame,textvariable=text,wraplength=510).pack(anchor="w",fill="x")
        def refresh():
            text.set("正在后台读取样本统计和模型状态…")
            def load():
                stats=self.store.sample_stats(game["id"])
                model=self.store.load_model(game["id"])
                return "游戏："+game["name"]+"\n有效样本："+str(stats["valid"])+"\n异常行："+str(stats["invalid"])+"\n数据大小："+str(round(stats["bytes"]/1024,1))+" KB\n模型原型："+str(len(model.get("prototypes",[])) if model else 0)
            def apply(value):
                if not state["closed"] and win.winfo_exists():
                    text.set(value)
            def failed(error):
                if not state["closed"] and win.winfo_exists():
                    text.set("数据读取失败："+str(error))
            self.run_background("data_dialog_refresh",load,apply,failed)
        def compact():
            result=self.store.compact_samples(game["id"])
            message="数据整理完成：按动作种类、按钮、规范动作与视觉多样性保留"+str(result["kept"])+"，移除"+str(result["removed"])
            self.status.set(message)
            self.show_info("数据压缩完成",message)
            refresh()
            self._refresh_all()
        def restore():
            self.store.restore_model_backup(game["id"])
            message="已从数据库中的完整校验备份恢复模型"
            self.status.set(message)
            self.show_info("模型恢复完成",message)
            refresh()
            self._refresh_all()
        def backup():
            path=self.store.create_recovery_backup("manual")
            self.show_info("恢复备份已创建","数据库、WAL与SHM恢复备份已保存到："+str(path))
        def clear():
            if not self.confirm_dialog("清空数据","确认清空当前游戏的全部样本、模型和备份吗？此操作不可撤销。"):
                return
            self.store.clear_game_data(game["id"])
            message="已清空当前游戏的样本、模型、备份和拒绝记录"
            self.status.set(message)
            self.close_dialog(win,state)
            self.show_info("数据清空完成",message)
            self._refresh_all()
        buttons=ttk.Frame(frame)
        buttons.pack(side="bottom",fill="x",pady=(14,0))
        ttk.Button(buttons,text="压缩重复样本",command=compact).pack(side="left",padx=(0,6))
        ttk.Button(buttons,text="恢复模型备份",command=restore).pack(side="left",padx=6)
        ttk.Button(buttons,text="创建恢复备份",command=backup).pack(side="left",padx=6)
        ttk.Button(buttons,text="清空全部数据",command=clear).pack(side="left",padx=6)
        ttk.Button(buttons,text="关闭",command=lambda:self.close_dialog(win,state)).pack(side="right")
        win.protocol("WM_DELETE_WINDOW",lambda:self.close_dialog(win,state))
        win.bind("<Escape>",lambda event:self.close_dialog(win,state))
        refresh()
    def close(self):
        if self.closing:
            return
        self.closing=True
        with self.background_lock:
            for key in list(self.background_generations):
                self.background_generations[key]+=1
        self.shutdown_deadline=time.monotonic()+8.0
        self.status.set("正在安全关闭：锁定输入并停止模式与采集")
        self.set_input_status("关闭过程中已锁定")
        if self.mode_state!=MODE_IDLE:
            self.request_mode_stop("stopped","程序关闭")
            self.mode_state=MODE_STOPPING
            if self.stop_event is not None:
                self.stop_event.set()
            if self.active_session is not None:
                self.active_session.request_stop()
        self._destroy_ask_window()
        self.api.block_input()
        self.api.release_all_buttons()
        if self.result_modal is not None:
            try:
                self.result_modal.grab_release()
            except Exception:
                pass
            try:
                self.result_modal.destroy()
            except Exception:
                pass
            self.result_modal=None
            self.result_modal_widget=None
        for button in self.controls:
            try:
                button.configure(state="disabled")
            except Exception:
                pass
        if self.stop_button:
            try:
                self.stop_button.configure(state="disabled")
            except Exception:
                pass
        self.root.after(0,self._poll_shutdown)
    def _poll_shutdown(self):
        self.api.block_input()
        self.api.release_all_buttons()
        deadline_reached=bool(self.shutdown_deadline is not None and time.monotonic()>=self.shutdown_deadline)
        pending=[]
        if self.mode_state!=MODE_IDLE:
            self.request_mode_stop("stopped","程序关闭")
            if self.stop_event is not None:
                self.stop_event.set()
            if self.review_process is not None:
                self.review_process.request_stop()
                if deadline_reached and self.review_process.alive():
                    self.review_process.terminate(0.2)
                if self.review_process.alive():
                    pending.append("OfflineReviewProcess")
            self._destroy_ask_window()
            session_done=True
            if self.active_session is not None:
                self.active_session.request_stop()
                session_done=self.active_session.close(0.0)
                if not session_done:
                    pending.extend(self.active_session.pending_names())
            thread_alive=bool(self.mode_thread and self.mode_thread.is_alive())
            if thread_alive:
                pending.append("模式线程")
            capture_pending=self.api.stop_capture_processes(0.0,deadline_reached)
            pending.extend("CaptureProcess:"+name for name in capture_pending)
            if deadline_reached and (thread_alive or pending or not session_done):
                self._forced_exit("程序关闭超过8秒，执行最终退出策略")
                return
            if pending or not session_done:
                self.status.set("正在安全关闭：等待"+"、".join(sorted(set(pending))))
                self.root.after(50,self._poll_shutdown)
                return
            self.mode_thread=None
            self.active_session=None
            self.review_process=None
            self.ask_buffer=None
            self.ask_producer=None
            self.ask_answer_queue=None
            self.ask_session_id=None
            self.ask_counts=None
            self.stop_event=None
            self.mode=None
            self.mode_state=MODE_IDLE
            self.lifecycle.finish()
            self.pending_mode_result=None
            self.pending_mode_error=None
            self.mode_shutdown_deadline=None
        capture_pending=self.api.stop_capture_processes(0.0,deadline_reached)
        if capture_pending:
            if deadline_reached:
                self._forced_exit("采集子进程未在关闭期限内退出")
                return
            self.status.set("正在安全关闭：等待采集子进程退出："+"、".join(capture_pending))
            self.root.after(50,self._poll_shutdown)
            return
        with self.background_lock:
            background=[thread for thread in self.background_threads if thread.is_alive()]
        for thread in background:
            try:
                thread.join(0.01)
            except Exception:
                pass
        with self.background_lock:
            background=[thread for thread in self.background_threads if thread.is_alive()]
        if background:
            if deadline_reached:
                self._forced_exit("后台线程未在关闭期限内退出："+",".join(thread.name for thread in background))
                return
            self.status.set("正在安全关闭：等待后台线程退出："+"、".join(thread.name for thread in background))
            self.root.after(50,self._poll_shutdown)
            return
        self.status.set("正在安全关闭：刷新待写样本并关闭SQLite")
        try:
            store_closed=self.store.close(0.0)
        except Exception as error:
            if deadline_reached:
                self._forced_exit("SQLite关闭失败："+str(error))
                return
            self.status.set("SQLite关闭失败，输入仍保持锁定："+str(error))
            self.root.after(200,self._poll_shutdown)
            return
        if not store_closed:
            if deadline_reached:
                self._forced_exit("样本写入线程未在关闭期限内退出")
                return
            self.status.set("正在安全关闭：等待样本写入线程退出")
            self.root.after(100,self._poll_shutdown)
            return
        self.status.set("正在安全关闭：释放WGC、GDI和系统资源")
        try:
            if not self.api.close():
                if deadline_reached:
                    self._forced_exit("采集资源未在关闭期限内释放")
                    return
                self.status.set("正在安全关闭：等待采集资源退出")
                self.root.after(100,self._poll_shutdown)
                return
        except Exception as error:
            if deadline_reached:
                self._forced_exit("采集资源关闭失败："+str(error))
                return
            self.status.set("采集资源关闭失败："+str(error))
            self.root.after(200,self._poll_shutdown)
            return
        self.shutdown_started=True
        try:
            self.root.destroy()
        except Exception:
            pass
def enable_dpi_awareness():
    if os.name!="nt":
        return
    user32=ctypes.WinDLL("user32",use_last_error=True)
    try:
        user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass
def install_global_hooks(app_holder):
    def sys_hook(exc_type,exc_value,exc_traceback):
        text="".join(traceback.format_exception(exc_type,exc_value,exc_traceback))
        app=app_holder.get("app")
        if app:
            app.show_error(text)
        else:
            try:
                sys.stderr.write(text)
            except Exception:
                pass
    def thread_hook(args):
        sys_hook(args.exc_type,args.exc_value,args.exc_traceback)
    sys.excepthook=sys_hook
    if hasattr(threading,"excepthook"):
        threading.excepthook=thread_hook
def startup_error(root,text):
    root.withdraw()
    win=tk.Toplevel(root)
    state={"closed":False}
    win.title("报错信息")
    win.geometry("700x390")
    frame=ttk.Frame(win,padding=14)
    frame.pack(fill="both",expand=True)
    widget=tk.Text(frame,wrap="word",font=("Microsoft YaHei UI",10))
    widget.pack(fill="both",expand=True)
    widget.insert("1.0",text)
    widget.configure(state="disabled")
    def close():
        if state["closed"]:
            return
        state["closed"]=True
        try:
            win.grab_release()
        except Exception:
            pass
        try:
            root.destroy()
        except Exception:
            pass
    ttk.Button(frame,text="确认",command=close).pack(pady=(10,0))
    win.protocol("WM_DELETE_WINDOW",close)
def run_self_test(path=None):
    source_path=Path(path or __file__).resolve()
    raw=source_path.read_bytes()
    text=raw.decode("utf-8")
    failures=[]
    checks={}
    def check(name,condition,detail=""):
        value=bool(condition)
        checks[str(name)]=value
        if not value:
            failures.append(str(name)+(":"+str(detail) if detail else ""))
    check("源文件无空行",not any(not line.strip() for line in text.splitlines()))
    try:
        tokens=list(tokenize.tokenize(io.BytesIO(raw).readline))
        check("源文件无COMMENT",not any(token.type==tokenize.COMMENT for token in tokens))
    except Exception as error:
        check("源文件可分词",False,error)
    try:
        compile(text,str(source_path),"exec")
        ast.parse(text,str(source_path))
        check("源文件可编译",True)
    except Exception as error:
        check("源文件可编译",False,error)
    points=([0.0,0.0],[1.0,1.0],[0.5,0.5],[0.137,0.829])
    check("请教坐标行为",all((lambda restored,point:restored is not None and max(abs(restored[index]-point[index]) for index in range(2))<1e-9)(PreviewCoordinateMapper.to_normalized(*PreviewCoordinateMapper.to_canvas(point)),point) for point in points))
    check("请教边框拒绝",PreviewCoordinateMapper.to_normalized(ASK_PREVIEW_X-1,ASK_PREVIEW_Y) is None and PreviewCoordinateMapper.to_normalized(ASK_PREVIEW_X,ASK_PREVIEW_Y-1) is None)
    actions=[{"kind":"click","button":"left","path":[[0.25,0.75]],"duration":0.08},{"kind":"double_click","button":"left","path":[[0.5,0.5]],"duration":0.16},{"kind":"long_press","button":"right","path":[[0.4,0.6]],"duration":0.8},{"kind":"drag","button":"left","path":[[0.1,0.2],[0.9,0.8]],"duration":0.5},{"kind":"scroll_v","delta":120,"path":[[0.5,0.5]],"duration":0.08},{"kind":"no_op","duration":0.3}]
    check("动作规范化行为",all(normalize_action(action) is not None and action_signature(action) for action in actions))
    converter=LearningInputEventConverter()
    converted=converter.convert({"x":20,"y":30,"time":1.0,"type":"move"},(10,20,100,100))
    merged=ClickMerger().merge({"time":1.0,"button":"left","point":[0.2,0.3]},{"time":1.2,"button":"left","point":[0.2,0.3]},0.32)
    check("学习控制器实际行为",converted.get("inside") and converted.get("point") and merged.get("kind")=="double_click" and NegativeSampleSampler().due(0.0,1.0,0.5))
    gate=TrainingFrameGate()
    confirmer=TrainingCandidateConfirmer()
    authorizer=TrainingActionAuthorizer()
    check("训练控制器实际行为",gate.usable({"usable_for_training":True,"black_frame":False,"capture_frozen":False,"method":"wgc"},"wgc") and confirmer.confirmed(3,3) and authorizer.authorized({"authorized":True,"ambiguous":False}) and not authorizer.authorized({"authorized":True,"ambiguous":True}))
    validator=ReviewValidator()
    ordinary={"total":VersionedThresholdConfig.ordinary_min_positive,"independent_sessions":VersionedThresholdConfig.ordinary_min_sessions,"errors":0,"false_positive":0,"coverage":1.0,"negative_total":0}
    dangerous={"total":VersionedThresholdConfig.dangerous_min_positive,"independent_sessions":VersionedThresholdConfig.dangerous_min_sessions,"errors":0,"false_positive":0,"coverage":1.0,"negative_total":VersionedThresholdConfig.dangerous_min_negative}
    check("危险动作独立session授权",validator.authorize(ordinary,False) and validator.authorize(dangerous,True) and not validator.authorize({**dangerous,"independent_sessions":VersionedThresholdConfig.dangerous_min_sessions-1},True))
    for stage in (MODE_STARTING,MODE_RUNNING,MODE_STOPPING):
        lifecycle=ModeLifecycle()
        event=lifecycle.begin("自检")
        if stage==MODE_RUNNING:
            lifecycle.mark_running()
        if stage==MODE_STOPPING:
            lifecycle.request_stop("stopped","预置")
        lifecycle.request_stop("stopped","ESC")
        lifecycle.request_stop("completed","后来完成")
        check("ESC可中止且完成不可覆盖"+stage,event.is_set() and lifecycle.snapshot()[0]==MODE_STOPPING and lifecycle.snapshot()[3]=="stopped")
    priority=ModeLifecycle()
    priority.begin("自检")
    priority.request_stop("failed","失败")
    priority.request_stop("stopped","后来停止")
    check("停止状态优先级",priority.snapshot()[3]=="failed")
    class Stubborn:
        def __init__(self):
            self.running=True
            self.forced=False
        def stop(self,timeout=0.0):
            return False
        def alive(self):
            return self.running
        def force(self):
            self.forced=True
            self.running=False
    stubborn=Stubborn()
    barrier=ResourceShutdownBarrier("阻塞采集",0.01)
    barrier.add("CaptureProcess",stubborn.stop,stubborn.alive,stubborn.force)
    barrier.request_stop()
    barrier.deadline=time.monotonic()-1
    check("采集阻塞超时强制终止",barrier.poll() and stubborn.forced and not stubborn.alive())
    check("仅识别本程序注入标记",own_injected_event(1,INPUT_EXTRA_INFO,3) and not own_injected_event(1,INPUT_EXTRA_INFO+1,3) and not own_injected_event(0,INPUT_EXTRA_INFO,3))
    marker_bridge=object.__new__(WinBridge)
    marker_bridge.input_lock=threading.RLock()
    marker_bridge.input_blocked=False
    marker_bridge.input_stop_event=None
    marker_bridge.held=set()
    class MarkerUser32:
        def __init__(self):
            self.extra=None
        def SendInput(self,count,pointer,size):
            self.extra=int(ctypes.cast(pointer,ctypes.POINTER(INPUT)).contents.mi.dwExtraInfo)
            return 1
    marker_bridge.user32=MarkerUser32()
    marker_bridge._send(1)
    check("SendInput写入专属标记",marker_bridge.user32.extra==INPUT_EXTRA_INFO)
    stop=threading.Event()
    isolation=StrictInputIsolation(stop)
    before=isolation.can_automate()
    isolation.signal("keyboard",time.monotonic())
    check("人工输入后自动化锁定",before and stop.is_set() and not isolation.can_automate())
    fake_bridge=object.__new__(WinBridge)
    fake_bridge.input_lock=threading.RLock()
    fake_bridge.input_blocked=False
    fake_bridge.input_stop_event=stop
    fake_bridge.held=set()
    class FakeUser32:
        def __init__(self):
            self.sent=0
        def SendInput(self,*args):
            self.sent+=1
            return 1
    fake_bridge.user32=FakeUser32()
    try:
        fake_bridge._send(1,require_allowed=True)
        blocked=False
    except InputStopped:
        blocked=True
    check("锁定后无新鼠标按下",blocked and fake_bridge.user32.sent==0)
    release_bridge=object.__new__(WinBridge)
    release_bridge.input_lock=threading.RLock()
    release_bridge.input_blocked=True
    release_bridge.input_stop_event=None
    release_bridge.held={"left","middle","right"}
    class ReleaseUser32:
        def __init__(self):
            self.calls=0
        def SendInput(self,count,pointer,size):
            self.calls+=1
            return 1
    release_bridge.user32=ReleaseUser32()
    release_bridge.release_all_buttons()
    check("异常退出释放三键",not release_bridge.held and release_bridge.user32.calls>=3)
    keyboard=KeyboardMonitor(None)
    keyboard.pressed_non_escape.update({65,66})
    keyboard.pressed_non_escape.discard(65)
    one_still_pressed=not keyboard.all_released()
    keyboard.pressed_non_escape.discard(66)
    check("键盘多键集合状态",one_still_pressed and keyboard.all_released())
    lazy=object.__new__(WinBridge)
    lazy.wgc_lock=threading.RLock()
    lazy.wgc=None
    lazy.wgc_error="尚未初始化"
    original_wgc=globals()["WindowsGraphicsCapture"]
    class BrokenWGC:
        def __init__(self,bridge):
            raise RuntimeError("forced")
    globals()["WindowsGraphicsCapture"]=BrokenWGC
    try:
        try:
            lazy.get_wgc()
            lazy_failed=False
        except CaptureUnavailable:
            lazy_failed=True
    finally:
        globals()["WindowsGraphicsCapture"]=original_wgc
    lazy.other_backend=lambda:"ok"
    check("WGC失败不破坏其他后端",lazy_failed and lazy.wgc is None and "不可用" in lazy.wgc_status() and lazy.other_backend()=="ok")
    review_api=ReviewProcessApi()
    check("复习路径SendInput恒零",not hasattr(review_api,"SendInput") and not hasattr(review_api,"_send"))
    fake=object.__new__(WinBridge)
    state={"pid":101,"thread":7,"class":"GameWnd","path":"c:\\game.exe","created":123,"integrity":8192,"dpi":96,"rect":(10,20,800,600),"title":"Game"}
    fake.valid=lambda hwnd:True
    fake.window_thread_pid=lambda hwnd:(state["thread"],state["pid"])
    fake.class_name=lambda hwnd:state["class"]
    fake.process_identity_for_pid=lambda pid:{"path":state["path"],"created":state["created"],"integrity":state["integrity"]}
    fake.foreground_hwnd=lambda:1
    fake.window_title=lambda hwnd:state["title"]
    fake.client_rect=lambda hwnd:state["rect"]
    fake.dpi_for_window=lambda hwnd:state["dpi"]
    class IdentityUser32:
        def IsIconic(self,hwnd):
            return False
    fake.user32=IdentityUser32()
    expected={"hwnd":1,"pid":101,"window_thread_id":7,"class":"GameWnd","process_path":"c:\\game.exe","process_created":123,"integrity":8192,"client_size":[800,600],"selected_dpi":96,"title_rule":{"mode":"none","value":""},"content_rect_norm":[0.0,0.0,0.8,1.0],"content_aspect":640/600}
    base_ok=fake.validate_target(expected,True)==(10,20,640,600)
    state["title"]="Game | FPS 60 | Server A"
    title_ok=fake.validate_target(expected,True)==(10,20,640,600)
    state["rect"]=(50,60,800,600)
    moved_ok=fake.validate_target(expected,True)==(50,60,640,600)
    state["dpi"]=120
    try:
        fake.validate_target(expected,True)
        dpi_rejected=False
    except TargetUnavailable:
        dpi_rejected=True
    state["dpi"]=96
    state["pid"]=102
    try:
        fake.validate_target(expected,True)
        pid_rejected=False
    except TargetUnavailable:
        pid_rejected=True
    state["pid"]=101
    state["created"]=124
    try:
        fake.validate_target(expected,True)
        restart_rejected=False
    except TargetUnavailable:
        restart_rejected=True
    state["created"]=123
    state["path"]="c:\\other.exe"
    try:
        fake.validate_target(expected,True)
        path_rejected=False
    except TargetUnavailable:
        path_rejected=True
    state["path"]="c:\\game.exe"
    state["rect"]=(50,60,900,600)
    try:
        fake.validate_target(expected,True)
        ratio_rejected=False
    except TargetUnavailable:
        ratio_rejected=True
    check("标题变化不中断且身份内容变化拒绝",base_ok and title_ok and moved_ok and dpi_rejected and pid_rejected and restart_rejected and path_rejected and ratio_rejected)
    content=apply_normalized_rect((0,0,1000,600),(0.0,0.0,0.8,1.0))
    check("工具栏排除与移动归一化",content==(0,0,800,600) and not (content[0]<=900<content[0]+content[2]))
    profile={"goal":"test","allowed_families":["no_op","click|left"],"max_consecutive_failures":2,"exploration_enabled":False,"restart_action":None,"success_states":[],"failure_states":[],"success_reward":1.0,"failure_reward":-1.0,"step_penalty":-0.01,"updated":1.0}
    binding={"process_paths":["c:\\game.exe"],"window_classes":["GameWnd"],"content_rect_norms":[[0.0,0.0,0.8,1.0]],"content_aspect_min":640/600,"content_aspect_max":640/600,"dpi_min":96,"dpi_max":96,"capture_methods":["wgc"],"window_rule_version":WINDOW_RULE_VERSION,"capture_backend_version":CAPTURE_BACKEND_VERSION}
    class BindingApi:
        def __init__(self):
            self.path="c:\\game.exe"
        def target_identity(self,target):
            return {**target,"process_path":self.path,"class":"GameWnd","content_rect_norm":[0.0,0.0,0.8,1.0],"dpi":96,"selected_dpi":96}
        def validate_target(self,target,foreground):
            return (0,0,640,600)
    binding_api=BindingApi()
    fake_app=object.__new__(App)
    fake_app.api=binding_api
    fake_app.store=type("BindingStore",(),{"load_game_profile":lambda self,gid:dict(profile)})()
    fake_app.selected_game={"id":"g"}
    fake_app.require_game=lambda:{"id":"g"}
    binding_model={"model_binding":binding,"safety_profile_checksum":profile_checksum(profile)}
    binding_ok=App.validate_model_binding(fake_app,binding_model,{"hwnd":1})
    binding_api.path="c:\\changed.exe"
    try:
        App.validate_model_binding(fake_app,binding_model,{"hwnd":1})
        binding_rejected=False
    except RuntimeError:
        binding_rejected=True
    check("模型窗口安全快照绑定",binding_ok and binding_rejected)
    split_app=type("SplitApp",(),{"should_stop":lambda self:False})()
    controller=ReviewController(split_app)
    sample_action_a=normalize_action({"kind":"click","button":"left","path":[[0.1,0.1]],"duration":0.08})
    sample_action_b=normalize_action({"kind":"click","button":"left","path":[[0.9,0.9]],"duration":0.08})
    def visual_pattern(descending):
        plane=bytearray()
        for y in range(FEATURE_H):
            for x in range(FEATURE_W):
                plane.append(20+(FEATURE_W-1-x if descending else x)*3)
        return bytes(plane)*FEATURE_CHANNELS
    samples=[]
    for session,descending,start in (("s1",False,0),("s2",True,200)):
        feature=visual_pattern(descending)
        for action,offset in ((sample_action_a,0),(sample_action_b,100)):
            for index in range(90):
                samples.append({"session_id":session,"capture_method":"wgc","a":action,"checksum":session+"-"+str(start+offset+index),"created":start+offset+index,"f":feature,"coarse":coarse_feature(feature),"context":{}})
    train,holdout,split=controller.split(samples)
    train_sessions={controller.session_of(item) for item in train}
    holdout_sessions={controller.session_of(item) for item in holdout}
    visual_overlap={visual_perceptual_hash(item["f"]) for item in train}&{visual_perceptual_hash(item["f"]) for item in holdout}
    check("训练留出按session与视觉近重复组隔离",bool(train and holdout) and not train_sessions.intersection(holdout_sessions) and not checksum_set(train).intersection(checksum_set(holdout)) and not visual_overlap and split.get("mode")=="session_family_backend_visual_group")
    policy=TaskAgentPolicy({"allowed_families":["click|left"],"max_consecutive_failures":2,"success_states":[visual_perceptual_hash(visual_pattern(False))],"failure_states":[visual_perceptual_hash(visual_pattern(True))]})
    allowed=policy.allowed_action(sample_action_a) and not policy.allowed_action({"kind":"click","button":"right","path":[[0.5,0.5]],"duration":0.08})
    failure_one=policy.register(visual_pattern(False),sample_action_a,visual_pattern(True),True)
    failure_two=policy.register(visual_pattern(True),sample_action_a,visual_pattern(True),False)
    check("任务白名单成功失败与连续停机",allowed and failure_one["state"]=="failure" and not failure_one["stop"] and failure_two["stop"])
    cache=BoundedLRU(32)
    for index in range(200):
        cache[index]=index
    check("复习距离缓存硬上限",len(cache)<=32)
    with tempfile.TemporaryDirectory() as folder:
        store=DataStore(folder)
        try:
            g1={"id":"g1","name":"游戏一","created":1.0,"needs_review":False,"last_review":None}
            g2={"id":"g2","name":"游戏二","created":2.0,"needs_review":False,"last_review":None}
            store.replace_games([g1,g2],"g1")
            valid_feature=bytes([1])*FEATURE_LEN
            valid_action=json.dumps(sample_action_a,ensure_ascii=False,separators=(",",":"))
            with store.lock,store.db:
                store.db.execute("INSERT INTO learning_sessions(game_id,session_id,status,started,finished,invalid_reason) VALUES('g1','s1','valid',1.0,2.0,'self_test')")
                store.db.execute("INSERT INTO samples(game_id,created,kind,action_signature,action_family,repeat_policy,feature_algorithm_version,action_algorithm_version,feature,coarse,action,source,session_id,capture_method,context,thumbnail,weight,fingerprint) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",("g1",1.0,"click",action_signature(sample_action_a),action_family_key(sample_action_a),"one_shot",FEATURE_ALGORITHM_VERSION,ACTION_ALGORITHM_VERSION,sqlite3.Binary(zlib.compress(valid_feature)),sqlite3.Binary(coarse_feature(valid_feature)),valid_action,"learn","s1","wgc","{}",None,1.0,"valid"))
                store.db.execute("INSERT INTO samples(game_id,created,kind,action_signature,action_family,repeat_policy,feature_algorithm_version,action_algorithm_version,feature,coarse,action,source,session_id,capture_method,context,thumbnail,weight,fingerprint) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",("g1",2.0,"click",action_signature(sample_action_a),action_family_key(sample_action_a),"one_shot",FEATURE_ALGORITHM_VERSION,ACTION_ALGORITHM_VERSION,sqlite3.Binary(b"bad"),sqlite3.Binary(coarse_feature(valid_feature)),valid_action,"learn","s1","wgc","{}",None,1.0,"corrupt"))
                store.db.execute("INSERT INTO models VALUES(?,?,?,?,?,?,?,?)",("g1","complete",1.0,1.0,1,"{}",sqlite3.Binary(b"x"),"x"))
                store.db.execute("INSERT INTO model_backups(game_id,created,prototype_count,validation,payload,checksum) VALUES(?,?,?,?,?,?)",("g1",1.0,1,"{}",sqlite3.Binary(b"x"),"x"))
                store.db.execute("INSERT INTO rejections(game_id,created,feature_algorithm_version,feature,coarse,thumbnail,candidates,source,session_id,capture_method) VALUES(?,?,?,?,?,?,?,?,?,?)",("g1",1.0,FEATURE_ALGORITHM_VERSION,sqlite3.Binary(zlib.compress(valid_feature)),sqlite3.Binary(coarse_feature(valid_feature)),None,"[]","test","s1","wgc"))
            store.save_game_profile("g1",profile)
            working=[dict(g1),dict(g2)]
            working=[item for item in working if item["id"]!="g1"]
            cancel_preserved=bool(store.db.execute("SELECT 1 FROM games WHERE id='g1'").fetchone()) and store.db.execute("SELECT COUNT(*) FROM samples WHERE game_id='g1'").fetchone()[0]==2
            try:
                store.replace_games([g2],"")
                invalid_selection_rejected=False
            except RuntimeError:
                invalid_selection_rejected=True
            loaded,stats=store.load_samples("g1")
            quarantined=store.db.execute("SELECT COUNT(*) FROM corrupt_rows WHERE source_table='samples' AND game_id='g1'").fetchone()[0]==1 and stats["invalid"]==1
            with store.pending_lock:
                store.pending_samples.append({"gid":"g1","fingerprint":"pending-only"})
            result=store.replace_games([g2],"g2")
            cascade=not store.db.execute("SELECT 1 FROM games WHERE id='g1'").fetchone() and all(store.db.execute("SELECT COUNT(*) FROM "+table+" WHERE game_id='g1'").fetchone()[0]==0 for table in ("samples","models","model_backups","rejections","game_profiles"))
            transactional=cancel_preserved and invalid_selection_rejected and quarantined and cascade and result["discarded_pending_samples"]==1 and store.selected_game()["id"]=="g2"
        finally:
            store.close(2.0)
    check("游戏事务删除取消选择与级联清理",transactional)
    with tempfile.TemporaryDirectory() as folder:
        db_path=Path(folder)/"universal_game_ai.db"
        connection=sqlite3.connect(str(db_path))
        connection.execute("CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        connection.execute("INSERT INTO meta VALUES('schema_version','1')")
        connection.execute("CREATE TABLE games(id TEXT PRIMARY KEY,name TEXT NOT NULL COLLATE NOCASE UNIQUE,created REAL NOT NULL,needs_review INTEGER NOT NULL DEFAULT 0,last_review REAL)")
        connection.execute("INSERT INTO games VALUES('g1','迁移游戏',1,0,NULL)")
        connection.execute("CREATE TABLE samples(id INTEGER PRIMARY KEY AUTOINCREMENT,game_id TEXT NOT NULL,created REAL NOT NULL,kind TEXT NOT NULL,action_signature TEXT NOT NULL,feature BLOB NOT NULL,action TEXT NOT NULL,source TEXT NOT NULL,context TEXT NOT NULL,thumbnail BLOB,weight REAL NOT NULL DEFAULT 1.0,fingerprint TEXT NOT NULL)")
        connection.execute("INSERT INTO samples(game_id,created,kind,action_signature,feature,action,source,context,weight,fingerprint) VALUES(?,?,?,?,?,?,?,?,?,?)",("g1",1,"click","click|left|1|1",sqlite3.Binary(zlib.compress(bytes([0])*FEATURE_LEN)),json.dumps(sample_action_a),"learn","{}",1.0,"fp1"))
        connection.execute("CREATE TABLE rejections(id INTEGER PRIMARY KEY AUTOINCREMENT,game_id TEXT NOT NULL,created REAL NOT NULL,feature BLOB NOT NULL,thumbnail BLOB,candidates TEXT NOT NULL,source TEXT NOT NULL)")
        connection.commit()
        connection.close()
        store=DataStore(folder)
        try:
            game_name=store.db.execute("SELECT name FROM games WHERE id='g1'").fetchone()[0]
            sample_count=store.db.execute("SELECT COUNT(*) FROM samples WHERE game_id='g1'").fetchone()[0]
            version=store.db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0]
        finally:
            store.close(2.0)
    check("数据库迁移保持样本和游戏名称",game_name=="迁移游戏" and sample_count==1 and int(version)==DATABASE_SCHEMA_VERSION)
    with tempfile.TemporaryDirectory() as folder:
        store=DataStore(folder)
        barrier_release=threading.Event()
        try:
            g1={"id":"g1","name":"屏障游戏一","created":1.0,"needs_review":False,"last_review":None}
            g2={"id":"g2","name":"屏障游戏二","created":2.0,"needs_review":False,"last_review":None}
            store.replace_games([g1,g2],"g1")
            action=normalize_action({"kind":"click","button":"left","path":[[0.31,0.41]],"duration":0.08})
            def context_for(sid):
                return {"session_id":sid,"capture_method":"wgc","repeat_policy":"one_shot","duplicate_threshold":0.1}
            entered=threading.Event()
            barrier_release.clear()
            store.writer_before_commit=lambda batch:(entered.set(),barrier_release.wait(3.0))
            sid="learn|barrier"
            store.begin_learning_session("g1",sid)
            store.append_sample("g1",bytes([11])*FEATURE_LEN,action,"learn",context_for(sid),None,1.0)
            store.pending_event.set()
            writer_taken=entered.wait(3.0)
            with store.pending_lock:
                inflight_visible=not store.pending_samples and store.writer_inflight==1
            barrier_done=threading.Event()
            barrier_errors=[]
            def wait_barrier():
                try:
                    store.sample_write_barrier(4.0)
                except Exception as error:
                    barrier_errors.append(str(error))
                finally:
                    store.close_current_thread()
                    barrier_done.set()
            barrier_thread=threading.Thread(target=wait_barrier,name="SelfTestBarrier")
            barrier_thread.start()
            time.sleep(0.08)
            barrier_waited=not barrier_done.is_set()
            barrier_release.set()
            barrier_thread.join(4.0)
            store.writer_before_commit=None
            store.validate_learning_session("g1",sid)
            committed=len(store.load_samples("g1")[0])==1
            discard_entered=threading.Event()
            barrier_release.clear()
            store.writer_before_commit=lambda batch:(discard_entered.set(),barrier_release.wait(3.0))
            discard_sid="learn|discard"
            store.begin_learning_session("g1",discard_sid)
            store.append_sample("g1",bytes([23])*FEATURE_LEN,action,"learn",context_for(discard_sid),None,1.0)
            store.pending_event.set()
            discard_taken=discard_entered.wait(3.0)
            discard_done=threading.Event()
            discard_result=[]
            def discard_worker():
                try:
                    discard_result.append(store.discard_session("g1",discard_sid,"self_test_discard"))
                finally:
                    store.close_current_thread()
                    discard_done.set()
            discard_thread=threading.Thread(target=discard_worker,name="SelfTestDiscard")
            discard_thread.start()
            time.sleep(0.08)
            discard_waited=not discard_done.is_set()
            barrier_release.set()
            discard_thread.join(4.0)
            store.writer_before_commit=None
            discard_clean=store.db.execute("SELECT COUNT(*) FROM samples WHERE game_id='g1' AND session_id=?",(discard_sid,)).fetchone()[0]==0 and store.learning_session_status("g1",discard_sid)["status"]=="invalid"
            delete_entered=threading.Event()
            barrier_release.clear()
            store.writer_before_commit=lambda batch:(delete_entered.set(),barrier_release.wait(3.0))
            delete_sid="learn|delete"
            store.begin_learning_session("g2",delete_sid)
            store.append_sample("g2",bytes([37])*FEATURE_LEN,action,"learn",context_for(delete_sid),None,1.0)
            store.pending_event.set()
            delete_taken=delete_entered.wait(3.0)
            delete_done=threading.Event()
            delete_result=[]
            def delete_worker():
                try:
                    delete_result.append(store.delete_game("g2"))
                finally:
                    store.close_current_thread()
                    delete_done.set()
            delete_thread=threading.Thread(target=delete_worker,name="SelfTestDelete")
            delete_thread.start()
            time.sleep(0.08)
            delete_waited=not delete_done.is_set()
            barrier_release.set()
            delete_thread.join(4.0)
            store.writer_before_commit=None
            delete_clean=delete_result==[True] and not store.db.execute("SELECT 1 FROM games WHERE id='g2'").fetchone()
            recovery_sid="learn|recovery"
            store.begin_learning_session("g1",recovery_sid)
            failed_once=threading.Event()
            def fail_once(batch):
                store.writer_before_commit=None
                failed_once.set()
                raise sqlite3.IntegrityError("self_test_writer_failure")
            store.writer_before_commit=fail_once
            store.append_sample("g1",bytes([49])*FEATURE_LEN,action,"learn",context_for(recovery_sid),None,1.0)
            store.pending_event.set()
            failure_seen=failed_once.wait(3.0)
            recovery_deadline=time.monotonic()+5.0
            recovered=False
            while time.monotonic()<recovery_deadline:
                with store.pending_lock:
                    recovered=not store.pending_samples and store.writer_inflight==0 and store.writer_error is None
                if recovered:
                    break
                time.sleep(0.05)
            if recovered:
                store.validate_learning_session("g1",recovery_sid)
            writer_race_ok=writer_taken and inflight_visible and barrier_waited and barrier_done.is_set() and not barrier_errors and committed and discard_taken and discard_waited and discard_done.is_set() and bool(discard_result) and discard_clean and delete_taken and delete_waited and delete_done.is_set() and delete_clean and failure_seen and recovered
        finally:
            barrier_release.set()
            store.writer_before_commit=None
            store.close(5.0)
    check("写入屏障覆盖提交中删除作废与错误恢复",writer_race_ok)
    with tempfile.TemporaryDirectory() as folder:
        store=DataStore(folder)
        try:
            game={"id":"g1","name":"崩溃恢复游戏","created":1.0,"needs_review":False,"last_review":None}
            store.replace_games([game],"g1")
            sid="learn|staging_crash"
            store.begin_learning_session("g1",sid)
            store.append_sample("g1",bytes([61])*FEATURE_LEN,sample_action_a,"learn",{"session_id":sid,"capture_method":"wgc","repeat_policy":"one_shot"},None,1.0)
            store.sample_write_barrier(4.0)
        finally:
            store.close(4.0)
        reopened=DataStore(folder)
        try:
            visible_samples,_=reopened.load_samples("g1")
            raw_count=reopened.db.execute("SELECT COUNT(*) FROM samples WHERE game_id='g1' AND session_id=?",(sid,)).fetchone()[0]
            staging_status=reopened.learning_session_status("g1",sid)
            staging_hidden=not visible_samples and raw_count==1 and staging_status and staging_status["status"]=="staging"
        finally:
            reopened.close(4.0)
    check("staging学习session崩溃后永不进入复习",staging_hidden)
    with tempfile.TemporaryDirectory() as folder:
        store=DataStore(folder)
        try:
            game={"id":"g1","name":"模型兼容游戏","created":1.0,"needs_review":False,"last_review":None}
            store.replace_games([game],"g1")
            temporal={"recent_frame_count":3,"recent_frame_deltas":[1.0,2.0],"recent_actions":["<START>","click|left"],"previous_action_changed_frame":True,"state_duration":0.1,"cursor":[0.5,0.5],"window_size":[640,360],"dpi":96,"capture_method":"wgc"}
            binding={"process_paths":["c:\\game.exe"],"window_classes":["GameWnd"],"content_rect_norms":[[0.0,0.0,1.0,1.0]],"content_aspect_min":16/9,"content_aspect_max":16/9,"dpi_min":96,"dpi_max":96,"capture_methods":["wgc"],"window_rule_version":WINDOW_RULE_VERSION,"capture_backend_version":CAPTURE_BACKEND_VERSION}
            model={"format_version":FORMAT_VERSION,"model_schema_version":MODEL_SCHEMA_VERSION,"feature_width":FEATURE_W,"feature_height":FEATURE_H,"feature_algorithm_version":FEATURE_ALGORITHM_VERSION,"action_algorithm_version":ACTION_ALGORITHM_VERSION,"game_id":"g1","complete":True,"compatibility_signature":compatibility_signature(),"source_build_hash":"0"*64,"algorithm_snapshot":{"compatibility_signature":compatibility_signature(),"source_build_hash":"0"*64},"model_binding":binding,"sequence_model":{},"safety_profile_checksum":"a"*64,"capture_backends":["wgc"],"validation":{},"prototypes":[{"id":"p1","cluster_id":"c1","canonical_action_signature":action_signature(sample_action_a),"f":bytes([71])*FEATURE_LEN,"coarse":coarse_feature(bytes([71])*FEATURE_LEN),"a":sample_action_a,"threshold":1.0,"support":1,"temporal":temporal,"temporal_threshold":1.0,"nearest_conflicting_distance":None,"nearest_rejected_distance":None,"minimum_second_candidate_gap":0.1,"repeat_policy":"one_shot","max_rate":1.0,"authorized":True}]}
            ui_only_changed=dict(model)
            ui_only_changed["source_build_hash"]="f"*64
            ui_only_changed["algorithm_snapshot"]={"compatibility_signature":compatibility_signature(),"source_build_hash":"f"*64}
            feature_changed=dict(model)
            changed_signature=dict(compatibility_signature())
            changed_signature["feature_algorithm_version"]=FEATURE_ALGORITHM_VERSION+1
            feature_changed["compatibility_signature"]=changed_signature
            compatibility_ok=store._model_valid(model,"g1",True) and store._model_valid(ui_only_changed,"g1",True) and not store._model_valid(feature_changed,"g1",True)
        finally:
            store.close(4.0)
    check("UI构建变化兼容且特征版本变化拒绝模型",compatibility_ok)
    threshold_original={key:getattr(VersionedThresholdConfig,key) for key in ("review_min_accepted","minimum_coverage","review_min_holdout","required_sessions")}
    try:
        enough_base,global_base=evaluate_validation_thresholds(True,VersionedThresholdConfig.required_sessions,VersionedThresholdConfig.review_min_holdout,VersionedThresholdConfig.review_min_accepted,VersionedThresholdConfig.minimum_coverage,VersionedThresholdConfig.minimum_overall_accuracy,VersionedThresholdConfig.maximum_error_upper_95,0,0)
        VersionedThresholdConfig.review_min_accepted=threshold_original["review_min_accepted"]+1
        enough_changed,_=evaluate_validation_thresholds(True,threshold_original["required_sessions"],threshold_original["review_min_holdout"],threshold_original["review_min_accepted"],VersionedThresholdConfig.minimum_coverage,VersionedThresholdConfig.minimum_overall_accuracy,VersionedThresholdConfig.maximum_error_upper_95,0,0)
        VersionedThresholdConfig.review_min_accepted=threshold_original["review_min_accepted"]
        VersionedThresholdConfig.minimum_coverage=min(1.0,threshold_original["minimum_coverage"]+0.01)
        _,global_changed=evaluate_validation_thresholds(True,threshold_original["required_sessions"],threshold_original["review_min_holdout"],threshold_original["review_min_accepted"],threshold_original["minimum_coverage"],VersionedThresholdConfig.minimum_overall_accuracy,VersionedThresholdConfig.maximum_error_upper_95,0,0)
        threshold_sync=enough_base and global_base and not enough_changed and not global_changed and abs((1.0-0.83)-0.17)<1e-12
    finally:
        for key,value in threshold_original.items():
            setattr(VersionedThresholdConfig,key,value)
    check("版本化验收阈值与拒识率同步",threshold_sync)
    with tempfile.TemporaryDirectory() as folder:
        store=DataStore(folder)
        try:
            game={"id":"g1","name":"百轮循环游戏","created":1.0,"needs_review":False,"last_review":None}
            store.replace_games([game],"g1")
            baseline_threads=len([thread for thread in threading.enumerate() if thread.name.startswith("UniversalGameAI-")])
            baseline_children=len(multiprocessing.active_children())
            for index in range(100):
                sid="learn|cycle|"+str(index)
                store.begin_learning_session("g1",sid)
                feature=bytes([(index*17)%251])*FEATURE_LEN
                action=normalize_action({"kind":"click","button":"left","path":[[(index%20+1)/21.0,((index*7)%20+1)/21.0]],"duration":0.08})
                store.append_sample("g1",feature,action,"learn",{"session_id":sid,"capture_method":"wgc","repeat_policy":"one_shot","recent_frame_count":3,"recent_frame_deltas":[float(index%5),float((index+1)%5)],"recent_actions":["<START>",action_signature(action)],"previous_action_changed_frame":True,"state_duration":0.1,"cursor":[0.5,0.5],"window_size":[640,360],"dpi":96},None,1.0)
                store.sample_write_barrier(4.0)
                store.validate_learning_session("g1",sid)
            initial_connections=store.connection_count()
            workers=[]
            def connection_probe():
                try:
                    store.sample_stats("g1")
                finally:
                    store.close_current_thread()
            for index in range(24):
                thread=threading.Thread(target=connection_probe,name="SelfTestConnection"+str(index))
                workers.append(thread)
                thread.start()
            for thread in workers:
                thread.join(5.0)
            lifecycle_stable=store.sample_stats("g1")["valid"]>0 and store.connection_count()<=initial_connections and len([thread for thread in threading.enumerate() if thread.name.startswith("UniversalGameAI-")])==baseline_threads and len(multiprocessing.active_children())==baseline_children and all(not thread.is_alive() for thread in workers)
        finally:
            store.close(5.0)
    check("百轮session与短线程SQLite连接长期稳定",lifecycle_stable)
    payload=add_checksum({"version":FORMAT_VERSION,"items":[1,2,3]})
    check("模型checksum行为",verify_checksum(payload) and not verify_checksum({**payload,"version":FORMAT_VERSION+1}))
    snapshot=algorithm_snapshot()
    check("模型兼容签名与源码审计哈希分离",len(str(snapshot.get("source_build_hash","")))==64 and snapshot.get("compatibility_signature")==compatibility_signature() and "source_build_hash" not in compatibility_signature())
    check("freeze_support可调用",callable(multiprocessing.freeze_support))
    basic_authorizer=BasicSafeAuthorizer()
    check("单session仅授权基础安全动作",basic_authorizer.authorize("click|left",VersionedThresholdConfig.basic_safe_min_positive,VersionedThresholdConfig.basic_safe_min_consistency,1,True,True) and basic_authorizer.authorize("no_op",VersionedThresholdConfig.basic_safe_min_positive,1.0,1,True,True) and not basic_authorizer.authorize("drag|left",100,1.0,4,True,True) and not basic_authorizer.authorize("click|left",VersionedThresholdConfig.basic_safe_min_positive-1,1.0,1,True,True))
    fake_app=object.__new__(App)
    fake_app.background_lock=threading.RLock()
    fake_app.background_generations=defaultdict(int)
    fake_app.background_threads=set()
    fake_app.closing=False
    fake_app.shutdown_started=False
    fake_app.mode=None
    class BackgroundStore:
        def log_error(self,*args,**kwargs):
            return None
        def close_current_thread(self):
            return None
    fake_app.store=BackgroundStore()
    fake_app.ui=lambda callback,key=None:callback()
    stale_gate=threading.Event()
    stale_errors=[]
    current_results=[]
    fake_app.run_background("generation_test",lambda:(stale_gate.wait(2.0),(_ for _ in ()).throw(RuntimeError("old")))[1],None,lambda error:stale_errors.append(str(error)))
    fake_app.run_background("generation_test",lambda:"new",lambda value:current_results.append(value),lambda error:stale_errors.append(str(error)))
    stale_gate.set()
    deadline=time.monotonic()+3.0
    while time.monotonic()<deadline:
        with fake_app.background_lock:
            alive=[thread for thread in fake_app.background_threads if thread.is_alive()]
        if not alive:
            break
        for thread in alive:
            thread.join(0.05)
    check("后台过时错误generation抑制",current_results==["new"] and not stale_errors and not fake_app.background_threads)
    class FakeDialog:
        def __init__(self):
            self.releases=0
            self.destroys=0
        def grab_release(self):
            self.releases+=1
        def destroy(self):
            self.destroys+=1
    fake_dialog=FakeDialog()
    dialog_state={"closed":False}
    first_close=fake_app.close_dialog(fake_dialog,dialog_state)
    second_close=fake_app.close_dialog(fake_dialog,dialog_state)
    check("统一对话框关闭幂等",first_close and not second_close and fake_dialog.releases==1 and fake_dialog.destroys==1)
    parsed=ast.parse(text,str(source_path))
    source_lines=text.splitlines()
    def self_test_method_source(class_name,method_name):
        for node in parsed.body:
            if isinstance(node,ast.ClassDef) and node.name==class_name:
                for child in node.body:
                    if isinstance(child,ast.FunctionDef) and child.name==method_name:
                        return "\n".join(source_lines[child.lineno-1:child.end_lineno])
        return ""
    game_dialog_source=self_test_method_source("App","open_game_dialog")
    window_dialog_source=self_test_method_source("App","open_window_dialog")
    background_method_source=self_test_method_source("App","run_background")
    check("游戏取消关闭无未定义state",game_dialog_source.count('state={"closed":False}')==1 and game_dialog_source.count("self.close_dialog(win,state)")>=2)
    check("窗口与内容区域仅一次总确认","select_content_region(" not in window_dialog_source and all(value in window_dialog_source for value in ("自动区域","整个客户区","手动调整")))
    check("四个长流程已下沉Controller",len(self_test_method_source("LearningController","_run_impl").splitlines())>250 and len(self_test_method_source("ReviewController","_run_impl").splitlines())>220 and len(self_test_method_source("TrainingController","_run_impl").splitlines())>250 and len(self_test_method_source("TeachingController","create_window").splitlines())>250 and len(self_test_method_source("App","_learning_worker_impl").splitlines())<=3)
    check("后台成功失败同代校验","current_generation()" in background_method_source and "background_threads.add" in background_method_source and "background_threads.discard" in background_method_source)
    result={"status":"passed" if not failures else "failed","checks":checks,"failures":failures}
    sys.stdout.write(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n")
    return 0 if not failures else 1
def run_windows_smoke_test():
    report={"status":"failed","checks":{},"details":{},"manual_required":[]}
    def record(name,value,detail=None):
        report["checks"][str(name)]=bool(value)
        if detail is not None:
            report["details"][str(name)]=detail
    if os.name!="nt":
        report["status"]="unsupported"
        report["details"]["platform"]="真实Windows 11冒烟测试只能在Windows 11目标机运行"
        sys.stdout.write(json.dumps(report,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n")
        return 2
    bridge=None
    root=None
    app=None
    original_local=os.environ.get("LOCALAPPDATA")
    try:
        version=sys.getwindowsversion()
        record("Windows 11系统",int(version.major)==10 and int(version.build)>=22000,{"major":int(version.major),"build":int(version.build)})
        with tempfile.TemporaryDirectory() as folder:
            os.environ["LOCALAPPDATA"]=folder
            enable_dpi_awareness()
            root=tk.Tk()
            root.withdraw()
            app=App(root)
            root.update_idletasks()
            record("Tk控制面板启动",bool(app.controls and app.root.winfo_exists()),{"control_count":len(app.controls)})
            bridge=app.api
            windows=bridge.enum_windows()
            record("窗口枚举",bool(windows),{"count":len(windows)})
            hydrated=[]
            dpi_values=set()
            for item in windows:
                try:
                    identity=bridge.target_identity(item)
                    hydrated.append(identity)
                    dpi_values.add(int(identity.get("dpi",0)))
                except Exception as error:
                    app.store.log_error("WINDOWS_SMOKE_IDENTITY_FAILED",error,window_identity=item)
            record("窗口完整身份读取",bool(hydrated),{"count":len(hydrated)})
            record("DPI观测",bool(dpi_values),{"observed":sorted(dpi_values),"required":[96,120,144]})
            exact=None
            for argument in sys.argv:
                if argument.startswith("--smoke-hwnd="):
                    exact=safe_int(argument.split("=",1)[1],0)
            selected=next((item for item in hydrated if exact and int(item.get("hwnd",0))==exact),None)
            if selected is None:
                selected=next((item for item in hydrated if any(token in (str(item.get("title",""))+" "+str(item.get("class",""))+" "+str(item.get("process_path",""))).casefold() for token in ("雷电","ldplayer","dnplayer"))),None)
            record("雷电模拟器窗口识别",selected is not None,{"selected":selected or {},"hint":"可使用--smoke-hwnd=窗口句柄指定其他目标窗口"})
            if selected is not None:
                selected["content_rect_norm"]=[0.0,0.0,1.0,1.0]
                selected["title_rule"]={"mode":"none","value":""}
                selected=bridge.target_identity(selected)
                methods=[]
                capture_error=""
                try:
                    captured=bridge.capture_gray(selected,False,True,False)
                    methods=sorted({str(item.get("method","")) for item in captured.get("validation_candidates",[]) if item.get("method")})
                except Exception as error:
                    capture_error=str(error)
                    app.store.log_error("WINDOWS_SMOKE_CAPTURE_FAILED",error,window_identity=selected)
                required_methods=["Windows Graphics Capture","PrintWindow客户区","窗口DC","前台桌面裁剪"]
                record("四采集后端冒烟",all(name in methods for name in required_methods),{"successful":methods,"required":required_methods,"error":capture_error})
                rect_before=tuple(bridge.client_rect(int(selected["hwnd"])))
                observe_seconds=0.0
                for argument in sys.argv:
                    if argument.startswith("--smoke-observe-seconds="):
                        observe_seconds=safe_float(argument.split("=",1)[1],0.0,0.0,300.0)
                observations={"moved":False,"resized":False,"minimized":False,"restored":False,"restarted":False}
                was_minimized=False
                deadline=time.monotonic()+observe_seconds
                while time.monotonic()<deadline:
                    hwnd=int(selected.get("hwnd",0))
                    if bridge.valid(hwnd):
                        minimized=bool(bridge.user32.IsIconic(wintypes.HWND(hwnd)))
                        observations["minimized"]|=minimized
                        observations["restored"]|=was_minimized and not minimized
                        was_minimized=minimized
                        if not minimized:
                            try:
                                rect_now=tuple(bridge.client_rect(hwnd))
                                observations["moved"]|=rect_now[:2]!=rect_before[:2]
                                observations["resized"]|=rect_now[2:]!=rect_before[2:]
                            except Exception:
                                pass
                    else:
                        replacement=None
                        for item in bridge.enum_windows():
                            try:
                                identity=bridge.target_identity(item)
                            except Exception:
                                continue
                            if str(identity.get("process_path",""))==str(selected.get("process_path","")) and str(identity.get("class",""))==str(selected.get("class","")):
                                replacement=identity
                                break
                        if replacement is not None:
                            observations["restarted"]=True
                            selected=replacement
                    time.sleep(0.1)
                record("真实窗口移动缩放最小化重启观察",observe_seconds>0 and all(observations.values()),{"observe_seconds":observe_seconds,"observed":observations})
            report["manual_required"]=["在100%、125%、150%缩放环境分别运行一次并确认DPI观测包含96、120、144","使用--smoke-observe-seconds=30期间移动、缩放、最小化、恢复并重启目标窗口","在STARTING、RUNNING、STOPPING阶段分别按ESC并确认停止延迟","使用真实外部鼠标注入与非ESC键盘输入确认立即停机且学习session变为invalid"]
            app.api.block_input()
            app.api.release_all_buttons()
            app.store.close(5.0)
            app.api.close()
            root.destroy()
            app=None
            bridge=None
            root=None
        automated=[value for key,value in report["checks"].items() if key!="真实窗口移动缩放最小化重启观察"]
        report["status"]="passed" if automated and all(automated) else "needs_attention"
    except Exception as error:
        report["details"]["fatal"]="".join(traceback.format_exception(type(error),error,error.__traceback__))
    finally:
        if app is not None:
            try:
                app.api.block_input()
                app.api.release_all_buttons()
                app.store.close(5.0)
                app.api.close()
            except Exception:
                pass
        if root is not None:
            try:
                root.destroy()
            except Exception:
                pass
        if original_local is None:
            os.environ.pop("LOCALAPPDATA",None)
        else:
            os.environ["LOCALAPPDATA"]=original_local
    sys.stdout.write(json.dumps(report,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n")
    return 0 if report["status"]=="passed" else 1
def run_acceptance_test(path=None):
    source_path=Path(path or __file__).resolve()
    raw=source_path.read_bytes()
    source=raw.decode("utf-8")
    report={"status":"failed","checks":{},"details":{},"manual_required":[]}
    failures=[]
    def record(name,value,detail=None):
        passed=bool(value)
        report["checks"][str(name)]=passed
        if not passed:
            failures.append(str(name))
        if detail is not None:
            report["details"][str(name)]=detail
    try:
        tree=ast.parse(source,str(source_path))
        lines=source.splitlines()
        def method_source(class_name,method_name):
            for node in tree.body:
                if isinstance(node,ast.ClassDef) and node.name==class_name:
                    for child in node.body:
                        if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef)) and child.name==method_name:
                            return "\n".join(lines[child.lineno-1:child.end_lineno])
            return ""
        game_source=method_source("App","open_game_dialog")
        window_source=method_source("App","open_window_dialog")
        background_source=method_source("App","run_background")
        training_source=method_source("TrainingController","_run_impl")
        execute_source=method_source("App","execute_action")
        ask_source=method_source("TeachingController","create_window")
        result_source=method_source("App","_show_result_modal")
        build_source=method_source("App","_build")
        review_api_source=next(("\n".join(lines[node.lineno-1:node.end_lineno]) for node in tree.body if isinstance(node,ast.ClassDef) and node.name=="ReviewProcessApi"),"")
        record("源文件可编译",bool(compile(source,str(source_path),"exec")))
        record("游戏对话框关闭状态已定义且幂等",'state={"closed":False}' in game_source and game_source.count("self.close_dialog(win,state)")>=2 and "state[\"closed\"]=True" not in game_source)
        record("窗口与区域一次确认","select_content_region(" not in window_source and all(label in window_source for label in ("自动区域","整个客户区","手动调整","一次确认")))
        record("六个主按钮突出",all(('"'+name+'",self.') in build_source for name in ("游戏","选择窗口","学习","复习","训练","请教")) and "高级设置" in build_source)
        record("后台成功失败均检查generation","current_generation()" in background_source and "background_threads.add" in background_source and "background_threads.discard" in background_source)
        record("复习路径SendInput恒零","SendInput" not in review_api_source and "_send" not in review_api_source)
        record("训练不存在键盘注入结构",all(token not in training_source for token in ("KBDINPUT","KEYEVENTF","keybd_event","SendInput")))
        record("自动动作反复验证区域",execute_source.count("validate_target")>=1 and execute_source.count("validate_action_point")>=3 and "point_to_screen" in execute_source)
        record("请教支持选择跳过自定义与ESC",all(token in ask_source for token in ("跳过","自定义","结束请教")) and "poll_global_escape" in source and "close_ask" in source)
        record("结果弹窗有确认按钮",'text="确认"' in result_source and "WM_DELETE_WINDOW" in result_source)
        basic=BasicSafeAuthorizer()
        record("基础安全动作单session分级授权",basic.authorize("click|left",VersionedThresholdConfig.basic_safe_min_positive,VersionedThresholdConfig.basic_safe_min_consistency,1,True,True) and not basic.authorize("drag|left",100,1.0,4,True,True) and not basic.authorize("click|left",VersionedThresholdConfig.basic_safe_min_positive-1,1.0,1,True,True))
        if os.name!="nt":
            report["manual_required"]=["在Windows 11运行 python main.py --acceptance-test 以执行真实Tk控件回调和窗口枚举验收","选择雷电模拟器与一个普通窗口各执行一次同界面区域确认","实际完成学习、复习、训练、请教并在STARTING、RUNNING、STOPPING阶段分别按ESC"]
            report["status"]="windows_required" if not failures else "failed"
            sys.stdout.write(json.dumps(report,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n")
            return 2 if not failures else 1
        original_local=os.environ.get("LOCALAPPDATA")
        root=None
        app=None
        try:
            with tempfile.TemporaryDirectory() as folder:
                os.environ["LOCALAPPDATA"]=folder
                enable_dpi_awareness()
                root=tk.Tk()
                root.deiconify()
                app=App(root)
                root.update_idletasks()
                root.update()
                def descendants(widget):
                    result=[]
                    for child in widget.winfo_children():
                        result.append(child)
                        result.extend(descendants(child))
                    return result
                def find_button(widget,label):
                    return next((child for child in descendants(widget) if isinstance(child,ttk.Button) and str(child.cget("text"))==label),None)
                def find_toplevel(title):
                    root.update_idletasks()
                    root.update()
                    return next((child for child in root.winfo_children() if isinstance(child,tk.Toplevel) and child.winfo_exists() and child.title()==title),None)
                record("启动后控制面板出现",root.winfo_exists() and all(find_button(root,name) is not None for name in ("游戏","选择窗口","学习","复习","训练","请教","停止")))
                app.prompt_text=lambda *args,**kwargs:"验收游戏A"
                app.open_game_dialog()
                dialog=find_toplevel("游戏")
                new_button=find_button(dialog,"新建") if dialog else None
                confirm_button=find_button(dialog,"确认") if dialog else None
                if new_button:
                    new_button.invoke()
                    root.update()
                if confirm_button:
                    confirm_button.invoke()
                    root.update()
                game_created=bool(app.selected_game and app.selected_game.get("name")=="验收游戏A")
                app.prompt_text=lambda *args,**kwargs:"验收游戏B"
                app.open_game_dialog()
                dialog=find_toplevel("游戏")
                if dialog:
                    find_button(dialog,"新建").invoke()
                    root.update()
                    find_button(dialog,"确认").invoke()
                    root.update()
                app.prompt_text=lambda *args,**kwargs:"验收游戏B编辑"
                app.open_game_dialog()
                dialog=find_toplevel("游戏")
                if dialog:
                    find_button(dialog,"编辑").invoke()
                    root.update()
                    find_button(dialog,"确认").invoke()
                    root.update()
                app.confirm_dialog=lambda *args,**kwargs:True
                app.open_game_dialog()
                dialog=find_toplevel("游戏")
                if dialog:
                    find_button(dialog,"删除").invoke()
                    root.update()
                    find_button(dialog,"确认").invoke()
                    root.update()
                game_crud=game_created and len(app.store.games())==1 and app.store.games()[0]["name"]=="验收游戏A"
                app.open_game_dialog()
                dialog=find_toplevel("游戏")
                cancel_ok=False
                if dialog:
                    find_button(dialog,"取消").invoke()
                    root.update()
                    cancel_ok=not dialog.winfo_exists()
                app.open_game_dialog()
                dialog=find_toplevel("游戏")
                close_ok=False
                if dialog:
                    command=dialog.protocol("WM_DELETE_WINDOW")
                    root.tk.call(command)
                    root.update()
                    close_ok=not dialog.winfo_exists()
                record("游戏新建编辑删除确认取消关闭无异常",game_crud and cancel_ok and close_ok)
                app.open_window_dialog()
                dialog=find_toplevel("选择窗口")
                window_cancel=False
                if dialog:
                    button=find_button(dialog,"取消")
                    if button:
                        button.invoke()
                        root.update()
                        window_cancel=not dialog.winfo_exists()
                record("选择窗口对话框取消无异常",window_cancel)
                popup_confirmed={"value":False}
                def confirm_popup():
                    dialog=find_toplevel("验收结果")
                    button=find_button(dialog,"确认") if dialog else None
                    popup_confirmed["value"]=button is not None
                    if button:
                        button.invoke()
                root.after(100,confirm_popup)
                app.show_info("验收结果","所有结果弹窗必须包含可用的确认按钮")
                record("真实结果弹窗确认按钮可用",popup_confirmed["value"])
                report["manual_required"]=["从窗口列表分别选择雷电模拟器和普通窗口，确认预览、自动区域、整个客户区、手动调整和一次总确认","在客户区内仅用鼠标完成学习并用非ESC键验证session整体作废","在STARTING、RUNNING、STOPPING阶段分别按ESC验证停止","实际复习确认鼠标注入计数为零，实际训练确认所有坐标都在区域内","实际请教验证选择、跳过、自定义和ESC结束"]
                with app.background_lock:
                    for key in list(app.background_generations):
                        app.background_generations[key]+=1
                    threads=list(app.background_threads)
                for thread in threads:
                    thread.join(2.0)
                app.store.close(5.0)
                app.api.close()
                root.destroy()
                root=None
                app=None
        finally:
            if app is not None:
                try:
                    with app.background_lock:
                        for key in list(app.background_generations):
                            app.background_generations[key]+=1
                    app.store.close(5.0)
                    app.api.close()
                except Exception:
                    pass
            if root is not None:
                try:
                    root.destroy()
                except Exception:
                    pass
            if original_local is None:
                os.environ.pop("LOCALAPPDATA",None)
            else:
                os.environ["LOCALAPPDATA"]=original_local
        report["status"]="passed" if not failures else "failed"
    except Exception as error:
        report["details"]["fatal"]="".join(traceback.format_exception(type(error),error,error.__traceback__))
        report["status"]="failed"
    sys.stdout.write(json.dumps(report,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n")
    return 0 if report["status"]=="passed" else 1
EXTENSION_SCHEMA_VERSION=2
VISION_ARCHITECTURE_VERSION=1
OCR_SEMANTIC_VERSION=1
SELECTED_DATA_DIR=None
CURRENT_VISION_RUNTIME=None
CURRENT_OCR_RUNTIME=None
class SemanticEventHub:
    def __init__(self):
        self.lock=threading.RLock()
        self.events={}
    def publish(self,game_id,region_id,event):
        value=dict(event) if isinstance(event,dict) else {}
        value["time"]=time.monotonic()
        value["game_id"]=str(game_id)
        value["region_id"]=str(region_id)
        with self.lock:
            self.events[(str(game_id),str(region_id))]=value
    def latest(self,game_id=None,max_age=1.5):
        now=time.monotonic()
        with self.lock:
            values=[dict(value) for value in self.events.values() if game_id is None or str(value.get("game_id"))==str(game_id)]
        values=[value for value in values if now-safe_float(value.get("time"),0.0)<=float(max_age)]
        if not values:
            return None
        values.sort(key=lambda value:(1 if value.get("terminal") else 0,abs(safe_float(value.get("progress"),0.0)),safe_float(value.get("time"),0.0)),reverse=True)
        result={"terminal":"","progress":0.0,"status":"neutral","events":[]}
        for value in values:
            result["events"].append({key:value.get(key) for key in ("region_id","terminal","progress","status","reset")})
            if value.get("terminal") in {"success","failure"}:
                result["terminal"]=value["terminal"]
                break
            if abs(safe_float(value.get("progress"),0.0))>abs(result["progress"]):
                result["progress"]=max(-1.0,min(1.0,safe_float(value.get("progress"),0.0)))
                result["status"]=str(value.get("status","neutral"))
        return result
SEMANTIC_EVENT_HUB=SemanticEventHub()
def configure_data_directory(path):
    global SELECTED_DATA_DIR
    base=Path(path).expanduser().resolve()
    base.mkdir(parents=True,exist_ok=True)
    for name in ("python_packages","models","models/vision","models/ocr","cache","cache/pip","temp","logs","backups"):
        (base/name).mkdir(parents=True,exist_ok=True)
    package_dir=str(base/"python_packages")
    if package_dir not in sys.path:
        sys.path.insert(0,package_dir)
    os.environ["UGAI_DATA_DIR"]=str(base)
    os.environ["PIP_TARGET"]=package_dir
    os.environ["PIP_CACHE_DIR"]=str(base/"cache"/"pip")
    os.environ["TORCH_HOME"]=str(base/"models"/"torch")
    os.environ["HF_HOME"]=str(base/"models"/"huggingface")
    os.environ["XDG_CACHE_HOME"]=str(base/"cache")
    os.environ["TMP"]=str(base/"temp")
    os.environ["TEMP"]=str(base/"temp")
    tempfile.tempdir=str(base/"temp")
    SELECTED_DATA_DIR=base
    return base
def startup_select_data_directory(root):
    from tkinter import filedialog
    root.title("通用游戏AI控制面板")
    root.geometry("760x360")
    root.minsize(680,320)
    root.option_add("*Font",("Microsoft YaHei UI",10))
    holder={"path":None,"done":False,"cancelled":False}
    path_var=tk.StringVar(value="尚未选择数据目录")
    status_var=tk.StringVar(value="请选择一个具有至少256MB可用空间的数据目录。数据库、模型、依赖、缓存、日志和临时文件都会放入该目录。")
    outer=ttk.Frame(root,padding=24)
    outer.pack(fill="both",expand=True)
    ttk.Label(outer,text="通用游戏AI控制面板",font=("Microsoft YaHei UI",18,"bold")).pack(anchor="w")
    ttk.Label(outer,text="第一步：选择数据目录",font=("Microsoft YaHei UI",14,"bold")).pack(anchor="w",pady=(20,6))
    ttk.Label(outer,textvariable=path_var,wraplength=700).pack(anchor="w",fill="x")
    ttk.Label(outer,textvariable=status_var,wraplength=700).pack(anchor="w",fill="x",pady=(8,16))
    buttons=ttk.Frame(outer)
    buttons.pack(fill="x")
    confirm_button=ttk.Button(buttons,text="确认",state="disabled")
    def choose():
        value=filedialog.askdirectory(parent=root,title="选择通用游戏AI数据目录",mustexist=False)
        if not value:
            return
        try:
            base=Path(value).expanduser().resolve()
            base.mkdir(parents=True,exist_ok=True)
            usage=shutil.disk_usage(base)
            if int(usage.free)<MIN_FREE_DISK:
                raise RuntimeError("剩余磁盘空间不足256MB")
            test=base/(".ugai_write_test_"+uuid.uuid4().hex)
            test.write_bytes(b"ok")
            test.unlink()
            holder["path"]=base
            path_var.set(str(base))
            status_var.set("目录读写与空间检查通过。点击“确认”后进入完整控制面板。")
            confirm_button.configure(state="normal")
        except Exception as error:
            holder["path"]=None
            confirm_button.configure(state="disabled")
            status_var.set("目录不可用："+str(error))
    def confirm():
        if holder["path"] is None:
            return
        try:
            configure_data_directory(holder["path"])
            holder["done"]=True
            root.quit()
        except Exception as error:
            status_var.set("初始化数据目录失败："+str(error))
    def cancel():
        holder["cancelled"]=True
        root.quit()
    ttk.Button(buttons,text="选择数据目录",command=choose).pack(side="left",fill="x",expand=True,ipady=8)
    confirm_button.configure(command=confirm)
    confirm_button.pack(side="left",fill="x",expand=True,padx=(10,0),ipady=8)
    root.protocol("WM_DELETE_WINDOW",cancel)
    root.mainloop()
    for child in list(root.winfo_children()):
        child.destroy()
    if holder["cancelled"] or not holder["done"]:
        return None
    return holder["path"]
class RuntimeInstaller:
    def __init__(self,base):
        self.base=Path(base)
        self.process=None
        self.lock=threading.RLock()
    def _gpu_vendor(self):
        try:
            creationflags=0x08000000 if os.name=="nt" else 0
            value=subprocess.check_output(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-Command","(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) -join ';'"],stderr=subprocess.STDOUT,text=True,timeout=12,creationflags=creationflags)
            text=value.lower()
            if "nvidia" in text:
                return "nvidia"
            if "amd" in text or "radeon" in text:
                return "amd"
            if "intel" in text:
                return "intel"
        except Exception:
            pass
        return "unknown"
    def _run_command(self,command,stop_event,on_line):
        env=os.environ.copy()
        env["PYTHONNOUSERSITE"]="1"
        env["PIP_DISABLE_PIP_VERSION_CHECK"]="1"
        env["PIP_NO_INPUT"]="1"
        creationflags=0x08000000 if os.name=="nt" else 0
        with self.lock:
            self.process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",env=env,creationflags=creationflags)
        try:
            while True:
                if stop_event is not None and stop_event.is_set():
                    self.stop()
                    raise InputStopped("下载已由ESC或停止按钮终止")
                line=self.process.stdout.readline() if self.process.stdout is not None else ""
                if line and on_line is not None:
                    on_line(line.rstrip())
                code=self.process.poll()
                if code is not None:
                    if code!=0:
                        raise RuntimeError("命令退出码"+str(code)+"："+" ".join(command[:5]))
                    return
                if not line:
                    time.sleep(0.05)
        finally:
            with self.lock:
                self.process=None
    def run(self,stop_event,on_progress=None,on_line=None):
        package_dir=self.base/"python_packages"
        package_dir.mkdir(parents=True,exist_ok=True)
        python=sys.executable
        steps=[]
        steps.append([python,"-m","ensurepip","--upgrade"])
        steps.append([python,"-m","pip","install","--upgrade","pip","setuptools","wheel","--target",str(package_dir)])
        vendor=self._gpu_vendor()
        common=["numpy","pillow","opencv-python-headless","rapidocr"]
        if vendor=="nvidia":
            common.append("onnxruntime-gpu")
            steps.append([python,"-m","pip","install","--upgrade","--target",str(package_dir),"torch","torchvision","--index-url","https://download.pytorch.org/whl/cu128"])
        else:
            common.append("onnxruntime-directml")
            steps.append([python,"-m","pip","install","--upgrade","--target",str(package_dir),"torch","torchvision"])
            if sys.version_info[:2]<=(3,10):
                steps.append([python,"-m","pip","install","--upgrade","--target",str(package_dir),"torch-directml"])
        steps.insert(2,[python,"-m","pip","install","--upgrade","--target",str(package_dir),*common])
        for index,command in enumerate(steps):
            if on_progress is not None:
                on_progress(index*90/max(1,len(steps)))
            self._run_command(command,stop_event,on_line)
        marker={"completed":time.time(),"python":sys.version,"vendor":vendor,"packages":common,"format":1}
        (self.base/"models"/"runtime_manifest.json").write_text(json.dumps(marker,ensure_ascii=False,sort_keys=True,separators=(",",":")),encoding="utf-8")
        if on_progress is not None:
            on_progress(100)
        return marker
    def stop(self):
        with self.lock:
            process=self.process
        if process is None or process.poll() is not None:
            return
        try:
            if os.name=="nt":
                subprocess.run(["taskkill","/PID",str(process.pid),"/T","/F"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=4)
            else:
                process.terminate()
        except Exception:
            try:
                process.kill()
            except Exception:
                pass
class OfflineVisionRuntime:
    def __init__(self,base):
        self.base=Path(base)
        self.model_dir=self.base/"models"/"vision"
        self.model_dir.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock()
        self.torch=None
        self.np=None
        self.device=None
        self.device_name="unavailable"
        self.model=None
        self.active_game=""
        self.active_path=None
        self.trained_steps=0
        self.ready=False
        self.error="尚未下载AI运行库"
        self._load_runtime()
    def _load_runtime(self):
        try:
            import importlib
            self.np=importlib.import_module("numpy")
            self.torch=importlib.import_module("torch")
            torch=self.torch
            if bool(torch.cuda.is_available()):
                self.device=torch.device("cuda")
                self.device_name=str(torch.cuda.get_device_name(0))
                try:
                    torch.backends.cudnn.benchmark=True
                    torch.backends.cuda.matmul.allow_tf32=True
                    torch.backends.cudnn.allow_tf32=True
                except Exception:
                    pass
            else:
                try:
                    directml=importlib.import_module("torch_directml")
                    self.device=directml.device()
                    self.device_name="DirectML GPU"
                except Exception:
                    self.device=torch.device("cpu")
                    self.device_name="CPU回退"
            self.ready=True
            self.error=""
        except Exception as error:
            self.ready=False
            self.error=str(error)
    def require_ready(self):
        if not self.ready:
            self._load_runtime()
        if not self.ready:
            raise RuntimeError("AI视觉运行库不可用，请先点击“下载”："+self.error)
        return True
    def _build_model(self):
        torch=self.torch
        class Encoder(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.c1=torch.nn.Conv2d(3,24,3,padding=1)
                self.c2=torch.nn.Conv2d(24,32,3,padding=1)
                self.c3=torch.nn.Conv2d(32,32,3,padding=1)
                self.out=torch.nn.Conv2d(32,4,1)
            def forward(self,value):
                value=torch.nn.functional.gelu(self.c1(value))
                value=torch.nn.functional.gelu(self.c2(value))
                value=torch.nn.functional.gelu(self.c3(value))
                return torch.sigmoid(self.out(value))
        return Encoder().to(self.device)
    def _path_for(self,game_id):
        safe=hashlib.sha256(str(game_id).encode("utf-8","replace")).hexdigest()
        return self.model_dir/(safe+".pt")
    def activate_game(self,game_id):
        self.require_ready()
        gid=str(game_id or "default")
        with self.lock:
            if self.active_game==gid and self.model is not None:
                return self.manifest()
            seed=int(hashlib.sha256((gid+"|"+str(VISION_ARCHITECTURE_VERSION)).encode("utf-8")).hexdigest()[:8],16)
            self.torch.manual_seed(seed)
            if bool(getattr(self.torch,"cuda",None)) and self.torch.cuda.is_available():
                self.torch.cuda.manual_seed_all(seed)
            model=self._build_model()
            path=self._path_for(gid)
            steps=0
            if path.exists():
                try:
                    packet=self.torch.load(str(path),map_location="cpu",weights_only=False)
                except TypeError:
                    packet=self.torch.load(str(path),map_location="cpu")
                if isinstance(packet,dict) and int(packet.get("architecture_version",0))==VISION_ARCHITECTURE_VERSION:
                    model.load_state_dict(packet.get("encoder",{}),strict=True)
                    steps=safe_int(packet.get("trained_steps",0),0,0,1000000000)
            else:
                self._atomic_save(path,{"architecture_version":VISION_ARCHITECTURE_VERSION,"encoder":{key:value.detach().cpu() for key,value in model.state_dict().items()},"trained_steps":0,"created":time.time()})
            model.eval()
            self.model=model
            self.active_game=gid
            self.active_path=path
            self.trained_steps=steps
            return self.manifest()
    def _atomic_save(self,path,packet):
        temp=path.with_suffix(path.suffix+"."+uuid.uuid4().hex+".tmp")
        self.torch.save(packet,str(temp))
        os.replace(temp,path)
    def manifest(self):
        checksum=""
        if self.active_path is not None and self.active_path.exists():
            checksum=hashlib.sha256(self.active_path.read_bytes()).hexdigest()
        return {"architecture_version":VISION_ARCHITECTURE_VERSION,"game_id":self.active_game,"checksum":checksum,"trained_steps":self.trained_steps,"device":self.device_name,"relative_path":str(self.active_path.relative_to(self.base)) if self.active_path is not None else ""}
    def _tensor_from_rgb(self,rgb):
        source=rgb_bytes(rgb)
        if source is None:
            raise CaptureUnavailable("AI视觉输入尺寸无效")
        array=self.np.frombuffer(source,dtype=self.np.uint8).reshape(FEATURE_H,FEATURE_W,3).copy()
        tensor=self.torch.from_numpy(array).permute(2,0,1).unsqueeze(0).to(self.device,dtype=self.torch.float32)/255.0
        return tensor
    def encode(self,rgb,previous_rgb=None):
        self.require_ready()
        with self.lock:
            if self.model is None:
                self.activate_game(self.active_game or "default")
            tensor=self._tensor_from_rgb(rgb)
            with self.torch.inference_mode():
                if getattr(self.device,"type","")=="cuda":
                    with self.torch.autocast(device_type="cuda",dtype=self.torch.float16):
                        encoded=self.model(tensor)
                else:
                    encoded=self.model(tensor)
            encoded=(encoded.squeeze(0).clamp(0,1)*255.0).to("cpu",dtype=self.torch.uint8).numpy()
            channels=[bytes(encoded[index].reshape(-1).tolist()) for index in range(4)]
        current=rgb_bytes(rgb)
        previous=rgb_bytes(previous_rgb)
        motion=bytearray(PIXELS)
        if previous is not None:
            for pixel in range(PIXELS):
                offset=pixel*3
                motion[pixel]=(abs(current[offset]-previous[offset])+abs(current[offset+1]-previous[offset+1])+abs(current[offset+2]-previous[offset+2]))//3
        return b"".join(channels)+bytes(motion)
    def encode_gray(self,gray):
        raw=gray_bytes(gray)
        if raw is None:
            raise RuntimeError("灰度样本无效")
        rgb=bytes(value for pixel in raw for value in (pixel,pixel,pixel))
        return self.encode(rgb,None)
    def train(self,game_id,grays,stop_event=None,progress=None):
        self.require_ready()
        valid=[gray_bytes(value) for value in grays if gray_bytes(value) is not None]
        if not valid:
            self.activate_game(game_id)
            return self.manifest()
        with self.lock:
            self.activate_game(game_id)
            torch=self.torch
            encoder=self.model
            class Autoencoder(torch.nn.Module):
                def __init__(self,enc):
                    super().__init__()
                    self.encoder=enc
                    self.decoder=torch.nn.Sequential(torch.nn.Conv2d(4,24,3,padding=1),torch.nn.GELU(),torch.nn.Conv2d(24,16,3,padding=1),torch.nn.GELU(),torch.nn.Conv2d(16,3,1),torch.nn.Sigmoid())
                def forward(self,value):
                    latent=self.encoder(value)
                    return latent,self.decoder(latent)
            model=Autoencoder(encoder).to(self.device)
            model.train()
            optimizer=torch.optim.AdamW(model.parameters(),lr=0.0015,weight_decay=0.0001)
            arrays=self.np.stack([self.np.frombuffer(value,dtype=self.np.uint8).reshape(FEATURE_H,FEATURE_W) for value in valid]).astype(self.np.float32)/255.0
            arrays=self.np.repeat(arrays[:,None,:,:],3,axis=1)
            total_steps=max(24,min(240,len(valid)*3))
            generator=random.Random(int(hashlib.sha256((str(game_id)+"|train").encode()).hexdigest()[:16],16)+self.trained_steps)
            for step in range(total_steps):
                if stop_event is not None and stop_event.is_set():
                    raise InputStopped("GPU离线视觉模型训练已停止")
                indexes=[generator.randrange(len(valid)) for _ in range(min(32,max(4,len(valid))))]
                batch=torch.from_numpy(arrays[indexes].copy()).to(self.device)
                noise=(torch.rand_like(batch)-0.5)*0.08
                noisy=(batch+noise).clamp(0,1)
                latent,reconstruction=model(noisy)
                loss=torch.nn.functional.smooth_l1_loss(reconstruction,batch)+0.02*(latent.var(dim=(2,3)).mean()+0.0001).reciprocal().clamp(max=10)
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(),2.0)
                optimizer.step()
                if progress is not None and step%2==0:
                    progress(35.0*(step+1)/total_steps)
            encoder=model.encoder
            encoder.eval()
            self.model=encoder
            self.trained_steps+=total_steps
            packet={"architecture_version":VISION_ARCHITECTURE_VERSION,"encoder":{key:value.detach().cpu() for key,value in encoder.state_dict().items()},"trained_steps":self.trained_steps,"updated":time.time()}
            self._atomic_save(self.active_path,packet)
            return self.manifest()
class OfflineOCRRuntime:
    def __init__(self,base):
        self.base=Path(base)
        self.lock=threading.RLock()
        self.engine=None
        self.np=None
        self.ready=False
        self.error="尚未下载OCR运行库"
        self._load_runtime()
    def _load_runtime(self):
        try:
            import importlib
            self.np=importlib.import_module("numpy")
            try:
                module=importlib.import_module("rapidocr")
                device_name=str(getattr(CURRENT_VISION_RUNTIME,"device_name",""))
                params={"EngineConfig.onnxruntime.use_cuda":True} if "NVIDIA" in device_name or "CUDA" in device_name.upper() else {"EngineConfig.onnxruntime.use_dml":True} if "DirectML" in device_name else {}
                try:
                    self.engine=module.RapidOCR(params=params) if params else module.RapidOCR()
                except Exception:
                    self.engine=module.RapidOCR()
            except Exception:
                module=importlib.import_module("rapidocr_onnxruntime")
                self.engine=module.RapidOCR()
            self.ready=True
            self.error=""
        except Exception as error:
            self.engine=None
            self.ready=False
            self.error=str(error)
    def require_ready(self):
        if not self.ready:
            self._load_runtime()
        if not self.ready:
            raise RuntimeError("OCR运行库不可用，请先点击“下载”："+self.error)
        return True
    def _array(self,rgb,width,height):
        raw=bytes(rgb)
        if len(raw)!=int(width)*int(height)*3:
            raise RuntimeError("OCR图像尺寸无效")
        return self.np.frombuffer(raw,dtype=self.np.uint8).reshape(int(height),int(width),3).copy()
    def recognize(self,rgb,width,height,region=None):
        self.require_ready()
        image=self._array(rgb,width,height)
        offset_x=0
        offset_y=0
        if region is not None:
            x,y,w,h=region
            x=max(0,min(int(width)-1,int(x))); y=max(0,min(int(height)-1,int(y)))
            w=max(1,min(int(width)-x,int(w))); h=max(1,min(int(height)-y,int(h)))
            image=image[y:y+h,x:x+w]
            offset_x=x
            offset_y=y
        with self.lock:
            output=self.engine(image)
        values=[]
        if hasattr(output,"boxes"):
            records=zip(output.boxes or [],output.txts or [],output.scores or [])
        elif isinstance(output,tuple) and len(output)>=1:
            records=output[0] or []
        else:
            records=output or []
        for item in records:
            try:
                box,text,score=item[:3] if isinstance(item,(list,tuple)) else item
                xs=[float(point[0])+offset_x for point in box]
                ys=[float(point[1])+offset_y for point in box]
                values.append({"box":[min(xs),min(ys),max(xs)-min(xs),max(ys)-min(ys)],"text":str(text),"confidence":max(0.0,min(1.0,float(score)))})
            except Exception:
                continue
        return values
    def recognize_region(self,frame,norm):
        preview=preview_rgb_bytes(frame.get("preview_rgb"))
        width=safe_int(frame.get("preview_width",PREVIEW_W),PREVIEW_W,1,8192)
        height=safe_int(frame.get("preview_height",PREVIEW_H),PREVIEW_H,1,8192)
        if preview is None:
            preview=rgb_bytes(frame.get("rgb"))
            width=FEATURE_W
            height=FEATURE_H
        if preview is None:
            raise RuntimeError("当前帧没有可用OCR图像")
        x=max(0,min(width-1,round(safe_float(norm[0])*width)))
        y=max(0,min(height-1,round(safe_float(norm[1])*height)))
        right=max(x+1,min(width,round((safe_float(norm[0])+safe_float(norm[2]))*width)))
        bottom=max(y+1,min(height,round((safe_float(norm[1])+safe_float(norm[3]))*height)))
        values=self.recognize(preview,width,height,[x,y,right-x,bottom-y])
        text="".join(value["text"] for value in values).strip()
        confidence=sum(value["confidence"] for value in values)/max(1,len(values))
        return {"text":text,"confidence":confidence,"items":values}
    def candidate_regions(self,frame,maximum=8):
        preview=preview_rgb_bytes(frame.get("preview_rgb"))
        width=safe_int(frame.get("preview_width",PREVIEW_W),PREVIEW_W,1,8192)
        height=safe_int(frame.get("preview_height",PREVIEW_H),PREVIEW_H,1,8192)
        if preview is None:
            raise RuntimeError("当前画面没有教学预览")
        regions=[]
        try:
            for item in self.recognize(preview,width,height):
                x,y,w,h=item["box"]
                margin=max(2,int(min(width,height)*0.008))
                x=max(0,x-margin); y=max(0,y-margin); w=min(width-x,w+margin*2); h=min(height-y,h+margin*2)
                if w>=4 and h>=4:
                    regions.append({"norm":[x/width,y/height,w/width,h/height],"score":2.0+item["confidence"],"text":item["text"]})
        except Exception:
            pass
        gray=[]
        for index in range(0,len(preview),3):
            gray.append((preview[index]*77+preview[index+1]*150+preview[index+2]*29)>>8)
        cells=[]
        cell_w=max(8,width//20)
        cell_h=max(6,height//14)
        for y in range(0,height,cell_h):
            for x in range(0,width,cell_w):
                values=[]
                for yy in range(y,min(height,y+cell_h)):
                    start=yy*width+x
                    values.extend(gray[start:start+min(cell_w,width-x)])
                if len(values)<8:
                    continue
                mean=sum(values)/len(values)
                variance=sum((value-mean)*(value-mean) for value in values)/len(values)
                if variance>=650:
                    cells.append([x,y,min(cell_w,width-x),min(cell_h,height-y),variance])
        cells.sort(key=lambda value:value[4],reverse=True)
        for x,y,w,h,score in cells[:maximum*3]:
            norm=[x/width,y/height,w/width,h/height]
            if any(_rect_iou(norm,value["norm"])>0.45 for value in regions):
                continue
            regions.append({"norm":norm,"score":score/1000.0,"text":""})
        regions.sort(key=lambda value:value["score"],reverse=True)
        selected=[]
        for value in regions:
            if any(_rect_iou(value["norm"],old["norm"])>0.65 for old in selected):
                continue
            selected.append(value)
            if len(selected)>=maximum:
                break
        if not selected:
            selected=[{"norm":[0.05,0.05,0.25,0.15],"score":0.0,"text":""},{"norm":[0.7,0.05,0.25,0.15],"score":0.0,"text":""},{"norm":[0.05,0.8,0.25,0.15],"score":0.0,"text":""},{"norm":[0.7,0.8,0.25,0.15],"score":0.0,"text":""}]
        return selected
def _rect_iou(first,second):
    ax,ay,aw,ah=[safe_float(value) for value in first]
    bx,by,bw,bh=[safe_float(value) for value in second]
    left=max(ax,bx); top=max(ay,by); right=min(ax+aw,bx+bw); bottom=min(ay+ah,by+bh)
    intersection=max(0.0,right-left)*max(0.0,bottom-top)
    union=max(1e-9,aw*ah+bw*bh-intersection)
    return intersection/union
def parse_ocr_number(text,number_format="auto"):
    import re
    raw=str(text or "").strip().replace("，",",").replace("％","%").replace("：",":").replace("／","/").replace("−","-").replace("O","0").replace("o","0")
    compact=re.sub(r"\s+","",raw)
    result={"valid":False,"kind":"unknown","value":None,"maximum":None,"seconds":None,"unit":"","normalized":compact}
    if not compact:
        return result
    time_match=re.fullmatch(r"(-?\d+):([0-5]?\d)(?::([0-5]?\d))?",compact)
    if time_match:
        parts=[int(value) for value in time_match.groups() if value is not None]
        seconds=parts[0]*60+parts[1] if len(parts)==2 else parts[0]*3600+parts[1]*60+parts[2]
        result.update({"valid":True,"kind":"time","seconds":float(seconds),"value":float(seconds)})
        return result
    pair=re.search(r"(-?\d+(?:\.\d+)?)[/](-?\d+(?:\.\d+)?)",compact)
    if pair:
        result.update({"valid":True,"kind":"current_max","value":float(pair.group(1)),"maximum":float(pair.group(2))})
        return result
    match=re.search(r"[-+]?\d+(?:[.,]\d+)?",compact)
    if not match:
        return result
    number=float(match.group(0).replace(",","."))
    suffix=compact[match.end():].upper()
    multiplier=1.0
    unit=suffix
    if suffix.startswith("K"):
        multiplier=1000.0; unit="K"
    elif suffix.startswith("M"):
        multiplier=1000000.0; unit="M"
    elif suffix.startswith("B"):
        multiplier=1000000000.0; unit="B"
    value=number*multiplier
    kind="decimal" if "." in match.group(0) or "," in match.group(0) else "integer"
    if "%" in compact:
        kind="percent"
    elif multiplier!=1.0:
        kind="unit"
    elif any(symbol in compact for symbol in ("$","¥","￥","€","£","分")):
        kind="currency_or_score"
    result.update({"valid":True,"kind":kind,"value":value,"unit":unit})
    return result
class OCRSemanticEngine:
    def __init__(self):
        self.previous={}
        self.lock=threading.RLock()
    def evaluate(self,definition,parsed):
        region_id=str(definition.get("id",""))
        event={"terminal":"","progress":0.0,"status":"neutral","reset":"","semantic_version":OCR_SEMANTIC_VERSION}
        if not isinstance(parsed,dict) or not parsed.get("valid"):
            event["status"]="unreadable"
            return event
        current=safe_float(parsed.get("value"),0.0)
        with self.lock:
            previous=self.previous.get(region_id)
            self.previous[region_id]=current
        target_min=definition.get("target_min")
        target_max=definition.get("target_max")
        relation=str(definition.get("goal_relation","uncertain"))
        special=definition.get("special_value")
        if finite_number(special) and abs(current-safe_float(special))<=max(1e-6,abs(safe_float(special))*0.001):
            meaning=str(definition.get("special_meaning","none"))
            if meaning=="success":
                event["terminal"]="success"
            elif meaning=="failure":
                event["terminal"]="failure"
            elif meaning=="next_level":
                event["status"]="next_level"
            elif meaning=="new_round":
                event["reset"]="new_round"
        if previous is not None:
            delta=current-previous
            tolerance=max(1e-6,max(abs(current),abs(previous),1.0)*0.0005)
            if abs(delta)>tolerance:
                if relation in {"higher_better","increase_progress"}:
                    event["progress"]=1.0 if delta>0 else -1.0
                elif relation in {"lower_better","decrease_progress","countdown"}:
                    event["progress"]=1.0 if delta<0 else -1.0
                elif relation=="near_target" and finite_number(target_min):
                    event["progress"]=1.0 if abs(current-safe_float(target_min))<abs(previous-safe_float(target_min)) else -1.0
                elif relation=="in_range" and finite_number(target_min) and finite_number(target_max):
                    low=min(safe_float(target_min),safe_float(target_max)); high=max(safe_float(target_min),safe_float(target_max))
                    before=0.0 if low<=previous<=high else min(abs(previous-low),abs(previous-high))
                    after=0.0 if low<=current<=high else min(abs(current-low),abs(current-high))
                    event["progress"]=1.0 if after<before else -1.0 if after>before else 0.0
            if previous!=0 and abs(current-previous)>max(10.0,abs(previous)*0.65):
                reset=str(definition.get("reset_meaning","uncertain"))
                if reset in {"new_round","level_change","player_failure","cycle","normal"}:
                    event["reset"]=reset
                if reset=="player_failure":
                    event["terminal"]="failure"
        if relation=="in_range" and finite_number(target_min) and finite_number(target_max):
            low=min(safe_float(target_min),safe_float(target_max)); high=max(safe_float(target_min),safe_float(target_max))
            event["status"]="in_range" if low<=current<=high else "out_of_range"
        elif relation=="resource":
            maximum=parsed.get("maximum")
            if finite_number(maximum) and safe_float(maximum)>0:
                ratio=current/safe_float(maximum)
                event["status"]="critical" if ratio<=0.2 else "full" if ratio>=0.95 else "normal"
            else:
                event["status"]="resource"
        elif relation=="countdown":
            event["status"]="countdown"
        return event
OCR_SEMANTIC_ENGINE=OCRSemanticEngine()
class OCRMonitor:
    def __init__(self,app,frame_buffer,purpose):
        self.app=app
        self.frame_buffer=frame_buffer
        self.purpose=str(purpose)
        self.stop_event=threading.Event()
        self.thread=None
        self.last_stamp=0.0
        self.last_saved=defaultdict(float)
    def start(self):
        self.thread=threading.Thread(target=self._run,name="UniversalGameAI-OCR-"+self.purpose,daemon=True)
        self.thread.start()
        return self
    def _run(self):
        try:
            game=self.app.require_game()
            definitions=self.app.store.list_ocr_regions(game["id"],True)
            if not definitions:
                return
            while not self.stop_event.is_set() and not self.app.should_stop():
                frame=self.frame_buffer.latest(None,1.0)
                if frame is None or frame.get("time")==self.last_stamp or not frame.get("capture_valid"):
                    self.stop_event.wait(0.12)
                    continue
                self.last_stamp=frame.get("time")
                for definition in definitions:
                    if self.stop_event.is_set() or self.app.should_stop():
                        break
                    try:
                        recognized=self.app.ocr_runtime.recognize_region(frame,definition["region_norm"])
                        parsed=parse_ocr_number(recognized.get("text"),definition.get("number_format","auto")) if definition.get("region_type")=="number" else {"valid":False}
                        event=OCR_SEMANTIC_ENGINE.evaluate(definition,parsed) if definition.get("region_type")=="number" else {"terminal":"","progress":0.0,"status":"text_only","reset":"","semantic_version":OCR_SEMANTIC_VERSION}
                        SEMANTIC_EVENT_HUB.publish(game["id"],definition["id"],event)
                        now=time.monotonic()
                        if now-self.last_saved[definition["id"]]>=0.8:
                            self.last_saved[definition["id"]]=now
                            self.app.store.append_ocr_observation(game["id"],definition["id"],recognized.get("text",""),parsed,recognized.get("confidence",0.0),1,event)
                    except Exception as error:
                        self.app.store.log_error("OCR_MONITOR_FRAME_FAILED",error,mode=self.app.mode,game_id=game["id"])
                self.stop_event.wait(0.18 if self.purpose=="training" else 0.3)
        finally:
            self.app.store.close_current_thread()
    def stop(self,timeout=1.0):
        self.stop_event.set()
        if self.thread and self.thread.is_alive() and self.thread is not threading.current_thread() and timeout>0:
            self.thread.join(max(0.0,float(timeout)))
        return not bool(self.thread and self.thread.is_alive())
    def alive(self):
        return bool(self.thread and self.thread.is_alive())
class ScreenNumericKeypad:
    def __init__(self,parent,title,initial=""):
        self.value=tk.StringVar(value=str(initial))
        self.frame=ttk.LabelFrame(parent,text=title,padding=8)
        self.entry=ttk.Entry(self.frame,textvariable=self.value,state="readonly",justify="right",font=("Consolas",14))
        self.entry.grid(row=0,column=0,columnspan=4,sticky="ew",pady=(0,6))
        keys=[("7","7"),("8","8"),("9","9"),("←","back"),("4","4"),("5","5"),("6","6"),("清空","clear"),("1","1"),("2","2"),("3","3"),("-","-"),("0","0"),(".","."),("K","K"),("M","M")]
        for index,(label,token) in enumerate(keys):
            ttk.Button(self.frame,text=label,command=lambda token=token:self.press(token)).grid(row=1+index//4,column=index%4,sticky="nsew",padx=2,pady=2,ipady=4)
        for column in range(4):
            self.frame.columnconfigure(column,weight=1)
    def press(self,token):
        text=self.value.get()
        if token=="back":
            self.value.set(text[:-1])
        elif token=="clear":
            self.value.set("")
        elif len(text)<32:
            self.value.set(text+token)
    def get_number(self):
        parsed=parse_ocr_number(self.value.get())
        if not parsed.get("valid"):
            raise ValueError("请输入有效数字")
        return parsed.get("value")
class OCRTeachingDialog:
    TYPE_CHOICES=[("A","数字","number"),("B","普通文字","text"),("C","图标或状态","icon"),("D","游戏画面内容","game_content"),("E","无意义区域","meaningless"),("F","不确定","uncertain")]
    FORMAT_CHOICES=[("A","整数","integer"),("B","小数","decimal"),("C","百分比","percent"),("D","时间","time"),("E","当前值/最大值，例如35/100","current_max"),("F","带单位，例如1.5K、2M","unit"),("G","货币或分数","currency_or_score"),("H","自动判断","auto")]
    RELATION_CHOICES=[("A","越高越好","higher_better"),("B","越低越好","lower_better"),("C","越接近指定值越好","near_target"),("D","保持在指定范围内最好","in_range"),("E","增加代表取得进展","increase_progress"),("F","减少代表取得进展","decrease_progress"),("G","只用于判断状态，不直接计算奖励","status_only"),("H","表示倒计时","countdown"),("I","表示生命、次数或资源","resource"),("J","不确定","uncertain")]
    SPECIAL_CHOICES=[("A","游戏成功","success"),("B","游戏失败","failure"),("C","进入下一关","next_level"),("D","新一局开始","new_round"),("E","没有特殊含义","none"),("F","不确定","uncertain")]
    RESET_CHOICES=[("A","新一局开始","new_round"),("B","关卡切换","level_change"),("C","玩家失败","player_failure"),("D","数值循环或溢出","cycle"),("E","正常变化","normal"),("F","不确定","uncertain")]
    CONFIRM_CHOICES=[("A","识别正确","correct"),("B","数字正确但含义错误","meaning_wrong"),("C","识别错误","recognition_wrong"),("D","当前画面无法判断","cannot_judge"),("E","删除此区域","delete")]
    def __init__(self,app,parent,game,buffer,frame,on_close=None):
        self.app=app
        self.parent=parent
        self.game=game
        self.buffer=buffer
        self.frame=frame
        self.on_close=on_close
        self.win=tk.Toplevel(parent)
        self.win.title("请教：OCR与数字语义")
        self.win.geometry("820x820")
        self.win.minsize(760,720)
        self.win.transient(parent)
        self.win.grab_set()
        self.win.protocol("WM_DELETE_WINDOW",self.cancel)
        self.win.bind("<Escape>",lambda event:self.app.close_ask(reason="stopped"))
        self.outer=ttk.Frame(self.win,padding=12)
        self.outer.pack(fill="both",expand=True)
        self.title=tk.StringVar(value="系统正在提出候选区域")
        ttk.Label(self.outer,textvariable=self.title,font=("Microsoft YaHei UI",14,"bold")).pack(anchor="w")
        self.info=tk.StringVar(value="正在执行离线OCR与画面变化分析")
        ttk.Label(self.outer,textvariable=self.info,wraplength=780).pack(anchor="w",fill="x",pady=(4,8))
        self.canvas=tk.Canvas(self.outer,width=ASK_CANVAS_W,height=ASK_CANVAS_H,bg="black",highlightthickness=1,highlightbackground="#777777")
        self.canvas.pack()
        self.question=ttk.Frame(self.outer)
        self.question.pack(fill="both",expand=True,pady=(10,0))
        self.state={"region":None,"region_type":"","number_format":"auto","goal_relation":"uncertain","target_min":None,"target_max":None,"special_value":None,"special_meaning":"uncertain","reset_meaning":"uncertain","recognized":{"text":"","confidence":0.0},"consistent":0,"corrected":None}
        self.candidates=[]
        self.images=[]
        self.closed=False
        self._render_image()
        threading.Thread(target=self._load_candidates,name="UniversalGameAI-OCR-Teach-Candidates",daemon=True).start()
    def _render_image(self):
        preview=preview_rgb_bytes(self.frame.get("preview_rgb")) or bytes(PREVIEW_W*PREVIEW_H*3)
        ppm=b"P6\n"+str(PREVIEW_W).encode("ascii")+b" "+str(PREVIEW_H).encode("ascii")+b"\n255\n"+preview
        image=tk.PhotoImage(data=base64.b64encode(ppm).decode("ascii"),format="PPM")
        scaled=image.zoom(2,2)
        self.images=[image,scaled]
        self.canvas.delete("all")
        self.canvas.create_image(ASK_PREVIEW_X,ASK_PREVIEW_Y,image=scaled,anchor="nw")
    def _load_candidates(self):
        try:
            candidates=self.app.ocr_runtime.candidate_regions(self.frame,8)
            self.app.ui(lambda:self._show_candidates(candidates))
        except Exception as error:
            self.app.ui(lambda error=error:self._fail(str(error)))
    def _fail(self,message):
        if not self.closed:
            self.info.set("OCR候选区域生成失败："+str(message))
    def _show_candidates(self,candidates):
        if self.closed:
            return
        self.candidates=list(candidates)
        self._render_image()
        colors=("#00ffff","#ffff00","#ff66ff","#66ff66","#ff9955","#55aaff","#ffffff","#ff5555")
        for index,item in enumerate(self.candidates):
            x,y,w,h=item["norm"]
            left=ASK_PREVIEW_X+x*ASK_PREVIEW_W
            top=ASK_PREVIEW_Y+y*ASK_PREVIEW_H
            right=left+w*ASK_PREVIEW_W
            bottom=top+h*ASK_PREVIEW_H
            color=colors[index%len(colors)]
            self.canvas.create_rectangle(left,top,right,bottom,outline=color,width=3,tags=("region"+str(index),))
            self.canvas.create_text(left+4,top+4,text="区域"+str(index+1),fill=color,font=("Microsoft YaHei UI",11,"bold"),anchor="nw")
        self.title.set("第一步：系统提出候选区域")
        self.info.set("请用鼠标点击一个编号框。无需键盘输入。")
        self.canvas.bind("<Button-1>",self._select_region)
    def _select_region(self,event):
        px=(event.x-ASK_PREVIEW_X)/ASK_PREVIEW_W
        py=(event.y-ASK_PREVIEW_Y)/ASK_PREVIEW_H
        matches=[]
        for index,item in enumerate(self.candidates):
            x,y,w,h=item["norm"]
            if x<=px<=x+w and y<=py<=y+h:
                matches.append((w*h,index,item))
        if not matches:
            self.info.set("请点击编号框内部。")
            return
        _,index,item=min(matches,key=lambda value:value[0])
        self.state["region"]=list(item["norm"])
        self.canvas.unbind("<Button-1>")
        self._show_choices("第二步：询问区域类型","这个区域表示什么？",self.TYPE_CHOICES,self._type_selected)
    def _clear_question(self):
        for child in self.question.winfo_children():
            child.destroy()
    def _show_choices(self,title,prompt,choices,callback):
        if self.closed:
            return
        self._clear_question()
        self.title.set(title)
        ttk.Label(self.question,text=prompt,font=("Microsoft YaHei UI",12,"bold"),wraplength=760).pack(anchor="w",pady=(0,6))
        for letter,label,value in choices:
            ttk.Button(self.question,text=letter+". "+label,command=lambda value=value:callback(value)).pack(fill="x",pady=2,ipady=4)
    def _type_selected(self,value):
        self.state["region_type"]=value
        if value!="number":
            self._save_non_number()
            return
        self._show_choices("第三步：数字格式","这个数字的格式是：",self.FORMAT_CHOICES,self._format_selected)
    def _save_non_number(self):
        payload=dict(self.state)
        payload["region_norm"]=payload.pop("region")
        payload["recognized_text"]=""
        self.app.store.save_ocr_region(self.game["id"],payload)
        self.app.ask_counts["ocr"]=safe_int(self.app.ask_counts.get("ocr",0),0)+1
        self.info.set("区域类型已保存。普通文字、图标和游戏画面内容不会自动提升任何鼠标动作授权等级。")
        self._finish_buttons()
    def _format_selected(self,value):
        self.state["number_format"]=value
        self._show_choices("第四步：数字含义","这个数字与游戏目标的关系是：",self.RELATION_CHOICES,self._relation_selected)
    def _relation_selected(self,value):
        self.state["goal_relation"]=value
        if value in {"near_target","in_range"}:
            self._target_input(value)
        else:
            self._show_choices("第五步：终局含义","这个数字达到特殊值时通常代表什么？",self.SPECIAL_CHOICES,self._special_selected)
    def _target_input(self,relation):
        self._clear_question()
        self.title.set("第四步：目标值或范围")
        ttk.Label(self.question,text="只能点击屏幕数字键盘；这些按钮只产生Tkinter控件事件，不会产生系统键盘注入。",wraplength=760).pack(anchor="w")
        first=ScreenNumericKeypad(self.question,"目标值" if relation=="near_target" else "范围下限")
        first.frame.pack(fill="x",pady=6)
        second=None
        if relation=="in_range":
            second=ScreenNumericKeypad(self.question,"范围上限")
            second.frame.pack(fill="x",pady=6)
        error=tk.StringVar()
        ttk.Label(self.question,textvariable=error).pack(anchor="w")
        def submit():
            try:
                self.state["target_min"]=first.get_number()
                self.state["target_max"]=second.get_number() if second is not None else first.get_number()
                self._show_choices("第五步：终局含义","这个数字达到特殊值时通常代表什么？",self.SPECIAL_CHOICES,self._special_selected)
            except Exception as value:
                error.set(str(value))
        ttk.Button(self.question,text="确认目标值",command=submit).pack(fill="x",pady=6,ipady=5)
    def _special_selected(self,value):
        self.state["special_meaning"]=value
        if value in {"success","failure","next_level","new_round"}:
            self._special_value_input()
        else:
            self._show_choices("第六步：复位语义","数字突然回到初始值通常表示：",self.RESET_CHOICES,self._reset_selected)
    def _special_value_input(self):
        self._clear_question()
        self.title.set("第五步：特殊值")
        ttk.Label(self.question,text="请输入触发该终局含义的特殊值。只允许使用屏幕数字键盘。",wraplength=760).pack(anchor="w")
        keypad=ScreenNumericKeypad(self.question,"特殊值")
        keypad.frame.pack(fill="x",pady=6)
        error=tk.StringVar()
        ttk.Label(self.question,textvariable=error).pack(anchor="w")
        def submit():
            try:
                self.state["special_value"]=keypad.get_number()
                self._show_choices("第六步：复位语义","数字突然回到初始值通常表示：",self.RESET_CHOICES,self._reset_selected)
            except Exception as value:
                error.set(str(value))
        ttk.Button(self.question,text="确认特殊值",command=submit).pack(fill="x",pady=6,ipady=5)
    def _reset_selected(self,value):
        self.state["reset_meaning"]=value
        self._clear_question()
        self.title.set("第七步：确认OCR")
        ttk.Label(self.question,text="正在对同一区域执行连续帧离线OCR。",wraplength=760).pack(anchor="w")
        threading.Thread(target=self._recognize_consistency,name="UniversalGameAI-OCR-Teach-Confirm",daemon=True).start()
    def _recognize_consistency(self):
        try:
            frames=[value for value in self.buffer.snapshot(2.5) if value.get("preview_rgb")][-4:]
            if not frames:
                frames=[self.frame]
            results=[self.app.ocr_runtime.recognize_region(value,self.state["region"]) for value in frames]
            texts=[value.get("text","").strip() for value in results]
            best=Counter(texts).most_common(1)[0][0] if texts else ""
            consistent=sum(1 for value in texts if value==best and value!="")
            selected=next((value for value in reversed(results) if value.get("text","").strip()==best),results[-1] if results else {"text":"","confidence":0.0})
            confidence=sum(value.get("confidence",0.0) for value in results if value.get("text","").strip()==best)/max(1,consistent)
            recognized={"text":best or selected.get("text",""),"confidence":confidence}
            self.app.ui(lambda:self._show_confirmation(recognized,consistent))
        except Exception as error:
            self.app.ui(lambda error=error:self._show_confirmation({"text":"","confidence":0.0,"error":str(error)},0))
    def _show_confirmation(self,recognized,consistent):
        if self.closed:
            return
        self.state["recognized"]=recognized
        self.state["consistent"]=consistent
        self._clear_question()
        self.title.set("第七步：确认OCR")
        text=recognized.get("text","")
        confidence=safe_float(recognized.get("confidence"),0.0)*100.0
        ttk.Label(self.question,text="识别内容："+text+"\n置信度："+str(round(confidence,1))+"%\n连续一致："+str(consistent)+"帧",font=("Microsoft YaHei UI",13,"bold"),justify="left").pack(anchor="w",pady=(0,8))
        if recognized.get("error"):
            ttk.Label(self.question,text="OCR错误："+recognized["error"],wraplength=760).pack(anchor="w")
        for letter,label,value in self.CONFIRM_CHOICES:
            ttk.Button(self.question,text=letter+". "+label,command=lambda value=value:self._confirm_selected(value)).pack(fill="x",pady=2,ipady=4)
    def _confirm_selected(self,value):
        if value=="meaning_wrong":
            self._show_choices("第四步：数字含义","请重新选择这个数字与游戏目标的关系：",self.RELATION_CHOICES,self._relation_selected)
            return
        if value=="recognition_wrong":
            self._correct_recognition()
            return
        if value=="cannot_judge":
            self.info.set("本次未保存；请在画面可判断时重新进入OCR请教。")
            self._finish_buttons()
            return
        if value=="delete":
            self.app.store.delete_ocr_region_by_overlap(self.game["id"],self.state["region"])
            self.info.set("此区域的已保存OCR定义已删除。")
            self._finish_buttons()
            return
        self._save_number()
    def _correct_recognition(self):
        self._clear_question()
        self.title.set("第七步：修正OCR数字")
        ttk.Label(self.question,text="请使用屏幕数字键盘输入正确数字。不会产生系统键盘注入。",wraplength=760).pack(anchor="w")
        keypad=ScreenNumericKeypad(self.question,"正确数字",self.state["recognized"].get("text",""))
        keypad.frame.pack(fill="x",pady=6)
        error=tk.StringVar()
        ttk.Label(self.question,textvariable=error).pack(anchor="w")
        def submit():
            parsed=parse_ocr_number(keypad.value.get(),self.state.get("number_format","auto"))
            if not parsed.get("valid"):
                error.set("请输入可解析数字")
                return
            self.state["corrected"]=keypad.value.get()
            self._save_number()
        ttk.Button(self.question,text="确认修正",command=submit).pack(fill="x",pady=6,ipady=5)
    def _save_number(self):
        text=self.state.get("corrected") or self.state["recognized"].get("text","")
        parsed=parse_ocr_number(text,self.state.get("number_format","auto"))
        if not parsed.get("valid"):
            self.info.set("识别内容不是有效数字，请选择“识别错误”并修正。")
            return
        payload=dict(self.state)
        payload["region_norm"]=payload.pop("region")
        payload["recognized_text"]=text
        payload["last_value"]=parsed.get("value")
        payload["confidence"]=self.state["recognized"].get("confidence",0.0)
        payload["stable_frames"]=self.state.get("consistent",0)
        region=self.app.store.save_ocr_region(self.game["id"],payload)
        event=OCR_SEMANTIC_ENGINE.evaluate(region,parsed)
        self.app.store.append_ocr_observation(self.game["id"],region["id"],text,parsed,payload["confidence"],payload["stable_frames"],event)
        SEMANTIC_EVENT_HUB.publish(self.game["id"],region["id"],event)
        self.app.ask_counts["ocr"]=safe_int(self.app.ask_counts.get("ocr",0),0)+1
        self.info.set("OCR数字语义已保存。奖励系统只接收离散语义事件，不接收OCR原始值；OCR文字不会改变动作授权等级。")
        self._finish_buttons()
    def _finish_buttons(self):
        self._clear_question()
        ttk.Button(self.question,text="继续动作请教",command=self.cancel).pack(fill="x",pady=6,ipady=5)
        ttk.Button(self.question,text="结束请教",command=lambda:self.app.close_ask(reason="completed")).pack(fill="x",pady=6,ipady=5)
    def cancel(self):
        if self.closed:
            return
        self.closed=True
        try:
            self.win.grab_release()
        except Exception:
            pass
        try:
            self.win.destroy()
        except Exception:
            pass
        if self.on_close is not None:
            try:
                self.on_close()
            except Exception:
                pass
_original_datastore_init=DataStore.__init__
def _enhanced_datastore_init(self,base=None):
    selected=base if base is not None else SELECTED_DATA_DIR
    _original_datastore_init(self,selected)
DataStore.__init__=_enhanced_datastore_init
_original_initialize_schema=DataStore._initialize_schema
def _enhanced_initialize_schema(self):
    _original_initialize_schema(self)
    with self.lock,self.db:
        self.db.execute("CREATE TABLE IF NOT EXISTS ocr_regions(id TEXT PRIMARY KEY,game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,created REAL NOT NULL,updated REAL NOT NULL,region_norm TEXT NOT NULL,region_type TEXT NOT NULL,number_format TEXT NOT NULL,goal_relation TEXT NOT NULL,target_min REAL,target_max REAL,special_value REAL,special_meaning TEXT NOT NULL,reset_meaning TEXT NOT NULL,unit TEXT NOT NULL,enabled INTEGER NOT NULL DEFAULT 1,last_text TEXT NOT NULL,last_value REAL,last_confidence REAL NOT NULL DEFAULT 0,stable_frames INTEGER NOT NULL DEFAULT 0,checksum TEXT NOT NULL)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_ocr_regions_game_enabled ON ocr_regions(game_id,enabled,updated DESC)")
        self.db.execute("CREATE TABLE IF NOT EXISTS ocr_observations(id INTEGER PRIMARY KEY AUTOINCREMENT,game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,region_id TEXT NOT NULL REFERENCES ocr_regions(id) ON DELETE CASCADE,created REAL NOT NULL,raw_text TEXT NOT NULL,parsed TEXT NOT NULL,confidence REAL NOT NULL,stable_frames INTEGER NOT NULL,semantic_event TEXT NOT NULL,checksum TEXT NOT NULL)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_ocr_observations_region_created ON ocr_observations(region_id,created DESC)")
        self.db.execute("CREATE TABLE IF NOT EXISTS vision_models(game_id TEXT PRIMARY KEY REFERENCES games(id) ON DELETE CASCADE,architecture_version INTEGER NOT NULL,updated REAL NOT NULL,relative_path TEXT NOT NULL,checksum TEXT NOT NULL,trained_steps INTEGER NOT NULL,device TEXT NOT NULL,metadata TEXT NOT NULL)")
        self.db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('extension_schema_version',?)",(str(EXTENSION_SCHEMA_VERSION),))
DataStore._initialize_schema=_enhanced_initialize_schema
def _save_ocr_region(self,gid,payload):
    self._ensure_writable()
    value=dict(payload) if isinstance(payload,dict) else {}
    norm=value.get("region_norm")
    if not isinstance(norm,(list,tuple)) or len(norm)!=4:
        raise ValueError("OCR区域坐标无效")
    norm=[round(max(0.0,min(1.0,safe_float(item))),8) for item in norm]
    if norm[2]<=0 or norm[3]<=0 or norm[0]+norm[2]>1.000001 or norm[1]+norm[3]>1.000001:
        raise ValueError("OCR区域必须位于确认内容区域内")
    existing=None
    for item in self.list_ocr_regions(gid,False):
        if _rect_iou(item["region_norm"],norm)>=0.82:
            existing=item
            break
    region_id=str(existing.get("id")) if existing else uuid.uuid4().hex
    created=safe_float(existing.get("created"),time.time()) if existing else time.time()
    now=time.time()
    row={"id":region_id,"game_id":str(gid),"created":created,"updated":now,"region_norm":norm,"region_type":str(value.get("region_type","uncertain")),"number_format":str(value.get("number_format","auto")),"goal_relation":str(value.get("goal_relation","uncertain")),"target_min":safe_float(value.get("target_min")) if finite_number(value.get("target_min")) else None,"target_max":safe_float(value.get("target_max")) if finite_number(value.get("target_max")) else None,"special_value":safe_float(value.get("special_value")) if finite_number(value.get("special_value")) else None,"special_meaning":str(value.get("special_meaning","uncertain")),"reset_meaning":str(value.get("reset_meaning","uncertain")),"unit":str(value.get("unit","")),"enabled":1,"last_text":str(value.get("recognized_text",value.get("last_text","")))[:256],"last_value":safe_float(value.get("last_value")) if finite_number(value.get("last_value")) else None,"last_confidence":safe_float(value.get("confidence",0.0),0.0,0.0,1.0),"stable_frames":safe_int(value.get("stable_frames",0),0,0,1000)}
    checksum=hashlib.sha256(canonical_bytes(row)).hexdigest()
    with self.lock,self.db:
        self.db.execute("INSERT OR REPLACE INTO ocr_regions(id,game_id,created,updated,region_norm,region_type,number_format,goal_relation,target_min,target_max,special_value,special_meaning,reset_meaning,unit,enabled,last_text,last_value,last_confidence,stable_frames,checksum) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(row["id"],row["game_id"],row["created"],row["updated"],json.dumps(norm,separators=(",",":")),row["region_type"],row["number_format"],row["goal_relation"],row["target_min"],row["target_max"],row["special_value"],row["special_meaning"],row["reset_meaning"],row["unit"],row["enabled"],row["last_text"],row["last_value"],row["last_confidence"],row["stable_frames"],checksum))
        self.db.execute("UPDATE games SET needs_review=1 WHERE id=?",(str(gid),))
    row["checksum"]=checksum
    return row
DataStore.save_ocr_region=_save_ocr_region
def _list_ocr_regions(self,gid,enabled_only=True):
    query="SELECT * FROM ocr_regions WHERE game_id=?"+(" AND enabled=1" if enabled_only else "")+" ORDER BY updated DESC"
    with self.lock:
        rows=self.db.execute(query,(str(gid),)).fetchall()
    result=[]
    for row in rows:
        try:
            item=dict(row)
            item["region_norm"]=json.loads(item["region_norm"])
            verification={key:item[key] for key in ("id","game_id","created","updated","region_norm","region_type","number_format","goal_relation","target_min","target_max","special_value","special_meaning","reset_meaning","unit","enabled","last_text","last_value","last_confidence","stable_frames")}
            if hashlib.sha256(canonical_bytes(verification)).hexdigest()!=str(item.get("checksum","")):
                continue
            result.append(item)
        except Exception:
            continue
    return result
DataStore.list_ocr_regions=_list_ocr_regions
def _delete_ocr_region_by_overlap(self,gid,norm):
    removed=0
    with self.lock,self.db:
        rows=self.db.execute("SELECT id,region_norm FROM ocr_regions WHERE game_id=?",(str(gid),)).fetchall()
        ids=[]
        for row in rows:
            try:
                if _rect_iou(json.loads(row["region_norm"]),norm)>=0.45:
                    ids.append(str(row["id"]))
            except Exception:
                pass
        for region_id in ids:
            removed+=max(0,int(self.db.execute("DELETE FROM ocr_regions WHERE id=?",(region_id,)).rowcount or 0))
        if removed:
            self.db.execute("UPDATE games SET needs_review=1 WHERE id=?",(str(gid),))
    return removed
DataStore.delete_ocr_region_by_overlap=_delete_ocr_region_by_overlap
def _append_ocr_observation(self,gid,region_id,raw_text,parsed,confidence,stable_frames,event):
    value={"game_id":str(gid),"region_id":str(region_id),"created":time.time(),"raw_text":str(raw_text)[:256],"parsed":parsed if isinstance(parsed,dict) else {},"confidence":safe_float(confidence,0.0,0.0,1.0),"stable_frames":safe_int(stable_frames,0,0,1000),"semantic_event":event if isinstance(event,dict) else {}}
    checksum=hashlib.sha256(canonical_bytes(value)).hexdigest()
    with self.lock,self.db:
        self.db.execute("INSERT INTO ocr_observations(game_id,region_id,created,raw_text,parsed,confidence,stable_frames,semantic_event,checksum) VALUES(?,?,?,?,?,?,?,?,?)",(value["game_id"],value["region_id"],value["created"],value["raw_text"],json.dumps(value["parsed"],ensure_ascii=False,sort_keys=True,separators=(",",":")),value["confidence"],value["stable_frames"],json.dumps(value["semantic_event"],ensure_ascii=False,sort_keys=True,separators=(",",":")),checksum))
        self.db.execute("DELETE FROM ocr_observations WHERE id IN (SELECT id FROM ocr_observations WHERE game_id=? ORDER BY created DESC LIMIT -1 OFFSET 20000)",(str(gid),))
    return True
DataStore.append_ocr_observation=_append_ocr_observation
def _record_vision_model(self,gid,manifest):
    value=dict(manifest) if isinstance(manifest,dict) else {}
    metadata=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    with self.lock,self.db:
        self.db.execute("INSERT OR REPLACE INTO vision_models(game_id,architecture_version,updated,relative_path,checksum,trained_steps,device,metadata) VALUES(?,?,?,?,?,?,?,?)",(str(gid),safe_int(value.get("architecture_version"),0),time.time(),str(value.get("relative_path","")),str(value.get("checksum","")),safe_int(value.get("trained_steps"),0),str(value.get("device","")),metadata))
    return True
DataStore.record_vision_model=_record_vision_model
def _reencode_samples(self,gid,runtime,stop_event=None,progress=None):
    self.sample_write_barrier()
    with self.lock:
        rows=self.db.execute("SELECT id,thumbnail,action,context FROM samples WHERE game_id=? ORDER BY created,id",(str(gid),)).fetchall()
    prepared=[]
    manifest=runtime.manifest()
    total=len(rows)
    for index,row in enumerate(rows):
        if stop_event is not None and stop_event.is_set():
            raise InputStopped("样本AI特征升级已停止")
        if row["thumbnail"] is None:
            continue
        try:
            gray=bounded_decompress(row["thumbnail"],PIXELS*2)
            feature=runtime.encode_gray(gray)
            action=json.loads(row["action"])
            context=json.loads(row["context"])
            context["vision_architecture_version"]=VISION_ARCHITECTURE_VERSION
            context["vision_model_checksum"]=manifest.get("checksum","")
            fingerprint=self._sample_fingerprint(feature,action,context)
            prepared.append((int(row["id"]),feature,coarse_feature(feature),json.dumps(context,ensure_ascii=False,separators=(",",":")),fingerprint))
        except Exception as error:
            self.logger.write("VISION_REENCODE_SAMPLE_FAILED",error,game_id=gid,details={"sample_id":int(row["id"])})
        if progress is not None and index%8==0:
            progress(35.0+25.0*(index+1)/max(1,total))
    unique={}
    for item in reversed(prepared):
        unique.setdefault(item[4],item)
    keep={item[0] for item in unique.values()}
    all_ids={int(row["id"]) for row in rows}
    with self.critical_transaction():
        for sample_id in sorted(all_ids-keep):
            self.db.execute("DELETE FROM samples WHERE id=?",(sample_id,))
        for sample_id,feature,coarse,context,fingerprint in unique.values():
            self.db.execute("UPDATE samples SET feature_algorithm_version=?,feature=?,coarse=?,context=?,fingerprint=? WHERE id=?",(FEATURE_ALGORITHM_VERSION,sqlite3.Binary(zlib.compress(feature,6)),sqlite3.Binary(coarse),context,fingerprint,sample_id))
        self.db.execute("UPDATE games SET needs_review=1 WHERE id=?",(str(gid),))
    self.model_cache.pop(str(gid),None)
    return {"updated":len(unique),"removed":len(all_ids-keep),"manifest":manifest}
DataStore.reencode_samples=_reencode_samples
_original_bridge_feature_from_rgb=WinBridge.feature_from_rgb
def _ai_feature_from_rgb(self,rgb,previous_rgb=None):
    runtime=getattr(self,"ai_runtime",None)
    if runtime is not None and runtime.ready and runtime.active_game:
        return runtime.encode(rgb,previous_rgb)
    return _original_bridge_feature_from_rgb(self,rgb,previous_rgb)
WinBridge.feature_from_rgb=_ai_feature_from_rgb
_original_mode_start_frames=ModeSession.start_frames
def _enhanced_start_frames(self,hz,seconds,motion_interval,purpose):
    buffer=_original_mode_start_frames(self,hz,seconds,motion_interval,purpose)
    try:
        game=self.app.require_game()
        if getattr(self.app,"ocr_runtime",None) is not None and self.app.ocr_runtime.ready and self.app.store.list_ocr_regions(game["id"],True):
            monitor=OCRMonitor(self.app,buffer,purpose).start()
            self.add_resource("OCRMonitor",monitor)
            self.app.active_ocr_monitor=monitor
    except Exception as error:
        self.app.store.log_error("OCR_MONITOR_START_FAILED",error,mode=self.app.mode)
    return buffer
ModeSession.start_frames=_enhanced_start_frames
_original_task_policy_init=TaskAgentPolicy.__init__
def _enhanced_task_policy_init(self,profile):
    _original_task_policy_init(self,profile)
    self.game_id=str(profile.get("game_id","")) if isinstance(profile,dict) else ""
TaskAgentPolicy.__init__=_enhanced_task_policy_init
_original_task_policy_classify=TaskAgentPolicy.classify
def _semantic_task_policy_classify(self,feature):
    state,reward=_original_task_policy_classify(self,feature)
    if state!="neutral":
        return state,reward
    event=SEMANTIC_EVENT_HUB.latest(self.game_id or None,1.5)
    if not event:
        return state,reward
    if event.get("terminal")=="success":
        return "success",1.0
    if event.get("terminal")=="failure":
        return "failure",-1.0
    semantic_reward=max(-0.25,min(0.25,safe_float(event.get("progress"),0.0)*0.25))
    return "neutral",semantic_reward
TaskAgentPolicy.classify=_semantic_task_policy_classify
_original_load_game_profile=DataStore.load_game_profile
def _enhanced_load_game_profile(self,gid):
    profile=_original_load_game_profile(self,gid)
    profile["game_id"]=str(gid)
    return profile
DataStore.load_game_profile=_enhanced_load_game_profile
_original_save_model=DataStore.save_model
def _enhanced_save_model(self,gid,model,complete=True):
    value=dict(model) if isinstance(model,dict) else {}
    runtime=CURRENT_VISION_RUNTIME
    if runtime is not None and runtime.ready:
        try:
            runtime.activate_game(gid)
            manifest=runtime.manifest()
            value["vision_model_manifest"]=manifest
            self.record_vision_model(gid,manifest)
        except Exception as error:
            self.logger.write("VISION_MODEL_BIND_FAILED",error,game_id=gid)
    value["ocr_semantic_version"]=OCR_SEMANTIC_VERSION
    value["ocr_regions_checksum"]=hashlib.sha256(canonical_bytes([{key:item.get(key) for key in ("id","region_norm","region_type","number_format","goal_relation","target_min","target_max","special_value","special_meaning","reset_meaning","checksum")} for item in self.list_ocr_regions(gid,True)])).hexdigest()
    return _original_save_model(self,gid,value,complete)
DataStore.save_model=_enhanced_save_model
_original_validate_model_binding=App.validate_model_binding
def _enhanced_validate_model_binding(self,model,target):
    result=_original_validate_model_binding(self,model,target)
    if not hasattr(self,"vision_runtime") or not hasattr(self,"ocr_runtime"):
        return result
    self.require_ai_runtime()
    manifest=self.vision_runtime.manifest()
    stored=model.get("vision_model_manifest") if isinstance(model,dict) else None
    if not isinstance(stored,dict) or str(stored.get("checksum",""))!=str(manifest.get("checksum","")) or safe_int(stored.get("architecture_version"),0)!=VISION_ARCHITECTURE_VERSION:
        raise RuntimeError("离线AI视觉模型版本或权重已变化，请重新复习")
    current_ocr=hashlib.sha256(canonical_bytes([{key:item.get(key) for key in ("id","region_norm","region_type","number_format","goal_relation","target_min","target_max","special_value","special_meaning","reset_meaning","checksum")} for item in self.store.list_ocr_regions(self.require_game()["id"],True)])).hexdigest()
    if str(model.get("ocr_regions_checksum",""))!=current_ocr or safe_int(model.get("ocr_semantic_version",0),0)!=OCR_SEMANTIC_VERSION:
        raise RuntimeError("OCR区域或数字语义已变化，请重新复习")
    return result
App.validate_model_binding=_enhanced_validate_model_binding
_original_app_init=App.__init__
def _enhanced_app_init(self,root):
    global CURRENT_VISION_RUNTIME,CURRENT_OCR_RUNTIME
    _original_app_init(self,root)
    self.data_directory=Path(self.store.base)
    self.runtime_installer=RuntimeInstaller(self.data_directory)
    self.vision_runtime=OfflineVisionRuntime(self.data_directory)
    CURRENT_VISION_RUNTIME=self.vision_runtime
    self.ocr_runtime=OfflineOCRRuntime(self.data_directory)
    CURRENT_OCR_RUNTIME=self.ocr_runtime
    self.api.ai_runtime=self.vision_runtime
    self.active_ocr_monitor=None
    if self.selected_game and self.vision_runtime.ready:
        try:
            self.vision_runtime.activate_game(self.selected_game["id"])
        except Exception as error:
            self.store.log_error("VISION_ACTIVATE_STARTUP_FAILED",error,game_id=self.selected_game.get("id",""))
    self._update_runtime_status()
App.__init__=_enhanced_app_init
_original_app_build=App._build
def _enhanced_app_build(self):
    _original_app_build(self)
    outer=self.root.winfo_children()[0] if self.root.winfo_children() else None
    if outer is None:
        return
    children=outer.winfo_children()
    before=children[1] if len(children)>1 else None
    setup=ttk.LabelFrame(outer,text="数据与离线AI运行库",padding=10)
    if before is not None:
        setup.pack(fill="x",pady=(0,12),before=before)
    else:
        setup.pack(fill="x",pady=(0,12))
    self.data_dir_text=tk.StringVar(value=str(getattr(self.store,"base","")))
    ttk.Label(setup,textvariable=self.data_dir_text,wraplength=790).pack(anchor="w",fill="x")
    buttons=ttk.Frame(setup)
    buttons.pack(fill="x",pady=(8,0))
    choose=ttk.Button(buttons,text="选择数据目录",command=self.choose_data_directory)
    download=ttk.Button(buttons,text="下载",command=self.start_download)
    choose.pack(side="left",fill="x",expand=True,ipady=6)
    download.pack(side="left",fill="x",expand=True,padx=(8,0),ipady=6)
    self.control_buttons["选择数据目录"]=choose
    self.control_buttons["下载"]=download
    self.controls.extend([choose,download])
App._build=_enhanced_app_build
def _update_runtime_status(self):
    vision=getattr(self,"vision_runtime",None)
    ocr=getattr(self,"ocr_runtime",None)
    if vision is None:
        return
    if vision.ready and ocr is not None and ocr.ready:
        manifest=vision.manifest() if vision.active_game else {"device":vision.device_name,"trained_steps":0}
        self.set_confidence("AI视觉："+str(manifest.get("device",vision.device_name))+"，训练步数"+str(manifest.get("trained_steps",0))+"；OCR：离线可用")
    else:
        self.set_confidence("离线AI运行库未就绪，请点击“下载”；视觉="+str(vision.error)+"；OCR="+str(getattr(ocr,"error","未初始化")))
App._update_runtime_status=_update_runtime_status
def _require_ai_runtime(self):
    self.vision_runtime.require_ready()
    self.ocr_runtime.require_ready()
    game=self.require_game()
    manifest=self.vision_runtime.activate_game(game["id"])
    self.api.ai_runtime=self.vision_runtime
    self.store.record_vision_model(game["id"],manifest)
    self._update_runtime_status()
    return manifest
App.require_ai_runtime=_require_ai_runtime
_original_require_game=App.require_game
def _enhanced_require_game(self):
    game=_original_require_game(self)
    runtime=getattr(self,"vision_runtime",None)
    if runtime is not None and runtime.ready:
        runtime.activate_game(game["id"])
    return game
App.require_game=_enhanced_require_game
def _choose_data_directory(self):
    from tkinter import filedialog
    if self.mode_state!=MODE_IDLE:
        self.show_error("运行模式期间不能切换数据目录")
        return
    value=filedialog.askdirectory(parent=self.root,title="选择通用游戏AI数据目录",mustexist=False,initialdir=str(self.store.base))
    if not value:
        return
    try:
        base=configure_data_directory(value)
        if Path(self.store.base).resolve()==base:
            self.status.set("数据目录未改变")
            return
        old=self.store
        old.close(5.0)
        self.store=DataStore(base)
        self.store.set_writer_error_callback(self._writer_status_changed)
        self.selected_game=self.store.selected_game()
        self.selected_window=None
        self.window_recommendation=self.store.load_window_descriptor()
        self.storage_fault=bool(self.store.read_only)
        self.data_directory=base
        self.runtime_installer=RuntimeInstaller(base)
        self.vision_runtime=OfflineVisionRuntime(base)
        self.ocr_runtime=OfflineOCRRuntime(base)
        global CURRENT_VISION_RUNTIME,CURRENT_OCR_RUNTIME
        CURRENT_VISION_RUNTIME=self.vision_runtime
        CURRENT_OCR_RUNTIME=self.ocr_runtime
        self.api.ai_runtime=self.vision_runtime
        self.data_dir_text.set(str(base))
        self._refresh_all()
        self._update_runtime_status()
        self.show_info("数据目录","已切换到："+str(base)+"。所有后续数据库、模型、依赖、缓存、日志和临时文件均使用该目录。")
    except Exception as error:
        self.show_error("切换数据目录失败："+str(error))
App.choose_data_directory=_choose_data_directory
def _start_download(self):
    if self.mode_state!=MODE_IDLE or self.closing:
        self.show_error("当前已有操作正在运行，请先停止")
        return
    try:
        stop_event=self.lifecycle.begin("下载")
    except Exception as error:
        self.show_error(str(error))
        return
    self.mode="下载"
    self.mode_state=MODE_STARTING
    self.stop_event=stop_event
    self.pending_mode_result=None
    self.pending_mode_error=None
    self.mode_shutdown_deadline=None
    self.mode_shutdown_forced=[]
    self.mode_stop_started=False
    self.mode_shutdown_polling=False
    self.api.block_input()
    self.set_input_status("已锁定")
    self.set_controls(True)
    self.progress_value.set(0)
    self.status.set("正在把依赖与模型运行库下载到所选数据目录；按ESC或点击“停止”可中止")
    self.mode_thread=threading.Thread(target=self.worker_entry,args=("下载",self.download_worker),name="UniversalGameAI-下载",daemon=True)
    self.mode_thread.start()
App.start_download=_start_download
def _download_worker(self):
    self.lifecycle.mark_running()
    self.mode_state=MODE_RUNNING
    def line(value):
        if value:
            self.set_status("下载中："+value[-180:])
    marker=self.runtime_installer.run(self.stop_event,self.set_progress,line)
    global CURRENT_VISION_RUNTIME,CURRENT_OCR_RUNTIME
    self.vision_runtime=OfflineVisionRuntime(self.data_directory)
    self.ocr_runtime=OfflineOCRRuntime(self.data_directory)
    self.ocr_runtime.require_ready()
    try:
        warmup=self.ocr_runtime.np.zeros((48,192,3),dtype=self.ocr_runtime.np.uint8)
        with self.ocr_runtime.lock:
            self.ocr_runtime.engine(warmup)
    except Exception as error:
        raise RuntimeError("OCR离线模型初始化失败："+str(error))
    CURRENT_VISION_RUNTIME=self.vision_runtime
    CURRENT_OCR_RUNTIME=self.ocr_runtime
    self.api.ai_runtime=self.vision_runtime
    if self.selected_game:
        manifest=self.vision_runtime.activate_game(self.selected_game["id"])
        self.store.record_vision_model(self.selected_game["id"],manifest)
    self.ui(self._update_runtime_status)
    return ModeResult("completed","下载完成；AI视觉模型将在本机离线生成和训练，OCR已可离线运行",{"runtime":marker})
App.download_worker=_download_worker
_original_request_mode_stop=App.request_mode_stop
def _enhanced_request_mode_stop(self,status="stopped",reason=""):
    result=_original_request_mode_stop(self,status,reason)
    if self.mode=="下载" and getattr(self,"runtime_installer",None) is not None:
        try:
            self.runtime_installer.stop()
        except Exception:
            pass
    return result
App.request_mode_stop=_enhanced_request_mode_stop
_original_review_run=ReviewController.run
def _enhanced_review_run(self):
    app=self.app
    app.require_ai_runtime()
    game=app.require_game()
    app.store.sample_write_barrier()
    with app.store.lock:
        rows=app.store.db.execute("SELECT thumbnail FROM samples WHERE game_id=? AND thumbnail IS NOT NULL ORDER BY created",(str(game["id"]),)).fetchall()
    grays=[]
    for row in rows:
        try:
            grays.append(bounded_decompress(row["thumbnail"],PIXELS*2))
        except Exception:
            pass
    app.set_status("复习阶段：正在GPU离线训练神经视觉编码器")
    manifest=app.vision_runtime.train(game["id"],grays,app.stop_event,app.set_progress)
    app.store.record_vision_model(game["id"],manifest)
    app.set_status("复习阶段：正在用新AI视觉模型升级全部样本特征")
    app.store.reencode_samples(game["id"],app.vision_runtime,app.stop_event,app.set_progress)
    return _original_review_run(self)
ReviewController.run=_enhanced_review_run
def _open_ocr_teaching_dialog(self,parent,game,buffer,frame,on_close=None):
    self.require_ai_runtime()
    return OCRTeachingDialog(self,parent,game,buffer,frame,on_close)
App.open_ocr_teaching_dialog=_open_ocr_teaching_dialog
_original_start_learning=App.start_learning
def _enhanced_start_learning(self):
    try:
        self.require_ai_runtime()
    except Exception as error:
        self.show_error(str(error))
        return
    return _original_start_learning(self)
App.start_learning=_enhanced_start_learning
_original_start_review=App.start_review
def _enhanced_start_review(self):
    try:
        self.require_ai_runtime()
    except Exception as error:
        self.show_error(str(error))
        return
    return _original_start_review(self)
App.start_review=_enhanced_start_review
_original_start_training=App.start_training
def _enhanced_start_training(self):
    try:
        self.require_ai_runtime()
    except Exception as error:
        self.show_error(str(error))
        return
    return _original_start_training(self)
App.start_training=_enhanced_start_training
_original_start_ask=App.start_ask
def _enhanced_start_ask(self):
    try:
        self.require_ai_runtime()
    except Exception as error:
        self.show_error(str(error))
        return
    return _original_start_ask(self)
App.start_ask=_enhanced_start_ask
def ocr_can_authorize_action(text,action):
    return False
def main():
    multiprocessing.freeze_support()
    if "--self-test" in sys.argv:
        raise SystemExit(run_self_test())
    if "--windows-smoke-test" in sys.argv:
        raise SystemExit(run_windows_smoke_test())
    if "--acceptance-test" in sys.argv:
        raise SystemExit(run_acceptance_test())
    enable_dpi_awareness()
    root=tk.Tk()
    selected=startup_select_data_directory(root)
    if selected is None:
        try:
            root.destroy()
        except Exception:
            pass
        return
    holder={"app":None}
    install_global_hooks(holder)
    try:
        holder["app"]=App(root)
    except Exception:
        startup_error(root,traceback.format_exc())
    root.mainloop()
if __name__=="__main__":
    main()
