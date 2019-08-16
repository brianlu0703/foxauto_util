
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 13:56:45 2019

@author: Brian
"""
import sys
import telnetlib
import foxfile
import pexpect
import time
import serial
from pexpect import popen_spawn
from subprocess import Popen, PIPE
    
newCon = None
""" log level 0, 1, 2 (normal, debug, console) """
log_lvl = 2

newSerial = None
matchMore = "--More--"
logFileP = None
testResult = []

timeout = 60
diagprompt="DIAG>"
diagshell="DIAG>"
iosen="Switch>"
iosprompt="Switch#"
rommonprompt="switch:"
bcmshell="BCM.0>"
linuxshell="#"

powerswitch = ""
bootmode ="DIAG"

consoleHelp = r"""
*****************************************************************
||===== ||=====|| ===  === ||====\\ ||=====|| ||=    || ||=    ||
||      ||     ||   \\//   ||       ||     || || \\  || || \\  ||
||===== ||     ||    \\    ||       ||     || ||  \\ || ||  \\ ||
||      ||     ||   // \\  ||       ||     || ||   \\|| ||   \\||
||      ||=====|| ===  === ||====// ||=====|| ||    =|| ||    =||
*****************************************************************
"""
"""
   Check bootmode connect to DUT/COM port terminator     
"""
def getTerminator():
    global bootmode
    
    terminator = ""
    
    if bootmode == "DIAG":
        terminator = diagshell
    elif bootmode == "IOS":
        terminator = iosprompt
    elif bootmode == "ROMMON":
        terminator = rommonprompt
    elif bootmode == "LINUX":
        terminator = linuxshell
    elif bootmode == "BCM":
        terminator = bcmshell
    else:
         terminator = diagshell
    
    return terminator

"""
    Set boot mode if IOS or DIAG or others
"""
def setBootMode(bmode):
    global bootmode
    bootmode = bmode
    pass

"""
    Set power switch/console switch
    is EDVT or DCN switch
