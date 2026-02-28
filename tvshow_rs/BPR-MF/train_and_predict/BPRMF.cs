// Copyright (C) 2011, 2012, 2013 Zeno Gantner
// Copyright (C) 2010 Zeno Gantner, Christoph Freudenthaler
//
// This file is part of MyMediaLite.
//
// MyMediaLite is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// MyMediaLite is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
//  You should have received a copy of the GNU General Public License
//  along with MyMediaLite.  If not, see <http://www.gnu.org/licenses/>.
using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using MyMediaLite;
using MyMediaLite.DataType;
using MyMediaLite.Eval;
using MyMediaLite.IO;

namespace MyMediaLite.ItemRecommendation
{
	/// <summary>Matrix factorization model for item prediction (ranking) optimized for BPR </summary>
	/// <remarks>
	///   <para>
	///     BPR reduces ranking to pairwise classification.
	///     The different variants (settings) of this recommender
	///     roughly optimize the area under the ROC curve (AUC).
	///   </para>
	///   <para>
	///     \f[
	///       \max_\Theta \sum_{(u,i,j) \in D_S}
	///                        \ln g(\hat{s}_{u,i,j}(\Theta)) - \lambda ||\Theta||^2 ,
	///     \f]
	///     where \f$\hat{s}_{u,i,j}(\Theta) := \hat{s}_{u,i}(\Theta) - \hat{s}_{u,j}(\Theta)\f$
	///     and \f$D_S = \{ (u, i, j) | i \in \mathcal{I}^+_u \wedge j \in \mathcal{I}^-_u \}\f$.
	///     \f$\Theta\f$ represents the parameters of the model and \f$\lambda\f$ is a regularization constant.
	///     \f$g\f$ is the  logistic function.
	///   </para>
	///   <para>
	///     In this implementation, we distinguish different regularization updates for users and positive and negative items,
	///     which means we do not have only one regularization constant. The optimization problem specified above thus is only
	///     an approximation.
	///   </para>
	///   <para>
	///     Literature:
	///     <list type="bullet">
	///       <item><description>
	///         Steffen Rendle, Christoph Freudenthaler, Zeno Gantner, Lars Schmidt-Thieme:
	///         BPR: Bayesian Personalized Ranking from Implicit Feedback.
	///         UAI 2009.
	///         http://www.ismll.uni-hildesheim.de/pub/pdfs/Rendle_et_al2009-Bayesian_Personalized_Ranking.pdf
	///       </description></item>
	///     </list>
	///   </para>
	///   <para>
	///     Different sampling strategies are configurable by setting the UniformUserSampling and WithReplacement accordingly.
	///     To get the strategy from the original paper, set UniformUserSampling=false and WithReplacement=false.
	///     WithReplacement=true (default) gives you usually a slightly faster convergence, and UniformUserSampling=true (default)
	///     (approximately) optimizes the average AUC over all users.
	///   </para>
	///   <para>
	///     This recommender supports incremental updates.
	///   </para>
	/// </remarks>
	public class BPRMF : MF, IFoldInItemRecommender
	{
		/// <summary>Item bias terms</summary>
		protected float[] item_bias;

		/// <summary>Sample positive observations with (true) or without (false) replacement</summary>
		public bool WithReplacement { get; set; }

		/// <summary>Sample uniformly from users</summary>
		public bool UniformUserSampling { get; set; }

		/// <summary>Regularization parameter for the bias term</summary>
		public float BiasReg { get; set; }

		/// <summary>Learning rate alpha</summary>
		public float LearnRate { get { return learn_rate; } set { learn_rate = value; } }
        /// <summary>Learning rate alpha</summary>
        //protected float learn_rate = 0.05f;
        protected float learn_rate = 0.001f;
        //protected float learn_rate = 0.0001f;

        /// <summary>Regularization parameter for user factors</summary>
        public float RegU { get { return reg_u; } set { reg_u = value; } }
        /// <summary>Regularization parameter for user factors</summary>
        //protected float reg_u = 0.0025f;
        //protected float reg_u = 0.005f;
        protected float reg_u = 0.00125f;

        /// <summary>Regularization parameter for positive item factors</summary>
        public float RegI { get { return reg_i; } set { reg_i = value;	} }
        /// <summary>Regularization parameter for positive item factors</summary>
        //protected float reg_i = 0.0025f;
        //protected float reg_i = 0.005f;
        protected float reg_i = 0.00125f;

