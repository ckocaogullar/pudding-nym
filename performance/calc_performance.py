'''

Calculates the results from latency and throughput measurements, and generates plots for them.
You might need to edit the code to generate plots for different types of messages; see relevant comments for more details

This script should be run with different system arguments for latency and throughput calulcations:

    python calc_performance.py <time_of_measurement> latency <num_of_messages_for_run_1> <num_of_messages_for_run_2> <num_of_messages_for_run_3> ...
    
    python calc_performance.py <time_of_measurement_with_surb> <time_of_measurement_without_surb> throughput <num_of_messages_for_run_1> <num_of_messages_for_run_2> <num_of_messages_for_run_3> ...

'''

import json
import sys
import logging
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import seaborn as sns
import pandas as pd
import os
import config
from scipy import stats

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

# Check and save system argument
assert len(
    sys.argv) >= 2, "Performance calculator must take at least two parameter: name of the log file(s), and the number(s) of messages for each trial"
assert sys.argv[2] in ['throughput', 'latency',
                       "load"], "Test type must be 'throughput', 'latency' or 'load'"

# Set constants
TEST_TYPE = sys.argv[2]
print(TEST_TYPE)
LOG_PATH = 'test' + '_logs/' + \
    sys.argv[2] if TEST_TYPE == 'latency' else None
WITH_SURB_LOG_PATH = 'test' + '_logs/' + sys.argv[1] + '/with_surb'
WITHOUT_SURB_LOG_PATH = 'test' + '_logs/' + sys.argv[1] + '/without_surb'


def calculate_latency(start_dict, end_dict):
    latency_arr = []
    for i in range(len(start_dict)):
        if str(i) in end_dict and str(i) and start_dict and end_dict[str(i)] > 0 and start_dict[str(i)] > 0:
            latency_arr.append(end_dict[str(i)] - start_dict[str(i)])
            #assert end_dict[str(i)] - start_dict[str(i)] > 0, i
    return np.array(latency_arr)


def plot_latency(arr):
    x_arr = [int(sys.argv.index(message_num)) - 3] * len(arr)
    plt.scatter(np.array(x_arr), arr)
    return x_arr


# Scatter plot trendline
def plot_best_fit(x, y):
    m, b = np.polyfit(x, y, 1)
    plt.plot(x, m*x + b, color='purple')
    return m*x + b


def calculate_throughput(data, tag, message_num):
    if tag in data:
        if tag == 'received_surb_time':
            return float(message_num) / float(data[tag][1])
        return float(message_num) / float(data[tag])


def calculate_loss(real_data, expected_data):
    return round((float(real_data) / float(expected_data)) * 100, 1)


def percentage(part, whole):
    return 100 * float(part)/float(whole)


# def prep_data_for_scatterplot(cumulative_x_data, cumulative_y_data, local_data, filter=None):
#     cumulative_y_data += list(local_data)
#     cumulative_x_data += plot_latency(local_data)

def prep_data_for_linegraph(dict, filtered=False):
    x_data = list()
    y_data = list()

    for freq in dict:
        x_data.append(float(freq))
        if filtered:
            y_data.append(stats.trim_mean([float(x) for x in dict[freq]], 0.1))
        else:
            print('Creating unfiltered lineplot')
            y_data.append(np.average([float(x) for x in dict[freq]]))

    return x_data, y_data


def prep_data_for_loss_graph(dict, num_total_messages):
    x_data = list()
    y_data = list()

    for freq in dict:
        x_data.append(float(freq))
        y_data.append((len(dict[freq]) / num_total_messages) * 100)

    return x_data, y_data


def prep_data_for_scatterplot(dict, filtered=False):
    x_data = list()
    y_data = list()
    for freq in dict:
        data = np.array(dict[freq])
        mean = np.mean(data)
        standard_deviation = np.std(data)
        for l in dict[freq]:
            if not filtered or (filtered and is_outlier(l, mean, standard_deviation)):
                x_data.append(float(freq))
                y_data.append(l)
    return x_data, y_data


def prep_data_for_boxplot(dict):
    y_data = list()
    for freq in dict:
        data = list()
        for l in dict[freq]:
            data.append(l)
        y_data.append(data)
    return y_data


def prep_data_for_boxlot_or_table(cumulative_y_data, local_data):
    cumulative_y_data.append(list(local_data))


def generate_poisson_distribution(delay, size):
    # return stats.poisson.rvs(mu=1000/(delay*hops), size=5000)
    return list(stats.poisson.rvs(mu=delay, size=size))

# Filters the outliers from an array, i.e. elements that are 2 or more standard deviations far from mean


def is_outlier(data, mean, standard_deviation):
    distance_from_mean = abs(data - mean)
    max_deviations = 3
    return distance_from_mean < max_deviations * standard_deviation


