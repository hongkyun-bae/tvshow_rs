import numpy as np
import pandas as pd
import time
from pathlib import Path

def computeShowTimeMatrix(PrefMatrix,watchLog,program):
    wLogs = watchLog[(watchLog['TVshowID'] == program['program_title'])\
                     & (watchLog['EntranceTime'] < program['endDate']) \
                     & (watchLog['LeavingTime'] > program['startDate'])]
    watchTime = {}
    for windex,wrow in wLogs.iterrows():
        idx = str(wrow['PanelID'])+'-'+str(wrow['MemberID'])
        
        if idx not in watchTime:
            watchTime[idx] = 0
            
        watchTime[idx]+= (wrow['LeavingTime']-wrow['EntranceTime']).seconds/60
        
    for key in watchTime:
        PrefMatrix[program['program_title']][key] += watchTime[key]
def computeRecTimeMatrix(PrefMatrix,watchLog,program):
    pTime = (program['endDate']-program['startDate']).seconds/60
    wLogs = watchLog[(watchLog['TVshowID'] == program['program_title'])\
                     & (watchLog['EntranceTime'] < program['endDate']) \
                     & (watchLog['LeavingTime'] > program['startDate'])]
    watchTime = {}
    for windex,wrow in wLogs.iterrows():
        idx = str(wrow['PanelID'])+'-'+str(wrow['MemberID'])
        
        if idx not in watchTime:
            watchTime[idx] = 0
            
        watchTime[idx]+= (wrow['LeavingTime']-wrow['EntranceTime']).seconds/60
        
    for key in watchTime:
        wRatio = watchTime[key]/pTime
        PrefMatrix[program['program_title']][key] += wRatio
        
def computePropMatrix_B(PrefMatrix,ConfMatrix,watchLog,program,alpha,beta):
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
      #  if mTVRatio >= alpha:
        wRatio = watchTime[key]/TVwatchTime[key]
            #    wRatio = 0
        PrefMatrix[program['program_title']][key] += wRatio
        ConfMatrix[program['program_title']][key]+=1
    #PrefMatrix = PrefMatrix.divide(ConfMatrix,axis='index')
    
def computePropMatrix_P(PrefMatrix,ConfMatrix,watchLog,program,alpha,beta):
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
      #  if mTVRatio >= alpha:
        wRatio = watchTime[key]/TVwatchTime[key]
        if wRatio < beta:
            continue
            #    wRatio = 0
        PrefMatrix[program['program_title']][key] += wRatio
        ConfMatrix[program['program_title']][key]+=1
    #PrefMatrix = PrefMatrix.divide(ConfMatrix,axis='index')
def computePropMatrix_PM(PrefMatrix,ConfMatrix,watchLog,program,alpha,beta):
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
            #if wRatio ==0:
            #    continue
            if wRatio < beta:
                continue
            #if wRatio < beta:
            #    continue
                #    wRatio = 0
            PrefMatrix[program['program_title']][key] += wRatio
            ConfMatrix[program['program_title']][key]+=1
    #PrefMatrix = PrefMatrix.divide(ConfMatrix,axis='index')
    
def computePropMatrix_PN(PrefMatrix,ConfMatrix,watchLog,program,alpha,beta):
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
      #  if mTVRatio >= alpha:
        wRatio = watchTime[key]/TVwatchTime[key]
        if wRatio < beta: 
            wRatio = 0
        PrefMatrix[program['program_title']][key] += wRatio
        ConfMatrix[program['program_title']][key]+=1
    #PrefMatrix = PrefMatrix.divide(ConfMatrix,axis='index')


