# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 09:59:23 2019

@author: Brian
"""
import time
import os
import sys

vsetup = 0
vend   = 0
uutcfg = 0

params = {}
uuts = {}
macrolist = []
testcmdlist = []
emphasis_params = {}
traftest_list = []

logfp = None
logfile =""

""" Return pre-emphasis 0x0f0000092108 """
def getPreempRegval(main, pre, post):
    preemp = post[2:].zfill(2)+main[2:].zfill(2)+pre[2:].zfill(2)
    return preemp

def createPreEmphasisCMDs(em_params,adj_main,adj_post,adj_pre):
    
    #for k, v in enumerate(em_params):
    #    print("{0:2} {1:20} {2:40}".format(k, v, em_params[v]))
    
    portrange=""    
    ports=[]
    post=0x0
    pre=0x0
    main=0x0
    lane=""
    lane_list=[]
    emphasis_cmd=""
    emp_cmd_list=[]
    ret_emphasis_list=[]
    pre_emphasis_value=[]
    
    if "port_range" in em_params:
        portrange = em_params["port_range"]
        ports = portrange.split(",")
        
    if "emphasis_main" in em_params:
        main = em_params["emphasis_main"]
        main = hex(int(main,16)+adj_main)
        
    if "emphasis_pre" in em_params:
        pre = em_params["emphasis_pre"]   
        pre = hex(int(pre,16)+adj_pre)
        
    if "emphasis_post" in em_params:
        post = em_params["emphasis_post"] 
        post = hex(int(post,16)+adj_post)
     
    if int(main,16) < 0 or int(pre,16) < 0 or int(post,16) < 0:
        print("Add preemphasis (post,main,pre) values wrong {0}{1}{2}".format(post,main,pre))
        return ret_emphasis_list, [post, main, pre]
        
    if "emphasis_regval" in em_params:
        regval = em_params["emphasis_regval"] 
        
    if "emphasis_lane" in em_params:
        lane = em_params["emphasis_lane"]
        lane_list=lane.split(",")
        
    if "emphasis_lane" in em_params:
        emphasis_cmd = em_params["emphasis_cmd"]
        emp_cmd_list = emphasis_cmd.split()
         
    #check port range and lane list
    if (len(ports)==len(lane_list)):
        for inx, p in enumerate(ports):
            
            lane = lane_list[inx]
                        
            epdm_cli_str = ""
            for i in range(len(emp_cmd_list)):
                if (emp_cmd_list[i] == "port"):
                    epdm_cli_str += str(p) + " "
                elif (emp_cmd_list[i] == "regval"):
                    preemp = getPreempRegval(main, pre, post)
                    epdm_cli_str += str(regval)[0:-6] + preemp +" "
                elif  (emp_cmd_list[i][0:4] == "lane"):
                    epdm_cli_str += "lane="+ str(lane) + " "
                else:
                    epdm_cli_str += emp_cmd_list[i] + " "
            
            
            ret_emphasis_list.append(epdm_cli_str[0:-1])
    
    #Add pre_emphasis value (main, pre, post)
    pre_emphasis_value = [post, main, pre]
            
    return  ret_emphasis_list, pre_emphasis_value
    
"""
Example:
    preempcmd PREEMPHASIS
    bcmshell_cmd bcm_shell
    diagtest_cmd linespeed extp port_range FF 64 50 10  
    port_range 1,24
    emphasis_adjust_range 0x2
    emphasis_pre  0x8
    emphasis_post 0x09
    emphasis_main 0x22
    emphasis_regval  0x0f0000092208
    emphasis_lane 0,1,2,3
    emphasis_if   line
    emphasis_cmd  "epdm_cli pre-emphasis set port regval lane=0 if=line"
    epdm_cr_mode  "epdm port xe12-xe23 sp=10000 line_intf=11 sys_intf=15"