def filter_outliers(data):
    data = np.array(data)
    mean = np.mean(data)
    standard_deviation = np.std(data)
    distance_from_mean = abs(data - mean)
    max_deviations = 2
    not_outlier = distance_from_mean < max_deviations * standard_deviation
    return data[not_outlier]


def prep_data_for_throughput(path):
    sender_data_x = list()
    sender_data_y = list()
    receiver_data_x = list()
    receiver_data_y = list()

    message_nums = os.listdir(WITH_SURB_LOG_PATH)
    for message_num in message_nums:
        try:
            message_num = int(message_num)
            sender_data_x.append(int(message_num))
            receiver_data_x.append(int(message_num))
            with open(path + '/' + str(message_num) + '/sender.json', 'r') as file:
                data = json.load(file)
                sender_data_y.append(
                    data['sent_time'] / len(data['message_timings']))

            with open(path + '/' + str(message_num) + '/receiver.json', 'r') as file:
                data = json.load(file)
                receiver_data_y.append(
                    data['received_time'] / len(data['message_timings']))
        except Exception as e:
            print(e)

    return [sender_data_x, sender_data_y], [receiver_data_x, receiver_data_y]


def prep_data_from_clients(first_freq, last_freq, freq_step, surb=False):
    sent_data = dict()
    original_payload = dict()
    tag_payload = dict()
    tag_time = dict()
    received_data = dict()
    latency_data = dict()
    missed_packets = dict()
    surb_path = 'with_surb/' if surb else 'no_surb/'

    # Read and store data from the sender logs
    for freq in range(first_freq, last_freq + freq_step, freq_step):
        freq = str(freq)
        path = "client_performance/" + surb_path
        sent_data[freq] = dict()
        received_data[freq] = dict()
        latency_data[freq] = list()
        original_payload[freq] = dict()
        tag_payload[freq] = dict()
        tag_time[freq] = dict()
        missed_packets[freq] = list()

        with open(path + 'sender-' + freq + '.txt') as file:
            lines = file.readlines()
            for line in lines:
                line = line.replace('\n', "")
                line = line.split(';')
                if line[0] == 'original_payload':
                    original = line[1].split('payload:')[
                        1].replace('}', '').strip()
                    payload = line[2].split('payload:')[1].strip()
                    original_payload[freq][payload] = original
                elif line[0] == 'tag_payload':
                    tag = line[1].replace('tag:', '').strip()
                    payload = line[2].replace('payload:', '').strip()
                    tag_payload[freq][tag] = payload
                elif line[0] == 'tag_time':
                    tag = line[1].replace('tag:', '').strip()
                    time = line[2].replace('time:', '').strip()
                    tag_time[freq][tag] = time
                else:
                    print(
                        'Problem with reading sender data from client: {}'.format(line))

        with open(path + 'receiver-' + freq + '.txt') as file:
            lines = file.readlines()
            for line in lines:
                line = line.replace('\n', "")
                line = line.split(';')
                original = line[0].split('payload:')[
                    1].replace('}', '').strip()
                time = line[1].replace('time:', '').strip()
                received_data[freq][original] = time

    # Match sent packet information among the prepared dicts and store which packet (i.e. payload) was sent when
    for freq in range(first_freq, last_freq + freq_step, freq_step):
        freq = str(freq)
        for tag in tag_time[freq]:
            time = tag_time[freq][tag]
            payload = tag_payload[freq][tag]
            try:
                original = original_payload[freq][payload]
                sent_data[freq][original] = time
            except:
                # print('Original matching the payload not found:', payload)
                pass

    # calculate latency for the newly matched data
    for freq in range(first_freq, last_freq + freq_step, freq_step):
        freq = str(freq)
        sent_data[freq] = dict(
            sorted(sent_data[freq].items(), key=lambda item: item[1]))
        for order, original in enumerate(sent_data[freq].keys()):
            if original in received_data[freq]:
                assert int(received_data[freq][original]) - \
                    int(sent_data[freq][original]) > 0, 'Message received before it was sent. Key: {}, Received: {}, Sent: {}, Difference: {}'.format(original,
                                                                                                                                                      received_data[freq][original], sent_data[freq][original], int(received_data[freq][original]) - int(sent_data[freq][original]))
                latency_data[freq].append(int(received_data[freq][original]) -
                                          int(sent_data[freq][original]))
            else:
                missed_packets[freq].append(order)

    return latency_data, missed_packets


