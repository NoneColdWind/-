"""
上班优搬来的......
"""

import time
import sys
import traceback
import os
import threading
import ctypes
from threading import Thread
from typing import (List, Tuple, Optional, Union, Dict, Any, SupportsIndex, Generic,
                    Literal, final, overload, TypeVar, Callable, Iterable, Iterator)
from collections import OrderedDict
import datetime
import copy
import math
import inspect
from queue import Queue
import platform
from typing_extensions import Iterable, Mapping
import inspect
from typing import Callable

try:
    from src.system import system, SystemLogger
except:
    from system import system, SystemLogger

from abc import ABC, abstractmethod
import random

if sys.stdout is None:
    if sys.__stdout__ is None:
        sys.stdout = open(os.getcwd() + "/log/log_{}_stdout.log".format(datetime.datetime.now().strftime("%Y%m%d%H%M%S")), "w", encoding="utf-8")
        sys.stderr = open(os.getcwd() + "/log/log_{}_stderr.log".format(datetime.datetime.now().strftime("%Y%m%d%H%M%S")), "w", encoding="utf-8")
        sys.__stdout__ = sys.stdout
        sys.__stderr__ = sys.stderr
    else:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

class SupportsKeyOrder(ABC):
    # 注：Supports是支持的意思（
    # 还有，其实把鼠标悬浮在"SupportsKeyOrder"上就可以看到这个注释了，经过美化了的
    """支持key排序的抽象类。
    
        意思就是说这个类有一个``key``属性，这个属性是``str``类型

        这个``SupportsKeyOrder``是为了方便使用而设计的，因为很多类都需要一个``key``属性

        （比如``ScoreModifactionTemplate``的``key``就表示模板本身的标识符）

        只要这个类实现了``key``属性，那么就可以使用``OrderedKeyList``（后面有讲）来存储这个类

        （比如``OrderedKeyList[ScoreModificationTemplate]``）

        还有，只要继承这个类，然后自己写一下key的实现，就可以直接使用``OrderedKeyList``来存储这个类了

        就像这样：
        >>> class SomeClassThatSupportsKeyOrder(SupportsKeyOrder):
        ...     def __init__(self, key: str):
        ...         self.key = key      # 在一个OrderedKeyList里面每一个元素都有自己的key
        ...                             # 至于这个key表示的是什么就由你来决定了
        ...                             # 但是但是，这个key只能是str，因为int拿来做索引值了，float和tuple(元组)之类的懒得写


    以前以来我们都用``collections.OrderedDict``来寻找模板，比如这样

    >>> DEFAULT_SCORE_TEMPLATES: OrderedDict[str, ScoreModificationTemplate] = OrderedDict([
    ...   "go_to_school_early": ScoreModificationTemplate("go_to_school_early", 1.0, "7:20前到校", "早起的鸟儿有虫吃"),
    ...   "go_to_school_late": ScoreModificationTemplate("go_to_school_late", -1.0, "7:25后到校", "早起的虫儿被鸟吃"),
    ... ])
    >>> DEFAULT_SCORE_TEMPLATES["go_to_school_early"]
    ScoreModificationTemplate("go_to_school_early", 1.0,  "7:20前到校", "早起的鸟儿有虫吃")

    这样做的好处是我们可以直接通过key来获取模板，也可以通过模板反向找到它的key值
    
    但是缺点是如果``OrderedDict``中的key和``ScoreModification``中的key不一致就会出错
    
    现在我们可以用``OrderedKeyList``来存储模板这类"SupportsKeyOrder"的对象，就不用写dict的key

    这样就不用担心dict中的key和模板中的不一样了

    >>> DEFAULT_SCORE_TEMPLATES = OrderedKeyList([
    ...   ScoreModificationTemplate("go_to_school_early", 1.0, "7:20前到校", "早起的鸟儿有虫吃"),
    ...   ScoreModificationTemplate("go_to_school_late", -1.0, "7:25后到校", "早起的虫儿被鸟吃"),
    ... ])   # 这就不需要写Key了，而且这个东西支持所有list的方法和部分dict的方法
    >>>      #（比如append，keys和items之类）
    >>> DEFAULT_SCORE_TEMPLATES[0]
    ScoreModificationTemplate("go_to_school_early", 1.0, "7:20前到校", "早起的鸟儿有虫吃")
    >>> DEFAULT_SCORE_TEMPLATES["go_to_school_early"]
    ScoreModificationTemplate("go_to_school_early", 1.0, "7:20前到校", "早起的鸟儿有虫吃")

    你学废了吗？
    """



