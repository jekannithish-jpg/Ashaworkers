# Security, Data Privacy & Regulatory Compliance (DPDP Act 2023 & Indian Health Standards)

## 1. Compliance Framework

This prototype adheres to the principles of:
1. **Digital Personal Data Protection (DPDP) Act, 2023 (India)**.
2. **MoHFW Electronic Health Record (EHR) Standards for India (2016)**.
3. **National Digital Health Blueprint (NDHB) & ABDM Data Protection Guidelines**.

## 2. Core Security Controls

### A. Role-Based Access Control (RBAC) & Principle of Least Privilege
- Every incoming request passes through server-side authorization dependency checks (`require_role([...])`).
- UI button concealment is **never** relied upon as security. Endpoints independently verify permissions against the authenticated user claims.
- System Administrators have operational administration access (user lifecycle, audit logs, system parameters) but are restricted from arbitrary clinical chart browsing.

### B. Authentication & Token Management
- Passwords are encrypted using salted `bcrypt` hashes with a work factor of 12.
- Session tokens are cryptographic HMAC-SHA256 signed bearer tokens with configurable expiration (default: 8 hours for field workers, 4 hours for supervisors).
- Automatic session invalidation upon password reset or role revocation.

### C. Offline Data Protection & Encryption
- In the mobile client, records are stored in browser/device sandboxed storage (IndexedDB).
- Sensitive records are wrapped with client-side AES-GCM encryption key derived from user login credentials.
- Automatic local store clearing upon explicit user logout.

### D. Tamper-Evident Audit Logging
- Every sensitive operation (login, record creation, clinical edit, high-risk flag, emergency referral, data export) is permanently appended to the `audit_logs` table.
- Logs include: `timestamp`, `user_id`, `role`, `action`, `target_entity`, `target_id`, `ip_address`, and `details`.
- Logs cannot be deleted or modified through the API.

### E. Synthetic Data Guarantee
- The application is distributed exclusively with synthetic demonstration datasets (`BEN-2026-0001` through `BEN-2026-0010`).
- No genuine patient identification, Aadhaar numbers, real telephone numbers, or live hospital records are included.

