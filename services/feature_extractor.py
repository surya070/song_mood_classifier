import numpy as np
import librosa


# NOISE
def noise(data):
    noise_amp = 0.035 * np.random.uniform() * np.amax(data)
    data = data + noise_amp * np.random.normal(size=data.shape[0])
    return data


# STRETCH
def stretch(data, rate=0.8):
    return librosa.effects.time_stretch(y=data, rate=rate)


# SHIFT
def shift(data):
    shift_range = int(np.random.uniform(low=-5, high=5) * 1000)
    return np.roll(data, shift_range)


# PITCH
def pitch(data, sampling_rate, pitch_factor=0.7):
    return librosa.effects.pitch_shift(
        y=data, sr=sampling_rate, n_steps=pitch_factor
    )


# Zero crossing rate
def zcr(data, frame_length, hop_length):
    zcr = librosa.feature.zero_crossing_rate(
        data, frame_length=frame_length, hop_length=hop_length
    )
    return np.squeeze(zcr)


# Root mean square
def rmse(data, frame_length=2048, hop_length=512):
    rmse = librosa.feature.rms(
        y=data, frame_length=frame_length, hop_length=hop_length
    )
    return np.squeeze(rmse)


# Mel-Frequency Cepstral coefficient
def mfcc(data, sr, frame_length=2048, hop_length=512, flatten: bool = True):
    mfcc = librosa.feature.mfcc(y=data, sr=sr)
    return np.squeeze(mfcc.T) if not flatten else np.ravel(mfcc.T)


# Combine all feature functions
def extract_features(data, sr=22050, frame_length=2048, hop_length=512):
    result = np.array([])

    result = np.hstack((
        result,
        zcr(data, frame_length, hop_length),
        rmse(data, frame_length, hop_length),
        mfcc(data, sr, frame_length, hop_length),
    ))
    return result


# Apply data augmentation and extract its features
def get_features(path, duration=28, offset=0.6):
    data, sr = librosa.load(path, duration=duration, offset=offset, mono=True)
    audio = np.array(extract_features(data))

    # Augment: Noise
    noised = noise(data)
    audio = np.vstack((audio, extract_features(noised)))

    # Augment: Pitch
    pitched = pitch(data, sr)
    audio = np.vstack((audio, extract_features(pitched)))

    # Augment: Pitch + Noise
    pitched_noised = noise(pitch(data, sr))
    audio = np.vstack((audio, extract_features(pitched_noised)))

    return audio