endpreempcmd
"""
def readPreEmphasisCFGfile(filename):   
    preEmphasisfind = 0
    preempcmdname = ""
    try:
        with open(filename, 'r') as fp:
            for line in fp.readlines():
                line = line.strip()

                if line[0:9] == "preempcmd":
                     tmp = line.split()
                     
                     if(len(tmp)>=1):
                         preempcmdname = tmp[1]
                         preEmphasisfind = 1
                elif line[0:10] == "endtestcmd":
                     preEmphasisfind = 0                     
                     preempcmdname = ""
                else:
                    """copy each emphasis setting to list"""
                    if (preEmphasisfind == 1):
                            
                        if line[0:1] == "#" or line[0:1] == "":
                            continue
                        else:
                            tmp = line.split()
                            
                            if(len(tmp)>=2):
                                if tmp[0] == "emphasis_cmd" or tmp[0] == "traftest_cmd" \
                                    or tmp[0] == "epdm_cr_mode":
                                        
                                    cmdstr = line.split("\"")
                                    
                                    if(len(cmdstr)>=2):
                                        emphasis_params.update({tmp[0]:cmdstr[1]})
                                else:
                                    emphasis_params.update({tmp[0]:tmp[1]})
                              
                    else:
                        pass

                continue
        fp.closed

        return emphasis_params
    except:
         print("open a readPreEmphasisCFGfile file error")
         return None

"""
 Example: create traffic test cmd for pre-emphasis
 1 traftest_cmd         linespeed extp port_range FF 64 50 10                                 
 2 port_range           13,14,15,16  
"""
def createEmphasisTrafTest(emph_params):
    global traftest_list
    
    traftest  = ""
    portrange = ""
    portlist   = []
    trafcmdstr = ""
    trafcmdlist = []
    
    if "traftest_cmd" in emph_params:
        traftest = emph_params["traftest_cmd"]
        trafcmdlist = traftest.split()
        
        
    if "port_range" in emph_params:
        portrange = emph_params["port_range"]
        tmp = portrange.split(",")
        
        #port range 1,2 
        for i in range(len(tmp)):
            portlist.append(tmp[i])
    
    if portrange != "" and traftest != "":
        
        for i in range(0, len(portlist),2):
            
            ports = portlist[i] + "-"+ portlist[i+1]
            trafcmdstr = ""
            trafcmdlist[0] + " " + trafcmdlist[1] +" " + ports 
            
            for s in range(len(trafcmdlist)):
                if s == 2:
                    trafcmdstr += ports + " "
                else:    
                    trafcmdstr += trafcmdlist[s] + " "
                
            #print(trafcmdstr[0:-1])
            traftest_list.append(trafcmdstr[0:-1])
        
    if(trafcmdstr!=""):
        #traftest_list.append(trafcmdstr[0:-1])
        return traftest_list
    else:
        return None
"""
Example:
testcmd
    cmd_file autotest_cmdfile.txt
endtestcmd 
"""
def readCMDTestfile(filename):   
    global testcmdlist
    
    testcmdfind = 0
    testcmdname = ""
    sublist = []
    cmdlist = []
    try:
        with open(filename, 'r') as fp:
            for line in fp.readlines():
                line = line.strip()

                if line[0:7] == "testcmd":
                     tmp = line.split()
                     
                     if(len(tmp)>=1):
                         testcmdname = tmp[1]
                         #print("new testcomd is defined: [" + testcmdname + "]")
                         testcmdfind = 1
                         sublist = []

                elif line[0:10] == "endtestcmd":
                     testcmdfind = 0
                     if(testcmdname !=""):
                         testcmdlist.append([testcmdname,sublist])
                         #print(testcmdlist)
                     testcmdname = ""
                     sublist = []
                else:
                    """testcmdfind cmd_file xxx.txt"""
                    if (testcmdfind == 1):
                        
                        if line[0:8] == "cmd_file":
                            cmdlist = []
                            sublist = []
                            tmp = line.split(' ')
                            
                            if(len(tmp)>=1):
                                cmdfile_name = tmp[1]
                                print("Add more test command list file: " + cmdfile_name)
                                
                                if (cmdfile_name !=""):
                                    #TODO open command file
                                    with open(cmdfile_name, 'r') as cmdfp:
                                        for cmdline in cmdfp.readlines():
                                            cmdline = cmdline.strip()
                                            cmdargs = cmdline.split()
                                            cmdlist = []
            
                
                                            if cmdline[0:1] == "#" or cmdline[0:1] == "":
                                                continue
                                            else:
                                                for x in range(len(cmdargs)):
                                                     cmdlist.append(cmdargs[x])
                                                sublist.append(cmdlist)
                                    
                                    cmdfp.closed
             
                    else:
                        testcmdfind = 0
                        sublist = []

                continue
        fp.closed


        #return test cmd list
        return (testcmdlist)
    except:
         #print("The testcmd file is ingored.")
         return None
"""
Example:
    macro MACRO_NAME
        madd {xxxx}
        madd {xxxx}
    endmarco
