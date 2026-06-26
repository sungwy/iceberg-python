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
"""Bucket-transform conformance: the Appendix B 32-bit hash that bucket[N] builds on."""

import os
import uuid as uuidmod
from decimal import Decimal
from typing import Any

import pytest
from _shared import FIXTURES, FIXTURES_PRESENT, load_jsonl, skip_if_absent

from pyiceberg.transforms import BucketTransform
from pyiceberg.types import PrimitiveType
from pyiceberg.utils.datetime import date_str_to_days, time_str_to_micros, timestamp_to_micros

pytestmark = skip_if_absent

# PyIceberg under-sizes the minimal two's-complement of byte-boundary decimals, so it
# hashes (and buckets) these to a different value than the spec fixes. Tracked in the
# open issue below; remove these entries when it lands and the cases XPASS.
BUCKET_XFAIL = {
    "hash-decimal-neg-1.28": "minimal-byte decimal serialization differs from spec; apache/iceberg-python#3522",
    "hash-decimal-neg-327.68": "minimal-byte decimal serialization differs from spec; apache/iceberg-python#3522",
    "hash-decimal-neg-83886.08": "minimal-byte decimal serialization differs from spec; apache/iceberg-python#3522",
}
_BUCKET_N = 2_000_003  # large prime; comparing bucket[N] avoids needing the raw hash API


def _physical_value(type_str: str, value: str) -> Any:
    """Convert a fixture's string value to the physical form PyIceberg buckets."""
    if type_str in ("int", "long"):
        return int(value)
    if type_str.startswith("decimal"):
        return Decimal(value)
    if type_str == "date":
        return date_str_to_days(value)
    if type_str == "time":
        return time_str_to_micros(value)
    if type_str == "timestamp":
        return timestamp_to_micros(value)
    if type_str == "string":
        return value
    if type_str == "uuid":
        return uuidmod.UUID(value)
    if type_str.startswith("fixed") or type_str == "binary":
        return bytes.fromhex(value)
    raise ValueError(type_str)


def _bucket_cases() -> list[Any]:
    if not FIXTURES_PRESENT:
        return []
    out: list[Any] = []
    for case in load_jsonl(os.path.join(FIXTURES, "transforms", "bucket", "cases.jsonl")):
        marks = [pytest.mark.xfail(reason=BUCKET_XFAIL[case["id"]], strict=False)] if case["id"] in BUCKET_XFAIL else []
        out.append(pytest.param(case, id=case["id"], marks=marks))
    return out


@pytest.mark.parametrize("case", _bucket_cases())
def test_bucket_hash(case: dict[str, Any]) -> None:
    source_type = PrimitiveType.model_validate(case["type"])
    bucket = BucketTransform(num_buckets=_BUCKET_N).transform(source_type)
    got = bucket(_physical_value(case["type"], case["value"]))
    assert got == (case["hash"] & 0x7FFFFFFF) % _BUCKET_N
