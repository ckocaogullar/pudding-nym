from distutils.log import set_verbosity
import json
import sys
import logging
from wsgiref.simple_server import sys_version
import matplotlib.pyplot as plt
import numpy as np
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

# Check and save system arguments
assert len(
    sys.argv) >= 2, "Performance calculator must take at least two parameter: name of the log file, and the number(s) of messages for each trial"
assert sys.argv[2] == 'throughput' or sys.argv[2] == 'latency', "Test type must be 'throughput' or 'latency'"

# Set constants
TEST_TYPE = sys.argv[2]
LOG_PATH = TEST_TYPE + '_logs/' + sys.argv[1]


def calculate_latency(start_dict, end_dict):
    latency_arr = []
    for i in range(len(start_dict)):
        if str(i) in end_dict and str(i) and start_dict and end_dict[str(i)] > 0 and start_dict[str(i)] > 0:
            latency_arr.append(end_dict[str(i)] - start_dict[str(i)])
            #assert end_dict[str(i)] - start_dict[str(i)] > 0, i
    return np.array(latency_arr)


def plot_latency(ax, arr):
    x_arr = [int(message_num)] * len(arr)
    ax.scatter(np.array(x_arr), arr)
    return x_arr


def plot_best_fit(ax, x, y):
    print('x is {}'.format(x))
    m, b = np.polyfit(x, y, 1)
    ax.plot(x, m*x + b)


if TEST_TYPE == 'latency':
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3)

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

        surb_reply_latency = calculate_latency(
            receiver_data['sent_surb_reply_text_time'], sender_data['received_surb_reply_text_time'])
        print('surb reply latency {}'.format(surb_reply_latency))
        all_y_surb_reply_latency += list(surb_reply_latency)
        all_x_surb_reply_latency += plot_latency(ax1, surb_reply_latency)

        text_latency_without_surb = calculate_latency(
            sender_data['sent_text_without_surb_time'], receiver_data['received_text_time'])
        all_y_text_latency_without_surb += list(text_latency_without_surb)
        all_x_text_latency_without_surb += plot_latency(
            ax2, text_latency_without_surb)

        text_latency_with_surb = calculate_latency(
            sender_data['sent_text_with_surb_time'], receiver_data['received_surb_text_time'])
        all_y_text_latency_with_surb += list(text_latency_with_surb)
        all_x_text_latency_with_surb += plot_latency(
            ax3, text_latency_with_surb)

    # Calculate and add best fit line. m is the slope, b is the intercept
    # print(all_x_surb_reply_latency)
    plot_best_fit(ax1, np.array(all_x_surb_reply_latency),
                  np.array(all_y_surb_reply_latency))
    plot_best_fit(ax2, np.array(all_x_text_latency_without_surb),
                  np.array(all_y_text_latency_without_surb))
    plot_best_fit(ax3, np.array(all_x_text_latency_with_surb),
                  np.array(all_y_text_latency_with_surb))

    plt.title("Latency")
    ax1.set_title("Text reply using SURB")
    ax2.set_title("Text message (no SURB attached)")
    ax3.set_title("Text message (SURB attached)")

    # plt.show()
    plt.savefig(LOG_PATH + '/plot.png')

else:
    fig, (ax1, ax2) = plt.subplots(1, 2)
    sent_text_with_surb_time_y = []
    sent_text_with_surb_time_x = []
    sent_text_without_surb_time_y = []
    sent_text_without_surb_time_x = []

    received_surb_text_time_y = []
    received_surb_text_time_x = []
    received_text_time_y = []
    received_text_time_x = []
    logging.info("[PERFORMANCE_CALC] Throughput data:")
    for message_num in sys.argv[3:]:
        with open(LOG_PATH + '/' + message_num + '/sender.json', 'r') as file:
            sender_data = json.load(file)

        with open(LOG_PATH + '/' + message_num + '/receiver.json', 'r') as file:
            receiver_data = json.load(file)

        print(receiver_data)
        print(sender_data)
        if 'sent_text_with_surb_time' in sender_data:
            logging.info(
                "{} secs to send messages *with* SURB".format(sender_data['sent_text_with_surb_time']))
            sent_text_with_surb_time_y.append(
                sender_data['sent_text_with_surb_time'] / int(message_num))
            sent_text_with_surb_time_x.append(int(message_num))

        elif 'sent_text_without_surb_time' in sender_data:
            logging.info("{} secs to send messages *without* SURB".format(
                sender_data['sent_text_without_surb_time']))

            sent_text_without_surb_time_y.append(
                sender_data['sent_text_with_surb_time'] / int(message_num))
            sent_text_without_surb_time_x.append(int(message_num))

        if 'received_surb_text_time' in receiver_data:
            logging.info(
                "{} secs to receive messages *with* SURB".format(receiver_data['received_surb_text_time']))
            received_surb_text_time_y.append(
                receiver_data['received_surb_text_time'] / int(message_num))
            received_surb_text_time_x.append(int(message_num))
        elif 'received_text_time' in receiver_data:
            logging.info(
                "{} secs to receive messages *without* SURB".format(receiver_data['received_text_time']))
            received_text_time_y.append(
                receiver_data['received_text_time'] / int(message_num))
            received_text_time_x.append(int(message_num))

    if sent_text_without_surb_time_x:
        ax1.plot(np.array(sent_text_without_surb_time_x),
                 np.array(sent_text_without_surb_time_y))
        ax1.set_title("Sending text without SURB")
    if sent_text_with_surb_time_x:
        print(sent_text_without_surb_time_x)
        print(sent_text_without_surb_time_y)
        ax1.plot(np.array(sent_text_with_surb_time_x),
                 np.array(sent_text_with_surb_time_y))
        ax1.set_title("Sending text with SURB")

    if received_surb_text_time_x:
        print(received_surb_text_time_x)
        print(received_surb_text_time_y)
        ax2.plot(np.array(received_surb_text_time_x),
                 np.array(received_surb_text_time_y))
        ax2.set_title("Receiving text with SURB")
    if received_text_time_x:
        ax2.plot(np.array(received_text_time_x),
                 np.array(received_text_time_y))
        ax2.set_title("Receiving text without SURB")

    plt.show()
    #plt.savefig(LOG_PATH + '/plot.png')
