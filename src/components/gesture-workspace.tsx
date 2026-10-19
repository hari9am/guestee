import { useEffect, useRef, useState } from "react";
import { Link } from "@tanstack/react-router";
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  ArrowUpRight,
  Camera,
  Check,
  CheckCircle2,
  ChevronRight,
  Code2,
  Ellipsis,
  Fingerprint,
  Hand,
  History,
  Monitor,
  MousePointer2,
  Pause,
  Play,
  Plus,
  Settings2,
  ShieldCheck,
  Sparkles,
  Trash2,
  Video,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import previewImage from "@/assets/gesture-preview.jpg";
import { useGestures } from "./gesture-provider";
import { GestureShell } from "./gesture-shell";
import { type Mapping, type View, CONTROL_ACTIONS } from "@/lib/gesture-types";

function AppIcon({ app }: { app: string }) {
  const icons: Record<string, string> = {
    Spotify: "≋", Chrome: "◉", Edge: "⊕", Firefox: "◈", Brave: "◆",
    "VS Code": "⌥", Kiro: "✦", Cursor: "⊙", Windsurf: "〜",
    Word: "W", Excel: "X", PowerPoint: "P", Outlook: "✉",
    Teams: "T", Zoom: "Z", Discord: "D", Slack: "S", WhatsApp: "✆", Telegram: "✈",
    "Android Studio": "A", PyCharm: "Py", IntelliJ: "IJ", Eclipse: "⊗",
    "MongoDB Compass": "M", DBeaver: "DB", Postman: "↗",
    VLC: "▶", OBS: "⏺", Steam: "♨", "Epic Games": "⚡",
    Blender: "⬡", GIMP: "G", Figma: "◐", Tableau: "⊞",
    "Notepad++": "N+", Calculator: "#", "File Explorer": "📁", "Task Manager": "⚙",
    // action mapping pseudo-app
    cursor: "⊹",
  };
  return (
    <span
      className={`app-icon ${app.toLowerCase().replace(/[^a-z0-9]/g, "")}`}
      aria-hidden="true"
    >
      {app === "YouTube" ? (
        <Play size={12} fill="currentColor" />
      ) : app === "VS Code" ? (
        <Code2 size={16} />
      ) : (
        icons[app] ?? app.substring(0, 1)
      )}
    </span>
  );
}

function MappingCard({
  item,
  edit,
  onDelete,
}: {
  item: Mapping;
  edit: (item: Mapping) => void;
  onDelete: (item: Mapping) => void;
}) {
  return (
    <article className="mapping-card">
      <div className="mapping-main">
        <div className="gesture-symbol">
          {(item.type ?? "launch") === "action"
            ? <MousePointer2 size={18} className="text-primary" />
            : item.symbol}
        </div>
        <div className="mapping-name">
          <strong>{item.name}</strong>
          <small className="font-mono">
            {item.id} <span className="mx-1">·</span>{" "}
            {item.samples ? `${item.samples} samples` : "Not trained"}
          </small>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            aria-label={`Edit ${item.name}`}
            onClick={() => edit(item)}
          >
            <Ellipsis />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 text-destructive hover:text-destructive"
            aria-label={`Delete ${item.name}`}
            onClick={() => onDelete(item)}
          >
            <Trash2 size={13} />
          </Button>
        </div>
      </div>
      <div className="mapping-target">
        <AppIcon app={(item.type ?? "launch") === "action" ? "cursor" : item.app} />
        <span>{(item.type ?? "launch") === "action" ? (CONTROL_ACTIONS.find(a => a.id === item.action)?.label ?? item.action) : item.app}</span>
        <ArrowRight size={11} className="mapping-action" />
        <span className={`text-[9px] ${item.enabled ? "text-success" : "text-muted-foreground"}`}>
          {(item.type ?? "launch") === "action" ? "Action" : item.enabled ? "Enabled" : "Disabled"}
        </span>
      </div>
    </article>
  );
}

function DeleteConfirmDialog({
  item,
  onConfirm,
  onCancel,
  busy,
}: {
  item: Mapping;
  onConfirm: () => void;
  onCancel: () => void;
  busy: boolean;
}) {
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="delete-title"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: 420 }}
      >
        <div className="flex items-center justify-between">
          <h2 id="delete-title" className="flex items-center gap-2">
            <Trash2 size={18} className="text-destructive" />
            Delete gesture
          </h2>
          <Button variant="ghost" size="icon" aria-label="Cancel" onClick={onCancel}><X /></Button>
        </div>
        <p className="page-subtitle mt-3">
          Delete <strong>{item.name}</strong> ({item.id})?
        </p>
        <div className="notice mt-3">
          This will permanently delete the gesture mapping
          {item.samples > 0 ? ` and all ${item.samples} training samples` : ""}.
          The model will be invalidated and must be retrained.
          This cannot be undone.
        </div>
        <div className="flex gap-3 mt-6">
          <Button variant="outline" className="flex-1" onClick={onCancel} disabled={busy}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            className="flex-1"
            onClick={onConfirm}
            disabled={busy}
          >
            <Trash2 size={14} />
            {busy ? "Deleting…" : "Delete gesture"}
          </Button>
        </div>
      </section>
    </div>
  );
}

