import json 
dic_main={0:'HeadFixer',1:'Rewarder',2:'Stimulator'}  
dic_headFixer={0:'headFixTime', 1: 'propHeadFix',2:'tightnessHeadFix'}
dic_rewarder={1:'breakBeamDelay',2:'breakBeamSize',3:'entryDelay',4:'entrySize',
              5:'lastBreakBeamTime',6:'lastEntryTime',7:'maxBreakBeamRewards',
              8:'maxEntryRewards',9:'taskSize',10:'totalBreakBeamRewardsToday',11:'totalEntryRewardsToday'}
dic_stimulator={0:'delayTime',1:'lickWithholdTime',2:'mouseLevel',3:'nRewards',4:'responseTime',5:'rewardInterval',6:'rewardNoGo'}
m1=None 
m2=None
m3=None
m4=None
m5=None
with open("AHF_mice_subjects.jsn", 'r') as f:
    a=f.read()
    b=a.replace('\n',',')
    c=json.loads(b.replace('=',':'))
    
def main():
    try:
        for (i,z) in zip(c.keys(),range(len(c))):
            print(str(z)+':'+'    '+i)
        Tag=input('Choose animal to edit or return to edit all:')
        if Tag != '':
            print(c[Tag])
        else:
            for key, values in dic_main.items():
                print (key, values)
            manuel2()
    except KeyboardInterrupt: 
        loop_manuel()
def manuel2():
    global m1, m2, m3,c
    m1=input('Choose class to alter or any key to return: ')
    if m1 == '0':
        for key, values in dic_headFixer.items():
            print(key, values)
        User_input()
        for i in c:
            c[i]['HeadFixer'][dic_headFixer[int(m2)]] =float(m3)
        save_reload()
        loop_manuel()
    elif m1 =='1':
        for key, values in dic_rewarder.items():
            print(key, values)
        User_input()
        for i in c:
            c[i]['Rewarder'][dic_rewarder[int(m2)]] =float(m3)
        save_reload()
        loop_manuel()
    elif m1 =='2':
        for key, values in dic_stimulator.items():
            print(key, values)
        User_input()
        for i in c:
            c[i]['Stimulator'][dic_stimulator[int(m2)]] =float(m3)
        save_reload()
        loop_manuel()
    else:
        main()
def User_input(): 
    global m2, m3
    m2=input('Enter settings to change: ')
    m3=input('Value to change to: ')
    return m2, m3 
def save_reload():
    global c
    c2=json.dumps(c)
    c2=c2.replace(':','=')
    c2=c2.replace(',','\n')
    with open('AHF_mice_subjects.jsn','w') as f2:
        f2.write(c2)
    with open("AHF_mice_subjects.jsn", 'r') as f:
        a=f.read()
        b=a.replace('\n',',')
        c=json.loads(b.replace('=',':'))
def loop_manuel():
    global m4 
    m4=input('Edit additional settings (Yes) or press any to exit:')
    if m4.lower()=='yes' or m4.lower()=='y':
        main()
    else: 
        return 
def loop_manuel2():
    global m5
    m5=input('Edit additional settings (Yes) or press any to exit:')
    if m5.lower()=='yes' or m5.lower()=='y':
        main()
    else:
        return
if __name__ == "__main__":
    main()        
      
        
        




