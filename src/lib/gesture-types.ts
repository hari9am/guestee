export type View =
  "overview" | "gestures" | "training" | "history" | "settings";

export type MappingType = "launch" | "action";

export type Mapping = {
  id: string;
  name: string;
  symbol: string;
  type: MappingType;
  app: string;       // used when type="launch"
  target: string;    // used when type="launch" + website
  action: string;    // used when type="action"
  enabled: boolean;
  samples: number;
};

export type Launch = {
  id: string;
  gesture: string;
  app: string;
  time: string;
  confidence: number;
  success: boolean;
  action?: "open" | "close";
};

export type Settings = {
  confidence: number;
  hold: number;
  cooldown: number;
  camera: number;
};

export type Status = {
  listening: boolean;
  camera: boolean;
  camera_permission: boolean;
  previewing: boolean;
  gesture: string | null;
  confidence: number;
  model: boolean;
  accuracy: number | null;
  mappings: Mapping[];
  history: Launch[];
  settings: Settings;
  recording: string | null;
  training: boolean;
  error: string | null;
};

// Control actions mirrored from Companion/control.py
export const CONTROL_ACTIONS: { id: string; label: string }[] = [
  { id: "cursor_move",      label: "Move cursor + click + scroll (all-in-one)" },
  { id: "left_click",       label: "Left click — pinch index + thumb" },
  { id: "right_click",      label: "Right click — pinch middle + thumb" },
  { id: "double_click",     label: "Double click — fast double pinch" },
  { id: "scroll_up",        label: "Scroll — index + middle up, move wrist" },
  { id: "scroll_down",      label: "Scroll down — index + middle, move down" },
  { id: "drag",             label: "Drag — fist to hold, open hand to release" },
  { id: "volume_up",        label: "Volume up — thumb + index, move hand up" },
  { id: "volume_down",      label: "Volume down — thumb + index, move hand down" },
  { id: "mute",             label: "Mute / unmute" },
  { id: "media_play_pause", label: "Play / pause — shaka (thumb + pinky)" },
  { id: "media_next",       label: "Next track — index only, pointing right" },
  { id: "media_prev",       label: "Previous track — thumb only" },
  { id: "screenshot",       label: "Screenshot — peace sign held 2 seconds" },
  { id: "zoom_in",          label: "Zoom in — spread thumb + index apart" },
  { id: "zoom_out",         label: "Zoom out — pinch thumb + index close" },
];

export const initialMappings: Mapping[] = [
  { id: "G01", name: "Peace sign",    symbol: "✌️", type: "launch", app: "YouTube", target: "https://www.youtube.com", action: "", enabled: true, samples: 0 },
  { id: "G02", name: "Closed fist",   symbol: "✊", type: "launch", app: "VS Code",  target: "",                       action: "", enabled: true, samples: 0 },
  { id: "G03", name: "Thumbs up",     symbol: "👍", type: "launch", app: "Spotify",  target: "",                       action: "", enabled: true, samples: 0 },
  { id: "G04", name: "Three fingers", symbol: "🤟", type: "launch", app: "Chrome",   target: "",                       action: "", enabled: true, samples: 0 },
];

export const initialSettings: Settings = {
  confidence: 90,
  hold: 1.5,
  cooldown: 5,
  camera: 0,
};
