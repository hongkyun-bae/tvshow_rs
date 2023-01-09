import numpy as np
import pandas as pd
import structures.ReadData as ReadData
from tqdm import tqdm

CV = 1
D = 0

wl_6m_df,epg_df = ReadData.readData()
PrefMatrix,ConfMatrix = ReadData.readMatrix('Prop',CV,D)

wl_2m_df,wl_1m_df,epg2_df,epg1_df,programs2,users2,programs1,users1 = ReadData.Preprocessing(CV,wl_6m_df,epg_df,PrefMatrix)

ST_PrefMatrix,ST_ConfMatrix = ReadData.readMatrix('ST',CV,D)

print(len(epg2_df))
print(epg2_df.head())

'''
print(ST_PrefMatrix.head())
print(ST_PrefMatrix.shape)
sum_arr = (ST_PrefMatrix != 0).astype(int).sum()
print(sum_arr)
print(sum(sum_arr))
print(sum((ST_PrefMatrix != 0).astype(int).sum()))

print(sum(ST_PrefMatrix.sum()))

broad_time = 0
for index,row in epg2_df.iterrows():
    broad_time += (row['endDate'] - row['startDate']).seconds/60

print('broad_time:',broad_time)

matrix = []
cnt = 0
for index,row in tqdm(epg2_df.iterrows()):
    wLogs = wl_2m_df[(wl_2m_df['TVshowID'] == row['program_title']) \
           & (wl_2m_df['EntranceTime'] < row['endDate']) \
           & (wl_2m_df['LeavingTime'] > row['startDate'])]
   
    user_dict = {}
    for user in users2:
        user_dict[user] = 0

    for windex,wrow in wLogs.iterrows():
        idx = str(wrow['PanelID'])+'-'+str(wrow['MemberID'])
        if idx not in user_dict:
            print(idx)
        else:
            user_dict[idx] = 1
            cnt+=1

print('cnt:{}'.format(cnt))
    #print('user dict len:',len(user_dict.values()))    
    #matrix.append(list(user_dict.values()))
    #matrix.append(user_dict.values())


#matrix = np.array(matrix)

#print(matrix.shape)

#cnt_non_zero = 0
#for row in matrix:
#    for val in row:
#        if val !=0:
#            cnt_non_zero+=1
            

#print(matrix)
'''
