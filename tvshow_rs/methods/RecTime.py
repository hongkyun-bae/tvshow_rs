import numpy as np
import pandas as pd
from datetime import datetime,timedelta,time
import math
# import tensorly as tl
# from tensorly.decomposition import parafac
import methods.PM as PM
import operator
import random
         
def checkRatio(val):
    if val <=0.25:
        return 0.25
    if val <=0.5:
        return 0.5
    if val <=0.75:
        return 0.75
    if val <=1.0:
        return 1.0
    
def Recommend_RT(epg_df,userLog,PrefMatrix,matrix,recTime):
    programs_df = epg_df[(epg_df['startDate'] <= recTime) & (epg_df['endDate'] > recTime)] 
    #programs = programs_df['program_title']
    
    RecList = {}
    k=5
    #users = PrefMatrix.index
    #items = PrefMatrix.columns
    users = {}
    items = {}

    ratio_idx = {0.25:0,0.50:1,0.75:2,1.0:3}

    for index,user in enumerate(PrefMatrix.index):
        users[user] = index
    for index,item in enumerate(PrefMatrix.columns):
        items[item] = index


    user_idx = str(userLog['PanelID'])+'-'+str(userLog['MemberID'])
    
    if user_idx not in users:
        return 0 
    
    uId = users[user_idx]
    
    
    for p_id, program in programs_df.iterrows():
        eId = 0
        startratio = 0
        wId = 0
        pTime = (program['endDate']-program['startDate']).seconds/60
        pg = program['program_title']
        
        if pg not in items:
            continue
        
        ItIdx = items[pg]
 
        startratio = 0
        starttime = (recTime - program['startDate']).seconds/60
        startratio = starttime/pTime
        wId = ratio_idx[checkRatio(startratio)]
        
        if pg == userLog['TVshowID']:
            if userLog['EntranceTime'] > program['startDate']:
                eTime = (userLog['EntranceTime'] - program['startDate']).seconds/60
                eRatio = eTime/pTime
                eId = ratio_idx[checkRatio(eRatio)]
        else:
            eId = wId
        RecList[pg] =matrix[eId][wId][uId][ItIdx]
    
    if len(RecList) == 0:
        return 0
    
    sorted_RecList = sorted(RecList.items(),key=operator.itemgetter(1),reverse=True)
    result = []
    
    for item in sorted_RecList:
        result.append(item[0])
    return result

        
def Experiment_RT(epg_df,trainingset,testset,PrefMatrix,matrix,log=0,logName='log.txt'):
    Score = {'TN1':0,'FN1':0,'TN3':0,'FN3':0,'TN5':0,'FN5':0}
    ndcgs ={'TN3':[],'TN5':[]}
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
            result = Recommend_RT(epg_df,wrow,PrefMatrix,matrix,cTime)
            
            if result == 0:
                break
                
            ans,wRatio,watch_time,tv_watch_time = PM.Answer(epg_df,user_idx,testset,cTime,0.1)
            
            if ans == 0:
                break
            
            #print(result,ans)
            PM.ComputeScore(Score,ndcgs,MRR,result,ans)
            
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
#'''
def computeRecTimeTensor(RecTensor,watchLog,program,users,items):
    ratio_idx = {0.25:0,0.50:1,0.75:2,1.0:3}
    
    pTime = (program['endDate']-program['startDate']).seconds/60
    wLogs = watchLog[(watchLog['TVshowID'] == program['program_title'])\
                     & (watchLog['EntranceTime'] < program['endDate']) \
                     & (watchLog['LeavingTime'] > program['startDate'])]
    
    wPanels = list(set(wLogs['PanelID']))
    pgr = program['program_title']
    if pgr not in items:
        return
    pId = items[pgr]
    for panel_id in wPanels:
        wMembers = list(set(wLogs[wLogs['PanelID'] == panel_id]['MemberID']))
        for member_id in wMembers:
            userLog = wLogs[(wLogs['PanelID'] == panel_id) & (wLogs['MemberID'] == member_id)]
            userLog1 = userLog.iloc[0]
            eId = 0
            if userLog1['EntranceTime'] > program['startDate']:
                eTime = (userLog1['EntranceTime'] - program['startDate']).seconds/60
                eRatio = eTime/pTime
                eId = ratio_idx[checkRatio(eRatio)]

            for windex,wrow in userLog.iterrows():
                uId = users[str(panel_id)+'-'+str(member_id)]
                #print (str(panel_id)+'-'+str(member_id))
                startratio = 0
                endratio = 1.0
                if wrow['EntranceTime'] > program['startDate']:
                    starttime = (wrow['EntranceTime'] - program['startDate']).seconds/60
                    startratio = starttime/pTime
                if wrow['LeavingTime'] < program['endDate']:
                    endtime = (wrow['LeavingTime'] - program['startDate']).seconds/60
                    endratio = endtime/pTime
                #print ('startratio:',startratio,'endratio:',endratio)
                sRatioidx = checkRatio(startratio)
                eRatioidx = checkRatio(endratio)
                #print ('sRatioidx:',sRatioidx,'eRatioidx:',eRatioidx)
                while sRatioidx!=eRatioidx:
                    wId = ratio_idx[checkRatio(sRatioidx)]
                    RecTensor[eId][wId][uId][pId] += (sRatioidx - startratio)/0.25
                    #print (eId,wId,uId,pId,(sRatioidx-startratio)/0.25)
                    startratio = sRatioidx
                    sRatioidx+=0.25
                wId = ratio_idx[checkRatio(eRatioidx)]
                RecTensor[eId][wId][uId][pId] += 1 - (eRatioidx - endratio)/0.25
                #print (eId,wId,uId,pId,1- (eRatioidx-endratio)/0.25)
    
