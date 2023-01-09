import numpy as np
import pandas as pd
import random
from datetime import datetime,timedelta,time 

def readData():
    wl_6m_df = pd.read_pickle('Z:\\hongkyun\\TVshow\\Data\\wl_6m_df.df')
    epg_df = pd.read_pickle('Z:\\hongkyun\\TVshow\\Data\\epg_df.df')
    return wl_6m_df,epg_df

def readTimeFactorMatrix(CV):
    return pd.read_pickle('Z:\\hongkyun\\TVshow\\Data\\time_factor_histogram.df')


def readNeuralPredMatrix(PrefMatrix, users2, programs2, method, batch, factor, lr, iter, CV):
    #path = '../NeuralResult/'+str(CV)+'CV_batch'+str(batch)+'_factor'+str(factor)+'_lr'+lr+'_iter'+str(iter)+'/Prop_test.mm.predict'
    # path = '../NeuralCF/Prop_New_test.mm.predict'
    # path = '../origin/' + str(CV) +'CV/Epi_Prop.predict'
    # path = '../origin/' + str(CV) + 'CV/Epi_Prop_x3_allneg.predict'
    # path = '../origin/' + str(CV) + 'CV/LR0.001/Reg0.00125/Epi_Prop_x1_allneg_onlypos0.5.predict'
    # path = '../origin/' + str(CV) +'CV/Epi_Prop_competable_alpha0.5_x50_all_wgt(rev).predict'
    # path = 'E:\\hongkyun\\TVshow\\wIntv-based\\MLP\\Epi_Prop_competable_alpha0.1_x3.0_all_reg0.00125_lr0.001_128_512.predict'
    path = 'Z:\\hongkyun\\TVshow\\wIntv-based\\Epi_Prop_competable_alpha0.05_x50_all.predict'
    # path = 'C:\\Users\\deadpool\\Documents\\origin\\TVshow\\Prop_train_x10.predict'

    print('Reading the episode-based predict file...')
    print(path)

    #file = method+'.mm.predict'
    predictMatrix = open(path, 'r')
    builtMatrix = pd.DataFrame(0.0, columns=programs2, index=users2)
    
    users = {}
    items = {}
    
    for index, user in enumerate(PrefMatrix.index):
        users[index+1] = user
    for index, item in enumerate(PrefMatrix.columns):
        items[index+1] = item
            
    for line in predictMatrix:
        user_idx, item_idx, val = line.split()
        # print(user_idx, item_idx, float(val))
        builtMatrix.set_value(users[int(user_idx)], items[int(item_idx)], float(val))

    return builtMatrix


def readPredMatrix(PrefMatrix, users2, programs2, method, factor, CV, wALS, reg=0):
    path = '../wALSResult/'+str(factor)+'Fact_'+str(CV)+'CV'
    # path = 'E:\\hongkyun\\TVshow\\Naive\\ProgPref_'

    if reg!=0:
        path+='_Reg'+str(reg)+'/'
    if wALS ==0 and method=='PNM':
        path +=method+'_test_PMF.mm.predict'
    else:
        path += method + '_PE_test.mm.predict'

    print("PredMatrix: " + path)

    predictMatrix = open(path, 'r')
    builtMatrix = pd.DataFrame(0.0, columns=programs2, index=users2)
    
    users = {}
    items = {}
    for index, user in enumerate(PrefMatrix.index):
        users[index+1] = user
    for index, item in enumerate(PrefMatrix.columns):
        items[index+1] = item
        
    for i in range(3):
        predictMatrix.readline() 
        
    for line in predictMatrix:
        user_idx, item_idx, val = line.split()
        builtMatrix.set_value(users[int(user_idx)], items[int(item_idx)], float(val))

    return builtMatrix


