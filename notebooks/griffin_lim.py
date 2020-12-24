# %%
import glob
import tempfile
import time

import librosa.display
import yaml

import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
from tensorflow_tts.utils import TFGriffinLim, griffin_lim_lb

# %config InlineBackend.figure_format = 'svg'

# %% [markdown]
# Get mel spectrogram example and corresponding ground truth audio.

# %%
mel_spec = np.load("dump/train/raw-feats/1-raw-feats.npy")
gt_wav = np.load("dump/train/wavs/1-wave.npy")

stats_path = "dump/stats.npy"
dataset_config_path = "preprocess/baker_preprocess.yaml"
config = yaml.load(open(dataset_config_path), Loader=yaml.Loader)

griffin_lim_tf = TFGriffinLim(stats_path, config)


# %%
print("mel_spec shape: ", mel_spec.shape)
print("gt_wav shape: ", gt_wav.shape)
print("config\n", config)

# %% [markdown]
# TF version has GPU compatibility and supports batch dimension.

# %%
# inv_wav_tf = griffin_lim_tf(mel_spec[tf.newaxis, :], n_iter=32)  # [1, mel_len] -> [1, audio_len]
inv_wav_lb = griffin_lim_lb(mel_spec, stats_path, config)  # [mel_len] -> [audio_len]


# %%
np.min(inv_wav_lb)

# %% [markdown]
# Time comparison between both implementations.

# %%
get_ipython().run_line_magic('timeit', 'griffin_lim_tf(mel_spec[tf.newaxis, :])')


# %%
get_ipython().run_line_magic('timeit', 'griffin_lim_lb(mel_spec, stats_path, config)')


# %%
tf_wav = tf.audio.encode_wav(inv_wav_tf[0, :, tf.newaxis], config["sampling_rate"])
lb_wav = tf.audio.encode_wav(inv_wav_lb[:, tf.newaxis], config["sampling_rate"])
gt_wav_ = tf.audio.encode_wav(gt_wav[:, tf.newaxis], config["sampling_rate"])


# %%
items = [
    Audio(value=x.numpy(), autoplay=False, loop=False)
    for x in [gt_wav_, lb_wav, tf_wav]
]
labels = [Label("Ground Truth"), Label("Librosa"), Label("TensorFlow")]
GridBox(
    children=[*labels, *items],
    layout=Layout(grid_template_columns="25% 25% 25%", grid_template_rows="30px 30px"),
)


# %%
_, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8), sharey=True, sharex=True)
librosa.display.waveplot(gt_wav, sr=config["sampling_rate"], color="b", ax=ax1)
ax1.set_title("Ground truth")
ax1.set_xlabel("")
librosa.display.waveplot(inv_wav_lb*100, sr=config["sampling_rate"], color="g", ax=ax2)
ax2.set_title("Griffin-Lim reconstruction (librosa)")
ax2.set_xlabel("")
librosa.display.waveplot(
    inv_wav_tf[0].numpy()*100, sr=config["sampling_rate"], color="r", ax=ax3
)
ax3.set_title("Griffin-Lim reconstruction (TF)");


# %%
def gen():
    file_list = glob.glob("../dump/train/norm-feats/*-norm-feats.npy")
    for file in file_list:
        yield np.load(file)


mel_ds = tf.data.Dataset.from_generator(
    gen, (tf.float32), tf.TensorShape([None, config["num_mels"]])
).padded_batch(10)

for mel_batch in mel_ds.take(5):
    start_batch = time.perf_counter()
    inv_wav_tf_batch = griffin_lim_tf(mel_batch)
    print(
        f"Iteration time: {time.perf_counter() - start_batch:.4f}s, output shape: {inv_wav_tf_batch.shape}"
    )

# %% [markdown]
# Saving outputs with both implementations.

# %%
# Single file
griffin_lim_lb(mel_spec, stats_path, config, output_dir="../tmp", wav_name="lb")
griffin_lim_tf.save_wav(inv_wav_tf, output_dir="../tmp", wav_name="tf")

# # Batch files
# griffin_lim_tf.save_wav(inv_wav_tf_batch, tempfile.gettempdir(), [x for x in range(10)])

# %ls {tempfile.gettempdir()} | grep '.wav'


# %%
tempfile.gettempdir()


# %%