def prep_data_for_latency(path):
    latency_data = dict()
    missed_packets = dict()
    with open(path + '/sender.json', 'r') as file:
        sender_data = json.load(file)

    with open(path + '/receiver.json', 'r') as file:
        receiver_data = json.load(file)

    for freq in sender_data['sent_text_time']:
        if freq != '1.0':
            for message_seq in sender_data['sent_text_time'][freq]:
                try:
                    if freq not in latency_data:
                        latency_data[freq] = list()
                    latency = receiver_data['received_text_time'][freq][message_seq] - \
                        sender_data['sent_text_time'][freq][message_seq]
                    latency_data[freq].append(latency)
                except:
                    print('Message no {}, freq {} was lost on its way to receiver'.format(
                        message_seq, freq))
                    try:
                        missed_packets[freq].append(message_seq)
                    except:
                        missed_packets[freq] = list()
                        missed_packets[freq].append(message_seq)

    return latency_data, missed_packets


def prep_data_for_load(path):
    latency_data = list()
    missed_packets = list()
    freq = str(config.INIT_FREQ)
    with open(path + '/sender.json', 'r') as file:
        sender_data = json.load(file)

    with open(path + '/receiver.json', 'r') as file:
        receiver_data = json.load(file)

        for message_seq in sender_data['sent_text_time'][freq]:
            try:
                latency = receiver_data['received_text_time'][freq][message_seq] - \
                    sender_data['sent_text_time'][freq][message_seq]
                latency_data.append(latency)
            except:
                print('Message no {}, freq {} was lost on its way to receiver'.format(
                    message_seq, freq))
                missed_packets.append(message_seq)

    return latency_data


