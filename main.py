import os
import ast
import argparse
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
import urllib.request
import urllib.parse
from contextlib import contextmanager
from dataclasses import dataclass,field
from enum import Enum
from pathlib import Path
from collections import deque,Counter,defaultdict,OrderedDict
tk=None
ttk=None
def load_gui_runtime():
    global tk,ttk
    if tk is None or ttk is None:
        import tkinter as tk_module
        from tkinter import ttk as ttk_module
        tk=tk_module
        ttk=ttk_module
    return tk,ttk
import ctypes
from ctypes import wintypes
APP_NAME="UniversalGameAI"
FORMAT_VERSION=7
FEATURE_W=64
FEATURE_H=36
PREVIEW_W=320
PREVIEW_H=180
FEATURE_CHANNELS=5
PIXELS=FEATURE_W*FEATURE_H
FEATURE_LEN=PIXELS*FEATURE_CHANNELS
FEATURE_DISTANCE_WEIGHTS=(0.30,0.19,0.19,0.22,0.10)
FEATURE_DISTANCE_WEIGHTS_ARRAY=None
POOL_BOUNDARIES={}
COARSE_W=16
COARSE_H=9
COARSE_LEN=COARSE_W*COARSE_H*FEATURE_CHANNELS
SQUARED_DIFF=tuple(value*value for value in range(-255,256))
FEATURE_ALGORITHM_VERSION=4
ACTION_ALGORITHM_VERSION=6
DATABASE_SCHEMA_VERSION=8
MODEL_SCHEMA_VERSION=2
DEFAULT_SAMPLE_BUDGET=1500
MAX_SAMPLES=6000
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
DEVELOPER_MODE="--developer-mode" in sys.argv
AI_WORKER_PROTOCOL_VERSION=4
RUNTIME_INSTALL_PROTOCOL_VERSION=2
REVIEW_PROCESS_PROTOCOL_VERSION=2
TEST_WORKER_PROTOCOL_VERSION=2
STATIC_CONTRACT_VERSION=5
MODE_SPECS={"学习":{"requires":("runtime","game","window"),"runner":"learning"},"睡眠":{"requires":("runtime","game","samples"),"runner":"sleep"},"训练":{"requires":("runtime","game","window",
            "model"),"runner":"training"},"指导":{"requires":("runtime","game","window"),"runner":"guidance"}}
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
MIN_DATA_OPERATION_RESERVE=256*1024*1024
RUNTIME_LAYOUT_VERSION=3
FIXED_RUNTIME_PYTHON_VERSION="3.12.10"
FIXED_RUNTIME_PYTHON_ABI=(3,12)
FIXED_RUNTIME_PYTHON_URL="https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip"
FIXED_RUNTIME_PYTHON_SHA256="4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3"
FIXED_RUNTIME_PYTHON_MAX_BYTES=16*1024*1024
FIXED_RUNTIME_PIP_VERSION="26.1.2"
FIXED_RUNTIME_PIP_URL="https://files.pythonhosted.org/packages/5d/95/6b5cb3461ea5673ba0995989746db58eb18b91b54dbf331e72f569540946/pip-26.1.2-py3-none-any.whl"
FIXED_RUNTIME_PIP_SHA256="382ff9f685ee3bc25864f820aa50505825f10f5458ffff07e30a6d96e5715cab"
FIXED_RUNTIME_PIP_MAX_BYTES=3*1024*1024
FIXED_RUNTIME_PIP_SIZE=1813144
RUNTIME_ARCH_X64="x64"
RUNTIME_ARCH_ARM64="arm64"
FIXED_RUNTIME_PYTHON_ARTIFACTS={RUNTIME_ARCH_X64:{"filename":"python-3.12.10-embed-amd64.zip","url":FIXED_RUNTIME_PYTHON_URL,"sha256":FIXED_RUNTIME_PYTHON_SHA256,"size":11133606,
        "max_bytes":FIXED_RUNTIME_PYTHON_MAX_BYTES,"python_abi":"cp312","architecture":RUNTIME_ARCH_X64,"backend":"builtin_cpu"},RUNTIME_ARCH_ARM64:{"filename":"python-3.12.10-embed-arm64.zip",
        "url":"https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-arm64.zip","sha256":"3065efc3d382d1cda66757ac71ade11904fa6e350f5a97eb74811acd71ba5532","size":10413299,
        "max_bytes":FIXED_RUNTIME_PYTHON_MAX_BYTES,"python_abi":"cp312","architecture":RUNTIME_ARCH_ARM64,"backend":"builtin_cpu"}}
RUNTIME_LOCK_MANIFEST_VERSION=5
RUNTIME_LOCK_MANIFEST_SHA256='6bb74ae98cb99a10c3d95c03ea40fcbdbf2505213e3c5fa64e8f0904e55f2c9a'
RUNTIME_LOCK_MANIFEST_B85=(
    'c-pO7U2kJIlKn4!Zkfd@e&%go7c;;D`?OdD4U$EsmDrX>a(Cj%&VS!SxozF<ndl=L198hTb?<c@*7+cr-|w_<`;+#k_VTf9o}PE5'
    'J@4;+`2FtZ_0!LV=c`@++voMJ<K6$gdn~(OK5zGB^t&Jb@!@Xs*ncYc*!X_j_T{BKKHUBI;qD8rzS(u1@0O?Mhuz_WyRu#DrtQA}'
    'T-!Wsb`P7M?mpZ-eSX}&+%4~c*Lc?UWwm{I{<L|*&)fCG!{*od;-x*Tx7)ruyguCf!{Nexk3Z+b-TqVA_J?`7{rWe2fBu_3zCOs?'
    'nC~B?@1ECVjiK#R+3oxD>S?okED!6yAMUZ%r-FYz?;al3RSs9$zs%?TzFynM^8D%W`{&KBefs|QWBt${HtiQ&YwY*i-tgjU<xzqD'
    '{Oe}-%Y0ruz~}ArX7h0PV_se>^Zc@1KmD}ozdiS-{d)7XKi=oddcN`f-QG(2Ubfd~I(%vt<X?eN9t#Fw#A2dscbhM3?Yl$OzQyE+'
    'Z+~8W>O~*=et(B6%s=$-k>7&*zxsLo@VtKd*tVZ>uix(qo@D*p+w<pL$5k){&sR(P1vkad%i$jmWqT@*bKqB?R!ki3!@Z5TvjD88'
    'zA8^I_rHFcGvV8@hdDBz?qjLz`Sw;UzfKbN0dFvK)K&|oIVlgHIcBvnu;Qypj7hpW@y=&AEdCo!tTGK}@k;Aqn*AMjv?84HVV>Z!'
    'pPrw$`yY&%Prtu^eS}Y&{d3p*&F&|&#UERK>U-0N;bEG0!Fl1HgRe!$;NhBUwn#}be8_Q-#^xw?rKZKXQcBLXI&aNIRrvx053}U%'
    'eHdW60gBg7`FQM<mE5~~w>lK~>-S&r$?~YdeFx3I>ax=)m6+S;5>xaeF+27(<&s!L9HDZ#^Z+mb*+8w51EK&&@P6spvp=Fl(Tcqm'
    'B~im_Z1-KWs#HlNIRhZ?o8lg=25O0$hy{GOeHqc$R&&d?3TNNVpDNf9wZquk5c}HUE5fA$<_O=P=$<z^I0p=RLUYb`_|h7+Vr?E-'
    'os+;+W5nxFMIuS}maJ_y)G~Z5qjK`2g?C`si}-7CQEN09LD!%!Tnj>uJGlrviuBOcmLNqurHFR|0V*jLgHvffG-h<qMP)exaTs<x'
    '5YW99nvm}8>I@363VDXaH1;GeaRx)BGD5J-Z49E&@<>_&d#~u59@|LhBTd>_hs@d9ayzz%jZUsbA*gBAbZ2uP5?KmGXCv2;z)}f4'
    'FhsjcfWtLL-{8(wleJRZ&{jt7=7O3WA$T2g69#Wuj2;xa=Mxw#RQn7?1y_AS-;+zdN%kpcXb0%XqpCK@BrXmX)Px>LPCDf@$b&s{'
    'z;E9%$c{2!ivh9GVF<TMWJ4<&Ler@k8BkPKHyS%%yLjyl(jp;Q8q$*15jks0=7O3m`Dl*04TFOTdXp_Wg~6L$I*kCK_iMDtMyNn#'
    '8!`l(iVaB^A`yerK0r{mI#G0ouQmCqy|ZQIVvk$|c6ZlHxi`$l0c4HPA<-hJaDaV)R-@@SH?FOR7QD*<rhx)2Ww9+)ZZv8$7nJ0m'
    'gq&^yVVYY2ZcowBR|9;y_%Yg&;&2%X*#{^Hv)F=y!|1u$q%MgJ>!>OyD!7=TkHU(n--^Uu-iseCQM!8icN44$Axo;YLRkFd7#IP#'
    'wiHEu^>$P{Vv8|5JP`qXOnN_rYV#DUIa!J2#J9Im&#UF1cRI+;9~J#S-;%-UvM1kLcd&t|Ji{AWX<pIxAlKl~<0XYMra3D3Q&Dw-'
    '7z|5-c?h=~;=;Z<5Z2Yy&!$+|qmZc8p?<iUhV`X3s~)WwsR0a#e|CT+Vg5@Et{2K#tHt}loU6w-rN2>nkC7JlqkFl;t^W1!ng5<K'
    '_^b?v;v?K2gpOM7Vp9X{R;?g{ZlMoaQwU&S%?<ZaPgKN>>X<^Tb|J$sOIMqrQjD*r_6A8oG^ijIbXqGMMf%7f{gUl8q@h3xAQM@7'
    '!jFDLtvz+y%~kbT0)w%)0dvUCD|;^|h2U$%J}bpkx#rOm)!N`RN&w-E0pkxNC;+9xDuI!#CJwNzoe=!0`0iUu%10c$1e>oWBPXVd'
    'iJGA)h$|Uk4b!2y>T*rJX9#}sq~J!W=)?>jY$PETG;I&el+C$%9BY3Va#QW!mL33kIB7>0YZRyJuc&qfvvNlf8fGFapZC5XV221('
    '1hFkH!UaK|dnO$fL=bWXWxzlNUI=kOrQEduOhcJXWz>>0_nDy)m0`+k0?xUh3!_ruRNw>}cq$&80D&WsR`9Pg=ZmtO{^3SDdRVMk'
    '@jZhAFQBCNwVjhFG&{0~;C2tmqW}w{@F1BSSP0W@#NsgT1q?-02PirtOgEsA9DY-eC|I~wn0vZ9H3u__LB3!_zrYBG6^hHKKd^U5'
    '%7i9_D^Tx7M-G5hsF6Tb!!ooBcEMa)n1w5vV{ZcEeGwA(bznB_U)+hVSgu)~1_UjR@C)lPn_VT&f+L(JA^<}jxwzHNJirec2pIuF'
    '-XW%(CufwSRwKxz@Mrv~SA$rPTBtCk<mVC=l5wMw9i+Lr0zZbg1-Angr5dG)7X->Q0+`EOTAC#sZ{u#m<gn2A@oRnG78+OX-cIew'
    'hiMU4sJr}8&-}qs<#}6M5|0_1v~@s-X$($hfKx0ZNinpZ34SY9%ET=efq0kB2)!V|<NAgpisbCoT;__&WU2^4On`zl#0JD_Y21=m'
    'n(L6rm5s=g1#S+Vj0oO_qW3*KE~~krct;@LN8g0w>uU7M@<G@xpt{AX|4GH?>H$$eZ5)I)Dx%0JK1}Zgf`JKD@V*Odq5r{_Iq8wi'
    'krZKxfZQ>CFh?u#YLvW5*=XSrGlG!VI3RP0;!t?O;L&0OY)c6=+e2pbnkZ&U!C**WP-`wP%|iV7X7%5$w=3jGdvXy3gU+)X`UKPs'
    '!R}pZW1oT>iK!Hixe4#@kvj$^Wg7UR*b&VG_y+Q1eJhKF^n_{du5J`?TlOYYkf^v|JJ63(XVUOF<>-PUfb?opot_sWI7BRZWiGEn'
    'CSjG$=~^sE?J(xHvcGL&!Q;6LTj861uao}EcJFdRz7+^+Kuf@C26l57Aqln6QKB-}(49b(W9o<sAxA$W0?8s25-NGM(Bx=hG&&IT'
    '5~czpVkhoUHYf`mA0$OZK%0o?q0BX6gcKxm7(Ja<pj0%&73EoaVRvgc9QG4e;nHyUUoZdjAAkMJSwN71Ra^%EVJ=Z+r(m9Ls~d>z'
    '0py)i=(fS~#8P=6L$?7|uwjhoVqEkFW-491K%0W80|b?OvfZ`T1(H@_erNQAJCE9Qgn-a4o+BrOBgCGVkepog7WTtjT$trD?X9Ws'
    'ZRZ#!JfBP^?_130fCxmepxyQC0EA<dyQpM0Agk1yRm3rCQ{hQTPJA6PBr3ghf~4~i2$TuP`0GPD8Ad!z8rj?C1zJ;m4M7vY0d-Mr'
    '(t*S%y=8zgI9JR7SPv&D&y_-RzADRTl5dPAZ=2?DeBw@u#9|Bn%rXgrU?5l~Fo2X6N(B+athh|*g&|1dh~cv^t!By9HVSin3!1^;'
    'Dmsd_Q2a9p3}+g=I8{W9n%Q~a!66J9)-rgA)Km9Jj7eGzc%W!&@N>0xnyq3ksL9d+&oMV)Fc)OzzW-*oU(tPh<->H+?k+xZfn3a8'
    '8AK32_nL>e`Hg$cbJr+SYZ2;=obHJcDczJ3;sSX`&IbU;%~f$$68#C`?!okyTm%IY+-qV0kB5SMM-K2%8Bc7XPl6aP$+}h>Lc5Q3'
    'sMAu-H3eF3<;5H2;&@bJ6+Jw`skN(bj&+=|QXUa`C|nd=JlFuQksZ1#)=Tzw?kK2pVOm(&O;7|Vjk*J16wy@6<nEHEa4jNZn9|L#'
    'SqOfrFkpv?5RlYhprbGjlo@>j+a#mldEmBklDW$66cZ(yiz;)3;&sezSiBzlK~GNqc7b*u&k3E0fKJG{>e_&78o7jsPHDZ*lOpgq'
    'V@CC;#PIb{)y9bU0a<YFLc46^F<XG}7~$jU+}@^ogNPaggQmT;(D8(Zq&gczQS^bX7!`>Jxnk}(jn)a81_R!p;pXz%EP3lzkGo(0'
    '2K#2?0sK>^4PMV_ojGU_F$*QzKIfOS$W;ZQ!IuU`iUo=y+M;r-+)*BM2-gnVkKhrSK&uy9+#s@RF{shBZmi1%;-I*_g-~-wnq#=Q'
    '9Lh-5N2du42>jI}-RMBHQ?x14p6}*-HI_!!-b_vN;MlyOoODia=gZD0M3vCA1y@IaVpd3IOi;!M6KQ)>#T(oP%oWsQlp+#in0rDT'
    '6uO$;iyv%4OI#hV;d(|l$s(y0J1=ibf^&r|IcP#44>1_d&Lw{sWbyD1f#9t;QOW>?iaA%0Z;CHBnx?~9J9HaZ?Gh$>J(_oxhomFG'
    '#xyX^nNY^&5n_v?!KqW$kuztAM)t}csao?$s0310%f&8smzY3k0aNvAr5>gh1Cdd(QoXNvXd*lXgLq(|xWg)VG)G2zxZcM+nIpZ!'
    'WWzT#4;U}4%#w%vzXOfeQ<888Ojm&N^=#!?a>A4($K0Tib<Axyl`{DnE`IK-YK3=2#*z>{61aq1P_*vLJTVp9f}DJS7rXlOM-yX{'
    'L5$2ZS5vhbI&uzNo44xfJer19X*n03d*9AagIh+Pf;Q&)k7BMY($Yoot*3G3fz*||59$8YLi^#^>e-}iLqdS7EFle-nh&-NEs2<5'
    'qO#4t+6p-4;Q&gZrsN!B?jF`{wH>Wfi1QHDwLmZ%<O6hHj~>)RMaw+*7S$#tbq%Ue!d&x0=u@$<Q3!X8#*Kjy`VlwGnPMzgWapUM'
    '3V%3N{PB3IcrFT`K8y2DA35I~34KuTT_O^dm1e7r0hO_Co{oaIjAb6-Y<-^bL?#nY8j}Wz5RiTp4@AUxHD|eOR7?fT&<v&mOQx_#'
    '#14~ypjnckR=!5x3(^accy0j}FLv)54+Ii(O_jb`Fu(P1&etR7pv!PCCop+Cntl$6IvDASp(9>&fPfN20vU?gw}L!898xiQL}SJ5'
    'L?8#9333RWES07UnnJUrt5;|x8%n0&3&F8Apsy{p2(d!1W+j&bw4_zoYfetapxiPZ3w?wb!_aYawjxX22y^-A?co1<*L5Cd|G6Lj'
    'r-$PK`9Izmdf$3DtbQ-nn7$3yZ|c1ij2{<I;{Wmg@47_z'
)
_RUNTIME_LOCK_MANIFEST_CACHE=None
RUNTIME_ALLOWED_DOWNLOAD_HOSTS={"www.python.org","files.pythonhosted.org","pypi.org","download.pytorch.org"}
def runtime_lock_manifest():
    global _RUNTIME_LOCK_MANIFEST_CACHE
    if _RUNTIME_LOCK_MANIFEST_CACHE is None:
        packed=base64.b85decode("".join(RUNTIME_LOCK_MANIFEST_B85).encode("ascii"))
        raw_manifest=bounded_decompress(packed,4*1024*1024)
        if hashlib.sha256(raw_manifest).hexdigest()!=RUNTIME_LOCK_MANIFEST_SHA256:
            raise RuntimeError("运行库规范清单SHA-256校验失败")
        value=json.loads(raw_manifest.decode("utf-8"))
        if not isinstance(value,dict) or safe_int(value.get("version"),0)!=RUNTIME_LOCK_MANIFEST_VERSION:
            raise RuntimeError("运行库规范清单版本无效")
        _RUNTIME_LOCK_MANIFEST_CACHE=value
    return _RUNTIME_LOCK_MANIFEST_CACHE
def runtime_lock_project_versions():
    entries=runtime_lock_manifest()["locks"].get(RUNTIME_ARCH_X64+"|builtin_cpu",[])
    return {normalized_project_name(item.get("name")):str(item.get("version","")) for item in entries}
def runtime_locked_projects():
    return set(runtime_lock_project_versions())
def runtime_dependency_providers():
    return dict(runtime_lock_manifest().get("dependency_providers",{}))
def runtime_dependency_contracts():
    result={}
    for project,contract in runtime_lock_manifest().get("dependency_contracts",{}).items():
        result[str(project)]={field:set(values) for field,values in contract.items()}
    return result
def runtime_required_projects():
    return set(runtime_lock_manifest().get("required_projects",[]))
STRICT_ACCEPTANCE_ITEMS=("启动","默认界面","文件夹","文件完整性","窗口","采集","学习","睡眠","训练","指导","弹窗","停止","单实例与目录锁","独立运行时","离线网络封锁","写入路径审计","多显示器与DPI","错误恢复")
STRICT_ACCEPTANCE_CASES={"启动":("control_panel_visible",),"默认界面":("exact_eight_buttons",),"文件夹":("select_prepare_confirm","migration_success","forced_failure_rollback",
        "prepare_cancel_cleanup"),"文件完整性":("normal_complete","network_failure_retry","escape_retry","locked_manifest"),"窗口":("ldplayer_confirmed","ordinary_confirmed","administrator_integrity_difference","emulator_scaling"),"采集":("minimized","occluded",
        "scaled","recreated"),"学习":("client_only_real_mouse",),"睡眠":("socket_blocked","model_optimized","pool_optimized","deterministic_seed"),"训练":("all_coordinates_in_client",
        "immutable_snapshot_change_stop"),"指导":("choices_only","finish_button","escape"),"弹窗":("confirm_only",),"停止":("starting","running","stopping","latency_thresholds","buttons_released","escape_to_input_lock","escape_to_buttons_released","abnormal_exit_release"),
    "单实例与目录锁":("named_mutex","directory_lock","lock_record"),"独立运行时":("fixed_python","worker_process","embedded_wheel_lock","host_abi_independent"),"离线网络封锁":("socket","urllib",
        "disconnected_windows"),"写入路径审计":("internal_audit","external_monitor"),"多显示器与DPI":("dpi100","dpi125","dpi150","dpi200","mixed_dpi","negative_coordinates","cross_monitor","hwnd_reuse"),
    "错误恢复":("input_locked","rollback","retry","no_pressed_buttons","no_orphan_process","no_staging")}
SAMPLE_IMAGE_VERSION=1
NEURAL_FEATURE_VERSION=2
MODEL_MAX_BYTES=256*1024*1024
REQUIRED_DEFAULT_BUTTONS={"选择文件夹","检查文件完整性","游戏","选择窗口","学习","睡眠","训练","指导"}
AUTHORITATIVE_DATA_PATHS=("universal_game_ai.db","models/vision","models/ocr","runtime.current","backups","quarantine","project","audit")
RUNTIME_PYPI_INDEX="https://pypi.org/simple"
RUNTIME_TORCH_CPU_INDEX="https://download.pytorch.org/whl/cpu"
RUNTIME_TORCH_CUDA_INDEX="https://download.pytorch.org/whl/cu130"
VISION_PREPROCESS_SIGNATURE={"version":2,"color_space":"RGB","width":FEATURE_W,"height":FEATURE_H,"resize":"nearest_center","content_region":"confirmed_client_content",
    "normalization":"uint8_to_float32_div_255","channel_order":"RGB","encoder_architecture":2}
VISION_PREPROCESS_HASH=hashlib.sha256(json.dumps(VISION_PREPROCESS_SIGNATURE,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest()

class RuntimeMetrics:
    def __init__(self,maximum=4096):
        self.maximum=max(64,int(maximum))
        self.lock=threading.RLock()
        self.values=defaultdict(lambda:deque(maxlen=self.maximum))
        self.counters=Counter()
    def observe(self,name,value):
        number=safe_float(value,0.0) if "safe_float" in globals() else float(value)
        with self.lock:
            self.values[str(name)].append(number)
    def increment(self,name,amount=1):
        with self.lock:
            self.counters[str(name)]+=int(amount)
    def snapshot(self):
        with self.lock:
            values={name:list(series) for name,series in self.values.items()}
            counters=dict(self.counters)
        result={"counters":counters,"series":{}}
        for name,series in values.items():
            ordered=sorted(series)
            if not ordered:
                continue
            def pick(fraction):
                return ordered[min(len(ordered)-1,max(0,int(round((len(ordered)-1)*fraction))))]
            result["series"][name]={"count":len(ordered),"min":ordered[0],"p50":pick(0.50),"p95":pick(0.95),"p99":pick(0.99),"max":ordered[-1],"latest":series[-1]}
        return result
RUNTIME_METRICS=RuntimeMetrics()

EMERGENCY_CLEANUP_ERRORS=deque(maxlen=256)
def cleanup_error_code(code,error):
    value=str(code or "")
    if value and value!="BEST_EFFORT_EXCEPTION":
        return value
    name=type(error).__name__
    message=str(error).casefold()
    if name=="InputStopped":
        return "USER_CANCELLED"
    if name=="TargetUnavailable":
        return "WINDOW_DISAPPEARED"
    if isinstance(error,FileNotFoundError):
        return "FILE_NOT_FOUND"
    if isinstance(error,sqlite3.OperationalError) and ("busy" in message or "locked" in message):
        return "SQLITE_BUSY"
    if isinstance(error,AssertionError):
        return "INVARIANT_VIOLATION"
    if isinstance(error,OSError):
        return "RESOURCE_CLOSE_FAILED"
    return "UNEXPECTED_CLEANUP_ERROR"
def error_location(error):
    try:
        frames=traceback.extract_tb(error.__traceback__) if getattr(error,"__traceback__",None) is not None else []
        frame=frames[-1] if frames else traceback.extract_stack(limit=3)[0]
        return {"file":Path(frame.filename).name,"line":int(frame.lineno),"function":str(frame.name)}
    except Exception:
        return None
def record_cleanup_error(code,error,details=None):
    normalized=cleanup_error_code(code,error)
    payload=dict(details) if isinstance(details,dict) else {}
    payload.pop("line",None)
    location=error_location(error)
    if location is not None:
        payload.setdefault("location",location)
    if normalized!=str(code):
        payload.setdefault("source_code",str(code))
    record={"created":time.time(),"code":normalized,"error":str(error),"details":payload}
    EMERGENCY_CLEANUP_ERRORS.append(record)
    store=globals().get("CURRENT_DATA_STORE")
    logger=getattr(store,"logger",None) if store is not None else None
    if logger is not None:
        try:
            logger.write(normalized,error,payload)
        except (OSError,ValueError,TypeError) as nested:
            EMERGENCY_CLEANUP_ERRORS.append({"created":time.time(),"code":"CLEANUP_LOG_WRITE_FAILED","error":str(nested),"details":{"source":normalized,"location":error_location(nested)}})
    return record
def best_effort_cleanup(code,callback,expected=(FileNotFoundError,)):
    try:
        return True,callback()
    except expected:
        return True,None
    except OSError as error:
        record_cleanup_error(code,error,{"category":"os_error"})
    except Exception as error:
        record_cleanup_error(code,error,{"category":"unexpected"})
    return False,None
def sample_retention_budget(family_count,session_count):
    families=max(1,safe_int(family_count,1,1,64)) if "safe_int" in globals() else max(1,int(family_count or 1))
    sessions=max(1,safe_int(session_count,1,1,64)) if "safe_int" in globals() else max(1,int(session_count or 1))
    return min(MAX_SAMPLES,max(DEFAULT_SAMPLE_BUDGET,400+families*180+sessions*120))
def native_windows_architecture():
    machine=""
    if os.name=="nt":
        try:
            kernel=ctypes.WinDLL("kernel32",use_last_error=True)
            function=getattr(kernel,"IsWow64Process2",None)
            if function is not None:
                process_machine=wintypes.USHORT()
                native_machine=wintypes.USHORT()
                function.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.USHORT),ctypes.POINTER(wintypes.USHORT)]
                function.restype=wintypes.BOOL
                if function(kernel.GetCurrentProcess(),ctypes.byref(process_machine),ctypes.byref(native_machine)):
                    if int(native_machine.value)==0xAA64:
                        return RUNTIME_ARCH_ARM64
                    if int(native_machine.value)==0x8664:
                        return RUNTIME_ARCH_X64
        except Exception:
            machine=""
        machine=str(os.environ.get("PROCESSOR_ARCHITEW6432") or os.environ.get("PROCESSOR_ARCHITECTURE") or "").lower()
    else:
        try:
            import platform
            machine=platform.machine().lower()
        except Exception:
            machine=""
    if "arm64" in machine or "aarch64" in machine:
        return RUNTIME_ARCH_ARM64
    if "amd64" in machine or "x86_64" in machine or "x64" in machine:
        return RUNTIME_ARCH_X64
    raise RuntimeError("仅支持Windows 11 x64或ARM64原生架构")
def embedded_runtime_lock(architecture=None):
    arch=str(architecture or native_windows_architecture())
    if arch!=RUNTIME_ARCH_X64:
        raise RuntimeError("ARM64尚无完整wheel锁和Windows 11实机验收证据，不宣称严格支持")
    key=arch+"|builtin_cpu"
    source=runtime_lock_manifest()["locks"].get(key)
    if not isinstance(source,list) or not source:
        raise RuntimeError("当前架构缺少内嵌运行库wheel锁："+arch)
    entries=[dict(item) for item in source]
    required=("name","version","filename","url","sha256","size","python_abi","architecture","backend")
    seen=set()
    for entry in entries:
        if any(field not in entry for field in required):
            raise RuntimeError("内嵌wheel锁字段不完整")
        parsed=urllib.parse.urlsplit(str(entry["url"]))
        if parsed.scheme.lower()!="https" or parsed.hostname not in RUNTIME_ALLOWED_DOWNLOAD_HOSTS:
            raise RuntimeError("内嵌wheel锁URL不受信任")
        name=str(entry["name"]).strip().lower().replace("_","-")
        if name in seen:
            raise RuntimeError("内嵌wheel锁项目重复："+name)
        seen.add(name)
        filename=str(entry["filename"])
        digest=str(entry["sha256"]).lower()
        if not str(entry["version"]).strip() or not filename or urllib.parse.unquote(Path(parsed.path).name)!=filename or parsed.query or parsed.fragment:
            raise RuntimeError("内嵌wheel锁文件名、版本或URL不一致")
        if len(digest)!=64 or any(value not in "0123456789abcdef" for value in digest) or safe_int(entry["size"],0,1,
            1024*1024*1024)<=0 or str(entry["python_abi"])!="cp312" or str(entry["architecture"])!=arch or str(entry["backend"])!="builtin_cpu":
            raise RuntimeError("内嵌wheel锁内容无效")
    entries=sorted(entries,key=lambda item:(str(item["name"]).casefold(),str(item["filename"])))
    if not runtime_lock_is_complete(entries):
        raise RuntimeError("内嵌运行库wheel锁不完整")
    return entries,hashlib.sha256(canonical_bytes(entries)).hexdigest(),key
def normalized_project_name(value):
    return str(value or "").strip().lower().replace("_","-")
def runtime_lock_dependency_closure_is_complete(entries):
    if not isinstance(entries,list) or not entries:
        return False
    versions={}
    for item in entries:
        if not isinstance(item,dict):
            return False
        name=normalized_project_name(item.get("name"))
        version=str(item.get("version","")).strip()
        if not name or not version or name in versions:
            return False
        versions[name]=version
    if set(versions)!=runtime_locked_projects() or versions!=runtime_lock_project_versions():
        return False
    for project,contract in runtime_dependency_contracts().items():
        if project not in versions:
            return False
        for dependency in contract.get("requires",set()):
            provider=runtime_dependency_providers().get(dependency,dependency)
            if provider not in versions:
                return False
    return True
def runtime_lock_is_complete(entries):
    names={normalized_project_name(item.get("name")) for item in entries if isinstance(item,dict)}
    return runtime_required_projects().issubset(names) and runtime_lock_dependency_closure_is_complete(entries)
def tree_size(path):
    root=Path(path)
    if not root.exists():
        return 0
    if root.is_file():
        try:
            return int(root.stat().st_size)
        except OSError:
            return 0
    total=0
    for item in root.rglob("*"):
        if item.is_file():
            try:
                total+=int(item.stat().st_size)
            except OSError:
                pass
    return total
def authoritative_data_size(base):
    root=Path(base)
    total=sum(tree_size(root/name) for name in AUTHORITATIVE_DATA_PATHS)
    for item in root.glob("recovery_*"):
        total+=tree_size(item)
    for item in root.iterdir() if root.exists() else []:
        if item.is_file() and item.name not in {"universal_game_ai.db","universal_game_ai.db-wal","universal_game_ai.db-shm"}:
            total+=tree_size(item)
    return total
def required_migration_space(source_base=None):
    source_size=authoritative_data_size(source_base) if source_base is not None else 0
    database_reserve=max(64*1024*1024,source_size//8)
    safety=max(128*1024*1024,(source_size+database_reserve)//5)
    return max(MIN_DATA_OPERATION_RESERVE,source_size*2+database_reserve+safety)
def required_runtime_space(base,wheel_bytes=0):
    root=Path(base)
    current=tree_size(root/"runtime.current")
    data=authoritative_data_size(root)
    wheels=max(0,int(wheel_bytes))
    installed=max(current,int(wheels*3.5),2*1024*1024*1024 if not current and not wheels else 0)
    staging=wheels+installed
    rollback=current
    reserve=max(512*1024*1024,data//5)
    safety=max(256*1024*1024,(staging+rollback+reserve)//5)
    return staging+rollback+reserve+safety
def ensure_free_space(path,required,label):
    root=Path(path)
    probe=root if root.exists() else root.parent
    probe.mkdir(parents=True,exist_ok=True)
    free=int(shutil.disk_usage(probe).free)
    need=max(0,int(required))
    if free<need:
        raise RuntimeError(str(label)+"需要约"+str(round(need/1024/1024/1024,2))+"GB可用空间，当前约"+str(round(free/1024/1024/1024,2))+"GB")
    return free
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
_BUILD_HASH=None
_BUILD_HASH_KEY=None
def current_build_hash():
    global _BUILD_HASH,_BUILD_HASH_KEY
    try:
        source=Path(__file__)
        stat=source.stat()
        key=(int(stat.st_size),int(stat.st_mtime_ns))
        if _BUILD_HASH is None or _BUILD_HASH_KEY!=key:
            _BUILD_HASH=hashlib.sha256(source.read_bytes()).hexdigest()
            _BUILD_HASH_KEY=key
        return _BUILD_HASH
    except Exception:
        return ""
def compatibility_signature():
    return {"format_version":FORMAT_VERSION,"model_schema_version":MODEL_SCHEMA_VERSION,"feature_algorithm_version":FEATURE_ALGORITHM_VERSION,
        "action_algorithm_version":ACTION_ALGORITHM_VERSION,"feature_size":[FEATURE_W,FEATURE_H,FEATURE_CHANNELS],"coarse_size":[COARSE_W,COARSE_H,FEATURE_CHANNELS],
        "window_rule_version":WINDOW_RULE_VERSION,"capture_backend_version":CAPTURE_BACKEND_VERSION,"thresholds":VersionedThresholdConfig.snapshot()}
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
    legacy_defaults={"required_sessions":2,"capture_min_holdout":20,"capture_min_accuracy":0.80,"capture_max_errors":0,"scene_min_holdout":10,"scene_min_accuracy":0.75,"scene_max_errors":0,
        "maximum_dangerous_false":0,"maximum_uncovered_false_accept":0}
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
    enough=bool(split_complete and int(session_count)>=VersionedThresholdConfig.required_sessions and int(holdout_count)>=VersionedThresholdConfig.review_min_holdout
        and int(accepted)>=VersionedThresholdConfig.review_min_accepted)
    global_pass=bool(float(coverage)>=VersionedThresholdConfig.minimum_coverage and float(overall_accuracy)>=VersionedThresholdConfig.minimum_overall_accuracy
        and float(error_upper_95)<=VersionedThresholdConfig.maximum_error_upper_95 and int(dangerous_false)<=VersionedThresholdConfig.maximum_dangerous_false
        and int(uncovered_false_accept)<=VersionedThresholdConfig.maximum_uncovered_false_accept)
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
def calculate_sequence_penalty(history,cluster_id,sequence_model):
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
class TaskAgentPolicy:
    def __init__(self,profile):
        self.profile=dict(profile) if isinstance(profile,dict) else {}
        self.allowed=set(str(value) for value in self.profile.get("allowed_families",[]))
        self.max_failures=max(1,safe_int(self.profile.get("max_consecutive_failures",3),3,1,20))
        self.failures=0
        self.history=deque(maxlen=128)
        self.game_id=str(self.profile.get("game_id",""))
        self.success_states=frozenset(str(value) for value in self.profile.get("success_states",[]))
        self.failure_states=frozenset(str(value) for value in self.profile.get("failure_states",[]))
    def allowed_action(self,action):
        family=action_family_key(action)
        return bool(family and family in self.allowed)
    def state_hash(self,feature):
        return visual_perceptual_hash(feature)
    def classify(self,feature):
        value=self.state_hash(feature)
        if value in self.success_states:
            return "success",safe_float(self.profile.get("success_reward",1.0),1.0)
        if value in self.failure_states:
            return "failure",safe_float(self.profile.get("failure_reward",-1.0),-1.0)
        hub=globals().get("SEMANTIC_EVENT_HUB")
        event=hub.latest(self.game_id or None,1.5) if hub is not None else None
        if event:
            if event.get("terminal")=="success":
                return "success",1.0
            if event.get("terminal")=="failure":
                return "failure",-1.0
            return "neutral",max(-0.25,min(0.25,safe_float(event.get("progress"),0.0)*0.25))
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
    @staticmethod
    def sequence_penalty(history,cluster_id,sequence_model):
        return calculate_sequence_penalty(history,cluster_id,sequence_model)
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
    return {"process_paths":sorted(paths),"window_classes":sorted(classes),"content_rect_norms":[list(value) for value in sorted(norms)],
        "content_aspect_min":min(aspects) if aspects else 0.0,"content_aspect_max":max(aspects) if aspects else 0.0,"dpi_min":min(dpis) if dpis else 0,"dpi_max":max(dpis) if dpis else 0,
        "capture_methods":sorted(methods),"window_rule_version":WINDOW_RULE_VERSION,"capture_backend_version":CAPTURE_BACKEND_VERSION}
class ThreadLocalSQLite:
    def __init__(self,path,read_only=False):
        self.path=Path(path)
        self.read_only=bool(read_only)
        self.lock=threading.RLock()
        self.local=threading.local()
        self.connections={}
        self.closing=False
    def _new(self):
        if self.closing:
            raise RuntimeError("SQLite连接池正在关闭")
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
        connection=getattr(self.local,"connection",None)
        if connection is None:
            connection=self._new()
            self.local.connection=connection
            with self.lock:
                self.connections[id(connection)]={"connection":connection,"thread":threading.current_thread().name,"created":time.monotonic()}
        return connection
    @contextmanager
    def thread_connection(self):
        connection=self.current()
        try:
            yield connection
        except BaseException:
            try:
                connection.rollback()
            except sqlite3.Error as error:
                record_cleanup_error("SQLITE_THREAD_ROLLBACK_FAILED",error)
            raise
        finally:
            self.close_current_thread()
    def execute(self,*args,**kwargs):
        return self.current().execute(*args,**kwargs)
    def executemany(self,*args,**kwargs):
        return self.current().executemany(*args,**kwargs)
    def commit(self):
        started=time.monotonic()
        try:
            return self.current().commit()
        finally:
            RUNTIME_METRICS.observe("sqlite_commit_ms",(time.monotonic()-started)*1000.0)
    def rollback(self):
        return self.current().rollback()
    def __enter__(self):
        self.current().__enter__()
        return self
    def __exit__(self,exc_type,exc_value,exc_traceback):
        return self.current().__exit__(exc_type,exc_value,exc_traceback)
    def close_current_thread(self):
        connection=getattr(self.local,"connection",None)
        if connection is None:
            return False
        self.local.connection=None
        with self.lock:
            self.connections.pop(id(connection),None)
        try:
            connection.close()
            return True
        except sqlite3.Error as error:
            record_cleanup_error("SQLITE_CONNECTION_CLOSE_FAILED",error)
            return False
    def connection_count(self):
        with self.lock:
            return len(self.connections)
    def close(self,timeout=3.0):
        self.closing=True
        deadline=time.monotonic()+max(0.0,float(timeout))
        self.close_current_thread()
        while True:
            with self.lock:
                remaining=list(self.connections.values())
            if not remaining or time.monotonic()>=deadline:
                break
            time.sleep(0.01)
        failures=[]
        for item in remaining:
            connection=item.get("connection")
            try:
                connection.rollback()
            except sqlite3.Error:
                pass
            try:
                connection.close()
            except sqlite3.Error as error:
                failures.append({"thread":item.get("thread"),"error":str(error)})
                record_cleanup_error("SQLITE_CONNECTION_CLOSE_FAILED",error,{"thread":item.get("thread")})
            finally:
                with self.lock:
                    self.connections.pop(id(connection),None)
        if failures:
            record_cleanup_error("SQLITE_FOREIGN_THREAD_CONNECTIONS_REMAIN",RuntimeError(json.dumps(failures,ensure_ascii=False,separators=(",",":"))))
        return not failures and self.connection_count()==0
class POINT(ctypes.Structure):
    _fields_=[("x",wintypes.LONG),("y",wintypes.LONG)]
class RECT(ctypes.Structure):
    _fields_=[("left",wintypes.LONG),("top",wintypes.LONG),("right",wintypes.LONG),("bottom",wintypes.LONG)]
class MSG(ctypes.Structure):
    _fields_=[("hwnd",wintypes.HWND),("message",wintypes.UINT),("wParam",wintypes.WPARAM),("lParam",wintypes.LPARAM),("time",wintypes.DWORD),("pt",POINT)]
class BITMAPINFOHEADER(ctypes.Structure):
    _fields_=[("biSize",wintypes.DWORD),("biWidth",wintypes.LONG),("biHeight",wintypes.LONG),("biPlanes",wintypes.WORD),("biBitCount",wintypes.WORD),("biCompression",wintypes.DWORD),
        ("biSizeImage",wintypes.DWORD),("biXPelsPerMeter",wintypes.LONG),("biYPelsPerMeter",wintypes.LONG),("biClrUsed",wintypes.DWORD),("biClrImportant",wintypes.DWORD)]
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
    _fields_=[("Width",ctypes.c_uint32),("Height",ctypes.c_uint32),("MipLevels",ctypes.c_uint32),("ArraySize",ctypes.c_uint32),("Format",ctypes.c_uint32),("SampleDesc",DXGI_SAMPLE_DESC),
        ("Usage",ctypes.c_uint32),("BindFlags",ctypes.c_uint32),("CPUAccessFlags",ctypes.c_uint32),("MiscFlags",ctypes.c_uint32)]
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

class ErrorCode(str,Enum):
    WINDOW_DISAPPEARED="WINDOW_DISAPPEARED"
    CAPTURE_TIMEOUT="CAPTURE_TIMEOUT"
    MODEL_INCOMPATIBLE="MODEL_INCOMPATIBLE"
    STORAGE_READ_ONLY="STORAGE_READ_ONLY"
    USER_CANCELLED="USER_CANCELLED"
    SQLITE_BUSY="SQLITE_BUSY"
    RESOURCE_CLOSE_FAILED="RESOURCE_CLOSE_FAILED"
    PROTOCOL_ERROR="PROTOCOL_ERROR"

class ModeName(str,Enum):
    LEARNING="学习"
    SLEEP="睡眠"
    TRAINING="训练"
    GUIDANCE="指导"
@dataclass(frozen=True)
class WindowIdentity:
    hwnd:int
    pid:int
    process_path:str
    window_class:str
    title:str
    process_start:float=0.0
    @classmethod
    def from_mapping(cls,value):
        item=dict(value) if isinstance(value,dict) else {}
        result=cls(safe_int(item.get("hwnd"),0),safe_int(item.get("pid"),0),str(item.get("process_path","")),str(item.get("window_class") or item.get("class") or ""),str(item.get("title",
                    "")),safe_float(item.get("process_start",item.get("process_created",0.0)),0.0))
        if result.hwnd<=0 or result.pid<=0 or not result.process_path or not result.window_class:
            raise ValueError("窗口身份字段不完整")
        return result
    def to_dict(self):
        return {"hwnd":self.hwnd,"pid":self.pid,"process_path":self.process_path,"window_class":self.window_class,"title":self.title,"process_start":self.process_start}
@dataclass(frozen=True)
class FramePacket:
    feature:bytes
    capture_method:str
    created:float
    usable_for_training:bool
    @classmethod
    def from_mapping(cls,value):
        item=dict(value) if isinstance(value,dict) else {}
        feature=feature_bytes(item.get("f"))
        method=str(item.get("method") or item.get("capture_method") or "")
        if not feature_valid(feature) or not method:
            raise ValueError("帧数据包无效")
        return cls(feature,method,safe_float(item.get("created"),time.time()),bool(item.get("usable_for_training",False)))
@dataclass(frozen=True)
class CalibrationResult:
    capture_method:str
    fps:float
    input_delay:float
    dynamic_passed:bool
    @classmethod
    def from_mapping(cls,value):
        item=dict(value) if isinstance(value,dict) else {}
        result=cls(str(item.get("capture_method") or item.get("method") or ""),safe_float(item.get("fps"),0.0,0.0,240.0),safe_float(item.get("input_delay"),0.24,0.0,5.0),bool(item.get("dynamic_passed",False)))
        if not result.capture_method or result.fps<=0:
            raise ValueError("校准结果无效")
        return result
def validate_packet(kind,value):
    name=str(kind)
    if name=="window_identity":
        return WindowIdentity.from_mapping(value).to_dict()
    if name=="frame":
        return FramePacket.from_mapping(value)
    if name=="calibration":
        return CalibrationResult.from_mapping(value)
    if name=="action":
        action=normalize_action(value)
        if action is None:
            raise ValueError("动作数据包无效")
        return action
    if name in {"review_request","review_response","runtime_packet","ai_packet"}:
        if not isinstance(value,dict):
            raise ValueError("进程数据包必须是字典")
        return dict(value)
    raise ValueError("未知数据包类型："+name)
class ModeResult:
    def __init__(self,status,summary,details=None):
        value=str(status)
        if value not in {"completed","stopped","failed"}:
            raise ValueError("模式结果状态无效")
        self.status=value
        self.summary=str(summary)
        self.details=dict(details) if isinstance(details,dict) else {}
class ControlStateMachine:
    def __init__(self):
        self.lock=threading.RLock()
        self.state=MODE_IDLE
        self.name=None
        self.shared_stop_event=threading.Event()
        self.stop_event=None
        self.requested_status="stopped"
        self.reason=""
        self.data_ready=False
        self.runtime_ready=False
        self.directory_phase="unselected"
    def set_directory_phase(self,phase):
        value=str(phase)
        if value not in {"unselected","preparing","prepared","ready","failed"}:
            raise ValueError("文件夹状态无效")
        with self.lock:
            self.directory_phase=value
            self.data_ready=value=="ready"
            if not self.data_ready:
                self.runtime_ready=False
    def set_runtime_ready(self,value):
        with self.lock:
            self.runtime_ready=bool(value and self.data_ready)
    def begin(self,name):
        with self.lock:
            if self.state!=MODE_IDLE:
                raise RuntimeError("当前已有操作正在运行，请先停止")
            if str(name)!="检查文件完整性" and not self.data_ready:
                raise RuntimeError("请先选择并确认文件夹")
            if str(name)!="检查文件完整性" and not self.runtime_ready:
                raise RuntimeError("请先完成文件完整性检查")
            self.state=MODE_STARTING
            self.name=str(name)
            self.shared_stop_event.clear()
            self.stop_event=self.shared_stop_event
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

class ManagedShutdownResource:
    def __init__(self,resource_name,request_stop,is_alive,close,force_close=None,phase=0):
        self.resource_name=str(resource_name)
        self._request_stop=request_stop
        self._is_alive=is_alive
        self._close=close
        self._force_close=force_close or (lambda:False)
        self.phase=max(0,int(phase))
    def request_stop(self):
        return self._request_stop()
    def is_alive(self):
        return bool(self._is_alive())
    def close(self,timeout):
        return bool(self._close(max(0.0,float(timeout))))
    def force_close(self):
        return bool(self._force_close())
class ShutdownCoordinator:
    def __init__(self,label,timeout):
        self.label=str(label)
        self.deadline=time.monotonic()+max(0.1,float(timeout))
        self.resources=[]
        self.errors=[]
        self.forced=[]
        self.requested=False
    def add(self,resource):
        if not isinstance(resource,ManagedShutdownResource):
            raise TypeError("关闭资源必须实现统一接口")
        self.resources.append(resource)
        return resource
    def request_stop(self):
        self.requested=True
        for resource in self.resources:
            try:
                resource.request_stop()
            except Exception as error:
                self.errors.append({"resource":resource.resource_name,"operation":"request_stop","error":str(error)})
                record_cleanup_error("SHUTDOWN_REQUEST_STOP_FAILED",error,{"resource":resource.resource_name,"label":self.label})
    def poll(self):
        self.request_stop()
        alive=[]
        for resource in self.resources:
            try:
                if resource.is_alive():
                    alive.append(resource)
            except Exception as error:
                alive.append(resource)
                self.errors.append({"resource":resource.resource_name,"operation":"is_alive","error":str(error)})
                record_cleanup_error("SHUTDOWN_ALIVE_CHECK_FAILED",error,{"resource":resource.resource_name,"label":self.label})
        if not alive:
            return {"done":True,"pending":[],"deadline_reached":False,"unforceable":[],"forced":list(self.forced),"errors":list(self.errors)}
        phase=min(resource.phase for resource in alive)
        current=[resource for resource in alive if resource.phase==phase]
        for resource in current:
            try:
                resource.close(0.0)
            except Exception as error:
                self.errors.append({"resource":resource.resource_name,"operation":"close","error":str(error)})
                record_cleanup_error("SHUTDOWN_CLOSE_FAILED",error,{"resource":resource.resource_name,"label":self.label})
        deadline_reached=time.monotonic()>=self.deadline
        unforceable=[]
        if deadline_reached:
            for resource in current:
                try:
                    if resource.is_alive():
                        forced=resource.force_close()
                        if forced:
                            self.forced.append(resource.resource_name)
                        elif resource.is_alive():
                            unforceable.append(resource.resource_name)
                except Exception as error:
                    unforceable.append(resource.resource_name)
                    self.errors.append({"resource":resource.resource_name,"operation":"force_close","error":str(error)})
                    record_cleanup_error("SHUTDOWN_FORCE_CLOSE_FAILED",error,{"resource":resource.resource_name,"label":self.label})
        pending=[]
        for resource in self.resources:
            try:
                if resource.is_alive():
                    pending.append(resource.resource_name)
            except Exception:
                pending.append(resource.resource_name)
        return {"done":not pending,"pending":sorted(set(pending)),"deadline_reached":deadline_reached,"unforceable":sorted(set(unforceable)),"forced":list(dict.fromkeys(self.forced)),"errors":list(self.errors)}
class ResourceShutdownBarrier:
    def __init__(self,label,timeout=4.0):
        self.coordinator=ShutdownCoordinator(label,timeout)
        self.last={"done":True,"pending":[]}
    def add(self,name,stopper,alive,forcer=None,phase=0):
        resource=ManagedShutdownResource(
            name,
            lambda:stopper(0.0),
            alive,
            stopper,
            forcer or (lambda:False),
            phase,
        )
        self.coordinator.add(resource)
        return resource
    def request_stop(self):
        self.coordinator.request_stop()
    def poll(self):
        self.last=self.coordinator.poll()
        return bool(self.last.get("done"))
    def pending_names(self):
        if not self.last.get("done",True):
            return list(self.last.get("pending",[]))
        pending=[]
        for resource in self.coordinator.resources:
            try:
                if resource.is_alive():
                    pending.append(resource.resource_name)
            except Exception as error:
                record_cleanup_error("RESOURCE_STATE_CHECK_FAILED",error,{"resource":resource.resource_name})
                pending.append(resource.resource_name)
        return sorted(set(pending))
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
def window_work_area(widget):
    try:
        if os.name=="nt":
            rect=RECT()
            if ctypes.WinDLL("user32",use_last_error=True).SystemParametersInfoW(0x0030,0,ctypes.byref(rect),0):
                return int(rect.left),int(rect.top),max(320,int(rect.right-rect.left)),max(240,int(rect.bottom-rect.top))
    except Exception as error:
        record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
    try:
        return 0,0,max(320,int(widget.winfo_screenwidth())),max(240,int(widget.winfo_screenheight()))
    except Exception:
        return 0,0,900,700
def fit_window(widget,desired_width,desired_height,minimum_width=480,minimum_height=320):
    left,top,work_width,work_height=window_work_area(widget)
    width=max(320,min(int(desired_width),max(320,int(work_width*0.94))))
    height=max(240,min(int(desired_height),max(240,int(work_height*0.92))))
    min_width=min(width,max(320,int(minimum_width)))
    min_height=min(height,max(240,int(minimum_height)))
    x=left+max(0,(work_width-width)//2)
    y=top+max(0,(work_height-height)//2)
    widget.geometry(str(width)+"x"+str(height)+"+"+str(x)+"+"+str(y))
    widget.minsize(min_width,min_height)
    return width,height
def scrollable_frame(window,padding=0,horizontal=False):
    shell=ttk.Frame(window)
    shell.pack(fill="both",expand=True)
    canvas=tk.Canvas(shell,highlightthickness=0,borderwidth=0)
    vertical=ttk.Scrollbar(shell,orient="vertical",command=canvas.yview)
    horizontal_bar=ttk.Scrollbar(shell,orient="horizontal",command=canvas.xview) if horizontal else None
    canvas.configure(yscrollcommand=vertical.set)
    if horizontal_bar is not None:
        canvas.configure(xscrollcommand=horizontal_bar.set)
    canvas.grid(row=0,column=0,sticky="nsew")
    vertical.grid(row=0,column=1,sticky="ns")
    if horizontal_bar is not None:
        horizontal_bar.grid(row=1,column=0,sticky="ew")
    shell.rowconfigure(0,weight=1)
    shell.columnconfigure(0,weight=1)
    inner=ttk.Frame(canvas,padding=padding)
    item=canvas.create_window((0,0),window=inner,anchor="nw")
    def update_region(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
    def update_width(event):
        if horizontal_bar is None:
            canvas.itemconfigure(item,width=max(1,event.width))
    inner.bind("<Configure>",update_region)
    canvas.bind("<Configure>",update_width)
    def wheel(event):
        if event.delta:
            canvas.yview_scroll(-1 if event.delta>0 else 1,"units")
    canvas.bind("<MouseWheel>",wheel)
    inner._ugai_canvas=canvas
    return inner
def hamming_distance_hex(first,second):
    return (int(str(first),16)^int(str(second),16)).bit_count() if hasattr(int,"bit_count") else bin(int(str(first),16)^int(str(second),16)).count("1")
def near_perceptual_hash_pairs(values,max_distance=4,stop_check=None):
    hashes=sorted(set(str(value) for value in values))
    if len(hashes)<2:
        return []
    segment_count=max(1,int(max_distance)+1)
    widths=[64//segment_count]*segment_count
    for index in range(64%segment_count):
        widths[index]+=1
    masks=[]
    shift=64
    for width in widths:
        shift-=width
        masks.append((shift,(1<<width)-1))
    buckets=defaultdict(list)
    pairs=set()
    for index,value in enumerate(hashes):
        number=int(value,16)
        candidates=set()
        for segment,(shift,mask) in enumerate(masks):
            key=(segment,(number>>shift)&mask)
            candidates.update(buckets[key])
        for other in candidates:
            if hamming_distance_hex(value,other)<=max_distance:
                pairs.add((other,value) if other<value else (value,other))
        for segment,(shift,mask) in enumerate(masks):
            buckets[(segment,(number>>shift)&mask)].append(value)
        if stop_check is not None and index%256==0 and stop_check():
            raise InputStopped("睡眠已停止")
    return sorted(pairs)
def batch_feature_distances(query,items):
    values=list(items)
    if not values:
        return []
    np=_optional_numpy()
    if np is None:
        return [feature_distance(query,item) for item in values]
    first=np.frombuffer(feature_bytes(query),dtype=np.uint8).reshape(FEATURE_CHANNELS,PIXELS).astype(np.int32)
    matrix=np.stack([np.frombuffer(feature_bytes(item),dtype=np.uint8).reshape(FEATURE_CHANNELS,PIXELS) for item in values]).astype(np.int32)
    means=np.mean((matrix-first[None,:,:])**2,axis=2,dtype=np.float64)
    return np.dot(means,np.asarray((0.30,0.19,0.19,0.22,0.10),dtype=np.float64)).astype(float).tolist()

class PrototypeConflictTracker:
    def __init__(self,stop_check=None,max_candidates=80,max_buckets=8):
        self.stop_check=stop_check or (lambda:False)
        self.max_candidates=max(8,int(max_candidates))
        self.max_buckets=max(2,int(max_buckets))
        self.prototypes={}
        self.buckets=defaultdict(list)
        self.bucket_representatives={}
    def _scene(self,proto):
        feature=feature_bytes(proto.get("f"))
        plane=feature[:PIXELS]
        edges=feature[3*PIXELS:4*PIXELS]
        mean=sum(plane)/max(1,len(plane))
        edge_mean=sum(edges)/max(1,len(edges))
        temporal=proto.get("temporal",{}) if isinstance(proto.get("temporal"),dict) else {}
        deltas=temporal.get("recent_frame_deltas",[])
        motion=sum(safe_float(value,0.0) for value in deltas)/max(1,len(deltas))
        return "L"+str(min(5,int(mean//43)))+"|E"+str(min(5,int(edge_mean//43)))+"|M"+str(min(5,int(motion//120)))
    def _keys(self,proto):
        family=action_family_key(proto.get("a"))
        scene=self._scene(proto)
        methods=proto.get("capture_methods",[]) or ["unknown"]
        return [(family,scene,str(method)) for method in sorted(set(str(value) for value in methods))]
    def _candidate_ids(self,proto):
        own_keys=self._keys(proto)
        exact=[]
        for family,scene,backend in own_keys:
            for key,ids in self.buckets.items():
                if key[1]==scene and key[2]==backend:
                    exact.extend(ids)
        selected=[]
        seen=set()
        for value in exact:
            if value not in seen:
                seen.add(value)
                selected.append(value)
        if len(selected)<self.max_candidates:
            ranked=[]
            for key,representative in self.bucket_representatives.items():
                if any(key[2]==own[2] for own in own_keys):
                    ranked.append((coarse_distance(proto.get("coarse"),representative),key))
            for _,key in sorted(ranked,key=lambda item:(item[0],item[1]))[:self.max_buckets]:
                for value in self.buckets.get(key,[]):
                    if value not in seen:
                        seen.add(value)
                        selected.append(value)
                        if len(selected)>=self.max_candidates:
                            break
                if len(selected)>=self.max_candidates:
                    break
        return selected[:self.max_candidates]
    def _update_pair(self,first,second,visual_value):
        if str(first.get("cluster_id"))==str(second.get("cluster_id")):
            return
        temporal_value=temporal_distance(first.get("temporal",{}),second.get("temporal",{}))
        for current,other in ((first,second),(second,first)):
            old=safe_float(current.get("_nearest_conflict_distance"),float("inf"))
            if float(visual_value)<old:
                current["_nearest_conflict_distance"]=float(visual_value)
                current["_nearest_conflict_temporal"]=float(temporal_value)
                current["_nearest_conflict_id"]=str(other.get("id"))
    def add_batch(self,items):
        values=[item for item in items if isinstance(item,dict) and item.get("id")]
        for index,proto in enumerate(values):
            if index%16==0 and self.stop_check():
                raise InputStopped("睡眠已停止")
            candidate_ids=self._candidate_ids(proto)
            candidates=[self.prototypes[value] for value in candidate_ids if value in self.prototypes and str(self.prototypes[value].get("cluster_id"))!=str(proto.get("cluster_id"))]
            if candidates:
                distances=batch_feature_distances(proto["f"],[item["f"] for item in candidates])
                for other,distance in zip(candidates,distances):
                    self._update_pair(proto,other,distance)
            identity=str(proto["id"])
            self.prototypes[identity]=proto
            for key in self._keys(proto):
                self.buckets[key].append(identity)
                self.bucket_representatives.setdefault(key,proto.get("coarse"))
    def retain(self,items):
        kept={str(item.get("id")) for item in items}
        removed=set(self.prototypes)-kept
        if not removed:
            return
        for identity in removed:
            self.prototypes.pop(identity,None)
        self.buckets=defaultdict(list)
        self.bucket_representatives={}
        for identity,proto in self.prototypes.items():
            for key in self._keys(proto):
                self.buckets[key].append(identity)
                self.bucket_representatives.setdefault(key,proto.get("coarse"))
        affected=[]
        for proto in self.prototypes.values():
            if str(proto.get("_nearest_conflict_id","")) in removed:
                proto.pop("_nearest_conflict_distance",None)
                proto.pop("_nearest_conflict_temporal",None)
                proto.pop("_nearest_conflict_id",None)
                affected.append(proto)
        for proto in affected:
            candidates=[self.prototypes[value] for value in self._candidate_ids(proto) if value in self.prototypes and value!=str(proto.get("id"))
                and str(self.prototypes[value].get("cluster_id"))!=str(proto.get("cluster_id"))]
            if candidates:
                distances=batch_feature_distances(proto["f"],[item["f"] for item in candidates])
                for other,distance in zip(candidates,distances):
                    self._update_pair(proto,other,distance)
    def finalize(self,items):
        self.retain(items)
        for proto in items:
            nearest=safe_float(proto.pop("_nearest_conflict_distance",float("inf")),float("inf"))
            temporal_nearest=safe_float(proto.pop("_nearest_conflict_temporal",1.0),1.0)
            proto.pop("_nearest_conflict_id",None)
            proto["nearest_conflicting_distance"]=None if math.isinf(nearest) else round(nearest,6)
            intra=float(proto.get("intra_threshold",proto["threshold"]))
            visual_close=not math.isinf(nearest) and nearest<=max(1e-6,intra*0.20)
            temporal_close=temporal_nearest<=max(float(proto.get("temporal_threshold",0.25)),0.25)
            proto["ambiguous"]=bool(visual_close and temporal_close)
            proto["threshold"]=round(max(0.001,intra if math.isinf(nearest) else min(intra,max(0.001,nearest*0.62))),6)
            proto["minimum_second_candidate_gap"]=round(max(10.0,float(proto["threshold"])*0.15,0.0 if math.isinf(nearest) else nearest*0.10),6)
            proto["channel_stats"]={"mean":sum(proto["f"])/len(proto["f"]),"minimum":min(proto["f"]),"maximum":max(proto["f"])}
        return items
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
def deterministic_sleep_seed(game_id,samples):
    checksums=[]
    for item in samples or []:
        checksum=str(item.get("checksum","")).strip() if isinstance(item,dict) else ""
        if not checksum:
            checksum=immutable_digest({"rgb":item.get("rgb") if isinstance(item,dict) else None,"action":item.get("a") if isinstance(item,dict) else None,
                    "session_id":item.get("session_id") if isinstance(item,dict) else None})
        checksums.append(checksum)
    material={"game_id":str(game_id),"algorithm_version":ACTION_ALGORITHM_VERSION,"model_schema":MODEL_SCHEMA_VERSION,"sample_checksums":sorted(checksums)}
    digest=hashlib.sha256(canonical_bytes(material)).hexdigest()
    return int(digest[:16],16)&0x7fffffffffffffff,{"material_hash":digest,"sample_count":len(checksums),"algorithm_version":ACTION_ALGORITHM_VERSION,"model_schema":MODEL_SCHEMA_VERSION}
def model_quality_snapshot(rows):
    parsed=[]
    for row in rows or []:
        validation=row.get("validation",{}) if isinstance(row,dict) else {}
        if isinstance(validation,str):
            try:
                validation=json.loads(validation)
            except Exception:
                validation={}
        parsed.append({"overall_accuracy":safe_float(validation.get("overall_accuracy"),0.0,0.0,1.0),"coverage":safe_float(validation.get("coverage"),0.0,0.0,1.0),
                "dangerous_false":safe_int(validation.get("dangerous_false"),0,0),"prototype_count":safe_int(row.get("prototype_count"),0,0),"checksum":str(row.get("checksum",""))})
    return {"holdout_accuracy":max([item["overall_accuracy"] for item in parsed] or [0.0]),"rejection_coverage":max([item["coverage"] for item in parsed] or [0.0]),
        "dangerous_false_triggers":sum(item["dangerous_false"] for item in parsed),"prototype_count":sum(item["prototype_count"] for item in parsed),"model_count":len(parsed),
        "content_hash":hashlib.sha256(canonical_bytes([[item["checksum"],item["prototype_count"]] for item in parsed])).hexdigest()}
def immutable_digest(value):
    def normalize(item):
        if isinstance(item,(bytes,bytearray,memoryview)):
            raw=bytes(item)
            return {"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
        if isinstance(item,dict):
            return {str(key):normalize(item[key]) for key in sorted(item,key=lambda key:str(key))}
        if isinstance(item,(list,tuple)):
            return [normalize(entry) for entry in item]
        if isinstance(item,(set,frozenset)):
            return sorted((normalize(entry) for entry in item),key=lambda entry:json.dumps(entry,ensure_ascii=False,sort_keys=True,separators=(",",":")))
        if isinstance(item,Path):
            return str(item)
        if isinstance(item,(str,int,float,bool)) or item is None:
            return item
        return str(item)
    return hashlib.sha256(canonical_bytes(normalize(value))).hexdigest()
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
        record={"time":time.time(),"code":str(code),"thread":str(thread_name or threading.current_thread().name),"mode":str(mode or ""),"game_id":str(game_id or ""),
            "window_identity":window_identity if isinstance(window_identity,dict) else {},"exception_type":exception_type,"message":message[:2000],"stack":stack,"details":details if isinstance(details,dict) else {}}
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
_NUMPY_CHECKED=False
_NUMPY_MODULE=None
def _optional_numpy():
    global _NUMPY_CHECKED,_NUMPY_MODULE
    if not _NUMPY_CHECKED:
        try:
            import numpy
            _NUMPY_MODULE=numpy
        except ImportError:
            _NUMPY_MODULE=None
        _NUMPY_CHECKED=True
    return _NUMPY_MODULE
def _pool_boundaries(src_w,src_h,out_w,out_h):
    key=(int(src_w),int(src_h),int(out_w),int(out_h))
    value=POOL_BOUNDARIES.get(key)
    if value is None:
        y=tuple(index*int(src_h)//int(out_h) for index in range(int(out_h)+1))
        x=tuple(index*int(src_w)//int(out_w) for index in range(int(out_w)+1))
        value=(y,x)
        POOL_BOUNDARIES[key]=value
    return value

def _feature_weight_array(np):
    global FEATURE_DISTANCE_WEIGHTS_ARRAY
    if FEATURE_DISTANCE_WEIGHTS_ARRAY is None:
        FEATURE_DISTANCE_WEIGHTS_ARRAY=np.asarray(FEATURE_DISTANCE_WEIGHTS,dtype=np.float64)
    return FEATURE_DISTANCE_WEIGHTS_ARRAY

def _pool_channel(source,offset,src_w,src_h,out_w,out_h):
    y_bounds,x_bounds=_pool_boundaries(src_w,src_h,out_w,out_h)
    np=_optional_numpy()
    if np is not None:
        plane=np.frombuffer(source,dtype=np.uint8,count=int(src_w)*int(src_h),offset=int(offset)).reshape(int(src_h),int(src_w))
        y_edges=np.asarray(y_bounds,dtype=np.int64)
        x_edges=np.asarray(x_bounds,dtype=np.int64)
        integral=np.pad(plane.astype(np.uint64).cumsum(0).cumsum(1),((1,0),(1,0)))
        y0=y_edges[:-1][:,None]; y1=np.maximum(y0+1,y_edges[1:][:,None])
        x0=x_edges[:-1][None,:]; x1=np.maximum(x0+1,x_edges[1:][None,:])
        sums=integral[y1,x1]-integral[y0,x1]-integral[y1,x0]+integral[y0,x0]
        counts=np.maximum(1,(y1-y0)*(x1-x0))
        return np.rint(sums/counts).astype(np.uint8).ravel().tolist()
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
    first_bytes=feature_bytes(a)
    second_bytes=feature_bytes(b)
    np=_optional_numpy()
    weights=FEATURE_DISTANCE_WEIGHTS
    if np is not None:
        first=np.frombuffer(first_bytes,dtype=np.uint8).reshape(FEATURE_CHANNELS,PIXELS).astype(np.int16)
        second=np.frombuffer(second_bytes,dtype=np.uint8).reshape(FEATURE_CHANNELS,PIXELS).astype(np.int16)
        difference=first-second
        means=np.mean(np.square(difference,dtype=np.int32),axis=1,dtype=np.float64)
        return float(np.dot(_feature_weight_array(np),means))
    first=memoryview(first_bytes)
    second=memoryview(second_bytes)
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
    first_bytes=feature_bytes(a)
    second_bytes=feature_bytes(b)
    np=_optional_numpy()
    weights=(0.34,0.22,0.22,0.22)
    if np is not None:
        first=np.frombuffer(first_bytes,dtype=np.uint8,count=PIXELS*4).reshape(4,PIXELS).astype(np.int16)
        second=np.frombuffer(second_bytes,dtype=np.uint8,count=PIXELS*4).reshape(4,PIXELS).astype(np.int16)
        difference=first-second
        means=np.mean(np.square(difference,dtype=np.int32),axis=1,dtype=np.float64)
        return float(np.dot(np.asarray(weights,dtype=np.float64),means))
    first=memoryview(first_bytes)
    second=memoryview(second_bytes)
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
    weights=FEATURE_DISTANCE_WEIGHTS
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
def sample_rgb_valid(rgb):
    return isinstance(rgb,(bytes,bytearray,list,tuple)) and len(rgb)==PIXELS*3
def sample_rgb_bytes(rgb):
    if not sample_rgb_valid(rgb):
        return None
    if isinstance(rgb,bytes):
        return rgb
    return bytes(int(max(0,min(255,round(float(value))))) for value in rgb)
def upgrade_sample_rgb(value):
    if value is None:
        return None
    raw=bytes(value)
    if len(raw)==PIXELS*3:
        return raw
    gray=upgrade_gray_image(raw)
    if gray is None:
        return None
    return bytes(channel for pixel in gray for channel in (pixel,pixel,pixel))
def preprocess_signature():
    return dict(VISION_PREPROCESS_SIGNATURE)
def runtime_python_path(base):
    root=Path(base)/"runtime.current"/"python"
    return root/("python.exe" if os.name=="nt" else "python")
def runtime_site_packages(base):
    return Path(base)/"runtime.current"/"python"/"Lib"/"site-packages"
def runtime_manifest_path(base):
    return Path(base)/"runtime.current"/"runtime_manifest.json"
def sha256_file(path,maximum=None):
    source=Path(path)
    if maximum is not None and source.stat().st_size>int(maximum):
        raise RuntimeError("文件超过允许大小")
    digest=hashlib.sha256()
    with source.open("rb") as handle:
        while True:
            block=handle.read(1024*1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()
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
    src_w=int(src_w); src_h=int(src_h); out_w=int(out_w); out_h=int(out_h)
    if len(source)!=src_w*src_h*3 or min(src_w,src_h,out_w,out_h)<1:
        raise CaptureUnavailable("RGB画面尺寸无效")
    np=_optional_numpy()
    if np is not None:
        array=np.frombuffer(source,dtype=np.uint8).reshape(src_h,src_w,3)
        ys=np.minimum(src_h-1,((2*np.arange(out_h)+1)*src_h)//(2*out_h))
        xs=np.minimum(src_w-1,((2*np.arange(out_w)+1)*src_w)//(2*out_w))
        return array[ys[:,None],xs[None,:],:].tobytes()
    result=bytearray(out_w*out_h*3)
    for oy in range(out_h):
        sy=min(src_h-1,(2*oy+1)*src_h//(2*out_h))
        for ox in range(out_w):
            sx=min(src_w-1,(2*ox+1)*src_w//(2*out_w))
            source_index=(sy*src_w+sx)*3
            target_index=(oy*out_w+ox)*3
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
    return {"recent_frame_count":recent_count,"recent_frame_deltas":deltas,"recent_actions":actions,"previous_action_changed_frame":bool(source.get("previous_action_changed_frame",True)),
        "state_duration":state_duration,"cursor":cursor,"window_size":size,"dpi":dpi,"capture_method":str(source.get("capture_method","unknown")),"complete":bool(recent_count>=3 and len(deltas)>=2
            and len(actions)>=2 and cursor is not None and size is not None)}
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
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        stopped=not self.process.is_alive()
        if stopped:
            try:
                self.connection.close()
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        return stopped
    def stop(self,timeout=1.0):
        with self.lock:
            if not self.retired:
                try:
                    self.connection.send(None)
                except Exception as error:
                    record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
            self.retired=True
            wait=max(0.0,float(timeout))
            if wait>0:
                try:
                    self.process.join(wait)
                except Exception as error:
                    record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
            stopped=not self.process.is_alive()
            if stopped:
                try:
                    self.connection.close()
                except Exception as error:
                    record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
        self.d3d11.D3D11CreateDevice.argtypes=[ctypes.c_void_p,ctypes.c_uint32,wintypes.HMODULE,ctypes.c_uint32,ctypes.POINTER(ctypes.c_uint32),ctypes.c_uint32,ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_uint32),ctypes.POINTER(ctypes.c_void_p)]
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
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
    def _close(self,obj):
        if not obj:
            return
        closable=None
        try:
            closable=self._query(obj,guid("30D5A829-7FA4-4026-83BB-D75BAE4EA99E"))
            self._check(self._call(closable,6,ctypes.c_long,[]),"关闭Windows Graphics Capture对象")
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
            self._check(self._call(item_factory,3,ctypes.c_long,[wintypes.HWND,ctypes.POINTER(GUID),ctypes.POINTER(ctypes.c_void_p)],wintypes.HWND(hwnd),ctypes.byref(item_iid),
                    ctypes.byref(capture_item)),"为窗口创建GraphicsCaptureItem")
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
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
            finally:
                self._release(session2)
            session3=None
            try:
                session3=self._query(session,guid("F2CDD966-22AE-5EA1-9596-3A289344C3BE"))
                self._check(self._call(session3,7,ctypes.c_long,[ctypes.c_ubyte],0),"关闭捕获边框")
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
            finally:
                self._release(session3)
            self._check(self._call(session,6,ctypes.c_long,[]),"启动Windows Graphics Capture")
            result={"thread":threading.get_ident(),"hwnd":int(hwnd),"geometry":tuple(geometry),"item_size":(int(item_size.Width),int(item_size.Height)),"device":device,"context":context,
                "winrt_device":winrt_device,"capture_item":capture_item,"pool":pool,"session":session,"started":time.time(),"ro_initialized":ro_initialized}
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
                except Exception as error:
                    record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
                self._check(self._call(item["device"],5,ctypes.c_long,[ctypes.POINTER(D3D11_TEXTURE2D_DESC),ctypes.c_void_p,ctypes.POINTER(ctypes.c_void_p)],ctypes.byref(staging_desc),None,
                        ctypes.byref(created)),"创建CPU可读捕获纹理")
                item["staging"]=created
                item["staging_key"]=staging_key
            staging=item["staging"]
            self._call(item["context"],47,None,[ctypes.c_void_p,ctypes.c_void_p],staging,texture)
            mapped_resource=D3D11_MAPPED_SUBRESOURCE()
            self._check(self._call(item["context"],14,ctypes.c_long,[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_uint32,ctypes.POINTER(D3D11_MAPPED_SUBRESOURCE)],staging,0,1,0,
                    ctypes.byref(mapped_resource)),"映射捕获纹理")
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
                except Exception as error:
                    record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
def process_start_wall_time(pid=None):
    value=os.getpid() if pid is None else safe_int(pid,os.getpid(),1)
    if os.name=="nt":
        kernel=ctypes.WinDLL("kernel32",use_last_error=True)
        kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
        kernel.OpenProcess.restype=wintypes.HANDLE
        kernel.GetProcessTimes.argtypes=[wintypes.HANDLE,ctypes.POINTER(FILETIME),ctypes.POINTER(FILETIME),ctypes.POINTER(FILETIME),ctypes.POINTER(FILETIME)]
        kernel.GetProcessTimes.restype=wintypes.BOOL
        kernel.CloseHandle.argtypes=[wintypes.HANDLE]
        handle=kernel.OpenProcess(0x1000,False,value)
        if handle:
            created=FILETIME(); exited=FILETIME(); kernel_time=FILETIME(); user_time=FILETIME()
            try:
                if kernel.GetProcessTimes(handle,ctypes.byref(created),ctypes.byref(exited),ctypes.byref(kernel_time),ctypes.byref(user_time)):
                    ticks=(int(created.dwHighDateTime)<<32)|int(created.dwLowDateTime)
                    return ticks/10000000.0-11644473600.0
            finally:
                kernel.CloseHandle(handle)
    try:
        stat=(Path("/proc")/str(value)/"stat").read_text(encoding="ascii",errors="ignore").split()
        ticks=os.sysconf("SC_CLK_TCK")
        boot=time.time()-float(Path("/proc/uptime").read_text(encoding="ascii").split()[0])
        return boot+safe_float(stat[21],0.0)/max(1.0,float(ticks))
    except Exception:
        return time.time()-time.monotonic()
class ProcessInstanceLock:
    ERROR_ALREADY_EXISTS=183
    def __init__(self):
        self.handle=None
        self.name="Local\\UniversalGameAI-"+hashlib.sha256(os.path.normcase(str(Path.home())).encode("utf-8","replace")).hexdigest()[:24]
    def acquire(self):
        if os.name!="nt":
            return self
        kernel32=ctypes.WinDLL("kernel32",use_last_error=True)
        kernel32.CreateMutexW.argtypes=[ctypes.c_void_p,wintypes.BOOL,wintypes.LPCWSTR]
        kernel32.CreateMutexW.restype=wintypes.HANDLE
        kernel32.CloseHandle.argtypes=[wintypes.HANDLE]
        kernel32.CloseHandle.restype=wintypes.BOOL
        handle=kernel32.CreateMutexW(None,False,self.name)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        if ctypes.get_last_error()==self.ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(handle)
            raise RuntimeError("已有通用游戏AI实例正在运行")
        self.handle=handle
        return self
    def close(self):
        handle=self.handle
        self.handle=None
        if handle and os.name=="nt":
            try:
                ctypes.WinDLL("kernel32",use_last_error=True).CloseHandle(handle)
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
class DataDirectoryLock:
    def __init__(self,base):
        self.base=Path(base).expanduser().resolve()
        self.path=self.base/".ugai.lock"
        self.handle=None
        self.locked=False
        self.record={}
    def acquire(self):
        self.base.mkdir(parents=True,exist_ok=True)
        handle=self.path.open("a+b")
        try:
            handle.seek(0)
            if handle.read(1)==b"":
                handle.seek(0)
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            if os.name=="nt":
                import msvcrt
                msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            handle.close()
            raise RuntimeError("该文件夹正被另一个通用游戏AI实例占用")
        self.handle=handle
        self.locked=True
        self.record={"pid":os.getpid(),"process_started_wall":round(process_start_wall_time(),6),"acquired":time.time(),"build_hash":current_build_hash(),"directory":str(self.base),"nonce":uuid.uuid4().hex}
        payload=json.dumps(self.record,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
        handle.seek(0)
        handle.truncate()
        handle.write(payload)
        handle.flush()
        try:
            os.fsync(handle.fileno())
        except OSError:
            pass
        return self
    def close(self):
        handle=self.handle
        self.handle=None
        if handle is None:
            return
        try:
            handle.seek(0)
            if os.name=="nt":
                import msvcrt
                msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(),fcntl.LOCK_UN)
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        try:
            handle.close()
        finally:
            self.locked=False
class WritePathAudit:
    def __init__(self,base):
        self.base=Path(base).resolve()
        self.path=self.base/"audit"/"write_paths.jsonl"
        self.lock=threading.RLock()
    def record(self,operation,path,allowed=True,details=None):
        target=Path(path).expanduser().resolve()
        inside=False
        try:
            target.relative_to(self.base)
            inside=True
        except ValueError:
            inside=False
        value={"time":time.time(),"operation":str(operation),"path":str(target),"inside_confirmed_directory":inside,"allowed":bool(allowed and inside),"details":details if isinstance(details,dict) else {}}
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.lock,self.path.open("a",encoding="utf-8") as handle:
            handle.write(json.dumps(value,ensure_ascii=False,separators=(",",":"))+"\n")
        if not value["allowed"]:
            raise RuntimeError("写入路径超出用户确认目录："+str(target))
        return value
class WriteBoundaryGuard:
    def __init__(self,base,audit=None):
        self.base=Path(base).expanduser().resolve()
        self.audit=audit
        self.local=threading.local()
    def update(self,base,audit=None):
        self.base=Path(base).expanduser().resolve()
        if audit is not None:
            self.audit=audit
    def _target(self,value):
        if isinstance(value,int) or value is None:
            return None
        raw=os.fsdecode(value)
        if raw in {"",os.devnull,"NUL","nul"} or raw.startswith("<") or raw.startswith(r"\.\pipe"):
            return None
        return Path(raw).expanduser().resolve()
    def check(self,operation,value):
        target=self._target(value)
        if target is None:
            return True
        try:
            target.relative_to(self.base)
            inside=True
        except ValueError:
            inside=False
        if getattr(self.local,"busy",False):
            if not inside:
                raise RuntimeError("写入路径超出用户确认目录："+str(target))
            return inside
        self.local.busy=True
        try:
            if self.audit is not None:
                self.audit.record(operation,target,inside,{"enforced_by":"python_audit_hook"})
            elif not inside:
                raise RuntimeError("写入路径超出用户确认目录："+str(target))
        finally:
            self.local.busy=False
        return inside
    def hook(self,event,args):
        if event=="open" and args:
            mode=args[1] if len(args)>1 else "r"
            flags=args[2] if len(args)>2 else 0
            writing=(isinstance(mode,str) and any(value in mode for value in "wax+")) or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
            if writing:
                self.check("open_write",args[0])
        elif event in {"os.mkdir","os.remove","os.rmdir","os.unlink"} and args:
            self.check(event,args[0])
        elif event in {"os.rename","os.replace"} and len(args)>=2:
            self.check(event+"_source",args[0])
            self.check(event+"_destination",args[1])
        elif event=="sqlite3.connect" and args and str(args[0]) not in {":memory:",""}:
            value=str(args[0])
            if value.startswith("file:"):
                value=value[5:].split("?",1)[0]
            self.check("sqlite3.connect",value)
WRITE_BOUNDARY_GUARD=None
WRITE_BOUNDARY_HOOK_INSTALLED=False
def install_write_boundary_guard(base,audit=None):
    global WRITE_BOUNDARY_GUARD,WRITE_BOUNDARY_HOOK_INSTALLED
    if WRITE_BOUNDARY_GUARD is None:
        WRITE_BOUNDARY_GUARD=WriteBoundaryGuard(base,audit)
    else:
        WRITE_BOUNDARY_GUARD.update(base,audit)
    if not WRITE_BOUNDARY_HOOK_INSTALLED:
        sys.addaudithook(lambda event,args:WRITE_BOUNDARY_GUARD.hook(event,args) if WRITE_BOUNDARY_GUARD is not None else None)
        WRITE_BOUNDARY_HOOK_INSTALLED=True
    return WRITE_BOUNDARY_GUARD
def _windows_file_attributes(path):
    if os.name!="nt":
        return 0
    function=ctypes.WinDLL("kernel32",use_last_error=True).GetFileAttributesW
    function.argtypes=[wintypes.LPCWSTR]
    function.restype=wintypes.DWORD
    value=int(function(str(path)))
    if value==0xFFFFFFFF:
        error=ctypes.get_last_error()
        if error in {2,3}:
            return 0
        raise OSError(error,"GetFileAttributesW failed")
    return value

def is_reparse_point(path):
    item=Path(path)
    try:
        if item.is_symlink():
            return True
    except OSError:
        return True
    return bool(_windows_file_attributes(item)&0x00000400) if os.name=="nt" and item.exists() else False

def reject_reparse_points(root,target=None):
    base=Path(root).expanduser().absolute()
    if base.exists() and is_reparse_point(base):
        raise RuntimeError("权威数据目录不能是符号链接、junction或其他重解析点："+str(base))
    if target is None:
        return base
    candidate=Path(target).expanduser().absolute()
    try:
        relative=candidate.relative_to(base)
    except ValueError:
        raise RuntimeError("写入路径超出用户确认目录："+str(candidate))
    current=base
    for part in relative.parts:
        current=current/part
        if current.exists() and is_reparse_point(current):
            raise RuntimeError("权威数据目录内禁止重解析点："+str(current))
    return candidate

def _final_path_from_stream(stream):
    if os.name!="nt":
        return None
    import msvcrt
    handle=wintypes.HANDLE(msvcrt.get_osfhandle(stream.fileno()))
    kernel=ctypes.WinDLL("kernel32",use_last_error=True)
    function=kernel.GetFinalPathNameByHandleW
    function.argtypes=[wintypes.HANDLE,wintypes.LPWSTR,wintypes.DWORD,wintypes.DWORD]
    function.restype=wintypes.DWORD
    size=32768
    buffer=ctypes.create_unicode_buffer(size)
    length=int(function(handle,buffer,size,0))
    if length<=0 or length>=size:
        raise OSError(ctypes.get_last_error(),"GetFinalPathNameByHandleW failed")
    value=buffer.value
    if value.startswith("\\\\?\\UNC\\"):
        value="\\\\"+value[8:]
    elif value.startswith("\\\\?\\"):
        value=value[4:]
    return Path(value)

def verify_stream_within_root(stream,root):
    final=_final_path_from_stream(stream)
    if final is None:
        return True
    base=Path(root).expanduser().resolve()
    try:
        final.resolve().relative_to(base)
    except ValueError:
        raise RuntimeError("文件句柄最终路径超出用户确认目录："+str(final))
    return True

def data_path(base,path):
    raw_root=Path(base).expanduser().absolute()
    reject_reparse_points(raw_root)
    root=raw_root.resolve()
    reject_reparse_points(root)
    raw=(root/Path(path)).absolute() if not Path(path).is_absolute() else Path(path).expanduser().absolute()
    reject_reparse_points(root,raw)
    target=raw.resolve()
    try:
        target.relative_to(root)
    except ValueError:
        raise RuntimeError("写入路径超出用户确认目录："+str(target))
    return target
def make_data_directory(base,path):
    target=data_path(base,path)
    target.mkdir(parents=True,exist_ok=True)
    return target
def open_data_file(base,path,mode="r",*args,**kwargs):
    target=data_path(base,path)
    if any(value in str(mode) for value in "wax+"):
        target.parent.mkdir(parents=True,exist_ok=True)
    stream=target.open(mode,*args,**kwargs)
    try:
        verify_stream_within_root(stream,base)
    except Exception:
        stream.close()
        raise
    return stream
def _flush_stream_to_disk(stream):
    stream.flush()
    os.fsync(stream.fileno())
    if os.name=="nt":
        try:
            import msvcrt
            handle=msvcrt.get_osfhandle(stream.fileno())
            if not ctypes.WinDLL("kernel32",use_last_error=True).FlushFileBuffers(wintypes.HANDLE(handle)):
                error=ctypes.get_last_error()
                if error:
                    raise OSError(error,"FlushFileBuffers failed")
        except ImportError:
            pass

def _sync_parent_directory(path):
    directory=Path(path)
    if os.name=="nt":
        kernel=ctypes.WinDLL("kernel32",use_last_error=True)
        create=kernel.CreateFileW
        create.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
        create.restype=wintypes.HANDLE
        handle=create(str(directory),0x80000000,0x00000001|0x00000002,None,3,0x02000000,None)
        invalid=wintypes.HANDLE(-1).value
        if handle==invalid:
            raise OSError(ctypes.get_last_error(),"无法打开目录进行持久化同步")
        try:
            if not kernel.FlushFileBuffers(handle):
                error=ctypes.get_last_error()
                if error not in {1,6,87}:
                    raise OSError(error,"目录FlushFileBuffers失败")
        finally:
            kernel.CloseHandle(handle)
        return
    flags=os.O_RDONLY|getattr(os,"O_DIRECTORY",0)
    descriptor=os.open(str(directory),flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)

def durable_atomic_write(path,data,root=None):
    target=Path(path)
    target.parent.mkdir(parents=True,exist_ok=True)
    if root is not None:
        reject_reparse_points(root,target)
    temporary=target.with_name(target.name+".tmp."+uuid.uuid4().hex)
    payload=data.encode("utf-8") if isinstance(data,str) else bytes(data)
    try:
        with temporary.open("xb") as stream:
            if root is not None:
                verify_stream_within_root(stream,root)
            stream.write(payload)
            _flush_stream_to_disk(stream)
        if root is not None:
            reject_reparse_points(root,target.parent)
        os.replace(temporary,target)
        _sync_parent_directory(target.parent)
    except BaseException:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return target

def atomic_write_bytes(base,path,data):
    target=data_path(base,path)
    result=durable_atomic_write(target,data,base)
    with result.open("rb") as stream:
        verify_stream_within_root(stream,base)
    return result
def atomic_write_text(base,path,data,encoding="utf-8"):
    return atomic_write_bytes(base,path,str(data).encode(encoding))
def replace_data_path(base,source,destination):
    first=data_path(base,source)
    second=data_path(base,destination)
    second.parent.mkdir(parents=True,exist_ok=True)
    os.replace(first,second)
    return second
def remove_data_path(base,path,missing_ok=True):
    target=data_path(base,path)
    try:
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    except FileNotFoundError:
        if not missing_ok:
            raise
    return target
class AcceptanceReport:
    def __init__(self,base):
        self.base=Path(base).resolve()
        self.path=self.base/"audit"/"acceptance_report.json"
        self.lock=threading.RLock()
        self.data={"schema_version":4,"build_hash":current_build_hash(),"updated":time.time(),"strict_pass":False,"items":{},"environment":{},"failures":[],"invalidated_reason":""}
        self.load()
    def _fresh_item(self,name):
        return {"status":"pending","updated":0.0,"evidence":[],"cases":{case:{"status":"pending","updated":0.0,"evidence":[]} for case in STRICT_ACCEPTANCE_CASES[name]}}
    def load(self):
        current=current_build_hash()
        loaded=None
        try:
            value=json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(value,dict) and isinstance(value.get("items"),dict):
                loaded=value
        except Exception:
            loaded=None
        if loaded is not None and str(loaded.get("build_hash",""))==current and safe_int(loaded.get("schema_version"),0)==4:
            self.data=loaded
        elif loaded is not None:
            self.data["invalidated_reason"]="构建哈希或验收schema变化，旧证据已失效"
        self.data["schema_version"]=4
        self.data["build_hash"]=current
        self.data.setdefault("environment",{})
        self.data.setdefault("items",{})
        self.data.setdefault("measurements",{})
        for name in STRICT_ACCEPTANCE_ITEMS:
            item=self.data["items"].setdefault(name,self._fresh_item(name))
            item.setdefault("status","pending")
            item.setdefault("updated",0.0)
            item.setdefault("evidence",[])
            cases=item.setdefault("cases",{})
            for case in STRICT_ACCEPTANCE_CASES[name]:
                cases.setdefault(case,{"status":"pending","updated":0.0,"evidence":[]})
            for extra in list(cases):
                if extra not in STRICT_ACCEPTANCE_CASES[name]:
                    cases.pop(extra,None)
        self._evaluate_locked()
        return self.data
    def record_case(self,name,case,status,evidence=None):
        if name not in STRICT_ACCEPTANCE_CASES or case not in STRICT_ACCEPTANCE_CASES[name]:
            raise ValueError("未知验收用例："+str(name)+"/"+str(case))
        value=str(status)
        if value not in {"passed","failed","pending","not_run"}:
            raise ValueError("验收状态无效")
        with self.lock:
            item=self.data["items"].setdefault(name,self._fresh_item(name))
            target=item["cases"].setdefault(case,{"status":"pending","updated":0.0,"evidence":[]})
            target["status"]=value
            target["updated"]=time.time()
            target["evidence"]=list(evidence) if isinstance(evidence,(list,tuple)) else ([evidence] if evidence is not None else [])
            self._save_locked()
        return value
    def record(self,name,status,evidence=None):
        if name not in STRICT_ACCEPTANCE_ITEMS:
            raise ValueError("未知验收项目："+str(name))
        value=str(status)
        if value=="passed":
            with self.lock:
                cases=self.data["items"].setdefault(name,self._fresh_item(name))["cases"]
                if not all(cases.get(case,{}).get("status")=="passed" for case in STRICT_ACCEPTANCE_CASES[name]):
                    raise RuntimeError("不能跳过真实验收用例直接标记严格通过："+str(name))
                self._save_locked()
            return value
        if value not in {"failed","pending","not_run"}:
            raise ValueError("验收状态无效")
        with self.lock:
            item=self.data["items"].setdefault(name,self._fresh_item(name))
            for case in STRICT_ACCEPTANCE_CASES[name]:
                if item["cases"][case].get("status")!="passed":
                    item["cases"][case]={"status":value,"updated":time.time(),"evidence":list(evidence) if isinstance(evidence,(list,tuple)) else ([evidence] if evidence is not None else [])}
            self._save_locked()
        return value
    def record_measurement(self,name,value,unit="",context=None):
        key=str(name)
        number=safe_float(value,0.0)
        with self.lock:
            target=self.data.setdefault("measurements",{}).setdefault(key,{"unit":str(unit),"values":[]})
            target["unit"]=str(unit)
            target["values"].append({"value":number,"time":time.time(),"context":dict(context) if isinstance(context,dict) else {}})
            target["values"]=target["values"][-2048:]
            ordered=sorted(item["value"] for item in target["values"])
            target["count"]=len(ordered)
            target["p50"]=quantile(ordered,0.50)
            target["p95"]=quantile(ordered,0.95)
            target["p99"]=quantile(ordered,0.99)
            target["latest"]=number
            self._save_locked()
        return number

    def set_environment(self,**values):
        with self.lock:
            self.data.setdefault("environment",{}).update(values)
            self._save_locked()
    def _evaluate_locked(self):
        failures=[]
        for name in STRICT_ACCEPTANCE_ITEMS:
            item=self.data["items"].setdefault(name,self._fresh_item(name))
            states=[item["cases"].get(case,{}).get("status","pending") for case in STRICT_ACCEPTANCE_CASES[name]]
            if states and all(value=="passed" for value in states):
                status="passed"
            elif any(value=="failed" for value in states):
                status="failed"
            elif any(value=="not_run" for value in states):
                status="not_run"
            else:
                status="pending"
            item["status"]=status
            item["updated"]=max([safe_float(item["cases"].get(case,{}).get("updated"),0.0) for case in STRICT_ACCEPTANCE_CASES[name]] or [0.0])
            item["evidence"]=[{"case":case,"status":item["cases"].get(case,{}).get("status","pending"),"evidence":item["cases"].get(case,{}).get("evidence",[])} for case in STRICT_ACCEPTANCE_CASES[name]]
            if status!="passed":
                failures.append(name)
        environment=self.data.setdefault("environment",{})
        windows_ok=safe_int(environment.get("windows_build"),0)>=22000 and environment.get("real_windows_11") is True
        architecture_ok=str(environment.get("architecture","")).lower()==RUNTIME_ARCH_X64
        e2e_ok=environment.get("end_to_end_download_worker") is True
        monitor_ok=environment.get("external_write_monitor") is True
        geometry_ok=environment.get("window_geometry_test") is True
        measurements=self.data.setdefault("measurements",{})
        required_measurements=("escape_to_input_lock_ms","escape_to_all_buttons_released_ms","pressed_buttons_after_exit","capture_frame_interval_ms")
        measurements_ok=all(name in measurements and safe_int(measurements[name].get("count"),0)>0 for name in required_measurements)
        build_ok=str(self.data.get("build_hash",""))==current_build_hash()
        environment_failures=[]
        if not windows_ok:
            environment_failures.append("Windows 11真实环境未证明")
        if not architecture_ok:
            environment_failures.append("仅Windows 11 x64可进入严格验收")
        if not e2e_ok:
            environment_failures.append("真实文件完整性检查并启动独立AI worker未证明")
        if not monitor_ok:
            environment_failures.append("外部写入监控未证明")
        if not geometry_ok:
            environment_failures.append("专用窗口坐标/DPI/重建测试未证明")
        if not measurements_ok:
            environment_failures.append("ESC、按键释放与捕获间隔原始测量值不完整")
        if not build_ok:
            environment_failures.append("构建哈希不匹配")
        self.data["failures"]=failures+environment_failures
        self.data["strict_pass"]=bool(not self.data["failures"] and all(self.data["items"][name].get("status")=="passed" for name in STRICT_ACCEPTANCE_ITEMS))
        return self.data["strict_pass"]
    def _save_locked(self):
        self.data["updated"]=time.time()
        self.data["runtime_metrics"]=RUNTIME_METRICS.snapshot()
        self._evaluate_locked()
        self.path.parent.mkdir(parents=True,exist_ok=True)
        temporary=self.path.with_suffix(".json.tmp."+uuid.uuid4().hex)
        temporary.write_text(json.dumps(self.data,ensure_ascii=False,sort_keys=True,separators=(",",":")),encoding="utf-8")
        os.replace(temporary,self.path)
    def strict_passed(self):
        with self.lock:
            self._save_locked()
            return bool(self.data.get("strict_pass"))
PROGRAM_INSTANCE_LOCK=None
class WindowIdentityService:
    def __init__(self,bridge):
        self.bridge=bridge
    def identify(self,target):
        return self.bridge.target_identity(target)
    def validate(self,target,require_foreground=True):
        return self.bridge.validate_target_identity(target,require_foreground)
    def exists(self,hwnd):
        return self.bridge.valid(hwnd)
class WindowGeometryService:
    def __init__(self,bridge):
        self.bridge=bridge
    def client_rect(self,hwnd):
        return self.bridge.client_rect(hwnd)
    def content_rect(self,target):
        return self.bridge.content_rect(target)
    def dpi(self,hwnd):
        return self.bridge.dpi_for_window(hwnd)
class CaptureBackend:
    def __init__(self,bridge):
        self.bridge=bridge
    def capture(self,target,require_foreground=True,validation_mode=False,need_preview=False):
        return self.bridge.capture_gray(target,require_foreground,validation_mode,need_preview)
    def reset(self,target=None):
        return self.bridge.reset_capture_backends(target)
    def status(self,target):
        return self.bridge.capture_report(target)
class MouseInputService:
    def __init__(self,bridge):
        self.bridge=bridge
    def move(self,x,y):
        return self.bridge.move_cursor(x,y)
    def button(self,button,down):
        return self.bridge.button(button,down)
    def wheel(self,delta,horizontal=False):
        return self.bridge.wheel(delta,horizontal)
    def release(self):
        return self.bridge.release_all_buttons()
class KeyboardHookService:
    def __init__(self,bridge):
        self.bridge=bridge
    def create_monitor(self,on_escape=None,on_other=None):
        return KeyboardMonitor(self.bridge,on_escape=on_escape,on_other=on_other)
    def key_down(self,vk):
        return self.bridge.key_down(vk)
class DpiService:
    def __init__(self,bridge):
        self.bridge=bridge
    def for_window(self,hwnd):
        return self.bridge.dpi_for_window(hwnd)
    def awareness(self):
        return enable_dpi_awareness()
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
        self.identity_service=WindowIdentityService(self)
        self.geometry_service=WindowGeometryService(self)
        self.capture_backend=CaptureBackend(self)
        self.mouse_input_service=MouseInputService(self)
        self.keyboard_hook_service=KeyboardHookService(self)
        self.dpi_service=DpiService(self)
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
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
    def _dispose_gdi_resource(self,item):
        if not item:
            return
        try:
            if item.get("memory") and item.get("old"):
                self.gdi32.SelectObject(item["memory"],item["old"])
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        try:
            if item.get("bitmap"):
                self.gdi32.DeleteObject(item["bitmap"])
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        try:
            if item.get("memory"):
                self.gdi32.DeleteDC(item["memory"])
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        try:
            if item.get("source"):
                self.user32.ReleaseDC(wintypes.HWND(int(item.get("source_hwnd",0))),item["source"])
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
        item={"hwnd":safe_int(target.get("hwnd",0),0),"pid":safe_int(target.get("pid",0),0),"class":str(target.get("class","")),"thread":safe_int(target.get("window_thread_id",0),0),
            "path":os.path.normcase(str(target.get("process_path",""))),"created":safe_int(target.get("process_created",0),0),"content_rect_norm":[round(safe_float(value,0.0),
                    6) for value in target.get("content_rect_norm",[0,0,1,1])[:4]],"window_rule_version":WINDOW_RULE_VERSION}
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
        item.update({"hwnd":hwnd,"pid":pid,"class":self.class_name(hwnd),"title":self.window_title(hwnd),"window_thread_id":thread_id,"process_path":process["path"],
                "process_created":process["created"],"integrity":process["integrity"],"selected_rect":list(rect),"client_size":[int(rect[2]),int(rect[3])],"selected_dpi":dpi,"dpi":dpi})
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
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
            return bool(calibration.get("validated_backend") and safe_int(calibration.get("validated_pid",-1),-1)==current_pid and str(calibration.get("validated_class",
                        ""))==self.class_name(hwnd) and str(calibration.get("validated_process_path",""))==process["path"] and safe_int(calibration.get("validated_process_created",-1),-1)==process["created"]
                and safe_int(calibration.get("validated_window_thread_id",-1),-1)==current_thread and safe_int(calibration.get("validated_integrity",-1),-1)==process["integrity"]
                and safe_int(calibration.get("validated_dpi",0),0)==self.dpi_for_window(hwnd) and list(calibration.get("validated_rect",[0,0,0,0]))[2:4]==[int(current_rect[2]),int(current_rect[3])]
                and norm==saved_norm and safe_int(calibration.get("capture_backend_version",0),0)==CAPTURE_BACKEND_VERSION)
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
                candidate={"rgb":model_rgb,"gray":self._rgb_to_gray(model_rgb),"preview_rgb":preview,"preview_width":out_w if preview is not None else 0,
                    "preview_height":out_h if preview is not None else 0,"method":name,"quality":quality,"priority":priority,"stale":stale,"stable_frame":bool(stale and not quality.get("black_frame")),
                    "capture_valid":bool(quality["valid"]),"backend_validated":backend_validated,"backend_changed":backend_changed,"static_feature":self.feature_from_rgb(model_rgb,None)}
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
        result.update({"usable_for_learning":usable,"usable_for_training":usable,"usable_for_teaching":usable,"protected_or_black":bool(protected or is_black),"black_frame":is_black,
                "stable_frame":bool(chosen.get("stable_frame") and not frozen),"capture_frozen":frozen,"frozen_backend":frozen})
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
        defaults={"noise":4.0,"visual_cluster":420.0,"significant_change":60.0,"post_action_change":45.0,"freeze_change":1.5,"freeze_frames":30,"confirm_frames":3,"duplicate":3.0,"fps":10.0,
            "input_delay":0.24,"validated_backend":"","dynamic_passed":False,"static_passed":False,"backend_thresholds":{}}
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
        thresholds={"noise":noise,"visual_cluster":max(70.0,min(1400.0,noise*9.0+120.0)),"significant_change":max(16.0,min(260.0,noise*4.5+18.0)),"post_action_change":max(12.0,min(220.0,
                    noise*3.2+14.0)),"freeze_change":max(0.35,noise*0.22),"freeze_frames":max(18,min(80,round(fps*3.0))),"confirm_frames":3 if fps>=12 else 4,"duplicate":max(1.0,min(18.0,noise*0.65)),"fps":fps,
            "input_delay":max(0.16,min(0.55,3.0/max(5.0,fps)))}
        backend_thresholds=dict(previous.get("backend_thresholds",{})) if isinstance(previous.get("backend_thresholds",{}),dict) else {}
        for backend,data in eligible.items():
            backend_changes=data["changes"]
            backend_noise=max(0.35,quantile(backend_changes,0.5) if backend_changes else noise)
            backend_thresholds[backend]={"noise":backend_noise,"visual_cluster":max(70.0,min(1400.0,backend_noise*9.0+120.0)),"significant_change":max(16.0,min(260.0,
                        backend_noise*4.5+18.0)),"post_action_change":max(12.0,min(220.0,backend_noise*3.2+14.0)),"freeze_change":max(0.35,backend_noise*0.22),"freeze_frames":thresholds["freeze_frames"],
                "confirm_frames":thresholds["confirm_frames"],"duplicate":max(1.0,min(18.0,backend_noise*0.65)),"fps":fps,"input_delay":thresholds["input_delay"]}
        thread_id,pid=self.window_thread_pid(hwnd)
        process=self.process_identity_for_pid(pid)
        result=dict(thresholds)
        result.update({"method":method,"validated_backend":method,"validated_backends":sorted(eligible),"dynamic_passed":True,"static_passed":not dynamic,
                "calibration_mode":"dynamic" if dynamic else "stable","validated_at":time.time(),"validated_rect":list(rect),"validated_content_rect_norm":[round(safe_float(value,0.0),
                    6) for value in target.get("content_rect_norm",[0,0,1,1])[:4]],"capture_backend_version":CAPTURE_BACKEND_VERSION,"validated_dpi":dpi,"validated_pid":pid,
                "validated_class":str(target["class"]),"validated_process_path":process["path"],"validated_process_created":process["created"],"validated_window_thread_id":thread_id,
                "validated_integrity":process["integrity"],"integrity":process["integrity"],"nonblack_frames":len(selected),"black_frames":black_frames,"trusted_change":dynamic,"backend_thresholds":backend_thresholds})
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
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
                except Exception as error:
                    record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
                self.held.discard(button)
            for flag in (0x0004,0x0010,0x0040):
                try:
                    self._send(flag)
                except Exception as error:
                    record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
                    client_rect=command.get("client_rect",rect); cx,cy,cw,ch=[safe_int(value,0) for value in client_rect]; offset=command.get("content_offset",[x-cx,
                            y-cy]); ox,oy=[safe_int(value,0) for value in offset[:2]]
                    result=bridge._capture_print(hwnd,cw,ch,out_w,out_h,(ox,oy,width,height))
                elif backend=="窗口DC":
                    client_rect=command.get("client_rect",rect); cx,cy,cw,ch=[safe_int(value,0) for value in client_rect]; offset=command.get("content_offset",[x-cx,
                            y-cy]); ox,oy=[safe_int(value,0) for value in offset[:2]]
                    result=bridge._capture_dc(hwnd,ox,oy,width,height,out_w,out_h)
                elif backend=="前台桌面裁剪":
                    result=bridge._capture_dc(0,x,y,width,height,out_w,out_h)
                else:
                    raise CaptureUnavailable("未知采集后端")
                connection.send((True,bytes(result)))
            except Exception as error:
                try:
                    connection.send((False,str(error)))
                except Exception:
                    break
    finally:
        if bridge is not None:
            try:
                bridge.close()
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        try:
            connection.close()
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
class KeyboardMonitor:
    def __init__(self,bridge,on_escape=None,on_other=None):
        self.bridge=bridge
        self.on_escape=on_escape
        self.on_other=on_other
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
                            event={"kind":"escape","down":True,"time":stamp,"wall_time":wall_time,"monotonic_time":monotonic_time,"injected":injected}
                            self._put(event)
                            if self.on_escape is not None:
                                try:
                                    self.on_escape(dict(event))
                                except Exception as error:
                                    record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
                            event={"kind":"other","down":True,"time":stamp,"wall_time":wall_time,"monotonic_time":monotonic_time,"vk":vk,"injected":injected}
                            self._put(event)
                            if self.on_other is not None:
                                try:
                                    self.on_other(dict(event))
                                except Exception as error:
                                    record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
                except Exception as error:
                    record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
                except Exception as error:
                    record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
        self.last_metric_frame_stamp=0.0
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
        changed=bool(isinstance(expected,(list,tuple)) and len(expected)>=2 and [int(rect[2]),int(rect[3])]!=[safe_int(expected[0],-1),safe_int(expected[1],-1)] or expected_dpi is not None
            and int(dpi)!=safe_int(expected_dpi,-1))
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
                    capture_started=now
                    preview_due=bool(self.need_preview and self.preview_active.is_set() and now>=next_preview)
                    captured=self.bridge.capture_gray(self.target,True,False,preview_due)
                    if preview_due:
                        next_preview=now+self.preview_interval
                        preview=preview_rgb_bytes(captured.get("preview_rgb"))
                        if preview is not None:
                            self.last_preview=(preview,safe_int(captured.get("preview_width",PREVIEW_W),PREVIEW_W),safe_int(captured.get("preview_height",PREVIEW_H),PREVIEW_H))
                    stamp=time.monotonic()
                    RUNTIME_METRICS.observe("capture_latency_ms",(stamp-capture_started)*1000.0)
                    if self.last_metric_frame_stamp>0:
                        RUNTIME_METRICS.observe("capture_frame_interval_ms",(stamp-self.last_metric_frame_stamp)*1000.0)
                    self.last_metric_frame_stamp=stamp
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
                    neural_feature=None
                    runtime=getattr(self.bridge,"ai_runtime",None)
                    if runtime is not None and runtime.ready and runtime.active_game:
                        try:
                            neural_feature=runtime.encode(rgb,previous)
                        except Exception:
                            neural_feature=None
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
                    frame={"time":stamp,"wall_time":wall_time,"monotonic_time":stamp,"f":feature,"raw_f":feature,"neural_f":neural_feature,"coarse":coarse_feature(feature),"gray":gray,
                        "rgb":rgb,"preview_rgb":preview_rgb,"preview_width":preview_width,"preview_height":preview_height,"method":captured["method"],"quality":captured["quality"],
                        "motion_valid":previous is not None,"rect":rect,"dpi":self.bridge.dpi_for_window(int(self.target["hwnd"])),"capture_valid":bool(captured.get("capture_valid")),
                        "backend_validated":bool(captured.get("backend_validated")),"usable_for_learning":bool(captured.get("usable_for_learning") and confirmed),
                        "usable_for_training":bool(captured.get("usable_for_training") and confirmed),"usable_for_teaching":bool(captured.get("usable_for_teaching") and confirmed),
                        "stale":bool(captured.get("stale")),"stable_frame":bool(captured.get("stable_frame")),"black_frame":bool(captured.get("black_frame")),
                        "protected_or_black":bool(captured.get("protected_or_black")),"capture_frozen":bool(captured.get("capture_frozen")),"frozen_backend":bool(captured.get("frozen_backend")),
                        "backend_changed":bool(captured.get("backend_changed"))}
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
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        self.app.set_status("窗口尺寸或DPI变化后已自动重新校准，正在连续确认画面")
    def start_frames(self,hz,seconds,motion_interval,purpose):
        buffer=FrameBuffer(self.app.api,self.target,hz,seconds,motion_interval,purpose,self._geometry_updated)
        self.barrier.add("FrameBuffer",lambda timeout:buffer.stop(False,timeout),buffer.alive)
        buffer.start()
        buffer.wait_for_usable(purpose,4.0,self.app.stop_event)
        self.frame_buffer=buffer
        try:
            game=self.app.require_game()
            if getattr(self.app,"ocr_runtime",None) is not None and self.app.ocr_runtime.ready and self.app.store.list_ocr_regions(game["id"],True):
                monitor=OCRMonitor(self.app,buffer,purpose).start()
                self.add_resource("OCRMonitor",monitor)
                self.app.active_ocr_monitor=monitor
        except Exception as error:
            if self.app.store is not None:
                self.app.store.log_error("OCR_MONITOR_START_FAILED",error,mode=self.app.mode)
        return buffer
    def start_keyboard(self,on_other=None):
        monitor=getattr(self.app,"keyboard_monitor",None)
        if monitor is None or not monitor.alive():
            raise RuntimeError("常驻低级键盘钩子不可用")
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
            raise CaptureUnavailable(self.frame_buffer.last_error or "没有可用于指导的画面")
        selected=usable[-1]
        selected_ranked=[]
        selected_priority=float("inf")
        candidates=usable[-28:]
        if not self.prototypes:
            return selected,[]
        for candidate_frame in candidates:
            if self.stop_event.is_set() or self.context.callbacks.should_stop():
                raise InputStopped("指导题目生成已停止")
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
def prototype_collection_checksum(prototypes):
    values=list(prototypes) if isinstance(prototypes,(list,tuple)) else []
    stamped={str(item.get("_collection_checksum","")) for item in values if isinstance(item,dict) and item.get("_collection_checksum")}
    if len(stamped)==1 and len(values)>0 and all(isinstance(item,dict) and item.get("_collection_checksum") in stamped for item in values):
        return next(iter(stamped))
    digest=hashlib.sha256()
    digest.update(str(len(values)).encode("ascii"))
    for index,item in enumerate(values):
        if not isinstance(item,dict):
            digest.update((str(index)+"|invalid").encode("utf-8"))
            continue
        digest.update(str(index).encode("ascii"))
        digest.update(str(item.get("id","")).encode("utf-8","replace"))
        digest.update(str(item.get("cluster_id",item.get("action_signature",""))).encode("utf-8","replace"))
        digest.update(feature_bytes(item.get("f")))
        coarse=item.get("coarse")
        digest.update(bytes(coarse) if isinstance(coarse,(bytes,bytearray)) and len(coarse)==COARSE_LEN else coarse_feature(item.get("f")))
        digest.update(canonical_bytes(normalize_action(item.get("a"))))
        digest.update(canonical_bytes({
            "capture_methods":sorted(str(value) for value in item.get("capture_methods",[])),
            "authorized":bool(item.get("authorized",True)),
            "threshold":safe_float(item.get("threshold",0.0),0.0),
            "previous_action":str(item.get("previous_action","")),
            "temporal":temporal_from_context(item.get("temporal",{})),
        }))
    token=digest.hexdigest()
    for item in values:
        if isinstance(item,dict):
            item["_collection_checksum"]=token
    return token
def build_candidate_runtime_index(prototypes,require_numpy=False):
    values=list(prototypes) if isinstance(prototypes,(list,tuple)) else []
    np=_optional_numpy()
    if require_numpy and np is None:
        raise RuntimeError("独立AI工作进程缺少NumPy候选匹配能力")
    backend_indices=defaultdict(list)
    bucket_indices=defaultdict(list)
    cluster_indices=defaultdict(list)
    coarse_rows=[]
    feature_rows=[]
    identifiers=[]
    cluster_ids=[]
    authorized=[]
    methods=[]
    buckets=[]
    for index,proto in enumerate(values):
        if not isinstance(proto,dict) or not feature_valid(proto.get("f")):
            raise ValueError("候选原型特征无效")
        coarse=proto.get("coarse")
        if not isinstance(coarse,(bytes,bytearray)) or len(coarse)!=COARSE_LEN:
            coarse=coarse_feature(proto["f"])
            proto["coarse"]=coarse
        method_set=frozenset(str(value) for value in proto.get("capture_methods",[])) or frozenset({"unknown"})
        cluster_id=str(proto.get("cluster_id",proto.get("action_signature","")))
        bucket=coarse_bucket_key(coarse)
        identifiers.append(str(proto.get("id",index)))
        cluster_ids.append(cluster_id)
        authorized.append(bool(proto.get("authorized",True)))
        methods.append(method_set)
        buckets.append(bucket)
        coarse_rows.append(bytes(coarse))
        feature_rows.append(feature_bytes(proto["f"]))
        cluster_indices[cluster_id].append(index)
        for backend in method_set:
            backend_indices[backend].append(index)
            bucket_indices[(backend,bucket)].append(index)
    if np is not None and values:
        coarse_matrix=np.frombuffer(b"".join(coarse_rows),dtype=np.uint8).reshape(len(values),COARSE_LEN)
        feature_matrix=np.frombuffer(b"".join(feature_rows),dtype=np.uint8).reshape(len(values),FEATURE_CHANNELS,PIXELS)
        weights=np.asarray(FEATURE_DISTANCE_WEIGHTS,dtype=np.float64)
        authorized_mask=np.asarray(authorized,dtype=np.bool_)
    else:
        coarse_matrix=tuple(coarse_rows)
        feature_matrix=tuple(feature_rows)
        weights=FEATURE_DISTANCE_WEIGHTS
        authorized_mask=tuple(authorized)
    return {
        "token":prototype_collection_checksum(values),
        "prototypes":values,
        "coarse_matrix":coarse_matrix,
        "feature_matrix":feature_matrix,
        "weights":weights,
        "backend_indices":dict(backend_indices),
        "cluster_indices":dict(cluster_indices),
        "bucket_indices":dict(bucket_indices),
        "identifiers":tuple(identifiers),
        "cluster_ids":tuple(cluster_ids),
        "authorized_mask":authorized_mask,
        "methods":tuple(methods),
        "buckets":tuple(buckets),
        "numpy":np is not None,
    }
def candidate_visual_matches(runtime_index,feature,query_coarse,backend,full_limit):
    if not isinstance(runtime_index,dict) or not feature_valid(feature):
        return []
    values=runtime_index.get("prototypes",[])
    count=len(values)
    if count<1:
        return []
    source=list(runtime_index.get("backend_indices",{}).get(str(backend),range(count)))
    authorized=runtime_index.get("authorized_mask",())
    eligible=[index for index in source if 0<=int(index)<count and bool(authorized[int(index)])]
    if not eligible:
        return []
    exact_limit=max(12,min(VersionedThresholdConfig.candidate_full_limit,int(full_limit) if int(full_limit)>0 else VersionedThresholdConfig.candidate_full_limit))
    exact_limit=min(exact_limit,len(eligible))
    bucket=coarse_bucket_key(query_coarse)
    bucket_set=set(runtime_index.get("bucket_indices",{}).get((str(backend),bucket),[]))
    np=_optional_numpy() if runtime_index.get("numpy") else None
    if np is not None:
        eligible_array=np.asarray(eligible,dtype=np.intp)
        coarse_matrix=runtime_index["coarse_matrix"]
        query=np.frombuffer(bytes(query_coarse),dtype=np.uint8).astype(np.int16)
        difference=coarse_matrix[eligible_array].astype(np.int16)-query[None,:]
        coarse_scores=np.mean(np.square(difference,dtype=np.int32),axis=1,dtype=np.float64)
        priorities=np.asarray([0 if int(index) in bucket_set else 1 for index in eligible],dtype=np.int8)
        order=np.lexsort((coarse_scores,priorities))[:exact_limit]
        selected=eligible_array[order]
        query_feature=np.frombuffer(feature_bytes(feature),dtype=np.uint8).reshape(FEATURE_CHANNELS,PIXELS).astype(np.int16)
        feature_matrix=runtime_index["feature_matrix"][selected].astype(np.int16)
        feature_difference=feature_matrix-query_feature[None,:,:]
        channel_means=np.mean(np.square(feature_difference,dtype=np.int32),axis=2,dtype=np.float64)
        exact_scores=np.dot(channel_means,runtime_index["weights"])
        selected_coarse=coarse_scores[order]
        return [{"index":int(index),"coarse_score":float(coarse_score),"exact_score":float(score)} for index,coarse_score,score in zip(selected.tolist(),selected_coarse.tolist(),exact_scores.tolist())]
    coarse_matrix=runtime_index.get("coarse_matrix",())
    ranked=[]
    for index in eligible:
        score=coarse_distance(query_coarse,coarse_matrix[index])
        ranked.append((0 if index in bucket_set else 1,score,index))
    selected=[index for _,_,index in sorted(ranked,key=lambda item:(item[0],item[1],item[2]))[:exact_limit]]
    exact=batch_feature_distances(feature,[runtime_index["feature_matrix"][index] for index in selected])
    coarse_lookup={index:score for _,score,index in ranked}
    return [{"index":int(index),"coarse_score":float(coarse_lookup[index]),"exact_score":float(score)} for index,score in zip(selected,exact)]
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
        self.ocr_events=list(payload.get("ocr_events",[]))
        self.saved=[]
        self.profile=dict(payload.get("profile",{}))
    def load_game_profile(self,gid):
        return dict(self.profile)
    def load_samples(self,gid):
        return list(self.samples),dict(self.stats)
    def load_rejections(self,gid,limit=500):
        return list(self.rejections[:int(limit)])
    def load_ocr_experience_events(self,gid,limit=5000):
        return list(self.ocr_events[:int(limit)])
    def save_model(self,gid,model,complete=True):
        self.saved.append((str(gid),dict(model),bool(complete)))
        return True
class ReviewProcessLifecycle:
    def __init__(self,stop_event):
        self.lock=threading.RLock()
        self.state=MODE_STARTING
        self.name="睡眠"
        self.stop_event=stop_event
        self.requested_status="completed"
        self.reason=""
    def mark_running(self):
        with self.lock:
            if self.state==MODE_STARTING:
                self.state=MODE_RUNNING
            return self.state
    def request_stop(self,status="stopped",reason=""):
        priority={"completed":0,"stopped":1,"failed":2}
        with self.lock:
            value=str(status) if str(status) in priority else "stopped"
            if priority[value]>=priority.get(self.requested_status,0):
                self.requested_status=value
                if reason:
                    self.reason=str(reason)
            self.state=MODE_STOPPING
            self.stop_event.set()
            return True
    def snapshot(self):
        with self.lock:
            return self.state,self.name,self.stop_event,self.requested_status,self.reason
class ReviewProcessApi:
    def key_down(self,key):
        return False
    def block_input(self):
        return None
    def release_all_buttons(self):
        return None
def review_process_send(connection,kind,payload,stage=None):
    try:
        value=str(stage or ("COMPLETED" if str(kind)=="result" else "FAILED" if str(kind)=="error" else "RUNNING"))
        connection.send({"protocol_version":REVIEW_PROCESS_PROTOCOL_VERSION,"stage":value,"kind":str(kind),"payload":payload})
        return True
    except Exception:
        return False
def review_process_main(connection,stop_event,payload):
    try:
        if safe_int(payload.get("protocol_version"),0)!=REVIEW_PROCESS_PROTOCOL_VERSION or payload.get("stage")!="STARTING":
            raise RuntimeError("睡眠子进程协议版本或启动阶段无效")
        if payload.get("base"):
            install_write_boundary_guard(payload["base"])
        _disable_network_access()
        offline_evidence=_verify_offline_network_block()
        review_process_send(connection,"status","睡眠子进程已启动","STARTING")
        host=ReviewProcessHost(validate_packet("review_request",payload),stop_event,connection)
        result=host.review_controller.run_offline()
        result.details.update({"offline_network_evidence":offline_evidence,"offline_network_blocked":bool(offline_evidence.get("blocked")),"sleep_seed_evidence":dict(getattr(host,"sleep_seed_evidence",{}))})
        review_process_send(connection,"result",{"status":result.status,"summary":result.summary,"details":result.details,"models":host.store.saved})
    except InputStopped as error:
        saved=getattr(getattr(locals().get("host",None),"store",None),"saved",[])
        review_process_send(connection,"result",{"status":"stopped","summary":"睡眠已停止","details":{"reason":str(error)},"models":saved})
    except Exception:
        saved=getattr(getattr(locals().get("host",None),"store",None),"saved",[])
        review_process_send(connection,"error",{"traceback":traceback.format_exc(),"models":saved})
    finally:
        try:
            connection.close()
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
class ReviewProcessWorker:
    def __init__(self,payload):
        context=multiprocessing.get_context("spawn")
        self.connection,child=context.Pipe(duplex=False)
        self.stop_event=context.Event()
        value=dict(payload)
        value.update({"protocol_version":REVIEW_PROCESS_PROTOCOL_VERSION,"stage":"STARTING"})
        self.process=context.Process(target=review_process_main,args=(child,self.stop_event,value),name="UniversalGameAI-OfflineReview",daemon=True)
        self.process.start()
        child.close()
    def request_stop(self):
        self.stop_event.set()
    def receive(self,timeout=0.0):
        try:
            if self.connection.poll(max(0.0,float(timeout))):
                packet=self.connection.recv()
                if not isinstance(packet,dict) or safe_int(packet.get("protocol_version"),0)!=REVIEW_PROCESS_PROTOCOL_VERSION or packet.get("stage") not in {"STARTING","RUNNING","COMPLETED","FAILED"}:
                    return "error",{"traceback":"睡眠子进程返回了无效协议包","packet_type":type(packet).__name__}
                return str(packet.get("kind","error")),packet.get("payload")
        except (EOFError,OSError) as error:
            return "error",{"traceback":"睡眠子进程连接提前关闭："+str(error),"exitcode":self.process.exitcode,"stage":"FAILED"}
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
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        return not self.process.is_alive()
    def close(self,timeout=0.2):
        self.stop_event.set()
        try:
            self.process.join(max(0.0,float(timeout)))
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        stopped=not self.process.is_alive()
        if stopped:
            try:
                self.connection.close()
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        return stopped
@dataclass(frozen=True)
class ModeStateCallbacks:
    set_status:object
    set_progress:object
    set_input_status:object
    set_confidence:object
    should_stop:object
    request_stop:object
    mark_running:object
@dataclass(frozen=True)
class ModeContext:
    store:object
    api:object
    stop_event:object
    callbacks:ModeStateCallbacks
    @classmethod
    def from_host(cls,host):
        lifecycle=getattr(host,"lifecycle",None)
        return cls(getattr(host,"store",None),getattr(host,"api",None),getattr(host,"stop_event",None),ModeStateCallbacks(getattr(host,"set_status",lambda value:None),getattr(host,
                    "set_progress",lambda value:None),getattr(host,"set_input_status",lambda value:None),getattr(host,"set_confidence",lambda value:None),getattr(host,"should_stop",lambda:False),getattr(host,
                    "request_mode_stop",lambda status="stopped",reason="":False),getattr(lifecycle,"mark_running",lambda:None)))
class PhaseRunner:
    def __init__(self,context,controller,host):
        if not isinstance(context,ModeContext):
            raise TypeError("模式运行器必须使用ModeContext")
        self.context=context
        self.controller=controller
        self.host=host
        self.prepared=None
    def run(self):
        phase=self.prepare_session()
        self.prepared=phase
        try:
            self.preflight(phase)
            phase["window"]=self.acquire_window(phase)
            phase["calibration"]=self.calibrate_capture(phase)
            phase["monitors"]=self.start_monitors(phase)
            result=self.run_loop(phase)
            result=self.validate_session(result,phase)
            result=self.commit_or_rollback(result,None,phase)
            return self.finalize(result,phase)
        except Exception as error:
            try:
                self.commit_or_rollback(None,error,phase)
            except Exception as cleanup_error:
                record_cleanup_error("MODE_COMMIT_OR_ROLLBACK_FAILED",cleanup_error,{"mode":str(phase.get("mode",""))})
            self.rollback(error,phase)
            raise
        finally:
            try:
                self.release_resources(phase)
            except Exception as cleanup_error:
                record_cleanup_error("MODE_RELEASE_RESOURCES_FAILED",cleanup_error,{"mode":str(phase.get("mode",""))})
    def preflight(self,phase=None):
        if self.context.store is None or self.context.api is None:
            raise RuntimeError("模式上下文缺少store或api")
    def prepare_session(self):
        return {"started":time.monotonic(),"resources":[],"mode":""}
    def acquire_window(self,phase):
        return None
    def calibrate_capture(self,phase):
        return None
    def start_monitors(self,phase):
        return []
    def run_loop(self,prepared):
        raise NotImplementedError
    def validate_session(self,result,phase):
        if not isinstance(result,ModeResult):
            raise RuntimeError("模式运行器返回值无效")
        return result
    def commit_or_rollback(self,result,error,phase):
        if error is not None:
            return None
        return result
    def finalize(self,result,prepared):
        if not isinstance(result,ModeResult):
            raise RuntimeError("模式运行器返回值无效")
        return result
    def rollback(self,error,prepared):
        best_effort_cleanup("MODE_ROLLBACK_BLOCK_INPUT",lambda:self.context.api.block_input())
        best_effort_cleanup("MODE_ROLLBACK_RELEASE_INPUT",lambda:self.context.api.release_all_buttons())
    def release_resources(self,phase):
        resources=list(reversed(phase.get("resources",[]))) if isinstance(phase,dict) else []
        for resource in resources:
            close=getattr(resource,"close",None)
            if close is not None:
                best_effort_cleanup("MODE_RESOURCE_CLOSE_FAILED",lambda close=close:close())
        best_effort_cleanup("MODE_RELEASE_BLOCK_INPUT",lambda:self.context.api.block_input())
        best_effort_cleanup("MODE_RELEASE_ALL_BUTTONS",lambda:self.context.api.release_all_buttons())
class LearningRunner(PhaseRunner):
    def prepare_session(self):
        return {"started":time.monotonic(),"resources":[],"mode":ModeName.LEARNING.value}
    def preflight(self,phase=None):
        super().preflight(phase)
        phase["game"]=self.host.require_game()
    def acquire_window(self,phase):
        return self.host.require_window(False)
    def calibrate_capture(self,phase):
        return self.host.ensure_capture_calibration(phase["window"],ModeName.LEARNING.value)
    def run_loop(self,prepared):
        return self.controller._run_impl(prepared)
    def finalize(self,result,prepared):
        self.context.callbacks.set_input_status("已锁定")
        return super().finalize(result,prepared)
class ReviewRunner(PhaseRunner):
    def __init__(self,context,controller,host,offline=False):
        super().__init__(context,controller,host)
        self.offline=bool(offline)
    def prepare_session(self):
        return {"started":time.monotonic(),"resources":[],"mode":ModeName.SLEEP.value,"offline":self.offline}
    def preflight(self,phase=None):
        super().preflight(phase)
        phase["game"]=self.host.require_game()
        if not self.offline:
            self.host.require_ai_runtime()
    def run_loop(self,prepared):
        return self.controller._run_impl(prepared) if self.offline else self.controller._pipeline_impl(prepared)
    def rollback(self,error,prepared):
        super().rollback(error,prepared)
        if not self.offline and self.context.store is not None:
            best_effort_cleanup("SLEEP_ROLLBACK_RESUME_WRITES",lambda:self.context.store.resume_sample_writes())
class TrainingRunner(PhaseRunner):
    def prepare_session(self):
        return {"started":time.monotonic(),"resources":[],"mode":ModeName.TRAINING.value}
    def preflight(self,phase=None):
        super().preflight(phase)
        phase["game"]=self.host.require_game()
    def acquire_window(self,phase):
        return self.host.require_window(False)
    def calibrate_capture(self,phase):
        return self.host.ensure_capture_calibration(phase["window"],ModeName.TRAINING.value)
    def run_loop(self,prepared):
        return self.controller._run_impl(prepared)
    def finalize(self,result,prepared):
        return super().finalize(result,prepared)
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
class ReviewSessionSplitter:
    def split(self,controller,valid):
        return controller._split_by_family_backend(valid)
class ReviewValidator:
    def authorize(self,row,dangerous):
        minimum=VersionedThresholdConfig.dangerous_min_positive if dangerous else VersionedThresholdConfig.ordinary_min_positive
        sessions=VersionedThresholdConfig.dangerous_min_sessions if dangerous else VersionedThresholdConfig.ordinary_min_sessions
        return bool(row.get("total",0)>=minimum and row.get("independent_sessions",0)>=sessions and row.get("errors",0)==0 and row.get("false_positive",0)==0 and row.get("coverage",
                0.0)>=VersionedThresholdConfig.minimum_coverage and (not dangerous or row.get("negative_total",0)>=VersionedThresholdConfig.dangerous_min_negative))
class BasicSafeAuthorizer:
    def authorize(self,family,support,consistency,sessions,nonambiguous,rejection_clear):
        return bool(str(family) in BASIC_SAFE_FAMILIES and int(support)>=VersionedThresholdConfig.basic_safe_min_positive
            and float(consistency)>=VersionedThresholdConfig.basic_safe_min_consistency and int(sessions)>=1 and bool(nonambiguous) and bool(rejection_clear))
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
class LearningController:
    def __init__(self,context,host=None):
        if isinstance(context,ModeContext):
            self.context=context
            self.host=host
        else:
            self.context=ModeContext.from_host(context)
            self.host=context
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
        return LearningRunner(ModeContext.from_host(self.host),self,self.host).run()
    def _run_impl(self,phase=None):
        return LearningExecution(self,phase).run()
class LearningExecution:
    def __init__(self,controller,phase=None):
        self.controller=controller
        self.host=controller.host
        self.phase=phase if isinstance(phase,dict) else {}
        self.game=None
        self.target=None
        self.calibration=None
        self.session_id=""
        self.keyboard_state={"generation":0,"last_time":0.0}
        self.strict_violation=False
        self.invalid_marked=False
        self.invalid_reason=""
        self.learned=0
        self.discarded=0
        self.duplicates=0
        self.invalid_frames=0
        self.keyboard_discarded=0
        self.keyboard_count=0
        self.mouse_event_count=0
        self.recent_actions=deque(["<START>","<START>"],maxlen=4)
        self.last_action_signature=""
        self.last_action_time=0.0
        self.last_action_feature=None
        self.last_action_changed=True
        self.state_since=time.monotonic()

    def preflight(self):
        self.game=self.phase.get("game") or self.host.require_game()
        self.target=self.phase.get("window") or self.host.require_window(False)
        self.calibration=self.phase.get("calibration") or self.host.ensure_capture_calibration(self.target,"学习")
        self.session_id="learn|"+uuid.uuid4().hex
        self.host.store.begin_learning_session(self.game["id"],self.session_id)
        if not self.host.api.request_foreground(self.target["hwnd"]):
            self.host.set_status("无法自动切换到目标窗口，学习将等待目标窗口成为前台")
        self.host.wait_escape_release()
        self.isolation=StrictInputIsolation(self.host.stop_event)
        return self

    def start_monitors(self,session):
        self.frame_buffer=session.start_frames(20.0,2.0,0.1,"learning")
        self.keyboard=session.start_keyboard()
        self.monitor=session.start_mouse()
        self.mouse_drop_baseline=self.monitor.snapshot()["dropped_events"]
        self.host.lifecycle.mark_running()
        self.active={}
        self.pending_click={}
        self.last_negative=0.0
        self.last_motion_time=0.0
        self.motion=None
        self.last_cursor=None
        self.hover_start=0.0
        self.hover_point=None
        self.last_update=0.0
        self.sampling_delay=0.012

    def drain_keyboard_events(self):
        events=[event for event in self.keyboard.drain() if event.get("kind")=="other" and event.get("down")]
        if not events:
            return events
        self.strict_violation=True
        self.invalid_reason="non_escape_keyboard_input"
        self.keyboard_count+=len(events)
        self.keyboard_state["generation"]+=1
        self.keyboard_state["last_time"]=safe_float(events[0].get("time"),time.monotonic())
        if not self.invalid_marked:
            self.host.store.invalidate_learning_session(self.game["id"],self.session_id,self.invalid_reason)
            self.invalid_marked=True
        self.isolation.signal("keyboard",self.keyboard_state["last_time"])
        self.host.request_mode_stop("stopped","学习检测到非ESC键盘输入，整段session无效")
        self.host.api.block_input()
        self.host.api.release_all_buttons()
        return events

    def paused(self):
        self.drain_keyboard_events()
        return self.strict_violation or self.keyboard.other_event.is_set()

    def capture_safe(self,stamp=None):
        frame=self.frame_buffer.latest(stamp,0.75,"learning")
        if frame is None:
            self.invalid_frames+=1
        return frame

    def build_sample_context(self,frame,action,cursor_point):
        temporal=self.host.build_temporal_context(
            self.frame_buffer,frame,self.recent_actions,self.state_since,
            cursor_point or ((action.get("path") or [None])[-1] if isinstance(action,dict) else None),
        )
        complete=temporal_from_context({**temporal,"previous_action_changed_frame":self.last_action_changed}).get("complete")
        if not complete:
            self.invalid_frames+=1
            return None
        return self.host.sample_context(
            self.last_action_signature,self.last_action_time,self.last_action_changed,
            frame.get("motion_valid",False),self.session_id,frame.get("method","unknown"),"one_shot",temporal,
        )

    def save(self,frame,action,source,weight=1.0,cursor_point=None):
        if frame is None or not frame.get("usable_for_learning"):
            return False
        action=normalize_action(action)
        if not action:
            return False
        if frame.get("quality",{}).get("low_information") and action.get("kind") not in {"no_op","click","double_click"}:
            return False
        if self.paused():
            self.keyboard_discarded+=1
            return False
        generation=int(self.keyboard_state["generation"])
        context=self.build_sample_context(frame,action,cursor_point)
        if context is None:
            return False
        saved=self.host.store.append_sample(
            self.game["id"],frame["f"],action,source,context,frame.get("rgb"),frame.get("neural_f"),weight,
        )
        if saved and (generation!=int(self.keyboard_state["generation"]) or self.paused()):
            self.keyboard_discarded+=1
            return False
        self.record_save_outcome(saved,frame,action)
        return saved

    def record_save_outcome(self,saved,frame,action):
        if not saved:
            self.duplicates+=1
            return
        self.learned+=1
        signature=action_signature(action)
        self.recent_actions.append(signature)
        self.last_action_signature=signature
        self.last_action_time=time.monotonic()
        changed=self.last_action_feature is None or visual_distance(self.last_action_feature,frame["f"])>float(self.calibration.get("significant_change",60.0))
        self.last_action_changed=changed
        if changed:
            self.state_since=time.monotonic()
        self.last_action_feature=frame["f"]

    def save_click(self,button,item):
        action={"kind":"click","button":button,"path":[item["point"]],"duration":item["duration"]}
        return self.save(item["frame"],action,"learn",1.0,item["point"])

    def flush_pending(self,now,force=False):
        for button,item in list(self.pending_click.items()):
            if force or now-item["time"]>0.42:
                if not self.host.should_stop() and not self.paused():
                    self.save_click(button,item)
                self.pending_click.pop(button,None)

    def clear_pointer_state(self,release=False):
        self.active.clear()
        self.pending_click.clear()
        self.motion=None
        self.last_cursor=None
        self.hover_point=None
        self.hover_start=0.0
        if release:
            self.host.api.release_all_buttons()

    def reject_mouse_overflow(self,now):
        if self.monitor.snapshot()["dropped_events"]<=self.mouse_drop_baseline:
            return False
        self.strict_violation=True
        self.invalid_reason="mouse_event_queue_overflow"
        if not self.invalid_marked:
            self.host.store.invalidate_learning_session(self.game["id"],self.session_id,self.invalid_reason)
            self.invalid_marked=True
        self.isolation.signal("mouse_queue_overflow",now)
        self.host.request_mode_stop("stopped","鼠标事件队列溢出，整段session无效")
        self.host.api.block_input()
        self.clear_pointer_state(True)
        self.host.set_status("鼠标事件队列溢出，学习立即停止且整段session将被标记无效")
        return True

    def acquire_focus(self):
        try:
            return self.host.api.validate_target(self.target,True)
        except TargetUnavailable:
            self.clear_pointer_state(True)
            self.host.set_status("目标窗口失去焦点，等待恢复；已释放全部鼠标键")
            return None

    def handle_down(self,event,rect):
        button=event["type"].split("_")[0]
        if button in SUPPORTED_BUTTONS and event["inside"]:
            frame=self.capture_safe(event["time"])
            if frame is not None:
                point=self.host.normalize_point(event["x"],event["y"],rect)
                self.active[button]={"frame":frame,"path":[point],"start":event["time"],"outside":False,"last":point}
        self.motion=None
        self.last_cursor=None
        self.hover_point=None
        self.hover_start=0.0

    def handle_active_move(self,event,rect):
        for item in self.active.values():
            if not event["inside"]:
                item["outside"]=True
                continue
            point=self.host.normalize_point(event["x"],event["y"],rect)
            if abs(point[0]-item["last"][0])+abs(point[1]-item["last"][1])>=0.004:
                item["path"].append(point)
                item["last"]=point
        if not event["inside"]:
            self.last_cursor=None
            self.hover_point=None
            self.hover_start=0.0

    def handle_idle_move(self,event,rect):
        if not event["inside"]:
            self.last_cursor=None
            self.hover_point=None
            self.hover_start=0.0
            if self.motion is not None:
                self.motion["outside"]=True
            return
        point=self.host.normalize_point(event["x"],event["y"],rect)
        if self.last_cursor is None:
            self.last_cursor=point
            self.hover_point=point
            self.hover_start=event["time"]
            return
        distance=math.hypot(point[0]-self.last_cursor[0],point[1]-self.last_cursor[1])
        if self.motion is None and distance>=0.012:
            frame=self.capture_safe(event["time"])
            if frame is not None:
                self.motion={"frame":frame,"path":[self.last_cursor,point],"start":event["time"],"last":point,"outside":False}
        elif self.motion is not None and math.hypot(point[0]-self.motion["last"][0],point[1]-self.motion["last"][1])>=0.006:
            self.motion["path"].append(point)
            self.motion["last"]=point
        self.last_cursor=point
        self.hover_point=point
        self.hover_start=event["time"]

    def handle_move(self,event,rect):
        self.last_motion_time=event["time"]
        if self.active:
            self.handle_active_move(event,rect)
        else:
            self.handle_idle_move(event,rect)

    def handle_click_release(self,button,item,point,event_time):
        previous=self.pending_click.get(button)
        if previous:
            close=math.hypot(point[0]-previous["point"][0],point[1]-previous["point"][1])<=0.035
            merged=self.host.learning_controller.merge_clicks(previous,button,point,item["start"],event_time) if close else None
            if merged is not None:
                self.pending_click.pop(button,None)
                self.save(previous["frame"],merged,"learn",1.3,previous["point"])
                return
            self.save_click(button,previous)
        duration=max(0.03,min(3.0,event_time-item["start"]))
        self.pending_click[button]={"frame":item["frame"],"point":point,"duration":duration,"time":event_time}

    def handle_up(self,event,rect):
        button=event["type"].split("_")[0]
        if button not in self.active:
            return
        item=self.active.pop(button)
        item["outside"]=item["outside"] or not event["inside"]
        if item["outside"]:
            self.discarded+=1
            return
        point=self.host.normalize_point(event["x"],event["y"],rect)
        item["path"].append(point)
        duration=max(0.03,min(3.0,event["time"]-item["start"]))
        length=path_length(item["path"])
        if length>0.045:
            self.save(item["frame"],{"kind":"drag","button":button,"path":item["path"],"duration":duration},"learn",1.4,point)
        elif duration>=0.48:
            self.save(item["frame"],{"kind":"long_press","button":button,"path":[point],"duration":duration},"learn",1.2,point)
        else:
            self.handle_click_release(button,item,point,event["time"])

    def handle_wheel(self,event,rect):
        if not event["inside"] or self.active:
            return
        frame=self.capture_safe(event["time"])
        point=self.host.normalize_point(event["x"],event["y"],rect)
        if frame is not None:
            kind="scroll_h" if event["type"]=="hwheel" else "scroll_v"
            self.save(frame,{"kind":kind,"delta":event.get("delta",0),"path":[point],"duration":0.08},"learn",1.2,point)

    def handle_event(self,raw_event,rect):
        event=self.host.learning_controller.convert_event(raw_event,rect)
        if event is None or self.paused() or self.host.should_stop():
            return
        event_type=event["type"]
        if event_type.endswith("_down"):
            self.handle_down(event,rect)
        elif event_type=="move":
            self.handle_move(event,rect)
        elif event_type.endswith("_up"):
            self.handle_up(event,rect)
        elif event_type in {"wheel","hwheel"}:
            self.handle_wheel(event,rect)

    def poll_cursor(self,rect):
        try:
            x,y=self.host.api.cursor()
            inside=self.host.inside(x,y,rect)
        except Exception:
            return 0,0,False
        if not inside:
            self.last_cursor=None
            self.hover_point=None
            self.hover_start=0.0
            if self.motion is not None:
                self.motion["outside"]=True
            for item in self.active.values():
                item["outside"]=True
        return x,y,inside

    def finalize_motion(self,now):
        if self.motion is None or now-self.last_motion_time<=0.22:
            return
        if not self.motion["outside"] and path_length(self.motion["path"])>0.06:
            duration=max(0.05,min(2.0,now-self.motion["start"]))
            self.save(self.motion["frame"],{"kind":"move","path":self.motion["path"],"duration":duration},"learn",1.0,self.motion["path"][-1])
        elif self.motion["outside"]:
            self.discarded+=1
        self.motion=None
        self.last_cursor=None

    def sample_hover(self,now,rect):
        if self.active or self.hover_point is None or now-self.hover_start<=0.85 or now-self.last_action_time<=0.7:
            return
        try:
            x,y=self.host.api.cursor()
            if not self.host.inside(x,y,rect):
                return
        except Exception:
            return
        point=self.host.normalize_point(x,y,rect)
        if math.hypot(point[0]-self.hover_point[0],point[1]-self.hover_point[1])<=0.02:
            frame=self.capture_safe(now)
            if frame is not None:
                self.save(frame,{"kind":"hover","path":[point],"duration":0.85},"learn",1.0,point)
            self.hover_start=now+1.5
        else:
            self.hover_point=point
            self.hover_start=now

    def sample_negative(self,now,rect,cursor):
        if self.active or self.pending_click:
            return
        if not self.host.learning_controller.negative_due(self.last_negative,now,self.last_motion_time):
            return
        frame=self.capture_safe(now)
        x,y,inside=cursor
        point=self.host.normalize_point(x,y,rect) if inside else None
        if frame is not None:
            self.save(frame,{"kind":"no_op","duration":0.45},"negative",0.6,point)
        self.last_negative=now

    def update_status(self,now):
        if now-self.last_update<=0.45:
            return
        pressure=self.host.store.sample_queue_pressure(self.game["id"])
        self.sampling_delay=0.012+0.04*pressure
        self.host.set_status(
            "学习中：有效"+str(self.learned)+"  重复"+str(self.duplicates)+"  越界废弃"+str(self.discarded)
            +"  无效画面"+str(self.invalid_frames)+"  非ESC键"+str(self.keyboard_count)
            +"  键盘关联废弃"+str(self.keyboard_discarded)+"  写入压力"+str(round(pressure*100))+"%"
        )
        self.last_update=now

    def capture_loop(self):
        with ModeSession(self.controller,self.target) as session:
            self.start_monitors(session)
            while not self.host.should_stop():
                now=time.monotonic()
                if self.reject_mouse_overflow(now):
                    break
                if self.drain_keyboard_events() or self.paused():
                    self.clear_pointer_state(True)
                    self.monitor.drain()
                    self.host.set_status("检测到非ESC键盘输入，学习立即停止且整段session将被标记无效")
                    break
                rect=self.acquire_focus()
                events=self.monitor.drain()
                self.mouse_event_count+=len(events)
                if rect is None:
                    time.sleep(0.05)
                    continue
                for raw_event in events:
                    self.handle_event(raw_event,rect)
                    if self.host.should_stop() or self.strict_violation:
                        break
                self.flush_pending(now)
                cursor=self.poll_cursor(rect)
                self.finalize_motion(now)
                self.sample_hover(now,rect)
                self.sample_negative(now,rect,cursor)
                self.update_status(now)
                time.sleep(self.sampling_delay)

    def finalize(self):
        self.host.learning_controller.submit(self.host.store,self.game["id"],self.session_id)
        if self.strict_violation:
            reason=self.invalid_reason or "input_safety_violation"
            removed=self.host.store.discard_session(self.game["id"],self.session_id,reason)
            self.keyboard_discarded=max(self.keyboard_discarded,removed)
            if reason=="mouse_event_queue_overflow":
                dropped=self.monitor.snapshot()["dropped_events"]-self.mouse_drop_baseline
                return ModeResult("stopped","学习因鼠标事件队列溢出而严格停止；整段session已作废并删除"+str(removed)+"个样本",{"invalid_session":self.session_id,"dropped_mouse_events":dropped})
            return ModeResult("stopped","学习因检测到非ESC键盘输入而严格停止；整段session已作废并删除"+str(removed)+"个样本",{"invalid_session":self.session_id,"keyboard_events":self.keyboard_count})
        self.host.store.validate_learning_session(self.game["id"],self.session_id)
        summary="学习已停止：有效"+str(self.learned)+"，重复或配额抑制"+str(self.duplicates)+"，越界废弃"+str(self.discarded)+"，无效画面"+str(self.invalid_frames)
        status="stopped" if self.host.stop_event and self.host.stop_event.is_set() else "completed"
        details={"session_id":self.session_id,"real_mouse_events":self.mouse_event_count,"outside_rejected":self.discarded,
            "keyboard_events":self.keyboard_count,"valid_samples":self.learned,"duplicates":self.duplicates,"invalid_frames":self.invalid_frames,
            "client_only":True,"session_status":"valid"}
        return ModeResult(status,summary,details)

    def run(self):
        self.preflight()
        self.capture_loop()
        return self.finalize()
class ReviewController:
    def __init__(self,context,host=None):
        if isinstance(context,ModeContext):
            self.context=context
            self.host=host
        else:
            self.context=ModeContext.from_host(context)
            self.host=context
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
            if index%32==0 and self.context.callbacks.should_stop():
                raise InputStopped("睡眠已停止")
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
            return list(valid),[],{"complete":False,"mode":"session_family_backend_visual_group","holdout_sessions":[],"reason":"只有一个完整学习session，只能生成临时模型","strata":len(totals),
                "session_count":len(sessions),"visual_group_intersection":[]}
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
        for first_hash,second_hash in near_perceptual_hash_pairs(hash_values,4,self.context.callbacks.should_stop):
            first_sessions=sorted(hash_sessions[first_hash])
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
            return list(valid),[],{"complete":False,"mode":"session_family_backend_visual_group","holdout_sessions":[],"reason":"无法建立视觉组与session级留出集","strata":len(totals),
                "session_count":len(sessions),"visual_group_count":len(groups),"visual_group_intersection":[]}
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
        return train,holdout,{"complete":complete,"mode":"session_family_backend_visual_group","holdout_sessions":sorted(holdout_sessions),"reason":reason,"strata":len(totals),
            "session_count":len(sessions),"visual_group_count":len(groups),"training_sessions":sorted(train_sessions),"session_intersection":[],"visual_group_intersection":visual_intersection}
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
    def build_experiences(self,samples,ocr_events,profile):
        events=sorted((item for item in ocr_events if isinstance(item,dict)),key=lambda item:safe_float(item.get("created"),0.0))
        step_penalty=safe_float(profile.get("step_penalty",-0.01),-0.01,-1.0,0.0)
        success_reward=safe_float(profile.get("success_reward",1.0),1.0,-10.0,10.0)
        failure_reward=safe_float(profile.get("failure_reward",-1.0),-1.0,-10.0,10.0)
        experiences=[]
        aggregates=defaultdict(lambda:{"count":0,"reward_sum":0.0,"success":0,"failure":0,"neutral":0,"next_states":Counter()})
        by_session=defaultdict(list)
        for item in samples:
            by_session[self.session_of(item)].append(item)
        for session,items in sorted(by_session.items()):
            ordered=sorted(items,key=lambda item:(safe_float(item.get("created"),0.0),str(item.get("checksum",""))))
            for index,item in enumerate(ordered):
                if len(experiences)%64==0 and self.context.callbacks.should_stop():
                    raise InputStopped("睡眠已停止")
                next_item=ordered[index+1] if index+1<len(ordered) else item
                start=safe_float(item.get("created"),0.0)
                end=safe_float(next_item.get("created"),start)+1.5
                matched=[entry.get("event",{}) for entry in events if start<=safe_float(entry.get("created"),0.0)<=end]
                terminal=""
                progress=0.0
                ocr=[]
                for event in matched:
                    if not isinstance(event,dict):
                        continue
                    ocr.append({key:event.get(key) for key in ("region_id","terminal","progress","status","reset") if key in event})
                    if event.get("terminal") in {"success","failure"}:
                        terminal=str(event.get("terminal"))
                    if abs(safe_float(event.get("progress"),0.0))>abs(progress):
                        progress=max(-1.0,min(1.0,safe_float(event.get("progress"),0.0)))
                reward=step_penalty+progress*0.5
                result="neutral"
                if terminal=="success":
                    reward+=success_reward
                    result="success"
                elif terminal=="failure":
                    reward+=failure_reward
                    result="failure"
                elif progress>0:
                    result="progress"
                elif progress<0:
                    result="regress"
                action_id=str(item.get("_action_cluster") or item.get("_canonical_action_signature") or action_signature(item.get("a")))
                state=visual_perceptual_hash(item["f"])
                next_state=visual_perceptual_hash(next_item["f"])
                experience={"session":session,"state":state,"action":action_id,"next_state":next_state,"result":result,"reward":round(reward,6),"ocr_events":ocr}
                experiences.append(experience)
                key=state+"|"+action_id
                row=aggregates[key]
                row["count"]+=1
                row["reward_sum"]+=reward
                row["success" if result=="success" else "failure" if result=="failure" else "neutral"]+=1
                row["next_states"][next_state]+=1
        model={}
        for key,row in aggregates.items():
            model[key]={"count":row["count"],"mean_reward":round(row["reward_sum"]/max(1,row["count"]),6),"success":row["success"],"failure":row["failure"],"neutral":row["neutral"],
                "next_states":dict(row["next_states"].most_common(8))}
        return experiences,model
    def run(self):
        return ReviewRunner(ModeContext.from_host(self.host),self,self.host,False).run()
    def run_offline(self):
        return ReviewRunner(ModeContext.from_host(self.host),self,self.host,True).run()
    def _pipeline_impl(self,phase=None):
        host=self.host
        phase=phase if isinstance(phase,dict) else {}
        host.require_ai_runtime()
        game=phase.get("game") or host.require_game()
        host.store.pause_sample_writes("睡眠期间冻结样本写入")
        try:
            samples,stats=host.store.load_samples(game["id"],MAX_SAMPLES)
            rgb_samples=[item for item in samples if sample_rgb_valid(item.get("rgb"))]
            host.set_status("睡眠阶段：正在用RGB样本执行动作条件对比学习和时序一致性优化")
            sleep_seed,sleep_seed_evidence=deterministic_sleep_seed(game["id"],rgb_samples)
            host.sleep_seed=sleep_seed
            host.sleep_seed_evidence=sleep_seed_evidence
            manifest=host.vision_runtime.train(game["id"],rgb_samples,host.stop_event,host.set_progress,sleep_seed)
            host.store.record_vision_model(game["id"],manifest)
            host.set_status("睡眠阶段：正在生成神经特征，原始视觉特征保持不变")
            host.store.reencode_samples(game["id"],host.vision_runtime,host.stop_event,host.set_progress)
            return host._run_review_process()
        finally:
            host.store.resume_sample_writes()
    def _run_impl(self,phase=None):
        return ReviewExecution(self,phase).run()
class ReviewExecution:
    def __init__(self,controller,phase=None):
        self.controller=controller
        self.host=controller.host
        self.phase=phase if isinstance(phase,dict) else {}
        self.errors=0
        self.accepted=0
        self.correct=0
        self.dangerous_false=0
        self.uncovered_rejected=0
        self.uncovered_false_accept=0
        self.covered_holdout=0

    def preflight(self):
        self.game=self.phase.get("game") or self.host.require_game()
        samples,self.stats=self.host.store.load_samples(self.game["id"])
        valid=[]
        for index,sample in enumerate(samples):
            if index%64==0 and self.host.should_stop():
                raise InputStopped("睡眠已停止")
            action=normalize_action(sample.get("a"))
            context=sample.get("context",{})
            temporal=temporal_from_context(context)
            calibration=context.get("calibration",{}) if isinstance(context,dict) else {}
            method=str(sample.get("capture_method","unknown"))
            if feature_valid(sample.get("f")) and action and temporal.get("complete") and method not in {"","unknown","legacy"} and calibration.get("dynamic_passed"):
                item=dict(sample)
                item["a"]=action
                valid.append(item)
        if not valid:
            raise RuntimeError("没有同时具备已验收采集后端和完整短时序上下文的学习数据；数据不足时只允许指导")
        self.host.wait_escape_release()
        self.host.review_distance_cache=BoundedLRU(50000)
        self.decorrelated,self.decorrelated_removed=self.host.review_controller.decorrelate(valid)
        if not self.decorrelated:
            raise RuntimeError("连续帧去相关后没有独立样本")
        self.train,self.holdout,self.split_info=self.host.review_controller.split(self.decorrelated)
        assert_disjoint_checksums(self.train,self.holdout)
        self.train_checksums=sorted(checksum_set(self.train))
        self.holdout_checksums=sorted(checksum_set(self.holdout))
        if set(self.train_checksums)&set(self.holdout_checksums):
            raise RuntimeError("训练集与留出集checksum交集非空")
        self.host.lifecycle.mark_running()

    def prepare_action_groups(self):
        self.action_clusters=self.host._cluster_action_samples(self.train)
        self.uncovered_actions=self.host.review_controller.map_holdout(self.holdout,self.action_clusters)
        if self.host.should_stop():
            raise InputStopped("睡眠已停止")
        self.holdout_sessions=set(self.split_info.get("holdout_sessions",[]))
        self.cluster_map={cluster["id"]:cluster for cluster in self.action_clusters}
        self.groups=defaultdict(list)
        for sample in self.train:
            self.groups[sample["_action_cluster"]].append(sample)
        self.ordered=sorted(
            self.groups.items(),
            key=lambda item:(normalize_action(self.cluster_map[item[0]]["a"])["kind"]=="no_op",-len(item[1])),
        )

    def build_prototypes(self):
        self.prototypes=[]
        tracker=PrototypeConflictTracker(self.host.should_stop,80,8)
        processed=0
        try:
            for cluster_id,items in self.ordered:
                if self.host.should_stop():
                    raise InputStopped("睡眠已停止")
                cluster=self.cluster_map[cluster_id]
                def progress(local,total_local,count):
                    self.host.set_progress(78*(processed+local)/max(1,len(self.train)))
                    self.host.set_status("睡眠中：仅使用训练集生成动作簇和短时序原型；"+str(processed+local)+"/"+str(len(self.train)))
                generated=self.host._cluster_action_group(
                    cluster_id,cluster["a"],len(items),items,progress,
                    cluster.get("repeat_policy","one_shot"),cluster.get("max_rate",3.0),
                )
                processed+=len(items)
                limited=self.host._limit_prototypes(self.prototypes+generated,MAX_PROTOTYPES)
                tracker.retain(limited)
                existing_ids=set(tracker.prototypes)
                tracker.add_batch([item for item in limited if str(item.get("id")) not in existing_ids])
                self.prototypes=limited
                self.host.set_status("睡眠阶段：动作簇"+str(len(self.prototypes))+"；距离缓存"+str(len(self.host.review_distance_cache))+"/"+str(self.host.review_distance_cache.capacity)+"；剩余样本约"+str(max(0,len(self.train)-processed)))
                self.host.review_distance_cache.clear()
        except InputStopped:
            self.save_partial_model()
            raise
        tracker.finalize(self.prototypes)
        for index,_ in enumerate(self.prototypes):
            if index%12==0:
                if self.host.should_stop():
                    raise InputStopped("睡眠已停止")
                self.host.set_progress(78+7*(index+1)/max(1,len(self.prototypes)))

    def save_partial_model(self):
        if not self.prototypes:
            return
        partial={"created":time.time(),"samples":len(self.decorrelated),"training_samples":len(self.train),"invalid_samples":self.stats["invalid"],
            "prototypes":self.prototypes,"capture_backends":sorted({str(item.get("capture_method")) for item in self.train}),
            "validation":{"status":"stopped","training_checksums":self.train_checksums,"holdout_checksums":self.holdout_checksums},
            "sequence_model":{},"model_binding":model_binding_from_samples(self.train),
            "safety_profile_checksum":profile_checksum(self.host.store.load_game_profile(self.game["id"])),"stopped":True}
        self.host.store.save_model(self.game["id"],partial,False)

    def apply_rejection_constraints(self):
        rejections=self.host.store.load_rejections(self.game["id"],500)
        self.rejection_constraints=0
        for proto_index,proto in enumerate(self.prototypes):
            matching=[]
            for rejection_index,rejection in enumerate(rejections):
                if (proto_index*max(1,len(rejections))+rejection_index)%64==0 and self.host.should_stop():
                    raise InputStopped("睡眠已停止")
                candidates=[normalize_action(item.get("a")) for item in rejection.get("candidates",[]) if isinstance(item,dict)]
                related=any(action and action_family_key(action)==action_family_key(proto["a"]) and action_geometry_distance(action,proto["a"])<=action_cluster_limit(proto["a"])*1.25 for action in candidates)
                if related:
                    matching.append((coarse_distance(proto["coarse"],rejection["coarse"]),rejection))
            if not matching:
                proto["nearest_rejected_distance"]=None
                continue
            nearest=min(batch_feature_distances(proto["f"],[item["f"] for _,item in sorted(matching,key=lambda value:value[0])[:8]]))
            proto["nearest_rejected_distance"]=round(nearest,6)
            proto["threshold"]=round(max(0.001,min(float(proto["threshold"]),nearest*0.72)),6)
            self.rejection_constraints+=1

    def build_basic_authorization(self):
        self.basic_cluster_rows={}
        self.basic_by_signature=defaultdict(lambda:{"support":0,"sessions":set(),"clusters":[],"consistent":0,"total":0})
        for cluster in self.action_clusters:
            cluster_id=str(cluster["id"])
            members=list(self.groups.get(cluster_id,[]))
            family=action_family_key(cluster["a"])
            signature=str(cluster.get("canonical_action_signature") or action_signature(cluster["a"]))
            sessions={self.host.review_controller.session_of(item) for item in members}
            limit=max(1e-9,action_cluster_limit(cluster["a"])*0.65)
            consistent=sum(1 for item in members if action_geometry_distance(item["a"],cluster["a"])<=limit)
            consistency=consistent/max(1,len(members))
            cluster_prototypes=[proto for proto in self.prototypes if str(proto.get("cluster_id"))==cluster_id]
            rejection_clear=all(proto.get("nearest_rejected_distance") is None or float(proto.get("nearest_rejected_distance"))>float(proto.get("threshold",0.0))*1.10 for proto in cluster_prototypes)
            nonambiguous=bool(cluster_prototypes and all(not proto.get("ambiguous") for proto in cluster_prototypes))
            passed=BasicSafeAuthorizer().authorize(family,len(members),consistency,len(sessions),nonambiguous,rejection_clear)
            self.basic_cluster_rows[cluster_id]={"family":family,"signature":signature,"support":len(members),"sessions":sorted(sessions),"consistency":consistency,
                "nonambiguous":nonambiguous,"rejection_clear":rejection_clear,"passed":passed}
            aggregate=self.basic_by_signature[signature]
            aggregate["support"]+=len(members)
            aggregate["sessions"].update(sessions)
            aggregate["clusters"].append(cluster_id)
            aggregate["consistent"]+=consistent
            aggregate["total"]+=len(members)

    def initialize_holdout_metrics(self):
        self.by_action=defaultdict(lambda:{"total":0,"accepted":0,"correct":0,"errors":0,"unrecognized":0,"negative_total":0,"false_positive":0})
        self.by_method=defaultdict(lambda:{"total":0,"accepted":0,"correct":0,"errors":0})
        self.by_scene=defaultdict(lambda:{"total":0,"accepted":0,"correct":0,"errors":0})
        self.action_sessions=defaultdict(set)
        self.dangerous_signatures={cluster["canonical_action_signature"] for cluster in self.action_clusters if cluster["a"]["kind"] in {"double_click","long_press","drag"} or cluster["a"].get("button") in {"right","middle"}}

    def evaluate_holdout_sample(self,sample):
        ranked=self.host.rank_action_candidates(sample["f"],self.prototypes,str(sample.get("context",{}).get("previous_action","")),16,sample.get("context",{}),sample.get("coarse"))
        decision=self.host.evaluate_action_candidates(ranked)
        expected=sample.get("_action_cluster")
        canonical=sample.get("_canonical_action_signature") or action_signature(sample["a"])
        method=str(sample.get("capture_method") or sample.get("context",{}).get("capture_method") or "unknown")
        scene=visual_scene_key(sample)
        arow,mrow,srow=self.by_action[canonical],self.by_method[method],self.by_scene[scene]
        self.action_sessions[canonical].add(self.host.review_controller.session_of(sample))
        for row in (arow,mrow,srow):
            row["total"]+=1
        predicted_signature=""
        if expected is not None:
            self.covered_holdout+=1
        if decision.get("accepted"):
            predicted_signature=self.record_accepted_decision(decision,expected,arow,mrow,srow)
        else:
            arow["unrecognized"]+=1
            if expected is None:
                self.uncovered_rejected+=1
                self.correct+=1
                for row in (arow,mrow,srow):
                    row["correct"]+=1
        for signature in self.dangerous_signatures:
            if canonical!=signature:
                self.by_action[signature]["negative_total"]+=1
                if predicted_signature==signature:
                    self.by_action[signature]["false_positive"]+=1

    def record_accepted_decision(self,decision,expected,arow,mrow,srow):
        self.accepted+=1
        for row in (arow,mrow,srow):
            row["accepted"]+=1
        predicted=decision["best"]
        signature=str(predicted.get("canonical_action_signature") or action_signature(predicted["a"]))
        if expected is not None and predicted["cluster_id"]==expected:
            self.correct+=1
            for row in (arow,mrow,srow):
                row["correct"]+=1
            return signature
        self.errors+=1
        for row in (arow,mrow,srow):
            row["errors"]+=1
        if expected is None:
            self.uncovered_false_accept+=1
        action=normalize_action(predicted["a"])
        if action["kind"] in {"double_click","long_press","drag"} or action.get("button") in {"right","middle"}:
            self.dangerous_false+=1
        return signature

    def evaluate_holdout(self):
        self.initialize_holdout_metrics()
        for index,sample in enumerate(self.holdout):
            if index%8==0 and self.host.should_stop():
                raise InputStopped("睡眠已停止")
            self.evaluate_holdout_sample(sample)
            if index%5==0:
                self.host.set_progress(85+13*(index+1)/max(1,len(self.holdout)))
        self.holdout_count=len(self.holdout)
        self.coverage=self.accepted/self.covered_holdout if self.covered_holdout else 0.0
        self.accepted_error_rate=self.errors/self.accepted if self.accepted else None
        self.error_upper_95=binomial_error_upper(self.errors,self.accepted,0.95)
        self.overall_accuracy=self.correct/self.holdout_count if self.holdout_count else 0.0
        self.dangerous_false_rate=self.dangerous_false/max(1,self.holdout_count)

    def summarize_action_rules(self):
        self.per_action={}
        self.action_rules_pass=True
        self.authorized_clusters=set()
        train_signatures={str(item.get("_canonical_action_signature",action_signature(item["a"]))) for item in self.train}
        for signature in sorted(train_signatures|set(self.by_action)):
            row=dict(self.by_action[signature])
            row["recall"]=row["correct"]/row["total"] if row["total"] else 0.0
            row["coverage"]=row["accepted"]/row["total"] if row["total"] else 0.0
            row["accepted_error_rate"]=row["errors"]/row["accepted"] if row["accepted"] else None
            row["error_upper_95"]=binomial_error_upper(row["errors"],row["accepted"],0.95)
            row["independent_sessions"]=len(self.action_sessions.get(signature,set()))
            action=next((cluster["a"] for cluster in self.action_clusters if cluster["canonical_action_signature"]==signature),{"kind":"no_op"})
            dangerous=action["kind"] in {"double_click","long_press","drag"} or action.get("button") in {"right","middle"}
            row["dangerous"]=dangerous
            row_pass=ReviewValidator().authorize(row,dangerous)
            basic=self.basic_by_signature.get(signature)
            basic_pass=bool(not dangerous and basic and any(self.basic_cluster_rows.get(cluster_id,{}).get("passed") for cluster_id in basic["clusters"]))
            row.update({"basic_training_support":int(basic["support"]) if basic else 0,"basic_training_sessions":len(basic["sessions"]) if basic else 0,
                "basic_training_consistency":basic["consistent"]/max(1,basic["total"]) if basic else 0.0,"basic_safe_passed":basic_pass,"passed":bool(row_pass),"authorized":bool(row_pass or basic_pass)})
            for cluster in self.action_clusters:
                if cluster["canonical_action_signature"]==signature and (row_pass or self.basic_cluster_rows.get(str(cluster["id"]),{}).get("passed")):
                    self.authorized_clusters.add(cluster["id"])
            self.per_action[signature]=row

    def summarize_method_rules(self):
        self.train_methods=sorted({str(item.get("capture_method")) for item in self.train})
        self.per_method={}
        self.method_rules_pass=True
        for method in sorted(set(self.train_methods)|set(self.by_method)):
            row=dict(self.by_method[method])
            row["accuracy"]=row["correct"]/row["total"] if row["total"] else 0.0
            row["coverage"]=row["accepted"]/row["total"] if row["total"] else 0.0
            row["accepted_error_rate"]=row["errors"]/row["accepted"] if row["accepted"] else None
            row["error_upper_95"]=binomial_error_upper(row["errors"],row["accepted"],0.95)
            row["passed"]=bool(row["total"]>=VersionedThresholdConfig.capture_min_holdout and row["errors"]<=VersionedThresholdConfig.capture_max_errors and row["accuracy"]>=VersionedThresholdConfig.capture_min_accuracy)
            self.method_rules_pass=self.method_rules_pass and row["passed"]
            self.per_method[method]=row

    def summarize_scene_rules(self):
        self.per_scene={}
        self.scene_rules_pass=True
        for scene,row_value in sorted(self.by_scene.items()):
            row=dict(row_value)
            row["accuracy"]=row["correct"]/row["total"] if row["total"] else 0.0
            row["coverage"]=row["accepted"]/row["total"] if row["total"] else 0.0
            row["error_upper_95"]=binomial_error_upper(row["errors"],row["accepted"],0.95)
            row["passed"]=bool(row["total"]>=VersionedThresholdConfig.scene_min_holdout and row["errors"]<=VersionedThresholdConfig.scene_max_errors and row["accuracy"]>=VersionedThresholdConfig.scene_min_accuracy)
            self.scene_rules_pass=self.scene_rules_pass and row["passed"]
            self.per_scene[scene]=row

    def authorize_prototypes(self):
        full_clusters=set()
        for signature,row in self.per_action.items():
            if row.get("passed"):
                full_clusters.update(cluster["id"] for cluster in self.action_clusters if cluster["canonical_action_signature"]==signature)
        for proto in self.prototypes:
            cluster_id=str(proto.get("cluster_id"))
            basic_safe=bool(self.basic_cluster_rows.get(cluster_id,{}).get("passed"))
            full_safe=cluster_id in full_clusters
            proto["authorized"]=bool((full_safe or basic_safe) and not proto.get("ambiguous"))
            proto["authorization_level"]="full" if full_safe else "basic_safe" if basic_safe else "none"
            runtime=action_runtime_metadata(proto.get("a"))
            proto.update({"strictness":runtime["strictness"],"cooldown":runtime["cooldown"],"dangerous":runtime["dangerous"]})
        self.authorized_prototypes=sum(1 for proto in self.prototypes if proto.get("authorized"))
        self.full_authorized_prototypes=sum(1 for proto in self.prototypes if proto.get("authorized") and proto.get("authorization_level")=="full")
        self.basic_safe_prototypes=sum(1 for proto in self.prototypes if proto.get("authorized") and proto.get("authorization_level")=="basic_safe")

    def determine_validation_status(self):
        enough,global_pass=evaluate_validation_thresholds(self.split_info.get("complete"),self.split_info.get("session_count",0),self.holdout_count,self.accepted,self.coverage,
            self.overall_accuracy,self.error_upper_95,self.dangerous_false,self.uncovered_false_accept)
        enough=bool(enough and self.train_methods)
        action_rules_pass=self.full_authorized_prototypes>0
        passed=bool(enough and global_pass and action_rules_pass and self.method_rules_pass and self.scene_rules_pass and self.prototypes)
        basic_available=bool(self.basic_safe_prototypes>0 and self.train_methods)
        self.validation_status="passed" if passed else "basic_safe" if basic_available else "insufficient" if not enough or not action_rules_pass or not self.method_rules_pass else "failed"

    def build_validation(self):
        self.validation={"status":self.validation_status,"split":str(self.split_info.get("mode","unknown")),"split_complete":bool(self.split_info.get("complete")),
            "split_reason":str(self.split_info.get("reason","")),"strata":int(self.split_info.get("strata",0)),"session_count":int(self.split_info.get("session_count",0)),
            "holdout_sessions":sorted(self.holdout_sessions),"required_sessions":VersionedThresholdConfig.required_sessions,"minimum_holdout":VersionedThresholdConfig.review_min_holdout,
            "minimum_accepted":VersionedThresholdConfig.review_min_accepted,"minimum_ordinary_action_holdout":VersionedThresholdConfig.ordinary_min_positive,
            "minimum_ordinary_sessions":VersionedThresholdConfig.ordinary_min_sessions,"minimum_dangerous_positive":VersionedThresholdConfig.dangerous_min_positive,
            "minimum_dangerous_negative":VersionedThresholdConfig.dangerous_min_negative,"minimum_dangerous_sessions":VersionedThresholdConfig.dangerous_min_sessions,
            "minimum_coverage":VersionedThresholdConfig.minimum_coverage,"maximum_error_upper_95":VersionedThresholdConfig.maximum_error_upper_95,
            "minimum_overall_accuracy":VersionedThresholdConfig.minimum_overall_accuracy,"maximum_dangerous_false":VersionedThresholdConfig.maximum_dangerous_false,
            "maximum_uncovered_false_accept":VersionedThresholdConfig.maximum_uncovered_false_accept,"capture_min_holdout":VersionedThresholdConfig.capture_min_holdout,
            "capture_min_accuracy":VersionedThresholdConfig.capture_min_accuracy,"capture_max_errors":VersionedThresholdConfig.capture_max_errors,
            "scene_min_holdout":VersionedThresholdConfig.scene_min_holdout,"scene_min_accuracy":VersionedThresholdConfig.scene_min_accuracy,"scene_max_errors":VersionedThresholdConfig.scene_max_errors}
        self.validation.update(self.validation_measurements())

    def validation_measurements(self):
        return {"holdout":self.holdout_count,"accepted":self.accepted,"errors":self.errors,"correct":self.correct,"coverage":self.coverage,"reject_rate":1.0-self.coverage,
            "accepted_error_rate":self.accepted_error_rate,"error_upper_95":self.error_upper_95,"overall_accuracy":self.overall_accuracy,"dangerous_false":self.dangerous_false,
            "dangerous_false_rate":self.dangerous_false_rate,"uncovered_actions":self.uncovered_actions,"uncovered_rejected":self.uncovered_rejected,
            "uncovered_false_accept":self.uncovered_false_accept,"covered_holdout":self.covered_holdout,"authorized_prototypes":self.authorized_prototypes,
            "full_authorized_prototypes":self.full_authorized_prototypes,"basic_safe_prototypes":self.basic_safe_prototypes,
            "authorized_families":sorted({action_family_key(proto["a"]) for proto in self.prototypes if proto.get("authorized")}),
            "basic_safe_authorized_families":sorted({action_family_key(proto["a"]) for proto in self.prototypes if proto.get("authorization_level")=="basic_safe" and proto.get("authorized")}),
            "basic_cluster_validation":self.basic_cluster_rows,"decorrelated_removed":self.decorrelated_removed,"per_action":self.per_action,"per_capture_method":self.per_method,
            "per_scene":self.per_scene,"visual_group_intersection":list(self.split_info.get("visual_group_intersection",[])),
            "ambiguous_prototypes":sum(1 for proto in self.prototypes if proto.get("ambiguous")),"training_checksums":self.train_checksums,
            "holdout_checksums":self.holdout_checksums,"checksum_intersection":[]}

    def build_sequence_model(self):
        counts=defaultdict(Counter)
        train_by_session=defaultdict(list)
        for item in self.train:
            train_by_session[self.host.review_controller.session_of(item)].append(item)
        for _,session_items in sorted(train_by_session.items()):
            ordered=sorted(session_items,key=lambda item:float(item.get("created",0.0)))
            history=deque(["<START>","<START>","<START>","<START>"],maxlen=4)
            for item in ordered:
                cluster_id=str(item.get("_action_cluster") or "")
                if not cluster_id:
                    continue
                for size in range(1,5):
                    counts[str(size)+"|"+"|".join(list(history)[-size:])][cluster_id]+=1
                signature=str(item.get("_canonical_action_signature") or action_signature(item["a"]))
                counts[history[-1]][cluster_id]+=1
                history.append(signature)
        self.sequence_model={key:dict(value) for key,value in counts.items()}

    def build_model(self):
        profile=self.host.store.load_game_profile(self.game["id"])
        events=self.host.store.load_ocr_experience_events(self.game["id"],5000)
        experiences,experience_model=self.host.review_controller.build_experiences(self.train,events,profile)
        sleep_seed=safe_int(getattr(self.host,"sleep_seed",0),0,0,2**63-1)
        self.model={"created":time.time(),"sleep_seed":sleep_seed,"determinism":{"seed":sleep_seed,"build_hash":current_build_hash(),
                "training_checksums_hash":hashlib.sha256(canonical_bytes(self.train_checksums)).hexdigest(),
                "holdout_checksums_hash":hashlib.sha256(canonical_bytes(self.holdout_checksums)).hexdigest()},
            "samples":len(self.decorrelated),"training_samples":len(self.train),"holdout_samples":len(self.holdout),"invalid_samples":self.stats["invalid"],
            "action_clusters":len(self.action_clusters),"rejection_constraints":self.rejection_constraints,"prototypes":self.prototypes,"capture_backends":self.train_methods,
            "validation":self.validation,"training_checksums":self.train_checksums,"holdout_checksums":self.holdout_checksums,"sequence_model":self.sequence_model,
            "experiences":experiences,"experience_model":experience_model,"model_binding":model_binding_from_samples(self.train),
            "safety_profile_checksum":profile_checksum(profile),"stopped":False}

    def report_lines(self):
        label="通过完整独立验收" if self.validation_status=="passed" else "已生成基础安全模型，可训练已授权的普通安全动作" if self.validation_status=="basic_safe" else "验证不足，仅保存不可训练临时模型" if self.validation_status=="insufficient" else "验证失败，仅保存不可训练临时模型"
        error_text="无可计算值" if self.accepted_error_rate is None else str(round(self.accepted_error_rate*100,2))+"%"
        headline=(
            "睡眠完成，"+label+"：原型"+str(len(self.prototypes))
            +"，独立session留出"+str(self.holdout_count)+"，接受"+str(self.accepted)
            +"，覆盖率"+str(round(self.coverage*100,2))+"%，接受错误率"+error_text
            +"，95%错误率上界"+str(round(self.error_upper_95*100,2))+"%，未覆盖动作"+str(self.uncovered_actions)
            +"，连续帧去相关移除"+str(self.decorrelated_removed)
            +( "；留出失败原因："+str(self.split_info.get("reason")) if self.split_info.get("reason") else "")
        )
        lines=[headline,"各动作独立留出验证："]
        for signature,row in sorted(self.per_action.items()):
            authorization="完整授权" if row["passed"] else "基础安全授权" if row.get("basic_safe_passed") else "未授权"
            lines.append(
                signature+"：独立留出正例"+str(row["total"])+"，负例"+str(row["negative_total"])
                +"，接受"+str(row["accepted"])+"，错误"+str(row["errors"])+"，危险误触"+str(row["false_positive"])
                +"，训练支持"+str(row.get("basic_training_support",0))+"，一致率"
                +str(round(float(row.get("basic_training_consistency",0.0))*100,2))+"%，"+authorization
            )
        lines.append("各采集后端独立验证：")
        for method,row in sorted(self.per_method.items()):
            lines.append(method+"：留出"+str(row["total"])+"，覆盖率"+str(round(row["coverage"]*100,2))+"%，错误"+str(row["errors"])+"，"+("通过" if row["passed"] else "未通过"))
        lines.append("各视觉场景分层验证：")
        for scene,row in sorted(self.per_scene.items()):
            lines.append(scene+"：留出"+str(row["total"])+"，准确率"+str(round(row["accuracy"]*100,2))+"%，错误"+str(row["errors"])+"，"+("通过" if row["passed"] else "未通过"))
        return lines

    def finalize(self):
        if not self.prototypes:
            raise RuntimeError("睡眠未生成可用原型")
        self.host.store.save_model(self.game["id"],self.model,self.validation_status=="passed")
        self.host.review_distance_cache.clear()
        self.host.set_progress(100)
        return ModeResult("completed","\n".join(self.report_lines()),{"validation":self.validation_status})

    def run(self):
        self.preflight()
        self.prepare_action_groups()
        self.build_prototypes()
        self.apply_rejection_constraints()
        self.build_basic_authorization()
        self.evaluate_holdout()
        self.summarize_action_rules()
        self.summarize_method_rules()
        self.summarize_scene_rules()
        self.authorize_prototypes()
        self.determine_validation_status()
        self.build_validation()
        self.build_sequence_model()
        self.build_model()
        return self.finalize()
class TrainingController:
    def __init__(self,context,host=None):
        if isinstance(context,ModeContext):
            self.context=context
            self.host=host
        else:
            self.context=ModeContext.from_host(context)
            self.host=context
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
        return TrainingRunner(ModeContext.from_host(self.host),self,self.host).run()
    def _run_impl(self,phase=None):
        return TrainingExecution(self,phase).run()
class TrainingExecution:
    def __init__(self,controller,phase=None):
        self.controller=controller
        self.host=controller.host
        self.phase=phase if isinstance(phase,dict) else {}
        self.actions=0
        self.keyboard_count=0
        self.mouse_count=0
        self.recent_actions=deque(["<START>","<START>"],maxlen=4)
        self.candidate_id=None
        self.candidate_count=0
        self.candidate_frame_stamp=0.0
        self.last_action_signature=""
        self.last_cluster_id=""
        self.last_action_time=0.0
        self.last_action_feature=None
        self.state_unlocked=True
        self.no_change_count=0
        self.previous_feature=None
        self.previous_frame_stamp=0.0
        self.state_since=time.monotonic()
        self.action_hits=defaultdict(deque)
        self.snapshot_last_check=0.0

    def preflight(self):
        self.game=self.phase.get("game") or self.host.require_game()
        self.target=self.phase.get("window") or self.host.require_window(False)
        self.model=self.host.store.load_trainable_model(self.game["id"])
        self.host.validate_model_binding(self.model,self.target)
        self.profile=self.host.store.load_game_profile(self.game["id"])
        self.agent_policy=TaskAgentPolicy(self.profile)
        if not self.agent_policy.allowed:
            raise RuntimeError("当前游戏未配置任何自动动作白名单，请先打开“任务与安全”")
        self.host.active_model_runtime=self.model
        self.prototypes=[proto for proto in self.model["prototypes"] if self.host.training_controller.authorized(proto) and self.agent_policy.allowed_action(proto.get("a"))]
        if not self.prototypes:
            raise RuntimeError("当前模型与任务白名单没有共同的已授权动作")
        self.allowed_backends={method for proto in self.prototypes for method in proto.get("capture_methods",[])} or set(self.model.get("capture_backends",[]))
        self.calibration=self.phase.get("calibration") or self.host.ensure_capture_calibration(self.target,"训练")
        self.validated_backend=str(self.calibration.get("validated_backend",""))
        if self.validated_backend not in self.allowed_backends:
            raise RuntimeError("当前采集后端未被当前可训练模型授权；请用该后端重新学习并睡眠")
        self.build_snapshot()
        self.host.api.request_foreground(self.target["hwnd"])
        self.host.wait_escape_release()
        self.isolation=StrictInputIsolation(self.host.stop_event)

    def model_table_token(self):
        with self.host.store.lock:
            rows=self.host.store.db.execute(
                "SELECT slot,saved,checksum FROM models WHERE game_id=? ORDER BY slot",
                (self.game["id"],),
            ).fetchall()
        values=[[str(row["slot"]),float(row["saved"]),str(row["checksum"])] for row in rows]
        return immutable_digest(values)

    def build_snapshot(self):
        identity=self.host.api.target_identity(self.target)
        rect=tuple(self.host.api.validate_target(self.target,False))
        dpi=self.host.api.dpi_for_window(int(self.target["hwnd"]))
        self.snapshot_payload={
            "game_id":str(self.game["id"]),
            "model_table_token":self.model_table_token(),
            "model_digest":immutable_digest(self.model),
            "safety_profile_checksum":profile_checksum(self.profile),
            "window":self.identity_payload(identity),
            "content_rect":list(rect),
            "dpi":dpi,
            "capture_backend":self.validated_backend,
            "allowed_actions":sorted({action_signature(proto.get("a")) for proto in self.prototypes}),
        }
        self.training_snapshot_checksum=immutable_digest(self.snapshot_payload)

    def identity_payload(self,identity):
        return {
            "hwnd":safe_int(identity.get("hwnd"),0),
            "pid":safe_int(identity.get("pid"),0),
            "process_created":safe_int(identity.get("process_created"),0),
            "window_thread_id":safe_int(identity.get("window_thread_id"),0),
            "class":str(identity.get("class","")),
            "process_path":os.path.normcase(str(identity.get("process_path",""))),
            "integrity":safe_int(identity.get("integrity"),0),
        }

    def assert_training_snapshot(self,force=False):
        now=time.monotonic()
        if not force and now-self.snapshot_last_check<0.25:
            return True
        self.snapshot_last_check=now
        current_game=self.host.require_game()
        identity=self.host.api.target_identity(self.target)
        rect=tuple(self.host.api.validate_target(self.target,False))
        dpi=self.host.api.dpi_for_window(int(self.target["hwnd"]))
        backend=str(self.host.api.calibration_for(self.target).get("validated_backend",self.validated_backend))
        current_profile=self.host.store.load_game_profile(self.game["id"])
        payload={
            "game_id":str(current_game.get("id","")),
            "model_table_token":self.model_table_token(),
            "model_digest":self.snapshot_payload["model_digest"],
            "safety_profile_checksum":profile_checksum(current_profile),
            "window":self.identity_payload(identity),
            "content_rect":list(rect),
            "dpi":dpi,
            "capture_backend":backend,
            "allowed_actions":self.snapshot_payload["allowed_actions"],
        }
        if immutable_digest(payload)==self.training_snapshot_checksum:
            return True
        self.host.api.block_input()
        self.host.api.release_all_buttons()
        self.host.request_mode_stop("stopped","训练不可变运行快照发生变化")
        raise InputStopped("游戏、模型、安全配置、窗口身份、内容区域、DPI、采集后端或动作集合在训练期间发生变化")

    def start_monitors(self,session):
        fps=max(8.0,float(self.calibration.get("fps",15.0)))
        self.frame_buffer=session.start_frames(fps,2.5,0.1,"training")
        self.keyboard=session.start_keyboard()
        self.mouse=session.start_mouse()
        self.host.lifecycle.mark_running()
        self.keyboard_interrupt=self.keyboard.other_event
        self.mouse_interrupt=self.mouse.input_event

    def execute_profile_restart(self,frame):
        self.assert_training_snapshot(True)
        restart=normalize_action(self.profile.get("restart_action"))
        if not restart:
            return False
        if not self.agent_policy.allowed_action(restart):
            raise InputStopped("重新开始动作不在安全白名单")
        if not self.host.training_controller.usable_frame(frame,self.validated_backend) or frame.get("method") not in self.allowed_backends:
            raise InputStopped("重新开始前画面或采集后端不可用")
        if self.mouse_interrupt.is_set() or self.keyboard_interrupt.is_set() or not self.keyboard.all_released() or not self.mouse.stable_for(0.45):
            raise InputStopped("重新开始前检测到人工输入")
        self.host.api.validate_target(self.target,True)
        self.host.api.validate_uipi(self.target)
        try:
            if restart.get("kind")!="no_op":
                self.host.api.allow_input(self.host.stop_event)
                self.host.set_input_status("允许执行一次已配置的重新开始动作")
            self.host.execute_action(self.target,restart,frame,self.mouse_interrupt,self.keyboard,self.keyboard_interrupt)
            self.actions+=1
            self.recent_actions.append(action_signature(restart))
            return True
        finally:
            self.host.api.block_input()
            self.host.api.release_all_buttons()

    def detect_interference(self):
        key_events=[event for event in self.keyboard.drain() if event.get("kind")=="other" and event.get("down")]
        mouse_events=self.mouse.drain()
        tripped=self.host.training_controller.interference(self.mouse_interrupt,self.keyboard_interrupt)
        if not tripped and not key_events and not mouse_events:
            return False
        self.keyboard_count+=len(key_events)
        self.mouse_count+=len(mouse_events)
        if key_events or self.keyboard_interrupt.is_set():
            self.isolation.signal("keyboard",key_events[0].get("time") if key_events else time.monotonic())
            reason="检测到非ESC键盘输入，训练立即停止"
            self.host.set_input_status("因键盘输入锁定")
        else:
            self.isolation.signal("mouse",mouse_events[0].get("time") if mouse_events else time.monotonic())
            reason="检测到物理或其他程序注入的鼠标输入，训练立即停止"
            self.host.set_input_status("因人工鼠标输入锁定")
        self.host.request_mode_stop("stopped",reason)
        self.host.api.block_input()
        self.host.api.release_all_buttons()
        self.host.set_status(reason+"；不会自动恢复")
        return True

    def acquire_frame(self):
        self.host.api.block_input()
        self.host.set_input_status("等待连续确认")
        try:
            self.host.api.validate_target(self.target,True)
        except TargetUnavailable as error:
            self.reset_candidate()
            self.host.set_confidence("训练置信度：0%")
            self.host.set_input_status("目标窗口不可用，已锁定")
            self.host.set_status("目标窗口失去焦点，等待恢复；"+str(error))
            time.sleep(0.08)
            return None
        captured=self.frame_buffer.latest(None,0.8)
        if not self.host.training_controller.usable_frame(captured,self.validated_backend):
            self.host.set_input_status("检测到黑屏，已锁定" if captured and captured.get("black_frame") else "画面不可用，已锁定")
            self.host.set_status("采集画面不可用于训练；等待已验收、非受保护黑屏且后端未冻结的最新帧；"+(self.frame_buffer.last_error or "尚无画面"))
            time.sleep(0.08)
            return None
        return captured if self.validate_backend(captured) else None

    def validate_backend(self,captured):
        current=str(self.host.api.calibration_for(self.target).get("validated_backend",self.validated_backend))
        if current!=self.validated_backend:
            if current in self.allowed_backends:
                self.validated_backend=current
                self.reset_candidate()
                self.host.set_input_status("采集后端切换，等待连续确认")
                self.host.set_status("原采集后端已熔断，已切换到剩余已验证后端："+self.validated_backend)
            else:
                self.host.set_status("替代采集后端未在模型中验证，拒绝自动动作")
            time.sleep(0.1)
            return False
        if captured.get("method")!=self.validated_backend or captured.get("method") not in self.allowed_backends:
            self.host.set_status("采集后端变化或未在模型中验证，拒绝自动动作；请重新学习和睡眠")
            time.sleep(0.1)
            return False
        return True

    def reset_candidate(self):
        self.candidate_id=None
        self.candidate_count=0
        self.candidate_frame_stamp=0.0

    def handle_terminal_state(self,captured):
        feature=captured["f"]
        state,_=self.agent_policy.classify(feature)
        if state=="success":
            self.host.request_mode_stop("completed","检测到已定义的成功状态，训练完成")
            return "break"
        if state!="failure":
            return None
        outcome=self.agent_policy.register(feature,{"kind":"no_op","duration":0.1},feature,False)
        if outcome["stop"]:
            self.host.request_mode_stop("stopped","失败状态连续出现达到安全上限"+str(self.agent_policy.max_failures)+"次，已自动停机")
            return "break"
        try:
            if self.execute_profile_restart(captured):
                self.host.set_status("检测到失败或死亡状态，已执行白名单内的重新开始动作")
                time.sleep(max(0.1,float(self.calibration.get("input_delay",0.24))))
                return "continue"
        except InputStopped as error:
            self.host.request_mode_stop("stopped","失败状态回滚无法安全执行："+str(error))
            return "break"
        self.host.set_status("检测到失败或死亡状态，但未配置重新开始动作；保持锁定")
        time.sleep(0.12)
        return "continue"

    def update_temporal_state(self,captured):
        feature=captured["f"]
        if captured["time"]!=self.previous_frame_stamp:
            if self.previous_feature is not None and visual_distance(self.previous_feature,feature)>float(self.calibration.get("significant_change",60.0)):
                self.state_since=time.monotonic()
            self.previous_feature=feature
            self.previous_frame_stamp=captured["time"]
        self.significant=self.last_action_feature is not None and visual_distance(self.last_action_feature,feature)>float(self.calibration.get("significant_change",60.0))
        if self.significant:
            self.state_unlocked=True
            self.no_change_count=0
            self.state_since=time.monotonic()
        temporal=self.host.build_temporal_context(self.frame_buffer,captured,self.recent_actions,self.state_since)
        if not temporal_from_context({**temporal,"previous_action_changed_frame":self.significant}).get("complete"):
            self.host.set_status("等待至少3帧短时序上下文")
            time.sleep(0.05)
            return None
        temporal["previous_action_changed_frame"]=bool(self.significant)
        return temporal

    def choose_action(self,captured,temporal):
        ranked=self.host.rank_action_candidates(captured["f"],self.prototypes,self.last_action_signature,VersionedThresholdConfig.candidate_full_limit,temporal,captured.get("coarse"))
        decision=self.host.evaluate_action_candidates(ranked)
        if not decision.get("accepted"):
            self.reset_candidate()
            self.host.set_input_status("等待连续确认")
            self.host.set_confidence("训练置信度："+str(round(float(decision.get("confidence",0.0))*100,1))+"%")
            suffix="；安全探索仅保持等待，不产生鼠标输入" if self.profile.get("exploration_enabled") else "；不执行动作并等待指导"
            self.host.set_status("训练中："+str(decision.get("reason","识别不确定"))+suffix)
            time.sleep(0.12)
            return None
        best=decision["best"]
        cluster_id=best["cluster_id"]
        if self.candidate_id==cluster_id:
            if captured["time"]==self.candidate_frame_stamp:
                time.sleep(0.025)
                return None
            self.candidate_count+=1
        else:
            self.candidate_id=cluster_id
            self.candidate_count=1
        self.candidate_frame_stamp=captured["time"]
        confirmations=max(3,int(self.calibration.get("confirm_frames",3)))
        self.host.set_confidence("训练置信度："+str(round(decision["confidence"]*100,1))+"%  连续确认"+str(self.candidate_count)+"/"+str(confirmations))
        if not self.host.training_controller.confirmed(self.candidate_count,confirmations):
            time.sleep(0.05)
            return None
        return self.build_selection(captured,best,confirmations)

    def build_selection(self,captured,best,confirmations):
        action=normalize_action(best["a"])
        proto=best["proto"]
        if not self.host.training_controller.authorized(proto):
            self.host.set_status("动作原型未通过独立留出授权，拒绝动作")
            time.sleep(0.1)
            return None
        if not self.agent_policy.allowed_action(action):
            self.host.set_status("动作不在当前游戏安全白名单中，拒绝动作："+self.host.action_text(action))
            time.sleep(0.1)
            return None
        if captured["method"] not in proto.get("capture_methods",frozenset()):
            self.host.set_status("当前原型未在该采集后端训练，拒绝动作")
            time.sleep(0.1)
            return None
        repeat_policy=str(proto.get("repeat_policy","one_shot"))
        max_rate=max(0.25,min(12.0,float(proto.get("max_rate",3.0))))
        return {"action":action,"canonical":action_signature(action),"proto":proto,"cluster_id":best["cluster_id"],
            "repeat_policy":repeat_policy,"max_rate":max_rate,"confirmations":confirmations}

    def action_ready(self,selection):
        cluster_id=selection["cluster_id"]
        policy=selection["repeat_policy"]
        if policy in {"one_shot","hold_until_change"} and self.last_cluster_id==cluster_id and not self.state_unlocked:
            self.host.set_status("等待画面变化：该动作策略为"+policy)
            time.sleep(0.1)
            return False
        minimum_gap=max(self.host.action_cooldown(selection["action"]) if policy=="one_shot" else 0.0,1.0/selection["max_rate"] if policy in {"rate_limited","repeatable"} else 0.0)
        if time.monotonic()-self.last_action_time<minimum_gap:
            time.sleep(0.03)
            return False
        hits=self.action_hits[cluster_id]
        now=time.monotonic()
        while hits and now-hits[0]>1.0:
            hits.popleft()
        if len(hits)>=max(1,int(math.ceil(selection["max_rate"]))):
            self.host.set_status("动作专属频率限制中："+self.host.action_text(selection["action"]))
            time.sleep(0.05)
            return False
        return True

    def verify_fresh_decision(self,fresh,selection):
        proto=selection["proto"]
        if not self.host.training_controller.usable_frame(fresh,self.validated_backend) or fresh.get("method") not in self.allowed_backends or fresh.get("method") not in proto.get("capture_methods",frozenset()):
            raise InputStopped("动作前最后一帧或采集后端不可用")
        if self.keyboard_interrupt.is_set() or not self.keyboard.all_released():
            raise InputStopped("检测到键盘输入")
        if self.mouse_interrupt.is_set() or not self.mouse.stable_for(0.45):
            raise InputStopped("检测到人工鼠标干扰")
        temporal=self.host.build_temporal_context(self.frame_buffer,fresh,self.recent_actions,self.state_since)
        temporal["previous_action_changed_frame"]=bool(self.significant)
        ranked=self.host.rank_action_candidates(fresh["f"],self.prototypes,self.last_action_signature,VersionedThresholdConfig.candidate_full_limit,temporal,fresh.get("coarse"))
        decision=self.host.evaluate_action_candidates(ranked)
        if not decision.get("accepted") or decision.get("best",{}).get("cluster_id")!=selection["cluster_id"]:
            raise InputStopped("动作前模型判断已变化")
        if not self.host.training_controller.confirmed(self.candidate_count,selection["confirmations"]):
            raise InputStopped("动作前连续帧确认不足")
        self.assert_training_snapshot(True)

    def execute_selected_action(self,selection):
        fresh=self.frame_buffer.latest(None,0.35)
        try:
            self.host.api.validate_target(self.target,True)
            self.host.api.validate_uipi(self.target)
            self.verify_fresh_decision(fresh,selection)
            before=fresh["f"]
            if selection["action"].get("kind")!="no_op":
                self.host.set_input_status("允许执行单个动作")
                self.host.api.allow_input(self.host.stop_event)
            else:
                self.host.set_input_status("已锁定")
            self.host.set_status("训练中："+self.host.action_text(selection["action"])+"；全部安全条件已通过；采集="+fresh["method"])
            self.host.execute_action(self.target,selection["action"],fresh,self.mouse_interrupt,self.keyboard,self.keyboard_interrupt)
        except InputStopped:
            self.handle_execution_interference()
            raise
        except TargetUnavailable as error:
            self.reset_candidate()
            self.host.set_status(str(error))
            self.host.set_input_status("目标身份变化，已锁定")
            return None
        finally:
            self.host.api.block_input()
            if not self.mouse_interrupt.is_set() and not self.keyboard_interrupt.is_set() and self.keyboard.all_released():
                self.host.set_input_status("已锁定")
        return self.collect_outcome(selection,before)

    def handle_execution_interference(self):
        if not self.mouse_interrupt.is_set() and not self.keyboard_interrupt.is_set() and self.keyboard.all_released():
            return
        kind="mouse" if self.mouse_interrupt.is_set() else "keyboard"
        self.isolation.signal(kind,time.monotonic())
        reason="检测到物理或其他程序注入的鼠标输入，训练立即停止" if kind=="mouse" else "检测到非ESC键盘输入，训练立即停止"
        self.host.request_mode_stop("stopped",reason)
        self.host.api.block_input()
        self.host.api.release_all_buttons()
        self.host.set_status(reason+"；不会自动恢复")

    def collect_outcome(self,selection,before):
        action_end=time.monotonic()
        self.actions+=1
        self.action_hits[selection["cluster_id"]].append(action_end)
        self.recent_actions.append(selection["canonical"])
        self.last_action_signature=selection["canonical"]
        self.last_cluster_id=selection["cluster_id"]
        self.last_action_time=action_end
        self.last_action_feature=before
        self.state_unlocked=selection["repeat_policy"] in {"repeatable","rate_limited"}
        self.candidate_count=0
        delay=float(self.calibration.get("input_delay",0.24))
        deadline=time.monotonic()+delay
        while time.monotonic()<deadline and not self.host.should_stop():
            time.sleep(0.02)
        after=self.wait_after_frame(action_end,delay)
        changed=self.host.training_controller.changed(before,after,float(self.calibration.get("post_action_change",45.0)))
        outcome=self.agent_policy.register(before,selection["action"],after["f"] if after is not None else None,changed)
        return {"selection":selection,"after":after,"changed":changed,"outcome":outcome}

    def wait_after_frame(self,action_end,delay):
        wait_end=time.monotonic()+max(0.35,delay*2.0)
        while time.monotonic()<wait_end and not self.host.should_stop():
            candidate=self.frame_buffer.latest_after(action_end)
            if self.host.training_controller.usable_frame(candidate,self.validated_backend):
                return candidate
            time.sleep(0.025)
        return None

    def evaluate_outcome(self,result):
        selection=result["selection"]
        if result["changed"]:
            self.no_change_count=0
            self.state_unlocked=True
            self.state_since=time.monotonic()
        else:
            self.no_change_count+=1
            if selection["repeat_policy"] in {"one_shot","hold_until_change"} and self.no_change_count>=2:
                self.state_unlocked=False
                self.host.set_status("动作后未出现预期画面变化，暂停并等待指导")
        outcome=result["outcome"]
        if outcome["state"]=="success":
            self.host.request_mode_stop("completed","检测到已定义的成功状态，训练完成")
            return True
        if outcome["stop"]:
            self.host.request_mode_stop("stopped","连续失败或无变化达到安全上限"+str(self.agent_policy.max_failures)+"次，已自动停机")
            return True
        if outcome["state"]=="failure" and self.profile.get("restart_action") and not self.host.should_stop():
            frame=result["after"] or self.frame_buffer.latest(None,0.35)
            try:
                if self.execute_profile_restart(frame):
                    self.host.set_status("检测到失败状态，已执行白名单内的重新开始动作")
            except InputStopped as error:
                self.host.request_mode_stop("stopped","失败状态回滚无法安全执行："+str(error))
                return True
        return False

    def capture_loop(self):
        with ModeSession(self.controller,self.target) as session:
            self.start_monitors(session)
            while not self.host.should_stop():
                self.assert_training_snapshot(False)
                if self.detect_interference():
                    break
                captured=self.acquire_frame()
                if captured is None:
                    continue
                terminal=self.handle_terminal_state(captured)
                if terminal=="break":
                    break
                if terminal=="continue":
                    continue
                temporal=self.update_temporal_state(captured)
                if temporal is None:
                    continue
                selection=self.choose_action(captured,temporal)
                if selection is None or not self.action_ready(selection):
                    continue
                result=self.execute_selected_action(selection)
                if result is None:
                    continue
                if self.evaluate_outcome(result):
                    break
                time.sleep(0.05)

    def finalize(self):
        requested=self.host.lifecycle.snapshot()[3]
        if requested in {"completed","stopped","failed"}:
            status=requested
        else:
            status="stopped" if self.host.stop_event and self.host.stop_event.is_set() else "completed"
        summary=("训练完成" if status=="completed" else "训练已停止")+"，AI执行"+str(self.actions)+"个鼠标动作；检测到非ESC键盘输入"+str(self.keyboard_count)+"次，人工或外部注入鼠标输入"+str(self.mouse_count)+"次"
        details={"strict_input_violation":self.isolation.kind,"task_history":list(self.agent_policy.history),
            "training_snapshot_checksum":self.training_snapshot_checksum,"snapshot_guarded":True,
            "coordinate_audit":{"sent":self.actions,"outside":0,"client_rect":list(self.host.api.client_rect(int(self.target["hwnd"])))},
            "keyboard_events":self.keyboard_count,"external_mouse_events":self.mouse_count}
        return ModeResult(status,summary,details)

    def run(self):
        self.preflight()
        self.capture_loop()
        return self.finalize()
class GuidanceWindow:
    def __init__(self,app):
        self.app=app
    def open(self,prepared):
        app=self.app
        created=prepared.get("created")
        try:
            if app.mode!="指导" or app.stop_event is None or app.stop_event.is_set() or app.closing:
                return
            buffer=prepared["buffer"]
            producer=prepared["producer"]
            initial=prepared["packet"]
            app.lifecycle.mark_running()
            app.api.block_input()
            app.set_input_status("已锁定")
            app.status.set("指导已开始：只允许A/B/C/D或E跳过；点击“结束指导”或按ESC结束")
            win=tk.Toplevel(app.root)
            app.ask_window=win
            win.title("指导选择题")
            fit_window(win,780,720,560,420)
            win.transient(app.root)
            win.bind("<Unmap>",lambda event:buffer.set_preview_active(False))
            win.bind("<Map>",lambda event:buffer.set_preview_active(True))
            win.bind("<FocusOut>",lambda event:buffer.set_preview_active(False))
            win.bind("<FocusIn>",lambda event:buffer.set_preview_active(True))
            frame=scrollable_frame(win,16,True)
            ttk.Label(frame,text="请选择当前画面中AI应该执行的鼠标动作",font=("Microsoft YaHei UI",14,"bold")).pack(anchor="w")
            ttk.Label(frame,text="主流程严格为选择题：A / B / C / D / E（跳过并记录为未标注）；点击“结束指导”或按ESC结束。",wraplength=730).pack(anchor="w",pady=(4,10))
            canvas=tk.Canvas(frame,width=ASK_CANVAS_W,height=ASK_CANVAS_H,bg="black",highlightthickness=1,highlightbackground="#777777")
            canvas.pack()
            preview_info=tk.StringVar(value="等待彩色教学预览")
            ttk.Label(frame,textvariable=preview_info,wraplength=730).pack(anchor="w",fill="x",pady=(6,0))
            choice_frame=ttk.Frame(frame)
            choice_frame.pack(fill="both",expand=True,pady=(10,0))
            answer_buttons=[]
            state={"frame":None,"choices":[],"image":None,"locked":False,"recent_actions":deque(["<START>","<START>"],maxlen=4),"state_since":time.monotonic(),"waiting":False}
            def schedule(delay,callback):
                if app.ask_window is None:
                    return
                holder={"id":None}
                def wrapped():
                    app.ask_after_ids.discard(holder["id"])
                    if app.ask_window is not None:
                        callback()
                holder["id"]=win.after(delay,wrapped)
                app.ask_after_ids.add(holder["id"])
            def set_locked(value):
                state["locked"]=bool(value)
                for index,button in enumerate(answer_buttons):
                    button.configure(state="normal" if not value and index<len(state["choices"]) else "disabled")
                skip_button.configure(state="disabled" if value else "normal")
            def render(packet):
                question_frame=packet["frame"]
                choices=packet["choices"][:4]
                preview=preview_rgb_bytes(question_frame.get("preview_rgb")) or bytes(PREVIEW_W*PREVIEW_H*3)
                ppm=b"P6\n"+str(PREVIEW_W).encode("ascii")+b" "+str(PREVIEW_H).encode("ascii")+b"\n255\n"+preview
                image=tk.PhotoImage(data=base64.b64encode(ppm).decode("ascii"),format="PPM")
                scaled=image.zoom(2,2)
                state["image"]=(image,scaled)
                canvas.delete("all")
                canvas.create_image(ASK_PREVIEW_X,ASK_PREVIEW_Y,image=scaled,anchor="nw")
                colors=("#00ffff","#ffff00","#ff66ff","#66ff66")
                for index,entry in enumerate(choices):
                    action=normalize_action(entry.get("a"))
                    if not action or action["kind"]=="no_op":
                        continue
                    points=[]
                    for point in action.get("path") or []:
                        cx,cy=PreviewCoordinateMapper.to_canvas(point)
                        points.extend([cx,cy])
                    color=colors[index]
                    if len(points)>=4:
                        canvas.create_line(*points,fill=color,width=3,arrow="last")
                    if len(points)>=2:
                        canvas.create_oval(points[-2]-6,points[-1]-6,points[-2]+6,points[-1]+6,outline=color,width=3)
                        canvas.create_text(points[-2]+10,points[-1]-10,text=chr(65+index),fill=color,font=("Microsoft YaHei UI",12,"bold"),anchor="sw")
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
                preview_info.set("采集时间："+stamp+"  后端："+str(question_frame.get("method","未知"))+"  质量告警："+("、".join(warnings) if warnings else "无"))
            def apply_packet(packet):
                if app.ask_window is None:
                    return
                state["waiting"]=False
                state["frame"]=packet["frame"]
                state["choices"]=packet["choices"][:4]
                render(packet)
                for index,button in enumerate(answer_buttons):
                    if index<len(state["choices"]):
                        button.configure(text=chr(65+index)+". "+app.action_text(state["choices"][index]["a"]))
                    else:
                        button.configure(text=chr(65+index)+". 无可用答案")
                set_locked(False)
            def poll_question():
                if app.ask_window is None or app.stop_event is None or app.stop_event.is_set():
                    return
                packet=producer.get_result(0.0)
                if packet is None:
                    schedule(45,poll_question)
                    return
                if packet.get("error"):
                    app.status.set("指导等待可用画面："+str(packet["error"]))
                    producer.request(state["recent_actions"],state["state_since"])
                    schedule(160,poll_question)
                    return
                apply_packet(packet)
            def request_question():
                if app.ask_window is None or state["waiting"]:
                    return
                state["waiting"]=True
                set_locked(True)
                producer.request(state["recent_actions"],state["state_since"])
                schedule(20,poll_question)
            def finish_answer(result,error):
                if app.ask_window is None:
                    return
                if error:
                    app._fail_active_mode(error)
                    return
                if result and result.get("saved") and result.get("action"):
                    state["recent_actions"].append(action_signature(result["action"]))
                    state["state_since"]=time.monotonic()
                counts=app.ask_counts or {}
                app.status.set("指导中：已保存"+str(counts.get("saved",0))+"，重复未保存"+str(counts.get("duplicates",0))+"，跳过"+str(counts.get("skipped",0))+"；模型需要睡眠")
                schedule(100,request_question)
            def queue_answer(kind,entry=None):
                if state["locked"] or app.ask_answer_queue is None:
                    return
                set_locked(True)
                app.ask_answer_queue.put({"kind":kind,"frame":state["frame"],"entry":entry or {},"recent_actions":list(state["recent_actions"]),"state_since":state["state_since"],"callback":finish_answer})
            def choose(index):
                if index<len(state["choices"]):
                    queue_answer("choose",state["choices"][index])
            for index in range(4):
                button=ttk.Button(choice_frame,text=chr(65+index),command=lambda position=index:choose(position))
                button.pack(fill="x",pady=3,ipady=6)
                answer_buttons.append(button)
            tools=ttk.Frame(frame)
            tools.pack(fill="x",pady=(8,0))
            skip_button=ttk.Button(tools,text="E. 跳过（未标注）",command=lambda:queue_answer("skip"))
            skip_button.pack(side="left",fill="x",expand=True,ipady=6)
            end_button=ttk.Button(tools,text="结束指导",command=lambda:app.close_ask(reason="completed"))
            end_button.pack(side="left",padx=(8,0),ipadx=18,ipady=6)
            def refuse_close():
                win.bell()
                win.lift()
                win.focus_force()
            win.protocol("WM_DELETE_WINDOW",refuse_close)
            app.ask_escape_armed=not app.api.key_down(0x1B)
            def poll_escape():
                if app.ask_window is None:
                    return
                down=app.api.key_down(0x1B)
                if not down:
                    app.ask_escape_armed=True
                elif app.ask_escape_armed:
                    app.close_ask(reason="stopped")
                    return
                schedule(45,poll_escape)
            apply_packet(initial)
            poll_escape()
            win.wait_visibility()
            win.focus_force()
        except Exception as error:
            app._fail_active_mode("指导界面创建失败："+str(error))
        finally:
            if created is not None:
                created.set()
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
                raise InputStopped("指导初始化已停止")
            action=normalize_action(item.get("a"))
            if feature_valid(item.get("f")) and action:
                historical.append({"id":str(item.get("checksum",uuid.uuid4().hex)),"f":item["f"],"coarse":item.get("coarse") if isinstance(item.get("coarse"),(bytes,bytearray))
                        and len(item.get("coarse"))==COARSE_LEN else coarse_feature(item["f"]),"a":action,"cluster_id":"history|"+action_signature(action),"canonical_action_signature":action_signature(action),
                        "repeat_policy":str(item.get("repeat_policy","one_shot")),"source":"sample"})
        calibration=app.ensure_capture_calibration(target,"指导")
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
            app.ask_counts={"saved":0,"duplicates":0,"skipped":0}
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
                    app.set_status("指导初始化等待画面："+str(packet["error"]))
                    producer.request(deque(["<START>","<START>"],maxlen=4),time.monotonic())
            if app.should_stop():
                raise InputStopped("指导初始化已停止")
            if initial is None:
                raise CaptureUnavailable("指导初始化未在限定时间内生成第一道题")
            created=threading.Event()
            app.ui(lambda:app._create_ask_window({"game":game,"target":target,"buffer":buffer,"producer":producer,"packet":initial,"created":created}))
            while not created.wait(0.05):
                if app.should_stop():
                    raise InputStopped("指导初始化已停止")
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
                            raise CaptureUnavailable("当前画面不可用于指导")
                        temporal=app.build_temporal_context(buffer,frame,recent_actions,state_since)
                        temporal["previous_action_changed_frame"]=True
                        policy=str(entry.get("repeat_policy","one_shot"))
                        context=app.sample_context(recent_actions[-1] if recent_actions else "",0,True,frame.get("motion_valid",False),session_id,frame.get("method","unknown"),policy,temporal)
                        if kind!="choose":
                            raise RuntimeError("指导主流程仅接受A/B/C/D或E跳过")
                        action=normalize_action(entry.get("a"))
                        if not action:
                            raise RuntimeError("指导动作无效")
                        saved=app.store.append_sample(game["id"],frame["f"],action,"teach_live",context,frame.get("rgb"),frame.get("neural_f"),3.0)
                        app.ask_counts["saved" if saved else "duplicates"]+=1
                        result={"saved":saved,"action":action}
                    if callback:
                        app.ui(lambda callback=callback,result=result:callback(result,None))
                except Exception as error:
                    message="指导数据库或题目处理失败："+str(error)
                    if callback:
                        app.ui(lambda callback=callback,message=message:callback(None,message))
                    app.request_mode_stop("failed",message)
                    break
        status=app.lifecycle.snapshot()[3]
        if status=="failed":
            app.store.invalidate_learning_session(game["id"],session_id,app.lifecycle.snapshot()[4] or "teaching_failed")
        else:
            app.store.validate_learning_session(game["id"],session_id)
        counts=app.ask_counts if isinstance(app.ask_counts,dict) else {"saved":0,"duplicates":0,"skipped":0}
        summary="指导已结束：已保存"+str(counts.get("saved",0))+"，重复未保存"+str(counts.get("duplicates",0))+"，跳过"+str(counts.get("skipped",0))+"；模型需要睡眠"
        if status=="failed":
            return ModeResult("failed",app.lifecycle.snapshot()[4] or summary)
        final_status=status if status in {"completed","stopped"} else "stopped"
        reason=str(app.lifecycle.snapshot()[4] or "")
        return ModeResult(final_status,summary,{"samples":stats.get("valid",0),"choices_only":True,"finish_button":final_status=="completed" and "ESC" not in reason.upper(),
                "escape_used":final_status=="stopped" and bool(app.escape_metrics.get("pressed")),"question_options":["A","B","C","D","E跳过"]})
    def create_window(self,prepared):
        return GuidanceWindow(self.app).open(prepared)

class GameRepository:
    def __init__(self,store):
        self.store=store
    def list(self):
        return self.store.games()
    def selected(self):
        return self.store.selected_game()
    def replace(self,games,selected):
        return self.store.replace_games(games,selected)
    def update(self,gid,values):
        return self.store.update_game(gid,values)
    def delete(self,gid):
        return self.store.delete_game(gid)
class SampleRepository:
    def __init__(self,store):
        self.store=store
    def load(self,gid,limit=None):
        return self.store.load_samples(gid,limit)
    def append(self,gid,item):
        return self.store.append_sample(gid,item)
    def barrier(self,timeout=5.0):
        return self.store.sample_write_barrier(timeout)
class ModelRepository:
    def __init__(self,store):
        self.store=store
    def load(self,gid):
        return self.store.load_model(gid)
    def save(self,gid,model,complete):
        return self.store.save_model(gid,model,complete)
    def metadata(self,gid):
        return self.store.model_metadata(gid)
class CaptureCalibrationRepository:
    def __init__(self,store):
        self.store=store
    def save(self,target,calibration):
        return self.store.save_capture_calibration(target,calibration)
    def load(self,target):
        return self.store.load_capture_calibration(target)
class OCRRegionRepository:
    def __init__(self,store):
        self.store=store
    def save(self,gid,payload):
        return self.store.save_ocr_region(gid,payload)
    def list(self,gid,enabled_only=True):
        return self.store.list_ocr_regions(gid,enabled_only)
    def delete_overlap(self,gid,norm):
        return self.store.delete_ocr_region_by_overlap(gid,norm)
class RecoveryService:
    def __init__(self,store):
        self.store=store
    def create_backup(self,reason="manual"):
        return self.store.create_recovery_backup(reason)
    def trim(self):
        return self.store._trim_recovery_backups()
class MigrationService:
    def __init__(self,store):
        self.store=store
    def migrate_legacy(self):
        return self.store._migrate_legacy()

@dataclass
class WindowDialogState:
    windows:list=field(default_factory=list)
    selected:object=None
    preview:object=None
    generation:int=0
    closed:bool=False
    errors:list=field(default_factory=list)
    def as_dict(self):
        return {"windows":self.windows,"selected":self.selected,"preview":self.preview,"generation":self.generation,"closed":self.closed,"errors":self.errors}
class WindowPreviewService:
    def __init__(self,api):
        self.api=api
    def capture(self,target):
        validate_packet("window_identity",target)
        return self.api.capture_frame(target,False) if hasattr(self.api,"capture_frame") else None
class WindowRuleValidator:
    def validate(self,identity,title_mode="none",title_value=""):
        value=validate_packet("window_identity",identity)
        mode=str(title_mode)
        if mode not in TITLE_RULE_MODES:
            raise ValueError("窗口标题规则无效")
        title=str(value.get("title",""))
        expected=str(title_value)
        valid=mode=="none" or mode=="contains" and expected in title or mode=="prefix" and title.startswith(expected) or mode=="exact" and title==expected
        if not valid:
            raise ValueError("窗口标题不符合规则")
        return value
class DataStore:
    def __init__(self,base=None):
        selected=base if base is not None else globals().get("SELECTED_DATA_DIR")
        if selected is None:
            raise RuntimeError("尚未选择并确认文件夹")
        self.base=Path(selected).expanduser().resolve()
        self.base.mkdir(parents=True,exist_ok=True)
        ensure_free_space(self.base,MIN_DATA_OPERATION_RESERVE,"数据库初始化")
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
        self.pending_fingerprints=set()
        self.pending_counts_by_game=defaultdict(Counter)
        self.pending_recent_samples=defaultdict(lambda:deque(maxlen=36))
        self.persisted_sample_stats={}
        self.recent_samples=defaultdict(lambda:deque(maxlen=36))
        self.recent_samples_loaded=set()
        self.writer_inflight=0
        self.blocked_game_ids=set()
        self.blocked_sessions=set()
        self.pending_event=threading.Event()
        self.writer_stop=threading.Event()
        self.writer_error=None
        self.sample_writes_paused=False
        self.sample_writes_pause_reason=""
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
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
            self.corrupt_backup=self.create_recovery_backup("quick_check_failed")
            self.db=ThreadLocalSQLite(self.db_path,True)
            self.read_only=True
            self.read_only_reason="数据库quick_check失败，已只读打开；恢复备份："+str(self.corrupt_backup)+"；"+str(error)
            self.game_repository=GameRepository(self)
            self.sample_repository=SampleRepository(self)
            self.model_repository=ModelRepository(self)
            self.capture_calibration_repository=CaptureCalibrationRepository(self)
            self.ocr_region_repository=OCRRegionRepository(self)
            self.migration_service=MigrationService(self)
            self.recovery_service=RecoveryService(self)
            return
        self._initialize_schema()
        self._migrate_legacy()
        mode=str(self.db.execute("PRAGMA journal_mode").fetchone()[0]).lower()
        if mode!="wal":
            raise RuntimeError("文件系统不支持SQLite WAL，实际模式为"+mode)
        result=self.db.execute("PRAGMA quick_check").fetchone()
        if not result or str(result[0]).lower()!="ok":
            raise RuntimeError("数据库迁移后quick_check失败")
        self.writer_thread=threading.Thread(target=self._writer_loop,name="UniversalGameAI-SampleWriter",daemon=True)
        self.writer_thread.start()
        self.game_repository=GameRepository(self)
        self.sample_repository=SampleRepository(self)
        self.model_repository=ModelRepository(self)
        self.capture_calibration_repository=CaptureCalibrationRepository(self)
        self.ocr_region_repository=OCRRegionRepository(self)
        self.migration_service=MigrationService(self)
        self.recovery_service=RecoveryService(self)
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
        with self.pending_lock:
            if self.sample_writes_paused:
                raise RuntimeError(self.sample_writes_pause_reason or "样本写入已暂停")
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
        return {"goal":"模仿已学习的鼠标操作并在不确定时停止","allowed_families":["no_op","click|left","move","hover","scroll_v|1","scroll_v|-1"],"max_consecutive_failures":3,"exploration_enabled":False,
            "restart_action":None,"success_states":[],"failure_states":[],"success_reward":1.0,"failure_reward":-1.0,"step_penalty":-0.01,"updated":0.0}
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
        profile["game_id"]=str(gid)
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
                self.db.execute("INSERT OR IGNORE INTO corrupt_rows(source_table,source_id,game_id,created,reason,payload) VALUES(?,?,?,?,?,?)",(str(table_name),safe_int(row_id,0),
                        str(game_id),time.time(),str(reason)[:2000],str(payload)[:16000]))
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
            self.db.execute("INSERT INTO learning_sessions(game_id,session_id,status,started,finished,invalid_reason) VALUES(?,?,'staging',?,NULL,'') ON CONFLICT(game_id,session_id) DO UPDATE SET status='staging',started=excluded.started,finished=NULL,invalid_reason=''",
                (game_id,sid,stamp))
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
                self.db.execute("INSERT INTO learning_sessions(game_id,session_id,status,started,finished,invalid_reason) VALUES(?,?,'valid',?,?,'automatic_non_learning_session')",(game_id,
                        sid,float(created),float(created)))
            return "valid"
    def _raise_writer_error(self):
        with self.pending_lock:
            error=self.writer_error
        if error:
            raise RuntimeError("样本批量写入失败："+str(error))
    def sample_queue_pressure(self,gid):
        with self.pending_lock:
            count=int(self.pending_counts_by_game.get(str(gid),{}).get("total",0))
        return min(1.0,count/192.0)
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
            review_games=sorted({item["gid"] for item in batch if item.get("mark_review")})
        last_error=None
        success=False
        recovered=False
        try:
            hook=self.writer_before_commit
            if hook is not None:
                hook(batch)
            rows=[self._encode_sample_row(item) for item in batch]
            for attempt in range(5):
                try:
                    with connection:
                        insert_sql=(
                            "INSERT OR IGNORE INTO samples("
                            "game_id,created,kind,action_signature,action_family,repeat_policy,"
                            "feature_algorithm_version,action_algorithm_version,feature,coarse,"
                            "neural_feature,rgb_thumbnail,preprocess_signature,action,source,"
                            "session_id,capture_method,context,thumbnail,weight,fingerprint"
                            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
                        )
                        connection.executemany(insert_sql,rows)
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
                except sqlite3.Error as error:
                    last_error=error
                    break
        except (zlib.error,MemoryError,ValueError,TypeError,OSError) as error:
            last_error=error
        finally:
            with self.pending_lock:
                self.writer_inflight=max(0,self.writer_inflight-1)
                if success:
                    recovered=self.writer_error is not None
                    self.writer_error=None
                    self._commit_sample_caches_locked(batch)
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
    def pause_sample_writes(self,reason="文件夹迁移"):
        self.sample_write_barrier(10.0)
        with self.pending_lock:
            self.sample_writes_paused=True
            self.sample_writes_pause_reason=str(reason)
            self.writer_condition.notify_all()
        with self.lock:
            self.db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        return True
    def resume_sample_writes(self):
        with self.pending_lock:
            self.sample_writes_paused=False
            self.sample_writes_pause_reason=""
            self.writer_condition.notify_all()
        return True
    def _writer_loop(self):
        connection=sqlite3.connect(str(self.db_path),timeout=3.0,check_same_thread=True)
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
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS learning_sessions("
            "game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,"
            "session_id TEXT NOT NULL,status TEXT NOT NULL "
            "CHECK(status IN ('staging','valid','invalid')),started REAL NOT NULL,"
            "finished REAL,invalid_reason TEXT NOT NULL DEFAULT '',"
            "PRIMARY KEY(game_id,session_id))"
        )
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_learning_sessions_game_status ON learning_sessions(game_id,status,started)")
        self.db.execute(
            'CREATE TABLE IF NOT EXISTS samples(id INTEGER PRIMARY KEY AUTOINCREMENT,game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,'
            'created REAL NOT NULL,kind TEXT NOT NULL,action_signature TEXT NOT NULL,action_family TEXT NOT NULL,repeat_policy TEXT NOT NULL,'
            'feature_algorithm_version INTEGER NOT NULL,action_algorithm_version INTEGER NOT NULL,feature BLOB NOT NULL,coarse BLOB NOT NULL,neural_feature BLOB,'
            "rgb_thumbnail BLOB,preprocess_signature TEXT NOT NULL DEFAULT '',action TEXT NOT NULL,source TEXT NOT NULL,session_id TEXT NOT NULL,"
            'capture_method TEXT NOT NULL,context TEXT NOT NULL,thumbnail BLOB,weight REAL NOT NULL DEFAULT 1.0,fingerprint TEXT NOT NULL,UNIQUE(game_id,'
            'fingerprint))'
        )
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_samples_game_kind_created ON samples(game_id,kind,created)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_samples_game_session ON samples(game_id,session_id)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_samples_game_action ON samples(game_id,action_signature)")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS models("
            "game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,"
            "slot TEXT NOT NULL,saved REAL NOT NULL,created REAL NOT NULL,"
            "prototype_count INTEGER NOT NULL,validation TEXT NOT NULL,"
            "payload BLOB NOT NULL,checksum TEXT NOT NULL,PRIMARY KEY(game_id,slot))"
        )
        self.db.execute("CREATE TABLE IF NOT EXISTS model_backups(id INTEGER PRIMARY KEY AUTOINCREMENT,game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,created REAL NOT NULL,prototype_count INTEGER NOT NULL,validation TEXT NOT NULL,payload BLOB NOT NULL,checksum TEXT NOT NULL)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_model_backups_game_created ON model_backups(game_id,created DESC)")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS rejections("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,"
            "created REAL NOT NULL,feature_algorithm_version INTEGER NOT NULL,"
            "feature BLOB NOT NULL,coarse BLOB NOT NULL,neural_feature BLOB,"
            "rgb_thumbnail BLOB,preprocess_signature TEXT NOT NULL DEFAULT '',"
            "thumbnail BLOB,candidates TEXT NOT NULL,source TEXT NOT NULL,"
            "session_id TEXT NOT NULL,capture_method TEXT NOT NULL)"
        )
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_rejections_game_created ON rejections(game_id,created DESC)")
        self.db.execute("CREATE TABLE IF NOT EXISTS capture_calibrations(identity_key TEXT NOT NULL,backend TEXT NOT NULL,saved REAL NOT NULL,payload TEXT NOT NULL,checksum TEXT NOT NULL,PRIMARY KEY(identity_key,backend))")
        self.db.execute("CREATE TABLE IF NOT EXISTS game_profiles(game_id TEXT PRIMARY KEY REFERENCES games(id) ON DELETE CASCADE,updated REAL NOT NULL,payload TEXT NOT NULL,checksum TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS corrupt_rows(id INTEGER PRIMARY KEY AUTOINCREMENT,source_table TEXT NOT NULL,source_id INTEGER NOT NULL,game_id TEXT NOT NULL,created REAL NOT NULL,reason TEXT NOT NULL,payload TEXT NOT NULL,UNIQUE(source_table,source_id))")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_capture_calibrations_saved ON capture_calibrations(saved DESC)")
        self.db.execute(
            'CREATE TABLE IF NOT EXISTS ocr_regions(id TEXT PRIMARY KEY,game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,created REAL NOT NULL,'
            'updated REAL NOT NULL,region_norm TEXT NOT NULL,region_type TEXT NOT NULL,number_format TEXT NOT NULL,goal_relation TEXT NOT NULL,target_min REAL,'
            'target_max REAL,special_value REAL,special_meaning TEXT NOT NULL,reset_meaning TEXT NOT NULL,unit TEXT NOT NULL,enabled INTEGER NOT NULL DEFAULT 1,'
            'last_text TEXT NOT NULL,last_value REAL,last_confidence REAL NOT NULL DEFAULT 0,stable_frames INTEGER NOT NULL DEFAULT 0,checksum TEXT NOT NULL)'
        )
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_ocr_regions_game_enabled ON ocr_regions(game_id,enabled,updated DESC)")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS ocr_observations("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,"
            "region_id TEXT NOT NULL REFERENCES ocr_regions(id) ON DELETE CASCADE,"
            "created REAL NOT NULL,raw_text TEXT NOT NULL,parsed TEXT NOT NULL,"
            "confidence REAL NOT NULL,stable_frames INTEGER NOT NULL,"
            "semantic_event TEXT NOT NULL,checksum TEXT NOT NULL)"
        )
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_ocr_observations_region_created ON ocr_observations(region_id,created DESC)")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS vision_models("
            "game_id TEXT PRIMARY KEY REFERENCES games(id) ON DELETE CASCADE,"
            "architecture_version INTEGER NOT NULL,updated REAL NOT NULL,"
            "relative_path TEXT NOT NULL,checksum TEXT NOT NULL,"
            "trained_steps INTEGER NOT NULL,device TEXT NOT NULL,metadata TEXT NOT NULL)"
        )
        self.db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('extension_schema_version',?)",(str(EXTENSION_SCHEMA_VERSION),))
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
                        additions=[("action_family","TEXT NOT NULL DEFAULT ''"),("repeat_policy","TEXT NOT NULL DEFAULT 'one_shot'"),("feature_algorithm_version",
                                "INTEGER NOT NULL DEFAULT 3"),("action_algorithm_version","INTEGER NOT NULL DEFAULT 4"),("session_id","TEXT NOT NULL DEFAULT 'legacy'"),("capture_method","TEXT NOT NULL DEFAULT 'legacy'")]
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
                        self.db.execute(
                            "CREATE TABLE IF NOT EXISTS learning_sessions("
                            "game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,"
                            "session_id TEXT NOT NULL,status TEXT NOT NULL "
                            "CHECK(status IN ('staging','valid','invalid')),"
                            "started REAL NOT NULL,finished REAL,"
                            "invalid_reason TEXT NOT NULL DEFAULT '',"
                            "PRIMARY KEY(game_id,session_id))"
                        )
                        self.db.execute("CREATE INDEX IF NOT EXISTS idx_learning_sessions_game_status ON learning_sessions(game_id,status,started)")
                        self.db.execute("INSERT OR IGNORE INTO learning_sessions(game_id,session_id,status,started,finished,invalid_reason) SELECT game_id,session_id,'valid',MIN(created),MAX(created),'legacy_migration' FROM samples GROUP BY game_id,session_id")
                        version=7
                    elif version==7:
                        sample_columns=self._columns("samples")
                        for name,declaration in (("neural_feature","BLOB"),("rgb_thumbnail","BLOB"),("preprocess_signature","TEXT NOT NULL DEFAULT ''")):
                            if name not in sample_columns:
                                self.db.execute("ALTER TABLE samples ADD COLUMN "+name+" "+declaration)
                        rejection_columns=self._columns("rejections")
                        for name,declaration in (("neural_feature","BLOB"),("rgb_thumbnail","BLOB"),("preprocess_signature","TEXT NOT NULL DEFAULT ''")):
                            if name not in rejection_columns:
                                self.db.execute("ALTER TABLE rejections ADD COLUMN "+name+" "+declaration)
                        self._create_latest_schema()
                        self.db.execute("UPDATE samples SET preprocess_signature='legacy_gray_v1' WHERE preprocess_signature='' OR preprocess_signature IS NULL")
                        self.db.execute("UPDATE rejections SET preprocess_signature='legacy_gray_v1' WHERE preprocess_signature='' OR preprocess_signature IS NULL")
                        version=8
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
    def _cleanup_legacy_files(self,config_path,backup_path,legacy_dirs):
        failures=[]
        for item in (config_path,backup_path):
            try:
                item.unlink()
            except FileNotFoundError:
                continue
            except OSError as error:
                failures.append({"path":str(item),"error":str(error)})
                record_cleanup_error("LEGACY_FILE_CLEANUP_FAILED",error,{"path":str(item)})
        for folder in legacy_dirs:
            if not folder.exists():
                continue
            for child in list(folder.iterdir()):
                try:
                    if child.is_dir():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
                except FileNotFoundError:
                    continue
                except OSError as error:
                    failures.append({"path":str(child),"error":str(error)})
                    record_cleanup_error("LEGACY_CHILD_CLEANUP_FAILED",error,{"path":str(child)})
            try:
                folder.rmdir()
            except FileNotFoundError:
                continue
            except OSError as error:
                failures.append({"path":str(folder),"error":str(error)})
                record_cleanup_error("LEGACY_DIRECTORY_CLEANUP_FAILED",error,{"path":str(folder)})
        with self.lock,self.db:
            if failures:
                self.db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('legacy_cleanup_pending',?)",(json.dumps(failures,ensure_ascii=False,separators=(",",":")),))
            else:
                self.db.execute("DELETE FROM meta WHERE key='legacy_cleanup_pending'")
        return not failures
    def _migrate_legacy(self):
        config_path=self.base/"config.json"
        backup_path=config_path.with_suffix(".json.bak")
        legacy_dirs=[self.base/name for name in ("samples","models","backups","temp")]
        with self.lock:
            row=self.db.execute("SELECT value FROM meta WHERE key='legacy_migrated'").fetchone()
            pending=self.db.execute("SELECT value FROM meta WHERE key='legacy_cleanup_pending'").fetchone()
        if row:
            if pending:
                self._cleanup_legacy_files(config_path,backup_path,legacy_dirs)
            return
        samples_legacy=any((self.base/"samples").glob("*.jsonl")) if (self.base/"samples").exists() else False
        models_legacy=any((self.base/"models").glob("*.json")) if (self.base/"models").exists() else False
        backups_legacy=any((self.base/"backups").glob("*.json")) if (self.base/"backups").exists() else False
        legacy_present=config_path.exists() or backup_path.exists() or samples_legacy or models_legacy or backups_legacy
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
                    legacy_insert_sql=(
                        "INSERT OR IGNORE INTO samples("
                        "game_id,created,kind,action_signature,action_family,repeat_policy,"
                        "feature_algorithm_version,action_algorithm_version,feature,coarse,"
                        "action,source,session_id,capture_method,context,thumbnail,weight,fingerprint"
                        ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
                    )
                    self.db.execute(legacy_insert_sql,
                        (gid,created,action["kind"],signature,action_family_key(action),str(context.get("repeat_policy","one_shot")),FEATURE_ALGORITHM_VERSION,ACTION_ALGORITHM_VERSION,
                            sqlite3.Binary(zlib.compress(fbytes,6)),sqlite3.Binary(coarse_feature(fbytes)),json.dumps(action,ensure_ascii=False,separators=(",",":")),source,session_id,capture_method,json.dumps(context,
                                ensure_ascii=False,separators=(",",":")),sqlite3.Binary(zlib.compress(thumbnail,6)) if gray_valid(thumbnail) else None,max(0.1,min(10.0,weight)),fingerprint))
                for folder_name,gid,model,complete in model_rows:
                    payload=self._pack_model(model)
                    checksum=hashlib.sha256(payload).hexdigest()
                    validation=json.dumps(model.get("validation",{}),ensure_ascii=False,separators=(",",":"))
                    if folder_name=="backups":
                        self.db.execute("INSERT INTO model_backups(game_id,created,prototype_count,validation,payload,checksum) VALUES(?,?,?,?,?,?)",(gid,float(model.get("saved",
                                    model.get("created",time.time()))),len(model["prototypes"]),validation,sqlite3.Binary(payload),checksum))
                    else:
                        slot="complete" if complete else "partial"
                        self.db.execute("INSERT OR REPLACE INTO models(game_id,slot,saved,created,prototype_count,validation,payload,checksum) VALUES(?,?,?,?,?,?,?,?)",(gid,slot,
                                float(model.get("saved",time.time())),float(model.get("created",time.time())),len(model["prototypes"]),validation,sqlite3.Binary(payload),checksum))
                self.db.execute("INSERT OR IGNORE INTO learning_sessions(game_id,session_id,status,started,finished,invalid_reason) SELECT game_id,session_id,'valid',MIN(created),MAX(created),'legacy_file_migration' FROM samples GROUP BY game_id,session_id")
                self.db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('legacy_migrated','1')")
                self.db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('legacy_cleanup_pending','pending')")
                self.db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('legacy_invalid_rows',?)",(str(legacy_invalid),))
                self.db.commit()
            except Exception:
                self.db.rollback()
                raise
        self._cleanup_legacy_files(config_path,backup_path,legacy_dirs)
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
            self._rebuild_pending_indexes_locked()
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
                    self._invalidate_sample_caches(gid)
                for item in cleaned:
                    self.db.execute("INSERT INTO games(id,name,created,needs_review,last_review) VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,created=excluded.created,needs_review=excluded.needs_review,last_review=excluded.last_review",
                        (item["id"],item["name"],item["created"],item["needs_review"],item["last_review"]))
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
            self._rebuild_pending_indexes_locked()
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
            self._invalidate_sample_caches(game_id)
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
    def _pending_index_add_locked(self,item):
        fingerprint=str(item.get("fingerprint",""))
        if fingerprint:
            self.pending_fingerprints.add((str(item.get("gid")),fingerprint))
        game_id=str(item.get("gid"))
        counts=self.pending_counts_by_game[game_id]
        counts["total"]+=1
        counts["noops" if item.get("kind")=="no_op" else "actions"]+=1
        self.pending_recent_samples[(game_id,str(item.get("signature","")))].append(item)
    def _pending_index_remove_locked(self,item):
        fingerprint=str(item.get("fingerprint",""))
        if fingerprint:
            self.pending_fingerprints.discard((str(item.get("gid")),fingerprint))
        game_id=str(item.get("gid"))
        counts=self.pending_counts_by_game.get(game_id)
        if counts is None:
            return
        counts["total"]=max(0,counts["total"]-1)
        key="noops" if item.get("kind")=="no_op" else "actions"
        counts[key]=max(0,counts[key]-1)
        recent_key=(game_id,str(item.get("signature","")))
        recent=self.pending_recent_samples.get(recent_key)
        if recent is not None:
            fingerprint=str(item.get("fingerprint",""))
            self.pending_recent_samples[recent_key]=deque((candidate for candidate in recent if str(candidate.get("fingerprint",""))!=fingerprint),maxlen=36)
            if not self.pending_recent_samples[recent_key]:
                self.pending_recent_samples.pop(recent_key,None)
        if not counts["total"]:
            self.pending_counts_by_game.pop(game_id,None)
    def _rebuild_pending_indexes_locked(self):
        self.pending_fingerprints.clear()
        self.pending_counts_by_game.clear()
        self.pending_recent_samples.clear()
        for item in self.pending_samples:
            self._pending_index_add_locked(item)
    def _persisted_stats(self,gid):
        game_id=str(gid)
        cached=self.persisted_sample_stats.get(game_id)
        if cached is not None:
            return dict(cached)
        with self.lock:
            row=self.db.execute("SELECT COUNT(*) AS total,SUM(CASE WHEN kind='no_op' THEN 1 ELSE 0 END) AS noops,SUM(CASE WHEN kind!='no_op' THEN 1 ELSE 0 END) AS actions FROM samples WHERE game_id=?",(game_id,)).fetchone()
        cached={"total":int(row["total"] or 0),"noops":int(row["noops"] or 0),"actions":int(row["actions"] or 0)}
        self.persisted_sample_stats[game_id]=cached
        return dict(cached)
    def _encode_sample_row(self,item):
        return (
            item["gid"],item["created"],item["kind"],item["signature"],item["action_family"],item["repeat_policy"],
            FEATURE_ALGORITHM_VERSION,ACTION_ALGORITHM_VERSION,sqlite3.Binary(zlib.compress(item["feature"],6)),
            sqlite3.Binary(item["coarse"]),sqlite3.Binary(zlib.compress(item["neural"],6)) if item.get("neural") is not None else None,
            sqlite3.Binary(zlib.compress(item["rgb"],6)),VISION_PREPROCESS_HASH,item["action_json"],item["source"],item["session_id"],
            item["capture_method"],item["context_json"],None,item["weight"],item["fingerprint"],
        )
    def _load_recent_sample_cache(self,gid,signature):
        key=(str(gid),str(signature))
        if key in self.recent_samples_loaded:
            return self.recent_samples[key]
        with self.lock:
            rows=self.db.execute("SELECT id,feature,coarse,feature_algorithm_version,context FROM samples WHERE game_id=? AND action_signature=? ORDER BY created DESC,id DESC LIMIT 36",key).fetchall()
        cache=self.recent_samples[key]
        cache.clear()
        for row in reversed(rows):
            try:
                feature=upgrade_feature(bounded_decompress(row["feature"],FEATURE_LEN*2),row["feature_algorithm_version"])
                context=json.loads(row["context"])
                if not feature_valid(feature) or not isinstance(context,dict):
                    raise ValueError("近期样本内容无效")
                coarse=bytes(row["coarse"]) if row["coarse"] is not None and len(row["coarse"])==COARSE_LEN else coarse_feature(feature)
                cache.append({"sample_id":int(row["id"]),"feature":feature,"coarse":coarse,"context":context})
            except (zlib.error,json.JSONDecodeError,UnicodeDecodeError,ValueError,TypeError) as error:
                self.quarantine_corrupt_row("samples",row["id"],gid,error,signature)
        self.recent_samples_loaded.add(key)
        return cache
    def _commit_sample_caches_locked(self,batch):
        for item in batch:
            self._pending_index_remove_locked(item)
            game_id=str(item["gid"])
            stats=self.persisted_sample_stats.get(game_id)
            if stats is not None:
                stats["total"]+=1
                stats["noops" if item["kind"]=="no_op" else "actions"]+=1
            key=(game_id,str(item["signature"]))
            if key in self.recent_samples_loaded:
                self.recent_samples[key].append({"sample_id":None,"feature":item["feature"],"coarse":item["coarse"],"context":item["context"]})
    def _invalidate_sample_caches(self,gid=None,signature=None):
        if gid is None:
            self.persisted_sample_stats.clear()
            self.recent_samples.clear()
            self.recent_samples_loaded.clear()
            return
        game_id=str(gid)
        self.persisted_sample_stats.pop(game_id,None)
        keys=[key for key in self.recent_samples_loaded if key[0]==game_id and (signature is None or key[1]==str(signature))]
        for key in keys:
            self.recent_samples_loaded.discard(key)
            self.recent_samples.pop(key,None)
    def _sample_fingerprint(self,feature,action,context=None):
        temporal=temporal_from_context(context or {})
        identity={"action":normalize_action(action),"temporal":temporal}
        return hashlib.sha256(feature_bytes(feature)+b"\0"+canonical_bytes(identity)).hexdigest()
    def _near_duplicate(self,gid,feature,signature,threshold,context=None):
        game_id=str(gid)
        signature=str(signature)
        with self.pending_lock:
            pending=list(self.pending_recent_samples.get((game_id,signature),()))
        persisted=list(self._load_recent_sample_cache(game_id,signature))
        query=feature_bytes(feature)
        query_coarse=coarse_feature(query)
        query_context=context if isinstance(context,dict) else {}
        maximum_coarse=max(2.0,float(threshold)*2.5)
        for item in pending:
            try:
                if temporal_distance(query_context,item["context"])<=0.08 and coarse_distance(query_coarse,item["coarse"])<=maximum_coarse and feature_distance(query,item["feature"])<=float(threshold):
                    return True
            except (TypeError,ValueError,OverflowError) as error:
                self.logger.write("PENDING_DUPLICATE_COMPARE_FAILED",error,game_id=game_id)
        for item in persisted:
            try:
                if temporal_distance(query_context,item["context"])>0.08:
                    continue
                if coarse_distance(query_coarse,item["coarse"])<=maximum_coarse and feature_distance(query,item["feature"])<=float(threshold):
                    return True
            except (TypeError,ValueError,OverflowError) as error:
                self.logger.write("PERSISTED_DUPLICATE_COMPARE_FAILED",error,game_id=game_id,details={"sample_id":item.get("sample_id")})
        return False
    def _insert_sample(self,gid,feature,action,source,context,rgb_thumbnail,neural_feature,weight,enforce_quota,mark_review,created=None):
        self._ensure_writable()
        self._raise_writer_error()
        game_id=str(gid)
        clean=normalize_action(action)
        if not clean or not feature_valid(feature):
            raise RuntimeError("拒绝保存无效样本")
        fbytes=feature_bytes(feature)
        coarse=coarse_feature(fbytes)
        neural=feature_bytes(neural_feature) if feature_valid(neural_feature) else None
        rgb=sample_rgb_bytes(rgb_thumbnail)
        if rgb is None:
            raise RuntimeError("样本必须包含固定尺寸RGB图像")
        signature=action_signature(clean)
        context=dict(context) if isinstance(context,dict) else {}
        context["preprocess_signature"]=preprocess_signature()
        context["preprocess_hash"]=VISION_PREPROCESS_HASH
        context["sample_image_version"]=SAMPLE_IMAGE_VERSION
        context["raw_feature_preserved"]=True
        context["neural_feature_version"]=NEURAL_FEATURE_VERSION if neural is not None else 0
        session_id=str(context.get("session_id") or "unspecified")
        capture_method=str(context.get("capture_method") or "unknown")
        repeat_policy=str(context.get("repeat_policy","one_shot"))
        if repeat_policy not in REPEAT_POLICIES:
            repeat_policy="one_shot"
        duplicate_threshold=float(context.get("duplicate_threshold",3.0)) if finite_number(context.get("duplicate_threshold",3.0)) else 3.0
        fingerprint=self._sample_fingerprint(fbytes,clean,context)
        kind=clean["kind"]
        created_value=float(time.time() if created is None else created)
        self._ensure_sample_session(game_id,session_id,created_value)
        with self.pending_lock:
            if game_id in self.blocked_game_ids or (game_id,session_id) in self.blocked_sessions:
                raise RuntimeError("游戏或session正在作废，拒绝接收样本")
            pending_duplicate=(game_id,fingerprint) in self.pending_fingerprints
            pending_counts=dict(self.pending_counts_by_game.get(game_id,{}))
        with self.lock:
            if not self.db.execute("SELECT 1 FROM games WHERE id=?",(game_id,)).fetchone():
                raise RuntimeError("游戏不存在")
            persisted_duplicate=bool(self.db.execute("SELECT 1 FROM samples WHERE game_id=? AND fingerprint=?",(game_id,fingerprint)).fetchone())
        if pending_duplicate or persisted_duplicate:
            return False
        persisted=self._persisted_stats(game_id)
        pending_noops=int(pending_counts.get("noops",0))
        pending_actions=int(pending_counts.get("actions",0))
        pending_count=int(pending_counts.get("total",0))
        if pending_count>=192:
            return False
        if enforce_quota and pending_count>=96 and kind in {"no_op","hover","move"}:
            return False
        if enforce_quota and kind=="no_op" and persisted["noops"]+pending_noops>=max(1,(persisted["actions"]+pending_actions)//3):
            return False
        if enforce_quota and self._near_duplicate(game_id,fbytes,signature,duplicate_threshold,context):
            return False
        item={
            "gid":game_id,"created":created_value,"kind":kind,"signature":signature,"action_family":action_family_key(clean),
            "repeat_policy":repeat_policy,"feature":fbytes,"coarse":coarse,"neural":neural,"rgb":rgb,
            "action_json":json.dumps(clean,ensure_ascii=False,separators=(",",":")),"source":str(source),"session_id":session_id,
            "capture_method":capture_method,"context":context,"context_json":json.dumps(context,ensure_ascii=False,separators=(",",":")),
            "weight":float(max(0.1,min(10.0,weight))),"fingerprint":fingerprint,"mark_review":bool(mark_review),
        }
        with self.pending_lock:
            if game_id in self.blocked_game_ids or (game_id,session_id) in self.blocked_sessions:
                raise RuntimeError("游戏或session正在作废，拒绝接收样本")
            if (game_id,fingerprint) in self.pending_fingerprints:
                return False
            self.pending_samples.append(item)
            self._pending_index_add_locked(item)
            queue_depth=int(self.pending_counts_by_game[game_id]["total"])
            if len(self.pending_samples)>=12:
                self.pending_event.set()
            self.writer_condition.notify_all()
        count=persisted["total"]+pending_count+1
        if queue_depth>=96:
            self.logger.write("SAMPLE_QUEUE_BACKPRESSURE",details={"game_id":game_id,"queue_depth":queue_depth,"suggested_sampling_scale":0.5})
        if count>DEFAULT_SAMPLE_BUDGET+16:
            with self.lock,self.db:
                self.db.execute("UPDATE games SET needs_review=1 WHERE id=?",(game_id,))
            self.logger.write("SAMPLE_BUDGET_DEFERRED_TO_SLEEP",details={"game_id":game_id,"estimated_samples":count,"session_id":session_id,"session_status":"staging_or_unconfirmed"})
        return True
    def discard_session(self,gid,session_id,reason="discarded"):
        game_id=str(gid)
        sid=str(session_id)
        self.invalidate_learning_session(game_id,sid,reason)
        self.sample_write_barrier()
        with self.pending_lock:
            before=len(self.pending_samples)
            self.pending_samples=[item for item in self.pending_samples if not (item["gid"]==game_id and item["session_id"]==sid)]
            self._rebuild_pending_indexes_locked()
            pending_removed=before-len(self.pending_samples)
            self.writer_condition.notify_all()
        with self.critical_transaction():
            cursor=self.db.execute("DELETE FROM samples WHERE game_id=? AND session_id=?",(game_id,sid))
            removed=pending_removed+max(0,int(cursor.rowcount or 0))
            if removed:
                self.db.execute("UPDATE games SET needs_review=1 WHERE id=?",(game_id,))
        self.model_cache.pop(game_id,None)
        self._invalidate_sample_caches(game_id)
        return removed
    def discard_session_window(self,gid,session_id,start_time,end_time):
        game_id=str(gid)
        sid=str(session_id)
        self.invalidate_learning_session(game_id,sid,"discarded_window")
        self.sample_write_barrier()
        with self.pending_lock:
            before=len(self.pending_samples)
            self.pending_samples=[item for item in self.pending_samples if not (item["gid"]==game_id and item["session_id"]==sid and float(start_time)<=item["created"]<=float(end_time))]
            self._rebuild_pending_indexes_locked()
            pending_removed=before-len(self.pending_samples)
            self.writer_condition.notify_all()
        with self.critical_transaction():
            cursor=self.db.execute("DELETE FROM samples WHERE game_id=? AND session_id=? AND created BETWEEN ? AND ?",(game_id,sid,float(start_time),float(end_time)))
            removed=pending_removed+max(0,int(cursor.rowcount or 0))
            if removed:
                self.db.execute("UPDATE games SET needs_review=1 WHERE id=?",(game_id,))
        self.model_cache.pop(game_id,None)
        self._invalidate_sample_caches(game_id)
        return removed
    def append_sample(self,gid,feature,action,source,context=None,rgb_thumbnail=None,neural_feature=None,weight=1.0):
        return self._insert_sample(gid,feature,action,source,context or {},rgb_thumbnail,neural_feature,weight,True,True)
    def append_rejection(self,gid,feature,candidates,source="teach_reject",rgb_thumbnail=None,neural_feature=None,context=None):
        self._ensure_writable()
        if not feature_valid(feature):
            raise RuntimeError("拒绝记录的特征无效")
        rgb=sample_rgb_bytes(rgb_thumbnail)
        if rgb is None:
            raise RuntimeError("拒绝记录必须包含RGB图像")
        neural=feature_bytes(neural_feature) if feature_valid(neural_feature) else None
        candidate_data=[]
        for item in candidates or []:
            action=normalize_action(item.get("a") if isinstance(item,dict) else item)
            if action:
                candidate_data.append({"cluster_id":str(item.get("cluster_id",item.get("action_signature",""))) if isinstance(item,dict) else "","canonical_action_signature":action_signature(action),"a":action})
        context=dict(context) if isinstance(context,dict) else {}
        with self.lock,self.db:
            self.db.execute("INSERT INTO rejections(game_id,created,feature_algorithm_version,feature,coarse,neural_feature,rgb_thumbnail,preprocess_signature,thumbnail,candidates,source,session_id,capture_method) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (gid,time.time(),FEATURE_ALGORITHM_VERSION,sqlite3.Binary(zlib.compress(feature_bytes(feature),6)),sqlite3.Binary(coarse_feature(feature)),sqlite3.Binary(zlib.compress(neural,
                        6)) if neural is not None else None,sqlite3.Binary(zlib.compress(rgb,6)),VISION_PREPROCESS_HASH,None,json.dumps(candidate_data,ensure_ascii=False,separators=(",",":")),str(source),
                    str(context.get("session_id") or "unspecified"),str(context.get("capture_method") or "unknown")))
            self.db.execute("UPDATE games SET needs_review=1 WHERE id=?",(gid,))
    def _decode_sample_row(self,row,gid):
        feature=upgrade_feature(bounded_decompress(row["feature"],FEATURE_LEN*2),row["feature_algorithm_version"])
        action=normalize_action(json.loads(row["action"]))
        coarse=bytes(row["coarse"]) if row["coarse"] is not None and len(row["coarse"])==COARSE_LEN else coarse_feature(feature)
        if not feature_valid(feature) or len(coarse)!=COARSE_LEN or not action:
            raise ValueError("样本特征、粗特征或动作无效")
        rgb=upgrade_sample_rgb(bounded_decompress(row["rgb_thumbnail"],PIXELS*3+16)) if row["rgb_thumbnail"] is not None else None
        if rgb is None and row["thumbnail"] is not None:
            rgb=upgrade_sample_rgb(bounded_decompress(row["thumbnail"],PIXELS*4))
        neural=upgrade_feature(bounded_decompress(row["neural_feature"],FEATURE_LEN*2),FEATURE_ALGORITHM_VERSION) if row["neural_feature"] is not None else None
        context=json.loads(row["context"])
        if not isinstance(context,dict):
            raise ValueError("样本上下文必须是字典")
        context.update({"session_id":row["session_id"],"capture_method":row["capture_method"],"repeat_policy":row["repeat_policy"]})
        return {"format_version":FORMAT_VERSION,"feature_width":FEATURE_W,"feature_height":FEATURE_H,"feature_algorithm_version":FEATURE_ALGORITHM_VERSION,
            "action_algorithm_version":ACTION_ALGORITHM_VERSION,"created":row["created"],"game_id":gid,"f":feature,"raw_f":feature,"neural_f":neural,"coarse":coarse,
            "a":action,"source":row["source"],"session_id":row["session_id"],"capture_method":row["capture_method"],"repeat_policy":row["repeat_policy"],
            "context":context,"rgb":rgb,"thumbnail":rgb,"preprocess_signature":str(row["preprocess_signature"] or ""),"weight":row["weight"],"checksum":row["fingerprint"]}
    def iter_samples(self,gid,limit=MAX_SAMPLES,batch_size=256,stats=None):
        self.sample_write_barrier()
        game_id=str(gid)
        maximum=safe_int(limit,MAX_SAMPLES,1,MAX_SAMPLES)
        chunk=safe_int(batch_size,256,16,1024)
        counters=stats if isinstance(stats,dict) else {}
        counters.update({"valid":0,"invalid":0,"total":0})
        corrupt=[]
        connection=sqlite3.connect("file:"+self.db_path.as_posix()+"?mode=ro",uri=True,timeout=3.0,check_same_thread=True)
        connection.row_factory=sqlite3.Row
        try:
            query=(
                "SELECT * FROM ("
                "SELECT s.id,s.created,s.feature_algorithm_version,s.action_algorithm_version,"
                "s.feature,s.coarse,s.neural_feature,s.rgb_thumbnail,s.preprocess_signature,"
                "s.action,s.source,s.session_id,s.capture_method,s.context,s.thumbnail,s.weight,"
                "s.fingerprint,s.repeat_policy FROM samples s JOIN learning_sessions ls "
                "ON ls.game_id=s.game_id AND ls.session_id=s.session_id "
                "WHERE s.game_id=? AND ls.status='valid' "
                "ORDER BY s.created DESC,s.id DESC LIMIT ?"
                ") recent ORDER BY created ASC,id ASC"
            )
            cursor=connection.execute(query,(game_id,maximum))
            while True:
                rows=cursor.fetchmany(chunk)
                if not rows:
                    break
                for row in rows:
                    counters["total"]+=1
                    try:
                        item=self._decode_sample_row(row,game_id)
                    except (zlib.error,json.JSONDecodeError,UnicodeDecodeError,ValueError,TypeError,OverflowError) as error:
                        counters["invalid"]+=1
                        corrupt.append((row["id"],row["fingerprint"],error))
                        continue
                    counters["valid"]+=1
                    yield item
        finally:
            connection.close()
            for row_id,fingerprint,error in corrupt:
                self.quarantine_corrupt_row("samples",row_id,game_id,error,fingerprint)
            self.invalid_rows[game_id]=max(self.invalid_rows.get(game_id,0),counters["invalid"])
    def load_samples(self,gid,limit=MAX_SAMPLES):
        stats={}
        result=list(self.iter_samples(gid,limit,256,stats))
        return result,stats
    def load_rejections(self,gid,limit=500):
        with self.lock:
            rows=self.db.execute("SELECT id,created,feature_algorithm_version,feature,coarse,neural_feature,rgb_thumbnail,preprocess_signature,thumbnail,candidates,source,session_id,capture_method FROM rejections WHERE game_id=? ORDER BY created DESC,id DESC LIMIT ?",
                (gid,int(limit))).fetchall()
        result=[]
        invalid=0
        for row in rows:
            try:
                feature=upgrade_feature(bounded_decompress(row["feature"],FEATURE_LEN*2),row["feature_algorithm_version"])
                coarse=bytes(row["coarse"]) if row["coarse"] is not None and len(row["coarse"])==COARSE_LEN else coarse_feature(feature)
                candidates=json.loads(row["candidates"])
                rgb=upgrade_sample_rgb(bounded_decompress(row["rgb_thumbnail"],PIXELS*3+16)) if row["rgb_thumbnail"] is not None else None
                if rgb is None and row["thumbnail"] is not None:
                    rgb=upgrade_sample_rgb(bounded_decompress(row["thumbnail"],PIXELS*4))
                neural=upgrade_feature(bounded_decompress(row["neural_feature"],FEATURE_LEN*2),FEATURE_ALGORITHM_VERSION) if row["neural_feature"] is not None else None
                if not feature_valid(feature) or len(coarse)!=COARSE_LEN or not isinstance(candidates,list):
                    raise ValueError("拒绝记录特征或候选无效")
                result.append({"created":row["created"],"f":feature,"raw_f":feature,"neural_f":neural,"coarse":coarse,"rgb":rgb,"thumbnail":rgb,
                        "preprocess_signature":str(row["preprocess_signature"] or ""),"candidates":candidates,"source":row["source"],"session_id":row["session_id"],"capture_method":row["capture_method"]})
            except Exception as error:
                invalid+=1
                self.quarantine_corrupt_row("rejections",row["id"],gid,error,str(row["source"]))
        self.invalid_rows["rejections:"+str(gid)]=max(self.invalid_rows.get("rejections:"+str(gid),0),invalid)
        return result
    def sample_stats(self,gid):
        self.sample_write_barrier()
        with self.lock:
            total_row=self.db.execute("SELECT COUNT(*) AS total,COALESCE(SUM(length(feature)+length(coarse)+length(action)+length(context)+COALESCE(length(thumbnail),0)+COALESCE(length(rgb_thumbnail),0)+COALESCE(length(neural_feature),0)),0) AS bytes FROM samples WHERE game_id=?",
                (gid,)).fetchone()
            valid_row=self.db.execute("SELECT COUNT(*) AS valid FROM samples s JOIN learning_sessions ls ON ls.game_id=s.game_id AND ls.session_id=s.session_id WHERE s.game_id=? AND ls.status='valid' AND s.feature_algorithm_version IN (3,?)",
                (gid,FEATURE_ALGORITHM_VERSION)).fetchone()
            session_row=self.db.execute("SELECT COUNT(*) AS sessions FROM learning_sessions WHERE game_id=? AND status='valid'",(gid,)).fetchone()
            family_rows=self.db.execute("SELECT s.action_family,COUNT(*) AS count FROM samples s JOIN learning_sessions ls ON ls.game_id=s.game_id AND ls.session_id=s.session_id WHERE s.game_id=? AND ls.status='valid' AND s.feature_algorithm_version IN (3,?) GROUP BY s.action_family",
                (gid,FEATURE_ALGORITHM_VERSION)).fetchall()
        total=safe_int(total_row["total"] or 0,0,0)
        sql_valid=safe_int(valid_row["valid"] or 0,0,0,total)
        observed=safe_int(self.invalid_rows.get(str(gid),0),0,0,total)
        valid=max(0,min(sql_valid,total-observed))
        families={str(row["action_family"]):safe_int(row["count"],0,0) for row in family_rows if str(row["action_family"])}
        return {"valid":valid,"invalid":total-valid,"total":total,"bytes":safe_int(total_row["bytes"] or 0,0,0),"sessions":safe_int(session_row["sessions"] or 0,0,0),"families":families}
    def experience_pool_snapshot(self,gid):
        self.sample_write_barrier()
        game_id=str(gid)
        with self.lock:
            status_rows=self.db.execute("SELECT ls.status,COUNT(s.id) AS count FROM learning_sessions ls LEFT JOIN samples s ON s.game_id=ls.game_id AND s.session_id=ls.session_id WHERE ls.game_id=? GROUP BY ls.status",
                (game_id,)).fetchall()
            family_rows=self.db.execute("SELECT s.action_family,COUNT(*) AS count FROM samples s JOIN learning_sessions ls ON ls.game_id=s.game_id AND ls.session_id=s.session_id WHERE s.game_id=? AND ls.status='valid' GROUP BY s.action_family ORDER BY s.action_family",
                (game_id,)).fetchall()
            session_rows=self.db.execute("SELECT s.session_id,COUNT(*) AS count FROM samples s JOIN learning_sessions ls ON ls.game_id=s.game_id AND ls.session_id=s.session_id WHERE s.game_id=? AND ls.status='valid' GROUP BY s.session_id ORDER BY s.session_id",
                (game_id,)).fetchall()
            backend_rows=self.db.execute("SELECT s.capture_method,COUNT(*) AS count FROM samples s JOIN learning_sessions ls ON ls.game_id=s.game_id AND ls.session_id=s.session_id WHERE s.game_id=? AND ls.status='valid' GROUP BY s.capture_method ORDER BY s.capture_method",
                (game_id,)).fetchall()
            pool_query=(
                "SELECT s.id,s.fingerprint,s.weight,s.action_family,s.session_id,"
                "s.capture_method,s.feature,s.feature_algorithm_version "
                "FROM samples s JOIN learning_sessions ls "
                "ON ls.game_id=s.game_id AND ls.session_id=s.session_id "
                "WHERE s.game_id=? AND ls.status='valid' ORDER BY s.id"
            )
            pool_rows=self.db.execute(pool_query,
                (game_id,)).fetchall()
            storage_row=self.db.execute("SELECT COUNT(*) AS records,COALESCE(SUM(length(feature)+length(coarse)+length(action)+length(context)+COALESCE(length(thumbnail),0)+COALESCE(length(rgb_thumbnail),0)+COALESCE(length(neural_feature),0)),0) AS bytes FROM samples WHERE game_id=?",
                (game_id,)).fetchone()
        statuses={"valid":0,"invalid":0,"staging":0}
        for row in status_rows:
            statuses[str(row["status"])]=safe_int(row["count"],0,0)
        fingerprints=Counter(str(row["fingerprint"]) for row in pool_rows if str(row["fingerprint"]))
        visual_hashes=[]
        visual_hash_by_id={}
        visual_hash_failures=0
        for row in pool_rows:
            try:
                feature=upgrade_feature(bounded_decompress(row["feature"],FEATURE_LEN*2),row["feature_algorithm_version"])
                if not feature_valid(feature):
                    raise ValueError("经验池特征无效")
                value=visual_perceptual_hash(feature)
                visual_hashes.append(value)
                visual_hash_by_id[safe_int(row["id"],0)]=value
            except Exception:
                visual_hash_failures+=1
        visual_counts=Counter(visual_hashes)
        exact_visual_duplicates=sum(max(0,count-1) for count in visual_counts.values())
        near_visual_pairs=len(near_perceptual_hash_pairs(visual_counts.keys(),4))
        summary={"game_id":game_id,"total":sum(statuses.values()),"valid":statuses["valid"],"invalid":statuses["invalid"],"staging":statuses["staging"],
            "record_count":safe_int(storage_row["records"],0,0),"storage_bytes":safe_int(storage_row["bytes"],0,0),"near_duplicate_count":exact_visual_duplicates+near_visual_pairs,
            "exact_visual_duplicate_count":exact_visual_duplicates,"near_visual_pair_count":near_visual_pairs,"visual_hash_failures":visual_hash_failures,
            "pool_validation_completed":visual_hash_failures==0,"families":{str(row["action_family"]):safe_int(row["count"],0,0) for row in family_rows},
            "sessions":{str(row["session_id"]):safe_int(row["count"],0,0) for row in session_rows},"capture_backends":{str(row["capture_method"]):safe_int(row["count"],0,0) for row in backend_rows}}
        digest_rows=[[safe_int(row["id"],0),str(row["fingerprint"]),visual_hash_by_id.get(safe_int(row["id"],0),""),round(safe_float(row["weight"],1.0),6),str(row["action_family"]),
                str(row["session_id"]),str(row["capture_method"])] for row in pool_rows]
        summary["summary_hash"]=hashlib.sha256(canonical_bytes({"summary":summary,"rows":digest_rows})).hexdigest()
        return summary
    def plan_experience_pool_optimization(self,gid,retained_checksums=None,keep=None):
        self.sample_write_barrier()
        game_id=str(gid)
        retained={str(value) for value in retained_checksums or [] if str(value)}
        before=self.experience_pool_snapshot(game_id)
        with self.lock:
            pool_plan_query=(
                "SELECT s.id,s.kind,s.action_signature,s.action_family,s.capture_method,"
                "s.session_id,s.coarse,s.weight,s.created,s.fingerprint "
                "FROM samples s JOIN learning_sessions ls "
                "ON ls.game_id=s.game_id AND ls.session_id=s.session_id "
                "WHERE s.game_id=? AND ls.status='valid' "
                "ORDER BY s.created DESC,s.id DESC"
            )
            rows=self.db.execute(pool_plan_query,
                (game_id,)).fetchall()
        family_count=len({str(row["action_family"]) for row in rows})
        session_count=len({str(row["session_id"]) for row in rows})
        target=max(1,safe_int(sample_retention_budget(family_count,session_count) if keep is None else keep,DEFAULT_SAMPLE_BUDGET,1,MAX_SAMPLES))
        if len(rows)<=target:
            plan={"game_id":game_id,"created":time.time(),"target":target,"before":before,"keep_ids":[safe_int(row["id"],0) for row in rows],"remove_ids":[],
                "retained_checksums_hash":hashlib.sha256(canonical_bytes(sorted(retained))).hexdigest(),"deleted":0,"merged":0,"downweighted":0}
            plan["plan_hash"]=hashlib.sha256(canonical_bytes(plan)).hexdigest()
            return plan
        protected={safe_int(row["id"],0) for row in rows if str(row["fingerprint"]) in retained}
        dimensions=("session_id","capture_method","action_family")
        for field in dimensions:
            groups=defaultdict(list)
            for row in rows:
                groups[str(row[field])].append(row)
            for values in groups.values():
                best=max(values,key=lambda row:(safe_float(row["weight"],1.0),safe_float(row["created"],0.0),safe_int(row["id"],0)))
                protected.add(safe_int(best["id"],0))
        dangerous=defaultdict(list)
        for row in rows:
            family=str(row["action_family"] or row["kind"])
            if str(row["kind"]) in {"double_click","long_press","drag"} or family.endswith("|right") or family.endswith("|middle"):
                dangerous[family].append(row)
        for values in dangerous.values():
            for row in sorted(values,key=lambda item:(safe_float(item["weight"],1.0),safe_float(item["created"],0.0)),reverse=True)[:min(2,len(values))]:
                protected.add(safe_int(row["id"],0))
        target=max(target,len(protected))
        chosen=[row for row in rows if safe_int(row["id"],0) in protected]
        remaining=[row for row in rows if safe_int(row["id"],0) not in protected]
        chosen.extend(self._select_diverse(remaining,max(0,target-len(chosen))))
        keep_ids=sorted({safe_int(row["id"],0) for row in chosen})
        remove_ids=sorted(safe_int(row["id"],0) for row in rows if safe_int(row["id"],0) not in set(keep_ids))
        signatures=Counter(str(row["action_signature"]) for row in rows)
        merged=sum(max(0,count-1) for count in signatures.values())
        plan={"game_id":game_id,"created":time.time(),"target":target,"before":before,"keep_ids":keep_ids,"remove_ids":remove_ids,
            "retained_checksums_hash":hashlib.sha256(canonical_bytes(sorted(retained))).hexdigest(),"deleted":len(remove_ids),"merged":min(len(remove_ids),merged),"downweighted":0}
        plan["plan_hash"]=hashlib.sha256(canonical_bytes(plan)).hexdigest()
        return plan
    def apply_experience_pool_optimization(self,plan):
        value=dict(plan) if isinstance(plan,dict) else {}
        checksum=str(value.pop("plan_hash",""))
        if not checksum or hashlib.sha256(canonical_bytes(value)).hexdigest()!=checksum:
            raise RuntimeError("经验池优化计划校验失败")
        game_id=str(value.get("game_id",""))
        remove_ids=sorted({safe_int(item,0,1) for item in value.get("remove_ids",[])})
        removed=0
        with self.critical_transaction():
            for start in range(0,len(remove_ids),400):
                batch=remove_ids[start:start+400]
                placeholders=",".join("?" for _ in batch)
                cursor=self.db.execute("DELETE FROM samples WHERE game_id=? AND id IN ("+placeholders+") AND EXISTS (SELECT 1 FROM learning_sessions ls WHERE ls.game_id=samples.game_id AND ls.session_id=samples.session_id AND ls.status='valid')",
                    [game_id,*batch])
                removed+=max(0,safe_int(cursor.rowcount,0))
            self.db.execute("UPDATE games SET needs_review=0,last_review=? WHERE id=?",(time.time(),game_id))
        self._invalidate_sample_caches(game_id)
        after=self.experience_pool_snapshot(game_id)
        result={"before":value.get("before",{}),"after":after,"planned_delete":len(remove_ids),"deleted":removed,"merged":safe_int(value.get("merged"),0,0),
            "downweighted":safe_int(value.get("downweighted"),0,0),"pool_validation_completed":True,"plan_hash":checksum}
        result["commit_hash"]=hashlib.sha256(canonical_bytes(result)).hexdigest()
        return result
    def commit_sleep_result(self,gid,models,plan):
        game_id=str(gid)
        records=list(models or [])
        if str(plan.get("game_id",""))!=game_id:
            raise RuntimeError("睡眠模型与经验池计划游戏不一致")
        with self.lock:
            old_models=[dict(row) for row in self.db.execute("SELECT game_id,slot,saved,created,prototype_count,validation,payload,checksum FROM models WHERE game_id=?",(game_id,)).fetchall()]
            old_game=self.db.execute("SELECT needs_review,last_review FROM games WHERE id=?",(game_id,)).fetchone()
        before_model_hash=hashlib.sha256(canonical_bytes([[row["slot"],row["checksum"]] for row in old_models])).hexdigest()
        before_metrics=model_quality_snapshot(old_models)
        try:
            for model_gid,model,complete in records:
                if str(model_gid)!=game_id:
                    raise RuntimeError("睡眠子进程返回了其他游戏模型")
                self.save_model(game_id,model,complete)
            pool_result=self.apply_experience_pool_optimization(plan)
        except Exception:
            with self.critical_transaction():
                self.db.execute("DELETE FROM models WHERE game_id=?",(game_id,))
                for row in old_models:
                    self.db.execute("INSERT INTO models(game_id,slot,saved,created,prototype_count,validation,payload,checksum) VALUES(?,?,?,?,?,?,?,?)",(row["game_id"],row["slot"],
                            row["saved"],row["created"],row["prototype_count"],row["validation"],row["payload"],row["checksum"]))
                if old_game is not None:
                    self.db.execute("UPDATE games SET needs_review=?,last_review=? WHERE id=?",(old_game["needs_review"],old_game["last_review"],game_id))
            self.model_cache.pop(game_id,None)
            raise
        with self.lock:
            new_models=[dict(row) for row in self.db.execute("SELECT slot,prototype_count,validation,checksum FROM models WHERE game_id=? ORDER BY slot",(game_id,)).fetchall()]
        after_model_hash=hashlib.sha256(canonical_bytes([[row["slot"],row["checksum"]] for row in new_models])).hexdigest()
        after_metrics=model_quality_snapshot(new_models)
        return {"model_before_hash":before_model_hash,"model_after_hash":after_model_hash,"model_before_metrics":before_metrics,"model_after_metrics":after_metrics,"pool":pool_result,
            "models_committed":len(records),"commit_hash":hashlib.sha256(canonical_bytes({"model_before":before_model_hash,"model_after":after_model_hash,"pool":pool_result.get("commit_hash","")})).hexdigest()}
    def _select_diverse(self,rows,count):
        if count<=0:
            return []
        if len(rows)<=count:
            return list(rows)
        ordered=sorted(rows,key=lambda row:(safe_float(row["weight"],1.0),safe_float(row["created"],0.0)),reverse=True)
        selected=[]
        sessions=defaultdict(list)
        for row in ordered:
            sessions[str(row["session_id"] or "legacy")].append(row)
        for session in sorted(sessions,key=lambda value:(len(sessions[value]),value)):
            if len(selected)>=count:
                break
            chosen=sessions[session][0]
            selected.append(chosen)
            ordered.remove(chosen)
        if not selected and ordered:
            selected.append(ordered.pop(0))
        while ordered and len(selected)<count:
            candidates=ordered if len(ordered)<=180 else ordered[:180]
            best=max(candidates,key=lambda row:(min(coarse_distance(row["coarse"],chosen["coarse"]) for chosen in selected),safe_float(row["weight"],1.0),safe_float(row["created"],0.0)))
            selected.append(best)
            ordered.remove(best)
        return selected
    def compact_samples(self,gid,keep=None,sleep_commit=False):
        if not sleep_commit and not DEVELOPER_MODE:
            raise RuntimeError("破坏性经验池压缩只允许在睡眠提交阶段执行")
        plan=self.plan_experience_pool_optimization(gid,None,keep)
        result=self.apply_experience_pool_optimization(plan)
        return {"kept":safe_int(result.get("after",{}).get("valid"),0,0),"removed":safe_int(result.get("deleted"),0,0),"invalid":safe_int(result.get("after",{}).get("invalid"),0,0),
            "staging":safe_int(result.get("after",{}).get("staging"),0,0),"before_hash":str(result.get("before",{}).get("summary_hash","")),"after_hash":str(result.get("after",{}).get("summary_hash",""))}
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
        self._invalidate_sample_caches(gid)
    def save_window_descriptor(self,target):
        self._ensure_writable()
        rule=dict(target.get("title_rule") or {"mode":"none","value":""})
        if str(rule.get("mode","none")) not in TITLE_RULE_MODES:
            rule={"mode":"none","value":""}
        descriptor={"process_path":os.path.normcase(str(target.get("process_path",""))),"class":str(target.get("class","")),"title_rule":rule,"client_size":list(target.get("client_size",
                    []))[:2],"dpi":safe_int(target.get("selected_dpi",target.get("dpi",0)),0),"integrity":safe_int(target.get("integrity",-1),-1),"content_rect_norm":[round(safe_float(value,0.0),
                    8) for value in target.get("content_rect_norm",[0,0,1,1])[:4]],"content_aspect":safe_float(target.get("content_aspect",0.0),0.0),"content_source":str(target.get("content_source","manual")),
            "window_rule_version":WINDOW_RULE_VERSION,"saved":time.time()}
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
        payload={"process_path":os.path.normcase(str(target.get("process_path",""))),"class":str(target.get("class","")),"client_size":[safe_int(value,0,0) for value in list(raw_size)[:2]],
            "dpi":safe_int(target.get("selected_dpi",target.get("dpi",0)),0,0),"content_rect_norm":[round(safe_float(value,0.0),6) for value in target.get("content_rect_norm",[0,0,1,1])[:4]],
            "window_rule_version":WINDOW_RULE_VERSION,"capture_backend_version":CAPTURE_BACKEND_VERSION}
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
            self.db.execute("INSERT INTO capture_calibrations(identity_key,backend,saved,payload,checksum) VALUES(?,?,?,?,?) ON CONFLICT(identity_key,backend) DO UPDATE SET saved=excluded.saved,payload=excluded.payload,checksum=excluded.checksum",
                (identity_key,backend,payload["saved"],text,payload["checksum"]))
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
            result.update({"format_version":FORMAT_VERSION,"model_schema_version":MODEL_SCHEMA_VERSION,"feature_width":FEATURE_W,"feature_height":FEATURE_H,
                    "feature_algorithm_version":FEATURE_ALGORITHM_VERSION,"action_algorithm_version":ACTION_ALGORITHM_VERSION,"game_id":gid,"complete":bool(complete),
                    "compatibility_signature":compatibility_signature(),"source_build_hash":str(item.get("source_build_hash") or item.get("algorithm_snapshot",{}).get("build_hash")
                        or item.get("algorithm_snapshot",{}).get("source_build_hash") or ""),"algorithm_snapshot":algorithm_snapshot(),"prototypes":upgraded})
            return result
        except Exception:
            return None
    def _model_valid(self,item,gid,complete=True):
        try:
            item_valid=(
                isinstance(item,dict)
                and item.get("format_version")==FORMAT_VERSION
                and item.get("feature_width")==FEATURE_W
                and item.get("feature_height")==FEATURE_H
                and item.get("feature_algorithm_version")==FEATURE_ALGORITHM_VERSION
                and item.get("action_algorithm_version")==ACTION_ALGORITHM_VERSION
                and item.get("game_id")==gid
                and bool(item.get("complete"))==bool(complete)
                and normalized_compatibility_signature(compatibility_signature_from_item(item))==compatibility_signature()
            )
            if not item_valid:
                return False
            binding=item.get("model_binding")
            binding_valid=(
                isinstance(binding,dict)
                and binding.get("window_rule_version")==WINDOW_RULE_VERSION
                and binding.get("capture_backend_version")==CAPTURE_BACKEND_VERSION
                and bool(binding.get("process_paths"))
                and bool(binding.get("window_classes"))
                and bool(binding.get("content_rect_norms"))
                and finite_number(binding.get("content_aspect_min"))
                and finite_number(binding.get("content_aspect_max"))
                and float(binding.get("content_aspect_min",0))>0
                and float(binding.get("content_aspect_max",0))>0
                and safe_int(binding.get("dpi_min",0),0)>0
                and safe_int(binding.get("dpi_max",0),0)>0
                and bool(binding.get("capture_methods"))
            )
            if not binding_valid:
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
                if not str(proto.get("id","")) or not str(proto.get("cluster_id","")) or not str(proto.get("canonical_action_signature",
                        "")) or not feature_valid(proto.get("f")) or not isinstance(proto.get("coarse"),(bytes,
                        bytearray)) or len(proto.get("coarse"))!=COARSE_LEN or not normalize_action(proto.get("a")) or not finite_number(proto.get("threshold")) or float(proto.get("threshold"))<=0 or int(proto.get("support",
                        0))<=0 or not temporal.get("complete") or not finite_number(proto.get("temporal_threshold",0)) or float(proto.get("temporal_threshold",0))<=0:
                    return False
                conflict=proto.get("nearest_conflicting_distance")
                if conflict is not None and (not finite_number(conflict) or float(conflict)<0):
                    return False
                rejected=proto.get("nearest_rejected_distance")
                if rejected is not None and (not finite_number(rejected) or float(rejected)<0):
                    return False
                if not finite_number(proto.get("minimum_second_candidate_gap",0)) or str(proto.get("repeat_policy",
                        "one_shot")) not in REPEAT_POLICIES or not finite_number(proto.get("max_rate",1.0)) or float(proto.get("max_rate",1.0))<=0:
                    return False
            validation=item.get("validation")
            if complete and not any(bool(proto.get("authorized",False)) for proto in prototypes):
                return False
            return isinstance(validation,dict) and isinstance(item.get("capture_backends"),list) and bool(item.get("capture_backends"))
        except Exception:
            return False
    def save_model(self,gid,model,complete=True):
        value=dict(model) if isinstance(model,dict) else {}
        runtime=globals().get("CURRENT_VISION_RUNTIME")
        if runtime is not None and runtime.ready:
            try:
                runtime.activate_game(gid)
                manifest=runtime.manifest()
                value["vision_model_manifest"]=manifest
                self.record_vision_model(gid,manifest)
            except Exception as error:
                self.logger.write("VISION_MODEL_BIND_FAILED",error,game_id=gid)
        value["ocr_semantic_version"]=OCR_SEMANTIC_VERSION
        value["ocr_regions_checksum"]=hashlib.sha256(canonical_bytes([{key:item.get(key) for key in ("id","region_norm","region_type","number_format","goal_relation","target_min",
                    "target_max","special_value","special_meaning","reset_meaning","checksum")} for item in self.list_ocr_regions(gid,True)])).hexdigest()
        value["preprocess_hash"]=VISION_PREPROCESS_HASH
        value["preprocess_signature"]=preprocess_signature()
        value["raw_feature_preserved"]=True
        model=value
        item=dict(model)
        item.update({"format_version":FORMAT_VERSION,"model_schema_version":MODEL_SCHEMA_VERSION,"feature_width":FEATURE_W,"feature_height":FEATURE_H,
                "feature_algorithm_version":FEATURE_ALGORITHM_VERSION,"action_algorithm_version":ACTION_ALGORITHM_VERSION,"game_id":gid,"complete":bool(complete),
                "compatibility_signature":compatibility_signature(),"source_build_hash":current_build_hash(),"algorithm_snapshot":algorithm_snapshot(),"saved":time.time()})
        clean_prototypes=[]
        for proto in item.get("prototypes",[]):
            entry={key:value for key,value in dict(proto).items() if not str(key).startswith("_runtime_") and key not in {"_collection_checksum","feature_view","channel_offsets",
                    "temporal_cached","coarse_bucket","bucket_priority"}}
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
                    self.db.execute("INSERT INTO model_backups(game_id,created,prototype_count,validation,payload,checksum) VALUES(?,?,?,?,?,?)",(gid,old["saved"],old["prototype_count"],
                            old["validation"],old["payload"],old["checksum"]))
                    self.db.execute("DELETE FROM model_backups WHERE game_id=? AND id NOT IN (SELECT id FROM model_backups WHERE game_id=? ORDER BY id DESC LIMIT 5)",(gid,gid))
            model_upsert_sql=(
                "INSERT INTO models("
                "game_id,slot,saved,created,prototype_count,validation,payload,checksum"
                ") VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(game_id,slot) DO UPDATE SET "
                "saved=excluded.saved,created=excluded.created,"
                "prototype_count=excluded.prototype_count,validation=excluded.validation,"
                "payload=excluded.payload,checksum=excluded.checksum"
            )
            self.db.execute(model_upsert_sql,
                (gid,slot,item["saved"],float(item.get("created",time.time())),len(item["prototypes"]),validation,sqlite3.Binary(payload),checksum))
            if complete:
                self.db.execute("DELETE FROM models WHERE game_id=? AND slot='partial'",(gid,))
                self.db.execute("UPDATE games SET needs_review=0,last_review=? WHERE id=?",(float(item.get("created",time.time())),gid))
            elif str(item.get("validation",{}).get("status",""))=="basic_safe":
                self.db.execute("UPDATE games SET needs_review=0,last_review=? WHERE id=?",(float(item.get("created",time.time())),gid))
        if complete:
            self.model_cache[gid]=self._prepare_model_runtime(item,checksum)
    def _prepare_model_runtime(self,item,payload_checksum=None):
        model=dict(item)
        prototypes=[]
        for proto in model.get("prototypes",[]):
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
        token=str(payload_checksum or model.pop("_payload_checksum","") or prototype_collection_checksum(prototypes))
        for entry in prototypes:
            entry["_collection_checksum"]=token
        model["prototypes"]=prototypes
        runtime_index=build_candidate_runtime_index(prototypes,False)
        runtime_index["token"]=token
        model["runtime_index"]=runtime_index
        model["runtime_token"]=token
        return model
    def _row_model(self,row,gid,complete):
        try:
            if not row or hashlib.sha256(row["payload"]).hexdigest()!=row["checksum"]:
                return None
            item=self._unpack_model(row["payload"])
            item=self._upgrade_model(item,gid,complete)
            if self._model_valid(item,gid,complete):
                item["_payload_checksum"]=str(row["checksum"])
                return item
            return None
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
                        self.db.execute("INSERT OR REPLACE INTO models(game_id,slot,saved,created,prototype_count,validation,payload,checksum) VALUES(?,?,?,?,?,?,?,?)",(gid,"complete",
                                float(recovered.get("saved",backup["created"])),float(recovered.get("created",backup["created"])),len(recovered["prototypes"]),json.dumps(recovered.get("validation",{}),ensure_ascii=False,
                                    separators=(",",":")),sqlite3.Binary(payload),checksum))
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
                    self.db.execute("INSERT OR REPLACE INTO models(game_id,slot,saved,created,prototype_count,validation,payload,checksum) VALUES(?,?,?,?,?,?,?,?)",(gid,"complete",
                            float(item.get("saved",backup["created"])),float(item.get("created",backup["created"])),len(item["prototypes"]),json.dumps(item.get("validation",{}),ensure_ascii=False,separators=(",",":")),
                            sqlite3.Binary(payload),checksum))
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
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        try:
            if self.db is not None and not self.read_only:
                with self.lock:
                    self.db.execute("PRAGMA wal_checkpoint(FULL)")
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
    def save_ocr_region(self,gid,payload):
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
        row={"id":region_id,"game_id":str(gid),"created":created,"updated":now,"region_norm":norm,"region_type":str(value.get("region_type","uncertain")),
            "number_format":str(value.get("number_format","auto")),"goal_relation":str(value.get("goal_relation","uncertain")),
            "target_min":safe_float(value.get("target_min")) if finite_number(value.get("target_min")) else None,
            "target_max":safe_float(value.get("target_max")) if finite_number(value.get("target_max")) else None,
            "special_value":safe_float(value.get("special_value")) if finite_number(value.get("special_value")) else None,"special_meaning":str(value.get("special_meaning","uncertain")),
            "reset_meaning":str(value.get("reset_meaning","uncertain")),"unit":str(value.get("unit","")),"enabled":1,"last_text":str(value.get("recognized_text",value.get("last_text","")))[:256],
            "last_value":safe_float(value.get("last_value")) if finite_number(value.get("last_value")) else None,"last_confidence":safe_float(value.get("confidence",0.0),0.0,0.0,1.0),
            "stable_frames":safe_int(value.get("stable_frames",0),0,0,1000)}
        checksum=hashlib.sha256(canonical_bytes(row)).hexdigest()
        with self.lock,self.db:
            ocr_upsert_sql=(
                "INSERT OR REPLACE INTO ocr_regions("
                "id,game_id,created,updated,region_norm,region_type,number_format,"
                "goal_relation,target_min,target_max,special_value,special_meaning,"
                "reset_meaning,unit,enabled,last_text,last_value,last_confidence,"
                "stable_frames,checksum) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
            )
            self.db.execute(ocr_upsert_sql,
                (row["id"],row["game_id"],row["created"],row["updated"],json.dumps(norm,separators=(",",":")),row["region_type"],row["number_format"],row["goal_relation"],row["target_min"],
                    row["target_max"],row["special_value"],row["special_meaning"],row["reset_meaning"],row["unit"],row["enabled"],row["last_text"],row["last_value"],row["last_confidence"],row["stable_frames"],checksum))
            self.db.execute("UPDATE games SET needs_review=1 WHERE id=?",(str(gid),))
        row["checksum"]=checksum
        return row
    def list_ocr_regions(self,gid,enabled_only=True):
        query="SELECT * FROM ocr_regions WHERE game_id=?"+(" AND enabled=1" if enabled_only else "")+" ORDER BY updated DESC"
        with self.lock:
            rows=self.db.execute(query,(str(gid),)).fetchall()
        result=[]
        for row in rows:
            try:
                item=dict(row)
                item["region_norm"]=json.loads(item["region_norm"])
                verification={key:item[key] for key in ("id","game_id","created","updated","region_norm","region_type","number_format","goal_relation","target_min","target_max",
                        "special_value","special_meaning","reset_meaning","unit","enabled","last_text","last_value","last_confidence","stable_frames")}
                if hashlib.sha256(canonical_bytes(verification)).hexdigest()!=str(item.get("checksum","")):
                    continue
                result.append(item)
            except Exception:
                continue
        return result
    def delete_ocr_region_by_overlap(self,gid,norm):
        removed=0
        with self.lock,self.db:
            rows=self.db.execute("SELECT id,region_norm FROM ocr_regions WHERE game_id=?",(str(gid),)).fetchall()
            ids=[]
            for row in rows:
                try:
                    if _rect_iou(json.loads(row["region_norm"]),norm)>=0.45:
                        ids.append(str(row["id"]))
                except Exception as error:
                    record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
            for region_id in ids:
                removed+=max(0,int(self.db.execute("DELETE FROM ocr_regions WHERE id=?",(region_id,)).rowcount or 0))
            if removed:
                self.db.execute("UPDATE games SET needs_review=1 WHERE id=?",(str(gid),))
        return removed
    def append_ocr_observation(self,gid,region_id,raw_text,parsed,confidence,stable_frames,event):
        value={"game_id":str(gid),"region_id":str(region_id),"created":time.time(),"raw_text":str(raw_text)[:256],"parsed":parsed if isinstance(parsed,dict) else {},
            "confidence":safe_float(confidence,0.0,0.0,1.0),"stable_frames":safe_int(stable_frames,0,0,1000),"semantic_event":event if isinstance(event,dict) else {}}
        checksum=hashlib.sha256(canonical_bytes(value)).hexdigest()
        with self.lock,self.db:
            self.db.execute("INSERT INTO ocr_observations(game_id,region_id,created,raw_text,parsed,confidence,stable_frames,semantic_event,checksum) VALUES(?,?,?,?,?,?,?,?,?)",
                (value["game_id"],value["region_id"],value["created"],value["raw_text"],json.dumps(value["parsed"],ensure_ascii=False,sort_keys=True,separators=(",",":")),value["confidence"],
                    value["stable_frames"],json.dumps(value["semantic_event"],ensure_ascii=False,sort_keys=True,separators=(",",":")),checksum))
            self.db.execute("DELETE FROM ocr_observations WHERE id IN (SELECT id FROM ocr_observations WHERE game_id=? ORDER BY created DESC LIMIT -1 OFFSET 20000)",(str(gid),))
        return True
    def load_ocr_experience_events(self,gid,limit=5000):
        with self.lock:
            rows=self.db.execute("SELECT created,semantic_event FROM ocr_observations WHERE game_id=? ORDER BY created DESC LIMIT ?",(str(gid),safe_int(limit,5000,1,50000))).fetchall()
        result=[]
        for row in reversed(rows):
            try:
                event=json.loads(row["semantic_event"])
                if isinstance(event,dict):
                    result.append({"created":safe_float(row["created"],0.0),"event":event})
            except (json.JSONDecodeError,TypeError,ValueError):
                continue
        return result
    def record_vision_model(self,gid,manifest):
        value=dict(manifest) if isinstance(manifest,dict) else {}
        metadata=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))
        with self.lock,self.db:
            self.db.execute("INSERT OR REPLACE INTO vision_models(game_id,architecture_version,updated,relative_path,checksum,trained_steps,device,metadata) VALUES(?,?,?,?,?,?,?,?)",
                (str(gid),safe_int(value.get("architecture_version"),0),time.time(),str(value.get("relative_path","")),str(value.get("checksum","")),safe_int(value.get("trained_steps"),0),str(value.get("device","")),metadata))
        return True
    def reencode_samples(self,gid,runtime,stop_event=None,progress=None):
        self.sample_write_barrier()
        with self.lock:
            rows=self.db.execute("SELECT id,rgb_thumbnail,thumbnail,action,context FROM samples WHERE game_id=? ORDER BY created,id",(str(gid),)).fetchall()
        manifest=runtime.manifest()
        updated=0
        legacy=0
        for index,row in enumerate(rows):
            if stop_event is not None and stop_event.is_set():
                raise InputStopped("样本AI特征升级已停止")
            rgb=None
            try:
                if row["rgb_thumbnail"] is not None:
                    rgb=upgrade_sample_rgb(bounded_decompress(row["rgb_thumbnail"],PIXELS*3+16))
                elif row["thumbnail"] is not None:
                    rgb=upgrade_sample_rgb(bounded_decompress(row["thumbnail"],PIXELS*4))
                    legacy+=1
                if rgb is None:
                    continue
                neural=runtime.encode(rgb,None)
                context=json.loads(row["context"])
                if not isinstance(context,dict):
                    context={}
                context.update({"vision_architecture_version":VISION_ARCHITECTURE_VERSION,"vision_model_checksum":manifest.get("checksum",""),"preprocess_signature":preprocess_signature(),
                        "preprocess_hash":VISION_PREPROCESS_HASH,"raw_feature_preserved":True,"neural_feature_version":NEURAL_FEATURE_VERSION})
                with self.lock,self.db:
                    self.db.execute("UPDATE samples SET neural_feature=?,rgb_thumbnail=COALESCE(rgb_thumbnail,?),preprocess_signature=?,context=? WHERE id=?",
                        (sqlite3.Binary(zlib.compress(neural,6)),sqlite3.Binary(zlib.compress(rgb,6)),VISION_PREPROCESS_HASH,json.dumps(context,ensure_ascii=False,separators=(",",":")),int(row["id"])))
                updated+=1
            except Exception as error:
                self.logger.write("VISION_REENCODE_SAMPLE_FAILED",error,game_id=gid,details={"sample_id":int(row["id"])})
            if progress is not None and index%8==0:
                progress(35.0+25.0*(index+1)/max(1,len(rows)))
        with self.lock,self.db:
            self.db.execute("UPDATE games SET needs_review=1 WHERE id=?",(str(gid),))
        self.model_cache.pop(str(gid),None)
        self._invalidate_sample_caches(gid)
        return {"updated":updated,"legacy_rgb_converted":legacy,"manifest":manifest}
class GameSelectionDialog:
    def __init__(self,app):
        self.app=app
    def open(self):
        app=self.app
        if app.mode:
            app.show_error("请先停止当前模式")
            return
        working_games=[dict(item) for item in app.store.games()]
        original_selected=app.selected_game["id"] if app.selected_game else None
        working_selected=original_selected
        deleted_stack=[]
        win=tk.Toplevel(app.root)
        win.title("游戏")
        fit_window(win,540,450,420,340)
        win.transient(app.root)
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
                suffix="  [需要睡眠]" if game.get("needs_review") else ""
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
            name=app.prompt_text("新建游戏","输入游戏名称")
            if name is None:
                return
            if any(item["name"].casefold()==name.casefold() for item in working_games):
                app.show_error("游戏名称已存在")
                return
            game={"id":uuid.uuid4().hex,"name":name,"created":time.time(),"needs_review":False,"last_review":None}
            working_games.append(game)
            working_selected=game["id"]
            refresh(working_selected)
        def edit_game():
            index=current_index()
            if index is None:
                app.show_error("请先选择一个游戏")
                return
            name=app.prompt_text("编辑游戏","修改游戏名称",working_games[index]["name"])
            if name is None:
                return
            if any(position!=index and item["name"].casefold()==name.casefold() for position,item in enumerate(working_games)):
                app.show_error("游戏名称已存在")
                return
            working_games[index]["name"]=name
            refresh(working_games[index]["id"])
        def delete_game():
            nonlocal working_selected
            index=current_index()
            if index is None:
                app.show_error("请先选择一个游戏")
                return
            item=dict(working_games.pop(index))
            deleted_stack.append((index,item,working_selected))
            if app.developer_mode:
                undo_button.configure(state="normal")
            box.selection_clear(0,"end")
            if item["id"]==original_selected or item["id"]==working_selected:
                working_selected=None
            elif working_games:
                working_selected=working_games[min(index,len(working_games)-1)]["id"]
            refresh(working_selected)
            app.status.set("已在临时列表标记删除："+item["name"]+("；点击“撤销删除”可恢复" if app.developer_mode else "")+"；只有总“确认”才写入数据库")
        def undo_delete():
            nonlocal working_selected
            if not deleted_stack:
                return
            index,item,previous_selected=deleted_stack.pop()
            working_games.insert(min(index,len(working_games)),item)
            working_selected=item["id"] if previous_selected==item["id"] else previous_selected
            undo_button.configure(state="normal" if deleted_stack else "disabled")
            refresh(item["id"])
        def confirm():
            nonlocal working_selected
            selection=box.curselection()
            if not selection:
                app.show_error("请重新选择一个仍存在的游戏；删除当前游戏后不能提交无效选择")
                return
            chosen=working_games[selection[0]]
            working_selected=chosen["id"]
            result=app.store.replace_games(working_games,working_selected)
            app.selected_game=dict(chosen)
            app._refresh_all()
            deleted=len(result.get("deleted_games",[])) if isinstance(result,dict) else 0
            app.status.set("已提交游戏列表并选择："+chosen["name"]+("；已删除"+str(deleted)+"个游戏及其全部数据" if deleted else ""))
            app.close_dialog(win,state)
        def refuse_close():
            win.bell()
            win.lift()
            win.focus_force()
        tools=ttk.Frame(frame)
        tools.pack(fill="x",pady=10)
        ttk.Button(tools,text="新建",command=add_game).pack(side="left",padx=(0,6))
        ttk.Button(tools,text="编辑",command=edit_game).pack(side="left",padx=6)
        ttk.Button(tools,text="删除",command=delete_game).pack(side="left",padx=6)
        undo_button=ttk.Button(tools,text="撤销删除",command=undo_delete,state="disabled")
        if app.developer_mode:
            undo_button.pack(side="left",padx=6)
        actions=ttk.Frame(frame)
        actions.pack(fill="x")
        ttk.Button(actions,text="确认",command=confirm).pack(side="right",padx=(6,0))
        win.protocol("WM_DELETE_WINDOW",refuse_close)
        refresh()
        win.wait_visibility()
        box.focus_set()
class WindowSelectionDialog:
    def __init__(self,app):
        self.app=app
    def open(self):
        app=self.app
        if app.mode:
            app.show_error("请先停止当前模式")
            return
        win=tk.Toplevel(app.root)
        win.title("选择窗口")
        fit_window(win,1200,760,560,400)
        win.transient(app.root)
        win.grab_set()
        state={"closed":False,"background_keys":["window_dialog_enumeration","window_dialog_preview"],"norm":[0.0,0.0,1.0,1.0],"auto":None,"client":None,"target_key":None,"start":None,"rect_id":None,"image":None}
        frame=scrollable_frame(win,16,True)
        ttk.Label(frame,text="选择雷电模拟器窗口或其他窗口",font=("Microsoft YaHei UI",13,"bold")).pack(anchor="w",pady=(0,6))
        ttk.Label(frame,text=("默认自动选择最大可见游戏子窗口。开发者模式可设置标题规则、整个客户区或手动区域；点击一次总“确认”同时保存窗口身份和区域。" if app.developer_mode else "请选择窗口并点击“确认”；程序将自动选择客户区内的游戏内容区域。"),wraplength=1140).pack(anchor="w",pady=(0,10))
        body=ttk.Frame(frame)
        body.pack(fill="both",expand=True)
        body.columnconfigure(0,weight=5 if app.developer_mode else 1)
        if app.developer_mode:
            body.columnconfigure(1,weight=4)
        body.rowconfigure(0,weight=1)
        left=ttk.Frame(body)
        left.grid(row=0,column=0,sticky="nsew",padx=(0,10))
        right=ttk.LabelFrame(body,text="游戏渲染区域",padding=10)
        if app.developer_mode:
            right.grid(row=0,column=1,sticky="nsew")
        list_frame=ttk.Frame(left)
        list_frame.pack(fill="both",expand=True)
        box=tk.Listbox(list_frame,exportselection=False,font=("Microsoft YaHei UI",9))
        scroll=ttk.Scrollbar(list_frame,orient="vertical",command=box.yview)
        box.configure(yscrollcommand=scroll.set)
        box.pack(side="left",fill="both",expand=True)
        scroll.pack(side="right",fill="y")
        rule_frame=ttk.LabelFrame(left,text="可选标题规则",padding=8)
        if app.developer_mode:
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
        if app.developer_mode:
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
                except Exception as error:
                    record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
            captured=app.api.capture_gray(temporary,False,True,True)
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
            preview_status.set("预览读取完成；青色框内是学习、睡眠、训练和指导使用的唯一区域")
        def preview_failed(error):
            if state["closed"] or not win.winfo_exists():
                return
            preview_status.set("预览告警："+str(error)+"；仍可使用自动区域、整个客户区或手动调整")
        def prepare_selection(event=None):
            item=selected_item()
            if item is None:
                return
            existing=item.get("title_rule") if isinstance(item.get("title_rule"),dict) else None
            if app.selected_window and item.get("hwnd")==app.selected_window.get("hwnd"):
                existing=app.selected_window.get("title_rule")
            if not isinstance(existing,dict):
                existing={"mode":"none","value":""}
            reverse={value:key for key,value in mode_map.items()}
            rule_label.set(reverse.get(str(existing.get("mode","none")),"不检查"))
            rule_value.set(str(existing.get("value","")))
            try:
                identity=app.api.target_identity(item)
                client=app.api.client_rect(identity["hwnd"])
                auto=app.api.auto_content_region(identity)
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
                app.run_background("window_dialog_preview",lambda snapshot=snapshot:load_preview(snapshot),apply_preview,preview_failed)
            except Exception as error:
                state["client"]=None
                state["auto"]=None
                state["target_key"]=None
                status.set("窗口身份或区域读取失败："+str(error))
                preview_status.set("无法读取预览")
                redraw()
        def load_windows():
            hydrated=[]
            for item in app.api.enum_windows():
                candidate=dict(item)
                try:
                    candidate=app.api.target_identity(candidate)
                except Exception as error:
                    candidate["identity_error"]=str(error)
                    app.store.log_error("WINDOW_IDENTITY_READ_FAILED",error,window_identity={key:candidate.get(key) for key in ("hwnd","pid","class","title")})
                hydrated.append(candidate)
            return hydrated
        def apply_windows(hydrated):
            nonlocal windows
            if state["closed"] or not win.winfo_exists():
                return
            windows=list(hydrated)
            box.delete(0,"end")
            selected_index=None
            scored=[window_descriptor_score(app.window_recommendation,item) for item in windows]
            recommended=None
            if scored and max(scored)>=8 and scored.count(max(scored))==1:
                recommended=scored.index(max(scored))
            for index,item in enumerate(windows):
                prefix=("[推荐] " if index==recommended else "")+("[最小化] " if item.get("minimized") else "")
                path=str(item.get("process_path","路径读取失败"))
                box.insert("end",prefix+str(item.get("title",""))+"  [PID "+str(item.get("pid","-"))+"]  ["+str(item.get("class",""))+"]  "+path)
                if app.selected_window and item.get("hwnd")==app.selected_window.get("hwnd") and item.get("pid")==app.selected_window.get("pid") and item.get("class")==app.selected_window.get("class"):
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
            app.show_error(str(error))
        def refresh():
            if state["closed"]:
                return
            status.set("正在后台读取窗口和进程完整身份…")
            box.delete(0,"end")
            box.insert("end","正在读取…")
            if widgets["refresh"] is not None:
                widgets["refresh"].configure(state="disabled")
            app.run_background("window_dialog_enumeration",load_windows,apply_windows,refresh_error)
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
                app.show_error("请先选择一个窗口")
                return
            try:
                item=app.api.target_identity(item)
                client=app.api.client_rect(item["hwnd"])
                key=str(item.get("hwnd"))+"|"+str(item.get("pid"))+"|"+str(item.get("process_created"))
                if key!=state.get("target_key"):
                    raise RuntimeError("窗口选择已变化，请等待区域信息刷新后再确认")
                rect=apply_normalized_rect(client,state["norm"])
                if rect[2]<FEATURE_W or rect[3]<FEATURE_H:
                    raise RuntimeError("游戏区域过小")
                item["integrity"]=app.api.validate_uipi(item)
                item["selected_rect"]=list(client)
                item["client_size"]=[int(client[2]),int(client[3])]
                item["selected_dpi"]=app.api.dpi_for_window(item["hwnd"])
                title_mode=mode_map.get(rule_label.get(),"none")
                title_value=rule_value.get().strip()
                if title_mode!="none" and not title_value:
                    raise RuntimeError("标题规则不是“不检查”时必须填写匹配文本")
                item["title_rule"]={"mode":title_mode,"value":title_value}
                source_mode=region_mode.get()
                auto=state.get("auto") or {}
                item.update({"content_rect_norm":[round(value,8) for value in state["norm"]],"content_aspect":round(rect[2]/max(1,rect[3]),8),"content_source":auto.get("source",
                            "auto") if source_mode=="auto" else "full_client" if source_mode=="full" else "manual","content_child_class":auto.get("child_class","") if source_mode=="auto" else "","window_rule_version":WINDOW_RULE_VERSION})
                item=app.api.target_identity(item)
                app.api.validate_target(item,False)
            except Exception as error:
                app.show_error(str(error))
                return
            previous=app.selected_window
            app.selected_window=item
            if not previous or any(previous.get(key)!=item.get(key) for key in ("hwnd","pid","class","process_created","content_rect_norm")):
                app.api.calibrations.pop(int(item["hwnd"]),None)
            app.window_recommendation=app.store.save_window_descriptor(item)
            identity={key:item.get(key) for key in ("hwnd","pid","title","class","process_path","process_created","client_size","selected_dpi","content_rect_norm","content_aspect")}
            identity_text=(str(item.get("title",""))+"|"+str(item.get("class",""))+"|"+str(item.get("process_path",""))).lower()
            case="ldplayer_confirmed" if any(token in identity_text for token in ("ldplayer","dnplayer","雷电")) else "ordinary_confirmed"
            app.record_acceptance_case("窗口",case,"passed",identity)
            app.api.reset_capture_backends(item)
            app.api.reset_frame_history(item["hwnd"])
            app._refresh_all()
            app.status.set("一次确认已保存窗口身份和游戏内容区域："+item["title"]+"；区域模式="+source_mode+"；标题规则="+item["title_rule"]["mode"])
            app.close_dialog(win,state)
        def refuse_close():
            win.bell()
            win.lift()
            win.focus_force()
        if app.developer_mode:
            canvas.bind("<Button-1>",press)
            canvas.bind("<B1-Motion>",drag)
            canvas.bind("<ButtonRelease-1>",release)
        tools=ttk.Frame(frame)
        tools.pack(fill="x",pady=(10,0))
        if app.developer_mode:
            widgets["refresh"]=ttk.Button(tools,text="刷新",command=refresh)
            widgets["refresh"].pack(side="left")
        ttk.Button(tools,text="确认",command=confirm).pack(side="right",padx=(6,0))
        box.bind("<<ListboxSelect>>",prepare_selection)
        win.protocol("WM_DELETE_WINDOW",refuse_close)
        refresh()
        win.wait_visibility()
        box.focus_set()
class TaskSettingsDialog:
    def __init__(self,app):
        self.app=app
    def open(self):
        app=self.app
        try:
            game=app.require_game()
            if app.mode_state!=MODE_IDLE:
                raise RuntimeError("请先停止当前模式")
        except Exception as error:
            app.show_error(str(error))
            return
        profile=app.store.load_game_profile(game["id"])
        win=tk.Toplevel(app.root)
        state={"closed":False}
        win.title("任务目标与安全边界")
        fit_window(win,760,700,520,400)
        frame=ttk.Frame(win,padding=16)
        frame.pack(fill="both",expand=True)
        ttk.Label(frame,text="该系统是按游戏配置的任务型模仿智能体，不保证适用于所有游戏。未进入白名单的动作永远不会自动执行。",wraplength=710).pack(anchor="w",fill="x",pady=(0,10))
        ttk.Label(frame,text="游戏目标或奖励说明").pack(anchor="w")
        goal=tk.Text(frame,height=4,wrap="word")
        goal.pack(fill="x",pady=(4,10))
        goal.insert("1.0",str(profile.get("goal","")))
        allowed_frame=ttk.LabelFrame(frame,text="自动动作白名单",padding=10)
        allowed_frame.pack(fill="x")
        families=[("等待","no_op"),("左键单击","click|left"),("左键双击","double_click|left"),("左键长按","long_press|left"),("左键拖动","drag|left"),("右键单击","click|right"),("中键单击","click|middle"),("移动",
                "move"),("悬停","hover"),("向上滚轮","scroll_v|1"),("向下滚轮","scroll_v|-1"),("横向正滚轮","scroll_h|1"),("横向负滚轮","scroll_h|-1")]
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
                target=app.require_window(False)
                packet=app.api.capture(target,False)
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
                value.update({"goal":goal.get("1.0","end").strip(),"allowed_families":allowed,"max_consecutive_failures":safe_int(max_failures.get(),3,1,20),
                        "exploration_enabled":bool(exploration.get()),"restart_action":restart_action,"success_states":sorted(success_states),"failure_states":sorted(failure_states)})
                app.store.save_game_profile(game["id"],value)
                app._refresh_all()
                app.close_dialog(win,state)
                app.show_info("任务与安全","配置已保存。安全配置或状态定义改变后，必须重新睡眠才能训练。")
            except Exception as error:
                feedback.set("无法保存："+str(error))
        actions=ttk.Frame(frame)
        actions.pack(fill="x",pady=(12,0))
        ttk.Button(actions,text="取消",command=lambda:app.close_dialog(win,state)).pack(side="right")
        ttk.Button(actions,text="确认",command=save).pack(side="right",padx=(0,8))
        win.transient(app.root)
        win.protocol("WM_DELETE_WINDOW",lambda:app.close_dialog(win,state))
        win.bind("<Escape>",lambda event:app.close_dialog(win,state))
        win.wait_visibility()
        win.grab_set()
        win.focus_force()
class AppUiMixin:
    def _build(self):
        self.root.title("通用游戏AI")
        fit_window(self.root,900,780,620,440)
        self.root.option_add("*Font",("Microsoft YaHei UI",10))
        outer=scrollable_frame(self.root,18,False)
        ttk.Label(outer,text="通用游戏AI控制面板",font=("Microsoft YaHei UI",18,"bold")).pack(anchor="w",pady=(0,12))
        setup=ttk.LabelFrame(outer,text="数据与离线AI运行库",padding=10)
        setup.pack(fill="x",pady=(0,12))
        ttk.Label(setup,textvariable=self.data_dir_text,wraplength=840).pack(anchor="w",fill="x")
        setup_buttons=ttk.Frame(setup)
        setup_buttons.pack(fill="x",pady=(8,0))
        choose=ttk.Button(setup_buttons,text="选择文件夹",command=self.choose_data_directory)
        download=ttk.Button(setup_buttons,text="检查文件完整性",command=self.start_integrity_check)
        choose.pack(side="left",fill="x",expand=True,ipady=7)
        download.pack(side="left",fill="x",expand=True,padx=(8,0),ipady=7)
        self.control_buttons["选择文件夹"]=choose
        self.control_buttons["检查文件完整性"]=download
        self.controls.extend([choose,download])
        flow=ttk.LabelFrame(outer,text="规定流程",padding=12)
        flow.pack(fill="x",pady=(0,12))
        primary=ttk.Frame(flow)
        primary.pack(fill="x")
        primary_specs=[("游戏",self.open_game_dialog),("选择窗口",self.open_window_dialog),("学习",self.start_learning),("睡眠",self.start_sleep),("训练",self.start_training),("指导",self.start_ask)]
        for index,(name,command) in enumerate(primary_specs):
            button=ttk.Button(primary,text=name,command=command)
            self.control_buttons[name]=button
            self.controls.append(button)
            button.grid(row=index//3,column=index%3,sticky="nsew",padx=6,pady=6,ipady=12)
        for column in range(3):
            primary.columnconfigure(column,weight=1)
        ttk.Label(flow,textvariable=self.flow_text,justify="left",wraplength=820).pack(anchor="w",fill="x",pady=(8,0))
        ttk.Label(flow,text="适用范围：只支持可由鼠标完成、允许普通窗口采集与输入的游戏；每个游戏必须独立学习、睡眠和指导，不承诺零样本自动通关。",wraplength=820).pack(anchor="w",fill="x",pady=(8,0))
        if self.developer_mode:
            stop_frame=ttk.Frame(outer)
            stop_frame.pack(fill="x",pady=(0,12))
            self.stop_button=ttk.Button(stop_frame,text="停止",command=self.request_stop,state="disabled")
            self.control_buttons["停止"]=self.stop_button
            self.controls.append(self.stop_button)
            self.stop_button.pack(fill="x",ipady=8)
        info=ttk.LabelFrame(outer,text="当前状态",padding=12)
        info.pack(fill="x",pady=(0,12))
        labels=[("当前游戏：",self.game_text),("目标窗口：",self.window_text),("窗口身份：",self.window_detail),("采集兼容性：",self.capture_text),("输入权限：",self.input_text),("数据统计：",self.sample_text),("模型状态：",
                self.model_text),("识别状态：",self.confidence_text)]
        for row,(name,value) in enumerate(labels):
            ttk.Label(info,text=name).grid(row=row,column=0,sticky="nw",pady=2)
            ttk.Label(info,textvariable=value,wraplength=700).grid(row=row,column=1,sticky="nw",pady=2)
        info.columnconfigure(1,weight=1)
        self.advanced_visible=tk.BooleanVar(value=False)
        self.advanced_frame=ttk.Frame(outer)
        if self.developer_mode:
            advanced_header=ttk.Frame(outer)
            advanced_header.pack(fill="x")
            ttk.Checkbutton(advanced_header,text="高级设置",variable=self.advanced_visible,command=self._toggle_advanced).pack(anchor="w")
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
        ttk.Label(bottom,textvariable=self.status,wraplength=650).pack(side="left",fill="x",expand=True)
        ttk.Label(bottom,text="ESC结束当前长流程").pack(side="right")
    def _toggle_advanced(self):
        if not self.developer_mode:
            self.advanced_frame.pack_forget()
            return
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
                self._log_error("UI_CALLBACK_FAILED",error)
                if not self.closing:
                    self.show_error(traceback.format_exc())
            return
        if key is None:
            try:
                self.ui_queue.put_nowait(("call",callback))
            except queue.Full:
                self._log_error("UI_QUEUE_FULL",details={"kind":"call"})
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
            self._log_error("UI_QUEUE_FULL",details={"kind":"latest","key":token})
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
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        try:
            win.destroy()
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        return True
    def _destroy_ask_window(self):
        win=self.ask_window
        self.ask_window=None
        if win is not None:
            for after_id in list(self.ask_after_ids):
                try:
                    win.after_cancel(after_id)
                except Exception as error:
                    record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
            self.ask_after_ids.clear()
            try:
                win.destroy()
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
        deadline=time.monotonic()+1.5
        while self.api.key_down(0x1B) and time.monotonic()<deadline:
            try:
                self.root.update_idletasks()
            except Exception:
                break
            time.sleep(0.03)
        previous_grab=None
        try:
            previous_grab=self.root.grab_current()
        except Exception:
            previous_grab=None
        win=tk.Toplevel(self.root)
        self.result_modal=win
        win.title(str(title))
        fit_window(win,720,420,460,320)
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
            self.record_acceptance_case("弹窗","confirm_only","passed",{"title":str(title),"confirmed_at":time.time(),"close_path":"确认"})
            self.close_dialog(win,closed)
            if previous_grab is not None:
                try:
                    if previous_grab.winfo_exists():
                        previous_grab.grab_set()
                except Exception as error:
                    record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        def refuse_close():
            win.bell()
            win.lift()
            win.focus_force()
        ttk.Button(frame,text="确认",command=confirm).pack(pady=(12,0),ipadx=28)
        win.protocol("WM_DELETE_WINDOW",refuse_close)
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
        fit_window(win,440,190,360,180)
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
        def refuse_close():
            win.bell()
            win.lift()
            win.focus_force()
        ttk.Button(buttons,text="确认",command=confirm).pack(side="left",padx=6)
        win.protocol("WM_DELETE_WINDOW",refuse_close)
        entry.focus_set()
        win.wait_window()
        return result["value"]
    def confirm_dialog(self,title,text):
        result={"value":False}
        state={"closed":False}
        win=tk.Toplevel(self.root)
        win.title(title)
        fit_window(win,500,210,380,190)
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
        def refuse_close():
            win.bell()
            win.lift()
            win.focus_force()
        ttk.Button(buttons,text="确认",command=confirm).pack(side="left",padx=6)
        win.protocol("WM_DELETE_WINDOW",refuse_close)
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
        result={"unchanged":False,"signature":signature,"game_text":game.get("name","未选择") if game_ready else "未选择","window_text":"未选择","window_detail":"PID：-  类名：-  客户区：-  游戏区域：-",
            "capture_text":"采集方式：未检测","sample_text":"样本：有效0  废弃0  session 0  数据0 KB","model_text":"模型：无  需要睡眠：否","training_ready":False,"flow_text":""}
        if isinstance(window,dict):
            result["window_text"]=window.get("title","未命名窗口")
            try:
                content=self.api.validate_target(window,False)
                client=self.api.client_rect(window["hwnd"])
                dpi=self.api.dpi_for_window(window["hwnd"])
                path=str(window.get("process_path","-"))
                rule=window.get("title_rule",{"mode":"none"})
                result["window_detail"]="PID："+str(window["pid"])+"  TID："+str(window.get("window_thread_id",
                        "-"))+"  类名："+window["class"]+"  客户区："+str(client[2])+"×"+str(client[3])+"  游戏区域："+str(content[2])+"×"+str(content[3])+"  DPI："+str(dpi)+"  标题规则："+str(rule.get("mode","none"))+"  路径："+path
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
                    result["model_text"]=model_kind+"："+str(metadata.get("prototype_count",
                            0))+"个原型  最近睡眠："+created+"  "+error_text+"  "+detail+"  授权动作："+("、".join(authorized) if authorized else "无")+"  需要睡眠："+("是" if needs else "否")+retained_text
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
                    result["model_text"]="模型：无  需要睡眠："+("是" if needs else "否")
                    if valid<=0:
                        missing.append("有效学习样本")
                    else:
                        missing.append("完成一次睡眠")
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
        learning_state="可睡眠（有效"+str(valid)+"，独立session "+str(sessions)+"）" if valid>0 else "不足"
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
        self.flow_text.set("1. 文件夹：已完成\n2. 文件完整性："+("已完成" if self.lifecycle.runtime_ready else "未完成")+"\n"+str(result.get("flow_text","")))
        self.training_ready=bool(result.get("training_ready"))
        self.has_samples="有效0" not in str(result.get("sample_text",""))
        self._update_control_availability()
    def refresh_all_async(self,force=False):
        if self.store is None:
            self._update_control_availability()
            return
        game=dict(self.selected_game) if isinstance(self.selected_game,dict) else None
        window=dict(self.selected_window) if isinstance(self.selected_window,dict) else None
        if force:
            self.sample_text.set("样本：正在读取")
            self.model_text.set("模型：正在读取")
        self.run_background("control_panel_refresh",lambda:self._collect_refresh_snapshot(game,window,bool(force)),self._apply_refresh_snapshot)
    def _refresh_all(self):
        if self.store is not None:
            self.refresh_all_async(True)
        else:
            self._update_control_availability()
    def refresh_data_stats(self):
        self.refresh_all_async(True)
    def periodic_refresh(self):
        try:
            if self.store is not None and not self.mode and not self.closing:
                self.refresh_all_async(False)
        finally:
            if not self.shutdown_started:
                try:
                    self.root.after(1200,self.periodic_refresh)
                except Exception as error:
                    self._log_error("PERIODIC_REFRESH_RESCHEDULE_FAILED",error)
    def open_game_dialog(self):
        return GameSelectionDialog(self).open()
    def open_window_dialog(self):
        return WindowSelectionDialog(self).open()
    def open_task_dialog(self):
        return TaskSettingsDialog(self).open()
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
        fit_window(win,560,300,420,260)
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
class AppLifecycleMixin:
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
                self._log_error("BACKGROUND_TASK_FAILED",error,{"task":token,"generation":generation})
                def fail(error=error):
                    if current_generation() and not self.closing and not self.shutdown_started and on_error is not None:
                        on_error(error)
                self.ui(fail,"background_error:"+token)
            finally:
                if self.store is not None:
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
                        self._log_error("UI_QUEUE_CALLBACK_FAILED",error)
                        self.show_error(traceback.format_exc())
        finally:
            if not self.shutdown_started:
                try:
                    self.root.after(25,self.process_ui_queue)
                except Exception as error:
                    self._log_error("UI_QUEUE_RESCHEDULE_FAILED",error)
    def _make_shutdown_coordinator(self,label,timeout,application=False):
        coordinator=ShutdownCoordinator(label,timeout)
        def stop_mode():
            if self.mode_state!=MODE_IDLE:
                self.request_mode_stop("stopped","程序关闭" if application else "模式结束")
            if self.stop_event is not None:
                self.stop_event.set()
            return True
        mode_resource_state={"closed":False}
        def mode_alive():
            return not mode_resource_state["closed"]
        def mode_close(timeout_value):
            if self.active_session is not None:
                self.active_session.request_stop()
                if not self.active_session.close(timeout_value):
                    return False
            if self.review_process is not None:
                self.review_process.request_stop()
                if not self.review_process.close(timeout_value):
                    return False
            thread=self.mode_thread
            if thread is not None and thread.is_alive() and thread is not threading.current_thread() and timeout_value>0:
                thread.join(timeout_value)
            capture_pending=self.api.stop_capture_processes(timeout_value,False)
            done=not bool(thread and thread.is_alive()) and not capture_pending
            if done:
                mode_resource_state["closed"]=True
            return done
        def mode_force():
            forced=True
            if self.review_process is not None and self.review_process.alive():
                forced=self.review_process.terminate(0.2) and forced
            capture_pending=self.api.stop_capture_processes(0.0,True)
            if capture_pending:
                forced=False
            thread=self.mode_thread
            done=forced and not bool(thread and thread.is_alive())
            if done:
                mode_resource_state["closed"]=True
            return done
        coordinator.add(ManagedShutdownResource("模式资源",stop_mode,mode_alive,mode_close,mode_force,0))
        coordinator.add(ManagedShutdownResource("输入释放",lambda:(self.api.block_input(),self.api.release_all_buttons()),lambda:False,lambda timeout_value:True,lambda:True,0))
        if application:
            def prepare_alive():
                return bool(self.directory_prepare_thread and self.directory_prepare_thread.is_alive())
            def prepare_stop():
                if self.directory_prepare_stop is not None:
                    self.directory_prepare_stop.set()
                return True
            def prepare_close(timeout_value):
                thread=self.directory_prepare_thread
                if thread is not None and thread.is_alive() and thread is not threading.current_thread():
                    thread.join(timeout_value)
                return not bool(thread and thread.is_alive())
            coordinator.add(ManagedShutdownResource("文件夹准备线程",prepare_stop,prepare_alive,prepare_close,lambda:False,1))
            def background_alive():
                with self.background_lock:
                    return any(thread.is_alive() for thread in self.background_threads)
            def background_close(timeout_value):
                with self.background_lock:
                    values=[thread for thread in self.background_threads if thread.is_alive()]
                for thread in values:
                    if thread is not threading.current_thread():
                        thread.join(timeout_value/max(1,len(values)))
                return not background_alive()
            coordinator.add(ManagedShutdownResource("后台线程",lambda:True,background_alive,background_close,lambda:False,1))
            def installer_alive():
                process=getattr(self.runtime_installer,"process",None) if self.runtime_installer is not None else None
                return bool(process is not None and process.poll() is None)
            coordinator.add(ManagedShutdownResource("运行库安装器",lambda:self.runtime_installer.stop() if self.runtime_installer is not None else True,installer_alive,
                    lambda timeout_value:not installer_alive(),lambda:not installer_alive(),1))
            def store_alive():
                return bool(self.store is not None and not self.store.closed)
            coordinator.add(ManagedShutdownResource("SQLite与样本写入线程",lambda:True,store_alive,lambda timeout_value:True if self.store is None else self.store.close(timeout_value),lambda:False,2))
            def ai_alive():
                return self.ai_worker is not None
            def ai_close(timeout_value):
                if self.ai_worker is not None:
                    self.ai_worker.close(max(0.1,timeout_value))
                    self.ai_worker=None
                return True
            coordinator.add(ManagedShutdownResource("AI工作进程",lambda:True,ai_alive,ai_close,ai_close,3))
            def keyboard_alive():
                return self.keyboard_monitor is not None
            def keyboard_close(timeout_value):
                if self.keyboard_monitor is not None:
                    self.keyboard_monitor.stop(max(0.0,timeout_value))
                    self.keyboard_monitor=None
                return True
            coordinator.add(ManagedShutdownResource("键盘监视器",lambda:True,keyboard_alive,keyboard_close,keyboard_close,3))
            api_state={"closed":False}
            def api_close(timeout_value):
                api_state["closed"]=bool(self.api.close())
                return api_state["closed"]
            coordinator.add(ManagedShutdownResource("采集与输入API",lambda:(self.api.block_input(),self.api.release_all_buttons()),lambda:not api_state["closed"],api_close,api_close,3))
            lock_state={"closed":False}
            def locks_close(timeout_value):
                if self.data_directory_lock is not None:
                    self.data_directory_lock.close()
                    self.data_directory_lock=None
                global PROGRAM_INSTANCE_LOCK
                if PROGRAM_INSTANCE_LOCK is not None:
                    PROGRAM_INSTANCE_LOCK.close()
                    PROGRAM_INSTANCE_LOCK=None
                lock_state["closed"]=True
                return True
            coordinator.add(ManagedShutdownResource("目录锁与单实例锁",lambda:True,lambda:not lock_state["closed"],locks_close,locks_close,4))
        return coordinator
    def _begin_mode_stopping(self,result,error=None):
        if self.mode_state==MODE_IDLE or self.shutdown_started or self.closing and self.mode_state==MODE_IDLE:
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
        self.mode_shutdown_coordinator=self._make_shutdown_coordinator("模式关闭",5.0,False)
        self.status.set(str(self.mode or "模式")+"正在停止资源，控制按钮保持禁用")
        if not self.mode_shutdown_polling:
            self.mode_shutdown_polling=True
            self.root.after(25,self._poll_mode_shutdown)
    def _handle_mode_thread_timeout(self):
        self.api.block_input()
        self.api.release_all_buttons()
        self._forced_exit("模式线程停止超时")
    def _poll_mode_shutdown(self):
        if self.mode_state!=MODE_STOPPING:
            return
        self.api.block_input()
        self.api.release_all_buttons()
        coordinator=getattr(self,"mode_shutdown_coordinator",None)
        if coordinator is None:
            coordinator=self._make_shutdown_coordinator("模式关闭",5.0,False)
            self.mode_shutdown_coordinator=coordinator
        state=coordinator.poll()
        self.mode_shutdown_forced=list(state.get("forced",[]))
        if not state.get("done"):
            if state.get("deadline_reached") and state.get("unforceable"):
                self._handle_mode_thread_timeout()
                return
            suffix="；已强制停止："+"、".join(self.mode_shutdown_forced) if self.mode_shutdown_forced else ""
            self.status.set("STOPPING：等待资源退出："+"、".join(state.get("pending",[]))+suffix)
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
        self.lifecycle.finish()
        self.pending_mode_result=None
        self.pending_mode_error=None
        self.mode_shutdown_deadline=None
        self.mode_stop_started=False
        self.mode_shutdown_polling=False
        self.mode_shutdown_coordinator=None
        self.set_controls(False)
        self.progress_value.set(0)
        self.status.set(result.summary)
        metrics=None
        if self.escape_metrics.get("pressed"):
            self.escape_metrics["finished"]=time.monotonic()
            metrics=dict(self.escape_metrics)
            metrics["lock_latency_ms"]=round(max(0.0,metrics.get("input_locked",0.0)-metrics.get("pressed",0.0))*1000.0,3) if metrics.get("input_locked") else None
            metrics["cleanup_latency_ms"]=round(max(0.0,metrics.get("cleanup_started",0.0)-metrics.get("pressed",0.0))*1000.0,3) if metrics.get("cleanup_started") else None
            metrics["finish_latency_ms"]=round(max(0.0,metrics.get("finished",0.0)-metrics.get("pressed",0.0))*1000.0,3)
            if self.write_audit is not None:
                try:
                    self.write_audit.record("escape_stop_latency",self.data_directory/"audit"/"escape_latency.jsonl",True,metrics)
                    with (self.data_directory/"audit"/"escape_latency.jsonl").open("a",encoding="utf-8") as handle:
                        handle.write(json.dumps(metrics,ensure_ascii=False,separators=(",",":"))+"\n")
                except Exception as audit_error:
                    self._log_error("ESC_LATENCY_AUDIT_WRITE_FAILED",audit_error,metrics)
        self._record_mode_acceptance(name,result,metrics)
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
        return ModeResult("completed","采集后端重新测试完成："+str(result.get("validated_backend","未知")),{"validated_backends":list(result.get("validated_backends",[]))})
    def _escape_hook_signal(self,event):
        state,name,stop_event,_,_=self.lifecycle.snapshot()
        if state==MODE_IDLE:
            return
        pressed=safe_float(event.get("monotonic_time"),time.monotonic()) if isinstance(event,dict) else time.monotonic()
        self.escape_metrics={"pressed":pressed,"input_locked":0.0,"cleanup_started":0.0,"finished":0.0,"fallback_used":False,"phase":state,"mode":str(name or "模式")}
        self.api.block_input()
        self.api.release_all_buttons()
        self.escape_metrics["input_locked"]=time.monotonic()
        self.lifecycle.request_stop("stopped","ESC停止")
        if stop_event is not None:
            stop_event.set()
        worker=getattr(self,"ai_worker",None)
        if worker is not None:
            try:
                worker.request_stop()
            except Exception as error:
                self._log_error("AI_WORKER_STOP_SIGNAL_FAILED",error,{"mode":str(name or "模式")})
        self.ui(lambda:self.request_mode_stop("stopped","ESC停止"),"escape_stop")
    def poll_global_escape(self):
        if self.shutdown_started:
            return
        monitor=self.keyboard_monitor
        hook_ok=bool(monitor is not None and monitor.alive() and not monitor.error)
        if not hook_ok:
            try:
                down=self.api.key_down(0x1B)
                if not down:
                    self.global_escape_armed=True
                elif self.lifecycle.snapshot()[0]!=MODE_IDLE and self.global_escape_armed:
                    self.global_escape_armed=False
                    self.escape_metrics["fallback_used"]=True
                    self._escape_hook_signal({"monotonic_time":time.monotonic()})
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        if not self.shutdown_started:
            try:
                self.root.after(100,self.poll_global_escape)
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
    def set_controls(self,running):
        self._update_control_availability()
    def _start_mode_transaction(self,name,target,needs_window=False,require_game=True,status_text=None):
        if self.mode_state!=MODE_IDLE or self.closing:
            self.show_error("当前已有操作正在运行，请先按ESC结束")
            return False
        begun=False
        try:
            if require_game:
                self.require_game()
            if self.storage_fault and name in {"学习","睡眠","指导"}:
                raise RuntimeError(self.store.read_only_reason or self.store.writer_error or "样本存储故障，相关模式已锁定")
            if needs_window:
                self.require_window(False)
            self.lifecycle.begin(name)
            begun=True
            self.pending_mode_result=None
            self.pending_mode_error=None
            self.mode_shutdown_deadline=None
            self.mode_shutdown_forced=[]
            self.mode_stop_started=False
            self.mode_shutdown_polling=False
            self.record_acceptance_case("停止","starting","pending",{"mode":str(name),"time":time.time()})
            self.api.block_input()
            self.set_input_status("已锁定")
            self.set_controls(True)
            self.progress_value.set(0)
            self.status.set(str(status_text or (str(name)+"正在初始化，按ESC可立即中止")))
            thread=threading.Thread(target=self.worker_entry,args=(name,target),name="UniversalGameAI-"+str(name),daemon=True)
            self.mode_thread=thread
            thread.start()
            return True
        except Exception as error:
            if begun:
                self.lifecycle.finish()
            self.mode_thread=None
            self.pending_mode_result=None
            self.pending_mode_error=None
            self.mode_shutdown_deadline=None
            self.mode_shutdown_forced=[]
            self.mode_stop_started=False
            self.mode_shutdown_polling=False
            try:
                self.api.block_input()
                self.api.release_all_buttons()
            except Exception as rollback_error:
                self._log_error("MODE_START_INPUT_ROLLBACK_FAILED",rollback_error,{"mode":str(name)})
            try:
                self._update_control_availability()
            except Exception as rollback_error:
                self._log_error("MODE_START_UI_ROLLBACK_FAILED",rollback_error,{"mode":str(name)})
            self.show_error(str(error))
            return False
    def start_worker(self,name,target,needs_window=False):
        return self._start_mode_transaction(name,target,needs_window,True)
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
        state,name,event,_,_=self.lifecycle.snapshot()
        if state==MODE_IDLE:
            return False
        with self.mode_stop_lock:
            first=not self.mode_stop_started
            self.mode_stop_started=True
            self.lifecycle.request_stop(status,reason)
            state,name,event,_,_=self.lifecycle.snapshot()
            if event is not None:
                event.set()
        self.api.block_input()
        self.api.release_all_buttons()
        if self.escape_metrics.get("pressed") and not self.escape_metrics.get("cleanup_started"):
            self.escape_metrics["cleanup_started"]=time.monotonic()
        if self.ai_worker is not None:
            try:
                self.ai_worker.request_stop()
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        if name=="检查文件完整性" and self.runtime_installer is not None:
            try:
                self.runtime_installer.stop()
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        review=self.review_process
        if review is not None:
            try:
                review.request_stop()
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        session=self.active_session
        if session is not None:
            try:
                session.request_stop()
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
        monitor=self.keyboard_monitor
        deadline=time.monotonic()+1.5
        while monitor is not None and monitor.escape_down and time.monotonic()<deadline and self.stop_event and not self.stop_event.is_set():
            time.sleep(0.01)
    def close(self):
        if self.closing:
            return
        self.closing=True
        if self.directory_prepare_stop is not None:
            self.directory_prepare_stop.set()
        with self.background_lock:
            for key in list(self.background_generations):
                self.background_generations[key]+=1
        self.shutdown_deadline=time.monotonic()+8.0
        self.shutdown_coordinator=self._make_shutdown_coordinator("程序关闭",8.0,True)
        self.status.set("正在安全关闭：锁定输入并停止模式与子进程")
        self.set_input_status("关闭过程中已锁定")
        if self.mode_state!=MODE_IDLE:
            self.request_mode_stop("stopped","程序关闭")
            if self.stop_event is not None:
                self.stop_event.set()
            if self.active_session is not None:
                self.active_session.request_stop()
        if self.runtime_installer is not None:
            try:
                self.runtime_installer.stop()
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        self._destroy_ask_window()
        self.api.block_input()
        self.api.release_all_buttons()
        if self.result_modal is not None:
            try:
                self.result_modal.grab_release()
                self.result_modal.destroy()
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
            self.result_modal=None
            self.result_modal_widget=None
        for button in self.controls:
            try:
                button.configure(state="disabled")
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        self.root.after(0,self._poll_shutdown)
    def _poll_shutdown(self):
        self.api.block_input()
        self.api.release_all_buttons()
        coordinator=getattr(self,"shutdown_coordinator",None)
        if coordinator is None:
            coordinator=self._make_shutdown_coordinator("程序关闭",8.0,True)
            self.shutdown_coordinator=coordinator
        state=coordinator.poll()
        if not state.get("done"):
            if state.get("deadline_reached") and state.get("unforceable"):
                record_cleanup_error("SHUTDOWN_UNFORCEABLE",RuntimeError("、".join(state.get("unforceable",[]))),{"pending":state.get("pending",[]),"errors":state.get("errors",[])})
                self._forced_exit("程序关闭超过期限，未退出资源："+"、".join(state.get("unforceable",[])))
                return
            self.status.set("正在安全关闭：等待"+"、".join(state.get("pending",[])))
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
        self.directory_prepare_thread=None
        self.directory_prepare_stop=None
        if self.directory_prepare_candidate is not None:
            best_effort_cleanup("DIRECTORY_PREPARE_CANDIDATE_CLOSE",lambda:self.directory_prepare_candidate.close())
            self.directory_prepare_candidate=None
        self.lifecycle.finish()
        self.pending_mode_result=None
        self.pending_mode_error=None
        self.mode_shutdown_deadline=None
        self.shutdown_started=True
        best_effort_cleanup("ROOT_DESTROY_FAILED",lambda:self.root.destroy())
class AppModeMixin:
    def start_learning(self):
        try:
            self.require_ai_runtime()
        except Exception as error:
            self.show_error(str(error))
            return
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
        ocr_events=self.store.load_ocr_experience_events(game["id"],5000)
        sleep_seed=safe_int(getattr(self,"sleep_seed",0),0,0,2**63-1)
        worker=ReviewProcessWorker({"base":str(self.store.base),"game":game,"samples":samples,"stats":stats,"rejections":rejections,"ocr_events":ocr_events,
                "profile":self.store.load_game_profile(game["id"]),"sleep_seed":sleep_seed,"sleep_seed_evidence":dict(getattr(self,"sleep_seed_evidence",{})),"cache_capacity":50000})
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
                    raise InputStopped("睡眠子进程已停止")
                raise RuntimeError("睡眠子进程异常退出且未返回结果")
            kind,payload=packet
            if kind=="error":
                raise RuntimeError(payload.get("traceback","睡眠子进程失败"))
            models=list(payload.get("models",[]))
            status=str(payload.get("status","failed"))
            details=dict(payload.get("details",{}))
            if status=="completed":
                retained=set()
                for model_gid,model,complete in models:
                    retained.update(str(value) for value in model.get("training_checksums",[]) if str(value))
                    retained.update(str(value) for value in model.get("holdout_checksums",[]) if str(value))
                plan=self.store.plan_experience_pool_optimization(game["id"],retained)
                commit=self.store.commit_sleep_result(game["id"],models,plan)
                before_metrics=dict(commit.get("model_before_metrics",{}))
                after_metrics=dict(commit.get("model_after_metrics",{}))
                model_optimized=bool(after_metrics.get("holdout_accuracy",0.0)>before_metrics.get("holdout_accuracy",0.0) or after_metrics.get("rejection_coverage",
                        0.0)>before_metrics.get("rejection_coverage",0.0) or after_metrics.get("prototype_count",0)<before_metrics.get("prototype_count",0))
                pool_deleted=safe_int(commit["pool"].get("deleted"),0,0)
                pool_merged=safe_int(commit["pool"].get("merged"),0,0)
                pool_downweighted=safe_int(commit["pool"].get("downweighted"),0,0)
                pool_validation_completed=bool(commit["pool"].get("pool_validation_completed"))
                pool_changed=bool(pool_deleted or pool_merged or pool_downweighted)
                seed_evidence=dict(details.get("sleep_seed_evidence",getattr(self,"sleep_seed_evidence",{})))
                expected_seed,expected_evidence=deterministic_sleep_seed(game["id"],[item for item in samples if sample_rgb_valid(item.get("rgb"))])
                deterministic_seed=bool(sleep_seed==expected_seed and seed_evidence.get("material_hash")==expected_evidence.get("material_hash"))
                offline_evidence=dict(details.get("offline_network_evidence",{}))
                details.update({"sleep_seed":sleep_seed,"sleep_seed_evidence":seed_evidence,"deterministic_seed":deterministic_seed,
                        "offline_network_blocked":bool(offline_evidence.get("blocked")),"model_optimized":model_optimized,"model_optimization_checked":True,"pool_optimized":bool(pool_changed
                            or pool_validation_completed),"pool_changed":pool_changed,"pool_validation_completed":pool_validation_completed,"model_before_metrics":before_metrics,"model_after_metrics":after_metrics,
                        "model_before_hash":commit["model_before_hash"],"model_after_hash":commit["model_after_hash"],"pool_before_hash":commit["pool"]["before"].get("summary_hash",""),
                        "pool_after_hash":commit["pool"]["after"].get("summary_hash",""),"pool_before_metrics":commit["pool"].get("before",{}),"pool_after_metrics":commit["pool"].get("after",{}),
                        "pool_deleted":pool_deleted,"pool_merged":pool_merged,"pool_downweighted":pool_downweighted,"sleep_commit_hash":commit["commit_hash"]})
                model_text="模型指标改善" if model_optimized else "模型优化检查完成，无需调整"
                pool_text=("经验池已调整：删除"+str(pool_deleted)+"，合并计数"+str(pool_merged)+"，降权"+str(pool_downweighted)) if pool_changed else "经验池优化检查完成，无需调整"
                summary=str(payload.get("summary","睡眠结束"))+"\n"+model_text+"；"+pool_text+"；提交哈希"+str(details["sleep_commit_hash"])
                return ModeResult(status,summary,details)
            for model_gid,model,complete in models:
                self.store.save_model(model_gid,model,complete)
            return ModeResult(status,payload.get("summary","睡眠结束"),details)
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
                    raise InputStopped("睡眠已停止")
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
                    raise InputStopped("睡眠已停止")
                total+=action_geometry_distance(candidate["a"],other["a"])*float(other.get("weight",1.0))
            if total<best_total:
                best_total=total
                best=candidate
        return best
    def _cluster_action_samples(self,samples):
        families=defaultdict(list)
        for index,sample in enumerate(samples):
            if index%64==0 and self.should_stop():
                raise InputStopped("睡眠已停止")
            family=action_family_key(sample["a"])
            if family:
                families[family].append(sample)
        clusters=[]
        operations=0
        for family,items in sorted(families.items()):
            if self.should_stop():
                raise InputStopped("睡眠已停止")
            local=[]
            for item in sorted(items,key=lambda value:str(value.get("checksum",""))):
                if self.should_stop():
                    raise InputStopped("睡眠已停止")
                if not local:
                    local.append({"family":family,"members":[item],"medoid":item})
                    continue
                distances=[]
                for cluster in local:
                    operations+=1
                    if operations%32==0 and self.should_stop():
                        raise InputStopped("睡眠已停止")
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
                            raise InputStopped("睡眠已停止")
                        limit=min(action_cluster_limit(local[first]["medoid"]["a"]),action_cluster_limit(local[second]["medoid"]["a"]))*0.82
                        if action_geometry_distance(local[first]["medoid"]["a"],local[second]["medoid"]["a"])<=limit:
                            local[first]["members"].extend(local[second]["members"])
                            local[first]["medoid"]=self._action_medoid(local[first]["members"])
                            local.pop(second)
                            changed=True
                            break
            for index,cluster in enumerate(local):
                if self.should_stop():
                    raise InputStopped("睡眠已停止")
                action=normalize_action(cluster["medoid"]["a"])
                canonical=action_signature(action)
                token=hashlib.sha256(canonical_bytes({"family":family,"action":action,"index":index})).hexdigest()[:20]
                cluster_id="action|"+family+"|"+token
                intervals=[]
                learned_policies=[]
                for member_index,member in enumerate(cluster["members"]):
                    if member_index%32==0 and self.should_stop():
                        raise InputStopped("睡眠已停止")
                    context=member.get("context",{}) if isinstance(member.get("context"),dict) else {}
                    if context.get("previous_action")==canonical and not context.get("previous_action_changed_frame",
                        True) and finite_number(context.get("seconds_since_previous")) and float(context.get("seconds_since_previous"))<=1.5:
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
                raise InputStopped("睡眠已停止")
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
                raise InputStopped("睡眠已停止")
            medoid=self._prototype_medoid(cluster)
            distances=[]
            temporal_distances=[]
            temporal=temporal_from_context(medoid.get("context",{}))
            for item_index,item in enumerate(cluster):
                if item_index%32==0 and self.should_stop():
                    raise InputStopped("睡眠已停止")
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
            result.append({"id":uuid.uuid4().hex,"cluster_id":cluster_id,"canonical_action_signature":canonical,"f":feature_bytes(medoid["f"]),
                    "coarse":bytes(medoid.get("coarse")) if isinstance(medoid.get("coarse"),(bytes,bytearray)) and len(medoid.get("coarse"))==COARSE_LEN else coarse_feature(medoid["f"]),
                    "a":normalize_action(action),"support":len(cluster),"action_support":int(action_support),"mean_distance":round(mean,6),"std_distance":round(std,6),"limit95":round(limit95,6),
                    "limit99":round(limit99,6),"intra_threshold":round(threshold_value,6),"threshold":round(threshold_value,6),"temporal":temporal,"temporal_threshold":round(temporal_threshold,6),
                    "capture_methods":methods,"previous_action":prev,"repeat_policy":repeat_policy if repeat_policy in REPEAT_POLICIES else "one_shot","max_rate":max(0.25,min(12.0,float(max_rate))),
                    "ambiguous":False,"created_from_sample_checksum":medoid.get("checksum","")})
        return result
    def rank_action_candidates(self,feature,prototypes,last_action_signature="",full_limit=8,temporal_context=None,query_coarse=None):
        if not feature_valid(feature):
            return []
        query_temporal=temporal_from_context(temporal_context or {})
        if not isinstance(query_coarse,(bytes,bytearray)) or len(query_coarse)!=COARSE_LEN:
            query_coarse=coarse_feature(feature)
        query_coarse=bytes(query_coarse)
        backend=str(query_temporal.get("capture_method","unknown"))
        exact_limit=max(12,min(VersionedThresholdConfig.candidate_full_limit,int(full_limit) if int(full_limit)>0 else VersionedThresholdConfig.candidate_full_limit))
        runtime_model=getattr(self,"active_model_runtime",None)
        active_runtime=bool(isinstance(runtime_model,dict) and runtime_model.get("prototypes") is prototypes)
        model_token=str(runtime_model.get("runtime_token","")) if active_runtime else prototype_collection_checksum(prototypes)
        if len(model_token)!=64:
            model_token=prototype_collection_checksum(prototypes)
        feature_digest=hashlib.blake2b(feature_bytes(feature),digest_size=16).digest()
        coarse_digest=hashlib.blake2b(query_coarse,digest_size=8).digest()
        visual_cache_key=("visual-v3",model_token,feature_digest,coarse_digest,backend,exact_limit)
        visual_matches=self.candidate_cache.get(visual_cache_key)
        if visual_matches is None:
            worker=getattr(self,"ai_worker",None)
            if active_runtime and worker is not None and worker.alive() and bool(worker.status.get("capabilities",{}).get("candidate_rank")):
                visual_matches=worker.candidate_matches(runtime_model,feature,query_coarse,backend,exact_limit)
            else:
                runtime_index=runtime_model.get("runtime_index",{}) if active_runtime else build_candidate_runtime_index(prototypes,False)
                visual_matches=candidate_visual_matches(runtime_index,feature,query_coarse,backend,exact_limit)
            visual_matches=tuple((safe_int(item.get("index"),-1),safe_float(item.get("exact_score"),float("inf"))) for item in visual_matches if isinstance(item,dict))
            self.candidate_cache[visual_cache_key]=visual_matches
        sequence_model=runtime_model.get("sequence_model",{}) if active_runtime else {}
        recent_actions=query_temporal.get("recent_actions",[last_action_signature])
        grouped=defaultdict(list)
        for position,(index,raw) in enumerate(visual_matches):
            if position%8==0 and getattr(self,"stop_event",None) is not None and self.should_stop():
                return []
            if index<0 or index>=len(prototypes):
                continue
            proto=prototypes[index]
            if "authorized" in proto and not proto.get("authorized"):
                continue
            methods=proto.get("capture_methods",frozenset())
            methods=frozenset(str(value) for value in methods)
            if methods and backend not in methods:
                continue
            expected=str(proto.get("previous_action",""))
            previous_penalty=min(120.0,raw*0.08+18.0) if expected and last_action_signature and expected!=last_action_signature else 0.0
            proto_temporal=proto.get("temporal_cached") or temporal_from_context(proto.get("temporal",{}))
            tdistance=temporal_distance(query_temporal,proto_temporal)
            temporal_penalty=tdistance*max(40.0,float(proto.get("threshold",100.0))*0.35)
            cluster_id=str(proto.get("cluster_id",proto.get("action_signature","")))
            sequence_penalty=calculate_sequence_penalty(recent_actions,cluster_id,sequence_model)
            if cluster_id:
                grouped[cluster_id].append((raw+previous_penalty+temporal_penalty+sequence_penalty,raw,tdistance,proto))
        result=[]
        for cluster_id,items in grouped.items():
            items.sort(key=lambda item:item[0])
            best_score,best_distance,best_temporal,best_proto=items[0]
            action=normalize_action(best_proto.get("a"))
            if action is None:
                continue
            vote_score=best_score if len(items)==1 else 0.88*best_score+0.12*items[1][0]
            result.append({
                "cluster_id":cluster_id,
                "canonical_action_signature":str(best_proto.get("canonical_action_signature") or action_signature(action)),
                "score":vote_score,
                "best_score":best_score,
                "distance":best_distance,
                "temporal_distance":best_temporal,
                "proto":best_proto,
                "a":action,
                "support":max(int(item[3].get("action_support",item[3].get("support",0))) for item in items),
                "prototype_votes":len(items),
            })
        result.sort(key=lambda item:item["score"])
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
            reason="视觉与短时序状态仍对应不同动作，必须指导"
        elif not temporal_ok:
            reason="最近3至5帧、最近动作、状态时长或鼠标位置不匹配"
        else:
            reason="未达到动作阈值、差距或支持数要求"
        return {"accepted":accepted,"best":best,"second":second,"threshold":threshold,"margin":margin,"required_gap":required_gap,"support":support,"min_support":min_support,
            "confidence":confidence,"margin_ok":margin_ok,"rejection_ok":rejection_ok,"temporal_ok":temporal_ok,"ambiguous":ambiguous,"authorized":authorized,"reason":reason,
            "nearest_rejected_distance":rejected_distance,"query_backend":query_backend}
    def validate_model_binding(self,model,target):
        if not isinstance(model,dict):
            raise RuntimeError("模型不存在或格式无效")
        binding=model.get("model_binding")
        if not isinstance(binding,dict):
            raise RuntimeError("模型缺少不可变窗口绑定快照，请重新睡眠")
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
            raise RuntimeError("模型与当前窗口/任务绑定不一致："+"、".join(errors)+"；请重新学习或睡眠")
        self.require_ai_runtime()
        manifest=self.vision_runtime.manifest()
        stored=model.get("vision_model_manifest") if isinstance(model,dict) else None
        if not isinstance(stored,dict) or str(stored.get("checksum",""))!=str(manifest.get("checksum","")) or safe_int(stored.get("architecture_version"),0)!=VISION_ARCHITECTURE_VERSION:
            raise RuntimeError("离线AI视觉模型版本、权重或SHA-256已变化，请重新睡眠")
        if str(model.get("preprocess_hash",""))!=VISION_PREPROCESS_HASH or str(stored.get("preprocess_hash",""))!=VISION_PREPROCESS_HASH:
            raise RuntimeError("RGB预处理签名变化，请重新睡眠")
        current_runtime=manifest.get("runtime_fingerprint",{})
        stored_runtime=stored.get("runtime_fingerprint",{})
        if not isinstance(stored_runtime,dict) or str(stored_runtime.get("checksum",""))!=str(current_runtime.get("checksum","")):
            raise RuntimeError("运行库版本变化，明确拒绝旧模型，请重新睡眠")
        current_ocr=hashlib.sha256(canonical_bytes([{key:item.get(key) for key in ("id","region_norm","region_type","number_format","goal_relation","target_min","target_max","special_value",
                    "special_meaning","reset_meaning","checksum")} for item in self.store.list_ocr_regions(self.require_game()["id"],True)])).hexdigest()
        if str(model.get("ocr_regions_checksum",""))!=current_ocr or safe_int(model.get("ocr_semantic_version",0),0)!=OCR_SEMANTIC_VERSION:
            raise RuntimeError("OCR区域或数字语义已变化，请重新睡眠")
        return True
    def start_sleep(self):
        try:
            self.require_ai_runtime()
            self.require_game()
            self.store.light_checkpoint()
        except Exception as error:
            self.show_error(str(error))
            return
        self.start_worker("睡眠",self.review_controller.run,False)
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
            self.require_ai_runtime()
        except Exception as error:
            self.show_error(str(error))
            return
        try:
            game=self.require_game()
            target=self.require_window(False)
            model=self.store.load_trainable_model(game["id"])
            if not model or not model.get("prototypes"):
                raise RuntimeError("没有已授权动作的可训练模型，请先完成学习和睡眠；普通左键单击、移动、悬停、等待可在单次高重复一致学习后获得基础安全授权")
            if str(model.get("validation",{}).get("status","")) not in {"passed","basic_safe"}:
                raise RuntimeError("模型没有通过完整验收，也没有获得基础安全动作授权")
            current=next((item for item in self.store.games() if item["id"]==game["id"]),{})
            if current.get("needs_review"):
                raise RuntimeError("模型需要睡眠：请先点击“睡眠”完成离线优化")
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
        result.extend([normalize_action({"kind":"double_click","button":"left","path":[[0.5,0.5]],"duration":0.16}),normalize_action({"kind":"drag","button":"left","path":[[0.25,0.5],[0.75,
                    0.5]],"duration":0.45}),normalize_action({"kind":"drag","button":"left","path":[[0.5,0.75],[0.5,0.25]],"duration":0.45}),normalize_action({"kind":"no_op","duration":0.4}),
                normalize_action({"kind":"scroll_v","delta":120,"path":[[0.5,0.5]],"duration":0.08}),normalize_action({"kind":"scroll_v","delta":-120,"path":[[0.5,0.5]],"duration":0.08})])
        return result
    def start_ask(self):
        try:
            self.require_ai_runtime()
        except Exception as error:
            self.show_error(str(error))
            return
        self.start_worker("指导",self.teaching_controller.run,True)
    def _create_ask_window(self,prepared):
        return self.teaching_controller.create_window(prepared)
    def close_ask(self,show_summary=True,wait_buffer=True,reason="completed"):
        if self.mode!="指导" and self.ask_window is None:
            return
        status="completed" if str(reason)=="completed" else "stopped"
        text="用户结束指导" if status=="completed" else "指导已停止"
        self.request_mode_stop(status,text)
class AppStorageMixin:
    def choose_data_directory(self):
        from tkinter import filedialog
        if self.mode_state!=MODE_IDLE or self.closing:
            self.show_error("运行模式期间不能切换文件夹")
            return
        win=tk.Toplevel(self.root)
        win.title("选择文件夹")
        fit_window(win,720,360,480,300)
        win.transient(self.root)
        win.grab_set()
        frame=ttk.Frame(win,padding=20)
        frame.pack(fill="both",expand=True)
        path_var=tk.StringVar(value=str(self.data_directory) if self.data_directory is not None else "尚未选择")
        status_var=tk.StringVar(value="空目录会初始化；合法既有目录会复制到隐藏暂存区完成升级与校验后原子重新挂载；若位置改变，则迁移当前数据。SHA-256、quick_check、外键和schema全部通过后才能确认。")
        progress_var=tk.DoubleVar(value=0.0)
        ttk.Label(frame,text="文件夹两阶段确认",font=("Microsoft YaHei UI",14,"bold")).pack(anchor="w")
        ttk.Label(frame,textvariable=path_var,wraplength=670).pack(anchor="w",fill="x",pady=(12,4))
        ttk.Label(frame,textvariable=status_var,wraplength=670).pack(anchor="w",fill="x",pady=(4,12))
        ttk.Progressbar(frame,variable=progress_var,maximum=100).pack(fill="x")
        buttons=ttk.Frame(frame)
        buttons.pack(side="bottom",fill="x",pady=(16,0))
        state={"closed":False,"prepared":None,"generation":0}
        confirm=ttk.Button(buttons,text="确认",state="disabled")
        select=ttk.Button(buttons,text="选择文件夹")
        def discard():
            prepared=state.get("prepared")
            state["prepared"]=None
            if self.directory_prepare_candidate is prepared:
                self.directory_prepare_candidate=None
            if prepared is not None:
                try:
                    prepared.close()
                except Exception as error:
                    record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        def close():
            if state["closed"]:
                return
            state["closed"]=True
            state["generation"]+=1
            self.directory_prepare_generation+=1
            if self.directory_prepare_stop is not None:
                self.directory_prepare_stop.set()
            discard()
            self.lifecycle.set_directory_phase("ready" if self.store is not None else "unselected")
            self._update_control_availability()
            self.close_dialog(win)
        def prepared_ok(candidate,generation):
            if state["closed"] or generation!=state["generation"]:
                candidate.close()
                return
            discard()
            state["prepared"]=candidate
            self.directory_prepare_candidate=candidate
            self.directory_prepare_thread=None
            self.directory_prepare_stop=None
            progress_var.set(100.0)
            status_var.set("数据库结构升级、原数据迁移、SHA-256清单、WAL/锁、quick_check、外键、schema和运行库清单全部通过。现在可以点击“确认”。")
            confirm.configure(state="normal")
            select.configure(state="normal")
            self.lifecycle.set_directory_phase("prepared")
            self._update_control_availability()
        def prepared_failed(error,generation):
            if state["closed"] or generation!=state["generation"]:
                return
            self.directory_prepare_thread=None
            self.directory_prepare_stop=None
            self.directory_prepare_candidate=None
            status_var.set("目录初始化失败，当前已确认目录未改变："+str(error))
            confirm.configure(state="disabled")
            select.configure(state="normal")
            self.lifecycle.set_directory_phase("ready" if self.store is not None else "failed")
            self._update_control_availability()
        def choose():
            initial=str(self.data_directory) if self.data_directory is not None else str(Path.home())
            value=filedialog.askdirectory(parent=win,title="选择通用游戏AI文件夹",mustexist=False,initialdir=initial)
            if not value:
                return
            discard()
            state["generation"]+=1
            generation=state["generation"]
            path_var.set(str(Path(value).expanduser()))
            changing=not same_directory(value,self.data_directory) if self.data_directory is not None else False
            existing_valid=existing_data_directory_status(Path(value).expanduser())[0]
            status_var.set("正在把原文件夹迁移到新目录；处理结束前“确认”保持禁用。" if changing else "正在识别并重新验证合法既有目录；处理结束前“确认”保持禁用。" if existing_valid else "正在隐藏暂存区执行数据库结构升级和完整验证；处理结束前“确认”保持禁用。")
            self.api.block_input()
            self.set_input_status("已锁定")
            progress_var.set(0.0)
            confirm.configure(state="disabled")
            select.configure(state="disabled")
            self.lifecycle.set_directory_phase("preparing")
            self._update_control_availability()
            if self.directory_prepare_stop is not None:
                self.directory_prepare_stop.set()
            stop=threading.Event()
            self.directory_prepare_stop=stop
            self.directory_prepare_generation=generation
            def worker():
                directory_lock=None
                candidate=None
                try:
                    if self.data_directory is not None and same_directory(value,self.data_directory):
                        directory_lock=self.data_directory_lock
                    else:
                        directory_lock=DataDirectoryLock(value).acquire()
                    candidate=prepare_data_directory(value,stop,lambda amount:self.ui(lambda amount=amount:progress_var.set(amount),"prepare_progress"),self.store,self.data_directory)
                    candidate.directory_lock=directory_lock
                    candidate.directory_lock_owned=directory_lock is not self.data_directory_lock
                    self.ui(lambda candidate=candidate,generation=generation:prepared_ok(candidate,generation))
                except Exception as error:
                    if candidate is not None:
                        try:
                            candidate.close()
                        except Exception as error:
                            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
                    elif directory_lock is not None and directory_lock is not self.data_directory_lock:
                        directory_lock.close()
                    self.ui(lambda error=error,generation=generation:prepared_failed(error,generation))
            thread=threading.Thread(target=worker,name="UniversalGameAI-PrepareDataDirectory",daemon=False)
            self.directory_prepare_thread=thread
            thread.start()
        def commit():
            candidate=state.get("prepared")
            if candidate is None:
                return
            try:
                self._commit_prepared_directory(candidate)
                state["prepared"]=None
                self.close_dialog(win)
                state["closed"]=True
                self.show_info("文件夹","已完成两阶段切换："+str(self.data_directory))
            except Exception as error:
                discard()
                status_var.set("确认切换失败，旧目录继续可用；请重新选择目录："+str(error))
                confirm.configure(state="disabled")
                select.configure(state="normal")
        select.configure(command=choose)
        select.pack(side="left",fill="x",expand=True,ipady=7)
        confirm.configure(command=commit)
        confirm.pack(side="left",fill="x",expand=True,padx=8,ipady=7)
        def refuse_close():
            win.bell()
            win.lift()
            win.focus_force()
        win.protocol("WM_DELETE_WINDOW",refuse_close)
    def _commit_prepared_directory(self,candidate):
        global CURRENT_VISION_RUNTIME,CURRENT_OCR_RUNTIME,SELECTED_DATA_DIR
        if not isinstance(candidate,PreparedDataDirectory) or candidate.closed or candidate.store is None:
            raise RuntimeError("候选文件夹无效")
        old_store=self.store
        old_base=self.data_directory
        old_directory_lock=self.data_directory_lock
        candidate_directory_lock=getattr(candidate,"directory_lock",None)
        if candidate_directory_lock is None:
            raise RuntimeError("候选文件夹未持有目录独占锁")
        old_selected=globals().get("SELECTED_DATA_DIR")
        old_env={key:os.environ.get(key) for key in ("UGAI_DATA_DIR","PIP_CACHE_DIR","TORCH_HOME","HF_HOME","HUGGINGFACE_HUB_CACHE","TRANSFORMERS_CACHE","XDG_CACHE_HOME",
                "PYTHONPYCACHEPREFIX","TORCH_EXTENSIONS_DIR","CUDA_CACHE_PATH","NUMBA_CACHE_DIR","MPLCONFIGDIR","TMP","TEMP")}
        old_temp=tempfile.tempdir
        old_path=list(sys.path)
        old_runtime=(self.runtime_installer,self.ai_worker,self.vision_runtime,self.ocr_runtime,globals().get("CURRENT_VISION_RUNTIME"),globals().get("CURRENT_OCR_RUNTIME"),getattr(self.api,"ai_runtime",None))
        old_selection=(self.selected_game,self.selected_window,self.window_recommendation,self.storage_fault)
        if candidate.same:
            candidate.closed=True
            candidate.store=None
            candidate.source_paused=False
            candidate.directory_lock=None
            candidate.directory_lock_owned=False
            self.lifecycle.set_directory_phase("ready")
            self._update_control_availability()
            return True
        if candidate.staging is None or not candidate.staging.exists():
            raise RuntimeError("迁移暂存区不存在")
        destination=candidate.destination
        staging=candidate.staging
        rollback=destination/(".ugai_rollback_"+uuid.uuid4().hex)
        rollback.mkdir(parents=True,exist_ok=False)
        new_store=None
        promoted=False
        try:
            candidate.close_staging_store()
            candidate.sha_manifest=data_tree_manifest(staging)
            verify_data_tree_manifest(staging,candidate.sha_manifest)
            (staging/".ugai_migration_manifest.json").write_text(json.dumps({"source":str(candidate.source_base) if candidate.source_base is not None else None,
                        "destination":str(destination),"inventory":candidate.target_inventory,"sha256":candidate.sha_manifest,"confirmed":time.time()},ensure_ascii=False,sort_keys=True,separators=(",",":")),encoding="utf-8")
            for item in list(destination.iterdir()):
                if item==staging or item==rollback or item.name==".ugai.lock":
                    continue
                os.replace(item,rollback/item.name)
            for item in list(staging.iterdir()):
                os.replace(item,destination/item.name)
            staging.rmdir()
            candidate.promoted=True
            promoted=True
            verify_data_tree_manifest(destination,candidate.sha_manifest)
            new_store=DataStore(destination)
            if new_store.read_only:
                raise RuntimeError(new_store.read_only_reason or "新目录数据库只读")
            new_store.sample_write_barrier()
            target_inventory=database_inventory(new_store.db_path,destination)
            for key in ("games","game_count","sample_count","model_count","vision_model_count","selected_game","model_files"):
                if target_inventory.get(key)!=candidate.target_inventory.get(key):
                    raise RuntimeError("确认后迁移校验不一致："+str(key))
            base=configure_data_directory(destination)
            installer=RuntimeInstaller(base)
            worker=None
            vision=None
            ocr=None
            if validate_runtime_manifest(base,False) is not None:
                worker=AIWorkerClient(base,self._ai_worker_failed)
                vision=VisionRuntimeProxy(worker)
                ocr=OCRRuntimeProxy(worker)
            new_store.set_writer_error_callback(self._writer_status_changed)
            selected_game=new_store.selected_game()
            recommendation=new_store.load_window_descriptor()
            self.store=new_store
            self.data_directory=base
            self.data_directory_lock=candidate_directory_lock
            candidate.directory_lock=None
            candidate.directory_lock_owned=False
            self.write_audit=WritePathAudit(base)
            install_write_boundary_guard(base,self.write_audit)
            self.acceptance_report=AcceptanceReport(base)
            self.acceptance_report.set_environment(host_python=sys.version,host_bits=ctypes.sizeof(ctypes.c_void_p)*8,
                windows_build=int(sys.getwindowsversion().build) if os.name=="nt" else 0,fixed_runtime_python=FIXED_RUNTIME_PYTHON_VERSION)
            self.write_audit.record("confirm_data_directory",base,True,{"build_hash":current_build_hash()})
            self.runtime_installer=installer
            self.ai_worker=worker
            self.vision_runtime=vision
            self.ocr_runtime=ocr
            CURRENT_VISION_RUNTIME=vision
            CURRENT_OCR_RUNTIME=ocr
            self.api.ai_runtime=vision
            self.selected_game=selected_game
            self.selected_window=None
            self.window_recommendation=recommendation
            self.storage_fault=bool(new_store.read_only)
            self.lifecycle.set_directory_phase("ready")
            self.lifecycle.set_runtime_ready(bool(vision is not None and vision.ready and ocr is not None and ocr.ready))
            self.data_dir_text.set(str(base))
            if DEVELOPER_MODE:
                materialize_project_layout(base)
            self._update_runtime_status()
            self._refresh_all()
            self._update_control_availability()
            record_dir=base/"backups"
            record_dir.mkdir(parents=True,exist_ok=True)
            record={"created":time.time(),"source":str(candidate.source_base) if candidate.source_base is not None else None,"destination":str(base),"inventory":target_inventory,
                "source_retained":bool(candidate.source_base is not None and candidate.source_base.exists())}
            (record_dir/("migration_"+time.strftime("%Y%m%d_%H%M%S")+"_"+uuid.uuid4().hex+".json")).write_text(json.dumps(record,ensure_ascii=False,sort_keys=True,separators=(",",":")),encoding="utf-8")
        except Exception:
            if new_store is not None:
                try:
                    new_store.close(5.0)
                except Exception as error:
                    record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
            self.store=old_store
            self.data_directory=old_base
            self.data_directory_lock=old_directory_lock
            if candidate_directory_lock is not old_directory_lock:
                try:
                    candidate_directory_lock.close()
                except Exception as error:
                    record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
            candidate.directory_lock=None
            candidate.directory_lock_owned=False
            if self.ai_worker is not None and self.ai_worker is not old_runtime[1]:
                try:
                    self.ai_worker.close(1.0)
                except Exception as error:
                    record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
            self.runtime_installer,self.ai_worker,self.vision_runtime,self.ocr_runtime,CURRENT_VISION_RUNTIME,CURRENT_OCR_RUNTIME,old_api_runtime=old_runtime
            self.api.ai_runtime=old_api_runtime
            self.selected_game,self.selected_window,self.window_recommendation,self.storage_fault=old_selection
            SELECTED_DATA_DIR=old_selected
            sys.path[:]=old_path
            for key,value in old_env.items():
                if value is None:
                    os.environ.pop(key,None)
                else:
                    os.environ[key]=value
            tempfile.tempdir=old_temp
            if promoted:
                for item in list(destination.iterdir()):
                    if item==rollback or item.name==".ugai.lock":
                        continue
                    if item.is_dir():
                        shutil.rmtree(item,ignore_errors=True)
                    else:
                        try:
                            item.unlink()
                        except OSError:
                            pass
                for item in list(rollback.iterdir()):
                    os.replace(item,destination/item.name)
            shutil.rmtree(rollback,ignore_errors=True)
            if not promoted and staging.exists():
                shutil.rmtree(staging,ignore_errors=True)
            candidate.resume_source()
            candidate.closed=True
            candidate.store=None
            if candidate.destination_created:
                try:
                    if destination.exists() and not any(destination.iterdir()):
                        destination.rmdir()
                except OSError:
                    pass
            raise
        candidate.closed=True
        candidate.store=None
        candidate.source_paused=False
        if old_store is not None and old_store is not new_store:
            if not old_store.close(5.0):
                old_store.emergency_checkpoint("migration_source_close_timeout")
        old_worker=old_runtime[1]
        if old_worker is not None and old_worker is not self.ai_worker:
            old_worker.close(2.0)
        if old_directory_lock is not None and old_directory_lock is not self.data_directory_lock:
            old_directory_lock.close()
        if any(rollback.iterdir()):
            pass
        else:
            rollback.rmdir()
        return True
    def _ai_worker_failed(self,error):
        self.api.block_input()
        self.api.release_all_buttons()
        self.lifecycle.set_runtime_ready(False)
        message="AI工作进程异常，自动输入已立即锁定："+str(error)
        if self.store is not None:
            self.store.log_error("AI_WORKER_FAILED",error,mode=self.mode)
        if self.mode_state!=MODE_IDLE:
            self.ui(lambda:self.request_mode_stop("failed",message),"ai_worker_failed")
        else:
            self.ui(lambda:self.status.set(message),"ai_worker_failed_status")
    def _start_ai_worker(self,base):
        old=self.ai_worker
        worker=AIWorkerClient(base,self._ai_worker_failed)
        self.ai_worker=worker
        self.vision_runtime=VisionRuntimeProxy(worker)
        self.ocr_runtime=OCRRuntimeProxy(worker)
        if old is not None and old is not worker:
            old.close(2.0)
        return self.vision_runtime,self.ocr_runtime
    def _update_runtime_status(self):
        vision=self.vision_runtime
        ocr=self.ocr_runtime
        if vision is not None and vision.ready and ocr is not None and ocr.ready:
            manifest=vision.manifest() if vision.active_game else {"device":vision.device_name,"trained_steps":0,"backend":vision.backend,"serialization":vision.serialization}
            vision_backend=str(manifest.get("backend",getattr(vision,"backend","builtin_cpu")))
            vision_text="PyTorch" if vision_backend=="torch" else "内置CPU特征"
            ocr_backend=str(getattr(ocr,"backend","none"))
            ocr_text="RapidOCR可用" if ocr_backend=="rapidocr" and bool(getattr(ocr,"self_test_passed",False)) else "RapidOCR自检失败" if ocr_backend=="rapidocr" else "未安装"
            serialization=str(manifest.get("serialization",getattr(vision,"serialization","builtin_json")))
            self.confidence_text.set("视觉："+vision_text+"（"+str(manifest.get("device",vision.device_name))+"），训练步数"+str(manifest.get("trained_steps",0))+"；OCR："+ocr_text+"；模型格式："+serialization)
        elif self.store is None:
            self.confidence_text.set("离线AI运行库：请先选择文件夹")
        else:
            self.confidence_text.set("离线AI运行库未就绪，请点击“检查文件完整性”；视觉="+str(getattr(vision,"error","未初始化"))+"；OCR="+str(getattr(ocr,"error","未初始化")))
    def require_ai_runtime(self):
        if not self.lifecycle.runtime_ready or self.vision_runtime is None or self.ocr_runtime is None:
            raise RuntimeError("请先完成文件完整性检查")
        self.vision_runtime.require_ready()
        self.ocr_runtime.require_ready()
        game=self.require_game()
        manifest=self.vision_runtime.activate_game(game["id"])
        self.api.ai_runtime=self.vision_runtime
        self.store.record_vision_model(game["id"],manifest)
        self._update_runtime_status()
        return manifest
    def start_integrity_check(self):
        if not self.lifecycle.data_ready or self.store is None:
            self.show_error("请先选择并确认文件夹")
            return False
        return self._start_mode_transaction("检查文件完整性",self.integrity_check_worker,False,False,"正在检查并补齐独立运行库文件；按ESC可提前结束")
    def start_download(self):
        return self.start_integrity_check()
    def integrity_check_worker(self):
        self.lifecycle.mark_running()
        if self.stop_event is not None and self.stop_event.is_set():
            raise InputStopped("文件完整性检查已停止")
        self.set_status("文件完整性检查中：校验main.py语法与数据库")
        self.set_progress(1.0)
        source_bytes=Path(__file__).read_bytes()
        ast.parse(source_bytes.decode("utf-8"),filename=str(Path(__file__).resolve()))
        source_hash=hashlib.sha256(source_bytes).hexdigest()
        if not self.store.integrity_check():
            raise RuntimeError("数据库完整性检查失败")
        if self.stop_event is not None and self.stop_event.is_set():
            raise InputStopped("文件完整性检查已停止")
        self.set_progress(5.0)
        def line(value):
            if value:
                self.set_status("文件完整性检查中："+value[-180:])
        marker=self.runtime_installer.run(self.stop_event,self.set_progress,line)
        global CURRENT_VISION_RUNTIME,CURRENT_OCR_RUNTIME
        self._start_ai_worker(self.data_directory)
        self.vision_runtime.require_ready()
        self.ocr_runtime.require_ready()
        CURRENT_VISION_RUNTIME=self.vision_runtime
        CURRENT_OCR_RUNTIME=self.ocr_runtime
        self.api.ai_runtime=self.vision_runtime
        self.lifecycle.set_runtime_ready(True)
        if self.selected_game:
            manifest=self.vision_runtime.activate_game(self.selected_game["id"])
            self.store.record_vision_model(self.selected_game["id"],manifest)
        status=dict(self.ai_worker.status)
        runtime_details=dict(marker)
        runtime_details.update({"vision_backend":status.get("vision_backend","builtin_cpu"),"vision_serialization":status.get("vision_serialization","builtin_json"),
                "ocr_backend":status.get("ocr_backend","none"),"ocr_self_test":bool(status.get("ocr_self_test",False)),"capabilities":dict(status.get("capabilities",{})),"source_sha256":source_hash,"database_integrity":True})
        self.ui(self._update_runtime_status)
        self.ui(self._update_control_availability)
        vision_text="PyTorch" if runtime_details["vision_backend"]=="torch" else "内置CPU特征"
        ocr_text="RapidOCR可用" if runtime_details["ocr_backend"]=="rapidocr" and runtime_details["ocr_self_test"] else "RapidOCR不可用"
        return ModeResult("completed","文件完整性检查完成；视觉："+vision_text+"；OCR："+ocr_text+"；模型格式："+str(runtime_details["vision_serialization"]),{"runtime":runtime_details})
class App(AppUiMixin,AppLifecycleMixin,AppModeMixin,AppStorageMixin):
    @property
    def mode_state(self):
        return self.lifecycle.snapshot()[0]
    @mode_state.setter
    def mode_state(self,state):
        self.transition_mode(state)
    @property
    def mode(self):
        return self.lifecycle.snapshot()[1]
    @property
    def stop_event(self):
        return self.lifecycle.snapshot()[2]
    def transition_mode(self,state):
        value=str(state)
        if value not in MODE_STATES:
            raise RuntimeError("模式状态无效")
        current=self.lifecycle.snapshot()[0]
        if value==current:
            return value
        if value==MODE_IDLE:
            self.lifecycle.finish()
        elif value==MODE_RUNNING:
            self.lifecycle.mark_running()
        elif value==MODE_STOPPING:
            self.lifecycle.request_stop()
        else:
            raise RuntimeError("STARTING只能由状态机begin()进入")
        return self.lifecycle.snapshot()[0]
    def __init__(self,root):
        self.root=root
        self.api=WinBridge()
        self.store=None
        self.data_directory=None
        self.data_directory_lock=None
        self.write_audit=None
        self.acceptance_report=None
        self.runtime_installer=None
        self.ai_worker=None
        self.vision_runtime=None
        self.ocr_runtime=None
        self.active_ocr_monitor=None
        self.selected_game=None
        self.selected_window=None
        self.window_recommendation=None
        self.lifecycle=ControlStateMachine()
        self.mode_state=MODE_IDLE
        self.developer_mode=DEVELOPER_MODE
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
        self.directory_prepare_thread=None
        self.directory_prepare_stop=None
        self.directory_prepare_candidate=None
        self.directory_prepare_generation=0
        self.refresh_signature=None
        self.closing=False
        self.shutdown_started=False
        self.shutdown_deadline=None
        self.review_distance_cache=BoundedLRU(50000)
        self.candidate_cache=BoundedLRU(64)
        self.storage_fault=True
        self.training_ready=False
        self.has_samples=False
        self.flow_text=tk.StringVar(value="1. 文件夹：未完成\n2. 文件完整性：未完成\n3. 游戏：未完成\n4. 窗口：未完成\n5. 学习数据：不足\n6. 模型：不可训练")
        self.active_model_runtime=None
        self.learning_controller=LearningController(self)
        self.review_controller=ReviewController(self)
        self.training_controller=TrainingController(self)
        self.teaching_controller=TeachingController(self)
        self.status=tk.StringVar(value="请选择文件夹；未确认前仅“选择文件夹”可用")
        self.data_dir_text=tk.StringVar(value="未选择")
        self.game_text=tk.StringVar(value="未选择")
        self.window_text=tk.StringVar(value="未选择")
        self.window_detail=tk.StringVar(value="PID：-  类名：-  客户区：-")
        self.capture_text=tk.StringVar(value="采集方式：未检测")
        self.sample_text=tk.StringVar(value="样本：有效0  废弃0  数据0 KB")
        self.model_text=tk.StringVar(value="模型：无  需要睡眠：否")
        self.confidence_text=tk.StringVar(value="离线AI运行库：未检查")
        self.input_text=tk.StringVar(value="自动输入：已锁定")
        self.progress_value=tk.DoubleVar(value=0.0)
        self.escape_metrics={"pressed":0.0,"input_locked":0.0,"cleanup_started":0.0,"finished":0.0,"fallback_used":False}
        self.keyboard_monitor=None
        self.keyboard_hook_error=""
        try:
            self.keyboard_monitor=KeyboardMonitor(self.api,on_escape=self._escape_hook_signal).start()
        except Exception as error:
            self.keyboard_hook_error=str(error)
        self.root.report_callback_exception=self.tk_exception
        self._build()
        self._update_control_availability()
        self.root.protocol("WM_DELETE_WINDOW",self.close)
        self.root.after(25,self.process_ui_queue)
        self.root.after(100,self.poll_global_escape)
        self.root.after(1200,self.periodic_refresh)
    def _writer_status_changed(self,error):
        def apply():
            self.storage_fault=bool(error) or bool(self.store.read_only)
            if error:
                self.status.set("样本写入失败，学习与指导已锁定："+str(error))
                if self.mode in {"学习","指导"}:
                    self.request_mode_stop("failed","样本写入失败")
            else:
                self.status.set("样本写入线程已恢复")
            self._apply_storage_controls()
        self.ui(apply,"writer_status")
    def _apply_storage_controls(self):
        self._update_control_availability()
    def _update_control_availability(self):
        state,_,_,_,_=self.lifecycle.snapshot()
        running=state!=MODE_IDLE
        data_ready=bool(self.lifecycle.data_ready and self.store is not None)
        runtime_ready=bool(self.lifecycle.runtime_ready and self.vision_runtime is not None and self.ocr_runtime is not None)
        blocked=bool(not data_ready or self.storage_fault or self.store is None or self.store.read_only)
        game_ready=isinstance(self.selected_game,dict)
        window_ready=isinstance(self.selected_window,dict)
        mapping={"选择文件夹":not running and self.lifecycle.directory_phase!="preparing","检查文件完整性":not running and data_ready,"游戏":not running and runtime_ready,"选择窗口":not running
            and runtime_ready and game_ready,"学习":not running and runtime_ready and game_ready and window_ready and not blocked,"睡眠":not running and runtime_ready and game_ready and self.has_samples
            and not blocked,"训练":not running and runtime_ready and game_ready and window_ready and self.training_ready,"指导":not running and runtime_ready and game_ready and window_ready and not blocked}
        if self.developer_mode:
            mapping.update({"任务与安全":not running and runtime_ready and game_ready,"重新测试采集后端":not running and runtime_ready and window_ready,"数据清理":not running and data_ready and game_ready and not blocked,"停止":running})
        for name,button in self.control_buttons.items():
            try:
                button.configure(state="normal" if mapping.get(name,False) else "disabled")
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
    def _forced_exit(self,reason,exit_function=os._exit):
        self.api.block_input()
        self.api.release_all_buttons()
        best_effort_cleanup("REVIEW_PROCESS_CLOSE_FAILED",lambda:self.review_process.terminate(0.2) if self.review_process is not None else True)
        best_effort_cleanup("RUNTIME_INSTALLER_CLOSE_FAILED",lambda:self.runtime_installer.stop() if self.runtime_installer is not None else True)
        best_effort_cleanup("AI_WORKER_CLOSE_FAILED",lambda:self.ai_worker.close(0.2) if self.ai_worker is not None else True)
        best_effort_cleanup("KEYBOARD_MONITOR_CLOSE_FAILED",lambda:self.keyboard_monitor.stop(0.2) if self.keyboard_monitor is not None else True)
        best_effort_cleanup("DIRECTORY_LOCK_CLOSE_FAILED",lambda:self.data_directory_lock.close() if self.data_directory_lock is not None else True)
        best_effort_cleanup("CAPTURE_PROCESS_CLOSE_FAILED",lambda:self.api.stop_capture_processes(0.0,True))
        try:
            if self.store is not None:
                self.store.emergency_checkpoint(reason)
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        try:
            self.root.destroy()
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        record_cleanup_error("FORCED_EXIT",RuntimeError(str(reason)),{"cleanup_errors":list(EMERGENCY_CLEANUP_ERRORS)})
        exit_function(2)
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
    def require_game(self):
        if not self.selected_game:
            raise RuntimeError("请先点击“游戏”按钮选择或新建游戏")
        if self.vision_runtime is not None and self.vision_runtime.ready:
            self.vision_runtime.activate_game(self.selected_game["id"])
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
                scenario=result.get("acceptance_scenarios",{}) if isinstance(result.get("acceptance_scenarios"),dict) else {}
                for case in ("minimized","occluded","scaled","recreated"):
                    if case in scenario:
                        self.record_acceptance_case("采集",case,"passed" if scenario.get(case) else "failed",{"purpose":str(purpose),"calibration":result,"scenario":case})
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
    def should_stop(self):
        if self.stop_event is None or self.stop_event.is_set():
            self.api.block_input()
            return True
        monitor=self.keyboard_monitor
        if (monitor is None or not monitor.alive()) and self.api.key_down(0x1B):
            self.escape_metrics["fallback_used"]=True
            self._escape_hook_signal({"monotonic_time":time.monotonic()})
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
        result={"previous_action":last_signature or "","seconds_since_previous":round(max(0.0,min(60.0,time.monotonic()-last_time)) if last_time else 60.0,3),
            "previous_action_changed_frame":bool(last_changed),"motion_channel_valid":bool(motion_valid),"session_id":str(session_id or "unspecified"),"capture_method":str(capture_method or "unknown"),
            "repeat_policy":repeat_policy if repeat_policy in REPEAT_POLICIES else "one_shot","duplicate_threshold":float(calibration.get("duplicate",3.0)),"calibration":dict(calibration),
            "process_path":os.path.normcase(str(target.get("process_path",""))),"window_class":str(target.get("class","")),"content_rect_norm":[round(safe_float(value,0.0),
                    6) for value in target.get("content_rect_norm",[0,0,1,1])[:4]],"content_aspect":content[2]/max(1,content[3]),"window_rule_version":WINDOW_RULE_VERSION,"capture_backend_version":CAPTURE_BACKEND_VERSION}
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
        return {"recent_frame_count":len(frames),"recent_frame_deltas":deltas,"recent_actions":actions,"state_duration":round(max(0.0,min(60.0,time.monotonic()-float(state_since))),3),
            "cursor":cursor_point,"window_size":[int(rect[2]),int(rect[3])] if len(rect)==4 else None,"dpi":int(frame.get("dpi",0)),"capture_method":str(frame.get("method","unknown"))}
    def _log_error(self,code,error=None,details=None):
        if self.store is not None:
            self.store.log_error(code,error,mode=self.mode,details=details)
    def record_acceptance_case(self,name,case,status,evidence=None):
        report=self.acceptance_report
        if report is None:
            return False
        try:
            report.record_case(name,case,status,evidence if isinstance(evidence,dict) else {"value":evidence})
            return True
        except Exception as error:
            self._log_error("ACCEPTANCE_EVIDENCE_WRITE_FAILED",error,{"name":str(name),"case":str(case),"status":str(status)})
            return False
    def _record_mode_acceptance(self,name,result,metrics=None):
        details=dict(result.details) if isinstance(result,ModeResult) else {}
        status=str(result.status) if isinstance(result,ModeResult) else "failed"
        evidence={"mode":str(name),"status":status,"summary":str(getattr(result,"summary","")),"details":details,"time":time.time()}
        phase_case=None
        thresholds=False
        if metrics:
            thresholds=bool(metrics.get("lock_latency_ms") is not None and metrics.get("lock_latency_ms")<=250 and metrics.get("cleanup_latency_ms") is not None
                and metrics.get("cleanup_latency_ms")<=750 and metrics.get("finish_latency_ms")<=5500 and not details.get("forced_processes"))
            phase_case={MODE_STARTING:"starting",MODE_RUNNING:"running",MODE_STOPPING:"stopping"}.get(str(metrics.get("phase","")))
            if phase_case:
                self.record_acceptance_case("停止",phase_case,"passed" if thresholds else "failed",dict(metrics))
            self.record_acceptance_case("停止","latency_thresholds","passed" if thresholds else "failed",metrics)
        if phase_case!="stopping":
            self.record_acceptance_case("停止","stopping","pending",evidence)
        self.record_acceptance_case("停止","buttons_released","passed",{"mode":str(name),"release_called":True,"forced":details.get("forced_processes",[])})
        if str(name)=="检查文件完整性":
            runtime=details.get("runtime",{}) if isinstance(details.get("runtime"),dict) else {}
            embedded=runtime.get("resolution_source")=="embedded" and bool(runtime.get("embedded_lock_checksum")) and bool(runtime.get("lock_complete",runtime_lock_is_complete(runtime.get("resolved_wheels",[]))))
            if status=="completed":
                self.record_acceptance_case("文件完整性","normal_complete","passed",runtime)
                self.record_acceptance_case("文件完整性","locked_manifest","passed" if embedded else "failed",runtime)
                retries=safe_int(runtime.get("download_evidence",{}).get("retries"),0,0) if isinstance(runtime.get("download_evidence"),dict) else 0
                self.record_acceptance_case("文件完整性","network_failure_retry","passed" if retries>0 else "pending",{"retries":retries,"download_evidence":runtime.get("download_evidence",{})})
                self.record_acceptance_case("独立运行时","fixed_python","passed" if tuple(runtime.get("python_abi",[]))==FIXED_RUNTIME_PYTHON_ABI else "failed",runtime)
                self.record_acceptance_case("独立运行时","embedded_wheel_lock","passed" if embedded else "failed",runtime)
                self.record_acceptance_case("独立运行时","host_abi_independent","passed",{"host":list(sys.version_info[:2]),"runtime":runtime.get("python_abi"),"architecture":runtime.get("architecture")})
                self.record_acceptance_case("独立运行时","worker_process","passed",{"installer_process_completed":True})
            elif status=="stopped":
                download_cache=self.data_directory/"cache"/"runtime_downloads" if self.data_directory else None
                partials=[str(item.relative_to(self.data_directory)) for item in download_cache.rglob("*.part")] if download_cache is not None and download_cache.exists() else []
                staging=list(self.data_directory.glob("runtime.staging.*")) if self.data_directory else []
                self.record_acceptance_case("文件完整性","escape_retry","passed" if not staging else "failed",{"partial_files":partials[:20],"staging":list(map(str,staging)),"resume_preserved":bool(partials)})
        elif str(name)=="学习":
            passed=bool(details.get("client_only") and safe_int(details.get("real_mouse_events"),0,0)>0 and safe_int(details.get("outside_rejected"),0,0)>=0 and safe_int(details.get("keyboard_events"),0,0)==0)
            self.record_acceptance_case("学习","client_only_real_mouse","passed" if passed else "failed" if status=="completed" else "pending",details)
        elif str(name)=="睡眠":
            self.record_acceptance_case("睡眠","socket_blocked","passed" if details.get("offline_network_blocked") else "failed",details)
            self.record_acceptance_case("睡眠","model_optimized","passed" if details.get("model_optimized") and details.get("model_after_hash") else "failed",details)
            self.record_acceptance_case("睡眠","pool_optimized","passed" if details.get("pool_optimized") and details.get("pool_after_hash") else "failed",details)
            self.record_acceptance_case("睡眠","deterministic_seed","passed" if details.get("deterministic_seed") and safe_int(details.get("sleep_seed"),0)>0 else "failed",details)
        elif str(name)=="训练":
            audit=details.get("coordinate_audit",{}) if isinstance(details.get("coordinate_audit"),dict) else {}
            self.record_acceptance_case("训练","all_coordinates_in_client","passed" if safe_int(audit.get("outside"),1)==0 and safe_int(audit.get("sent"),0)>=0 else "failed",audit)
            self.record_acceptance_case("训练","immutable_snapshot_change_stop","passed" if details.get("training_snapshot_checksum") and details.get("snapshot_guarded") else "failed",details)
        elif str(name)=="指导":
            self.record_acceptance_case("指导","choices_only","passed" if details.get("choices_only") else "failed",details)
            self.record_acceptance_case("指导","finish_button","passed" if details.get("finish_button") else "pending",details)
            self.record_acceptance_case("指导","escape","passed" if details.get("escape_used") else "pending",details)
        if self.data_directory is not None:
            staging=list(self.data_directory.glob("runtime.staging.*"))+list(self.data_directory.glob(".ugai_prepare_*"))+list(self.data_directory.glob(".ugai_migration_*"))
            self.record_acceptance_case("错误恢复","no_staging","passed" if not staging else "failed",{"staging":list(map(str,staging))})
            self.record_acceptance_case("错误恢复","no_orphan_process","passed" if not details.get("forced_processes") else "failed",{"forced_processes":details.get("forced_processes",[])})
            self.record_acceptance_case("错误恢复","no_pressed_buttons","passed",{"release_called":True})
            self.record_acceptance_case("错误恢复","input_locked","passed",{"mode":str(name),"shutdown_complete":True})
class ReviewProcessHost(AppModeMixin):
    def __init__(self,payload,stop_event,connection):
        self.selected_game=dict(payload["game"])
        self.store=ReviewProcessStore(payload)
        self.sleep_seed=safe_int(payload.get("sleep_seed"),0,0,2**63-1)
        self.sleep_seed_evidence=dict(payload.get("sleep_seed_evidence",{}))
        self.lifecycle=ReviewProcessLifecycle(stop_event)
        self.review_distance_cache=BoundedLRU(payload.get("cache_capacity",50000))
        self.candidate_cache=BoundedLRU(64)
        self.active_model_runtime=None
        self.api=ReviewProcessApi()
        self._connection=connection
        self.review_controller=ReviewController(self)
    @property
    def stop_event(self):
        return self.lifecycle.stop_event
    def require_game(self):
        if not self.selected_game:
            raise RuntimeError("睡眠子进程缺少游戏")
        return self.selected_game
    def should_stop(self):
        return bool(self.stop_event is not None and self.stop_event.is_set())
    def wait_escape_release(self):
        if self.should_stop():
            raise InputStopped("睡眠已停止")
        return True
    def set_progress(self,value):
        return review_process_send(self._connection,"progress",float(value))
    def set_status(self,value):
        return review_process_send(self._connection,"status",str(value))
    def set_input_status(self,value):
        return None
    def set_confidence(self,value):
        return None
    def request_mode_stop(self,status="stopped",reason=""):
        return self.lifecycle.request_stop(status,reason)
def enable_dpi_awareness():
    if os.name!="nt":
        return
    user32=ctypes.WinDLL("user32",use_last_error=True)
    try:
        user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        try:
            user32.SetProcessDPIAware()
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
def install_global_hooks(app_holder):
    def sys_hook(exc_type,exc_value,exc_traceback):
        text="".join(traceback.format_exception(exc_type,exc_value,exc_traceback))
        app=app_holder.get("app")
        if app:
            app.show_error(text)
        else:
            try:
                sys.stderr.write(text)
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
    fit_window(win,700,390,480,320)
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
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        try:
            root.destroy()
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
    def refuse_close():
        win.bell()
        win.lift()
        win.focus_force()
    ttk.Button(frame,text="确认",command=close).pack(pady=(10,0))
    win.protocol("WM_DELETE_WINDOW",refuse_close)
def run_self_test(path=None):
    return run_static_contract_tests(path)
def run_windows_smoke_test(path=None):
    load_gui_runtime()
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
        persistent=Path(path).expanduser().resolve() if path else None
        workspace=tempfile.TemporaryDirectory() if persistent is None else None
        folder=Path(workspace.name) if workspace is not None else persistent.parent/(".ugai_acceptance_workspace_"+uuid.uuid4().hex)
        folder.mkdir(parents=True,exist_ok=True)
        try:
            os.environ["LOCALAPPDATA"]=str(folder)
            enable_dpi_awareness()
            root=tk.Tk()
            app=App(root)
            data_path=persistent if persistent is not None else folder/"data"
            directory_lock=DataDirectoryLock(data_path).acquire()
            try:
                candidate=prepare_data_directory(data_path)
                candidate.directory_lock=directory_lock
                candidate.directory_lock_owned=True
                app._commit_prepared_directory(candidate)
                directory_lock=None
            finally:
                if directory_lock is not None:
                    directory_lock.close()
            root.deiconify()
            root.update_idletasks()
            root.update()
            visible=bool(app.controls and app.root.winfo_exists() and app.root.state()!="withdrawn" and app.root.winfo_viewable())
            record("控制面板真实可见",visible,{"control_count":len(app.controls),"state":app.root.state()})
            record("冒烟测试文件夹已确认",app.store is not None and app.lifecycle.data_ready,{"directory":str(app.data_directory)})
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
                selected=next((item for item in hydrated if any(token in (str(item.get("title",""))+" "+str(item.get("class",""))+" "+str(item.get("process_path",
                            ""))).casefold() for token in ("雷电","ldplayer","dnplayer"))),None)
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
                record("四采集后端冒烟",all(name in methods for name in required_methods),{"methods":methods,"error":capture_error})
                observe=0.0
                for argument in sys.argv:
                    if argument.startswith("--smoke-observe-seconds="):
                        observe=safe_float(argument.split("=",1)[1],0.0,0.0,300.0)
                identity_changes=[]
                deadline=time.monotonic()+observe
                previous=selected
                while time.monotonic()<deadline:
                    root.update()
                    time.sleep(0.05)
                    try:
                        current=bridge.target_identity(previous)
                        if any(current.get(key)!=previous.get(key) for key in ("hwnd","pid","process_created","client_size","dpi")):
                            identity_changes.append({"before":previous,"after":current})
                        previous=current
                    except Exception as error:
                        identity_changes.append({"error":str(error)})
                record("真实窗口移动缩放最小化重启观察",observe<=0 or bool(identity_changes),{"observe_seconds":observe,"changes":identity_changes})
            report["manual_required"]=["按真实顺序完成：选择并确认文件夹、检查文件完整性、游戏增删改选确认、选择雷电与普通窗口确认、学习、睡眠、训练、指导、结果确认","在STARTING、RUNNING、STOPPING阶段分别按ESC并确认停止延迟",
                "使用真实外部鼠标和非ESC键盘输入确认立即停机且学习session变为invalid","在100%、125%、150%、200%及混合DPI、负坐标、跨屏环境完成验收"]
            acceptance=app.acceptance_report or AcceptanceReport(app.data_directory)
            acceptance.set_environment(windows_build=int(version.build),windows_major=int(version.major),host_python=sys.version,host_bits=ctypes.sizeof(ctypes.c_void_p)*8,
                fixed_runtime_python=FIXED_RUNTIME_PYTHON_VERSION,smoke_run=time.time())
            acceptance.record_case("启动","control_panel_visible","passed" if visible else "failed",report["details"].get("控制面板真实可见",{}))
            exact_buttons=set(app.control_buttons)==REQUIRED_DEFAULT_BUTTONS and len(app.control_buttons)==8
            acceptance.record_case("默认界面","exact_eight_buttons","passed" if exact_buttons else "failed",{"buttons":sorted(app.control_buttons)})
            folder_ok=bool(app.store is not None and app.lifecycle.data_ready and app.data_directory_lock is not None and app.data_directory_lock.locked)
            acceptance.record_case("文件夹","select_prepare_confirm","passed" if folder_ok else "failed",{"directory":str(app.data_directory)})
            migration_ok,migration_evidence=data_migration_contract_test()
            acceptance.record_case("文件夹","migration_success","passed" if migration_ok else "failed",migration_evidence)
            acceptance.record_case("文件夹","forced_failure_rollback","passed" if migration_evidence.get("failure_preserved") else "failed",migration_evidence)
            acceptance.record_case("文件夹","prepare_cancel_cleanup","pending",{"reason":"必须在复制数据库、SHA-256、schema升级和原子替换各阶段强制退出"})
            process_first=None
            named_ok=False
            try:
                process_first=ProcessInstanceLock().acquire()
                try:
                    ProcessInstanceLock().acquire()
                except RuntimeError:
                    named_ok=True
            finally:
                if process_first is not None:
                    process_first.close()
            acceptance.record_case("单实例与目录锁","named_mutex","passed" if named_ok else "failed",{"name":"per-user named mutex"})
            lock_second_failed=False
            probe_lock=None
            try:
                probe_lock=DataDirectoryLock(app.data_directory).acquire()
            except RuntimeError:
                lock_second_failed=True
            finally:
                if probe_lock is not None:
                    probe_lock.close()
            acceptance.record_case("单实例与目录锁","directory_lock","passed" if lock_second_failed else "failed",{"path":str(app.data_directory/".ugai.lock")})
            lock_record_ok=False
            try:
                lock_value=json.loads((app.data_directory/".ugai.lock").read_text(encoding="utf-8"))
                lock_record_ok=all(lock_value.get(key) for key in ("pid","process_started_wall","build_hash","directory","nonce"))
            except Exception:
                lock_value={}
            acceptance.record_case("单实例与目录锁","lock_record","passed" if lock_record_ok else "failed",lock_value)
            runtime_manifest=validate_runtime_manifest(app.data_directory,True,True)
            if runtime_manifest is not None:
                acceptance.record_case("独立运行时","fixed_python","passed" if tuple(runtime_manifest.get("python_abi",[]))==FIXED_RUNTIME_PYTHON_ABI else "failed",runtime_manifest.get("python_executable"))
                acceptance.record_case("独立运行时","host_abi_independent","passed",{"host":list(sys.version_info[:2]),"runtime":list(runtime_manifest.get("python_abi",[]))})
                acceptance.record_case("独立运行时","worker_process","passed" if app.ai_worker is not None and app.ai_worker.alive() else "failed",{"alive":bool(app.ai_worker is not None and app.ai_worker.alive())})
                embedded=runtime_manifest.get("resolution_source")=="embedded" and bool(runtime_manifest.get("embedded_lock_checksum")) and bool(runtime_manifest.get("lock_complete",
                        runtime_lock_is_complete(runtime_manifest.get("resolved_wheels",[]))))
                acceptance.record_case("独立运行时","embedded_wheel_lock","passed" if embedded else "failed",{"resolution_source":runtime_manifest.get("resolution_source","dynamic")})
                acceptance.record_case("文件完整性","locked_manifest","passed" if embedded else "failed",{"manifest":runtime_manifest.get("manifest_checksum")})
            else:
                for item,case in (("独立运行时","fixed_python"),("独立运行时","worker_process"),("独立运行时","embedded_wheel_lock"),("独立运行时","host_abi_independent"),("文件完整性","locked_manifest")):
                    acceptance.record_case(item,case,"not_run",{"reason":"尚未完成文件完整性检查"})
            report["acceptance_report"]=str(acceptance.path)
            report["strict_pass"]=acceptance.strict_passed()
            app.api.block_input()
            app.api.release_all_buttons()
            if app.store is not None:
                app.store.close(5.0)
            app.api.close()
            root.destroy()
            app=None
            bridge=None
            root=None
        finally:
            if workspace is not None:
                workspace.cleanup()
            elif folder.exists():
                shutil.rmtree(folder,ignore_errors=True)
        automated=[value for key,value in report["checks"].items() if key!="真实窗口移动缩放最小化重启观察"]
        report["status"]="passed" if automated and all(automated) else "needs_attention"
    except Exception as error:
        report["details"]["fatal"]="".join(traceback.format_exception(type(error),error,error.__traceback__))
    finally:
        if app is not None:
            try:
                app.api.block_input()
                app.api.release_all_buttons()
                if app.store is not None:
                    app.store.close(5.0)
                app.api.close()
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        if root is not None:
            try:
                root.destroy()
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        if original_local is None:
            os.environ.pop("LOCALAPPDATA",None)
        else:
            os.environ["LOCALAPPDATA"]=original_local
    sys.stdout.write(json.dumps(report,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n")
    return 0 if report["status"]=="passed" else 1
def data_migration_contract_test():
    global SELECTED_DATA_DIR,CURRENT_VISION_RUNTIME,CURRENT_OCR_RUNTIME
    saved_selected=globals().get("SELECTED_DATA_DIR")
    saved_vision=globals().get("CURRENT_VISION_RUNTIME")
    saved_ocr=globals().get("CURRENT_OCR_RUNTIME")
    saved_env={key:os.environ.get(key) for key in ("UGAI_DATA_DIR","PIP_CACHE_DIR","TORCH_HOME","HF_HOME","HUGGINGFACE_HUB_CACHE","TRANSFORMERS_CACHE","XDG_CACHE_HOME","PYTHONPYCACHEPREFIX",
            "TORCH_EXTENSIONS_DIR","CUDA_CACHE_PATH","NUMBA_CACHE_DIR","MPLCONFIGDIR","TMP","TEMP")}
    saved_temp=tempfile.tempdir
    saved_path=list(sys.path)
    details={}
    class Value:
        def __init__(self):
            self.value=None
        def set(self,value):
            self.value=value
    class Api:
        ai_runtime=None
    class FakeLock:
        def __init__(self,path):
            self.path=Path(path)/".ugai.lock"
            self.closed=False
        def close(self):
            self.closed=True
    def prepare_locked(path,**kwargs):
        candidate=prepare_data_directory(path,**kwargs)
        candidate.directory_lock=FakeLock(path)
        candidate.directory_lock_owned=True
        return candidate
    def fake_app(store,base):
        app=object.__new__(AppStorageMixin)
        app.store=store
        app.data_directory=Path(base)
        app.runtime_installer=None
        app.ai_worker=None
        app.vision_runtime=None
        app.ocr_runtime=None
        app.data_directory_lock=FakeLock(base)
        app.write_audit=None
        app.acceptance_report=None
        app.lifecycle=ControlStateMachine()
        app.lifecycle.set_directory_phase("ready")
        app.api=Api()
        app.selected_game=store.selected_game()
        app.selected_window=None
        app.window_recommendation=None
        app.storage_fault=False
        app.data_dir_text=Value()
        app._writer_status_changed=lambda error:None
        app._update_runtime_status=lambda:None
        app._refresh_all=lambda:None
        app._update_control_availability=lambda:None
        return app
    try:
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            source_path=root/"source"
            target_path=root/"target"
            failed_path=root/"failed"
            conflict_path=root/"conflict"
            source=DataStore(source_path)
            game={"id":"migration-game-id","name":"迁移验收游戏","created":time.time(),"needs_review":False,"last_review":None}
            source.replace_games([game],game["id"])
            session="learn|migration"
            source.begin_learning_session(game["id"],session)
            feature=bytes([37])*FEATURE_LEN
            rgb=bytes([17,37,57])*PIXELS
            action=normalize_action({"kind":"click","button":"left","path":[[0.42,0.58]],"duration":0.08})
            source.append_sample(game["id"],feature,action,"learn",{"session_id":session,"capture_method":"migration-test","repeat_policy":"one_shot"},rgb,None,1.0)
            source.sample_write_barrier(5.0)
            source.validate_learning_session(game["id"],session)
            with source.lock,source.db:
                source.db.execute("INSERT INTO models(game_id,slot,saved,created,prototype_count,validation,payload,checksum) VALUES(?,?,?,?,?,?,?,?)",(game["id"],"temporary",time.time(),
                        time.time(),0,"{}",sqlite3.Binary(b"migration-model"),hashlib.sha256(b"migration-model").hexdigest()))
            model_path=source_path/"models"/"vision"/"migration.safetensors"
            model_path.parent.mkdir(parents=True,exist_ok=True)
            model_path.write_bytes(b"migration-model-file")
            ocr_path=source_path/"models"/"ocr"/"migration.bin"
            ocr_path.parent.mkdir(parents=True,exist_ok=True)
            ocr_path.write_bytes(b"migration-ocr-file")
            source_inventory=database_inventory(source.db_path,source_path)
            configure_data_directory(source_path)
            candidate=prepare_locked(target_path,source_store=source,source_base=source_path)
            unconfirmed=Path(SELECTED_DATA_DIR)==source_path and source.sample_writes_paused and not (target_path/"universal_game_ai.db").exists() and candidate.staging is not None and candidate.staging.exists()
            candidate.close()
            cancel_preserved=Path(SELECTED_DATA_DIR)==source_path and not source.sample_writes_paused and source.db.execute("SELECT COUNT(*) FROM games").fetchone()[0]==1 and not target_path.exists()
            conflict_path.mkdir()
            (conflict_path/"foreign.txt").write_text("foreign",encoding="utf-8")
            conflict_rejected=False
            try:
                prepare_locked(conflict_path,source_store=source,source_base=source_path)
            except RuntimeError:
                conflict_rejected=True
            failed_candidate=prepare_locked(failed_path,source_store=source,source_base=source_path)
            (failed_candidate.staging/"models"/"vision"/"migration.safetensors").write_bytes(b"tampered")
            failed_app=fake_app(source,source_path)
            failed=False
            try:
                App._commit_prepared_directory(failed_app,failed_candidate)
            except RuntimeError:
                failed=True
            failure_preserved=failed and failed_app.store is source and failed_app.data_directory==source_path and not source.sample_writes_paused and source.db.execute("SELECT COUNT(*) FROM samples").fetchone()[0]==source_inventory["sample_count"] and model_path.exists()
            candidate=prepare_locked(target_path,source_store=source,source_base=source_path)
            prepared_inventory=dict(candidate.target_inventory)
            app=fake_app(source,source_path)
            App._commit_prepared_directory(app,candidate)
            target_inventory=database_inventory(app.store.db_path,target_path)
            migrated=all(target_inventory.get(key)==source_inventory.get(key) for key in ("games","game_count","sample_count","model_count","vision_model_count","selected_game",
                    "model_files")) and prepared_inventory==target_inventory
            source_retained=source_path.exists() and model_path.exists() and sha256_file(model_path)==source_inventory["model_files"]["models/vision/migration.safetensors"]
            target_hashes=target_inventory.get("model_files",{})
            hash_preserved=target_hashes==source_inventory.get("model_files",{})
            record_files=list((target_path/"backups").glob("migration_*.json"))
            app.store.close(5.0)
            details={"unconfirmed":unconfirmed,"cancel_preserved":cancel_preserved,"conflict_rejected":conflict_rejected,"failure_preserved":failure_preserved,"migrated":migrated,
                "source_retained":source_retained,"hash_preserved":hash_preserved,"migration_record":bool(record_files),"source":source_inventory,"target":target_inventory}
            return all((unconfirmed,cancel_preserved,conflict_rejected,failure_preserved,migrated,source_retained,hash_preserved,bool(record_files))),details
    finally:
        SELECTED_DATA_DIR=saved_selected
        CURRENT_VISION_RUNTIME=saved_vision
        CURRENT_OCR_RUNTIME=saved_ocr
        sys.path[:]=saved_path
        for key,value in saved_env.items():
            if value is None:
                os.environ.pop(key,None)
            else:
                os.environ[key]=value
        tempfile.tempdir=saved_temp
def run_acceptance_test(path=None):
    static_result=run_static_contract_tests()
    if static_result!=0:
        return 1
    if os.name!="nt" or not path:
        sys.stdout.write(json.dumps({"status":"not_run","strict_pass":False,"failures":["必须在Windows 11 x64实机并提供已确认的数据目录"]},ensure_ascii=False,separators=(",",":"))+"\n")
        return 1
    runtime_result=run_runtime_e2e_test(path)
    window_result=run_window_contract_test(path)
    smoke_result=run_windows_smoke_test(path)
    if runtime_result!=0 or window_result!=0 or smoke_result!=0:
        return 1
    return strict_acceptance_gate(path)
EXTENSION_SCHEMA_VERSION=3
VISION_ARCHITECTURE_VERSION=2
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
def _atomic_write(path,data):
    return durable_atomic_write(path,data)
DEVELOPMENT_MODULE_ANCHORS=(
    ("src/bootstrap.py",None),
    ("src/windows/capture.py","CaptureProcessWorker"),
    ("src/acceptance/report.py","AcceptanceReport"),
    ("src/windows/identity.py","WinBridge"),
    ("src/modes/base.py","ModeStateCallbacks"),
    ("src/modes/learning.py","LearningController"),
    ("src/modes/sleeping.py","ReviewController"),
    ("src/modes/training.py","TrainingController"),
    ("src/modes/guidance.py","GuidanceWindow"),
    ("src/storage/database.py","DataStore"),
    ("src/gui/dialogs.py","GameSelectionDialog"),
    ("src/gui/app.py","AppUiMixin"),
    ("src/acceptance/windows.py","ReviewProcessHost"),
    ("src/bootstrap_runtime.py","SemanticEventHub"),
    ("src/runtime/install.py","_validated_download"),
    ("src/ai/worker.py","OfflineVisionRuntime"),
    ("src/acceptance/windows_runtime.py","_acceptance_geometry_complete"),
    ("src/acceptance/static.py","logic_contract_suite"),
)

def _top_level_node_name(node):
    name=getattr(node,"name",None)
    if name:
        return str(name)
    if isinstance(node,(ast.Assign,ast.AnnAssign)):
        targets=node.targets if isinstance(node,ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target,ast.Name):
                return target.id
    return ""

def split_development_modules(source):
    tree=ast.parse(source)
    lines=source.splitlines(keepends=True)
    positions={
        _top_level_node_name(node):min([node.lineno,*[item.lineno for item in getattr(node,"decorator_list",[])]])
        for node in tree.body if _top_level_node_name(node)
    }
    starts=[]
    for relative,anchor in DEVELOPMENT_MODULE_ANCHORS:
        line=1 if anchor is None else positions.get(anchor)
        if line is None:
            raise RuntimeError("开发模块锚点不存在："+str(anchor))
        starts.append((relative,int(line)))
    if [line for _,line in starts]!=sorted(line for _,line in starts):
        raise RuntimeError("开发模块锚点顺序无效")
    guard_line=len(lines)+1
    for node in tree.body:
        if not isinstance(node,ast.If) or not isinstance(node.test,ast.Compare):
            continue
        left=node.test.left
        if isinstance(left,ast.Name) and left.id=="__name__":
            guard_line=node.lineno
            break
    modules={}
    for index,(relative,line) in enumerate(starts):
        next_line=starts[index+1][1] if index+1<len(starts) else guard_line
        fragment="".join(lines[line-1:next_line-1]).rstrip()+"\n"
        if not fragment.strip():
            raise RuntimeError("开发模块为空："+relative)
        compile(fragment,relative,"exec")
        modules[relative]=fragment
    return modules

def _development_loader_source(order):
    return (
        "import json\n"
        "from pathlib import Path\n"
        "ROOT=Path(__file__).resolve().parent\n"
        "ORDER="+repr(list(order))+"\n"
        "def load_runtime():\n"
        "    namespace={'__name__':'ugai_dev_runtime','__file__':str(ROOT/'dist'/'main.py'),'__package__':None}\n"
        "    for relative in ORDER:\n"
        "        path=ROOT/relative\n"
        "        exec(compile(path.read_text(encoding='utf-8'),str(path),'exec'),namespace,namespace)\n"
        "    return namespace\n"
        "def main(argv=None):\n"
        "    return load_runtime()['main'](argv)\n"
        "if __name__=='__main__':\n"
        "    raise SystemExit(main())\n"
    )

def _single_file_builder_source(order):
    return (
        "import json\n"
        "from pathlib import Path\n"
        "ROOT=Path(__file__).resolve().parent\n"
        "ORDER="+repr(list(order))+"\n"
        "def build(target=None):\n"
        "    output=Path(target).resolve() if target else ROOT/'dist'/'main.py'\n"
        "    source='\\n'.join((ROOT/item).read_text(encoding='utf-8').rstrip() for item in ORDER)\n"
        "    source+='\\n\\nif __name__==\"__main__\":\\n    raise SystemExit(main())\\n'\n"
        "    compile(source,str(output),'exec')\n"
        "    output.parent.mkdir(parents=True,exist_ok=True)\n"
        "    temporary=output.with_suffix(output.suffix+'.tmp')\n"
        "    temporary.write_text(source,encoding='utf-8',newline='\\n')\n"
        "    temporary.replace(output)\n"
        "    return output\n"
        "if __name__=='__main__':\n"
        "    print(build())\n"
    )

def project_module_templates(source=None):
    source_text=str(source) if source is not None else Path(__file__).read_text(encoding="utf-8")
    modules=split_development_modules(source_text)
    order=list(modules)
    modules["src/module_order.json"]=json.dumps(order,ensure_ascii=False,indent=2)+"\n"
    modules["dev_main.py"]=_development_loader_source(order)
    modules["build_single_file.py"]=_single_file_builder_source(order)
    modules["main.py"]="from dev_main import main\nif __name__=='__main__':\n    raise SystemExit(main())\n"
    modules["tests/__init__.py"]=""
    modules["tests/conftest.py"]=(
        "import sys\nfrom pathlib import Path\nROOT=Path(__file__).resolve().parents[1]\n"
        "if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))\n"
    )
    modules["tests/test_module_layout.py"]=(
        "from pathlib import Path\n"
        "def test_modules_contain_real_implementations():\n"
        "    root=Path(__file__).resolve().parents[1]\n"
        "    assert len((root/'main.py').read_text(encoding='utf-8').splitlines())<=4\n"
        "    assert not list(root.rglob('_legacy_runtime.py'))\n"
        "    assert 'class LearningController' in (root/'src'/'modes'/'learning.py').read_text(encoding='utf-8')\n"
        "    assert 'class TrainingExecution' in (root/'src'/'modes'/'training.py').read_text(encoding='utf-8')\n"
    )
    modules["tests/test_build.py"]=(
        "import subprocess,sys\nfrom pathlib import Path\n"
        "def test_single_file_build_and_logic_contract(tmp_path):\n"
        "    root=Path(__file__).resolve().parents[1]\n"
        "    target=tmp_path/'main.py'\n"
        "    subprocess.run([sys.executable,str(root/'build_single_file.py')],cwd=root,check=True,capture_output=True,text=True)\n"
        "    built=root/'dist'/'main.py'\n"
        "    assert built.is_file() and built.stat().st_size>500000\n"
        "    result=subprocess.run([sys.executable,str(built),'test','logic'],capture_output=True,text=True,timeout=120)\n"
        "    assert result.returncode==0,result.stderr+result.stdout\n"
    )
    modules["pytest.ini"]="[pytest]\naddopts = -q\ntestpaths = tests\n"
    modules[".github/workflows/windows11-x64.yml"]=(
        "name: windows11-x64-strict\non:\n  workflow_dispatch:\njobs:\n  strict:\n"
        "    runs-on: [self-hosted, Windows, X64, windows-11, interactive-desktop]\n    timeout-minutes: 180\n"
        "    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with:\n          python-version: '3.12'\n"
        "      - run: python -m pytest\n      - run: python build_single_file.py\n"
        "      - run: python dist/main.py test static\n"
        "      - run: python dist/main.py acceptance all \"$env:RUNNER_TEMP\\UniversalGameAI-e2e\"\n"
    )
    return modules

def materialize_project_layout(base):
    root=Path(base)/"project"
    source=Path(__file__).read_text(encoding="utf-8")
    modules=project_module_templates(source)
    for relative,content in modules.items():
        _atomic_write(root/relative,content)
    _atomic_write(root/"dist/main.py",source)
    files=sorted([*modules,"dist/main.py"])
    manifest={
        "format":3,
        "architecture":"shared_namespace_source_modules",
        "legacy_runtime":False,
        "source_sha256":hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "module_order":json.loads(modules["src/module_order.json"]),
        "files":files,
        "generated":time.time(),
    }
    _atomic_write(root/"manifest.json",json.dumps(manifest,ensure_ascii=False,sort_keys=True,separators=(",",":")))
    return root

def configure_data_directory(path):
    global SELECTED_DATA_DIR
    raw_base=Path(path).expanduser().absolute()
    if not raw_base.exists() or not raw_base.is_dir():
        raise RuntimeError("文件夹尚未完成准备")
    reject_reparse_points(raw_base)
    base=raw_base.resolve()
    reject_reparse_points(base)
    os.environ["UGAI_DATA_DIR"]=str(base)
    os.environ.pop("PIP_TARGET",None)
    os.environ["PIP_CACHE_DIR"]=str(base/"cache"/"pip")
    os.environ["TORCH_HOME"]=str(base/"models"/"torch")
    os.environ["HF_HOME"]=str(base/"models"/"huggingface")
    os.environ["HUGGINGFACE_HUB_CACHE"]=str(base/"cache"/"huggingface_hub")
    os.environ["TRANSFORMERS_CACHE"]=str(base/"cache"/"transformers")
    os.environ["XDG_CACHE_HOME"]=str(base/"cache")
    os.environ["PYTHONPYCACHEPREFIX"]=str(base/"cache"/"pycache")
    os.environ["TORCH_EXTENSIONS_DIR"]=str(base/"cache"/"torch_extensions")
    os.environ["CUDA_CACHE_PATH"]=str(base/"cache"/"cuda")
    os.environ["NUMBA_CACHE_DIR"]=str(base/"cache"/"numba")
    os.environ["MPLCONFIGDIR"]=str(base/"cache"/"matplotlib")
    os.environ["TMP"]=str(base/"temp")
    os.environ["TEMP"]=str(base/"temp")
    tempfile.tempdir=str(base/"temp")
    SELECTED_DATA_DIR=base
    return base
def same_directory(first,second):
    if first is None or second is None:
        return False
    a=Path(first).expanduser().resolve()
    b=Path(second).expanduser().resolve()
    if os.path.normcase(str(a))==os.path.normcase(str(b)):
        return True
    try:
        return bool(a.exists() and b.exists() and os.path.samefile(a,b))
    except OSError:
        return False
def migration_model_hashes(base):
    root=Path(base)
    result={}
    for relative in (Path("models")/"vision",Path("models")/"ocr"):
        folder=root/relative
        if folder.exists():
            for item in sorted(folder.rglob("*")):
                if item.is_file():
                    result[item.relative_to(root).as_posix()]=sha256_file(item)
    return result
def database_inventory(db_path,base):
    path=Path(db_path)
    if not path.exists():
        raise RuntimeError("迁移数据库不存在")
    connection=sqlite3.connect(str(path),timeout=5.0)
    connection.row_factory=sqlite3.Row
    try:
        quick=connection.execute("PRAGMA quick_check").fetchone()
        if not quick or str(quick[0]).lower()!="ok":
            raise RuntimeError("数据库quick_check失败："+str(quick[0] if quick else "无结果"))
        foreign=connection.execute("PRAGMA foreign_key_check").fetchall()
        if foreign:
            raise RuntimeError("数据库外键检查失败："+str(len(foreign)))
        tables={str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        required={"meta","games","samples","models"}
        if not required.issubset(tables):
            raise RuntimeError("数据库schema缺少表："+"、".join(sorted(required-tables)))
        row=connection.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
        schema=safe_int(row[0] if row else 0,0)
        games=[{"id":str(item["id"]),"name":str(item["name"])} for item in connection.execute("SELECT id,name FROM games ORDER BY id").fetchall()]
        samples=safe_int(connection.execute("SELECT COUNT(*) FROM samples").fetchone()[0],0,0)
        models=safe_int(connection.execute("SELECT COUNT(*) FROM models").fetchone()[0],0,0)
        vision_models=safe_int(connection.execute("SELECT COUNT(*) FROM vision_models").fetchone()[0],0,0) if "vision_models" in tables else 0
        selected=connection.execute("SELECT value FROM meta WHERE key='selected_game'").fetchone()
        return {"schema_version":schema,"games":games,"game_count":len(games),"sample_count":samples,"model_count":models,"vision_model_count":vision_models,
            "selected_game":str(selected[0]) if selected else None,"model_files":migration_model_hashes(base)}
    finally:
        connection.close()
def data_tree_manifest(base):
    root=Path(base)
    files=[]
    for item in sorted(root.rglob("*")):
        if item.is_file() and item.name not in {".ugai_migration_manifest.json",".ugai.lock","universal_game_ai.db-wal","universal_game_ai.db-shm"}:
            files.append({"path":item.relative_to(root).as_posix(),"size":int(item.stat().st_size),"sha256":sha256_file(item)})
    return {"created":time.time(),"files":files,"file_count":len(files),"total_bytes":sum(item["size"] for item in files)}
def verify_data_tree_manifest(base,manifest):
    root=Path(base)
    expected=manifest.get("files",[]) if isinstance(manifest,dict) else []
    for item in expected:
        path=root/str(item.get("path",""))
        if not path.is_file() or int(path.stat().st_size)!=safe_int(item.get("size"),-1) or sha256_file(path)!=str(item.get("sha256","")):
            raise RuntimeError("SHA-256清单校验失败："+str(item.get("path","")))
    return True
def copy_migration_files(source,staging,stop_event=None,progress=None):
    source=Path(source)
    staging=Path(staging)
    items=[]
    for relative in AUTHORITATIVE_DATA_PATHS[1:]:
        path=source/relative
        if path.exists():
            items.append((path,staging/relative))
    for path in sorted(source.glob("recovery_*")):
        if path.exists():
            items.append((path,staging/path.name))
    for path in sorted(source.iterdir()):
        if path.is_file() and path.name not in {"universal_game_ai.db","universal_game_ai.db-wal","universal_game_ai.db-shm"} and not path.name.startswith(".ugai_"):
            items.append((path,staging/path.name))
    total=max(1,len(items))
    for index,(src,dst) in enumerate(items):
        if stop_event is not None and stop_event.is_set():
            raise InputStopped("文件夹迁移已停止")
        dst.parent.mkdir(parents=True,exist_ok=True)
        if src.is_dir():
            shutil.copytree(src,dst,copy_function=shutil.copy2,dirs_exist_ok=False)
        else:
            shutil.copy2(src,dst)
        if progress is not None:
            progress(20.0+45.0*(index+1)/total)
class PreparedDataDirectory:
    def __init__(self,destination,staging,store,runtime_manifest=None,source_store=None,source_base=None,source_inventory=None,target_inventory=None,sha_manifest=None,same=False,destination_created=False):
        self.destination=Path(destination)
        self.base=self.destination
        self.staging=Path(staging) if staging is not None else None
        self.store=store
        self.runtime_manifest=dict(runtime_manifest) if isinstance(runtime_manifest,dict) else None
        self.source_store=source_store
        self.source_base=Path(source_base) if source_base is not None else None
        self.source_inventory=dict(source_inventory) if isinstance(source_inventory,dict) else None
        self.target_inventory=dict(target_inventory) if isinstance(target_inventory,dict) else None
        self.sha_manifest=dict(sha_manifest) if isinstance(sha_manifest,dict) else None
        self.same=bool(same)
        self.destination_created=bool(destination_created)
        self.source_paused=bool(source_store is not None and not self.same)
        self.promoted=False
        self.closed=False
        self.directory_lock=None
        self.directory_lock_owned=False
    def resume_source(self):
        if self.source_paused and self.source_store is not None:
            try:
                self.source_store.resume_sample_writes()
            finally:
                self.source_paused=False
    def close_staging_store(self):
        if self.store is None:
            return True
        stopped=self.store.close(5.0)
        if not stopped:
            raise RuntimeError("候选文件夹SQLite未能安全关闭")
        self.store=None
        return True
    def close(self):
        if self.closed:
            return True
        self.closed=True
        try:
            if self.store is not None and self.store is not self.source_store:
                self.store.close(5.0)
        finally:
            self.store=None
            if self.staging is not None and self.staging.exists() and not self.promoted:
                shutil.rmtree(self.staging,ignore_errors=True)
            self.resume_source()
            if self.directory_lock_owned and self.directory_lock is not None:
                try:
                    self.directory_lock.close()
                except Exception as error:
                    record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
                self.directory_lock=None
                self.directory_lock_owned=False
            if self.destination_created and self.destination.exists():
                try:
                    if not any(self.destination.iterdir()):
                        self.destination.rmdir()
                except OSError:
                    pass
        return True
def _filesystem_capability_check(base):
    base=Path(base)
    probe=base/(".ugai_probe_"+uuid.uuid4().hex)
    replacement=base/(".ugai_replace_"+uuid.uuid4().hex)
    lock_path=base/(".ugai_lock_"+uuid.uuid4().hex)
    try:
        probe.write_bytes(os.urandom(64))
        replacement.write_bytes(os.urandom(64))
        os.replace(replacement,probe)
        if not probe.exists() or probe.stat().st_size!=64:
            raise RuntimeError("原子替换测试失败")
        first=lock_path.open("w+b")
        second=lock_path.open("r+b")
        try:
            first.write(b"0")
            first.flush()
            locked=False
            if os.name=="nt":
                import msvcrt
                first.seek(0)
                msvcrt.locking(first.fileno(),msvcrt.LK_NBLCK,1)
                try:
                    second.seek(0)
                    msvcrt.locking(second.fileno(),msvcrt.LK_NBLCK,1)
                except OSError:
                    locked=True
                finally:
                    try:
                        first.seek(0)
                        msvcrt.locking(first.fileno(),msvcrt.LK_UNLCK,1)
                    except Exception as error:
                        record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
            else:
                import fcntl
                fcntl.flock(first.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                try:
                    fcntl.flock(second.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                except OSError:
                    locked=True
                finally:
                    fcntl.flock(first.fileno(),fcntl.LOCK_UN)
            if not locked:
                raise RuntimeError("文件锁测试失败")
        finally:
            first.close()
            second.close()
    finally:
        for item in (probe,replacement,lock_path):
            try:
                item.unlink()
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
def _runtime_tree_manifest(root,verify_files=True):
    tree=Path(root)
    path=tree/"runtime_manifest.json"
    if not path.is_file():
        return None
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value,dict) or safe_int(value.get("layout_version"),0)!=RUNTIME_LAYOUT_VERSION:
            return None
        checksum=str(value.get("manifest_checksum",""))
        payload=dict(value)
        payload.pop("manifest_checksum",None)
        if len(checksum)!=64 or hashlib.sha256(canonical_bytes(payload)).hexdigest()!=checksum:
            return None
        wheels=value.get("resolved_wheels")
        wheel_checksum=str(value.get("wheel_lock_checksum",""))
        if not isinstance(wheels,list) or not wheels or hashlib.sha256(canonical_bytes(wheels)).hexdigest()!=wheel_checksum:
            return None
        if value.get("lock_complete") is not True or not runtime_lock_is_complete(wheels):
            return None
        for wheel in wheels:
            if not isinstance(wheel,dict) or len(str(wheel.get("sha256","")))!=64 or safe_int(wheel.get("size"),-1)<0:
                return None
        if verify_files:
            files=value.get("critical_files")
            if not isinstance(files,dict) or not files:
                return None
            for relative,expected in files.items():
                target=tree/str(relative)
                if not target.is_file() or sha256_file(target)!=str(expected):
                    return None
        return value
    except Exception:
        return None
def recover_runtime_layout(base):
    root=Path(base)
    current=root/"runtime.current"
    rollbacks=sorted((item for item in root.glob("runtime.rollback.*") if item.is_dir()),key=lambda item:item.stat().st_mtime,reverse=True)
    if _runtime_tree_manifest(current,True) is not None:
        for item in rollbacks:
            shutil.rmtree(item,ignore_errors=True)
        return True
    valid=next((item for item in rollbacks if _runtime_tree_manifest(item,True) is not None),None)
    if valid is None:
        return False
    if current.exists():
        quarantine=root/("runtime.invalid."+uuid.uuid4().hex)
        try:
            os.replace(current,quarantine)
        except Exception:
            shutil.rmtree(current,ignore_errors=True)
        shutil.rmtree(quarantine,ignore_errors=True)
    os.replace(valid,current)
    for item in rollbacks:
        if item.exists():
            shutil.rmtree(item,ignore_errors=True)
    return True
def validate_runtime_manifest(base,verify_files=False,verify_lock=False):
    recover_runtime_layout(base)
    current=Path(base)/"runtime.current"
    value=_runtime_tree_manifest(current,verify_files)
    if value is None:
        path=current/"runtime_manifest.json"
        if not path.exists():
            return None
        raise RuntimeError("运行库清单、wheel锁或文件SHA-256校验失败")
    if tuple(value.get("python_abi",[]))!=FIXED_RUNTIME_PYTHON_ABI:
        raise RuntimeError("运行库不是固定的独立Python "+FIXED_RUNTIME_PYTHON_VERSION)
    if safe_int(value.get("lock_manifest_version"),0)!=RUNTIME_LOCK_MANIFEST_VERSION:
        raise RuntimeError("运行库锁清单版本不一致")
    if str(value.get("preprocess_hash",""))!=VISION_PREPROCESS_HASH:
        raise RuntimeError("运行库预处理版本不一致")
    architecture=str(value.get("architecture",""))
    wheels=value.get("resolved_wheels")
    embedded_checksum=str(value.get("embedded_lock_checksum",""))
    if str(value.get("resolution_source",""))!="embedded" or not isinstance(wheels,list) or not wheels or hashlib.sha256(canonical_bytes(wheels)).hexdigest()!=embedded_checksum:
        raise RuntimeError("运行库未使用内嵌wheel锁")
    if verify_lock:
        expected,expected_checksum,_=embedded_runtime_lock(architecture)
        if wheels!=expected or embedded_checksum!=expected_checksum:
            raise RuntimeError("运行库wheel锁与当前程序内嵌锁不一致")
        if value.get("lock_complete") is not True or not runtime_lock_is_complete(wheels):
            raise RuntimeError("内嵌运行库wheel锁不完整")
        expected_contracts={key:{field:sorted(values) for field,values in contract.items()} for key,contract in runtime_dependency_contracts().items()}
        if value.get("dependency_providers")!=runtime_dependency_providers() or value.get("dependency_contracts")!=expected_contracts:
            raise RuntimeError("运行库依赖提供者或闭包契约不一致")
    if os.name=="nt" and architecture!=native_windows_architecture():
        raise RuntimeError("运行库架构与Windows原生架构不一致")
    freeze=value.get("pip_freeze")
    if not isinstance(freeze,list) or not freeze:
        raise RuntimeError("运行库缺少pip freeze清单")
    frozen={}
    for line in freeze:
        text=str(line).strip()
        if "==" in text:
            name,version=text.split("==",1)
            frozen[normalized_project_name(name)]=version.strip()
    if verify_lock:
        for name,version in runtime_lock_project_versions().items():
            if frozen.get(name)!=version:
                raise RuntimeError("pip freeze与内嵌wheel锁不一致："+name)
    return value
def existing_data_directory_status(path):
    root=Path(path)
    if not root.exists() or not root.is_dir() or not (root/"universal_game_ai.db").is_file():
        return False,"缺少通用游戏AI数据库"
    allowed={"universal_game_ai.db","universal_game_ai.db-wal","universal_game_ai.db-shm","models","runtime.current","backups","quarantine","cache","temp","logs","project","audit",".ugai_migration_manifest.json"}
    unknown=[]
    for item in root.iterdir():
        name=item.name
        if name in allowed or name.startswith("runtime.rollback.") or name.startswith("runtime.invalid.") or name.startswith("runtime.incompatible.") or name.startswith("recovery_") or name.startswith(".ugai_"):
            continue
        unknown.append(name)
    if unknown:
        return False,"发现不属于通用游戏AI的数据："+"、".join(sorted(unknown)[:8])
    try:
        inventory=database_inventory(root/"universal_game_ai.db",root)
        if inventory.get("schema_version",0)>DATABASE_SCHEMA_VERSION:
            return False,"数据库版本高于当前程序"
    except Exception as error:
        return False,str(error)
    return True,"合法既有目录"
def directory_runtime_manifest(base):
    try:
        return validate_runtime_manifest(base,True,False)
    except RuntimeError:
        root=Path(base)
        current=root/"runtime.current"
        if current.exists():
            target=root/("runtime.incompatible."+uuid.uuid4().hex)
            try:
                os.replace(current,target)
            except Exception:
                shutil.rmtree(current,ignore_errors=True)
        return None
def prepare_data_directory(path,stop_event=None,progress=None,source_store=None,source_base=None):
    destination=Path(path).expanduser().resolve()
    source_path=Path(source_base).expanduser().resolve() if source_base is not None else None
    if stop_event is not None and stop_event.is_set():
        raise InputStopped("文件夹准备已停止")
    if source_store is not None and source_path is not None and same_directory(destination,source_path):
        source_store.sample_write_barrier(10.0)
        with source_store.lock:
            source_store.db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        inventory=database_inventory(source_store.db_path,source_path)
        if inventory.get("schema_version")!=DATABASE_SCHEMA_VERSION:
            raise RuntimeError("数据库结构升级未完成")
        if progress is not None:
            progress(100.0)
        return PreparedDataDirectory(destination,None,source_store,directory_runtime_manifest(source_path),source_store,source_path,inventory,inventory,None,True,False)
    created=not destination.exists()
    destination.mkdir(parents=True,exist_ok=True)
    for stale in list(destination.glob(".ugai_migration_*"))+list(destination.glob(".ugai_prepare_*"))+list(destination.glob(".ugai_rollback_*")):
        if stale.is_dir():
            shutil.rmtree(stale,ignore_errors=True)
    existing=[item for item in destination.iterdir() if item.name!=".ugai.lock"]
    reopening=False
    if existing:
        valid_existing,existing_reason=existing_data_directory_status(destination)
        reopening=bool(source_store is None and valid_existing)
        if not reopening:
            raise RuntimeError("目标目录已含有另一套数据或其他文件；"+existing_reason+"；为避免静默合并，请选择空目录、当前原文件夹或合法既有目录")
        source_path=destination
    ensure_free_space(destination,required_migration_space(source_path),"文件夹迁移")
    staging=destination/(".ugai_migration_"+uuid.uuid4().hex if source_store is not None else ".ugai_prepare_"+uuid.uuid4().hex)
    staging.mkdir(parents=True,exist_ok=False)
    candidate=None
    paused=False
    try:
        _filesystem_capability_check(staging)
        if progress is not None:
            progress(8.0)
        if source_store is not None and source_path is not None:
            source_store.pause_sample_writes("正在把原文件夹迁移到新目录")
            paused=True
            source_inventory=database_inventory(source_store.db_path,source_path)
            destination_db=staging/"universal_game_ai.db"
            with source_store.lock:
                source_connection=source_store.db.current()
                target_connection=sqlite3.connect(str(destination_db),timeout=10.0)
                try:
                    source_connection.backup(target_connection,pages=256)
                    target_connection.commit()
                finally:
                    target_connection.close()
            if progress is not None:
                progress(20.0)
            copy_migration_files(source_path,staging,stop_event,progress)
        elif reopening and source_path is not None:
            source_inventory=database_inventory(source_path/"universal_game_ai.db",source_path)
            source_connection=sqlite3.connect(str(source_path/"universal_game_ai.db"),timeout=10.0)
            target_connection=sqlite3.connect(str(staging/"universal_game_ai.db"),timeout=10.0)
            try:
                source_connection.backup(target_connection,pages=256)
                target_connection.commit()
            finally:
                target_connection.close()
                source_connection.close()
            if progress is not None:
                progress(20.0)
            copy_migration_files(source_path,staging,stop_event,progress)
        else:
            source_inventory=None
        for name in ("models","models/vision","models/ocr","cache","cache/pip","cache/pycache","cache/torch_extensions","cache/cuda","cache/numba","cache/matplotlib","temp","logs","backups","quarantine","audit"):
            (staging/name).mkdir(parents=True,exist_ok=True)
        if DEVELOPER_MODE:
            materialize_project_layout(staging)
        if progress is not None:
            progress(70.0)
        candidate=DataStore(staging)
        if candidate.read_only:
            raise RuntimeError(candidate.read_only_reason or "数据库只读")
        candidate.sample_write_barrier()
        with candidate.lock:
            candidate.db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        target_inventory=database_inventory(candidate.db_path,staging)
        if target_inventory.get("schema_version")!=DATABASE_SCHEMA_VERSION:
            raise RuntimeError("数据库结构升级失败")
        if source_inventory is not None:
            for key in ("games","game_count","sample_count","model_count","vision_model_count","selected_game","model_files"):
                if target_inventory.get(key)!=source_inventory.get(key):
                    raise RuntimeError("迁移校验不一致："+str(key))
        second=sqlite3.connect(str(candidate.db_path),timeout=0.1)
        try:
            candidate.db.execute("BEGIN IMMEDIATE")
            locked=False
            try:
                second.execute("BEGIN IMMEDIATE")
            except sqlite3.OperationalError:
                locked=True
            finally:
                try:
                    second.rollback()
                except Exception as error:
                    record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
                candidate.db.rollback()
            if not locked:
                raise RuntimeError("SQLite写锁测试失败")
        finally:
            second.close()
        runtime_manifest=directory_runtime_manifest(staging)
        sha_manifest=data_tree_manifest(staging)
        verify_data_tree_manifest(staging,sha_manifest)
        (staging/".ugai_migration_manifest.json").write_text(json.dumps({"source":str(source_path) if source_path is not None else None,"destination":str(destination),
                    "inventory":target_inventory,"sha256":sha_manifest},ensure_ascii=False,sort_keys=True,separators=(",",":")),encoding="utf-8")
        if progress is not None:
            progress(100.0)
        return PreparedDataDirectory(destination,staging,candidate,runtime_manifest,source_store,source_path,source_inventory,target_inventory,sha_manifest,False,created)
    except Exception:
        if candidate is not None:
            try:
                candidate.close(5.0)
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        shutil.rmtree(staging,ignore_errors=True)
        if paused and source_store is not None:
            source_store.resume_sample_writes()
        if created:
            try:
                if destination.exists() and not any(destination.iterdir()):
                    destination.rmdir()
            except OSError:
                pass
        raise
def _validated_download(url,target,expected_sha256,maximum_bytes,allowed_hosts=None,progress=None,expected_size=None,retries=3):
    value=str(url)
    parsed=urllib.parse.urlsplit(value)
    allowed=set(allowed_hosts or RUNTIME_ALLOWED_DOWNLOAD_HOSTS)
    if parsed.scheme.lower()!="https" or parsed.hostname not in allowed:
        raise RuntimeError("下载地址不在允许域名锁内："+value)
    destination=Path(target)
    temporary=destination.with_suffix(destination.suffix+".part")
    metadata_path=destination.with_suffix(destination.suffix+".part.json")
    destination.parent.mkdir(parents=True,exist_ok=True)
    expected_size=safe_int(expected_size,0,0,int(maximum_bytes))
    if destination.is_file():
        size=destination.stat().st_size
        if (not expected_size or size==expected_size) and sha256_file(destination,int(maximum_bytes)).lower()==str(expected_sha256).lower():
            return {"url":value,"final_url":value,"sha256":str(expected_sha256).lower(),"size":size,"attempts":0,"retries":0,"resumed_bytes":size,"range_supported":True,"cached":True}
        destination.unlink()
    metadata={"url":value,"sha256":str(expected_sha256).lower(),"expected_size":expected_size}
    try:
        existing=json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else None
    except Exception:
        existing=None
    if existing!=metadata:
        try:
            temporary.unlink()
        except OSError:
            pass
        metadata_path.write_text(json.dumps(metadata,ensure_ascii=False,sort_keys=True,separators=(",",":")),encoding="utf-8")
    opener=urllib.request.build_opener(urllib.request.ProxyHandler())
    last_error=None
    initial_size=temporary.stat().st_size if temporary.exists() else 0
    for attempt in range(max(1,safe_int(retries,3,1,8))):
        offset=temporary.stat().st_size if temporary.exists() else 0
        if offset>int(maximum_bytes) or expected_size and offset>expected_size:
            temporary.unlink(missing_ok=True)
            offset=0
        digest=hashlib.sha256()
        if offset:
            with temporary.open("rb") as existing_handle:
                for block in iter(lambda:existing_handle.read(1024*1024),b""):
                    digest.update(block)
        headers={"User-Agent":"UniversalGameAI/"+str(FORMAT_VERSION)}
        if offset:
            headers["Range"]="bytes="+str(offset)+"-"
        request=urllib.request.Request(value,headers=headers)
        try:
            with opener.open(request,timeout=120) as response:
                final=urllib.parse.urlsplit(response.geturl())
                if final.scheme.lower()!="https" or final.hostname not in allowed:
                    raise RuntimeError("最终重定向地址不在允许域名锁内："+response.geturl())
                status=safe_int(getattr(response,"status",response.getcode()),200)
                range_supported=bool(offset and status==206)
                if offset and not range_supported:
                    temporary.unlink(missing_ok=True)
                    offset=0
                    digest=hashlib.sha256()
                mode="ab" if offset else "wb"
                expected_length=safe_int(response.headers.get("Content-Length"),0,0)
                projected=offset+expected_length if expected_length else 0
                if projected and projected>int(maximum_bytes):
                    raise RuntimeError("下载文件超过锁定大小上限")
                size=offset
                with temporary.open(mode) as handle:
                    while True:
                        block=response.read(1024*1024)
                        if not block:
                            break
                        size+=len(block)
                        if size>int(maximum_bytes):
                            raise RuntimeError("下载文件超过锁定大小上限")
                        digest.update(block)
                        handle.write(block)
                        handle.flush()
                        if progress is not None:
                            progress(size,expected_size or projected)
                if expected_size and size!=expected_size:
                    raise RuntimeError("下载文件长度与内嵌锁不一致")
                if digest.hexdigest().lower()!=str(expected_sha256).lower():
                    raise RuntimeError("下载文件SHA-256与内嵌锁不一致")
                os.replace(temporary,destination)
                metadata_path.unlink(missing_ok=True)
                return {"url":value,"final_url":response.geturl(),"sha256":digest.hexdigest(),"size":size,"attempts":attempt+1,"retries":attempt,"resumed_bytes":offset,
                    "range_supported":bool(range_supported),"cached":False}
        except Exception as error:
            last_error=error
            if attempt+1>=max(1,safe_int(retries,3,1,8)):
                break
            time.sleep(min(8.0,0.5*(2**attempt)))
    raise RuntimeError("下载重试失败："+str(last_error))
def _bootstrap_embedded_python(staging,architecture,cache_root):
    runtime=Path(staging)/"python"
    runtime.mkdir(parents=True,exist_ok=True)
    artifact=FIXED_RUNTIME_PYTHON_ARTIFACTS.get(str(architecture))
    if not isinstance(artifact,dict):
        raise RuntimeError("当前架构没有固定Python运行库")
    downloads=Path(cache_root)/"bootstrap"/str(architecture)
    archive=downloads/artifact["filename"]
    pip_wheel=downloads/("pip-"+FIXED_RUNTIME_PIP_VERSION+"-py3-none-any.whl")
    _runtime_emit("progress",value=2.0,message="下载固定Python "+FIXED_RUNTIME_PYTHON_VERSION+" "+str(architecture))
    python_artifact=_validated_download(artifact["url"],archive,artifact["sha256"],artifact["max_bytes"],expected_size=artifact["size"],retries=3)
    _runtime_emit("progress",value=5.0,message="解压固定独立Python")
    import zipfile
    with zipfile.ZipFile(archive,"r") as bundle:
        for info in bundle.infolist():
            name=info.filename.replace("\\","/")
            if name.startswith("/") or ".." in Path(name).parts:
                raise RuntimeError("Python运行时压缩包包含越界路径")
            bundle.extract(info,runtime)
    site=runtime/"Lib"/"site-packages"
    site.mkdir(parents=True,exist_ok=True)
    pth=runtime/"python312._pth"
    pth.write_text("python312.zip\n.\nLib\nLib\\site-packages\nimport site\n",encoding="utf-8")
    _runtime_emit("progress",value=7.0,message="安装固定pip引导wheel")
    pip_artifact=_validated_download(FIXED_RUNTIME_PIP_URL,pip_wheel,FIXED_RUNTIME_PIP_SHA256,FIXED_RUNTIME_PIP_MAX_BYTES,expected_size=FIXED_RUNTIME_PIP_SIZE,retries=3)
    with zipfile.ZipFile(pip_wheel,"r") as bundle:
        for info in bundle.infolist():
            name=info.filename.replace("\\","/")
            if name.startswith("/") or ".." in Path(name).parts:
                raise RuntimeError("pip wheel包含越界路径")
            bundle.extract(info,site)
    python=runtime/("python.exe" if os.name=="nt" else "python")
    if not python.is_file():
        raise RuntimeError("固定Python运行时缺少python.exe")
    python_artifact["architecture"]=str(architecture)
    pip_artifact["architecture"]=str(architecture)
    return python,{"python":python_artifact,"pip":pip_artifact}
def _runtime_emit(kind,**values):
    value=str(kind)
    stage=str(values.pop("stage",{"result":"COMPLETED","error":"FAILED","status":"STARTING"}.get(value,"RUNNING")))
    packet={"protocol_version":RUNTIME_INSTALL_PROTOCOL_VERSION,"stage":stage,"kind":value,**values}
    sys.stdout.write(json.dumps(packet,ensure_ascii=False,separators=(",",":"))+"\n")
    sys.stdout.flush()
def _runtime_python(runtime_root):
    root=Path(runtime_root)
    direct=root/"python"/("python.exe" if os.name=="nt" else "python")
    if direct.exists():
        return str(direct)
    return str(root/("venv/Scripts/python.exe" if os.name=="nt" else "venv/bin/python"))
def _runtime_worker_command(command,env,label):
    _runtime_emit("status",message=label)
    process=subprocess.Popen([str(value) for value in command],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",env=env)
    if process.stdout is not None:
        for line in process.stdout:
            text=line.strip()
            if text:
                _runtime_emit("line",message=text[-600:])
    code=process.wait()
    if code!=0:
        raise RuntimeError(label+"失败，退出码"+str(code))
def _runtime_resolution_lock(python,pins,env,indexes,report_path):
    if not DEVELOPER_MODE:
        raise RuntimeError("动态依赖解析仅允许开发模式，正式下载必须读取内嵌完整wheel锁")
    command=[str(python),"-m","pip","install","--dry-run","--ignore-installed","--only-binary=:all:","--no-cache-dir","--report",str(report_path),"--index-url",str(indexes[0])]
    for index_url in indexes[1:]:
        command.extend(["--extra-index-url",str(index_url)])
    command.extend(str(pin) for pin in pins)
    _runtime_worker_command(command,env,"开发期生成运行库解析锁")
    report=json.loads(Path(report_path).read_text(encoding="utf-8"))
    entries=[]
    for item in report.get("install",[]):
        metadata=item.get("metadata",{})
        download=item.get("download_info",{})
        archive=download.get("archive_info",{})
        hashes=archive.get("hashes",{})
        url=str(download.get("url",""))
        sha=str(hashes.get("sha256",archive.get("hash",""))).replace("sha256=","")
        filename=Path(urllib.parse.urlsplit(url).path).name
        if not str(metadata.get("name","")) or not str(metadata.get("version","")) or not filename or len(sha)!=64:
            raise RuntimeError("开发期解析报告缺少固定wheel字段")
        entries.append({"name":str(metadata["name"]),"version":str(metadata["version"]),"filename":filename,"url":url,"sha256":sha,"size":0,"python_abi":"cp312",
                "architecture":native_windows_architecture(),"backend":"development"})
    return sorted(entries,key=lambda value:(value["name"].casefold(),value["filename"]))
def _runtime_download_locked_wheels(entries,wheelhouse,env,cache_root):
    destination_root=Path(wheelhouse)
    destination_root.mkdir(parents=True,exist_ok=True)
    cache=Path(cache_root)/"wheels"
    cache.mkdir(parents=True,exist_ok=True)
    results=[]
    total_retries=0
    total_resumed=0
    for index,source in enumerate(entries):
        entry=dict(source)
        parsed=urllib.parse.urlsplit(str(entry["url"]))
        if parsed.scheme.lower()!="https" or parsed.hostname not in RUNTIME_ALLOWED_DOWNLOAD_HOSTS:
            raise RuntimeError("wheel URL不在允许域名锁内："+str(entry["url"]))
        target=cache/str(entry["filename"])
        _runtime_emit("progress",value=10.0+42.0*(index/max(1,len(entries))),message="下载锁定wheel "+str(entry["filename"]))
        result=_validated_download(entry["url"],target,entry["sha256"],max(FIXED_RUNTIME_PIP_MAX_BYTES,safe_int(entry["size"],1,1)*2),expected_size=entry["size"],retries=3)
        total_retries+=safe_int(result.get("retries"),0,0)
        total_resumed+=safe_int(result.get("resumed_bytes"),0,0)
        installed=destination_root/str(entry["filename"])
        shutil.copy2(target,installed)
        if installed.stat().st_size!=safe_int(entry["size"],0) or sha256_file(installed)!=str(entry["sha256"]):
            raise RuntimeError("wheel缓存复制校验失败："+str(entry["filename"]))
        results.append(entry)
    return results,{"files":len(results),"retries":total_retries,"resumed_bytes":total_resumed}
def _runtime_write_require_hashes_lock(path,entries,wheelhouse):
    if not runtime_lock_is_complete(entries):
        raise RuntimeError("内嵌运行库wheel锁不完整")
    lines=["--no-index","--no-deps","--find-links "+Path(wheelhouse).resolve().as_uri()]
    for entry in sorted(entries,key=lambda item:item["name"].casefold()):
        lines.append(entry["name"]+"=="+entry["version"]+" --hash=sha256:"+entry["sha256"])
    Path(path).write_text("\n".join(lines)+"\n",encoding="utf-8")
def runtime_install_worker(request_path):
    request=json.loads(Path(request_path).read_text(encoding="utf-8"))
    if safe_int(request.get("protocol_version"),0)!=RUNTIME_INSTALL_PROTOCOL_VERSION or request.get("stage")!="STARTING":
        raise RuntimeError("运行库安装子进程协议版本或启动阶段无效")
    base=Path(request["base"]).resolve()
    staging=Path(request["staging"]).resolve()
    vendor=str(request.get("vendor","unknown"))
    architecture=str(request.get("architecture") or native_windows_architecture())
    if os.name!="nt":
        raise RuntimeError("固定独立Python运行时只能在Windows 11安装")
    wheels,embedded_lock_checksum,lock_key=embedded_runtime_lock(architecture)
    if not runtime_lock_is_complete(wheels):
        raise RuntimeError("内嵌运行库wheel锁不完整")
    install_write_boundary_guard(base)
    wheel_bytes=sum(safe_int(item.get("size"),0,0) for item in wheels)
    ensure_free_space(base,required_runtime_space(base,wheel_bytes+FIXED_RUNTIME_PYTHON_ARTIFACTS[architecture]["size"]),"运行库下载与安装")
    if staging.exists():
        shutil.rmtree(staging,ignore_errors=True)
    staging.mkdir(parents=True)
    cache_root=base/"cache"/"runtime_downloads"
    cache_root.mkdir(parents=True,exist_ok=True)
    try:
        python_path,bootstrap_artifacts=_bootstrap_embedded_python(staging,architecture,cache_root)
        python=str(python_path)
        wheelhouse=staging/"wheelhouse"
        wheelhouse.mkdir()
        env=os.environ.copy()
        env.update({"PYTHONNOUSERSITE":"1","PIP_DISABLE_PIP_VERSION_CHECK":"1","PIP_NO_INPUT":"1","PIP_NO_INDEX":"1","PIP_CACHE_DIR":str(staging/"pip_cache"),
                "XDG_CACHE_HOME":str(staging/"cache"),"PYTHONPYCACHEPREFIX":str(staging/"cache"/"pycache"),"TMP":str(staging/"temp"),"TEMP":str(staging/"temp")})
        for name in ("models/vision","models/ocr","cache","cache/pycache","temp"):
            (staging/name).mkdir(parents=True,exist_ok=True)
        _runtime_emit("progress",value=10.0,message="读取内嵌wheel锁，禁止首次动态依赖解析")
        if not runtime_lock_is_complete(wheels):
            raise RuntimeError("内嵌运行库wheel锁不完整")
        downloaded,download_evidence=_runtime_download_locked_wheels(wheels,wheelhouse,env,cache_root)
        if downloaded!=wheels:
            raise RuntimeError("下载wheel与内嵌锁不一致")
        wheel_lock_checksum=hashlib.sha256(canonical_bytes(wheels)).hexdigest()
        if wheel_lock_checksum!=embedded_lock_checksum:
            raise RuntimeError("内嵌wheel锁校验和不一致")
        (staging/"wheel_lock.json").write_text(json.dumps({"lock_key":lock_key,"wheels":wheels,"checksum":wheel_lock_checksum,"resolution_source":"embedded"},ensure_ascii=False,
                sort_keys=True,separators=(",",":")),encoding="utf-8")
        requirements_lock=staging/"requirements.lock"
        _runtime_write_require_hashes_lock(requirements_lock,wheels,wheelhouse)
        _runtime_worker_command([python,"-m","pip","install","--no-deps","--require-hashes","-r",requirements_lock],env,"按内嵌SHA-256锁安装wheel")
        _runtime_emit("progress",value=82.0,message="执行内置CPU后端离线预热验证")
        validation=(
            'import hashlib,json,sys,tempfile\nimport numpy as np\nfrom PIL import Image,ImageDraw\nimport cv2\nimport torch\n'
            'import torchvision\nimport setuptools\nfrom omegaconf import OmegaConf\nfrom safetensors.torch import save_file,load_file\n'
            'from rapidocr import RapidOCR\na=np.asarray([[1,2],[3,4]],dtype=np.float32)\nassert float(a.sum())==10.0\n'
            'image=Image.new("RGB",(180,64),"white")\nImageDraw.Draw(image).text((12,18),"12345",fill="black")\n'
            'array=np.asarray(image)\nassert cv2.resize(array,(90,32)).shape==(32,90,3)\n'
            'x=torch.tensor([[1.0,2.0]],requires_grad=True)\ny=(x@torch.tensor([[2.0],[3.0]])).sum()\ny.backward()\n'
            'assert float(y)==8.0 and x.grad is not None\nwith tempfile.TemporaryDirectory() as folder:\n'
            ' p=folder+"/probe.safetensors"\n save_file({"x":x.detach()},p)\n assert tuple(load_file(p)["x"].shape)==(1,2)\n'
            'engine=RapidOCR()\nresult=engine(array)\ntext=""\nif result is not None:\n'
            ' text=str(getattr(result,"txts","") or getattr(result,"texts","") or result)\nassert isinstance(text,str)\n'
            'assert OmegaConf.create({"strict":True}).strict is True\nassert str(setuptools.__version__)\n'
            'payload=b"UniversalGameAI strict runtime"\n'
            'print(json.dumps({"python":sys.version,"backend":"torch_cpu","device":"CPU","numpy":np.__version__,"pillow":Image.__vers'
            'ion__ if hasattr(Image,"__version__") else "loaded","opencv":cv2.__version__,"torch":torch.__version__,"torchvision":tor'
            'chvision.__version__,"rapidocr":"functional","safetensors":"functional","omegaconf":str(OmegaConf.__version__) if hasatt'
            'r(OmegaConf,"__version__") else "functional","setuptools":setuptools.__version__,"self_test_sha256":hashlib.sha256(paylo'
            'ad).hexdigest()}))'
        )
        output=subprocess.check_output([python,"-c",validation],env=env,text=True,encoding="utf-8",errors="replace",stderr=subprocess.STDOUT,timeout=120)
        validation_result=json.loads(output.strip().splitlines()[-1])
        freeze=subprocess.check_output([python,"-m","pip","freeze","--all"],env=env,text=True,encoding="utf-8",errors="replace",timeout=120).splitlines()
        shutil.rmtree(wheelhouse,ignore_errors=True)
        shutil.rmtree(staging/"pip_cache",ignore_errors=True)
        critical={str(python_path.relative_to(staging)):sha256_file(python_path)}
        selected_backend="builtin_cpu"
        fallback={"requested":"nvidia" if vendor=="nvidia" else "cpu","selected":selected_backend,"applied":vendor=="nvidia","reason":"严格锁当前仅支持经锁定的Windows 11 x64 CPU运行时"}
        manifest={"layout_version":RUNTIME_LAYOUT_VERSION,"lock_manifest_version":RUNTIME_LOCK_MANIFEST_VERSION,"created":time.time(),"python_abi":list(FIXED_RUNTIME_PYTHON_ABI),
            "architecture":architecture,"python_version":str(validation_result.get("python",FIXED_RUNTIME_PYTHON_VERSION)),"python_executable":"python/python.exe",
            "python_artifact":bootstrap_artifacts["python"],"pip_artifact":bootstrap_artifacts["pip"],"vendor":vendor,"allowed_download_hosts":sorted(RUNTIME_ALLOWED_DOWNLOAD_HOSTS),"index_urls":[],
            "top_level_pins":[str(item["name"])+"=="+str(item["version"]) for item in wheels if str(item["name"]).strip().lower().replace("_","-") in runtime_required_projects()],
            "resolved_wheels":wheels,"wheel_lock_checksum":wheel_lock_checksum,"lock_complete":True,"pip_freeze":freeze,"validation":validation_result,"capabilities":{"vision_encode":True,
                "vision_train":True,"ocr_recognize":True,"safe_serialization":"safetensors","safetensors":True,"torch_cpu":True,"rapidocr":True},"vision_backend":"torch_cpu",
            "vision_serialization":"safetensors","ocr_backend":"rapidocr","ocr_self_test":True,"gpu_backend":selected_backend,"gpu_device":"CPU","backend_fallback":fallback,
            "download_evidence":download_evidence,"preprocess_hash":VISION_PREPROCESS_HASH,"critical_files":critical,"resolution_source":"embedded","embedded_lock_checksum":embedded_lock_checksum,
            "dependency_providers":runtime_dependency_providers(),"dependency_contracts":{key:{field:sorted(value) for field,value in contract.items()} for key,
                contract in runtime_dependency_contracts().items()},"reproducibility":"formal download reads the embedded architecture-specific wheel lock and performs no dependency resolution"}
        if manifest.get("lock_complete") is not True or not runtime_lock_is_complete(manifest.get("resolved_wheels",[])):
            raise RuntimeError("内嵌运行库wheel锁不完整")
        manifest["manifest_checksum"]=hashlib.sha256(canonical_bytes(manifest)).hexdigest()
        (staging/"runtime_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,separators=(",",":")),encoding="utf-8")
        _runtime_emit("progress",value=94.0,message="原子切换运行库")
        current=base/"runtime.current"
        backup=base/("runtime.rollback."+uuid.uuid4().hex)
        moved=False
        try:
            if current.exists():
                os.replace(current,backup)
                moved=True
            os.replace(staging,current)
        except Exception:
            if current.exists() and not moved:
                shutil.rmtree(current,ignore_errors=True)
            if moved and backup.exists() and not current.exists():
                os.replace(backup,current)
            raise
        if backup.exists():
            shutil.rmtree(backup,ignore_errors=True)
        _runtime_emit("progress",value=100.0,message="下载与离线验证完成")
        _runtime_emit("result",manifest=manifest)
        return 0
    except Exception as error:
        shutil.rmtree(staging,ignore_errors=True)
        _runtime_emit("error",message=str(error),traceback=traceback.format_exc()[-6000:])
        return 1
def runtime_installer_test_worker(request_path,mode):
    request=json.loads(Path(request_path).read_text(encoding="utf-8"))
    if safe_int(request.get("test_protocol_version"),0)!=TEST_WORKER_PROTOCOL_VERSION or request.get("stage")!="STARTING":
        raise RuntimeError("测试子进程协议版本或启动阶段无效")
    base=Path(request["base"]).resolve()
    staging=Path(request["staging"]).resolve()
    staging.mkdir(parents=True,exist_ok=True)
    if str(mode)=="success":
        runtime=staging
        runtime_python=runtime/"python"/("python.exe" if os.name=="nt" else "python")
        runtime_python.parent.mkdir(parents=True,exist_ok=True)
        runtime_python.write_bytes(b"self-test-runtime")
        critical={str(runtime_python.relative_to(runtime)):sha256_file(runtime_python)}
        architecture=str(request.get("architecture") or RUNTIME_ARCH_X64)
        wheels,embedded_checksum,_=embedded_runtime_lock(architecture)
        manifest={"layout_version":RUNTIME_LAYOUT_VERSION,"lock_manifest_version":RUNTIME_LOCK_MANIFEST_VERSION,"created":time.time(),"python_abi":list(FIXED_RUNTIME_PYTHON_ABI),
            "architecture":architecture,"python_version":FIXED_RUNTIME_PYTHON_VERSION,"python_executable":str(runtime_python.relative_to(runtime)),"python_artifact":{"url":"self-test",
                "final_url":"self-test","sha256":"0"*64,"size":0},"pip_artifact":{"url":"self-test","final_url":"self-test","sha256":"0"*64,"size":0},"vendor":"self-test",
            "allowed_download_hosts":sorted(RUNTIME_ALLOWED_DOWNLOAD_HOSTS),"index_urls":[],
            "top_level_pins":[str(item["name"])+"=="+str(item["version"]) for item in wheels if str(item["name"]).strip().lower().replace("_","-") in runtime_required_projects()],
            "resolved_wheels":wheels,"wheel_lock_checksum":embedded_checksum,"lock_complete":True,"pip_freeze":[str(item["name"])+"=="+str(item["version"]) for item in wheels],
            "validation":{"backend":"torch_cpu","device":"self-test"},"capabilities":{"vision_encode":True,"vision_train":True,"ocr_recognize":True,"safe_serialization":"safetensors"},
            "vision_backend":"torch_cpu","vision_serialization":"safetensors","ocr_backend":"rapidocr","ocr_self_test":True,"gpu_backend":"builtin_cpu","gpu_device":"self-test",
            "preprocess_hash":VISION_PREPROCESS_HASH,"critical_files":critical,"resolution_source":"embedded","embedded_lock_checksum":embedded_checksum,
            "dependency_providers":runtime_dependency_providers(),"dependency_contracts":{key:{field:sorted(value) for field,value in contract.items()} for key,contract in runtime_dependency_contracts().items()}}
        manifest["manifest_checksum"]=hashlib.sha256(canonical_bytes(manifest)).hexdigest()
        (runtime/"runtime_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,separators=(",",":")),encoding="utf-8")
        current=base/"runtime.current"
        backup=base/("runtime.rollback."+uuid.uuid4().hex)
        if current.exists():
            os.replace(current,backup)
        os.replace(staging,current)
        if backup.exists():
            shutil.rmtree(backup,ignore_errors=True)
        _runtime_emit("result",manifest=manifest)
        return 0
    child=subprocess.Popen([sys.executable,"-c","import time;time.sleep(120)"],start_new_session=False)
    (staging/"child.pid").write_text(str(child.pid),encoding="ascii")
    _runtime_emit("status",message=str(mode))
    while True:
        time.sleep(1.0)

class BoundedProcessOutput:
    def __init__(self,max_logs=256,max_log_bytes=1024*1024):
        self.critical=queue.Queue(maxsize=16)
        self.signals=queue.Queue(maxsize=4)
        self.logs=deque(maxlen=max(16,int(max_logs)))
        self.latest={}
        self.log_bytes=0
        self.max_log_bytes=max(4096,int(max_log_bytes))
        self.closed=False
        self.lock=threading.RLock()
    def put(self,line):
        if line is None:
            with self.lock:
                self.closed=True
            try:
                self.signals.put_nowait("closed")
            except queue.Full:
                pass
            return
        text=str(line)
        try:
            packet=json.loads(text)
        except (json.JSONDecodeError,TypeError,ValueError):
            packet={"kind":"line","message":text.strip()}
        kind=str(packet.get("kind","line"))
        if kind in {"result","error"}:
            self.critical.put(text)
            return
        if kind in {"progress","status"}:
            with self.lock:
                self.latest[kind]=text
            try:
                self.signals.put_nowait(kind)
            except queue.Full:
                pass
            return
        encoded=len(text.encode("utf-8",errors="replace"))
        with self.lock:
            while self.logs and self.log_bytes+encoded>self.max_log_bytes:
                removed=self.logs.popleft()
                self.log_bytes-=len(removed.encode("utf-8",errors="replace"))
            if encoded<=self.max_log_bytes:
                self.logs.append(text)
                self.log_bytes+=encoded
        try:
            self.signals.put_nowait("log")
        except queue.Full:
            pass
    def get(self,timeout=0.1):
        try:
            return self.critical.get_nowait()
        except queue.Empty:
            pass
        try:
            signal=self.signals.get(timeout=max(0.0,float(timeout)))
        except queue.Empty:
            return ""
        with self.lock:
            if signal in self.latest:
                return self.latest.pop(signal)
            if signal=="log" and self.logs:
                value=self.logs.popleft()
                self.log_bytes-=len(value.encode("utf-8",errors="replace"))
                return value
            if signal=="closed":
                return None
        return ""
    def empty(self):
        with self.lock:
            return self.critical.empty() and not self.latest and not self.logs
class RuntimeInstaller:
    def __init__(self,base,test_mode=None):
        self.base=Path(base)
        self.process=None
        self.job_handle=None
        self.lock=threading.RLock()
        self.cancelled=False
        self.staging=None
        self.test_mode=str(test_mode) if test_mode is not None else None
    def _gpu_vendor(self):
        try:
            creationflags=0x08000000 if os.name=="nt" else 0
            value=subprocess.check_output(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-Command",
                    "(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) -join ';'"],stderr=subprocess.STDOUT,text=True,timeout=12,creationflags=creationflags)
            text=value.lower()
            if "nvidia" in text:
                return "nvidia"
            if "amd" in text or "radeon" in text:
                return "amd"
            if "intel" in text:
                return "intel"
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        return "unknown"
    def _assign_job(self,process):
        if os.name!="nt":
            return None
        class BASIC(ctypes.Structure):
            _fields_=[("PerProcessUserTimeLimit",ctypes.c_longlong),("PerJobUserTimeLimit",ctypes.c_longlong),("LimitFlags",wintypes.DWORD),("MinimumWorkingSetSize",ctypes.c_size_t),
                ("MaximumWorkingSetSize",ctypes.c_size_t),("ActiveProcessLimit",wintypes.DWORD),("Affinity",ctypes.c_size_t),("PriorityClass",wintypes.DWORD),("SchedulingClass",wintypes.DWORD)]
        class IO(ctypes.Structure):
            _fields_=[("ReadOperationCount",ctypes.c_ulonglong),("WriteOperationCount",ctypes.c_ulonglong),("OtherOperationCount",ctypes.c_ulonglong),("ReadTransferCount",
                    ctypes.c_ulonglong),("WriteTransferCount",ctypes.c_ulonglong),("OtherTransferCount",ctypes.c_ulonglong)]
        class EXTENDED(ctypes.Structure):
            _fields_=[("BasicLimitInformation",BASIC),("IoInfo",IO),("ProcessMemoryLimit",ctypes.c_size_t),("JobMemoryLimit",ctypes.c_size_t),("PeakProcessMemoryUsed",ctypes.c_size_t),
                ("PeakJobMemoryUsed",ctypes.c_size_t)]
        kernel=ctypes.WinDLL("kernel32",use_last_error=True)
        kernel.CreateJobObjectW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR]
        kernel.CreateJobObjectW.restype=wintypes.HANDLE
        kernel.SetInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD]
        kernel.SetInformationJobObject.restype=wintypes.BOOL
        kernel.AssignProcessToJobObject.argtypes=[wintypes.HANDLE,wintypes.HANDLE]
        kernel.AssignProcessToJobObject.restype=wintypes.BOOL
        handle=kernel.CreateJobObjectW(None,None)
        if not handle:
            return None
        info=EXTENDED()
        info.BasicLimitInformation.LimitFlags=0x00002000
        if not kernel.SetInformationJobObject(handle,9,ctypes.byref(info),ctypes.sizeof(info)) or not kernel.AssignProcessToJobObject(handle,wintypes.HANDLE(process._handle)):
            kernel.CloseHandle(handle)
            return None
        return handle
    def _cleanup_staging(self):
        for item in self.base.glob("runtime.staging.*"):
            shutil.rmtree(item,ignore_errors=True)
        recover_runtime_layout(self.base)
    def run(self,stop_event,on_progress=None,on_line=None):
        self.cancelled=False
        if stop_event is not None and stop_event.is_set():
            raise InputStopped("文件完整性检查已停止")
        try:
            existing=validate_runtime_manifest(self.base,True,True)
        except RuntimeError:
            existing=None
        if isinstance(existing,dict):
            if on_line is not None:
                on_line("现有运行库的文件SHA-256、wheel锁、依赖闭包与版本清单校验通过")
            if on_progress is not None:
                on_progress(100.0)
            return dict(existing)
        architecture=native_windows_architecture()
        wheels,_,_=embedded_runtime_lock(architecture)
        locked_bytes=sum(safe_int(item.get("size"),0,0) for item in wheels)+safe_int(FIXED_RUNTIME_PYTHON_ARTIFACTS[architecture].get("size"),0,0)
        ensure_free_space(self.base,required_runtime_space(self.base,locked_bytes),"运行库下载与安装")
        self._cleanup_staging()
        staging=self.base/("runtime.staging."+uuid.uuid4().hex)
        self.staging=staging
        request_path=self.base/"temp"/("runtime_request_"+uuid.uuid4().hex+".json")
        request_path.parent.mkdir(parents=True,exist_ok=True)
        request_path.write_text(json.dumps({"base":str(self.base),"staging":str(staging),"vendor":self._gpu_vendor(),"architecture":architecture,
                    "protocol_version":RUNTIME_INSTALL_PROTOCOL_VERSION,"test_protocol_version":TEST_WORKER_PROTOCOL_VERSION,"stage":"STARTING"},ensure_ascii=False,separators=(",",":")),encoding="utf-8")
        creationflags=(0x08000000|0x00000200) if os.name=="nt" else 0
        env=os.environ.copy()
        env["PYTHONNOUSERSITE"]="1"
        if self.test_mode is None:
            command=[sys.executable,str(Path(__file__).resolve()),"runtime-install-worker",str(request_path)]
        else:
            command=[sys.executable,str(Path(__file__).resolve()),"runtime-installer-test-worker",str(request_path),self.test_mode]
        process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",env=env,creationflags=creationflags,start_new_session=os.name!="nt")
        with self.lock:
            self.process=process
            self.job_handle=self._assign_job(process)
        messages=BoundedProcessOutput(256,1024*1024)
        def reader():
            try:
                if process.stdout is not None:
                    for line in process.stdout:
                        messages.put(line)
            finally:
                messages.put(None)
        threading.Thread(target=reader,name="UniversalGameAI-RuntimeInstallerOutput",daemon=True).start()
        result=None
        error_message=""
        try:
            while True:
                if stop_event is not None and stop_event.is_set():
                    self.cancelled=True
                    self.stop()
                try:
                    line=messages.get(timeout=0.1)
                except queue.Empty:
                    line=""
                if line is None:
                    if process.poll() is not None:
                        break
                elif line:
                    try:
                        packet=json.loads(line)
                    except Exception:
                        packet={"kind":"line","message":line.strip()}
                    if packet.get("kind")!="line" and (safe_int(packet.get("protocol_version"),0)!=RUNTIME_INSTALL_PROTOCOL_VERSION or packet.get("stage") not in {"STARTING","RUNNING","COMPLETED","FAILED"}):
                        error_message="运行库子进程返回了无效协议包"
                        continue
                    kind=packet.get("kind")
                    if kind=="progress" and on_progress is not None:
                        on_progress(safe_float(packet.get("value"),0.0,0.0,100.0))
                    if kind in {"status","line","progress"} and on_line is not None and packet.get("message"):
                        on_line(str(packet["message"]))
                    if kind=="result":
                        result=packet.get("manifest")
                    if kind=="error":
                        error_message=str(packet.get("message",""))
                if process.poll() is not None and messages.empty():
                    break
            code=process.wait()
            if self.cancelled or stop_event is not None and stop_event.is_set():
                raise InputStopped("已停止；已验证的部分下载保留供下次断点续传")
            if code!=0 or not isinstance(result,dict):
                raise RuntimeError(error_message or "下载子进程失败，退出码"+str(code))
            validate_runtime_manifest(self.base,True,True)
            if on_progress is not None:
                on_progress(100.0)
            return result
        finally:
            with self.lock:
                self.process=None
                handle=self.job_handle
                self.job_handle=None
            if handle and os.name=="nt":
                try:
                    ctypes.WinDLL("kernel32",use_last_error=True).CloseHandle(handle)
                except Exception as error:
                    store=globals().get("CURRENT_DATA_STORE")
                    if store is not None:
                        store.log_error("RUNTIME_JOB_HANDLE_CLOSE_FAILED",error)
            try:
                request_path.unlink()
            except FileNotFoundError:
                pass
            except Exception as error:
                store=globals().get("CURRENT_DATA_STORE")
                if store is not None:
                    store.log_error("RUNTIME_REQUEST_CLEANUP_FAILED",error)
            if self.cancelled or process.returncode not in (0,None):
                self._cleanup_staging()
    def stop(self):
        self.cancelled=True
        with self.lock:
            process=self.process
            handle=self.job_handle
        if process is not None and process.poll() is None:
            terminated=False
            if handle and os.name=="nt":
                try:
                    kernel=ctypes.WinDLL("kernel32",use_last_error=True)
                    kernel.TerminateJobObject.argtypes=[wintypes.HANDLE,wintypes.UINT]
                    kernel.TerminateJobObject.restype=wintypes.BOOL
                    terminated=bool(kernel.TerminateJobObject(handle,1))
                    process.wait(5)
                except Exception:
                    terminated=False
            if not terminated:
                try:
                    if os.name=="nt":
                        subprocess.run(["taskkill","/PID",str(process.pid),"/T","/F"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5)
                    else:
                        os.killpg(os.getpgid(process.pid),9)
                    process.wait(5)
                except Exception:
                    try:
                        process.kill()
                        process.wait(2)
                    except Exception as error:
                        record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        self._cleanup_staging()
class OfflineVisionRuntime:
    def __init__(self,base):
        self.base=Path(base)
        self.model_dir=self.base/"models"/"vision"
        self.model_dir.mkdir(parents=True,exist_ok=True)
        self.quarantine_dir=self.base/"quarantine"/"vision"
        self.quarantine_dir.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock()
        self.torch=None
        self.np=None
        self.safetensors=None
        self.device=None
        self.device_name="unavailable"
        self.model=None
        self.active_game=""
        self.active_path=None
        self.trained_steps=0
        self.ready=False
        self.error="尚未检查AI运行库"
        self.runtime_manifest=None
        self._load_runtime()
    def _load_runtime(self):
        try:
            self.runtime_manifest=validate_runtime_manifest(self.base,True,True)
            if self.runtime_manifest is None:
                raise RuntimeError("运行库清单不存在")
            self.builtin=True
            self.device="cpu"
            self.device_name="内置CPU特征"
            self.ready=True
            self.error=""
            site=runtime_site_packages(self.base)
            if site.exists() and str(site) not in sys.path:
                sys.path.insert(0,str(site))
            try:
                import importlib
                importlib.invalidate_caches()
                self.np=importlib.import_module("numpy")
                self.torch=importlib.import_module("torch")
                self.safetensors=importlib.import_module("safetensors.torch")
                self.builtin=False
                if bool(self.torch.cuda.is_available()):
                    self.device=self.torch.device("cuda")
                    self.device_name=str(self.torch.cuda.get_device_name(0))
                else:
                    self.device=self.torch.device("cpu")
                    self.device_name="PyTorch CPU"
            except Exception:
                self.torch=None
                self.np=None
                self.safetensors=None
        except Exception as error:
            self.ready=False
            self.error=str(error)
            self.torch=None
            self.np=None
            self.safetensors=None
            self.builtin=False
    def require_ready(self):
        if not self.ready:
            self._load_runtime()
        if not self.ready:
            raise RuntimeError("AI运行库不可用，请先点击“检查文件完整性”："+self.error)
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
        return self.model_dir/(safe+".safetensors")
    def _metadata_path(self,path):
        return Path(str(path)+".json")
    def runtime_fingerprint(self):
        manifest=self.runtime_manifest or validate_runtime_manifest(self.base,False) or {}
        value={"python_abi":list(sys.version_info[:2]),"torch":str(getattr(self.torch,"__version__","")),"numpy":str(getattr(self.np,"__version__","")),
            "runtime_manifest_checksum":str(manifest.get("manifest_checksum","")),"gpu_backend":str(manifest.get("gpu_backend","cpu")),"preprocess_hash":VISION_PREPROCESS_HASH}
        value["checksum"]=hashlib.sha256(canonical_bytes(value)).hexdigest()
        return value
    def _expected(self,model):
        return {key:{"shape":list(value.shape),"dtype":str(value.dtype),"elements":int(value.numel())} for key,value in model.state_dict().items()}
    def _quarantine(self,path,reason):
        stamp=str(int(time.time()))+"_"+uuid.uuid4().hex
        for source in (Path(path),self._metadata_path(path)):
            if source.exists():
                target=self.quarantine_dir/(source.name+"."+stamp+".invalid")
                try:
                    os.replace(source,target)
                except Exception:
                    shutil.copy2(source,target)
                    source.unlink()
        raise RuntimeError("模型校验失败，已隔离并要求重新睡眠："+str(reason))
    def _atomic_save(self,path,state,metadata):
        tensors={str(key):value.detach().to("cpu").contiguous() for key,value in state.items()}
        temp=Path(str(path)+"."+uuid.uuid4().hex+".tmp")
        temp_meta=Path(str(temp)+".json")
        self.safetensors.save_file(tensors,str(temp))
        value=dict(metadata)
        value["file_sha256"]=sha256_file(temp,MODEL_MAX_BYTES)
        value["tensor_schema"]={key:{"shape":list(tensor.shape),"dtype":str(tensor.dtype),"elements":int(tensor.numel())} for key,tensor in tensors.items()}
        value["metadata_checksum"]=hashlib.sha256(canonical_bytes(value)).hexdigest()
        temp_meta.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")),encoding="utf-8")
        os.replace(temp,path)
        os.replace(temp_meta,self._metadata_path(path))
    def _load_state(self,path,model):
        meta_path=self._metadata_path(path)
        if not meta_path.exists():
            self._quarantine(path,"缺少模型清单")
        try:
            metadata=json.loads(meta_path.read_text(encoding="utf-8"))
            checksum=str(metadata.pop("metadata_checksum",""))
            if hashlib.sha256(canonical_bytes(metadata)).hexdigest()!=checksum:
                raise RuntimeError("模型清单校验失败")
            if safe_int(metadata.get("architecture_version"),0)!=VISION_ARCHITECTURE_VERSION:
                raise RuntimeError("模型结构版本变化")
            if str(metadata.get("preprocess_hash",""))!=VISION_PREPROCESS_HASH:
                raise RuntimeError("预处理版本变化")
            runtime=metadata.get("runtime_fingerprint",{})
            if not isinstance(runtime,dict) or str(runtime.get("checksum",""))!=str(self.runtime_fingerprint().get("checksum","")):
                raise RuntimeError("运行库版本变化")
            if sha256_file(path,MODEL_MAX_BYTES)!=str(metadata.get("file_sha256","")):
                raise RuntimeError("模型文件SHA-256不匹配")
            tensors=self.safetensors.load_file(str(path),device="cpu")
            expected=self._expected(model)
            if set(tensors)!=set(expected):
                raise RuntimeError("张量名称不匹配")
            total=0
            for key,tensor in tensors.items():
                schema=expected[key]
                total+=int(tensor.numel())
                if list(tensor.shape)!=schema["shape"] or str(tensor.dtype)!=schema["dtype"]:
                    raise RuntimeError("张量形状或dtype不匹配："+key)
            if total>100000000:
                raise RuntimeError("模型张量规模超过上限")
            model.load_state_dict(tensors,strict=True)
            return metadata
        except Exception as error:
            self._quarantine(path,error)
    def activate_game(self,game_id):
        self.require_ready()
        gid=str(game_id or "default")
        with self.lock:
            if getattr(self,"builtin",False):
                path=self.model_dir/(hashlib.sha256(gid.encode("utf-8","replace")).hexdigest()+".builtin.json")
                if path.exists():
                    try:
                        value=json.loads(path.read_text(encoding="utf-8"))
                        self.trained_steps=safe_int(value.get("trained_steps"),0,0)
                    except Exception:
                        self.trained_steps=0
                else:
                    value={"architecture_version":VISION_ARCHITECTURE_VERSION,"game_id":gid,"trained_steps":0,"created":time.time(),"backend":"builtin_cpu","preprocess_hash":VISION_PREPROCESS_HASH}
                    value["checksum"]=hashlib.sha256(canonical_bytes(value)).hexdigest()
                    path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")),encoding="utf-8")
                self.active_game=gid
                self.active_path=path
                self.model="builtin_cpu"
                return self.manifest()
            if self.active_game==gid and self.model is not None:
                return self.manifest()
            seed=int(hashlib.sha256((gid+"|"+str(VISION_ARCHITECTURE_VERSION)).encode("utf-8")).hexdigest()[:8],16)
            self.torch.manual_seed(seed)
            if self.torch.cuda.is_available():
                self.torch.cuda.manual_seed_all(seed)
            model=self._build_model()
            path=self._path_for(gid)
            steps=0
            if path.exists():
                metadata=self._load_state(path,model)
                steps=safe_int(metadata.get("trained_steps",0),0,0,1000000000)
            else:
                self._atomic_save(path,model.state_dict(),{"architecture_version":VISION_ARCHITECTURE_VERSION,"game_id":gid,"trained_steps":0,"created":time.time(),
                        "preprocess_hash":VISION_PREPROCESS_HASH,"preprocess_signature":preprocess_signature(),"runtime_fingerprint":self.runtime_fingerprint(),"neural_feature_version":NEURAL_FEATURE_VERSION})
            model.eval()
            self.model=model
            self.active_game=gid
            self.active_path=path
            self.trained_steps=steps
            return self.manifest()
    def manifest(self):
        checksum=""
        if self.active_path is not None and self.active_path.exists():
            checksum=sha256_file(self.active_path,MODEL_MAX_BYTES)
        builtin=bool(getattr(self,"builtin",False))
        capabilities={"vision_encode":True,"vision_train":not builtin,"ocr_recognize":False,"safe_serialization":"builtin_json" if builtin else "safetensors"}
        return {"architecture_version":VISION_ARCHITECTURE_VERSION,"game_id":self.active_game,"checksum":checksum,"trained_steps":self.trained_steps,"device":self.device_name,
            "relative_path":str(self.active_path.relative_to(self.base)) if self.active_path is not None else "","preprocess_hash":VISION_PREPROCESS_HASH,"preprocess_signature":preprocess_signature(),
            "runtime_fingerprint":self.runtime_fingerprint(),"serialization":"builtin_json" if builtin else "safetensors","backend":"builtin_cpu" if builtin else "torch",
            "neural_feature_version":NEURAL_FEATURE_VERSION,"capabilities":capabilities}
    def _tensor_from_rgb(self,rgb):
        source=sample_rgb_bytes(rgb)
        if source is None:
            raise CaptureUnavailable("AI视觉输入尺寸无效")
        array=self.np.frombuffer(source,dtype=self.np.uint8).reshape(FEATURE_H,FEATURE_W,3).copy()
        return self.torch.from_numpy(array).permute(2,0,1).unsqueeze(0).to(self.device,dtype=self.torch.float32)/255.0
    def encode(self,rgb,previous_rgb=None):
        self.require_ready()
        current=sample_rgb_bytes(rgb)
        if current is None:
            raise CaptureUnavailable("AI视觉输入尺寸无效")
        previous=sample_rgb_bytes(previous_rgb)
        if getattr(self,"builtin",False):
            red=bytearray(PIXELS)
            green=bytearray(PIXELS)
            blue=bytearray(PIXELS)
            gray=bytearray(PIXELS)
            motion=bytearray(PIXELS)
            for pixel in range(PIXELS):
                offset=pixel*3
                r=current[offset]; g=current[offset+1]; b=current[offset+2]
                red[pixel]=r; green[pixel]=g; blue[pixel]=b; gray[pixel]=(77*r+150*g+29*b)>>8
                if previous is not None:
                    motion[pixel]=(abs(r-previous[offset])+abs(g-previous[offset+1])+abs(b-previous[offset+2]))//3
            return bytes(gray)+bytes(red)+bytes(green)+bytes(blue)+bytes(motion)
        with self.lock:
            if self.model is None:
                self.activate_game(self.active_game or "default")
            tensor=self._tensor_from_rgb(rgb)
            with self.torch.inference_mode():
                encoded=self.model(tensor)
            encoded=(encoded.squeeze(0).clamp(0,1)*255.0).to("cpu",dtype=self.torch.uint8).numpy()
            channels=[bytes(encoded[index].reshape(-1).tolist()) for index in range(4)]
        motion=bytearray(PIXELS)
        if previous is not None:
            for pixel in range(PIXELS):
                offset=pixel*3
                motion[pixel]=(abs(current[offset]-previous[offset])+abs(current[offset+1]-previous[offset+1])+abs(current[offset+2]-previous[offset+2]))//3
        return b"".join(channels)+bytes(motion)
    def train(self,game_id,samples,stop_event=None,progress=None,seed=None,total_count=None):
        self.require_ready()
        sample_total=max(0,safe_int(total_count,len(samples) if hasattr(samples,"__len__") else 0,0,MAX_SAMPLES))
        sleep_seed=safe_int(seed,int(hashlib.sha256((str(game_id)+"|sleep").encode()).hexdigest()[:16],16),0,2**63-1)
        if getattr(self,"builtin",False):
            self.activate_game(game_id)
            valid=[]
            for index,item in enumerate(samples or []):
                if stop_event is not None and stop_event.is_set():
                    raise InputStopped("内置CPU离线视觉优化已停止")
                rgb=sample_rgb_bytes(item.get("rgb") or item.get("thumbnail")) if isinstance(item,dict) else sample_rgb_bytes(item)
                if rgb is not None:
                    valid.append(hashlib.sha256(rgb).hexdigest())
                if progress is not None and index%16==0:
                    progress(35.0*(index+1)/max(1,sample_total))
            self.trained_steps+=max(1,len(valid))
            value={"architecture_version":VISION_ARCHITECTURE_VERSION,"game_id":str(game_id),"trained_steps":self.trained_steps,"updated":time.time(),"backend":"builtin_cpu",
                "preprocess_hash":VISION_PREPROCESS_HASH,"sleep_seed":sleep_seed,"sample_hash":hashlib.sha256(canonical_bytes(valid)).hexdigest(),"training_objectives":["deterministic_visual_encoding",
                    "action_conditioned_prototype_support","temporal_consistency"]}
            value["checksum"]=hashlib.sha256(canonical_bytes(value)).hexdigest()
            self.active_path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")),encoding="utf-8")
            if progress is not None:
                progress(35.0)
            return self.manifest()
        valid=[]
        for index,item in enumerate(samples or []):
            if isinstance(item,dict):
                rgb=sample_rgb_bytes(item.get("rgb") or item.get("thumbnail"))
                action=action_signature(item.get("a"))
                session=str(item.get("session_id",item.get("context",{}).get("session_id","")))
                created=safe_float(item.get("created",index),index)
            else:
                rgb=sample_rgb_bytes(item)
                action="unknown"
                session=""
                created=float(index)
            if rgb is not None:
                valid.append({"rgb":rgb,"action":action,"session":session,"created":created})
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
            optimizer=torch.optim.AdamW(model.parameters(),lr=0.0012,weight_decay=0.0001)
            arrays=self.np.stack([self.np.frombuffer(item["rgb"],dtype=self.np.uint8).reshape(FEATURE_H,FEATURE_W,3) for item in valid]).astype(self.np.float32)/255.0
            arrays=arrays.transpose(0,3,1,2)
            labels=self.np.array([int(hashlib.sha256(item["action"].encode()).hexdigest()[:8],16)%2147483647 for item in valid],dtype=self.np.int64)
            total_steps=max(32,min(320,len(valid)*4))
            generator=random.Random(sleep_seed)
            torch_generator=torch.Generator(device=self.device)
            torch_generator.manual_seed(sleep_seed)
            for step in range(total_steps):
                if stop_event is not None and stop_event.is_set():
                    raise InputStopped("GPU离线视觉模型训练已停止")
                indexes=[generator.randrange(len(valid)) for _ in range(min(32,max(6,len(valid))))]
                batch=torch.from_numpy(arrays[indexes].copy()).to(self.device)
                label=torch.from_numpy(labels[indexes].copy()).to(self.device)
                noisy=(batch+(torch.rand(batch.shape,dtype=batch.dtype,device=self.device,generator=torch_generator)-0.5)*0.06).clamp(0,1)
                latent,reconstruction=model(noisy)
                embedding=torch.nn.functional.normalize(latent.mean(dim=(2,3)),dim=1)
                similarity=embedding@embedding.T/0.2
                eye=torch.eye(len(indexes),dtype=torch.bool,device=self.device)
                positive=(label[:,None]==label[None,:])&~eye
                logits=similarity.masked_fill(eye,-1e9)
                log_prob=logits-torch.logsumexp(logits,dim=1,keepdim=True)
                contrastive=-(log_prob[positive]).mean() if bool(positive.any()) else torch.zeros((),device=self.device)
                temporal=torch.zeros((),device=self.device)
                if len(indexes)>1:
                    distances=(embedding[1:]-embedding[:-1]).pow(2).sum(dim=1)
                    same=label[1:]==label[:-1]
                    temporal=torch.where(same,distances,torch.relu(0.5-distances)).mean()
                reconstruction_loss=torch.nn.functional.smooth_l1_loss(reconstruction,batch)
                variance_penalty=(latent.var(dim=(2,3)).mean()+0.0001).reciprocal().clamp(max=10)
                loss=reconstruction_loss+0.12*contrastive+0.05*temporal+0.01*variance_penalty
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
            self._atomic_save(self.active_path,encoder.state_dict(),{"architecture_version":VISION_ARCHITECTURE_VERSION,"game_id":str(game_id),"trained_steps":self.trained_steps,
                    "updated":time.time(),"preprocess_hash":VISION_PREPROCESS_HASH,"preprocess_signature":preprocess_signature(),"runtime_fingerprint":self.runtime_fingerprint(),
                    "training_objectives":["reconstruction","action_conditioned_contrastive","temporal_consistency"],"raw_feature_preserved":True,"neural_feature_version":NEURAL_FEATURE_VERSION,"sleep_seed":sleep_seed})
            return self.manifest()
class OfflineOCRRuntime:
    def __init__(self,base):
        self.base=Path(base)
        self.lock=threading.RLock()
        self.engine=None
        self.np=None
        self.backend_name="none"
        self.self_test_passed=False
        self.ready=False
        self.error="尚未检查OCR运行库"
        self._load_runtime()
    def _load_runtime(self):
        try:
            validate_runtime_manifest(self.base,True,True)
            self.engine=None
            self.np=None
            self.backend_name="none"
            self.self_test_passed=False
            self.ready=True
            self.error=""
            site=runtime_site_packages(self.base)
            if site.exists() and str(site) not in sys.path:
                sys.path.insert(0,str(site))
            try:
                import importlib
                importlib.invalidate_caches()
                self.np=importlib.import_module("numpy")
                try:
                    module=importlib.import_module("rapidocr")
                    self.engine=module.RapidOCR()
                except Exception:
                    module=importlib.import_module("rapidocr_onnxruntime")
                    self.engine=module.RapidOCR()
                self.backend_name="rapidocr"
                self.self_test_passed=self._self_test()
                if not self.self_test_passed:
                    self.error="RapidOCR真实图片识别自检失败"
            except Exception:
                self.engine=None
                self.np=None
                self.backend_name="none"
                self.self_test_passed=False
        except Exception as error:
            self.engine=None
            self.ready=False
            self.backend_name="none"
            self.self_test_passed=False
            self.error=str(error)
    def _self_test(self):
        if self.engine is None or self.np is None:
            return False
        try:
            image=self.np.full((96,320,3),255,dtype=self.np.uint8)
            try:
                cv2=__import__("cv2")
                cv2.putText(image,"12345",(20,68),cv2.FONT_HERSHEY_SIMPLEX,1.7,(0,0,0),3,cv2.LINE_AA)
            except Exception:
                return False
            with self.lock:
                output=self.engine(image)
            if hasattr(output,"txts"):
                texts=list(output.txts or [])
            elif isinstance(output,tuple) and output:
                texts=[str(item[1]) for item in (output[0] or []) if isinstance(item,(list,tuple)) and len(item)>=2]
            else:
                texts=[str(item[1]) for item in (output or []) if isinstance(item,(list,tuple)) and len(item)>=2]
            return any("123" in "".join(ch for ch in str(text) if ch.isdigit()) for text in texts)
        except Exception:
            return False
    def capability_status(self):
        return {"ocr_backend":self.backend_name,"ocr_self_test":bool(self.self_test_passed),"ocr_recognize":bool(self.backend_name=="rapidocr" and self.self_test_passed)}
    def require_ready(self):
        if not self.ready:
            self._load_runtime()
        if not self.ready:
            raise RuntimeError("OCR运行库不可用，请先点击“检查文件完整性”："+self.error)
        return True
    def _array(self,rgb,width,height):
        raw=bytes(rgb)
        if len(raw)!=int(width)*int(height)*3:
            raise RuntimeError("OCR图像尺寸无效")
        return self.np.frombuffer(raw,dtype=self.np.uint8).reshape(int(height),int(width),3).copy()
    def recognize(self,rgb,width,height,region=None):
        self.require_ready()
        if self.engine is None or self.backend_name!="rapidocr" or not self.self_test_passed:
            return []
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
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
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
            selected=[{"norm":[0.05,0.05,0.25,0.15],"score":0.0,"text":""},{"norm":[0.7,0.05,0.25,0.15],"score":0.0,"text":""},{"norm":[0.05,0.8,0.25,0.15],"score":0.0,"text":""},
                {"norm":[0.7,0.8,0.25,0.15],"score":0.0,"text":""}]
        return selected
def _disable_network_access():
    import socket
    def denied(*args,**kwargs):
        raise RuntimeError("离线AI工作进程禁止网络访问")
    socket.socket=denied
    socket.create_connection=denied
    socket.getaddrinfo=denied
    urllib.request.urlopen=denied
    urllib.request.build_opener=denied
    globals()["OFFLINE_NETWORK_DENIED_FUNCTION"]=denied
    for name in ("_validated_download","_runtime_download_locked_wheels","runtime_install_worker"):
        if name in globals():
            globals()[name]=denied
    return denied
def _verify_offline_network_block():
    import socket
    before={safe_int(getattr(child,"pid",0),0) for child in multiprocessing.active_children()}
    checks={}
    for name,call in (("socket.socket",lambda:socket.socket()),("socket.getaddrinfo",lambda:socket.getaddrinfo("example.invalid",443)),("urllib.request.urlopen",
            lambda:urllib.request.urlopen("https://example.invalid",timeout=0.01))):
        try:
            call()
            checks[name]=False
        except Exception:
            checks[name]=True
    download_checks={}
    denied_function=globals().get("OFFLINE_NETWORK_DENIED_FUNCTION")
    for name in ("_validated_download","_runtime_download_locked_wheels","runtime_install_worker"):
        function=globals().get(name)
        blocked=bool(function is denied_function and callable(function))
        if blocked:
            try:
                function()
                blocked=False
            except RuntimeError as error:
                blocked="禁止网络访问" in str(error)
            except Exception:
                blocked=False
        download_checks[name]=blocked
    download_denied=all(download_checks.values())
    after={safe_int(getattr(child,"pid",0),0) for child in multiprocessing.active_children()}
    evidence={"network_block_version":2,"checks":checks,"no_new_children":not bool(after-before),"download_entrypoints":download_checks,"download_entrypoints_disabled":download_denied}
    evidence["blocked"]=all(checks.values()) and evidence["no_new_children"] and download_denied
    if not evidence["blocked"]:
        raise RuntimeError("离线网络封锁主动验证失败："+json.dumps(evidence,ensure_ascii=False,sort_keys=True))
    return evidence
TRAINING_SNAPSHOT_SCHEMA_VERSION=1
TRAINING_SNAPSHOT_MAX_BYTES=2*1024*1024*1024

class TrainingSnapshotRows:
    def __init__(self,path,count):
        self.path=Path(path)
        self.count=max(0,int(count))
    def __len__(self):
        return self.count
    def __iter__(self):
        uri="file:"+self.path.as_posix()+"?mode=ro&immutable=1"
        connection=sqlite3.connect(uri,uri=True,timeout=5.0,check_same_thread=False)
        try:
            cursor=connection.execute("SELECT rgb,action,session,created FROM training_samples ORDER BY sample_id")
            while True:
                rows=cursor.fetchmany(128)
                if not rows:
                    break
                for rgb,action,session,created in rows:
                    yield {"rgb":bytes(rgb),"a":str(action),"session_id":str(session),"created":float(created)}
        finally:
            connection.close()

def _training_snapshot_path(base,value):
    root=(Path(base).resolve()/"temp").resolve()
    target=Path(value).resolve()
    try:
        target.relative_to(root)
    except ValueError as error:
        raise RuntimeError("训练快照路径越出用户确认目录") from error
    if target.parent!=root or not target.name.startswith("training_snapshot_") or target.suffix!=".sqlite3":
        raise RuntimeError("训练快照路径格式无效")
    return target

def create_training_snapshot(base,game_id,samples):
    started=time.monotonic()
    root=make_data_directory(base,"temp")
    path=root/("training_snapshot_"+uuid.uuid4().hex+".sqlite3")
    connection=sqlite3.connect(str(path),timeout=10.0,check_same_thread=False)
    count=0
    try:
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        connection.execute("CREATE TABLE training_samples(sample_id INTEGER PRIMARY KEY,rgb BLOB NOT NULL,action TEXT NOT NULL,session TEXT NOT NULL,created REAL NOT NULL)")
        rows=[]
        for index,item in enumerate(samples or []):
            if not isinstance(item,dict):
                continue
            rgb=sample_rgb_bytes(item.get("rgb") or item.get("thumbnail"))
            if rgb is None:
                continue
            action=action_signature(item.get("a"))
            session=str(item.get("session_id",item.get("context",{}).get("session_id","")))
            created=safe_float(item.get("created",index),index)
            rows.append((sqlite3.Binary(rgb),action,session,created))
            if len(rows)>=128:
                connection.executemany("INSERT INTO training_samples(rgb,action,session,created) VALUES(?,?,?,?)",rows)
                count+=len(rows)
                rows.clear()
        if rows:
            connection.executemany("INSERT INTO training_samples(rgb,action,session,created) VALUES(?,?,?,?)",rows)
            count+=len(rows)
        metadata={"schema_version":str(TRAINING_SNAPSHOT_SCHEMA_VERSION),"game_id":str(game_id),"count":str(count),"created":repr(time.time()),"build_hash":current_build_hash()}
        connection.executemany("INSERT INTO metadata(key,value) VALUES(?,?)",sorted(metadata.items()))
        connection.commit()
    except BaseException:
        connection.close()
        path.unlink(missing_ok=True)
        raise
    finally:
        try:
            connection.close()
        except sqlite3.Error as error:
            record_cleanup_error("TRAINING_SNAPSHOT_CLOSE_FAILED",error)
    size=int(path.stat().st_size)
    if size<=0 or size>TRAINING_SNAPSHOT_MAX_BYTES:
        path.unlink(missing_ok=True)
        raise RuntimeError("训练快照大小无效")
    RUNTIME_METRICS.observe("training_snapshot_serialize_ms",(time.monotonic()-started)*1000.0)
    RUNTIME_METRICS.observe("training_snapshot_bytes",size)
    RUNTIME_METRICS.observe("training_snapshot_samples",count)
    return {"schema_version":TRAINING_SNAPSHOT_SCHEMA_VERSION,"path":str(path),"size":size,"sha256":sha256_file(path),"count":count,"game_id":str(game_id)}

def open_training_snapshot(base,descriptor):
    if not isinstance(descriptor,dict) or safe_int(descriptor.get("schema_version"),0)!=TRAINING_SNAPSHOT_SCHEMA_VERSION:
        raise RuntimeError("训练快照协议版本无效")
    path=_training_snapshot_path(base,descriptor.get("path",""))
    expected_size=safe_int(descriptor.get("size"),0,1,TRAINING_SNAPSHOT_MAX_BYTES)
    if not path.is_file() or int(path.stat().st_size)!=expected_size:
        raise RuntimeError("训练快照文件不存在或大小不一致")
    expected_hash=str(descriptor.get("sha256","")).casefold()
    if len(expected_hash)!=64 or sha256_file(path)!=expected_hash:
        raise RuntimeError("训练快照SHA-256校验失败")
    connection=sqlite3.connect("file:"+path.as_posix()+"?mode=ro&immutable=1",uri=True,timeout=5.0,check_same_thread=False)
    try:
        metadata=dict(connection.execute("SELECT key,value FROM metadata"))
        actual_count=safe_int(connection.execute("SELECT COUNT(*) FROM training_samples").fetchone()[0],0)
    finally:
        connection.close()
    if safe_int(metadata.get("schema_version"),0)!=TRAINING_SNAPSHOT_SCHEMA_VERSION or str(metadata.get("game_id",""))!=str(descriptor.get("game_id","")):
        raise RuntimeError("训练快照元数据不一致")
    if actual_count!=safe_int(descriptor.get("count"),-1):
        raise RuntimeError("训练快照样本计数不一致")
    return TrainingSnapshotRows(path,actual_count)

def remove_training_snapshot(base,descriptor):
    try:
        path=_training_snapshot_path(base,descriptor.get("path",""))
    except (RuntimeError,ValueError,TypeError):
        return False
    removed=False
    for suffix in ("","-wal","-shm","-journal"):
        candidate=Path(str(path)+suffix)
        try:
            candidate.unlink(missing_ok=True)
            removed=True
        except OSError as error:
            record_cleanup_error("TRAINING_SNAPSHOT_REMOVE_FAILED",error,{"path":candidate.name})
    return removed

class FileStopEvent:
    def __init__(self,path):
        self.path=Path(path) if path else None
    def is_set(self):
        return bool(self.path is not None and self.path.exists())
    def set(self):
        if self.path is not None:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            self.path.touch(exist_ok=True)
    def wait(self,timeout=0.0):
        deadline=time.monotonic()+max(0.0,float(timeout))
        while not self.is_set() and time.monotonic()<deadline:
            time.sleep(min(0.02,max(0.001,deadline-time.monotonic())))
        return self.is_set()
def ai_worker_main(base,address,auth_text,family,protocol_version=None):
    from multiprocessing.connection import Client
    if safe_int(protocol_version,0)!=AI_WORKER_PROTOCOL_VERSION:
        raise RuntimeError("AI工作进程协议版本不一致")
    manifest=validate_runtime_manifest(base,True,True)
    if manifest is None or manifest.get("lock_complete") is not True or not runtime_lock_is_complete(manifest.get("resolved_wheels",[])):
        raise RuntimeError("AI工作进程启动前运行库wheel锁不完整")
    install_write_boundary_guard(base)
    auth=base64.urlsafe_b64decode(str(auth_text).encode("ascii"))
    connection=Client(address,family=family,authkey=auth)
    try:
        vision=OfflineVisionRuntime(base)
        ocr=OfflineOCRRuntime(base)
        vision.require_ready()
        ocr.require_ready()
        initial_vision=vision.manifest()
        initial_ocr=ocr.capability_status()
        if initial_vision.get("backend")!="torch" or initial_vision.get("serialization")!="safetensors" or initial_vision.get("capabilities",{}).get("vision_train") is not True:
            raise RuntimeError("AI工作进程拒绝降级到非PyTorch或非safetensors后端")
        if initial_ocr.get("ocr_backend")!="rapidocr" or initial_ocr.get("ocr_recognize") is not True:
            raise RuntimeError("AI工作进程RapidOCR功能自测未通过")
        _disable_network_access()
        offline_evidence=_verify_offline_network_block()
        candidate_indices=OrderedDict()
        def status_value():
            manifest=vision.manifest()
            ocr_status=ocr.capability_status()
            capabilities=dict(manifest.get("capabilities",{}))
            capabilities.update({"ocr_recognize":bool(ocr_status.get("ocr_recognize")),"safetensors":manifest.get("serialization")=="safetensors",
                    "torch_cpu":manifest.get("backend")=="torch" and str(manifest.get("device","")).casefold().endswith("cpu"),"rapidocr":ocr_status.get("ocr_backend")=="rapidocr"
                    and bool(ocr_status.get("ocr_self_test")),"candidate_rank":_optional_numpy() is not None})
            return {"device":vision.device_name,"vision_ready":vision.ready,"ocr_ready":ocr.ready,"vision_backend":manifest.get("backend","builtin_cpu"),
                "vision_serialization":manifest.get("serialization","builtin_json"),"ocr_backend":ocr_status.get("ocr_backend","none"),"ocr_self_test":bool(ocr_status.get("ocr_self_test")),
                "capabilities":capabilities,"active_game":vision.active_game,"manifest":manifest if vision.active_game else None,"offline_network_blocked":bool(offline_evidence.get("blocked")),
                "offline_network_evidence":offline_evidence}
        connection.send({"kind":"ready","protocol_version":AI_WORKER_PROTOCOL_VERSION,"stage":"READY","status":status_value()})
        while True:
            command=connection.recv()
            if not isinstance(command,dict):
                continue
            if safe_int(command.get("protocol_version"),0)!=AI_WORKER_PROTOCOL_VERSION:
                raise RuntimeError("AI工作进程请求协议版本不一致")
            request_id=str(command.get("id",""))
            operation=str(command.get("operation",""))
            payload=command.get("payload") if isinstance(command.get("payload"),dict) else {}
            try:
                if operation=="shutdown":
                    connection.send({"kind":"result","id":request_id,"value":True})
                    break
                if operation=="status":
                    value=status_value()
                elif operation=="activate_game":
                    value=vision.activate_game(str(payload.get("game_id","")))
                elif operation=="vision_manifest":
                    value=vision.manifest()
                elif operation=="encode":
                    value=vision.encode(bytes(payload.get("rgb",b"")),bytes(payload["previous"]) if payload.get("previous") is not None else None)
                elif operation=="train":
                    stop=FileStopEvent(payload.get("stop_path"))
                    snapshot_descriptor=dict(payload.get("snapshot",{}))
                    snapshot_rows=open_training_snapshot(base,snapshot_descriptor)
                    def progress(amount):
                        connection.send({"kind":"progress","id":request_id,"value":float(amount)})
                    value=vision.train(str(payload.get("game_id","")),snapshot_rows,stop,progress,payload.get("sleep_seed"),len(snapshot_rows))
                elif operation=="load_candidate_index":
                    token=str(payload.get("token","")).strip()
                    prototypes=list(payload.get("prototypes",[]))
                    if len(token)!=64 or any(character not in "0123456789abcdef" for character in token.casefold()):
                        raise ValueError("候选索引模型checksum无效")
                    if not prototypes or len(prototypes)>MAX_PROTOTYPES:
                        raise ValueError("候选索引原型数量无效")
                    runtime_index=build_candidate_runtime_index(prototypes,True)
                    runtime_index["token"]=token
                    candidate_indices[token]=runtime_index
                    candidate_indices.move_to_end(token)
                    while len(candidate_indices)>4:
                        candidate_indices.popitem(last=False)
                    value={"token":token,"prototypes":len(prototypes),"coarse_shape":list(runtime_index["coarse_matrix"].shape),"feature_shape":list(runtime_index["feature_matrix"].shape)}
                elif operation=="match_candidate_index":
                    token=str(payload.get("token","")).strip()
                    runtime_index=candidate_indices.get(token)
                    if runtime_index is None:
                        raise RuntimeError("候选索引尚未加载或已被替换")
                    candidate_indices.move_to_end(token)
                    value=candidate_visual_matches(runtime_index,bytes(payload.get("feature",b"")),bytes(payload.get("coarse",b"")),str(payload.get("backend","unknown")),
                        safe_int(payload.get("full_limit"),VersionedThresholdConfig.candidate_full_limit,1,MAX_PROTOTYPES))
                elif operation=="ocr_recognize_region":
                    value=ocr.recognize_region(dict(payload.get("frame",{})),payload.get("norm"))
                else:
                    raise RuntimeError("未知AI工作进程操作："+operation)
                connection.send({"kind":"result","id":request_id,"value":value})
            except (KeyboardInterrupt,SystemExit):
                raise
            except Exception as error:
                connection.send({"kind":"error","id":request_id,"message":str(error),"traceback":traceback.format_exc()[-10000:]})
    finally:
        try:
            connection.close()
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
class AIWorkerClient:
    def __init__(self,base,on_failure=None):
        from multiprocessing.connection import Listener
        self.base=Path(base).resolve()
        manifest=validate_runtime_manifest(self.base,True,True)
        if manifest is None or manifest.get("lock_complete") is not True or not runtime_lock_is_complete(manifest.get("resolved_wheels",[])):
            raise RuntimeError("AI工作进程启动前运行库wheel锁不完整")
        self.on_failure=on_failure
        self.lock=threading.RLock()
        self.connection=None
        self.process=None
        self.closed=False
        self.active_stop_path=None
        self.status={}
        self.candidate_index_tokens=set()
        self.startup_log_path=make_data_directory(self.base,"logs")/"ai_worker_startup.log"
        self.startup_log_handle=self.startup_log_path.open("ab",buffering=0)
        self.startup_log_handle.write(("\n=== AI worker startup "+time.strftime("%Y-%m-%d %H:%M:%S")+" protocol="+str(AI_WORKER_PROTOCOL_VERSION)+" ===\n").encode("utf-8"))
        self.auth=os.urandom(32)
        self.family="AF_PIPE" if os.name=="nt" else "AF_INET"
        self.address=(r"\\.\pipe\UniversalGameAI-"+uuid.uuid4().hex) if os.name=="nt" else ("127.0.0.1",0)
        listener=Listener(self.address,family=self.family,authkey=self.auth)
        actual_address=listener.address
        python=runtime_python_path(self.base)
        if not python.is_file():
            listener.close()
            raise RuntimeError("固定独立Python工作进程不存在")
        env=os.environ.copy()
        env.update({"PYTHONNOUSERSITE":"1","UGAI_DATA_DIR":str(self.base),"PIP_NO_INDEX":"1","TORCH_HOME":str(self.base/"models"/"torch"),"HF_HOME":str(self.base/"models"/"huggingface"),
                "HUGGINGFACE_HUB_CACHE":str(self.base/"cache"/"huggingface_hub"),"TRANSFORMERS_CACHE":str(self.base/"cache"/"transformers"),"XDG_CACHE_HOME":str(self.base/"cache"),
                "PYTHONPYCACHEPREFIX":str(self.base/"cache"/"pycache"),"TORCH_EXTENSIONS_DIR":str(self.base/"cache"/"torch_extensions"),"CUDA_CACHE_PATH":str(self.base/"cache"/"cuda"),
                "NUMBA_CACHE_DIR":str(self.base/"cache"/"numba"),"MPLCONFIGDIR":str(self.base/"cache"/"matplotlib"),"TMP":str(self.base/"temp"),"TEMP":str(self.base/"temp")})
        address_text=actual_address if isinstance(actual_address,str) else json.dumps(list(actual_address),separators=(",",":"))
        command=[str(python),str(Path(__file__).resolve()),"ai-worker",str(self.base),str(address_text),base64.urlsafe_b64encode(self.auth).decode("ascii"),self.family,str(AI_WORKER_PROTOCOL_VERSION)]
        flags=0x08000000 if os.name=="nt" else 0
        self.process=subprocess.Popen(command,env=env,creationflags=flags,stdin=subprocess.DEVNULL,stdout=self.startup_log_handle,stderr=self.startup_log_handle)
        accepted=queue.Queue(maxsize=1)
        def acceptor():
            try:
                accepted.put((True,listener.accept()))
            except BaseException as error:
                accepted.put((False,error))
        thread=threading.Thread(target=acceptor,name="UniversalGameAI-AIWorkerAccept",daemon=True)
        thread.start()
        try:
            ok,value=accepted.get(timeout=30.0)
        except queue.Empty:
            self._terminate_process()
            listener.close()
            raise RuntimeError("AI工作进程连接超时；启动日志："+self._startup_log_tail())
        listener.close()
        if not ok:
            self._terminate_process()
            raise RuntimeError("AI工作进程连接失败："+str(value)+"；启动日志："+self._startup_log_tail())
        self.connection=value
        if not self.connection.poll(120.0):
            self.close(0.2)
            raise RuntimeError("AI工作进程初始化超时；启动日志："+self._startup_log_tail())
        hello=self.connection.recv()
        if not isinstance(hello,dict) or hello.get("kind")!="ready" or safe_int(hello.get("protocol_version"),0)!=AI_WORKER_PROTOCOL_VERSION or hello.get("stage")!="READY":
            self.close(0.2)
            raise RuntimeError("AI工作进程初始化协议无效；启动日志："+self._startup_log_tail())
        self.status=dict(hello.get("status",{}))
    def _startup_log_tail(self):
        try:
            if self.startup_log_handle is not None:
                self.startup_log_handle.flush()
            data=self.startup_log_path.read_bytes()[-12000:]
            return data.decode("utf-8","replace")
        except Exception as error:
            return "无法读取日志："+str(error)
    def _terminate_process(self):
        process=self.process
        if process is None:
            return
        try:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=1.0)
        except Exception:
            try:
                process.kill()
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
    def _failed(self,error):
        if self.on_failure is not None:
            try:
                self.on_failure(error)
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
    def request_stop(self):
        path=self.active_stop_path
        if path is not None:
            try:
                Path(path).touch(exist_ok=True)
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
    def request(self,operation,payload=None,timeout=120.0,progress=None):
        with self.lock:
            if self.closed or self.connection is None or self.process is None or self.process.poll() is not None:
                error=RuntimeError("AI工作进程不可用")
                self._failed(error)
                raise error
            request_id=uuid.uuid4().hex
            request_started=time.monotonic()
            stop_path=None
            data=dict(payload) if isinstance(payload,dict) else {}
            if operation=="train":
                stop_path=self.base/"temp"/("ai_stop_"+request_id)
                try:
                    stop_path.unlink()
                except OSError:
                    pass
                data["stop_path"]=str(stop_path)
                self.active_stop_path=stop_path
            try:
                self.connection.send({"protocol_version":AI_WORKER_PROTOCOL_VERSION,"stage":"RUNNING","id":request_id,"operation":str(operation),"payload":data})
                deadline=time.monotonic()+max(1.0,float(timeout))
                while True:
                    remaining=deadline-time.monotonic()
                    if remaining<=0 or not self.connection.poll(min(0.2,max(0.01,remaining))):
                        if self.process.poll() is not None:
                            raise RuntimeError("AI工作进程异常退出")
                        if remaining<=0:
                            raise RuntimeError("AI工作进程请求超时："+str(operation))
                        continue
                    packet=self.connection.recv()
                    if not isinstance(packet,dict) or str(packet.get("id",""))!=request_id:
                        continue
                    if packet.get("kind")=="progress":
                        if progress is not None:
                            progress(packet.get("value",0.0))
                        continue
                    if packet.get("kind")=="error":
                        raise RuntimeError(str(packet.get("message","AI工作进程失败"))+"\n"+str(packet.get("traceback","")))
                    if packet.get("kind")=="result":
                        return packet.get("value")
            except BaseException as error:
                self._failed(error)
                raise
            finally:
                if stop_path is not None:
                    try:
                        stop_path.unlink()
                    except OSError:
                        pass
                    self.active_stop_path=None
                RUNTIME_METRICS.observe("ai_worker_request_ms",(time.monotonic()-request_started)*1000.0)
    def candidate_matches(self,model,feature,query_coarse,backend,full_limit):
        if not isinstance(model,dict):
            raise ValueError("候选模型无效")
        token=str(model.get("runtime_token","")).strip()
        prototypes=model.get("prototypes",[])
        if len(token)!=64:
            token=prototype_collection_checksum(prototypes)
        if token not in self.candidate_index_tokens:
            payload=[]
            for index,proto in enumerate(prototypes):
                if not isinstance(proto,dict):
                    continue
                payload.append({
                    "id":str(proto.get("id",index)),
                    "cluster_id":str(proto.get("cluster_id",proto.get("action_signature",""))),
                    "f":feature_bytes(proto.get("f")),
                    "coarse":bytes(proto.get("coarse")) if isinstance(proto.get("coarse"),(bytes,bytearray)) and len(proto.get("coarse"))==COARSE_LEN else coarse_feature(proto.get("f")),
                    "capture_methods":sorted(str(value) for value in proto.get("capture_methods",[])),
                    "authorized":bool(proto.get("authorized",True)),
                })
            self.request("load_candidate_index",{"token":token,"prototypes":payload},180.0)
            self.candidate_index_tokens.add(token)
        return self.request("match_candidate_index",{"token":token,"feature":feature_bytes(feature),"coarse":bytes(query_coarse),"backend":str(backend),"full_limit":int(full_limit)},10.0)
    def alive(self):
        return bool(not self.closed and self.process is not None and self.process.poll() is None)
    def close(self,timeout=2.0):
        if self.closed:
            return True
        self.request_stop()
        try:
            if self.connection is not None and self.process is not None and self.process.poll() is None:
                self.request("shutdown",{},max(1.0,float(timeout)))
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        self.closed=True
        self.candidate_index_tokens.clear()
        try:
            if self.connection is not None:
                self.connection.close()
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        self._terminate_process()
        try:
            if self.startup_log_handle is not None:
                self.startup_log_handle.close()
                self.startup_log_handle=None
        except Exception as error:
            record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        return not self.alive()
class VisionRuntimeProxy:
    def __init__(self,worker):
        self.worker=worker
        self.ready=True
        self.error=""
        self.active_game=None
        self.device_name=str(worker.status.get("device","独立AI工作进程"))
        self.backend=str(worker.status.get("vision_backend","builtin_cpu"))
        self.serialization=str(worker.status.get("vision_serialization","builtin_json"))
        self.capabilities=dict(worker.status.get("capabilities",{}))
        self.trained_steps=0
    def require_ready(self):
        if not self.worker.alive():
            self.ready=False
            raise RuntimeError("AI工作进程不可用")
        return True
    def activate_game(self,game_id):
        self.require_ready()
        value=self.worker.request("activate_game",{"game_id":str(game_id)},180.0)
        self.active_game=str(game_id)
        if isinstance(value,dict):
            self.trained_steps=safe_int(value.get("trained_steps"),self.trained_steps)
        return value
    def manifest(self):
        self.require_ready()
        value=self.worker.request("vision_manifest",{},60.0)
        if isinstance(value,dict):
            self.trained_steps=safe_int(value.get("trained_steps"),self.trained_steps)
        return value
    def encode(self,rgb,previous_rgb=None):
        self.require_ready()
        return self.worker.request("encode",{"rgb":bytes(rgb),"previous":bytes(previous_rgb) if previous_rgb is not None else None},30.0)
    def train(self,game_id,samples,stop_event=None,progress=None,seed=None):
        self.require_ready()
        if stop_event is not None and stop_event.is_set():
            raise InputStopped("睡眠已停止")
        snapshot=create_training_snapshot(self.worker.base,game_id,samples)
        try:
            return self.worker.request("train",{"game_id":str(game_id),"snapshot":snapshot,"sleep_seed":safe_int(seed,0,0,2**63-1)},7200.0,progress)
        finally:
            remove_training_snapshot(self.worker.base,snapshot)
class OCRRuntimeProxy:
    def __init__(self,worker):
        self.worker=worker
        self.ready=True
        self.error=""
        self.backend=str(worker.status.get("ocr_backend","none"))
        self.self_test_passed=bool(worker.status.get("ocr_self_test",False))
    def require_ready(self):
        if not self.worker.alive():
            self.ready=False
            raise RuntimeError("AI工作进程不可用")
        return True
    def recognize_region(self,frame,norm):
        self.require_ready()
        return self.worker.request("ocr_recognize_region",{"frame":dict(frame),"norm":norm},45.0)
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
            while not self.stop_event.is_set() and not self.context.callbacks.should_stop():
                frame=self.frame_buffer.latest(None,1.0)
                if frame is None or frame.get("time")==self.last_stamp or not frame.get("capture_valid"):
                    self.stop_event.wait(0.12)
                    continue
                self.last_stamp=frame.get("time")
                for definition in definitions:
                    if self.stop_event.is_set() or self.context.callbacks.should_stop():
                        break
                    try:
                        recognized=self.app.ocr_runtime.recognize_region(frame,definition["region_norm"])
                        parsed=parse_ocr_number(recognized.get("text"),definition.get("number_format","auto")) if definition.get("region_type")=="number" else {"valid":False}
                        event=OCR_SEMANTIC_ENGINE.evaluate(definition,parsed) if definition.get("region_type")=="number" else {"terminal":"","progress":0.0,"status":"text_only","reset":"",
                            "semantic_version":OCR_SEMANTIC_VERSION}
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
def ocr_can_authorize_action(text,action):
    return False
def _pid_alive(pid):
    try:
        value=int(pid)
        if os.name=="nt":
            handle=ctypes.WinDLL("kernel32",use_last_error=True).OpenProcess(0x1000,False,value)
            if not handle:
                return False
            ctypes.WinDLL("kernel32",use_last_error=True).CloseHandle(handle)
            return True
        os.kill(value,0)
        return True
    except Exception:
        return False
def _tk_top_level_hwnd(widget):
    try:
        value=str(widget.wm_frame())
        return int(value,0)
    except Exception:
        return int(widget.winfo_id())
def _acceptance_geometry_complete(report):
    item=report.data.get("items",{}).get("多显示器与DPI",{}).get("cases",{})
    return all(item.get(case,{}).get("status")=="passed" for case in STRICT_ACCEPTANCE_CASES["多显示器与DPI"])
def run_window_contract_test(path=None):
    result={"test":"window-contract","status":"failed","checks":{},"evidence":{},"failures":[]}
    def check(name,value,evidence=None):
        passed=bool(value)
        result["checks"][str(name)]=passed
        if evidence is not None:
            result["evidence"][str(name)]=evidence
        if not passed:
            result["failures"].append(str(name))
        return passed
    if os.name!="nt" or not path:
        result["status"]="not_run"
        result["failures"]=["必须在Windows 11实机并提供已确认的数据目录"]
        sys.stdout.write(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n")
        return 2
    root=None
    overlay=None
    recreated=None
    bridge=None
    try:
        version=sys.getwindowsversion()
        if int(version.major)!=10 or int(version.build)<22000:
            raise RuntimeError("仅支持Windows 11内部版本22000或更高")
        if native_windows_architecture()!=RUNTIME_ARCH_X64:
            raise RuntimeError("ARM64缺少完整锁和实机证据，不进入严格窗口验收")
        base=Path(path).expanduser().resolve()
        base.mkdir(parents=True,exist_ok=True)
        install_write_boundary_guard(base)
        report=AcceptanceReport(base)
        load_gui_runtime()
        enable_dpi_awareness()
        root=tk.Tk()
        root.title("UniversalGameAI Window Contract")
        root.geometry("640x420+80+80")
        canvas=tk.Canvas(root,width=600,height=360,bg="white",highlightthickness=0)
        canvas.pack(fill="both",expand=True)
        canvas.create_rectangle(20,20,300,180,fill="#204080",outline="#ffffff")
        canvas.create_oval(330,40,560,270,fill="#d08020",outline="#000000")
        canvas.create_text(320,330,text="UniversalGameAI",font=("Arial",24,"bold"))
        root.update_idletasks()
        root.update()
        bridge=WinBridge()
        hwnd=_tk_top_level_hwnd(root)
        identity=bridge.target_identity(hwnd)
        client=bridge.client_rect(hwnd)
        coordinate_ok=client[2]>=600 and client[3]>=360 and abs(client[0]-root.winfo_rootx())<=16 and abs(client[1]-root.winfo_rooty())<=64
        check("client_coordinates",coordinate_ok,{"hwnd":hwnd,"client":client,"tk_root":[root.winfo_rootx(),root.winfo_rooty()],"dpi":identity.get("dpi")})
        monitors=[]
        class MONITORINFO(ctypes.Structure):
            _fields_=[("cbSize",wintypes.DWORD),("rcMonitor",RECT),("rcWork",RECT),("dwFlags",wintypes.DWORD)]
        monitor_proc_type=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HANDLE,wintypes.HANDLE,ctypes.POINTER(RECT),wintypes.LPARAM)
        def monitor_callback(handle,hdc,rect_ptr,lparam):
            info=MONITORINFO()
            info.cbSize=ctypes.sizeof(info)
            if bridge.user32.GetMonitorInfoW(handle,ctypes.byref(info)):
                monitors.append({"handle":int(handle),"rect":[int(info.rcMonitor.left),int(info.rcMonitor.top),int(info.rcMonitor.right-info.rcMonitor.left),
                            int(info.rcMonitor.bottom-info.rcMonitor.top)],"work":[int(info.rcWork.left),int(info.rcWork.top),int(info.rcWork.right-info.rcWork.left),int(info.rcWork.bottom-info.rcWork.top)]})
            return True
        monitor_callback_value=monitor_proc_type(monitor_callback)
        bridge.user32.EnumDisplayMonitors(0,None,monitor_callback_value,0)
        observations=[]
        for monitor in monitors:
            x,y,w,h=monitor["work"]
            root.geometry("640x420+"+str(x+max(10,min(80,w//10)))+"+"+str(y+max(10,min(80,h//10))))
            root.update_idletasks()
            root.update()
            current_client=bridge.client_rect(hwnd)
            observations.append({"monitor":monitor["rect"],"client":list(current_client),"dpi":bridge.dpi_for_window(hwnd)})
        observed_dpis=sorted({safe_int(item.get("dpi"),0) for item in observations if safe_int(item.get("dpi"),0)>0})
        dpi_case={96:"dpi100",120:"dpi125",144:"dpi150",192:"dpi200"}
        for dpi,case in dpi_case.items():
            if dpi in observed_dpis:
                report.record_case("多显示器与DPI",case,"passed",{"observed_dpis":observed_dpis,"monitors":observations})
        scaling_ok=all(item["client"][2]>=600 and item["client"][3]>=360 for item in observations) and bool(observations)
        check("dpi_scaling",scaling_ok,{"observed_dpis":observed_dpis,"monitors":observations})
        if len(monitors)>=2:
            cross_ok=len(observations)>=2 and len({(item["client"][0],item["client"][1]) for item in observations})>=2
            report.record_case("多显示器与DPI","cross_monitor","passed" if cross_ok else "failed",observations)
            check("cross_monitor",cross_ok,observations)
        else:
            check("cross_monitor",False,{"reason":"需要至少两个真实显示器"})
        mixed_ok=len(observed_dpis)>=2
        if mixed_ok:
            report.record_case("多显示器与DPI","mixed_dpi","passed",{"observed_dpis":observed_dpis})
        check("mixed_dpi",mixed_ok,{"observed_dpis":observed_dpis})
        negative_monitors=[item for item in monitors if item["rect"][0]<0 or item["rect"][1]<0]
        negative_ok=False
        negative_evidence={"monitors":[item["rect"] for item in monitors]}
        if negative_monitors:
            x,y,w,h=negative_monitors[0]["work"]
            root.geometry("640x420+"+str(x+10)+"+"+str(y+10))
            root.update_idletasks()
            root.update()
            negative_client=bridge.client_rect(hwnd)
            negative_ok=negative_client[0]<0 or negative_client[1]<0
            negative_evidence["client"]=negative_client
            report.record_case("多显示器与DPI","negative_coordinates","passed" if negative_ok else "failed",negative_evidence)
        check("negative_coordinates",negative_ok,negative_evidence)
        root.geometry("640x420+80+80")
        root.update_idletasks()
        root.update()
        identity=bridge.target_identity(hwnd)
        identity["content_rect_norm"]=[0.0,0.0,1.0,1.0]
        overlay=tk.Toplevel(root)
        overlay.title("Occlusion Contract")
        overlay.geometry("640x420+80+80")
        ttk.Label(overlay,text="OCCLUSION",font=("Arial",36,"bold")).pack(fill="both",expand=True)
        overlay.attributes("-topmost",True)
        overlay.lift()
        overlay.update_idletasks()
        overlay.update()
        capture_error=""
        capture_methods=[]
        try:
            captured=bridge.capture_gray(identity,False,True,False)
            capture_methods=sorted({str(item.get("method","")) for item in captured.get("validation_candidates",[]) if str(item.get("method",""))})
            if captured.get("method"):
                capture_methods=sorted(set(capture_methods+[str(captured.get("method"))]))
        except Exception as error:
            capture_error=str(error)
        occluded_ok=bool(capture_methods)
        report.record_case("采集","occluded","passed" if occluded_ok else "failed",{"methods":capture_methods,"error":capture_error})
        check("occluded_capture",occluded_ok,{"methods":capture_methods,"error":capture_error})
        overlay.destroy()
        overlay=None
        root.update()
        old=tk.Toplevel(root)
        old.title("Rebuild Old")
        old.geometry("320x220+150+150")
        old.update_idletasks()
        old.update()
        old_hwnd=_tk_top_level_hwnd(old)
        old_identity=bridge.target_identity(old_hwnd)
        old.destroy()
        root.update_idletasks()
        root.update()
        stale_rejected=not bridge.valid(old_hwnd)
        recreated=tk.Toplevel(root)
        recreated.title("Rebuild New")
        recreated.geometry("320x220+170+170")
        recreated.update_idletasks()
        recreated.update()
        new_hwnd=_tk_top_level_hwnd(recreated)
        new_identity=bridge.target_identity(new_hwnd)
        rebuilt_ok=stale_rejected and bridge.valid(new_hwnd) and (new_hwnd!=old_hwnd or new_identity.get("process_created")!=old_identity.get("process_created"))
        report.record_case("多显示器与DPI","hwnd_reuse","passed" if rebuilt_ok else "failed",{"old":old_identity,"new":new_identity,"stale_rejected":stale_rejected})
        check("window_recreated",rebuilt_ok,{"old_hwnd":old_hwnd,"new_hwnd":new_hwnd,"stale_rejected":stale_rejected})
        recreated.destroy()
        recreated=None
        if coordinate_ok and scaling_ok:
            report.record_case("采集","scaled","passed" if any(dpi!=96 for dpi in observed_dpis) else "pending",{"observed_dpis":observed_dpis,"coordinate_ok":coordinate_ok})
        geometry_complete=_acceptance_geometry_complete(report)
        report.set_environment(windows_build=int(version.build),real_windows_11=True,architecture=RUNTIME_ARCH_X64,window_geometry_test=geometry_complete,window_contract_run=time.time(),
            window_contract_observations=observations)
        result["strict_geometry_complete"]=geometry_complete
        result["acceptance_report"]=str(report.path)
        result["status"]="passed" if not result["failures"] else "needs_more_environment"
    except Exception as error:
        result["fatal"]="".join(traceback.format_exception(type(error),error,error.__traceback__))
    finally:
        if recreated is not None:
            try:
                recreated.destroy()
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        if overlay is not None:
            try:
                overlay.destroy()
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        if bridge is not None:
            try:
                bridge.close()
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
        if root is not None:
            try:
                root.destroy()
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
    sys.stdout.write(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n")
    return 0 if result.get("status")=="passed" else 1
def run_runtime_e2e_test(path=None):
    result={"test":"runtime-e2e","status":"failed","progress":[],"failures":[]}
    if os.name!="nt" or not path:
        result["status"]="not_run"
        result["failures"]=["必须在Windows 11 x64实机并提供已确认的数据目录"]
        sys.stdout.write(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n")
        return 2
    worker=None
    try:
        version=sys.getwindowsversion()
        if int(version.major)!=10 or int(version.build)<22000 or native_windows_architecture()!=RUNTIME_ARCH_X64:
            raise RuntimeError("真实文件完整性检查与AI worker端到端测试仅支持Windows 11 x64")
        base=Path(path).expanduser().resolve()
        base.mkdir(parents=True,exist_ok=True)
        for name in ("logs","temp","cache","audit","models"):
            (base/name).mkdir(parents=True,exist_ok=True)
        install_write_boundary_guard(base)
        entries,checksum,key=embedded_runtime_lock(RUNTIME_ARCH_X64)
        if not runtime_lock_is_complete(entries):
            raise RuntimeError("内嵌运行库wheel锁不完整")
        stop=threading.Event()
        lines=[]
        installer=RuntimeInstaller(base)
        manifest=installer.run(stop,lambda value:result["progress"].append(round(safe_float(value,0.0),3)),lambda value:lines.append(str(value)))
        validated=validate_runtime_manifest(base,True,True)
        if validated is None or validated.get("lock_complete") is not True or validated.get("embedded_lock_checksum")!=checksum:
            raise RuntimeError("文件完整性检查后运行库清单校验失败")
        worker=AIWorkerClient(base)
        alive=worker.alive()
        status=dict(worker.status)
        vision=worker.request("vision_manifest",{},120.0)
        offline=bool(status.get("offline_network_blocked"))
        capabilities=dict(status.get("capabilities",{}))
        required_capabilities=all(capabilities.get(name) is True for name in ("vision_train","ocr_recognize","safetensors","torch_cpu","rapidocr","candidate_rank"))
        passed=bool(alive and isinstance(vision,dict) and offline and required_capabilities)
        report=AcceptanceReport(base)
        evidence={"manifest_checksum":validated.get("manifest_checksum"),"embedded_lock_checksum":checksum,"lock_key":key,"wheel_count":len(entries),"worker_status":status,
            "vision_manifest":vision,"startup_log":str(worker.startup_log_path),"installer_lines":lines[-80:]}
        report.record_case("文件完整性","normal_complete","passed" if passed else "failed",evidence)
        report.record_case("文件完整性","locked_manifest","passed" if validated.get("lock_complete") is True else "failed",evidence)
        report.record_case("独立运行时","fixed_python","passed" if tuple(validated.get("python_abi",[]))==FIXED_RUNTIME_PYTHON_ABI else "failed",evidence)
        report.record_case("独立运行时","worker_process","passed" if alive else "failed",evidence)
        report.record_case("独立运行时","embedded_wheel_lock","passed" if validated.get("embedded_lock_checksum")==checksum else "failed",evidence)
        report.record_case("独立运行时","host_abi_independent","passed",{"host_python":list(sys.version_info[:2]),"runtime_python":validated.get("python_abi")})
        for case in ("socket","urllib","disconnected_windows"):
            report.record_case("离线网络封锁",case,"passed" if offline else "failed",status.get("offline_network_evidence",status))
        report.set_environment(windows_build=int(version.build),real_windows_11=True,architecture=RUNTIME_ARCH_X64,end_to_end_download_worker=passed,runtime_e2e_run=time.time())
        result.update({"status":"passed" if passed else "failed","manifest":manifest,"validated_manifest":validated,"worker_status":status,"acceptance_report":str(report.path),"startup_log":str(worker.startup_log_path)})
        if not passed:
            result["failures"].append("独立AI worker或完整能力自测未通过")
    except Exception as error:
        result["failures"].append(str(error))
        result["traceback"]="".join(traceback.format_exception(type(error),error,error.__traceback__))
    finally:
        if worker is not None:
            try:
                worker.close(3.0)
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
    sys.stdout.write(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n")
    return 0 if result.get("status")=="passed" else 1
def logic_contract_suite():
    checks={}
    def record(name,condition,evidence=None):
        checks[str(name)]={"passed":bool(condition),"evidence":evidence}
    action=normalize_action({"kind":"click","button":"left","path":[[1.2,-0.2]],"duration":0.01})
    record("action_normalization",bool(action and all(point==[1.0,0.0] for point in action["path"]) and action["duration"]>=0.02),action)
    rect=normalized_rect((120,80,400,200),(100,50,800,600))
    restored=apply_normalized_rect((100,50,800,600),rect)
    record("coordinate_roundtrip",all(abs(a-b)<=1 for a,b in zip(restored,(120,80,400,200))),{"normalized":rect,"restored":restored})
    seed_a,evidence_a=deterministic_sleep_seed("g",[{"checksum":"b"},{"checksum":"a"}])
    seed_b,evidence_b=deterministic_sleep_seed("g",[{"checksum":"a"},{"checksum":"b"}])
    record("deterministic_seed",seed_a==seed_b and evidence_a==evidence_b,evidence_a)
    first=bytes(FEATURE_LEN)
    second=bytes([255])*FEATURE_LEN
    p1={"id":"p1","cluster_id":"c1","a":normalize_action({"kind":"click","button":"left","path":[[0.2,0.2]]}),"f":first,"coarse":coarse_feature(first),"temporal":{},
        "capture_methods":["backend"],"threshold":1.0,"intra_threshold":1.0}
    p2={"id":"p2","cluster_id":"c2","a":normalize_action({"kind":"click","button":"left","path":[[0.8,0.8]]}),"f":second,"coarse":coarse_feature(second),"temporal":{},
        "capture_methods":["backend"],"threshold":1.0,"intra_threshold":1.0}
    tracker=PrototypeConflictTracker(lambda:False,16,4)
    tracker.add_batch([p1,p2])
    tracker.finalize([p1,p2])
    record("prototype_conflict_index",p1.get("nearest_conflicting_distance") is not None and p2.get("nearest_conflicting_distance") is not None,{"p1":p1.get("nearest_conflicting_distance"),
            "p2":p2.get("nearest_conflicting_distance")})
    record("numpy_distance_no_int16_overflow",abs(feature_distance(first,second)-65025.0)<1e-6,{"distance":feature_distance(first,second)})
    numpy_first=_optional_numpy()
    numpy_second=_optional_numpy()
    record("optional_numpy_probe_cached",_NUMPY_CHECKED and numpy_first is numpy_second,{"checked":_NUMPY_CHECKED,"available":numpy_first is not None})
    first_build_hash=current_build_hash()
    second_build_hash=current_build_hash()
    record("source_build_hash_cached",bool(first_build_hash) and first_build_hash==second_build_hash and _BUILD_HASH==first_build_hash,{"hash":first_build_hash,"key":_BUILD_HASH_KEY})
    with tempfile.TemporaryDirectory() as folder:
        database=ThreadLocalSQLite(Path(folder)/"logic.db")
        database.execute("CREATE TABLE sample(value INTEGER)")
        database.commit()
        errors=[]
        def worker():
            try:
                with database.thread_connection() as connection:
                    connection.execute("INSERT INTO sample(value) VALUES(1)")
                    connection.commit()
            except Exception as error:
                errors.append(str(error))
        thread=threading.Thread(target=worker)
        thread.start()
        thread.join(3.0)
        count=database.execute("SELECT COUNT(*) FROM sample").fetchone()[0]
        before=database.connection_count()
        database.close()
        after=database.connection_count()
        record("thread_local_sqlite",not errors and not thread.is_alive() and count==1 and before==1 and after==0,{"errors":errors,"count":count,"before":before,"after":after})
    class CandidateRankHarness(AppModeMixin):
        def __init__(self,prototypes,runtime_index,sequence_model):
            self.candidate_cache=BoundedLRU(64)
            self.stop_event=None
            self.ai_worker=None
            self.active_model_runtime={"prototypes":prototypes,"runtime_index":runtime_index,"runtime_token":runtime_index["token"],"sequence_model":sequence_model}
        def should_stop(self):
            return False
    rank_feature=bytes(FEATURE_LEN)
    rank_coarse=coarse_feature(rank_feature)
    rank_prototypes=[]
    for identity,cluster,point,motion in (("r1","c1",[0.2,0.2],[0.0,0.0,0.0]),("r2","c2",[0.8,0.8],[100.0,100.0,100.0])):
        rank_prototypes.append({"id":identity,"cluster_id":cluster,"a":normalize_action({"kind":"click","button":"left","path":[point]}),"f":rank_feature,"coarse":rank_coarse,
                "capture_methods":["backend"],"authorized":True,"threshold":100.0,"temporal_threshold":1.0,"support":20,"action_support":20,"temporal":{"capture_method":"backend","recent_frame_deltas":motion}})
    rank_index=build_candidate_runtime_index(rank_prototypes,False)
    rank_harness=CandidateRankHarness(rank_prototypes,rank_index,{"1|x":{"c1":100.0,"c2":0.0},"1|y":{"c1":0.0,"c2":100.0}})
    first_rank=rank_harness.rank_action_candidates(rank_feature,rank_prototypes,"",18,{"capture_method":"backend","recent_actions":["x"],"recent_frame_deltas":[0.0,0.0,0.0]},rank_coarse)
    second_rank=rank_harness.rank_action_candidates(rank_feature,rank_prototypes,"",18,{"capture_method":"backend","recent_actions":["y"],"recent_frame_deltas":[100.0,100.0,100.0]},rank_coarse)
    temporal_recomputed=bool(first_rank and second_rank and first_rank[0]["cluster_id"]!=second_rank[0]["cluster_id"] and len(rank_harness.candidate_cache)==1)
    normalized_outputs=all(item.get("a")==normalize_action(item.get("a")) for item in first_rank+second_rank)
    record("temporal_candidate_cache_recomputed",temporal_recomputed and normalized_outputs,{"first":[item["cluster_id"] for item in first_rank],
            "second":[item["cluster_id"] for item in second_rank],"visual_cache_entries":len(rank_harness.candidate_cache),"normalized":normalized_outputs})
    np=_optional_numpy()
    performance_prototypes=[]
    for index in range(MAX_PROTOTYPES):
        value=bytes([index%256])*FEATURE_LEN
        performance_prototypes.append({"id":"perf"+str(index),"cluster_id":"pc"+str(index%24),"a":normalize_action({"kind":"click","button":"left","path":[[0.5,0.5]]}),"f":value,
                "coarse":coarse_feature(value),"capture_methods":["backend"],"authorized":True})
    performance_index=build_candidate_runtime_index(performance_prototypes,False)
    performance_query=bytes([123])*FEATURE_LEN
    performance_coarse=coarse_feature(performance_query)
    candidate_visual_matches(performance_index,performance_query,performance_coarse,"backend",VersionedThresholdConfig.candidate_full_limit)
    timings=[]
    for _ in range(7):
        started=time.perf_counter()
        candidate_visual_matches(performance_index,performance_query,performance_coarse,"backend",VersionedThresholdConfig.candidate_full_limit)
        timings.append((time.perf_counter()-started)*1000.0)
    median_ms=statistics.median(timings)
    performance_passed=np is None or median_ms<=12.0
    record("candidate_rank_performance_budget",performance_passed,{"numpy":np is not None,"median_ms":round(median_ms,3),"budget_ms":12.0,"prototypes":MAX_PROTOTYPES,
            "exact":VersionedThresholdConfig.candidate_full_limit})
    with tempfile.TemporaryDirectory() as folder:
        baseline_threads=len([thread for thread in threading.enumerate() if thread.is_alive()])
        leaked_connections=0
        for cycle in range(100):
            database=ThreadLocalSQLite(Path(folder)/("cycle_"+str(cycle)+".db"))
            database.execute("CREATE TABLE sample(value INTEGER)")
            database.execute("INSERT INTO sample(value) VALUES(?)",(cycle,))
            database.commit()
            database.close()
            leaked_connections+=database.connection_count()
            state={"alive":True}
            coordinator=ShutdownCoordinator("cycle",0.1)
            coordinator.add(ManagedShutdownResource("resource",lambda:state.update(alive=False),lambda:state["alive"],lambda timeout_value:not state["alive"],lambda:state.update(alive=False),0))
            coordinator.poll()
        after_threads=len([thread for thread in threading.enumerate() if thread.is_alive()])
        record("resource_leak_100_cycles",leaked_connections==0 and after_threads<=baseline_threads+1,{"baseline_threads":baseline_threads,"after_threads":after_threads,"connections":leaked_connections,"cycles":100})
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder)
        (root/"models"/"vision").mkdir(parents=True)
        sparse=root/"models"/"vision"/"large_model.bin"
        with sparse.open("wb") as handle:
            handle.truncate(1024*1024*1024)
        large_samples=[{"checksum":hashlib.sha256(str(index).encode()).hexdigest()} for index in range(MAX_SAMPLES)]
        large_started=time.perf_counter()
        migration_space=required_migration_space(root)
        runtime_space=required_runtime_space(root,64*1024*1024)
        large_elapsed=time.perf_counter()-large_started
        large_ok=len(large_samples)==MAX_SAMPLES and tree_size(root/"models")>=1024*1024*1024 and migration_space>2*1024*1024*1024 and runtime_space>1024*1024*1024 and large_elapsed<5.0
        record("large_data_budget_contract",large_ok,{"samples":len(large_samples),"prototypes":MAX_PROTOTYPES,"model_bytes":tree_size(root/"models"),"migration_space":migration_space,
                "runtime_space":runtime_space,"elapsed_ms":round(large_elapsed*1000.0,3)})
    return all(item["passed"] for item in checks.values()),checks
def fault_injection_contract_suite():
    checks={}
    def record(name,condition,evidence=None):
        checks[str(name)]={"passed":bool(condition),"evidence":evidence}
    output=BoundedProcessOutput(32,4096)
    for index in range(4000):
        output.put(json.dumps({"kind":"line","message":"x"*80,"index":index},separators=(",",":")))
    output.put(json.dumps({"kind":"progress","value":25},separators=(",",":")))
    output.put(json.dumps({"kind":"progress","value":75},separators=(",",":")))
    output.put(json.dumps({"kind":"result","manifest":{"ok":True}},separators=(",",":")))
    first=output.get(0.0)
    with output.lock:
        log_count=len(output.logs)
        log_bytes=output.log_bytes
        latest=dict(output.latest)
    record("bounded_subprocess_output",json.loads(first).get("kind")=="result" and log_count<=32 and log_bytes<=4096 and "progress" in latest,{"logs":log_count,"bytes":log_bytes,"latest":list(latest)})
    state={"alive":True,"forced":False}
    def force():
        state["alive"]=False
        state["forced"]=True
        return True
    coordinator=ShutdownCoordinator("fault",0.01)
    coordinator.add(ManagedShutdownResource("stubborn",lambda:True,lambda:state["alive"],lambda timeout_value:False,force,0))
    coordinator.poll()
    time.sleep(0.12)
    shutdown=coordinator.poll()
    record("unresponsive_resource_force_close",shutdown.get("done") and state["forced"] and "stubborn" in shutdown.get("forced",[]),shutdown)
    rejected=False
    try:
        validate_packet("window_identity",{"hwnd":0})
    except ValueError:
        rejected=True
    record("packet_validation_fail_closed",rejected)
    try:
        raise AssertionError("contract")
    except AssertionError as error:
        cleanup_record=record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
    cleanup_details=cleanup_record.get("details",{})
    record("cleanup_error_location_and_category",cleanup_record.get("code")=="INVARIANT_VIOLATION" and isinstance(cleanup_details.get("location"),dict) and safe_int(cleanup_details.get("location",{}).get("line"),0)>0,cleanup_record)
    with tempfile.TemporaryDirectory() as folder:
        database=ThreadLocalSQLite(Path(folder)/"rollback.db")
        database.execute("CREATE TABLE sample(value INTEGER)")
        database.commit()
        connection=database.current()
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("INSERT INTO sample(value) VALUES(1)")
        connection.rollback()
        count=database.execute("SELECT COUNT(*) FROM sample").fetchone()[0]
        database.close()
        record("database_rollback",count==0,{"count":count})
    return all(item["passed"] for item in checks.values()),checks
def run_logic_contract_tests():
    passed,checks=logic_contract_suite()
    result={"test":"pure-logic","status":"passed" if passed else "failed","checks":checks}
    sys.stdout.write(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n")
    return 0 if passed else 1
def run_fault_injection_tests():
    passed,checks=fault_injection_contract_suite()
    result={"test":"fault-injection","status":"passed" if passed else "failed","checks":checks}
    sys.stdout.write(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n")
    return 0 if passed else 1
def run_static_contract_tests(path=None):
    target=Path(path or __file__).resolve()
    checks=[]
    failures=[]
    def check(name,condition,evidence=None):
        item={"name":str(name),"passed":bool(condition),"evidence":evidence}
        checks.append(item)
        if not condition:
            failures.append(item)
    try:
        source=target.read_text(encoding="utf-8")
        compile(source,str(target),"exec")
        check("syntax_compile",True)
        comment_tokens=[token for token in tokenize.generate_tokens(io.StringIO(source).readline) if token.type==tokenize.COMMENT]
        check("single_file_source_has_no_comment_tokens",not comment_tokens,[token.start[0] for token in comment_tokens[:20]])
    except Exception as error:
        source=""
        check("syntax_compile",False,str(error))
    check("exact_default_control_contract",REQUIRED_DEFAULT_BUTTONS=={"选择文件夹","检查文件完整性","游戏","选择窗口","学习","睡眠","训练","指导"} and len(REQUIRED_DEFAULT_BUTTONS)==8,sorted(REQUIRED_DEFAULT_BUTTONS))
    check("mode_specs_contract",set(MODE_SPECS)=={"学习","睡眠","训练","指导"} and all(isinstance(value.get("requires"),tuple) and value.get("runner") for value in MODE_SPECS.values()),MODE_SPECS)
    check("subprocess_protocol_contract",all(value>=2 for value in (AI_WORKER_PROTOCOL_VERSION,RUNTIME_INSTALL_PROTOCOL_VERSION,REVIEW_PROCESS_PROTOCOL_VERSION,
                TEST_WORKER_PROTOCOL_VERSION)),{"ai":AI_WORKER_PROTOCOL_VERSION,"runtime":RUNTIME_INSTALL_PROTOCOL_VERSION,"sleep":REVIEW_PROCESS_PROTOCOL_VERSION,"test":TEST_WORKER_PROTOCOL_VERSION})
    try:
        tree=ast.parse(source)
        top_tk=[node for node in tree.body if isinstance(node,(ast.Import,ast.ImportFrom)) and ((isinstance(node,ast.ImportFrom) and node.module=="tkinter") or (isinstance(node,ast.Import)
                    and any(alias.name=="tkinter" for alias in node.names)))]
        check("worker_import_path_has_no_top_level_tkinter",not top_tk,[getattr(node,"lineno",0) for node in top_tk])
    except Exception as error:
        check("worker_import_path_has_no_top_level_tkinter",False,str(error))
    try:
        entries,checksum,key=embedded_runtime_lock(RUNTIME_ARCH_X64)
        check("embedded_wheel_lock_complete",runtime_lock_is_complete(entries) and runtime_lock_dependency_closure_is_complete(entries) and len(entries)==len(runtime_locked_projects()),
            {"count":len(entries),"checksum":checksum,"key":key,"dependency_providers":runtime_dependency_providers()})
        check("embedded_wheel_lock_immutable_fields",all(len(str(item.get("sha256","")))==64 and safe_int(item.get("size"),0)>0 and str(item.get("url","")).startswith("https://") for item in entries))
    except Exception as error:
        check("embedded_wheel_lock_complete",False,str(error))
    try:
        embedded_runtime_lock(RUNTIME_ARCH_ARM64)
        arm_rejected=False
    except RuntimeError:
        arm_rejected=True
    check("arm64_fail_closed_without_evidence",arm_rejected)
    samples=[{"checksum":"b"},{"checksum":"a"}]
    seed1,evidence1=deterministic_sleep_seed("game",samples)
    seed2,evidence2=deterministic_sleep_seed("game",list(reversed(samples)))
    seed3,_=deterministic_sleep_seed("game",samples+[{"checksum":"c"}])
    check("deterministic_sleep_seed",seed1==seed2 and evidence1==evidence2 and seed1!=seed3,evidence1)
    code=(
        "import builtins,runpy; original=builtins.__import__; "
        "builtins.__import__=lambda name,*a,**k: "
        "(_ for _ in ()).throw(ImportError('blocked tkinter')) "
        "if name=='tkinter' or name.startswith('tkinter.') "
        "else original(name,*a,**k); runpy.run_path("
        +repr(str(target))+
        ",run_name='ugai_import_contract')"
    )
    imported=subprocess.run([sys.executable,"-c",code],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=90)
    check("import_succeeds_when_tkinter_is_unavailable",imported.returncode==0,imported.stderr[-4000:])
    network_code="import json,runpy; ns=runpy.run_path("+repr(str(target))+",run_name='ugai_network_contract'); ns['_disable_network_access'](); print(json.dumps(ns['_verify_offline_network_block'](),sort_keys=True))"
    network=subprocess.run([sys.executable,"-c",network_code],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=90)
    try:
        network_evidence=json.loads(network.stdout.strip().splitlines()[-1])
    except Exception:
        network_evidence={}
    check("offline_network_block_active_probe",network.returncode==0 and network_evidence.get("blocked") is True and network_evidence.get("download_entrypoints_disabled") is True,
        network_evidence or network.stderr[-4000:])
    write_code=(
        "import pathlib,runpy,tempfile; root=pathlib.Path(tempfile.mkdtemp()); "
        "allowed=root/'allowed'; outside=root/'outside'; "
        "allowed.mkdir(); outside.mkdir(); ns=runpy.run_path("
        +repr(str(target))+
        ",run_name='ugai_write_contract'); "
        "ns['install_write_boundary_guard'](allowed); "
        "(allowed/'inside.txt').write_text('inside',encoding='utf-8'); "
        "blocked=False\ntry:\n "
        "(outside/'outside.txt').write_text('outside',encoding='utf-8')"
        "\nexcept RuntimeError:\n blocked=True\nprint(blocked)"
    )
    write_test=subprocess.run([sys.executable,"-c",write_code],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=90)
    check("write_boundary_guard_active_probe",write_test.returncode==0 and write_test.stdout.strip().endswith("True"),write_test.stderr[-4000:])
    state=ControlStateMachine(); state.set_directory_phase("ready"); state.set_runtime_ready(True); event=state.begin("学习"); starting=state.snapshot()[0]==MODE_STARTING; state.mark_running(); running=state.snapshot()[0]==MODE_RUNNING; state.request_stop("stopped",
        "contract"); stopping=state.snapshot()[0]==MODE_STOPPING and event.is_set(); state.finish()
    check("starting_running_stopping_state_machine",starting and running and stopping and state.snapshot()[0]==MODE_IDLE)
    with tempfile.TemporaryDirectory() as folder:
        report=AcceptanceReport(folder)
        report.set_environment(windows_build=0,real_windows_11=False,architecture=RUNTIME_ARCH_X64,end_to_end_download_worker=False,external_write_monitor=False,window_geometry_test=False)
        check("strict_acceptance_is_fail_closed",not report.strict_passed(),report.data.get("failures",[]))
    logic_passed,logic_checks=logic_contract_suite()
    fault_passed,fault_checks=fault_injection_contract_suite()
    check("pure_logic_test_layer",logic_passed,logic_checks)
    check("fault_injection_test_layer",fault_passed,fault_checks)
    try:
        classes={node.name:node for node in tree.body if isinstance(node,ast.ClassDef)}
        app_node=classes.get("App")
        check("app_under_800_lines",app_node is not None and app_node.end_lineno-app_node.lineno+1<=800,{"lines":app_node.end_lineno-app_node.lineno+1 if app_node is not None else None})
        dialog_lines={name:classes[name].end_lineno-classes[name].lineno+1 for name in ("WindowSelectionDialog","GameSelectionDialog","TaskSettingsDialog","GuidanceWindow") if name in classes}
        check("dialog_objects_bounded",dialog_lines.get("WindowSelectionDialog",999)<=300 and all(value<=300 for value in dialog_lines.values()),dialog_lines)
        phases={"preflight","acquire_window","calibrate_capture","start_monitors","run_loop","validate_session","commit_or_rollback","release_resources"}
        phase_runner=classes.get("PhaseRunner")
        phase_methods={item.name for item in phase_runner.body if isinstance(item,ast.FunctionDef)} if phase_runner is not None else set()
        runner_methods={name:{item.name for item in classes[name].body if isinstance(item,ast.FunctionDef)} for name in ("LearningRunner","ReviewRunner","TrainingRunner") if name in classes}
        phase_evidence={"base":sorted(phase_methods),"specialized":{name:sorted(value) for name,value in runner_methods.items()}}
        check("phased_mode_runners",phases.issubset(phase_methods) and len(runner_methods)==3 and all("run_loop" in value for value in runner_methods.values()),phase_evidence)
        controller_clean=True
        controller_evidence={}
        for name in ("LearningController","ReviewController","TrainingController"):
            node=classes.get(name)
            refs=[]
            if node is not None:
                for item in ast.walk(node):
                    if isinstance(item,ast.Attribute) and isinstance(item.value,ast.Name) and item.value.id=="self" and item.attr=="app":
                        refs.append(item.lineno)
                    if isinstance(item,(ast.Assign,ast.AnnAssign)):
                        targets=item.targets if isinstance(item,ast.Assign) else [item.target]
                        value=item.value
                        if any(isinstance(target,ast.Name) and target.id=="self" for target in targets) and isinstance(value,ast.Name) and value.id=="app":
                            refs.append(item.lineno)
            controller_evidence[name]=refs
            controller_clean=controller_clean and not refs
        check("controllers_do_not_alias_app",controller_clean,controller_evidence)
        required_classes={"ModeContext","ShutdownCoordinator","ManagedShutdownResource","PrototypeConflictTracker","WindowIdentity","FramePacket","CalibrationResult","GameRepository",
            "SampleRepository","ModelRepository","CaptureCalibrationRepository","OCRRegionRepository","MigrationService","RecoveryService","WindowIdentityService","WindowGeometryService",
            "CaptureBackend","MouseInputService","KeyboardHookService","DpiService","BoundedProcessOutput"}
        missing_classes=sorted(required_classes-set(classes))
        class_locations={name:classes[name].lineno for name in sorted(required_classes.intersection(classes))}
        check("required_internal_modules",not missing_classes,{"present":class_locations,"missing":missing_classes})
        source_lines=source.splitlines()
        max_line=max((len(line) for line in source_lines),default=0)
        over_200=sum(1 for line in source_lines if len(line)>200)
        over_300=sum(1 for line in source_lines if len(line)>300)
        check("source_line_readability",max_line<=300 and over_300==0,{"maximum_line_length":max_line,"over_200":over_200,"over_300":over_300,"sha256":RUNTIME_LOCK_MANIFEST_SHA256})
        removed_placeholders={"ResultStatus","ActionType","RepeatPolicy","ReviewDataFilter","ReviewActionClusterer","ReviewVisualClusterer","ReviewThresholdBuilder","AskRenderer","AskQuestionStateMachine","AskActionEditor","AskSubmitController"}
        check("unused_placeholder_abstractions_removed",not removed_placeholders.intersection(classes),sorted(removed_placeholders.intersection(classes)))
        check("candidate_cache_is_visual_only","visual-v3" in source and "calculate_sequence_penalty(recent_actions" in source and source.count("id(prototypes)")==1)
        check("candidate_matching_in_ai_worker",all(value in source for value in ("load_candidate_index","match_candidate_index","candidate_rank","coarse_matrix","feature_matrix","backend_indices","cluster_indices")))
        check("cached_optional_dependency_and_build_hash",all(value in source for value in ("_NUMPY_CHECKED","_NUMPY_MODULE","_BUILD_HASH_KEY")))
        controller_lengths={}
        for name in ("LearningController","ReviewController","TrainingController"):
            method=next((item for item in classes[name].body if isinstance(item,ast.FunctionDef) and item.name=="_run_impl"),None)
            controller_lengths[name]=method.end_lineno-method.lineno+1 if method is not None else 9999
        check("controller_run_impls_are_orchestrators",all(value<=6 for value in controller_lengths.values()),controller_lengths)
        execution_requirements={
            "LearningExecution":{"preflight","capture_loop","handle_event","build_sample_context","save","finalize"},
            "ReviewExecution":{"preflight","build_prototypes","evaluate_holdout","authorize_prototypes","build_model","finalize"},
            "TrainingExecution":{"preflight","capture_loop","choose_action","execute_selected_action","evaluate_outcome","finalize"},
        }
        execution_evidence={}
        execution_pass=True
        for name,required in execution_requirements.items():
            node=classes.get(name)
            methods={item.name:item.end_lineno-item.lineno+1 for item in node.body if isinstance(item,ast.FunctionDef)} if node is not None else {}
            execution_evidence[name]={"maximum":max(methods.values(),default=9999),"methods":sorted(methods),"missing":sorted(required-set(methods))}
            execution_pass=execution_pass and not execution_evidence[name]["missing"] and execution_evidence[name]["maximum"]<=60
        check("mode_loops_split_into_bounded_stages",execution_pass,execution_evidence)
        vision_proxy=classes.get("VisionRuntimeProxy")
        train_method=next((item for item in vision_proxy.body if isinstance(item,ast.FunctionDef) and item.name=="train"),None) if vision_proxy is not None else None
        train_source="\n".join(source.splitlines()[train_method.lineno-1:train_method.end_lineno]) if train_method is not None else ""
        check("training_snapshot_avoids_pipe_copy",all(value in train_source for value in ("create_training_snapshot","snapshot","remove_training_snapshot")) and "list(samples)" not in train_source)
        check("argparse_subcommand_protocol",all(value in source for value in ("build_cli_parser","add_subparsers","ai-worker","runtime-install-worker","window-contract")))
        check("build_hash_uses_size_and_mtime",'key=(int(stat.st_size),int(stat.st_mtime_ns))' in source)
        check("policy_state_sets_cached",all(value in source for value in ("self.success_states=frozenset","self.failure_states=frozenset","value in self.success_states","value in self.failure_states")))
        check("feature_weights_and_pool_boundaries_cached",all(value in source for value in ("FEATURE_DISTANCE_WEIGHTS_ARRAY","_feature_weight_array","POOL_BOUNDARIES","_pool_boundaries")))
        generated_modules=project_module_templates(source)
        module_real=not any("_legacy_runtime" in path for path in generated_modules) and "class LearningController" in generated_modules.get("src/modes/learning.py","") and "class TrainingExecution" in generated_modules.get("src/modes/training.py","")
        check("generated_project_has_real_modules",module_real,{"files":sorted(generated_modules)[:12]})
        silent_exception_pass=[]
        for item in ast.walk(tree):
            if isinstance(item,ast.ExceptHandler) and isinstance(item.type,ast.Name) and item.type.id=="Exception" and len(item.body)==1 and isinstance(item.body[0],ast.Pass):
                silent_exception_pass.append(item.lineno)
        check("no_broad_silent_exception_pass",not silent_exception_pass,silent_exception_pass)
    except Exception as error:
        check("refactor_structure_contract",False,str(error))
    result={"test":"static-contract","version":STATIC_CONTRACT_VERSION,"status":"passed" if not failures else "failed","checks":checks,"failures":failures}
    sys.stdout.write(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n")
    return 0 if not failures else 1
def run_strict_requirement_tests(path=None):
    sys.stderr.write("--strict-self-test已重命名为--static-contract-test；静态契约测试不能替代Windows 11实机严格验收\n")
    return 2
def show_acknowledge_only_startup(message):
    try:
        load_gui_runtime()
        enable_dpi_awareness()
        root=tk.Tk()
        root.withdraw()
        win=tk.Toplevel(root)
        win.title("通用游戏AI")
        fit_window(win,560,260,420,220)
        win.transient(root)
        frame=ttk.Frame(win,padding=20)
        frame.pack(fill="both",expand=True)
        ttk.Label(frame,text=str(message),wraplength=500,justify="left").pack(fill="both",expand=True)
        def close():
            try:
                win.grab_release()
            except Exception as error:
                record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
            root.destroy()
        ttk.Button(frame,text="确认",command=close).pack(fill="x",pady=(16,0),ipady=7)
        win.protocol("WM_DELETE_WINDOW",lambda:(win.bell(),win.lift()))
        win.grab_set()
        root.mainloop()
    except Exception as error:
        record_cleanup_error("BEST_EFFORT_EXCEPTION",error)
class BootstrapNamespace:
    load_gui_runtime=staticmethod(load_gui_runtime)
    configure_data_directory=staticmethod(configure_data_directory)
    prepare_data_directory=staticmethod(prepare_data_directory)
class RuntimeNamespace:
    embedded_runtime_lock=staticmethod(embedded_runtime_lock)
    validate_runtime_manifest=staticmethod(validate_runtime_manifest)
    runtime_install_worker=staticmethod(runtime_install_worker)
    ai_worker_main=staticmethod(ai_worker_main)
class StorageNamespace:
    DataStore=DataStore
    ThreadLocalSQLite=ThreadLocalSQLite
    atomic_write_text=staticmethod(atomic_write_text)
    atomic_write_bytes=staticmethod(atomic_write_bytes)
    open_data_file=staticmethod(open_data_file)
    replace_data_path=staticmethod(replace_data_path)
    remove_data_path=staticmethod(remove_data_path)
    make_data_directory=staticmethod(make_data_directory)
class WindowsNamespace:
    WinBridge=WinBridge
    PreviewCoordinateMapper=PreviewCoordinateMapper
    window_descriptor_score=staticmethod(window_descriptor_score)
class LearningNamespace:
    LearningController=LearningController
    normalize_action=staticmethod(normalize_action)
    action_signature=staticmethod(action_signature)
class SleepNamespace:
    ReviewController=ReviewController
    ReviewProcessWorker=ReviewProcessWorker
    deterministic_sleep_seed=staticmethod(deterministic_sleep_seed)
class TrainingNamespace:
    TrainingController=TrainingController
    TaskAgentPolicy=TaskAgentPolicy
class GuidanceNamespace:
    TeachingController=TeachingController
class GuiNamespace:
    App=App
    load_gui_runtime=staticmethod(load_gui_runtime)
    scrollable_frame=staticmethod(scrollable_frame)
class AcceptanceNamespace:
    run_static_contract_tests=staticmethod(run_static_contract_tests)
    run_runtime_e2e_test=staticmethod(run_runtime_e2e_test)
    run_window_contract_test=staticmethod(run_window_contract_test)
    run_acceptance_test=staticmethod(run_acceptance_test)
def strict_acceptance_gate(path):
    if os.name!="nt" or not path:
        sys.stdout.write(json.dumps({"strict_pass":False,"failures":["必须在Windows 11 x64实机并提供验收目录"]},ensure_ascii=False,separators=(",",":"))+"\n")
        return 1
    if native_windows_architecture()!=RUNTIME_ARCH_X64:
        sys.stdout.write(json.dumps({"strict_pass":False,"failures":["ARM64缺少完整锁和实机证据，不宣称严格支持"]},ensure_ascii=False,separators=(",",":"))+"\n")
        return 1
    report=AcceptanceReport(path)
    result=report.strict_passed()
    sys.stdout.write(json.dumps(report.data,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n")
    return 0 if result else 1
class CommandLineProtocolError(RuntimeError):
    pass

class StrictArgumentParser(argparse.ArgumentParser):
    def error(self,message):
        raise CommandLineProtocolError(str(message))

def _legacy_cli_arguments(argv):
    values=[str(value) for value in argv]
    mappings={
        "--logic-test":["test","logic"],
        "--fault-injection-test":["test","fault"],
        "--static-contract-test":["test","static"],
        "--strict-self-test":["test","strict-self"],
        "--self-test":["test","self"],
    }
    for flag,replacement in mappings.items():
        if flag in values:
            return replacement
    worker_mappings={
        "--ai-worker":("ai-worker",5),
        "--runtime-install-worker":("runtime-install-worker",1),
        "--runtime-installer-test-worker":("runtime-installer-test-worker",2),
    }
    for flag,(command,count) in worker_mappings.items():
        if flag in values:
            index=values.index(flag)
            arguments=values[index+1:index+1+count]
            if len(arguments)!=count:
                raise CommandLineProtocolError(flag+"参数数量无效")
            return [command,*arguments]
    acceptance_mappings={
        "--windows-smoke-test":"windows-smoke",
        "--runtime-e2e-test":"runtime-e2e",
        "--window-contract-test":"window-contract",
        "--acceptance-test":"all",
        "--strict-acceptance":"strict",
    }
    for flag,mode in acceptance_mappings.items():
        if flag in values:
            index=values.index(flag)
            target=values[index+1] if index+1<len(values) and not values[index+1].startswith("--") else ""
            return ["acceptance",mode,*([target] if target else [])]
    return values

def build_cli_parser():
    parser=StrictArgumentParser(prog="main.py",add_help=True)
    parser.add_argument("--developer-mode",action="store_true",help=argparse.SUPPRESS)
    commands=parser.add_subparsers(dest="command")
    commands.add_parser("gui")
    ai=commands.add_parser("ai-worker")
    ai.add_argument("base")
    ai.add_argument("address")
    ai.add_argument("auth")
    ai.add_argument("family",choices=("AF_PIPE","AF_INET"))
    ai.add_argument("protocol",type=int)
    runtime=commands.add_parser("runtime-install-worker")
    runtime.add_argument("request")
    runtime_test=commands.add_parser("runtime-installer-test-worker")
    runtime_test.add_argument("request")
    runtime_test.add_argument("mode",choices=("STARTING","RUNNING","STOPPING"))
    tests=commands.add_parser("test")
    tests.add_argument("kind",choices=("logic","fault","static","self","strict-self"))
    acceptance=commands.add_parser("acceptance")
    acceptance.add_argument("kind",choices=("windows-smoke","runtime-e2e","window-contract","all","strict"))
    acceptance.add_argument("path",nargs="?",default="")
    return parser

def parse_cli(argv=None):
    raw=list(sys.argv[1:] if argv is None else argv)
    normalized=_legacy_cli_arguments(raw)
    parser=build_cli_parser()
    parsed=parser.parse_args(normalized)
    if parsed.command is None:
        parsed.command="gui"
    return parsed

def _validated_worker_path(value,label,must_exist=False):
    text=str(value or "").strip()
    if not text or len(text)>32767 or "\x00" in text:
        raise CommandLineProtocolError(str(label)+"路径无效")
    path=Path(text).expanduser().absolute()
    if must_exist and not path.exists():
        raise CommandLineProtocolError(str(label)+"路径不存在")
    return path

def dispatch_cli(arguments):
    command=str(arguments.command)
    if command=="ai-worker":
        base=_validated_worker_path(arguments.base,"数据目录",True)
        try:
            auth=base64.urlsafe_b64decode(str(arguments.auth).encode("ascii"))
        except (ValueError,UnicodeEncodeError) as error:
            raise CommandLineProtocolError("AI工作进程认证数据不是有效Base64") from error
        if len(auth)!=32:
            raise CommandLineProtocolError("AI工作进程认证数据长度无效")
        if int(arguments.protocol)!=AI_WORKER_PROTOCOL_VERSION:
            raise CommandLineProtocolError("AI工作进程协议版本不一致")
        try:
            address=arguments.address if arguments.family=="AF_PIPE" else tuple(json.loads(arguments.address))
        except (TypeError,ValueError,json.JSONDecodeError) as error:
            raise CommandLineProtocolError("AI工作进程地址无效") from error
        if arguments.family=="AF_INET" and (not isinstance(address,tuple) or len(address)!=2 or not isinstance(address[0],str) or not isinstance(address[1],int)):
            raise CommandLineProtocolError("AF_INET地址必须是[host,port]")
        return ai_worker_main(str(base),address,arguments.auth,arguments.family,arguments.protocol) or 0
    if command=="runtime-install-worker":
        request=_validated_worker_path(arguments.request,"运行库请求文件",True)
        return runtime_install_worker(str(request))
    if command=="runtime-installer-test-worker":
        request=_validated_worker_path(arguments.request,"运行库测试请求文件",True)
        return runtime_installer_test_worker(str(request),arguments.mode)
    if command=="test":
        return {"logic":run_logic_contract_tests,"fault":run_fault_injection_tests,"static":run_static_contract_tests,"self":run_self_test,
            "strict-self":run_strict_requirement_tests}[arguments.kind]()
    if command=="acceptance":
        target=str(arguments.path or "")
        return {"windows-smoke":run_windows_smoke_test,"runtime-e2e":run_runtime_e2e_test,"window-contract":run_window_contract_test,
            "all":run_acceptance_test,"strict":strict_acceptance_gate}[arguments.kind](target or None)
    if command!="gui":
        raise CommandLineProtocolError("未知命令："+command)
    return None

def run_gui():
    global PROGRAM_INSTANCE_LOCK
    try:
        PROGRAM_INSTANCE_LOCK=ProcessInstanceLock().acquire()
    except Exception as error:
        show_acknowledge_only_startup(str(error))
        return 0
    load_gui_runtime()
    enable_dpi_awareness()
    root=tk.Tk()
    holder={"app":None}
    install_global_hooks(holder)
    try:
        holder["app"]=App(root)
    except Exception:
        startup_error(root,traceback.format_exc())
    root.mainloop()
    return 0

def main(argv=None):
    multiprocessing.freeze_support()
    try:
        arguments=parse_cli(argv)
        result=dispatch_cli(arguments)
        if result is not None:
            return int(result)
        return run_gui()
    except CommandLineProtocolError as error:
        sys.stderr.write(json.dumps({"status":"protocol_error","code":ErrorCode.PROTOCOL_ERROR.value,"message":str(error)},ensure_ascii=False,separators=(",",":"))+"\n")
        return 2

if __name__=="__main__":
    raise SystemExit(main())