"""
def setPowerSwitch(powertype):
    global powerswitch
    
    powerswitch = powertype
    pass

def openNewConsole():
    global newCon

    try:
        # open new consoles
        rconsole = Popen([sys.executable, "-c", """import sys
    for line in sys.stdin:
        sys.stdout.write(line)
        sys.stdout.flush()
    """],
        stdin=PIPE, bufsize=1, universal_newlines=True,
        creationflags=0)
        rconsole.stdin.write(consoleHelp + "\n")
        rconsole.stdin.flush()
        newCon = rconsole
    except:
        print("Open new console error")
    return newCon

def closeConsole(rview):
    if (rview != None):
        #time.sleep(10)
        rview.communicate("bye\n")
        print("Closed a open console {}".format(rview))

def toConsole(rview, msg):
    if (rview != None):
        #rview.stdin.write(msg + "\n")
        rview.stdin.write(msg)
        rview.stdin.flush()

def killtcpPIDWindows():
    """ netstat -ano | findstr :23
    taskkill/pid 17024 /F
    taskkill -pid 17024 -F
    Windows: Usage
    Because pexpect can't decode "|>/" special character"
    Use alternative command solution
    """
    """ '/bin/bash -c "ls -l | grep LOG > log_list.txt"'"""

    netstr = "netstat -ano -P tcp"
    killstr = "taskkill -pid "
    pidlist = []
    #print(len(pidlist))
    try:
        pid = pexpect.popen_spawn.PopenSpawn(netstr)
        for line in pid.readlines():
            line = line.strip()
            tmp = line.split( )
            if (len(tmp) >= 2):
                ss = tmp[2]
                if ((ss[-3: ]) == b':23'):
                    print(int(tmp[4]))
                    pidlist.append(int(tmp[4]))
                else:
                    pass
            #print(line)

    except:
        print("error netstat")

    """ Kill PID list """
    #print(len(pidlist))

    if len(pidlist) > 0:
        for x in range(len(pidlist)):
            try:
                cmdstr = killstr + str(pidlist[x]) + " -F"
                print(cmdstr)
                pp = pexpect.popen_spawn.PopenSpawn(cmdstr)
                pp.closed
            except:
                print("Kill PID error")

def dut_sendcmd(con, wtime, flag, str_=""):
    global newCon
    global logFileP
    
    try:
        #logFileP = foxfile.isLogfileOpen() 
        
        con.write(str_.encode() + b"\n")
        dd = con.read_until(flag.encode(), timeout=wtime)
        
        print(dd.decode(errors='ignore')[len(str_):], end="")
    
        #return data
        if(newCon != None):
            toConsole(newCon, dd.decode(errors='ignore'))
         
        #save log to file
        #if(logFileP != None):
        #    foxfile.writelogtofile(dd.decode(errors='ignore'))   
            
    except KeyboardInterrupt:
            print("Press Keyboard Interrupt (CTRL+C)")        
    except:
        print("dut_sendcmd error")

def command(con, flag, str_=""):
    global newCon
    global logFileP
    
    try:
        logFileP = foxfile.isLogfileOpen() 
        
        con.write(str_.encode() + b"\n")
        data = con.read_until(flag.encode(), timeout=10)
    
        #if(log_lvl == 1):
        print(data.decode(errors='ignore')[len(str_):],end="")
        
        #Display output message to another console
        if(newCon != None):
            toConsole(newCon, data.decode(errors='ignore'))
            
        #save log to file
        if(logFileP != None):
            foxfile.writelogtofile(data.decode(errors='ignore'))    
    
    except KeyboardInterrupt:
            print("Press Keyboard Interrupt (CTRL+C)")    
    except:
        print("function command error")
    return data

def console_cmd(con, flag, str_=""):
    global newCon
    global logFileP
    global testResult
    
    try:
        logFileP = foxfile.isLogfileOpen()   
        
        if(con == None):
             print("Please check console port if open")
             return None 
         
        #print(str_)
        con.write(str_.encode() + b"\n")
        data = con.read_until(flag.encode(), timeout=60)
        print(data.decode(errors='ignore'),end="")
        
        out = ""
        out = out + data.decode()
        
        if out.find("FAIL") > -1:
            testResult.append([str_, "FAIL"])
        elif out.find("PASS") > -1:
            testResult.append([str_, "PASS"])
        else:
            testResult.append([str_, "    "])
            
        #save log to file
        if(logFileP != None):
            foxfile.writelogtofile(data.decode(errors='ignore'))
    
        #return data
        if(newCon != None):
            toConsole(newCon, data.decode(errors='ignore'))
            
    except KeyboardInterrupt:
            print("Press Keyboard Interrupt (CTRL+C)")        
    except:
        print("console_cmd error")

def connectUUT(ip, line):
    print("Telent to connect DUT {} {}".format(ip,line))
    try:
        telnetlib.Telnet()
        tn = telnetlib.Telnet(ip, port=line, timeout=10)
        #tn.close() # tn.write(‘exit\n’)
    except:
        print("telnet UUT error of line {}".format(line))
        print("Please clear this line!")
        return "None"

    return tn

def runCmdtoUUT(con, prompt, runcmds):
    if(con != None):
        
         for i in range(len(runcmds)):
             ss = runcmds[i]
             cmdstr = ""
             for j in range(len(ss)):
                 cmdstr = cmdstr + ss[j] + " "

             console_cmd(con, prompt, cmdstr)

         return True
    else:
        print("please check UUT connection")
        return None
    pass

def runCMDToConsole(con, flag):

    if(con == None):
        print("Please check console port if open")
        return None
    else:  
        print('Enter "quit" to leave program\r\n')
        print(flag,end="")
        try:
            while True:
            
                data = input("")
                
                if data == "quit":
                    print("Return to AUTOTEST mode")
                    break
                else:
                    wtime = 60
                    dut_sendcmd(con, wtime, flag, data)
                 
        except KeyboardInterrupt:
            print("Press Keyboard Interrupt (CTRL+C)")
        except:
            print("runCMDToConsole: Enter command to console error")
    
def sendDataToUUT(con, prompt, data):
    if(con != None):
        #command(con, "DIAG/>", data)
        command(con, prompt, data)

def disconnectUUT(con):
    if(con != None):
        try:
            print("Disconnecting DUT")
            #con.close() # tn.write(‘exit\n’)
            con.write("\x29".encode())
            flag = "telnet>"
            data = con.read_until(flag.encode(), timeout=3)
            #print(data.decode(errors='ignore'))
            con.write("quit".encode() + b"\n")
        except:
            print("Disconnect UUT error")
    #pass

def clearline(ip, line):
    global powerswitch
    
    try:
        tn = telnetlib.Telnet(ip, port=23, timeout=10)
        time.sleep(2)
        
        if powerswitch == "EDVT":
            password = "rHoz"
        else:
            password = "switch"
            
        command(tn, "Password:", "")
        command(tn, "> ", password)
        command(tn, "Password:", "en")
        command(tn, "#", password)
        command(tn, "[confirm]", "clear line " + line)
        command(tn, "# ", "")
        tn.close() 
    except:
        print("clearline: telnet lib error")

def connectTelnet(ip, line):
    global powerswitch
    try:
        tn = telnetlib.Telnet(ip, port=23, timeout=10)
        time.sleep(2)
        if powerswitch == "EDVT":
            password = "rHoz"
        else:
            password = "switch"
            
        command(tn, "Password:", "")
        command(tn, ">", password)
        command(tn, "Password:", "en")
        command(tn, "#", password)
        command(tn, "__More__", "show line " + line)
        command(tn, "#", "")
        command(tn, "(config)#", "conf t")
        command(tn, "#", "exit")
        command(tn, "#", "")
        tn.close()
    except:
        print("connectTelnet: telnet lib error")
    #pass

""" power AC1 on/off
Power switch
AC1 power on --> switch_sw(config-line)#no modem dtr-active
AC1 power off--> switch_sw(config-line)#modem dtr-active
"""
def runPowerAC1(ip, line, onOff):
    global powerswitch
    try:
        tn = telnetlib.Telnet(ip, port=23, timeout=10)
        time.sleep(2)
        if powerswitch == "EDVT" or powerswitch == "edvt":
            password = "rHoz"
        else:
            password = "switch"
            
        console_cmd(tn, "Password", "")
        console_cmd(tn, ">", password)
        console_cmd(tn, "Password", "en")
        console_cmd(tn, "#", password)            
        console_cmd(tn, "(config)#", "conf t")
        console_cmd(tn, "(config-line)#", "line " + line)

        if (onOff == "on"):
            console_cmd(tn, "(config-line)#", "no modem dtr-active")
        else:
            console_cmd(tn, "(config-line)#", "modem dtr-active")

        console_cmd(tn, "(config)#", "exit")
        console_cmd(tn, "#", "exit")
        console_cmd(tn, "#", "")
        tn.close()

        if (onOff == "on"):
            print("Power AC1 on line=", line)
        else:
            print("Power AC1 off line=", line)

    except:
        print("runPowerAC1: telnet to power switch error")


def decodeCFG(filename):

    foxfile.readCFGfile(filename)
    #foxfile.showparam()

    params = foxfile.getparam()

    #print(params)
    for i, j in params.items():
        """ Show comments in line """
        if i == "comment":
            data = j
            tmp = data.split("*")
            print(i)
            for x in range(len(tmp)):
                print(tmp[x])

        else:
            print(i, j)

"""
Open com port from pyserial package