function DeleteSamplesConfirmDialog({
  item,
  onConfirm,
  onCancel,
  busy,
}: {
  item: Mapping;
  onConfirm: () => void;
  onCancel: () => void;
  busy: boolean;
}) {
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="delete-samples-title"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: 420 }}
      >
        <div className="flex items-center justify-between">
          <h2 id="delete-samples-title" className="flex items-center gap-2">
            <Trash2 size={18} className="text-destructive" />
            Clear training data
          </h2>
          <Button variant="ghost" size="icon" aria-label="Cancel" onClick={onCancel}><X /></Button>
        </div>
        <p className="page-subtitle mt-3">
          Clear all training samples for <strong>{item.name}</strong>?
        </p>
        <div className="notice mt-3">
          This will delete all {item.samples} recorded samples for this gesture.
          The gesture mapping itself will be kept. The model will be invalidated
          and must be retrained. This cannot be undone.
        </div>
        <div className="flex gap-3 mt-6">
          <Button variant="outline" className="flex-1" onClick={onCancel} disabled={busy}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            className="flex-1"
            onClick={onConfirm}
            disabled={busy}
          >
            <Trash2 size={14} />
            {busy ? "Clearing…" : "Clear samples"}
          </Button>
        </div>
      </section>
    </div>
  );
}

