from distutils.log import set_verbosity
import json
import sys
import logging
import matplotlib.pyplot as plt
import numpy as np

assert len(
    sys.argv) >= 2, "Performance calculator must take at least two parameter: name of the log file, and the number(s) of messages for each trial"

LOG_PATH = 'logs/' + sys.argv[1]

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


def calculate_latency(start_arr, end_arr):
    latency_arr = []
    for i in range(len(start_arr)):
        if end_arr[str(i)] > 0 and start_arr[str(i)] > 0:
            latency_arr.append(end_arr[str(i)] - start_arr[str(i)])
    return np.array(latency_arr)


def plot_latency(ax, arr):
    x_arr = [int(message_num)] * len(arr)
    ax.scatter(np.array(x_arr), arr)
    return x_arr


def plot_best_fit(ax, x, y):
    print(len(x), len(y))
    m, b = np.polyfit(x, y, 1)
    ax.plot(x, m*x + b)


fig, (ax1, ax2, ax3) = plt.subplots(1, 3)

# To draw the best fit lines for each graph, we need to accumulate the data from different runs
all_x_surb_reply_latency = []
all_y_surb_reply_latency = []
all_x_text_latency_without_surb = []
all_y_text_latency_without_surb = []
all_x_text_latency_with_surb = []
all_y_text_latency_with_surb = []

for message_num in sys.argv[2:]:
    with open(LOG_PATH + '/' + message_num + '/sender.json', 'r') as file:
        sender_data = json.load(file)

    with open(LOG_PATH + '/' + message_num + '/receiver.json', 'r') as file:
        receiver_data = json.load(file)

    surb_reply_latency = calculate_latency(
        receiver_data[message_num]['sent_surb_reply_text_time'], sender_data[message_num]['received_surb_reply_text_time'])
    all_y_surb_reply_latency += list(surb_reply_latency)
    all_x_surb_reply_latency += plot_latency(ax1, surb_reply_latency)
    print(all_y_surb_reply_latency)
    print(all_x_surb_reply_latency)

    text_latency_without_surb = calculate_latency(
        sender_data[message_num]['sent_text_without_surb_time'], receiver_data[message_num]['received_text_time'])
    all_y_text_latency_without_surb += list(text_latency_without_surb)
    all_x_text_latency_without_surb += plot_latency(
        ax2, text_latency_without_surb)

    text_latency_with_surb = calculate_latency(
        sender_data[message_num]['sent_text_with_surb_time'], receiver_data[message_num]['received_surb_text_time'])
    all_y_text_latency_with_surb += list(text_latency_with_surb)
    all_x_text_latency_with_surb += plot_latency(ax3, text_latency_with_surb)


# Calculate and add best fit line. m is the slope, b is the intercept
plot_best_fit(ax1, np.array(all_x_surb_reply_latency),
              np.array(all_y_surb_reply_latency))
plot_best_fit(ax2, np.array(all_x_text_latency_without_surb),
              np.array(all_y_text_latency_without_surb))
plot_best_fit(ax3, np.array(all_x_text_latency_with_surb),
              np.array(all_y_text_latency_with_surb))


ax1.set_title("Text message (SURB attached)")
ax2.set_title("Text message (no SURB attached)")
ax3.set_title("Text reply using SURB")

plt.show()