# program에 대한 각 사용자의 watchable interval 및 그에 따른 estimated preference를 계산
def computePropMatrix(PrefMatrix, ConfMatrix, watchLog, program, alpha, beta):
    pTime = (program['endDate']-program['startDate']).seconds/60
    wLogs = watchLog[(watchLog['EntranceTime']< program['endDate']) & (watchLog['LeavingTime'] > program['startDate'])]
    watchTime = {}
    TVwatchTime= {}

    for windex, wrow in wLogs.iterrows():
        idx = str(wrow['PanelID'])+'-'+str(wrow['MemberID'])
        TVsTime = wrow['EntranceTime']
        TVeTime = wrow['LeavingTime']
        
        if idx not in watchTime:
            watchTime[idx] = 0
        if idx not in TVwatchTime:
            TVwatchTime[idx] = 0
            
        # if wrow['TVshowID'] == program['program_title']:
        if (wrow['TVshowID'] == program['program_title']) & (wrow['EntranceTime'] >= program['startDate']) & (wrow['LeavingTime'] <= program['endDate']):
            watchTime[idx] += (wrow['LeavingTime']-wrow['EntranceTime']).seconds/60
        if program['startDate'] > wrow['EntranceTime']:
            TVsTime = program['startDate']
        if program['endDate'] < wrow['LeavingTime']:
            TVeTime = program['endDate']
        TVwatchTime[idx] += (TVeTime - TVsTime).seconds/60    # watchable interval
    
    for key in TVwatchTime:
        mTVRatio = TVwatchTime[key]/pTime
        wRatio = watchTime[key]/TVwatchTime[key]
        if wRatio < beta:
            wRatio = 0
        elif mTVRatio < alpha:
            continue

        PrefMatrix[program['program_title']][key] += wRatio
        ConfMatrix[program['program_title']][key] += 1
    #PrefMatrix = PrefMatrix.divide(ConfMatrix,axis='index')


def computePMMatrix(RatingMatrix, watchLog, program):
    pTime = (program['endDate'] - program['startDate']).seconds/60
    wLogs = watchLog[(watchLog['TVshowID'] == program['program_title'])\
                     & (watchLog['EntranceTime'] < program['endDate']) \
                     & (watchLog['LeavingTime'] > program['startDate'])]
    watchTime = {}
    for windex, wrow in wLogs.iterrows():
        idx = str(wrow['PanelID'])+ '-' + str(wrow['MemberID'])
        
        if idx not in watchTime:
            watchTime[idx] = 0
            
        watchTime[idx] += (wrow['LeavingTime'] - wrow['EntranceTime']).seconds/60
        
    for key in watchTime:
        wRatio = watchTime[key]/pTime
        entry = RatingMatrix[program['program_title']][key] 
        if entry > 0:
            if entry < 1:
                entry = 2
            else:
                entry += 1
        else:
            entry = wRatio
        RatingMatrix[program['program_title']][key] = entry


def computePMPrefConfMatrix(PrefMatrix, ConfMatrix, RatingMatrix,alpha):
    for index, row in RatingMatrix.iterrows():
        for col,val in row.iteritems():
            if val > 0:
                PrefMatrix[col][index] = 1
            else:
                PrefMatrix[col][index] = 0
            ConfMatrix[col][index] = 1+alpha*val
            
def computePNMMatrix(PrefMatrix,ConfMatrix,watchLog,program):
    pTime = (program['endDate']-program['startDate']).seconds/60
    wLogs = watchLog[(watchLog['TVshowID'] == program['program_title'])\
                     &(watchLog['EntranceTime'] < program['endDate'])\
                     & (watchLog['LeavingTime'] > program['startDate'])]
    watchTime = {}
    for windex,wrow in wLogs.iterrows():
        idx = str(wrow['PanelID'])+'-'+str(wrow['MemberID'])
        
        #if wrow['PanelID'] not in users:
        #    continue
        if idx not in watchTime:
            watchTime[idx] = 0
            
        watchTime[idx]+= (wrow['LeavingTime']-wrow['EntranceTime']).seconds/60
        
    for key in watchTime:
        wRatio = watchTime[key]/pTime
        PrefMatrix[program['program_title']][key] += wRatio
        ConfMatrix[program['program_title']][key] +=1
    #PrefMatrix = PrefMatrix.divide(ConfMatrix,axis='index')


