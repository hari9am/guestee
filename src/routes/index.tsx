import { createFileRoute } from "@tanstack/react-router";
import { GestureWorkspace } from "@/components/gesture-workspace";
export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Gustee — Your personal launch space" },
      {
        name: "description",
        content: "Launch your applications with your own custom hand gestures.",
      },
      { property: "og:title", content: "Gustee — Your personal launch space" },
      {
        property: "og:description",
        content: "Your gestures. Your apps. A more natural workflow.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});
function Index() {
  return <GestureWorkspace view="overview" />;
}
