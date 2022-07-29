"""Utility functions for lightning Frontends."""
# Todo: Refactor stream_lit and streamlit_base to use this functionality

from __future__ import annotations

import inspect
import os
import pydoc
from typing import Callable

from lightning_app.core.flow import LightningFlow
from lightning_app.utilities.state import AppState


def get_render_fn_from_environment(render_fn_name: str, render_fn_module_file: str) -> Callable:
    """Returns the render_fn function to serve in the Frontend."""
    module = pydoc.importfile(render_fn_module_file)
    return getattr(module, render_fn_name)


def _reduce_to_flow_scope(state: AppState, flow: str | LightningFlow) -> AppState:
    """Returns a new AppState with the scope reduced to the given flow."""
    flow_name = flow.name if isinstance(flow, LightningFlow) else flow
    flow_name_parts = flow_name.split(".")[1:]  # exclude root
    flow_state = state
    for part in flow_name_parts:
        flow_state = getattr(flow_state, part)
    return flow_state


def get_flow_state(flow: str) -> AppState:
    """Returns an AppState scoped to the current Flow.

    Returns:
        AppState: An AppState scoped to the current Flow.
    """
    app_state = AppState()
    app_state._request_state()  # pylint: disable=protected-access
    flow_state = _reduce_to_flow_scope(app_state, flow)
    return flow_state


def get_allowed_hosts() -> str:
    """Returns a comma separated list of host[:port] that should be allowed to connect."""
    # Todo: Improve this. I don't know how to find the specific host(s).
    # I tried but it did not work in cloud
    return "*"


def has_panel_autoreload() -> bool:
    """Returns True if the PANEL_AUTORELOAD environment variable is set to 'yes' or 'true'.

    Please note the casing of value does not matter
    """
    return os.environ.get("PANEL_AUTORELOAD", "no").lower() in ["yes", "y", "true"]


def get_frontend_environment(flow: str, render_fn_or_file: Callable | str, port: int, host: str) -> os._Environ:
    """Returns an _Environ with the environment variables for serving a Frontend app set.

    Args:
        flow (str): The name of the flow, for example root.lit_frontend
        render_fn (Callable): A function to render
        port (int): The port number, for example 54321
        host (str): The host, for example 'localhost'

    Returns:
        os._Environ: An environement
    """
    env = os.environ.copy()
    env["LIGHTNING_FLOW_NAME"] = flow
    env["LIGHTNING_RENDER_PORT"] = str(port)
    env["LIGHTNING_RENDER_ADDRESS"] = str(host)

    if isinstance(render_fn_or_file, str):
        env["LIGHTNING_RENDER_FILE"] = render_fn_or_file
    else:
        env["LIGHTNING_RENDER_FUNCTION"] = render_fn_or_file.__name__
        env["LIGHTNING_RENDER_MODULE_FILE"] = inspect.getmodule(render_fn_or_file).__file__

    return env


def is_running_locally() -> bool:
    """Returns True if the lightning app is running locally.

    This function can be used to determine if the app is running locally and provide a better developer experience.
    """
    return "LIGHTNING_APP_STATE_URL" not in os.environ