# trainEPG: Episodes of training set,
# trainWL: Watching log of training set,
# programs2: TV shows of training set
def BuildMatrix(method, CV, trainEPG, trainWL, programs2, users2):
    PrefMatrix = pd.DataFrame(0.0, columns = programs2, index = users2)
    ConfMatrix = pd.DataFrame(1.0, columns = programs2, index = users2)
    RatingMatrix = 0
    if method in ['PM','PNM','Prop','Prop_P','Prop_PM','Prop_PN','Prop_B','Prop_New']:
        ConfMatrix = pd.DataFrame(0.0, columns = programs2, index = users2)
        if method =='PM':
            RatingMatrix = pd.DataFrame(0.0, columns = programs2, index = users2)
        
    unit = int(len(trainEPG)*0.01)
    cnt = 0
    for index, row in trainEPG.iterrows():
        if cnt%unit == 0:
            print(cnt/unit, '%...')
        if method =='ST':
            computeShowTimeMatrix(PrefMatrix, trainWL, row)
        elif method =='RT':
            computeRecTimeMatrix(PrefMatrix, trainWL, row)
        elif method=='PM':
            computePMMatrix(RatingMatrix, trainWL, row)
        elif method=='PNM':
            computePNMMatrix(PrefMatrix, ConfMatrix, trainWL, row)
        elif method=='Prop':
            computePropMatrix(PrefMatrix, ConfMatrix, trainWL, row, 0.5, 0.1)    # row: each episode
        elif method =='Prop_New':
            computePropMatrix(PrefMatrix, ConfMatrix, trainWL, row, 0.5, 0.1)
        elif method=='Prop_P':
            computePropMatrix_P(PrefMatrix, ConfMatrix, trainWL, row, 0.5, 0.1)
        elif method =='Prop_PM':
            computePropMatrix_PM(PrefMatrix, ConfMatrix, trainWL, row, 0.5, 0.1)
        elif method =='Prop_PN':
            computePropMatrix_PN(PrefMatrix, ConfMatrix, trainWL, row, 0.5, 0.1)
        elif method =='Prop_B':
            computePropMatrix_B(PrefMatrix, ConfMatrix, trainWL, row, 0.5, 0.1)
        elif method.startswith('Prop'):
            computePropMatrix(PrefMatrix, ConfMatrix, trainWL, row, 0.9, 0.1)
        else:
            return -1
        cnt+=1

    path1 = 'data/' + str(CV) + 'CV/ProgPrefMatrix_' + method + '.df'
    path2 = 'data/' + str(CV) + 'CV/ProgConfMatrix_' + method + '.df'

    # if method =='PM':
    #     computePrefConfMatrix(PrefMatrix, ConfMatrix, RatingMatrix, 0.4)
    #     RatingMatrix.to_pickle(path1)
    
    Path(path1).parent.mkdir(parents=True, exist_ok=True)
    Path(path2).parent.mkdir(parents=True, exist_ok=True)

    ConfMatrix.to_pickle(path2)
    PrefMatrix.to_pickle(path1)

    return PrefMatrix, ConfMatrix


def BuildMatrix_sample(method, CV, trainEPG, trainWL, programs2, users2, sample_size):
    # print('Start buildMatrix for sampling')

    PrefMatrix = pd.DataFrame(0.0, columns=programs2, index=users2)
    ConfMatrix = pd.DataFrame(1.0, columns=programs2, index=users2)

    if method in ['PM', 'PNM', 'Prop', 'Prop_P', 'Prop_PM', 'Prop_PN', 'Prop_B', 'Prop_New']:
        ConfMatrix = pd.DataFrame(0.0, columns=programs2, index=users2)

    unit = int(len(trainEPG) * 0.01)
    cnt = 0
    for index, row in trainEPG.iterrows():
        if cnt % unit == 0:
            print(cnt / unit, '%...')

        computePropMatrix(PrefMatrix, ConfMatrix, trainWL, row, 0.5, 0.1)
        cnt += 1

    path1 = '../wALSResult/' + str(CV) + 'CV/PrefMatrix_' + method + '_' + str(sample_size) + '.df'
    path2 = '../wALSResult/' + str(CV) + 'CV/ConfMatrix_' + method + '_' + str(sample_size) + '.df'

    # if method == 'PM':
    #     computePrefConfMatrix(PrefMatrix, ConfMatrix, RatingMatrix, 0.4)
    #     RatingMatrix.to_pickle(path)

    ConfMatrix.to_pickle(path2)
    PrefMatrix.to_pickle(path1)

    return PrefMatrix, ConfMatrix