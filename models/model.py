import torch
import torch.nn as nn
import torch.nn.functional as F
from .operations import ConvBlock, ImagePoolingSequencer
import numpy as np

class CRNN(nn.Module):

    def __init__(self,
                 num_input_channels,
                 num_output_labels,
                 rnn_units,  # type: int
                 rnn_layers,  # type: int
                 rnn_dropout,  # type: float
                 lin_dropout,  # type: float
                 vertical_text=False,
                 rnn_type=nn.LSTM,
                 height=None):
        super(CRNN, self).__init__()
        self._rnn_dropout = rnn_dropout
        self._lin_dropout = lin_dropout
        out_channels = [16,32,48,64,80]
        kernel_size = [3,3,3,3,3]
        stride = [1,1,1,1,1]
        dilation = [1,1,1,1,1]
        activation = [nn.LeakyReLU,nn.LeakyReLU,nn.LeakyReLU,nn.LeakyReLU,nn.LeakyReLU]
        dropout = [0,0,0.2,0.2,0.2]
        batchnorm = [True, True, True, True, True]
        poolsize = [(2, 2), (2, 2), (2, 2), (0, 0), (0,0)]
        #poolsize = [(2, 2), (0,0), (0,0), (0, 0), (0,0)]


        conv_blocks = []
        ni = num_input_channels
        for i in range(len(out_channels)):
            conv_blocks.append(
                ConvBlock(
                    in_channels=ni,
                    out_channels=out_channels[i],
                    kernel_size=kernel_size[i],
                    stride=stride[i],
                    dilation=dilation[i],
                    activation=activation[i],
                    poolsize=poolsize[i],
                    dropout=dropout[i],
                    batchnorm=batchnorm[i],
                )
            )
            ni = out_channels[i]
        self.conv = nn.Sequential(*conv_blocks)

        self.sequencer = ImagePoolingSequencer(
            sequencer=None, columnwise=not vertical_text, _fix_size=height
        )

        # Add bidirectional rnn
        self.rnn_units = rnn_units
        if rnn_units == 100:
            print("MHA")
            embed_dim = ni * self.sequencer.fix_size
            num_heads = 8
            # self.mha = nn.MultiheadAttention(embed_dim, num_heads)
            encoder_layer = nn.TransformerEncoderLayer(d_model=embed_dim, nhead=num_heads)
            self.trans = nn.TransformerEncoder(encoder_layer, 3)
            self.linear = nn.Linear(embed_dim, num_output_labels)
        else:
            self.rnn = rnn_type(
                ni * self.sequencer.fix_size,
                rnn_units,
                rnn_layers,
                dropout=rnn_dropout,
                bidirectional=True,
                batch_first=False,
            )
            self.rnn.flatten_parameters()
            # Add final linear layer
            self.linear = nn.Linear(2 * rnn_units, num_output_labels)
            self.rnn.flatten_parameters()
            # Add final linear layer
            self.linear = nn.Linear(2 * rnn_units, num_output_labels)

    def dropout(self, x, p):
        if 0.0 < p < 1.0:
            cls = None
            d = F.dropout(x, p=p, training=self.training)
            return d
        else:
            return x

    def forward(self, x):
        #self.check(x, inp="input")
        #print(x.size())
        x = self.conv(x)
        #print(x.size())
        #self.check(x, inp="After conv")

        x = self.sequencer(x)
        #print(x.size())
        #self.check(x, inp="After seq")
        #x = self.dropout(x, p=self._rnn_dropout)
        if self.rnn_units == 100:
            x = self.trans(x)
        else:
            x, _ = self.rnn(x)
            x = self.dropout(x, p=self._lin_dropout)
        #print(x.size())
        #self.check(x, inp="After rnn")
        x = self.linear(x)
        #print(x.size())
        return x

    def check(self, x, inp="x"):
        if x is not None:
            if torch.sum(torch.isnan(x)).item() > 0:
                raise ValueError("NaN values in {}".format(inp))
            if torch.sum(torch.isinf(x)).item() > 0:
                raise ValueError("+/-Inf in {}".format(inp))
    @staticmethod
    def get_conv_output_size(
            size,  # type: Tuple[int, int]
            cnn_kernel_size,  # type: Sequence[Union[int, Tuple[int, int]]]
            cnn_stride,  # type: Sequence[Union[int, Tuple[int, int]]]
            cnn_dilation,  # type: Sequence[Union[int, Tuple[int, int]]]
            cnn_poolsize,  # type: Sequence[Union[int, Tuple[int, int]]]
    ):
        size_h, size_w = size
        for ks, st, di, ps in zip(
                cnn_kernel_size, cnn_stride, cnn_dilation, cnn_poolsize
        ):
            size_h = ConvBlock.get_output_size(
                size_h, kernel_size=ks[0], dilation=di[0], stride=st[0], poolsize=ps[0]
            )
            size_w = ConvBlock.get_output_size(
                size_w, kernel_size=ks[1], dilation=di[1], stride=st[1], poolsize=ps[1]
            )
        return size_h, size_w