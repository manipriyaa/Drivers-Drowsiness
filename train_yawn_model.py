import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout

IMG = 64
BATCH = 32
EPOCHS = 10

datagen = ImageDataGenerator(rescale=1./255, validation_split=0.2)

train = datagen.flow_from_directory(
    "dataset_yawn",
    target_size=(IMG, IMG),
    batch_size=BATCH,
    class_mode="binary",
    subset="training"
)

val = datagen.flow_from_directory(
    "dataset_yawn",
    target_size=(IMG, IMG),
    batch_size=BATCH,
    class_mode="binary",
    subset="validation"
)

model = Sequential([
    Conv2D(32,(3,3),activation="relu",input_shape=(IMG,IMG,3)),
    MaxPooling2D(),
    Conv2D(64,(3,3),activation="relu"),
    MaxPooling2D(),
    Flatten(),
    Dense(128,activation="relu"),
    Dropout(0.3),
    Dense(1,activation="sigmoid")
])

model.compile(optimizer="adam",loss="binary_crossentropy",metrics=["accuracy"])
model.fit(train,validation_data=val,epochs=EPOCHS)
model.save("yawn_model.h5")
print("Saved yawn_model.h5")
