# %%
import pytorch_lightning as pl
from pytorch_lightning.callbacks import EarlyStopping, ModelCheckpoint

callbacks = [
    EarlyStopping(monitor="validation_loss", patience=5, mode="min"),
    ModelCheckpoint(
        monitor="validation_loss",
        mode="min",
        save_top_k=1,
        filename="best-model",
    ),
]

# %%
import torch
from torch.utils.data import DataLoader

B, C, H, W = 4, 14, 64, 64
dummy_dataset = [
    {"pixel_values": torch.randn(C, H, W), "labels": torch.randint(0, 10, (H, W))}
    for _ in range(16)
]

def collate(batch):
    return {
        "pixel_values": torch.stack([x["pixel_values"] for x in batch]),
        "labels": torch.stack([x["labels"] for x in batch]),
    }

train_loader = DataLoader(dummy_dataset[:12], batch_size=B, collate_fn=collate)
val_loader   = DataLoader(dummy_dataset[12:], batch_size=B, collate_fn=collate)

trainer = pl.Trainer(
    max_epochs=20,
    accelerator="auto",   # uses GPU if available, CPU otherwise
    devices="auto",
    callbacks=callbacks,
    log_every_n_steps=10,
)

trainer.fit(module, train_loader, val_loader)

# %%
import torch
from transformers import SegformerConfig
from src.models.model import SemanticSegmentationSegformer
from src.models.module import SegmentationModule
from torch import nn, optim

# 1. Minimal config
config = SegformerConfig(
    num_channels=14,
    num_labels=3,
    depths=[1, 1, 1, 1],
    id2label={0: "background", 1: "building", 2: "vegetation"},
    label2id={"background": 0, "building": 1, "vegetation": 2},
)

# 2. Model without pre-trained weights
tiny_model = SemanticSegmentationSegformer(config)

# 3. Lightning module
tiny_module = SegmentationModule(
    model=tiny_model,
    loss=nn.CrossEntropyLoss(ignore_index=255),
    optimizer=optim.AdamW,
    optimizer_params={"lr": 1e-3},
    scheduler=optim.lr_scheduler.ReduceLROnPlateau,
    scheduler_params={"mode": "min", "patience": 3, "monitor": "validation_loss"},
    scheduler_interval="epoch",
)

# 4. Three manual training steps on random data
B, C, H, W = 2, 14, 128, 128
dummy_batch = {
    "pixel_values": torch.randn(B, C, H, W),
    "labels": torch.randint(0, 3, (B, H, W)),
}

tiny_module.train()
optimizer = optim.AdamW(tiny_module.parameters(), lr=1e-3)
for step in range(3):
    optimizer.zero_grad()
    loss = tiny_module.training_step(dummy_batch, step)
    loss.backward()
    optimizer.step()
    print(f"Step {step + 1} loss: {loss.item():.4f}")

# %%
from pytorch_lightning.loggers import MLFlowLogger

mlf_logger = MLFlowLogger(
    experiment_name="eksperyment",
    tracking_uri="mlruns"
)

B, C, H, W = 4, 14, 64, 64
images = torch.randn(16, C, H, W)
labels = torch.randint(0, 3, (16, H, W))
dataset = [{"pixel_values": images[i], "labels": labels[i]} for i in range(16)]
def collate(batch):
    return {
        "pixel_values": torch.stack([x["pixel_values"] for x in batch]),
        "labels": torch.stack([x["labels"] for x in batch]),
    }

train_dl = DataLoader(dataset[:12], batch_size=4, collate_fn=collate)
val_dl   = DataLoader(dataset[12:], batch_size=4, collate_fn=collate)

# 3. Trainer
trainer = pl.Trainer(
    max_epochs=3,            # TODO: 3
    accelerator="cpu",
    logger=mlf_logger,                # TODO: mlf_logger
    log_every_n_steps=1,
    enable_progress_bar=False,
)

trainer.fit(tiny_module, train_dl, val_dl)
print("Run logged to:", mlf_logger.run_id)
# %%
import os
from dotenv import load_dotenv
from pytorch_lightning.loggers import MLFlowLogger

load_dotenv()

mlf_logger = MLFlowLogger(
    experiment_name="segformer-satellite",
    tracking_uri=os.getenv("MLFLOW_TRACKING_URI"),
    log_model=True,
)

trainer = pl.Trainer(
    max_epochs=CONFIG["epochs"],
    accelerator="auto",
    devices="auto",
    callbacks=callbacks,
    logger=mlf_logger,
    log_every_n_steps=10,
)
# %%
