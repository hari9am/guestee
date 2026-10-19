import { createFileRoute } from "@tanstack/react-router";
import { GestureWorkspace } from "@/components/gesture-workspace";
export const Route = createFileRoute("/training")({
  head: () => ({
    meta: [
      { title: "Train your model — Gustee" },
      {
        name: "description",
        content:
          "Record hand gesture samples and train your local custom PyTorch classifier.",
      },
      { property: "og:title", content: "Train your model — Gustee" },
      {
        property: "og:description",
        content:
          "A private gesture model trained entirely on your own hand poses.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Page,
});
function Page() {
  return <GestureWorkspace view="training" />;
}
