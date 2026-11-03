import { Link } from "react-router-dom";

type LegalPageProps = {
  page: "privacy" | "terms";
};

const LegalPage = ({ page }: LegalPageProps) => {
  const isPrivacy = page === "privacy";

  return (
    <div className="flex min-h-screen flex-col text-white">
      <header className="flex items-center justify-between px-6 py-5 sm:px-10">
        <Link
          className="text-sm text-white/70 transition-colors hover:text-white"
          to="/"
        >
          ← Back to CheckMates
        </Link>
        <nav aria-label="Legal pages" className="flex gap-4 text-sm">
          <Link
            aria-current={isPrivacy ? "page" : undefined}
            className={isPrivacy ? "text-white" : "text-white/50 hover:text-white"}
            to="/privacy-policy"
          >
            Privacy
          </Link>
          <Link
            aria-current={!isPrivacy ? "page" : undefined}
            className={!isPrivacy ? "text-white" : "text-white/50 hover:text-white"}
            to="/terms-of-service"
          >
            Terms
          </Link>
        </nav>
      </header>

      <main className="mx-auto w-full max-w-3xl flex-1 px-6 pb-12 pt-6 sm:px-10">
        <div className="mb-8 space-y-2 border-b border-white/15 pb-6">
          <p className="text-sm font-semibold uppercase tracking-widest text-sky-400">
            CheckMates
          </p>
          <h1 className="text-3xl font-bold sm:text-4xl">
            {isPrivacy ? "Privacy Policy" : "Terms of Service"}
          </h1>
          <p className="text-sm text-white/60">
            {isPrivacy
              ? "How information is used when you play on CheckMates."
              : "The ground rules for using CheckMates."}
          </p>
        </div>

        {isPrivacy ? <PrivacyContent /> : <TermsContent />}
      </main>
      <footer className="border-t border-white/10 px-6 py-4 text-center text-xs text-white/50">
        CheckMates is an educational chess project.{" "}
        <Link className="underline underline-offset-2 hover:text-white" to="/">
          Return to the home page
        </Link>
        .
      </footer>
    </div>
  );
};

const PrivacyContent = () => (
  <div className="space-y-7 leading-7 text-white/75">
    <section className="space-y-2">
      <h2 className="text-xl font-semibold text-white">Information used</h2>
      <p>
        When you register, CheckMates uses your username, email address, and
        password. Passwords are stored as hashes, not as plain text. You may
        also add an avatar and preferences such as board colors.
      </p>
      <p>
        To provide the service, CheckMates stores chess games and moves, results,
        ratings, tournament participation, and online presence. If you use
        friends or chat features, friend relationships and messages you send
        are processed as well.
      </p>
    </section>

    <section className="space-y-2">
      <h2 className="text-xl font-semibold text-white">How it is used</h2>
      <p>
        This information supports account sign-in, matchmaking, games and
        tournaments, profiles, ratings, statistics, and social features.
        Sign-in tokens are stored in your browser&apos;s local storage to keep
        you signed in between visits.
      </p>
    </section>

    <section className="space-y-2">
      <h2 className="text-xl font-semibold text-white">
        Information visible to other players
      </h2>
      <p>
        Your username, avatar, rating, and relevant game or tournament details
        may appear in profiles, leaderboards, match listings, and games.
        Private chat messages are available to the conversation participants
        and are processed to deliver the chat feature.
      </p>
    </section>

    <section className="space-y-2">
      <h2 className="text-xl font-semibold text-white">
        Storage and your choices
      </h2>
      <p>
        Information is stored by the operator of the CheckMates instance you use.
        Instance hosting and retention practices may vary. Information may be
        accessed by the people maintaining that instance when needed to
        operate, troubleshoot, or protect the service; it is not intended for
        sale.
      </p>
      <p>
        Signing out removes the locally stored session from your browser. For
        questions about account information, retention, or deletion, contact
        the team or administrator responsible for your instance to ask what
        options are available.
      </p>
    </section>

    <section className="space-y-2">
      <h2 className="text-xl font-semibold text-white">Policy updates</h2>
      <p>
        This policy may be updated as the project or its practices change.
        Please check this page for the current information.
      </p>
    </section>
  </div>
);

const TermsContent = () => (
  <div className="space-y-7 leading-7 text-white/75">
    <section className="space-y-2">
      <h2 className="text-xl font-semibold text-white">Using CheckMates</h2>
      <p>
        CheckMates is an educational chess platform for playing against people or
        AI, viewing matches, and using features such as profiles, ratings,
        tournaments, friends, and chat. Use the service lawfully, provide
        accurate account information, and keep your sign-in details secure.
        Do not use another person&apos;s account without permission.
      </p>
    </section>

    <section className="space-y-2">
      <h2 className="text-xl font-semibold text-white">Fair play and conduct</h2>
      <p>
        Play fairly and treat other players respectfully. Do not cheat, exploit
        bugs for an unfair advantage, disrupt the service, harass users, send
        unlawful or abusive content, or try to access accounts or information
        that are not yours.
      </p>
    </section>

    <section className="space-y-2">
      <h2 className="text-xl font-semibold text-white">Your content</h2>
      <p>
        You are responsible for content you submit, including chat messages
        and profile information. Only share content you are allowed to share.
        Game records, ratings, and statistics are provided for gameplay and
        may change when results are updated or corrected.
      </p>
    </section>

    <section className="space-y-2">
      <h2 className="text-xl font-semibold text-white">Access and availability</h2>
      <p>
        The instance operator may restrict access when reasonably needed to
        address abuse, protect users, or keep the service working. Features
        may change or become unavailable, and uninterrupted access is not
        guaranteed. Do not rely on CheckMates as the only copy of important
        information.
      </p>
      <p>
        You may stop using the service at any time. Account and data handling
        depends on the operator of your instance; see the{" "}
        <Link
          className="text-sky-300 underline underline-offset-2 hover:text-sky-200"
          to="/privacy-policy"
        >
          Privacy Policy
        </Link>
        .
      </p>
    </section>

    <section className="space-y-2">
      <h2 className="text-xl font-semibold text-white">Terms updates</h2>
      <p>
        These terms may be updated when the project or its rules change.
        Continued use means you agree to follow the current terms, subject to
        any rights that apply where you live.
      </p>
    </section>
  </div>
);

export default LegalPage;