"""
def readMacrofile(filename):

    marcofind = 0
    macroname = ""
    sublist = []
    cmdlist = []

    try:
       with open(filename, 'r') as fp:
            for line in fp.readlines():
                line = line.strip()

                if line[0:5] == "macro":
                     #if macro define another new one
                     if (marcofind == 1):
                         macrolist.append([macroname,sublist])
                         macroname = ""
                         sublist = []

                     tmp = line.split()
                     macroname = tmp[1]
                     #print("new Marco is defined: [" + macroname + "]")
                     marcofind = 1
                     sublist = []

                elif line[0:8] == "endmacro":
                     marcofind = 0
                     if(macroname !=""):
                         macrolist.append([macroname,sublist])
                         #print(macrolist)
                     macroname = ""
                     sublist = []

                else:
                    """madd {"newcommand"}"""
                    if (marcofind == 1):
                        if line[0:4] == "madd":
                            cmdlist = []
                            tmp = line.split('{')
                            if(len(tmp)>=1):
                                ss = tmp[1]
                                ss = ss[:-1]
                                cmdargs = ss.split()
                                for i in range(len(cmdargs)):
                                    cmdlist.append(cmdargs[i])
                                    #print(cmdstr[i])
                                sublist.append(cmdlist)
                        else:
                             if line[0:1] == "#" or line[0:1] == "":
                                 continue
                    else:
                        marcofind = 0
                        sublist = []

                    continue
            fp.closed

            #Append the final Macro define to list
            if (marcofind == 1):
                 macrolist.append([macroname,sublist])
                 #print(macrolist)
                 macroname = ""
                 sublist = []
                 marcofind = 0

            #print(macrolist)
            return macrolist
    except:
         print("open a file error")
         return None

"""
Read auto test config file
Example:
vsetup parameters
 vsetup ip 172.18.60.244
