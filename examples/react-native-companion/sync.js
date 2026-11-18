// sync.js — Background synchronization module for React Native companion app
import { listRecords, markAsSynced } from "./db";

const SERVER_SYNC_URL = "http://localhost:8000/api/sync/push";

export async function syncNow() {
  const dirtyRecords = listRecords().filter((r) => r.dirty);
  if (dirtyRecords.length === 0) return { synced: 0, status: "UP_TO_DATE" };

  try {
    const payload = {
      transactions: dirtyRecords.map((r) => ({
        client_tx_id: r.clientTxId,
        entity_type: r.type,
        action: "CREATE",
        client_timestamp: r.createdAt,
        payload: r.data
      }))
    };

    const res = await fetch(SERVER_SYNC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      dirtyRecords.forEach((r) => markAsSynced(r.id));
      return { synced: dirtyRecords.length, status: "SUCCESS" };
    } else {
      return { synced: 0, status: "SERVER_ERROR" };
    }
  } catch (err) {
    console.log("Offline or server unreachable, keeping local queue.");
    return { synced: 0, status: "OFFLINE" };
  }
}

export function startAutoSync(intervalMs = 60000) {
  const interval = setInterval(async () => {
    await syncNow();
  }, intervalMs);

  return () => clearInterval(interval);
}
