// API Service & Sync Dispatcher
const API = {
  baseUrl: '',

  getToken: function() {
    return localStorage.getItem('asha_auth_token') || '';
  },

  setToken: function(token) {
    localStorage.setItem('asha_auth_token', token);
  },

  getHeaders: function() {
    const headers = { 'Content-Type': 'application/json' };
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  },

  request: async function(endpoint, options = {}) {
    // If user has toggled simulated offline mode, reject immediately so offline fallback engages!
    if (window.AppState && window.AppState.isOfflineSimulated && !options.forceOnline) {
      throw new Error("NETWORK_OFFLINE_SIMULATED");
    }

    options.headers = Object.assign({}, this.getHeaders(), options.headers);
    try {
      const res = await fetch(endpoint, options);
      if (res.status === 401) {
        console.warn("Session expired or unauthorized");
      }
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText || `HTTP Error ${res.status}`);
      }
      return await res.json();
    } catch(err) {
      throw err;
    }
  },

  // Auth
  login: async function(username, password) {
    const data = await this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
      forceOnline: true
    });
    this.setToken(data.access_token);
    return data;
  },

  mobileLogin: async function(phoneNumber, pin = null, otp = null) {
    const body = { phone_number: phoneNumber };
    if (pin) body.pin = pin;
    if (otp) body.otp = otp;

    const data = await this.request('/api/auth/mobile-login', {
      method: 'POST',
      body: JSON.stringify(body),
      forceOnline: true
    });
    this.setToken(data.access_token);
    return data;
  },

  sendOtp: async function(phoneNumber) {
    return await this.request('/api/auth/send-otp', {
      method: 'POST',
      body: JSON.stringify({ phone_number: phoneNumber }),
      forceOnline: true
    });
  },

  setPin: async function(phoneNumber, newPin) {
    return await this.request('/api/auth/set-pin', {
      method: 'POST',
      body: JSON.stringify({ phone_number: phoneNumber, new_pin: newPin }),
      forceOnline: true
    });
  },

  // Beneficiaries
  getBeneficiaries: async function(params = {}) {
    const qs = new URLSearchParams(params).toString();
    try {
      const data = await this.request(`/api/beneficiaries?${qs}`);
      localStorage.setItem('asha_cache_beneficiary', JSON.stringify(data));
      return data;
    } catch(e) {
      console.log("Serving beneficiaries from local offline cache");
      return LocalDB.getLocalEntities('beneficiary');
    }
  },

  getBeneficiaryDetails: async function(id) {
    try {
      return await this.request(`/api/beneficiaries/${id}`);
    } catch(e) {
      const local = LocalDB.getLocalEntities('beneficiary').find(b => b.beneficiary_id === id);
      if (local) {
        return { beneficiary: local, active_pregnancy: { beneficiary_id: id, status: 'ACTIVE', high_risk_flag: false } };
      }
      throw e;
    }
  },

  registerBeneficiary: async function(benData) {
    if (window.AppState && window.AppState.isOfflineSimulated) {
      benData.beneficiary_id = benData.beneficiary_id || `BEN-${new Date().getFullYear()}-OFF-${Math.random().toString(36).substring(2,6).toUpperCase()}`;
      LocalDB.enqueue('beneficiary', 'CREATE', benData);
      return {
        message: "Beneficiary registered offline. Enqueued for server synchronization.",
        beneficiary: benData,
        pregnancy: { beneficiary_id: benData.beneficiary_id, edd_date: benData.edd_date, status: 'ACTIVE' },
        is_offline_saved: true
      };
    }

    try {
      return await this.request('/api/beneficiaries', {
        method: 'POST',
        body: JSON.stringify(benData)
      });
    } catch(e) {
      LocalDB.enqueue('beneficiary', 'CREATE', benData);
      return {
        message: "Network unavailable. Saved locally to sync queue.",
        beneficiary: benData,
        is_offline_saved: true
      };
    }
  },

  // ANC
  getANCDueList: async function(status = '') {
    try {
      const data = await this.request(`/api/anc/due-list?status_filter=${status}`);
      localStorage.setItem('asha_cache_anc_visit', JSON.stringify(data));
      return data;
    } catch(e) {
      return LocalDB.getLocalEntities('anc_visit');
    }
  },

  recordANCVisit: async function(visitData) {
    if (window.AppState && window.AppState.isOfflineSimulated) {
      visitData.visit_uuid = visitData.visit_uuid || `ANC-OFF-${Date.now()}`;
      LocalDB.enqueue('anc_visit', 'CREATE', visitData);
      return { message: "ANC visit recorded offline. Queued for sync.", visit: visitData, is_offline_saved: true };
    }
    try {
      return await this.request('/api/anc/record-visit', {
        method: 'POST',
        body: JSON.stringify(visitData)
      });
    } catch(e) {
      LocalDB.enqueue('anc_visit', 'CREATE', visitData);
      return { message: "Network error. Recorded in local offline queue.", visit: visitData, is_offline_saved: true };
    }
  },

  // Electronic Health Records (EHR)
  getEHR: async function(beneficiaryId) {
    try {
      const data = await this.request(`/api/ehr/${beneficiaryId}`);
      localStorage.setItem(`asha_ehr_${beneficiaryId}`, JSON.stringify(data));
      return data;
    } catch(e) {
      const cached = localStorage.getItem(`asha_ehr_${beneficiaryId}`);
      if (cached) return JSON.parse(cached);
      return {
        beneficiary_id: beneficiaryId,
        history: LocalDB.getLocalEntities('ehr_history').find(h => h.beneficiary_id === beneficiaryId) || null,
        diagnoses: LocalDB.getLocalEntities('ehr_diagnosis').filter(d => d.beneficiary_id === beneficiaryId),
        medicines: LocalDB.getLocalEntities('ehr_medicine').filter(m => m.beneficiary_id === beneficiaryId),
        lab_reports: LocalDB.getLocalEntities('ehr_lab_report').filter(l => l.beneficiary_id === beneficiaryId)
      };
    }
  },

  updateMedicalHistory: async function(historyData) {
    if (window.AppState && window.AppState.isOfflineSimulated) {
      LocalDB.enqueue('ehr_history', 'UPDATE', historyData);
      return { status: "SUCCESS", message: "Medical history saved locally (offline).", history: historyData, is_offline_saved: true };
    }
    try {
      return await this.request('/api/ehr/history', {
        method: 'POST',
        body: JSON.stringify(historyData)
      });
    } catch(e) {
      LocalDB.enqueue('ehr_history', 'UPDATE', historyData);
      return { status: "SUCCESS", message: "Saved to local offline queue.", history: historyData, is_offline_saved: true };
    }
  },

  addDiagnosis: async function(diagnosisData) {
    diagnosisData.diagnosis_uuid = diagnosisData.diagnosis_uuid || `DX-OFF-${Date.now()}`;
    if (window.AppState && window.AppState.isOfflineSimulated) {
      LocalDB.enqueue('ehr_diagnosis', 'CREATE', diagnosisData);
      return { status: "SUCCESS", message: "Diagnosis saved offline.", diagnosis: diagnosisData, is_offline_saved: true };
    }
    try {
      return await this.request('/api/ehr/diagnosis', {
        method: 'POST',
        body: JSON.stringify(diagnosisData)
      });
    } catch(e) {
      LocalDB.enqueue('ehr_diagnosis', 'CREATE', diagnosisData);
      return { status: "SUCCESS", message: "Saved locally.", diagnosis: diagnosisData, is_offline_saved: true };
    }
  },

  addMedicine: async function(medicineData) {
    medicineData.medicine_uuid = medicineData.medicine_uuid || `RX-OFF-${Date.now()}`;
    if (window.AppState && window.AppState.isOfflineSimulated) {
      LocalDB.enqueue('ehr_medicine', 'CREATE', medicineData);
      return { status: "SUCCESS", message: "Medicine dispensation saved offline.", medicine: medicineData, is_offline_saved: true };
    }
    try {
      return await this.request('/api/ehr/medicine', {
        method: 'POST',
        body: JSON.stringify(medicineData)
      });
    } catch(e) {
      LocalDB.enqueue('ehr_medicine', 'CREATE', medicineData);
      return { status: "SUCCESS", message: "Saved locally.", medicine: medicineData, is_offline_saved: true };
    }
  },

  addLabReport: async function(labData) {
    labData.report_uuid = labData.report_uuid || `LAB-OFF-${Date.now()}`;
    if (window.AppState && window.AppState.isOfflineSimulated) {
      LocalDB.enqueue('ehr_lab_report', 'CREATE', labData);
      return { status: "SUCCESS", message: "Lab report saved offline.", lab_report: labData, is_offline_saved: true };
    }
    try {
      return await this.request('/api/ehr/lab-report', {
        method: 'POST',
        body: JSON.stringify(labData)
      });
    } catch(e) {
      LocalDB.enqueue('ehr_lab_report', 'CREATE', labData);
      return { status: "SUCCESS", message: "Saved locally.", lab_report: labData, is_offline_saved: true };
    }
  },

  // Children & Immunizations
  getChildren: async function(params = {}) {
    const qs = new URLSearchParams(params).toString();
    try {
      const data = await this.request(`/api/children?${qs}`);
      localStorage.setItem('asha_cache_child', JSON.stringify(data));
      return data;
    } catch(e) {
      return LocalDB.getLocalEntities('child');
    }
  },

  getChildProfile: async function(childId) {
    try {
      return await this.request(`/api/children/${childId}`);
    } catch(e) {
      const c = LocalDB.getLocalEntities('child').find(ch => ch.child_id === childId) || { child_id: childId, child_name: "Child" };
      return {
        child: c,
        immunizations: LocalDB.getLocalEntities('child_immunization').filter(i => i.child_id === childId),
        growth_history: LocalDB.getLocalEntities('child_growth').filter(g => g.child_id === childId)
      };
    }
  },

  registerChild: async function(childData) {
    childData.child_id = childData.child_id || `CHD-OFF-${Date.now()}`;
    if (window.AppState && window.AppState.isOfflineSimulated) {
      LocalDB.enqueue('child', 'CREATE', childData);
      return { status: "SUCCESS", message: "Child registered locally in offline mode.", child: childData, is_offline_saved: true };
    }
    try {
      return await this.request('/api/children', {
        method: 'POST',
        body: JSON.stringify(childData)
      });
    } catch(e) {
      LocalDB.enqueue('child', 'CREATE', childData);
      return { status: "SUCCESS", message: "Saved locally.", child: childData, is_offline_saved: true };
    }
  },

  recordImmunization: async function(immData) {
    immData.record_uuid = immData.record_uuid || `IMM-${immData.child_id}-${immData.vaccine_code}`;
    if (window.AppState && window.AppState.isOfflineSimulated) {
      LocalDB.enqueue('child_immunization', 'UPDATE', immData);
      return { status: "SUCCESS", message: "Vaccination recorded offline.", immunization: immData, is_offline_saved: true };
    }
    try {
      return await this.request('/api/children/immunize', {
        method: 'POST',
        body: JSON.stringify(immData)
      });
    } catch(e) {
      LocalDB.enqueue('child_immunization', 'UPDATE', immData);
      return { status: "SUCCESS", message: "Vaccination recorded locally.", immunization: immData, is_offline_saved: true };
    }
  },

  recordGrowth: async function(growthData) {
    growthData.growth_uuid = growthData.growth_uuid || `GRW-OFF-${Date.now()}`;
    if (window.AppState && window.AppState.isOfflineSimulated) {
      LocalDB.enqueue('child_growth', 'CREATE', growthData);
      return { status: "SUCCESS", message: "Growth entry saved offline.", growth: growthData, is_offline_saved: true };
    }
    try {
      return await this.request('/api/children/growth', {
        method: 'POST',
        body: JSON.stringify(growthData)
      });
    } catch(e) {
      LocalDB.enqueue('child_growth', 'CREATE', growthData);
      return { status: "SUCCESS", message: "Saved locally.", growth: growthData, is_offline_saved: true };
    }
  },

  // Home Visits & Surveys (with GPS)
  recordHomeVisit: async function(visitData) {
    if (window.AppState && window.AppState.isOfflineSimulated) {
      visitData.visit_uuid = visitData.visit_uuid || `HV-OFF-${Date.now()}`;
      LocalDB.enqueue('home_visit', 'CREATE', visitData);
      return { message: "Home visit saved locally with GPS.", home_visit: visitData, is_offline_saved: true };
    }
    try {
      return await this.request('/api/home-visits', {
        method: 'POST',
        body: JSON.stringify(visitData)
      });
    } catch(e) {
      LocalDB.enqueue('home_visit', 'CREATE', visitData);
      return { message: "Network unavailable. Saved to local queue.", home_visit: visitData, is_offline_saved: true };
    }
  },

  // High-Risk & Referrals
  getHighRiskCases: async function() {
    return await this.request('/api/high-risk');
  },

  getDangerSigns: async function() {
    return await this.request('/api/referrals/danger-signs');
  },

  getFacilities: async function() {
    return await this.request('/api/referrals/facilities');
  },

  getEmergencyInfo: async function() {
    try {
      return await this.request('/api/referrals/emergency-info');
    } catch(e) {
      return {
        emergency_contacts: [
          { name: "108 Emergency Ambulance", number: "108", type: "Ambulance", is_toll_free: true },
          { name: "102 Janani Shishu Suraksha", number: "102", type: "Maternal Transport", is_toll_free: true },
          { name: "104 Health Helpline", number: "104", type: "Medical Advice", is_toll_free: true },
        ],
        facilities: [
          { id: 1, facility_name: "Vadipatti PHC", facility_type: "PHC", emergency_phone_1: "0452-240101", district: "Madurai", block: "Vadipatti" },
          { id: 2, facility_name: "Alanganallur CHC & FRU", facility_type: "FRU", emergency_phone_1: "0452-240202", district: "Madurai", block: "Vadipatti" }
        ]
      };
    }
  },

  initiateReferral: async function(refData) {
    if (window.AppState && window.AppState.isOfflineSimulated) {
      refData.referral_uuid = refData.referral_uuid || `REF-OFF-${Date.now()}`;
      const bookingCode = `EMG-${new Date().getFullYear()}-${Math.random().toString(36).substring(2,6).toUpperCase()}`;
      LocalDB.enqueue('referral', 'CREATE', refData);
      return {
        message: "Referral logged in local emergency register.",
        emergency_booking_code: bookingCode,
        sms_notification_text: `🚨 108 EMERGENCY ALERT\nCode: ${bookingCode}\nPatient: ${refData.beneficiary_id}\nDanger Sign: ${refData.danger_sign_code || 'Critical Obstetric Complication'}\nAction: Dispatch Ambulance Immediately`,
        emergency_instruction: "Immediately arrange 108 Emergency Ambulance. Place mother on left lateral side.",
        referral: refData,
        is_offline_saved: true
      };
    }
    return await this.request('/api/referrals/initiate', {
      method: 'POST',
      body: JSON.stringify(refData)
    });
  },

  dispatchReferralSMS: async function(referralUuid) {
    return await this.request(`/api/referrals/${referralUuid}/send-sms`, {
      method: 'POST'
    });
  },

  // Postnatal Care
  getPNCDueList: async function() {
    return await this.request('/api/pnc/due-list');
  },

  recordPNCVisit: async function(pncData) {
    if (window.AppState && window.AppState.isOfflineSimulated) {
      pncData.pnc_uuid = pncData.pnc_uuid || `PNC-OFF-${Date.now()}`;
      LocalDB.enqueue('pnc_visit', 'CREATE', pncData);
      return { message: "PNC visit saved offline.", visit: pncData, is_offline_saved: true };
    }
    return await this.request('/api/pnc/record-visit', {
      method: 'POST',
      body: JSON.stringify(pncData)
    });
  },

  // Supervisor KPIs with Timeframe (Daily, Weekly, Monthly)
  getSupervisorKPIs: async function(village = '', timeFrame = 'monthly') {
    return await this.request(`/api/supervisor/dashboard-kpis?village=${village}&time_frame=${timeFrame}`);
  },

  exportReport: async function(timeFrame = 'monthly') {
    return await this.request(`/api/supervisor/export-report?time_frame=${timeFrame}`);
  },

  getAuditLogs: async function() {
    return await this.request('/api/supervisor/audit-logs');
  },

  // RAG Assistant
  askAssistant: async function(query) {
    return await this.request('/api/assistant/query', {
      method: 'POST',
      body: JSON.stringify({ query })
    });
  },

  // Sync Push Engine
  syncNow: async function() {
    const queue = LocalDB.getQueue();
    if (queue.length === 0) {
      return { message: "Sync queue is empty. All records are up to date." };
    }

    const payload = { items: queue };
    const res = await this.request('/api/sync/push', {
      method: 'POST',
      body: JSON.stringify(payload),
      forceOnline: true
    });

    if (res.acknowledged_ids && res.acknowledged_ids.length > 0) {
      let currentQ = LocalDB.getQueue();
      currentQ = currentQ.filter(i => !res.acknowledged_ids.includes(i.client_tx_id));
      LocalDB.saveQueue(currentQ);
    }

    return res;
  },

  // Government Portal Integration Test (JANANI / ANMOL)
  testGovSync: async function(benId) {
    return await this.request(`/api/sync/government/test?beneficiary_id=${benId}`, {
      method: 'POST',
      forceOnline: true
    });
  }
};