def tensorPred(eIdx,wIdx,uIdx,itIdx,factors):
    #userItem = np.dot(factors[2][uIdx].asnumpy(),factors[3][itIdx].asnumpy())
    #entWat = np.dot(factors[0][eIdx].asnumpy(),factors[1][wIdx].asnumpy())
    userItem = np.dot(np.array(factors[2][uIdx]),np.array(factors[3][itIdx]))
    entWat = np.dot(np.array(factors[0][eIdx]),np.array(factors[1][wIdx]))
    return userItem*entWat

def BuildTensor(trainEPG,trainWL,PrefMatrix,rankNum):
    NumTVshows = len(PrefMatrix.columns)
    NumUsers = len(PrefMatrix.index)
    ratio_idx = {0.25:0,0.50:1,0.75:2,1.0:3}
    
    users = {}
    items = {}
    print('NumTVshows: %d, NumUsers:%d'%(NumTVshows, NumUsers))
    
    for index,user in enumerate(PrefMatrix.index):
        users[user] = index
    for index,item in enumerate(PrefMatrix.columns):
        items[item] = index
    
    RecTensor = tl.tensor(np.zeros((4,4,NumUsers,NumTVshows)))
    PredRecTensor = tl.tensor(np.zeros((4,4,NumUsers,NumTVshows)))
    #''' 
    #RecTensor = tl.tensor(np.ones((4,4,NumUsers,NumTVshows)))
    #PredRecTensor = tl.tensor(np.ones((4,4,NumUsers,NumTVshows)))

    #'''
    unit = int(len(trainEPG)*0.01)
    cnt = 0
    for index,row in trainEPG.iterrows():
        if cnt%unit ==0:
            print(cnt/unit,'%....')
        #if cnt > 5:
        #    break
        computeRecTimeTensor(RecTensor,trainWL,row,users,items)
        cnt+=1
    factors = parafac(RecTensor,rank=rankNum)
    
    unit = int(4*4*2014*5211*0.01)
    cnt= 0 
    for eIdx,eP in enumerate(PredRecTensor):
        for wIdx,wP in enumerate(eP):
            for uIdx,usrs in enumerate(wP):
                for itIdx,items in enumerate(usrs):
                    if cnt%unit==0:
                        print(cnt/unit,'%...')
                    #if cnt> 5:
                    #    break
                    PredRecTensor[eIdx][wIdx][uIdx][itIdx] = tensorPred(eIdx,wIdx,uIdx,itIdx,factors)
                    cnt+=1
    #'''
    return RecTensor,PredRecTensor          
    #'''
