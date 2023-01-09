def computePropMatrix(PrefMatrix,ConfMatrix,watchLog,program,alpha,beta):
    pTime = (program['endDate']-program['startDate']).seconds/60
    wLogs = watchLog[(watchLog['EntranceTime']< program['endDate']) & (watchLog['LeavingTime'] > program['startDate'])]
    watchTime = {}
    TVwatchTime= {}
    for windex,wrow in wLogs.iterrows():
        idx = str(wrow['PanelID'])+'-'+str(wrow['MemberID'])
        TVsTime = wrow['EntranceTime']
        TVeTime = wrow['LeavingTime']
        
        if idx not in watchTime:
            watchTime[idx] = 0
        if idx not in TVwatchTime:
            TVwatchTime[idx] = 0
            
        if wrow['TVshowID'] == program['program_title']:
            watchTime[idx]+= (wrow['LeavingTime']-wrow['EntranceTime']).seconds/60
        if program['startDate'] > wrow['EntranceTime']:
            TVsTime = program['startDate']
        if program['endDate'] < wrow['LeavingTime']:
            TVeTime = program['endDate']
        TVwatchTime[idx]+= (TVeTime - TVsTime).seconds/60
    
    for key in TVwatchTime:
        mTVRatio = TVwatchTime[key]/pTime
        if mTVRatio >= alpha:
            wRatio = watchTime[key]/TVwatchTime[key]
            if wRatio < beta:
                wRatio = 0
            PrefMatrix[program['program_title']][key] += wRatio
            ConfMatrix[program['program_title']][key]+=1
    PrefMatrix = PrefMatrix.divide(ConfMatrix,axis='index')
    
    
def Recommend(user_idx,matrix,recTime):
    programs_df = epg_df[(epg_df['startDate'] <= recTime) & (epg_df['endDate'] > recTime)] 
    #programs = programs_df['program_title']
    RecList = {}
    k=5
    users = matrix.index
    items = matrix.columns
    
    if user_idx not in users:
        return 0 
    
    for p_index,programs in programs_df.iterrows():
        pg = programs['program_title']
        if pg not in items:
            continue
        RecList[pg] = matrix[pg][user_idx]
    
    if len(RecList) == 0:
        return 0
    
    sorted_RecList = sorted(RecList.items(),key=operator.itemgetter(1),reverse=True)
    #print (sorted_RecList)
    #print(user_idx,sorted_RecList)
    rec = []
    result = {}
    #print (sorted_RecList)
    for i in range(k):
        result[i]=[]
    top_item = sorted_RecList[0]
    result[0].append(top_item[0])
    ith = 0
    
    #print(result[0])
    
    for rtuple in sorted_RecList[1:]:
        if top_item[1] != rtuple[1]:
            ith+=1
            top_item = rtuple
        if ith == k:
            break
        result[ith].append(rtuple[0])
    
    ith = 0
    while True:
        random.shuffle(result[ith])
        for item in result[ith]:
            rec.append(item)
            if len(rec) ==k:
                return rec
        ith+=1
            
def getWatchRatio(TVshow):
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

def Answer(user_idx,testset,recTime,threshold):
    sTime = recTime
    #eTime = recTime+inc_time+inc_time
    panel_id,member_id = user_idx.split('-')
    wPrograms = testset[(testset['PanelID']==int(panel_id))&(testset['MemberID']==int(member_id))\
                        &(testset['EntranceTime'] <= sTime) & (testset['LeavingTime'] >= sTime)]
  
    pg = wPrograms.iloc[0]
    wRatio = getWatchRatio(pg)
    if wRatio > threshold:
        return pg['TVshowID']
    else:
        return 0
    
    
def Experiment(trainingset,testset,PrefMatrix,matrix,log=0,logName='log.txt'):
    Score = {'TN1':0,'FN1':0,'TN3':0,'FN3':0,'TN5':0,'FN5':0}
    unit = int(len(testset)*0.01)
    cnt = 0
    k=5
    log_file = open(logName,'w')
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
            result = Recommend(user_idx,matrix,cTime,time_factor_histogram)
            
            if result == 0:
                break
                
            ans = Answer(user_idx,testset,cTime,0.1)
            
            if ans == 0:
                break
            
            ComputeScore(Score,result,ans)
            
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
    return Score
