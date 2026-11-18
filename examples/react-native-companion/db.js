// db.js — Local storage & offline queue engine for React Native
const storage = new Map();
let recordCounter = 1;

export function saveRecord(type, data, ashaId = "9363302117") {
  const id = `LOCAL-${Date.now()}-${recordCounter++}`;
  const record = {
    id,
    type,
    data,
    ashaId,
    clientTxId: `TX-${id}`,
    dirty: true,
    createdAt: new Date().toISOString()
  };
  storage.set(id, record);
  return record;
}

export function listRecords(type = null) {
  const all = Array.from(storage.values());
  if (!type) return all;
  return all.filter((r) => r.type === type);
}

export function pendingCount() {
  return Array.from(storage.values()).filter((r) => r.dirty).length;
}

export function markAsSynced(id, serverId = null) {
  const rec = storage.get(id);
  if (rec) {
    rec.dirty = false;
    if (serverId) rec.serverId = serverId;
    storage.set(id, rec);
  }
}
