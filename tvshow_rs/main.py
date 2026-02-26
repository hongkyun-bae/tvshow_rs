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
    parser.add_argument('--mode', type=int,default=-1, help='0 - Build Matrix, 1 - Preference Estimation, 2 - Evaluation')
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
    
    Score = 0

    ## read data
    print('ReadData')
    wl_6m_df, epg_df = ReadData.readData()
    wl_2m_df, wl_1m_df, epg2_df, epg1_df, programs2, users2, programs1, users1 = ReadData.Preprocessing(CV, wl_6m_df, epg_df, mode)

    if mode == 0:
        print('Mode' + str(mode) + ': BuildMatrix')

        start_time = time.time()
        PrefMatrix, ConfMatrix = BuildMatrix.BuildMatrix(method, CV, epg2_df, wl_2m_df, programs2, users2)
        print('PE time: {}'.format(time.time() - start_time))

        PrefMatrix = PrefMatrix.divide(ConfMatrix, axis='index')
        PrefMatrix = PrefMatrix.fillna(0.0)

        ConvertFormat.BuildMM(PrefMatrix, ConfMatrix, factor, CV, method, reg)


    elif mode == 1:
        print('Mode' + str(mode) + ': Episode-based estimation considering TV watching interval')

        start_time = time.time()
        PrefMatrix, ConfMatrix = BuildDict.BuildDictMatrix_ver2(method, CV, epg2_df, wl_2m_df, programs2, users2)
        print('Episode-based estimation time: {}'.format(time.time() - start_time))

        PrefMatrix = PrefMatrix.divide(ConfMatrix, axis='index')
        PrefMatrix = PrefMatrix.fillna(0.0)
        ConvertFormat.BuildMM(PrefMatrix, ConfMatrix, factor, CV, method, reg)
        print("Complete: BuildMM")    
    

    elif mode == 2:
        print ('Mode' + str(mode) + ': Evaluate')
        PrefMatrix, ConfMatrix = ReadData.readMatrix('ST', CV, D)
        
        predMatrix = 0
        if isConf == 0:
            method += 'woConf'
                        
        predMatrix = ReadData.readNeuralPredMatrix(PrefMatrix, users2, programs2, method, batch, factor, lr, iteR, CV)    # include BPR-MF predictions
           
        Checked_TestSet = wl_1m_df[wl_1m_df['Watched'] == 1]
        Unchecked_TestSet = wl_1m_df[wl_1m_df['Watched'] == 0]
        
        Score2 = 0
        ndcgs2 = 0
        MRR2 = 0
        Score = 0
        ndcgs = 0
        MRR = 0

        start_time = time.time()

        if wALS == 1 or method == 'PNM' or method in ['Prop', 'Prop_New']:
            time_factor_histogram = ReadData.readTimeFactorMatrix(CV)

            # For watched test set (pred)
            Score, ndcgs, MRR = ShowTime.Experiment_ST(epg_df, wl_2m_df, Checked_TestSet, PrefMatrix, predMatrix, time_factor_histogram, log, logname, data_type=1)
            if D != 1:
                # For non-watched test set (pred)
                Score2, ndcgs2, MRR2 = ShowTime.Experiment_ST(epg_df, wl_2m_df, Unchecked_TestSet, PrefMatrix, predMatrix, time_factor_histogram, log, logname, data_type=0)

        print('Recommendation time :{}'.format(time.time() - start_time))

        if D == 2:
            Evaluate.Evaluate(Score2, ndcgs2, MRR2, Score2, ndcgs2, MRR2, method, CV, reg, factor, D)
            print("Average of watchTime: " + str(np.average(excluded_watchTimes)))
        else:
            Evaluate.Evaluate(Score, ndcgs, MRR, Score2, ndcgs2, MRR2, method, CV, reg, factor, D)

    else:
        print ("Mode should be from 0 to 2.")
    #'''
