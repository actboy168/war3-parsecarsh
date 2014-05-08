import os
import string
import struct
import pefile

###############################################################

class GameDll:
    
    def __init__(self, path):
        self.__path = path
        self.__open_pe()
        self.__open_file()        

    def get_string(self, string):
        pos = self.__search_string(string)
        if pos == - 1:
            return -1
        return self.__search_int32(self.__int32_to_string(pos + self.__base))
    
    def funclist(self, string):
        pos = self.get_string(string)
        if pos == - 1:
            return

        pos = pos - 1
        while True:
            if self.__buf[pos] != '\xBA':
                break
            if self.__buf[pos+5] != '\xB9':
                break
            if self.__buf[pos+10] != '\xE8':
                break
            beg = self.__string_to_int32(self.__buf[pos-4:pos])-self.__base
            end = self.__buf.find('\x00', beg)
            func_param = self.__buf[beg:end]            
            beg = self.__string_to_int32(self.__buf[pos+1:pos+5])-self.__base
            end = self.__buf.find('\x00', beg)
            func_name = self.__buf[beg:end]
            func_addr = self.__string_to_int32(self.__buf[pos+6:pos+10])
            pos += 20
            yield func_name, func_addr-self.__base, func_param
        return 
    
    '---------------------------------------------------------'

    def __open_pe(self):
        pe = pefile.PE(self.__path)
        self.__base = pe.OPTIONAL_HEADER.ImageBase
        self.__sections = {}
        for section in pe.sections:
            self.__sections[section.Name.rstrip('\0')] = (section.VirtualAddress, section.VirtualAddress+section.SizeOfRawData)

    def __open_file(self):
        try:
            f  = file(self.__path, "rb")
            try:
                self.__buf = f.read()
            finally:
                f.close()
        except IOError:
            pass
        
    def __search_string(self, string):
        pos = self.__buf.find('\0'+string, self.__sections['.rdata'][0], self.__sections['.rdata'][1])
        if pos != -1:
            return pos+1
        pos = self.__buf.find('\0'+string, self.__sections['.data'][0],  self.__sections['.data'][1])
        if pos != -1:
            return pos+1
        pos = self.__buf.find(     string, self.__sections['.rdata'][0], self.__sections['.rdata'][1])
        if pos != -1:
            return pos
        pos = self.__buf.find(     string, self.__sections['.data'][0],  self.__sections['.data'][1])
        if pos != -1:
            return pos   
        return -1
    
    def __search_int32(self, int32):
        pos = self.__buf.find(int32, self.__sections['.text'][0], self.__sections['.text'][1])
        if pos != -1:
            return pos 
        return -1
    
    def __int32_to_string(self, int32):
        return struct.pack('<L', int32)

    def __string_to_int32(self, string):
        return struct.unpack('<L', string)[0]

def CountParam(param):
    if param[0] != '(':
        return 0
    n = 0
    for c in param:
        if c == ')':
            return n
        if c.isupper():
            n = n + 1

###############################################################
    
h = GameDll('Game24e.dll')

try:
    f  = file('funclist24e.txt', "w")
    try:
        for name, addr, param in h.funclist('Deg2Rad'):
            f.write('%08X %02d %s\n' % (addr, CountParam(param), name))
        for name, addr, param in h.funclist('DebugS'):
            f.write('%08X %02d %s\n' % (addr, CountParam(param), name))
    finally:
        f.close()
except IOError:
    pass




