import asyncio
from cmath import e
import json
import websockets
from datetime import datetime
import time
import config
import logging
import sys
import os
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

# Check and save system arguments
assert len(sys.argv) >= 3, "Sender must take at least three parameters: test type (latency or throughput), name of the log file and the number of messages per trial"
assert sys.argv[2] == 'throughput' or sys.argv[2] == 'latency', "Test type must be 'throughput' or 'latency'"
throughput_with_surb = None
if sys.argv[2] == 'throughput':
    for i in range(len(sys.argv) - 1):
        if sys.argv[i] == '--surb':
            throughput_with_surb = sys.argv[i+1]
        if throughput_with_surb == None:
            assert "Must provide is throughput test will be using SURB or not. Please do so using a --surb flag. Allowed inputs are 'TRUE' and 'FALSE'"
        else:
            assert throughput_with_surb == 'TRUE' or throughput_with_surb == 'FALSE', "Allowed inputs for the --surb flag are are 'TRUE' and 'FALSE'"

# Set constants
THROUGHPUT_WITH_SURB = throughput_with_surb
MESSAGE_PER_TRIAL = int(sys.argv[3])
TEST_TYPE = sys.argv[2]
surb_folder = None

if TEST_TYPE == 'latency':
    surb_folder = ''
elif TEST_TYPE == 'throughput':
    if THROUGHPUT_WITH_SURB == 'TRUE':
        surb_folder = 'with_surb/'
    else:
        surb_folder = 'without_surb/'

LOG_PATH = TEST_TYPE + '_logs/' + \
    sys.argv[1] + '/' + surb_folder + str(MESSAGE_PER_TRIAL)

# For storing the test results on the run
latency_data = {
    "sent_text_with_surb_time": dict(),
    "sent_text_without_surb_time": dict(),
    "received_surb_reply_text_time": dict(),

}
throughput_data = dict()

# The program needs make a self-address query to the client before it starts sending messages
self_address_request = json.dumps({
    "type": "selfAddress"
})


def save_to_file(data):
    logging.info('[SENDER] Writing to file')

    if not os.path.exists(TEST_TYPE + '_logs/' + sys.argv[1]):
        os.mkdir(TEST_TYPE + '_logs/' + sys.argv[1])

    if not os.path.exists(TEST_TYPE + '_logs/' + sys.argv[1] + '/' + surb_folder):
        os.mkdir(TEST_TYPE + '_logs/' + sys.argv[1] + '/' + surb_folder)

    if not os.path.exists(LOG_PATH):
        os.mkdir(LOG_PATH)

    with open(LOG_PATH + '/sender.json', 'w+') as file:
        # json.dump({MESSAGE_PER_TRIAL: data}, file)
        json.dump(data, file)
        file.close()
    return 1


async def send_text():
    count = 0

    async with websockets.connect(config.SENDER_CLIENT_URI) as websocket:
        await websocket.send(self_address_request)
        self_address = json.loads(await websocket.recv())
        logging.info("[SENDER] Our address is: {}".format(
            self_address["address"]))

        text_send = {
            "type": "send",
            "message": str(count),
            "recipient": config.RECEIVER_ADDRESS,
            "withReplySurb": False,
        }

        # Send messages without SURB
        logging.info("[SENDER] **Starting sending messages *without* SURB**")
        while count < MESSAGE_PER_TRIAL:
            text_send['message'] = str(count)
            logging.info(
                "[SENDER] Sending '{}' (*without* reply SURB) over the mix network...".format(text_send['message']))
            await websocket.send(json.dumps(text_send))
            latency_data["sent_text_without_surb_time"][count] = (time.time())
            logging.info(
                "[SENDER] Waiting to receive a message from the mix network...")
            try:
                received_message = json.loads(
                    await asyncio.wait_for(websocket.recv(), timeout=20))
            except asyncio.TimeoutError:
                received_message = {'type': 'timeout'}
            if received_message['type'] == 'error':
                logging.error(
                    "[SENDER] Received error message from the mix network: {}".format(received_message))
            elif received_message['type'] == 'timeout':
                logging.error('Timeout. Assuming ack was received.')
            else:
                receive_time = time.time()
                logging.info(
                    "[SENDER] Received message from: {}".format(received_message['message']))
                if 'with_surb' in received_message['message']:
                    latency_data['received_surb_reply_text_time'][received_message['message'].split('.')[
                        0]] = receive_time
            count += 1

        count = 0

        # Send messages with SURB
        logging.info("[SENDER] **Starting sending messages *with* SURB**")
        text_send['withReplySurb'] = True
        while count < MESSAGE_PER_TRIAL:
            text_send['message'] = str(count)
            logging.info(
                "[SENDER] Sending '{}' (*with* reply SURB) over the mix network...".format(text_send['message']))
            await websocket.send(json.dumps(text_send))
            latency_data["sent_text_with_surb_time"][count] = time.time()
            logging.info(
                "[SENDER] Waiting to receive a message from the mix network...")

            try:
                received_message = json.loads(
                    await asyncio.wait_for(websocket.recv(), timeout=20))
            except asyncio.TimeoutError:
                received_message = {'type': 'timeout'}

            if received_message['type'] == 'error':
                logging.error(
                    "[SENDER] Received error message from the mix network: {}".format(received_message))
            elif received_message['type'] == 'timeout':
                logging.error('Timeout. Assuming ack was received.')
                # latency_data["received_surb_reply_text_time"][count] = -1
            else:
                receive_time = time.time()
                logging.info(
                    "[SENDER] Received message from: {}".format(received_message))
                if 'with_surb' in received_message['message']:
                    latency_data['received_surb_reply_text_time'][received_message['message'].split('.')[
                        0]] = receive_time
            count += 1

        count = 0


