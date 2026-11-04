// Local Offline Database & Sync Queue Manager
const LocalDB = {
  getQueue: function() {
    try {
      const q = localStorage.getItem('asha_sync_queue');
      return q ? JSON.parse(q) : [];
    } catch(e) {
      return [];
    }
  },

  saveQueue: function(queue) {
    localStorage.setItem('asha_sync_queue', JSON.stringify(queue));
    this.updateBadge();
  },

  enqueue: function(entityType, operation, payload, clientVersion = 1) {
    const queue = this.getQueue();
    const txId = 'TX-' + Date.now() + '-' + Math.random().toString(36).substring(2, 7).toUpperCase();
    const item = {
      client_tx_id: txId,
      entity_type: entityType,
      operation: operation,
      client_version: clientVersion,
      payload: payload,
      enqueued_at: new Date().toISOString()
    };
    queue.push(item);
    this.saveQueue(queue);

    // Also persist into local cache for immediate offline viewing
    this.saveLocalEntity(entityType, payload);
    return txId;
  },

  saveLocalEntity: function(entityType, payload) {
    try {
      const key = `asha_cache_${entityType}`;
      const cache = JSON.parse(localStorage.getItem(key) || '[]');
      // Deduplicate by ID
      const idKey = entityType === 'beneficiary' ? 'beneficiary_id' :
                    entityType === 'anc_visit' ? 'visit_uuid' :
                    entityType === 'home_visit' ? 'visit_uuid' :
                    entityType === 'referral' ? 'referral_uuid' :
                    entityType === 'child' ? 'child_id' :
                    entityType === 'child_immunization' ? 'record_uuid' :
                    entityType === 'child_growth' ? 'growth_uuid' :
                    entityType === 'ehr_diagnosis' ? 'diagnosis_uuid' :
                    entityType === 'ehr_medicine' ? 'medicine_uuid' :
                    entityType === 'ehr_lab_report' ? 'report_uuid' :
                    entityType === 'ehr_history' ? 'beneficiary_id' : 'id';
      
      const idx = cache.findIndex(i => i[idKey] && i[idKey] === payload[idKey]);
      if (idx >= 0) {
        cache[idx] = Object.assign({}, cache[idx], payload);
      } else {
        cache.unshift(payload);
      }
      localStorage.setItem(key, JSON.stringify(cache));
    } catch(e) {
      console.warn("Local cache save error", e);
    }
  },

  getLocalEntities: function(entityType) {
    try {
      return JSON.parse(localStorage.getItem(`asha_cache_${entityType}`) || '[]');
    } catch(e) {
      return [];
    }
  },

  updateBadge: function() {
    const count = this.getQueue().length;
    const badge = document.getElementById('sync-badge-count');
    if (badge) {
      badge.textContent = count;
      badge.style.display = count > 0 ? 'inline-block' : 'none';
    }
    const indicator = document.getElementById('header-sync-status');
    if (indicator) {
      if (window.AppState && window.AppState.isOfflineSimulated) {
        indicator.className = 'status-pill status-offline';
        indicator.innerHTML = `⚠️ ${window.t('sync_offline')} (${count} pending)`;
      } else if (count > 0) {
        indicator.className = 'status-pill status-waiting';
        indicator.innerHTML = `⏳ ${window.t('sync_saved_locally')} (${count})`;
      } else {
        indicator.className = 'status-pill status-online';
        indicator.innerHTML = `✓ ${window.t('sync_online')}`;
      }
    }
  },

  clearQueueItem: function(txId) {
    const queue = this.getQueue().filter(i => i.client_tx_id !== txId);
    this.saveQueue(queue);
  }
};

