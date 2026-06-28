import { ReadinessWorkspace as ReadinessWorkspaceType } from "../types";

type Props = {
  data: ReadinessWorkspaceType | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
};

function ValueList(props: { title: string; values: Record<string, unknown> }): JSX.Element {
  return (
    <section className="panel-card readiness-card">
      <div className="panel-card__header">
        <h2 className="panel-card__title">{props.title}</h2>
      </div>
      <div className="panel-card__body panel-card__body--padded">
        <dl className="readiness-dl">
          {Object.entries(props.values).map(([key, value]) => (
            <div key={key}>
              <dt>{key.replaceAll("_", " ")}</dt>
              <dd>{Array.isArray(value) ? value.join(", ") : String(value)}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}

export function ReadinessWorkspace(props: Props): JSX.Element {
  const { data, loading, error, onRefresh } = props;
  if (error) {
    return (
      <div className="alert-banner" role="alert" style={{ margin: 0 }}>
        {error}
      </div>
    );
  }
  if (!data) {
    return (
      <div className="panel-card">
        <div className="panel-card__body panel-card__body--padded">
          <p style={{ margin: 0, color: "var(--text-secondary)" }}>
            {loading ? "Loading readiness workspace..." : "No readiness data loaded."}
          </p>
          <button type="button" className="btn btn--secondary" onClick={onRefresh} style={{ marginTop: 12 }}>
            Refresh readiness
          </button>
        </div>
      </div>
    );
  }
  return (
    <div className="readiness-grid">
      <section className="panel-card readiness-card readiness-card--wide">
        <div className="panel-card__header">
          <div className="panel-card__header-row">
            <div>
              <h2 className="panel-card__title">{data.workload}</h2>
              <p className="panel-card__hint">{data.criticality}</p>
            </div>
            <button type="button" className="btn btn--secondary" disabled={loading} onClick={onRefresh}>
              {loading ? "Refreshing..." : "Refresh"}
            </button>
          </div>
        </div>
        <div className="panel-card__body panel-card__body--padded">
          <div className="readiness-kpis">
            <div>
              <span>Availability target</span>
              <strong>{data.availability_target}</strong>
            </div>
            <div>
              <span>RTO</span>
              <strong>{data.rto}</strong>
            </div>
            <div>
              <span>RPO</span>
              <strong>{data.rpo}</strong>
            </div>
          </div>
        </div>
      </section>

      <ValueList title="SLO Summary" values={data.slo_summary} />
      <ValueList title="Observability Readiness" values={data.observability_readiness} />
      <ValueList title="Runbook Coverage" values={data.runbook_coverage} />
      <ValueList title="Resilience Test Status" values={data.resilience_test_status} />

      <section className="panel-card readiness-card">
        <div className="panel-card__header">
          <h2 className="panel-card__title">Open Risks</h2>
        </div>
        <div className="panel-card__body panel-card__body--padded">
          <ul className="readiness-list">
            {data.open_risks.map((risk) => (
              <li key={String(risk.id)}>
                <strong>{String(risk.id)}</strong>
                <span>{String(risk.summary)}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="panel-card readiness-card readiness-card--wide">
        <div className="panel-card__header">
          <h2 className="panel-card__title">Enablement Progress</h2>
        </div>
        <div className="panel-card__body panel-card__body--padded">
          <ul className="readiness-list readiness-list--columns">
            {data.enablement_progress.map((item) => (
              <li key={String(item.item)}>
                <strong>{String(item.item)}</strong>
                <span>{String(item.status)}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="panel-card readiness-card readiness-card--wide">
        <div className="panel-card__header">
          <h2 className="panel-card__title">Problem Management Actions</h2>
        </div>
        <div className="panel-card__body panel-card__body--padded">
          <ul className="readiness-list readiness-list--columns">
            {data.problem_management_actions.map((item) => (
              <li key={item}>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}