"""
def openCOMPort(cport, baud):
    global newSerial
    
    print("openCOMPort (" + cport + " : " + baud + ")")
    
    try:
        newSerial = serial.Serial(
            port= cport,
            baudrate=baud,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        )
        
        newSerial.isOpen()
        #newSerial = ser
        return newSerial
    except:   
        print("Open %s port error"  % (cport))

def closeCOMPort(rSerial):    
    try:
        if (rSerial!=None):
            rSerial.close()
    except:
        print("Close a serial COM port error")
        
def readMoreData(ser, match, out):
    global newCon
    global logFileP
    
    try:
        if ser == None or match == None:
            print("read More data is None")
            return True
        elif len(out)<=0 or out == " ":
            return True
        else:
            i = out.find(match)
            
            if i > -1:
                ser.write("\x20".encode())
                out = ""
                time.sleep(2)
            
                while ser.inWaiting()>0:
                   data = ser.read(1)
                   out = out + data.decode()
    
                print("Console>>" + out)
                
                #Save log File
                if (logFileP != None):
                    foxfile.writelogtofile("Console>>"+ out)
                
                if(newCon !=None):
                    toConsole(newCon, out)
                
                readMoreData(ser, match, out)
            else:
                out = ""
                return True
    
    except:
        print("Read more console output data error")  
        
def runCMDtoCOMPortPrompt(ser,runcmds,prompt):   
    global newCon
    global logFileP
    global testResult
    global iosprompt
    
    bcmshellcmd = False
    linuxshellcmd = False
    
    if (ser==None):
        print("Please check console port if open")
        return None
    else:    

        logFileP = foxfile.isLogfileOpen()      
        
        try:
            
                ser.flushInput()
                ser.flushOutput()
                sys.stdin.flush()
                sys.stdout.flush()
                
                if prompt == iosprompt:
                    ss = '\r\n'
                    ser.write(ss.encode())
                    out = ""
                    
                    ser.timeout = 5
                    out = ser.read_until(iosprompt.encode()) 
                    
                    if out.decode() == "":
                        ss = '\r\n'
                        ser.write(ss.encode())
                        out = ""
                    
                        ser.timeout = 5
                        out = ser.read_until(iosen.encode())
                        print(out.decode(), end="")
                        ser.write("en\n".encode())
                        out = ser.read_until(iosprompt.encode())
                        print(out.decode(), end="")
                    else:    
                        print(out.decode(), end="")
                   
                            
                for i in range(len(runcmds)):
                    ss = runcmds[i]
                    cmdstr = ""
                    
                    linuxshellcmd = bcmshellcmd = False
                    
                    for j in range(len(ss)):
                        if j==0:
                            if ss[0]==bcmshell:
                                bcmshellcmd = True   
                                continue
                            elif ss[0][-1:]==linuxshell:
                                linuxshellcmd = True
                                continue
                            else:
                                cmdstr = cmdstr + ss[j] + " "
                        else:    
                            cmdstr = cmdstr + ss[j] + " "
                    
                    #Check if testcmd is a bcmshell or linuxshell command
                    #call sub function 
                    if bcmshellcmd == True:
                        #print(cmdstr)
                        runEmphasisCMDtoBCMShell(ser, [cmdstr])
                        testResult.append([cmdstr[:-2], "   "])
                        continue
                    elif linuxshellcmd == True:
                        #print(cmdstr)
                        runCMDtoLinuxShell(ser, [cmdstr])
                        testResult.append([cmdstr[:-2], "    "])
                        continue
                        
                    print(prompt,cmdstr)  
                    
                    ser.flushInput()
                    ser.flushOutput()
                    sys.stdin.flush()
                    sys.stdout.flush()
              
                    if cmdstr =="" or cmdstr == " ":
                        cmdstr = '\r\n'
                    else:
                        cmdstr = cmdstr + '\n'
                        
                    ser.write(cmdstr.encode())
                    out = ""
                    
                    ser.timeout = 60
                    
                    data = ser.read_until(prompt.encode())  
                    out += data.decode()
                
                    print(out[len(cmdstr):-(len(prompt))])
                    
                    if out.find("FAIL") > -1:
                        testResult.append([cmdstr[:-2], "FAIL"])
                    elif out.find("PASS") > -1:
                        testResult.append([cmdstr[:-2], "PASS"])
                    else:
                        testResult.append([cmdstr[:-2], "    "])
                        
                    #Save log file
                    if (logFileP!=None):
                        foxfile.writelogtofile(out)   
                        
                    if (newCon !=None):
                        toConsole(newCon, out)
                                            
                #print("Closed runCMDtoCOMPort")     
        except KeyboardInterrupt:
            print("Press Keyboard Interrupt (CTRL+C)")        
        except:
            print("error communicating serial port ")

"""
Example enter to DIAG shell
DIAG>
"""
def runCMDtoDIAGShell(ser):
    global diagshell
    
    firstime = True
    
    if (ser==None):
        print("Please check com" + ser.port+ " port if open")
        return None
    else:  
        print('Enter console  after '+ diagshell+'\r\nEnter "quit" to leave')
        try:
            while True:
                
                ser.flushInput()
                ser.flushOutput()
                sys.stdin.flush()
                sys.stdout.flush()
                    
                if (firstime==True):
                    firstime = False
                    s = ""

                else:    
                    s = input("")
                
                if s == "quit":
                    print("Return to AUTOTEST mode")
                    break
                else:
                    if s =="" or s == " ":
                        s = '\r\n'
                    else:
                        s = s + '\n'  
                

                    """ change timeout if traffic test command """         
                    if (s.find("linespeed")>-1) or (s.find("minicycle")>-1):
                        tmp = s.split()
                        n = len(tmp)
                        if n > 0 and tmp[n-1] == 0:
                            ser.timeout = 120
                        else:
                            ser.timeout = int(tmp[n-1])*2+60
                    else:
                        ser.timeout = 10
                        
                    ser.write(s.encode())
                    out = ""
                    out = ser.read_until(diagshell.encode())    
                    print(out.decode(), end="")
                    
        except KeyboardInterrupt:
            print("Press Keyboard Interrupt (CTRL+C)")        
        except:
            print("error communicating serial port (runCMDtoDIAGShell) ")
"""
Example
DIAG>bcm_shell

