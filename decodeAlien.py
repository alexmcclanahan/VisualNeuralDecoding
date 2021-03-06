import os
import shutil

#os.environ['HDF5_DISABLE_VERSION_CHECK']='2'

import numpy as np
import pandas as pd
from pandas import ExcelWriter
from allensdk.brain_observatory.ecephys.ecephys_session import EcephysSession
from allensdk.brain_observatory.ecephys.ecephys_project_cache import EcephysProjectCache
from keras.layers import Dense, Dropout, LSTM, BatchNormalization, Flatten, TimeDistributed
from keras.models import Sequential
from keras.utils import to_categorical
import tensorflow as tf
from keras.optimizers import Adam
import decoding_functions
from openpyxl import Workbook, load_workbook

data_dir = '/Users/bioel/PycharmProjects/untitled4/ecephys_cache_dir'
manifest_path = os.path.join(data_dir, 'manifest.json')
cache = EcephysProjectCache.from_warehouse(manifest = manifest_path)
session_table = cache.get_session_table()

all_sessions_all = session_table.loc[session_table.session_type == 'brain_observatory_1.1'].index
all_sessions_pre = all_sessions_all[0:28]
all_sessions_post = all_sessions_all[29:]
all_sessions = np.append(all_sessions_pre, all_sessions_post)

wb = Workbook()
SVM_acc = np.empty(len(all_sessions))
SNN_acc = np.empty(len(all_sessions))
DNN_acc = np.empty(len(all_sessions))

########################################################################
# INPUT (Brain regions of interest as array of strings) REQUIRED HERE, along with a description for excel file: #
areas = ['VISp', 'VISrl', 'VISam', 'VISl', 'VISpm', 'VISal']
areas_description = 'All V1'
########################################################################
# INPUT (Bin duration in ms) REQUIRED HERE: #
bin_duration_in_msec = 50
########################################################################

new_folder = areas_description + '_' + str(bin_duration_in_msec) + '_ms'
# Toggle below off if session fails and have to run again
os.mkdir(new_folder)


for session_of_interest in range(len(all_sessions)):
    print('Session ' + str(session_of_interest) + '/' + str(len(all_sessions)))
    session_id = all_sessions[session_of_interest]
    session = cache.get_session_data(session_id)

    scene_presentations = decoding_functions.fetch_scenes(session)

    # These three lines will fetch units from specified session, & areas. Then, X & Y from those units, & time bins
    # specified, as well as prepare X & Y into train, test, validation sets using 70%, 15%, 15%, of the data, respectively. No need to input anything here.
    units = decoding_functions.fetch_units(session, areas)
    X_hold, X = decoding_functions.fetch_x(scene_presentations,units,session,bin_duration_in_seconds=bin_duration_in_msec/1000)
    Y = scene_presentations.loc[X_hold.stimulus_presentation_id.values, 'frame']
    X_train, X_test, X_valid, Y_train, Y_test, Y_valid = decoding_functions.prepare_data(X, Y)

    # Machine learning-based decoders below: #
    ##########################################

    # SVM #
    svm_acc = decoding_functions.svm(X,Y)
    print('Post SVM')

    # SNN #
    df_SNN = decoding_functions.snn(X_train, Y_train, X_test, Y_test, X_valid, Y_valid)
    print('Post SNN')

    # DNN #
    df_DNN = decoding_functions.dnn(X_train, Y_train, X_test, Y_test, X_valid, Y_valid)
    print('Post DNN')

    sess_file_name = str(session_id) + '.xlsx'

    with ExcelWriter(new_folder + '/' + sess_file_name) as writer:
        svm_acc.to_excel(writer, sheet_name='SVM')
        df_SNN.to_excel(writer, sheet_name='SNN')
        df_DNN.to_excel(writer, sheet_name='DNN')
    continue