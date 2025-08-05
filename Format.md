I need you to create complete project specifications for the GA4 Admin Automation System - a full-stack application for managing Google Analytics 4 permissions.

APP DESCRIPTION:
A comprehensive web-based system that automates GA4 permission management for service partners managing multiple client accounts. The system handles permission requests, approvals, extensions, and expiration with role-based access control (RBAC), real-time notifications, and complete audit trails.

TECH STACK PREFERENCES:
- Frontend: Next.js 14 (App Router), TypeScript, Shadcn UI, Tailwind CSS, Lucide React
- Backend: FastAPI (Python 3.11+), SQLAlchemy 2.0, PostgreSQL, JWT Authentication
- Infrastructure: Docker, Kubernetes, GitHub Actions CI/CD, Nginx, Redis
- Google Integration: Google Analytics Admin API
- Monitoring: Prometheus + Grafana + Loki
- Testing: Pytest (backend), Vitest/Jest (frontend), Playwright (E2E)

INCLUDE THESE FEATURES:
- User Authentication & Authorization (JWT-based with refresh tokens)
- Role-Based Access Control (Super Admin, Admin, Requester, GA User)
- GA4 Permission Management (request, approve, reject, revoke, extend)
- Email Notification System (SMTP-based alerts and summaries)
- Audit Logging System (comprehensive activity tracking)
- Real-time Dashboard with Metrics and Analytics
- Service Account Management
- Client Organization Management
- Automated Permission Expiration Handling
- Multi-tenant Architecture Support
- API Rate Limiting and Security

EXCLUDE THESE FEATURES:
- Mobile native apps (focus on responsive web)
- Offline mode functionality
- Third-party analytics integration (other than GA4)
- Social media login (only email/password auth)

UI REFERENCE:
The current implementation uses Shadcn UI components with a dark theme option. Maintain consistency with the existing design system and component library.

Please create these specification files:

CORE SPECS (Required):
1. main-spec.md - Overall project blueprint with phases and git rules
2. frontend-spec.md - Detailed frontend implementation with tmux agent assignments
3. backend-spec.md - API specification with agent responsibilities
4. integration-spec.md - How frontend and backend connect
5. testing-qa-spec.md - Comprehensive testing and QA procedures

FEATURE SPECS (Create separate files for each):
- auth-spec.md - Authentication and authorization system
- rbac-spec.md - Role-based access control implementation
- ga4-integration-spec.md - Google Analytics Admin API integration
- notifications-spec.md - Email notification system
- audit-spec.md - Audit logging and activity tracking
- dashboard-spec.md - Real-time dashboard and analytics
- client-management-spec.md - Multi-tenant client organization management
- service-accounts-spec.md - Service account handling

TMUX AGENT TEAM SPECS:
- agent-orchestration-spec.md - How tmux agents will be organized and coordinated
- agent-assignments-spec.md - Specific agent roles and responsibilities
- agent-communication-spec.md - Inter-agent communication protocols
- qa-automation-spec.md - Automated QA processes for agent development

Each feature spec should include:
- Overview of the feature
- Frontend components needed
- Backend endpoints required
- Database models
- Integration points with main app
- Testing requirements
- Implementation phases
- Agent responsibilities (which agent handles what)
- Common error patterns and solutions

Make sure ALL specs include:
- Clear phases with time estimates
- Git commit reminders every 30 minutes
- Specific implementation details
- Success criteria for each phase
- Dependencies on other specs
- Agent team assignments for tmux orchestration
- QA checkpoints and validation steps

Format everything in markdown, ready to be saved as separate files. List all the spec files I should create at the end.