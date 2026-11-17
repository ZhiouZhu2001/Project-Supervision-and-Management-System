import { Brand, Icon } from "@/components/icon";
import { LoginForm } from "@/components/login-form";

const STEPS = [
  { icon: "check" as const, label: "Show up.", index: "01" },
  { icon: "check" as const, label: "Write it down.", index: "02" },
  { icon: "arrow" as const, label: "Keep going.", index: "03" },
];

export default function LoginPage() {
  return (
    <main className="grid min-h-dvh grid-cols-2 max-[900px]:grid-cols-[46%_54%] max-[700px]:block">
      <section
        aria-labelledby="manifesto"
        className="flex flex-col justify-between border-r border-border bg-secondary px-14 py-12 max-[1150px]:px-[38px] max-[900px]:px-[25px] max-[900px]:py-8 max-[700px]:hidden"
      >
        <Brand />

        <div className="max-w-[420px]">
          <p className="mb-[10px] text-[10px] font-[650] tracking-[2px] text-accent-foreground">
            YOUR DAYS, ACCOUNTED FOR.
          </p>
          <h1
            id="manifesto"
            className="font-serif text-[56px] leading-[1.05] tracking-[-1.5px] text-foreground max-[900px]:text-[46px]"
          >
            Less drifting.
            <br />
            More <em className="italic text-accent-foreground">doing.</em>
          </h1>
          <p className="mt-5 text-[13px] text-muted-foreground">
            A quiet space to record what you actually did.
            <br />A little honesty to help you keep going.
          </p>

          <div className="relative mb-3 mt-9 w-[330px] max-w-full pb-2" aria-hidden="true">
            <div className="absolute -left-3 top-4 h-[calc(100%-16px)] w-[calc(100%+24px)] -rotate-[6deg] rounded-[10px] border border-[#8c9979]/50 bg-[#d9dfcb]" />
            <div className="relative rotate-[1.5deg] rounded-[10px] border border-[#8c9979]/60 bg-[#fafbf2] px-5 py-4 shadow-[0_10px_30px_-18px_rgba(41,45,41,0.55)]">
              <div className="flex items-center justify-between border-b border-[#e4e5de] pb-3">
                <span className="text-[9px] font-[600] tracking-[1.6px] text-sage-ink">
                  SMALL STEPS. REAL PROGRESS.
                </span>
                <Icon name="book" size={14} />
              </div>
              {STEPS.map((step) => (
                <div
                  key={step.label}
                  className="flex items-center gap-3 border-b border-[#e4e5de] py-[10px] last:border-b-0 last:pb-1"
                >
                  <span className="grid h-6 w-6 place-items-center rounded-full bg-sage text-sage-ink">
                    <Icon name={step.icon} size={13} />
                  </span>
                  <span className="text-[12px] text-foreground">{step.label}</span>
                  <span className="ml-auto text-[9px] text-muted-foreground">{step.index}</span>
                </div>
              ))}
            </div>
          </div>

          <p className="relative z-10 mt-4 text-[10px] text-muted-foreground">
            One project. One log. Something to build on.
          </p>
        </div>

        <footer className="flex justify-between gap-4 text-[10px] uppercase tracking-[1.4px] text-muted-foreground max-[900px]:flex-col">
          <span>Built for one person. You.</span>
          <span>PROJECT SUPERVISION</span>
        </footer>
      </section>

      <section
        aria-labelledby="login-heading"
        className="flex flex-col justify-center px-14 py-12 max-[1150px]:px-[38px] max-[700px]:min-h-dvh max-[700px]:px-[25px] max-[700px]:py-10"
      >
        <div className="mb-[60px] hidden max-[700px]:block">
          <Brand />
        </div>
        <div className="mx-auto w-full max-w-[360px]">
          <p className="mb-[10px] text-[10px] font-[650] tracking-[2px] text-accent-foreground">
            WELCOME TO YOUR SPACE
          </p>
          <h2
            id="login-heading"
            className="text-[28px] font-[650] leading-[1.15] tracking-[-0.8px] text-foreground"
          >
            Pick up where you left off.
          </h2>
          <p className="mb-7 mt-2 text-[13px] text-muted-foreground">
            Sign in to your personal workspace.
          </p>

          <LoginForm />

          <p className="mt-7 flex items-center justify-center gap-2 border-t border-border pt-6 text-[11px] text-muted-foreground">
            <Icon name="lock" size={14} />
            One owner. A space that stays yours.
          </p>
        </div>
      </section>
    </main>
  );
}
