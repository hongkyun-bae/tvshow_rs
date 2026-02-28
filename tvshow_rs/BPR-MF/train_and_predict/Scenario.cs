using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using MyMediaLite.Data;
using MyMediaLite.DataType;
using MyMediaLite.Eval;
using MyMediaLite.IO;
using MyMediaLite.ItemRecommendation;
using MyMediaLite.RatingPrediction;
using System.IO;

namespace MyMediaLite
{
    class Scenario
    {
        public static string file_path = "..\\..\\DataFile\\";

        public static RatingPredictor SelectAlgorithm(Algorithm alg)
        {
            switch (alg)
            {
                case Algorithm.ItemPopularity:
                    return new ItemPopularity();

                case Algorithm.ItemKNN:
                    return new MyMediaLite.RatingPrediction.ItemKNN();

                case Algorithm.NonNormalizedItemKNN:
                    return new NonNormalizedItemKNN();

                case Algorithm.PrefItemKNN:
                    return new PrefItemKNN();

                case Algorithm.UserKNN:
                    return new MyMediaLite.RatingPrediction.UserKNN();

                case Algorithm.NonNormalizedUserKNN:
                    return new NonNormalizedUserKNN();

                case Algorithm.PrefUserKNN:
                    return new PrefUserKNN();

                case Algorithm.SVD:
                    return new MatrixFactorization();

                case Algorithm.SVDPlusPlus:
                    return new SVDPlusPlus();

                case Algorithm.PureSVD:
                    return new PureSVD();

                case Algorithm.PrefPureSVD:
                    return new PrefPureSVD();

                case Algorithm.DecoupledModel:
                    return new DecoupledModel();

                default:
                    return new ItemPopularity();
            }
        }

        public static ItemRecommender SelectPosOnlyFeedbackAlgorithm(Algorithm alg)
        {
            switch (alg)
            {
                case Algorithm.BPRLinear:
                    return new BPRLinear();

                case Algorithm.BPRMF:
                    return new BPRMF();

                case Algorithm.BPRSLIM:
                    return new BPRSLIM();

                case Algorithm.LeastSquareSLIM:
                    return new LeastSquareSLIM();

                case Algorithm.WRMF:
                    return new WRMF();

                case Algorithm.SoftMarginRankingMF:
                    return new SoftMarginRankingMF();

                default:
                    return new BPRLinear();
            }
        }

        /// <summary>k-fold cross-validation split for traditional experiment</summary>
        public static RatingCrossValidationSplit SplitData(string data_file)
        {
            uint num_folds = 5;

            Random.Seed = 1;
            var all_data = RatingData.Read(file_path + data_file);

            return new RatingCrossValidationSplit(all_data, num_folds);
        }

        /// <summary>k-fold cross-validation split for cold-start experiment</summary>
        /// <param name="num_training">the number of training users</param>
        /// <param name="train_given">the number of items rated by testing users</param>
        /// <param name="test_given">the number of items that will be predicted for each testing user</param>
        /// <param name="cold_user">if we perform cold-user experiments(i.e. UserKNN, SVD), assign true (cold-item experimetns(i.e. ItemKNN) -> false)</param>
        public static RatingCrossValidationSplit SplitDataForCold(string data_file, uint num_training, uint train_given, uint test_given, bool cold_user)
        {
            uint num_folds = 5;

            Random.Seed = 1;
            var all_data = RatingData.Read(file_path + data_file);

            return new RatingCrossValidationSplit(all_data, num_folds, num_training, train_given, test_given, cold_user); 
        }

        /// <summary>k-fold cross-validation split for traditional experiment</summary>
        public static PosOnlyFeedbackCrossValidationSplit<PosOnlyFeedback<SparseBooleanMatrix>> SplitBinaryData(string data_file)
        {
            uint num_folds = 5;

            Random.Seed = 1;
            var all_data = RatingData.Read(file_path + data_file);

            return new PosOnlyFeedbackCrossValidationSplit<PosOnlyFeedback<SparseBooleanMatrix>>(all_data, num_folds);
        }

        /// <summary>k-fold cross-validation split for cold-start experiment</summary>
        /// <param name="num_training">the number of training users</param>
        /// <param name="train_given">the number of items rated by testing users</param>
        /// <param name="test_given">the number of items that will be predicted for each testing user</param>
        /// <param name="cold_user">if we perform cold-user experiments(i.e. UserKNN, SVD), assign true (cold-item experimetns(i.e. ItemKNN) -> false)</param>
        public static PosOnlyFeedbackCrossValidationSplit<PosOnlyFeedback<SparseBooleanMatrix>> SplitBinaryDataForCold(string data_file, uint num_training, uint train_given, uint test_given, bool cold_user)
        {
            uint num_folds = 5;

            Random.Seed = 1;
            var all_data = RatingData.Read(file_path + data_file);

            return new PosOnlyFeedbackCrossValidationSplit<PosOnlyFeedback<SparseBooleanMatrix>>(all_data, num_folds, num_training, train_given, test_given, cold_user);
        }

        /// <summary>k-fold cross-validation</summary>
        /// <param name="split">a dataset split</param>
        /// <param name="cur_mode">the mode used to determine the candidate items</param>
        /// <param name="alg">selected algorithm</param>
        /// <param name="cold">if we perform cold-start experiments, assign true</param>
        public static void DoCrossValidation(string file_name, RatingCrossValidationSplit split, CandidateItems cur_mode, Algorithm alg, bool cold)
        {
            // select algorithm
            var recommender = SelectAlgorithm(alg);

            // perform k-fold cross-validation
            var results = RatingsCrossValidationForTopN.DoCrossValidation(recommender, split, null, cold, cur_mode);

            // print results
            PrintResults(file_name, alg, results);
        }

        /// <summary>k-fold cross-validation</summary>
        /// <param name="split">a dataset split</param>
        /// <param name="cur_mode">the mode used to determine the candidate items</param>
        /// <param name="alg">selected algorithm</param>
        /// <param name="cold">if we perform cold-start experiments, assign true</param>
        public static void DoCrossValidation(string file_name, PosOnlyFeedbackCrossValidationSplit<PosOnlyFeedback<SparseBooleanMatrix>> split, CandidateItems cur_mode, Algorithm alg, bool cold)
        {
            // select algorithm
            var recommender = SelectPosOnlyFeedbackAlgorithm(alg);

            Console.WriteLine(recommender.ToString());            
            
            // perform k-fold cross-validation
            var results = ItemCrossValidationForTopN.DoCrossValidation(recommender, split, null, cold, cur_mode);

            PrintResults(file_name, alg, results);            
        }

        public static void PrintResults(string file_name, Algorithm alg, Dictionary<string, double> results)
        {
            string output_file = file_path + file_name;
            FileStream fs = new FileStream(output_file, FileMode.Append, FileAccess.Write);
            StreamWriter sw = new StreamWriter(fs, System.Text.Encoding.UTF8);

            sw.WriteLine(" \t" + alg);
            foreach (KeyValuePair<string, double> measure in results)
            {
                sw.Write(measure.Key + "\t");
                sw.WriteLine("{0,10:F3}", measure.Value);
            }
            sw.WriteLine();
            Console.WriteLine("Completed: " + alg);

            sw.Close();
            fs.Close();
        }
    }
}