def readNeuralPredMatrix_total(PrefMatrix, ConfMatrix, users2, programs2):
    path = 'E:\\hongkyun\\TVshow\\wIntv-based\\Epi_Prop_competable_alpha0.1_x50_all.predict'

    print('Reading the episode-based predict file totally...')
    print(path)

    predictMatrix = open(path, 'r')
    builtMatrix = pd.DataFrame(0.0, columns=programs2, index=users2)

    users = {}
    items = {}

    for index, user in enumerate(PrefMatrix.index):
        users[index + 1] = user
    for index, item in enumerate(PrefMatrix.columns):
        items[index + 1] = item

    for line in predictMatrix:
        user_idx, item_idx, val = line.split()

        if ConfMatrix[items[int(item_idx)]][users[int(user_idx)]] == 0:
            builtMatrix.set_value(users[int(user_idx)], items[int(item_idx)], float(PrefMatrix[items[int(item_idx)]][users[int(user_idx)]]))
            # builtMatrix.set_value(users[int(user_idx)], items[int(item_idx)], float(val))
        else:
            builtMatrix.set_value(users[int(user_idx)], items[int(item_idx)], float(val))
            # builtMatrix.set_value(users[int(user_idx)], items[int(item_idx)],
            #                       float(PrefMatrix[items[int(item_idx)]][users[int(user_idx)]]))

    return builtMatrix


def readMatrix(method, CV, D):
    # prefPath = 'E:\\hongkyun\\TVshow\\Naive\\ProgPrefMatrix_' + method + '.df'
    # prefPath = 'Z:\\hongkyun\\TVshow\\Naive\\ProgPrefMatrix_Prop.df'
    prefPath = '../wALSResult/'+str(CV)+'CV/PrefMatrix_' + method + '_PE.df'
    PrefMatrix = pd.read_pickle(prefPath)
    print('PrefMatrix: ' + prefPath)

    # confPath = 'E:\\hongkyun\\TVshow\\Naive\\ProgConfMatrix_Prop' + '.df'
    # confPath = 'Z:\\hongkyun\\TVshow\\Naive\\ProgConfMatrix_Prop.df'
    confPath = '../wALSResult/'+str(CV)+'CV/ConfMatrix_' + method + '_PE.df'
    ConfMatrix = pd.read_pickle(confPath)
    print('ConffMatrix: ' + confPath)

    if method in ['PNM'] or method.startswith('Prop'):
        PrefMatrix = PrefMatrix.divide(ConfMatrix, axis='index')
        PrefMatrix = PrefMatrix.fillna(0.0)

    return PrefMatrix, ConfMatrix


def readMatrix_sample(method, CV, D, sample_size):
    prefPath = '../wALSResult/' + str(CV) + 'CV/PrefMatrix_' + method + '_' + str(sample_size) + '.df'
    PrefMatrix = pd.read_pickle(prefPath)

    ConfMatrix = 0

    if D == 1:
        confPath = '../wALSResult/' + str(CV) + 'CV/ConfMatrix_Prop' + '_' + str(sample_size) + '.df'
        ConfMatrix = pd.read_pickle(confPath)
    # else:
    elif method in ['PNM', 'Prop', 'PM', 'Prop_PM', 'Prop_PN', 'Prop_P', 'Prop_New']:
        confPath = '../wALSResult/' + str(CV) + 'CV/ConfMatrix_' + method + '.df'
        ConfMatrix = pd.read_pickle(confPath)
    else:
        confPath = '../wALSResult/' + str(CV) + 'CV/ConfMatrix_Prop' + '.df'
        ConfMatrix = pd.read_pickle(confPath)

    if method in ['PNM'] or method.startswith('Prop'):
        PrefMatrix = PrefMatrix.divide(ConfMatrix, axis='index')
        PrefMatrix = PrefMatrix.fillna(0.0)

    return PrefMatrix, ConfMatrix


def readMatrix_episode(method, CV):
    prefPath = 'Z:\\hongkyun\\TVshow\\EpiPrefMatrix_' + method + '_competable.df'
    PrefMatrix = pd.read_pickle(prefPath)
    confPath = 'Z:\\hongkyun\\TVshow\\EpiConfMatrix_' + method + '_competable.df'
    ConfMatrix = pd.read_pickle(confPath)

    if method in ['PNM'] or method.startswith('Prop'):
        PrefMatrix = PrefMatrix.divide(ConfMatrix, axis='index')
        PrefMatrix = PrefMatrix.fillna(0.0)

    return PrefMatrix, ConfMatrix


