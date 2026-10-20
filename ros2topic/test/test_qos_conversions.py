# Copyright 2019 Amazon.com, Inc. or its affiliates. All rights reserved.
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

import time

import rclpy
from rclpy.duration import Duration

from ros2topic.api import qos_profile_from_short_keys
from ros2topic.api import sensor_qos_matching_publishers
from std_msgs.msg import Empty


def test_profile_conversion():
    profile = qos_profile_from_short_keys(
        'sensor_data', reliability='reliable', durability='transient_local',
        depth=10, history='keep_last', liveliness='manual_by_topic',
        liveliness_lease_duration_s=10.3)
    assert profile.durability == rclpy.qos.QoSDurabilityPolicy.TRANSIENT_LOCAL
    assert profile.reliability == rclpy.qos.QoSReliabilityPolicy.RELIABLE
    assert profile.depth == 10
    assert profile.history == rclpy.qos.QoSHistoryPolicy.KEEP_LAST
    assert profile.liveliness == rclpy.qos.QoSLivelinessPolicy.MANUAL_BY_TOPIC
    assert profile.liveliness_lease_duration == Duration(seconds=10.3)


def test_sensor_qos_follows_publisher_reliability():
    context = rclpy.context.Context()
    rclpy.init(context=context)
    node = rclpy.create_node('sensor_qos_test', context=context)

    def publishers_seen(count):
        end = time.monotonic() + 5
        while node.count_publishers('/sensor_qos_a') < count and time.monotonic() < end:
            time.sleep(0.01)

    try:
        reliable = rclpy.qos.QoSReliabilityPolicy.RELIABLE
        best_effort = rclpy.qos.QoSReliabilityPolicy.BEST_EFFORT
        assert sensor_qos_matching_publishers(node, '/sensor_qos_a').reliability == best_effort
        node.create_publisher(Empty, '/sensor_qos_a', 10)
        publishers_seen(1)
        assert sensor_qos_matching_publishers(node, '/sensor_qos_a').reliability == reliable
        node.create_publisher(Empty, '/sensor_qos_a', rclpy.qos.qos_profile_sensor_data)
        publishers_seen(2)
        assert sensor_qos_matching_publishers(node, '/sensor_qos_a').reliability == best_effort
        assert rclpy.qos.qos_profile_sensor_data.reliability == best_effort
    finally:
        node.destroy_node()
        rclpy.shutdown(context=context)
