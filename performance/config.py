

# Number of tested message types on a single run
# In other words, number of while loops in the sender
NUM_TRIALS = 2

# Nym network addresses of the clients
SENDER_ADDRESS = 'FmxuwvGkTN4JNkCSuDkr7dARtr8YAFo5Gndcut8SB8vu.86EmEgPYxDkp8sReZhG7w42U2w9rG6pMvttyGMYBgzG7@CbxxDmmNCufXSsi7hqUnorchtsqqSLSZp7QfRJ5ugSRA',
RECEIVER_ADDRESS = 'AAqLF34HVFebrcS3snMFk676SvkjCkG2iXobFHFLmL4Q.3aZyZHxMNNhcq7KLCKtkxg2RnyuzEjnm68FAYXocqA6s@4kjgWmFU1tcGAZYRZR57yFuVAexjLbJ5M7jvo3X5Hkcf'

# Where you are running the clients locally
SENDER_CLIENT_URI = "ws://localhost:1977"
RECEIVER_CLIENT_URI = "ws://localhost:1978"

# Latency params
INIT_FREQ = 0.1
FREQ_STEP = 0.1
MAX_FREQ = 10