def Preprocessing(CV, wl_6m_df, epg_df, mode, PrefMatrix=None):
    shift_time = timedelta(days=7)
    dec_time = timedelta(days=6)
    
    TestEndDate2s = datetime.strptime('2011-09-01','%Y-%m-%d')
    TestEndDate2e = TestEndDate2s+dec_time
    TrainStartDate = datetime.strptime('2011-07','%Y-%m')
    TestEndDate = datetime.strptime('2011-09','%Y-%m')
    
    CV -= 1

    for i in range(CV):
        TrainStartDate = TrainStartDate - shift_time
        TestEndDate = TestEndDate - shift_time
        TestEndDate2s = TestEndDate2s - shift_time
        TestEndDate2e = TestEndDate2e - shift_time

    wl_2m_df = wl_6m_df[(wl_6m_df['EntranceTime'] >= TrainStartDate) & (wl_6m_df['EntranceTime'] < TestEndDate)]    # Watching log of training set
    wl_1m_df = wl_6m_df[(wl_6m_df['EntranceTime'] >= TestEndDate2s) & (wl_6m_df['EntranceTime'] <= TestEndDate2e)]    # Watching log of test set

    wl_1m_df['Watched'] = 0
    epg2_df = epg_df[(epg_df['startDate'] >= TrainStartDate) & (epg_df['startDate'] < TestEndDate)]    # Episodes of training set
    epg1_df = epg_df[(epg_df['startDate']>=TestEndDate2s) & (epg_df['startDate'] <= TestEndDate2e)]    # Episodes of test set
    
    programs2 = list(set(epg2_df['program_title']))    # TV shows of training set
    programs1 = list(set(epg1_df['program_title']))    # TV shows of test set
    
    users2 = []
    panels2 = list(set(wl_2m_df['PanelID']))

    for panel in panels2:
        members = list(set(wl_2m_df[wl_2m_df['PanelID'] == panel]['MemberID']))
        for member in members:
            users2.append(str(panel)+'-'+str(member))    # Users of training set
        
    users1 = []
    panels1 = list(set(wl_1m_df['PanelID']))

    for panel in panels1:
        members = list(set(wl_1m_df[wl_1m_df['PanelID'] == panel]['MemberID']))
        for member in members:
            users1.append(str(panel)+'-'+str(member))    # Users of test set

    # if PrefMatrix != None:    # If mode is not 0 nor 4    # Why error?...
        # for index, row in wl_1m_df.iterrows():
        #     try:
        #         if PrefMatrix[row['TVshowID']][str(row['PanelID']) + '-' + str(row['MemberID'])] > 0:
        #             wl_1m_df.set_value(index, 'Watched', 1)
        #     except:
        #         wl_1m_df.set_value(index, 'Watched', -1)
        #         continue

    if (mode != 0) & (mode != 4) & (mode != 5):
        for index, row in wl_1m_df.iterrows():
            try:
                if PrefMatrix[row['TVshowID']][str(row['PanelID']) + '-' + str(row['MemberID'])] > 0:
                    # Assigns the value of 1 to TV show selected by the corresponding user
                    wl_1m_df.set_value(index, 'Watched', 1)
            except:
                # If the corresponding TV show has been newly inserted within wl_1m, then except it
                wl_1m_df.set_value(index, 'Watched', -1)
                continue

    return wl_2m_df, wl_1m_df, epg2_df, epg1_df, programs2, users2, programs1, users1


