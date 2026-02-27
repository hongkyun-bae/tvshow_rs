import numpy as np
import pandas as pd
from datetime import datetime,timedelta
import math
import operator
import copy
import random
import time
import methods.ShowTime as ShowTime



excluded_watchTimes = []

def Recommend(epg_df, user_idx, matrix, recTime):
    programs_df = epg_df[(epg_df['startDate'] <= recTime) & (epg_df['endDate'] > recTime)]
    #programs = programs_df['program_title']
    RecList = {}
    k=5
    users = matrix.index
    items = matrix.columns
     
    if user_idx not in users:
        return 0 

    for p_index, programs in programs_df.iterrows():    # Initialize RecList dictionary
        stayRatio = 0.0
        remainRatio = 0.0
        pg = programs['program_title']
        if pg not in items:
            continue
        #if time_factor_histogram!=0:
        #    if pg == wrow['TVshowID']:
        #        stayRatio,remainRatio = computeTimeFactors(wrow['EntranceTime'],recTime,programs['startDate'],programs['endDate'])
        #    else:
        #        stayRatio, remainRatio = computeTimeFactors(recTime,recTime,programs['startDate'],programs['endDate'])
        #    RecList[pg] = matrix[pg][user_idx]*time_factor_histogram[remainRatio][stayRatio]
        #else:
        RecList[pg] = matrix[pg][user_idx]


    # RecList[pg] = matrix[pg][user_idx]
    # RecList.append(matrix[pg][user_idx])
    if len(RecList) == 0:
        return 0

    sorted_RecList = sorted(RecList.items(), key=lambda x: x[1], reverse=True)    # Sort RecList by descending-order
    max_val = sorted_RecList[0][1]

    tempResult1 = []
    tempResult2 = []
    for item in sorted_RecList:
        if item[1] == max_val:
            tempResult1.append(item[0])    # Add item having the largest PP value into tempResult1
        else:
            tempResult2.append(item[0])
    
    random.shuffle(tempResult1)
    result = []
    for item in tempResult1:
        #if ConfList[item] >= per:
        result.append(item)
            
    for item in tempResult2:
        #if ConfList[item] >= per:
        result.append(item)

    return result, []
    '''
    result = []
    val = [] 
    for item in sorted_RecList:
        result.append(item[0])
        val.append(item[1])
    return result,val
    '''
    #print (sorted_RecList)
    #print(user_idx,sorted_RecList)
    #rec = []
    #result = {}
    #print (sorted_RecList)
    
    #for i in range(k):
    #    result[i]=[]
    #top_item = sorted_RecList[0]
    #result[0].append(top_item[0])
   # #ith = 0
    
    #print(result[0])
    
    #for rtuple in sorted_RecList[1:]:
    #    if top_item[1] != rtuple[1]:
    #        ith+=1
    #        top_item = rtuple
    #   if ith == k:
    #        break
    #   result[ith].append(rtuple[0])
    
    #ith = 0
    #while True:
    # for item in result[ith]:
    #        rec.append(item)
    #        if len(rec) == k:
    #            return rec
    #    ith+=1
    
#def getWatchRatio(epg_df,TVshow):
#    program = epg_df[(epg_df['program_title'] == TVshow['TVshowID'])\
#                     & (epg_df['channel'] == TVshow['Channel']) \
#                     & (epg_df['startDate'] <= TVshow['EntranceTime']) \
#                     & (epg_df['endDate'] >= TVshow['EntranceTime'])]
    #print (program)
    #print (TVshow)
#    program = program.iloc[0]
#    timeslot = (program['endDate'] - program['startDate']).seconds/60
#    wTime = (TVshow['LeavingTime'] -  TVshow['EntranceTime']).seconds/60
#    return wTime/timeslot

