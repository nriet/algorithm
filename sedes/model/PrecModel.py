import torch
from torch import nn
import torch.nn.functional as F
import pytorch_lightning as pl
from model.BasicBlock import BasicBlock
# from audtorch.metrics.functional import pearsonr
class PrecModel(pl.LightningModule):

    def __init__(self, hparams):
        super().__init__()
        num_ss_feature = 2 
        self.ss_embedding = nn.Sequential(
            nn.Linear(12, num_ss_feature),
            nn.Tanh()
        )
        channels, height, width = hparams.input_shape
        self.feature_extraction = nn.Sequential(
            BasicBlock(
                channels+num_ss_feature, hparams.kernels[0], height, width),
            BasicBlock(
                hparams.kernels[0], hparams.kernels[1], height//2, width//2),
            BasicBlock(
                hparams.kernels[1], hparams.kernels[2], height//4, width//4),
            BasicBlock(
                hparams.kernels[2], hparams.kernels[3], height//8, width//8),
            BasicBlock(
                hparams.kernels[3], hparams.kernels[4], height//16, width//16),
            nn.Flatten(),
            nn.Dropout(0.5),
        )
        num_nodes = (height // 32) * (width // 32)
        self.fc = nn.Sequential(
            nn.Linear(hparams.kernels[4]*num_nodes, hparams.num_features),
            nn.Tanh(),
        )
        self.pred = nn.Linear(hparams.num_features, hparams.num_outputs)
        self.fraction = hparams.fraction
        self.eof = hparams.eof
        self.decay = hparams.decay
        self.save_hyperparameters()
        if not hparams.warm_start:
            self.init_weights_()

    @staticmethod
    def add_model_args(parent_parser):
        parser = parent_parser.add_argument_group('PrecModel')
        parser.add_argument(
            '--input_shape', type=int, nargs=3,default=[13,80,120],
            help='Num of input shape (variables, lats, lons)'
        )
        parser.add_argument(
            '--kernels', type=int, nargs=5, default=[64, 128, 256, 512, 512],
            help='kernels of 5 CNN layers'
        )
        parser.add_argument(
            '--num_features', type=int, default=512,
            help='num of features after CNN layers'
        )
        parser.add_argument(
            '--num_outputs', type=int, default=50,
            help='num of output nodes'
        )
        parser.add_argument(
            '--decay', type=float, default=0.01,
            help='weight decay parameter in optimizer'
        )
        parser.add_argument(
            '--warm_start', action='store_true',
            help='initialize model with pretrained parameters'
        )
        return parent_parser

    def init_weights_(self):
        for module in self.modules():
            if isinstance(module, torch.nn.Conv2d):
                torch.nn.init.xavier_normal_(
                    module.weight, gain=torch.nn.init.calculate_gain('tanh'))
                if module.bias is not None:
                    torch.nn.init.zeros_(module.bias)
            elif isinstance(module, torch.nn.Linear):
                torch.nn.init.normal_(module.weight, 0, 0.01)
                torch.nn.init.zeros_(module.bias)
    def gen_ss_feature(self, month, shape):
        oh = F.one_hot(month.to(torch.int64), 12).float()
        feature = self.ss_embedding(oh)
        feature = feature[:, :, None, None].repeat(1, 1, shape[0], shape[1])
        return feature

    def forward(self, x,month):
        ss_feature = self.gen_ss_feature(month, x.shape[-2:])
        x = torch.cat([x, ss_feature], dim=1)
        x = self.feature_extraction(x)
        x = self.fc(x)
        x = self.pred(x)
        return x

    def weighted_loss(self, y_hat, y):
        if self.fraction is not None:
            mse = torch.square(y_hat - y) * self.fraction
            mse = (mse.sum(dim=1) / self.fraction.sum()).mean()
        else:
            mse = F.mse_loss(y_hat, y)
        return mse

    def training_step(self, batch, batch_idx):
        x, month,y = batch
        y_hat = self.forward(x,month)
        loss = self.weighted_loss(y_hat, y)
#        pcc = self.pcc_score(y_hat, y)
        self.log('train_loss', loss)
#        self.log('acc', pcc,prog_bar=True,on_step=True)
        return loss

    def validation_step(self, batch, batch_idx):
        x,month, y = batch
        y_hat = self.forward(x,month)
        loss = self.weighted_loss(y_hat, y)
#        pcc = self.pcc_score(y_hat, y)
        self.log('validation_loss', loss)
#        self.log('acc', pcc,prog_bar=True,on_step=True)
        return loss

    def test_step(self, batch, batch_idx):
        x,month, y = batch
        y_hat = self.forward(x,month)
        loss = self.weighted_loss(y_hat, y)
        self.log('test_loss', loss)
#        pcc = self.pcc_score(y_hat, y)
#        self.log("ACC", pcc)
        return loss

    def pcc_score(self, forecast, obs):
        pcc_avg = []
        for idx in range(forecast.shape[0]):
            pcc = (forecast[idx] * obs[idx]).sum()
            pcc /= torch.sqrt((forecast[idx]**2).sum() * (obs[idx]**2).sum())
            pcc_avg.append(pcc)
        pcc_avg = torch.stack(pcc_avg).mean()
        return pcc_avg

    def configure_optimizers(self):
        optimizer = torch.optim.AdamW(
            self.parameters(), weight_decay=self.decay)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, 'min', patience=2, threshold=1e-3,
            threshold_mode='abs', min_lr=1e-5, verbose=True)
        return {
            'optimizer': optimizer,
            'lr_scheduler': scheduler,
            'monitor': 'validation_loss'
        }