Broadcom Command Monitor (BCM) service started.
BCM.0> 
"""
def runCMDtoBCMShell(ser):
    global bcmshell
    
    firstime = True
    
    if (ser==None):
        print("Please check com" + ser.port+ " port if open")
        return None
    else:  
        print('Enter console  after '+ bcmshell+'\r\nEnter "quit or exit" to leave shell')
        try:
            while True:
                
                ser.flushInput()
                ser.flushOutput()
                sys.stdin.flush()
                sys.stdout.flush()
                
                if (firstime==True):
                    firstime = False
                    s = "bcm_shell"
                else:    
                    s = input("")
                
                if s == "quit":
                    print("exit bcm_shell")
                    s = s + '\n'
                    ser.write(s.encode())
                    ser.timeout = 5
                    out = ""
                    out = ser.read_until(diagprompt.encode())    
                    #print(out.decode(), end="")
                    break
                elif s == "exit":
                    print("go to DIAG shell")
                    s = s + '\n'
                    ser.write(s.encode())
                    ser.timeout = 5
                    out = ""
                    out = ser.read_until(diagprompt.encode())    
          
                    consoleToCOMPort(ser)
                    break
                else:
                    
                    if s =="" or s == " ":
                        s = '\n'
                    else:
                        s = s + '\n'  
                
                    ser.timeout = 30
                    ser.write(s.encode())
                    out = ""
                    out = ser.read_until(bcmshell.encode())    
                    print(out.decode(), end="")
                    
        except KeyboardInterrupt:
            print("Press Keyboard Interrupt (CTRL+C)")        
        except:
            print("error communicating serial port ")

"""
Example
runEmphasisCMDtoBCMShell runcmds
DIAG>bcm_shell

