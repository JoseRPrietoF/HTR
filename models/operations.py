import torch, re
import torch.nn as nn
import torch.nn.functional as F

class ConvBlock(nn.Module):
    def __init__(
        self,
        in_channels,  # type: int
        out_channels,  # type: int
        kernel_size=3,  # type: Union[int, Tuple[int, int]]
        stride=1,  # type: Union[int, Tuple[int, int]]
        dilation=1,  # type: Union[int, Tuple[int, int]]
        activation=nn.LeakyReLU,  # type: Optional[nn.Module]
        poolsize=None,  # type: Optional[Union[int, Tuple[int, int]]]
        dropout=None,  # type: Optional[float]
        batchnorm=False,  # type: bool
    ):
        # type: (...) -> None
        super(ConvBlock, self).__init__()

        self.dropout = dropout
        self.in_channels = in_channels
        self.poolsize = poolsize

        if not isinstance(kernel_size, (list, tuple)):
            kernel_size = (kernel_size, kernel_size)
        if not isinstance(dilation, (list, tuple)):
            dilation = (dilation,) * 2
        # Add Conv2d layer (compute padding to perform a full convolution).
        self.conv = nn.Conv2d(
            in_channels,
            out_channels,
            kernel_size,
            stride=stride,
            padding=tuple(
                (kernel_size[dim] - 1) // 2 * dilation[dim] for dim in (0, 1)
            ),
            dilation=dilation,
            # Note: If batchnorm is used, the bias does not affect the output
            # of the unit.
            bias=not batchnorm,
        )

        # Add Batch normalization
        self.batchnorm = nn.BatchNorm2d(out_channels) if batchnorm else None

        # Activation function must support inplace operations.
        self.activation = activation(inplace=False) if activation else None

        # Add maxpool layer
        self.pool = nn.MaxPool2d(poolsize) if self.poolsize and self.poolsize[0]>0 and \
        self.poolsize[1] > 0 else None

    def forward(self, x):
        # type: (Union[Tensor, PaddedTensor]) -> Union[Tensor, PaddedTensor]

        xs = None
        assert x.size(1) == self.in_channels, (
            "Input image depth ({}) does not match the "
            "expected ({})".format(x.size(1), self.in_channels)
        )

        if self.dropout and 0.0 < self.dropout < 1.0:
            x = F.dropout(x, p=self.dropout, training=self.training)

        x = self.conv(x)

        if self.batchnorm:
            x = self.batchnorm(x)

        if self.activation:
            x = self.activation(x)

        if self.pool:
            x = self.pool(x)

        return x


class ImagePoolingSequencer(torch.nn.Module):
    def __init__(self, sequencer=None, columnwise=True, _fix_size=5):
        super(ImagePoolingSequencer, self).__init__()

        self._fix_size = _fix_size
        self._columnwise = columnwise
        #self._fix_size = int(m.group(2))

        # Assume that the images have a fixed height
        # (or width if columnwise=False)
        self.sequencer = None

    @property
    def columnwise(self):
        return self._columnwise

    @property
    def fix_size(self):
        return self._fix_size

    def forward(self, x):
        if self._columnwise and x.size(-2) != self._fix_size:
            raise ValueError(
                "Input images must have a fixed height of {} pixels, "
                "size is {} - height is {}".format(self._fix_size, str(x.size()), str(x.size(-2)))
            )
        elif not self._columnwise and x.size(-1) != self._fix_size:
            raise ValueError(
                "Input images must have a fixed width of {} pixels, "
                "size is {}".format(self._fix_size, str(x.size()))
            )

        x = image_to_sequence(x, columnwise=self._columnwise, return_packed=True)
        return x

def image_to_sequence(x, columnwise=True, return_packed=False):
    x, xs = (x, None)

    if x.dim() == 2:
        x = x.view(1, 1, x.size(0), x.size(1))
    elif x.dim() == 3:
        x = x.view(1, x.size(0), x.size(1), x.size(2))
    assert x.dim() == 4

    n, c, h, w = x.size()
    if columnwise:
        x = x.permute(3, 0, 1, 2).contiguous().view(w, n, h * c)
    else:
        x = x.permute(2, 0, 1, 3).contiguous().view(h, n, w * c)

    return x

