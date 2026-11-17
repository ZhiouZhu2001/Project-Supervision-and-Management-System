import { Brand, Icon } from "@/components/icon";
import { LoginForm } from "@/components/login-form";

export default function LoginPage() {
  return (
    <main className="login-layout">
      <section className="login-story" aria-labelledby="manifesto">
        <Brand />
        <div className="login-manifesto">
          <p className="eyebrow">YOUR DAYS, ACCOUNTED FOR.</p>
          <h1 id="manifesto">
            Less drifting.
            <br />
            More <em>doing.</em>
          </h1>
          <p>
            A quiet space to record what you actually did.
            <br />A little honesty to help you keep going.
          </p>
          <div className="paper-stack" aria-hidden="true">
            <div className="paper-top">
              <span>SMALL STEPS. REAL PROGRESS.</span>
              <Icon name="book" size={14} />
            </div>
            <div className="paper-row">
              <span>
                <Icon name="check" size={14} />
              </span>
              Show up.<small>01</small>
            </div>
            <div className="paper-row">
              <span>
                <Icon name="check" size={14} />
              </span>
              Write it down.<small>02</small>
            </div>
            <div className="paper-row">
              <span>
                <Icon name="arrow" size={14} />
              </span>
              Keep going.<small>03</small>
            </div>
          </div>
          <div className="paper-caption">
            One project. One log. Something to build on.
          </div>
        </div>
        <footer className="login-story-footer">
          <span>Built for one person. You.</span>
          <span>PROJECT SUPERVISION</span>
        </footer>
      </section>
      <section className="login-main" aria-labelledby="login-heading">
        <div className="login-mobile-brand">
          <Brand />
        </div>
        <div className="login-box">
          <p className="eyebrow">WELCOME TO YOUR SPACE</p>
          <h2 id="login-heading">Pick up where you left off.</h2>
          <p className="page-description">
            Sign in to your personal workspace.
          </p>
          <LoginForm />
          <p className="login-privacy">
            <Icon name="lock" size={14} />
            One owner. A space that stays yours.
          </p>
        </div>
      </section>
    </main>
  );
}
