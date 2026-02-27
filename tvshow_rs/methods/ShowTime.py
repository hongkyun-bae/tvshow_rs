import methods.PM as PM
import math
import operator
from datetime import datetime,timedelta
import pandas as pd
import time

def computeTimeFactors(wl_startDate,wl_endDate,epg_startDate,epg_endDate):
    remain_ratio = 0.0
    stay_ratio = 0.0
    remain_t = 0.0
    total_t=0.0
    if wl_startDate < epg_startDate:
        total_t = epg_endDate - epg_startDate
        remain_t = epg_endDate - epg_startDate
        if wl_endDate < epg_endDate:
            stay_t = wl_endDate - epg_startDate
        else:
            stay_t = epg_endDate - epg_startDate
    else:
        total_t = epg_endDate - epg_startDate
        remain_t = epg_endDate - wl_startDate
        if wl_endDate < epg_endDate:
            stay_t = wl_endDate - wl_startDate
        else:
            stay_t = epg_endDate - wl_startDate
    
    #print(stay_t.seconds)
    #print(remain_t.seconds)
    
    remain_ratio = remain_t.seconds / float(total_t.seconds)
    remain_ratio = math.ceil(remain_ratio*10)/10
        
    stay_ratio = stay_t.seconds/float(remain_t.seconds)
    stay_ratio = math.ceil(stay_ratio*100)/100
    
    if stay_ratio ==0:
        stay_ratio = 0.01
    if remain_ratio ==0:
        remain_ratio = 0.1
        
    return stay_ratio, remain_ratio


def fill_histogram(wl_startDate,wl_endDate,epg_startDate,epg_endDate):
    stay_ratio, remain_ratio = computeTimeFactors(wl_startDate,wl_endDate,epg_startDate,epg_endDate)
    for st in staying_time:
        if st <= stay_ratio:
            time_factor_histogram[remain_ratio][st]+=1
            
def BuildTimeFactorMatrix(wl_2m_df,epg2_df,method,CV):
    remaining_time = []
    for i in range(0,10):
        remaining_time.append((i+1)/10)

    staying_time = []
    for i in range(0,100):
        staying_time.append((i+1)/100)
        
    time_factor_histogram = pd.DataFrame(0,columns = remaining_time,index = staying_time)
    unit = int(len(wl_2m_df)*0.01)
    i=0
    for wl_index,wl_log in wl_2m_df.iterrows():
        if i%unit == 0:
            print (str(i/unit)+'%.....')
        program_log = epg2_df[(epg2_df['channel'] == wl_log['Channel']) & \
                                    (epg2_df['startDate'] < wl_log['LeavingTime']) \
                                    & (epg2_df['endDate'] > wl_log['EntranceTime'])]
      #  print ('program log num: '+str(len(program_log)))
        for epg_index,epg_log in program_log.iterrows():
            fill_histogram(wl_log['EntranceTime'],wl_log['LeavingTime'],epg_log['startDate'],epg_log['endDate'])
        i+=1
        
    time_factor_histogram = time_factor_histogram.astype(float)
    for column in time_factor_histogram:
        for index in time_factor_histogram.index:
            entry = time_factor_histogram[column][index]
            watched = time_factor_histogram[column][1.00]
            if watched ==0 or entry ==0:
                continue
            tf = watched/float(entry)
            #print (entry,watched,tf)
            time_factor_histogram[column][index] = tf
            
    time_factor_histogram = pd.read_pickle('../wALSResult/'+str(CV)+'CV'+'time_factor_histogram.df')
    
