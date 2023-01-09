import pandas as pd
import math
from collections import defaultdict


def get_filtered_pg_dict(epg, thres_bIntv, thres_cnt):  # thres_bIntv = 30, thres_cnt = 10
    pg_dict = defaultdict(list)
    chan_dict = defaultdict(set)

    for idx, row in epg.iterrows():
        pg_id = int(row['program_id'])  # key of pg_dict
        channel = int(row['channel'])  # key of chan_dict

        s_date = row['startDate']
        e_date = row['endDate']

        bIntv_len = (row['endDate'] - row['startDate']).seconds / 60

        if bIntv_len >= thres_bIntv:
            bInfo = [s_date, e_date, channel]

            pg_dict[pg_id].append(bInfo)
            chan_dict[pg_id].add(channel)

    del_list = []

    for pg_id in pg_dict.keys():
        pg_cnt = len(pg_dict[pg_id])

        if pg_cnt < thres_cnt:
            del_list.append(pg_id)

    for del_id in del_list:
        del (pg_dict[del_id])
        del (chan_dict[del_id])

    if len(pg_dict.keys()) == len(chan_dict.keys()):
        print('Number of keys: {0}'.format(str(len(pg_dict.keys()))))
    else:
        print('Check Required')

    return pg_dict, chan_dict


def get_overlapped_value(pg_dict, chan_dict, tgt_id, thres_ovp, min_max_flag, entropy_flag):
    ts_list = pg_dict[tgt_id]
    chan_list = chan_dict[tgt_id]

    if entropy_flag:
        oth_chan_dict = defaultdict(dict)
    else:
        oth_chan_dict = defaultdict(set)

    for ts in ts_list:
        start = ts[0]
        end = ts[1]
        amount = (end - start).seconds / 60

        for oth_id in pg_dict.keys():
            if oth_id == tgt_id:
                continue

            oth_ts_list = pg_dict[oth_id]

            for oth_ts in oth_ts_list:
                oth_channel = oth_ts[2]
                if oth_channel in chan_list:
                    continue

                oth_start = oth_ts[0]
                oth_end = oth_ts[1]

                overlapped_start = start
                overlapped_end = end

                if oth_end < overlapped_start or oth_start > overlapped_end:
                    continue

                if oth_start > overlapped_start:
                    overlapped_start = oth_start
                if oth_end < overlapped_end:
                    overlapped_end = oth_end

                overlapped_amount = (overlapped_end - overlapped_start).seconds / 60

                if overlapped_amount > amount * thres_ovp:
                    if entropy_flag:
                        sub_dict = oth_chan_dict[oth_channel]
                        if oth_id in sub_dict.keys():
                            sub_dict[oth_id] += 1
                        else:
                            sub_dict[oth_id] = 1
                    else:
                        oth_chan_dict[oth_channel].add(oth_id)

    if entropy_flag:
        prob_sum = 0
        for chan_id in oth_chan_dict.keys():
            prob_sum += get_entropy_prob(oth_chan_dict[chan_id])
        tgt_prob = prob_sum / len(oth_chan_dict.keys())
    else:
        tgt_progs = 0
        for chan_id in oth_chan_dict.keys():
            prog_ids = oth_chan_dict[chan_id]
            tgt_progs += (len(prog_ids) / len(oth_chan_dict.keys()))

        if min_max_flag:
            tgt_prob = (tgt_progs - 1) / (len(ts_list) - 1)
        else:
            tgt_prob = tgt_progs / len(ts_list)


    return tgt_prob, oth_chan_dict


# Compute the probability reflecting with the value of entropy
def get_entropy_prob(c_dict):
    c_num = len(c_dict.keys())    # CAUTION: If c_num is equal to 1, max_H becomes 0
    b_count = 0

    for key in c_dict.keys():
        b_count += c_dict[key]

    prob = c_num / b_count
    # print('Probability before adjustment: {0}'.format(str(prob)))

    # Compute the maximum value of entropy
    log_sum = 0
    for i in range(c_num):
        log_sum += (1 / c_num * math.log(1 / c_num))
    max_H = -1 * log_sum

    # Compute the current value of entropy
    log_sum = 0
    for key in c_dict.keys():
        log_sum += ((c_dict[key] / b_count) * math.log(c_dict[key] / b_count))
    H = -1 * log_sum

    if max_H == 0:
        H_ratio = 1.0
    else:
        H_ratio = H / max_H
    # print('Value of entropy: {0}, {1} ({2}%)'.format(str(H), str(max_H), str(H / max_H * 100)))

    prob *= H_ratio
    # print('Probability after adjustment: {0}'.format(str(prob)))

    return prob


def write_file(result_list, output_file, entropy_flag):
    fout = open(output_file, 'w')

    for results in result_list:
        tgt_id = results[0]
        tgt_prob = results[1]
        fout.write(str(tgt_id) + '\t' + str(tgt_prob) + '\n')

        oth_chan_dict = results[2]
        for chan_key in oth_chan_dict.keys():
            fout.write(str(chan_key) + '\n')

            elem_str = ''
            if entropy_flag:
                sub_dict = oth_chan_dict[chan_key]
                for pg in sub_dict.keys():
                    elem_str += (str(pg) + ',')
                # print(elem_str)
            else:
                for pg in oth_chan_dict[chan_key]:
                    elem_str += (str(pg) + ',')

            fout.write(elem_str + '\n')

    fout.close()


# Main
def main():
    # Load watching-log file
    epg_path = 'E:\\hongkyun\\TVshow\\Data\\epg_df.df'
    epg = pd.read_pickle(epg_path)
    print('Reading complete: ' + epg_path)

    thres_bIntv = 30
    thres_cnt = 10
    pg_dict, chan_dict = get_filtered_pg_dict(epg, thres_bIntv, thres_cnt)

    min_max_flag = False
    entropy_flag = True
    thres_ovp = 0.5
    prob_list = []

    cnt = 0
    for tgt_id in pg_dict:
        if cnt > 2:
            break
        cnt += 1
        tgt_prob, oth_chan_dict = get_overlapped_value(pg_dict, chan_dict, tgt_id, thres_ovp, min_max_flag, entropy_flag)
        print('{0}. Target ID: {1} ({2})'.format(str(cnt), str(tgt_id), str(tgt_prob)))
        prob_list.append([tgt_id, tgt_prob, oth_chan_dict])

    file_path = '../results/1CV/'
    file_name = 'Analysis_overlapped_programs_chan'

    if min_max_flag:
        file_name += '_mmnorm'
    if entropy_flag:
        file_name += '_entropy'

    file_name += '.txt'
    write_file(prob_list, file_path + file_name, entropy_flag)

    print('Writing complete: ' + file_path + file_name)


if __name__ == '__main__':
    main()