        /// <summary>Regularization parameter for negative item factors</summary>
        public float RegJ { get { return reg_j; } set { reg_j = value; } }
        /// <summary>Regularization parameter for negative item factors</summary>
        //protected float reg_j = 0.00025f;
        //protected float reg_j = 0.005f;
        protected float reg_j = 0.00125f;

		/// <summary>If set (default), update factors for negative sampled items during learning</summary>
		public bool UpdateJ { get { return update_j; } set { update_j = value; } }
		/// <summary>If set (default), update factors for negative sampled items during learning</summary>
		protected bool update_j = true;

		/// <summary>array of user components of triples to use for approximate loss computation</summary>
		int[] loss_sample_u;
		/// <summary>array of positive item components of triples to use for approximate loss computation</summary>
		int[] loss_sample_i;
		/// <summary>array of negative item components of triples to use for approximate loss computation</summary>
		int[] loss_sample_j;

		/// <summary>Reference to (per-thread) singleton random number generator</summary>
		[ThreadStatic] // we need one random number generator per thread because synchronizing is slow
		static protected System.Random random;

        ArrayList positive_list;
        ArrayList w_positive_list;					// if hasRandPair is equal to true
        ArrayList wintv_list;
        Dictionary<int, ArrayList> negative_dict;

		Dictionary<int, ArrayList> weight_dict;		// if hasWeight is equal to true
		double term_weight;							// if hasWeight is equal to true

        /// <summary>Default constructor</summary>
        public BPRMF()
		{
            //NumIter = 200;
            UniformUserSampling = true;
            WithReplacement = true;     // Add the option of replacement
			UpdateUsers = true;
			UpdateItems = false;
		}

        public BPRMF(int numIter, int numFact, float learnRate, float reg):base(numIter, numFact)
        {
            LearnRate = learnRate;
            RegU = reg;
            RegI = reg;
            RegJ = reg / 10.0f;

            UniformUserSampling = true;
            UpdateUsers = true;
            UpdateItems = false;
        }

		///
		protected override void InitModel()
		{
			base.InitModel();

			item_bias = new float[MaxItemID + 1];
		}

