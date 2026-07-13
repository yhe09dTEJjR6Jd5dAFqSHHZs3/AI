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
FORMAT_VERSION=4
FEATURE_W=64
FEATURE_H=36
FEATURE_CHANNELS=5
PIXELS=FEATURE_W*FEATURE_H
FEATURE_LEN=PIXELS*FEATURE_CHANNELS
COARSE_W=16
COARSE_H=9
COARSE_LEN=COARSE_W*COARSE_H*FEATURE_CHANNELS
FEATURE_ALGORITHM_VERSION=4
ACTION_ALGORITHM_VERSION=5
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
        result=bytearray(PIXELS*3)
        for oy in range(FEATURE_H):
            sy0=top+oy*crop_h//FEATURE_H
            sy1=max(sy0+1,top+(oy+1)*crop_h//FEATURE_H)
            ystep=max(1,(sy1-sy0)//4)
            for ox in range(FEATURE_W):
                sx0=left+ox*crop_w//FEATURE_W
                sx1=max(sx0+1,left+(ox+1)*crop_w//FEATURE_W)
                xstep=max(1,(sx1-sx0)//4)
                rs=gs=bs=count=0
                for sy in range(sy0,min(height,sy1),ystep):
                    row=sy*row_pitch
                    for sx in range(sx0,min(width,sx1),xstep):
                        index=row+sx*4
                        bs+=raw[index]
                        gs+=raw[index+1]
                        rs+=raw[index+2]
                        count+=1
                position=(oy*FEATURE_W+ox)*3
                result[position]=round(rs/max(1,count))
                result[position+1]=round(gs/max(1,count))
                result[position+2]=round(bs/max(1,count))
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
        self._bind()
        self.previous_frames={}
        self.frame_lock=threading.RLock()
        self.held=set()
        self.input_lock=threading.RLock()
        self.capture_health={}
        self.capture_reports={}
        self.calibrations={}
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
    def _rgb_from_raw(self,raw,width,height,out_w=FEATURE_W,out_h=FEATURE_H):
        result=bytearray(out_w*out_h*3)
        for oy in range(out_h):
            sy0=oy*height//out_h
            sy1=max(sy0+1,(oy+1)*height//out_h)
            ystep=max(1,(sy1-sy0)//4)
            for ox in range(out_w):
                sx0=ox*width//out_w
                sx1=max(sx0+1,(ox+1)*width//out_w)
                xstep=max(1,(sx1-sx0)//4)
                rs=gs=bs=count=0
                for sy in range(sy0,min(height,sy1),ystep):
                    row=sy*width*4
                    for sx in range(sx0,min(width,sx1),xstep):
                        index=row+sx*4
                        bs+=raw[index]
                        gs+=raw[index+1]
                        rs+=raw[index+2]
                        count+=1
                position=(oy*out_w+ox)*3
                result[position]=round(rs/max(1,count))
                result[position+1]=round(gs/max(1,count))
                result[position+2]=round(bs/max(1,count))
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
            memory,bitmap,old,bits=self._make_dib(source,FEATURE_W,FEATURE_H)
            self.gdi32.SetStretchBltMode(memory,4)
            if not self.gdi32.StretchBlt(memory,0,0,FEATURE_W,FEATURE_H,source,sx,sy,width,height,0x00CC0020):
                raise CaptureUnavailable("窗口DC采集失败")
            raw=ctypes.string_at(bits.value,FEATURE_W*FEATURE_H*4)
            return self._rgb_from_raw(raw,FEATURE_W,FEATURE_H)
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
        gray=self._rgb_to_gray(rgb)
        if gray is None or not gray:
            return {"mean":0.0,"std":0.0,"spread":0,"black":True,"solid":True,"low_information":True,"valid":False}
        mean=sum(gray)/len(gray)
        variance=sum((value-mean)*(value-mean) for value in gray)/len(gray)
        std=math.sqrt(variance)
        spread=max(gray)-min(gray)
        black=max(gray)<10 or mean<2.5
        solid=std<0.9 or spread<3
        return {"mean":mean,"std":std,"spread":spread,"black":black,"solid":solid,"low_information":bool(black or solid),"valid":True}
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
    def capture_gray(self,target,require_foreground_for_desktop=True):
        rect=self.validate_target(target,False)
        hwnd=int(target["hwnd"])
        x,y,width,height=rect
        attempts=[]
        candidates=[]
        backends=[("Windows Graphics Capture",lambda:self.wgc.capture(hwnd,rect)),("PrintWindow客户区",lambda:self._capture_print(hwnd,width,height)),("窗口DC",lambda:self._capture_dc(hwnd,0,0,width,height))]
        if not require_foreground_for_desktop or self.foreground_hwnd()==hwnd:
            backends.append(("前台桌面裁剪",lambda:self._capture_dc(0,x,y,width,height)))
        else:
            attempts.append("前台桌面裁剪被跳过：目标窗口不在前台")
        for priority,(name,callback) in enumerate(backends):
            try:
                rgb=rgb_bytes(callback())
                if rgb is None:
                    raise CaptureUnavailable("返回画面尺寸无效")
                quality=self._quality(rgb)
                stale=self._health(hwnd,name,rgb)
                quality["stale_suspected"]=stale
                candidate={"rgb":rgb,"gray":self._rgb_to_gray(rgb),"method":name,"quality":quality,"priority":priority,"stale":stale}
                candidates.append(candidate)
                if quality["valid"] and not quality["low_information"] and not stale:
                    self.capture_reports[hwnd]="当前采集："+name+"；兼容性检测正常"
                    return candidate
                reason=[]
                if quality["low_information"]:
                    reason.append("低信息量画面")
                if stale:
                    reason.append("疑似长时间未更新")
                attempts.append(name+"："+"、".join(reason or ["可用"]))
            except Exception as error:
                attempts.append(name+"失败："+str(error))
        if candidates:
            chosen=min(candidates,key=lambda item:(item["stale"],item["priority"]))
            state="合法低信息量画面" if chosen["quality"]["low_information"] else "疑似静止画面"
            self.capture_reports[hwnd]="当前采集："+chosen["method"]+"；"+state+"；已完成多后端兼容性检测"
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
        return self.capture_reports.get(int(hwnd),"尚未执行采集兼容性检测；优先Windows Graphics Capture，失败后自动降级")
    def calibration_for(self,target):
        hwnd=int(target.get("hwnd",0)) if isinstance(target,dict) else int(target or 0)
        return dict(self.calibrations.get(hwnd,{"noise":4.0,"visual_cluster":420.0,"significant_change":60.0,"post_action_change":45.0,"freeze_change":1.5,"freeze_frames":30,"confirm_frames":2,"duplicate":3.0,"fps":10.0,"input_delay":0.24}))
    def calibrate(self,target,duration=1.2):
        hwnd=int(target["hwnd"])
        deadline=time.time()+max(0.6,min(2.5,float(duration)))
        features=[]
        methods=Counter()
        stamps=[]
        previous_rgb=None
        while time.time()<deadline:
            captured=self.capture_gray(target,True)
            feature=self.feature_from_rgb(captured["rgb"],previous_rgb)
            previous_rgb=captured["rgb"]
            features.append(feature)
            methods[captured["method"]]+=1
            stamps.append(time.time())
            time.sleep(0.06)
        changes=[visual_distance(a,b) for a,b in zip(features,features[1:]) if feature_valid(a) and feature_valid(b)]
        noise=max(0.5,quantile(changes,0.9)) if changes else 4.0
        fps=(len(stamps)-1)/max(0.01,stamps[-1]-stamps[0]) if len(stamps)>1 else 8.0
        result={"noise":noise,"visual_cluster":max(80.0,min(1400.0,noise*9.0+120.0)),"significant_change":max(18.0,min(260.0,noise*4.5+18.0)),"post_action_change":max(14.0,min(220.0,noise*3.2+14.0)),"freeze_change":max(0.4,noise*0.22),"freeze_frames":max(18,min(80,round(fps*3.0))),"confirm_frames":2 if fps>=12 else 3,"duplicate":max(1.0,min(18.0,noise*0.65)),"fps":fps,"input_delay":max(0.16,min(0.55,3.0/max(5.0,fps))),"method":methods.most_common(1)[0][0] if methods else "未知"}
        self.calibrations[hwnd]=result
        self.capture_reports[hwnd]=self.capture_status(hwnd)+"；校准帧率"+str(round(fps,1))+"fps，静态噪声"+str(round(noise,2))
        return dict(result)
    def _send(self,flags,data=0,dx=0,dy=0):
        item=INPUT()
        item.type=0
        item.mi=MOUSEINPUT(int(dx),int(dy),ctypes.c_ulong(int(data)&0xffffffff).value,int(flags),0,0)
        if self.user32.SendInput(1,ctypes.byref(item),ctypes.sizeof(INPUT))!=1:
            raise ctypes.WinError(ctypes.get_last_error())
    def move_cursor(self,x,y):
        left=self.user32.GetSystemMetrics(76)
        top=self.user32.GetSystemMetrics(77)
        width=self.user32.GetSystemMetrics(78)
        height=self.user32.GetSystemMetrics(79)
        nx=round((int(x)-left)*65535/max(1,width-1))
        ny=round((int(y)-top)*65535/max(1,height-1))
        self._send(0x0001|0x8000|0x4000,0,nx,ny)
    def button(self,button,down):
        flags={"left":(0x0002,0x0004),"right":(0x0008,0x0010),"middle":(0x0020,0x0040)}
        if button not in flags:
            raise RuntimeError("不支持的鼠标按钮")
        with self.input_lock:
            self._send(flags[button][0 if down else 1])
            if down:
                self.held.add(button)
            else:
                self.held.discard(button)
    def wheel(self,delta,horizontal=False):
        self._send(0x01000 if horizontal else 0x0800,int(delta))
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
        self.thread=threading.Thread(target=self._run)
        self.thread.start()
        self.ready.wait(2.0)
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
    def stop(self):
        if self.thread_id:
            try:
                self.bridge.user32.PostThreadMessageW(self.thread_id,0x0012,0,0)
            except Exception:
                pass
        if self.thread and self.thread.is_alive() and self.thread is not threading.current_thread():
            self.thread.join()
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
        self.thread=threading.Thread(target=self._run)
        self.thread.start()
        return self
    def _run(self):
        thread_id=threading.get_ident()
        next_time=time.time()
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
                    frame={"time":stamp,"f":feature,"coarse":coarse_feature(feature),"gray":gray,"rgb":rgb,"method":captured["method"],"quality":captured["quality"],"motion_valid":previous is not None,"rect":rect,"dpi":self.bridge.dpi_for_window(int(self.target["hwnd"]))}
                    with self.lock:
                        self.frames.append(frame)
                    self.last_error=""
                    self.ready.set()
                except Exception as error:
                    self.last_error=str(error)
                next_time=max(next_time+self.interval,time.time())
                self.stop_event.wait(max(0.001,next_time-time.time()))
        finally:
            try:
                self.bridge.wgc.release_thread(thread_id)
            except Exception:
                pass
    def latest(self,before=None,max_age=0.6):
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
    def stop(self,wait=True):
        self.stop_event.set()
        if wait and self.thread and self.thread.is_alive() and self.thread is not threading.current_thread():
            self.thread.join()
    def alive(self):
        return bool(self.thread and self.thread.is_alive())
class DataStore:
    def __init__(self):
        local=os.environ.get("LOCALAPPDATA")
        self.base=(Path(local) if local else Path.home()/"AppData"/"Local")/APP_NAME
        self.base.mkdir(parents=True,exist_ok=True)
        self.db_path=self.base/"universal_game_ai.db"
        self.lock=threading.RLock()
        self.model_cache={}
        self.closed=False
        self.db=sqlite3.connect(str(self.db_path),timeout=20.0,check_same_thread=False)
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
    def _sample_fingerprint(self,feature,action):
        return hashlib.sha256(feature_bytes(feature)+b"\0"+canonical_bytes(normalize_action(action))).hexdigest()
    def _near_duplicate(self,gid,feature,signature,threshold):
        with self.lock:
            rows=self.db.execute("SELECT feature,feature_algorithm_version FROM samples WHERE game_id=? AND action_signature=? ORDER BY created DESC,id DESC LIMIT 36",(gid,signature)).fetchall()
        query=feature_bytes(feature)
        query_coarse=coarse_feature(query)
        for row in rows:
            try:
                candidate=upgrade_feature(zlib.decompress(row["feature"]),row["feature_algorithm_version"])
                if candidate is None:
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
        fingerprint=self._sample_fingerprint(fbytes,clean)
        kind=clean["kind"]
        with self.lock:
            if not self.db.execute("SELECT 1 FROM games WHERE id=?",(gid,)).fetchone():
                raise RuntimeError("游戏不存在")
            if enforce_quota and kind=="no_op":
                row=self.db.execute("SELECT SUM(CASE WHEN kind='no_op' THEN 1 ELSE 0 END) AS noops,SUM(CASE WHEN kind!='no_op' THEN 1 ELSE 0 END) AS actions FROM samples WHERE game_id=?",(gid,)).fetchone()
                if int(row["noops"] or 0)>=max(1,int(row["actions"] or 0)//3):
                    return False
            if enforce_quota and self._near_duplicate(gid,fbytes,signature,duplicate_threshold):
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
            feature_version=int(item.get("feature_algorithm_version",3))
            upgraded=[]
            for proto in item.get("prototypes",[]):
                if not isinstance(proto,dict):
                    return None
                action=normalize_action(proto.get("a"))
                feature=upgrade_feature(proto.get("f"),feature_version)
                if not action or feature is None:
                    return None
                entry=dict(proto)
                entry["f"]=feature
                entry["coarse"]=coarse_feature(feature)
                old_identifier=str(entry.get("cluster_id") or entry.get("action_signature") or "")
                if old_identifier.startswith("action|"):
                    cluster_id=old_identifier
                else:
                    token=hashlib.sha256(canonical_bytes({"a":action,"old":old_identifier})).hexdigest()[:20]
                    cluster_id="action|"+action_family_key(action)+"|"+token
                entry["cluster_id"]=cluster_id
                entry["canonical_action_signature"]=str(entry.get("canonical_action_signature") or action_signature(action))
                entry.pop("action_signature",None)
                if str(entry.get("previous_action","")).startswith("action|"):
                    entry["previous_action"]=""
                policy=str(entry.get("repeat_policy","one_shot"))
                entry["repeat_policy"]=policy if policy in REPEAT_POLICIES else "one_shot"
                entry["max_rate"]=float(entry.get("max_rate",3.0)) if finite_number(entry.get("max_rate",3.0)) else 3.0
                conflict=entry.get("nearest_conflicting_distance")
                entry["ambiguous"]=bool(entry.get("ambiguous",conflict is not None and finite_number(conflict) and float(conflict)<=max(1e-6,float(entry.get("threshold",1.0))*0.05)))
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
            if not isinstance(prototypes,list) or not prototypes:
                return False
            for proto in prototypes:
                if not isinstance(proto,dict) or not str(proto.get("id","")) or not str(proto.get("cluster_id","")) or not str(proto.get("canonical_action_signature","")) or not feature_valid(proto.get("f")) or not isinstance(proto.get("coarse"),(bytes,bytearray)) or len(proto.get("coarse"))!=COARSE_LEN or not normalize_action(proto.get("a")) or not finite_number(proto.get("threshold")) or float(proto.get("threshold"))<=0 or int(proto.get("support",0))<=0:
                    return False
                conflict=proto.get("nearest_conflicting_distance")
                if conflict is not None and (not finite_number(conflict) or float(conflict)<0):
                    return False
                rejected=proto.get("nearest_rejected_distance")
                if rejected is not None and (not finite_number(rejected) or float(rejected)<0):
                    return False
                if not finite_number(proto.get("minimum_second_candidate_gap",0)) or str(proto.get("repeat_policy","one_shot")) not in REPEAT_POLICIES or not finite_number(proto.get("max_rate",1.0)) or float(proto.get("max_rate",1.0))<=0:
                    return False
            return isinstance(item.get("validation"),dict)
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
        self.error_windows=[]
        self.info_windows=[]
        self.ui_queue=queue.Queue()
        self.closing=False
        self.shutdown_started=False
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
        win=tk.Toplevel(self.root)
        self.error_windows.append(win)
        win.title("报错信息")
        win.geometry("700x390")
        win.minsize(500,300)
        win.transient(self.root)
        frame=ttk.Frame(win,padding=14)
        frame.pack(fill="both",expand=True)
        ttk.Label(frame,text="报错信息",font=("Microsoft YaHei UI",14,"bold")).pack(anchor="w",pady=(0,8))
        body=ttk.Frame(frame)
        body.pack(fill="both",expand=True)
        widget=tk.Text(body,wrap="word",font=("Microsoft YaHei UI",10),relief="solid",borderwidth=1)
        scroll=ttk.Scrollbar(body,orient="vertical",command=widget.yview)
        widget.configure(yscrollcommand=scroll.set)
        widget.pack(side="left",fill="both",expand=True)
        scroll.pack(side="right",fill="y")
        widget.insert("1.0",message)
        widget.configure(state="disabled")
        def close_error():
            try:
                self.error_windows.remove(win)
            except ValueError:
                pass
            win.destroy()
        ttk.Button(frame,text="确认",command=close_error).pack(pady=(12,0),ipadx=24)
        win.bind("<Return>",lambda event:close_error())
        win.protocol("WM_DELETE_WINDOW",close_error)
        win.wait_visibility()
        win.focus_force()
    def show_info(self,title,text):
        if threading.current_thread() is not threading.main_thread():
            self.ui(lambda:self.show_info(title,text))
            return
        if self.shutdown_started:
            return
        win=tk.Toplevel(self.root)
        self.info_windows.append(win)
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
        scroll=ttk.Scrollbar(body,orient="vertical",command=widget.yview)
        widget.configure(yscrollcommand=scroll.set)
        widget.pack(side="left",fill="both",expand=True)
        scroll.pack(side="right",fill="y")
        widget.insert("1.0",str(text))
        widget.configure(state="disabled")
        def confirm():
            try:
                self.info_windows.remove(win)
            except ValueError:
                pass
            try:
                win.destroy()
            except Exception:
                pass
        ttk.Button(frame,text="确认",command=confirm).pack(pady=(12,0),ipadx=28)
        win.bind("<Return>",lambda event:confirm())
        win.protocol("WM_DELETE_WINDOW",confirm)
        win.wait_visibility()
        win.focus_force()
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
        win.geometry("820x540")
        win.transient(self.root)
        win.grab_set()
        frame=ttk.Frame(win,padding=16)
        frame.pack(fill="both",expand=True)
        ttk.Label(frame,text="选择雷电模拟器窗口或其他窗口",font=("Microsoft YaHei UI",13,"bold")).pack(anchor="w",pady=(0,6))
        ttk.Label(frame,text="确认后会短暂执行后台采集兼容性与窗口自适应阈值校准。",wraplength=760).pack(anchor="w",pady=(0,10))
        list_frame=ttk.Frame(frame)
        list_frame.pack(fill="both",expand=True)
        box=tk.Listbox(list_frame,exportselection=False,font=("Microsoft YaHei UI",10))
        scroll=ttk.Scrollbar(list_frame,orient="vertical",command=box.yview)
        box.configure(yscrollcommand=scroll.set)
        box.pack(side="left",fill="both",expand=True)
        scroll.pack(side="right",fill="y")
        windows=[]
        def refresh():
            nonlocal windows
            windows=self.api.enum_windows()
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
            self.api.validate_target(item,False)
            self.status.set("正在检测窗口采集兼容性并校准阈值")
            try:
                calibration=self.api.calibrate(item,1.2)
            except Exception as error:
                self.api.capture_reports[item["hwnd"]]="兼容性检测未完成："+str(error)+"；运行时仍会按WGC、PrintWindow、窗口DC、前台裁剪顺序降级"
                calibration=self.api.calibration_for(item)
            self.selected_window=item
            self.api.reset_frame_history(item["hwnd"])
            self._refresh_all()
            self.status.set("已选择窗口："+item["title"]+"；校准帧率"+str(round(float(calibration.get("fps",0.0)),1))+"fps")
            win.destroy()
        tools=ttk.Frame(frame)
        tools.pack(fill="x",pady=(10,0))
        ttk.Button(tools,text="刷新",command=refresh).pack(side="left")
        ttk.Button(tools,text="确认",command=confirm).pack(side="right",padx=(6,0))
        ttk.Button(tools,text="取消",command=win.destroy).pack(side="right")
        box.bind("<Double-Button-1>",lambda event:confirm())
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
        self.set_controls(True)
        self.progress_value.set(0)
        self.status.set(name+"已开始，按ESC或点击“停止”结束")
        self.mode_thread=threading.Thread(target=self.worker_entry,args=(name,target),name="UniversalGameAI-"+name,daemon=False)
        self.mode_thread.start()
    def worker_entry(self,name,target):
        error=None
        final_text=name+"已结束"
        try:
            final_text=target()
        except Exception:
            error=traceback.format_exc()
        finally:
            self.api.release_all_buttons()
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
        self.api.release_all_buttons()
        if self.ask_window is not None:
            self.close_ask()
            return
        if self.stop_event:
            self.stop_event.set()
            self.status.set("正在停止，已释放全部鼠标键")
    def wait_escape_release(self):
        while self.api.key_down(0x1B) and self.stop_event and not self.stop_event.is_set():
            time.sleep(0.04)
    def should_stop(self):
        if not self.stop_event or self.stop_event.is_set():
            return True
        if self.api.key_down(0x1B):
            self.stop_event.set()
            self.api.release_all_buttons()
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
    def sample_context(self,last_signature,last_time,last_changed,motion_valid=True,session_id="",capture_method="unknown",repeat_policy="one_shot"):
        calibration=self.api.calibration_for(self.selected_window.get("hwnd") if self.selected_window else 0)
        return {"previous_action":last_signature or "","seconds_since_previous":round(max(0.0,min(60.0,time.time()-last_time)) if last_time else 60.0,3),"previous_action_changed_frame":bool(last_changed),"motion_channel_valid":bool(motion_valid),"session_id":str(session_id or "unspecified"),"capture_method":str(capture_method or "unknown"),"repeat_policy":repeat_policy if repeat_policy in REPEAT_POLICIES else "one_shot","duplicate_threshold":float(calibration.get("duplicate",3.0)),"calibration":dict(calibration)}
    def start_learning(self):
        self.start_worker("学习",self.learning_worker,True)
    def learning_worker(self):
        game=self.require_game()
        target=self.require_window(False)
        hwnd=target["hwnd"]
        session_id="learn|"+uuid.uuid4().hex
        calibration=self.api.calibration_for(target)
        focused=self.api.request_foreground(hwnd)
        if not focused:
            self.set_status("无法自动切换到目标窗口，学习将等待目标窗口成为前台")
        self.wait_escape_release()
        frame_buffer=FrameBuffer(self.api,target,20.0,2.0,0.1).start()
        monitor=MouseMonitor(self.api)
        monitor.start()
        active={}
        pending_click={}
        learned=0
        discarded=0
        duplicates=0
        invalid_frames=0
        last_action_signature=""
        last_action_time=0.0
        last_action_feature=None
        last_action_changed=True
        last_negative=0.0
        last_motion_time=0.0
        motion=None
        last_cursor=None
        hover_start=0.0
        hover_point=None
        last_update=0.0
        def capture_safe(stamp=None):
            nonlocal invalid_frames
            frame=frame_buffer.latest(stamp,0.75)
            if frame is None:
                invalid_frames+=1
            return frame
        def save(frame,action,source,weight=1.0):
            nonlocal learned,duplicates,last_action_signature,last_action_time,last_action_feature,last_action_changed
            if frame is None:
                return False
            context=self.sample_context(last_action_signature,last_action_time,last_action_changed,frame.get("motion_valid",False),session_id,frame.get("method","unknown"),"one_shot")
            saved=self.store.append_sample(game["id"],frame["f"],action,source,context,frame.get("gray"),weight)
            if saved:
                learned+=1
                last_action_signature=action_signature(action)
                last_action_time=time.time()
                last_action_changed=True if last_action_feature is None else visual_distance(last_action_feature,frame["f"])>float(calibration.get("significant_change",60.0))
                last_action_feature=frame["f"]
            else:
                duplicates+=1
            return saved
        def save_click(button,item):
            save(item["frame"],{"kind":"click","button":button,"path":[item["point"]],"duration":item["duration"]},"learn")
        def flush_pending(now,force=False):
            for button,item in list(pending_click.items()):
                if force or now-item["time"]>0.42:
                    save_click(button,item)
                    pending_click.pop(button,None)
        try:
            while not self.should_stop():
                now=time.time()
                try:
                    rect=self.api.validate_target(target,True)
                    focused=True
                except TargetUnavailable:
                    focused=False
                    active.clear()
                    if motion is not None:
                        motion["outside"]=True
                    motion=None
                    last_cursor=None
                    hover_point=None
                    hover_start=0.0
                    self.api.release_all_buttons()
                    self.set_status("目标窗口失去焦点，等待恢复；已释放全部鼠标键")
                events=monitor.drain()
                if not focused:
                    flush_pending(now)
                    time.sleep(0.05)
                    continue
                for event in events:
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
                        if motion is not None:
                            motion["outside"]=True
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
                            if motion is not None and motion.get("outside"):
                                discarded+=1
                                motion=None
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
                                last_cursor=None
                                hover_point=None
                                hover_start=0.0
                                continue
                            point=self.normalize_point(x,y,rect)
                            item["path"].append(point)
                            duration=max(0.03,min(3.0,event_time-item["start"]))
                            length=path_length(item["path"])
                            if length>0.045:
                                save(item["frame"],{"kind":"drag","button":button,"path":item["path"],"duration":duration},"learn",1.4)
                            elif duration>=0.48:
                                save(item["frame"],{"kind":"long_press","button":button,"path":[point],"duration":duration},"learn",1.2)
                            else:
                                previous=pending_click.get(button)
                                if previous:
                                    click_gap=item["start"]-previous["time"]
                                    close=math.hypot(point[0]-previous["point"][0],point[1]-previous["point"][1])<=0.035
                                    if click_gap<=0.42 and close:
                                        pending_click.pop(button,None)
                                        save(previous["frame"],{"kind":"double_click","button":button,"path":[previous["point"]],"duration":max(0.06,event_time-previous["time"])},"learn",1.3)
                                        continue
                                    save_click(button,previous)
                                    pending_click.pop(button,None)
                                pending_click[button]={"frame":item["frame"],"point":point,"duration":duration,"time":event_time}
                    elif etype in {"wheel","hwheel"} and inside and not active:
                        frame=capture_safe(event_time)
                        if frame is not None:
                            save(frame,{"kind":"scroll_h" if etype=="hwheel" else "scroll_v","delta":event.get("delta",0),"path":[self.normalize_point(x,y,rect)],"duration":0.08},"learn",1.2)
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
                        save(motion["frame"],{"kind":"move","path":motion["path"],"duration":max(0.05,min(2.0,now-motion["start"]))},"learn")
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
                                save(frame,{"kind":"hover","path":[current_point],"duration":0.85},"learn")
                            hover_start=now+1.5
                        else:
                            hover_point=current_point
                            hover_start=now
                    else:
                        last_cursor=None
                        hover_point=None
                        hover_start=0.0
                        if motion is not None:
                            motion["outside"]=True
                if not active and not pending_click and now-last_negative>0.9 and now-last_motion_time>0.35:
                    frame=capture_safe(now)
                    if frame is not None:
                        save(frame,{"kind":"no_op","duration":0.45},"negative",0.6)
                    last_negative=now
                if now-last_update>0.45:
                    self.set_status("学习中：有效"+str(learned)+"  重复或配额抑制"+str(duplicates)+"  越界废弃"+str(discarded)+"  无效画面"+str(invalid_frames)+"；事件使用发生前最近帧，仅保存全程位于客户区内的动作")
                    last_update=now
                time.sleep(0.012)
        finally:
            flush_pending(time.time(),True)
            monitor.stop()
            frame_buffer.stop()
            self.api.release_all_buttons()
        return "学习已结束：有效"+str(learned)+"，重复或配额抑制"+str(duplicates)+"，废弃"+str(discarded)+"，无效画面"+str(invalid_frames)
    def _prototype_medoid(self,members):
        if len(members)==1:
            return members[0]
        candidates=members if len(members)<=28 else [members[round(index*(len(members)-1)/27)] for index in range(28)]
        comparisons=members if len(members)<=72 else [members[round(index*(len(members)-1)/71)] for index in range(72)]
        best=candidates[0]
        best_total=float("inf")
        for candidate in candidates:
            total=0.0
            for other in comparisons:
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
        return min(candidates,key=lambda candidate:sum(action_geometry_distance(candidate["a"],other["a"])*float(other.get("weight",1.0)) for other in comparisons))
    def _cluster_action_samples(self,samples):
        families=defaultdict(list)
        for sample in samples:
            family=action_family_key(sample["a"])
            if family:
                families[family].append(sample)
        clusters=[]
        for family,items in sorted(families.items()):
            if self.should_stop():
                break
            local=[]
            for item in sorted(items,key=lambda value:str(value.get("checksum",""))):
                if self.should_stop():
                    break
                if not local:
                    local.append({"family":family,"members":[item],"medoid":item})
                    continue
                distances=[action_geometry_distance(item["a"],cluster["medoid"]["a"]) for cluster in local]
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
                        limit=min(action_cluster_limit(local[first]["medoid"]["a"]),action_cluster_limit(local[second]["medoid"]["a"]))*0.82
                        if action_geometry_distance(local[first]["medoid"]["a"],local[second]["medoid"]["a"])<=limit:
                            local[first]["members"].extend(local[second]["members"])
                            local[first]["medoid"]=self._action_medoid(local[first]["members"])
                            local.pop(second)
                            changed=True
                            break
            for index,cluster in enumerate(local):
                action=normalize_action(cluster["medoid"]["a"])
                canonical=action_signature(action)
                token=hashlib.sha256(canonical_bytes({"family":family,"action":action,"index":index})).hexdigest()[:20]
                cluster_id="action|"+family+"|"+token
                intervals=[]
                learned_policies=[]
                for member in cluster["members"]:
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
                break
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
        for cluster in clusters:
            medoid=self._prototype_medoid(cluster)
            distances=[feature_distance(item["f"],medoid["f"]) for item in cluster]
            mean=statistics.fmean(distances) if distances else 0.0
            std=statistics.pstdev(distances) if len(distances)>1 else 0.0
            limit95=quantile(distances,0.95)
            limit99=quantile(distances,0.99)
            threshold_value=max(1.0,min(1800.0,max(limit99,mean+2.58*std)+max(8.0,std*0.35)))
            previous=Counter(str(item.get("context",{}).get("previous_action","")) for item in cluster)
            previous.pop("",None)
            prev=previous.most_common(1)[0][0] if previous else ""
            result.append({"id":uuid.uuid4().hex,"cluster_id":cluster_id,"canonical_action_signature":canonical,"f":feature_bytes(medoid["f"]),"coarse":coarse_feature(medoid["f"]),"a":normalize_action(action),"support":len(cluster),"action_support":int(action_support),"mean_distance":round(mean,6),"std_distance":round(std,6),"limit95":round(limit95,6),"limit99":round(limit99,6),"intra_threshold":round(threshold_value,6),"threshold":round(threshold_value,6),"previous_action":prev,"repeat_policy":repeat_policy if repeat_policy in REPEAT_POLICIES else "one_shot","max_rate":max(0.25,min(12.0,float(max_rate))),"ambiguous":False,"created_from_sample_checksum":medoid.get("checksum","")})
        return result
    def rank_action_candidates(self,feature,prototypes,last_action_signature="",full_limit=16):
        if not feature_valid(feature):
            return []
        query_coarse=coarse_feature(feature)
        coarse_rank=[]
        best_per_cluster={}
        for proto in prototypes:
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
            cluster_id=str(proto.get("cluster_id",proto.get("action_signature","")))
            if cluster_id:
                grouped[cluster_id].append((raw+penalty,raw,proto))
        result=[]
        for cluster_id,items in grouped.items():
            items.sort(key=lambda item:item[0])
            best_score,best_distance,best_proto=items[0]
            vote_score=best_score if len(items)==1 else 0.88*best_score+0.12*items[1][0]
            action=normalize_action(best_proto["a"])
            result.append({"cluster_id":cluster_id,"canonical_action_signature":str(best_proto.get("canonical_action_signature") or action_signature(action)),"score":vote_score,"best_score":best_score,"distance":best_distance,"proto":best_proto,"a":action,"support":max(int(item[2].get("action_support",item[2].get("support",0))) for item in items),"prototype_votes":len(items)})
        result.sort(key=lambda item:item["score"])
        return result
    def evaluate_action_candidates(self,ranked):
        if not ranked:
            return {"accepted":False,"confidence":0.0,"reason":"没有候选"}
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
        ambiguous=bool(proto.get("ambiguous",False))
        accepted=not ambiguous and best["distance"]<threshold and margin_ok and support>=min_support and rejection_ok
        confidence=max(0.0,min(1.0,1.0-best["distance"]/max(1.0,threshold)))
        reason="视觉状态存在不同动作歧义，必须请教" if ambiguous else "未达到动作阈值、差距或支持数要求"
        return {"accepted":accepted,"best":best,"second":second,"threshold":threshold,"margin":margin,"required_gap":required_gap,"support":support,"min_support":min_support,"confidence":confidence,"margin_ok":margin_ok,"rejection_ok":rejection_ok,"ambiguous":ambiguous,"reason":reason,"nearest_rejected_distance":rejected_distance}
    def start_review(self):
        self.start_worker("复习",self.review_worker,False)
    def _limit_prototypes(self,prototypes,limit):
        if len(prototypes)<=int(limit):
            return list(prototypes)
        groups=defaultdict(list)
        for proto in prototypes:
            groups[str(proto.get("cluster_id",""))].append(proto)
        chosen=[]
        remaining=[]
        for cluster_id,items in groups.items():
            ordered=sorted(items,key=lambda item:(int(item.get("support",0)),int(item.get("action_support",0))),reverse=True)
            chosen.append(ordered[0])
            remaining.extend(ordered[1:])
        if len(chosen)>int(limit):
            return chosen
        remaining.sort(key=lambda item:(int(item.get("support",0)),int(item.get("action_support",0))),reverse=True)
        chosen.extend(remaining[:int(limit)-len(chosen)])
        return chosen
    def review_worker(self):
        game=self.require_game()
        samples,stats=self.store.load_samples(game["id"])
        valid=[]
        for sample in samples:
            action=normalize_action(sample.get("a"))
            if feature_valid(sample.get("f")) and action:
                item=dict(sample)
                item["a"]=action
                valid.append(item)
        if not valid:
            raise RuntimeError("没有可复习的有效学习数据，请先进行学习")
        self.wait_escape_release()
        action_clusters=self._cluster_action_samples(valid)
        if self.should_stop():
            return "复习已中断：尚未保存不完整的动作聚类，旧完整模型未被覆盖"
        session_groups=defaultdict(list)
        for item in valid:
            session_groups[str(item.get("session_id") or item.get("context",{}).get("session_id") or "legacy")].append(item)
        sessions=sorted(session_groups,key=lambda key:hashlib.sha256(key.encode("utf-8","replace")).hexdigest())
        holdout_sessions=set()
        target=max(20,round(len(valid)*0.22))
        selected_count=0
        if len(sessions)>1:
            for session in sessions:
                if len(valid)-selected_count-len(session_groups[session])<1:
                    continue
                holdout_sessions.add(session)
                selected_count+=len(session_groups[session])
                if selected_count>=target:
                    break
        train=[item for item in valid if str(item.get("session_id") or item.get("context",{}).get("session_id") or "legacy") not in holdout_sessions]
        holdout=[item for item in valid if item not in train]
        groups=defaultdict(list)
        cluster_map={cluster["id"]:cluster for cluster in action_clusters}
        for sample in train:
            groups[sample["_action_cluster"]].append(sample)
        ordered=sorted(groups.items(),key=lambda item:(normalize_action(cluster_map[item[0]]["a"])["kind"]=="no_op",-len(item[1])))
        prototypes=[]
        processed=0
        stopped=False
        for cluster_id,items in ordered:
            if self.should_stop():
                stopped=True
                break
            cluster=cluster_map[cluster_id]
            def progress(local,total_local,count):
                self.set_progress(82*(processed+local)/max(1,len(train)))
                self.set_status("复习中：按动作几何聚类和窗口自适应视觉阈值生成原型；"+str(processed+local)+"/"+str(len(train)))
            prototypes.extend(self._cluster_action_group(cluster_id,cluster["a"],len(cluster["members"]),items,progress,cluster.get("repeat_policy","one_shot"),cluster.get("max_rate",3.0)))
            processed+=len(items)
            prototypes=self._limit_prototypes(prototypes,MAX_PROTOTYPES)
        for index,proto in enumerate(prototypes):
            conflicting=[other for other in prototypes if other["id"]!=proto["id"] and other.get("cluster_id")!=proto.get("cluster_id")]
            nearest=float("inf")
            if conflicting:
                rough=sorted((coarse_distance(proto["coarse"],other["coarse"]),other) for other in conflicting)[:20]
                nearest=min(feature_distance(proto["f"],other["f"]) for _,other in rough)
            proto["nearest_conflicting_distance"]=None if math.isinf(nearest) else round(nearest,6)
            intra=float(proto.get("intra_threshold",proto["threshold"]))
            ambiguity_limit=max(1e-6,intra*0.05)
            proto["ambiguous"]=not math.isinf(nearest) and nearest<=ambiguity_limit
            proto["threshold"]=round(max(0.001,intra if math.isinf(nearest) else min(intra,max(0.001,nearest*0.62))),6)
            proto["minimum_second_candidate_gap"]=round(max(8.0,float(proto["threshold"])*0.12,0.0 if math.isinf(nearest) else nearest*0.08),6)
            if index%12==0:
                self.set_progress(82+6*(index+1)/max(1,len(prototypes)))
        rejections=self.store.load_rejections(game["id"],500)
        rejection_constraints=0
        for proto in prototypes:
            matching=[]
            for rejection in rejections:
                candidate_actions=[normalize_action(item.get("a")) for item in rejection.get("candidates",[]) if isinstance(item,dict)]
                if any(action and action_family_key(action)==action_family_key(proto["a"]) and action_geometry_distance(action,proto["a"])<=action_cluster_limit(proto["a"])*1.25 for action in candidate_actions):
                    matching.append((coarse_distance(proto["coarse"],coarse_feature(rejection["f"])),rejection))
            if matching:
                nearest_rejected=min(feature_distance(proto["f"],rejection["f"]) for _,rejection in sorted(matching,key=lambda item:item[0])[:8])
                proto["nearest_rejected_distance"]=round(nearest_rejected,6)
                proto["threshold"]=round(max(0.001,min(float(proto["threshold"]),nearest_rejected*0.78)),6)
                rejection_constraints+=1
            else:
                proto["nearest_rejected_distance"]=None
        if stopped:
            if prototypes:
                self.store.save_model(game["id"],{"created":time.time(),"samples":len(valid),"training_samples":len(train),"invalid_samples":stats["invalid"],"rejection_constraints":rejection_constraints,"prototypes":prototypes,"validation":{"status":"stopped","holdout":0,"accepted":0,"coverage":0.0,"accepted_error_rate":None,"overall_accuracy":0.0,"reject_rate":1.0},"stopped":True},False)
            return "复习已中断：旧完整模型未被覆盖，部分结果仅保存为临时模型"
        errors=accepted=correct=0
        by_action=defaultdict(lambda:{"total":0,"accepted":0,"correct":0,"errors":0,"unrecognized":0})
        by_method=defaultdict(lambda:{"total":0,"accepted":0,"correct":0})
        dangerous_false=0
        for index,sample in enumerate(holdout):
            ranked=self.rank_action_candidates(sample["f"],prototypes,str(sample.get("context",{}).get("previous_action","")),16)
            decision=self.evaluate_action_candidates(ranked)
            expected=sample["_action_cluster"]
            canonical=sample.get("_canonical_action_signature",action_signature(sample["a"]))
            method=str(sample.get("capture_method") or sample.get("context",{}).get("capture_method") or "unknown")
            arow=by_action[canonical]; mrow=by_method[method]
            arow["total"]+=1; mrow["total"]+=1
            if decision.get("accepted"):
                accepted+=1; arow["accepted"]+=1; mrow["accepted"]+=1
                predicted=decision["best"]
                if predicted["cluster_id"]==expected:
                    correct+=1; arow["correct"]+=1; mrow["correct"]+=1
                else:
                    errors+=1; arow["errors"]+=1
                    action=normalize_action(predicted["a"])
                    if action["kind"] in {"double_click","long_press","drag"} or action.get("button") in {"right","middle"}:
                        dangerous_false+=1
            else:
                arow["unrecognized"]+=1
            if index%5==0:
                self.set_progress(88+10*(index+1)/max(1,len(holdout)))
        holdout_count=len(holdout)
        coverage=accepted/holdout_count if holdout_count else 0.0
        accepted_error_rate=errors/accepted if accepted else None
        overall_accuracy=correct/holdout_count if holdout_count else 0.0
        reject_rate=1.0-coverage if holdout_count else 1.0
        dangerous_false_rate=dangerous_false/max(1,holdout_count)
        per_action={key:{**value,"recall":value["correct"]/value["total"] if value["total"] else 0.0,"error_rate":value["errors"]/value["total"] if value["total"] else 0.0,"unrecognized_rate":value["unrecognized"]/value["total"] if value["total"] else 0.0} for key,value in by_action.items()}
        per_method={key:{**value,"accuracy":value["correct"]/value["total"] if value["total"] else 0.0,"coverage":value["accepted"]/value["total"] if value["total"] else 0.0} for key,value in by_method.items()}
        if holdout_count<20 or accepted==0 or coverage<0.55:
            validation_status="insufficient"
        elif (accepted_error_rate is not None and accepted_error_rate>0.12) or overall_accuracy<0.45 or dangerous_false_rate>0.03:
            validation_status="failed"
        else:
            validation_status="passed"
        validation={"status":validation_status,"split":"session_id","holdout_sessions":len(holdout_sessions),"minimum_holdout":20,"minimum_coverage":0.55,"maximum_accepted_error_rate":0.12,"minimum_overall_accuracy":0.45,"maximum_dangerous_false_rate":0.03,"holdout":holdout_count,"accepted":accepted,"errors":errors,"correct":correct,"coverage":coverage,"accepted_error_rate":accepted_error_rate,"overall_accuracy":overall_accuracy,"reject_rate":reject_rate,"dangerous_false_rate":dangerous_false_rate,"per_action":per_action,"per_capture_method":per_method,"ambiguous_prototypes":sum(1 for proto in prototypes if proto.get("ambiguous"))}
        model={"created":time.time(),"samples":len(valid),"training_samples":len(train),"invalid_samples":stats["invalid"],"action_clusters":len(action_clusters),"rejection_constraints":rejection_constraints,"prototypes":prototypes,"validation":validation,"stopped":False}
        if not prototypes:
            raise RuntimeError("复习未生成可用原型")
        self.store.save_model(game["id"],model,validation_status=="passed")
        self.set_progress(100)
        label="通过验收" if validation_status=="passed" else ("验证不足" if validation_status=="insufficient" else "验证未通过")
        error_text="无可计算值" if accepted_error_rate is None else str(round(accepted_error_rate*100,2))+"%"
        lines=["复习完成，"+label+"：原型"+str(len(prototypes))+"，歧义原型"+str(validation["ambiguous_prototypes"])+"，按会话留出"+str(holdout_count)+"，覆盖率"+str(round(coverage*100,2))+"%，接受错误率"+error_text+"，总体正确率"+str(round(overall_accuracy*100,2))+"%，危险动作误触率"+str(round(dangerous_false_rate*100,2))+"%","各动作验证："]
        for signature,row in sorted(per_action.items()):
            lines.append(signature+"：样本"+str(row["total"])+"，召回率"+str(round(row["recall"]*100,2))+"%，错误率"+str(round(row["error_rate"]*100,2))+"%，未识别率"+str(round(row["unrecognized_rate"]*100,2))+"%")
        lines.append("各采集方式验证：")
        for method,row in sorted(per_method.items()):
            lines.append(method+"：样本"+str(row["total"])+"，准确率"+str(round(row["accuracy"]*100,2))+"%，覆盖率"+str(round(row["coverage"]*100,2))+"%")
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
        def geometry():
            rect=self.api.validate_target(target,True)
            dpi=self.api.dpi_for_window(int(target["hwnd"]))
            if len(expected_rect)==4 and (max(abs(int(rect[i])-int(expected_rect[i])) for i in range(4))>2 or expected_dpi and abs(dpi-expected_dpi)>1):
                raise TargetUnavailable("窗口客户区几何或DPI已变化，放弃当前动作并重新识别")
            return rect
        kind=item["kind"]
        if kind=="no_op":
            end=time.time()+item.get("duration",0.35)
            while time.time()<end and not self.should_stop():
                geometry()
                time.sleep(0.02)
            return
        path=item.get("path") or [[0.5,0.5]]*16
        def move_to(point):
            rect=geometry()
            x,y=self.point_to_screen(point,rect)
            if not self.inside(x,y,rect):
                raise TargetUnavailable("动作坐标超出客户区")
            self.api.move_cursor(x,y)
            geometry()
        move_to(path[0])
        if self.should_stop():
            return
        if kind=="move":
            for point in path[1:]:
                if self.should_stop():
                    return
                move_to(point)
                time.sleep(max(0.004,item["duration"]/max(1,len(path)-1)))
            return
        if kind=="hover":
            end=time.time()+item["duration"]
            while time.time()<end and not self.should_stop():
                geometry()
                time.sleep(0.02)
            return
        if kind in {"scroll_v","scroll_h"}:
            geometry()
            self.api.wheel(item["delta"],kind=="scroll_h")
            geometry()
            return
        button=item["button"]
        if kind=="double_click":
            for iteration in range(2):
                geometry(); self.api.button(button,True); time.sleep(0.045); geometry(); self.api.button(button,False)
                if iteration==0:
                    time.sleep(0.09)
            return
        geometry(); self.api.button(button,True)
        try:
            if kind=="drag":
                step_time=item["duration"]/max(1,len(path)-1)
                for point in path[1:]:
                    if self.should_stop():
                        break
                    move_to(point)
                    end=time.time()+step_time
                    while time.time()<end and not self.should_stop():
                        geometry(); time.sleep(min(0.012,max(0.002,end-time.time())))
            else:
                hold=item["duration"] if kind=="long_press" else min(0.13,item["duration"])
                end=time.time()+hold
                while time.time()<end and not self.should_stop():
                    geometry(); time.sleep(0.01)
        finally:
            try:
                self.api.button(button,False)
            except Exception:
                self.api.release_all_buttons()
    def start_training(self):
        try:
            game=self.require_game()
            self.require_window(False)
            model=self.store.load_model(game["id"])
            if not model or not model.get("prototypes"):
                raise RuntimeError("没有可用完整模型，请先学习并完成复习")
            if str(model.get("validation",{}).get("status",""))!="passed":
                raise RuntimeError("完整模型未通过留出数量、覆盖率、错误率和总体正确率验收，请重新复习")
            current=next((item for item in self.store.games() if item["id"]==game["id"]),{})
            if current.get("needs_review"):
                raise RuntimeError("模型需要复习：请先点击“复习”完成离线优化")
        except Exception as error:
            self.show_error(str(error))
            return
        self.start_worker("训练",self.training_worker,True)
    def training_worker(self):
        game=self.require_game()
        target=self.require_window(False)
        model=self.store.load_model(game["id"])
        prototypes=model["prototypes"]
        calibration=self.api.calibration_for(target)
        self.api.request_foreground(target["hwnd"])
        self.wait_escape_release()
        frame_buffer=FrameBuffer(self.api,target,max(8.0,float(calibration.get("fps",15.0))),2.5,0.1).start()
        actions=0
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
        action_hits=defaultdict(deque)
        try:
            while not self.should_stop():
                try:
                    self.api.validate_target(target,True)
                except TargetUnavailable as error:
                    self.api.release_all_buttons(); candidate_id=None; candidate_count=0
                    self.set_confidence("训练置信度：0%")
                    self.set_status("目标窗口失去焦点，等待恢复；已释放全部鼠标键；"+str(error))
                    time.sleep(0.08); continue
                captured=frame_buffer.latest(None,0.8)
                if captured is None:
                    self.api.release_all_buttons(); self.set_status("等待固定间隔画面缓冲；"+(frame_buffer.last_error or "尚无有效帧")); time.sleep(0.08); continue
                feature=captured["f"]
                frame_change=float("inf")
                if captured["time"]!=previous_frame_stamp:
                    if previous_feature is not None:
                        frame_change=visual_distance(previous_feature,feature)
                        frozen_count=frozen_count+1 if frame_change<float(calibration.get("freeze_change",1.5)) else 0
                    previous_feature=feature; previous_frame_stamp=captured["time"]
                if frozen_count>=int(calibration.get("freeze_frames",30)):
                    self.set_status("画面长时间未变化；保留合法静止画面但暂停自动输入，等待变化或请教")
                    self.api.release_all_buttons(); time.sleep(0.1); continue
                significant=last_action_feature is not None and visual_distance(last_action_feature,feature)>float(calibration.get("significant_change",60.0))
                if significant:
                    state_unlocked=True; no_change_count=0
                ranked=self.rank_action_candidates(feature,prototypes,last_action_signature,18)
                decision=self.evaluate_action_candidates(ranked)
                if not decision.get("accepted"):
                    candidate_id=None; candidate_count=0
                    self.set_confidence("训练置信度："+str(round(float(decision.get("confidence",0.0))*100,1))+"%")
                    self.set_status("训练中："+str(decision.get("reason","识别不确定"))+"；不执行动作并优先等待请教")
                    time.sleep(0.12); continue
                best=decision["best"]
                cluster_id=best["cluster_id"]
                if candidate_id==cluster_id:
                    if captured["time"]==candidate_frame_stamp:
                        time.sleep(0.025); continue
                    candidate_count+=1
                else:
                    candidate_id=cluster_id; candidate_count=1
                candidate_frame_stamp=captured["time"]
                confirmations=max(1,int(calibration.get("confirm_frames",2)))
                self.set_confidence("训练置信度："+str(round(decision["confidence"]*100,1))+"%  连续确认"+str(candidate_count)+"/"+str(confirmations))
                if candidate_count<confirmations:
                    time.sleep(0.05); continue
                action=normalize_action(best["a"])
                canonical=action_signature(action)
                proto=best["proto"]
                policy=str(proto.get("repeat_policy","one_shot"))
                max_rate=max(0.25,min(12.0,float(proto.get("max_rate",3.0))))
                if policy in {"one_shot","hold_until_change"} and last_cluster_id==cluster_id and not state_unlocked:
                    self.set_status("等待画面变化：该动作策略为"+policy)
                    time.sleep(0.1); continue
                minimum_gap=max(self.action_cooldown(action) if policy=="one_shot" else 0.0,1.0/max_rate if policy in {"rate_limited","repeatable"} else 0.0)
                if time.time()-last_action_time<minimum_gap:
                    time.sleep(0.03); continue
                now=time.time(); hits=action_hits[cluster_id]
                while hits and now-hits[0]>1.0:
                    hits.popleft()
                if len(hits)>=max(1,int(math.ceil(max_rate))):
                    self.set_status("动作专属频率限制中："+self.action_text(action)); time.sleep(0.05); continue
                before=feature
                self.set_status("训练中："+self.action_text(action)+"；策略="+policy+"；采集="+captured["method"])
                try:
                    self.execute_action(target,action,captured)
                except TargetUnavailable as error:
                    self.api.release_all_buttons(); candidate_id=None; candidate_count=0
                    self.set_status(str(error)); continue
                action_end=time.time()
                actions+=1; hits.append(action_end)
                last_action_signature=canonical
                last_cluster_id=cluster_id
                last_action_time=action_end
                last_action_feature=before
                state_unlocked=policy in {"repeatable","rate_limited"}
                candidate_count=0
                delay=float(calibration.get("input_delay",0.24))
                end=time.time()+delay
                while time.time()<end and not self.should_stop():
                    time.sleep(0.02)
                after=None
                wait_end=time.time()+max(0.35,delay*2.0)
                while time.time()<wait_end and not self.should_stop():
                    after=frame_buffer.latest_after(action_end)
                    if after is not None:
                        break
                    time.sleep(0.025)
                change=visual_distance(before,after["f"]) if after is not None else 0.0
                if change<float(calibration.get("post_action_change",45.0)):
                    no_change_count+=1
                    if policy in {"one_shot","hold_until_change"} and no_change_count>=3:
                        self.set_status("动作后画面变化不足，暂停该一次性动作并等待请教")
                else:
                    no_change_count=0; state_unlocked=True
                time.sleep(0.05)
        finally:
            frame_buffer.stop()
            self.api.release_all_buttons()
        return "训练已结束，AI执行"+str(actions)+"个鼠标动作；窗口几何和DPI在每次动作前均已复核"
    def basic_actions(self):
        result=[]
        for y in (0.18,0.35,0.5,0.68,0.84):
            for x in (0.16,0.32,0.5,0.68,0.84):
                result.append(normalize_action({"kind":"click","button":"left","path":[[x,y]],"duration":0.08}))
        result.extend([normalize_action({"kind":"double_click","button":"left","path":[[0.5,0.5]],"duration":0.16}),normalize_action({"kind":"drag","button":"left","path":[[0.25,0.5],[0.75,0.5]],"duration":0.45}),normalize_action({"kind":"drag","button":"left","path":[[0.5,0.75],[0.5,0.25]],"duration":0.45}),normalize_action({"kind":"no_op","duration":0.4}),normalize_action({"kind":"scroll_v","delta":120,"path":[[0.5,0.5]],"duration":0.08}),normalize_action({"kind":"scroll_v","delta":-120,"path":[[0.5,0.5]],"duration":0.08})])
        return result
    def start_ask(self):
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
        choice_frame=ttk.Frame(frame)
        choice_frame.pack(fill="both",expand=True,pady=(10,0))
        answer_buttons=[]
        count={"saved":0,"duplicates":0,"skipped":0,"rejected":0}
        self.ask_counts=count
        state={"frame":None,"choices":[],"image":None,"locked":False,"candidates":[]}
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
        def render(gray):
            image=tk.PhotoImage(width=FEATURE_W,height=FEATURE_H)
            source=gray_bytes(gray) or bytes(PIXELS)
            rows=[]
            for y in range(FEATURE_H):
                row=[]
                for x in range(FEATURE_W):
                    value=source[y*FEATURE_W+x]
                    row.append("#%02x%02x%02x"%(value,value,value))
                rows.append("{"+" ".join(row)+"}")
            image.put(" ".join(rows))
            scaled=image.zoom(10,10)
            state["image"]=(image,scaled)
            canvas.delete("all")
            canvas.create_image(336,189,image=scaled)
        def select_question_frame():
            frames=self.ask_buffer.snapshot(1.8) if self.ask_buffer is not None else []
            if not frames:
                return None,[]
            if not prototypes:
                return frames[-1],[]
            selected=frames[-1]
            selected_ranked=self.rank_action_candidates(selected["f"],prototypes,"",18)
            selected_priority=float("inf")
            for candidate_frame in frames[-28:]:
                ranked=self.rank_action_candidates(candidate_frame["f"],prototypes,"",18)
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
                self.status.set("请教等待目标窗口恢复或等待后台采集画面："+str(error))
                schedule(180,new_question)
                return
            question_frame,ranked=select_question_frame()
            if question_frame is None:
                self.status.set("请教等待目标窗口恢复或等待后台采集画面："+(self.ask_buffer.last_error if self.ask_buffer is not None else "尚无画面"))
                schedule(160,new_question)
                return
            choices,candidates=make_choices(question_frame,ranked)
            state["frame"]=question_frame
            state["choices"]=choices
            state["candidates"]=candidates
            render(question_frame["gray"])
            for index,button in enumerate(answer_buttons):
                if index<len(choices):
                    button.configure(text=chr(65+index)+". "+self.action_text(choices[index]["a"]))
                else:
                    button.configure(text=chr(65+index)+". 无可用答案")
            set_locked(False)
        def context_for(entry=None):
            question_frame=state["frame"] or {}
            policy=str((entry or {}).get("repeat_policy","one_shot"))
            return self.sample_context("",0,True,question_frame.get("motion_valid",False),self.ask_session_id,question_frame.get("method","unknown"),policy)
        def finish_answer():
            self.status.set("请教中：已保存"+str(count["saved"])+"，重复未保存"+str(count["duplicates"])+"，跳过"+str(count["skipped"])+"，拒绝记录"+str(count["rejected"])+"；模型需要复习")
            schedule(140,new_question)
        def choose(index):
            if self.ask_window is None or state["locked"] or index>=len(state["choices"]):
                return
            set_locked(True)
            entry=state["choices"][index]
            question_frame=state["frame"]
            saved=self.store.append_sample(game["id"],question_frame["f"],entry["a"],"teach_live",context_for(entry),question_frame.get("gray"),3.0)
            count["saved" if saved else "duplicates"]+=1
            finish_answer()
        def skip():
            if state["locked"]:
                return
            set_locked(True); count["skipped"]+=1; finish_answer()
        def reject():
            if state["locked"]:
                return
            set_locked(True)
            question_frame=state["frame"]
            self.store.append_rejection(game["id"],question_frame["f"],state["candidates"],"teach_live_reject",question_frame.get("gray"),context_for())
            count["rejected"]+=1
            finish_answer()
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
                    saved=self.store.append_sample(game["id"],question_frame["f"],action,"teach_live_custom",context_for(entry),question_frame.get("gray"),3.5)
                    count["saved" if saved else "duplicates"]+=1
                    dialog.destroy(); finish_answer()
                except Exception as error:
                    error_var.set(str(error))
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
            self.ask_buffer.stop(wait_buffer)
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
        self.status.set("正在安全关闭：等待工作线程释放资源")
        self.api.release_all_buttons()
        if self.stop_event:
            self.stop_event.set()
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
        self.api.release_all_buttons()
        mode_alive=bool(self.mode_thread and self.mode_thread.is_alive())
        ask_alive=bool(self.ask_buffer and self.ask_buffer.alive())
        if mode_alive or ask_alive:
            try:
                self.root.after(50,self._poll_shutdown)
            except Exception:
                pass
            return
        self.shutdown_started=True
        try:
            self.api.wgc.close()
        except Exception:
            pass
        try:
            self.store.close()
        except Exception:
            pass
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
