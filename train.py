import h5py

from keras.models import Sequential
from keras.preprocessing.image import ImageDataGenerator

import data
import numpy as np
import model as m


def get_top_n_error(preds, y, n):
    index_of_true = np.argmax(y, axis=1)
    index_of_preds = np.argsort(preds, axis=1)
    total = float(len(y))
    correct = float(0)

    for i in range(len(index_of_true)):
        for j in range(1, n+1):
            if index_of_true[i] == index_of_preds[i,-j]:
                correct = correct+1
                break

    accuracy = float(correct/total)

    return accuracy

def run(epochs=500, split=0.1, extract=True, cont=True):
    '''Does the routine required to get the data, put them in needed format and start training the model
       saves weights whenever the model produces a better test result and keeps track of the best loss'''
    if extract:
        print("Extracting data..")
        X, y = data.extract_data(size=128)

        print("Getting data into shape..")
        X, y, nb_samples, num_categories = data.preprocess_data(X, y, save=True, subtract_mean=True)

    else:
        h5f = h5py.File('data.hdf5', 'r')
        nb_samples = h5f['nb_samples'].value
        #print(nb_samples)
        num_categories = h5f['n_categories'].value
        h5f.close()
        #

    print("Loading data..")
    print(num_categories)
    print(nb_samples)
    data_ids = np.arange(start=0, stop=nb_samples)
    val_ids = data.produce_validation_indices(data_ids, 4000)
    train_ids = data.produce_train_indices(dataset_indx=data_ids, number_of_samples=7500, val_indx=val_ids)
    #X_train, y_train, X_test, y_test = data.split_data(X, y, split_ratio=split)
    X_train, y_train, X_val, y_val = data.load_dataset_bit_from_hdf5(train_ids, val_ids, only_train=False)
    X_val = X_val / 255
    print("Building and Compiling model..")
    model = m.get_model(n_outputs=num_categories)

    if cont:
        #model.load_weights_until_layer("pre_trained_weights/latest_model_weights.hdf5", 26)
        model.load_weights("pre_trained_weights/latest_model_weights.hdf5")
    model.compile(optimizer='adam', loss='categorical_crossentropy')

    print("Training..")

    best_performance = np.inf
    for i in range(epochs):
        # X_train_augmented = data.augment_data(X_train.copy())
        # metadata = model.fit(X=X_train_augmented, y=y_train, batch_size=64, nb_epoch=1, verbose=1,
        #                      validation_data=[X_test, y_test], show_accuracy=True)

        # compute quantities required for featurewise normalization
        # (std, mean, and principal components if ZCA whitening is applied)
        train_ids = data.produce_train_indices(dataset_indx=data_ids, number_of_samples=15000, val_indx=val_ids)

        X_train, y_train = data.load_dataset_bit_from_hdf5(train_ids, val_ids, only_train=True)
        import matplotlib.pyplot as p

        X_train = X_train / 255
        X_train = data.augment_data(X_train)

        # fit the model on the batches generated by datagen.flow()
        metadata = model.fit(X_train, y_train, validation_data=[X_val, y_val], batch_size=64,
                             nb_epoch=1, verbose=1, shuffle=True, show_accuracy=True, class_weight=None, sample_weight=None)
        top_k = 3
        current_loss = metadata.history['loss'][-1]
        current_val_loss = metadata.history['val_loss'][-1]
        preds = model.predict_proba(X_val, batch_size=64)
        print("Loss: "+str(current_loss))
        print("Val_loss: "+str(current_val_loss))

        top_3_error = get_top_n_error(preds, y_val, top_k)
        print("Top 3 error: "+str(top_3_error))
        if current_val_loss<best_performance:
            model.save_weights("pre_trained_weights/model_weights.hdf5", overwrite=True)
            best_performance=current_val_loss
            print("Saving weights..")
        model.save_weights("pre_trained_weights/latest_model_weights.hdf5", overwrite=True)

if __name__ == '__main__':
    run()