		///
		public override void Train()
		{
			InitModel();

			random = MyMediaLite.Random.GetInstance();

			{
				int num_sample_triples = (int) Math.Sqrt(MaxUserID) * 100;      // if MaxUserID is equal to 943, num_sample_triples is set to 3000
				Console.Error.WriteLine("loss_num_sample_triples={0}", num_sample_triples);
				// create the sample to estimate loss from
				loss_sample_u = new int[num_sample_triples];
				loss_sample_i = new int[num_sample_triples];
				loss_sample_j = new int[num_sample_triples];
				int user_id, item_id, other_item_id;
				for (int c = 0; c < num_sample_triples; c++)
				{
					SampleTriple(out user_id, out item_id, out other_item_id);
					loss_sample_u[c] = user_id;
					loss_sample_i[c] = item_id;
					loss_sample_j[c] = other_item_id;
				}
			}

            /* Set positive_list */
            positive_list = new ArrayList();

            string file_path = "C:\\Users\\hongkyun\\Desktop\\MyMediaLite_BPRMF for TV show Recommendation_Competable_all_build_negatives_wable\\data\\";
            StreamReader sr_ep = new StreamReader(file_path + "500000_Epi_Prop_competable.base");

            string line = "";
            double ep_sum = 0.0;
            while ((line = sr_ep.ReadLine()) != null)
            {
                string[] row = line.Split();
                double ep = double.Parse(row[2]);

				if (ep > Program.pos_threshold)
					ep_sum += ep;
				//if (ep > 0.1)
				//	ep_sum += ep;
			}
            sr_ep.Close();

            sr_ep = new StreamReader(file_path + "500000_Epi_Prop_competable.base");

            int num_rows = 0;
            double base_prob = 0.0;
            line = "";
            while ((line = sr_ep.ReadLine()) != null)
            {
                string[] row = line.Split();
                int uid = int.Parse(row[0]);
                int tid = int.Parse(row[1]);
                double ep = double.Parse(row[2]);

                num_rows += 1;

				if (ep > Program.pos_threshold)
				{
					double temp = base_prob;
					base_prob += (ep / ep_sum);
					UserItemEP positive_pair = new UserItemEP(num_rows, uid, tid, ep, temp, base_prob);
					positive_list.Add(positive_pair);
				}
				//if (ep > 0.1)
				//{
				//	double temp = base_prob;
				//	base_prob += (ep / ep_sum);
				//	UserItemEP positive_pair = new UserItemEP(num_rows, uid, tid, ep, temp, base_prob);
				//	positive_list.Add(positive_pair);
				//}
			}
            sr_ep.Close();
            Console.WriteLine("Total number of rows in competable file: " + num_rows);
            Console.WriteLine("Aggregated probability: " + base_prob);

            /* Set wintv_list */
            //         wintv_list = new ArrayList();
            //StreamReader sr_wintv = new StreamReader("E:\\hongkyun\\TVshow\\Epi_Prop_w_intv.base");

            //num_rows = 0;
            //         line = "";
            //         while ((line = sr_wintv.ReadLine()) != null)
            //         {
            //             string[] row = line.Split('\t');
            //             int uid = int.Parse(row[0]);
            //             int tid = int.Parse(row[1]);
            //             string dates = row[2];

            //             num_rows += 1;

            //             char[] delimiterChars = { ',' };
            //             string[] dt = dates.Split(delimiterChars, StringSplitOptions.RemoveEmptyEntries);
            //             if (dt.Length > 0)
            //             {
            //                 ArrayList dt_list = new ArrayList();
            //                 for (int i = 0; i < dt.Length; i++)
            //                 {
            //                     DateTime date_time = Convert.ToDateTime(dt[i]);
            //                     dt_list.Add(date_time);
            //                 }

            //                 UserItemDate date_pair = new UserItemDate(num_rows, uid, tid, dt_list);
            //                 wintv_list.Add(date_pair);
            //             }
            //         }
            //         sr_wintv.Close();
            //         Console.WriteLine("Total number of rows in wintv file: " + num_rows);

            /* Set negative_dict */
            negative_dict = new Dictionary<int, ArrayList>();
			foreach (UserItemEP positive_pair in positive_list)
			{
				int idx = positive_pair.IDX;
                //string negatives_file_name = "E:\\hongkyun\\TVshow\\wIntv-based\\negatives_0.1\\Epi_Prop_negatives_" + idx + ".base";
                //string negatives_file_name = "E:\\hongkyun\\TVshow\\wableIntv-based\\negatives_0.1_0.1\\Epi_Prop_negatives_" + idx + ".base";
                string negatives_file_name = "D:\\Deadpool_backup\\TVshow\\wableIntv-based\\negatives_0.1_0.1\\Epi_Prop_negatives_" + idx + ".base";

                //FileInfo file_info = new FileInfo(negatives_file_name);
                StreamReader sr_negative = null;
				//if (file_info.Exists)
				//	sr_negative = new StreamReader(negatives_file_name);
				//else
				//	continue;

				sr_negative = new StreamReader(negatives_file_name);

				negative_dict[idx] = new ArrayList();

				while ((line = sr_negative.ReadLine()) != null)
				{
					char[] delimiterChars = { ',' };
					string[] ids = line.Split(delimiterChars, StringSplitOptions.RemoveEmptyEntries);

					for (int i = 0; i < ids.Length; i++)
					{
						int negative_id = int.Parse(ids[i]);
						negative_dict[idx].Add(negative_id);
					}
				}
				sr_negative.Close();
			}
			Console.WriteLine("Total number of elements in negative_dict: " + negative_dict.Count);

			/* Set weight_dict */
			if (Program.hasWeight == true)
			{
				weight_dict = new Dictionary<int, ArrayList>();
				foreach (UserItemEP positive_pair in positive_list)
				{
					int idx = positive_pair.IDX;
					int max_diff = 0, min_diff = 0;
					StreamReader sr_negative_diff = new StreamReader("E:\\hongkyun\\TVshow\\wIntv-based\\negatives_diff_" + Program.pos_threshold + "\\Epi_Prop_negatives_" + idx + "_diff.base");					

					weight_dict[idx] = new ArrayList();

					while ((line = sr_negative_diff.ReadLine()) != null)
					{
						char[] delimiterChars = { ',' };
						string[] ids = line.Split(delimiterChars, StringSplitOptions.RemoveEmptyEntries);

						for (int i = 0; i < ids.Length; i++)
						{
							int negative_diff = int.Parse(ids[i]);

							if (i == 0)
							{
								max_diff = negative_diff;
								min_diff = negative_diff;
							}
							else
							{
								if (negative_diff > max_diff)
									max_diff = negative_diff;
								if (negative_diff < min_diff)
									min_diff = negative_diff;
							}							
						}

						for (int i = 0; i < ids.Length; i++)
						{
							int negative_diff = int.Parse(ids[i]);
							double weight = 1.0;

							if (max_diff != min_diff)
							{
								weight = ((double)(negative_diff - min_diff)) / (max_diff - min_diff);
								//weight = ((double)(negative_diff)) / max_diff;

								weight = 1 - weight;

								//if (weight != 0.0)
								//	weight = 1 / weight;
								//else
								//{
								//	Console.WriteLine("weight is equal to zero");
								//	weight = max_diff;
								//}
							}
							//Console.WriteLine("Weight: " + weight);
							weight_dict[idx].Add(weight);
						}
					}
					sr_negative_diff.Close();
				}

				Console.WriteLine("Total number of elements in negative_diff_dict: " + weight_dict.Count);
			}


			Console.WriteLine("Total iterations: " + Program.globalIter);
			for (int i = 0; i < Program.globalIter; i++)
            {
                Console.WriteLine("Iteration: " + i);
                Iterate();
            }
        }