function MappingDialog({
  mapping,
  close,
}: {
  mapping: Mapping | null;
  close: () => void;
}) {
  const { mappings, saveMapping, connected, busy, error } = useGestures();
  const [form, setForm] = useState<Mapping>(
    mapping ?? {
      id: `G${String((mappings.length > 0 ? Math.max(...mappings.map((m) => Number(m.id.slice(1)) || 0)) : 0) + 1).padStart(2, "0")}`,
      name: "",
      symbol: "🖐️",
      type: "launch",
      app: "Chrome",
      target: "",
      action: "",
      enabled: true,
      samples: 0,
    },
  );
  const [localError, setLocalError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (mappings.some((m) => m.id !== form.id && m.name.toLowerCase() === form.name.trim().toLowerCase())) {
      setLocalError("Choose a unique gesture name.");
      return;
    }
    if (form.type === "action" && !form.action) {
      setLocalError("Choose a cursor/keyboard action.");
      return;
    }
    if (await saveMapping({ ...form, name: form.name.trim() })) close();
  }

  return (
    <div className="modal-overlay" onClick={close}>
      <section className="modal" role="dialog" aria-modal="true" aria-labelledby="mapping-title" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <h2 id="mapping-title">{mapping ? "Edit gesture" : "New gesture"}</h2>
          <Button variant="ghost" size="icon" aria-label="Close gesture editor" onClick={close}><X /></Button>
        </div>
        <form onSubmit={submit}>
          {/* Name */}
          <label className="field">
            <span>Gesture name</span>
            <input autoFocus required maxLength={40} placeholder="e.g. Open palm" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </label>

          {/* Symbol */}
          {/* Symbol — only for app launch mappings, not cursor actions */}
          {form.type === "launch" && (
          <label className="field">
            <span>Gesture symbol</span>
            <select value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value })}>
              {["🖐️", "✌️", "✊", "👍", "🤟", "👌", "👆", "🤙", "🤘", "🤞"].map((s) => <option key={s}>{s}</option>)}
            </select>
          </label>
          )}

          {/* Type toggle */}
          <div className="field">
            <span className="text-xs text-muted-foreground mb-2 block">What should this gesture do?</span>
            <div className="flex gap-2">
              <button
                type="button"
                className={`flex-1 py-2 px-3 rounded-md text-xs font-medium border transition-colors ${form.type === "launch" ? "bg-primary text-primary-foreground border-primary" : "border-border text-muted-foreground hover:border-foreground"}`}
                onClick={() => setForm({ ...form, type: "launch", app: form.app || "Chrome", action: "" })}
              >
                Launch app
              </button>
              <button
                type="button"
                className={`flex-1 py-2 px-3 rounded-md text-xs font-medium border transition-colors ${form.type === "action" ? "bg-primary text-primary-foreground border-primary" : "border-border text-muted-foreground hover:border-foreground"}`}
                onClick={() => setForm({ ...form, type: "action", app: "", action: form.action || "cursor_move" })}
              >
                Cursor / keys
              </button>
            </div>
          </div>

          {/* Launch: app selector */}
          {form.type === "launch" && <>
            <label className="field">
              <span>Application</span>
              <select value={form.app} onChange={(e) => setForm({ ...form, app: e.target.value, target: e.target.value === "YouTube" ? "https://www.youtube.com" : "" })}>
                <optgroup label="Browsers">{["Chrome", "Edge", "Firefox", "Brave"].map(s => <option key={s}>{s}</option>)}</optgroup>
                <optgroup label="Web">{["YouTube", "Website"].map(s => <option key={s}>{s}</option>)}</optgroup>
                <optgroup label="Development">{["VS Code", "Kiro", "Cursor", "Windsurf", "Android Studio", "PyCharm", "IntelliJ", "Eclipse"].map(s => <option key={s}>{s}</option>)}</optgroup>
                <optgroup label="Database & API">{["MongoDB Compass", "DBeaver", "Postman"].map(s => <option key={s}>{s}</option>)}</optgroup>
                <optgroup label="Office">{["Word", "Excel", "PowerPoint", "Outlook"].map(s => <option key={s}>{s}</option>)}</optgroup>
                <optgroup label="Communication">{["Teams", "Zoom", "Discord", "Slack", "WhatsApp", "Telegram"].map(s => <option key={s}>{s}</option>)}</optgroup>
                <optgroup label="Media & Creative">{["Spotify", "VLC", "OBS", "Blender", "GIMP", "Figma"].map(s => <option key={s}>{s}</option>)}</optgroup>
                <optgroup label="Gaming">{["Steam", "Epic Games"].map(s => <option key={s}>{s}</option>)}</optgroup>
                <optgroup label="System">{["Notepad", "Notepad++", "Calculator", "Paint", "File Explorer", "Task Manager", "Tableau"].map(s => <option key={s}>{s}</option>)}</optgroup>
              </select>
            </label>
            {(form.app === "Website" || form.app === "YouTube") && (
              <label className="field">
                <span>Website address</span>
                <input type="url" required pattern="https://.*" placeholder="https://example.com" value={form.target} onChange={(e) => setForm({ ...form, target: e.target.value })} />
                <small>HTTPS addresses only.</small>
              </label>
            )}
          </>}

          {/* Action: control selector */}
          {form.type === "action" && <>
            <label className="field">
              <span>Action</span>
              <select value={form.action} onChange={(e) => setForm({ ...form, action: e.target.value })}>
                <optgroup label="Mouse">
                  {CONTROL_ACTIONS.filter(a => ["cursor_move","left_click","right_click","double_click","drag"].includes(a.id)).map(a => <option key={a.id} value={a.id}>{a.label}</option>)}
                </optgroup>
                <optgroup label="Scroll & Zoom">
                  {CONTROL_ACTIONS.filter(a => ["scroll_up","scroll_down","zoom_in","zoom_out"].includes(a.id)).map(a => <option key={a.id} value={a.id}>{a.label}</option>)}
                </optgroup>
                <optgroup label="Volume">
                  {CONTROL_ACTIONS.filter(a => ["volume_up","volume_down","mute"].includes(a.id)).map(a => <option key={a.id} value={a.id}>{a.label}</option>)}
                </optgroup>
                <optgroup label="Media">
                  {CONTROL_ACTIONS.filter(a => ["media_play_pause","media_next","media_prev"].includes(a.id)).map(a => <option key={a.id} value={a.id}>{a.label}</option>)}
                </optgroup>
                <optgroup label="System">
                  {CONTROL_ACTIONS.filter(a => ["screenshot"].includes(a.id)).map(a => <option key={a.id} value={a.id}>{a.label}</option>)}
                </optgroup>
              </select>
            </label>
            <div className="notice text-xs">
              Action gestures fire continuously while your hand is detected. Use a high confidence threshold to avoid false triggers.
            </div>
          </>}

          {/* Enable toggle */}
          <label className="flex items-center gap-2 text-xs mt-2">
            <input type="checkbox" checked={form.enabled} onChange={(e) => setForm({ ...form, enabled: e.target.checked })} />
            Enable this mapping
          </label>

          {!connected && <div className="notice mt-3">Connect your companion first. All gestures are stored in MongoDB via the companion.</div>}
          {(localError || error) && <p role="alert" className="error-message">{localError || error}</p>}

          <Button type="submit" className="w-full mt-6" disabled={busy}>
            <Check />{mapping ? "Save changes" : "Create gesture"}
          </Button>
        </form>
      </section>
    </div>
  );
}

