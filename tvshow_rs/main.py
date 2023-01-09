import numpy as np
import pandas as pd
import argparse
import time
import structures.BuildMatrix as BuildMatrix
import structures.BuildDict as BuildDict
import structures.ConvertFormat as ConvertFormat
import structures.ReadData as ReadData
import methods.Evaluate as Evaluate
import methods.PM as PM
import methods.Random as Random
import methods.Popular as Popular
import methods.RecTime as RecTime
import methods.ShowTime as ShowTime
from subprocess import call
from os import environ
from methods.PM import excluded_watchTimes


def parse_args():
    parser = argparse.ArgumentParser(description="Run Experiment.")
    parser.add_argument('--mode', type=int,default=-1, help='0 - Build Matrix, 1 - Matrix Factorization, 2 - Evaluate')
    parser.add_argument('--method', nargs='?', default='Prop', help='ST RT PM PNM Prop Prop_P Prop_PM Prop_N')
    parser.add_argument('--CV', type=int, default=1, help='from 1~3 CV')
    parser.add_argument('--reg', type=float, default=0.01, help = '0~1')
    parser.add_argument('--factor', type=int, default=50, help='factor for MF')
    parser.add_argument('--wALS', type=int, default=0, help='wALS or original method')
    parser.add_argument('--TF', type=int, default=0, help='timefactor')
    parser.add_argument('--D', type=int, default=0, help='0 all, 1 checked, 2 unchecked')
    parser.add_argument('--C', type=int, default=1, help='0, 1')
    parser.add_argument('--log', type=int, default=0, help='write log or not')
    parser.add_argument('--batch', type=int, default=256, help='batch')
    parser.add_argument('--lr', type=float, default=0.001, help='learning rate')
    parser.add_argument('--iter', type=int, default=20, help='iteration')
    parser.add_argument('--sample', type=int, default=0, help='size of sample')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    mode = args.mode
    method = args.method
    CV = args.CV
    factor = args.factor
    wALS = args.wALS
    TF = args.TF
    reg = args.reg
    log = args.log
    batch = args.batch
    lr = args.lr
    iteR = args.iter
    D = args.D
    isConf = args.C
    sample_size = args.sample
    #print (mode,method,CV,factor,wALS,reg,log)
    
    Score = 0
    # sample_size = 200

    ## read data
    print('ReadData')
    wl_6m_df, epg_df = ReadData.readData()

    if (mode != 0) & (mode != 4) & (mode != 5):
        PrefMatrix, ConfMatrix = ReadData.readMatrix(method, CV, D)    # For program-based matrix
        # PrefMatrix, ConfMatrix = ReadData.readMatrix_episode('Prop', CV)    # For episode-based matrix

        if sample_size == 0:
            wl_2m_df, wl_1m_df, epg2_df, epg1_df, programs2, users2, programs1, users1 = ReadData.Preprocessing(CV,
                                                                                                                wl_6m_df,
                                                                                                                epg_df, mode,
                                                                                                                PrefMatrix)
        else:
            wl_2m_df, epg2_df, programs2, sample_user_list = ReadData.Preprocessing_sample(CV, wl_6m_df, epg_df,
                                                                                           sample_size)
    else:
        if sample_size == 0:
            wl_2m_df, wl_1m_df, epg2_df, epg1_df, programs2, users2, programs1, users1 = ReadData.Preprocessing(CV,
                                                                                                                wl_6m_df,
                                                                                                                epg_df, mode)
        else:
            wl_2m_df, epg2_df, programs2, sample_user_list = ReadData.Preprocessing_sample(CV, wl_6m_df, epg_df,
                                                                                           sample_size)

    if mode == -2:
        PrefMatrix, ConfMatrix = ReadData.readMatrix(method, CV, D)
        # PrefMatrix_sp, ConfMatrix_sp = ReadData.readMatrix_sample(method, CV, D, sample_size)
        ConvertFormat.BuildMM(PrefMatrix, ConfMatrix, factor, CV, method, reg)
        # ConvertFormat.BuildMM_sample(PrefMatrix_sp, ConfMatrix_sp, factor, CV, method, reg, sample_size)
        # print("Complete: BuildMM_sample")

    elif mode == -1:
        if method != 'Prop':
            PrefMatrix, ConfMatrix  = ReadData.readMatrix(method, CV, D)
        ConvertFormat.BuildNeuralCFFormat(PrefMatrix, ConfMatrix, method, CV)

    elif mode == 0:
        print('Mode' + str(mode) + ': BuildMatrix')
        if isConf == 1:
            start_time = time.time()
            PrefMatrix, ConfMatrix = BuildMatrix.BuildMatrix(method, CV, epg2_df, wl_2m_df, programs2, users2)
            print('PE time: {}'.format(time.time() - start_time))

            PrefMatrix = PrefMatrix.divide(ConfMatrix, axis='index')
            PrefMatrix = PrefMatrix.fillna(0.0)

            ConvertFormat.BuildMM(PrefMatrix, ConfMatrix, factor, CV, method, reg)
        else:
            if method == 'Random' or method == 'Pop':
                PrefMatrix, ConfMatrix = ReadData.readMatrix('ST', CV, D)
            elif method != 'Prop':
                PrefMatrix, ConfMatrix  = ReadData.readMatrix(method, CV, D)
            ConfMatrix = pd.DataFrame(1.0, columns=programs2, index=users2)
            #method+='woConf'
            ConvertFormat.BuildMM(PrefMatrix, ConfMatrix, factor, CV, method, reg)
        
        if method == 'ST' and wALS == 0:
            ShowTime.BuildTimeFactorMatrix(wl_2m_df, epg2_df, method, CV)
        elif method == 'Prop' and wALS == 0:
            ConvertFormat.BuildNeuralCFFormat(PrefMatrix, ConfMatrix, factor, CV, method)
            
    elif mode == 1:
        print ('Matrix factorization')
        
        if isConf == 0:
            method += 'woConf'
        testpath = '../wALSResult/' + str(factor) + 'Fact_' + str(CV) + 'CV_Reg' + str(reg) + '/' + method

        if sample_size > 0:
            testpath += ('_test_' + str(sample_size))
        else:
            testpath += '_test'

        trainingpath = '../wALSResult/' + str(CV) + 'CV/' + method

        if sample_size > 0:
            trainingpath += ('_train_' + str(sample_size))
        else:
            trainingpath += '_train'

        graphchi = environ['GRAPHCHI_ROOT']
        callpath = graphchi+"/toolkits/collaborative_filtering/"
        #callpath = "${GRAPCHI_ROOT}"
        maxVal = 1 
        
        if wALS == 1:
            trainingpath += '.mm'
            testpath += '.mm'
            callpath += 'wals'
        else:
            trainingpath += '_PMF.mm'
            testpath += '_PMF.mm'
            callpath += 'pmf'
        
        if method == 'ST':
            maxVal = 10000
        elif method == 'RT':
            maxVal = 100
        #call(["echo",callpath])

        start_time = time.time()
        call([callpath, "--training=" + trainingpath, "--test=" + testpath, "--minval=0", "--maxval=" + str(maxVal),
              "--max_iter=200", "--lambda=" + str(reg), "--quiet=1", "--nshards=1", "--D=" + str(factor)])

        print('PP time: {}'.format(time.time() - start_time))
        
    elif mode == 2:
        print ('Mode' + str(mode) + ': Evaluate')
        if method == 'Random' or method == 'Pop':
            PrefMatrix, ConfMatrix = ReadData.readMatrix('ST', CV, D)
        # elif method != 'Prop':    # 221222: blocked for ShowTime
        #     PrefMatrix, ConfMatrix = ReadData.readMatrix(method, CV, D)
        
        predMatrix = 0
        if isConf == 0:
            method += 'woConf'
                        
        if wALS == 0 and method in ['Prop', 'Prop_New']:
            predMatrix = ReadData.readNeuralPredMatrix(PrefMatrix, users2, programs2, method, batch, factor, lr, iteR, CV)    # include BPR-MF predictions
            # predMatrix = ReadData.readNeuralPredMatrix_total(PrefMatrix, ConfMatrix, users2, programs2)  # include BPR-MF predictions
        elif not (method == 'Random' or method == 'Pop' or D == 1):    # D==1: using checked test set
            predMatrix = ReadData.readPredMatrix(PrefMatrix, users2, programs2, method, factor, CV, wALS, reg)
           
        #print(predMatrix.head())
        #print(predMatrix[predMatrix.notnull()])
        #print (predMatrix.head())
        Checked_TestSet = wl_1m_df[wl_1m_df['Watched'] == 1]
        Unchecked_TestSet = wl_1m_df[wl_1m_df['Watched'] == 0]


        logname = 'log.txt'
        if log == 1:
            logname = '../wALSResult/' + str(factor) + 'Fact_' + str(CV) + 'CV_Reg' + str(reg) + '/' + method + '.txt'
        
        Score2 = 0
        ndcgs2 = 0
        MRR2 = 0
        Score = 0
        ndcgs = 0
        MRR = 0

        start_time = time.time()

        if wALS == 1 or method == 'PNM' or method in ['Prop', 'Prop_New']:
            if TF != 0:
                time_factor_histogram = ReadData.readTimeFactorMatrix(CV)
                # For watched test set (pred)
                Score, ndcgs, MRR = ShowTime.Experiment_ST(epg_df, wl_2m_df, Checked_TestSet, PrefMatrix, predMatrix, time_factor_histogram, log, logname, data_type=1)
                #print(predMatrix.head())
                if D != 1:
                    # For non-watched test set (pred)
                    Score2, ndcgs2, MRR2 = ShowTime.Experiment_ST(epg_df, wl_2m_df, Unchecked_TestSet, PrefMatrix, predMatrix, time_factor_histogram, log, logname, data_type=0)
                print('Read tf_histogram')
            else:
                #'''
                if D == 1:
                    if method == 'Pop':
                        Score, ndcgs, MRR = Popular.PE_Experiment(epg_df, wl_2m_df, Checked_TestSet, PrefMatrix, ConfMatrix, 5)
                    elif method == 'Random':
                        Score, ndcgs, MRR = Random.PE_Experiment(epg_df, wl_2m_df, Checked_TestSet, PrefMatrix, ConfMatrix, 5)
                    else:
                        Score, ndcgs, MRR = PM.PE_Experiment(epg_df, wl_2m_df, Checked_TestSet, PrefMatrix, ConfMatrix, 5)
                elif D == 2:
                    Score2, ndcgs2, MRR2 = PM.Experiment(epg_df, wl_2m_df, Unchecked_TestSet, PrefMatrix, predMatrix, log, logname, data_type=0)    # for non-watched test set
                else:
                #'''
                    #Score,ndcgs,MRR = PM.PE_Experiment(epg_df,wl_2m_df,Checked_TestSet,PrefMatrix,ConfMatrix,5)
                    # Score, ndcgs, MRR = PM.Experiment(epg_df, wl_2m_df, Checked_TestSet, PrefMatrix, PrefMatrix, log, logname, data_type=1)    # for watched test set

                    Score, ndcgs, MRR = PM.Experiment(epg_df, wl_2m_df, Checked_TestSet, PrefMatrix, predMatrix, log, logname, data_type=1)  # for watched test set (pred)
                    Score2, ndcgs2, MRR2 = PM.Experiment(epg_df, wl_2m_df, Unchecked_TestSet, PrefMatrix, predMatrix, log, logname, data_type=0)    # for non-watched test set
        elif method=='ST':
            time_factor_histogram = ReadData.readTimeFactorMatrix(CV)
            Score,ndcgs,MRR = ShowTime.Experiment_ST(epg_df,wl_2m_df,Checked_TestSet,PrefMatrix,PrefMatrix,time_factor_histogram,log,logname,data_type=1)
            if D!=1:
                Score2,ndcgs2,MRR2 = ShowTime.Experiment_ST(epg_df,wl_2m_df,Unchecked_TestSet,PrefMatrix,predMatrix,time_factor_histogram,log,logname,data_type=0)
        elif method=='RT':
            PrefMatrix,ConfMatrix  = ReadData.readMatrix('Prop',CV,D)
            RecTensor,PredRecTensor = RecTime.BuildTensor(epg_df,wl_2m_df,PrefMatrix,2)
            Score,ndcgs,MRR = RecTime.Experiment_RT(epg_df,wl_2m_df,Checked_TestSet,PrefMatrix,RecTensor,log,logname)    
            if D!=1:
                Score2,ndcgs2,MRR2 = RecTime.Experiment_RT(epg_df,wl_2m_df,Unchecked_TestSet,PrefMatrix,PredRecTensor,log,logname)    
        elif method=='Random':
            Score,ndcgs,MRR = Random.Experiment(epg_df,wl_2m_df,Checked_TestSet,PrefMatrix,PrefMatrix,log,logname)
            if D!=1:
                Score2,ndcgs2,MRR2 = Random.Experiment(epg_df,wl_2m_df,Unchecked_TestSet,PrefMatrix,PrefMatrix,log,logname)
        elif method=="Pop":
            Score,ndcgs,MRR = Popular.Experiment(epg_df,wl_2m_df,Checked_TestSet,PrefMatrix,PrefMatrix,log,logname)
            Score2,ndcgs2,MRR2 = Popular.Experiment(epg_df,wl_2m_df,Unchecked_TestSet,PrefMatrix,PrefMatrix,log,logname)
            #Score2 = {}
            #ndcgs2= {}
            #MRR2 = {}
        #elif method =="PNM":
            #Score2,ndcgs2,MRR2 = 
            
            #Score2,ndcgs2,MRR2 = PM.Experiment(epg_df,wl_2m_df,Unchecked_TestSet,PrefMatrix,PrefMatrix,log,logname)
        print('Recommendation time :{}'.format(time.time() - start_time))

        if D == 2:
            Evaluate.Evaluate(Score2, ndcgs2, MRR2, Score2, ndcgs2, MRR2, method, CV, reg, factor, D)
            print("Average of watchTime: " + str(np.average(excluded_watchTimes)))
        else:
            Evaluate.Evaluate(Score, ndcgs, MRR, Score2, ndcgs2, MRR2, method, CV, reg, factor, D)

    elif mode == 3:
        print('Performance test')
        print('Size of sample: ' + str(sample_size))

        start_time = time.time()
        PrefMatrix, ConfMatrix = BuildMatrix.BuildMatrix_sample(method, CV, epg2_df, wl_2m_df, programs2,
                                                                  sample_user_list, sample_size)
        print('PE time: {}'.format(time.time() - start_time))

        PrefMatrix = PrefMatrix.divide(ConfMatrix, axis='index')
        PrefMatrix = PrefMatrix.fillna(0.0)

        ConvertFormat.BuildMM_sample(PrefMatrix, ConfMatrix, factor, CV, method, reg, sample_size)

        print("Complete: BuildMM_sample")

        # ConvertFormat.BuildMM(PrefMatrix, ConfMatrix, factor, CV, method, reg)

    elif mode == 4:
        print('Mode' + str(mode) + ': Episode-based estimation')

        start_time = time.time()
        PrefDict, PrefMatrix, ConfMatrix = BuildDict.BuildDictMatrix(method, CV, epg2_df, wl_2m_df, programs2, users2)
        print('Episode-based estimation time: {}'.format(time.time() - start_time))

        PrefMatrix = PrefMatrix.divide(ConfMatrix, axis='index')
        PrefMatrix = PrefMatrix.fillna(0.0)
        ConvertFormat.BuildMM(PrefMatrix, ConfMatrix, factor, CV, method, reg)
        print("Complete: BuildMM")

    elif mode == 5:
        print('Mode' + str(mode) + ': Episode-based estimation considering TV watching interval')

        start_time = time.time()
        PrefMatrix, ConfMatrix = BuildDict.BuildDictMatrix_ver2(method, CV, epg2_df, wl_2m_df, programs2, users2)
        print('Episode-based estimation time: {}'.format(time.time() - start_time))

        PrefMatrix = PrefMatrix.divide(ConfMatrix, axis='index')
        PrefMatrix = PrefMatrix.fillna(0.0)
        ConvertFormat.BuildMM(PrefMatrix, ConfMatrix, factor, CV, method, reg)
        print("Complete: BuildMM")

    else:
        print ("Mode should be from 0 to 5.")
    #'''
