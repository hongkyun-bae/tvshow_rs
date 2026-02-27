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

		public static Dictionary<string, double> PerformAlgorithm(Algorithm algo, CandidateItems mode, IRatings training_data, IRatings test_data)
        {
            var recommender = Scenario.SelectAlgorithm(algo);
            recommender.Ratings = training_data;
            recommender.Train();

            // evlaute Top-N recommendation
            return Ratings2.Evaluate(recommender, test_data, training_data, null, null, mode);
        }

        // For only positive feedback data
        public static Dictionary<string, double> PerformAlgorithm(Algorithm algo, CandidateItems mode, IPosOnlyFeedback training_data, IPosOnlyFeedback test_data=null)
        {
            var recommender = Scenario.SelectPosOnlyFeedbackAlgorithm(algo);
            recommender.Feedback = training_data;
            recommender.Train();

            // evlaute Top-N recommendation
            //return Items2.Evaluate(recommender, test_data, training_data, null, null, mode);
            return null;
        }

        /* BPRMF를 통한 prediction 파일 생성 */
        public static void PerformPrediction(Algorithm algo, IPosOnlyFeedback trainingData)
        {
			globalIter = 1;

			var recommender = Scenario.SelectPosOnlyFeedbackAlgorithm(algo);
            recommender.Feedback = trainingData;
            recommender.Train();

            int maxUserid = recommender.Feedback.MaxUserID;
            int maxItemid = recommender.Feedback.MaxItemID;

            Console.WriteLine("Users: " + maxUserid + ", Items: " + maxItemid);

			//string outputPath = "../../../../origin/TVshow/LR0.001/Reg0.00125/Epi_Prop_x5_allneg_pos0.5.predict";

			//string filePath = "F:\\hongkyun_F\\Exp_result\\190201_TVshow_hongkyun\\origin\\1CV\\";

			//string filePath = "E:\\hongkyun\\TVshow\\";
			//string predictFile = "Epi_Prop_competable_alpha0.5_x" + globalIter + "_all.predict";
            //StreamWriter streamWriter = new StreamWriter(filePath + predictFile);

            //Console.WriteLine("PerformPrediction: Writing file...");
            //for (int uid = 1; uid <= maxUserid; uid++)
            //{
            //    for (int tid = 1; tid <= maxItemid; tid++)
            //    {
            //        float predictedPref = recommender.Predict(uid, tid);
            //        streamWriter.WriteLine("{0}\t{1}\t{2}", uid, tid, predictedPref);
            //    }
            //}
            //streamWriter.Close();

            return;
        }

        public static void PrintResults(string output, Dictionary<string, double> results, Dictionary<string, double> average)
        {
            var positions = new int[] { 5, 10, 15, 20 };

            sw = new StreamWriter(output);
            //sw.WriteLine("ATOP\t" + results["ATOP"]);
            //sw.WriteLine("MRR\t" + results["MRR"]);
            //sw.WriteLine("AUC\t" + results["AUC"]);
            //sw.WriteLine("HLU\t" + results["HLU"]);
            foreach (int pos in positions)
                sw.WriteLine("prec@" + pos + "\t" + results["prec@" + pos]);
            foreach (int pos in positions)
                sw.WriteLine("recall@" + pos + "\t" + results["recall@" + pos]);
            foreach (int pos in positions)
                sw.WriteLine("f1@" + pos + "\t" + (2 * (results["prec@" + pos] * results["recall@" + pos])) / (results["prec@" + pos] + results["recall@" + pos]));
            foreach (int pos in positions)
                sw.WriteLine("NDCG@" + pos + "\t" + results["NDCG@" + pos]);
            sw.Flush();
            sw.Close();

            sr = new StreamReader(output);
            while (!sr.EndOfStream)
            {
                string[] line = sr.ReadLine().Split(new char[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);

                if (!average.ContainsKey(line[0]))
                    average.Add(line[0], double.Parse(line[1].ToString()));
                else
                    average[line[0]] += double.Parse(line[1].ToString());
            }
            sr.Close();
        }

        public static void Main(string[] args)
        {
            //string filePath = "F:\\hongkyun_F\\Exp_result\\190201_TVshow_hongkyun\\origin\\1CV\\";
            //string filePath = "E:\\hongkyun\\TVshow\\";
            string filePath = "../../../data/";
            string baseFile = "Epi_Prop_competable.base";

            var trainingData = ItemData.Read(filePath + baseFile);

            Algorithm algo = Algorithm.BPRMF;

            PerformPrediction(algo, trainingData);
            //PerformAlgorithm(algo, CandidateItems.UNION, trainingData, testData);
            //PerformAlgorithm(algo, CandidateItems.UNION, trainingData);

            return;
        }

    }

}
