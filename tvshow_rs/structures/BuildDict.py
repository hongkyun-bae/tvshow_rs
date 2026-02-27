import pandas as pd
from pathlib import Path


def BuildDictMatrix(method, CV, trainEPG, trainWL, programs2, users2):
    print('Building dictionary...')
    print('Users: ' + str(len(users2)) + ', Programs: ' + str(len(programs2)))
    # PrefDict = defaultdict(lambda: {})

    PrefDict = {}    # Initialize PrefDict
    PrefDict = PrefDict.fromkeys(users2)
    for uid in PrefDict.keys():
        # print(uid)
        PrefDict[uid] = {}
        PrefDict[uid] = PrefDict[uid].fromkeys(programs2)
        for pid in PrefDict[uid].keys():
            PrefDict[uid][pid] = []

    print('Building matrix...')
    PrefMatrix = pd.DataFrame(0.0, columns=programs2, index=users2)
    ConfMatrix = pd.DataFrame(1.0, columns=programs2, index=users2)

    if method in ['PM', 'PNM', 'Prop', 'Prop_P', 'Prop_PM', 'Prop_PN', 'Prop_B', 'Prop_New']:
        ConfMatrix = pd.DataFrame(0.0, columns=programs2, index=users2)

    print('>> ComputePropDictMatrix()')
    unit = int(len(trainEPG) * 0.01)
    cnt = 0
    for index, episode in trainEPG.iterrows():
        if cnt % unit == 0:
            print(cnt / unit, '%...')

        ComputePropDictMatrix(PrefDict, PrefMatrix, ConfMatrix, trainWL, episode, 0.5, 0.1)
        cnt += 1

    print('Writing the base file...')
    path = '../origin/' + str(CV) + 'CV/Epi_' + method
    f = open(path + '.base', 'w')

    unit = int(len(PrefDict) * 0.01)
    cnt = 0
    for idx1, key1 in enumerate(PrefDict):
        if cnt % unit == 0:
            print(cnt / unit, '%....')

        for idx2, key2 in enumerate(PrefDict[key1]):
            if len(PrefDict[key1][key2]) == 0:
                continue    # Skip the TV show if user's watching-count is equal to zero

            for pref in PrefDict[key1][key2]:
                f.write(str(idx1+1) + '\t' + str(idx2+1) + '\t' + str(pref) + '\n')

        cnt += 1

    f.close()

    print('Writing the df files...')
    path_matrix1 = '../origin/' + str(CV) + 'CV/EpiPrefMatrix_' + method + '.df'
    path_matrix2 = '../origin/' + str(CV) + 'CV/EpiConfMatrix_' + method + '.df'

    PrefMatrix.to_pickle(path_matrix1)
    ConfMatrix.to_pickle(path_matrix2)

    return PrefDict, PrefMatrix, ConfMatrix


def ComputePropDictMatrix(PrefDict, PrefMatrix, ConfMatrix, watchLog, episode, alpha, beta):
    pTime = (episode['endDate'] - episode['startDate']).seconds / 60
    wLogs = watchLog[(watchLog['EntranceTime'] < episode['endDate']) & (watchLog['LeavingTime'] > episode['startDate'])]

    watchTime = {}
    TVwatchTime = {}

    for windex, wrow in wLogs.iterrows():
        idx = str(wrow['PanelID']) + '-' + str(wrow['MemberID'])
        TVsTime = wrow['EntranceTime']
        TVeTime = wrow['LeavingTime']

        if idx not in watchTime:
            watchTime[idx] = 0
        if idx not in TVwatchTime:
            TVwatchTime[idx] = 0

        # if wrow['TVshowID'] == episode['program_title']:
        #     watchTime[idx] += (wrow['LeavingTime'] - wrow['EntranceTime']).seconds / 60


        if (wrow['TVshowID']==episode['program_title']) & (wrow['EntranceTime']>=episode['startDate']) & (wrow['LeavingTime']<=episode['endDate']):
            watchTime[idx] += (wrow['LeavingTime'] - wrow['EntranceTime']).seconds / 60

        if episode['startDate'] > wrow['EntranceTime']:
            TVsTime = episode['startDate']
        if episode['endDate'] < wrow['LeavingTime']:
            TVeTime = episode['endDate']

        TVwatchTime[idx] += (TVeTime - TVsTime).seconds / 60   # Compute user's watchable interval for corresponding episode

    for key in TVwatchTime:
        mTVRatio = TVwatchTime[key] / pTime
        wRatio = watchTime[key] / TVwatchTime[key]

        if wRatio > 1.0:
            print('wRatio is larger than 1.0')

        if wRatio < beta:
            continue    # Skip the user whose wRatio for corresponding episode is smaller than beta
        elif mTVRatio < alpha:
            continue

        PrefDict[key][episode['program_title']].append(wRatio)

        PrefMatrix[episode['program_title']][key] += wRatio
        ConfMatrix[episode['program_title']][key] += 1


