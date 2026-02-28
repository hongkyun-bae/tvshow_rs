using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using MyMediaLite.Data;
using MyMediaLite.Eval;
using MyMediaLite.IO;
using MyMediaLite.RatingPrediction;
using MyMediaLite.ItemRecommendation;
using System.Diagnostics;
using System.IO;

namespace MyMediaLite
{
    public enum Algorithm
    {
        ItemPopularity,
        ItemKNN,
        NonNormalizedItemKNN,
        PrefItemKNN,
        UserKNN,
        NonNormalizedUserKNN,
        PrefUserKNN,
        SVD,
        SVDPlusPlus,
        PureSVD,
        PrefPureSVD,
        DecoupledModel,
        BPRLinear,
        BPRMF,
        BPRSLIM,
        LeastSquareSLIM,
        WRMF,
        SoftMarginRankingMF
    };

    class Program
    {
        public static StreamReader sr;
        public static StreamWriter sw;
		public static int globalIter;
		public static bool isSequential, isPosRandom, isNegRandom, hasWeight, hasRandPair;
		public static double pos_threshold;

        /* BPRMF를 통한 prediction 파일 생성 */
        public static void PerformPrediction(Algorithm algo, IPosOnlyFeedback trainingData)
        {
			globalIter = 50;
			isSequential = false;
			isPosRandom = true;
			isNegRandom = true;

			hasWeight = false;      // Currently, not used anymore
			hasRandPair = false;    // Currently, not used anymore

			pos_threshold = 0.1;

			var recommender = Scenario.SelectPosOnlyFeedbackAlgorithm(algo);
            recommender.Feedback = trainingData;

            DateTime startTime = DateTime.Now;
            recommender.Train();
            DateTime finishTime = DateTime.Now;
            TimeSpan elapsedTime = finishTime - startTime;
            Console.WriteLine("Training model (500000): " + elapsedTime.TotalSeconds);

            int maxUserid = recommender.Feedback.MaxUserID;
            int maxItemid = recommender.Feedback.MaxItemID;

            Console.WriteLine("Users: " + maxUserid + ", Items: " + maxItemid);

			//string filePath = "E:\\hongkyun\\TVshow\\";
			//string filePath = "E:\\hongkyun\\TVshow\\wIntv-based\\";
			//string filePath = "E:\\hongkyun\\TVshow\\wableIntv-based\\";
			////string predictFile = "Epi_Prop_competable_alpha" + pos_threshold + "_0.1_x" + globalIter + "_all";
			//string predictFile = "Epi_Prop_competable_alpha" + pos_threshold + "_x" + globalIter + "_all";

			//if (isSequential)
			//	predictFile += "_seq";
			//if (isPosRandom)
			//	predictFile += "_posrand";
			//if (isNegRandom)
			//	predictFile += "_negrand";
			//if (hasWeight)
			//	predictFile += "_wgt(rev)";
			//if (hasRandPair)
			//	predictFile += "_randpair1";

			//predictFile += ".predict";
			////string predictFile = "Epi_Prop_competable_alpha0.5_x" + globalIter + "_all_seq_wgt.predict";
			//StreamWriter streamWriter = new StreamWriter(filePath + predictFile);

			//Console.WriteLine("PerformPrediction: Writing file...");
			//for (int uid = 1; uid <= maxUserid; uid++)
			//{
			//	for (int tid = 1; tid <= maxItemid; tid++)
			//	{
			//		float predictedPref = recommender.Predict(uid, tid);
			//		streamWriter.WriteLine("{0}\t{1}\t{2}", uid, tid, predictedPref);
			//	}
			//}
			//streamWriter.Close();

			return;
        }

        public static void Main(string[] args)
        {
            //string filePath = "E:\\hongkyun\\TVshow\\";
            //string filePath = "../../../data/";
            string filePath = "C:\\Users\\hongkyun\\Desktop\\MyMediaLite_BPRMF for TV show Recommendation_Competable_all_build_negatives_wable\\data\\";
            string baseFile = "Epi_Prop_competable.base";

            var trainingData = ItemData.Read(filePath + baseFile);

            Algorithm algo = Algorithm.BPRMF;

            PerformPrediction(algo, trainingData);

            return;
        }

    }

}
