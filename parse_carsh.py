# -*- coding: utf-8 -*-

import os
import sys
import re
import shutil

#1.24.4.6387
PayloadProc = 0x0045DCC8

###############################################################
carsh_re = re.compile(r"\={78}[\s\S]*\-{78}")
war3_version_re = re.compile(r"Warcraft\ III\ \(build\ (?P<VERSION>[0-9]*)\)")
map_path_re = re.compile(r"Played (?P<MAP_PATH>.*)")
map_name_re = re.compile(r"([^\\]*\\)*(?P<MAP_NAME>[^\\]*)\.w3x")
stack_trace_manual_re = re.compile(r"\-{40}[\s]*Stack Trace \(Manual\)[\s]*\-{40}(?P<STACK_TRACE>[\s\S]*?)\-{40}")
stack_trace_re = re.compile(r"\-{40}[\s]*Stack Trace \(Using DBGHELP.DLL\)[\s]*\-{40}(?P<STACK_TRACE>[\s\S]*?)\-{40}")
loaded_modules_re = re.compile(r"\-{40}[\s]*Loaded Modules[\s]*\-{40}(?P<LOADED_MODULES>[\s\S]*?)\-{40}")
memory_dump_re = re.compile(r"\-{40}[\s]*Memory Dump[\s]*\-{40}(?P<MEMORY_DUMP>[\s\S]*?)\-{40}")
parse_loaded_modules_re = re.compile(r"0x(?P<BASE>[0-9A-Fa-f]{8})\ \-\ 0x[0-9A-Fa-f]{8}\ (?P<NAME>.*)")
parse_stack_re = re.compile(r"(?P<ADDR>[0-9A-Fa-f]{8})\ [0-9A-Fa-f]{8}\ (?P<ADDRHI>[0-9A-Fa-f]{4})\:(?P<ADDRLO>[0-9A-Fa-f]{8}) (?P<NAME>.*)")
parse_game_dll_re = re.compile(r"(\\|\/|\ )game\.dll")
parse_memory_dump_re = re.compile(r"(?P<ADDR>[0-9A-F]{2}\ [0-9A-F]{2}\ [0-9A-F]{2}\ [0-9A-F]{2})")
###############################################################
GameDllCarshList = {
'20ACF7':"非英雄单位吃属性书。",
'208760':"创建的非英雄单位有工程升级的技能。",
'36DF4E':"技能按钮的坐标越界。",
'5A45F6':"地图载入时随机出现，魔兽bug(?)。",
'477EB1':"准备释放技能/开始释放技能/发动技能效果事件里删除技能('AHav')。",
'4733C0':"准备释放技能/开始释放技能/发动技能效果事件里删除技能(大多数变身技能)。",
'3E16B4':"没有路径纹理的单位 变身/升级 为有路径纹理的单位。有路径纹理的单位 变身/升级 为没有路径纹理的单位。",
'371C51':"建造一个英雄建筑取消，再次建造时。",
'28D5B2':"超过一个非英雄单位变身为英雄。",
'0CE49D':"投射物命中可破坏物之前移除可破坏物",
'128505':"删除民兵的战斗号召(Amil)技能,在持续时间到之后弹错",
'0537CA':"治疗守卫(Ahwd)技能的召唤单位选项(UnitID1)为空 未设置单位类型 ",
'07E87C':"闪电之球(Aill)技能关联引导性持续施法的技能",
'25E208':"带有法球技能的炮火攻击类型的单位攻击地面",
'4DECE0':"战棍(Agra)技能以单位为目标",
}
###############################################################
CommonJCarshList = {
'SetUnitAbilityLevel':"修改死亡单位的光环技能。",
'IncUnitAbilityLevel':"修改死亡单位的光环技能。",
'UnitAddAbility'     :"给非英雄单位添加工程升级。",
'MoveLightningEx'    :"使用一个已经被删除的闪电。",
'MoveLightning'      :"使用一个已经被删除的闪电。",
'Player'             :"使用了0~15之外的值。",
'SetUnitX'           :"单位超出地图范围。",
'SetUnitY'           :"单位超出地图范围。",
'SetUnitPosition'    :"单位超出地图范围。",
'SetUnitPositionLoc' :"单位超出地图范围。",
'AddWeatherEffect'   :"effectID不存在/错误。",
}
###############################################################
def conver_hexstringt(s):
    return int(s[9:11] + s[6:8] + s[3:5] + s[0:2], 16)
