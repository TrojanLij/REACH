import { useEffect, useMemo, useState } from "react";
import {
  createDnsZone,
  deleteDnsZone,
  listDnsZones,
  updateDnsZone
} from "../api/reachApi";
import { useApiConfig } from "../state/ApiConfigContext";

function defaultForm() {
  return {
    zone: "oob.example.test",
    a: "127.0.0.1",
    aaaa: "",
    ttl: 60,
    ns: "ns1.oob.example.test,ns2.oob.example.test",
    soa_mname: "",
    soa_rname: "",
    soa_serial: "",
    soa_refresh: 3600,
    soa_retry: 600,
    soa_expire: 1209600,
    soa_minimum: 300,
    wildcard: true,
    enabled: true
  };
}

function parseNs(value) {
  const raw = value.trim();
  if (!raw) {
    return null;
  }
  return raw
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function buildCreatePayload(form) {
  return {
    zone: form.zone.trim(),
    a: form.a.trim(),
    aaaa: form.aaaa.trim() || null,
    ttl: Number(form.ttl),
    ns: parseNs(form.ns),
    soa_mname: form.soa_mname.trim() || null,
    soa_rname: form.soa_rname.trim() || null,
    soa_serial: form.soa_serial ? Number(form.soa_serial) : null,
    soa_refresh: Number(form.soa_refresh),
    soa_retry: Number(form.soa_retry),
    soa_expire: Number(form.soa_expire),
    soa_minimum: Number(form.soa_minimum),
    wildcard: Boolean(form.wildcard),
    enabled: Boolean(form.enabled)
  };
}

function buildUpdatePayload(form) {
  return {
    a: form.a.trim(),
    aaaa: form.aaaa.trim() || null,
    ttl: Number(form.ttl),
    ns: parseNs(form.ns) || [],
    soa_mname: form.soa_mname.trim() || null,
    soa_rname: form.soa_rname.trim() || null,
    soa_serial: form.soa_serial ? Number(form.soa_serial) : null,
    soa_refresh: Number(form.soa_refresh),
    soa_retry: Number(form.soa_retry),
    soa_expire: Number(form.soa_expire),
    soa_minimum: Number(form.soa_minimum),
    wildcard: Boolean(form.wildcard),
    enabled: Boolean(form.enabled)
  };
}

function zoneToForm(zone) {
  return {
    zone: zone.zone || "",
    a: zone.a || "",
    aaaa: zone.aaaa || "",
    ttl: zone.ttl ?? 60,
    ns: (zone.ns || []).join(","),
    soa_mname: zone.soa_mname || "",
    soa_rname: zone.soa_rname || "",
    soa_serial: zone.soa_serial ?? "",
    soa_refresh: zone.soa_refresh ?? 3600,
    soa_retry: zone.soa_retry ?? 600,
    soa_expire: zone.soa_expire ?? 1209600,
    soa_minimum: zone.soa_minimum ?? 300,
    wildcard: Boolean(zone.wildcard),
    enabled: Boolean(zone.enabled)
  };
}

export function DnsZonesPage() {
  const { apiBase } = useApiConfig();
  const [zones, setZones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(defaultForm);

  const isEditing = useMemo(() => editingId !== null, [editingId]);

  useEffect(() => {
    async function loadZones() {
      setLoading(true);
      setError("");
      try {
        const data = await listDnsZones(apiBase);
        setZones(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load DNS zones.");
      } finally {
        setLoading(false);
      }
    }
    loadZones();
  }, [apiBase]);

  function resetForm() {
    setEditingId(null);
    setForm(defaultForm());
  }

  async function onSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      if (isEditing && editingId) {
        const payload = buildUpdatePayload(form);
        const updated = await updateDnsZone(editingId, payload, apiBase);
        setZones((prev) => prev.map((zone) => (zone.id === editingId ? updated : zone)));
      } else {
        const payload = buildCreatePayload(form);
        const created = await createDnsZone(payload, apiBase);
        setZones((prev) => [...prev, created]);
      }
      resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save DNS zone.");
    } finally {
      setSaving(false);
    }
  }

  function onEdit(zone) {
    setEditingId(zone.id);
    setForm(zoneToForm(zone));
  }

  async function onDelete(zone) {
    const confirmed = window.confirm(`Delete zone ${zone.zone}?`);
    if (!confirmed) {
      return;
    }
    setDeletingId(zone.id);
    setError("");
    try {
      await deleteDnsZone(zone.id, apiBase);
      setZones((prev) => prev.filter((item) => item.id !== zone.id));
      if (editingId === zone.id) {
        resetForm();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete DNS zone.");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <section>
      <h2>DNS Zones</h2>
      <p>Manage DNS zones used by the REACH DNS service.</p>
      {error && <p className="error">{error}</p>}

      <form className="dns-form" onSubmit={onSubmit}>
        <label>
          Zone
          <input
            type="text"
            value={form.zone}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, zone: event.target.value }))
            }
            required
            disabled={isEditing}
          />
        </label>
        <label>
          A (IPv4)
          <input
            type="text"
            value={form.a}
            onChange={(event) => setForm((prev) => ({ ...prev, a: event.target.value }))}
            required
          />
        </label>
        <label>
          AAAA (IPv6 optional)
          <input
            type="text"
            value={form.aaaa}
            onChange={(event) => setForm((prev) => ({ ...prev, aaaa: event.target.value }))}
          />
        </label>
        <label>
          TTL
          <input
            type="number"
            min="1"
            value={form.ttl}
            onChange={(event) => setForm((prev) => ({ ...prev, ttl: event.target.value }))}
          />
        </label>
        <label>
          NS (comma separated)
          <input
            type="text"
            value={form.ns}
            onChange={(event) => setForm((prev) => ({ ...prev, ns: event.target.value }))}
            placeholder="ns1.example.test,ns2.example.test"
          />
        </label>
        <label>
          SOA mname
          <input
            type="text"
            value={form.soa_mname}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, soa_mname: event.target.value }))
            }
          />
        </label>
        <label>
          SOA rname
          <input
            type="text"
            value={form.soa_rname}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, soa_rname: event.target.value }))
            }
          />
        </label>
        <label>
          SOA serial
          <input
            type="number"
            min="1"
            value={form.soa_serial}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, soa_serial: event.target.value }))
            }
          />
        </label>
        <label>
          SOA refresh
          <input
            type="number"
            min="1"
            value={form.soa_refresh}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, soa_refresh: event.target.value }))
            }
          />
        </label>
        <label>
          SOA retry
          <input
            type="number"
            min="1"
            value={form.soa_retry}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, soa_retry: event.target.value }))
            }
          />
        </label>
        <label>
          SOA expire
          <input
            type="number"
            min="1"
            value={form.soa_expire}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, soa_expire: event.target.value }))
            }
          />
        </label>
        <label>
          SOA minimum
          <input
            type="number"
            min="1"
            value={form.soa_minimum}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, soa_minimum: event.target.value }))
            }
          />
        </label>
        <label className="dns-check">
          <input
            type="checkbox"
            checked={form.wildcard}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, wildcard: event.target.checked }))
            }
          />
          Wildcard
        </label>
        <label className="dns-check">
          <input
            type="checkbox"
            checked={form.enabled}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, enabled: event.target.checked }))
            }
          />
          Enabled
        </label>
        <div className="dns-form-actions">
          <button type="submit" disabled={saving}>
            {saving ? "Saving..." : isEditing ? "Update Zone" : "Create Zone"}
          </button>
          {isEditing && (
            <button type="button" onClick={resetForm}>
              Cancel Edit
            </button>
          )}
        </div>
      </form>

      {loading && <p>Loading zones...</p>}

      {!loading && (
        <div className="dns-zone-list">
          {zones.length === 0 && <p>No DNS zones configured.</p>}
          {zones.map((zone) => (
            <details key={zone.id} className="dns-zone-item">
              <summary>
                {zone.zone} | A={zone.a} | ttl={zone.ttl} |{" "}
                {zone.enabled ? "enabled" : "disabled"}
              </summary>
              <div className="dns-zone-details">
                <p>
                  <strong>NS:</strong> {(zone.ns || []).join(", ") || "-"}
                </p>
                <p>
                  <strong>SOA:</strong> mname={zone.soa_mname}, rname={zone.soa_rname},
                  serial={zone.soa_serial}
                </p>
                <p>
                  <strong>Flags:</strong> wildcard={String(zone.wildcard)} enabled=
                  {String(zone.enabled)}
                </p>
                <div className="dns-zone-actions">
                  <button type="button" onClick={() => onEdit(zone)}>
                    Edit
                  </button>
                  <button
                    type="button"
                    className="danger"
                    disabled={deletingId === zone.id}
                    onClick={() => onDelete(zone)}
                  >
                    {deletingId === zone.id ? "Deleting..." : "Delete"}
                  </button>
                </div>
              </div>
            </details>
          ))}
        </div>
      )}
    </section>
  );
}
