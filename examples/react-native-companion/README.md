# React Native Companion App Example

This directory contains an example React Native companion application demonstrating:
1. **Offline-first record creation** in local device storage.
2. **Real-time pending sync counter** badge.
3. **Background auto-synchronization daemon** to the central FastAPI backend (`/api/sync/push`).
4. **Idempotent transaction push** with `client_tx_id` deduplication.

### Files
- **`App.js`**: Main React Native view with UI, status badge, and offline action buttons.
- **`db.js`**: Offline storage and queue manager.
- **`sync.js`**: Background sync loop and API sync client.