###############################################################
def read_funclist():
    funclist = {}
    try:
        f  = file('funclist24e.txt', "r")
        try:
            for line in f:
                 funclist[line[0:8]] = line[9:-1]
        finally:
            f.close()
    except IOError:
        print '  ├-读取函数列表失败！'
    return funclist
###############################################################
def read_carsh(buf):
    try:
        return carsh_re.search(buf).group()
    except:
        return None
###############################################################
def read_war3_version(buf):
    try:
        return int(war3_version_re.search(buf).group('VERSION'))
    except:
        return 0
###############################################################
def read_map_path_and_name(buf):
    try:
        path = map_path_re.search(buf).group('MAP_PATH')
        name = map_name_re.match(path).group('MAP_NAME')
        return path, name
    except:
        return None, None
###############################################################
def read_stack_trace(buf):
    return stack_trace_re.search(buf).group('STACK_TRACE')
###############################################################
def read_loaded_modules(buf):
    return loaded_modules_re.search(buf).group('LOADED_MODULES')
###############################################################
def read_memory_dump(buf):
    try:
        return memory_dump_re.search(buf).group('MEMORY_DUMP')
    except:
        return None
###############################################################
def get_game_dll_base(buf,filename):
    try:
        dll_list = read_loaded_modules(buf)
        while True:
            m = parse_loaded_modules_re.search(dll_list)
            if not m:
                break
            if parse_game_dll_re.search(m.group('NAME').lower()):
                return int(m.group('BASE'), 16)
            dll_list = dll_list[m.end():]
    except:
        pass

    try:
        dll_list = stack_trace_manual_re.search(buf).group('STACK_TRACE')
        while True:
            m = parse_stack_re.search(dll_list)
            if not m:
                break
            if parse_game_dll_re.search(m.group('NAME').lower()):
                return int(m.group('ADDR'), 16)-int(m.group('ADDRHI'), 16)*0x1000-int(m.group('ADDRLO'), 16)
            dll_list = dll_list[m.end():]
    except:
        pass
    #print '    ├-无法找到Game.dll的基址，将使用默认值！'
    return 0x6F000000
###############################################################
def get_addr_list(memory_dump):
    while True:
        m = parse_memory_dump_re.search(memory_dump)
        if not m:
            break
        memory_dump = memory_dump[m.end():]
        yield conver_hexstringt(m.group('ADDR'))
###############################################################
def get_hex_string(n):
    a = chr(n/256/256/256%256)
    b = chr(n/256/256%256)
    c = chr(n/256%256)
    d = chr(n%256)
    if (a.isalpha() or a.isdigit()) and (b.isalpha() or b.isdigit()) and (c.isalpha() or c.isdigit()) and (d.isalpha() or d.isdigit()):
        return '%08X(\'%s%s%s%s\')' % (n, a, b, c, d)
    else:
        return '%08X' % n
###############################################################
def parse_war3shell(buf):
    m = re.compile(r"gp\_(?P<ORDER>[0-9]{4})").search(buf)
    if m:
        return 'Module/Platform/war3shell.dll/' + m.group('ORDER')
    return 'Module/Platform/war3shell.dll'
###############################################################
def parse_gamedll(dll_list, name):
    m = parse_stack_re.search(dll_list)
    if not m or m.group('NAME').lower().find('game.dll') == -1:
        return 'Module/War3/Other'
    s = '%06X' % (int(m.group('ADDRLO'), 16) + int(m.group('ADDRHI'), 16)*0x1000)
    if not s in GameDllCarshList:
        return 'Module/War3/game.dll/' + s
    print '      [ %s] %s' % (s, GameDllCarshList[s])
    print '      %s' % name
    return 'GameDllCarsh/' + s
