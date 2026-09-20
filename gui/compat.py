# -*- coding: utf-8 -*-
"""
Compatibilité entre versions de Streamlit.

`use_container_width=True` est déprécié (Streamlit >= 1.50) au profit de `width="stretch"`,
mais les versions plus anciennes ne connaissent pas encore `width="stretch"`.
Utilisation : st.dataframe(df, **STRETCH)
"""

import streamlit as st


def _supports_width_stretch() -> bool:
    try:
        major, minor = (int(part) for part in st.__version__.split(".")[:2])
    except ValueError:
        return True  # version inhabituelle : on suppose une version récente
    return (major, minor) >= (1, 50)


STRETCH = {"width": "stretch"} if _supports_width_stretch() else {"use_container_width": True}
