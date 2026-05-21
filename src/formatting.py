"""수치 표시: 조·억 단위 (원본 데이터 단위 = 억원, 1조 = 10,000억)."""

from __future__ import annotations

import math

import pandas as pd

JO_EOK_UNIT = 10_000


def fmt_jo_eok(value: float | None, *, signed: bool = False) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "-"

    v = float(value)
    prefix = ""
    if signed:
        if v > 0:
            prefix = "+"
        elif v < 0:
            prefix = "-"
        v = abs(v)
    elif v < 0:
        prefix = "-"
        v = abs(v)

    jo = int(v // JO_EOK_UNIT)
    eok = int(round(v - jo * JO_EOK_UNIT))
    if eok >= JO_EOK_UNIT:
        jo += eok // JO_EOK_UNIT
        eok = eok % JO_EOK_UNIT

    if jo == 0:
        return f"{prefix}{eok:,}억"
    if eok == 0:
        return f"{prefix}{jo:,}조"
    return f"{prefix}{jo:,}조 {eok:,}억"


def fmt_axis_tick(value: float) -> str:
    """차트 축 눈금: 1조 미만은 '500억', 이상은 '1.1조'."""
    v = float(value)
    if abs(v) >= JO_EOK_UNIT:
        return f"{v / JO_EOK_UNIT:.1f}조"
    return f"{int(round(v))}억"


def _nice_step(span: float, target: int = 5) -> float:
    if span <= 0:
        return 1.0
    raw = span / max(target, 1)
    magnitude = 10 ** math.floor(math.log10(raw))
    for mult in (1, 2, 5, 10):
        step = mult * magnitude
        if step >= raw:
            return step
    return magnitude * 10


def yaxis_ticks_jo_eok(
    y_min: float, y_max: float, *, target: int = 6, min_jo_step: float | None = None
) -> tuple[list[float], list[str]]:
    """억원 단위 값 범위에서 Plotly용 tickvals / ticktext 생성."""
    if y_max < y_min:
        y_min, y_max = y_max, y_min
    if math.isclose(y_min, y_max):
        y_max = y_min + 1.0

    padding = (y_max - y_min) * 0.08 or 1.0
    lo = y_min - padding
    hi = y_max + padding

    if hi >= JO_EOK_UNIT:
        lo_jo = lo / JO_EOK_UNIT
        hi_jo = hi / JO_EOK_UNIT
        span_jo = hi_jo - lo_jo
        step = _nice_step(span_jo, target)
        if min_jo_step is not None:
            step = max(step, min_jo_step)
        elif span_jo < 0.6:
            step = max(step, 0.2)
        if step < 0.1:
            step = 0.1
        start = math.floor(lo_jo / step) * step
        ticks_jo: list[float] = []
        t = start
        while t <= hi_jo + step * 0.001:
            if t >= lo_jo - step * 0.5:
                ticks_jo.append(round(t, 4))
            t += step
        if len(ticks_jo) < 2:
            ticks_jo = [lo_jo, hi_jo]
        tickvals = [t * JO_EOK_UNIT for t in ticks_jo]
        ticktext = [f"{t:.1f}조" for t in ticks_jo]
    else:
        step = _nice_step(hi - lo, target)
        if step < 10:
            step = 10.0
        start = math.floor(lo / step) * step
        tickvals = []
        t = start
        while t <= hi + step * 0.001:
            if t >= lo - step * 0.5:
                tickvals.append(t)
            t += step
        if len(tickvals) < 2:
            tickvals = [lo, hi]
        ticktext = [fmt_axis_tick(v) for v in tickvals]

    # 실제 데이터가 최댓값·최솟값을 넘지 않도록 눈금 확장
    if tickvals[-1] < y_max:
        step = (
            tickvals[-1] - tickvals[-2]
            if len(tickvals) > 1
            else max(tickvals[-1] * 0.1, 1.0)
        )
        v = tickvals[-1] + step
        while v < y_max:
            tickvals.append(v)
            ticktext.append(
                f"{v / JO_EOK_UNIT:.1f}조"
                if hi >= JO_EOK_UNIT
                else fmt_axis_tick(v)
            )
            v += step
        tickvals.append(v)
        ticktext.append(
            f"{v / JO_EOK_UNIT:.1f}조" if hi >= JO_EOK_UNIT else fmt_axis_tick(v)
        )

    if tickvals[0] > y_min:
        step = (
            tickvals[1] - tickvals[0]
            if len(tickvals) > 1
            else max(tickvals[0] * 0.1, 1.0)
        )
        v = tickvals[0] - step
        while v > y_min:
            tickvals.insert(0, v)
            ticktext.insert(
                0,
                f"{v / JO_EOK_UNIT:.1f}조"
                if hi >= JO_EOK_UNIT
                else fmt_axis_tick(v),
            )
            v -= step

    return tickvals, ticktext


def _jo_eok_axis_core(
    y_values: list[float],
    *,
    autoscale: bool,
    title: str,
    target_ticks: int = 6,
    pad_factor: float = 1.0,
    min_jo_step: float | None = None,
) -> dict:
    if not y_values:
        return {}

    y_min, y_max = min(y_values), max(y_values)
    tickvals, ticktext = yaxis_ticks_jo_eok(
        y_min, y_max, target=target_ticks, min_jo_step=min_jo_step
    )
    if len(tickvals) != len(ticktext):
        ticktext = [fmt_axis_tick(v) for v in tickvals]
    cfg: dict = {
        "tickmode": "array",
        "tickvals": tickvals,
        "ticktext": ticktext,
        "separatethousands": False,
    }

    if autoscale:
        span = y_max - y_min
        if span <= 0:
            span = max(abs(y_max) * 0.02, 1.0)
        pad = max(span * 0.1 * pad_factor, 1.0)
        cfg["range"] = [y_min - pad, y_max + pad]
        cfg["autorange"] = False
    else:
        cfg["autorange"] = True

    return cfg


def jo_eok_yaxis_kwargs(
    y_values: list[float],
    *,
    autoscale: bool = True,
    title: str = "수탁고 (조·억)",
    target_ticks: int = 6,
    pad_factor: float = 1.0,
    min_jo_step: float | None = None,
) -> dict:
    """fig.update_layout(yaxis / yaxis2) 용 — title 키 사용."""
    cfg = _jo_eok_axis_core(
        y_values,
        autoscale=autoscale,
        title=title,
        target_ticks=target_ticks,
        pad_factor=pad_factor,
        min_jo_step=min_jo_step,
    )
    if cfg:
        cfg["title"] = {"text": title}
    return cfg


def jo_eok_yaxes_update_kwargs(
    y_values: list[float],
    *,
    autoscale: bool = True,
    title: str = "수탁고 (조·억)",
    target_ticks: int = 6,
    pad_factor: float = 1.0,
    min_jo_step: float | None = None,
) -> dict:
    """fig.update_yaxes() 용."""
    cfg = _jo_eok_axis_core(
        y_values,
        autoscale=autoscale,
        title=title,
        target_ticks=target_ticks,
        pad_factor=pad_factor,
        min_jo_step=min_jo_step,
    )
    if cfg:
        cfg["title_text"] = title
    return cfg


# 하위 호환
jo_eok_yaxis_dict = jo_eok_yaxis_kwargs


def apply_jo_eok_yaxis(
    fig,
    y_values: list[float] | None = None,
    *,
    autoscale: bool = True,
    secondary_y: bool = False,
    axis_title: str = "수탁고 (조·억)",
) -> None:
    """Plotly Y축을 억/조 눈금으로 설정. autoscale 시 데이터 min~max에 맞춤."""
    if y_values is None:
        y_values = []
        for trace in fig.data:
            ys = getattr(trace, "y", None)
            if ys is not None:
                y_values.extend(float(v) for v in ys if v is not None and not pd.isna(v))

    cfg = jo_eok_yaxes_update_kwargs(y_values, autoscale=autoscale, title=axis_title)
    if not cfg:
        return

    if secondary_y:
        fig.update_yaxes(**cfg, secondary_y=True, showgrid=False, side="right")
    else:
        fig.update_yaxes(**cfg)
        fig.update_traces(cliponaxis=True)
