# -*- coding: utf-8 -*-
"""
Title: Foxconn Auto-Test Utility
Created on Tue Jun  4 11:23:51 2019

@author: Brian
"""
import foxfile
import fox_connect
import time
import sys, os
import pyfiglet
from pyfiglet import Figlet

prompt = "AUTOTEST/>"
conprompt = "CONSOLE/>"
diagprompt = "DIAG>"
bootmode = "DIAG"
iosprompt ="Switch#"

cmdlist = []
conuut = None
cfgcmdlist = []
rcon = None
rcomP = None
auto_version = "0.3"
osPlatform = "win32"

def showbanner():
    
    showstr = r"""
    ************************************************************************
                           Foxconn Auto Test v0.1
                          *************************
        ||===== ||=====|| ===  === ||====\\ ||=====|| ||=    || ||=    ||
        ||      ||     ||   \\//   ||       ||     || || \\  || || \\  ||
        ||===== ||     ||    \\    ||       ||     || ||  \\ || ||  \\ ||
        ||      ||     ||   //\\   ||       ||     || ||   \\|| ||   \\||
        ||      ||=====|| ===  === ||====// ||=====|| ||    =|| ||    =||
    *************************************************************************
    """
    ascii_banner = pyfiglet.figlet_format("Foxconn")
    print(ascii_banner)
    vbanner = pyfiglet.figlet_format("Auto Test " + auto_version )
    print(vbanner)
    
def showcmd():
    print("show run all command list")
    print("======================================")
    if len(cmdlist) > 0:
        for i in range(len(cmdlist)):
            ss = cmdlist[i]
            for cmd in ss:
                print(cmd + " ",end="")
            print("")
    pass
    print("======================================")

def helper(cmd):
    helpstr = """
    'q'      : Quit the Foxconn auto test
    add      : Add new test cmd into runall command list
    com      : COM port utility
    console  : Console to DUT utility
    diag     : Enter to DIAG shell mode
    del      : Delete command in runall command list
    power    : Power AC on/off to power switch
    run      : Run all of test command
    sfp      : Run SFP ports pre-emphasis test 
    show     : Show runall test command 
    bcmshell : Enter to bcm shell mode 
    help:
    """
    
    helpcmd  = { "q"       : "quit the autotest",
                 "add"     : "add command string",
                 "com"     : "open com port, [open|close|dut]",
                 "console" : "[diag|close|clear]",
                 "diag"    : "enter to diag shell, [quit] to shell",
                 "bcmshell": "enter to bcm shell,  [quit] to shell",
                 "power"   : "choice the AC power [on|off]",
                 "run"     : "Run all command with corner loops",
                 "show"    : "Show current test command, [all] show all CFG file",
                 "sfp"     : "Run SFP/SFP+ ports pre-emphasis"
               }
    
    if(cmd==""):
        print(helpstr)
    else:
        if cmd in helpcmd:
            print("{0:10}: {1:50}".format(cmd,helpcmd[cmd]))
        else:
            print("Enter commmand \'{0}\' is not exist".format(cmd))
    pass

def addcmd(cmd):
    cmdlist.append(cmd)
    pass

def delcmd(cmd):
    try:
        print("delete a command with " + cmd)
        
        if len(cmdlist) > 0:
            for i in range(len(cmdlist)):
                ss = cmdlist[i]
                for j in range(len(ss)):
                    if ss[j] == cmd:
                        print("Deleted {0} successfully".format(ss))
                        del cmdlist[i]
                        return "ok"
        pass
    except:
        print("delete a command error")
def corner_test(cornstr):
    if(cornstr != None):
        seqs = cornstr.split(",")
        
        if (len(seqs) > 0):
            return seqs
        else:
            return None
    return None

def execcmd(cmds):
    if (len(cmds) == 0):
       return None

    print("run command list")
    cmdstr = ""
    for i in range(len(cmds)):
        ss = cmds[i]
        cmdstr = ""
        for j in range(len(ss)):
            cmdstr = cmdstr + ss[j] + " "

        print(cmdstr)
    pass

