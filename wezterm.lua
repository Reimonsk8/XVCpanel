local wezterm = require "wezterm"
local config = wezterm.config_builder()

-- Collapse / show / hide the inactive panes:
--   F9  - zoom the focused pane (other panes collapse out of the way)
--   F10 - zoom the preview pane (top-right)
--   F11 - zoom the control panel (bottom-right)
-- Each toggles back to the full 3-pane layout.
config.keys = {
  { key = "F9", mods = "NONE", action = wezterm.action.TogglePaneZoomState },
}

-- simple, cinema-dark, no OS titling noise
config.color_scheme = "Dark"
config.font_size = 11.0
config.hide_tab_bar_if_only_one_tab = true
config.window_close_confirmation = "NeverPrompt"

return config