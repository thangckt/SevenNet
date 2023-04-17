from typing import List, Dict, Callable

import torch.nn as nn
from e3nn.o3 import Irreps
from e3nn.nn import Gate
from e3nn.util.jit import compile_mode

import sevenn._keys as KEY
from sevenn._const import AtomGraphDataType


@compile_mode('script')
class EquivariantGate(nn.Module):
    """
    To 'gate' specific irreps, it needs additional scalars(irreps_gates).
    in e3nn, it does not specify which dim is this additional scalar at forward stage
    it just require 'new' irreps_in which includes this additional
    scalar dimension in tensor. Nequip prepare this additional scalar by
    second self-interaction at interaction_block.

    wrapper of e3nn.nn Gate (equivariant-nonlinear gate for irreps)
    required irreps_in for Gate forward is determined after instantiation
    of this class
    see
    https://docs.e3nn.org/en/stable/api/nn/nn_gate.html
    in nequip, result of convolution and self-interaction linear2
    is directly used for irreps_gates
    """
    def __init__(
        self,
        irreps_x: Irreps,
        act_scalar_dict: Dict[int, Callable],
        act_gate_dict: Dict[int, Callable],
        data_key_x: str = KEY.NODE_FEATURE,
    ):
        super().__init__()
        self.KEY_X = data_key_x

        parity_mapper = {"e": 1, "o": -1}
        act_scalar_dict = {parity_mapper[k]: v for k, v in act_scalar_dict.items()}
        act_gate_dict = {parity_mapper[k]: v for k, v in act_gate_dict.items()}

        irreps_gated_elem = []
        irreps_scalars_elem = []
        for mul, irreps in irreps_x:
            if irreps.l > 0:
                irreps_gated_elem.append((mul, irreps))
            else:
                irreps_scalars_elem.append((mul, irreps))
        irreps_scalars = Irreps(irreps_scalars_elem)
        irreps_gated = Irreps(irreps_gated_elem)

        # determine whether this scalar is odd or even
        # in gates, whether scalar is odd or even is not important but it should be
        # found in irreps_x to operate
        irreps_gates_parity = 1 if "0e" in irreps_scalars else -1
        irreps_gates = \
            Irreps([(mul, (0, irreps_gates_parity)) for mul, _ in irreps_gated])

        act_scalars = [act_scalar_dict[p] for mul, (l, p) in irreps_scalars]
        act_gates = [act_gate_dict[p] for mul, (l, p) in irreps_gates]

        self.gate = \
            Gate(irreps_scalars, act_scalars, irreps_gates, act_gates, irreps_gated)
        self.required_irreps_in = self.gate.irreps_in

    def get_gate_irreps_in(self):
        """
        user must call this function to get adequate irreps in for forward
        """
        return self.gate.irreps_in

    def forward(self, data: AtomGraphDataType) -> AtomGraphDataType:
        data[self.KEY_X] = self.gate(data[self.KEY_X])
        return data


def main():
    _ = 1


if __name__ == "__main__":
    main()
