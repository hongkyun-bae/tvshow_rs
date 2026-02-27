import numpy as np
from pathlib import Path

def Recall(Score,result):
    
    print ('===Recall===')
    result.write('===Recall===\n')

    result.write('Top1:'+str(Score['TN1']/(Score['TN1']+Score['FN1']))+'\n')
    result.write('Top3:'+str(Score['TN3']/(Score['TN3']+Score['FN3']))+'\n')
    result.write('Top5:'+str(Score['TN5']/(Score['TN5']+Score['FN5']))+'\n')
    result.write('Top10:' + str(Score['TN10'] / (Score['TN10'] + Score['FN10'])) + '\n')
    result.write('Top20:' + str(Score['TN20'] / (Score['TN20'] + Score['FN20'])) + '\n')
    
    print('Top1:'+str(Score['TN1']/(Score['TN1']+Score['FN1'])))
    print('Top3:'+str(Score['TN3']/(Score['TN3']+Score['FN3'])))
    print('Top5:'+str(Score['TN5']/(Score['TN5']+Score['FN5'])))
    print('Top10:' + str(Score['TN10'] / (Score['TN10'] + Score['FN10'])))
    print('Top20:' + str(Score['TN20'] / (Score['TN20'] + Score['FN20'])))

def Precision(Score,result):
    
    print('===Precision===')
    result.write('===Precision===\n')

    result.write('Top1:'+str(Score['TN1']/(Score['TN1']+Score['FN1']))+'\n')
    result.write('Top3:'+str((Score['TN3']/(Score['TN3']+Score['FN3']))*1/3)+'\n')
    result.write('Top5:'+str((Score['TN5']/(Score['TN5']+Score['FN5']))*1/5)+'\n')
    result.write('Top10:' + str((Score['TN10'] / (Score['TN10'] + Score['FN10'])) * 1 / 10) + '\n')
    result.write('Top20:' + str((Score['TN20'] / (Score['TN20'] + Score['FN20'])) * 1 / 20) + '\n')
    
    print('Top1:'+str((Score['TN1']/(Score['TN1']+Score['FN1']))))
    print('Top3:'+str((Score['TN3']/(Score['TN3']+Score['FN3']))*1/3))
    print('Top5:'+str((Score['TN5']/(Score['TN5']+Score['FN5']))*1/5))
    print('Top10:' + str((Score['TN10'] / (Score['TN10'] + Score['FN10'])) * 1 / 10))
    print('Top20:' + str((Score['TN20'] / (Score['TN20'] + Score['FN20'])) * 1 / 20))
    
def ndcg(Score,ndcgs,result):
    result.write('===NDCG===\n')
    print('===NDCG===')
    result.write('Top1:'+str(Score['TN1']/(Score['TN1']+Score['FN1']))+'\n')
    result.write('Top3:'+str(np.array(ndcgs['TN3']).mean())+'\n')
    result.write('Top5:'+str(np.array(ndcgs['TN5']).mean())+'\n')
    result.write('Top10:' + str(np.array(ndcgs['TN10']).mean()) + '\n')
    result.write('Top20:' + str(np.array(ndcgs['TN20']).mean()) + '\n')
    print('Top1:'+str(Score['TN1']/(Score['TN1']+Score['FN1'])))
    print('Top3:'+str(np.array(ndcgs['TN3']).mean()))
    print('Top5:'+str(np.array(ndcgs['TN5']).mean()))
    print('Top10:' + str(np.array(ndcgs['TN10']).mean()))
    print('Top20:' + str(np.array(ndcgs['TN20']).mean()))

def mrr(MRR,result):
    result.write('===MRR===\n')
    result.write(str(np.array(MRR).mean())+'\n')
    print('===MRR===')
    print(str(np.array(MRR).mean()))
    
def Evaluate(Score,ndcgs,MRR,Score2,ndcgs2,MRR2,method,CV,reg,factor,D):
    path = 'result/' + str(CV) + 'CV'
    Path(path).mkdir(parents=True, exist_ok=True)

    result = open(path + '/sample_result.txt', 'w')

    if D == 0:
        result.write("===Total===\n")
        print('===Total===')
        tScore = {'TN1':Score['TN1']+Score2['TN1'],'TN3':Score['TN3']+Score2['TN3'],'TN5':Score['TN5']+Score2['TN5'],'TN10':Score['TN10']+Score2['TN10'],'TN20':Score['TN20']+Score2['TN20'],
                  'FN1':Score['FN1']+Score2['FN1'],'FN3':Score['FN3']+Score2['FN3'],'FN5':Score['FN5']+Score2['FN5'],'FN10':Score['FN10']+Score2['FN10'],'FN20':Score['FN20']+Score2['FN20']}
        tndcgs = {'TN3':ndcgs['TN3']+ndcgs2['TN3'], 'TN5':ndcgs['TN5']+ndcgs2['TN5'], 'TN10':ndcgs['TN10']+ndcgs2['TN10'], 'TN20':ndcgs['TN20']+ndcgs2['TN20']}
        tMRR = MRR+MRR2

        Recall(tScore, result)
        Precision(tScore, result)
        ndcg(tScore,tndcgs, result)
        mrr(tMRR, result)

    if D != 2:
        result.write("\n===Watched===\n")
        print('===Watched===')
        
        Recall(Score,result)
        Precision(Score,result)
        ndcg(Score,ndcgs,result)
        mrr(MRR,result)

    if D != 1:
        result.write("\n===Unwatched===\n")
        print('===Unwatched===')

        Recall(Score2,result)
        Precision(Score2,result)
        ndcg(Score2,ndcgs2,result)
        mrr(MRR2,result)