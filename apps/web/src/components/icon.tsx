import type { CSSProperties } from "react";

const paths = {
  today: "M3 10.5 12 3l9 7.5M5 9v11h5v-6h4v6h5V9",
  projects:
    "M3 7a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z",
  plus: "M12 5v14M5 12h14",
  arrow: "M5 12h14m-5-5 5 5-5 5",
  back: "M19 12H5m5-5-5 5 5 5",
  up: "m6 15 6-6 6 6",
  down: "m6 9 6 6 6-6",
  book: "M4 4h12a3 3 0 0 1 3 3v14H7a3 3 0 0 1-3-3V4Zm0 13h15M8 8h7M8 12h5",
  check: "m5 12 4 4L19 6",
  clock: "M12 8v4l3 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0",
  lock: "M7 10V7a5 5 0 0 1 10 0v3M5 10h14v11H5Zm7 5v2",
  logout: "M9 4H4v16h5M10 12h11m-4-4 4 4-4 4",
  eye: "M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Zm13 0a3 3 0 1 1-6 0 3 3 0 0 1 6 0",
  info: "M12 11v6M12 7h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0",
} as const;

export function Icon({
  name,
  size = 20,
  style,
}: {
  name: keyof typeof paths;
  size?: number;
  style?: CSSProperties;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.65"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      style={style}
    >
      <path d={paths[name]} />
    </svg>
  );
}

export function Brand() {
  return (
    <span className="brand">
      <span className="brand-mark">
        <Icon name="book" size={21} />
      </span>
      <span>
        Daymark<span className="brand-caption">A little proof, every day.</span>
      </span>
    </span>
  );
}
