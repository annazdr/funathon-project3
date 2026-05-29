# %%
from src.models.model import SegformerB5

model = SegformerB5(
    n_bands=14,
    logits=True,
    freeze_encoder=False,
    # type_labeler="CLCplus-Backbone",
)


def count_params(module):
    total = sum(p.numel() for p in module.parameters())
    trainable = sum(p.numel() for p in module.parameters() if p.requires_grad)
    return total, trainable


print('AAAAAAAA')
total, trainable = count_params(model)
enc_total, enc_trainable = count_params(model.segformer)
dec_total, dec_trainable = count_params(model.decode_head)

print(f"{'Component':<20} {'Total params':>15} {'Trainable params':>18}")
print("-" * 55)
print(f"{'Encoder (MiT-B5)':<20} {enc_total:>15,} {enc_trainable:>18,}")
print(f"{'Decoder (MLP)':<20} {dec_total:>15,} {dec_trainable:>18,}")
print(f"{'Full model':<20} {total:>15,} {trainable:>18,}")
# %%
model.freeze()

total, trainable = count_params(model)
print(f"After freezing encoder — trainable: {trainable:,} / {total:,}")

# Unfreeze for full fine-tuning
model.unfreeze()
total, trainable = count_params(model)
print(f"After unfreezing — trainable: {trainable:,} / {total:,}")
# %%
# 1. Parameters per encoder stage
for i, stage in enumerate(model.segformer.encoder.block):
    n = sum(p.numel() for p in stage.parameters())
    print(f"Stage {i+1}: {n:} parameters")

# 2. Decoder breakdown
for i, proj in enumerate(model.decode_head.linear_c):
    n = sum(p.numel() for p in proj.parameters())  # TODO
    print(f"Decoder projection {i+1}: {n:} parameters")

clf_params = sum(p.numel() for p in model.decode_head.classifier.parameters())
print(f"Classifier: {clf_params:} / {dec_total:} decoder params ")
# %%
import torch

B, C, H, W = 2, 14, 512, 512   # batch size, channels, height, width
dummy_input = torch.randn(B, C, H, W)
dummy_labels = torch.randint(0, model.config.num_labels, (B, H, W))

print(f"Input  shape: {tuple(dummy_input.shape)}")
print(f"Labels shape: {tuple(dummy_labels.shape)}")
# %%
model.eval()
with torch.no_grad():
    # Without labels → raw logits at H/4 × W/4
    logits = model(dummy_input)
    print(f"Logits shape (no labels):   {tuple(logits.shape)}")
    # Expected: (2, num_classes, 128, 128)  — quarter resolution

    # With labels → logits upsampled to label resolution
    upsampled = model(dummy_input, dummy_labels)
    print(f"Logits shape (with labels): {tuple(upsampled.shape)}")
    # Expected: (2, num_classes, 512, 512)
# %%
outputs = model.segformer(
    dummy_input,
    output_hidden_states=True,
    return_dict=True,
)

for i, hs in enumerate(outputs.hidden_states):
    print(f"Stage {i+1} hidden state: {tuple(hs.shape)}")
# %%
import torch.nn.functional as F

model.eval()
with torch.no_grad():
    logits = model(dummy_input)
    outputs = model.segformer(
        dummy_input, output_hidden_states=True, return_dict=True
    )

# 1. Manual upsampling
logits_full = F.interpolate(
    logits,
    size=(H, W),                 # TODO: target (H, W)
    mode="bilinear",
    align_corners=False,
)
print(f"Manually upsampled: {tuple(logits_full.shape)}")

# 2. Predicted class map
probs = torch.softmax(logits_full, dim=1)   # TODO: softmax over class dimension
pred = torch.argmax(probs, dim=1) # TODO: argmax → (B, H, W)
print(f"Predicted map shape: {tuple(pred.shape)}")
print(f"Unique predicted classes: {pred.unique().tolist()}")

# 3. Spatial area ratios
for i, hs in enumerate(outputs.hidden_states):
    ratio = (hs.shape[-2] * hs.shape[-1]) / (H * W)
    print(f"Stage {i+1}: {ratio:.4f}")
# %%
from src.models.module import SegmentationModule
from torch import nn, optim

module = SegmentationModule(
    model=model,
    loss=nn.CrossEntropyLoss(ignore_index=255),
    optimizer=optim.AdamW,
    optimizer_params={"lr": 1e-3, "weight_decay": 1e-2},
    scheduler=optim.lr_scheduler.OneCycleLR,
    scheduler_params={},
    scheduler_interval="step",
)
# %%
from src.training.metrics import IOU, positive_rate

# Simulate model output and labels
B, num_classes, H, W = 2, 11, 512, 512
dummy_logits = torch.randn(B, num_classes, H, W)
dummy_labels = torch.randint(0, num_classes, (B, H, W))

iou_mean, iou_building = IOU(dummy_logits, dummy_labels, logits=True)
building_rate = positive_rate(dummy_logits, logits=True)

print(f"Mean IoU:      {iou_mean:.4f}")
print(f"Building IoU:  {iou_building:.4f}")
print(f"Building rate: {building_rate:.4f}  (fraction of pixels predicted as building)")
# %%