Broadcom Command Monitor (BCM) service started.
BCM.0> edpi cli xxxxxx
BCM.0> exit
"""
def runEmphasisCMDtoBCMShell(ser, runcmds):
    global diagprompt
    global bcmshell
    global logFileP
        
    firstime = True
        
    if (ser==None):
        print("Please check com port if open")
        return None
    else:

        logFileP = foxfile.isLogfileOpen()  
        
        try:
                            
            ser.flushInput()
            ser.flushOutput() 
            sys.stdin.flush()
            sys.stdout.flush()
            
            if (firstime==True):
                firstime = False
                ss = "bcm_shell" + '\n'
                ser.timeout = 30
                ser.write(ss.encode())
                out = ""
                out = ser.read_until(bcmshell.encode())    
                print(out.decode(), end="")
            
            for i in range(len(runcmds)):
                ss = runcmds[i]
                ss = ss + '\n'
                print(ss)
                
                ser.flushInput()
                ser.flushOutput() 
                sys.stdin.flush()
                sys.stdout.flush()
                  
                ser.write(ss.encode())
                out = ""
                ser.timeout = 60
                
                if (ss[0:4] == "exit"):
                    out = ser.read_until(diagprompt.encode())
                    print(out.decode()[len(ss):], end="")
                    break
                else:    
                    out = ser.read_until(bcmshell.encode())    
                    print(out.decode()[len(ss):], end="")
                
                #Save log file
                if (logFileP!=None) and (out.decode()!=""):
                    foxfile.writelogtofile(bcmshell+out.decode()) 

            time.sleep(1)  
            
            #If bcmshell cmd is "exit", then return to DIAG> already
            if (ss[0:4] == "exit"):
                print("Got bcmshell command is exit. ")
                #Save log file
                if (logFileP!=None) and (out.decode()!=""):
                    foxfile.writelogtofile(bcmshell+out.decode())
            else:
                #always exit bcmshell   
                ss = "exit" + "\n"
                ser.timeout = 10
                ser.write(ss.encode())
                out = ""
                out = ser.read_until(diagprompt.encode())
                print(out.decode(), end="")
                
                #Save log file
                if (logFileP!=None) and (out.decode()!=""):
                    foxfile.writelogtofile(out.decode())
          
       
        except KeyboardInterrupt:
            print("Press Keyboard Interrupt (CTRL+C)")        
        except:
            print("error communicating serial port (runEmphasisCMDtoBCMShell) ")
            
"""
Example
runCMDtoLinuxShell runcmds
DIAG>linux_shell
root@localhost:~# exit
"""
def runCMDtoLinuxShell(ser, runcmds):
    global diagprompt
    global linuxshell
    global logFileP
        
    firstime = True
        
    if (ser==None):
        print("Please check com port if open")
        return None
    else:

        logFileP = foxfile.isLogfileOpen()  
        
        try:
            
            if (firstime==True):
                firstime = False
                ss = "linux_shell" + '\n'
                ser.timeout = 3
                ser.write(ss.encode())
                out = ""
                out = ser.read_until(linuxshell.encode())    
                print(out.decode(), end="")
            
            for i in range(len(runcmds)):
                ss = runcmds[i]
                ss = ss + '\n'
                
                ser.flushInput()
                ser.flushOutput()
                sys.stdin.flush()
                sys.stdout.flush()
                                  
                ser.write(ss.encode())
                out = ""
                ser.timeout = 30
                
                if(ss[0:4]=="exit"):
                    out = ser.read_until(diagprompt.encode())    
                    print(out.decode(), end="")
                    break
                else:
                    out = ser.read_until(linuxshell.encode())    
                    print(out.decode(), end="")
                
                #Save log file
                if (logFileP!=None) and (out.decode()!=""):
                    foxfile.writelogtofile(linuxshell+out.decode()) 
                    
            if(ss[0:4]=="exit"):
                print("Got linux shell command is exit.")
                #Save log file
                if (logFileP!=None) and (out.decode()!=""):
                    foxfile.writelogtofile(linuxshell+out.decode()) 
            else:
                #read if lastest cmd succeed    
                if(len(out)>0):
                    ss = "exit" + "\n"
                    ser.timeout = 5
                    ser.write(ss.encode())
                    out = ""
                    out = ser.read_until(diagprompt.encode())
                    print(out.decode(), end="")
                        
                else:
                    ss = "\n"
                    ser.timeout = 2
                    ser.write(ss.encode())
                    out = ""
                    out = ser.read_until(linuxshell.encode())
                    print(out.decode(), end="")
                
        except KeyboardInterrupt:
            print("Press Keyboard Interrupt (CTRL+C)")        
        except:
            print("error communicating serial port (runCMDtoLinuxShell) ")            

"""
Example run cmd to console port