_Template = TypeVar("_Template", bound=SupportsKeyOrder)
"""这东西不用管，写类型注释用的，方便理解

（可以理解为写在类型注释里的一个变量，绑定``SupportsKeyOrder``的类，传进去什么类型就传出来什么类型）

如果你给一个``OrderedKeyList``初始值是``ScoreModificationTemplate``的列表，他就会自动识别为``OrderedKeyList[ScoreModificationTemplate]``

那么这个``OrderedKeyList``迭代或者取值的时候VSCode就会知道取出来的东西ScoreModificationTemplate，就方便查看它的属性和方法，肥肠方便

（但是对于写类型注释的人并不方便）
"""


class OrderedKeyList(list, Iterable[_Template]):
    """有序的key列表，可以用方括号来根据SupportsKeyOrder对象的key，索引值或者对象本身来获取对象

    举个例子

    建立一个新的OrderedKeyList
    >>> template = ScoreModificationTemplate("go_to_school_late_more", -2.0, "7:30后到校", "哥们为什么不睡死在家里？")
    >>> # 这里有一个存在变量里面的模板，我们叫它template
    >>> DEFAULT_SCORE_TEMPLATES = OrderedKeyList([
    ...   ScoreModificationTemplate("go_to_school_early", 1.0, "7:20前到校", "早起的鸟儿有虫吃"),
    ...   ScoreModificationTemplate("go_to_school_late", -1.0, "7:25后到校", "早起的虫儿被鸟吃"),
    ...   template
    ... ])

    获取里面的元素
    >>> DEFAULT_SCORE_TEMPLATES[0]
    ScoreModificationTemplate("go_to_school_early", 1.0, "7:20前到校", "早起的鸟儿有虫吃")
    >>> DEFAULT_SCORE_TEMPLATES["go_to_school_early"]
    ScoreModificationTemplate("go_to_school_early", 1.0, "7:20前到校", "早起的鸟儿有虫吃")
    >>> DEFAULT_SCORE_TEMPLATES[template]
    ScoreModificationTemplate("go_to_school_late_more", -2.0, "7:30后到校", "哥们为什么不睡死在家里？")
    >>> DEFAULT_SCORE_TEMPLATES.keys()
    ["go_to_school_early", "go_to_school_late", "go_to_school_late"]
    >>> len(DEFAULT_SCORE_TEMPLATES)
    3

    添加元素
    >>> DEFAULT_SCORE_TEMPLATES.append(ScoreModificationTemplate("Chinese_class_good", 2.0,"语文课堂表扬","王の表扬"))
    >>> DEFAULT_SCORE_TEMPLATES.append(template) # 这里如果设置了不允许重复的话还往里面放同一个模板就会报错
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
        DEFAULT_SCORE_TEMPLATES.append(template)
      File "<stdin>", line 166, in append
        raise ValueError(F"模板的key（{getattr(v, self.keyattr)!r}）重复")
    ValueError: 模板的key（'go_to_school_late_more'）重复


    交换里面的元素顺序
    >>> DEFAULT_SCORE_TEMPLATES.swaps(0, 1)     # 交换索引0和1的元素，当然也可以填模板的key
    OrderedKeyList([
        ScoreModificationTemplate("go_to_school_late", -1.0, "7:25后到校", "早起的虫儿被鸟吃"),
        ScoreModificationTemplate("go_to_school_early", 1.0, "7:20前到校", "早起的鸟儿有虫吃"),
        ScoreModificationTemplate("go_to_school_late_more", -2.0, "7:30后到校", "哥们为什么不睡死在家里？")
    ])

    删掉/修改里面的元素
    >>> del DEFAULT_SCORE_TEMPLATES["go_to_school_early"]    # 删除key为"go_to_school_early"的元素
    >>> DEFAULT_SCORE_TEMPLATES.pop(0)                       # 删除索引为0的元素
    >>> len(DEFAULT_SCORE_TEMPLATES)                         # 查看长度（现在只剩一个7:30以后到校的了）
    1

    """

    allow_dumplicate = False
    "是否允许key重复"

    dumplicate_suffix = "_copy"
    "key重复时自动添加的后缀（如果允许放行重复的key进到列表里）"

    keyattr = "key"
    'SupportsKeyOrder的这个"Key"的属性名'


    def __init__(self, objects: Union[Iterable[_Template], 
                                        Dict[str, _Template], 
                                        "OrderedDict[str, _Template]", 
                                        "OrderedKeyList[_Template]"]):
        """初始化OrderedKeyList
        
        :param templates: 模板列表
        """

        super().__init__()
        if isinstance(objects, (dict, OrderedDict)):
            for k, v in objects.items():
                if getattr(v, self.keyattr) != k:
                    Base.log("W", F"模板在dict中的key（{k!r}）与模板本身的（{getattr(v, self.keyattr)!r}）不一致，"
                                    "已自动修正为dict中的key", "OrderedTemplateGroup.__init__")
                    setattr(v, self.keyattr, k)
                self.append(v)
        elif isinstance(objects, OrderedKeyList):
            self.extend([t for t in objects])
        else:
            keys = []
            for v in objects:
                if getattr(v, self.keyattr) in keys:
                    if not self.allow_dumplicate:
                        raise ValueError(F"模板的key（{getattr(v, self.keyattr)!r}）重复")
                    Base.log("W", F"模板的key（{getattr(v, self.keyattr)!r}）重复，补充为{getattr(v, self.keyattr)!r}{self.dumplicate_suffix}", "OrderedTemplateGroup.__init__")
                    setattr(v, self.keyattr, getattr(v, self.keyattr) + self.dumplicate_suffix)
                keys.append(getattr(v, self.keyattr))
                self.append(v)

    def __getitem__(self, key: Union[int, str, _Template]) -> _Template:
        "返回指定索引或key的模板"
        if isinstance(key, int):
            return super().__getitem__(key)
        else:
            for obj in self:
                if getattr(obj, self.keyattr) == key:
                    return obj
            for obj in self:
                if obj is key:
                    return obj
            raise KeyError(F"列表中不存在key为{key!r}的模板")

    def __setitem__(self, key: Union[int, str, _Template], value: _Template):
        "设置指定索引或key的模板"
        if isinstance(key, int):
            super().__setitem__(key, value)
        else:
            for i, obj in enumerate(self):
                if getattr(obj, self.keyattr) == key:
                    super().__setitem__(i, value)
                    return
                elif obj is key:
                    super().__setitem__(i, value)
            if getattr(value, self.keyattr) == key and isinstance(value, SupportsKeyOrder) and isinstance(key, str):
                self.append(value)  # 如果key是字符串，并且value是模板，则直接添加到列表中
            else:
                raise KeyError(F"列表中不存在key为{key!r}的模板")
        
    
    def __delitem__(self, key: Union[int, str]):
        "删除指定索引或key的模板"
        if isinstance(key, int):
            super().__delitem__(key)
        else:
            for i, obj in enumerate(self):
                if getattr(obj, self.keyattr) == key:
                    super().__delitem__(i)
                    return
            raise KeyError(F"列表中不存在key为{key!r}的模板")

    def __len__(self) -> int:
        "返回列表中模板的数量"
        return super().__len__()


    def __reversed__(self) -> Iterator[_Template]:
        "返回列表的反向迭代器"
        return super().__reversed__()

    def __contains__(self, item: _Template) -> bool:
        "判断列表中是否包含指定模板"
        return super().__contains__(item) or [getattr(obj, self.keyattr) for obj in self].count(item) > 0

    def swaps(self, lh: Union[int, str], rh: Union[int, str]):
        "交换指定索引或key的模板"
        if  isinstance(lh, str):
            for i, obj in enumerate(self):
                if getattr(obj, self.keyattr) == lh:
                    lh = i
                    break
            else:
                raise KeyError(F"列表中不存在key为{lh!r}的模板")
        if isinstance(rh, str):
            for i, obj in enumerate(self):
                if getattr(obj, self.keyattr) == rh:
                    lh = i
                    break
            else:
                raise KeyError(F"列表中不存在key为{rh!r}的模板")
        self[lh], self[rh] = self[rh], self[lh]
        return self
    
    def __iter__(self) -> Iterator[_Template]:
        "返回列表的迭代器"
        return super().__iter__()

    def append(self, obj: _Template):
        "添加到列表"
        if getattr(obj, self.keyattr) in self.keys():
            if not self.allow_dumplicate:  # 如果不允许重复直接抛出异常
                raise ValueError(F"模板的key（{getattr(obj, self.keyattr)!r}）重复")
            Base.log("W", F"模板的key（{getattr(obj, self.keyattr)!r}）重复，补充为{getattr(obj, self.keyattr)!r}{self.dumplicate_suffix}", "OrderedTemplateGroup.append")
            setattr(obj, self.keyattr, getattr(obj, self.keyattr) + self.dumplicate_suffix)
        super().append(obj)
        return self

    def extend(self, templates: Iterable[_Template]):
        "扩展列表"
        for template in templates:
            self.append(template)
        return self
    
    def keys(self) -> List[str]:
        "返回列表中所有元素的key"
        return [getattr(obj, self.keyattr) for obj in self]
    
    def values(self) -> List[_Template]:
        "返回列表中所有模板"
        return [obj for obj in self]

    def items(self) -> List[Tuple[str, _Template]]:
        "返回列表中所有模板的key和模板"
        return [(getattr(obj, self.keyattr), obj) for obj in self]
    

    def __copy__(self) -> "OrderedKeyList[_Template]":
        "返回列表的浅拷贝"
        return OrderedKeyList(self)
    
    def __deepcopy__(self, memo: dict) -> "OrderedKeyList[_Template]":
        "返回列表的深拷贝"
        return OrderedKeyList([copy.deepcopy(obj, memo) for obj in self])
    
    def copy(self) -> "OrderedKeyList[_Template]":
        "返回列表的拷贝"
        return self.__copy__()

    
    def __repr__(self) -> str:
        "返回列表的表达式"
        return F"OrderedTemplateGroup({super().__repr__()})"