# Preprocessing for randomly selected users
def Preprocessing_sample(CV, wl_6m_df, epg_df, sample_size):
    print('Start preprocessing for sampling')

    shift_time = timedelta(days=7)

    TrainStartDate = datetime.strptime('2011-07', '%Y-%m')
    TestEndDate = datetime.strptime('2011-09', '%Y-%m')

    CV -= 1

    for i in range(CV):
        TrainStartDate = TrainStartDate - shift_time
        TestEndDate = TestEndDate - shift_time

    wl_2m_df = wl_6m_df[(wl_6m_df['EntranceTime'] >= TrainStartDate) & (wl_6m_df['EntranceTime'] < TestEndDate)]

    epg2_df = epg_df[(epg_df['startDate'] >= TrainStartDate) & (epg_df['startDate'] < TestEndDate)]
    programs2 = list(set(epg2_df['program_title']))

    users2 = []
    panels2 = list(set(wl_2m_df['PanelID']))
    user_cnt = 0
    for panel in panels2:
        members = list(set(wl_2m_df[wl_2m_df['PanelID'] == panel]['MemberID']))
        for member in members:
            users2.append(str(panel) + '-' + str(member))
            user_cnt += 1

    print('Total users: ' + str(user_cnt))


    # Select user ids randomly
    rd_uid_list = []
    if sample_size < user_cnt:
        rd_uid_list = random.sample(range(user_cnt), sample_size)
    else:
        rd_uid_list = random.sample(range(user_cnt), user_cnt-(user_cnt%1000))

    sample_user_list = []

    for rd_uid in rd_uid_list:
        sample_user_list.append(users2[rd_uid])

    wl_2m_df_list = []

    sample_cnt = 0
    for sample_user in sample_user_list:
        keywords = sample_user.split('-')
        panel_id = int(keywords[0])
        member_id = int(keywords[1])

        wl_2m_df_list.append(wl_2m_df[(wl_2m_df['PanelID'] == panel_id) & (wl_2m_df['MemberID'] == member_id)])
        sample_cnt += 1

    print('Value of sample_cnt: ' + str(sample_cnt))
    print('Size of sample_user_list: ' + str(np.size(sample_user_list)))

    merged_wl_2m_df = pd.concat(wl_2m_df_list)


    # In the case that sample_size is larger than user_cnt
    if sample_size > user_cnt:
        print('Case: Size of sample is larger than total number of users.')

        original_wl_2m_df = merged_wl_2m_df.copy()
        cp_wl_2m_df_list = [merged_wl_2m_df]
        bound_user_cnt = user_cnt - (user_cnt % 1000)
        num_wl_2m_df = int((sample_size / bound_user_cnt) - 1)

        # unit = int(len(merged_wl_2m_df) * 0.01)

        for i in range(num_wl_2m_df):
            print('Expansion: ' + str(i + 1))

            cp_wl_2m_df = original_wl_2m_df.copy()
            cp_idx = 0

            for idx, row in cp_wl_2m_df.iterrows():
                # if cp_idx % unit == 0:
                #     print(str(cp_idx/unit) + '%...')

                current_panel_id = row['PanelID']
                new_panel_id = current_panel_id + (1000000*(i+1))

                cp_wl_2m_df.at[idx, 'PanelID'] = new_panel_id
                cp_idx += 1

            cp_wl_2m_df_list.append(cp_wl_2m_df)

        merged_wl_2m_df = pd.concat(cp_wl_2m_df_list)

        m_path = '../wALSResult/1CV/Merged_wl_2m_df_' + str(sample_size) + '.df'
        merged_wl_2m_df.to_pickle(m_path)
        print('Writing complete: Merged_wl_2m_df_' + str(sample_size) + '.df')

        sample_user_list = []
        sample_panel_list = list(set(merged_wl_2m_df['PanelID']))
        expanded_user_cnt = 0

        for s_panel in sample_panel_list:
            sample_member_list = list(set(merged_wl_2m_df[merged_wl_2m_df['PanelID'] == s_panel]['MemberID']))
            for s_member in sample_member_list:
                sample_user_list.append(str(s_panel) + '-' + str(s_member))
                expanded_user_cnt += 1

        print('Total users after expansion: ' + str(expanded_user_cnt))
    else:
        m_path = '../wALSResult/1CV/Merged_wl_2m_df' + '_' + str(sample_size) + '.df'
        merged_wl_2m_df.to_pickle(m_path)
        print('Writing complete.')


    return merged_wl_2m_df, epg2_df, programs2, sample_user_list