// ── Cursor gesture reference card ────────────────────────────────────────────
const GESTURE_GUIDE = [
  { icon: "☝",  action: "Move cursor",  gesture: "Point with index finger",      tip: "Only index finger up — others folded down" },
  { icon: "⌖",  action: "Left click",   gesture: "Pinch index + thumb",           tip: "Tap together then release. Double-tap fast for double-click" },
  { icon: "⌗",  action: "Right click",  gesture: "Pinch middle + thumb",          tip: "Bring middle fingertip to thumb tip" },
  { icon: "⇅",  action: "Scroll",       gesture: "Index + middle up, move wrist", tip: "Move hand up = scroll up, move hand down = scroll down" },
  { icon: "⊠",  action: "Drag",         gesture: "Close fist",                    tip: "Fist = mouse button held. Open hand = release" },
  { icon: "◈",  action: "Volume",       gesture: "Thumb + index up, move hand",   tip: "Move hand up = louder, move hand down = quieter" },
  { icon: "▶",  action: "Play / Pause", gesture: "Shaka — thumb + pinky spread",  tip: "Hold the shaka pose for 1 second" },
  { icon: "⊞",  action: "Screenshot",  gesture: "Peace sign held",               tip: "Index + middle up, others folded — hold 2 seconds" },
];