###############################################################
def parse_module(buf, base, name):
    try:
        dll_list = stack_trace_manual_re.search(buf).group('STACK_TRACE').lower()
        # 输入法
        if dll_list.find('.ime') != -1:
            if dll_list.find('sogoupy.ime') != -1:
                return 'Module/IME/sogoupy.ime'
            if dll_list.find('unispim6.ime') != -1:
                return 'Module/IME/unispim6.ime'
            return 'Module/IME/Other'
        if dll_list.find('wnoperatemb.dll') != -1:
            return 'Module/IME/wnoperatemb.dll'
        # 外挂
        if dll_list.find('jasline.dll') != -1:
            return 'Module/Cheat/jasline.dll'
        if dll_list.find('manabars.dll') != -1:
            return 'Module/Cheat/manabars.dll'
        if dll_list.find('manabar.dll') != -1:
            return 'Module/Cheat/manabar.dll'
        if dll_list.find('warbar.dll') != -1:
            return 'Module/Cheat/warbar.dll'
        if dll_list.find('ndx.dll') != -1:
            return 'Module/Cheat/ndx.dll'
        # 11平台
        if dll_list.find('assocket.dll') != -1:
            return 'Module/Platform/assocket.dll'
        if dll_list.find('11xp.dll') != -1:
            return 'Module/Platform/11xp.dll'
        if dll_list.find('dxworker.dll') != -1:
            return 'Module/Platform/dxworker.dll'
        if dll_list.find('d3d8hook.dll') != -1:
            return 'Module/Platform/d3d8hook.dll'
        if dll_list.find('dxrender.dll') != -1:
            return 'Module/Platform/dxrender.dll'
        if dll_list.find('war3shell.dll') != -1:
            return parse_war3shell(buf)
        # 显卡驱动
        if dll_list.find('nvoglnt.dll') != -1:
            return 'Module/Graphics/nvoglnt.dll'
        if dll_list.find('nvumdshim.dll') != -1:
            return 'Module/Graphics/nvumdshim.dll'
        if dll_list.find('nvd3dum.dll') != -1:
            return 'Module/Graphics/nvd3dum.dll'
        if dll_list.find('atiumdag.dll') != -1:
            return 'Module/Graphics/atiumdag.dll'
        if dll_list.find('igdumd32.dll') != -1:
            return 'Module/Graphics/igdumd32.dll'
        # 系统
        if dll_list.find('d3d8.dll') != -1:
            return 'Module/System/d3d8.dll'
        if dll_list.find('dsound.dll') != -1:
            return 'Module/System/dsound.dll'
        if dll_list.find('imm32.dll') != -1:
            return 'Module/System/imm32.dll'
        if dll_list.find('msctf.dll') != -1:
            return 'Module/System/msctf.dll'
        if dll_list.find('gdiplus.dll') != -1:
            return 'Module/System/gdiplus.dll'
        if dll_list.find('msvcr80.dll') != -1:
            return 'Module/System/msvcr80.dll'
        if dll_list.find('ws2_32.dll') != -1:
            return 'Module/System/ws2_32.dll'
        if dll_list.find('wintrust.dll') != -1:
            return 'Module/System/wintrust.dll'
        if dll_list.find('shell32.dll') != -1:
            return 'Module/System/shell32.dll'
        # 魔兽
        if dll_list.find('msseax2.m3d') != -1:
            return 'Module/War3/msseax2.m3d'
        if dll_list.find('mssfast.m3d') != -1:
            return 'Module/War3/mssfast.m3d'
        if dll_list.find('mp3dec.asi') != -1:
            return 'Module/War3/mp3dec.asi'
        if dll_list.find('reverb3.flt') != -1:
            return 'Module/War3/reverb3.flt'
        if dll_list.find('mss32.dll') != -1:
            return 'Module/War3/mss32.dll'
        if dll_list.find('storm.dll') != -1:
            return 'Module/War3/storm.dll'
        if dll_list.find('game.dll') != -1:
            return parse_gamedll(dll_list, name)
        if dll_list.find('war3.exe') != -1:
            return 'Module/War3/war3.exe'
        # 未知
        if dll_list.find('yuanlexi') != -1:
            return 'Module/Other/yuanlexi'
        if dll_list.find('lsp.dll') != -1:
            return 'Module/Other/lsp.dll'
        if dll_list.find('user32.dll') != -1:
            return 'Module/Other/user32.dll'
        if dll_list.find('kernel32.dll') != -1:
            return 'Module/Other/kernel32.dll'
        if dll_list.find('ntdll.dll') != -1:
            return 'Module/Other/ntdll.dll'
        # 其他
        if dll_list.find('.') != -1:
            return 'Module/Other'
    except:
        pass
    return 'OtherCarsh'
