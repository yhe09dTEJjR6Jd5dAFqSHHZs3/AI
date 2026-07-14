import os
import sys
import json
import time
import math
import uuid
import random
import hashlib
import threading
import queue
import traceback
import statistics
import sqlite3
import zlib
import base64
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
FEATURE_ALGORITHM_VERSION=4
ACTION_ALGORITHM_VERSION=6
DATABASE_SCHEMA_VERSION=3
MAX_SAMPLES=1500
MAX_PROTOTYPES=320
SUPPORTED_BUTTONS={"left","right","middle"}
SUPPORTED_KINDS={"no_op","click","double_click","long_press","drag","scroll_v","scroll_h","move","hover"}
REPEAT_POLICIES={"one_shot","repeatable","hold_until_change","rate_limited"}
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
def finite_number(value):
    try:
        return math.isfinite(float(value))
    except Exception:
        return False
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
    weights=(0.30,0.19,0.19,0.22,0.10)
    total=0.0
    for channel,weight in enumerate(weights):
        offset=channel*PIXELS
        value=0.0
        for index in range(offset,offset+PIXELS):
            delta=float(a[index])-float(b[index])
            value+=delta*delta
        total+=weight*value/PIXELS
    return total
def visual_distance(a,b):
    if not feature_valid(a) or not feature_valid(b):
        return float("inf")
    weights=(0.34,0.22,0.22,0.22)
    total=0.0
    for channel,weight in enumerate(weights):
        offset=channel*PIXELS
        value=0.0
        for index in range(offset,offset+PIXELS):
            delta=float(a[index])-float(b[index])
            value+=delta*delta
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
    deltas=[]
    for value in source.get("recent_frame_deltas",[])[:4]:
        if finite_number(value):
            deltas.append(max(0.0,min(5000.0,float(value))))
    actions=[str(value) for value in source.get("recent_actions",[])[:4] if str(value)]
    cursor=source.get("cursor")
    if not isinstance(cursor,(list,tuple)) or len(cursor)<2 or not finite_number(cursor[0]) or not finite_number(cursor[1]):
        cursor=None
    else:
        cursor=[max(0.0,min(1.0,float(cursor[0]))),max(0.0,min(1.0,float(cursor[1])))]
    size=source.get("window_size")
    if not isinstance(size,(list,tuple)) or len(size)<2 or not finite_number(size[0]) or not finite_number(size[1]):
        size=None
    else:
        size=[max(1,int(size[0])),max(1,int(size[1]))]
    return {"recent_frame_count":int(source.get("recent_frame_count",0)),"recent_frame_deltas":deltas,"recent_actions":actions,"previous_action_changed_frame":bool(source.get("previous_action_changed_frame",True)),"state_duration":max(0.0,min(60.0,float(source.get("state_duration",0.0)))) if finite_number(source.get("state_duration",0.0)) else 0.0,"cursor":cursor,"window_size":size,"dpi":int(source.get("dpi",0)) if finite_number(source.get("dpi",0)) else 0,"capture_method":str(source.get("capture_method","unknown")),"complete":bool(int(source.get("recent_frame_count",0))>=3 and len(deltas)>=2 and len(actions)>=2 and cursor is not None and size is not None)}
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
        for key in ("session","pool","capture_item","winrt_device","context","device"):
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
    def _sample_bgra(self,raw,row_pitch,width,height,crop):
        left,top,crop_w,crop_h=crop
        result=bytearray(PREVIEW_W*PREVIEW_H*3)
        for oy in range(PREVIEW_H):
            sy=min(height-1,top+(2*oy+1)*crop_h//(2*PREVIEW_H))
            for ox in range(PREVIEW_W):
                sx=min(width-1,left+(2*ox+1)*crop_w//(2*PREVIEW_W))
                index=sy*row_pitch+sx*4
                position=(oy*PREVIEW_W+ox)*3
                result[position]=raw[index+2]
                result[position+1]=raw[index+1]
                result[position+2]=raw[index]
        return bytes(result)
    def capture(self,hwnd,client_rect):
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
        surface=access=texture=staging=None
        mapped=False
        try:
            surface=ctypes.c_void_p()
            self._check(self._call(frame,6,ctypes.c_long,[ctypes.POINTER(ctypes.c_void_p)],ctypes.byref(surface)),"读取捕获帧表面")
            access=self._query(surface,guid("A9B3D012-3DF2-4EE3-B8D1-8695F457D3C1"))
            texture=ctypes.c_void_p()
            texture_iid=guid("6F15AAF2-D208-4E89-9AB4-489535D34F9C")
            self._check(self._call(access,3,ctypes.c_long,[ctypes.POINTER(GUID),ctypes.POINTER(ctypes.c_void_p)],ctypes.byref(texture_iid),ctypes.byref(texture)),"获取D3D11纹理")
            desc=D3D11_TEXTURE2D_DESC()
            self._call(texture,10,None,[ctypes.POINTER(D3D11_TEXTURE2D_DESC)],ctypes.byref(desc))
            staging_desc=D3D11_TEXTURE2D_DESC(desc.Width,desc.Height,1,1,desc.Format,DXGI_SAMPLE_DESC(1,0),3,0,0x20000,0)
            staging=ctypes.c_void_p()
            self._check(self._call(item["device"],5,ctypes.c_long,[ctypes.POINTER(D3D11_TEXTURE2D_DESC),ctypes.c_void_p,ctypes.POINTER(ctypes.c_void_p)],ctypes.byref(staging_desc),None,ctypes.byref(staging)),"创建CPU可读捕获纹理")
            self._call(item["context"],47,None,[ctypes.c_void_p,ctypes.c_void_p],staging,texture)
            mapped_resource=D3D11_MAPPED_SUBRESOURCE()
            self._check(self._call(item["context"],14,ctypes.c_long,[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_uint32,ctypes.POINTER(D3D11_MAPPED_SUBRESOURCE)],staging,0,1,0,ctypes.byref(mapped_resource)),"映射捕获纹理")
            mapped=True
            raw=ctypes.string_at(mapped_resource.pData,int(mapped_resource.RowPitch)*int(desc.Height))
            cx,cy,cw,ch=client_rect
            wx,wy,ww,wh=window_rect
            scale_x=float(desc.Width)/max(1,ww)
            scale_y=float(desc.Height)/max(1,wh)
            left=max(0,min(int(desc.Width)-1,round((cx-wx)*scale_x)))
            top=max(0,min(int(desc.Height)-1,round((cy-wy)*scale_y)))
            crop_w=max(1,min(int(desc.Width)-left,round(cw*scale_x)))
            crop_h=max(1,min(int(desc.Height)-top,round(ch*scale_y)))
            return self._sample_bgra(raw,int(mapped_resource.RowPitch),int(desc.Width),int(desc.Height),(left,top,crop_w,crop_h))
        finally:
            if mapped:
                try:
                    self._call(item["context"],15,None,[ctypes.c_void_p,ctypes.c_uint32],staging,0)
                except Exception:
                    pass
            for obj in (staging,texture,access,surface):
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
        self.capture_tasks={}
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
    def integrity_for_pid(self,pid):
        handle=self.kernel32.OpenProcess(0x1000,False,int(pid))
        if not handle:
            raise TargetUnavailable("无法读取目标进程权限，拒绝自动输入")
        try:
            return self._token_integrity(handle)
        finally:
            self.kernel32.CloseHandle(handle)
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
        self.input_blocked=True
        self.release_all_buttons()
    def input_allowed(self):
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
    def _isolated_capture(self,key,callback,timeout=0.35):
        with self.capture_task_lock:
            existing=self.capture_tasks.get(key)
            if existing and existing["thread"].is_alive():
                raise CaptureUnavailable(str(key[1])+"采集线程疑似挂起，已隔离且不再等待")
            output=queue.Queue(maxsize=1)
            holder={}
            def run():
                try:
                    output.put((True,callback()),block=False)
                except BaseException as error:
                    try:
                        output.put((False,error),block=False)
                    except Exception:
                        pass
                finally:
                    with self.capture_task_lock:
                        if self.capture_tasks.get(key) is holder:
                            self.capture_tasks.pop(key,None)
            thread=threading.Thread(target=run,name="UniversalGameAI-Capture-"+str(key[1]),daemon=True)
            holder.update({"thread":thread,"output":output,"started":time.time()})
            self.capture_tasks[key]=holder
            thread.start()
        try:
            ok,value=output.get(timeout=max(0.05,float(timeout)))
        except queue.Empty:
            raise CaptureUnavailable(str(key[1])+"采集超时，后端已隔离；不会把超时结果用于学习或训练")
        if ok:
            return value
        raise value
    def valid(self,hwnd):
        return bool(hwnd and self.user32.IsWindow(wintypes.HWND(hwnd)))
    def class_name(self,hwnd):
        buffer=ctypes.create_unicode_buffer(512)
        if not self.user32.GetClassNameW(wintypes.HWND(hwnd),buffer,512):
            raise ctypes.WinError(ctypes.get_last_error())
        return buffer.value
    def pid(self,hwnd):
        value=wintypes.DWORD()
        if not self.user32.GetWindowThreadProcessId(wintypes.HWND(hwnd),ctypes.byref(value)):
            raise ctypes.WinError(ctypes.get_last_error())
        return int(value.value)
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
    def validate_target(self,target,require_foreground=True):
        if not isinstance(target,dict):
            raise TargetUnavailable("目标窗口身份信息无效")
        hwnd=int(target.get("hwnd",0))
        if not self.valid(hwnd):
            raise TargetUnavailable("目标窗口已关闭或句柄无效")
        current_pid=self.pid(hwnd)
        if current_pid!=int(target.get("pid",-1)):
            raise TargetUnavailable("目标窗口PID已变化，窗口句柄可能被复用")
        current_class=self.class_name(hwnd)
        if current_class!=str(target.get("class","")):
            raise TargetUnavailable("目标窗口类名已变化，窗口身份不确定")
        if self.user32.IsIconic(wintypes.HWND(hwnd)):
            raise TargetUnavailable("目标窗口已最小化")
        if require_foreground and self.foreground_hwnd()!=hwnd:
            raise TargetUnavailable("目标窗口失去焦点，等待恢复")
        rect=self.client_rect(hwnd)
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
    def _capture_print(self,hwnd,width,height):
        reference=self.user32.GetDC(wintypes.HWND(0))
        if not reference:
            raise ctypes.WinError(ctypes.get_last_error())
        memory=bitmap=old=bits=None
        try:
            memory,bitmap,old,bits=self._make_dib(reference,width,height)
            ctypes.memset(bits,0,width*height*4)
            if not self.user32.PrintWindow(wintypes.HWND(hwnd),memory,3):
                raise CaptureUnavailable("PrintWindow采集失败")
            raw=ctypes.string_at(bits.value,width*height*4)
            return self._rgb_from_raw(raw,width,height)
        finally:
            if memory and old:
                self.gdi32.SelectObject(memory,old)
            if bitmap:
                self.gdi32.DeleteObject(bitmap)
            if memory:
                self.gdi32.DeleteDC(memory)
            self.user32.ReleaseDC(wintypes.HWND(0),reference)
    def _capture_dc(self,source_hwnd,sx,sy,width,height):
        source=self.user32.GetDC(wintypes.HWND(source_hwnd))
        if not source:
            raise ctypes.WinError(ctypes.get_last_error())
        memory=bitmap=old=bits=None
        try:
            memory,bitmap,old,bits=self._make_dib(source,PREVIEW_W,PREVIEW_H)
            self.gdi32.SetStretchBltMode(memory,4)
            if not self.gdi32.StretchBlt(memory,0,0,PREVIEW_W,PREVIEW_H,source,sx,sy,width,height,0x00CC0020):
                raise CaptureUnavailable("窗口DC采集失败")
            raw=ctypes.string_at(bits.value,PREVIEW_W*PREVIEW_H*4)
            return self._rgb_from_raw(raw,PREVIEW_W,PREVIEW_H,PREVIEW_W,PREVIEW_H)
        finally:
            if memory and old:
                self.gdi32.SelectObject(memory,old)
            if bitmap:
                self.gdi32.DeleteObject(bitmap)
            if memory:
                self.gdi32.DeleteDC(memory)
            self.user32.ReleaseDC(wintypes.HWND(source_hwnd),source)
    def _rgb_to_gray(self,rgb):
        source=rgb_bytes(rgb)
        if source is None:
            return None
        return bytes((source[index]*77+source[index+1]*150+source[index+2]*29)>>8 for index in range(0,len(source),3))
    def _quality(self,rgb):
        source=preview_rgb_bytes(rgb)
        if source is None:
            return {"mean":0.0,"std":0.0,"spread":0,"black":True,"solid":True,"low_information":True,"valid":False,"protected_or_black":True}
        gray=[(source[index]*77+source[index+1]*150+source[index+2]*29)>>8 for index in range(0,len(source),3)]
        mean=sum(gray)/len(gray)
        variance=sum((value-mean)*(value-mean) for value in gray)/len(gray)
        std=math.sqrt(variance)
        spread=max(gray)-min(gray)
        black=max(gray)<10 or mean<2.5
        solid=std<0.9 or spread<3
        return {"mean":mean,"std":std,"spread":spread,"black":black,"solid":solid,"low_information":bool(black or solid),"valid":True,"protected_or_black":bool(black)}
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
        key=(int(hwnd),str(method))
        previous=self.capture_health.get(key)
        if previous and previous["digest"]==digest:
            unchanged_since=previous["unchanged_since"]
        else:
            unchanged_since=now
        stale=now-unchanged_since>4.0
        self.capture_health[key]={"digest":digest,"unchanged_since":unchanged_since,"last":now,"stale":stale}
        return stale
    def capture_gray(self,target,require_foreground_for_desktop=True,validation_mode=False):
        rect=self.validate_target(target,False)
        hwnd=int(target["hwnd"])
        x,y,width,height=rect
        if width<FEATURE_W or height<FEATURE_H:
            raise CaptureUnavailable("客户区尺寸异常，拒绝采集")
        attempts=[]
        candidates=[]
        calibration=self.calibrations.get(hwnd,{})
        validated_method=str(calibration.get("validated_backend",""))
        backends=[("Windows Graphics Capture",lambda:self.wgc.capture(hwnd,rect),False),("PrintWindow客户区",lambda:self._capture_print(hwnd,width,height),True),("窗口DC",lambda:self._capture_dc(hwnd,0,0,width,height),True)]
        if not require_foreground_for_desktop or self.foreground_hwnd()==hwnd:
            backends.append(("前台桌面裁剪",lambda:self._capture_dc(0,x,y,width,height),True))
        else:
            attempts.append("前台桌面裁剪被跳过：目标窗口不在前台")
        if validated_method:
            backends.sort(key=lambda item:0 if item[0]==validated_method else 1)
        for priority,(name,callback,isolate) in enumerate(backends):
            try:
                preview=preview_rgb_bytes(self._isolated_capture((hwnd,name),callback,0.35) if isolate else callback())
                if preview is None:
                    raise CaptureUnavailable("返回画面尺寸无效")
                model_rgb=resize_rgb(preview,PREVIEW_W,PREVIEW_H,FEATURE_W,FEATURE_H)
                quality=self._quality(preview)
                stale=self._health(hwnd,name,preview)
                validation_identity=bool(calibration.get("dynamic_passed") and int(calibration.get("validated_pid",-1))==self.pid(hwnd) and str(calibration.get("validated_class",""))==self.class_name(hwnd) and int(calibration.get("validated_dpi",0))==self.dpi_for_window(hwnd) and list(calibration.get("validated_rect",[0,0,0,0]))[2:4]==[int(width),int(height)])
                backend_validated=bool(validation_mode or validated_method and name==validated_method and validation_identity)
                backend_changed=bool(validated_method and (name!=validated_method or not validation_identity))
                capture_valid=bool(quality["valid"] and not quality["low_information"] and not stale)
                usable=bool(capture_valid and backend_validated and not backend_changed)
                candidate={"rgb":model_rgb,"gray":self._rgb_to_gray(model_rgb),"preview_rgb":preview,"preview_width":PREVIEW_W,"preview_height":PREVIEW_H,"method":name,"quality":quality,"priority":priority,"stale":stale,"capture_valid":capture_valid,"backend_validated":backend_validated,"usable_for_learning":usable,"usable_for_training":usable,"usable_for_teaching":usable,"protected_or_black":bool(quality.get("protected_or_black")),"backend_changed":backend_changed}
                candidates.append(candidate)
                if usable or validation_mode and capture_valid:
                    self.capture_reports[hwnd]="当前采集："+name+"；画面有效；后端"+("已验收" if backend_validated else "待验收")
                    return candidate
                reason=[]
                if quality["low_information"]:
                    reason.append("黑屏或纯色")
                if stale:
                    reason.append("长时间重复")
                if backend_changed:
                    reason.append("后端突然变化")
                if not backend_validated:
                    reason.append("后端未验收")
                attempts.append(name+"："+"、".join(reason or ["不可用于自动输入"]))
            except Exception as error:
                attempts.append(name+"失败："+str(error))
        if candidates:
            chosen=min(candidates,key=lambda item:(not item["capture_valid"],item["backend_changed"],item["priority"]))
            chosen=dict(chosen)
            chosen.update({"usable_for_learning":False,"usable_for_training":False,"usable_for_teaching":False})
            self.capture_reports[hwnd]="采集画面仅可预览，已拒绝学习/训练/请教："+"；".join(attempts)
            return chosen
        self.capture_reports[hwnd]="采集失败："+"；".join(attempts)
        raise CaptureUnavailable("无法采集目标窗口："+"；".join(attempts))
    def capture(self,target,require_foreground_for_desktop=True):
        item=self.capture_gray(target,require_foreground_for_desktop)
        item["f"]=self._features(item["rgb"],int(target["hwnd"]))
        item["motion_valid"]=True
        item["rect"]=self.validate_target(target,False)
        item["dpi"]=self.dpi_for_window(int(target["hwnd"]))
        return item
    def capture_status(self,hwnd):
        return self.capture_reports.get(int(hwnd),"尚未完成动态采集验收；未验收后端只能预览，不能学习或训练")
    def calibration_for(self,target):
        hwnd=int(target.get("hwnd",0)) if isinstance(target,dict) else int(target or 0)
        return dict(self.calibrations.get(hwnd,{"noise":4.0,"visual_cluster":420.0,"significant_change":60.0,"post_action_change":45.0,"freeze_change":1.5,"freeze_frames":30,"confirm_frames":3,"duplicate":3.0,"fps":10.0,"input_delay":0.24,"validated_backend":"","dynamic_passed":False}))
    def calibrate(self,target,duration=1.8,stop_event=None,progress=None):
        hwnd=int(target["hwnd"])
        self.validate_target(target,False)
        integrity=self.validate_uipi(target)
        with self.frame_lock:
            for key in [key for key in self.capture_health if key[0]==hwnd]:
                self.capture_health.pop(key,None)
        deadline=time.monotonic()+max(1.2,min(3.0,float(duration)))
        features=[]
        methods=[]
        stamps=[]
        previous_rgb=None
        while time.monotonic()<deadline:
            if stop_event is not None and stop_event.is_set():
                raise RuntimeError("窗口校准已取消")
            self.validate_target(target,False)
            captured=self.capture_gray(target,True,True)
            if not captured.get("capture_valid"):
                raise CaptureUnavailable("动态校准遇到无效画面")
            feature=self.feature_from_rgb(captured["rgb"],previous_rgb)
            previous_rgb=captured["rgb"]
            features.append(feature)
            methods.append(captured["method"])
            stamps.append(time.time())
            if progress:
                progress(min(1.0,1.0-max(0.0,deadline-time.monotonic())/max(0.1,float(duration))))
            time.sleep(0.06)
        if len(features)<8:
            raise CaptureUnavailable("动态校准有效帧不足")
        if len(set(methods))!=1:
            raise CaptureUnavailable("校准期间采集后端发生变化，拒绝确认窗口")
        changes=[visual_distance(a,b) for a,b in zip(features,features[1:])]
        unique=len({hashlib.sha256(bytes(feature[:PIXELS])).digest() for feature in features})
        if unique<2 or not changes or max(changes)<1.0:
            raise CaptureUnavailable("未检测到采集画面动态变化；请让目标窗口画面发生变化后重新确认")
        noise=max(0.5,quantile(changes,0.5))
        fps=(len(stamps)-1)/max(0.01,stamps[-1]-stamps[0]) if len(stamps)>1 else 8.0
        rect=self.validate_target(target,False)
        dpi=self.dpi_for_window(hwnd)
        method=methods[0]
        result={"noise":noise,"visual_cluster":max(80.0,min(1400.0,noise*9.0+120.0)),"significant_change":max(18.0,min(260.0,noise*4.5+18.0)),"post_action_change":max(14.0,min(220.0,noise*3.2+14.0)),"freeze_change":max(0.4,noise*0.22),"freeze_frames":max(18,min(80,round(fps*3.0))),"confirm_frames":3 if fps>=12 else 4,"duplicate":max(1.0,min(18.0,noise*0.65)),"fps":fps,"input_delay":max(0.16,min(0.55,3.0/max(5.0,fps))),"method":method,"validated_backend":method,"dynamic_passed":True,"validated_at":time.time(),"validated_rect":list(rect),"validated_dpi":dpi,"validated_pid":int(target["pid"]),"validated_class":str(target["class"]),"integrity":integrity}
        self.calibrations[hwnd]=result
        self.capture_reports[hwnd]="当前采集："+method+"；动态检测通过；帧率"+str(round(fps,1))+"fps；后端已验收"
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
class KeyboardMonitor:
    def __init__(self,bridge,on_escape=None,on_other=None):
        self.bridge=bridge
        self.on_escape=on_escape
        self.on_other=on_other
        self.events=deque(maxlen=2000)
        self.lock=threading.RLock()
        self.held=set()
        self.thread=None
        self.thread_id=0
        self.hook=None
        self.callback=None
        self.ready=threading.Event()
        self.error=None
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
    def _run(self):
        try:
            self.thread_id=int(self.bridge.kernel32.GetCurrentThreadId())
            def callback(code,wparam,lparam):
                if code>=0 and int(wparam) in {0x0100,0x0101,0x0104,0x0105}:
                    data=ctypes.cast(lparam,ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                    vk=int(data.vkCode)
                    down=int(wparam) in {0x0100,0x0104}
                    now=time.time()
                    event={"vk":vk,"down":down,"time":now,"injected":bool(int(data.flags)&0x12)}
                    first_down=False
                    with self.lock:
                        if down:
                            first_down=vk not in self.held
                            self.held.add(vk)
                        else:
                            self.held.discard(vk)
                        self.events.append(event)
                        if first_down and vk!=0x1B:
                            self.non_escape_count+=1
                    if first_down and vk==0x1B and self.on_escape:
                        try:
                            self.on_escape(event)
                        except Exception:
                            pass
                    elif first_down and vk!=0x1B and self.on_other:
                        try:
                            self.on_other(event)
                        except Exception:
                            pass
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
        with self.lock:
            result=list(self.events)
            self.events.clear()
        return result
    def all_released(self):
        with self.lock:
            return not any(vk!=0x1B for vk in self.held)
    def stop(self,timeout=1.0):
        if self.thread_id:
            try:
                self.bridge.user32.PostThreadMessageW(self.thread_id,0x0012,0,0)
            except Exception:
                pass
        if self.thread and self.thread.is_alive() and self.thread is not threading.current_thread():
            self.thread.join(max(0.0,float(timeout)))
        return not bool(self.thread and self.thread.is_alive())
class MouseMonitor:
    def __init__(self,bridge):
        self.bridge=bridge
        self.events=deque(maxlen=6000)
        self.lock=threading.Lock()
        self.thread=None
        self.thread_id=0
        self.hook=None
        self.callback=None
        self.ready=threading.Event()
        self.error=None
        self.last_move=0.0
    def start(self):
        self.thread=threading.Thread(target=self._run,name="UniversalGameAI-MouseHook",daemon=True)
        self.thread.start()
        if not self.ready.wait(2.0):
            raise RuntimeError("鼠标监听器启动超时")
        if self.error:
            raise RuntimeError(self.error)
        if not self.hook:
            raise RuntimeError("无法安装鼠标监听器")
    def _append(self,event):
        with self.lock:
            self.events.append(event)
    def _run(self):
        try:
            self.thread_id=int(self.bridge.kernel32.GetCurrentThreadId())
            messages={0x0200:"move",0x0201:"left_down",0x0202:"left_up",0x0204:"right_down",0x0205:"right_up",0x0207:"middle_down",0x0208:"middle_up",0x020A:"wheel",0x020E:"hwheel"}
            def callback(code,wparam,lparam):
                if code>=0 and int(wparam) in messages:
                    data=ctypes.cast(lparam,ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                    if int(data.flags)&0x00000003:
                        return self.bridge.user32.CallNextHookEx(self.hook,code,wparam,lparam)
                    now=time.time()
                    kind=messages[int(wparam)]
                    if kind!="move" or now-self.last_move>=0.018:
                        if kind=="move":
                            self.last_move=now
                        event={"type":kind,"x":int(data.pt.x),"y":int(data.pt.y),"time":now}
                        if kind in {"wheel","hwheel"}:
                            raw=(int(data.mouseData)>>16)&0xffff
                            event["delta"]=raw-0x10000 if raw&0x8000 else raw
                        self._append(event)
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
        with self.lock:
            result=list(self.events)
            self.events.clear()
        return result
    def stop(self,timeout=1.0):
        if self.thread_id:
            try:
                self.bridge.user32.PostThreadMessageW(self.thread_id,0x0012,0,0)
            except Exception:
                pass
        if self.thread and self.thread.is_alive() and self.thread is not threading.current_thread():
            self.thread.join(max(0.0,float(timeout)))
        return not bool(self.thread and self.thread.is_alive())
class FrameBuffer:
    def __init__(self,bridge,target,hz=20.0,seconds=2.0,motion_interval=0.1):
        self.bridge=bridge
        self.target=dict(target)
        self.interval=1.0/max(5.0,float(hz))
        self.motion_interval=max(0.05,min(0.25,float(motion_interval)))
        self.frames=deque(maxlen=max(12,int(float(hz)*float(seconds))+4))
        self.lock=threading.RLock()
        self.stop_event=threading.Event()
        self.ready=threading.Event()
        self.thread=None
        self.last_error=""
    def start(self):
        self.bridge.reset_frame_history(self.target.get("hwnd"))
        self.stop_event.clear()
        self.thread=threading.Thread(target=self._run,name="UniversalGameAI-FrameBuffer",daemon=True)
        self.thread.start()
        return self
    def _run(self):
        thread_id=threading.get_ident()
        next_time=time.monotonic()
        try:
            while not self.stop_event.is_set():
                try:
                    captured=self.bridge.capture_gray(self.target,True)
                    stamp=time.time()
                    rgb=captured["rgb"]
                    gray=captured["gray"]
                    with self.lock:
                        previous=None
                        for frame in reversed(self.frames):
                            if frame["time"]<=stamp-self.motion_interval:
                                previous=frame["rgb"]
                                break
                    feature=self.bridge.feature_from_rgb(rgb,previous)
                    rect=self.bridge.validate_target(self.target,False)
                    frame={"time":stamp,"f":feature,"coarse":coarse_feature(feature),"gray":gray,"rgb":rgb,"preview_rgb":captured.get("preview_rgb"),"preview_width":captured.get("preview_width",PREVIEW_W),"preview_height":captured.get("preview_height",PREVIEW_H),"method":captured["method"],"quality":captured["quality"],"motion_valid":previous is not None,"rect":rect,"dpi":self.bridge.dpi_for_window(int(self.target["hwnd"])),"capture_valid":bool(captured.get("capture_valid")),"backend_validated":bool(captured.get("backend_validated")),"usable_for_learning":bool(captured.get("usable_for_learning")),"usable_for_training":bool(captured.get("usable_for_training")),"usable_for_teaching":bool(captured.get("usable_for_teaching")),"stale":bool(captured.get("stale")),"protected_or_black":bool(captured.get("protected_or_black")),"backend_changed":bool(captured.get("backend_changed"))}
                    with self.lock:
                        self.frames.append(frame)
                    self.last_error="" if frame["capture_valid"] else "画面无效或后端未验收"
                    self.ready.set()
                except Exception as error:
                    self.last_error=str(error)
                next_time=max(next_time+self.interval,time.monotonic())
                self.stop_event.wait(max(0.001,next_time-time.monotonic()))
        finally:
            try:
                self.bridge.wgc.release_thread(thread_id)
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
        if wait and self.thread and self.thread.is_alive() and self.thread is not threading.current_thread():
            self.thread.join(max(0.0,float(timeout)))
        return not bool(self.thread and self.thread.is_alive())
    def wait_for_usable(self,purpose,timeout=3.0,external_stop=None):
        deadline=time.monotonic()+max(0.1,float(timeout))
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
            self.ready.wait(0.05)
        raise CaptureUnavailable("未在限定时间内获得可用于"+str(purpose)+"的已验收画面："+(self.last_error or "未知原因"))
    def alive(self):
        return bool(self.thread and self.thread.is_alive())
class ModeSession:
    def __init__(self,app,target):
        self.app=app
        self.target=dict(target)
        self.resources=[]
        self.frame_buffer=None
        self.mouse_monitor=None
        self.keyboard_monitor=None
    def start_frames(self,hz,seconds,motion_interval,purpose):
        buffer=FrameBuffer(self.app.api,self.target,hz,seconds,motion_interval)
        self.resources.append(("frame",buffer))
        buffer.start()
        buffer.wait_for_usable(purpose,3.0,self.app.stop_event)
        self.frame_buffer=buffer
        return buffer
    def start_keyboard(self,on_other=None):
        monitor=KeyboardMonitor(self.app.api,self.app._keyboard_escape,on_other)
        self.resources.append(("keyboard",monitor))
        monitor.start()
        self.keyboard_monitor=monitor
        return monitor
    def start_mouse(self):
        monitor=MouseMonitor(self.app.api)
        self.resources.append(("mouse",monitor))
        monitor.start()
        self.mouse_monitor=monitor
        return monitor
    def close(self):
        deadline=time.monotonic()+1.5
        for kind,resource in reversed(self.resources):
            remaining=max(0.0,deadline-time.monotonic())
            try:
                resource.stop(min(1.0,remaining)) if kind!="frame" else resource.stop(True,min(1.0,remaining))
            except Exception:
                pass
        self.resources.clear()
        self.app.api.block_input()
    def __enter__(self):
        return self
    def __exit__(self,exc_type,exc_value,exc_traceback):
        self.close()
        return False
class DataStore:
    def __init__(self):
        local=os.environ.get("LOCALAPPDATA")
        self.base=(Path(local) if local else Path.home()/"AppData"/"Local")/APP_NAME
        self.base.mkdir(parents=True,exist_ok=True)
        self.db_path=self.base/"universal_game_ai.db"
        self.lock=threading.RLock()
        self.model_cache={}
        self.closed=False
        self.db=sqlite3.connect(str(self.db_path),timeout=1.0,check_same_thread=False)
        self.db.row_factory=sqlite3.Row
        with self.db:
            self.db.execute("PRAGMA foreign_keys=ON")
            self.db.execute("PRAGMA journal_mode=DELETE")
            self.db.execute("PRAGMA synchronous=FULL")
            self.db.execute("PRAGMA temp_store=MEMORY")
        self._initialize_schema()
        self._migrate_legacy()
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
        self.db.execute("CREATE TABLE IF NOT EXISTS model_backups(id INTEGER PRIMARY KEY AUTOINCREMENT,game_id TEXT NOT NULL,created REAL NOT NULL,prototype_count INTEGER NOT NULL,validation TEXT NOT NULL,payload BLOB NOT NULL,checksum TEXT NOT NULL)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_model_backups_game_created ON model_backups(game_id,created DESC)")
        self.db.execute("CREATE TABLE IF NOT EXISTS rejections(id INTEGER PRIMARY KEY AUTOINCREMENT,game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,created REAL NOT NULL,feature_algorithm_version INTEGER NOT NULL,feature BLOB NOT NULL,coarse BLOB NOT NULL,thumbnail BLOB,candidates TEXT NOT NULL,source TEXT NOT NULL,session_id TEXT NOT NULL,capture_method TEXT NOT NULL)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_rejections_game_created ON rejections(game_id,created DESC)")
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
        for game in config.get("games",[]):
            if not isinstance(game,dict) or not game.get("id") or not str(game.get("name","")).strip():
                raise RuntimeError("旧配置包含无效游戏，迁移已整体取消")
            gid=str(game["id"])
            if gid in game_ids:
                raise RuntimeError("旧配置包含重复游戏ID，迁移已整体取消")
            game_ids.add(gid)
            games.append((gid,str(game["name"]).strip(),float(game.get("created",time.time())),1 if game.get("needs_review") else 0,game.get("last_review")))
        sample_rows=[]
        samples_dir=self.base/"samples"
        if samples_dir.exists():
            for path in sorted(samples_dir.glob("*.jsonl")):
                gid=path.stem
                if gid not in game_ids:
                    raise RuntimeError("旧样本引用不存在的游戏，迁移已整体取消："+path.name)
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
                        except Exception as error:
                            raise RuntimeError("旧样本第"+str(line_number)+"行无效，迁移已整体取消："+path.name+"；"+str(error))
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
                    raise RuntimeError("旧模型损坏，迁移已整体取消："+path.name)
                gid=str(raw.get("game_id",path.stem.split(".")[0]))
                if gid not in game_ids:
                    raise RuntimeError("旧模型引用不存在的游戏，迁移已整体取消："+path.name)
                complete=bool(raw.get("complete",True))
                upgraded=self._upgrade_model(raw,gid,complete)
                if not upgraded or not self._model_valid(upgraded,gid,complete):
                    raise RuntimeError("旧模型无法升级，迁移已整体取消："+path.name)
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
                self.db.execute("DELETE FROM games WHERE id=?",(gid,))
                self.model_cache.pop(gid,None)
            for item in cleaned:
                self.db.execute("INSERT INTO games(id,name,created,needs_review,last_review) VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,created=excluded.created,needs_review=excluded.needs_review,last_review=excluded.last_review",(item["id"],item["name"],item["created"],item["needs_review"],item["last_review"]))
            self.db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('selected_game',?)",(selected,))
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
            rows=self.db.execute("SELECT feature,feature_algorithm_version,context FROM samples WHERE game_id=? AND action_signature=? ORDER BY created DESC,id DESC LIMIT 36",(gid,signature)).fetchall()
        query=feature_bytes(feature)
        query_coarse=coarse_feature(query)
        query_context=context if isinstance(context,dict) else {}
        for row in rows:
            try:
                candidate=upgrade_feature(zlib.decompress(row["feature"]),row["feature_algorithm_version"])
                candidate_context=json.loads(row["context"])
                if candidate is None or not isinstance(candidate_context,dict):
                    continue
                if temporal_distance(query_context,candidate_context)>0.08:
                    continue
                if coarse_distance(query_coarse,coarse_feature(candidate))<=max(2.0,float(threshold)*2.5) and feature_distance(query,candidate)<=float(threshold):
                    return True
            except Exception:
                continue
        return False
    def _insert_sample(self,gid,feature,action,source,context,thumbnail,weight,enforce_quota,mark_review,created=None):
        clean=normalize_action(action)
        if not clean or not feature_valid(feature):
            raise RuntimeError("拒绝保存无效样本")
        fbytes=feature_bytes(feature)
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
        with self.lock:
            if not self.db.execute("SELECT 1 FROM games WHERE id=?",(gid,)).fetchone():
                raise RuntimeError("游戏不存在")
            if enforce_quota and kind=="no_op":
                row=self.db.execute("SELECT SUM(CASE WHEN kind='no_op' THEN 1 ELSE 0 END) AS noops,SUM(CASE WHEN kind!='no_op' THEN 1 ELSE 0 END) AS actions FROM samples WHERE game_id=?",(gid,)).fetchone()
                if int(row["noops"] or 0)>=max(1,int(row["actions"] or 0)//3):
                    return False
            if enforce_quota and self._near_duplicate(gid,fbytes,signature,duplicate_threshold,context):
                return False
            try:
                with self.db:
                    cursor=self.db.execute("INSERT INTO samples(game_id,created,kind,action_signature,action_family,repeat_policy,feature_algorithm_version,action_algorithm_version,feature,coarse,action,source,session_id,capture_method,context,thumbnail,weight,fingerprint) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(gid,float(created or time.time()),kind,signature,action_family_key(clean),repeat_policy,FEATURE_ALGORITHM_VERSION,ACTION_ALGORITHM_VERSION,sqlite3.Binary(zlib.compress(fbytes,6)),sqlite3.Binary(coarse_feature(fbytes)),json.dumps(clean,ensure_ascii=False,separators=(",",":")),str(source),session_id,capture_method,json.dumps(context,ensure_ascii=False,separators=(",",":")),sqlite3.Binary(zlib.compress(gray_bytes(thumbnail),6)) if gray_valid(thumbnail) else None,float(max(0.1,min(10.0,weight))),fingerprint))
                    if mark_review:
                        self.db.execute("UPDATE games SET needs_review=1 WHERE id=?",(gid,))
            except sqlite3.IntegrityError:
                return False
            count=int(self.db.execute("SELECT COUNT(*) FROM samples WHERE game_id=?",(gid,)).fetchone()[0])
        if count>MAX_SAMPLES:
            self.compact_samples(gid,MAX_SAMPLES)
        return cursor.rowcount>0
    def discard_session_window(self,gid,session_id,start_time,end_time):
        with self.lock,self.db:
            cursor=self.db.execute("DELETE FROM samples WHERE game_id=? AND session_id=? AND created BETWEEN ? AND ?",(gid,str(session_id),float(start_time),float(end_time)))
            removed=max(0,int(cursor.rowcount or 0))
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
        with self.lock:
            rows=self.db.execute("SELECT created,feature_algorithm_version,action_algorithm_version,feature,action,source,session_id,capture_method,context,thumbnail,weight,fingerprint,repeat_policy FROM samples WHERE game_id=? ORDER BY created DESC,id DESC LIMIT ?",(gid,int(limit))).fetchall()
        result=[]
        invalid=0
        for row in reversed(rows):
            try:
                feature=upgrade_feature(zlib.decompress(row["feature"]),row["feature_algorithm_version"])
                action=normalize_action(json.loads(row["action"]))
                if not feature_valid(feature) or not action:
                    invalid+=1
                    continue
                thumbnail=zlib.decompress(row["thumbnail"]) if row["thumbnail"] is not None else None
                thumbnail=upgrade_gray_image(thumbnail) if thumbnail is not None else None
                context=json.loads(row["context"])
                if not isinstance(context,dict):
                    context={}
                context.update({"session_id":row["session_id"],"capture_method":row["capture_method"],"repeat_policy":row["repeat_policy"]})
                result.append({"format_version":FORMAT_VERSION,"feature_width":FEATURE_W,"feature_height":FEATURE_H,"feature_algorithm_version":FEATURE_ALGORITHM_VERSION,"action_algorithm_version":ACTION_ALGORITHM_VERSION,"created":row["created"],"game_id":gid,"f":feature,"a":action,"source":row["source"],"session_id":row["session_id"],"capture_method":row["capture_method"],"repeat_policy":row["repeat_policy"],"context":context,"thumbnail":thumbnail,"weight":row["weight"],"checksum":row["fingerprint"]})
            except Exception:
                invalid+=1
        return result,{"valid":len(result),"invalid":invalid,"total":len(rows)}
    def load_rejections(self,gid,limit=500):
        with self.lock:
            rows=self.db.execute("SELECT created,feature_algorithm_version,feature,thumbnail,candidates,source,session_id,capture_method FROM rejections WHERE game_id=? ORDER BY created DESC,id DESC LIMIT ?",(gid,int(limit))).fetchall()
        result=[]
        for row in rows:
            try:
                feature=upgrade_feature(zlib.decompress(row["feature"]),row["feature_algorithm_version"])
                candidates=json.loads(row["candidates"])
                thumbnail=zlib.decompress(row["thumbnail"]) if row["thumbnail"] is not None else None
                thumbnail=upgrade_gray_image(thumbnail) if thumbnail is not None else None
                if feature_valid(feature) and isinstance(candidates,list):
                    result.append({"created":row["created"],"f":feature,"thumbnail":thumbnail,"candidates":candidates,"source":row["source"],"session_id":row["session_id"],"capture_method":row["capture_method"]})
            except Exception:
                pass
        return result
    def sample_stats(self,gid):
        with self.lock:
            row=self.db.execute("SELECT COUNT(*) AS total,SUM(CASE WHEN feature_algorithm_version IN (3,?) THEN 1 ELSE 0 END) AS valid,COALESCE(SUM(length(feature)+length(coarse)+length(action)+length(context)+COALESCE(length(thumbnail),0)),0) AS bytes FROM samples WHERE game_id=?",(FEATURE_ALGORITHM_VERSION,gid)).fetchone()
        total=int(row["total"] or 0)
        valid=int(row["valid"] or 0)
        return {"valid":valid,"invalid":total-valid,"total":total,"bytes":int(row["bytes"] or 0)}
    def _select_diverse(self,rows,count):
        if count<=0:
            return []
        if len(rows)<=count:
            return list(rows)
        ordered=sorted(rows,key=lambda row:(float(row["weight"]),float(row["created"])),reverse=True)
        selected=[ordered.pop(0)]
        while ordered and len(selected)<count:
            candidates=ordered if len(ordered)<=180 else ordered[:180]
            best=max(candidates,key=lambda row:(min(coarse_distance(row["coarse"],chosen["coarse"]) for chosen in selected),float(row["weight"]),float(row["created"])))
            selected.append(best)
            ordered.remove(best)
        return selected
    def compact_samples(self,gid,keep=MAX_SAMPLES):
        keep=max(1,int(keep))
        with self.lock:
            rows=self.db.execute("SELECT id,kind,action_signature,action_family,coarse,weight,created FROM samples WHERE game_id=?",(gid,)).fetchall()
        if len(rows)<=keep:
            return {"kept":len(rows),"removed":0,"invalid":0}
        signature_groups=defaultdict(list)
        family_groups=defaultdict(set)
        for row in rows:
            signature=str(row["action_signature"])
            signature_groups[signature].append(row)
            family_groups[str(row["action_family"] or row["kind"])].add(signature)
        signatures=list(signature_groups)
        targets={signature:1 for signature in signatures}
        remaining=max(0,keep-len(targets))
        family_order=sorted(family_groups,key=lambda family:sum(len(signature_groups[sig]) for sig in family_groups[family]),reverse=True)
        while remaining>0:
            progressed=False
            for family in family_order:
                candidates=[sig for sig in family_groups[family] if sig in targets and targets[sig]<len(signature_groups[sig])]
                if not candidates:
                    continue
                signature=max(candidates,key=lambda sig:(len(signature_groups[sig])-targets[sig])/(targets[sig]+1))
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
        keep_ids={int(row["id"]) for row in chosen}
        with self.lock,self.db:
            placeholders=",".join("?" for _ in keep_ids)
            if keep_ids:
                self.db.execute("DELETE FROM samples WHERE game_id=? AND id NOT IN ("+placeholders+")",[gid]+list(keep_ids))
            else:
                self.db.execute("DELETE FROM samples WHERE game_id=?",(gid,))
        return {"kept":len(keep_ids),"removed":len(rows)-len(keep_ids),"invalid":0}
    def clear_game_data(self,gid):
        with self.lock,self.db:
            self.db.execute("DELETE FROM samples WHERE game_id=?",(gid,))
            self.db.execute("DELETE FROM models WHERE game_id=?",(gid,))
            self.db.execute("DELETE FROM model_backups WHERE game_id=?",(gid,))
            self.db.execute("DELETE FROM rejections WHERE game_id=?",(gid,))
            self.db.execute("UPDATE games SET needs_review=0,last_review=NULL WHERE id=?",(gid,))
        self.model_cache.pop(gid,None)
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
        item=json.loads(zlib.decompress(payload).decode("utf-8"))
        unpacked=[]
        for proto in item.get("prototypes",[]):
            entry=dict(proto)
            entry["f"]=zlib.decompress(base64.b64decode(entry.pop("f_blob")))
            entry["coarse"]=base64.b64decode(entry.pop("coarse_blob"))
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
    def close(self):
        with self.lock:
            if self.closed:
                return
            self.closed=True
            self.db.close()
class App:
    def __init__(self,root):
        self.root=root
        self.api=WinBridge()
        self.store=DataStore()
        self.selected_game=self.store.selected_game()
        self.selected_window=None
        self.mode=None
        self.stop_event=None
        self.mode_thread=None
        self.controls=[]
        self.stop_button=None
        self.ask_window=None
        self.ask_buffer=None
        self.ask_after_ids=set()
        self.ask_escape_armed=False
        self.ask_session_id=None
        self.ask_counts=None
        self.error_recent={}
        self.result_modal=None
        self.result_modal_widget=None
        self.ui_queue=queue.Queue()
        self.closing=False
        self.shutdown_started=False
        self.shutdown_deadline=None
        self.status=tk.StringVar(value="就绪")
        self.game_text=tk.StringVar(value="未选择")
        self.window_text=tk.StringVar(value="未选择")
        self.window_detail=tk.StringVar(value="PID：-  类名：-  客户区：-")
        self.capture_text=tk.StringVar(value="采集方式：未检测")
        self.sample_text=tk.StringVar(value="样本：有效0  废弃0  数据0 KB")
        self.model_text=tk.StringVar(value="模型：无  需要复习：否")
        self.confidence_text=tk.StringVar(value="训练置信度：-")
        self.progress_value=tk.DoubleVar(value=0.0)
        self.root.report_callback_exception=self.tk_exception
        self._build()
        self._refresh_all()
        self.root.protocol("WM_DELETE_WINDOW",self.close)
        self.root.after(25,self.process_ui_queue)
        self.root.after(1200,self.periodic_refresh)
    def _build(self):
        self.root.title("通用游戏AI")
        self.root.geometry("780x660")
        self.root.minsize(700,590)
        self.root.option_add("*Font",("Microsoft YaHei UI",10))
        outer=ttk.Frame(self.root,padding=18)
        outer.pack(fill="both",expand=True)
        ttk.Label(outer,text="通用游戏AI控制面板",font=("Microsoft YaHei UI",18,"bold")).pack(anchor="w",pady=(0,12))
        info=ttk.LabelFrame(outer,text="当前状态",padding=12)
        info.pack(fill="x",pady=(0,12))
        labels=[("当前游戏：",self.game_text),("目标窗口：",self.window_text),("窗口身份：",self.window_detail),("采集兼容性：",self.capture_text),("数据统计：",self.sample_text),("模型状态：",self.model_text),("识别状态：",self.confidence_text)]
        for row,(name,value) in enumerate(labels):
            ttk.Label(info,text=name).grid(row=row,column=0,sticky="nw",pady=2)
            ttk.Label(info,textvariable=value,wraplength=610).grid(row=row,column=1,sticky="nw",pady=2)
        info.columnconfigure(1,weight=1)
        grid=ttk.Frame(outer)
        grid.pack(fill="both",expand=True)
        specs=[("游戏",self.open_game_dialog),("选择窗口",self.open_window_dialog),("学习",self.start_learning),("复习",self.start_review),("训练",self.start_training),("请教",self.start_ask),("停止",self.request_stop),("数据清理",self.open_data_dialog)]
        for index,(text,command) in enumerate(specs):
            button=ttk.Button(grid,text=text,command=command)
            button.grid(row=index//2,column=index%2,sticky="nsew",padx=7,pady=7,ipady=11)
            if text=="停止":
                self.stop_button=button
                button.configure(state="disabled")
            else:
                self.controls.append(button)
        for column in range(2):
            grid.columnconfigure(column,weight=1)
        for row in range(4):
            grid.rowconfigure(row,weight=1)
        ttk.Progressbar(outer,variable=self.progress_value,maximum=100).pack(fill="x",pady=(12,8))
        bottom=ttk.Frame(outer)
        bottom.pack(fill="x")
        ttk.Label(bottom,text="状态：").pack(side="left")
        ttk.Label(bottom,textvariable=self.status,wraplength=560).pack(side="left",fill="x",expand=True)
        ttk.Label(bottom,text="ESC或“停止”结束").pack(side="right")
    def tk_exception(self,exc_type,exc_value,exc_traceback):
        self.show_error("".join(traceback.format_exception(exc_type,exc_value,exc_traceback)))
    def ui(self,callback):
        if self.closing and threading.current_thread() is not threading.main_thread():
            return
        if threading.current_thread() is threading.main_thread():
            try:
                callback()
            except Exception:
                self.show_error(traceback.format_exc())
            return
        self.ui_queue.put(("call",callback))
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
    def set_status(self,text):
        self.ui(lambda:self.status.set(str(text)))
    def set_confidence(self,text):
        self.ui(lambda:self.confidence_text.set(str(text)))
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
                self.window_detail.set("PID："+str(self.selected_window["pid"])+"  类名："+self.selected_window["class"]+"  客户区："+str(rect[2])+"×"+str(rect[3])+"  DPI："+str(dpi))
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
            if not self.confirm_dialog("删除游戏","确认删除“"+games[index]["name"]+"”及其学习数据、模型和备份吗？"):
                return
            games.pop(index)
            refresh(games[min(index,len(games)-1)]["id"] if games else None)
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
        ttk.Button(tools,text="删除",command=delete_game).pack(side="left",padx=6)
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
        win.geometry("820x590")
        win.transient(self.root)
        win.grab_set()
        frame=ttk.Frame(win,padding=16)
        frame.pack(fill="both",expand=True)
        ttk.Label(frame,text="选择雷电模拟器窗口或其他窗口",font=("Microsoft YaHei UI",13,"bold")).pack(anchor="w",pady=(0,6))
        ttk.Label(frame,text="确认后将在工作线程执行动态采集校准。请让目标窗口画面发生变化；校准失败、窗口消失、最小化、权限不足或后端切换时不会保存选择。",wraplength=760).pack(anchor="w",pady=(0,10))
        list_frame=ttk.Frame(frame)
        list_frame.pack(fill="both",expand=True)
        box=tk.Listbox(list_frame,exportselection=False,font=("Microsoft YaHei UI",10))
        scroll=ttk.Scrollbar(list_frame,orient="vertical",command=box.yview)
        box.configure(yscrollcommand=scroll.set)
        box.pack(side="left",fill="both",expand=True)
        scroll.pack(side="right",fill="y")
        status=tk.StringVar(value="请选择窗口")
        ttk.Label(frame,textvariable=status,wraplength=760).pack(anchor="w",fill="x",pady=(8,2))
        progress=ttk.Progressbar(frame,maximum=100)
        progress.pack(fill="x",pady=(0,8))
        windows=[]
        cancel_event=threading.Event()
        state={"calibrating":False,"closed":False}
        def refresh():
            nonlocal windows
            if state["calibrating"]:
                return
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
        def set_busy(value):
            state["calibrating"]=bool(value)
            confirm_button.configure(state="disabled" if value else "normal")
            refresh_button.configure(state="disabled" if value else "normal")
            box.configure(state="disabled" if value else "normal")
        def finish_success(item,calibration):
            if state["closed"] or cancel_event.is_set():
                return
            item=dict(item)
            item["integrity"]=int(calibration["integrity"])
            item["capture_backend"]=str(calibration["validated_backend"])
            self.selected_window=item
            self.api.reset_frame_history(item["hwnd"])
            self._refresh_all()
            self.status.set("已选择窗口："+item["title"]+"；后端"+str(calibration["validated_backend"])+"；动态校准"+str(round(float(calibration.get("fps",0.0)),1))+"fps")
            state["closed"]=True
            try:
                win.grab_release()
            except Exception:
                pass
            win.destroy()
        def finish_error(message):
            if state["closed"] or cancel_event.is_set():
                return
            set_busy(False)
            progress["value"]=0
            status.set("校准失败："+str(message))
        def confirm():
            if state["calibrating"]:
                return
            selection=box.curselection()
            if not selection:
                self.show_error("请先选择一个窗口")
                return
            item=dict(windows[selection[0]])
            try:
                self.api.validate_target(item,False)
                item["integrity"]=self.api.validate_uipi(item)
            except Exception as error:
                self.show_error(str(error))
                return
            cancel_event.clear()
            set_busy(True)
            status.set("正在动态检测采集后端、画面变化、窗口身份和权限；可点击取消")
            progress["value"]=1
            def update_progress(value):
                self.ui(lambda:progress.configure(value=max(1,min(99,float(value)*100))) if not state["closed"] else None)
            def work():
                try:
                    calibration=self.api.calibrate(item,1.8,cancel_event,update_progress)
                    self.ui(lambda:finish_success(item,calibration))
                except Exception as error:
                    self.ui(lambda message=str(error):finish_error(message))
                finally:
                    try:
                        self.api.wgc.release_thread(threading.get_ident())
                    except Exception:
                        pass
            threading.Thread(target=work,name="UniversalGameAI-WindowCalibration",daemon=True).start()
        def cancel():
            if state["closed"]:
                return
            state["closed"]=True
            cancel_event.set()
            try:
                win.grab_release()
            except Exception:
                pass
            win.destroy()
        tools=ttk.Frame(frame)
        tools.pack(fill="x",pady=(4,0))
        refresh_button=ttk.Button(tools,text="刷新",command=refresh)
        refresh_button.pack(side="left")
        confirm_button=ttk.Button(tools,text="确认",command=confirm)
        confirm_button.pack(side="right",padx=(6,0))
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
        self.api.validate_target(self.selected_window,foreground)
        return self.selected_window
    def set_controls(self,running):
        for button in self.controls:
            button.configure(state="disabled" if running else "normal")
        if self.stop_button:
            self.stop_button.configure(state="normal" if running else "disabled")
    def start_worker(self,name,target,needs_window=False):
        if self.mode or self.closing:
            self.show_error("当前已有操作正在运行，请先停止")
            return
        try:
            self.require_game()
            if needs_window:
                self.require_window(False)
        except Exception as error:
            self.show_error(str(error))
            return
        self.mode=name
        self.stop_event=threading.Event()
        self.api.allow_input(self.stop_event)
        self.set_controls(True)
        self.progress_value.set(0)
        self.status.set(name+"已开始，按ESC或点击“停止”结束")
        self.mode_thread=threading.Thread(target=self.worker_entry,args=(name,target),name="UniversalGameAI-"+name,daemon=True)
        self.mode_thread.start()
    def worker_entry(self,name,target):
        error=None
        final_text=name+"已结束"
        try:
            final_text=target()
        except InputStopped:
            final_text=name+"已停止"
        except Exception:
            error=traceback.format_exc()
        finally:
            self.api.block_input()
        def finish():
            if self.shutdown_started:
                return
            self.mode=None
            self.stop_event=None
            self.mode_thread=None
            self.set_controls(False)
            self.progress_value.set(0)
            self.status.set(final_text)
            self._refresh_all()
            if error:
                self.show_error(error)
            else:
                self.show_info(name+"完成",final_text)
        self.ui(finish)
    def request_stop(self):
        if self.stop_event:
            self.stop_event.set()
        self.api.block_input()
        if self.ask_window is not None:
            self.close_ask()
            return
        self.status.set("正在停止，已阻止新的鼠标按下并释放全部鼠标键")
    def _keyboard_escape(self,event=None):
        if self.stop_event:
            self.stop_event.set()
        self.api.block_input()
    def wait_escape_release(self):
        while self.api.key_down(0x1B) and self.stop_event and not self.stop_event.is_set():
            time.sleep(0.04)
    def should_stop(self):
        if not self.stop_event or self.stop_event.is_set():
            self.api.block_input()
            return True
        if self.api.key_down(0x1B):
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
        self.start_worker("学习",self.learning_worker,True)
    def learning_worker(self):
        game=self.require_game()
        target=self.require_window(False)
        hwnd=target["hwnd"]
        session_id="learn|"+uuid.uuid4().hex
        calibration=self.api.calibration_for(target)
        if not calibration.get("dynamic_passed") or not calibration.get("validated_backend"):
            raise RuntimeError("目标窗口尚未通过动态采集验收，请重新选择窗口")
        if not self.api.request_foreground(hwnd):
            self.set_status("无法自动切换到目标窗口，学习将等待目标窗口成为前台")
        self.wait_escape_release()
        keyboard_queue=queue.Queue()
        keyboard_state={"until":0.0,"generation":0,"last_time":0.0}
        def other_key(event):
            keyboard_state["until"]=max(float(keyboard_state["until"]),float(event["time"])+0.75)
            keyboard_state["generation"]=int(keyboard_state["generation"])+1
            keyboard_state["last_time"]=float(event["time"])
            try:
                keyboard_queue.put_nowait(event)
            except Exception:
                pass
            self.api.release_all_buttons()
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
            keyboard=session.start_keyboard(other_key)
            monitor=session.start_mouse()
            active={}
            pending_click={}
            last_negative=0.0
            last_motion_time=0.0
            motion=None
            last_cursor=None
            hover_start=0.0
            hover_point=None
            last_update=0.0
            def paused(now=None):
                current=time.time() if now is None else float(now)
                return current<float(keyboard_state["until"]) or not keyboard.all_released()
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
                    event_time=float(keyboard_state.get("last_time") or time.time())
                    keyboard_discarded+=self.store.discard_session_window(game["id"],session_id,event_time-0.75,event_time+0.75)
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
                while True:
                    try:
                        event=keyboard_queue.get_nowait()
                    except queue.Empty:
                        break
                    keyboard_count+=1
                    keyboard_state["until"]=max(float(keyboard_state["until"]),float(event["time"])+0.75)
                    keyboard_discarded+=self.store.discard_session_window(game["id"],session_id,float(event["time"])-0.75,float(event["time"])+0.75)
                    active.clear()
                    pending_click.clear()
                    motion=None
                    last_cursor=None
                    hover_point=None
                    hover_start=0.0
                    monitor.drain()
                if paused(now):
                    active.clear()
                    pending_click.clear()
                    motion=None
                    self.api.release_all_buttons()
                    self.set_status("检测到非ESC键盘输入，学习已暂停并废弃按键前后样本；等待全部按键释放")
                    time.sleep(0.03)
                    continue
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
        return "学习已结束：有效"+str(learned)+"，重复或配额抑制"+str(duplicates)+"，越界废弃"+str(discarded)+"，无效画面"+str(invalid_frames)+"，检测到非ESC键盘输入"+str(keyboard_count)+"次，因此废弃样本"+str(keyboard_discarded)+"个"
    def _prototype_medoid(self,members):
        if len(members)==1:
            return members[0]
        candidates=members if len(members)<=28 else [members[round(index*(len(members)-1)/27)] for index in range(28)]
        comparisons=members if len(members)<=72 else [members[round(index*(len(members)-1)/71)] for index in range(72)]
        best=candidates[0]
        best_total=float("inf")
        operations=0
        for candidate in candidates:
            total=0.0
            for other in comparisons:
                operations+=1
                if operations%32==0 and self.should_stop():
                    raise InputStopped("复习已停止")
                total+=feature_distance(candidate["f"],other["f"])
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
            result.append({"id":uuid.uuid4().hex,"cluster_id":cluster_id,"canonical_action_signature":canonical,"f":feature_bytes(medoid["f"]),"coarse":coarse_feature(medoid["f"]),"a":normalize_action(action),"support":len(cluster),"action_support":int(action_support),"mean_distance":round(mean,6),"std_distance":round(std,6),"limit95":round(limit95,6),"limit99":round(limit99,6),"intra_threshold":round(threshold_value,6),"threshold":round(threshold_value,6),"temporal":temporal,"temporal_threshold":round(temporal_threshold,6),"capture_methods":methods,"previous_action":prev,"repeat_policy":repeat_policy if repeat_policy in REPEAT_POLICIES else "one_shot","max_rate":max(0.25,min(12.0,float(max_rate))),"ambiguous":False,"created_from_sample_checksum":medoid.get("checksum","")})
        return result
    def rank_action_candidates(self,feature,prototypes,last_action_signature="",full_limit=16,temporal_context=None):
        if not feature_valid(feature):
            return []
        query_temporal=temporal_from_context(temporal_context or {})
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
        for distance,proto in coarse_rank[:max(8,int(full_limit))]:
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
        self.start_worker("复习",self.review_worker,False)
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
    def review_worker(self):
        game=self.require_game()
        samples,stats=self.store.load_samples(game["id"])
        valid=[]
        for index,sample in enumerate(samples):
            if index%64==0 and self.should_stop():
                return "复习已中断：旧完整模型未被覆盖"
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
        action_clusters=self._cluster_action_samples(valid)
        if self.should_stop():
            return "复习已中断：旧完整模型未被覆盖"
        session_groups=defaultdict(list)
        for item in valid:
            session_groups[str(item.get("session_id") or item.get("context",{}).get("session_id") or "legacy")].append(item)
        sessions=sorted(session_groups,key=lambda key:hashlib.sha256(key.encode("utf-8","replace")).hexdigest())
        holdout_sessions=set()
        target=max(20,round(len(valid)*0.25))
        selected_count=0
        if len(sessions)>1:
            for session_id in sessions:
                if len(valid)-selected_count-len(session_groups[session_id])<1:
                    continue
                holdout_sessions.add(session_id)
                selected_count+=len(session_groups[session_id])
                if selected_count>=target:
                    break
        train=[item for item in valid if str(item.get("session_id") or item.get("context",{}).get("session_id") or "legacy") not in holdout_sessions]
        holdout=[item for item in valid if item not in train]
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
                    self.set_status("复习中：生成短时序原型；"+str(processed+local)+"/"+str(len(train)))
                prototypes.extend(self._cluster_action_group(cluster_id,cluster["a"],len(items),items,progress,cluster.get("repeat_policy","one_shot"),cluster.get("max_rate",3.0)))
                processed+=len(items)
                prototypes=self._limit_prototypes(prototypes,MAX_PROTOTYPES)
        except InputStopped:
            if prototypes:
                partial={"created":time.time(),"samples":len(valid),"training_samples":len(train),"invalid_samples":stats["invalid"],"prototypes":prototypes,"capture_backends":sorted({str(item.get("capture_method")) for item in train}),"validation":{"status":"stopped"},"stopped":True}
                self.store.save_model(game["id"],partial,False)
            return "复习已中断：旧完整模型未被覆盖，部分结果仅保存为临时模型"
        operations=0
        for index,proto in enumerate(prototypes):
            conflicting=[]
            for other in prototypes:
                operations+=1
                if operations%64==0 and self.should_stop():
                    return "复习已中断：旧完整模型未被覆盖"
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
                        return "复习已中断：旧完整模型未被覆盖"
                    distances.append((feature_distance(proto["f"],other["f"]),temporal_distance(proto.get("temporal",{}),other.get("temporal",{}))))
                nearest,temporal_nearest=min(distances,key=lambda item:item[0])
            proto["nearest_conflicting_distance"]=None if math.isinf(nearest) else round(nearest,6)
            intra=float(proto.get("intra_threshold",proto["threshold"]))
            visual_close=not math.isinf(nearest) and nearest<=max(1e-6,intra*0.20)
            temporal_close=temporal_nearest<=max(float(proto.get("temporal_threshold",0.25)),0.25)
            proto["ambiguous"]=bool(visual_close and temporal_close)
            proto["threshold"]=round(max(0.001,intra if math.isinf(nearest) else min(intra,max(0.001,nearest*0.62))),6)
            proto["minimum_second_candidate_gap"]=round(max(10.0,float(proto["threshold"])*0.15,0.0 if math.isinf(nearest) else nearest*0.10),6)
            if index%12==0:
                self.set_progress(78+7*(index+1)/max(1,len(prototypes)))
        rejections=self.store.load_rejections(game["id"],500)
        rejection_constraints=0
        for proto_index,proto in enumerate(prototypes):
            matching=[]
            for rejection_index,rejection in enumerate(rejections):
                if (proto_index*max(1,len(rejections))+rejection_index)%64==0 and self.should_stop():
                    return "复习已中断：旧完整模型未被覆盖"
                candidate_actions=[normalize_action(item.get("a")) for item in rejection.get("candidates",[]) if isinstance(item,dict)]
                if any(action and action_family_key(action)==action_family_key(proto["a"]) and action_geometry_distance(action,proto["a"])<=action_cluster_limit(proto["a"])*1.25 for action in candidate_actions):
                    matching.append((coarse_distance(proto["coarse"],coarse_feature(rejection["f"])),rejection))
            if matching:
                nearest_rejected=min(feature_distance(proto["f"],rejection["f"]) for _,rejection in sorted(matching,key=lambda item:item[0])[:8])
                proto["nearest_rejected_distance"]=round(nearest_rejected,6)
                proto["threshold"]=round(max(0.001,min(float(proto["threshold"]),nearest_rejected*0.72)),6)
                rejection_constraints+=1
            else:
                proto["nearest_rejected_distance"]=None
        errors=accepted=correct=0
        by_action=defaultdict(lambda:{"total":0,"accepted":0,"correct":0,"errors":0,"unrecognized":0})
        by_method=defaultdict(lambda:{"total":0,"accepted":0,"correct":0,"errors":0})
        dangerous_false=0
        for index,sample in enumerate(holdout):
            if index%8==0 and self.should_stop():
                return "复习已中断：旧完整模型未被覆盖"
            ranked=self.rank_action_candidates(sample["f"],prototypes,str(sample.get("context",{}).get("previous_action","")),16,sample.get("context",{}))
            decision=self.evaluate_action_candidates(ranked)
            expected=sample["_action_cluster"]
            canonical=sample.get("_canonical_action_signature",action_signature(sample["a"]))
            method=str(sample.get("capture_method") or sample.get("context",{}).get("capture_method") or "unknown")
            arow=by_action[canonical]
            mrow=by_method[method]
            arow["total"]+=1
            mrow["total"]+=1
            if decision.get("accepted"):
                accepted+=1
                arow["accepted"]+=1
                mrow["accepted"]+=1
                predicted=decision["best"]
                if predicted["cluster_id"]==expected:
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
            if index%5==0:
                self.set_progress(85+13*(index+1)/max(1,len(holdout)))
        holdout_count=len(holdout)
        coverage=accepted/holdout_count if holdout_count else 0.0
        accepted_error_rate=errors/accepted if accepted else None
        overall_accuracy=correct/holdout_count if holdout_count else 0.0
        dangerous_false_rate=dangerous_false/max(1,holdout_count)
        per_action={}
        action_rules_pass=True
        train_signatures={str(item.get("_canonical_action_signature",action_signature(item["a"]))) for item in train}
        for signature in sorted(train_signatures|set(by_action)):
            row=dict(by_action[signature])
            row["recall"]=row["correct"]/row["total"] if row["total"] else 0.0
            row["accepted_error_rate"]=row["errors"]/row["accepted"] if row["accepted"] else None
            row["unrecognized_rate"]=row["unrecognized"]/row["total"] if row["total"] else 0.0
            action=next((item["a"] for item in valid if str(item.get("_canonical_action_signature",action_signature(item["a"])))==signature),{"kind":"no_op"})
            dangerous=action["kind"] in {"double_click","long_press","drag"} or action.get("button") in {"right","middle"}
            row["dangerous"]=dangerous
            row_pass=row["total"]>=1 and row["accepted"]>=1 and row["errors"]==0 if dangerous else row["total"]>=1 and row["accepted"]>=1 and row["accepted_error_rate"] is not None and row["accepted_error_rate"]<=0.02
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
            row["passed"]=bool(row["total"]>=3 and row["accepted"]>=1 and row["accepted_error_rate"] is not None and row["accepted_error_rate"]<=0.02 and row["coverage"]>=0.80)
            method_rules_pass=method_rules_pass and row["passed"]
            per_method[method]=row
        enough=holdout_count>=20 and len(holdout_sessions)>=1 and accepted>0 and bool(train_methods)
        global_pass=coverage>=0.80 and overall_accuracy>=0.80 and accepted_error_rate is not None and accepted_error_rate<=0.02 and dangerous_false==0
        validation_status="passed" if enough and global_pass and action_rules_pass and method_rules_pass and prototypes and not any(proto.get("ambiguous") for proto in prototypes) else ("insufficient" if not enough or not action_rules_pass or not method_rules_pass else "failed")
        validation={"status":validation_status,"split":"session_id","holdout_sessions":len(holdout_sessions),"minimum_holdout":20,"minimum_coverage":0.80,"maximum_accepted_error_rate":0.02,"minimum_overall_accuracy":0.80,"maximum_dangerous_false":0,"holdout":holdout_count,"accepted":accepted,"errors":errors,"correct":correct,"coverage":coverage,"accepted_error_rate":accepted_error_rate,"overall_accuracy":overall_accuracy,"dangerous_false":dangerous_false,"dangerous_false_rate":dangerous_false_rate,"per_action":per_action,"per_capture_method":per_method,"ambiguous_prototypes":sum(1 for proto in prototypes if proto.get("ambiguous"))}
        model={"created":time.time(),"samples":len(valid),"training_samples":len(train),"invalid_samples":stats["invalid"],"action_clusters":len(action_clusters),"rejection_constraints":rejection_constraints,"prototypes":prototypes,"capture_backends":train_methods,"validation":validation,"stopped":False}
        if not prototypes:
            raise RuntimeError("复习未生成可用原型")
        self.store.save_model(game["id"],model,validation_status=="passed")
        self.set_progress(100)
        label="通过验收" if validation_status=="passed" else ("验证不足，仅保存临时模型并禁止训练" if validation_status=="insufficient" else "验证失败，仅保存临时模型并禁止训练")
        error_text="无可计算值" if accepted_error_rate is None else str(round(accepted_error_rate*100,2))+"%"
        lines=["复习完成，"+label+"：原型"+str(len(prototypes))+"，按会话留出"+str(holdout_count)+"，覆盖率"+str(round(coverage*100,2))+"%，接受错误率"+error_text+"，总体正确率"+str(round(overall_accuracy*100,2))+"%，危险动作误触"+str(dangerous_false)+"次","各动作独立留出验证："]
        for signature,row in sorted(per_action.items()):
            lines.append(signature+"：留出"+str(row["total"])+"，接受"+str(row["accepted"])+"，错误"+str(row["errors"])+"，"+("通过" if row["passed"] else "未通过"))
        lines.append("各采集后端独立验证：")
        for method,row in sorted(per_method.items()):
            lines.append(method+"：留出"+str(row["total"])+"，覆盖率"+str(round(row["coverage"]*100,2))+"%，"+("通过" if row["passed"] else "未通过"))
        return "\n".join(lines)
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
    def execute_action(self,target,action,expected_frame=None):
        item=normalize_action(action)
        if not item:
            raise RuntimeError("模型包含无效动作")
        expected_rect=tuple(expected_frame.get("rect",())) if isinstance(expected_frame,dict) else ()
        expected_dpi=int(expected_frame.get("dpi",0)) if isinstance(expected_frame,dict) and finite_number(expected_frame.get("dpi",0)) else 0
        def stop_check():
            if self.should_stop() or not self.api.input_allowed():
                self.api.block_input()
                raise InputStopped("已停止，拒绝剩余动作")
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
            model=self.store.load_model(game["id"])
            if not model or not model.get("prototypes"):
                raise RuntimeError("没有可用完整模型，请先学习并完成复习")
            if str(model.get("validation",{}).get("status",""))!="passed":
                raise RuntimeError("完整模型未通过严格独立留出验收，请重新学习、请教或复习")
            current=next((item for item in self.store.games() if item["id"]==game["id"]),{})
            if current.get("needs_review"):
                raise RuntimeError("模型需要复习：请先点击“复习”完成离线优化")
            calibration=self.api.calibration_for(target)
            backend=str(calibration.get("validated_backend",""))
            if not calibration.get("dynamic_passed") or backend not in set(model.get("capture_backends",[])):
                raise RuntimeError("当前采集后端未在模型中独立验证；请使用该后端重新学习和复习")
        except Exception as error:
            self.show_error(str(error))
            return
        self.start_worker("训练",self.training_worker,True)
    def training_worker(self):
        game=self.require_game()
        target=self.require_window(False)
        model=self.store.load_model(game["id"])
        prototypes=model["prototypes"]
        allowed_backends=set(model.get("capture_backends",[]))
        calibration=self.api.calibration_for(target)
        validated_backend=str(calibration.get("validated_backend",""))
        self.api.request_foreground(target["hwnd"])
        self.wait_escape_release()
        key_queue=queue.Queue()
        def other_key(event):
            try:
                key_queue.put_nowait(event)
            except Exception:
                pass
            self.api.block_input()
        actions=0
        keyboard_count=0
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
        frozen_count=0
        previous_feature=None
        previous_frame_stamp=0.0
        state_since=time.time()
        action_hits=defaultdict(deque)
        pause_until=0.0
        with ModeSession(self,target) as session:
            frame_buffer=session.start_frames(max(8.0,float(calibration.get("fps",15.0))),2.5,0.1,"training")
            keyboard=session.start_keyboard(other_key)
            while not self.should_stop():
                while True:
                    try:
                        event=key_queue.get_nowait()
                    except queue.Empty:
                        break
                    keyboard_count+=1
                    pause_until=max(pause_until,float(event["time"])+0.25)
                    self.api.block_input()
                    candidate_id=None
                    candidate_count=0
                if time.time()<pause_until or not keyboard.all_released():
                    self.api.block_input()
                    self.set_status("检测到非ESC键盘输入，训练已暂停；等待全部按键释放")
                    time.sleep(0.03)
                    continue
                if not self.api.input_allowed():
                    self.api.allow_input(self.stop_event)
                try:
                    self.api.validate_target(target,True)
                except TargetUnavailable as error:
                    self.api.block_input()
                    candidate_id=None
                    candidate_count=0
                    self.set_confidence("训练置信度：0%")
                    self.set_status("目标窗口失去焦点，等待恢复；"+str(error))
                    time.sleep(0.08)
                    continue
                captured=frame_buffer.latest(None,0.8)
                if captured is None or not captured.get("usable_for_training"):
                    self.api.block_input()
                    self.set_status("采集画面不可用于训练；等待已验收、非黑屏、非重复且后端稳定的最新帧；"+(frame_buffer.last_error or "尚无画面"))
                    time.sleep(0.08)
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
                        frozen_count=frozen_count+1 if frame_change<float(calibration.get("freeze_change",1.5)) else 0
                        if frame_change>float(calibration.get("significant_change",60.0)):
                            state_since=time.time()
                    previous_feature=feature
                    previous_frame_stamp=captured["time"]
                if frozen_count>=int(calibration.get("freeze_frames",30)) or captured.get("stale"):
                    self.api.block_input()
                    self.set_status("画面长时间重复，训练停止输入并等待画面变化")
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
                ranked=self.rank_action_candidates(feature,prototypes,last_action_signature,18,temporal)
                decision=self.evaluate_action_candidates(ranked)
                if not decision.get("accepted"):
                    candidate_id=None
                    candidate_count=0
                    self.api.block_input()
                    self.set_confidence("训练置信度："+str(round(float(decision.get("confidence",0.0))*100,1))+"%")
                    self.set_status("训练中："+str(decision.get("reason","识别不确定"))+"；不执行动作并等待请教")
                    time.sleep(0.12)
                    continue
                if not self.api.input_allowed():
                    self.api.allow_input(self.stop_event)
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
                before=feature
                self.set_status("训练中："+self.action_text(action)+"；短时序已确认；采集="+captured["method"])
                try:
                    self.execute_action(target,action,captured)
                except InputStopped:
                    if self.stop_event is not None and self.stop_event.is_set():
                        raise
                    self.api.block_input()
                    candidate_id=None
                    candidate_count=0
                    self.set_status("检测到非ESC键盘输入，动作已中止并等待全部按键释放")
                    continue
                except TargetUnavailable as error:
                    self.api.block_input()
                    candidate_id=None
                    candidate_count=0
                    self.set_status(str(error))
                    continue
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
        return "训练已结束，AI执行"+str(actions)+"个鼠标动作；检测到非ESC键盘输入"+str(keyboard_count)+"次；每次按下、滚轮和双击均复核前台、遮挡、客户区、DPI、PID、类名和完整性级别"
    def basic_actions(self):
        result=[]
        for y in (0.18,0.35,0.5,0.68,0.84):
            for x in (0.16,0.32,0.5,0.68,0.84):
                result.append(normalize_action({"kind":"click","button":"left","path":[[x,y]],"duration":0.08}))
        result.extend([normalize_action({"kind":"double_click","button":"left","path":[[0.5,0.5]],"duration":0.16}),normalize_action({"kind":"drag","button":"left","path":[[0.25,0.5],[0.75,0.5]],"duration":0.45}),normalize_action({"kind":"drag","button":"left","path":[[0.5,0.75],[0.5,0.25]],"duration":0.45}),normalize_action({"kind":"no_op","duration":0.4}),normalize_action({"kind":"scroll_v","delta":120,"path":[[0.5,0.5]],"duration":0.08}),normalize_action({"kind":"scroll_v","delta":-120,"path":[[0.5,0.5]],"duration":0.08})])
        return result
    def start_ask(self):
        try:
            return self._start_ask_impl()
        except Exception:
            error=traceback.format_exc()
            try:
                self.close_ask(show_summary=False,wait_buffer=False)
            except Exception:
                pass
            self.mode=None
            self.set_controls(False)
            self.show_error(error)
    def _start_ask_impl(self):
        if self.mode or self.closing:
            self.show_error("当前已有操作正在运行，请先停止")
            return
        try:
            game=self.require_game()
            target=self.require_window(False)
            samples,stats=self.store.load_samples(game["id"])
            try:
                model=self.store.load_model(game["id"])
            except Exception:
                model=None
            prototypes=[item for item in (model.get("prototypes",[]) if model else []) if feature_valid(item.get("f")) and normalize_action(item.get("a"))]
            historical=[]
            for item in samples:
                action=normalize_action(item.get("a"))
                if feature_valid(item.get("f")) and action:
                    historical.append({"id":str(item.get("checksum",uuid.uuid4().hex)),"f":item["f"],"coarse":coarse_feature(item["f"]),"a":action,"cluster_id":"history|"+action_signature(action),"canonical_action_signature":action_signature(action),"repeat_policy":str(item.get("repeat_policy","one_shot")),"source":"sample"})
            calibration=self.api.calibration_for(target)
            if not calibration.get("dynamic_passed") or not calibration.get("validated_backend"):
                raise RuntimeError("目标窗口尚未通过动态采集验收，请重新选择窗口")
            self.ask_session_id="teach|"+uuid.uuid4().hex
            self.ask_buffer=FrameBuffer(self.api,target,20.0,2.5,0.1).start()
        except Exception as error:
            if self.ask_buffer is not None:
                self.ask_buffer.stop()
                self.ask_buffer=None
            self.show_error(str(error))
            return
        self.mode="请教"
        self.set_controls(True)
        self.status.set("请教已开始：请教窗口可保持前台，目标窗口将通过后台采集出题；ESC或“停止”结束")
        win=tk.Toplevel(self.root)
        self.ask_window=win
        win.title("请教")
        win.geometry("780x780")
        win.minsize(700,700)
        win.transient(self.root)
        frame=ttk.Frame(win,padding=16)
        frame.pack(fill="both",expand=True)
        ttk.Label(frame,text="请选择当前画面中AI应该执行的鼠标动作",font=("Microsoft YaHei UI",14,"bold")).pack(anchor="w")
        ttk.Label(frame,text="优先展示歧义、拒识或候选动作接近的实时状态。请教窗口在前台时不会要求游戏窗口也在前台。",wraplength=730).pack(anchor="w",pady=(4,10))
        canvas=tk.Canvas(frame,width=672,height=378,bg="black",highlightthickness=1,highlightbackground="#777777")
        canvas.pack()
        preview_info=tk.StringVar(value="等待彩色教学预览")
        ttk.Label(frame,textvariable=preview_info,wraplength=730).pack(anchor="w",fill="x",pady=(6,0))
        choice_frame=ttk.Frame(frame)
        choice_frame.pack(fill="both",expand=True,pady=(10,0))
        answer_buttons=[]
        count={"saved":0,"duplicates":0,"skipped":0,"rejected":0}
        self.ask_counts=count
        state={"frame":None,"choices":[],"image":None,"locked":False,"candidates":[],"recent_actions":deque(["<START>","<START>"],maxlen=4),"state_since":time.time(),"init_deadline":time.monotonic()+3.0,"initialized":False}
        sources=[]
        for proto in prototypes:
            sources.append({"a":normalize_action(proto["a"]),"repeat_policy":str(proto.get("repeat_policy","one_shot")),"cluster_id":str(proto.get("cluster_id",""))})
        for item in historical:
            sources.append({"a":item["a"],"repeat_policy":item.get("repeat_policy","one_shot"),"cluster_id":item["cluster_id"]})
        sources.extend({"a":action,"repeat_policy":"one_shot","cluster_id":"basic|"+action_signature(action)} for action in self.basic_actions())
        unique=[]
        seen=set()
        for entry in sources:
            signature=action_signature(entry["a"])
            if signature and signature not in seen:
                seen.add(signature)
                unique.append(entry)
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
        def render(question_frame,choices):
            preview=preview_rgb_bytes(question_frame.get("preview_rgb")) or bytes(PREVIEW_W*PREVIEW_H*3)
            ppm=b"P6\n"+str(PREVIEW_W).encode("ascii")+b" "+str(PREVIEW_H).encode("ascii")+b"\n255\n"+preview
            image=tk.PhotoImage(data=base64.b64encode(ppm).decode("ascii"),format="PPM")
            scaled=image.zoom(2,2)
            state["image"]=(image,scaled)
            canvas.delete("all")
            x0=16
            y0=9
            canvas.create_image(x0,y0,image=scaled,anchor="nw")
            colors=("#00ffff","#ffff00","#ff66ff","#66ff66")
            for index,entry in enumerate(choices[:4]):
                action=normalize_action(entry.get("a"))
                if not action or action["kind"]=="no_op":
                    continue
                path=action.get("path") or []
                points=[]
                for point in path:
                    points.extend([x0+float(point[0])*639,y0+float(point[1])*359])
                color=colors[index%len(colors)]
                if len(points)>=4:
                    canvas.create_line(*points,fill=color,width=3,arrow="last")
                if len(points)>=2:
                    canvas.create_oval(points[-2]-6,points[-1]-6,points[-2]+6,points[-1]+6,outline=color,width=3)
                    canvas.create_text(points[-2]+10,points[-1]-10,text=chr(65+index),fill=color,font=("Microsoft YaHei UI",12,"bold"),anchor="sw")
            latest=self.ask_buffer.latest(None,2.0) if self.ask_buffer is not None else None
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
        def select_question_frame():
            frames=self.ask_buffer.snapshot(1.8) if self.ask_buffer is not None else []
            if not frames:
                return None,[]
            usable=[frame for frame in frames if frame.get("usable_for_teaching")]
            if not usable:
                return frames[-1],[]
            if not prototypes:
                return usable[-1],[]
            selected=usable[-1]
            temporal=self.build_temporal_context(self.ask_buffer,selected,state["recent_actions"],state["state_since"])
            temporal["previous_action_changed_frame"]=True
            selected_ranked=self.rank_action_candidates(selected["f"],prototypes,"",18,temporal)
            selected_priority=float("inf")
            for candidate_frame in usable[-28:]:
                temporal=self.build_temporal_context(self.ask_buffer,candidate_frame,state["recent_actions"],state["state_since"])
                temporal["previous_action_changed_frame"]=True
                ranked=self.rank_action_candidates(candidate_frame["f"],prototypes,"",18,temporal)
                if not ranked:
                    priority=-2.0
                else:
                    decision=self.evaluate_action_candidates(ranked)
                    gap=(ranked[1]["score"]-ranked[0]["score"])/max(1.0,ranked[0]["score"]) if len(ranked)>1 else 10.0
                    priority=gap
                    if decision.get("ambiguous"):
                        priority-=3.0
                    elif not decision.get("accepted"):
                        priority-=1.0
                if priority<selected_priority:
                    selected_priority=priority
                    selected=candidate_frame
                    selected_ranked=ranked
            return selected,selected_ranked
        def make_choices(question_frame,ranked):
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
            if not choices and historical:
                query=coarse_feature(question_frame["f"])
                rough=sorted((coarse_distance(query,item["coarse"]),item) for item in historical)[:20]
                for _,item in sorted((feature_distance(question_frame["f"],item["f"]),item) for _,item in rough):
                    signature=action_signature(item["a"])
                    if signature not in signatures:
                        signatures.add(signature)
                        choices.append({"a":item["a"],"repeat_policy":item.get("repeat_policy","one_shot"),"cluster_id":item["cluster_id"]})
                    if len(choices)>=2:
                        break
            distractors=list(unique)
            random.shuffle(distractors)
            for entry in distractors:
                signature=action_signature(entry["a"])
                if signature and signature not in signatures:
                    signatures.add(signature)
                    choices.append(dict(entry))
                if len(choices)>=4:
                    break
            random.shuffle(choices)
            choices=choices[:4]
            candidates=[{"cluster_id":entry.get("cluster_id",""),"canonical_action_signature":action_signature(entry["a"]),"a":entry["a"]} for entry in choices]
            return choices,candidates
        def new_question():
            if self.ask_window is None:
                return
            set_locked(True)
            try:
                self.api.validate_target(target,False)
            except Exception as error:
                if not state["initialized"] and time.monotonic()>=state["init_deadline"]:
                    self.close_ask(show_summary=False,wait_buffer=False)
                    self.show_error("请教启动失败："+str(error))
                    return
                self.status.set("请教等待目标窗口恢复或等待后台采集画面："+str(error))
                schedule(180,new_question)
                return
            question_frame,ranked=select_question_frame()
            if question_frame is None:
                if not state["initialized"] and time.monotonic()>=state["init_deadline"]:
                    message=self.ask_buffer.last_error if self.ask_buffer is not None else "尚无画面"
                    self.close_ask(show_summary=False,wait_buffer=False)
                    self.show_error("请教启动失败：未在3秒内获得合格画面；"+str(message))
                    return
                self.status.set("请教等待目标窗口恢复或等待后台采集画面："+(self.ask_buffer.last_error if self.ask_buffer is not None else "尚无画面"))
                schedule(160,new_question)
                return
            if not question_frame.get("usable_for_teaching"):
                if not state["initialized"] and time.monotonic()>=state["init_deadline"]:
                    self.close_ask(show_summary=False,wait_buffer=False)
                    self.show_error("请教启动失败：采集画面未通过黑屏、重复、动态后端或质量验收")
                    return
                state["frame"]=question_frame
                state["choices"]=[]
                state["candidates"]=[]
                render(question_frame,[])
                self.status.set("当前画面仅可预览，因黑屏、重复、未验收或后端变化而拒绝请教答案")
                schedule(180,new_question)
                return
            state["initialized"]=True
            choices,candidates=make_choices(question_frame,ranked)
            state["frame"]=question_frame
            state["choices"]=choices
            state["candidates"]=candidates
            render(question_frame,choices)
            for index,button in enumerate(answer_buttons):
                if index<len(choices):
                    button.configure(text=chr(65+index)+". "+self.action_text(choices[index]["a"]))
                else:
                    button.configure(text=chr(65+index)+". 无可用答案")
            set_locked(False)
        def context_for(entry=None):
            question_frame=state["frame"] or {}
            policy=str((entry or {}).get("repeat_policy","one_shot"))
            temporal=self.build_temporal_context(self.ask_buffer,question_frame,state["recent_actions"],state["state_since"])
            temporal["previous_action_changed_frame"]=True
            return self.sample_context(state["recent_actions"][-1] if state["recent_actions"] else "",0,True,question_frame.get("motion_valid",False),self.ask_session_id,question_frame.get("method","unknown"),policy,temporal)
        def finish_answer():
            self.status.set("请教中：已保存"+str(count["saved"])+"，重复未保存"+str(count["duplicates"])+"，跳过"+str(count["skipped"])+"，拒绝记录"+str(count["rejected"])+"；模型需要复习")
            schedule(140,new_question)
        def choose(index):
            if self.ask_window is None or state["locked"] or index>=len(state["choices"]):
                return
            set_locked(True)
            try:
                entry=state["choices"][index]
                question_frame=state["frame"]
                if not question_frame.get("usable_for_teaching"):
                    raise CaptureUnavailable("当前画面不可用于请教")
                saved=self.store.append_sample(game["id"],question_frame["f"],entry["a"],"teach_live",context_for(entry),question_frame.get("gray"),3.0)
                count["saved" if saved else "duplicates"]+=1
                if saved:
                    state["recent_actions"].append(action_signature(entry["a"]))
                    state["state_since"]=time.time()
                finish_answer()
            except Exception as error:
                self.close_ask(show_summary=False,wait_buffer=False)
                self.show_error("请教数据库写入失败，已逆序释放资源："+str(error))
        def skip():
            if state["locked"]:
                return
            set_locked(True); count["skipped"]+=1; finish_answer()
        def reject():
            if state["locked"]:
                return
            set_locked(True)
            try:
                question_frame=state["frame"]
                if not question_frame.get("usable_for_teaching"):
                    raise CaptureUnavailable("当前画面不可用于请教")
                self.store.append_rejection(game["id"],question_frame["f"],state["candidates"],"teach_live_reject",question_frame.get("gray"),context_for())
                count["rejected"]+=1
                finish_answer()
            except Exception as error:
                self.close_ask(show_summary=False,wait_buffer=False)
                self.show_error("请教数据库写入失败，已逆序释放资源："+str(error))
        def custom():
            if state["locked"]:
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
            ttk.Label(dialog,text="在画面上单击可选择位置；拖动可定义移动或拖动路径。其他动作也会使用最后位置。",wraplength=720).pack(pady=(0,8))
            custom_canvas=tk.Canvas(dialog,width=672,height=378,bg="black",highlightthickness=1,highlightbackground="#777777")
            custom_canvas.pack()
            custom_canvas.create_image(336,189,image=state["image"][1])
            path_state={"start":[0.5,0.5],"end":[0.5,0.5],"line":None}
            def press(event):
                path_state["start"]=[max(0,min(671,event.x))/671,max(0,min(377,event.y))/377]
                path_state["end"]=list(path_state["start"])
            def motion_event(event):
                path_state["end"]=[max(0,min(671,event.x))/671,max(0,min(377,event.y))/377]
                if path_state["line"]:
                    custom_canvas.delete(path_state["line"])
                path_state["line"]=custom_canvas.create_line(path_state["start"][0]*671,path_state["start"][1]*377,path_state["end"][0]*671,path_state["end"][1]*377,width=3,arrow="last")
            def release(event):
                motion_event(event)
            error_var=tk.StringVar()
            ttk.Label(dialog,textvariable=error_var).pack()
            def submit():
                try:
                    kind=kind_var.get()
                    duration=float(duration_var.get())
                    if kind=="no_op":
                        raw={"kind":kind,"duration":duration}
                    elif kind in {"scroll_v","scroll_h"}:
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
                    question_frame=state["frame"]
                    entry={"a":action,"repeat_policy":policy_var.get()}
                    if not question_frame.get("usable_for_teaching"):
                        raise CaptureUnavailable("当前画面不可用于请教")
                    saved=self.store.append_sample(game["id"],question_frame["f"],action,"teach_live_custom",context_for(entry),question_frame.get("gray"),3.5)
                    count["saved" if saved else "duplicates"]+=1
                    if saved:
                        state["recent_actions"].append(action_signature(action))
                        state["state_since"]=time.time()
                    dialog.destroy(); finish_answer()
                except Exception as error:
                    try:
                        dialog.destroy()
                    except Exception:
                        pass
                    self.close_ask(show_summary=False,wait_buffer=False)
                    self.show_error("请教数据库写入失败，已逆序释放资源："+str(error))
            def cancel():
                dialog.destroy(); set_locked(False)
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
        ttk.Button(tools,text="结束请教",command=self.close_ask).pack(side="right")
        win.protocol("WM_DELETE_WINDOW",self.close_ask)
        self.ask_escape_armed=not self.api.key_down(0x1B)
        def poll_escape():
            if self.ask_window is None:
                return
            down=self.api.key_down(0x1B)
            if not down:
                self.ask_escape_armed=True
            elif self.ask_escape_armed:
                self.close_ask(); return
            schedule(45,poll_escape)
        schedule(120,new_question)
        poll_escape()
        win.wait_visibility()
        win.focus_force()
    def close_ask(self,show_summary=True,wait_buffer=True):
        if self.ask_window is None and self.ask_buffer is None:
            return
        win=self.ask_window
        self.ask_window=None
        if win is not None:
            for after_id in list(self.ask_after_ids):
                try:
                    win.after_cancel(after_id)
                except Exception:
                    pass
            self.ask_after_ids.clear()
        if self.ask_buffer is not None:
            self.ask_buffer.stop(wait_buffer,1.0)
            if wait_buffer or not self.ask_buffer.alive():
                self.ask_buffer=None
        if win is not None:
            try:
                win.destroy()
            except Exception:
                pass
        summary="请教已结束"
        if isinstance(self.ask_counts,dict):
            summary+="：已保存"+str(self.ask_counts.get("saved",0))+"，重复未保存"+str(self.ask_counts.get("duplicates",0))+"，跳过"+str(self.ask_counts.get("skipped",0))+"，拒绝记录"+str(self.ask_counts.get("rejected",0))+"；模型需要复习"
        self.ask_session_id=None
        self.ask_counts=None
        self.mode=None
        if not self.closing:
            self.set_controls(False)
            self.status.set(summary)
            self._refresh_all()
            if show_summary:
                self.show_info("请教完成",summary)
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
        self.shutdown_deadline=time.monotonic()+3.0
        self.status.set("正在安全关闭：最多等待3秒")
        if self.stop_event:
            self.stop_event.set()
        self.api.block_input()
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
        if self.ask_window is not None:
            self.close_ask(show_summary=False,wait_buffer=False)
        self._poll_shutdown()
    def _poll_shutdown(self):
        self.api.block_input()
        mode_alive=bool(self.mode_thread and self.mode_thread.is_alive())
        ask_alive=bool(self.ask_buffer and self.ask_buffer.alive())
        deadline_reached=bool(self.shutdown_deadline is not None and time.monotonic()>=self.shutdown_deadline)
        if (mode_alive or ask_alive) and not deadline_reached:
            try:
                self.root.after(50,self._poll_shutdown)
            except Exception:
                pass
            return
        self.shutdown_started=True
        try:
            if self.ask_buffer is not None:
                self.ask_buffer.stop(False,0.0)
        except Exception:
            pass
        def close_resources():
            try:
                self.api.wgc.close()
            except Exception:
                pass
            try:
                self.store.close()
            except Exception:
                pass
        threading.Thread(target=close_resources,name="UniversalGameAI-FinalClose",daemon=True).start()
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
def main():
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
