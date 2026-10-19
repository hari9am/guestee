import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  initialSettings,
  type Mapping,
  type Settings,
  type Status,
} from "@/lib/gesture-types";

// ── Token persistence (sessionStorage survives refresh, clears on tab close) ──
const TOKEN_KEY = "gustee_token";

function loadStoredToken(): string {
  try { return sessionStorage.getItem(TOKEN_KEY) ?? ""; } catch { return ""; }
}
function storeToken(t: string) {
  try { if (t) sessionStorage.setItem(TOKEN_KEY, t); else sessionStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ }
}

// ── Core state hook ───────────────────────────────────────────────────────────
function useGestureState() {
  const [mappings, setMappings] = useState<Mapping[]>([]);
  const [settings, setSettings] = useState<Settings>(initialSettings);
  const [status, setStatus]     = useState<Status | null>(null);
  const [connected, setConnected] = useState(false);
  const [token, setToken]       = useState(loadStoredToken);
  const [error, setError]       = useState("");
  const [busy, setBusy]         = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  const polling  = useRef(false);
  const didAutoConnect = useRef(false);

  // ── Request helper ──────────────────────────────────────────────────────────
  const request = useCallback(
    async (path: string, body?: unknown, auth = token) => {
      const response = await fetch(`http://127.0.0.1:8765${path}`, {
        method: body === undefined ? "GET" : "POST",
        headers: {
          Authorization: `Bearer ${auth}`,
          ...(body === undefined ? {} : { "Content-Type": "application/json" }),
        },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
        signal: AbortSignal.timeout(12000),
      });
      const data = await response.json();
      if (!response.ok)
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "The companion could not complete this action.",
        );
      return data;
    },
    [token],
  );

  // ── Sync status from companion ──────────────────────────────────────────────
  function sync(data: Status, updateSettings = true) {
    setStatus(data);
    setMappings(data.mappings);
    if (updateSettings) setSettings(data.settings);
    if (data.error) setError(data.error);
  }

  // ── Manual connect (from pairing modal) ────────────────────────────────────
  async function connect(value: string) {
    setBusy(true);
    setError("");
    try {
      const data = await request("/status", undefined, value);
      setToken(value);
      storeToken(value);        // persist so next refresh auto-connects
      sync(data);
      setConnected(true);
    } catch (e) {
      setError(
        e instanceof TypeError
          ? "Companion not reachable. Make sure it is running and allow local network access."
          : e instanceof Error ? e.message : "Connection failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  // ── Auto-connect on page load if token is stored ────────────────────────────
  useEffect(() => {
    if (didAutoConnect.current) return;
    didAutoConnect.current = true;
    const stored = loadStoredToken();
    if (!stored) return;

    setReconnecting(true);
    request("/status", undefined, stored)
      .then((data) => {
        setToken(stored);
        sync(data);
        setConnected(true);
      })
      .catch(() => {
        // Companion not running yet — clear token so user sees the connect button
        // (they'll need to re-pair after restarting the companion)
        storeToken(stored);   // keep token — companion may start later
      })
      .finally(() => setReconnecting(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Action helper ───────────────────────────────────────────────────────────
  async function action(path: string, body: unknown = {}) {
    if (!connected) {
      setError("Connect your companion first.");
      return false;
    }
    setBusy(true);
    setError("");
    try {
      await request(path, body);
      sync(await request("/status"));
      return true;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed.");
      return false;
    } finally {
      setBusy(false);
    }
  }

  // ── CRUD helpers ────────────────────────────────────────────────────────────
  async function saveMapping(mapping: Mapping) {
    if (!connected) { setError("Connect your companion first to save gestures."); return false; }
    return action("/mapping", mapping);
  }
  async function deleteMapping(id: string) {
    if (!connected) { setError("Connect your companion first to delete gestures."); return false; }
    return action("/mapping/delete", { id });
  }
  async function deleteSamples(id: string) {
    if (!connected) { setError("Connect your companion first to clear training samples."); return false; }
    return action("/samples/delete", { id });
  }

  // ── Polling loop ────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!connected) return;
    const interval = setInterval(async () => {
      if (polling.current) return;
      polling.current = true;
      try {
        sync(await request("/status"), false);
      } catch {
        setConnected(false);
        setStatus(null);
        setMappings([]);
        setError("Connection lost. Reconnecting…");
        // Auto-retry every 3 seconds using stored token
        const retry = setInterval(async () => {
          const stored = loadStoredToken();
          if (!stored) { clearInterval(retry); return; }
          try {
            const data = await request("/status", undefined, stored);
            sync(data);
            setConnected(true);
            setError("");
            clearInterval(retry);
          } catch { /* still not reachable */ }
        }, 3000);
      } finally {
        polling.current = false;
      }
    }, 1500);
    return () => clearInterval(interval);
  }, [connected, token, request]);

  return {
    mappings,
    settings,
    setSettings,
    status,
    connected,
    reconnecting,
    error,
    setError,
    busy,
    connect,
    action,
    saveMapping,
    deleteMapping,
    deleteSamples,
    token,
  };
}

const GestureContext = createContext<ReturnType<typeof useGestureState> | null>(null);

export function GestureProvider({ children }: { children: ReactNode }) {
  const state = useGestureState();
  return (
    <GestureContext.Provider value={state}>{children}</GestureContext.Provider>
  );
}

export function useGestures() {
  const context = useContext(GestureContext);
  if (!context) throw new Error("GestureProvider is required");
  return context;
}
