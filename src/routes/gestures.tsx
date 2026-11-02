import { createFileRoute } from "@tanstack/react-router";
import { GestureWorkspace } from "@/components/gesture-workspace";
export const Route = createFileRoute("/gestures")({
  head: () => ({
    meta: [
      { title: "My gestures — Gestuee" },
      {
        name: "description",
        content: "Assign your own hand gestures to your favorite applications.",
      },
      { property: "og:title", content: "My gestures — Gestuee" },
      {
        property: "og:description",
        content: "Create and manage your custom gesture mappings.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Page,
});
function Page() {
  return <GestureWorkspace view="gestures" />;
}