if TEST_TYPE == 'latency':
    font = {'family': 'normal',
            'weight': 'bold',
            'size': 16}

    plt.rc('font', **font)

    WITHOUT_SURB_LOG_PATH = "client_performance/no_surb"
    # with_surb_latency_data, with_surb_missed_packets = prep_data_for_latency(
    #     WITH_SURB_LOG_PATH)

    # without_surb_latency_data, without_surb_missed_packets = prep_data_for_latency(
    #     WITHOUT_SURB_LOG_PATH)

    without_surb_latency_data, without_surb_missed_packets = prep_data_from_clients(
        10, 10, 50)

    for freq in without_surb_latency_data:
        print(freq)
        print(np.average(without_surb_latency_data[freq]))
        print(np.std(without_surb_latency_data[freq]))

    # print(without_surb_latency_data)
    plt.grid(visible=True, axis='y')
    plt.figure(figsize=(8, 8))

    ### BOXPLOT ###

    y_data = prep_data_for_boxplot(without_surb_latency_data)

    plt.title("Latency of sending a non-SURB reply")
    plt.xlabel('Message frequency (message/sec)')
    plt.ylabel('Latency per message (ms)')

    plt.boxplot(y_data, labels=list(without_surb_latency_data.keys()))
    plt.savefig(WITHOUT_SURB_LOG_PATH + '/boxplot.pdf')

    plt.clf()

    ### TIME SERIES GRAPH ###

    # Modify the array to pick which frequencies you would like to show in the plot.
    selected_freqs = ['10']

    # With SURB
    # Filtered
    # plt.title("Time-series graph of latency based on message order (SURB)")
    # plt.xlabel('Message order')
    # plt.ylabel('Latency (sec)')
    # for freq in with_surb_latency_data:
    #     if freq in selected_freqs:
    #         plt.plot(filter_outliers(
    #             with_surb_latency_data[freq]), label=int(float(freq)))

    # plt.legend(loc="upper left", title='frequencies')
    # plt.savefig(WITH_SURB_LOG_PATH + '/time-series-filtered.pdf')

    # plt.clf()

    # # Unfiltered
    # plt.title("Time-series graph of latency based on message order (SURB)")
    # plt.xlabel('Message order')
    # plt.ylabel('Latency (sec)')
    # for freq in with_surb_latency_data:
    #     if freq in selected_freqs:
    #         plt.plot(with_surb_latency_data[freq], label=int(float(freq)))

    # plt.legend(loc="upper left", title='frequencies')
    # plt.savefig(WITH_SURB_LOG_PATH + '/time-series.pdf')

    # plt.clf()

    # Without SURB
    # plt.title("Time-series graph of latency - 10 msg/sec")
    plt.xlabel('Message order')
    plt.ylabel('Latency (sec)')
    for freq in selected_freqs:
        plt.plot(without_surb_latency_data[freq], label=int(float(freq)))

    # plt.legend(loc="upper left", title='frequencies')
    plt.savefig(WITHOUT_SURB_LOG_PATH + '/time-series.pdf')
    plt.clf()

    ###  SCATTER PLOT ###

    # # With SURB
    # Filtered
    # x_data, y_data = prep_data_for_scatterplot(with_surb_latency_data, True)

    # plt.title("Latency of sending a SURB message")
    # plt.xlabel('Message frequency (message/sec)')
    # plt.ylabel('Latency per message (sec)')

    # plt.xticks(x_data, rotation=45)
    # plt.scatter(x_data, y_data)
    # plt.savefig(WITH_SURB_LOG_PATH + '/scatterplot-filtered.pdf')

    # # Unfiltered
    # x_data, y_data = prep_data_for_scatterplot(with_surb_latency_data)

    # plt.title("Latency of sending a SURB message")
    # plt.xlabel('Message frequency (message/sec)')
    # plt.ylabel('Latency per message (sec)')

    # plt.xticks(x_data, rotation=45)
    # plt.scatter(x_data, y_data)
    # plt.savefig(WITH_SURB_LOG_PATH + '/scatterplot.pdf')

    # plt.clf()

    # Without SURB
    # x_data, y_data = prep_data_for_scatterplot(without_surb_latency_data)

    # plt.title("Latency of sending a non-SURB reply")
    # plt.xlabel('Message frequency (message/sec)')
    # plt.ylabel('Latency per message (sec)')

    # plt.xticks(x_data, rotation=45)
    # plt.scatter(x_data, y_data)
    # plt.savefig(WITHOUT_SURB_LOG_PATH + '/scatterplot.pdf')

    # plt.clf()

    ### LINE GRAPH ###

    # With SURB
    # Filtered
    # x_data, y_data = prep_data_for_linegraph(with_surb_latency_data, True)

    # plt.title("Average latency of sending a SURB message")
    # plt.xlabel('Message frequency (message/sec)')
    # plt.ylabel('Average latency per message (secs)')

    # plt.plot(x_data, y_data)
    # # plt.xticks(x_data, rotation=45)
    # plt.savefig(WITH_SURB_LOG_PATH + '/linegraph-filtered.pdf')

    # plt.clf()

    # # Unfiltered
    # x_data, y_data = prep_data_for_linegraph(with_surb_latency_data)

    # plt.title("Average latency of sending a SURB message")
    # plt.xlabel('Message frequency (message/sec)')
    # plt.ylabel('Average latency per message (secs)')

    # plt.plot(x_data, y_data)
    # # plt.xticks(x_data, rotation=45)
    # plt.savefig(WITH_SURB_LOG_PATH + '/linegraph.pdf')

    # plt.clf()

    # Without SURB
    # x_data, y_data = prep_data_for_linegraph(without_surb_latency_data, True)

    # plt.title("Average latency of sending a non-SURB reply")
    # plt.xlabel('Message frequency (message/sec)')
    # plt.ylabel('Average latency per message (secs)')

    # plt.plot(x_data, y_data)
    # # plt.xticks(x_data, rotation=45)
    # plt.savefig(WITHOUT_SURB_LOG_PATH + '/linegraph.pdf')

    # plt.clf()

    ### LOST PACKETS ###

    # With SURB
    # x_data, y_data = prep_data_for_loss_graph(with_surb_missed_packets, 500)

    # # Uncomment to filter out the outliers
    # x_data = filter_outliers(x_data)

    # plt.title("Percentage of lost SURB packets")
    # plt.xlabel('Message frequency (message/sec)')
    # plt.ylabel('Percentage')

    # plt.plot(x_data, y_data)
    # plt.savefig(WITH_SURB_LOG_PATH + '/lost_packets.pdf')

    # plt.clf()

    # Without SURB
    # x_data, y_data = prep_data_for_loss_graph(without_surb_missed_packets, 500)
    # plt.title("Percentage of lost non-SURB packets")
    # plt.xlabel('Message frequency (message/sec)')
    # plt.ylabel('Percentage')

    # plt.plot(x_data, y_data)
    # plt.savefig(WITHOUT_SURB_LOG_PATH + '/lost_packets.pdf')

    ### HISTOGRAM ###
    histogram_freq = '10'
    # # Without SURB
    histogram_data = list(filter(lambda latency: latency <
                                 1000, without_surb_latency_data[freq]))

    # histogram_data = without_surb_latency_data[freq]

    plt.figure(figsize=(15, 5))
    # plt.title("Latency distribution (10 msg/sec)")
    plt.xlabel('Latency')
    plt.ylabel('Density')

    a = 3
    scale = 50
    # x = np.arange(min(histogram_data), max(histogram_data), 1)
    x = np.arange(0, 1000, 1)
    histogram_data.sort()
    print(histogram_data)
    fit_alpha, fit_loc, fit_beta = stats.gamma.fit(histogram_data)
    print("fit_alpha, fit_loc, fit_beta", fit_alpha, fit_loc, fit_beta)
    sns.distplot(histogram_data, fit=stats.gamma, color="b", bins=np.arange(
        min(histogram_data), max(histogram_data), 1.0), kde=True, kde_kws={"color": "b", "lw": 2, "label": "KDE of measured data"}, fit_kws={"color": "r", "lw": 2, "label": "real (fitted) Gamma distribution", "linestyle": "--"})
    sns.lineplot(x, stats.gamma.pdf(x, a, scale=scale), linewidth=2,
                 label='theoretical Gamma distribution', linestyle="--", color="g")
    plt.legend()
    plt.savefig(WITHOUT_SURB_LOG_PATH + '/histogram.pdf')

    # plt.show()

    # With SURB
    # with_surb_latency_data = prep_data_for_load(WITH_SURB_LOG_PATH)
    # print('number of unlost surb replies', len(with_surb_latency_data))

    # plt.figure(figsize=(10, 10))
    # plt.title("Distribution of per-message latency for 10000 SURB replies in total")
    # plt.xlabel('Latency (sec)')
    # plt.ylabel('Count')
    # plt.hist(with_surb_latency_data, bins=np.arange(
    #     min(with_surb_latency_data), max(with_surb_latency_data), 1.0))
    # plt.savefig(WITH_SURB_LOG_PATH + '/histogram.pdf')

    plt.clf()


