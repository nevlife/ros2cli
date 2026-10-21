# Copyright 2026 Open Source Robotics Foundation, Inc.
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

import subprocess
import sys

import pytest

CODE = """
import sys
from ros2cli.cli import main
assert 'rclpy' not in sys.modules
try:
    main(argv=['--help'])
except SystemExit:
    pass
with open('/proc/self/status') as f:
    print([line.split()[1] for line in f if line.startswith('FDSize:')][0])
"""


@pytest.mark.skipif(sys.platform != 'linux', reason='the fd table is grown on Linux only')
def test_fd_table_grown_before_rclpy_is_imported():
    out = subprocess.run(
        [sys.executable, '-c', CODE], check=True, capture_output=True, text=True).stdout
    assert int(out.split()[-1]) >= 1024
