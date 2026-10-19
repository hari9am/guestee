<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

## GestureFlow architecture
- Keep the web interface in TanStack routes with a shared workspace provider; navigation must preserve the active companion connection.
- Run camera capture, PyTorch training, data persistence, and desktop launches in the downloadable cross-platform companion, not the hosted web runtime; operating-system access requires a local process.
- Bind the companion to loopback, require an ephemeral pairing key, validate browser origins, and launch only hardcoded approved applications with shell disabled; websites must be HTTPS.
- Keep all visual styles and semantic colors in the global design system; application views consume the existing Button component.
- Keep disconnected drafts in memory and persist connected configuration only in the local companion; offline edits must never silently overwrite a saved device workspace.
- Pre-optimize shared UI dependencies in Vite while preserving the template React deduplication; late dependency graph replacement can mix React dispatchers in open preview tabs.
- Keep consent and tray UI on the desktop main thread, with loopback server and camera workers in background threads; never capture without in-session consent or suppress OS camera indicators.
