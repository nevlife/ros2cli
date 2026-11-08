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

"""Filter expressions for `ros2 topic echo --filter` and `ros2 topic hz --filter`."""

import re

from ros2topic.eval import base_eval_model, Expr
from rosidl_runtime_py.utilities import get_message

_SAFE_BUILTINS = [
    'abs', 'all', 'any', 'bin', 'bool', 'chr', 'divmod', 'enumerate', 'float',
    'format', 'hex', 'int', 'isinstance', 'len', 'list', 'max', 'min', 'ord',
    'pow', 'range', 'reversed', 'round', 'slice', 'sorted', 'str', 'sum', 'tuple',
    'zip', 'filter', 'dict', 'set', 'next',
]

_EXTRA_NODES = [
    'Call', 'Attribute', 'List', 'Tuple', 'Dict', 'Set', 'ListComp', 'DictComp',
    'SetComp', 'comprehension', 'Mult', 'Pow', 'Invert', 'Is', 'IsNot', 'FloorDiv',
]

_NESTED_TYPE = re.compile(r'^(?:sequence<)?([\w]+/(?:msg/)?[\w]+)')


def _field_names(msg_class, seen):
    """Return the field names of a message class and of all its nested messages."""
    if msg_class in seen:
        return []
    seen.add(msg_class)
    names = []
    for name, type_name in msg_class.get_fields_and_field_types().items():
        names.append(name)
        nested = _NESTED_TYPE.match(type_name)
        if nested:
            nested_type = nested.group(1)
            if '/msg/' not in nested_type:
                package, message = nested_type.split('/')
                nested_type = f'{package}/msg/{message}'
            names.extend(_field_names(get_message(nested_type), seen))
    return names


def _model_for(msg_class):
    model = base_eval_model.clone()
    model.nodes.extend(_EXTRA_NODES)
    model.allowed_functions.extend(_SAFE_BUILTINS)
    model.attributes.extend(name for name in dir(str) if not name.startswith('_'))
    model.attributes.extend(name for name in dir(list) if not name.startswith('_'))
    if hasattr(msg_class, 'get_fields_and_field_types'):
        model.attributes.extend(_field_names(msg_class, set()))
    return model


def make_filter(expression):
    """
    Return a function that evaluates `expression` with the message bound to `m`.

    The expression may only call a fixed set of built-in functions and read message
    fields and string or list methods, so it cannot run arbitrary code. It is checked
    against the type of the first message and compiled once.
    """
    compiled = {}

    def filter_fn(m):
        msg_class = type(m)
        if msg_class not in compiled:
            compiled[msg_class] = Expr(expression, model=_model_for(msg_class))
        return compiled[msg_class].safe_eval({'m': m})

    return filter_fn