def getWatchRatio(epg_df, TVshow, watchLog):
    program = epg_df[(epg_df['program_title'] == TVshow['TVshowID'])\
                     & (epg_df['channel'] == TVshow['Channel']) \
                     & (epg_df['startDate'] <= TVshow['EntranceTime']) \
                     & (epg_df['endDate'] >= TVshow['EntranceTime'])]
    #print (program)
    #print (TVshow)
    
    program = program.iloc[0]
    
    ## added code
    pTime = (program['endDate']-program['startDate']).seconds/60
    wLogs = watchLog[(watchLog['PanelID'] == TVshow['PanelID']) & (watchLog['MemberID']==TVshow['MemberID']) & (watchLog['EntranceTime']< program['endDate']) & (watchLog['LeavingTime'] > program['startDate'])]
    watchTime = {}
    TVwatchTime= {}
    dict_idx = 0

    for windex, wrow in wLogs.iterrows():
        idx = str(wrow['PanelID']) + '-' + str(wrow['MemberID'])
        TVsTime = wrow['EntranceTime']
        TVeTime = wrow['LeavingTime']
        
        if idx not in watchTime:
            watchTime[idx] = 0
        if idx not in TVwatchTime:
            TVwatchTime[idx] = 0
            
        # if wrow['TVshowID'] == program['program_title']:    # ERROR: several wrows can be employed...
        #     watchTime[idx] += (wrow['LeavingTime']-wrow['EntranceTime']).seconds/60

        if (wrow['TVshowID']==program['program_title']) & (wrow['EntranceTime']>=program['startDate']) & (wrow['LeavingTime']<=program['endDate']):
            watchTime[idx] += (wrow['LeavingTime'] - wrow['EntranceTime']).seconds / 60

        if program['startDate'] > wrow['EntranceTime']:
            TVsTime = program['startDate']
        if program['endDate'] < wrow['LeavingTime']:
            TVeTime = program['endDate']

        TVwatchTime[idx] += (TVeTime - TVsTime).seconds/60
    
    wRatio = -1
    #print (TVwatchTime.keys())
    '''
    for key in TVwatchTime:
        #dict_idx = key
        mTVRatio = TVwatchTime[key]/pTime
        if mTVRatio >= 0.5:
            wRatio = watchTime[key]/TVwatchTime[key]
            dict_idx = key
            if wRatio < 0.1:
                wRatio = 0
    '''
    #'''
    idx = str(TVshow['PanelID']) + '-' + str(TVshow['MemberID'])
    dict_idx = idx
    mTVRatio = TVwatchTime[idx] / pTime
    if mTVRatio >= 0.5:
        wRatio = watchTime[idx] / TVwatchTime[idx]

        if wRatio > 1.0:
            print('wRatio is larger than 1.0')

        if wRatio < 0.1:
            wRatio = 0
            # print(watchTime[idx])
            excluded_watchTimes.append(watchTime[idx])
    #'''
    #timeslot = (program['endDate'] - program['startDate']).seconds/60
    #wTime = (TVshow['LeavingTime'] -  TVshow['EntranceTime']).seconds/60

    if dict_idx == 0:    # In the case that idx cannot be filled with PanelID and MemberID
        watchTime = 0
        TVwatchTime = 0
    else:
        watchTime = watchTime[dict_idx]
        TVwatchTime = TVwatchTime[dict_idx]

    ### TODO fixed to broadcasted interval
    # wRatio = watchTime / pTime    # Isn't it right to block this line? (block on 190417)

    return wRatio, watchTime, TVwatchTime


def Answer(epg_df, user_idx, testset, recTime, threshold):
    sTime = recTime
    #eTime = recTime+inc_time+inc_time
    panel_id, member_id = user_idx.split('-')
    wPrograms = testset[(testset['PanelID'] == int(panel_id)) & (testset['MemberID'] == int(member_id))\
                        & (testset['EntranceTime'] <= sTime) & (testset['LeavingTime'] >= sTime)]
  
    pg = wPrograms.iloc[0]
    # print(user_idx)
    # print(pg)
    wRatio, watch_time, tv_watch_time = getWatchRatio(epg_df, pg, testset)    # compute EP using watchable interval
    if wRatio >= threshold:
        return pg['TVshowID'], wRatio, watch_time, tv_watch_time
    else:
        return 0, 0, 0, 0
    