def buildDict(users, programs):
    newDict = {}
    newDict = newDict.fromkeys(users)
    for uid in newDict.keys():
        newDict[uid] = {}
        newDict[uid] = newDict[uid].fromkeys(programs)
        for pid in newDict[uid].keys():
            newDict[uid][pid] = []

    return newDict


def writeBaseFile(method, CV, currentDict, fileType):
    print('Writing the base file...')
    path = 'data/' + str(CV) + 'CV'
    Path(path).mkdir(parents=True, exist_ok=True)
    
    f = open(path + '/Epi_' + method + '_' + fileType + '.base', 'w')
    
    print(path)

    unit = int(len(currentDict) * 0.01)
    cnt = 0
    for idx1, key1 in enumerate(currentDict):
        if cnt % unit == 0:
            print(cnt / unit, '%....')

        for idx2, key2 in enumerate(currentDict[key1]):
            if len(currentDict[key1][key2]) == 0:
                continue  # Skip the TV show if user's watching-count is equal to zero

            for value in currentDict[key1][key2]:
                if value != '|':
                    f.write(str(idx1 + 1) + '\t' + str(idx2 + 1) + '\t' + str(value) + '\n')

        cnt += 1

    f.close()


def BuildDictMatrix_ver2(method, CV, trainEPG, trainWL, programs2, users2):
    print('Building dictionary with considering TV watching interval...')
    print('Users: ' + str(len(users2)) + ', Programs: ' + str(len(programs2)))
    # PrefDict = defaultdict(lambda: {})

    PrefDict = buildDict(users2, programs2)
    TVwatchDict = buildDict(users2, programs2)
    WatchDict = buildDict(users2, programs2)

    print('Building matrix with considering TV watching interval...')
    PrefMatrix = pd.DataFrame(0.0, columns=programs2, index=users2)
    ConfMatrix = pd.DataFrame(1.0, columns=programs2, index=users2)

    if method in ['PM', 'PNM', 'Prop', 'Prop_P', 'Prop_PM', 'Prop_PN', 'Prop_B', 'Prop_New']:
        ConfMatrix = pd.DataFrame(0.0, columns=programs2, index=users2)

    print('>> ComputePropDictMatrix_ver2()')
    unit = int(len(trainEPG) * 0.01)
    cnt = 0
    for index, episode in trainEPG.iterrows():
        if cnt % unit == 0:
            print(cnt / unit, '%...')

        ComputePropDictMatrix_ver2(PrefDict, TVwatchDict, WatchDict, PrefMatrix, ConfMatrix, trainWL, episode, 0.5, 0.0)    # beta <- 0.0
        cnt += 1

    writeBaseFile(method, CV, PrefDict, 'competable')
    writeBaseFile(method, CV, TVwatchDict, 'wable_intv')
    writeBaseFile(method, CV, WatchDict, 'w_intv')

    print('Writing the df files...')
    path_matrix1 = 'data/' + str(CV) + 'CV/EpiPrefMatrix_' + method + '_competable.df'
    path_matrix2 = 'data/' + str(CV) + 'CV/EpiConfMatrix_' + method + '_competable.df'

    Path(path_matrix1).parent.mkdir(parents=True, exist_ok=True)
    Path(path_matrix2).parent.mkdir(parents=True, exist_ok=True)

    PrefMatrix.to_pickle(path_matrix1)
    ConfMatrix.to_pickle(path_matrix2)

    return PrefMatrix, ConfMatrix