		/// <summary>Perform one iteration of stochastic gradient ascent over the training data</summary>
		/// <remarks>
		/// One iteration is samples number of positive entries in the training matrix times
		/// </remarks>
		public override void Iterate()
		{
			random = MyMediaLite.Random.GetInstance(); // in case Iterate() is not called from Train()

			if (UniformUserSampling)
			{
				if (WithReplacement)
					IterateWithReplacementUniformUser();    // Run
                else
					IterateWithoutReplacementUniformUser();
			}
			else
			{
				if (WithReplacement)
					IterateWithReplacementUniformPair();
				else
					IterateWithoutReplacementUniformPair();
			}
		}

		/// <summary>
		/// Iterate over the training data, uniformly sample from users with replacement.
		/// </summary>
		protected virtual void IterateWithReplacementUniformUser()
		{
			int num_pos_events = positive_list.Count;
			Console.WriteLine("Number of iterations: " + num_pos_events);	// 315,248

            int idx = 0, user_id = 0, pos_item_id = 0;
            int unit = num_pos_events / 100;

            for (int i = 0; i < num_pos_events; i++)
			{
				//Console.WriteLine("i: " + i);

				if ((i % unit) == 0)
					Console.WriteLine((i / unit) + "%...");

				double rand_double = random.NextDouble();

				/* Determine positive episode according to random number */
				if (Program.isSequential == false)
				{
					if (Program.isPosRandom == false)
					{
						foreach (UserItemEP ep_pair in positive_list)
						{
							double prob1 = ep_pair.Prob1;
							double prob2 = ep_pair.Prob2;

							if ((prob1 <= rand_double) && (rand_double < prob2))
							{
								idx = ep_pair.IDX;
								user_id = ep_pair.UserID;
								pos_item_id = ep_pair.ItemID;

								//Console.WriteLine("IDX: " + idx + ", UID: " + user_id + ", Pos_TID: " + pos_item_id);

								break;
							}
						}
					}
					else
					{
						int posRandom = random.Next(positive_list.Count);
						UserItemEP ep_pair = (UserItemEP)positive_list[posRandom];
						idx = ep_pair.IDX;
						user_id = ep_pair.UserID;
						pos_item_id = ep_pair.ItemID;

						//Console.WriteLine("IDX: " + idx + ", UID: " + user_id + ", Pos_TID: " + pos_item_id);
					}
				}

				/* Determine positive episode sequentially */
				else
				{
					UserItemEP ep_pair = (UserItemEP)positive_list[i];
					idx = ep_pair.IDX;
					user_id = ep_pair.UserID;
					pos_item_id = ep_pair.ItemID;
				}


				if (negative_dict[idx].Count == 0)
				{
					//if (Program.hasRandPair == true)
					//{
					//	//Console.WriteLine("Building a non-watchable pair...");
					//	int neg_item_id = 0;
					//	do
					//		neg_item_id = random.Next(MaxItemID + 1);
					//	while (Feedback.UserMatrix[user_id].Contains(neg_item_id));

					//	if (Program.hasWeight == true)
					//		term_weight = 1.0;

					//	UpdateFactors(user_id, pos_item_id, neg_item_id, true, true, update_j);
					//}

					continue;
				}
				else
				{
					//foreach (int neg_item_id in negative_dict[idx])
					//{
					//	UpdateFactors(user_id, pos_item_id, neg_item_id, true, true, update_j);
					//}

					if (Program.isNegRandom == false)
					{
						for (int j = 0; j < negative_dict[idx].Count; j++)
						{
							int neg_item_id = (int)negative_dict[idx][j];

							if (Program.hasWeight == true)
								term_weight = (double)weight_dict[idx][j];

							UpdateFactors(user_id, pos_item_id, neg_item_id, true, true, update_j);
						}
					}
					else
					{
						int negRandom = random.Next(negative_dict[idx].Count);
						int neg_item_id = (int)negative_dict[idx][negRandom];

						UpdateFactors(user_id, pos_item_id, neg_item_id, true, true, update_j);
					}
				}

				//if (Program.hasRandPair == true)
				//{
				//	int neg_item_id = 0;
				//	do
				//		neg_item_id = random.Next(MaxItemID + 1);
				//	while (Feedback.UserMatrix[user_id].Contains(neg_item_id));

				//	if (Program.hasWeight == true)
				//		term_weight = 1.0;

				//	UpdateFactors(user_id, pos_item_id, neg_item_id, true, true, update_j);
				//}
			}
        }

