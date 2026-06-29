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
"""Type-string conformance: parse the input and re-serialize to the canonical form."""

import glob
import os
from typing import Any

import pytest
from _shared import FIXTURES, FIXTURES_PRESENT, load_jsonl, skip_if_absent

from pyiceberg.exceptions import ValidationError
from pyiceberg.types import DecimalType, FixedType, PrimitiveType

pytestmark = skip_if_absent

# Cases PyIceberg does not satisfy yet (consumer-side staged-adoption list). Each
# reason links the open issue that tracks the divergence; when it lands the case
# passes (reported XPASS, since these xfails are non-strict) and the entry here can
# be removed. fixed[...] whitespace has no dedicated issue; it is the same
# type-string-whitespace class as the decimal case.
TYPE_XFAIL = {
    "decimal-space-around-params": "rejects optional whitespace around decimal params; apache/iceberg#16798",
    "fixed-space-around": "rejects whitespace inside fixed[...] brackets; type-string whitespace, cf. apache/iceberg#16798",
    "geometry-default": "geometry type not supported yet; apache/iceberg-python#3004",
    "geometry-unquoted-crs": "geometry type not supported yet; apache/iceberg-python#3004",
    "decimal-precision-over-max": "does not reject decimal precision > 38 (spec: precision must be 38 or less; Java rejects it)",
}


def _type_fields(parsed: PrimitiveType) -> dict[str, int]:
    if isinstance(parsed, DecimalType):
        return {"precision": parsed.precision, "scale": parsed.scale}
    if isinstance(parsed, FixedType):
        return {"length": parsed.root}
    return {}


def _type_cases(*, accept: bool) -> list[Any]:
    if not FIXTURES_PRESENT:
        return []
    out: list[Any] = []
    for path in sorted(glob.glob(os.path.join(FIXTURES, "types", "*", "cases.jsonl"))):
        for case in load_jsonl(path):
            if case["accept"] is not accept:
                continue
            marks = [pytest.mark.xfail(reason=TYPE_XFAIL[case["id"]], strict=False)] if case["id"] in TYPE_XFAIL else []
            out.append(pytest.param(case, id=case["id"], marks=marks))
    return out


@pytest.mark.parametrize("case", _type_cases(accept=True))
def test_type_string_accepted(case: dict[str, Any]) -> None:
    parsed = PrimitiveType.model_validate(case["input"])
    assert _type_fields(parsed) == case["parsed"]
    assert str(parsed) == case["canonical"]


@pytest.mark.parametrize("case", _type_cases(accept=False))
def test_type_string_rejected(case: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        PrimitiveType.model_validate(case["input"])