# Episode에 대한 각 사용자의 watchable interval 및 그에 따른 estimated preference를 계산
def ComputePropDictMatrix_ver2(PrefDict, TVwatchDict, WatchDict, PrefMatrix, ConfMatrix, watchLog, episode, alpha, beta):
    pTime = (episode['endDate'] - episode['startDate']).seconds / 60
    wLogs = watchLog[(watchLog['EntranceTime'] < episode['endDate']) & (watchLog['LeavingTime'] > episode['startDate'])]

    watchTime = {}
    TVwatchTime = {}

    str_wrow = {}

    TVwatchStart = {}
    TVwatchEnd = {}

    for windex, wrow in wLogs.iterrows():
        idx = str(wrow['PanelID']) + '-' + str(wrow['MemberID'])
        TVsTime = wrow['EntranceTime']
        TVeTime = wrow['LeavingTime']

        if idx not in watchTime:
            watchTime[idx] = 0
            str_wrow[idx] = ','
        if idx not in TVwatchTime:
            TVwatchTime[idx] = 0

        if (wrow['TVshowID']==episode['program_title']) & (wrow['EntranceTime']>=episode['startDate']) & (wrow['LeavingTime']<=episode['endDate']):
            watchTime[idx] += (wrow['LeavingTime'] - wrow['EntranceTime']).seconds / 60

            # Build watchStart and watchEnd dictionaries
            str_wrow[idx] += (str(wrow['EntranceTime']) + ',' + str(wrow['LeavingTime']) + str(','))
            # print(str_wrow[idx])


        if episode['startDate'] > wrow['EntranceTime']:
            TVsTime = episode['startDate']
        if episode['endDate'] < wrow['LeavingTime']:
            TVeTime = episode['endDate']

        TVwatchTime[idx] += (TVeTime - TVsTime).seconds / 60   # Compute user's watchable interval for corresponding episode

        # Build TVwatchStart and TVwatchEnd dictionaries
        if idx not in TVwatchStart:
            TVwatchStart[idx] = TVsTime
        else:
            if TVwatchStart[idx] > TVsTime:
                TVwatchStart[idx] = TVsTime
        if idx not in TVwatchEnd:
            TVwatchEnd[idx] = TVeTime
        else:
            if TVwatchEnd[idx] < TVeTime:
                TVwatchEnd[idx] = TVeTime


    for key in TVwatchTime:
        mTVRatio = TVwatchTime[key] / pTime
        wRatio = watchTime[key] / TVwatchTime[key]

        if wRatio > 1.0:
            print('wRatio is larger than 1.0')

        if wRatio < beta:
            continue    # Skip the user whose wRatio for the corresponding episode is smaller than beta
        elif mTVRatio < alpha:
            continue

        PrefDict[key][episode['program_title']].append(wRatio)
        PrefDict[key][episode['program_title']].append('|')

        TVwatchDict[key][episode['program_title']].append(str(TVwatchStart[key]) + ',' + str(TVwatchEnd[key]))
        TVwatchDict[key][episode['program_title']].append('|')

        WatchDict[key][episode['program_title']].append(str_wrow[key])
        WatchDict[key][episode['program_title']].append('|')

        PrefMatrix[episode['program_title']][key] += wRatio
        ConfMatrix[episode['program_title']][key] += 1