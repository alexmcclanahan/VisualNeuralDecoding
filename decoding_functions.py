from keras.layers import Dense, Dropout, LSTM, BatchNormalization, Flatten, Conv1D, MaxPooling1D
from keras.models import Sequential
from keras.utils import to_categorical
import tensorflow as tf
from keras.optimizers import Adam
from sklearn.svm import SVC
import numpy as np
import pandas as pd

def fetch_scenes(session):
    scene_presentations = session.get_stimulus_table('natural_scenes')
    scene_presentations["valid"] = True

    for idx, row in session.invalid_times.iterrows():
        scene_presentations.loc[
            (scene_presentations["stop_time"] >= row["start_time"])
            & (scene_presentations["start_time"] <= row["stop_time"]),
            "valid"
        ] = False

    scene_presentations = scene_presentations[scene_presentations["valid"]]
    return scene_presentations
###############################################################################################

##### arrive at a units variable, which contains the units of interest #####
def fetch_units(session, areas):

    # if performing the anatomical analysis, as these will come through as one area string to fetch_units
    if type(areas) is str:
        units = session.units[session.units['ecephys_structure_acronym'] == areas]

    # otherwise, with the time bin analysis, areas will be an array of strings
    else:
        units = session.units[session.units['ecephys_structure_acronym'] == areas[0]]
        for sp_area in range(len(areas[1:])):
            units2 = [session.units[session.units['ecephys_structure_acronym'] == areas[sp_area + 1]]]

            # units2new = units2new.append(units2)
            units = units.append(units2)
            continue

    return units



####################################################################################################

##### Obtain X, the input to the deep learning algorithms, which are the spike counts for each unit during each stimulus_presentation #####
##### Important to note here that depending on 'bin_duration_in_seconds' determines the size of X that is returned. Meaning, the      #####
##### second dimension of X will be of size = 250/(bin_duration_in_seconds)
def fetch_x(scene_presentations, units, session, bin_duration_in_seconds):

    # Toggle time bins:

    time_bins = np.arange(0, 0.25+bin_duration_in_seconds, bin_duration_in_seconds)
    # edge = (0, 0.25)
    # print(time_bins)
    X_hold = session.presentationwise_spike_counts(
        stimulus_presentation_ids=scene_presentations.index.values,
        bin_edges=time_bins,
        unit_ids=units.index.values[:]
    )
    X = X_hold.values
    # X_2d = np.reshape(X_hold.values, (5950, len(visp_units_sess_1.index.values)))

    return X_hold, X



##### Takes X from presentationwise_spike_counts and Y from scene_presentations, formats them into train, test, validation #####
def prepare_data(X,Y):
    train = int(0.7 * len(X))
    test = int(0.85 * len(X))

    # %%

    Y_cat = to_categorical(Y, num_classes=119)

    X_train = X[:train]
    Y_train = Y_cat[:train]

    X_test = X[train:test]
    Y_test = Y_cat[train:test]

    X_valid = X[test:]
    Y_valid = Y_cat[test:]

    return X_train, X_test, X_valid, Y_train, Y_test, Y_valid


##### Support Vector Machine #####

def svm(X,Y):

    ## reshape X_train to fit into 2D-requiring SVM! ##

    ## These merely for formatting prior to reshaping ##
    train_test_svm = int(0.7 * len(X))
    X_train_svm_hold = X[:train_test_svm]
    X_test_svm_hold = X[train_test_svm:]

    ## reshape X_train to fit into 2D-requiring SVM! ##
    X_train_svm = np.reshape(X_train_svm_hold, (np.shape(X_train_svm_hold)[0], ((np.shape(X_train_svm_hold)[1])*(np.shape(X_train_svm_hold)[2]))))
    X_test_svm = np.reshape(X_test_svm_hold, (np.shape(X_test_svm_hold)[0], ((np.shape(X_test_svm_hold)[1])*(np.shape(X_test_svm_hold)[2]))))

    ## Important that Y remains non-categorical here, as Sklearn requires nominals, as opposed to Keras implemented as categorical Y's ##
    Y_train_svm_nonint = Y[:train_test_svm]
    Y_train_svm = Y_train_svm_nonint.astype('int')
    Y_test_svm_nonint = Y[train_test_svm:]
    Y_test_svm = Y_test_svm_nonint.astype('int')

    ## Build and fit linear classifier ##
    clf = SVC(kernel='linear')
    clf.fit(X_train_svm, Y_train_svm)
    #y_pred = clf.predict(X_test_re)
    svm_score = clf.score(X_test_svm, Y_test_svm)
    svm_accuracy = pd.DataFrame({'Accuracy': [svm_score]})
    return svm_accuracy


