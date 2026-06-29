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
"""Shared helpers for the iceberg-testing conformance suite.

The cross-language fixtures are language-neutral: a static input plus the expected
result the spec fixes for it, pinned in the ``iceberg-testing/`` submodule. The
per-surface test modules walk them and run them against PyIceberg. Cases PyIceberg
does not satisfy yet are marked xfail in each module with a tracking issue; that
staged-adoption list is a consumer-side concern. The submodule must be checked out
(``git submodule update --init``); otherwise these tests skip.
"""

import json
import os
from typing import Any

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FIXTURES = os.path.join(ROOT, "iceberg-testing", "table-spec")
FIXTURES_PRESENT = os.path.isdir(FIXTURES)

skip_if_absent = pytest.mark.skipif(
    not FIXTURES_PRESENT,
    reason="iceberg-testing submodule not initialized (git submodule update --init --recursive)",
)


def load_jsonl(path: str) -> list[dict[str, Any]]:
    with open(path) as handle:
        return [json.loads(line) for line in handle if line.strip()]