###############################################################
def parse_commonj(buf, base, name, funclist, map_list):
    memory_dump = read_memory_dump(buf)
    if memory_dump is None:
        return 'Failed/NotFoundMemoryDump'

    param = []
    found = False
    for addr_int in get_addr_list(memory_dump):
        if found:
            param.append(addr_int)
        if addr_int > base:
            addr_int = addr_int-base
            if not found:
                if addr_int == PayloadProc:
                    found = True
            else:
                if ('%08X' % addr_int) in funclist:
                    param_count = int(funclist['%08X' % addr_int][0:2])
                    func_name = funclist['%08X' % addr_int][3:]
                    if func_name in CommonJCarshList:
                        s = '      [CommonJ] %s %s(' % (CommonJCarshList[func_name], func_name)
                    else:
                        s = '      [CommonJ] %s(' % func_name
                    for i in range(0, param_count):
                        if i == 0:
                            s = s + get_hex_string(param[i])
                        else:
                            s = s + ', ' + get_hex_string(param[i])
                    s = s + ')'
                    print s
                    print '      %s' % name
                    if name in map_list:
                        map_list[name] = map_list[name] + 1
                    else:
                        map_list[name] = 1
                    map_list['total'] = map_list['total'] + 1
                    return 'CommonJCarsh/'+ func_name
    return None
###############################################################
def parse_buf(buf, funclist, map_list, filename):
    try:
        buf = read_carsh(buf)
        if buf is None:
            return 'Failed/IncompleteCarsh/'
        ver = read_war3_version(buf)
        if ver == 0:
            return 'Failed/WECarsh/'
        if ver != 6387:
            return 'Failed/ErrorVersion/'+str(ver)

        base = get_game_dll_base(buf,filename)
        path, name = read_map_path_and_name(buf)
        if name is None:
            name = '<unknown>'
        try:
            name.decode('utf-8')
        except:
            try:
                name = name.decode('gbk').encode('utf-8')
            except:
                pass
        er = parse_commonj(buf, base, name, funclist, map_list)
        if er is not None:
            return er
        return parse_module(buf, base, name)
    except:
        pass
    return 'Failed/UnknownError'
###############################################################
def parse_file(filename, funclist, map_list):
    try:
        f  = file(filename, 'r')
        try:
            return parse_buf(f.read(), funclist, map_list, filename)
        finally:
            f.close()
    except IOError:
        pass
    return 'Failed/CantOpenFile'
###############################################################
def copy_file(er, path, filename):
    try:
        os.makedirs(os.path.join('CarshReport', er))
    except:
        pass
    shutil.copy(os.path.join(path, filename), os.path.join('CarshReport', er))
###############################################################
class Redirect:
    def __init__(self, stdout):
        try:
            os.makedirs('CarshReport')
        except:
            pass
        self.stdout = stdout
        self.__f  = file('CarshReport/Report.txt', 'w')
    def __del__(self):
        self.__f.close()
    def write(self, s):
        self.__f.write(s)
        self.stdout.write(s.decode('utf-8').encode('gbk'))

old_stdout = sys.stdout
sys.stdout = Redirect(sys.stdout)
###############################################################
def main():
    print 'Crash文件分析 v0.0.8'
    print '    --by actboy168'
    print '================================================'
    try:
        #print '读取函数列表...'
        funclist = read_funclist()
        #print '  ├-读取了%d个函数' % len(funclist)
        map_list = {}
        map_list['total'] = 0
        path = 'Errors'
        for item in os.listdir(path):
            if os.path.splitext(item)[1] == '.txt':
                er = parse_file(os.path.join(path, item), funclist, map_list)
                if er is not None:
                    copy_file(er, path, item)
        print '--End--'
        print 'total ' + str(map_list['total'])
        for k, v in sorted(map_list.items(), key=lambda d: d[1]):
            if k != 'total':
                print str(v) + ' ' + k
    except:
        pass
###############################################################
if __name__ == "__main__":
    main()