##### Obtain train, test, eval accuracy and loss for SNN #####
def snn(X_train, Y_train, X_test, Y_test, X_valid, Y_valid):
    model_SNN = Sequential()

    model_SNN.add(BatchNormalization())
    model_SNN.add(Dropout(rate=0.5))
    model_SNN.add(Flatten())
    model_SNN.add(Dense(400, activation='relu',input_shape=X_train.shape[1:]))
    model_SNN.add(Dense(119, activation='softmax'))
    # Time dist?

    opt = Adam(lr=1e-3, decay=1e-5)

    model_SNN.compile(loss='categorical_crossentropy',
                      optimizer=opt,
                      metrics=['categorical_accuracy'])

    history_SNN = model_SNN.fit(X_train, Y_train, epochs=20, validation_data=(X_valid, Y_valid))
    eval_SNN = model_SNN.evaluate(X_test, Y_test)

    df_SNN = pd.DataFrame(
        {'Validation_loss': history_SNN.history['val_loss'],
         'Validation_accuracy': history_SNN.history['val_categorical_accuracy'],
         'Training_loss': history_SNN.history['loss'], 'Training_accuracy': history_SNN.history['categorical_accuracy'],
         'Evaluation_loss': eval_SNN[0], 'Evaluation_accuracy': eval_SNN[1]})
    return df_SNN


##### Function obtaining the same parameters from DNN
def dnn(X_train, Y_train, X_test, Y_test, X_valid, Y_valid):
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

    history_DNN = model_DNN.fit(X_train, Y_train, epochs=20, validation_data=(X_valid, Y_valid))
    eval_DNN = model_DNN.evaluate(X_test, Y_test)

    df_DNN = pd.DataFrame(
        {'Validation_loss': history_DNN.history['val_loss'],
         'Validation_accuracy': history_DNN.history['val_categorical_accuracy'],
         'Training_loss': history_DNN.history['loss'], 'Training_accuracy': history_DNN.history['categorical_accuracy'],
         'Evaluation_loss': eval_DNN[0], 'Evaluation_accuracy': eval_DNN[1]})

    return df_DNN

def LSTM(X_train, Y_train, X_test, Y_test, X_valid, Y_valid):
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

    return df_LSTM

def cnn(X_train, Y_train, X_test, Y_test, X_valid, Y_valid):

    model_CNN = Sequential()
    model_CNN.add(BatchNormalization())

    model_CNN.add(Conv1D(64, kernel_size=3, activation='relu', input_shape=X_train.shape))
    model_CNN.add(Dropout(rate=0.5))
    model_CNN.add(MaxPooling1D())
    model_CNN.add(Flatten())
    model_CNN.add(Dense(400, activation='relu'))
    model_CNN.add(Dropout(rate=0.2))
    model_CNN.add(Dense(119, activation='softmax'))

    opt = tf.keras.optimizers.Adam(lr=1e-3, decay=1e-5)
    model_CNN.compile(loss='categorical_crossentropy', optimizer=opt,
                      metrics=['categorical_accuracy'])

    history_CNN = model_CNN.fit(X_train, Y_train, epochs=20, validation_data=(X_valid, Y_valid))

    eval_CNN = model_CNN.evaluate(X_test, Y_test)

    df_CNN = pd.DataFrame(
        {'Validation_loss': history_CNN.history['val_loss'],
         'Validation_accuracy': history_CNN.history['val_categorical_accuracy'],
         'Training_loss': history_CNN.history['loss'], 'Training_accuracy': history_CNN.history['categorical_accuracy'],
         'Evaluation_loss': eval_CNN[0], 'Evaluation_accuracy': eval_CNN[1]})

    return df_CNN
