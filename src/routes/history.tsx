import { createFileRoute } from "@tanstack/react-router";
import { GestureWorkspace } from "@/components/gesture-workspace";
export const Route = createFileRoute("/history")({
  head: () => ({
    meta: [
      { title: "Launch history — Gustee" },
      {
        name: "description",
        content:
          "Review and export your gesture-triggered application launch history.",
      },
      { property: "og:title", content: "Launch history — Gustee" },
      {
        property: "og:description",
        content: "Every gesture and application launch in one place.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Page,
});
function Page() {
  return <GestureWorkspace view="history" />;
}
