import numpy as np
import pandas as pd
from datetime import datetime,timedelta,time
import math
import operator
import copy
import random
        
def Recommend(epg_df,user_idx,matrix,recTime):
    programs_df = epg_df[(epg_df['startDate'] <= recTime) & (epg_df['endDate'] > recTime)] 
    programs = programs_df['program_title']
    RecList = {}
    k=5
    users = matrix.index
    items = matrix.columns
    
    if user_idx not in users:
        return 0 
    
    for pg in programs:
        if pg not in items:
            continue
        RecList.append(pg)
    if len(RecList) == 0:
        return 0
    random.shuffle(RecList)
        #RecList.append(matrix[pg][user_idx])

    
    #sorted_RecList = sorted(RecList.items(),key=operator.itemgetter(1),reverse=True)
    result = []
    
    for item in sorted_RecList:
        result.append(item[0])
    return result
    

def getWatchRatio(epg_df,TVshow):
    program = epg_df[(epg_df['program_title'] == TVshow['TVshowID'])\
                     & (epg_df['channel'] == TVshow['Channel']) \
                     & (epg_df['startDate'] <= TVshow['EntranceTime']) \
                     & (epg_df['endDate'] >= TVshow['EntranceTime'])]
    #print (program)
    #print (TVshow)
    program = program.iloc[0]
    timeslot = (program['endDate'] - program['startDate']).seconds/60
    wTime = (TVshow['LeavingTime'] -  TVshow['EntranceTime']).seconds/60
    return wTime/timeslot

def Answer(epg_df,user_idx,testset,recTime,threshold):
    sTime = recTime
    #eTime = recTime+inc_time+inc_time
    panel_id,member_id = user_idx.split('-')
    wPrograms = testset[(testset['PanelID']==int(panel_id))&(testset['MemberID']==int(member_id))\
                        &(testset['EntranceTime'] <= sTime) & (testset['LeavingTime'] >= sTime)]
  
    pg = wPrograms.iloc[0]
    wRatio = getWatchRatio(epg_df,pg)
    if wRatio > threshold:
        return pg['TVshowID']
    else:
        return 0
    
def ComputeScore(Score,ndcgs,MRR,result,ans):   
    for i in range(len(result)):
        if result[i] == ans:
            if i ==0:
                Score['TN1']+=1
                Score['TN3']+=1
                Score['TN5']+=1
                ndcgs['TN3'].append(math.log(2)/math.log(i+2))
                ndcgs['TN5'].append(math.log(2)/math.log(i+2)) 
            elif i < 3:
                ndcgs['TN3'].append(math.log(2)/math.log(i+2))
                ndcgs['TN5'].append(math.log(2)/math.log(i+2))
                Score['TN3']+=1
                Score['TN5']+=1
                Score['FN1']+=1
            elif i < 5:
                ndcgs['TN5'].append(math.log(2)/math.log(i+2))
                ndcgs['TN3'].append(0)
                Score['FN3']+=1
                Score['FN1']+=1
                Score['TN5']+=1
            else:
                Score['FN1']+=1
                Score['FN3']+=1
                Score['FN5']+=1
                ndcgs['TN5'].append(0)
                ndcgs['TN3'].append(0) 
            MRR.append(1.0/(i+1))
            
def Experiment(epg_df,trainingset,testset,PrefMatrix,matrix,log=0,logName='log.txt'):
    Score = {'TN1':0,'FN1':0,'TN3':0,'FN3':0,'TN5':0,'FN5':0}
    ndcgs = {'TN3':[],'TN5':[]}
    MRR = []
    unit = int(len(testset)*0.01)
    cnt = 0
    k=5
    log_file = open(logName,'w')
    inc_time = timedelta(minutes = 5)
    for windex,wrow in testset.iterrows():
        if cnt%unit==0:
            print (cnt/unit,'%...')
        cnt+=1
        
        #isWatched = checkWatchedShow(wrow,PrefMatrix)
        
        if wrow['Watched']==-1:
            continue
        eTime = wrow['EntranceTime']
        lTime = wrow['LeavingTime']
        cTime = eTime

        user_idx = str(wrow['PanelID'])+'-'+str(wrow['MemberID'])
        while cTime < lTime:
            result = Recommend(epg_df,user_idx,matrix,cTime)
            
            if result == 0:
                break
            
            ans = Answer(epg_df,user_idx,testset,cTime,0.1)
            
            if ans == 0:
                break
            
            #print (result[0],ans)
            ComputeScore(Score,ndcgs,MRR,result,ans)
            
            if log==1:
                #print (cTime,user_idx,result,ans)
                #print ('C_T:',check_TrueNum,'C_F:','check_FalseNum','UC_T:',uncheck_TrueNum,'UC_F:',uncheck_FalseNum)
                #print(str(cTime)+' '+str(user_idx)+' '+str(result)+' '+str(ans)+'\n')
                log_file.write(str(cTime)+' '+str(user_idx)+' '+str(result)+' '+str(ans)+'\n')
                for key in Score:
                    log_file.write(str(key)+':'+str(Score[key])+' ')
                    #print(str(key)+':'+str(Score[key])+' ')
                #print ('')
                log_file.write('\n')
                #log_file.write('TN: '+str()+' FN: '+str(FalseNum))
                #print (cTime,user_idx,result,ans)
                #print(check_TrueNum,uncheck_TrueNum,check_FalseNum,uncheck_FalseNum)
            cTime +=inc_time
    log_file.close()
    return Score,ndcgs,MRR