"""    
def runCMDtoCOMPort(ser, runcmds):
    global newCon
    global logFileP
    global testResult
    
    if (ser==None):
        print("Please check console port if open")
        return None
    else:    
        #print('Enter console commands after >>\r\nEnter "quit" to leave program.')
        logFileP = foxfile.isLogfileOpen()     
        
        #check bootmode terminator
        terminator = getTerminator()
        
        try:
                for i in range(len(runcmds)):
                    ss = runcmds[i]
                    cmdstr = ""
                     
                    for j in range(len(ss)):
                        cmdstr = cmdstr + ss[j] + " "
                
                    ser.flushInput()
                    ser.flushOutput()
                    sys.stdin.flush()
                    sys.stdout.flush()
                    #print(cmdstr)   
                    
                    if cmdstr =="" or cmdstr == " ":
                        cmdstr = '\r\n'
                    else:
                        cmdstr = cmdstr + '\n'
                        
                    ser.write(cmdstr.encode())
                    out = ""
                    ser.timeout = 10
                
                    data = ser.read_until(terminator.encode())   
                    out += data.decode()
                    print(out[len(cmdstr):], end="")
                    
                    
                    if (out.find("FAIL") > -1) or (out.find("FAILED") > -1):
                        testResult.append([cmdstr[:-2], "FAIL"])
                    elif (out.find("PASS") > -1) or (out.find("PASSED") > -1):
                        testResult.append([cmdstr[:-2], "PASS"])
                    else:
                        testResult.append([cmdstr[:-2], "    "])
                        
                    #Save log file
                    if (logFileP!=None):
                        foxfile.writelogtofile(">>"+ out)   
                        
                    if (newCon !=None):
                        toConsole(newCon, out)
                                              
        except KeyboardInterrupt:
            print("Press Keyboard Interrupt (CTRL+C)")        
        except:
            print("(runCMDtoCOMPort) Error to communicating serial port ")


def showTestResult(showstr, heads, verbose):
    global testResult
    global logFileP
        
    total_pass = 0
    total_fail = 0
    out = "\n"
    
    logFileP = foxfile.isLogfileOpen()  
    
    
    #print("\n*********************************************************")
    #out += "\n*********************************************************\n"
    
    if(showstr==""):
        print("\nShow autotest run all result ")
        out += "Show autotest run all result\n"
    else:
        print("\n"+showstr)
        out += showstr + "\n"

    resban = "===================="
    s = 0
    
    for res in testResult:
        s = len(res)
        resban = s * resban
        out += resban + "\n"
        break
    
    print(resban)
    
    #Show result tilte
    if (heads!="") and len(heads)>0:
        for i, head in enumerate(heads):
            if i == 0:
                print("{0:35}".format(head), end="")
                out += "{0:35}".format(head)
            elif i == 1:
                print("{0:30}".format(head), end="")
                out += "{0:30}".format(head)
            else:
                print("{0:10}".format(head), end="")
                out += "{0:10}".format(head)
    
    subban = "--------------------"
    subban *= s
    
    print("\n"+ subban)
    out += "\n" + subban + "\n"
    
    for res in testResult:

        s = len(res)
        if res[s-1] == "PASS":
            total_pass +=1
        elif res[s-1] == "FAIL":
            total_fail +=1
        else:
            pass
        #else:se
        #    continue
                
        for i in range(len(res)):
            if i==0:
                if len(res[i])>35:
                    print("{0:55}".format(res[i]), end="")
                    out += "{0:55}".format(res[i])
                else:
                    print("{0:35}".format(res[i]), end="")
                    out += "{0:35}".format(res[i])
            elif i==1:
                print("{0:30}".format(res[i]), end="")
                out += "{0:30}".format(res[i])
            else:
                print("{0:10}".format(res[i]), end="")
                out += "{0:10}".format(res[i])
            
        print("")  
        out += "\n"
        
    print(resban)
    out += "\n" + resban + "\n"
    
    print("Total of PASSED {0:4}, FAILED {1:4}".format(total_pass,total_fail))
    out += "Total of PASSED {0:4}, FAILED {1:4}\n".format(total_pass,total_fail)
    #print("*********************************************************")
    #out += "*********************************************************\n"
    #Save log file
    if (logFileP!=None):
        foxfile.writelogtofile(out) 
    
    if(verbose == "en"):
        print("Debug test result for detail")
        for res in testResult:
            print(res)
            
    testResult=[]
    
def consoleToCOMPort(ser):
    global matchMore
    global newCon
    global logFileP
    global timeout
    global diagprompt
    global iosen
    global iosprompt
    global rommonprompt
    global bcmshell
    
    firsttime = False
    #check bootmode terminator
    terminator = getTerminator()
        
        
    if (ser==None):
        print("Please check console port if open")
        return None
    else:    
        print('Enter any commands after {0}\r\nEnter "quit" to leave program.'.format(terminator))
        
        logFileP = foxfile.isLogfileOpen()
        
        
        try: 
                    
            while True:
                ser.flushInput()
                ser.flushOutput()
                sys.stdin.flush()
                sys.stdout.flush()
                    
                if (firsttime==False):
                    s = input(terminator)
                    firsttime = True
                else:
                    s = input("")
                    
                if s == "quit":
                    print("quit console program")
                    break
                else:
                    
                    if s =="" or s == " ":
                        s = '\n'
                    else:
                        s = s + '\n'
                    
                    ser.write(s.encode())
                    out = ""
                    ser.timeout = 10
                
                    data = ser.read_until(terminator.encode())   
                    out += data.decode()
                    print(out[len(s):], end="")
                            
                    #Save log file
                    if (logFileP!=None):
                        foxfile.writelogtofile(">>"+ out)   
                        
                    if (newCon !=None):
                        toConsole(newCon, out)
                    
                    #read more data if match "--More--"
                    #readMoreData(ser, matchMore, out)
        
        except KeyboardInterrupt:
            print("Press Keyboard Interrupt (CTRL+C)")
        except:
            print("error communicating serial port ")

"""
Example: runTestCmdToCOMPort
com_port, testcmds, terminator prompt(diag, or bcm shell, or others)
wait_time -- read com port buffer until timeout
option -- pre-emphasis (main, post, pre)
    