elif TEST_TYPE == 'load':
    ### HISTOGRAM ###
    # Without SURB
    without_surb_latency_data = prep_data_for_load(WITHOUT_SURB_LOG_PATH)
    plt.figure(figsize=(10, 10))
    plt.title(
        "Distribution of per-message latency for 10000 non-SURB messages in total")
    plt.xlabel('latency (sec)')
    plt.ylabel('Count')
    plt.hist(without_surb_latency_data, bins=np.arange(
        min(without_surb_latency_data), max(without_surb_latency_data), 1.0))
    plt.savefig(WITHOUT_SURB_LOG_PATH + '/histogram.pdf')

    # With SURB
    with_surb_latency_data = prep_data_for_load(WITH_SURB_LOG_PATH)
    print('number of unlost surb replies', len(with_surb_latency_data))

    plt.figure(figsize=(10, 10))
    plt.title("Distribution of per-message latency for 10000 SURB replies in total")
    plt.xlabel('Latency (sec)')
    plt.ylabel('Count')
    plt.hist(with_surb_latency_data, bins=np.arange(
        min(with_surb_latency_data), max(with_surb_latency_data), 1.0))
    plt.savefig(WITH_SURB_LOG_PATH + '/histogram.pdf')

    plt.clf()

elif TEST_TYPE == 'throughput':
    #  With SURB
    sender_data, receiver_data = prep_data_for_throughput(WITH_SURB_LOG_PATH)
    print(sender_data)

    plt.title("Throughput of sending SURB replies")
    plt.xlabel('Number of total messages sent')
    plt.ylabel('Throughput (msg/sec)')
    plt.plot(sender_data[0], sender_data[1])

    plt.savefig(WITH_SURB_LOG_PATH + '/throughput-sender-linegraph.pdf')

    plt.clf()

    plt.title("Throughput of receiving SURB replies")
    plt.xlabel('Number of total messages sent')
    plt.ylabel('Throughput (msg/sec)')
    plt.plot(receiver_data[0], receiver_data[1])

    plt.savefig(WITH_SURB_LOG_PATH + '/throughput-receiver-linegraph.pdf')

    # plt.clf()

    #  Without SURB
    sender_data, receiver_data = prep_data_for_throughput(
        WITHOUT_SURB_LOG_PATH)
    print(sender_data)
    # Modify according to the graph
    plt.title("Throughput of sending non-SURB messages")
    plt.xlabel('Number of total messages sent')
    plt.ylabel('Throughput (msg/sec)')
    plt.plot(sender_data[0], sender_data[1])

    plt.savefig(WITHOUT_SURB_LOG_PATH + '/throughput-sender-linegraph.pdf')

    plt.clf()

    plt.title("Throughput of receiving non-SURB messages")
    plt.xlabel('Number of total messages sent')
    plt.ylabel('Throughput (msg/sec)')
    plt.plot(receiver_data[0], receiver_data[1])

    plt.savefig(WITHOUT_SURB_LOG_PATH + '/throughput-receiver-linegraph.pdf')

