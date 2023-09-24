from torch import nn
from SEDES.model.CBAM import Attn_Block


class BasicBlock(nn.Module):

    def __init__(self, inchannels, outchannels, height, width,
                 groups=1, pool=True, cbam=True):
        super().__init__()
        layers = [
            nn.Conv2d(inchannels, outchannels, 3, padding=1, groups=groups),
            nn.Tanh(),
            nn.LayerNorm([outchannels, height, width]),
        ]
        if pool:
            layers.append(nn.AvgPool2d(2, 2))
        if cbam:
            layers.append(Attn_Block(outchannels))
        self.conv = nn.Sequential(*layers)

    def forward(self, x):
        x = self.conv(x)
        return x