async def load_text():
    global throughput_data
    count = 0
    async with websockets.connect(config.SENDER_CLIENT_URI) as websocket:
        await websocket.send(self_address_request)
        self_address = json.loads(await websocket.recv())
        logging.info("[SENDER] Our address is: {}".format(
            self_address["address"]))

        text_send = {
            "type": "send",
            "message": str(count),
            "recipient": config.RECEIVER_ADDRESS,
            "withReplySurb": False,
        }

        text_send['withReplySurb'] = True if THROUGHPUT_WITH_SURB == 'TRUE' else False

        start = time.time()
        while count < MESSAGE_PER_TRIAL:
            text_send['message'] = str(count)
            await websocket.send(json.dumps(text_send))
            count += 1

        end = time.time()
        if THROUGHPUT_WITH_SURB == 'TRUE':
            throughput_data["sent_text_with_surb_time"] = end - start
            logging.info(
                '[SENDER] It took {} seconds to send {} messages *with* SURB'.format(throughput_data["sent_text_with_surb_time"], MESSAGE_PER_TRIAL))

            # After sending all messages with SURB, wait for the receiver to send SURB replies
            start = time.time()
            count = 0
            received_message_cnt = 0
            # I observed that once the receiver ramps up the SURB messages, some of them fail to make their way to the sender
            # I don't know why yet.
            # I give a timeout value to await to prevent the sender being stuck waiting for SURB messages.
            # But it takes too long to wait for each lost SURB. Also, I observed that once the sender gets a timeout,
            # It does not receive any more SURBs. For that reason, I stop waiting after a few timeouts.
            timeout_cnt = 0
            received_surb_indexes = list()

            # Uncomment for checking the receival pattern of SURB replies
            surb_reply_arrivals = list()

            while count < MESSAGE_PER_TRIAL: \
                    # and timeout_cnt < 5: # Comment out for checking the receival pattern of SURB replies
                if count == 0:
                    received_message = json.loads(await websocket.recv())
                    received_surb_indexes.append(
                        (received_message['message'], time.time()))
                    print('received the first SURB')
                    end = time.time()
                else:
                    try:
                        received_message = json.loads(await asyncio.wait_for(websocket.recv(), timeout=10))
                        end = time.time()
                        received_message_cnt += 1

                        # Uncomment for checking the receival pattern of SURB replies
                        received_surb_indexes.append(
                            (received_message['message'], time.time()))

                    except asyncio.TimeoutError:
                        logging.info(
                            '[SENDER] Timeout while waiting for SURB messages')
                        timeout_cnt += 1
                count += 1
            throughput_data["received_surb_time"] = (
                received_message_cnt, end - start)
            logging.info(
                '[SENDER] Received {} SURB replies in {} seconds'.format(received_message_cnt, end - start))
            throughput_data['surb_receival_pattern'] = received_surb_indexes
        else:
            throughput_data["sent_text_without_surb_time"] = end - start
            logging.info(
                '[SENDER] It took {} seconds to send {} messages *without* SURB'.format(throughput_data["sent_text_without_surb_time"], MESSAGE_PER_TRIAL))

if TEST_TYPE == 'latency':
    asyncio.get_event_loop().run_until_complete(send_text())
    save_to_file(latency_data)
elif TEST_TYPE == 'throughput':
    asyncio.get_event_loop().run_until_complete(load_text())
    save_to_file(throughput_data)

logging.info("[SENDER] Sender loop complete")
