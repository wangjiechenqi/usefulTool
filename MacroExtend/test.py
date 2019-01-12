from PyMacroParser import PyMacroParser


a1 = PyMacroParser()
a2 = PyMacroParser()

a1.load("a.cpp")
filename = "b.cpp"
a1.dump(filename)  # 没有预定义宏的情况下，dump cpp

a2.load(filename)
a2.dumpDict()

a1.preDefine("MC1;MC2") #指定预定义宏，再dump
a1.dumpDict()
a1.dump("c.cpp")