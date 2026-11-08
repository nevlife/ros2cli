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

from geometry_msgs.msg import Pose
from geometry_msgs.msg import PoseArray
import pytest
from ros2topic.eval import EvalException
from ros2topic.eval.message_filter import make_filter
from std_msgs.msg import String


def test_filter_reads_fields():
    assert make_filter("m.data == 'hi'")(String(data='hi'))
    assert not make_filter("m.data == 'hi'")(String(data='no'))
    assert make_filter('len(m.data) > 1 and m.data.startswith("h")')(String(data='hi'))


def test_filter_reads_fields_inside_message_arrays():
    poses = PoseArray(poses=[Pose()])
    poses.poses[0].position.x = 2.0
    assert make_filter('m.poses[0].position.x > 1.0')(poses)


@pytest.mark.parametrize('expression', [
    '__import__("os").system("true")',
    'open("/tmp/ros2topic_filter_marker", "w")',
    'm.__class__',
    '(lambda: 1)()',
    'exec("1")',
])
def test_filter_rejects_code_execution(expression):
    with pytest.raises(EvalException):
        make_filter(expression)(String(data='hi'))