		/// <summary>
		/// Iterate over the training data, uniformly sample from users without replacement.
		/// </summary>
		protected virtual void IterateWithoutReplacementUniformUser()
		{
			int num_pos_events = Feedback.Count;
			int user_id, pos_item_id, neg_item_id;

            StreamWriter streamWriter = new StreamWriter("../../../../results/10Fact_1CV_Reg0.0025_Prop.pairs");

			for (int i = 0; i < num_pos_events; i++)
			{
				SampleTriple(out user_id, out pos_item_id, out neg_item_id);
                streamWriter.WriteLine("{0}\t{1}\t{2}", user_id, pos_item_id, neg_item_id);
				UpdateFactors(user_id, pos_item_id, neg_item_id, true, true, update_j);     // (In the case of TV show) should construct the pair of uid, positive_epi, negative_epi
			}
            streamWriter.Close();
		}

		/// <summary>
		/// Iterate over the training data, uniformly sample from user-item pairs with replacement.
		/// </summary>
		protected virtual void IterateWithReplacementUniformPair()
		{
			int num_pos_events = Feedback.Count;
			for (int i = 0; i < num_pos_events; i++)
			{
				int index = random.Next(num_pos_events);
				int user_id = Feedback.Users[index];
				int pos_item_id = Feedback.Items[index];
				int neg_item_id = -1;
				SampleOtherItem(user_id, pos_item_id, out neg_item_id);
				UpdateFactors(user_id, pos_item_id, neg_item_id, true, true, update_j);
			}
		}

		/// <summary>
		/// Iterate over the training data, uniformly sample from user-item pairs without replacement.
		/// </summary>
		protected virtual void IterateWithoutReplacementUniformPair()
		{
			IterateWithoutReplacementUniformPair(Feedback.RandomIndex);
		}

		/// <summary>
		/// Iterate over the training data, uniformly sample from user-item pairs without replacement.
		/// </summary>
		protected virtual void IterateWithoutReplacementUniformPair(IList<int> indices)
		{
			random = MyMediaLite.Random.GetInstance(); // if necessary, initialize for this thread

			foreach (int index in indices)
			{
				int user_id = Feedback.Users[index];
				int pos_item_id = Feedback.Items[index];
				int neg_item_id = -1;
				SampleOtherItem(user_id, pos_item_id, out neg_item_id);
				UpdateFactors(user_id, pos_item_id, neg_item_id, true, true, update_j);
			}
		}

		/// <summary>Sample another item, given the first one and the user</summary>
		/// <param name="user_id">the user ID</param>
		/// <param name="item_id">the ID of the given item</param>
		/// <param name="other_item_id">the ID of the other item</param>
		/// <returns>true if the given item was already seen by user u</returns>
		protected virtual bool SampleOtherItem(int user_id, int item_id, out int other_item_id)
		{
			bool item_is_positive = Feedback.UserMatrix[user_id, item_id];

			do
				other_item_id = random.Next(MaxItemID + 1);
			while (Feedback.UserMatrix[user_id, other_item_id] == item_is_positive);

			return item_is_positive;
		}