def utc(precision:int=3):
    """返回当前时间戳

    :param precision: 精度，默认为3
    """
    return int(time.time() * pow(10, precision))

def get_function_namespace(func) -> str:
    "获取函数的命名空间"
    module = inspect.getmodule(func)
    if not hasattr(func, "__module__"):
        try:
            return func.__qualname__
        except:
            try:
                return func.__name__
            except:
                if isinstance(func, property):
                    return str(func.fget.__qualname__)
                elif isinstance(func, classmethod):
                    return str(func.__func__.__qualname__)
                try:
                    return func.__class__.__qualname__
                except:
                    return func.__class__.__name__            
    if module is None:
        module_name = func.__self__.__module__ if hasattr(func, "__self__") else func.__module__
    else:
        module_name = module.__name__

    return f"{module_name}.{func.__qualname__}"

def format_exc_like_java(exc: Exception) -> List[str]:
    "不是我做这东西有啥用啊"
    result = [f"{get_function_namespace(exc.__class__)}: " + (str(exc) if str(exc).strip() else "no further information"), "Stacktrace:"]
    tb = exc.__traceback__
    while tb is not None:
        frame = tb.tb_frame
        filename = frame.f_code.co_filename
        filename_strip = os.path.basename(filename)
        lineno = tb.tb_lineno
        funcname = frame.f_code.co_name
        _locals = frame.f_locals.copy()
        instance = None
        method_obj = None
        for i in _locals.values():
            if isinstance(i, object) and hasattr(i, "__class__"):
                instance = i
                class_obj = instance.__class__
                method_obj = getattr(class_obj, funcname, None)
                if method_obj:
                    break
        if instance and method_obj:
            full_path = get_function_namespace(method_obj)
            result.append(f"  at {full_path}({filename_strip}:{lineno})")
        else:
            func_obj = frame.f_globals.get(funcname) or frame.f_locals.get(funcname)
            if func_obj:
                qualname = get_function_namespace(func_obj)
                result.append(f"  at {qualname}({filename_strip}:{lineno})")
        tb = tb.tb_next
    return result

