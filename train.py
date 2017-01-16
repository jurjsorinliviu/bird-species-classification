import os
import time
import pickle
from time import localtime, strftime
from subprocess import call
from optparse import OptionParser

parser = OptionParser()
parser.add_option("--model_name", dest="model_name")
(options, args) = parser.parse_args()
model_name = options.model_name


# Training Settings
nb_iterations = 20

train_path = "/disk/martinsson-spring17/birdClef2016Whole/train"
valid_path = "/disk/martinsson-spring17/birdClef2016Whole/valid"
noise_path = "/home/martinsson-spring17/data/noise"

#basename = strftime("%Y_%m_%d_%H:%M:%S_", localtime()) + model_name
basename = "2017_01_11_01:15:36_cuberun"
weight_file_path = os.path.join("./weights", basename + ".h5")
history_file_path = os.path.join("./history", basename + ".pkl")
tmp_history_file_path = os.path.join("./history", basename + "_tmp.pkl")
lock_file  = basename + ".lock"

# Arguments
qsub_args = [
    "-cwd",
    "-l", "gpu=1",
    "-e", "./log/" + model_name+ "_run_job.sh.error",
    "-o", "./log/" + model_name+ "_run_job.sh.log",
    "./run_job.sh",
    weight_file_path,
    tmp_history_file_path,
    train_path,
    valid_path,
    noise_path,
    lock_file,
    model_name
]

def train():
    print("#############################")
    print("# Training Settings")
    print("#############################")
    print("Model        : ", model_name)
    print("Weight path  : ", weight_file_path)
    print("History path : ", history_file_path)
    print("Train path   : ", train_path)
    print("Valid path   : ", valid_path)

    train_loss = []
    valid_loss = []
    train_acc = []
    valid_acc = []

    # if exists means we are restarting a crashed training
    if os.path.isfile(history_file_path):
        print("Loading previous history data...")
        with open(history_file_path, 'rb') as input:
            train_loss = pickle.load(input)
            valid_loss = pickle.load(input)
            train_acc = pickle.load(input)
            valid_acc = pickle.load(input)

    for i in range(14, nb_iterations):

        # create lock file
        print("Creating lock file: ", lock_file)
        open(lock_file, 'a').close()

        # submit job, train once
        print("Submitting Job ", str(i), "/", str(nb_iterations))
        if not i == 0:
            call(["qsub"] + qsub_args + ['False'])
        else:
            call(["qsub"] + qsub_args + ['True'])

        # block until job is finished
        while os.path.exists(lock_file):
            time.sleep(5)

        print("Job " + str(i) + " is done.")

        # load all history data and append
        print("Loading temporary history data...")
        with open(tmp_history_file_path, 'rb') as input:
            train_loss = train_loss + pickle.load(input)
            valid_loss = valid_loss + pickle.load(input)
            train_acc = train_acc + pickle.load(input)
            valid_acc = valid_acc + pickle.load(input)

        # save all collected history data
        print("Save all collected history data...")
        with open(history_file_path, 'wb') as output:
            pickle.dump(train_loss, output, pickle.HIGHEST_PROTOCOL)
            pickle.dump(valid_loss, output, pickle.HIGHEST_PROTOCOL)
            pickle.dump(train_acc, output, pickle.HIGHEST_PROTOCOL)
            pickle.dump(valid_acc, output, pickle.HIGHEST_PROTOCOL)

train()