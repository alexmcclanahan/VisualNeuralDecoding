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

data_dir = '/Users/bioel/PycharmProjects/untitled4/ecephys_cache_dir'
manifest_path = os.path.join(data_dir, 'manifest.json')
cache = EcephysProjectCache.from_warehouse(manifest = manifest_path)
# session_table = cache.get_session_table()
# all_sessions = session_table.loc[session_table.session_type == 'brain_observatory_1.1'].index
all_sessions = [715093703]

for session_of_interest in range(len(all_sessions)):
    print(str(session_of_interest))
    session_id = all_sessions[session_of_interest]
    session = cache.get_session_data(session_id)

    scene_presentations = decoding_functions.fetch_scenes(session)
    units = decoding_functions.fetch_units(session)


    bin_duration_in_msec = 250

    X_hold, X = decoding_functions.fetch_x(scene_presentations, units, session,
                                           bin_duration_in_seconds=bin_duration_in_msec / 1000)
    Y = scene_presentations.loc[X_hold.stimulus_presentation_id.values, 'frame']

    X_train, X_test, X_valid, Y_train, Y_test, Y_valid = decoding_functions.prepare_data(X, Y)

    print(np.shape(X_train))
    print(np.shape(Y_train))
    # SNN #
    model = Sequential()
    model.add(BatchNormalization())
    model.add(Dropout(rate=0.2))
    model.add(Flatten())
    model.add(Dense(400, activation='relu', input_shape=X_train.shape[1:]))
    # model.add(Dense(400, activation='relu'))
    model.add(Dense(119, activation='softmax'))
    # Time dist?

    opt = tf.keras.optimizers.Adam(lr=1e-3, decay=1e-5)

    model.compile(loss='categorical_crossentropy',
                  optimizer=opt,
                  metrics=['categorical_accuracy'])
    print('Fit SNN for session ' + str(session_id))
    history_SNN = model.fit(X_train, Y_train, epochs=20, validation_data=(X_valid, Y_valid))
    eval_SNN = model.evaluate(X_test, Y_test)

    df_SNN = pd.DataFrame(
        {'Validation_loss': history_SNN.history['val_loss'],
         'Validation_accuracy': history_SNN.history['val_categorical_accuracy'],
         'Training_loss': history_SNN.history['loss'], 'Training_accuracy': history_SNN.history['categorical_accuracy'],
         'Evaluation_loss': eval_SNN[0], 'Evaluation_accuracy': eval_SNN[1]})

    print('Post SNN')
    # DNN #
    model_DNN = Sequential()
    model_DNN.add(BatchNormalization())

    model_DNN.add(Dense(units=400, activation='relu', input_shape=X_train.shape[1:]))
    model_DNN.add(Dropout(rate=0.5))
    model_DNN.add(Flatten())
    model_DNN.add(Dense(units=400, activation='relu'))
    model_DNN.add(Dropout(rate=0.5))
    model_DNN.add(Dense(119, activation='softmax'))

    opt = tf.keras.optimizers.Adam(lr=1e-3, decay=1e-5)

    model_DNN.compile(loss='categorical_crossentropy',
                      optimizer=opt,
                      metrics=['categorical_accuracy'])
    print('Fit DNN for session ' + str(session_id))
    history_DNN = model_DNN.fit(X_train, Y_train, epochs=20, validation_data=(X_valid, Y_valid))

    eval_DNN = model_DNN.evaluate(X_test, Y_test)

    df_DNN = pd.DataFrame(
        {'Validation_loss': history_DNN.history['val_loss'],
         'Validation_accuracy': history_DNN.history['val_categorical_accuracy'],
         'Training_loss': history_DNN.history['loss'], 'Training_accuracy': history_DNN.history['categorical_accuracy'],
         'Evaluation_loss': eval_DNN[0], 'Evaluation_accuracy': eval_DNN[1]})

    print('Post DNN')
    # LSTM #
    model_LSTM = Sequential()
    model_LSTM.add(LSTM(400, activation='relu', input_shape=X_train.shape[1:], return_sequences=False, dropout=0.2))
    # model_LSTM.add(Flatten())
    # model_LSTM.add(TimeDistributed(Dense(119)))
    model_LSTM.add(Dense(119, activation='softmax'))

    opt = tf.keras.optimizers.Adam(lr=1e-3, decay=1e-5)

    model_LSTM.compile(loss='categorical_crossentropy',
                       optimizer=opt,
                       metrics=['categorical_accuracy'])

    history_LSTM = model_LSTM.fit(X_train, Y_train, epochs=20, validation_data=(X_valid, Y_valid))
    eval_LSTM = model_LSTM.evaluate(X_test, Y_test)

    df_LSTM = pd.DataFrame(
        {'Validation_loss': history_LSTM.history['val_loss'],
         'Validation_accuracy': history_LSTM.history['val_categorical_accuracy'],
         'Training_loss': history_LSTM.history['loss'],
         'Training_accuracy': history_LSTM.history['categorical_accuracy'],
         'Evaluation_loss': eval_LSTM[0], 'Evaluation_accuracy': eval_LSTM[1]})

    print('Post LSTM')
    with ExcelWriter('session_' + str(session_id) + '_allV1LGN_' + str(bin_duration_in_msec) + 'msbin.xlsx') as writer:
        df_SNN.to_excel(writer, sheet_name='SNN')
        df_DNN.to_excel(writer, sheet_name='DNN')
        df_LSTM.to_excel(writer, sheet_name='LSTM')


    continue