from ctypes import c_int, c_int8, c_int16, c_int32, c_int64, c_uint, c_uint8, c_uint16, c_uint32, c_uint64

_cinttype = Union[int, c_int, c_uint, c_int8, c_int16, c_int32, c_int64, c_uint8, c_uint16, c_uint32, c_uint64]

def cinttype(dtype: _cinttype, name: Optional[str] = None):
    """搓了一个我自己的cint类型（bushi
    
    :param dtype: 要继承的数据类型
    :param name:  类名
    :return: 继承了cint类型的类

    byd越来越癫了
    """
    if name is None:
        name = dtype.__name__
    class _CIntType:
        "继承cint类型的类"
        
        def __init__(self, value: _cinttype):
            try:
                value = int(value)
            except:
                value = int(value.value)

            self._dtype: _cinttype = dtype
            self._data: _cinttype = self._dtype(value)
            self._tpname: str = name

        
        def __str__(self):
            return str(self._data.value)
        
        def __repr__(self):
            return f"{self._tpname}({repr(self._data.value)})"
        
        def __int__(self):
            return int(self._data.value)
        
        def __float__(self):
            return float(self._data.value)
        
        def __bool__(self):
            return bool(self._data.value)
        
        def __hash__(self):
            return hash(self._data.value)
        
        def __eq__(self, other):
            if other == inf:
                return False
            if other == -inf:
                return False
            if math.isnan(other):
                return False
            return self._data.value == int(other)
        
        def __ne__(self, other):
            if other == inf:
                return True
            if other == -inf:
                return True
            if math.isnan(other):
                return True
            return self._data.value != int(other)
        
        def __lt__(self, other):
            if other == inf:
                return True
            if other == -inf:
                return False
            if math.isnan(other):
                return False
            return self._data.value < int(other)
        
        def __le__(self, other):
            if other == inf:
                return True
            if other == -inf:
                return False
            if math.isnan(other):
                return False
            return self._data.value <= int(other)
        
        def __gt__(self, other):
            if other == inf:
                return False
            if other == -inf:
                return True
            if math.isnan(other):
                return False
            return self._data.value > int(other)
        
        def __ge__(self, other):
            if other == inf:
                return True
            if other == -inf:
                return True
            if math.isnan(other):
                return False
            return self._data.value >= int(other)
        
        def __abs__(self):
            return cinttype(self._dtype, self._tpname)(abs(self._data.value))
        
        def __neg__(self):
            return cinttype(self._dtype, self._tpname)(-self._data.value)
        
        def __pos__(self):
            return cinttype(self._dtype, self._tpname)(+self._data.value)
    
        def __round__(self, ndigits=None):
            return cinttype(self._dtype, self._tpname)(round(self._data.value, ndigits))
        
        def __add__(self, other: Any):
            return cinttype(self._dtype, self._tpname)(self._data.value + int(other))
        
        def __sub__(self, other):
            return cinttype(self._dtype, self._tpname)(self._data.value - int(other))
        
        def __mul__(self, other):
            return cinttype(self._dtype, self._tpname)(self._data.value * int(other))
        
        def __truediv__(self, other):
            return cinttype(self._dtype, self._tpname)(self._data.value / int(other))
        
        def __floordiv__(self, other):
            return cinttype(self._dtype, self._tpname)(self._data.value // int(other))
        
        def __mod__(self, other):
            return cinttype(self._dtype, self._tpname)(self._data.value % int(other))
        
        def __pow__(self, other):
            return cinttype(self._dtype, self._tpname)(self._data.value ** int(other))
        
        def __lshift__(self, other):
            return cinttype(self._dtype, self._tpname)(self._data.value << int(other))
        
        def __rshift__(self, other):
            return cinttype(self._dtype, self._tpname)(self._data.value >> int(other))
        
        def __and__(self, other):
            return cinttype(self._dtype, self._tpname)(self._data.value & int(other))
        
        def __or__(self, other):
            return cinttype(self._dtype, self._tpname)(self._data.value | int(other))
        
        def __xor__(self, other):
            return cinttype(self._dtype, self._tpname)(self._data.value ^ int(other))
        
        def __invert__(self):
            return cinttype(self._dtype, self._tpname)(~self._data.value)
        
        def __iadd__(self, other):
            self._data.value += int(other)
            return cinttype(self._dtype, self._tpname)(self._data.value)

        def __isub__(self, other):
            self._data.value -= int(other)
            return cinttype(self._dtype, self._tpname)(self._data.value)

        def __imul__(self, other):
            self._data.value *= int(other)
            return cinttype(self._dtype, self._tpname)(self._data.value)

        def __itruediv__(self, other):
            self._data.value /= int(other)
            return cinttype(self._dtype, self._tpname)(self._data.value)

        def __ifloordiv__(self, other):
            self._data.value //= int(other)
            return cinttype(self._dtype, self._tpname)(self._data.value)

        def __imod__(self, other):
            self._data.value %= int(other)
            return cinttype(self._dtype, self._tpname)(self._data.value)

        def __ipow__(self, other):
            self._data.value **= int(other)
            return cinttype(self._dtype, self._tpname)(self._data.value)

        def __ilshift__(self, other):
            self._data.value <<= int(other)
            return cinttype(self._dtype, self._tpname)(self._data.value)

        def __irshift__(self, other):
            self._data.value >>= int(other)
            return cinttype(self._dtype, self._tpname)(self._data.value)

        def __iand__(self, other):
            self._data.value &= int(other)
            return cinttype(self._dtype, self._tpname)(self._data.value)

        def __ior__(self, other):
            self._data.value |= int(other)
            return cinttype(self._dtype, self._tpname)(self._data.value)
        
        def __ixor__(self, other):
            self._data.value ^= int(other)
            return cinttype(self._dtype, self._tpname)(self._data.value)

    return _CIntType


int8   = byte             = cinttype(c_int8,   "byte")
int16  = short            = cinttype(c_int16,  "short")
int32  = integer          = cinttype(c_int32,  "integer")
int64  = qword            = cinttype(c_int64,  "qword")
uint8  = unsigned_byte    = cinttype(c_uint8,  "unsigned_byte")
uint16 = unsigned_short   = cinttype(c_uint16, "unsigned_short")
uint32 = unsigned_integer = cinttype(c_uint32, "unsigned_integer")
uint64 = unsigned_qword   = cinttype(c_uint64, "unsigned_qword")


    




def get_function_module(func: Union[object, Callable]) -> str:
    "获取函数的模块"
    module = inspect.getmodule(func)
    if module is None:
        module_name = func.__self__.__module__ if hasattr(func, "__self__") else func.__module__
    else:
        module_name = module.__name__
    return module_name

cwd = os.getcwd()
"当前工作目录"

bs = "\\"

debug = True
"是否为调试模式"

LOG_FILE_PATH = os.getcwd() + "/log/log_{}.log".format(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
LOG_FILE_PATH = LOG_FILE_PATH.replace("/" if platform.platform() == "Windows"  else "\\", "\\" if platform.platform() == "Windows" else "/")
"日志文件名"

function = type(lambda: None)
"函数类型"


SOUND_BRUH = os.getcwd() + "/res/sounds/bruh.mp3"
"bruh"

class NULLPTR:
    "虽然没用"
    def __eq__(self, value: object) -> bool:
        return isinstance(value, NULLPTR)
    
    def __ne__(self, value: object) -> bool:
        return not isinstance(value, NULLPTR)

    def __str__(self) -> str:
        return "nullptr"

    def __repr__(self) -> str:
        return "nullptr"
    
    def __hash__(self):
        return -1
    
    def __bool__(self):
        return False
    

null = NULLPTR()
"空指针"

if not os.path.isdir("log"):
    os.mkdir("log")

# 先把所有的输出流存起来作为备份
stdout_orig = sys.stdout
stderr_orig = sys.stderr


NoneType = type(None)

function = Callable



class Stack:
    "非常朴素的栈"

    def __init__(self):
        "初始化栈"
        self.items = []

    def is_empty(self):
        "判断栈是否为空"
        return self.items == []

    def push(self, item):
        "添加元素到栈顶"
        self.items.append(item)

    def pop(self):
        "移除栈顶元素并返回该元素"
        return self.items.pop()

    def peek(self):
        "返回栈顶元素"
        return self.items[len(self.items) - 1]

    def size(self):
        "返回栈的大小"
        return len(self.items)

    def clear(self):
        "清空栈"
        self.items = []


def steprange(start:Union[int, float], stop:Union[int, float], step:int) -> List[float]:
    """生成step步长的从start到stop的列表
    
    :param start: 起始值
    :param stop: 结束值
    :param step: 步长
    :return: 从start到stop的列表

    :example:
    >>> steprange(0, 10, 5)
    [0, 2.5, 5.0, 7.5, 10]
    """
    if (stop - start) % step != 0:
        return [start + i * (int(stop - start) / step) for i in range(step)][:-1] + [stop]
    else:
        return [start + i * (int(stop - start) / (step - 1)) for i in range(step)]

class Thread(threading.Thread):
    "自己做的一个可以返回数据的Thread"

    def __init__(
            self,
            group: None = None,
            target: Optional[Callable] = None,
            name: Optional[str] = None,
            args: Iterable[Any] = None,
            kwargs: Optional[Mapping[str, Any]] = None,
            *,
            daemon: Optional[bool] = None) -> None:
        """初始化线程
        
        :param group: 线程组，默认为None
        :param target: 线程函数，默认为None
        :param name: 线程名称，默认为None
        :param args: 线程函数的参数，默认为空元组
        :param kwargs: 线程函数的关键字参数，默认为None
        """
        args = () if args is None else args
        kwargs = {} if kwargs is None else kwargs
        super().__init__(group=group, target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)
        self._return = None
        self._finished = False
        
    @property
    def return_value(self):
        "返回线程的返回值"
        if self._finished:
            return self._return
        else:
            raise RuntimeError("线程并未执行完成")
    

    def run(self):
        "运行线程"
        self.thread_id = ctypes.CFUNCTYPE(ctypes.c_long) (lambda: ctypes.pythonapi.PyThread_get_thread_ident()) ()
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)
        self._finished = True
        

    def join(self, timeout:Optional[float]=None) -> Any:
        """"等待线程完成并返回结果
        
        :param timeout: 超时时间，默认为None，表示无限等待"""
        super().join(timeout=timeout)
        return self._return



inf = float("inf")
"无穷大"

ninf = float("-inf")
"无穷小"

nan = float("nan")
"非数"

    


class ModifyingError(Exception):"修改出现错误。"



import colorama

colorama.init(autoreset=True)
class Color:
    """颜色类（给终端文字上色的）
    
    :example:
    
    >>> print(Color.RED + "Hello, " + Color.End + "World!")
    Hello, World!       (红色Hello，默认颜色的World)
    
    """
    RED     =   colorama.Fore.RED
    "红色"
    GREEN   =   colorama.Fore.GREEN
    "绿色"
    YELLOW  =   colorama.Fore.YELLOW
    "黄色"
    BLUE    =   colorama.Fore.BLUE
    "蓝色"
    MAGENTA =   colorama.Fore.MAGENTA
    "品红色"
    CYAN    =   colorama.Fore.CYAN
    "青色"
    WHITE   =   colorama.Fore.WHITE
    "白色"
    BLACK   =   colorama.Fore.BLACK
    "黑色"
    END     =   colorama.Fore.RESET
    "着色结束"
    @staticmethod
    @final
    def from_rgb(r:int, g:int, b:int) -> str:
        "从RGB数值中生成颜色"
        return f"\033[38;2;{r};{g};{b}m"

log_file = open(LOG_FILE_PATH, "a", buffering=1, encoding="utf-8")

class Mutex:
    "一个简单的互斥锁"
    def __init__(self):
        self.locked = False

    def lock(self):
        "锁定"
        if self.locked:
            raise RuntimeError("互斥锁已经被锁定")
        self.locked = True

    def unlock(self):
        "解锁"
        if not self.locked:
            raise RuntimeError("互斥锁没有被锁定")
        self.locked = False

    def __enter__(self):
        self.lock()
    
    def __exit__(self, exc_type:type, exc_val:Exception, exc_tb:traceback.StackSummary):
        self.unlock()



class FrameCounter:
    "帧计数器"
    def __init__(self, maxcount: Optional[int] = None, timeout: Optional[float] = None):
        "初始化帧计数器"
        self.maxcount = maxcount
        self.timeout = timeout
        self._c = 0
        self.running = False
        
    @property
    def _t(self):
        "获取当前时间戳"
        return time.time()
    
    @property
    def framerate(self):
        "获取帧率"
        if self._c == 0 or not self.running:
            return 0
        return self._c / self._t


    def start(self):
        "启动计数器"
        if self.running:
            raise RuntimeError("这个计数器已经启动过了！")
        self._c = 0
        self.running = True
        while (self.maxcount is None or self._c < self.maxcount) and (self.timeout is None or time.time() - self._t <= self.timeout) and self.running:
            self._c += 1

    def stop(self):
        "停止计数器"
        self.running = False



class Object(object):
    "一个基础类"
    def copy(self):
        "给自己复制一次，两个对象不会互相影响"
        return copy.deepcopy(self)

    def __repr__(self):
        "返回这个对象的表达式"
        return f"{self.__class__.__name__}({', '.join([f'{k}={v!r}' for k, v in self.__dict__.items() if not k.startswith('_')])})"
        # 我个人认为不要把下划线开头的变量输出出来（不过只以一个下划线开头的还得考虑考虑）
    

class Base(Object):
    "工具基层"
    log_file = log_file
    "日志文件"
    fast_log_file = open("log_buffered.txt", "a", buffering=1, encoding="utf-8")
    "临时日志文件（现在没用了）"
    stdout_orig = stdout_orig
    "标准输出"
    stderr_orig = stderr_orig
    "标准错误"
    stdout = SystemLogger(sys.stdout, logger_name="sys.stdout", level="I", function=lambda l, m, s: Base.log(l, m, s))
    "经过处理的输出"
    stderr = SystemLogger(sys.stderr, logger_name="sys.stderr", level="E", function=lambda l, m, s: Base.log(l, m, s))
    "经过处理的错误输出"
    window_log_queue = Queue()
    "主窗口显示日志的队列（每一个项目是一行的字符串）"
    console_log_queue = Queue()
    "控制台日志队列"
    logfile_log_queue = Queue()
    "日志文件日志队列"
    log_mutex = Mutex()
    "记录日志的互斥锁（现在没用了）"
    log_file_keepcount = 20
    "日志文件保留数量"
    _writing = False
    "没用的东西"
    thread_id = ctypes.CFUNCTYPE(ctypes.c_long) (lambda: ctypes.pythonapi.PyThread_get_thread_ident()) ()
    "当前进程的pid"
    thread_name = threading.current_thread().name
    "当前进程的名称"
    thread = threading.current_thread()
    "当前进程的线程对象"
    logger_running = True
    "日志记录器是否在运行（我自己都不知道有没有用，忘了）"
    log_level:Literal["I", "W", "E", "F", "D", "C"] = "D"
    "日志记录器等级"


    @staticmethod
    def utc(precision:int=3):
        """返回当前时间戳

        :param precision: 精度，默认为3
        """
        return int(time.time() * pow(10, precision))


    @staticmethod
    def gettime():
        "获得当前时间"
        lt = time.localtime()
        return F"{lt.tm_year}-{lt.tm_mon:02}-{lt.tm_mday:02} {lt.tm_hour:02}:{lt.tm_min:02}:{lt.tm_sec:02}.{int((time.time()%1)*1000):03}"

    @staticmethod
    def log(type:Literal["I", "W", "E", "F", "D", "C"], msg:str, source:str="MainThread"):
                """
                向控制台和日志输出信息

                :param type: 类型
                :param msg: 信息
                :param send: 发送者
                :return: None
                """
                # 如果日志等级太低就不记录
                if (type == "D" and Base.log_level not in ("D"))                \
                or (type == "I" and Base.log_level not in ("D", "I"))            \
                or (type == "W" and Base.log_level not in ("D", "I", "W"))        \
                or (type == "E" and Base.log_level not in ("D", "I", "W", "E"))    \
                or (type == "F" or type == "C" and Base.log_level not in ("D", "I", "W", "E", "F", "C")):
                    return

                if not isinstance(msg, str):
                    msg = msg.__repr__()
                for m in msg.splitlines():
                    if type == "I":
                        color = Color.GREEN
                    elif type == "W":
                        color = Color.YELLOW
                    elif type == "E":
                        color = Color.RED
                    elif type == "F" or type == "C":
                        color = Color.MAGENTA
                    elif type == "D":
                        color = Color.CYAN
                    else:
                        color = Color.WHITE
                    
                    if not m.strip():
                        continue
                    frame = inspect.currentframe()
                    lineno = frame.f_back.f_lineno
                    file = frame.f_back.f_code.co_filename.replace(cwd, "")
                    if file == "<string>":
                        lineno = 0
                    if file.startswith(("/", "\\")):
                        file = file[1:]
                    cm = f"{Color.BLUE}{Base.gettime()}{Color.END} {color}{type}{Color.END} {Color.from_rgb(50, 50, 50)}{source.ljust(35)}{color} {m}{Color.END}"
                    lm = f"{Base.gettime()} {type} {(source).ljust(35)} {m}" 
                    lfm = f"{Base.gettime()} {type} {(source + f' -> {file}:{lineno}').ljust(60)} {m}"
                    Base.window_log_queue.put(lm)
                    Base.console_log_queue.put(cm)
                    # Base.logfile_log_queue.put(lfm)
                    Base.log_file.write(lfm + "\n")
                    # print(lfm, file=Base.fast_log_file)
                    Base.log_file.flush()

    @staticmethod
    def log_thread_logfile():
        "把日志写进日志文件的线程的运行函数"
        while Base.logger_running:
            s = Base.logfile_log_queue.get()
            Base.log_file.write(s + "\n")
            Base.log_file.flush()


    @staticmethod
    def log_thread_console():
        "把日志写在终端的线程的运行函数"
        while Base.logger_running:
            s = Base.console_log_queue.get()
            Base.stdout_orig.write(s + "\n")
            Base.stdout_orig.flush()

    @staticmethod
    def stop_loggers():
        "停止所有日志记录器"
        Base.logger_running = False

    console_log_thread = Thread(target=lambda: Base.log_thread_console(), daemon=True, name="ConsoleLogThread")
    "把日志写在终端的线程的线程对象"
    logfile_log_thread = Thread(target=lambda: Base.log_thread_logfile(), daemon=True, name="LogfileLogThread")
    "把日志写进日志文件的线程的线程对象"

    from abc import abstractmethod
    abstract = abstractmethod
    "抽象方法"

    @staticmethod
    def clear_oldfile(keep_count:int=10):
        "清理日志文件"
        if not os.path.exists(LOG_FILE_PATH):
            return
        log_files = sorted([f for f in os.listdir(os.path.dirname(LOG_FILE_PATH)) if f.startswith("log_") and f.endswith(".log")], reverse=True)
        if len(log_files) > keep_count:
            for f in log_files[keep_count:]:
                os.remove(os.path.join(os.path.dirname(LOG_FILE_PATH), f))
    
    @staticmethod
    def read_ini(filepath:str="options.ini",encoding="utf-8",nospace:bool=True) -> Union[int,Dict[str,Union[bool,str]]]:
        """读取一个写满了<变量名>=<值>的文本文件然后返回一个字典
        
        :param filepath: 文件路径
        :param encoding: 编码
        :param nospace: 是否去除空格
        :return: 一个dict
        """
        reading_file = open(filepath,encoding=encoding,mode="r",errors="ignore")
        content = reading_file.readlines()
        reading_file.close()
        if len(content) == 0:
            return {}
        output = {}
        for i in range(len(content)):
            try:
                line_setting = str(content[i]).split("=",2)
                prop = str(line_setting[0])   
                value = line_setting[1].split("\n",1)[0]
                if nospace:value = value.replace(" ","")
                if value.upper() == "FALSE": value = False
                if value.upper() == "TRUE":  value = True
                output[prop]=value
            except:
                continue
        return output  

    @staticmethod
    def log_exc(info:str="未知错误：", 
                sender="MainThread -> Unknown", 
                level:Literal["I", "W", "E", "F", "D", "C"]="E", 
                exc:Exception=None):
        """向控制台和日志报错。
        
        :param info: 信息
        :param sender: 发送者
        :param level: 级别
        :param exc: 指定的Exception，可以不传（就默认是最近发生的一次）
        :return: None
        """
        if exc is None:
            exc = sys.exc_info()[1]
            if exc is None:
                return
        Base.log(level, "---------------------------ExceptionCaught-----------------------------", sender)
        Base.log(level, info, sender)
        Base.log(level, "-----------------------------------------------------------------------", sender)
        Base.log(level, ("").join(traceback.format_exception(exc.__class__, exc, exc.__traceback__)), sender)
        Base.log(level, "-----------------------------------------------------------------------", sender)
        Base.log(level, "\n".join(format_exc_like_java(exc)), sender)
        Base.log(level, "-----------------------------------------------------------------------", sender)

    @staticmethod
    def log_exc_short(info:str="未知错误：", 
                        sender="MainThread -> Unknown", 
                        level:Literal["I", "W", "E", "F", "D", "C"]="W", 
                        exc:Exception=None):
        if exc is None:
            exc = sys.exc_info()[1]
            if exc is None:
                return
        Base.log(level, f"{info} [{exc.__class__.__qualname__}] {exc}", sender)



Base.console_log_thread.start()
Base.logfile_log_thread.start()

app:Base