def ComputeScore(Score, ndcgs, MRR, result, ans):
    #if result[0] == ans:
    #   Score['TN1']+=1
    #    Score['TN3']+=1
    #    Score['TN5']+=1
    #elif ans in result[:3]:
    #    Score['TN3']+=1
    #   Score['TN5']+=1
    #    Score['FN1']+=1
    #elif ans in result[:5]:
    #    Score['TN5']+=1
    #   Score['FN1']+=1
    #    Score['FN3']+=1
    #else:
    #    Score['FN1']+=1
    #    Score['FN3']+=1
    #    Score['FN5']+=1
    
    for i in range(len(result)):
        if result[i] == ans:
            if i == 0:
                Score['TN1']+=1
                Score['TN3']+=1
                Score['TN5']+=1
                Score['TN10'] += 1
                Score['TN20'] += 1
                ndcgs['TN3'].append(math.log(2)/math.log(i+2))
                ndcgs['TN5'].append(math.log(2)/math.log(i+2))
                ndcgs['TN10'].append(math.log(2) / math.log(i + 2))
                ndcgs['TN20'].append(math.log(2) / math.log(i + 2))
            elif i < 3:
                ndcgs['TN3'].append(math.log(2)/math.log(i+2))
                ndcgs['TN5'].append(math.log(2)/math.log(i+2))
                ndcgs['TN10'].append(math.log(2) / math.log(i + 2))
                ndcgs['TN20'].append(math.log(2) / math.log(i + 2))
                Score['TN3']+=1
                Score['TN5']+=1
                Score['TN10'] += 1
                Score['TN20'] += 1
                Score['FN1']+=1
            elif i < 5:
                ndcgs['TN5'].append(math.log(2)/math.log(i+2))
                ndcgs['TN10'].append(math.log(2) / math.log(i + 2))
                ndcgs['TN20'].append(math.log(2) / math.log(i + 2))
                ndcgs['TN3'].append(0)
                Score['FN3']+=1
                Score['FN1']+=1
                Score['TN5']+=1
                Score['TN10'] += 1
                Score['TN20'] += 1
            elif i < 10:
                ndcgs['TN10'].append(math.log(2) / math.log(i + 2))
                ndcgs['TN20'].append(math.log(2) / math.log(i + 2))
                ndcgs['TN3'].append(0)
                ndcgs['TN5'].append(0)
                Score['FN5'] += 1
                Score['FN3'] += 1
                Score['FN1'] += 1
                Score['TN10'] += 1
                Score['TN20'] += 1
            elif i < 20:
                ndcgs['TN20'].append(math.log(2) / math.log(i + 2))
                ndcgs['TN3'].append(0)
                ndcgs['TN5'].append(0)
                ndcgs['TN10'].append(0)
                Score['FN10'] += 1
                Score['FN5'] += 1
                Score['FN3'] += 1
                Score['FN1'] += 1
                Score['TN20'] += 1
            else:
                #'''
                Score['FN1']+=1
                Score['FN3']+=1
                Score['FN5']+=1
                Score['FN10'] += 1
                Score['FN20'] += 1
                ndcgs['TN20'].append(0)
                ndcgs['TN10'].append(0)
                ndcgs['TN5'].append(0)
                ndcgs['TN3'].append(0) 
                #'''
                '''
                Score['FN1'] += len(result) - 6
                Score['FN3'] += len(result) - 6
                Score['FN5'] += len(result) - 6
                ndcgs['TN5'] += [0] * (len(result) - 6)
                ndcgs['TN3'] += [0] * (len(rresult) -6)
                MRR += (
                '''
            MRR.append(1.0/(i+1))


def Experiment(epg_df, trainingset, testset, PrefMatrix, matrix, log=0, logName='log.txt', data_type=0):
    print('PM')

    Score = {'TN1': 0, 'FN1': 0, 'TN3': 0, 'FN3': 0, 'TN5': 0, 'FN5': 0, 'TN10': 0, 'FN10': 0, 'TN20': 0, 'FN20': 0}
    ndcgs = {'TN3': [], 'TN5': [], 'TN10': [], 'TN20': []}
    MRR = []
    unit = int(len(testset)*0.01)
    cnt = 0
    k=5
    log_file = open(logName, 'w')
    inc_time = timedelta(minutes=5)

    rec_arr = []
    for windex, wrow in testset.iterrows():
        if cnt%unit==0:
            print (cnt/unit, '%...')
        cnt += 1
        
        #isWatched = checkWatchedShow(wrow,PrefMatrix)
        
        if wrow['Watched'] == -1:
            continue
        eTime = wrow['EntranceTime']
        lTime = wrow['LeavingTime']
        cTime = eTime

        user_idx = str(wrow['PanelID']) + '-' +str(wrow['MemberID'])
        while cTime < lTime:
            start_time = time.time()
            result, val = Recommend(epg_df, user_idx, matrix, cTime)    # result: list of items sorted by PP value in descending-order
            #print('one rec time: {}'.format(time.time() - start_time))
            if result == 0:
                break
            
            ans, wRatio, watch_time, tv_watch_time = Answer(epg_df, user_idx, testset, cTime, 0.1)
            
            if ans == 0:
                break
            #rec_arr.append([user_idx,cTime,result[0],ans,val[0],wRatio,watch_time,tv_watch_time])
            #rec_arr.append([] 
            #print (result[0],ans)
            ComputeScore(Score, ndcgs, MRR, result, ans)
            
            if log == 1:
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
            cTime += inc_time

    log_file.close()
    #save_df = pd.DataFrame(rec_arr,columns=['user_idx','rec_time','rec_item','ans','val','watch_ratio','watch_time','tv_watch_time']) 
    '''
    if data_type==0:
        save_df.to_csv('ST_200_unwatched.csv',index=False)
    else:
        save_df.to_csv('ST_200_watched.csv',index=False)
    #'''
    #save_df.to_csv('RT_watched.csv',index=False)
    return Score, ndcgs, MRR


