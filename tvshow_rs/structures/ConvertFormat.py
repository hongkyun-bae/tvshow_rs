# build MM Format

import pandas as pd
import numpy as np
from pathlib import Path

def BuildPredMatrix(predictMatrix,PrefMatrix):
    predictMatrix.seek(0)
    builtMatrix = pd.DataFrame(0.0,columns = programs2,index=users2)
    
    users = {}
    items = {}
    for index,user in enumerate(PrefMatrix.index):
        users[index+1] = user
    for index,item in enumerate(PrefMatrix.columns):
        items[index+1] = item
    for i in range(3):
        print(predictMatrix.readline()) 
    for line in predictMatrix:
        user_idx,item_idx,val = line.split()
        builtMatrix.set_value(users[int(user_idx)],items[int(item_idx)],float(val))
    return builtMatrix


def BuildMM(PrefMatrix, ConfMatrix, factor, CV, method, reg):
    prefmatrix = PrefMatrix.values
    confmatrix = ConfMatrix.values
    m, n = prefmatrix.shape
    # path = '../wALSResult/' + str(CV) + 'CV/' + method
    # path2 = '../wALSResult/%dFact_%dCV_Reg%.2f/%s_test.mm' % (factor, CV, reg, method)

    path = 'data/' + str(CV) + 'CV'
    Path(path).mkdir(parents=True, exist_ok=True)

    # path2 = '../origin/' + str(CV) + 'CV/EpiPref_Prop_test.mm'

    # path = '../origin/' + str(CV) + 'CV/ProgPref_' + method + '_competable'
    # path2 = '../origin/' + str(CV) + 'CV/ProgPref_Prop_competable_test.mm'

    f = open(path + '/EpiPref_' + method + '_train.mm', 'w')
    f2 = open(path + '/EpiPref_' + method + '_test.mm', 'w')

    f.write('%%MatrixMarket matrix coordinate real general\n')
    f2.write('%%MatrixMarket matrix coordinate real general\n')

    f.write(str(m) + ' ' + str(n) + ' ' + str(m*n) + '\n')
    f2.write(str(m) + ' ' + str(n) + ' ' + str(m*n) + '\n')
    print(m,n)

    cnt = 0
    unit = int(len(prefmatrix) * 0.01)
    for index, arr in enumerate(prefmatrix):
        if cnt%unit == 0:
            print(cnt/unit, '%....')
        for index2, col in enumerate(arr):
            f.write(str(index+1)+' '+str(index2+1)+' '+str(confmatrix[index][index2])+' '+str(col)+'\n')
            f2.write(str(index+1)+' '+str(index2+1)+' '+str(1)+'\n')
        cnt+=1
    #os.system('sh Movefile.sh')
    f.close()
    f2.close()


def BuildMM_sample(PrefMatrix, ConfMatrix, factor, CV, method, reg, sample_size):
    prefmatrix = PrefMatrix.values
    confmatrix = ConfMatrix.values
    m, n = prefmatrix.shape

    path = '../wALSResult/' + str(CV) + 'CV/' + method

    path2 = '../wALSResult/' + str(factor) + 'Fact_' + str(CV) + 'CV_Reg' + str(reg) + '/' + method + '_test_' \
            + str(sample_size) + '.mm'
    # path2 = '../wALSResult/%dFact_%dCV_Reg%.2f/%s_test_' + str(sample_size) + '.mm' % (factor, CV, reg, method)

    f = open(path+'_train_' + str(sample_size) + '.mm', 'w')
    f2 = open(path2, 'w')

    f.write('%%MatrixMarket matrix coordinate real general\n')
    f2.write('%%MatrixMarket matrix coordinate real general\n')

    f.write(str(m) + ' ' + str(n) + ' ' + str(m*n) + '\n')
    f2.write(str(m) + ' ' + str(n) + ' ' + str(m*n) + '\n')
    print(m, n)

    cnt = 0
    unit = int(len(prefmatrix) * 0.01)
    for index, arr in enumerate(prefmatrix):
        if cnt%unit == 0:
            print(cnt/unit, '%....')
        for index2, col in enumerate(arr):
            #if index==2000:
                #print (index,index2)
            f.write(str(index+1)+' '+str(index2+1)+' '+str(confmatrix[index][index2])+' '+str(col)+'\n')
            f2.write(str(index+1)+' '+str(index2+1)+' '+str(1)+'\n')
        cnt+=1
    #os.system('sh Movefile.sh')
    f.close()
    f2.close()


def BuildNeuralCFFormat(PrefMatrix,ConfMatrix,method,CV):
    prefmatrix = PrefMatrix.values
    confmatrix = ConfMatrix.values
    m,n = prefmatrix.shape
                        
    path = '../NeuralResult/'+str(CV)+'CV/'+method
                        
    f = open(path+'.train.rating','w')
    f2 = open(path+'.test.rating','w')
    
    cnt=0
    unit = int(len(prefmatrix)*0.01)
                        
    for index,arr in enumerate(prefmatrix):
        if cnt%unit==0:
            print (cnt/unit,'%....')
        for index2,col in enumerate(arr):
            f.write(str(index+1)+' '+str(index2+1)+' '+str(col)+' '+str(confmatrix[index][index2])+'\n')
            f2.write(str(index+1)+' '+str(index2+1)+' '+str(1)+'\n')
        cnt+=1
    f.close()
    f2.close()
