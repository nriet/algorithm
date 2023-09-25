import pytorch_lightning as pl
import torch
from torch import nn


class Attn_Ch(pl.LightningModule):

    def __init__(self, channels, ratio=8):
        super().__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)
        self.sharedMLP = nn.Sequential(
            nn.Conv2d(channels, channels//ratio, 1),
            nn.Tanh(),
            nn.Conv2d(channels//ratio, channels, 1)
        )
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        avgout = self.sharedMLP(self.avg_pool(x))
        maxout = self.sharedMLP(self.max_pool(x))
        return self.sigmoid(avgout + maxout)


class Attn_Pos(pl.LightningModule):

    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2d(2, 1, 3, padding=1, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        avgout = torch.mean(x, dim=1, keepdim=True)
        maxout, _ = torch.max(x, dim=1, keepdim=True)
        x = torch.cat([avgout, maxout], dim=1)
        x = self.conv(x)
        return self.sigmoid(x)


class Attn_Block(pl.LightningModule):

    def __init__(self, channels):
        super().__init__()
        self.attn_ch = Attn_Ch(channels)
        self.attn_pos = Attn_Pos()

    def forward(self, x):
        x = self.attn_ch(x) * x
        x = self.attn_pos(x) * x
        return x