def PE_Recommend(epg_df, user_idx, matrix, Confmatrix, recTime, per):
    programs_df = epg_df[(epg_df['startDate'] <= recTime) & (epg_df['endDate'] > recTime)] 
    RecList = {}
    ConfList = {}
    k = 5
    users = matrix.index
    items = matrix.columns
    result = []
    if user_idx not in users:
        return 0 
    for p_index, programs in programs_df.iterrows():
        pg = programs['program_title']
        if pg not in items:
            continue
        ConfList[pg] = Confmatrix[pg][user_idx]
        RecList[pg] = matrix[pg][user_idx]
    
    if len(RecList) == 0:
        return 0
    
    
    #cutPer = int(len(ConfList)*per)
    
    #sorted_ConfList = sorted(ConfList.items(),key=lambda x: x[1], reverse=True)
    sorted_RecList = sorted(RecList.items(), key=lambda x: x[1], reverse=True)
    
    max_val = sorted_RecList[0][1]
    #print(sorted_RecList)
    #topN = {}
    #i=0
    #for item in sorted_RecList:
    #    if i not in topN:
    #        topN[i] = []
    #confItems = sorted_ConfList[:cutPer]
    #confItems = [x[0] for x in confItems]
    
    #print(confItems
    #'''   
    #'''

    tempResult1 = []
    tempResult2 = []

    for item in sorted_RecList:
        if item[1] == max_val:
            tempResult1.append(item[0])
        else:
            tempResult2.append(item[0])
    
    random.shuffle(tempResult1)
    result = []
    for item in tempResult1:
        #if ConfList[item] >= per:
        result.append(item)
            
    for item in tempResult2:
        #if ConfList[item] >= per:
        result.append(item)
    '''
    #'''
    '''
    for item in sorted_RecList:
        #if ConfList[item[0]] >= per:
        result.append(item[0])
    #''' 
    '''
    if len(tempResult1) > 1:
        print (tempResult1)
        print(sorted_RecList)
        print (result)
    ''' 
    if len(result) == 0:
        return 0 
    
    return result


def PE_Experiment(epg_df,trainingset,testset,PrefMatrix,ConfMatrix,per):
    Score = {'TN1': 0, 'FN1': 0, 'TN3': 0, 'FN3': 0, 'TN5': 0, 'FN5': 0}
    ndcgs = {'TN3': [], 'TN5': []}
    MRR = []
    unit = int(len(testset)*0.01)
    cnt = 0
    k=5
    inc_time = timedelta(minutes=5)
    for windex, wrow in testset.iterrows():
        if cnt%unit == 0:
            print(cnt/unit, '%...')
        cnt += 1
        
        #isWatched = checkWatchedShow(wrow,PrefMatrix)
        
        if wrow['Watched'] == -1:
            continue
        eTime = wrow['EntranceTime']
        lTime = wrow['LeavingTime']
        cTime = eTime    # current time?

        user_idx = str(wrow['PanelID'])+'-'+str(wrow['MemberID'])
        while cTime < lTime:
            result = PE_Recommend(epg_df, user_idx, PrefMatrix, ConfMatrix, cTime, per)
            
            if result == 0:
                break
            
 
            ans, wRatio, watch_time, tv_watch_time = Answer(epg_df, user_idx, testset, cTime, 0.1)

            
            if ans == 0:
                break
            
            #print("result:",result)
            #print("answer:",ans)
            ComputeScore(Score,ndcgs,MRR,result,ans)
            
     
            cTime += inc_time

    return Score,ndcgs,MRR
