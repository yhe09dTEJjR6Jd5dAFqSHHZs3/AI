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
from pathlib import Path
from collections import deque,Counter,defaultdict
import tkinter as tk
from tkinter import ttk
import ctypes
from ctypes import wintypes
APP_NAME="UniversalGameAI"
FORMAT_VERSION=5
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
DATABASE_SCHEMA_VERSION=5
MAX_SAMPLES=1500
MAX_PROTOTYPES=320
SUPPORTED_BUTTONS={"left","right","middle"}
SUPPORTED_KINDS={"no_op","click","double_click","long_press","drag","scroll_v","scroll_h","move","hover"}
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
        with self.lock:
            if self.state==MODE_IDLE:
                return False
            if status in {"completed","stopped","failed"}:
                if status=="failed" or self.requested_status!="failed":
                    self.requested_status=status
            if reason:
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
                self.stamp=float(time.time() if stamp is None else stamp)
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
        deadline=time.time()+0.45
        while time.time()<deadline:
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
        self.wgc=WindowsGraphicsCapture(self)
    def _bind(self):
        self.WNDENUMPROC=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
        self.HOOKPROC=ctypes.WINFUNCTYPE(wintypes.LPARAM,ctypes.c_int,wintypes.WPARAM,wintypes.LPARAM)
        self.user32.EnumWindows.argtypes=[self.WNDENUMPROC,wintypes.LPARAM]
        self.user32.EnumWindows.restype=wintypes.BOOL
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
        try:
            self.wgc.release_thread(wanted)
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
        item={"hwnd":safe_int(target.get("hwnd",0),0),"pid":safe_int(target.get("pid",0),0),"class":str(target.get("class","")),"thread":safe_int(target.get("window_thread_id",0),0),"path":os.path.normcase(str(target.get("process_path",""))),"created":safe_int(target.get("process_created",0),0)}
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
        if rule is not None and not isinstance(rule,dict):
            item.pop("title_rule",None)
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
            mode=str(rule.get("mode",""))
            value=str(rule.get("value",""))
            title=self.window_title(hwnd)
            if mode=="exact" and title!=value:
                raise TargetUnavailable("目标窗口标题不再符合精确规则")
            if mode=="contains" and value not in title:
                raise TargetUnavailable("目标窗口标题不再符合包含规则")
            if mode=="prefix" and not title.startswith(value):
                raise TargetUnavailable("目标窗口标题不再符合前缀规则")
        return self.client_rect(hwnd),self.dpi_for_window(hwnd)
    def validate_target(self,target,require_foreground=True):
        rect,dpi=self.validate_target_identity(target,require_foreground)
        expected_size=target.get("client_size")
        if isinstance(expected_size,(list,tuple)) and len(expected_size)>=2 and [int(rect[2]),int(rect[3])]!=[safe_int(expected_size[0],-1),safe_int(expected_size[1],-1)]:
            raise TargetUnavailable("目标窗口客户区尺寸或DPI已变化，正在暂停并自动重新校准")
        expected_dpi=target.get("selected_dpi",target.get("dpi"))
        if expected_dpi is not None and int(dpi)!=safe_int(expected_dpi,-1):
            raise TargetUnavailable("目标窗口客户区尺寸或DPI已变化，正在暂停并自动重新校准")
        return rect
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
    def _rgb_from_raw(self,raw,width,height,out_w=PREVIEW_W,out_h=PREVIEW_H):
        result=bytearray(out_w*out_h*3)
        for oy in range(out_h):
            sy=min(height-1,(2*oy+1)*height//(2*out_h))
            for ox in range(out_w):
                sx=min(width-1,(2*ox+1)*width//(2*out_w))
                index=(sy*width+sx)*4
                position=(oy*out_w+ox)*3
                result[position]=raw[index+2]
                result[position+1]=raw[index+1]
                result[position+2]=raw[index]
        return bytes(result)
    def _capture_print(self,hwnd,width,height,out_w=FEATURE_W,out_h=FEATURE_H):
        key_kind="print|"+str(int(hwnd))
        item=self._gdi_resource(key_kind,0,int(width),int(height))
        ctypes.memset(item["bits"],0,int(width)*int(height)*4)
        if not self.user32.PrintWindow(wintypes.HWND(hwnd),item["memory"],3):
            raise CaptureUnavailable("PrintWindow采集失败")
        raw=(ctypes.c_ubyte*(int(width)*int(height)*4)).from_address(int(item["bits"].value))
        return self._rgb_from_raw(raw,int(width),int(height),int(out_w),int(out_h))
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
        now=time.time()
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
        now=time.time()
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
            return bool(calibration.get("validated_backend") and safe_int(calibration.get("validated_pid",-1),-1)==current_pid and str(calibration.get("validated_class",""))==self.class_name(hwnd) and str(calibration.get("validated_process_path",""))==process["path"] and safe_int(calibration.get("validated_process_created",-1),-1)==process["created"] and safe_int(calibration.get("validated_window_thread_id",-1),-1)==current_thread and safe_int(calibration.get("validated_integrity",-1),-1)==process["integrity"] and safe_int(calibration.get("validated_dpi",0),0)==self.dpi_for_window(hwnd) and list(calibration.get("validated_rect",[0,0,0,0]))[2:4]==[int(current_rect[2]),int(current_rect[3])])
        except Exception:
            return False
    def capture_gray(self,target,require_foreground_for_desktop=True,validation_mode=False,need_preview=False):
        rect=self.validate_target(target,False)
        hwnd=safe_int(target["hwnd"],0)
        x,y,width,height=rect
        if width<FEATURE_W or height<FEATURE_H:
            raise CaptureUnavailable("客户区尺寸异常，拒绝采集")
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
        for priority,name in enumerate(backend_names):
            allowed,reason=self._circuit_allows((identity_key,name))
            if not allowed:
                attempts.append(name+"已跳过："+reason)
                continue
            try:
                command={"backend":name,"hwnd":hwnd,"rect":list(rect),"out_w":out_w,"out_h":out_h}
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
            raise CaptureUnavailable("无法采集目标窗口："+"；".join(attempts))
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
        if usable:
            mode="合法静态画面" if result.get("stable_frame") else ("低纹理画面" if result["quality"].get("flat_frame") else "画面有效")
            self.capture_reports[hwnd]="当前采集："+result["method"]+"；"+mode+"；后端已验收"
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
            stamp=time.time()
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
        result.update({"method":method,"validated_backend":method,"validated_backends":sorted(eligible),"dynamic_passed":True,"static_passed":not dynamic,"calibration_mode":"dynamic" if dynamic else "stable","validated_at":time.time(),"validated_rect":list(rect),"validated_dpi":dpi,"validated_pid":pid,"validated_class":str(target["class"]),"validated_process_path":process["path"],"validated_process_created":process["created"],"validated_window_thread_id":thread_id,"validated_integrity":process["integrity"],"integrity":process["integrity"],"nonblack_frames":len(selected),"black_frames":black_frames,"trusted_change":dynamic,"backend_thresholds":backend_thresholds})
        self.calibrations[hwnd]=result
        mode="动态校准" if dynamic else "稳定性校准"
        self.capture_reports[hwnd]="当前采集："+method+"；"+mode+"通过；非黑帧"+str(len(selected))+"；帧率"+str(round(fps,1))+"fps；后端已验收"
        return dict(result)
    def _send(self,flags,data=0,dx=0,dy=0,require_allowed=False):
        if require_allowed and not self.input_allowed():
            raise InputStopped("停止标志已设置，拒绝新的鼠标输入")
        item=INPUT()
        item.type=0
        item.mi=MOUSEINPUT(int(dx),int(dy),ctypes.c_ulong(int(data)&0xffffffff).value,int(flags),0,0)
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
        try:
            self.wgc.close()
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
                    result=bridge.wgc.capture(hwnd,(x,y,width,height),out_w,out_h)
                elif backend=="PrintWindow客户区":
                    result=bridge._capture_print(hwnd,width,height,out_w,out_h)
                elif backend=="窗口DC":
                    result=bridge._capture_dc(hwnd,0,0,width,height,out_w,out_h)
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
        self.non_escape_active=False
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
                    is_escape=int(data.vkCode)==0x1B
                    down=int(wparam) in {0x0100,0x0104}
                    stamp=time.time()
                    if is_escape:
                        first=down and not self.escape_down
                        self.escape_down=down
                        if first:
                            self.escape_event.set()
                            self._put({"kind":"escape","down":True,"time":stamp})
                    else:
                        if down:
                            self.non_escape_active=True
                            self.non_escape_count+=1
                            self.other_event.set()
                            self._put({"kind":"other","down":True,"time":stamp})
                        else:
                            self.non_escape_active=False
                            self._put({"kind":"other","down":False,"time":stamp})
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
        return not self.non_escape_active
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
        self.held=set()
        self.thread=None
        self.thread_id=0
        self.hook=None
        self.callback=None
        self.ready=threading.Event()
        self.error=None
        self.last_move=0.0
        self.last_input_time=0.0
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
        except queue.Full:
            pass
    def _run(self):
        try:
            self.thread_id=int(self.bridge.kernel32.GetCurrentThreadId())
            messages={0x0200:"move",0x0201:"left_down",0x0202:"left_up",0x0204:"right_down",0x0205:"right_up",0x0207:"middle_down",0x0208:"middle_up",0x020A:"wheel",0x020E:"hwheel"}
            def callback(code,wparam,lparam):
                if code>=0 and int(wparam) in messages:
                    data=ctypes.cast(lparam,ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                    if int(data.flags)&0x00000003:
                        return self.bridge.user32.CallNextHookEx(self.hook,code,wparam,lparam)
                    stamp=time.time()
                    kind=messages[int(wparam)]
                    if kind!="move" or stamp-self.last_move>=0.018:
                        if kind=="move":
                            self.last_move=stamp
                        event={"type":kind,"x":int(data.pt.x),"y":int(data.pt.y),"time":stamp}
                        if kind in {"wheel","hwheel"}:
                            raw=(int(data.mouseData)>>16)&0xffff
                            event["delta"]=raw-0x10000 if raw&0x8000 else raw
                        if kind.endswith("_down"):
                            self.held.add(kind.split("_",1)[0])
                        elif kind.endswith("_up"):
                            self.held.discard(kind.split("_",1)[0])
                        self.last_input_time=stamp
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
    def all_released(self):
        return not self.held
    def stable_for(self,seconds):
        return not self.held and time.time()-self.last_input_time>=max(0.0,float(seconds))
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
                    stamp=time.time()
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
                    frame={"time":stamp,"f":feature,"coarse":coarse_feature(feature),"gray":gray,"rgb":rgb,"preview_rgb":preview_rgb,"preview_width":preview_width,"preview_height":preview_height,"method":captured["method"],"quality":captured["quality"],"motion_valid":previous is not None,"rect":rect,"dpi":self.bridge.dpi_for_window(int(self.target["hwnd"])),"capture_valid":bool(captured.get("capture_valid")),"backend_validated":bool(captured.get("backend_validated")),"usable_for_learning":bool(captured.get("usable_for_learning") and confirmed),"usable_for_training":bool(captured.get("usable_for_training") and confirmed),"usable_for_teaching":bool(captured.get("usable_for_teaching") and confirmed),"stale":bool(captured.get("stale")),"stable_frame":bool(captured.get("stable_frame")),"black_frame":bool(captured.get("black_frame")),"protected_or_black":bool(captured.get("protected_or_black")),"capture_frozen":bool(captured.get("capture_frozen")),"frozen_backend":bool(captured.get("frozen_backend")),"backend_changed":bool(captured.get("backend_changed"))}
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
        now=time.time()
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
        if time.time()-float(stamp)>max_wait_age:
            return None
        return None
    def snapshot(self,seconds=1.5):
        cutoff=time.time()-max(0.1,float(seconds))
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
class LearningController:
    def __init__(self,app):
        self.app=app
    def run(self):
        return self.app._learning_worker_impl()
class ReviewController:
    def __init__(self,app):
        self.app=app
    def session_of(self,item):
        return str(item.get("session_id") or item.get("context",{}).get("session_id") or "legacy")
    def method_of(self,item):
        return str(item.get("capture_method") or item.get("context",{}).get("capture_method") or "unknown")
    def stratum_of(self,item):
        return (action_family_key(item["a"]),action_signature(item["a"]),self.method_of(item))
    def decorrelate(self,valid):
        result=[]
        previous={}
        removed=0
        ordered=sorted(valid,key=lambda item:(self.session_of(item),float(item.get("created",0.0)),str(item.get("checksum",""))))
        for index,item in enumerate(ordered):
            if index%32==0 and self.app.should_stop():
                raise InputStopped("复习已停止")
            key=(self.session_of(item),self.stratum_of(item))
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
        session_groups=defaultdict(list)
        for item in valid:
            session_groups[self.session_of(item)].append(item)
        sessions=sorted(session_groups,key=lambda key:hashlib.sha256(key.encode("utf-8","replace")).hexdigest())
        totals=Counter(self.stratum_of(item) for item in valid)
        if len(sessions)<2:
            return list(valid),[],{"complete":False,"mode":"independent_session","holdout_sessions":[],"reason":"只有一个完整学习session，只能生成临时模型","strata":len(totals),"session_count":len(sessions)}
        session_counts={session:Counter(self.stratum_of(item) for item in items) for session,items in session_groups.items()}
        session_sizes={session:len(items) for session,items in session_groups.items()}
        target=max(150,round(len(valid)*0.25))
        best=None
        best_score=None
        def consider(chosen):
            nonlocal best,best_score
            if not chosen or len(chosen)>=len(sessions):
                return
            hold_counts=Counter()
            hold_count=0
            for session in chosen:
                hold_counts.update(session_counts[session])
                hold_count+=session_sizes[session]
            complete=all(0<hold_counts[key]<totals[key] for key in totals)
            score=(0 if complete else 1,0 if hold_count>=150 else 1,abs(hold_count-target),len(chosen))
            if best_score is None or score<best_score:
                best=set(chosen)
                best_score=score
        count=len(sessions)
        if count<=16:
            for mask in range(1,(1<<count)-1):
                consider({sessions[index] for index in range(count) if mask&(1<<index)})
        else:
            generator=random.Random(int(hashlib.sha256("|".join(sessions).encode("utf-8","replace")).hexdigest()[:16],16))
            for order in (sessions,sorted(sessions,key=lambda value:session_sizes[value]),sorted(sessions,key=lambda value:session_sizes[value],reverse=True)):
                for length in range(1,min(len(order),16)+1):
                    consider(set(order[:length]))
            for _ in range(5000):
                consider({session for session in sessions if generator.random()<0.25})
        if not best:
            return list(valid),[],{"complete":False,"mode":"independent_session","holdout_sessions":[],"reason":"无法建立完整session留出集","strata":len(totals),"session_count":len(sessions)}
        train=[item for item in valid if self.session_of(item) not in best]
        holdout=[item for item in valid if self.session_of(item) in best]
        assert_disjoint_checksums(train,holdout)
        hold_counts=Counter(self.stratum_of(item) for item in holdout)
        complete=bool(train and holdout and all(0<hold_counts[key]<totals[key] for key in totals))
        return train,holdout,{"complete":complete,"mode":"independent_session","holdout_sessions":sorted(best),"reason":"" if complete else "完整session划分后无法同时覆盖全部原始动作签名与采集后端","strata":len(totals),"session_count":len(sessions)}
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
        return self.app._review_worker_impl()
class TrainingController:
    def __init__(self,app):
        self.app=app
    def run(self):
        return self.app._training_worker_impl()
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
            app.ask_counts={"saved":0,"duplicates":0,"skipped":0,"rejected":0}
            answer_queue=queue.Queue()
            app.ask_answer_queue=answer_queue
            producer.request(deque(["<START>","<START>"],maxlen=4),time.time())
            initial=None
            deadline=time.monotonic()+5.0
            while initial is None and time.monotonic()<deadline and not app.should_stop():
                packet=producer.get_result(0.15)
                if packet and not packet.get("error") and packet.get("frame") is not None:
                    initial=packet
                elif packet and packet.get("error"):
                    app.set_status("请教初始化等待画面："+str(packet["error"]))
                    producer.request(deque(["<START>","<START>"],maxlen=4),time.time())
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
                    state_since=safe_float(command.get("state_since"),time.time())
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
                    app.lifecycle.request_stop("failed",message)
                    app.mode_state=MODE_STOPPING
                    if app.stop_event is not None:
                        app.stop_event.set()
                    app.api.block_input()
                    break
        try:
            app.store.flush_samples()
        except Exception:
            pass
        counts=app.ask_counts if isinstance(app.ask_counts,dict) else {"saved":0,"duplicates":0,"skipped":0,"rejected":0}
        summary="请教已结束：已保存"+str(counts.get("saved",0))+"，重复未保存"+str(counts.get("duplicates",0))+"，跳过"+str(counts.get("skipped",0))+"，拒绝记录"+str(counts.get("rejected",0))+"；模型需要复习"
        status=app.lifecycle.snapshot()[3]
        if status=="failed":
            return ModeResult("failed",app.lifecycle.snapshot()[4] or summary)
        return ModeResult(status if status in {"completed","stopped"} else "stopped",summary,{"samples":stats.get("valid",0)})
class DataStore:
    def __init__(self):
        local=os.environ.get("LOCALAPPDATA")
        self.base=(Path(local) if local else Path.home()/"AppData"/"Local")/APP_NAME
        self.base.mkdir(parents=True,exist_ok=True)
        self.db_path=self.base/"universal_game_ai.db"
        self.lock=threading.RLock()
        self.model_cache={}
        self.closed=False
        self.closing=False
        self.invalid_rows=defaultdict(int)
        self.pending_samples=[]
        self.pending_event=threading.Event()
        self.writer_stop=threading.Event()
        self.writer_error=None
        self.writer_thread=None
        self.db=sqlite3.connect(str(self.db_path),timeout=3.0,check_same_thread=False)
        self.db.row_factory=sqlite3.Row
        with self.db:
            self.db.execute("PRAGMA foreign_keys=ON")
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA synchronous=NORMAL")
            self.db.execute("PRAGMA temp_store=MEMORY")
            self.db.execute("PRAGMA busy_timeout=3000")
        self._initialize_schema()
        self._migrate_legacy()
        self.writer_thread=threading.Thread(target=self._writer_loop,name="UniversalGameAI-SampleWriter",daemon=True)
        self.writer_thread.start()
    def _raise_writer_error(self):
        if self.writer_error:
            raise RuntimeError("样本批量写入失败："+str(self.writer_error))
    def _flush_pending(self):
        with self.lock:
            if not self.pending_samples:
                self.pending_event.clear()
                self._raise_writer_error()
                return 0
            batch=self.pending_samples
            self.pending_samples=[]
            self.pending_event.clear()
            rows=[item["row"] for item in batch]
            review_games=sorted({item["gid"] for item in batch if item.get("mark_review")})
            try:
                with self.db:
                    self.db.executemany("INSERT OR IGNORE INTO samples(game_id,created,kind,action_signature,action_family,repeat_policy,feature_algorithm_version,action_algorithm_version,feature,coarse,action,source,session_id,capture_method,context,thumbnail,weight,fingerprint) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",rows)
                    for gid in review_games:
                        self.db.execute("UPDATE games SET needs_review=1 WHERE id=?",(gid,))
            except Exception:
                self.pending_samples=batch+self.pending_samples
                self.writer_error=traceback.format_exc()
                raise
            return len(batch)
    def flush_samples(self):
        self._raise_writer_error()
        return self._flush_pending()
    def _writer_loop(self):
        while not self.writer_stop.is_set():
            self.pending_event.wait(0.35)
            if self.writer_stop.is_set():
                break
            try:
                self._flush_pending()
            except Exception:
                self.writer_stop.set()
                break
        try:
            self._flush_pending()
        except Exception:
            pass
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
        self.flush_samples()
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
        if selected not in {item["id"] for item in cleaned}:
            raise RuntimeError("所选游戏不存在")
        with self.lock,self.db:
            self.db.execute("INSERT INTO config_backups(created,payload) VALUES(?,?)",(time.time(),json.dumps(self._config_snapshot(),ensure_ascii=False,separators=(",",":"))))
            self.db.execute("DELETE FROM config_backups WHERE id NOT IN (SELECT id FROM config_backups ORDER BY id DESC LIMIT 5)")
            keep={item["id"] for item in cleaned}
            existing={row[0] for row in self.db.execute("SELECT id FROM games")}
            for gid in existing-keep:
                self.db.execute("DELETE FROM model_backups WHERE game_id=?",(gid,))
                self.db.execute("DELETE FROM games WHERE id=?",(gid,))
                self.model_cache.pop(gid,None)
            for item in cleaned:
                self.db.execute("INSERT INTO games(id,name,created,needs_review,last_review) VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,created=excluded.created,needs_review=excluded.needs_review,last_review=excluded.last_review",(item["id"],item["name"],item["created"],item["needs_review"],item["last_review"]))
            self.db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('selected_game',?)",(selected,))
    def delete_game(self,gid):
        self.flush_samples()
        game_id=str(gid)
        with self.lock,self.db:
            row=self.db.execute("SELECT 1 FROM games WHERE id=?",(game_id,)).fetchone()
            if not row:
                return False
            self.db.execute("DELETE FROM games WHERE id=?",(game_id,))
            selected=self.db.execute("SELECT value FROM meta WHERE key='selected_game'").fetchone()
            if selected and str(selected[0])==game_id:
                self.db.execute("DELETE FROM meta WHERE key='selected_game'")
        self.model_cache.pop(game_id,None)
        return True
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
        with self.lock,self.db:
            self.db.execute("UPDATE games SET "+",".join(fields)+" WHERE id=?",values)
    def _sample_fingerprint(self,feature,action,context=None):
        temporal=temporal_from_context(context or {})
        identity={"action":normalize_action(action),"temporal":temporal}
        return hashlib.sha256(feature_bytes(feature)+b"\0"+canonical_bytes(identity)).hexdigest()
    def _near_duplicate(self,gid,feature,signature,threshold,context=None):
        with self.lock:
            rows=self.db.execute("SELECT feature,coarse,feature_algorithm_version,context FROM samples WHERE game_id=? AND action_signature=? ORDER BY created DESC,id DESC LIMIT 36",(gid,signature)).fetchall()
            pending=[item for item in self.pending_samples if item["gid"]==gid and item["signature"]==signature][-36:]
        query=feature_bytes(feature)
        query_coarse=coarse_feature(query)
        query_context=context if isinstance(context,dict) else {}
        for item in pending:
            try:
                if temporal_distance(query_context,item["context"])<=0.08 and coarse_distance(query_coarse,item["coarse"])<=max(2.0,float(threshold)*2.5) and feature_distance(query,item["feature"])<=float(threshold):
                    return True
            except Exception:
                pass
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
        need_compact=False
        with self.lock:
            if not self.db.execute("SELECT 1 FROM games WHERE id=?",(gid,)).fetchone():
                raise RuntimeError("游戏不存在")
            if any(item["gid"]==gid and item["fingerprint"]==fingerprint for item in self.pending_samples) or self.db.execute("SELECT 1 FROM samples WHERE game_id=? AND fingerprint=?",(gid,fingerprint)).fetchone():
                return False
            if enforce_quota and kind=="no_op":
                row=self.db.execute("SELECT SUM(CASE WHEN kind='no_op' THEN 1 ELSE 0 END) AS noops,SUM(CASE WHEN kind!='no_op' THEN 1 ELSE 0 END) AS actions FROM samples WHERE game_id=?",(gid,)).fetchone()
                pending_noops=sum(1 for item in self.pending_samples if item["gid"]==gid and item["kind"]=="no_op")
                pending_actions=sum(1 for item in self.pending_samples if item["gid"]==gid and item["kind"]!="no_op")
                if int(row["noops"] or 0)+pending_noops>=max(1,(int(row["actions"] or 0)+pending_actions)//3):
                    return False
            if enforce_quota and self._near_duplicate(gid,fbytes,signature,duplicate_threshold,context):
                return False
            row=(gid,created_value,kind,signature,action_family_key(clean),repeat_policy,FEATURE_ALGORITHM_VERSION,ACTION_ALGORITHM_VERSION,sqlite3.Binary(zlib.compress(fbytes,6)),sqlite3.Binary(coarse),json.dumps(clean,ensure_ascii=False,separators=(",",":")),str(source),session_id,capture_method,json.dumps(context,ensure_ascii=False,separators=(",",":")),sqlite3.Binary(zlib.compress(gray_bytes(thumbnail),6)) if gray_valid(thumbnail) else None,float(max(0.1,min(10.0,weight))),fingerprint)
            self.pending_samples.append({"row":row,"gid":gid,"signature":signature,"coarse":coarse,"feature":fbytes,"context":context,"kind":kind,"fingerprint":fingerprint,"session_id":session_id,"created":created_value,"mark_review":bool(mark_review)})
            if len(self.pending_samples)>=12:
                self.pending_event.set()
            count=int(self.db.execute("SELECT COUNT(*) FROM samples WHERE game_id=?",(gid,)).fetchone()[0])+sum(1 for item in self.pending_samples if item["gid"]==gid)
            need_compact=count>MAX_SAMPLES+16
        if need_compact:
            self.flush_samples()
            self.compact_samples(gid,MAX_SAMPLES)
        return True
    def discard_session(self,gid,session_id):
        with self.lock:
            before=len(self.pending_samples)
            self.pending_samples=[item for item in self.pending_samples if not (item["gid"]==gid and item["session_id"]==str(session_id))]
            pending_removed=before-len(self.pending_samples)
            with self.db:
                cursor=self.db.execute("DELETE FROM samples WHERE game_id=? AND session_id=?",(gid,str(session_id)))
                removed=pending_removed+max(0,int(cursor.rowcount or 0))
                if removed:
                    self.db.execute("UPDATE games SET needs_review=1 WHERE id=?",(gid,))
        self.model_cache.pop(gid,None)
        return removed
    def discard_session_window(self,gid,session_id,start_time,end_time):
        with self.lock:
            before=len(self.pending_samples)
            self.pending_samples=[item for item in self.pending_samples if not (item["gid"]==gid and item["session_id"]==str(session_id) and float(start_time)<=item["created"]<=float(end_time))]
            pending_removed=before-len(self.pending_samples)
            with self.db:
                cursor=self.db.execute("DELETE FROM samples WHERE game_id=? AND session_id=? AND created BETWEEN ? AND ?",(gid,str(session_id),float(start_time),float(end_time)))
                removed=pending_removed+max(0,int(cursor.rowcount or 0))
                if removed:
                    self.db.execute("UPDATE games SET needs_review=1 WHERE id=?",(gid,))
        self.model_cache.pop(gid,None)
        return removed
    def append_sample(self,gid,feature,action,source,context=None,thumbnail=None,weight=1.0):
        return self._insert_sample(gid,feature,action,source,context or {},thumbnail,weight,True,True)
    def append_rejection(self,gid,feature,candidates,source="teach_reject",thumbnail=None,context=None):
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
        self.flush_samples()
        with self.lock:
            rows=self.db.execute("SELECT created,feature_algorithm_version,action_algorithm_version,feature,coarse,action,source,session_id,capture_method,context,thumbnail,weight,fingerprint,repeat_policy FROM samples WHERE game_id=? ORDER BY created DESC,id DESC LIMIT ?",(gid,int(limit))).fetchall()
        result=[]
        invalid=0
        for row in reversed(rows):
            try:
                feature=upgrade_feature(bounded_decompress(row["feature"],FEATURE_LEN*2),row["feature_algorithm_version"])
                action=normalize_action(json.loads(row["action"]))
                coarse=bytes(row["coarse"]) if row["coarse"] is not None and len(row["coarse"])==COARSE_LEN else coarse_feature(feature)
                if not feature_valid(feature) or len(coarse)!=COARSE_LEN or not action:
                    invalid+=1
                    continue
                thumbnail=bounded_decompress(row["thumbnail"],PIXELS*4) if row["thumbnail"] is not None else None
                thumbnail=upgrade_gray_image(thumbnail) if thumbnail is not None else None
                context=json.loads(row["context"])
                if not isinstance(context,dict):
                    context={}
                context.update({"session_id":row["session_id"],"capture_method":row["capture_method"],"repeat_policy":row["repeat_policy"]})
                result.append({"format_version":FORMAT_VERSION,"feature_width":FEATURE_W,"feature_height":FEATURE_H,"feature_algorithm_version":FEATURE_ALGORITHM_VERSION,"action_algorithm_version":ACTION_ALGORITHM_VERSION,"created":row["created"],"game_id":gid,"f":feature,"coarse":coarse,"a":action,"source":row["source"],"session_id":row["session_id"],"capture_method":row["capture_method"],"repeat_policy":row["repeat_policy"],"context":context,"thumbnail":thumbnail,"weight":row["weight"],"checksum":row["fingerprint"]})
            except Exception:
                invalid+=1
        self.invalid_rows[str(gid)]=max(self.invalid_rows.get(str(gid),0),invalid)
        return result,{"valid":len(result),"invalid":invalid,"total":len(rows)}
    def load_rejections(self,gid,limit=500):
        with self.lock:
            rows=self.db.execute("SELECT created,feature_algorithm_version,feature,coarse,thumbnail,candidates,source,session_id,capture_method FROM rejections WHERE game_id=? ORDER BY created DESC,id DESC LIMIT ?",(gid,int(limit))).fetchall()
        result=[]
        invalid=0
        for row in rows:
            try:
                feature=upgrade_feature(bounded_decompress(row["feature"],FEATURE_LEN*2),row["feature_algorithm_version"])
                coarse=bytes(row["coarse"]) if row["coarse"] is not None and len(row["coarse"])==COARSE_LEN else coarse_feature(feature)
                candidates=json.loads(row["candidates"])
                thumbnail=bounded_decompress(row["thumbnail"],PIXELS*4) if row["thumbnail"] is not None else None
                thumbnail=upgrade_gray_image(thumbnail) if thumbnail is not None else None
                if feature_valid(feature) and len(coarse)==COARSE_LEN and isinstance(candidates,list):
                    result.append({"created":row["created"],"f":feature,"coarse":coarse,"thumbnail":thumbnail,"candidates":candidates,"source":row["source"],"session_id":row["session_id"],"capture_method":row["capture_method"]})
                else:
                    invalid+=1
            except Exception:
                invalid+=1
        self.invalid_rows["rejections:"+str(gid)]=max(self.invalid_rows.get("rejections:"+str(gid),0),invalid)
        return result
    def sample_stats(self,gid):
        self.flush_samples()
        with self.lock:
            row=self.db.execute("SELECT COUNT(*) AS total,SUM(CASE WHEN feature_algorithm_version IN (3,?) THEN 1 ELSE 0 END) AS valid,COALESCE(SUM(length(feature)+length(coarse)+length(action)+length(context)+COALESCE(length(thumbnail),0)),0) AS bytes FROM samples WHERE game_id=?",(FEATURE_ALGORITHM_VERSION,gid)).fetchone()
        total=safe_int(row["total"] or 0,0,0)
        sql_valid=safe_int(row["valid"] or 0,0,0,total)
        observed=safe_int(self.invalid_rows.get(str(gid),0),0,0,total)
        valid=max(0,min(sql_valid,total-observed))
        return {"valid":valid,"invalid":total-valid,"total":total,"bytes":safe_int(row["bytes"] or 0,0,0)}
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
        self.flush_samples()
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
        self.flush_samples()
        with self.lock,self.db:
            self.db.execute("DELETE FROM samples WHERE game_id=?",(gid,))
            self.db.execute("DELETE FROM models WHERE game_id=?",(gid,))
            self.db.execute("DELETE FROM model_backups WHERE game_id=?",(gid,))
            self.db.execute("DELETE FROM rejections WHERE game_id=?",(gid,))
            self.db.execute("UPDATE games SET needs_review=0,last_review=NULL WHERE id=?",(gid,))
        self.model_cache.pop(gid,None)
    def _calibration_identity_key(self,target):
        if not isinstance(target,dict):
            return ""
        raw_size=target.get("client_size")
        if not isinstance(raw_size,(list,tuple)):
            raw_size=[0,0]
        payload={"process_path":os.path.normcase(str(target.get("process_path",""))),"class":str(target.get("class","")),"client_size":[safe_int(value,0,0) for value in list(raw_size)[:2]],"dpi":safe_int(target.get("selected_dpi",target.get("dpi",0)),0,0)}
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
            except Exception:
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
            result.update({"format_version":FORMAT_VERSION,"feature_width":FEATURE_W,"feature_height":FEATURE_H,"feature_algorithm_version":FEATURE_ALGORITHM_VERSION,"action_algorithm_version":ACTION_ALGORITHM_VERSION,"game_id":gid,"complete":bool(complete),"prototypes":upgraded})
            return result
        except Exception:
            return None
    def _model_valid(self,item,gid,complete=True):
        try:
            if not isinstance(item,dict) or item.get("format_version")!=FORMAT_VERSION or item.get("feature_width")!=FEATURE_W or item.get("feature_height")!=FEATURE_H or item.get("feature_algorithm_version")!=FEATURE_ALGORITHM_VERSION or item.get("action_algorithm_version")!=ACTION_ALGORITHM_VERSION or item.get("game_id")!=gid or bool(item.get("complete"))!=bool(complete):
                return False
            prototypes=item.get("prototypes")
            if not isinstance(prototypes,list) or not prototypes or len(prototypes)>MAX_PROTOTYPES:
                return False
            for proto in prototypes:
                temporal=temporal_from_context(proto.get("temporal",{}))
                if not isinstance(proto,dict) or not str(proto.get("id","")) or not str(proto.get("cluster_id","")) or not str(proto.get("canonical_action_signature","")) or not feature_valid(proto.get("f")) or not isinstance(proto.get("coarse"),(bytes,bytearray)) or len(proto.get("coarse"))!=COARSE_LEN or not normalize_action(proto.get("a")) or not finite_number(proto.get("threshold")) or float(proto.get("threshold"))<=0 or int(proto.get("support",0))<=0 or not temporal.get("complete") or not finite_number(proto.get("temporal_threshold",0)) or float(proto.get("temporal_threshold",0))<=0:
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
            return isinstance(validation,dict) and isinstance(item.get("capture_backends"),list) and bool(item.get("capture_backends"))
        except Exception:
            return False
    def save_model(self,gid,model,complete=True):
        item=dict(model)
        item.update({"format_version":FORMAT_VERSION,"feature_width":FEATURE_W,"feature_height":FEATURE_H,"feature_algorithm_version":FEATURE_ALGORITHM_VERSION,"action_algorithm_version":ACTION_ALGORITHM_VERSION,"game_id":gid,"complete":bool(complete),"saved":time.time()})
        clean_prototypes=[]
        for proto in item.get("prototypes",[]):
            entry=dict(proto)
            action=normalize_action(entry.get("a"))
            if action:
                entry["a"]=action
                entry["canonical_action_signature"]=str(entry.get("canonical_action_signature") or action_signature(action))
                entry["cluster_id"]=str(entry.get("cluster_id") or "action|"+action_family_key(action)+"|"+hashlib.sha256(canonical_bytes(action)).hexdigest()[:20])
            if "coarse" not in entry and feature_valid(entry.get("f")):
                entry["coarse"]=coarse_feature(entry["f"])
            entry["repeat_policy"]=str(entry.get("repeat_policy","one_shot")) if str(entry.get("repeat_policy","one_shot")) in REPEAT_POLICIES else "one_shot"
            entry["max_rate"]=float(entry.get("max_rate",3.0)) if finite_number(entry.get("max_rate",3.0)) else 3.0
            clean_prototypes.append(entry)
        item["prototypes"]=clean_prototypes
        if not self._model_valid(item,gid,complete):
            raise RuntimeError("模型完整schema校验失败")
        payload=self._pack_model(item)
        checksum=hashlib.sha256(payload).hexdigest()
        slot="complete" if complete else "partial"
        validation=json.dumps(item.get("validation",{}),ensure_ascii=False,separators=(",",":"))
        with self.lock,self.db:
            if complete:
                old=self.db.execute("SELECT saved,prototype_count,validation,payload,checksum FROM models WHERE game_id=? AND slot='complete'",(gid,)).fetchone()
                if old:
                    self.db.execute("INSERT INTO model_backups(game_id,created,prototype_count,validation,payload,checksum) VALUES(?,?,?,?,?,?)",(gid,old["saved"],old["prototype_count"],old["validation"],old["payload"],old["checksum"]))
                    self.db.execute("DELETE FROM model_backups WHERE game_id=? AND id NOT IN (SELECT id FROM model_backups WHERE game_id=? ORDER BY id DESC LIMIT 5)",(gid,gid))
            self.db.execute("INSERT INTO models(game_id,slot,saved,created,prototype_count,validation,payload,checksum) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(game_id,slot) DO UPDATE SET saved=excluded.saved,created=excluded.created,prototype_count=excluded.prototype_count,validation=excluded.validation,payload=excluded.payload,checksum=excluded.checksum",(gid,slot,item["saved"],float(item.get("created",time.time())),len(item["prototypes"]),validation,sqlite3.Binary(payload),checksum))
            if complete:
                self.db.execute("DELETE FROM models WHERE game_id=? AND slot='partial'",(gid,))
                self.db.execute("UPDATE games SET needs_review=0,last_review=? WHERE id=?",(float(item.get("created",time.time())),gid))
        if complete:
            self.model_cache[gid]=item
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
            self.model_cache[gid]=item
            return item
        with self.lock:
            backups=self.db.execute("SELECT id,created,prototype_count,validation,payload,checksum FROM model_backups WHERE game_id=? ORDER BY id DESC",(gid,)).fetchall()
        for backup in backups:
            recovered=self._row_model(backup,gid,True)
            if recovered:
                payload=self._pack_model(recovered)
                checksum=hashlib.sha256(payload).hexdigest()
                with self.lock,self.db:
                    self.db.execute("INSERT OR REPLACE INTO models(game_id,slot,saved,created,prototype_count,validation,payload,checksum) VALUES(?,?,?,?,?,?,?,?)",(gid,"complete",float(recovered.get("saved",backup["created"])),float(recovered.get("created",backup["created"])),len(recovered["prototypes"]),json.dumps(recovered.get("validation",{}),ensure_ascii=False,separators=(",",":")),sqlite3.Binary(payload),checksum))
                self.model_cache[gid]=recovered
                return recovered
        if row:
            raise RuntimeError("模型版本、游戏ID、特征尺寸、算法版本或原型schema校验失败，且无法从数据库备份恢复")
        return None
    def model_metadata(self,gid):
        with self.lock:
            row=self.db.execute("SELECT slot,saved,created,prototype_count,validation FROM models WHERE game_id=? ORDER BY saved DESC LIMIT 1",(gid,)).fetchone()
        if not row:
            return None
        try:
            validation=json.loads(row["validation"])
        except Exception:
            validation={"status":"invalid"}
        return {"slot":row["slot"],"saved":row["saved"],"created":row["created"],"prototype_count":row["prototype_count"],"validation":validation}
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
        self.flush_samples()
        with self.lock:
            row=self.db.execute("PRAGMA quick_check").fetchone()
        return bool(row and str(row[0]).lower()=="ok")
    def close(self,timeout=5.0):
        with self.lock:
            if self.closed:
                return True
            if self.closing:
                return False
            self.closing=True
        self.writer_stop.set()
        self.pending_event.set()
        if self.writer_thread and self.writer_thread.is_alive() and self.writer_thread is not threading.current_thread() and float(timeout)>0:
            self.writer_thread.join(float(timeout))
        if self.writer_thread and self.writer_thread.is_alive():
            with self.lock:
                self.closing=False
            return False
        try:
            with self.lock:
                self._flush_pending()
                if self.db is not None:
                    self.db.execute("PRAGMA wal_checkpoint(FULL)")
                    self.db.close()
                    self.db=None
                self.closed=True
                self.closing=False
            return True
        except Exception:
            with self.lock:
                self.closing=False
            raise
class App:
    def __init__(self,root):
        self.root=root
        self.api=WinBridge()
        self.store=DataStore()
        self.selected_game=self.store.selected_game()
        self.selected_window=None
        self.lifecycle=ModeLifecycle()
        self.mode=None
        self.mode_state=MODE_IDLE
        self.stop_event=None
        self.mode_thread=None
        self.active_session=None
        self.pending_mode_result=None
        self.pending_mode_error=None
        self.mode_shutdown_deadline=None
        self.mode_shutdown_forced=[]
        self.controls=[]
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
        self.ui_queue=queue.Queue()
        self.closing=False
        self.shutdown_started=False
        self.shutdown_deadline=None
        self.review_distance_cache={}
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
        self._build()
        self._refresh_all()
        self.root.protocol("WM_DELETE_WINDOW",self.close)
        self.root.after(25,self.process_ui_queue)
        self.root.after(35,self.poll_global_escape)
        self.root.after(1200,self.periodic_refresh)
    def _build(self):
        self.root.title("通用游戏AI")
        self.root.geometry("800x680")
        self.root.minsize(720,610)
        self.root.option_add("*Font",("Microsoft YaHei UI",10))
        outer=ttk.Frame(self.root,padding=18)
        outer.pack(fill="both",expand=True)
        ttk.Label(outer,text="通用游戏AI控制面板",font=("Microsoft YaHei UI",18,"bold")).pack(anchor="w",pady=(0,12))
        info=ttk.LabelFrame(outer,text="当前状态",padding=12)
        info.pack(fill="x",pady=(0,12))
        labels=[("当前游戏：",self.game_text),("目标窗口：",self.window_text),("窗口身份：",self.window_detail),("采集兼容性：",self.capture_text),("输入权限：",self.input_text),("数据统计：",self.sample_text),("模型状态：",self.model_text),("识别状态：",self.confidence_text)]
        for row,(name,value) in enumerate(labels):
            ttk.Label(info,text=name).grid(row=row,column=0,sticky="nw",pady=2)
            ttk.Label(info,textvariable=value,wraplength=630).grid(row=row,column=1,sticky="nw",pady=2)
        info.columnconfigure(1,weight=1)
        grid=ttk.Frame(outer)
        grid.pack(fill="both",expand=True)
        specs=[("游戏",self.open_game_dialog),("选择窗口",self.open_window_dialog),("重新测试采集后端",self.retest_capture_backends),("学习",self.start_learning),("复习",self.start_review),("训练",self.start_training),("请教",self.start_ask),("停止",self.request_stop),("数据清理",self.open_data_dialog)]
        for index,(text,command) in enumerate(specs):
            button=ttk.Button(grid,text=text,command=command)
            button.grid(row=index//3,column=index%3,sticky="nsew",padx=6,pady=6,ipady=10)
            if text=="停止":
                self.stop_button=button
                button.configure(state="disabled")
            else:
                self.controls.append(button)
        for column in range(3):
            grid.columnconfigure(column,weight=1)
        for row in range(3):
            grid.rowconfigure(row,weight=1)
        ttk.Progressbar(outer,variable=self.progress_value,maximum=100).pack(fill="x",pady=(12,8))
        bottom=ttk.Frame(outer)
        bottom.pack(fill="x")
        ttk.Label(bottom,text="状态：").pack(side="left")
        ttk.Label(bottom,textvariable=self.status,wraplength=580).pack(side="left",fill="x",expand=True)
        ttk.Label(bottom,text="ESC或“停止”结束").pack(side="right")
    def tk_exception(self,exc_type,exc_value,exc_traceback):
        self.show_error("".join(traceback.format_exception(exc_type,exc_value,exc_traceback)))
    def ui(self,callback):
        if self.shutdown_started:
            return
        if threading.current_thread() is threading.main_thread():
            try:
                callback()
            except Exception:
                if not self.closing:
                    self.show_error(traceback.format_exc())
            return
        try:
            self.ui_queue.put_nowait(("call",callback))
        except queue.Full:
            pass
    def process_ui_queue(self):
        try:
            for _ in range(200):
                try:
                    kind,payload=self.ui_queue.get_nowait()
                except queue.Empty:
                    break
                if kind=="call" and not self.shutdown_started:
                    try:
                        payload()
                    except Exception:
                        self.show_error(traceback.format_exc())
        finally:
            if not self.shutdown_started:
                try:
                    self.root.after(25,self.process_ui_queue)
                except Exception:
                    pass
    def _begin_mode_stopping(self,result,error=None):
        if self.shutdown_started or self.closing and self.mode_state==MODE_IDLE:
            return
        if result is None:
            result=ModeResult("failed",str(self.mode or "模式")+"失败")
        self.pending_mode_result=result
        self.pending_mode_error=error
        self.lifecycle.mark_stopping(result.status,result.summary if result.status=="failed" else "")
        self.mode_state=MODE_STOPPING
        if self.stop_event is not None:
            self.stop_event.set()
        self.api.block_input()
        self._destroy_ask_window()
        if self.active_session is not None:
            self.active_session.request_stop()
        self.mode_shutdown_deadline=time.monotonic()+5.0
        self.status.set(str(self.mode or "模式")+"正在停止资源，控制按钮保持禁用")
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
        capture_pending=self.api.stop_capture_processes(0.0,False)
        deadline_reached=bool(self.mode_shutdown_deadline is not None and time.monotonic()>=self.mode_shutdown_deadline)
        if deadline_reached and capture_pending:
            forced=self.api.stop_capture_processes(0.0,True)
            self.mode_shutdown_forced.extend(name for name in capture_pending if name not in self.mode_shutdown_forced)
            capture_pending=forced
        thread_alive=bool(self.mode_thread and self.mode_thread.is_alive())
        if thread_alive:
            pending.append("模式线程")
        pending.extend("CaptureProcess:"+name for name in capture_pending)
        if pending or not session_done:
            suffix="；已到关闭期限并强制终止采集子进程："+"、".join(self.mode_shutdown_forced) if self.mode_shutdown_forced else ""
            self.status.set("STOPPING：等待资源退出："+"、".join(sorted(set(pending)))+suffix)
            self.root.after(50,self._poll_mode_shutdown)
            return
        result=self.pending_mode_result or ModeResult("failed",str(self.mode or "模式")+"失败")
        error=self.pending_mode_error
        name=str(self.mode or "模式")
        if self.mode_shutdown_forced:
            result.details["forced_capture_processes"]=list(dict.fromkeys(self.mode_shutdown_forced))
            result.summary+="；以下采集子进程未正常退出并已强制终止："+"、".join(result.details["forced_capture_processes"])
        self.mode_thread=None
        self.active_session=None
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
        self.set_controls(False)
        self.progress_value.set(0)
        self.status.set(result.summary)
        self._refresh_all()
        if self.closing:
            self._poll_shutdown()
            return
        if error:
            self.show_error(error)
        elif result.status=="failed":
            self.show_error(result.summary)
        else:
            title=name+("完成" if result.status=="completed" else "已停止")
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
        self.lifecycle.request_stop("failed",str(message))
        self.mode_state=MODE_STOPPING
        if self.stop_event is not None:
            self.stop_event.set()
        self.api.block_input()
        self._destroy_ask_window()
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
        self.ui(lambda:self.status.set(str(text)))
    def set_confidence(self,text):
        self.ui(lambda:self.confidence_text.set(str(text)))
    def set_input_status(self,text):
        value=str(text)
        if not value.startswith("自动输入："):
            value="自动输入："+value
        self.ui(lambda:self.input_text.set(value))
    def lock_input(self,reason="已锁定"):
        self.api.block_input()
        self.set_input_status(reason)
    def set_progress(self,value):
        self.ui(lambda:self.progress_value.set(max(0.0,min(100.0,float(value)))))
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
        closed={"done":False}
        def confirm():
            if closed["done"]:
                return
            closed["done"]=True
            self.result_modal=None
            self.result_modal_widget=None
            try:
                win.grab_release()
            except Exception:
                pass
            try:
                win.destroy()
            except Exception:
                pass
            if previous_grab is not None:
                try:
                    if previous_grab.winfo_exists():
                        previous_grab.grab_set()
                except Exception:
                    pass
        ttk.Button(frame,text="确认",command=confirm).pack(pady=(12,0),ipadx=28)
        win.bind("<Return>",lambda event:confirm())
        win.protocol("WM_DELETE_WINDOW",confirm)
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
        now=time.time()
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
            text=value.get().strip()
            if not text:
                error.set("名称不能为空")
                return
            if len(text)>80:
                error.set("名称不能超过80个字符")
                return
            result["value"]=text
            win.destroy()
        ttk.Button(buttons,text="确认",command=confirm).pack(side="left",padx=6)
        ttk.Button(buttons,text="取消",command=win.destroy).pack(side="left",padx=6)
        entry.bind("<Return>",lambda event:confirm())
        entry.bind("<Escape>",lambda event:win.destroy())
        entry.focus_set()
        win.wait_window()
        return result["value"]
    def confirm_dialog(self,title,text):
        result={"value":False}
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
            win.destroy()
        ttk.Button(buttons,text="确认",command=confirm).pack(side="left",padx=6)
        ttk.Button(buttons,text="取消",command=win.destroy).pack(side="left",padx=6)
        win.wait_window()
        return result["value"]
    def _refresh_all(self):
        self.game_text.set(self.selected_game["name"] if self.selected_game else "未选择")
        if self.selected_window:
            self.window_text.set(self.selected_window.get("title","未命名窗口"))
            try:
                rect=self.api.validate_target(self.selected_window,False)
                dpi=self.api.dpi_for_window(self.selected_window["hwnd"])
                path=str(self.selected_window.get("process_path","-"))
                self.window_detail.set("PID："+str(self.selected_window["pid"])+"  TID："+str(self.selected_window.get("window_thread_id","-"))+"  类名："+self.selected_window["class"]+"  客户区："+str(rect[2])+"×"+str(rect[3])+"  DPI："+str(dpi)+"  完整性："+str(self.selected_window.get("integrity","-"))+"  路径："+path)
                self.capture_text.set(self.api.capture_status(self.selected_window["hwnd"]))
            except Exception as error:
                self.window_detail.set("PID："+str(self.selected_window.get("pid","-"))+"  类名："+str(self.selected_window.get("class","-"))+"  "+str(error))
                self.capture_text.set("采集方式：等待目标窗口恢复")
        else:
            self.window_text.set("未选择")
            self.window_detail.set("PID：-  类名：-  客户区：-")
            self.capture_text.set("采集方式：未检测")
        self.refresh_data_stats()
    def refresh_data_stats(self):
        if not self.selected_game:
            self.sample_text.set("样本：有效0  废弃0  数据0 KB")
            self.model_text.set("模型：无  需要复习：否")
            return
        gid=self.selected_game["id"]
        try:
            stats=self.store.sample_stats(gid)
            self.sample_text.set("样本：有效"+str(stats["valid"])+"  废弃"+str(stats["invalid"])+"  数据"+str(round(stats["bytes"]/1024,1))+" KB")
            metadata=self.store.model_metadata(gid)
            needs=bool(next((game.get("needs_review") for game in self.store.games() if game["id"]==gid),False))
            if metadata:
                created=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(metadata.get("created",0)))
                validation=metadata.get("validation",{})
                holdout=int(validation.get("holdout",0) or 0)
                accepted=int(validation.get("accepted",0) or 0)
                coverage=float(validation.get("coverage",0.0) or 0.0)
                reject_rate=float(validation.get("reject_rate",1.0) or 0.0)
                overall=float(validation.get("overall_accuracy",0.0) or 0.0)
                accepted_error=validation.get("accepted_error_rate")
                status=str(validation.get("status","insufficient"))
                if accepted_error is None:
                    error_text="接受样本错误率无法计算（验证不足）"
                else:
                    error_text="接受样本错误率"+str(round(float(accepted_error)*100,2))+"%（"+("通过" if status=="passed" else "未通过")+"）"
                detail="留出"+str(holdout)+" 接受"+str(accepted)+" 覆盖"+str(round(coverage*100,1))+"% 总体正确"+str(round(overall*100,1))+"% 拒识"+str(round(reject_rate*100,1))+"%"
                model_kind="完整模型" if metadata.get("slot")=="complete" else "未验收临时模型（旧完整模型如存在则保留）"
                self.model_text.set(model_kind+"："+str(metadata.get("prototype_count",0))+"个原型  最近复习："+created+"  "+error_text+"  "+detail+"  需要复习："+("是" if needs else "否"))
            else:
                self.model_text.set("模型：无  需要复习："+("是" if needs else "否"))
        except Exception as error:
            self.sample_text.set("数据统计失败")
            self.model_text.set(str(error))
    def periodic_refresh(self):
        try:
            if not self.mode and not self.closing:
                self._refresh_all()
        finally:
            if not self.shutdown_started:
                try:
                    self.root.after(1200,self.periodic_refresh)
                except Exception:
                    pass
    def open_game_dialog(self):
        if self.mode:
            self.show_error("请先停止当前模式")
            return
        games=[dict(item) for item in self.store.games()]
        selected_id=self.selected_game["id"] if self.selected_game else None
        win=tk.Toplevel(self.root)
        win.title("游戏")
        win.geometry("540x450")
        win.transient(self.root)
        win.grab_set()
        frame=ttk.Frame(win,padding=16)
        frame.pack(fill="both",expand=True)
        ttk.Label(frame,text="选择、新建、编辑或删除游戏名称",font=("Microsoft YaHei UI",13,"bold")).pack(anchor="w",pady=(0,10))
        list_frame=ttk.Frame(frame)
        list_frame.pack(fill="both",expand=True)
        box=tk.Listbox(list_frame,exportselection=False,font=("Microsoft YaHei UI",11))
        scroll=ttk.Scrollbar(list_frame,orient="vertical",command=box.yview)
        box.configure(yscrollcommand=scroll.set)
        box.pack(side="left",fill="both",expand=True)
        scroll.pack(side="right",fill="y")
        def refresh(target=None):
            box.delete(0,"end")
            for game in games:
                suffix="  [需要复习]" if game.get("needs_review") else ""
                box.insert("end",game["name"]+suffix)
            wanted=target or selected_id
            for index,game in enumerate(games):
                if game["id"]==wanted:
                    box.selection_set(index)
                    box.see(index)
                    break
        def current_index():
            selection=box.curselection()
            return selection[0] if selection else None
        def add_game():
            name=self.prompt_text("新建游戏","输入游戏名称")
            if name is None:
                return
            if any(item["name"].casefold()==name.casefold() for item in games):
                self.show_error("游戏名称已存在")
                return
            game={"id":uuid.uuid4().hex,"name":name,"created":time.time(),"needs_review":False,"last_review":None}
            games.append(game)
            refresh(game["id"])
        def edit_game():
            index=current_index()
            if index is None:
                self.show_error("请先选择一个游戏")
                return
            name=self.prompt_text("编辑游戏","修改游戏名称",games[index]["name"])
            if name is None:
                return
            if any(position!=index and item["name"].casefold()==name.casefold() for position,item in enumerate(games)):
                self.show_error("游戏名称已存在")
                return
            games[index]["name"]=name
            refresh(games[index]["id"])
        def delete_game():
            index=current_index()
            if index is None:
                self.show_error("请先选择一个游戏")
                return
            item=dict(games[index])
            if not self.confirm_dialog("立即删除游戏","确认立即删除“"+item["name"]+"”及其学习数据、模型和备份吗？此操作不依赖对话框总“确认”。"):
                return
            if not self.store.delete_game(item["id"]):
                self.show_error("游戏已不存在")
                return
            games.pop(index)
            if self.selected_game and self.selected_game.get("id")==item["id"]:
                self.selected_game=None
            refresh(games[min(index,len(games)-1)]["id"] if games else None)
            self._refresh_all()
            self.status.set("已立即删除游戏："+item["name"])
        def confirm():
            selection=box.curselection()
            if not selection:
                self.show_error("请先选择一个游戏；如果列表为空，请先新建游戏")
                return
            chosen=games[selection[0]]
            self.store.replace_games(games,chosen["id"])
            self.selected_game=dict(chosen)
            self._refresh_all()
            self.status.set("已选择游戏："+chosen["name"])
            win.destroy()
        tools=ttk.Frame(frame)
        tools.pack(fill="x",pady=10)
        ttk.Button(tools,text="新建",command=add_game).pack(side="left",padx=(0,6))
        ttk.Button(tools,text="编辑",command=edit_game).pack(side="left",padx=6)
        ttk.Button(tools,text="删除（立即）",command=delete_game).pack(side="left",padx=6)
        actions=ttk.Frame(frame)
        actions.pack(fill="x")
        ttk.Button(actions,text="确认",command=confirm).pack(side="right",padx=(6,0))
        ttk.Button(actions,text="取消",command=win.destroy).pack(side="right")
        box.bind("<Double-Button-1>",lambda event:confirm())
        refresh()
        win.wait_visibility()
        box.focus_set()
    def open_window_dialog(self):
        if self.mode:
            self.show_error("请先停止当前模式")
            return
        win=tk.Toplevel(self.root)
        win.title("选择窗口")
        win.geometry("820x540")
        win.transient(self.root)
        win.grab_set()
        frame=ttk.Frame(win,padding=16)
        frame.pack(fill="both",expand=True)
        ttk.Label(frame,text="选择雷电模拟器窗口或其他窗口",font=("Microsoft YaHei UI",13,"bold")).pack(anchor="w",pady=(0,6))
        ttk.Label(frame,text="确认按钮只保存窗口身份，不再要求画面变化。学习、训练或请教开始前，程序会单独执行动态采集验收；静态菜单、暂停画面和棋盘画面可通过稳定性校准。",wraplength=760).pack(anchor="w",pady=(0,10))
        list_frame=ttk.Frame(frame)
        list_frame.pack(fill="both",expand=True)
        box=tk.Listbox(list_frame,exportselection=False,font=("Microsoft YaHei UI",10))
        scroll=ttk.Scrollbar(list_frame,orient="vertical",command=box.yview)
        box.configure(yscrollcommand=scroll.set)
        box.pack(side="left",fill="both",expand=True)
        scroll.pack(side="right",fill="y")
        status=tk.StringVar(value="请选择窗口")
        ttk.Label(frame,textvariable=status,wraplength=760).pack(anchor="w",fill="x",pady=(8,2))
        windows=[]
        state={"closed":False}
        def refresh():
            nonlocal windows
            try:
                windows=self.api.enum_windows()
            except Exception as error:
                self.show_error(str(error))
                return
            box.delete(0,"end")
            selected_index=None
            for index,item in enumerate(windows):
                prefix="[最小化] " if item["minimized"] else ""
                box.insert("end",prefix+item["title"]+"  [PID "+str(item["pid"])+"]  ["+item["class"]+"]")
                if self.selected_window and item["hwnd"]==self.selected_window["hwnd"] and item["pid"]==self.selected_window["pid"] and item["class"]==self.selected_window["class"]:
                    selected_index=index
            if selected_index is not None:
                box.selection_set(selected_index)
                box.see(selected_index)
        def confirm():
            selection=box.curselection()
            if not selection:
                self.show_error("请先选择一个窗口")
                return
            item=dict(windows[selection[0]])
            try:
                item=self.api.target_identity(item)
                rect=self.api.validate_target(item,False)
                item["integrity"]=self.api.validate_uipi(item)
                item["selected_rect"]=list(rect)
                item["client_size"]=[int(rect[2]),int(rect[3])]
                item["selected_dpi"]=self.api.dpi_for_window(item["hwnd"])
            except Exception as error:
                self.show_error(str(error))
                return
            previous=self.selected_window
            self.selected_window=item
            if not previous or any(previous.get(key)!=item.get(key) for key in ("hwnd","pid","class","process_created")):
                self.api.calibrations.pop(int(item["hwnd"]),None)
            self.api.reset_capture_backends(item)
            self.api.reset_frame_history(item["hwnd"])
            self._refresh_all()
            self.status.set("已保存窗口身份："+item["title"]+"；采集动态或稳定性验收将在学习、训练或请教开始前执行")
            state["closed"]=True
            try:
                win.grab_release()
            except Exception:
                pass
            win.destroy()
        def cancel():
            if state["closed"]:
                return
            state["closed"]=True
            try:
                win.grab_release()
            except Exception:
                pass
            win.destroy()
        tools=ttk.Frame(frame)
        tools.pack(fill="x",pady=(8,0))
        ttk.Button(tools,text="刷新",command=refresh).pack(side="left")
        ttk.Button(tools,text="确认",command=confirm).pack(side="right",padx=(6,0))
        ttk.Button(tools,text="取消",command=cancel).pack(side="right")
        box.bind("<Double-Button-1>",lambda event:confirm())
        win.protocol("WM_DELETE_WINDOW",cancel)
        refresh()
        win.wait_visibility()
        box.focus_set()
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
        for button in self.controls:
            button.configure(state="disabled" if running else "normal")
        if self.stop_button:
            self.stop_button.configure(state="normal" if running else "disabled")
    def start_worker(self,name,target,needs_window=False):
        if self.mode_state!=MODE_IDLE or self.closing:
            self.show_error("当前已有操作正在运行，请先停止")
            return
        try:
            self.require_game()
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
            status=requested if requested in {"completed","stopped","failed"} else "stopped"
            result=ModeResult(status,name+("已完成" if status=="completed" else "已停止"),{"reason":str(stopped_error)})
        except Exception:
            error=traceback.format_exc()
            result=ModeResult("failed",name+"失败")
        finally:
            self.api.block_input()
            self.set_input_status("已锁定")
        self.ui(lambda:self._begin_mode_stopping(result,error))
    def request_stop(self):
        if self.mode_state==MODE_IDLE:
            return
        self.lifecycle.request_stop("stopped","用户请求停止")
        self.mode_state=MODE_STOPPING
        if self.stop_event:
            self.stop_event.set()
        self.lock_input("因停止请求锁定")
        self._destroy_ask_window()
        if self.active_session is not None:
            self.active_session.request_stop()
        self.status.set("正在停止，已阻止新的鼠标按下并释放全部鼠标键")
    def _keyboard_escape(self,event=None):
        if self.mode_state==MODE_IDLE:
            return
        self.lifecycle.request_stop("stopped","ESC停止")
        self.mode_state=MODE_STOPPING
        if self.stop_event:
            self.stop_event.set()
        self.api.block_input()
        self.set_input_status("因ESC锁定")
    def wait_escape_release(self):
        while self.api.key_down(0x1B) and self.stop_event and not self.stop_event.is_set():
            time.sleep(0.04)
    def should_stop(self):
        if self.stop_event is None or self.stop_event.is_set():
            self.api.block_input()
            return True
        if self.api.key_down(0x1B):
            self.lifecycle.request_stop("stopped","ESC停止")
            self.mode_state=MODE_STOPPING
            self.stop_event.set()
            self.api.block_input()
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
        result={"previous_action":last_signature or "","seconds_since_previous":round(max(0.0,min(60.0,time.time()-last_time)) if last_time else 60.0,3),"previous_action_changed_frame":bool(last_changed),"motion_channel_valid":bool(motion_valid),"session_id":str(session_id or "unspecified"),"capture_method":str(capture_method or "unknown"),"repeat_policy":repeat_policy if repeat_policy in REPEAT_POLICIES else "one_shot","duplicate_threshold":float(calibration.get("duplicate",3.0)),"calibration":dict(calibration)}
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
        return {"recent_frame_count":len(frames),"recent_frame_deltas":deltas,"recent_actions":actions,"state_duration":round(max(0.0,min(60.0,time.time()-float(state_since))),3),"cursor":cursor_point,"window_size":[int(rect[2]),int(rect[3])] if len(rect)==4 else None,"dpi":int(frame.get("dpi",0)),"capture_method":str(frame.get("method","unknown"))}
    def start_learning(self):
        self.start_worker("学习",self.learning_controller.run,True)
    def learning_worker(self):
        return self.learning_controller.run()
    def _learning_worker_impl(self):
        game=self.require_game()
        target=self.require_window(False)
        hwnd=target["hwnd"]
        session_id="learn|"+uuid.uuid4().hex
        calibration=self.ensure_capture_calibration(target,"学习")
        if not self.api.request_foreground(hwnd):
            self.set_status("无法自动切换到目标窗口，学习将等待目标窗口成为前台")
        self.wait_escape_release()
        keyboard_state={"generation":0,"last_time":0.0}
        strict_violation=False
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
        state_since=time.time()
        with ModeSession(self,target) as session:
            frame_buffer=session.start_frames(20.0,2.0,0.1,"learning")
            keyboard=session.start_keyboard()
            monitor=session.start_mouse()
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
                nonlocal keyboard_count,strict_violation
                events=[event for event in keyboard.drain() if event.get("kind")=="other" and event.get("down")]
                if events:
                    strict_violation=True
                    keyboard_count+=len(events)
                    keyboard_state["generation"]=safe_int(keyboard_state["generation"],0)+1
                    keyboard_state["last_time"]=safe_float(events[0].get("time"),time.time())
                    isolation.signal("keyboard",keyboard_state["last_time"])
                    self.lifecycle.request_stop("stopped","学习检测到非ESC键盘输入，整段session无效")
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
                    last_action_time=time.time()
                    changed=True if last_action_feature is None else visual_distance(last_action_feature,frame["f"])>float(calibration.get("significant_change",60.0))
                    last_action_changed=changed
                    if changed:
                        state_since=time.time()
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
                now=time.time()
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
                for event in events:
                    if paused(event["time"]) or self.should_stop():
                        break
                    etype=event["type"]
                    x=event["x"]
                    y=event["y"]
                    event_time=event["time"]
                    inside=self.inside(x,y,rect)
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
                                    if click_gap<=0.42 and close:
                                        pending_click.pop(button,None)
                                        save(previous["frame"],{"kind":"double_click","button":button,"path":[previous["point"]],"duration":max(0.06,event_time-previous["time"])},"learn",1.3,previous["point"])
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
                if not active and not pending_click and now-last_negative>0.9 and now-last_motion_time>0.35:
                    frame=capture_safe(now)
                    if frame is not None:
                        cursor_point=self.normalize_point(polled_x,polled_y,rect) if polled_inside else None
                        save(frame,{"kind":"no_op","duration":0.45},"negative",0.6,cursor_point)
                    last_negative=now
                if now-last_update>0.45:
                    self.set_status("学习中：有效"+str(learned)+"  重复"+str(duplicates)+"  越界废弃"+str(discarded)+"  无效画面"+str(invalid_frames)+"  非ESC键"+str(keyboard_count)+"  键盘关联废弃"+str(keyboard_discarded))
                    last_update=now
                time.sleep(0.012)
        self.store.flush_samples()
        if strict_violation:
            removed=self.store.discard_session(game["id"],session_id)
            keyboard_discarded=max(keyboard_discarded,removed)
            return ModeResult("stopped","学习因检测到非ESC键盘输入而严格停止；整段session已作废并删除"+str(removed)+"个样本",{"invalid_session":session_id,"keyboard_events":keyboard_count})
        summary="学习已停止：有效"+str(learned)+"，重复或配额抑制"+str(duplicates)+"，越界废弃"+str(discarded)+"，无效画面"+str(invalid_frames)
        return ModeResult("stopped" if self.stop_event and self.stop_event.is_set() else "completed",summary)
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
            candidate_key=str(candidate.get("checksum") or candidate.get("created") or id(candidate))
            for other in comparisons:
                operations+=1
                if operations%32==0 and self.should_stop():
                    raise InputStopped("复习已停止")
                other_key=str(other.get("checksum") or other.get("created") or id(other))
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
    def rank_action_candidates(self,feature,prototypes,last_action_signature="",full_limit=16,temporal_context=None,query_coarse=None):
        if not feature_valid(feature):
            return []
        query_temporal=temporal_from_context(temporal_context or {})
        if not isinstance(query_coarse,(bytes,bytearray)) or len(query_coarse)!=COARSE_LEN:
            query_coarse=coarse_feature(feature)
        coarse_rank=[]
        best_per_cluster={}
        for index,proto in enumerate(prototypes):
            if index%64==0 and self.stop_event is not None and self.should_stop():
                return []
            pc=proto.get("coarse")
            if not isinstance(pc,(bytes,bytearray)) or len(pc)!=COARSE_LEN:
                pc=coarse_feature(proto["f"])
                proto["coarse"]=pc
            distance=coarse_distance(query_coarse,pc)
            coarse_rank.append((distance,proto))
            cluster_id=str(proto.get("cluster_id",proto.get("action_signature","")))
            if cluster_id and (cluster_id not in best_per_cluster or distance<best_per_cluster[cluster_id][0]):
                best_per_cluster[cluster_id]=(distance,proto)
        coarse_rank.sort(key=lambda item:item[0])
        selected=[]
        selected_ids=set()
        for distance,proto in coarse_rank[:max(8,min(12,int(full_limit)))]:
            if proto["id"] not in selected_ids:
                selected.append(proto)
                selected_ids.add(proto["id"])
        for distance,proto in sorted(best_per_cluster.values(),key=lambda item:item[0])[:12]:
            if proto["id"] not in selected_ids:
                selected.append(proto)
                selected_ids.add(proto["id"])
        grouped=defaultdict(list)
        for proto in selected:
            raw=feature_distance(feature,proto["f"])
            expected=str(proto.get("previous_action",""))
            penalty=0.0
            if expected and last_action_signature and expected!=last_action_signature:
                penalty=min(120.0,raw*0.08+18.0)
            tdistance=temporal_distance(query_temporal,proto.get("temporal",{}))
            temporal_penalty=tdistance*max(40.0,float(proto.get("threshold",100.0))*0.35)
            cluster_id=str(proto.get("cluster_id",proto.get("action_signature","")))
            if cluster_id:
                grouped[cluster_id].append((raw+penalty+temporal_penalty,raw,tdistance,proto))
        result=[]
        for cluster_id,items in grouped.items():
            items.sort(key=lambda item:item[0])
            best_score,best_distance,best_temporal,best_proto=items[0]
            vote_score=best_score if len(items)==1 else 0.88*best_score+0.12*items[1][0]
            action=normalize_action(best_proto["a"])
            result.append({"cluster_id":cluster_id,"canonical_action_signature":str(best_proto.get("canonical_action_signature") or action_signature(action)),"score":vote_score,"best_score":best_score,"distance":best_distance,"temporal_distance":best_temporal,"proto":best_proto,"a":action,"support":max(int(item[3].get("action_support",item[3].get("support",0))) for item in items),"prototype_votes":len(items)})
        result.sort(key=lambda item:item["score"])
        return result
    def evaluate_action_candidates(self,ranked):
        if not ranked:
            return {"accepted":False,"confidence":0.0,"reason":"没有候选或停止请求"}
        best=ranked[0]
        second=ranked[1] if len(ranked)>1 else None
        proto=best["proto"]
        strict_multiplier,min_support,margin_ratio=self.action_strictness(best["a"])
        threshold=float(proto["threshold"])/strict_multiplier
        second_score=second["score"] if second else float("inf")
        margin=second_score-best["score"]
        required_gap=max(float(proto.get("minimum_second_candidate_gap",16.0)),best["score"]*0.12)
        margin_ok=math.isinf(second_score) or best["score"]<second_score*margin_ratio and margin>required_gap
        support=int(best.get("support",0))
        rejected_distance=proto.get("nearest_rejected_distance")
        rejection_ok=rejected_distance is None or best["distance"]<float(rejected_distance)*0.65
        temporal_ok=float(best.get("temporal_distance",1.0))<=float(proto.get("temporal_threshold",0.0))
        query_backend=str(temporal_from_context(proto.get("temporal",{})).get("capture_method","unknown"))
        ambiguous=bool(proto.get("ambiguous",False))
        accepted=not ambiguous and best["distance"]<threshold and margin_ok and support>=min_support and rejection_ok and temporal_ok
        confidence=max(0.0,min(1.0,1.0-best["distance"]/max(1.0,threshold)))*(1.0-min(1.0,float(best.get("temporal_distance",1.0))))
        if ambiguous:
            reason="视觉与短时序状态仍对应不同动作，必须请教"
        elif not temporal_ok:
            reason="最近3至5帧、最近动作、状态时长或鼠标位置不匹配"
        else:
            reason="未达到动作阈值、差距或支持数要求"
        return {"accepted":accepted,"best":best,"second":second,"threshold":threshold,"margin":margin,"required_gap":required_gap,"support":support,"min_support":min_support,"confidence":confidence,"margin_ok":margin_ok,"rejection_ok":rejection_ok,"temporal_ok":temporal_ok,"ambiguous":ambiguous,"reason":reason,"nearest_rejected_distance":rejected_distance,"query_backend":query_backend}
    def start_review(self):
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
        self.review_distance_cache={}
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
        except InputStopped:
            if prototypes:
                partial={"created":time.time(),"samples":len(decorrelated),"training_samples":len(train),"invalid_samples":stats["invalid"],"prototypes":prototypes,"capture_backends":sorted({str(item.get("capture_method")) for item in train}),"validation":{"status":"stopped","training_checksums":train_checksums,"holdout_checksums":holdout_checksums},"stopped":True}
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
        errors=0
        accepted=0
        correct=0
        by_action=defaultdict(lambda:{"total":0,"accepted":0,"correct":0,"errors":0,"unrecognized":0,"negative_total":0,"false_positive":0})
        by_method=defaultdict(lambda:{"total":0,"accepted":0,"correct":0,"errors":0})
        dangerous_false=0
        dangerous_signatures={cluster["canonical_action_signature"] for cluster in action_clusters if cluster["a"]["kind"] in {"double_click","long_press","drag"} or cluster["a"].get("button") in {"right","middle"}}
        for index,sample in enumerate(holdout):
            if index%8==0 and self.should_stop():
                raise InputStopped("复习已停止")
            ranked=self.rank_action_candidates(sample["f"],prototypes,str(sample.get("context",{}).get("previous_action","")),16,sample.get("context",{}),sample.get("coarse"))
            decision=self.evaluate_action_candidates(ranked)
            expected=sample.get("_action_cluster")
            canonical=sample.get("_canonical_action_signature") or action_signature(sample["a"])
            method=str(sample.get("capture_method") or sample.get("context",{}).get("capture_method") or "unknown")
            arow=by_action[canonical]
            mrow=by_method[method]
            arow["total"]+=1
            mrow["total"]+=1
            predicted_signature=""
            if decision.get("accepted"):
                accepted+=1
                arow["accepted"]+=1
                mrow["accepted"]+=1
                predicted=decision["best"]
                predicted_signature=str(predicted.get("canonical_action_signature") or action_signature(predicted["a"]))
                if expected is not None and predicted["cluster_id"]==expected:
                    correct+=1
                    arow["correct"]+=1
                    mrow["correct"]+=1
                else:
                    errors+=1
                    arow["errors"]+=1
                    mrow["errors"]+=1
                    predicted_action=normalize_action(predicted["a"])
                    if predicted_action["kind"] in {"double_click","long_press","drag"} or predicted_action.get("button") in {"right","middle"}:
                        dangerous_false+=1
            else:
                arow["unrecognized"]+=1
            for signature in dangerous_signatures:
                if canonical!=signature:
                    by_action[signature]["negative_total"]+=1
                    if predicted_signature==signature:
                        by_action[signature]["false_positive"]+=1
            if index%5==0:
                self.set_progress(85+13*(index+1)/max(1,len(holdout)))
        holdout_count=len(holdout)
        coverage=accepted/holdout_count if holdout_count else 0.0
        accepted_error_rate=errors/accepted if accepted else None
        error_upper_95=binomial_error_upper(errors,accepted,0.95)
        overall_accuracy=correct/holdout_count if holdout_count else 0.0
        dangerous_false_rate=dangerous_false/max(1,holdout_count)
        per_action={}
        action_rules_pass=True
        train_signatures={str(item.get("_canonical_action_signature",action_signature(item["a"]))) for item in train}
        for signature in sorted(train_signatures|set(by_action)):
            row=dict(by_action[signature])
            row["recall"]=row["correct"]/row["total"] if row["total"] else 0.0
            row["coverage"]=row["accepted"]/row["total"] if row["total"] else 0.0
            row["accepted_error_rate"]=row["errors"]/row["accepted"] if row["accepted"] else None
            row["error_upper_95"]=binomial_error_upper(row["errors"],row["accepted"],0.95)
            action=next((cluster["a"] for cluster in action_clusters if cluster["canonical_action_signature"]==signature),{"kind":"no_op"})
            dangerous=action["kind"] in {"double_click","long_press","drag"} or action.get("button") in {"right","middle"}
            row["dangerous"]=dangerous
            if dangerous:
                row_pass=row["total"]>=50 and row["negative_total"]>=50 and row["errors"]==0 and row["false_positive"]==0 and row["coverage"]>=0.80
            else:
                row_pass=row["total"]>=20 and row["errors"]==0 and row["coverage"]>=0.80
            row["passed"]=bool(row_pass)
            action_rules_pass=action_rules_pass and bool(row_pass)
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
            row["passed"]=bool(row["total"]>=20 and row["errors"]==0 and row["coverage"]>=0.80)
            method_rules_pass=method_rules_pass and row["passed"]
            per_method[method]=row
        enough=bool(split_info.get("complete")) and int(split_info.get("session_count",0))>=2 and holdout_count>=150 and accepted>=150 and bool(train_methods)
        global_pass=coverage>=0.80 and overall_accuracy>=0.80 and error_upper_95<0.02 and dangerous_false==0 and uncovered_actions==0
        passed=bool(enough and global_pass and action_rules_pass and method_rules_pass and prototypes and not any(proto.get("ambiguous") for proto in prototypes))
        validation_status="passed" if passed else "insufficient" if not enough or not action_rules_pass or not method_rules_pass else "failed"
        validation={"status":validation_status,"split":str(split_info.get("mode","unknown")),"split_complete":bool(split_info.get("complete")),"split_reason":str(split_info.get("reason","")),"strata":int(split_info.get("strata",0)),"session_count":int(split_info.get("session_count",0)),"holdout_sessions":sorted(holdout_sessions),"minimum_holdout":150,"minimum_accepted":150,"minimum_ordinary_action_holdout":20,"minimum_dangerous_positive":50,"minimum_dangerous_negative":50,"minimum_coverage":0.80,"maximum_error_upper_95":0.02,"minimum_overall_accuracy":0.80,"maximum_dangerous_false":0,"holdout":holdout_count,"accepted":accepted,"errors":errors,"correct":correct,"coverage":coverage,"accepted_error_rate":accepted_error_rate,"error_upper_95":error_upper_95,"overall_accuracy":overall_accuracy,"dangerous_false":dangerous_false,"dangerous_false_rate":dangerous_false_rate,"uncovered_actions":uncovered_actions,"decorrelated_removed":decorrelated_removed,"per_action":per_action,"per_capture_method":per_method,"ambiguous_prototypes":sum(1 for proto in prototypes if proto.get("ambiguous")),"training_checksums":train_checksums,"holdout_checksums":holdout_checksums,"checksum_intersection":[]}
        model={"created":time.time(),"samples":len(decorrelated),"training_samples":len(train),"holdout_samples":len(holdout),"invalid_samples":stats["invalid"],"action_clusters":len(action_clusters),"rejection_constraints":rejection_constraints,"prototypes":prototypes,"capture_backends":train_methods,"validation":validation,"training_checksums":train_checksums,"holdout_checksums":holdout_checksums,"stopped":False}
        if not prototypes:
            raise RuntimeError("复习未生成可用原型")
        self.store.save_model(game["id"],model,validation_status=="passed")
        self.review_distance_cache={}
        self.set_progress(100)
        label="通过验收" if validation_status=="passed" else "验证不足，仅保存临时模型并禁止训练" if validation_status=="insufficient" else "验证失败，仅保存临时模型并禁止训练"
        error_text="无可计算值" if accepted_error_rate is None else str(round(accepted_error_rate*100,2))+"%"
        lines=["复习完成，"+label+"：原型"+str(len(prototypes))+"，独立session留出"+str(holdout_count)+"，接受"+str(accepted)+"，覆盖率"+str(round(coverage*100,2))+"%，接受错误率"+error_text+"，95%错误率上界"+str(round(error_upper_95*100,2))+"%，未覆盖动作"+str(uncovered_actions)+"，连续帧去相关移除"+str(decorrelated_removed)+("；留出失败原因："+str(split_info.get("reason")) if split_info.get("reason") else ""),"各动作独立留出验证："]
        for signature,row in sorted(per_action.items()):
            lines.append(signature+"：正例"+str(row["total"])+"，负例"+str(row["negative_total"])+"，接受"+str(row["accepted"])+"，错误"+str(row["errors"])+"，危险误触"+str(row["false_positive"])+"，"+("通过" if row["passed"] else "未通过"))
        lines.append("各采集后端独立验证：")
        for method,row in sorted(per_method.items()):
            lines.append(method+"：留出"+str(row["total"])+"，覆盖率"+str(round(row["coverage"]*100,2))+"%，错误"+str(row["errors"])+"，"+("通过" if row["passed"] else "未通过"))
        return ModeResult("completed","\n".join(lines),{"validation":validation_status})
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
        kind=normalize_action(action)["kind"]
        return {"click":0.8,"double_click":1.5,"long_press":2.0,"drag":1.2,"scroll_v":0.8,"scroll_h":1.0,"move":0.45,"hover":1.0,"no_op":0.25}.get(kind,1.0)
    def action_strictness(self,action):
        kind=normalize_action(action)["kind"]
        button=normalize_action(action).get("button")
        if kind in {"double_click","long_press","drag"} or button in {"right","middle"}:
            return 1.35,4,0.78
        if kind in {"scroll_v","scroll_h"}:
            return 1.2,3,0.80
        if kind in {"move","hover"}:
            return 1.0,2,0.84
        if kind=="no_op":
            return 1.0,1,0.88
        return 1.0,2,0.84
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
            self.require_window(False)
            model=self.store.load_model(game["id"])
            if not model or not model.get("prototypes"):
                raise RuntimeError("没有可用完整模型，请先学习并完成复习")
            if str(model.get("validation",{}).get("status",""))!="passed":
                raise RuntimeError("完整模型未通过严格独立留出验收，请重新学习、请教或复习")
            current=next((item for item in self.store.games() if item["id"]==game["id"]),{})
            if current.get("needs_review"):
                raise RuntimeError("模型需要复习：请先点击“复习”完成离线优化")
        except Exception as error:
            self.show_error(str(error))
            return
        self.start_worker("训练",self.training_controller.run,True)
    def training_worker(self):
        return self.training_controller.run()
    def _training_worker_impl(self):
        game=self.require_game()
        target=self.require_window(False)
        model=self.store.load_model(game["id"])
        prototypes=model["prototypes"]
        allowed_backends=set(model.get("capture_backends",[]))
        calibration=self.ensure_capture_calibration(target,"训练")
        validated_backend=str(calibration.get("validated_backend",""))
        if validated_backend not in allowed_backends:
            raise RuntimeError("当前采集后端未在完整模型中独立验证；请用该后端重新学习并复习")
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
        state_since=time.time()
        action_hits=defaultdict(deque)
        with ModeSession(self,target) as session:
            frame_buffer=session.start_frames(max(8.0,float(calibration.get("fps",15.0))),2.5,0.1,"training")
            keyboard=session.start_keyboard()
            mouse=session.start_mouse()
            self.lifecycle.mark_running()
            self.mode_state=MODE_RUNNING
            keyboard_interrupt=keyboard.other_event
            mouse_interrupt=mouse.input_event
            while not self.should_stop():
                key_events=[event for event in keyboard.drain() if event.get("kind")=="other" and event.get("down")]
                mouse_events=mouse.drain()
                if key_events or mouse_events:
                    keyboard_count+=len(key_events)
                    mouse_count+=len(mouse_events)
                    if key_events:
                        isolation.signal("keyboard",key_events[0].get("time"))
                        reason="检测到非ESC键盘输入，训练立即停止"
                        self.set_input_status("因键盘输入锁定")
                    else:
                        isolation.signal("mouse",mouse_events[0].get("time") if mouse_events else time.time())
                        reason="检测到物理鼠标输入，训练立即停止"
                        self.set_input_status("因人工鼠标输入锁定")
                    self.lifecycle.request_stop("stopped",reason)
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
                    self.api.block_input()
                    candidate_id=None
                    candidate_count=0
                    self.set_confidence("训练置信度：0%")
                    self.set_input_status("目标窗口不可用，已锁定")
                    self.set_status("目标窗口失去焦点，等待恢复；"+str(error))
                    time.sleep(0.08)
                    continue
                captured=frame_buffer.latest(None,0.8)
                if captured is None or not captured.get("usable_for_training"):
                    self.api.block_input()
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
                        self.api.block_input()
                        self.set_input_status("采集后端切换，等待连续确认")
                        self.set_status("原采集后端已熔断，已切换到剩余已验证后端："+validated_backend)
                        time.sleep(0.1)
                        continue
                    self.api.block_input()
                    self.set_status("替代采集后端未在模型中验证，拒绝自动动作")
                    time.sleep(0.1)
                    continue
                if captured.get("method")!=validated_backend or captured.get("method") not in allowed_backends:
                    self.api.block_input()
                    self.set_status("采集后端变化或未在模型中验证，拒绝自动动作；请重新学习和复习")
                    time.sleep(0.1)
                    continue
                feature=captured["f"]
                frame_change=float("inf")
                if captured["time"]!=previous_frame_stamp:
                    if previous_feature is not None:
                        frame_change=visual_distance(previous_feature,feature)
                        if frame_change>float(calibration.get("significant_change",60.0)):
                            state_since=time.time()
                    previous_feature=feature
                    previous_frame_stamp=captured["time"]
                if captured.get("capture_frozen"):
                    self.api.block_input()
                    self.set_input_status("采集后端冻结，已锁定")
                    self.set_status("检测到采集后端冻结而其他后端仍变化，训练停止输入并等待恢复")
                    time.sleep(0.1)
                    continue
                significant=last_action_feature is not None and visual_distance(last_action_feature,feature)>float(calibration.get("significant_change",60.0))
                if significant:
                    state_unlocked=True
                    no_change_count=0
                    state_since=time.time()
                temporal=self.build_temporal_context(frame_buffer,captured,recent_actions,state_since)
                if not temporal_from_context({**temporal,"previous_action_changed_frame":significant}).get("complete"):
                    self.api.block_input()
                    self.set_status("等待至少3帧短时序上下文")
                    time.sleep(0.05)
                    continue
                temporal["previous_action_changed_frame"]=bool(significant)
                ranked=self.rank_action_candidates(feature,prototypes,last_action_signature,18,temporal,captured.get("coarse"))
                decision=self.evaluate_action_candidates(ranked)
                if not decision.get("accepted"):
                    candidate_id=None
                    candidate_count=0
                    self.api.block_input()
                    self.set_input_status("等待连续确认")
                    self.set_confidence("训练置信度："+str(round(float(decision.get("confidence",0.0))*100,1))+"%")
                    self.set_status("训练中："+str(decision.get("reason","识别不确定"))+"；不执行动作并等待请教")
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
                if candidate_count<confirmations:
                    time.sleep(0.05)
                    continue
                action=normalize_action(best["a"])
                canonical=action_signature(action)
                proto=best["proto"]
                if captured["method"] not in set(proto.get("capture_methods",[])):
                    self.api.block_input()
                    self.set_status("当前原型未在该采集后端训练，拒绝动作")
                    time.sleep(0.1)
                    continue
                policy=str(proto.get("repeat_policy","one_shot"))
                max_rate=max(0.25,min(12.0,float(proto.get("max_rate",3.0))))
                if policy in {"one_shot","hold_until_change"} and last_cluster_id==cluster_id and not state_unlocked:
                    self.set_status("等待画面变化：该动作策略为"+policy)
                    time.sleep(0.1)
                    continue
                minimum_gap=max(self.action_cooldown(action) if policy=="one_shot" else 0.0,1.0/max_rate if policy in {"rate_limited","repeatable"} else 0.0)
                if time.time()-last_action_time<minimum_gap:
                    time.sleep(0.03)
                    continue
                now=time.time()
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
                    if fresh is None or not fresh.get("usable_for_training") or fresh.get("black_frame") or fresh.get("capture_frozen") or fresh.get("frozen_backend"):
                        raise InputStopped("动作前最后一帧不可用")
                    if fresh.get("method")!=validated_backend or fresh.get("method") not in allowed_backends or fresh.get("method") not in set(proto.get("capture_methods",[])):
                        raise InputStopped("动作前采集后端不匹配")
                    if keyboard_interrupt.is_set() or not keyboard.all_released():
                        raise InputStopped("检测到键盘输入")
                    if mouse_interrupt.is_set() or not mouse.stable_for(0.45):
                        raise InputStopped("检测到人工鼠标干扰")
                    fresh_temporal=self.build_temporal_context(frame_buffer,fresh,recent_actions,state_since)
                    fresh_temporal["previous_action_changed_frame"]=bool(significant)
                    fresh_ranked=self.rank_action_candidates(fresh["f"],prototypes,last_action_signature,18,fresh_temporal,fresh.get("coarse"))
                    fresh_decision=self.evaluate_action_candidates(fresh_ranked)
                    if not fresh_decision.get("accepted") or fresh_decision.get("best",{}).get("cluster_id")!=cluster_id:
                        raise InputStopped("动作前模型判断已变化")
                    if candidate_count<confirmations:
                        raise InputStopped("动作前连续帧确认不足")
                    before=fresh["f"]
                    needs_input=action.get("kind")!="no_op"
                    if needs_input:
                        self.set_input_status("允许执行单个动作")
                        self.api.allow_input(self.stop_event)
                    else:
                        self.api.block_input()
                        self.set_input_status("已锁定")
                    self.set_status("训练中："+self.action_text(action)+"；全部安全条件已通过；采集="+fresh["method"])
                    self.execute_action(target,action,fresh,mouse_interrupt,keyboard,keyboard_interrupt)
                except InputStopped:
                    if mouse_interrupt.is_set() or keyboard_interrupt.is_set() or not keyboard.all_released():
                        kind="mouse" if mouse_interrupt.is_set() else "keyboard"
                        isolation.signal(kind,time.time())
                        reason="检测到物理鼠标输入，训练立即停止" if kind=="mouse" else "检测到非ESC键盘输入，训练立即停止"
                        self.lifecycle.request_stop("stopped",reason)
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
                action_end=time.time()
                actions+=1
                hits.append(action_end)
                recent_actions.append(canonical)
                last_action_signature=canonical
                last_cluster_id=cluster_id
                last_action_time=action_end
                last_action_feature=before
                state_unlocked=policy in {"repeatable","rate_limited"}
                candidate_count=0
                delay=float(calibration.get("input_delay",0.24))
                deadline=time.monotonic()+delay
                while time.monotonic()<deadline and not self.should_stop():
                    time.sleep(0.02)
                after=None
                wait_end=time.monotonic()+max(0.35,delay*2.0)
                while time.monotonic()<wait_end and not self.should_stop():
                    candidate_after=frame_buffer.latest_after(action_end)
                    if candidate_after is not None and candidate_after.get("usable_for_training") and candidate_after.get("method")==validated_backend:
                        after=candidate_after
                        break
                    time.sleep(0.025)
                change=visual_distance(before,after["f"]) if after is not None else 0.0
                if change<float(calibration.get("post_action_change",45.0)):
                    no_change_count+=1
                    if policy in {"one_shot","hold_until_change"} and no_change_count>=2:
                        state_unlocked=False
                        self.api.block_input()
                        self.set_status("动作后未出现预期画面变化，暂停并等待请教")
                else:
                    no_change_count=0
                    state_unlocked=True
                    state_since=time.time()
                time.sleep(0.05)
        summary="训练已停止，AI执行"+str(actions)+"个鼠标动作；检测到非ESC键盘输入"+str(keyboard_count)+"次，物理鼠标输入"+str(mouse_count)+"次"
        return ModeResult("stopped" if self.stop_event and self.stop_event.is_set() else "completed",summary,{"strict_input_violation":isolation.kind})
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
            state={"frame":None,"choices":[],"candidates":[],"image":None,"locked":False,"recent_actions":deque(["<START>","<START>"],maxlen=4),"state_since":time.time(),"waiting":False}
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
                stamp=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(float(question_frame.get("time",time.time()))))
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
                    state["state_since"]=time.time()
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
            def custom():
                if state["locked"] or state["image"] is None:
                    return
                set_locked(True)
                dialog=tk.Toplevel(win)
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
                    try:
                        dialog.grab_release()
                    except Exception:
                        pass
                    dialog.destroy()
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
                        try:
                            dialog.grab_release()
                        except Exception:
                            pass
                        dialog.destroy()
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
    def close_ask(self,show_summary=True,wait_buffer=True,reason="completed"):
        if self.mode!="请教" and self.ask_window is None:
            return
        status="completed" if str(reason)=="completed" else "stopped"
        text="用户结束请教" if status=="completed" else "请教已停止"
        self.lifecycle.request_stop(status,text)
        self.mode_state=MODE_STOPPING
        if self.stop_event is not None:
            self.stop_event.set()
        self.api.block_input()
        self.set_input_status("已锁定")
        self._destroy_ask_window()
        if self.active_session is not None:
            self.active_session.request_stop()
        if not self.closing:
            self.status.set("请教正在停止，等待FrameBuffer、题目线程和采集进程退出")
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
            stats=self.store.sample_stats(game["id"])
            model=self.store.load_model(game["id"])
            text.set("游戏："+game["name"]+"\n有效样本："+str(stats["valid"])+"\n异常行："+str(stats["invalid"])+"\n数据大小："+str(round(stats["bytes"]/1024,1))+" KB\n模型原型："+str(len(model.get("prototypes",[])) if model else 0))
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
        def clear():
            if not self.confirm_dialog("清空数据","确认清空当前游戏的全部样本、模型和备份吗？此操作不可撤销。"):
                return
            self.store.clear_game_data(game["id"])
            message="已清空当前游戏的样本、模型、备份和拒绝记录"
            self.status.set(message)
            win.destroy()
            self.show_info("数据清空完成",message)
            self._refresh_all()
        buttons=ttk.Frame(frame)
        buttons.pack(side="bottom",fill="x",pady=(14,0))
        ttk.Button(buttons,text="压缩重复样本",command=compact).pack(side="left",padx=(0,6))
        ttk.Button(buttons,text="恢复模型备份",command=restore).pack(side="left",padx=6)
        ttk.Button(buttons,text="清空全部数据",command=clear).pack(side="left",padx=6)
        ttk.Button(buttons,text="关闭",command=win.destroy).pack(side="right")
        refresh()
    def close(self):
        if self.closing:
            return
        self.closing=True
        self.shutdown_deadline=time.monotonic()+8.0
        self.status.set("正在安全关闭：锁定输入并停止模式与采集")
        self.set_input_status("关闭过程中已锁定")
        if self.mode_state!=MODE_IDLE:
            self.lifecycle.request_stop("stopped","程序关闭")
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
            self.lifecycle.request_stop("stopped","程序关闭")
            if self.stop_event is not None:
                self.stop_event.set()
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
            if pending or not session_done:
                suffix="；关闭期限已到，采集子进程已请求强制终止" if deadline_reached else ""
                self.status.set("正在安全关闭：等待"+"、".join(sorted(set(pending)))+suffix)
                self.root.after(50,self._poll_shutdown)
                return
            self.mode_thread=None
            self.active_session=None
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
            self.status.set("正在安全关闭：等待采集子进程退出："+"、".join(capture_pending)+( "；已强制终止" if deadline_reached else ""))
            self.root.after(50,self._poll_shutdown)
            return
        self.status.set("正在安全关闭：刷新待写样本并关闭SQLite")
        try:
            store_closed=self.store.close(0.0)
        except Exception as error:
            self.status.set("SQLite关闭失败，输入仍保持锁定："+str(error))
            self.root.after(200,self._poll_shutdown)
            return
        if not store_closed:
            self.status.set("正在安全关闭：等待样本写入线程退出")
            self.root.after(100,self._poll_shutdown)
            return
        self.status.set("正在安全关闭：释放WGC、GDI和系统资源")
        try:
            if not self.api.close():
                self.status.set("正在安全关闭：等待采集资源退出")
                self.root.after(100,self._poll_shutdown)
                return
        except Exception as error:
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
    win.title("报错信息")
    win.geometry("700x390")
    frame=ttk.Frame(win,padding=14)
    frame.pack(fill="both",expand=True)
    widget=tk.Text(frame,wrap="word",font=("Microsoft YaHei UI",10))
    widget.pack(fill="both",expand=True)
    widget.insert("1.0",text)
    widget.configure(state="disabled")
    ttk.Button(frame,text="确认",command=root.destroy).pack(pady=(10,0))
    win.protocol("WM_DELETE_WINDOW",root.destroy)
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
            failures.append(str(name)+("："+str(detail) if detail else ""))
    check("源文件无空行",not any(not line.strip() for line in text.splitlines()))
    try:
        tokens=list(tokenize.tokenize(io.BytesIO(raw).readline))
        check("源文件无COMMENT",not any(token.type==tokenize.COMMENT for token in tokens))
    except Exception as error:
        check("源文件可分词",False,error)
    try:
        compile(text,str(source_path),"exec")
        tree=ast.parse(text,str(source_path))
        check("源文件可编译",True)
    except Exception as error:
        tree=None
        check("源文件可编译",False,error)
    required_classes={"ModeLifecycle","LearningController","ReviewController","TrainingController","TeachingController","PreviewCoordinateMapper","ResourceShutdownBarrier"}
    class_map={node.name:node for node in tree.body if isinstance(node,ast.ClassDef)} if tree is not None else {}
    check("单文件职责类完整",required_classes.issubset(class_map),sorted(required_classes-set(class_map)))
    app_methods={node.name for node in class_map["App"].body if isinstance(node,ast.FunctionDef)} if "App" in class_map else set()
    check("模式生命周期方法归属App",{"_begin_mode_stopping","_poll_mode_shutdown","_poll_shutdown","_create_ask_window"}.issubset(app_methods))
    points=([0.0,0.0],[1.0,1.0],[0.5,0.5],[0.137,0.829])
    roundtrip=True
    for point in points:
        canvas=PreviewCoordinateMapper.to_canvas(point)
        restored=PreviewCoordinateMapper.to_normalized(canvas[0],canvas[1])
        roundtrip=roundtrip and restored is not None and max(abs(restored[index]-point[index]) for index in range(2))<1e-9
    check("请教坐标往返",roundtrip)
    check("请教边框点击拒绝",PreviewCoordinateMapper.to_normalized(ASK_PREVIEW_X-1,ASK_PREVIEW_Y) is None and PreviewCoordinateMapper.to_normalized(ASK_PREVIEW_X,ASK_PREVIEW_Y-1) is None and PreviewCoordinateMapper.to_normalized(ASK_PREVIEW_X+ASK_PREVIEW_W,ASK_PREVIEW_Y) is None)
    actions=[{"kind":"click","button":"left","path":[[0.25,0.75]],"duration":0.08},{"kind":"double_click","button":"left","path":[[0.5,0.5]],"duration":0.16},{"kind":"long_press","button":"right","path":[[0.4,0.6]],"duration":0.8},{"kind":"drag","button":"left","path":[[0.1,0.2],[0.9,0.8]],"duration":0.5},{"kind":"scroll_v","delta":120,"path":[[0.5,0.5]],"duration":0.08},{"kind":"no_op","duration":0.3}]
    check("动作规范化",all(normalize_action(action) is not None and action_signature(action) for action in actions))
    check("INPUT仅鼠标联合体",[name for name,_ in INPUTUNION._fields_]==["mi"] and ("KEYBD"+"INPUT") not in text)
    input_type_assignments=[]
    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node,ast.Assign):
                for target in node.targets:
                    if isinstance(target,ast.Attribute) and target.attr=="type":
                        input_type_assignments.append(node.value.value if isinstance(node.value,ast.Constant) else None)
    check("自动INPUT类型恒为鼠标",bool(input_type_assignments) and all(value==0 for value in input_type_assignments),input_type_assignments)
    payload=add_checksum({"version":FORMAT_VERSION,"items":[1,2,3]})
    check("模型checksum",verify_checksum(payload) and not verify_checksum({**payload,"version":FORMAT_VERSION+1}))
    compressed=zlib.compress(canonical_bytes(payload),9)
    check("压缩上限正常",bounded_decompress(compressed,len(canonical_bytes(payload)))==canonical_bytes(payload))
    try:
        bounded_decompress(zlib.compress(b"x"*1024,9),128)
        compression_rejected=False
    except ValueError:
        compression_rejected=True
    check("压缩上限拒绝超限",compression_rejected)
    connection=sqlite3.connect(":memory:")
    try:
        connection.execute("CREATE TABLE sample(id INTEGER PRIMARY KEY,value TEXT NOT NULL)")
        connection.execute("INSERT INTO sample(value) VALUES('ok')")
        integrity=connection.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        connection.close()
    check("数据库完整性",str(integrity).lower()=="ok")
    train=[{"checksum":"train-a"},{"checksum":"train-b"}]
    holdout=[{"checksum":"holdout-a"},{"checksum":"holdout-b"}]
    try:
        assert_disjoint_checksums(train,holdout)
        disjoint=True
    except Exception:
        disjoint=False
    check("训练留出checksum不相交",disjoint and not checksum_set(train).intersection(checksum_set(holdout)))
    for stage in (MODE_STARTING,MODE_RUNNING,MODE_STOPPING):
        lifecycle=ModeLifecycle()
        event=lifecycle.begin("自检")
        if stage==MODE_RUNNING:
            lifecycle.mark_running()
        if stage==MODE_STOPPING:
            lifecycle.request_stop("stopped","预置")
        lifecycle.request_stop("stopped","ESC")
        check("ESC可中止"+stage,event.is_set() and lifecycle.snapshot()[0]==MODE_STOPPING)
    stop=threading.Event()
    isolation=StrictInputIsolation(stop)
    before=isolation.can_automate()
    isolation.signal("keyboard",time.time())
    check("人工输入后禁止自动输入",before and stop.is_set() and not isolation.can_automate())
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
    check("人工输入后无新SendInput",blocked and fake_bridge.user32.sent==0)
    class FakeResource:
        def __init__(self):
            self.running=True
        def stop(self,timeout=0.0):
            self.running=False
            return True
        def alive(self):
            return self.running
    resources={name:FakeResource() for name in ("FrameBuffer","KeyboardHook","MouseHook","CaptureProcess")}
    barrier=ResourceShutdownBarrier("自检",0.5)
    for name,resource in resources.items():
        barrier.add(name,resource.stop,resource.alive)
    barrier.request_stop()
    check("模式结束资源无存活",barrier.poll() and not barrier.pending_names() and not any(resource.alive() for resource in resources.values()))
    if tree is not None:
        for class_name in ("KeyboardMonitor","MouseMonitor"):
            node=class_map.get(class_name)
            segment=ast.get_source_segment(text,node) if node is not None else ""
            check(class_name+"回调轻量",all(fragment not in segment for fragment in ("block_input(","release_all_buttons(","self.app.ui(","on_other(","on_input(")))
    check("关闭期限已使用","shutdown_deadline=time.monotonic()+8.0" in text and "deadline_reached" in text)
    check("ESC主线程轮询","poll_global_escape" in app_methods and "self.root.after(35,self.poll_global_escape)" in text)
    check("危险验收样本阈值","positive_total>=50" in text and "negative_total>=50" in text and "holdout_count>=150" in text)
    result={"status":"passed" if not failures else "failed","checks":checks,"failures":failures}
    sys.stdout.write(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n")
    return 0 if not failures else 1
def main():
    if "--self-test" in sys.argv:
        raise SystemExit(run_self_test())
    enable_dpi_awareness()
    holder={"app":None}
    install_global_hooks(holder)
    root=tk.Tk()
    try:
        holder["app"]=App(root)
    except Exception:
        startup_error(root,traceback.format_exc())
    root.mainloop()
if __name__=="__main__":
    main()