elif TEST_TYPE == 'x':
    # fig, (ax1, ax2, ax3) = plt.subplots(1, 3)

    # To draw the best fit lines for each graph, we need to accumulate the data from different runs. (Not a pretty or smart way, but OK for now)
    all_x_surb_reply_latency = []
    all_y_surb_reply_latency = []
    all_x_text_latency_without_surb = []
    all_y_text_latency_without_surb = []
    all_x_text_latency_with_surb = []
    all_y_text_latency_with_surb = []

    for message_num in sys.argv[3:]:
        with open(LOG_PATH + '/' + message_num + '/sender.json', 'r') as file:
            sender_data = json.load(file)

        with open(LOG_PATH + '/' + message_num + '/receiver.json', 'r') as file:
            receiver_data = json.load(file)

        # SURB Reply latency
        surb_reply_latency = calculate_latency(
            receiver_data['sent_surb_reply_text_time'], sender_data['received_surb_reply_text_time'])
        print('surb reply latency {}'.format(surb_reply_latency))

        # Uncomment for unfiltered boxplot OR table creation
        # prep_data_for_boxlot_or_table(all_y_surb_reply_latency, surb_reply_latency)

        # Uncomment for scatter plot
        prep_data_for_scatterplot(
            all_x_surb_reply_latency, all_y_surb_reply_latency, surb_reply_latency)

        ####################################################
        # Text message (no SURB attached) latency
        text_latency_without_surb = calculate_latency(
            sender_data['sent_text_without_surb_time'], receiver_data['received_text_time'])

        # Uncomment for unfiltered boxplot OR table creation
        # prep_data_for_boxlot_or_table(all_y_text_latency_without_surb, text_latency_without_surb)

        # Uncomment for scatter plot
        # prep_data_for_scatterplot(all_x_text_latency_without_surb,
        #                           all_y_text_latency_without_surb, text_latency_without_surb)

        ####################################################
        # Text message (SURB attached) latency
        text_latency_with_surb = calculate_latency(
            sender_data['sent_text_with_surb_time'], receiver_data['received_surb_text_time'])

        # Uncomment for unfiltered boxplot OR table creation
        # prep_data_for_boxlot_or_table(all_y_text_latency_with_surb, text_latency_with_surb)

        # Uncomment for scatter plot
        # prep_data_for_scatterplot(
        #     all_x_text_latency_with_surb, all_y_text_latency_with_surb, text_latency_with_surb)

    ##### GRAPHS #####
    plt.grid(visible=True, axis='y')

    # Modify according to the graph
    plt.title("Latency of sending a SURB reply")
    plt.xlabel('Number of total messages sent')
    plt.ylabel('Latency per message (secs)')
    plot_name = '/surb-scatterplot.pdf'
    x_data = all_x_surb_reply_latency
    y_data = all_y_surb_reply_latency

    # Uncomment for boxplot
    # plt.boxplot(y_data, labels=sys.argv[3:])

    # Uncomment  for scatter plot
    ticks = range(len(sys.argv[3:]))
    # Offests for the best fit line intersection labels, edit if needed
    x_offset = 0.03
    y_offset = 0.3
    plt.xticks(ticks=ticks, labels=sys.argv[3:])
    best_fit = plot_best_fit(np.array(x_data),
                             np.array(y_data))
    for count, message_num in enumerate(sys.argv[3:]):
        best_fit_point = round(best_fit[x_data.index(count)], 2)
        if count < len(sys.argv[3:]) - 1:
            plt.text(ticks[count] + x_offset, best_fit_point + y_offset, best_fit_point,
                     color='purple', va='center')
        else:
            plt.text(ticks[count] - x_offset, best_fit_point + y_offset, best_fit_point,
                     color='purple', va='center', ha='right')
    purple_patch = mpatches.Patch(color='purple', label='best fit line')
    loss_legend = plt.legend(loc='upper left', handles=[purple_patch])

    plt.savefig(LOG_PATH + plot_name)

    ##### TABLES #####
    # Table structure is:
    #                       Average | StdDev | Min | Max | Loss
    # <msg type>_<msg num>
    # <msg type>_<msg num>
    #          ...

    # table = dict()
    # table['Average'] = list()
    # table['StdDev'] = list()
    # table['Min'] = list()
    # table['Max'] = list()
    # table['Loss'] = list()
    # table['Average'].extend(np.average(latency)
    # for latency in all_y_surb_reply_latency)
    # table['Average'].extend(np.average(latency)
    #                         for latency in all_y_text_latency_with_surb)
    # table['Average'].extend(np.average(latency)
    #                         for latency in all_y_text_latency_without_surb)
    # table['StdDev'].extend(np.std(latency)
    #    for latency in all_y_surb_reply_latency)
    # table['StdDev'].extend(np.std(latency)
    #                        for latency in all_y_text_latency_with_surb)
    # table['StdDev'].extend(np.std(latency)
    #                        for latency in all_y_text_latency_without_surb)
    # table['Min'].extend(np.min(latency)
    # for latency in all_y_surb_reply_latency)
    # table['Min'].extend(np.min(latency)
    #                     for latency in all_y_text_latency_with_surb)
    # table['Min'].extend(np.min(latency)
    #                     for latency in all_y_text_latency_without_surb)
    # table['Max'].extend(np.max(latency)
    # for latency in all_y_surb_reply_latency)
    # table['Max'].extend(np.max(latency)
    #                     for latency in all_y_text_latency_with_surb)
    # table['Max'].extend(np.max(latency)
    #                     for latency in all_y_text_latency_without_surb)
    # table['Loss'].extend(percentage(len(all_y_surb_reply_latency[i]),
    # sys.argv[3 + i])for i in range(len(all_y_surb_reply_latency)))
    # table['Loss'].extend(percentage(len(all_y_text_latency_with_surb[i]),
    #                                 sys.argv[3 + i])for i in range(len(all_y_text_latency_with_surb)))
    # table['Loss'].extend(percentage(len(all_y_text_latency_without_surb[i]),
    #                                 sys.argv[3 + i])for i in range(len(all_y_text_latency_without_surb)))
    # df = pd.DataFrame(table, index=['SURB_100', 'SURB_1000'])
    # df.to_csv(LOG_PATH + '/table.csv')