def exeRunCmdToUUT(cmds):
    global conuut

    if (len(cmds) == 0):
       return None

    if (conuut != None):
        #TODO: run command to UUT console
        res = fox_connect.runCmdtoUUT(conuut, diagprompt, cmds)

        if (res == None):
            print("Exeute Run command error")
    else:
        print("Error of exeRunCmdTOUUT")
    pass

def exeRunCmdtoCOM(cmds):
    global rcomP
    global bootmode 
    
    if (len(cmds) == 0):
       return None
   
    if(rcomP != None):
        if bootmode == "DIAG" or bootmode =="diags":
            #print(diagprompt, end="")
            fox_connect.runCMDtoCOMPortPrompt(rcomP, cmds, diagprompt)
        elif bootmode == "IOS":
            fox_connect.runCMDtoCOMPortPrompt(rcomP, cmds, iosprompt)
        else:
            fox_connect.runCMDtoCOMPort(rcomP,cmds)
            
    else:
        print("Error of exeRunCmdtoCOM")
    pass

def readConfig():
    """ Read auto test config file """
    filename = "autotest_v01.cfg"

    foxfile.readfile(filename)

def main():

    global conuut
    global rcon
    global rcomP
    global osPlatform
    global bootmode
    
    showbanner()
    firsttime = 0
    
    #TODO input conf file name
    if (len(sys.argv) == 2):
        filename = str(sys.argv[1])

    else:
        #TODO
        filename = "autotest_template.cfg"
        
    if sys.platform == "win32":
        osPlatform = "win32"
    else:
        osPlatform = "Others"

    print("Auto test conf. file is " + filename)
    ret = foxfile.readCFGfile(filename)
    
    if (ret !=None):
        print("Please provide the autotest configure file " + filename)
        return None
        
    host_ip     = foxfile.findvalue("host_ip")
    line_uut    = foxfile.findvalue("line_uut")
    line_power  = foxfile.findvalue("line_power")
    cornerlist  = foxfile.finduutcfg("corner_sequence")
    com_port    = foxfile.findvalue("com_port")
    com_baud    = foxfile.findvalue("com_baud")
    boot_mode   = foxfile.findvalue("boot_mode")
    power_switch = foxfile.findvalue("power_switch")
    
    #set console or power switch mode
    fox_connect.setPowerSwitch(power_switch)
    
    #Set boot mode from configure file
    if boot_mode != None:
        bootmode = boot_mode
        
    #Set default boot mode if DIAG or others    
    fox_connect.setBootMode(bootmode)
    
    log_dir  = foxfile.findvalue("log_dir")
    log_file = foxfile.findvalue("log_file")
    filedir = ""
    
    if osPlatform == "win32":
        #print("Debug: Windows platfom")
        filedir  = os.getcwd()+"\logs"
        if not os.path.exists(filedir):
            os.makedirs(filedir)
    else:
        filedir = log_dir
         
    """ read Macro command to list """
    cfgcmdlist = foxfile.readMacrofile(filename)

    for i in range(len(cfgcmdlist)):
        size = len(cfgcmdlist[i])
        for j in range(1, size):
            subcmd = cfgcmdlist[i][j]
            for x in range(len(subcmd)):
                addcmd(subcmd[x])
                
    """ read cmdlist from a file """
    cmdtestlist =  foxfile.readCMDTestfile(filename)
    
    if ((cmdtestlist!=None) and (len(cmdtestlist)!=0)):
        for i in range(len(cmdtestlist)):
            size = len(cmdtestlist[i])
            for j in range(1, size):
                subcmd = cmdtestlist[i][j]
                for x in range(len(subcmd)):
                    addcmd(subcmd[x])
                    
    """ read pre-emphasis setting """
    preemphasis = foxfile.readPreEmphasisCFGfile(filename)                

    while(True):
       if  firsttime == 0:
           s = input("Please \"q\" to quit auto test program. \n"+prompt)
       else:
           s = input(""+prompt)

       firsttime +=1

       if (len(s) == 0):
           continue
       if s == 'q' or s[0:4] == "quit":
           if (rcomP != None):
               fox_connect.closeCOMPort(rcomP)
               rcomP = None
           
           if(conuut != None):
               fox_connect.disconnectUUT(conuut)
               conuut = None
           break
       elif s[0:3] == "run":
           #Default 
           if(rcomP == None) and (conuut == None):
                if osPlatform == "win32":
                    if(com_port != None and com_baud != None):
                        rcomP = fox_connect.openCOMPort(com_port, com_baud)
                        
                        if(rcomP != None):
                            print("COM port is opened successfully")
                        else:
                            print("Connect COM port failed")
                            continue
                else:
                    """ Open console as default in Linux """
                    if (conuut==None):
                        conuut = fox_connect.connectUUT(host_ip, line_uut)
                        
                        if(conuut != None):
                            print("Console port is opened successfully")
                        else:
                            print("Connect console port failed")
                            continue
                
           if(cmdlist != None) and ((conuut != None) or (rcomP != None)):
               sys.stdin.flush()
               sys.stdout.flush()
               
               print("Running runall test command ....")
               #Open log file
               foxfile.openlogfile(filedir, log_file)
               
               #Update log file is open
               fox_connect.checkLogFileIsOpen()
               
               #time.sleep(2)
               cnts = corner_test(cornerlist)

               for cn in range(len(cnts)):
                   if(cnts[cn] !=0):
             
                       if (conuut != None):
                           exeRunCmdToUUT(cmdlist)
                       elif (rcomP != None):
                           exeRunCmdtoCOM(cmdlist)

               #Show Test result
               fox_connect.showTestResult("", "", "")
               
               #Close log file         
               foxfile.closelogfile()

               #Close the file global flag
               fox_connect.setLogFileToClose()
               
               sys.stdin.flush()
               sys.stdout.flush()
              
           else:
               print("Running stopped, please open a console or com port firstly")
           continue
       elif s[0:4] == "show":
           tmp = s.split()

           if(len(tmp) == 1):
               showcmd()
           else:
               if(tmp[1] == "all"):
                   foxfile.showparam()
                   foxfile.showUUTcfg()                   
                   foxfile.showpreemphasis()
               elif (tmp[1] == "emphasis"):
                   foxfile.showpreemphasis()
               elif (tmp[1] == "uut"):
                   foxfile.showparam() 
                   foxfile.showUUTcfg() 
               else:
                   pass
           continue
       elif s[0:3] == "add":
           ss = s
           newcmd = []
           tmp = ss.split( )

           if (len(tmp)==1):
               print("Add new test cmd is empty")
               continue

           #aa = " ".join(ss[4:].split( ))
           #print(aa)

           for x in range(1, len(tmp)):
               newcmd.append(tmp[x])

           addcmd(newcmd)
           continue
       elif s[0:3] == "del":

           dd = s.split( )

           if (len(dd)==1):
               print("delete cmd can not empty")
               continue

           delcmd(dd[1])
           continue

       elif s[0:7] == "console":
            rview = s.split( )
            
            if (len(rview)==1):    
                if (conuut==None):
                    conuut = fox_connect.connectUUT(host_ip, line_uut)
                    if (conuut == None):
                        print("Console line connect failed")
                        continue
                    
                if(conuut != None):
                    if boot_mode == "DIAG":
                        flag=diagprompt
                    elif boot_mode == "IOS":
                        flag=iosprompt
                    else:
                        flag=diagprompt
                        
                    fox_connect.runCMDToConsole(conuut, flag)
                    print("\r\n")

                continue
            else:   
                if (rview[1] == "close"):
                    if(conuut != None):
                        fox_connect.disconnectUUT(conuut)
                        print("\r\n")
                        conuut = None
                    else:
                        print("Closed console line failed")
                    
                    continue
                elif (rview[1] == "diag"):
                    
                    if (conuut==None):
                        conuut = fox_connect.connectUUT(host_ip, line_uut)
                        if (connut == None):
                            print("Open console line failed")
                            continue
                    
                    if(conuut != None):
                        fox_connect.runCMDToConsole(conuut, diagprompt)
                        print("\r\n")
                        
                    continue
                elif (rview[1] == "clear"):
                    cr_line = line_uut[-2:]
                    print("Clear console line " + cr_line)
                    fox_connect.clearline(host_ip, cr_line)
                    print("\r\n")
                    continue
                else:
                    print("please choice console line [diag|close|clear]")
                    continue
       elif s[0:8] == "bcmshell":
           rcom = s.split( )
           if (len(rcom)==1):
                 if(rcomP == None):
                    if(com_port !=None and com_baud != None):
                        rcomP = fox_connect.openCOMPort(com_port, com_baud)
                        
                        if(rcomP != None):
                            print("COM port is opened successfully")
                        else:
                            print("Connect COM port failed")
                 if(rcomP != None):
                    fox_connect.runCMDtoBCMShell(rcomP)
                 continue
       elif s[0:4] == "diag":
           rcom = s.split( )
           if (len(rcom)==1):
                 if(rcomP == None):
                    if(com_port !=None and com_baud != None):
                        rcomP = fox_connect.openCOMPort(com_port, com_baud)
                        
                        if(rcomP != None):
                            print("COM port is opened successfully")
                        else:
                            print("Connect COM port failed")
                 if(rcomP != None):
                    fox_connect.runCMDtoDIAGShell(rcomP)
                 continue      
       elif s[0:3] == "com":
            rcom = s.split( )

            if (len(rcom)==1):
                #print("please choice COM port [open|close|connect|bcmshell]")
                if(rcomP == None):
                    if(com_port !=None and com_baud != None):
                        rcomP = fox_connect.openCOMPort(com_port, com_baud)
                        
                        if(rcomP != None):
                            print("COM port is opened successfully")
                        else:
                            print("Connect COM port failed")
                            
                if(rcomP != None):
                    #Open log file
                    foxfile.openlogfile(filedir, log_file)
                    fox_connect.consoleToCOMPort(rcomP)
                    #Close log file         
                    foxfile.closelogfile()
                continue
            if(rcom[1] == "open"):
                if(com_port !=None and com_baud != None):
                    #print("Opening a %s port, Baud=%s" % (com_port, com_baud))
                
                    #rcon = fox_connect.openNewConsole()
                    #if(rcon != None):
                    #    print("open a new console successful")
                    
                    rcomP = fox_connect.openCOMPort(com_port, com_baud)
                    if(rcomP != None):
                        print("COM port is opened successfully")
                continue
            elif(rcom[1] == "dut"):
                if(rcomP == None):
                    if(com_port !=None and com_baud != None):
                        rcomP = fox_connect.openCOMPort(com_port, com_baud)
                        
                        if(rcomP != None):
                            print("COM port is opened successfully")
                        else:
                            print("Connect COM port failed")
                            
                if(rcomP != None):
                    #Open log file
                    foxfile.openlogfile(filedir, log_file)
                    fox_connect.consoleToCOMPort(rcomP)
                    #Close log file         
                    foxfile.closelogfile()
                continue
            elif(rcom[1] == "close"):
                if(rcomP != None):
                    fox_connect.closeCOMPort(rcomP)
                    rcomP = None
                    print("COM port is closed successfully")
                continue
            else:
                print("please choice COM port [open|close|dut]")
                continue
       elif s[0:5] == "power":
            ac = s.split( )

            if (len(ac)==1):
                print("please enter power on or off")
                continue

            fox_connect.runPowerAC1(host_ip, line_power, ac[1])
            print("\r\n")
            time.sleep(2)
            continue
       elif s[0:4] == "help" or s[0] == '?':
            tmp = s.split( )
            if (len(tmp)==1):
                helper("")
            else:
                helper(tmp[1])
            continue   
       elif s[0:3] == "sfp":
           
            if(rcomP == None):
                if(com_port !=None and com_baud != None):
                    rcomP = fox_connect.openCOMPort(com_port, com_baud)
                    
                    if(rcomP != None):
                        print("COM port is opened successfully")
                    else:
                        print("Connect COM port failed")
            
            if(rcomP != None):                
                #Open log file
                foxfile.openlogfile(filedir, log_file)
                     
                epdm_cr_mode = []
                epdm_cr_mode = foxfile.readpreemphasis("epdm_cr_mode")
                
                epdm_link = ["epdm link all"]
                
                # Change EPDM CR mode
                if (epdm_cr_mode != "") and (rcomP != None):
                    #print(epdm_cr_mode)
                    fox_connect.runEmphasisCMDtoBCMShell(rcomP, epdm_cr_mode)
                    fox_connect.runEmphasisCMDtoBCMShell(rcomP, epdm_link)
                #for k, v in enumerate(preemphasis):
                #    print("{0:2} {1:20} {2:40}".format(k, v, preemphasis[v]))
                diag_traf_cmds = foxfile.createEmphasisTrafTest(preemphasis)
                
                testcmds = ""
                terminator = diagprompt
                wait_time = 120
                
                #Show diag traffic test command (TBD: one test command)
                #for cmds in diag_traf_cmds:
                #    testcmd = cmds
                #    break
                """ copy traffic test command"""
                testcmds = diag_traf_cmds
                
                #if(rcomP != None):
                #    fox_connect.runTestCmdToCOMPort(rcomP, testcmd, terminator, wait_time)
                if "emphasis_adj" in preemphasis:
                    main_offset = preemphasis["emphasis_adj"]
                    #print("main_offset = ", main_offset )
                else:
                    main_offset = 1
                
                if "emphasis_main" in preemphasis:
                    mainval = preemphasis["emphasis_main"]
                    
                if "emphasis_pre" in preemphasis:
                    preval = preemphasis["emphasis_pre"]   
           
                if "emphasis_post" in preemphasis:
                    postval = preemphasis["emphasis_post"] 
                    
                adj_main =  adj_pre = adj_post = 0
                
                """ Create emphasis list range +/- offset """
                emp_list = [(0,0,0)] 
                x=y=z=0
                
                for i in range(int(main_offset)+1):
                    emp_list.append((x+i   , y, z))
                    emp_list.append((-(x+i), y, z))
                    
                    emp_list.append((x,    y+i, z))
                    emp_list.append((x, -(y+i), z))
                    
                    emp_list.append((x, y,    z+i))
                    emp_list.append((x, y, -(z+i)))
    
                    
                emp_list = list(set(emp_list))
                #print(type(emp_list), len(emp_list))
                emp_list.sort(reverse=True)
                
                for emp in emp_list:
                    adj_main = emp[0]
                    adj_post = emp[1]
                    adj_pre  = emp[2]
                    
                    #print(adj_main , adj_post , adj_pre )
                    if (int(mainval,16)+adj_main >= 0) and (int(postval,16)+adj_post >= 0) and (int(preval,16)+adj_pre>= 0):
                        res, pre_val = foxfile.createPreEmphasisCMDs(preemphasis, adj_main, adj_post, adj_pre)
                        if(rcomP != None):
                            fox_connect.runEmphasisCMDtoBCMShell(rcomP, res)
                            fox_connect.runTestCmdToCOMPort(rcomP, testcmds, terminator, wait_time, pre_val)
                
                #Show Test result
                restitle = ["TestCMD", "Emphasis(Post, Main, Pre)", "Temp", "Status"]
                fox_connect.showTestResult("Pre-Emphasis Test result", restitle, "")
                
                #Close log file         
                foxfile.closelogfile()
            continue
       else:
           #print("This not a support command!")
           #helper()
           pass

if __name__ == '__main__':
    main()