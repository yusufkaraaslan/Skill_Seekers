import { useMemo } from 'react';

// Animated radar sweep — blips represent skills discovered across CLIs.
export default function Radar({ blips = 18, size = 220 }: { blips?: number; size?: number }) {
  const points = useMemo(
    () =>
      Array.from({ length: blips }, (_, i) => {
        const angle = (i * 137.5) % 360; // golden angle scatter
        const r = 22 + ((i * 53) % 68);
        const rad = (angle * Math.PI) / 180;
        return {
          x: 100 + r * Math.cos(rad) * 0.92,
          y: 100 + r * Math.sin(rad) * 0.92,
          delay: (i % 6) * 0.4,
          hot: i % 5 === 0,
        };
      }),
    [blips]
  );

  return (
    <svg viewBox="0 0 200 200" width={size} height={size} className="shrink-0">
      <defs>
        <radialGradient id="sweep" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="hsl(187 92% 50% / 0.25)" />
          <stop offset="100%" stopColor="hsl(187 92% 50% / 0)" />
        </radialGradient>
        <linearGradient id="beam" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="hsl(187 92% 50% / 0.5)" />
          <stop offset="100%" stopColor="hsl(187 92% 50% / 0)" />
        </linearGradient>
      </defs>

      {/* rings */}
      {[40, 65, 90, 98].map((r) => (
        <circle key={r} cx="100" cy="100" r={r} fill="none" stroke="hsl(220 16% 18%)" strokeWidth="0.6" />
      ))}
      {/* cross */}
      <line x1="100" y1="2" x2="100" y2="198" stroke="hsl(220 16% 14%)" strokeWidth="0.5" />
      <line x1="2" y1="100" x2="198" y2="100" stroke="hsl(220 16% 14%)" strokeWidth="0.5" />
      <circle cx="100" cy="100" r="98" fill="none" stroke="hsl(187 92% 50% / 0.25)" strokeWidth="1" />

      {/* sweep */}
      <g className="animate-radar">
        <path d="M100 100 L100 2 A98 98 0 0 0 31 31 Z" fill="url(#sweep)" />
        <line x1="100" y1="100" x2="100" y2="2" stroke="hsl(187 92% 60%)" strokeWidth="1" />
      </g>

      {/* blips */}
      {points.map((p, i) => (
        <circle
          key={i}
          cx={p.x}
          cy={p.y}
          r={p.hot ? 3.4 : 2.2}
          className="animate-blip"
          style={{ animationDelay: `${p.delay}s` }}
          fill={p.hot ? 'hsl(45 93% 55%)' : 'hsl(187 92% 55%)'}
          opacity="0.8"
        />
      ))}

      {/* center */}
      <circle cx="100" cy="100" r="3" fill="hsl(187 92% 60%)" />
      <circle cx="100" cy="100" r="6" fill="none" stroke="hsl(187 92% 50% / 0.6)" strokeWidth="0.8" />
    </svg>
  );
}