"""
def runTestCmdToCOMPort(ser, testcmds, terminator, wait_time, option):
    global logFileP
    global testResult
    ret = None
    
    if (ser==None):
        print("Please check com port if open")
        return None
    else:    
    
        logFileP = foxfile.isLogfileOpen()
        
        try:
            sys.stdin.flush()
            sys.stdout.flush()
            ser.flushInput()
            ser.flushOutput()
            
            for i in range(len(testcmds)):
                testcmd = testcmds[i]
                    
                if(len(testcmd)==0):
                    testcmd ="\n"
                    return ret
                else:
                    testcmd = testcmd + '\n'
                    
                print(testcmd)
                ser.write(testcmd.encode())
                out = ""
                ser.timeout = wait_time
                
                data = ser.read_until(terminator.encode())   
                out += data.decode()
                print(out[len(testcmd):], end="")
                
                if(out==""): 
                    print("runTestCmdToCOMPort is timeout!")
                    ret = "Timeout"
                    
                if (logFileP!=None) and (len(out)>0):
                    foxfile.writelogtofile(terminator+out)   
                
                tempidx = -1
                
                if testcmd.find("linespeed")>-1:
                    tempidx = out.find("100 %")   
                
                # Add temperature result
                if (tempidx > -1):
                    #print(out[tempidx+10:tempidx+14])
                
                    if (out.find("FAIL") > -1) or (out.find("FAILED") > -1):
                        testResult.append([testcmd[:-1], str(option), out[tempidx+10:tempidx+15], "FAIL"])
                    elif (out.find("PASS") > -1) or (out.find("PASSED") > -1):
                        testResult.append([testcmd[:-1], str(option), out[tempidx+10:tempidx+15], "PASS"])
                    else:
                        testResult.append([testcmd[:-1], str(option), "     ", "      "])  
                else:
                    if (out.find("FAIL") > -1) or (out.find("FAILED") > -1):
                        testResult.append([testcmd[:-1], str(option), "FAIL"])
                    elif (out.find("PASS") > -1) or (out.find("PASSED") > -1):
                        testResult.append([testcmd[:-1], str(option), "PASS"])
                    else:
                        testResult.append([testcmd[:-1], str(option), "      "])  
            
        except KeyboardInterrupt:
            print("Press Keyboard Interrupt (CTRL+C)")
        except:
            print("error communicating serial port (runTestCmdToCOMPort)")
            
        return ret    

def checkLogFileIsOpen():
    global logFileP
    
    #Check if file already open
    logFileP = foxfile.isLogfileOpen() 
    
    return logFileP

def setLogFileToClose():
    
    global logFileP
    
    logFileP = None
        
    return logFileP
        
def main():
    filename = "autotest_v01.cfg"
    #decodeCFG(filename)
    #findvalue("host_ip")
    ip = "172.18.60.244"
    line = "7"
    global newCon
    global newSerial

    foxfile.readCFGfile(filename)
    
    host_ip     = foxfile.findvalue("host_ip")
    line_uut    = foxfile.findvalue("line_uut")
    line_power  = foxfile.findvalue("line_power")
    
    com_port = foxfile.findvalue("com_port")
    com_baud = foxfile.findvalue("com_baud")
    power_switch = foxfile.findvalue("power_switch")
    setPowerSwitch(power_switch)
    
    #print(com_port, com_baud)
    """
    if sys.platform == 'win64':
        print("win64")
    elif sys.platform == 'win32':
        print("win32")
    else:
        print("other")
    """

    #TODO this kill TCP session connection first in windows
    #killtcpPIDWindows()

    #TODO telnet console swtich (OK)


    #runPowerAC1(ip, line, "off")
    #runPowerAC1(ip, line, "off")

    #openNewConsole()
    #runPowerAC1(ip, "10", "off")
    #time.sleep(2)
    #runPowerAC1(ip, "10", "on")
    #time.sleep(10)

    clearline(host_ip, line_uut[-2:])
    #clearline(ip, "7")
    #clearline(ip, "7")
    #clearline(ip, "7")
    #time.sleep(10)

    #try:
        #co = ""
        #connectTelnet(ip, line)
        #tp = connectUUT(ip, 2007)
    #flag = "DIAG>"
    #str_ = "version"

    #sys.stdin.flush()
    #sys.stdout.flush()

    #openCOMPort(com_port, com_baud)
    
    #time.sleep(2)
    #if(newSerial!=None):
    #    consoleToCOMPort(newSerial)
    
    #if(newSerial!=None):
    #    closeCOMPort(newSerial)
    #con = telnetlib.Telnet(ip, port=2007, timeout=10)

    #dut_sendcmd(con, 120, flag, str_)

    #dd = con.read_until(flag.encode(), timeout=120)
    #print(dd.decode(errors='ignore'))
    #con.write(str_.encode() + b"\n")

    #dd = con.read_until(flag.encode(), timeout=10)
    #print(dd.decode(errors='ignore'))
    #con.write(str_.encode() + b"\n")

    #tp.debuglevel
    #print(data)

    #command(tp, ">", "")
    #command(tp, ">", "")
    #data = tp.read_until(flag.encode(),timeout=0)
    #co.write(b'\r\n')
    #print(co.read_all())

    #print(data.decode(errors='ignore'))
    #time.sleep(10)
    #con.close()
    #con.write("\x29".encode())
    #flag = "telnet>"
    #dd = con.read_until(flag.encode(), timeout=10)
    #con.write("quit".encode() + b"\n")
    #time.sleep(10)
    #except:
      #disconnectUUT(con)
      #print("telent error")

    if (newCon != None):
       closeConsole(newCon)
       
    print("End of fox_connect main()")   
    time.sleep(2)
    
if __name__ == "__main__":
    main()