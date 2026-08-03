#!/usr/bin/env python3
"""Fetch and verify the KOSPI OHLC inputs used by the 2026-07-31 report."""

import ast
from urllib.request import Request, urlopen

URL = (
    "https://api.finance.naver.com/siseJson.naver?symbol=KOSPI&requestType=1"
    "&startTime=20260724&endTime=20260731&timeframe=day"
)


def main() -> None:
    request = Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    text = urlopen(request, timeout=30).read().decode("utf-8")
    # The endpoint uses a Python-literal-style array with single-quoted headers.
    rows = ast.literal_eval(text.strip())
    header = [str(value).strip() for value in rows[0]]
    records = [dict(zip(header, row)) for row in rows[1:]]
    for record in records:
        print(record)

    by_date = {str(record["날짜"]): record for record in records}
    assert float(by_date["20260729"]["저가"]) == 5262.77
    assert float(by_date["20260731"]["시가"]) == 5657.79
    assert float(by_date["20260724"]["종가"]) == 6690.62


if __name__ == "__main__":
    main()