function GestureReferenceCard() {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-6 rounded-lg border border-border overflow-hidden">
      <button
        type="button"
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-accent/30 transition-colors"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        <span className="flex items-center gap-2 text-sm font-medium">
          <Hand size={14} className="text-primary" />
          Cursor control — gesture guide
          <span className="tag ml-1 text-[9px]">NO TRAINING NEEDED</span>
        </span>
        <span className={`text-muted-foreground text-xs transition-transform duration-200 inline-block ${open ? "-rotate-180" : ""}`}>▾</span>
      </button>
      {open && (
        <div className="border-t border-border">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-0">
            {GESTURE_GUIDE.map((g, i) => (
              <div key={i} className="flex items-start gap-3 px-4 py-3 border-b border-border/40 last:border-0 hover:bg-accent/10 transition-colors">
                <span className="text-lg font-mono font-bold text-primary w-9 text-center flex-shrink-0 leading-none mt-0.5 bg-primary/10 rounded px-1 py-0.5">{g.icon}</span>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-sm font-semibold text-foreground">{g.action}</span>
                    <span className="text-[10px] text-muted-foreground font-mono bg-muted px-1.5 py-0.5 rounded">{g.gesture}</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground mt-0.5 leading-relaxed">{g.tip}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="px-4 py-3 bg-muted/30 text-[10px] text-muted-foreground flex items-center gap-2 border-t border-border/40">
            <ShieldCheck size={11} className="text-primary flex-shrink-0" />
            Cursor actions run directly on hand geometry every frame — no ML training required. Add them via My gestures → New gesture → Cursor / keys.
          </div>
        </div>
      )}
    </div>
  );
}

export function GestureWorkspace({ view }: { view: View }) {
  const state = useGestures();
  const {
    mappings,
    status,
    connected,
    settings,
    setSettings,
    busy,
    error,
    setError,
    action,
    deleteMapping,
    deleteSamples,
  } = state;
  const [editor, setEditor] = useState<Mapping | null | undefined>(undefined);
  const [deleteTarget, setDeleteTarget] = useState<Mapping | null>(null);
  const [deleteSamplesTarget, setDeleteSamplesTarget] = useState<Mapping | null>(null);
  const [filter, setFilter] = useState("All launches");
  const [saved, setSaved] = useState(false);
  const [frame, setFrame] = useState<string | null>(null);
  const frameRef = useRef<string | null>(null);
  const frameInterval = useRef<ReturnType<typeof setInterval> | null>(null);

  // Auto-refresh camera frame whenever the companion is actively listening or recording
  useEffect(() => {
    const active =
      connected &&
      (status?.listening || Boolean(status?.recording) || Boolean(status?.previewing));

    async function fetchFrame() {
      if (!active) return;
      try {
        const res = await fetch("http://127.0.0.1:8765/frame", {
          headers: { Authorization: `Bearer ${state.token}` },
          signal: AbortSignal.timeout(4000),
        });
        if (!res.ok) return;
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        // Revoke PREVIOUS url only after the new one is ready
        setFrame((prev) => {
          if (prev && prev !== url && frameRef.current === prev) {
            // Schedule revoke after browser has rendered the new frame
            setTimeout(() => URL.revokeObjectURL(prev), 2000);
          }
          frameRef.current = url;
          return url;
        });
      } catch {
        /* polling in gesture-provider handles disconnects */
      }
    }

    if (active) {
      void fetchFrame();
      frameInterval.current = setInterval(() => {
        void fetchFrame();
      }, 1000);
    } else {
      if (frameInterval.current) clearInterval(frameInterval.current);
      frameInterval.current = null;
      // Keep last frame visible — don't revoke immediately on stop
      // It will be cleaned up on next active cycle or unmount
    }
    return () => {
      if (frameInterval.current) clearInterval(frameInterval.current);
    };
  }, [connected, status?.listening, status?.recording, state.token]);

  // Release object URL on unmount
  useEffect(() => {
    return () => {
      if (frameRef.current) URL.revokeObjectURL(frameRef.current);
    };
  }, []);

  async function refreshFrame() {
    try {
      const res = await fetch("http://127.0.0.1:8765/frame", {
        headers: { Authorization: `Bearer ${state.token}` },
        signal: AbortSignal.timeout(4000),
      });
      if (!res.ok) return;
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setFrame((prev) => {
        if (prev) setTimeout(() => URL.revokeObjectURL(prev), 2000);
        frameRef.current = url;
        return url;
      });
    } catch {
      /* status polling handles disconnects */
    }
  }

  const history = status?.history ?? [];
  const title =
    view === "overview"
      ? "Your workflow, at your fingertips."
      : view === "gestures"
        ? "My gestures"
        : view === "training"
          ? "Make it your own."
          : view === "history"
            ? "Launch history"
            : "Fine-tune your flow.";
  const subtitle =
    view === "overview"
      ? "A little movement. A whole new way to launch."
      : view === "gestures"
        ? "Your hand signs. Your favorite apps. Your rules."
        : view === "training"
          ? "Teach your model the gestures that come naturally to you."
          : view === "history"
            ? "Every gesture. Every launch. All in one place."
            : "The right balance between responsiveness and peace of mind.";

  return (
    <GestureShell view={view}>
      <div className="page-intro flex items-center justify-between gap-4">
        <div>
          <div className="section-eyebrow mb-3">
            {view === "overview"
              ? "YOUR PERSONAL LAUNCH SPACE"
              : "GUSTEE WORKSPACE"}
          </div>
          <h1 className="page-title">{title}</h1>
          <p className="page-subtitle">{subtitle}</p>
        </div>
        {view === "overview" ? (
          <Button
            onClick={() => {
              if (!connected) {
                setError("Connect your companion using Connect device in the sidebar.");
                return;
              }
              if (status?.listening) {
                void action("/stop");
              } else if (status?.model) {
                void action("/start");
              } else {
                // No model yet — toggle camera preview
                void action(status?.previewing ? "/stop" : "/preview");
              }
            }}
            disabled={busy}
            variant={!status?.model && !status?.listening ? "outline" : "default"}
          >
            <span>
              {status?.listening ? <Pause /> : <Play fill="currentColor" />}
            </span>
            <span className="desktop-label">
              {status?.listening
                ? "Pause session"
                : status?.model
                  ? "Start session"
                  : status?.previewing
                    ? "Stop preview"
                    : "Preview camera"}
            </span>
            <span className="sm:hidden">
              {status?.listening ? "Pause" : status?.previewing ? "Stop" : "Preview"}
            </span>
          </Button>
        ) : view === "gestures" ? (
          <Button
            onClick={() => {
              setError("");
              setEditor(null);
            }}
          >
            <Plus />
            New gesture
          </Button>
        ) : null}
      </div>

      {error && (
        <div
          className="notice flex items-start justify-between gap-3"
          role="alert"
        >
          <span>{error}</span>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 shrink-0"
            aria-label="Dismiss notice"
            onClick={() => setError("")}
          >
            <X />
          </Button>
        </div>
      )}

      {view === "overview" && (
        <>
          <div className="stats-grid">
            <article className="stat">
              <div className="stat-title">
                Active gestures
                <Hand size={15} />
              </div>
              <div className="stat-number">
                {String(mappings.filter((m) => m.enabled).length).padStart(
                  2,
                  "0",
                )}
                <span className="text-sm text-muted-foreground ml-2">
                  / {String(mappings.length).padStart(2, "0")}
                </span>
              </div>
              <div className="stat-note">
                <span className="text-primary">↗</span>{" "}
                {mappings.filter((m) => m.samples >= 30).length} ready for
                recognition
              </div>
            </article>
            <article className="stat">
              <div className="stat-title">
                Apps launched
                <Activity size={15} />
              </div>
              <div className="stat-number">
                {history.filter((h) => h.success).length}
                <span className="text-xs text-muted-foreground ml-2">
                  launches
                </span>
              </div>
              <div className="stat-note">All-time on this device</div>
            </article>
            <article className="stat">
              <div className="stat-title">
                Model accuracy
                <Fingerprint size={15} />
              </div>
              <div className="stat-number">
                {status?.accuracy ? `${status.accuracy.toFixed(1)}` : "—"}
                <span className="text-sm text-muted-foreground ml-1">
                  {status?.accuracy ? "%" : ""}
                </span>
              </div>
              <div className="stat-note flex items-center gap-1.5">
                <span className={`dot ${status?.model ? "connected" : ""}`} />
                {status?.model
                  ? "Custom model · PyTorch"
                  : "Your model is not trained yet"}
              </div>
            </article>
          </div>
          <div className="session-grid">
            <section>
              <div className="section-heading">
                <h2>
                  <Video size={16} className="text-muted-foreground" />
                  Live session
                </h2>
                <span className="tag">
                  <span
                    className={`dot ${status?.listening ? "connected" : ""}`}
                  />
                  {status?.listening ? "LISTENING" : "STANDBY"}
                </span>
              </div>
              <div className="camera-frame">
                <img
                  src={frame ?? previewImage}
                  width={1280}
                  height={768}
                  alt={
                    frame
                      ? "Your webcam frame"
                      : "Example peace-sign gesture, not a live camera feed"
                  }
                />
                <div className="camera-top">
                  <span className="camera-badge">
                    <Camera size={11} />
                    {frame ? "CAMERA 01" : "PREVIEW · NOT LIVE"}
                  </span>
                  <span className="camera-badge">
                    <ShieldCheck size={11} />
                    ON-DEVICE
                  </span>
                </div>
                <div className="camera-bottom">
                  <div>
                    <div className="section-eyebrow text-primary">
                      {status?.listening
                        ? "RECOGNITION ACTIVE"
                        : "READY WHEN YOU ARE"}
                    </div>
                    <h3>{status?.gesture ?? "A new way to connect."}</h3>
                  </div>
                  <span className="camera-badge">
                    {status?.listening ? "LIVE" : "SESSION PAUSED"}
                  </span>
                </div>
              </div>
              <div className="camera-controls">
                <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                  <Monitor size={13} />
                  {connected ? "Local camera" : "No camera connected"}
                  <ChevronRight size={12} />
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={!status?.camera}
                    onClick={refreshFrame}
                  >
                    <Camera />
                    Refresh frame
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    aria-label="Camera settings"
                    asChild
                  >
                    <Link to="/settings">
                      <Settings2 />
                    </Link>
                  </Button>
                </div>
              </div>
              <div className="recognition">
                <div className="recognition-icon">
                  <Hand size={22} />
                </div>
                <div className="recognition-info">
                  <span className="section-eyebrow">DETECTED GESTURE</span>
                  <strong>
                    {status?.gesture ?? "Waiting for your gesture"}
                  </strong>
                </div>
                <div className="text-right">
                  <div className="confidence">
                    {status?.gesture
                      ? `${(status.confidence * 100).toFixed(0)}%`
                      : "—"}
                  </div>
                  <div className="text-[9px] text-muted-foreground mt-1">
                    CONFIDENCE
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                <ShieldCheck size={12} className="text-primary" />
                {settings.hold}s hold to launch<span className="mx-2">·</span>
                {settings.cooldown}s cooldown<span className="mx-2">·</span>
                {settings.confidence}% threshold
              </div>
            </section>
            <section>
              <div className="section-heading">
                <h2>
                  Gesture mappings
                  <span className="tag">
                    {String(mappings.length).padStart(2, "0")}
                  </span>
                </h2>
                <Button variant="link" size="sm" asChild>
                  <Link to="/gestures">
                    View all
                    <ArrowUpRight size={12} />
                  </Link>
                </Button>
              </div>
              <div className="mapping-list">
                {mappings.slice(0, 4).map((item) => (
                  <MappingCard key={item.id} item={item} edit={setEditor} onDelete={setDeleteTarget} />
                ))}
                <Button
                  variant="outline"
                  className="add-mapping text-muted-foreground"
                  onClick={() => {
                    setError("");
                    setEditor(null);
                  }}
                >
                  <Plus />
                  Add new gesture
                </Button>
              </div>
            </section>
          </div>
          <section className="activity-section">
            <div className="section-heading">
              <h2>
                <History size={15} className="text-muted-foreground" />
                Recent activity
              </h2>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/history">
                  View history
                  <ArrowUpRight size={12} />
                </Link>
              </Button>
            </div>
            <HistoryTable history={history.slice(0, 4)} />
          </section>
        </>
      )}

      {view === "gestures" && (
        <>
          <div className="flex items-center gap-3 mt-7 text-xs text-muted-foreground">
            <span className="tag">{mappings.length} GESTURES</span>
            <span>
              {connected ? "Synced with MongoDB via companion" : "Connect your companion to load gestures"}
            </span>
          </div>
          {!connected && mappings.length === 0 ? (
            <div className="empty-activity mt-8">
              <Hand size={22} />
              <span>No gestures yet. Connect your companion to load or create gestures stored in MongoDB.</span>
            </div>
          ) : (
            <div className="library-grid">
              {mappings.map((item) => (
                <MappingCard key={item.id} item={item} edit={setEditor} onDelete={setDeleteTarget} />
              ))}
            </div>
          )}
        </>
      )}

      {view === "training" && (
        <>
          <div className="notice">
            <span className="text-foreground font-medium">
              Custom gestures. A model that learns you.
            </span>
            <br />
            {connected
              ? "Record at least 30 samples for every gesture. Vary your hand position and angle. Add a neutral pose mapped as disabled to reduce false launches."
              : "Connect your Gustee companion to capture samples and train your custom PyTorch model."}
          </div>

          {/* ── Cursor gesture reference card ─────────────────────────────── */}
          <GestureReferenceCard />
          <section className="mt-8">
            <div className="section-heading">
              <h2>Training dataset</h2>
              <span className="tag">
                <ShieldCheck size={11} />
                LOCAL ONLY
              </span>
            </div>
            {mappings.map((item) => (
              <div className="training-row" key={item.id}>
                <div className="flex items-center gap-4">
                  <span className="gesture-symbol">{item.symbol}</span>
                  <div>
                    <strong className="text-sm font-medium">{item.name}</strong>
                    <div className="text-muted-foreground text-xs mt-1">
                      {item.samples} samples <span className="mx-1">/</span> 30
                      minimum
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="tag">
                    {item.samples >= 30 ? "READY" : "NEEDS SAMPLES"}
                  </span>
                  <Button
                    variant={
                      status?.recording === item.id ? "default" : "outline"
                    }
                    disabled={
                      !connected ||
                      busy ||
                      Boolean(status?.training) ||
                      Boolean(status?.recording && status.recording !== item.id)
                    }
                    onClick={() =>
                      void action(
                        status?.recording === item.id
                          ? "/record/stop"
                          : "/record",
                        { id: item.id },
                      )
                    }
                  >
                    {status?.recording === item.id ? <Pause /> : <Camera />}
                    {status?.recording === item.id
                      ? "Stop recording"
                      : "Record samples"}
                  </Button>
                  {item.samples > 0 && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive hover:text-destructive"
                      aria-label={`Clear training samples for ${item.name}`}
                      disabled={!connected || busy || Boolean(status?.recording) || Boolean(status?.training)}
                      onClick={() => setDeleteSamplesTarget(item)}
                    >
                      <Trash2 size={14} />
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </section>
          <div className="flex justify-between items-center gap-5 flex-wrap mt-7">
            <div className="text-xs text-muted-foreground">
              <Sparkles size={14} className="inline mr-2 text-primary" />
              {status?.training
                ? "Training your model…"
                : status?.model
                  ? `Model ready · ${status.accuracy?.toFixed(1) ?? "—"}% validation accuracy`
                  : "A fresh model, trained entirely on your gestures."}
            </div>
            {(() => {
              const readyCount = mappings.filter(m => m.samples >= 30).length;
              const notReady = mappings.filter(m => m.samples > 0 && m.samples < 30);
              const reason = !connected
                ? "Connect companion first"
                : readyCount === 0
                  ? "Record 30+ samples for at least one gesture"
                  : notReady.length > 0
                    ? `${notReady.map(m => m.name).join(", ")} need ${30} samples`
                    : "";
              return (
                <div className="flex flex-col items-end gap-1">
                  {reason && !status?.training && (
                    <span className="text-[10px] text-muted-foreground">{reason}</span>
                  )}
                  <Button
                    disabled={!connected || busy || !!status?.training || readyCount === 0}
                    onClick={() => void action("/train")}
                  >
                    <Sparkles />
                    {status?.training ? "Training…" : `Train model${readyCount > 0 ? ` (${readyCount} gesture${readyCount > 1 ? "s" : ""})` : ""}`}
                  </Button>
                </div>
              );
            })()}
          </div>
        </>
      )}

      {view === "history" && (
        <>
          <div className="flex items-center justify-between gap-4 mt-8 mb-5">
            <select
              aria-label="Filter launch history"
              className="max-w-44"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            >
              {["All launches", "Successful", "Failed"].map((f) => (
                <option key={f}>{f}</option>
              ))}
            </select>
            <Button
              variant="outline"
              disabled={!history.length}
              onClick={() => {
                const blob = new Blob(
                  [
                    "Time,Gesture,Application,Confidence,Success\n" +
                      history
                        .map((h) =>
                          [h.time, h.gesture, h.app, h.confidence, h.success]
                            .map((v) => `"${String(v).replaceAll('"', '""')}"`)
                            .join(","),
                        )
                        .join("\n"),
                  ],
                  { type: "text/csv" },
                );
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "gustee-launches.csv";
                a.click();
                URL.revokeObjectURL(url);
              }}
            >
              <ArrowDownToLine />
              Export
            </Button>
          </div>
          <HistoryTable
            history={history.filter(
              (h) =>
                filter === "All launches" ||
                (filter === "Successful" ? h.success : !h.success),
            )}
          />
        </>
      )}

      {view === "settings" && (
        <section className="settings-grid">
          <div className="section-heading">
            <h2>
              <ShieldCheck size={17} className="text-primary" />
              Launch protection
            </h2>
            <span className="tag">
              {connected ? "DEVICE SETTINGS" : "WORKSPACE DRAFT"}
            </span>
          </div>
          {[
            {
              key: "confidence" as const,
              title: "Confidence threshold",
              detail: "Only launch when the model is confident.",
              min: 60,
              max: 99,
              step: 1,
              unit: "%",
            },
            {
              key: "hold" as const,
              title: "Gesture hold time",
              detail: "How long a gesture must remain stable.",
              min: 0.5,
              max: 4,
              step: 0.1,
              unit: "s",
            },
            {
              key: "cooldown" as const,
              title: "Launch cooldown",
              detail: "A short pause between application launches.",
              min: 2,
              max: 15,
              step: 1,
              unit: "s",
            },
          ].map((item) => (
            <div className="setting-row" key={item.key}>
              <div>
                <h3>{item.title}</h3>
                <p>{item.detail}</p>
              </div>
              <div className="setting-control">
                <div className="setting-value">
                  {settings[item.key]}
                  {item.unit}
                </div>
                <input
                  type="range"
                  aria-label={item.title}
                  min={item.min}
                  max={item.max}
                  step={item.step}
                  value={settings[item.key]}
                  onChange={(e) => {
                    setSaved(false);
                    setSettings({
                      ...settings,
                      [item.key]: Number(e.target.value),
                    });
                  }}
                />
              </div>
            </div>
          ))}
          <div className="setting-row">
            <div>
              <h3>Camera</h3>
              <p>Your camera device index.</p>
            </div>
            <select
              className="setting-control"
              aria-label="Camera device"
              value={settings.camera}
              onChange={(e) => {
                setSaved(false);
                setSettings({ ...settings, camera: Number(e.target.value) });
              }}
            >
              {[0, 1, 2, 3].map((i) => (
                <option value={i} key={i}>
                  Camera {i + 1}
                  {i === 0 ? " (default)" : ""}
                </option>
              ))}
            </select>
          </div>
          <div className="flex justify-end mt-6">
            <Button
              disabled={!connected || busy}
              onClick={async () =>
                setSaved(await action("/settings", settings))
              }
            >
              {saved ? <CheckCircle2 /> : <Check />}
              {saved ? "Settings saved" : "Save settings"}
            </Button>
          </div>
          <div className="notice">
            Camera frames and training samples never leave your device. Only
            approved applications can be launched.
          </div>
          <Button asChild variant="link" className="mt-3">
            <a href="https://github.com/hari9am/guestee/releases/latest/download/Gustee-Setup.exe" target="_blank" rel="noreferrer">
              <ArrowDownToLine />
              Download Windows setup
            </a>
          </Button>
        </section>
      )}

      {editor !== undefined && (
        <MappingDialog mapping={editor} close={() => setEditor(undefined)} />
      )}

      {deleteTarget !== null && (
        <DeleteConfirmDialog
          item={deleteTarget}
          busy={busy}
          onConfirm={async () => {
            const ok = await deleteMapping(deleteTarget.id);
            if (ok) setDeleteTarget(null);
          }}
          onCancel={() => setDeleteTarget(null)}
        />
      )}

      {deleteSamplesTarget !== null && (
        <DeleteSamplesConfirmDialog
          item={deleteSamplesTarget}
          busy={busy}
          onConfirm={async () => {
            const ok = await deleteSamples(deleteSamplesTarget.id);
            if (ok) setDeleteSamplesTarget(null);
          }}
          onCancel={() => setDeleteSamplesTarget(null)}
        />
      )}
    </GestureShell>
  );
}

function HistoryTable({
  history,
}: {
  history: NonNullable<ReturnType<typeof useGestures>["status"]>["history"];
}) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Application</th>
            <th>Gesture</th>
            <th>Action</th>
            <th>Confidence</th>
            <th>Time</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {history.map((h) => (
            <tr key={h.id}>
              <td>
                <span className="flex items-center gap-2">
                  <AppIcon app={h.app} />
                  {h.app}
                </span>
              </td>
              <td>{h.gesture}</td>
              <td>
                <span className={h.action === "close" ? "text-muted-foreground" : "text-primary"}>
                  {h.action === "close" ? "↓ Close" : "↑ Open"}
                </span>
              </td>
              <td className="font-mono">{(h.confidence * 100).toFixed(0)}%</td>
              <td className="text-muted-foreground">
                {new Date(h.time).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </td>
              <td>
                <span className={h.success ? "text-success" : "text-destructive"}>
                  {h.success ? (h.action === "close" ? "Closed" : "Launched") : "Failed"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!history.length && (
        <div className="empty-activity">
          <History size={17} />
          <span>No launches yet. Your next gesture starts the story.</span>
        </div>
      )}
    </div>
  );
}
