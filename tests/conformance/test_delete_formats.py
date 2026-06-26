# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Delete-file conformance: decode positional and equality delete files by field-id."""

import glob
import json
import os
from typing import Any

import pyarrow.parquet as pq
import pytest
from _shared import FIXTURES, skip_if_absent

pytestmark = skip_if_absent


def _encode(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, bytes):
        return value.hex().upper()
    return value


def _decode(path: str) -> list[dict[str, Any]]:
    table = pq.read_table(path)
    ids = {field.name: int((field.metadata or {})[b"PARQUET:field_id"]) for field in table.schema}
    cols = {name: table.column(name).to_pylist() for name in table.column_names}
    return [{str(ids[name]): _encode(cols[name][row]) for name in table.column_names} for row in range(table.num_rows)]


@pytest.mark.parametrize(
    "sidecar",
    sorted(glob.glob(os.path.join(FIXTURES, "delete-formats", "*", "*.parquet.expected.json"))),
    ids=lambda p: os.path.basename(os.path.dirname(p)),
)
def test_delete_file_decode(sidecar: str) -> None:
    with open(sidecar) as handle:
        expected = json.load(handle)
    data_file = os.path.join(os.path.dirname(sidecar), expected["delete-file"])
    assert _decode(data_file) == expected["decoded-rows"]
