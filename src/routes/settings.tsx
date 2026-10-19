import { createFileRoute } from "@tanstack/react-router";
import { GestureWorkspace } from "@/components/gesture-workspace";
export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Settings — Gustee" },
      {
        name: "description",
        content:
          "Adjust gesture confidence, hold time, cooldown, and camera settings.",
      },
      { property: "og:title", content: "Settings — Gustee" },
      {
        property: "og:description",
        content:
          "Fine-tune gesture recognition and accidental-launch protection.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Page,
});
function Page() {
  return <GestureWorkspace view="settings" />;
}
