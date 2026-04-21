"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Overview" },
  { href: "/traces", label: "Traces" },
  { href: "/incidents", label: "Incidents" },
  { href: "/alerts", label: "Alerts" },
  { href: "/services", label: "Services" },
  { href: "/settings", label: "Settings" },
];

export function ConsoleShell({
  title,
  eyebrow,
  children,
}: {
  title: string;
  eyebrow: string;
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="console-root">
      <aside className="console-sidebar">
        <div className="brand-block">
          <div className="brand-mark" />
          <div>
            <p className="eyebrow">Real-Time Observability</p>
            <h1 className="brand-title">Incident Intelligence</h1>
          </div>
        </div>

        <nav className="nav-stack" aria-label="Primary">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href;
            return (
              <Link key={item.href} href={item.href} className={`nav-link ${active ? "is-active" : ""}`}>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-foot">
          <span className="pill pill-live">Demo Tenant</span>
          <p className="muted-copy">
            Synthetic probes, traces, incidents, and assistive RCA flow through the same platform model.
          </p>
        </div>
      </aside>

      <main className="console-main">
        <header className="page-head">
          <div>
            <p className="eyebrow">{eyebrow}</p>
            <h2 className="page-title">{title}</h2>
          </div>
          <div className="page-actions">
            <span className="pill pill-live">Live Pipeline</span>
            <span className="pill">demo-tenant</span>
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
