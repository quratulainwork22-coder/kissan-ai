"""Train the cotton leaf classifier (MobileNetV2 transfer learning).

Folder layout (rename the dataset folders to match):
    data/healthy/*.jpg
    data/curl_virus/*.jpg
    data/bacterial_blight/*.jpg

Usage:  pip install -r requirements-ml.txt
        python ml/train_model.py --data data --epochs 10
Copy models/cotton_model.keras and models/labels.txt into the app's models/ folder.
"""
import argparse
import os

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers
from sklearn.metrics import classification_report, confusion_matrix

parser = argparse.ArgumentParser()
parser.add_argument("--data", default="data")
parser.add_argument("--epochs", type=int, default=10)
parser.add_argument("--out", default="models")
args = parser.parse_args()

IMG = (224, 224)
train_ds = tf.keras.utils.image_dataset_from_directory(
    args.data, validation_split=0.2, subset="training", seed=42, image_size=IMG, batch_size=32)
val_ds = tf.keras.utils.image_dataset_from_directory(
    args.data, validation_split=0.2, subset="validation", seed=42, image_size=IMG, batch_size=32)
class_names = train_ds.class_names
print("Classes:", class_names)

augment = tf.keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.1),
    layers.RandomZoom(0.1),
])

base = tf.keras.applications.MobileNetV2(input_shape=IMG + (3,), include_top=False, weights="imagenet")
base.trainable = False

inputs = tf.keras.Input(shape=IMG + (3,))
x = augment(inputs)
x = layers.Rescaling(1.0 / 127.5, offset=-1)(x)  # same as MobileNetV2 preprocessing
x = base(x, training=False)
x = layers.GlobalAveragePooling2D()(x)
x = layers.Dropout(0.2)(x)
outputs = layers.Dense(len(class_names), activation="softmax")(x)
model = tf.keras.Model(inputs, outputs)

model.compile(optimizer=tf.keras.optimizers.Adam(1e-3),
              loss="sparse_categorical_crossentropy", metrics=["accuracy"])
model.fit(train_ds, validation_data=val_ds, epochs=args.epochs)

# Evaluation: precision, recall, F1 and confusion matrix
y_true, y_pred = [], []
for images, labels in val_ds:
    probs = model.predict(images, verbose=0)
    y_true.extend(labels.numpy())
    y_pred.extend(np.argmax(probs, axis=1))
print(classification_report(y_true, y_pred, target_names=class_names))
print(confusion_matrix(y_true, y_pred))

os.makedirs(args.out, exist_ok=True)
model.save(os.path.join(args.out, "cotton_model.keras"))
with open(os.path.join(args.out, "labels.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(class_names))
print("Saved model to", args.out)