		/// <summary>Sample a pair of items, given a user</summary>
		/// <param name="user_items">the items accessed by the given user</param>
		/// <param name="item_id">the ID of the first item</param>
		/// <param name="other_item_id">the ID of the second item</param>
		protected virtual void SampleItemPair(ICollection<int> user_items, out int item_id, out int other_item_id)
		{
			item_id = user_items.ElementAt(random.Next(user_items.Count));  // Randomly select the item id which is i-th position in user_items
			do
				other_item_id = random.Next(MaxItemID + 1);
			while (user_items.Contains(other_item_id));
		}

		/// <summary>Uniformly sample a user that has viewed at least one and not all items</summary>
		/// <returns>the user ID</returns>
		protected virtual int SampleUser()
		{
			while (true)
			{
				int user_id = random.Next(MaxUserID + 1);
				var user_items = Feedback.UserMatrix[user_id];
				if (user_items.Count == 0 || user_items.Count == MaxItemID + 1)
					continue;
				return user_id;
			}
		}

		/// <summary>Sample a triple for BPR learning</summary>
		/// <param name="user_id">the user ID</param>
		/// <param name="item_id">the ID of the first item</param>
		/// <param name="other_item_id">the ID of the second item</param>
		protected virtual void SampleTriple(out int user_id, out int item_id, out int other_item_id)
		{
			user_id = SampleUser();
			var user_items = Feedback.UserMatrix[user_id];
			SampleItemPair(user_items, out item_id, out other_item_id);
		}

		/// <summary>Update latent factors according to the stochastic gradient descent update rule</summary>
		/// <param name="user_id">the user ID</param>
		/// <param name="item_id">the ID of the first item</param>
		/// <param name="other_item_id">the ID of the second item</param>
		/// <param name="update_u">if true, update the user latent factors</param>
		/// <param name="update_i">if true, update the latent factors of the first item</param>
		/// <param name="update_j">if true, update the latent factors of the second item</param>
		protected virtual void UpdateFactors(int user_id, int item_id, int other_item_id, bool update_u, bool update_i, bool update_j)
		{
			double x_uij = item_bias[item_id] - item_bias[other_item_id] + DataType.MatrixExtensions.RowScalarProductWithRowDifference(user_factors, user_id, item_factors, item_id, item_factors, other_item_id);

			//if (Program.hasWeight == true)
			//	x_uij *= term_weight;

			double one_over_one_plus_ex = 1 / (1 + Math.Exp(x_uij));

			if (Program.hasWeight == true)
			{
				one_over_one_plus_ex *= term_weight;      // Applies weight to the corresponding term
			}
			// adjust bias terms
			if (update_i)
			{
				double update = one_over_one_plus_ex - BiasReg * item_bias[item_id];
				item_bias[item_id] += (float) (learn_rate * update);
			}

			if (update_j)
			{
				double update = -one_over_one_plus_ex - BiasReg * item_bias[other_item_id];
				item_bias[other_item_id] += (float) (learn_rate * update);
			}

			// adjust factors
			for (int f = 0; f < num_factors; f++)
			{
				float w_uf = user_factors[user_id, f];
				float h_if = item_factors[item_id, f];
				float h_jf = item_factors[other_item_id, f];

				if (update_u)
				{
					double update = (h_if - h_jf) * one_over_one_plus_ex - reg_u * w_uf;
					user_factors[user_id, f] = (float) (w_uf + learn_rate * update);
				}

				if (update_i)
				{
					double update = w_uf * one_over_one_plus_ex - reg_i * h_if;
					item_factors[item_id, f] = (float) (h_if + learn_rate * update);
				}

				if (update_j)
				{
					double update = -w_uf * one_over_one_plus_ex - reg_j * h_jf;
					item_factors[other_item_id, f] = (float) (h_jf + learn_rate * update);
				}
			}
		}

		///
		protected override void AddItem(int item_id)
		{
			base.AddItem(item_id);
			Array.Resize(ref item_bias, MaxItemID + 1);
		}

		///
		public override void RemoveItem(int item_id)
		{
			base.RemoveItem(item_id);
			item_bias[item_id] = 0;
		}

