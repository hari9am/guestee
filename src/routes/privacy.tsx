import { createFileRoute, Link } from "@tanstack/react-router";

export const Route = createFileRoute("/privacy")({
  head: () => ({
    meta: [
      { title: "Privacy Policy — Gustee" },
      {
        name: "description",
        content:
          "Learn how Gustee handles camera access, gesture data, and device information.",
      },
    ],
  }),
  component: PrivacyPolicy,
});

function PrivacyPolicy() {
  return (
    <main className="min-h-screen bg-background px-6 py-12 text-foreground sm:px-10">
      <article className="mx-auto max-w-3xl">
        <Link
          to="/"
          className="text-sm text-primary underline-offset-4 hover:underline"
        >
          Back to Gustee
        </Link>
        <h1 className="mt-8 text-4xl font-bold tracking-tight">
          Gustee Privacy Policy
        </h1>
        <p className="mt-3 text-sm text-muted-foreground">
          Last updated: October 23, 2026
        </p>

        <div className="mt-8 space-y-8 leading-7 text-muted-foreground">
          <section>
            <h2 className="text-xl font-semibold text-foreground">Overview</h2>
            <p className="mt-2">
              Gustee is a hand-gesture desktop companion and optional web
              workspace. The companion processes camera input and gesture
              training on your computer. You can use its built-in gestures
              without connecting to the website. This policy explains what
              information the companion and website handle and where it is
              stored.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground">
              Camera and gesture data
            </h2>
            <p className="mt-2">
              The companion does not open the camera until you grant camera
              access in its consent prompt. Consent is requested again when the
              companion restarts. While recognition, preview, or recording is
              active, the companion processes camera frames locally to detect
              hand gestures. Frames are held in memory for processing and are
              not uploaded to Gustee servers.
            </p>
            <p className="mt-2">
              If you connect the website to the companion and request a live
              preview, the companion serves the current preview frame to your
              browser over your computer&apos;s loopback connection (127.0.0.1).
              This preview is not sent to Gustee&apos;s hosted website. You can
              stop recognition or preview, pause the camera, or revoke consent
              using the companion controls.
            </p>
            <p className="mt-2">
              If you choose to record custom gestures, the companion stores
              hand-landmark training samples and the resulting model locally; it
              does not store video recordings. Gesture mappings, settings, and
              launch history are also stored on your computer. On Windows, the
              companion data folder is{" "}
              <code className="rounded bg-muted px-1.5 py-0.5 text-foreground">
                %LOCALAPPDATA%\Gustee
              </code>
              . You can remove custom samples and mappings in the companion
              workspace or uninstall the app; uninstalling may not remove data
              stored separately in that folder.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground">
              Pairing and the website
            </h2>
            <p className="mt-2">
              Pairing is optional. When you connect, the website communicates
              directly with the companion running on your computer. The one-time
              pairing key is kept in your browser tab&apos;s session storage so
              the website can reconnect during that tab session; it is not an
              account password. The companion creates a new key when it
              restarts.
            </p>
            <p className="mt-2">
              The website does not need your camera to pair with the desktop
              companion. It sends your chosen gesture settings and training
              actions to the companion, which saves them locally. The
              companion stores your samples, model, settings, and history
              locally by default and does not connect to a cloud database unless
              an operator explicitly configures a MongoDB connection using the
              MONGO_URI environment variable. If configured, data may be sent
              to that database, whose operator controls its handling.
            </p>
            <p className="mt-2">
              The website is hosted by Netlify. Like other website hosts,
              Netlify may process technical request information, such as IP
              addresses and server logs, to deliver and secure the website. See{" "}
              <a
                className="text-primary underline-offset-4 hover:underline"
                href="https://www.netlify.com/privacy/"
                target="_blank"
                rel="noreferrer"
              >
                Netlify&apos;s privacy policy
              </a>{" "}
              for details.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground">
              App launches and third parties
            </h2>
            <p className="mt-2">
              The companion can launch approved applications and HTTPS websites
              according to your gesture mappings. Those applications and
              websites are separate services and may handle information under
              their own privacy policies. Gustee does not control their
              practices.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-foreground">
              Changes and contact
            </h2>
            <p className="mt-2">
              This policy may be updated when Gustee&apos;s features or data
              practices change. The current version will be published at this
              page, with its latest update date shown above. For questions or
              support, contact the project through{" "}
              <a
                className="text-primary underline-offset-4 hover:underline"
                href="https://github.com/hari9am/guestee/issues"
                target="_blank"
                rel="noreferrer"
              >
                Gustee&apos;s GitHub issues page
              </a>
              .
            </p>
          </section>
        </div>
      </article>
    </main>
  );
}