# Throughput
else:
    sent_text_with_surb_throughput_y = []
    sent_text_with_surb_throughput_x = []
    sent_text_without_surb_throughput_y = []
    sent_text_without_surb_throughput_x = []
    received_surb_reply_throughput_y = []
    received_surb_reply_throughput_x = []

    received_surb_text_throughput_y = []
    received_surb_text_throughput_x = []
    received_text_throughput_y = []
    received_text_throughput_x = []
    sent_surb_reply_throughput_y = []
    sent_surb_reply_throughput_x = []

    received_surb_loss = []

    logging.info("[PERFORMANCE_CALC] Throughput data:")
    for message_num in sys.argv[4:]:
        sender_data = dict()
        receiver_data = dict()
        with open(WITH_SURB_LOG_PATH + '/' + message_num + '/sender.json', 'r') as file:
            sender_data.update(json.load(file))

        with open(WITHOUT_SURB_LOG_PATH + '/' + message_num + '/sender.json', 'r') as file:
            sender_data.update(json.load(file))

        with open(WITH_SURB_LOG_PATH + '/' + message_num + '/receiver.json', 'r') as file:
            receiver_data.update(json.load(file))

        with open(WITHOUT_SURB_LOG_PATH + '/' + message_num + '/receiver.json', 'r') as file:
            receiver_data.update(json.load(file))

        sent_text_with_surb_throughput_y.append(calculate_throughput(
            sender_data, 'sent_text_with_surb_time', message_num))
        sent_text_with_surb_throughput_x.append(int(message_num))

        sent_text_without_surb_throughput_y.append(calculate_throughput(
            sender_data, 'sent_text_without_surb_time', message_num))
        sent_text_without_surb_throughput_x.append(int(message_num))

        received_surb_text_throughput_y.append(calculate_throughput(
            receiver_data, 'received_text_with_surb_time', message_num))
        received_surb_text_throughput_x.append(int(message_num))

        received_text_throughput_y.append(calculate_throughput(
            receiver_data, 'received_text_without_surb_time', message_num))
        received_text_throughput_x.append(int(message_num))

        sent_surb_reply_throughput_y.append(calculate_throughput(
            receiver_data, 'sent_surb_time', message_num))
        sent_surb_reply_throughput_x.append(int(message_num))

        received_surb_reply_throughput_y.append(calculate_throughput(
            sender_data, 'received_surb_time', sender_data['received_surb_time'][0]))
        received_surb_reply_throughput_x.append(int(message_num))

        received_surb_loss.append(calculate_loss(
            sender_data['received_surb_time'][0], message_num))

    # Sent messages plot
    fig, ax = plt.subplots(figsize=(15, 8))
    plt.plot(sent_text_with_surb_throughput_x, sent_text_with_surb_throughput_y,
             label='text message (SURB attached)')
    plt.plot(sent_text_without_surb_throughput_x, sent_text_without_surb_throughput_y,
             label='text message (no SURB attached)')
    plt.plot(sent_surb_reply_throughput_x, sent_surb_reply_throughput_y,
             label='SURB reply - delivered packets')
    plt.legend()
    plt.grid(visible=True, axis='y')
    plt.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    plt.title('Throughput: Sending messages')
    plt.xlabel('Number of messages')
    plt.ylabel('Throughput (msg/sec)')
    ax = plt.gca()
    plt.xticks([100, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500,
                5000, 5500, 6000, 6500, 7000, 7500, 8000, 8500, 9000, 9500, 10000], rotation=90)
    plt.savefig(TEST_TYPE + '_logs/' + sys.argv[1] + '/sent_text_plot.pdf')

    plt.clf()

    # Received messages plot
    fig, ax = plt.subplots(figsize=(15, 8))
    ax.set_ylim(0, 20)
    plt.title('Throughput: Receiving messages')
    l1 = plt.plot(received_surb_text_throughput_x, received_surb_text_throughput_y,
                  label='text message (SURB attached)')
    l2 = plt.plot(received_text_throughput_x, received_text_throughput_y,
                  label='text message (no SURB attached)')
    l3 = plt.plot(received_surb_reply_throughput_x, received_surb_reply_throughput_y,
                  label='reply message using SURB')
    yellow_patch = mpatches.Patch(
        color='green', label='% received SURB replies')
    loss_legend = plt.legend(loc=(0.803, 0.13), handles=[yellow_patch])
    print(received_surb_reply_throughput_y)
    plt.legend(loc='lower right')
    plt.gca().add_artist(loss_legend)
    plt.grid(visible=True)
    plt.title('Throughput: Receiving messages')
    plt.xlabel('Number of messages')
    plt.ylabel('Throughput (msg/sec)')
    plt.xticks([100, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500,
                5000, 5500, 6000, 6500, 7000, 7500, 8000, 8500, 9000, 9500, 10000], rotation=90)

    # Draw boxes for received SURB message percentages
    for label, x, y in zip(received_surb_loss, received_surb_reply_throughput_x, received_surb_reply_throughput_y):
        plt.annotate(
            label,
            xy=(x, y), xytext=(x, 19.7),
            # xy=(x, y), xytext=(x, 9.8),
            textcoords='data', ha='center', va='top',
            bbox=dict(boxstyle='round,pad=0.5', fc='green', alpha=0.5),)
    plt.savefig(TEST_TYPE + '_logs/' + sys.argv[1] + '/received_text_plot.pdf')

    plt.clf()

    # Message Loss Plot
    fig, ax = plt.subplots(figsize=(15, 8))
    ax.set_ylim(60, 100)
    plt.plot(received_surb_reply_throughput_x, [
             100.0 - x for x in received_surb_loss])
    plt.grid(visible=True, axis='y')
    plt.title('Percentage of Message Loss on Receiving SURB Replies')
    plt.ylabel('Loss percentage')
    plt.xlabel('Number of SURB replies sent by the sender')
    plt.xticks([100, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500,
                5000, 5500, 6000, 6500, 7000, 7500, 8000, 8500, 9000, 9500, 10000], rotation=90)
    plt.savefig(TEST_TYPE + '_logs/' +
                sys.argv[1] + '/surb_reply_loss_plot.pdf')

    # Throughput statistics table
    table = dict()
    table['Average'] = list()
    table['StdDev'] = list()
    table['Min'] = list()
    table['Max'] = list()
    table['Loss'] = list()
    table['Average'].append(np.average(sent_surb_reply_throughput_y))
    table['Average'].append(np.average(sent_text_with_surb_throughput_y))
    table['Average'].append(np.average(sent_text_without_surb_throughput_y))
    table['StdDev'].append(np.std(sent_surb_reply_throughput_y))
    table['StdDev'].append(np.std(sent_text_with_surb_throughput_y))
    table['StdDev'].append(np.std(sent_text_without_surb_throughput_y))
    table['Min'].append(np.min(sent_surb_reply_throughput_y))
    table['Min'].append(np.min(sent_text_with_surb_throughput_y))
    table['Min'].append(np.min(sent_text_without_surb_throughput_y))
    table['Max'].append(np.max(sent_surb_reply_throughput_y))
    table['Max'].append(np.max(sent_text_with_surb_throughput_y))
    table['Max'].append(np.max(sent_text_without_surb_throughput_y))
    table['Average'].append(np.average(received_surb_reply_throughput_y))
    table['Average'].append(np.average(received_surb_text_throughput_y))
    table['Average'].append(np.average(received_text_throughput_y))
    table['StdDev'].append(np.std(received_surb_reply_throughput_y))
    table['StdDev'].append(np.std(received_surb_text_throughput_y))
    table['StdDev'].append(np.std(received_text_throughput_y))
    table['Min'].append(np.min(received_surb_reply_throughput_y))
    table['Min'].append(np.min(received_surb_text_throughput_y))
    table['Min'].append(np.min(received_text_throughput_y))
    table['Max'].append(np.max(received_surb_reply_throughput_y))
    table['Max'].append(np.max(received_surb_text_throughput_y))
    table['Max'].append(np.max(received_text_throughput_y))

    table['Loss'].extend([0, 0, 0, np.average(received_surb_loss), 0, 0])

    df = pd.DataFrame(table, index=['Sent_SURB_Reply', 'Sent_Text_With_SURB', 'Sent_Text_Without_SURB',
                                    'Received_SURB_Reply', 'Received_Text_With_SURB', 'Received_Text_Without_SURB'])
    df.to_csv(TEST_TYPE + '_logs/' + sys.argv[1] + '/table.csv')