		///
		protected override void RetrainUser(int user_id)
		{
			user_factors.RowInitNormal(user_id, InitMean, InitStdDev);

			var user_items = Feedback.UserMatrix[user_id];
			for (int i = 0; i < user_items.Count; i++)
			{
				int item_id_1, item_id_2;
				SampleItemPair(user_items, out item_id_1, out item_id_2);
				UpdateFactors(user_id, item_id_1, item_id_2, true, false, false);
			}
		}

		///
		protected override void RetrainItem(int item_id)
		{
			item_factors.RowInitNormal(item_id, InitMean, InitStdDev);

			int num_pos_events = Feedback.UserMatrix.NumberOfEntries;
			int num_item_iterations = num_pos_events  / (MaxItemID + 1);
			for (int i = 0; i < num_item_iterations; i++) {
				// remark: the item may be updated more or less frequently than in the normal from-scratch training
				int user_id = SampleUser();
				int other_item_id;
				bool item_is_positive = SampleOtherItem(user_id, item_id, out other_item_id);

				if (item_is_positive)
					UpdateFactors(user_id, item_id, other_item_id, false, true, false);
				else
					UpdateFactors(user_id, other_item_id, item_id, false, false, true);
			}
		}

		///
		public override float ComputeObjective()
		{
			double ranking_loss = 0;
			for (int c = 0; c < loss_sample_u.Length; c++)
			{
				double x_uij = Predict(loss_sample_u[c], loss_sample_i[c]) - Predict(loss_sample_u[c], loss_sample_j[c]);
				ranking_loss += 1 / (1 + Math.Exp(x_uij));
			}

			double complexity = 0;
			for (int c = 0; c < loss_sample_u.Length; c++)
			{
				complexity += RegU * Math.Pow(user_factors.GetRow(loss_sample_u[c]).EuclideanNorm(), 2);
				complexity += RegI * Math.Pow(item_factors.GetRow(loss_sample_i[c]).EuclideanNorm(), 2);
				complexity += RegJ * Math.Pow(item_factors.GetRow(loss_sample_j[c]).EuclideanNorm(), 2);
				complexity += BiasReg * Math.Pow(item_bias[loss_sample_i[c]], 2);
				complexity += BiasReg * Math.Pow(item_bias[loss_sample_j[c]], 2);
			}

			return (float) (ranking_loss + 0.5 * complexity);
		}

		///
		public override float Predict(int user_id, int item_id)
		{
			if (user_id > MaxUserID || item_id > MaxItemID)
				return float.MinValue;

			return item_bias[item_id] + DataType.MatrixExtensions.RowScalarProduct(user_factors, user_id, item_factors, item_id);
		}

		///
		public override void SaveModel(string file)
		{
			using ( StreamWriter writer = Model.GetWriter(file, this.GetType(), "2.99") )
			{
				writer.WriteMatrix(user_factors);
				writer.WriteVector(item_bias);
				writer.WriteMatrix(item_factors);
			}
		}

		///
		public override void LoadModel(string file)
		{
			random = MyMediaLite.Random.GetInstance();

			using ( StreamReader reader = Model.GetReader(file, this.GetType()) )
			{
				var user_factors = (Matrix<float>) reader.ReadMatrix(new Matrix<float>(0, 0));
				var item_bias = reader.ReadVector();
				var item_factors = (Matrix<float>) reader.ReadMatrix(new Matrix<float>(0, 0));

				if (user_factors.NumberOfColumns != item_factors.NumberOfColumns)
					throw new IOException(
						string.Format(
							"Number of user and item factors must match: {0} != {1}",
							user_factors.NumberOfColumns, item_factors.NumberOfColumns));
				if (item_bias.Count != item_factors.dim1)
					throw new IOException(
						string.Format(
							"Number of items must be the same for biases and factors: {0} != {1}",
							item_bias.Count, item_factors.dim1));

				this.MaxUserID = user_factors.NumberOfRows - 1;
				this.MaxItemID = item_factors.NumberOfRows - 1;

				// assign new model
				if (this.num_factors != user_factors.NumberOfColumns)
				{
					Console.Error.WriteLine("Set num_factors to {0}", user_factors.NumberOfColumns);
					this.num_factors = user_factors.NumberOfColumns;
				}
				this.user_factors = user_factors;
				this.item_bias    = (float[]) item_bias;
				this.item_factors = item_factors;
			}
		}

