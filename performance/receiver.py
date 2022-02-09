import asyncio
from cmath import e
import websockets
import json
import time
from datetime import datetime
import config
import logging
import sys
import os
import signal

assert len(sys.argv) == 3, "Receiver must take two parameters: name of the log file and the number of messages per trial"


MESSAGE_PER_TRIAL = int(sys.argv[2])
LOG_PATH = 'logs/' + sys.argv[1] + '/' + str(MESSAGE_PER_TRIAL)

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

data = {
    "sent_surb_reply_text_time": dict(),
    "received_text_time": dict(),
    "received_surb_text_time": dict()
}

self_address_request = json.dumps({
    "type": "selfAddress"
})


def save_to_file():
    logging.info('writing to file')

    if not os.path.exists('logs/' + sys.argv[1]):
        os.mkdir('logs/' + sys.argv[1])

    if not os.path.exists(LOG_PATH):
        os.mkdir(LOG_PATH)

    # if os.path.exists(LOG_PATH +'/receiver.json'):
    #     with open(LOG_PATH + '/receiver.json', 'a+') as file:
    #         if len(file.readlines()) != 0:
    #             file.seek(0)
    #             output = json.loads(file.read())
    #             output.update({MESSAGE_PER_TRIAL: data})
    #             json.dump(output, file)
    #         else:
    #             logging.error("[RECEIVER] Could not load existing data")
    # else:
    #     logging.error('[RECEIVER] Path does not exist')
    with open(LOG_PATH + '/receiver.json', 'w+') as file:
        json.dump({MESSAGE_PER_TRIAL: data}, file)
        file.close()


async def reply_text():
    count = 0
    surb_count = 0

    async with websockets.connect(config.RECEIVER_CLIENT_URI) as websocket:
        await websocket.send(self_address_request)
        self_address = json.loads(await websocket.recv())
        logging.info("[RECEIVER] Our address is: {}".format(
            self_address['address']))

        while count < MESSAGE_PER_TRIAL * config.NUM_TRIALS:
            logging.info(
                "[RECEIVER] Waiting to receive a message from the mix network...")

            try:
                received_message = json.loads(
                    await asyncio.wait_for(websocket.recv(), timeout=10))
            except asyncio.TimeoutError:
                received_message = {'type': 'timeout'}

            message_received = time.time()
            if received_message['type'] == 'error':
                logging.error(
                    "[RECEIVER] Received error message from the mix network: {}".format(received_message))
            elif received_message['type'] == 'timeout':
                logging.error('Timeout. Assuming ack was received.')
                # Add -1 to each of the arrays below, since we cannot know if the sent message actually had a SURB or not
                data['received_surb_text_time'][surb_count] = -1
                data['received_text_time'][count] = -1
            else:
                logging.info(
                    "[RECEIVER] Received message from the mix network: {}".format(received_message['message']))

                # use the received surb to send an anonymous reply!
                reply_surb = received_message["replySurb"]
                reply_message = 'Hello back!'

                if reply_surb:
                    # Get rid of the -1 added above if it was a mistake
                    data['received_surb_text_time'][surb_count] = (
                        message_received)
                    text_send = json.dumps({
                        'type': "reply",
                        'message': str(surb_count),
                        'replySurb': reply_surb
                    })

                    logging.info(
                        "[RECEIVER] Sending '{}' over the mix network, *using* reply SURB".format(reply_message))
                    await websocket.send(text_send)
                    data['sent_surb_reply_text_time'][surb_count] = (
                        time.time())
                    surb_count += 1

                else:
                    data['received_text_time'][count] = (message_received)
                    text_send = json.dumps({
                        'type': "send",
                        'message': reply_message,
                        'recipient': config.SENDER_ADDRESS[0],
                        'withReplySurb': True,
                    })
                    await websocket.send(text_send)
                    logging.info(
                        "[RECEIVER] Reply '{}' sent, *not using* a SURB".format(reply_message))

                count += 1


asyncio.get_event_loop().run_until_complete(reply_text())
logging.info("[RECEIVER] Receiver loop complete")

save_to_file()
