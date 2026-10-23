import { useState } from "react";
import { Link } from "@tanstack/react-router";
import {
  ArrowDownToLine,
  ArrowUpRight,
  ChevronRight,
  Fingerprint,
  Hand,
  History,
  LayoutGrid,
  Loader2,
  Menu,
  Monitor,
  Settings2,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useGestures } from "./gesture-provider";
import type { View } from "@/lib/gesture-types";

const navigation = [
  { view: "overview",  label: "Overview",       path: "/",         icon: LayoutGrid },
  { view: "gestures",  label: "My gestures",     path: "/gestures", icon: Hand },
  { view: "training",  label: "Train model",     path: "/training", icon: Sparkles },
  { view: "history",   label: "Launch history",  path: "/history",  icon: History },
  { view: "settings",  label: "Settings",        path: "/settings", icon: Settings2 },
] as const;

export function GestureShell({ view, children }: { view: View; children: React.ReactNode }) {
  const [menu, setMenu] = useState(false);
  const [pairing, setPairing] = useState(false);
  const [tokenInput, setTokenInput] = useState("");
  const { connected, reconnecting, error, setError, connect, busy } = useGestures();

  const statusLabel = reconnecting
    ? "Reconnecting…"
    : connected
      ? "Companion connected"
      : "Companion offline";

  const statusDot = connected ? "connected" : "";

  return (
    <div className="app-shell">
      {/* ── Sidebar ─────────────────────────────────────────────────────────── */}
      <aside className={`sidebar ${menu ? "open" : ""}`}>
        <Link to="/" className="brand" onClick={() => setMenu(false)}>
          <span className="brand-mark"><Fingerprint size={33} strokeWidth={1.8} /></span>
          Gustee<span className="text-primary text-xs">®</span>
        </Link>
        <div className="nav-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {navigation.map((item) => (
            <Link key={item.view} to={item.path} onClick={() => setMenu(false)}
              className={`nav-item ${view === item.view ? "active" : ""}`}>
              <item.icon />{item.label}
            </Link>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="device-state">
            <div className="flex items-center gap-2 font-medium">
              <Monitor size={14} />
              Gustee companion
              {reconnecting
                ? <Loader2 size={12} className="ml-auto animate-spin text-muted-foreground" />
                : <span className={`dot ${statusDot} ml-auto`} />}
            </div>
            <div className="text-muted-foreground mt-2 text-[10px]">
              {reconnecting ? "Reconnecting automatically…" : connected ? "Connected · local processing" : "Not connected"}
            </div>
            <Button variant="outline" size="sm" className="mt-3 w-full"
              onClick={() => { setError(""); setPairing(true); }}>
              {connected ? "Connection details" : "Connect device"}
              <ArrowUpRight size={12} />
            </Button>
          </div>
          <div className="flex items-center gap-2 mt-5 text-[10px] text-muted-foreground">
            <ShieldCheck size={13} />Your gestures stay on your device.
          </div>
          <div className="mt-4 text-[9px] font-mono text-muted-foreground">GUSTEE / V1.0</div>
        </div>
      </aside>

      {/* ── Main workspace ──────────────────────────────────────────────────── */}
      <div className="workspace">
        <header className="topbar">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" className="mobile-menu"
              aria-label="Toggle navigation" onClick={() => setMenu(!menu)}>
              <Menu />
            </Button>
            <div className="topbar-crumb">
              <span>Workspace</span><ChevronRight size={12} />
              <strong>{navigation.find((item) => item.view === view)?.label}</strong>
            </div>
          </div>
          <div className="flex items-center gap-5">
            <span className="topbar-status flex items-center gap-2 text-[10px] text-muted-foreground">
              {reconnecting
                ? <Loader2 size={11} className="animate-spin" />
                : <span className={`dot ${statusDot}`} />}
              {statusLabel}
            </span>
            <span className="h-5 border-l border-border" />
            <div className="avatar" title="Local workspace">GS</div>
          </div>
        </header>
        <main className="page-content">
          {children}
          <footer className="page-footer">
            <span className="flex items-center gap-2"><ShieldCheck size={11} />LOCAL-FIRST. PRIVACY BY DESIGN.</span>
            <span className="flex items-center gap-3">
              <Link to="/privacy" className="hover:text-foreground">Privacy</Link>
              <span>MADE FOR A MORE NATURAL WORKFLOW <span className="text-primary">↗</span></span>
            </span>
          </footer>
        </main>
      </div>

      {/* ── Pairing modal ────────────────────────────────────────────────────── */}
      {pairing && (
        <div className="modal-overlay" onClick={() => setPairing(false)}>
          <section className="modal" role="dialog" aria-modal="true"
            aria-labelledby="pair-title" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center">
              <h2 id="pair-title">Connect your PC</h2>
              <Button variant="ghost" size="icon" aria-label="Close" onClick={() => setPairing(false)}><X /></Button>
            </div>
            <p className="page-subtitle mt-3">
              Your camera, model, and desktop apps run privately on your computer.
              Once paired, Gustee reconnects automatically on every page refresh.
            </p>
            <div className="notice">
              <strong className="text-foreground">Install once:</strong> Gustee runs locally in the background and keeps your training data on this computer.<br />
              <strong className="text-foreground">Windows:</strong> Install Gustee, then open it from the Start menu.<br />
              <strong className="text-foreground">macOS:</strong> Download the macOS package, then run the installer from the app bundle.<br />
              <strong className="text-foreground">Linux:</strong> Download the Linux package, extract it, and run the installer script.<br /><br />
              Use the website only to pair this device and train or manage custom gestures.
            </div>
            <div className="mt-4 grid gap-2">
              <Button asChild variant="outline" className="w-full">
                <a href="https://github.com/hari9am/guestee/releases/latest/download/Gustee-Setup.exe" target="_blank" rel="noreferrer">
                  <ArrowDownToLine />Download Windows setup
                </a>
              </Button>
              <Button asChild variant="outline" className="w-full">
                <a href="https://github.com/hari9am/guestee/releases/latest/download/Gustee-macOS.zip" target="_blank" rel="noreferrer">
                  <ArrowDownToLine />Download macOS companion
                </a>
              </Button>
              <Button asChild variant="outline" className="w-full">
                <a href="https://github.com/hari9am/guestee/releases/latest/download/Gustee-Linux-x64.tar.gz" target="_blank" rel="noreferrer">
                  <ArrowDownToLine />Download Linux companion
                </a>
              </Button>
            </div>
            <form onSubmit={async (e) => { e.preventDefault(); if (await connect(tokenInput.trim())) setPairing(false); }}>
              <label className="field">
                <span>Pairing key</span>
                <input type="password" value={tokenInput}
                  onChange={(e) => setTokenInput(e.target.value)}
                  placeholder="Paste the key from your companion"
                  autoComplete="off" required />
              </label>
              {error && <p className="error-message" role="alert">{error}</p>}
              {connected && <p className="text-success text-xs mb-4">Connected. Gustee will reconnect automatically next time.</p>}
              <Button className="w-full" disabled={busy || !tokenInput.trim()} type="submit">
                <Monitor />
                {busy ? "Connecting…" : connected ? "Reconnect" : "Connect companion"}
              </Button>
            </form>
            <p className="text-muted-foreground text-[10px] mt-4 leading-relaxed">
              Allow local network access if prompted. Chrome or Edge recommended.
              Your pairing key is stored for this browser session and used to auto-reconnect.
            </p>
          </section>
        </div>
      )}
    </div>
  );
}