		///
		public IList<Tuple<int, float>> ScoreItems(IList<int> accessed_items, IList<int> candidate_items)
		{
			var user_factors = FoldIn(accessed_items);

			var scored_items = new Tuple<int, float>[candidate_items.Count];
			for (int i = 0; i < scored_items.Length; i++)
			{
				int item_id = candidate_items[i];
				float score = item_bias[item_id] + item_factors.RowScalarProduct(item_id, user_factors);
				scored_items[i] = Tuple.Create(item_id, score);
			}
			return scored_items;
		}

		///
		float[] FoldIn(IList<int> accessed_items)
		{
			var positive_items = new HashSet<int>(accessed_items);

			// initialize user parameters
			var user_factors = new float[NumFactors];
			user_factors.InitNormal(InitMean, InitStdDev);

			// perform training
			for (uint it = 0; it < NumIter; it++)
				IterateUser(positive_items, user_factors);

			return user_factors;
		}

		void IterateUser(ISet<int> user_items, IList<float> user_factors)
		{
			if (WithReplacement) // case 1: item sampling with replacement
			{
				throw new NotImplementedException();
			}
			else // case 2: item sampling without replacement
			{
				int num_pos_events = user_items.Count;
				int pos_item_id, neg_item_id;

				for (int i = 0; i < num_pos_events; i++)
				{
					SampleItemPair(user_items, out pos_item_id, out neg_item_id);
					// TODO generalize and call UpdateFactors -- need to represent factors as arrays, not matrices for this
					double x_uij = item_bias[pos_item_id] - item_bias[neg_item_id] + DataType.VectorExtensions.ScalarProduct(user_factors, DataType.MatrixExtensions.RowDifference(item_factors, pos_item_id, item_factors, neg_item_id));
					double one_over_one_plus_ex = 1 / (1 + Math.Exp(x_uij));

					// adjust factors
					for (int f = 0; f < num_factors; f++)
					{
						float w_uf = user_factors[f];
						float h_if = item_factors[pos_item_id, f];
						float h_jf = item_factors[neg_item_id, f];

						double update = (h_if - h_jf) * one_over_one_plus_ex - reg_u * w_uf;
						user_factors[f] = (float) (w_uf + learn_rate * update);
					}
				}
			}
		}

		///
		public override string ToString()
		{
			return string.Format(
				CultureInfo.InvariantCulture,
				"{0} num_factors={1} bias_reg={2} reg_u={3} reg_i={4} reg_j={5} num_iter={6} learn_rate={7} uniform_user_sampling={8} with_replacement={9} update_j={10}",
				this.GetType().Name, num_factors, BiasReg, reg_u, reg_i, reg_j, NumIter, learn_rate, UniformUserSampling, WithReplacement, UpdateJ);
		}
	}


    class UserItemEP
    {
        int idx, userID, itemID;
        double ep, prob1, prob2; 

        public UserItemEP(int idx, int userID, int itemID, double ep, double prob1, double prob2)
        {
            this.idx = idx;
            this.userID = userID;
            this.itemID = itemID;
            this.ep = ep;
            this.prob1 = prob1;
            this.prob2 = prob2;
        }

        public int IDX
        {
            get { return idx; }
            set { idx = value; }
        }
        public int UserID
        {
            get { return userID; }
            set { userID = value; }
        }
        public int ItemID
        {
            get { return itemID; }
            set { itemID = value; }
        }
        public double EP
        {
            get { return ep; }
            set { ep = value; }
        }
        public double Prob1
        {
            get { return prob1; }
            set { prob1 = value; }
        }
        public double Prob2
        {
            get { return prob2; }
            set { prob2 = value; }
        }
    }


    class UserItemDate
    {
        int idx, userID, itemID;
        ArrayList dateList;

        public UserItemDate(int idx, int userID, int itemID, ArrayList dateList)
        {
            this.idx = idx;
            this.userID = userID;
            this.itemID = itemID;
            this.dateList = dateList;
        }

        public int IDX
        {
            get { return idx; }
            set { idx = value; }
        }
        public int UserID
        {
            get { return userID; }
            set { userID = value; }
        }
        public int ItemID
        {
            get { return itemID; }
            set { itemID = value; }
        }
        public ArrayList DateList
        {
            get { return dateList; }
            set { dateList = value; }
        }
    }
}