def Recommend_ST(epg_df,wrow, matrix,time_factor_histogram,recTime):
    programs_df = epg_df[(epg_df['startDate'] <= recTime) & (epg_df['endDate'] > recTime)] 
    #programs = programs_df['program_title']
    RecList = {}
    k=5
    
    user_idx = str(wrow['PanelID'])+'-'+str(wrow['MemberID'])
    
    users = matrix.index
    items = matrix.columns
    
    if user_idx not in users:
        return 0 
    
    #print('Recommend ST')
    #print(matrix.head())
    for p_index,programs in programs_df.iterrows():
        stayRatio = 0.0
        remainRatio = 0.0
        pg = programs['program_title']
        if pg not in items:
            continue
        if pg == wrow['TVshowID']:
            stayRatio,remainRatio = computeTimeFactors(wrow['EntranceTime'], recTime, programs['startDate'], programs['endDate'])
        else:
            stayRatio,remainRatio = computeTimeFactors(recTime, recTime, programs['startDate'], programs['endDate'])
        RecList[pg] = matrix[pg][user_idx]*time_factor_histogram[remainRatio][stayRatio]
    
    #for pg in programs:
    #    if pg not in items:
    #        continue
    #    RecList[pg] = matrix[pg][user_idx]
    
    if len(RecList) == 0:
        return 0
    
    sorted_RecList = sorted(RecList.items(),key=operator.itemgetter(1),reverse=True)
    result = []
    val = []
    for item in sorted_RecList:
        result.append(item[0])
        val.append(item[1])
    return result,val
    #print (sorted_RecList)
    #print(user_idx,sorted_RecList)
    #rec = []
    #result = {}
    #print (sorted_RecList)
    
    '''
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
       ''' 
def Experiment_ST(epg_df,trainingset,testset,PrefMatrix,matrix,time_factor_histogram,log=0,logName='log.txt',data_type=0):
    Score = {'TN1': 0, 'FN1': 0, 'TN3': 0, 'FN3': 0, 'TN5': 0, 'FN5': 0, 'TN10': 0, 'FN10': 0, 'TN20': 0, 'FN20': 0}
    ndcgs = {'TN3': [], 'TN5': [], 'TN10': [], 'TN20': []}
    MRR = []
    unit = int(len(testset)*0.01)
    cnt = 0
    k=5
    log_file = open(logName,'w')
    inc_time = timedelta(minutes = 5)

    #print (matrix.head())
    rec_arr = []

    cnt_ans = 0
    cnt_rec = 0
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
            start_time = time.time()
            result,val = Recommend_ST(epg_df,wrow,matrix,time_factor_histogram,cTime)
            #print('one rec time: {}'.format(time.time() - start_time))  
            #print(result,val)

            if result == 0:
                break
                
            ans,wRatio,watch_time,tv_watch_time = PM.Answer(epg_df,user_idx,testset,cTime,0.1)
            #print('answer')
            #print(ans)           
            #print(wRatio)
            if ans == 0:
                ans = 'temp'
                #break
            ''' 
            if result[0] == ans:
                print(cTime,'correct:',result[0],ans,val[0]) 
            else:
                print(cTime,'incorrect:',result[0],ans,val[0])
            '''

            rec_arr.append([user_idx,cTime,result[0],ans,val[0],wRatio,watch_time,tv_watch_time])

            PM.ComputeScore(Score,ndcgs,MRR,result,ans)
            
            if log==1:
                #print (cTime,user_idx,result,ans)
                #print ('C_T:',check_TrueNum,'C_F:','check_FalseNum','UC_T:',uncheck_TrueNum,'UC_F:',uncheck_FalseNum)
                #print(str(cTime)+' '+str(user_idx)+' '+str(result)+' '+str(ans)+'\n')
                log_file.write(str(cTime)+' '+str(user_idx)+' '+str(result)+' '+str(ans)+'\n')
                for key in Score:
                    log_file.write(str(key)+':'+str(Score[key])+' ')
                #    print(str(key)+':'+str(Score[key])+' ')
                #print ('')
                log_file.write('\n')
                #log_file.write('TN: '+str()+' FN: '+str(FalseNum))
                #print (cTime,user_idx,result,ans)
                #print(check_TrueNum,uncheck_TrueNum,check_FalseNum,uncheck_FalseNum)
            cTime +=inc_time
    log_file.close()

    print('# rec & ans:',len(rec_arr))
    #save_df = pd.DataFrame(rec_arr,columns=['user_idx','rec_time','rec_item','ans','val','watch_ratio','watch_time','tv_watch_time']) 
    '''
    if data_type==0:
        save_df.to_csv('RT_200_unwatched.csv',index=False)
    else:
        save_df.to_csv('RT_200_watched.csv',index=False)
    #'''
    return Score, ndcgs, MRR
