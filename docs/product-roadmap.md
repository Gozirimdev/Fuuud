# FUUUD product roadmap

FUUUD is a healthcare access and navigation platform for patients, doctors, hospitals, and platform administrators. The FU Agent is one supporting feature; it is not the identity of the product.

Work is divided into complete, testable components. A component is complete only when its data model, API, permissions, interface, validation, tests, and user states are implemented.

## Delivery order

### 1. Accounts, roles, and access

- Patient, doctor, hospital staff, and administrator roles
- Registration, login, logout, password recovery, and contact verification
- Protected role-specific routes and dashboards
- Staff permissions and account status
- Audit trail for important account and clinical actions

### 2. Patient experience

- Patient profile and contact details
- Care preferences, consent, and privacy controls
- Saved providers and hospitals
- Appointment history, rescheduling, and cancellation
- Notifications and account management

### 3. Doctor onboarding and workspace

- Doctor registration and professional profile
- Licence and identity document submission
- Administrator verification workflow
- Availability and consultation-fee management
- Appointment queue, consultation status, and patient communication

### 4. Hospital directory and partnerships

- Public listings for hospitals that are not connected to FUUUD
- Location, directions, and verified public contact numbers
- Clear `listed`, `registered`, and `verified partner` states
- Hospital-managed information for registered hospitals
- Departments, services, opening hours, facilities, and affiliated doctors

FUUUD must never imply that an unregistered hospital has accepted a patient or confirmed availability.

### 5. Hospital onboarding and workspace

- Hospital registration and authority verification
- Hospital owner and staff accounts
- Staff roles and permissions
- Service, department, doctor, and facility management
- Appointment, referral, and incoming-patient operations

### 6. Appointments and consultations

- Doctor and hospital appointment types
- Real availability, booking, confirmation, rescheduling, and cancellation
- Protection against double booking
- Online and physical consultation workflows
- Appointment reminders and status history

### 7. Messaging and notifications

- Patient-to-doctor messaging
- Patient-to-registered-hospital messaging
- Attachments, delivery state, moderation, and retention rules
- Email, SMS, push, and in-app notifications
- Unregistered hospitals remain phone-and-directions only

### 8. Emergency access

- Nearby hospital discovery, including non-partners
- Direct call and navigation for every valid public listing
- Live emergency availability for registered hospitals only
- Incoming-patient alert, questions, location sharing, and estimated arrival
- Explicit consent, escalation, and emergency-service warnings

### 9. Prescriptions and pharmacies

- Clinician-issued prescriptions with audit history
- Patient prescription access
- Registered pharmacy directory and medicine enquiries
- Safety warnings and controlled access to health information

### 10. Payments and business operations

- Consultation pricing and payment collection
- Receipts, refunds, cancellations, and provider settlement
- Hospital and doctor plans or commissions
- Financial reporting and dispute handling

### 11. FU Agent and navigation assistance

- Help users find relevant platform services conversationally
- Use only information the user is permitted to access
- Hand off clinical decisions to qualified professionals
- Never present navigation support as diagnosis or emergency confirmation

### 12. Administration, safety, and launch

- Doctor and hospital verification console
- Reports, suspensions, support, and content management
- Security testing, privacy controls, backups, monitoring, and incident response
- Accessibility, performance, end-to-end, and load testing
- Controlled pilot before public availability

## Current position

The current application has a broad patient-facing prototype. Real backend support currently covers general user authentication, doctor discovery, availability, and patient appointment booking/cancellation. Doctor accounts, hospital accounts, administration, and most other workflows are still demonstrations.

## Active milestone

Component 1: accounts, roles, and access. The first implementation slice is the shared role model and protected role-specific entry points for patients, doctors, hospital staff, and administrators.
