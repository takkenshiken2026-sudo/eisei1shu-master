#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第一種衛生管理者 知識ハブ CSV 統合出力（S30 + S31 …）."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.write_eisei1shu_hub_s30 import DATA, HEADER_COMPARE, HEADER_MISTAKES, HEADER_NUMBERS  # noqa: E402
from tools.write_eisei1shu_hub_s30_content import COMPARISONS as C30, MISTAKES as M30, NUMBERS as N30  # noqa: E402
from tools.write_eisei1shu_hub_s31_content import (  # noqa: E402
    COMPARISONS_ADD,
    MISTAKES_ADD,
    NUMBERS_ADD,
)
from tools.write_eisei1shu_hub_s32_content import (  # noqa: E402
    COMPARISONS_ADD as COMPARISONS_ADD_S32,
    MISTAKES_ADD as MISTAKES_ADD_S32,
    NUMBERS_ADD as NUMBERS_ADD_S32,
)
from tools.write_eisei1shu_hub_s33_content import (  # noqa: E402
    COMPARISONS_ADD as COMPARISONS_ADD_S33,
    MISTAKES_ADD as MISTAKES_ADD_S33,
    NUMBERS_ADD as NUMBERS_ADD_S33,
)
from tools.write_eisei1shu_hub_s34_content import (  # noqa: E402
    COMPARISONS_ADD as COMPARISONS_ADD_S34,
    MISTAKES_ADD as MISTAKES_ADD_S34,
    NUMBERS_ADD as NUMBERS_ADD_S34,
)
from tools.write_eisei1shu_hub_s35_content import (  # noqa: E402
    COMPARISONS_ADD as COMPARISONS_ADD_S35,
    MISTAKES_ADD as MISTAKES_ADD_S35,
    NUMBERS_ADD as NUMBERS_ADD_S35,
)
from tools.write_eisei1shu_hub_s36_content import (  # noqa: E402
    COMPARISONS_ADD as COMPARISONS_ADD_S36,
    MISTAKES_ADD as MISTAKES_ADD_S36,
    NUMBERS_ADD as NUMBERS_ADD_S36,
)
from tools.write_eisei1shu_hub_s37_content import (  # noqa: E402
    COMPARISONS_ADD as COMPARISONS_ADD_S37,
    MISTAKES_ADD as MISTAKES_ADD_S37,
    NUMBERS_ADD as NUMBERS_ADD_S37,
)
from tools.write_eisei1shu_hub_s38_content import (  # noqa: E402
    COMPARISONS_ADD as COMPARISONS_ADD_S38,
    MISTAKES_ADD as MISTAKES_ADD_S38,
    NUMBERS_ADD as NUMBERS_ADD_S38,
)
from tools.write_eisei1shu_hub_s39_content import (  # noqa: E402
    COMPARISONS_ADD as COMPARISONS_ADD_S39,
    MISTAKES_ADD as MISTAKES_ADD_S39,
    NUMBERS_ADD as NUMBERS_ADD_S39,
)
from tools.write_eisei1shu_hub_s40_content import (  # noqa: E402
    COMPARISONS_ADD as COMPARISONS_ADD_S40,
    MISTAKES_ADD as MISTAKES_ADD_S40,
    NUMBERS_ADD as NUMBERS_ADD_S40,
)
from tools.write_eisei1shu_hub_s41_content import (  # noqa: E402
    COMPARISONS_ADD as COMPARISONS_ADD_S41,
    MISTAKES_ADD as MISTAKES_ADD_S41,
    NUMBERS_ADD as NUMBERS_ADD_S41,
)
from tools.write_eisei1shu_hub_s42_content import (  # noqa: E402
    COMPARISONS_ADD as COMPARISONS_ADD_S42,
    MISTAKES_ADD as MISTAKES_ADD_S42,
    NUMBERS_ADD as NUMBERS_ADD_S42,
)
from tools.write_eisei1shu_hub_s43_content import (  # noqa: E402
    COMPARISONS_ADD as COMPARISONS_ADD_S43,
    MISTAKES_ADD as MISTAKES_ADD_S43,
    NUMBERS_ADD as NUMBERS_ADD_S43,
)
from tools.write_eisei1shu_hub_s44_content import (  # noqa: E402
    COMPARISONS_ADD as COMPARISONS_ADD_S44,
    MISTAKES_ADD as MISTAKES_ADD_S44,
    NUMBERS_ADD as NUMBERS_ADD_S44,
)
from tools.write_eisei1shu_hub_premium_faqs import apply_all as apply_premium_faqs  # noqa: E402
from tools.hub_merge_data import merge_rows, write_hub_csvs  # noqa: E402


def main() -> None:
    write_hub_csvs(
        DATA,
        header_compare=HEADER_COMPARE,
        header_numbers=HEADER_NUMBERS,
        header_mistakes=HEADER_MISTAKES,
        comparisons=merge_rows(
            C30,
            COMPARISONS_ADD,
            COMPARISONS_ADD_S32,
            COMPARISONS_ADD_S33,
            COMPARISONS_ADD_S34,
            COMPARISONS_ADD_S35,
            COMPARISONS_ADD_S36,
            COMPARISONS_ADD_S37,
            COMPARISONS_ADD_S38,
            COMPARISONS_ADD_S39,
            COMPARISONS_ADD_S40,
            COMPARISONS_ADD_S41,
            COMPARISONS_ADD_S42,
            COMPARISONS_ADD_S43,
            COMPARISONS_ADD_S44,
        ),
        numbers=merge_rows(
            N30,
            NUMBERS_ADD,
            NUMBERS_ADD_S32,
            NUMBERS_ADD_S33,
            NUMBERS_ADD_S34,
            NUMBERS_ADD_S35,
            NUMBERS_ADD_S36,
            NUMBERS_ADD_S37,
            NUMBERS_ADD_S38,
            NUMBERS_ADD_S39,
            NUMBERS_ADD_S40,
            NUMBERS_ADD_S41,
            NUMBERS_ADD_S42,
            NUMBERS_ADD_S43,
            NUMBERS_ADD_S44,
        ),
        mistakes=merge_rows(
            M30,
            MISTAKES_ADD,
            MISTAKES_ADD_S32,
            MISTAKES_ADD_S33,
            MISTAKES_ADD_S34,
            MISTAKES_ADD_S35,
            MISTAKES_ADD_S36,
            MISTAKES_ADD_S37,
            MISTAKES_ADD_S38,
            MISTAKES_ADD_S39,
            MISTAKES_ADD_S40,
            MISTAKES_ADD_S41,
            MISTAKES_ADD_S42,
            MISTAKES_ADD_S43,
            MISTAKES_ADD_S44,
        ),
        apply_premium=apply_premium_faqs,
    )


if __name__ == "__main__":
    main()