vend
"""
def readCFGfile(filename):
    comment = ""
    commentstart = 0
    content = ""
    global uutcfg

    try:
        with open(filename, 'r') as fp:
            for line in fp.readlines():
                line = line.strip()

                if line[0:1] == "#" or line[0:1] == "" :
                    continue
                elif line[0:6] == "vsetup":
                    vsetup = 1
                    continue
                elif line[0:4] == "vset":
                    if (vsetup == 1):
                        tmp = line.split()
                        ss = tmp[2]
                        if (ss[0:1] == "\""):
                            commentstart = 1
                            comment = tmp[1]
                        else:
                            params.update({tmp[1]:tmp[2]})
                elif line[0:4] == "vend":
                    vsetup = 0
                    continue
                elif line[0:3] == "uut":
                    uutcfg = 1
                    continue
                elif line[0:6] == "enduut":
                    uutcfg = 0
                    break #To end pharse the cfg file in here
                else:
                     #TODO set UUT cfg
                    if uutcfg == 1:
                        tmp = line.split()
                        if(len(tmp)>=2):
                            uuts.update({tmp[0]:tmp[1]})

                        continue
                    if line[0:1] == "\"" and commentstart == 1:
                        params.update({comment:content})
                        commentstart = 0
                        continue
                    #TODO add comments in parameter dictionary
                    if (commentstart == 1):
                        content += line
                        continue
                    else:
                        #print("Not define parameters ")
                        print("Not define variables ==> " +line)

        fp.closed
    except:
         print("open file error")
         return "None"

def showparam():
    print("Show auto test cfg parameters")
    for k, v in params.items():
        print("{0:20}{1:50}".format(k,v))
        
    #print(params)
    pass

def showUUTcfg():
    print("Show UUT configuration")
    for k, v in uuts.items():
        print("{0:20}{1:50}".format(k,v))
    
    #print(uuts)
    pass

def showpreemphasis():
    print("Show pre-emphasis parameters")
    for k, v in emphasis_params.items():
        print("{0:20}{1:50}".format(k,v))
    #for e in emphasis_params:
    #    for m in e:
    #        print("{0:10}".format(m))
    #print(emphasis_params)
    pass    

def readpreemphasis(key):
    if key in emphasis_params:
        return [emphasis_params[key]]
    else:
        return ""

def getparam():
    """ return cfg  parameters """
    return params

def findvalue(key):
    for i, j in params.items():
        if i == key:
           return j

def finduutcfg(key):
    for i, j in uuts.items():
        if i == key:
            return j
        
def isLogfileOpen():
    global logfp
    if logfp != None:
        #print("isLogfileOpen ok")
        return logfp
    else:
        #print("isLogfileOpen None")
        return None
    
def writelogtofile(msg):
    global logfp
    try:
        if logfp != None:
            logfp.write(msg+"\n")
        else:
            print("error to find log filePtr")
    except:
        print("write log file error")
        
def openlogfile(filedir, filename):
    global logfp
    global logfile
    
    ns = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    
    if sys.platform == "win32":
        filepath = os.path.join(os.getcwd()+"\logs", filename+"_"+ns+".log")
    else:
        filepath = filedir+"/"+filename+"_"+ns+".log"
        
    print(filepath) 
    logfile =  filename+"_"+ns+".log"
    
    try:
        if not os.path.exists(filedir):
            os.makedirs(filedir)
            print("create the logs file dir: "+filedir)
            
        logfp = open(filepath, 'w+')
        logfp.write("###Create a test log:"+ns+"###\n")
        #logfp.close()
    except:
         print("open log file error")
         
def closelogfile():
    global logfp
    global logfile
    
    try:
        if logfp != None:
            logfp.close()
            print("closed log file", logfile)
            logfp = None
            logfile = None
        else:
            print("closed log " + logfile + " file is not open")
        
    except:
         print("closed log file " + logfile + " error")
    
def main():
    global logfp
        
    filename = "autotest_template.cfg"
    readCFGfile(filename)
    showparam()
    showUUTcfg()

    #host = findvalue("host_ip")
    #print(host)
    #readMacrofile(filename)
    log_dir = findvalue("log_dir")
    log_file = findvalue("log_file")
   
    
    if sys.platform == "win32":
        filedir  = os.getcwd()+"\logs"
        if not os.path.exists(filedir):
            os.makedirs(filedir)
      
    else:
        filedir = log_dir

    #openlogfile(filedir, log_file)
    #openlogfile(filename)
    #time.sleep(2)
    #writelogtofile("test")
    #time.sleep(2)
    
    #closelogfile()
    #readMacrofile(filename) 
    #testcmd = readCMDTestfile(filename)
    #print(testcmd)
    
    preemphasis = readPreEmphasisCFGfile(filename)
    
    for k, v in enumerate(preemphasis):
        print("{0:2} {1:20} {2:40}".format(k, v, preemphasis[v]))

    diag_traf_cmds = createEmphasisTrafTest(preemphasis)
    #print(diag_traf_cmds)
    #Show diag traffic test command
    for cmds in diag_traf_cmds:
        print(cmds)
    
    adj_main= adj_pre = adj_post = 0
    count = 0
    while (adj_main<=2):
        if adj_main == 0:
            res, pre_val = createPreEmphasisCMDs(preemphasis,adj_main, adj_post, adj_pre)
        else:
            res, pre_val = createPreEmphasisCMDs(preemphasis,adj_main, adj_post, adj_pre)
            #print(res,pre_val)
            res, pre_val = createPreEmphasisCMDs(preemphasis,-adj_main, adj_post, adj_pre)
            #print(res)
        adj_main+=1
        print(res)
        
    #Create the traffic test command for pre-emphasis    
    #createEmphasisTrafTest(preemphasis)
     
    #showparam()
    #showUUTcfg()
    #showpreemphasis()
    res = readpreemphasis("epdm_cr_mode")
    print(res)
        
if __name__ == "__main__":
    main()