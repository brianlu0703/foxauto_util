# foxauto_util
It's auto-test utility to test single device 
1. Open a Serial port 
2. Open a Console Switch line to access device
3. Power device
4. Run all test command from file to Macro cfg file
5. Add and Del a test command


    _         _          _____         _      ___   ____
   / \  _   _| |_ ___   |_   _|__  ___| |_   / _ \ |___ \
  / _ \| | | | __/ _ \    | |/ _ \/ __| __| | | | |  __) |
 / ___ \ |_| | || (_) |   | |  __/\__ \ |_  | |_| | / __/
/_/   \_\__,_|\__\___/    |_|\___||___/\__|  \___(_)_____|


Auto test conf. file is autotest_template.cfg
Add more test command list file: autotest_cmdfile.txt
Please "q" to quit auto test program.
AUTOTEST/>help

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

AUTOTEST/>  
