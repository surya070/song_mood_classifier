import tensorflow as tf
import numpy as np
from services.feature_extractor import get_features
import multiprocessing as mp
import timeit
from tqdm import tqdm

# Extract the features.
start = timeit.default_timer()
X,Y=[],[]
for path,emotion,index in tqdm (zip(data_path.Path,data_path.Cluster,range(data_path.Path.shape[0]))):
    features=get_features(path)
    if index%500==0:
        print(f'{index} audio has been processed')
    for i in features:
        X.append(i)
        Y.append(emotion)
print('Done')
stop = timeit.default_timer()

print('Time: ', stop - start) 

model = tf.keras.models.load_model("models/my_model.keras")
moods = ["Energetic & Bold", "Happy & Playful", "Melancholic & Reflective", "Humorous & Quirky", "Intense & Dramatic"]


