"use client";

import { useEffect, useState } from "react";

import { ConsoleShell } from "@/components/console-shell";
import { Panel } from "@/components/panel";
import {
  type AlertRule,
  type ApiKeyRecord,
  bootstrapDemoTenant,
  createDemoAlertRule,
  createDemoApiKey,
  listAlertRules,
  listApiKeys,
} from "@/lib/api";

export default function SettingsPage() {
  const [apiKeys, setApiKeys] = useState<ApiKeyRecord[]>([]);
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [lastCreatedKey, setLastCreatedKey] = useState<string>("");

  const load = async () => {
    const [nextKeys, nextRules] = await Promise.all([listApiKeys(), listAlertRules()]);
    setApiKeys(nextKeys);
    setRules(nextRules);
  };

  useEffect(() => {
    let mounted = true;
    void (async () => {
      const [nextKeys, nextRules] = await Promise.all([listApiKeys(), listAlertRules()]);
      if (!mounted) return;
      setApiKeys(nextKeys);
      setRules(nextRules);
    })();
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <ConsoleShell title="Tenant Settings" eyebrow="Control Plane">
      <div className="content-grid">
        <Panel title="Bootstrap Actions" description="Spin up the demo tenant, ingest key, and first alert rule from the UI.">
          <div className="action-stack">
            <button
              className="action-button"
              onClick={async () => {
                await bootstrapDemoTenant();
                await load();
              }}
            >
              Create Demo Tenant
            </button>
            <button
              className="action-button secondary"
              onClick={async () => {
                const record = await createDemoApiKey();
                setLastCreatedKey(record.raw_api_key ?? "");
                await load();
              }}
            >
              Create Ingest API Key
            </button>
            <button
              className="action-button secondary"
              onClick={async () => {
                await createDemoAlertRule();
                await load();
              }}
            >
              Create Critical Latency Rule
            </button>
          </div>

          {lastCreatedKey ? (
            <div className="highlight-card">
              <p className="eyebrow">Last Created API Key</p>
              <strong>{lastCreatedKey}</strong>
            </div>
          ) : null}
        </Panel>

        <Panel title="Current API Keys" description="Control-plane key inventory for the demo tenant.">
          <div className="stack-list">
            {apiKeys.length ? (
              apiKeys.map((item) => (
                <article className="list-card" key={item.id}>
                  <div className="list-row">
                    <strong>{item.name}</strong>
                    <span className="pill">{item.key_prefix}</span>
                  </div>
                  <p>{item.scopes.join(", ")}</p>
                </article>
              ))
            ) : (
              <div className="empty-state">No API keys yet.</div>
            )}
          </div>
        </Panel>
      </div>

      <Panel title="Alert Rules" description="Rules stored in metadata and consumed by alert-engine.">
        <div className="stack-list">
          {rules.length ? (
            rules.map((rule) => (
              <article className="list-card" key={rule.id}>
                <div className="list-row">
                  <strong>{rule.name}</strong>
                  <span className="pill">{rule.severity}</span>
                </div>
                <p>
                  {rule.metric_name} {rule.operator} {rule.threshold}
                </p>
              </article>
            ))
          ) : (
            <div className="empty-state">No rules created yet.</div>
          )}
        </div>
      </Panel>
    </ConsoleShell>
  );
}
