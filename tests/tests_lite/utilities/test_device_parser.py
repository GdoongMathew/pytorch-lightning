# Copyright The PyTorch Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from unittest import mock

import pytest
import torch

from lightning_lite.accelerators.cpu import parse_cpu_cores
from lightning_lite.accelerators.cuda import is_cuda_available, num_cuda_devices
from lightning_lite.utilities import device_parser
from lightning_lite.utilities.exceptions import MisconfigurationException

_PRETEND_N_OF_GPUS = 16


@pytest.mark.parametrize(
    ["devices", "expected_root_gpu"],
    [
        pytest.param(None, None, id="No gpus, expect gpu root device to be None"),
        pytest.param([0], 0, id="Oth gpu, expect gpu root device to be 0."),
        pytest.param([1], 1, id="1st gpu, expect gpu root device to be 1."),
        pytest.param([3], 3, id="3rd gpu, expect gpu root device to be 3."),
        pytest.param([1, 2], 1, id="[1, 2] gpus, expect gpu root device to be 1."),
    ],
)
def test_determine_root_gpu_device(devices, expected_root_gpu):
    assert device_parser.determine_root_gpu_device(devices) == expected_root_gpu


@pytest.mark.parametrize(
    ["devices", "expected_gpu_ids"],
    [
        (None, None),
        (0, None),
        ([], None),
        (1, [0]),
        (3, [0, 1, 2]),
        pytest.param(-1, list(range(_PRETEND_N_OF_GPUS)), id="-1 - use all gpus"),
        ([0], [0]),
        ([1, 3], [1, 3]),
        ((1, 3), [1, 3]),
        ("0", None),
        ("3", [0, 1, 2]),
        ("1, 3", [1, 3]),
        ("2,", [2]),
        pytest.param("-1", list(range(_PRETEND_N_OF_GPUS)), id="'-1' - use all gpus"),
    ],
)
@mock.patch("lightning_lite.accelerators.cuda.num_cuda_devices", return_value=_PRETEND_N_OF_GPUS)
def test_parse_gpu_ids(_, devices, expected_gpu_ids):
    assert device_parser.parse_gpu_ids(devices, include_cuda=True) == expected_gpu_ids


@pytest.mark.parametrize("devices", [0.1, -2, False, [-1], [None], ["0"], [0, 0]])
@mock.patch("lightning_lite.accelerators.cuda.num_cuda_devices", return_value=_PRETEND_N_OF_GPUS)
def test_parse_gpu_fail_on_unsupported_inputs(_, devices):
    with pytest.raises(MisconfigurationException):
        device_parser.parse_gpu_ids(devices, include_cuda=True)


@pytest.mark.parametrize("devices", [[1, 2, 19], -1, "-1"])
@mock.patch("lightning_lite.accelerators.cuda.num_cuda_devices", return_value=0)
def test_parse_gpu_fail_on_non_existent_id(_, devices):
    with pytest.raises(MisconfigurationException):
        device_parser.parse_gpu_ids(devices, include_cuda=True)


@mock.patch("lightning_lite.accelerators.cuda.num_cuda_devices", return_value=_PRETEND_N_OF_GPUS)
def test_parse_gpu_fail_on_non_existent_id_2(_):
    with pytest.raises(MisconfigurationException):
        device_parser.parse_gpu_ids([1, 2, 19], include_cuda=True)


@pytest.mark.parametrize("devices", [-1, "-1"])
@mock.patch("lightning_lite.accelerators.cuda.num_cuda_devices", return_value=0)
def test_parse_gpu_returns_none_when_no_devices_are_available(_, devices):
    with pytest.raises(MisconfigurationException):
        device_parser.parse_gpu_ids(devices, include_cuda=True)


@pytest.mark.skipif(
    "fork" in torch.multiprocessing.get_all_start_methods(), reason="Requires platform without forking support"
)
@mock.patch("torch.cuda.is_available", return_value=True)
@mock.patch("torch.cuda.device_count", return_value=2)
def test_num_cuda_devices_without_forking(*_):
    """This merely tests that on platforms without fork support our helper functions fall back to the default
    implementation for determining cuda availability."""
    assert is_cuda_available()
    assert num_cuda_devices() == 2


@pytest.mark.parametrize("devices", ([3], -1))
def test_invalid_devices_with_cpu_accelerator(devices):
    """Test invalid device flag raises MisconfigurationException."""
    with pytest.raises(TypeError, match="should be an int > 0"):
        parse_cpu_cores(devices)