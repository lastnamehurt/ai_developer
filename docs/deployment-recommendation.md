# Global Entry Notifier v2.0 – Design and Deployment Recommendation

## Provided Design Plan (verbatim)

### **Design Plan: Global Entry Notifier v2.0**

The goal is to transform the application from a single, monolithic process into a decoupled, event-driven system of microservices. This design prioritizes horizontal scalability, modularity for adding new sources and notification platforms, and overall performance and reliability.

#### **1. High-Level Architecture: An Event-Driven Microservices Model**

We will break the application into four distinct domains, communicating asynchronously via a central message queue (like RabbitMQ or AWS SQS).

**Proposed Architecture Diagram:**

```
                                 ┌──────────────────┐
                                 │   Scraper Svc    │   (e.g., TTP.gov)
                                 └──────────────────┘
                                          │
                                          ▼ (Raw Appointment Data)
                                 ┌──────────────────┐
                                 │  Message Broker  │   (RabbitMQ / SQS)
                                 └──────────────────┘
                                          │
                                          ▼ (New Appointment Event)
┌─────────────────┐              ┌──────────────────┐               ┌────────────────────┐
│ API & Web App   │◄─────────────┤ Appointment      │───────────────►│  Notification      │
│ (Django/Flask)  │ (User Prefs) │ Processor Svc    │(Notification Request) │  Dispatcher Svcs   │
└─────────────────┘              └──────────────────┘               └────────────────────┘
      ▲                                                                  │ │ │
      │                                    ┌───────────┴─┴───────────┐
      │                                    │           │             │
      │                             ┌────────┴─┐  ┌────────┴──┐  ┌────────┴──┐
      │                             │  SMS     │  │  Twitter  │  │  Discord  │
      └─────────────────────────────│ (Twilio) │  │ (X API)   │  │ (Webhook) │
           (User Signups)             └──────────┘  └───────────┘  └───────────┘
```

---

#### **2. Core Service Breakout**

**a. Scraper Services (The "Producers")**
*   **Responsibility:** Solely responsible for fetching appointment data from a single source. Each scraper is an independent, lightweight process.
*   **Implementation:** We can start by extracting the `interview_finder_service` logic into its own service. This service runs on a schedule (e.g., a cron job or a timed AWS Lambda).
*   **Modularity:** To add a new source (e.g., a different country's visa site), we simply build a new scraper service. It adheres to a standard data format and publishes to the same message queue, requiring no changes to the rest of the system.
*   **Output:** Publishes a standardized JSON message for every available slot found. Example:
    ```json
    {
      "source": "TTP_GOV",
      "location_id": 5446,
      "location_name": "San Francisco, CA",
      "appointment_ts": "2026-02-10T09:00:00Z",
      "scraped_at": "2025-12-04T15:30:00Z"
    }
    ```

**b. Appointment Processor Service (The "Brain")**
*   **Responsibility:** Consumes raw appointment data from the message queue, determines if it's a "new" or "changed" appointment, and identifies which subscribers need to be notified.
*   **Implementation:** This service maintains the state of appointments. It can use a combination of a fast in-memory database (like Redis) for recent slot data and the main PostgreSQL database for persistence.
*   **Logic:**
    1.  Consume a message from the "raw appointments" queue.
    2.  Check Redis/Postgres: "Have I seen this `location_id` with this `appointment_ts` before?"
    3.  If it's new/changed, update the `InterviewTimeSlot` model in the database.
    4.  Query the database for all active subscribers for this `location_id`.
    5.  For each subscriber, generate a *notification request* and publish it to a "notifications" topic on the message queue.
*   **Output:** A specific notification job. Example:
    ```json
    {
      "user_id": 123,
      "notification_channels": ["sms", "twitter"],
      "data": {
        "location_name": "San Francisco, CA",
        "appointment_pretty": "Tuesday, Feb. 10, 2026 @ 9:00 AM"
      }
    }
    ```

**c. Notification Dispatcher Services (The "Consumers")**
*   **Responsibility:** Each dispatcher is a small service that knows how to talk to exactly one platform (e.g., Twitter, Twilio, Discord, Slack).
*   **Implementation:** They subscribe to the "notifications" message topic. A `TwilioDispatcher` would handle jobs for the "sms" channel, a `TwitterDispatcher` for the "twitter" channel, and so on.
*   **Modularity:** This is the key to multi-platform support. To add Discord notifications, we create a new `DiscordDispatcher` service. It requires zero changes to the Scraper or Processor. This isolates API keys, formatting logic, and platform-specific error handling (like rate limits).

**d. API & Web Service (The "Frontend & User Management")**
*   **Responsibility:** Manages user accounts, preferences, and payments. This is where the Django app will be refactored to shine.
*   **Implementation:**
    *   Remove all the bot/polling logic from Django.
    *   Focus on providing a robust REST API for user management (`/api/v1/subscribers`, `/api/v1/preferences`).
    *   Continue to handle the user-facing web interface for signups, payments (Stripe), and a new user dashboard.
    *   The Appointment Processor will call this API if it needs to fetch detailed user preferences.

---

#### **3. Proposed New Features Enabled by this Architecture**

1.  **User Dashboard:** A page where users can see their notification history, preferred locations, active channels (SMS, email, etc.), and update their preferences in real-time.
2.  **Granular Notification Controls:** Users can choose to receive alerts on multiple platforms (e.g., "Send me an SMS and an email, but not a tweet"). This is managed in the `Subscriber` model's `preferences` JSON field and honored by the Processor service.
3.  **Real-Time Status Page:** The availability report can be updated in real-time via WebSockets. When the Processor confirms a new slot, it can also send an event to the Web App to instantly update the public availability page.
4.  **Support for Multiple Appointment Sources:** The system can be expanded to monitor TSA PreCheck, other Trusted Traveler Programs, or even visa appointments for different countries by simply adding new Scraper services.

---

#### **4. Phased Rollout & Migration Plan**

A big-bang rewrite is risky. We can migrate incrementally:

*   **Phase 1: Decouple the Notifiers.**
    1.  Create the `Notification Dispatcher` services (starting with SMS and Twitter).
    2.  Modify the existing `bot.py` loop. Instead of calling the Twilio/Tweepy APIs directly, have it publish a job to the message queue for the new dispatchers to consume.
    3.  *Result:* Notification logic is now isolated and independently scalable.

*   **Phase 2: Decouple the Scraper.**
    1.  Create the `Scraper Service` and have it publish to the message queue.
    2.  Create the new `Appointment Processor Service` to consume from the scrapers and produce notification requests.
    3.  Decommission the old `bot.py` polling loop entirely.
    4.  *Result:* The core processing logic is now a standalone, scalable service.

*   **Phase 3: Refactor the Web App & Add New Features.**
    1.  Clean up the Django application, removing all old bot code.
    2.  Build out the user dashboard and granular preference controls.
    3.  Start adding new dispatchers (e.g., Discord, Email) and scrapers as desired.

---

#### **5. Benefits of this Redesign**

*   **Scalability:** Each service can be scaled independently. If scraping is slow, we add more scraper instances. If we have millions of notifications to send, we scale up the dispatchers.
*   **Modularity & Maintainability:** Adding a new notification platform (e.g., Slack) or a new appointment source doesn't require touching the core logic. The team can work on different services in parallel.
*   **Performance:** By processing appointments and sending notifications asynchronously, the system can handle high volume without slowing down. The user-facing web app remains fast and responsive because it's not burdened with background processing.
*   **Reliability:** If the Twitter dispatcher fails, it doesn't stop SMS notifications. The message queue provides resiliency, allowing for retries and dead-letter queues for failed jobs, ensuring data isn't lost.

---

## Deployment Recommendation

### Primary choice: GKE Autopilot + Pub/Sub + Cloud SQL
- **Why:** Lowest ops burden with good autoscaling; managed queue avoids running RabbitMQ.
- **Cluster:** GKE Autopilot, zonal, tight quotas (≈2–3 vCPU, 3–4 GiB). HPAs on all services with min 0–1 replicas.
- **Messaging:** Google Pub/Sub for both raw appointments and notifications topics (push or pull).
- **Data:** Cloud SQL Postgres (shared-core f1/f2) for persistence; Memorystore Redis (small tier) for dedupe/cache.
- **Ingress:** GKE Ingress + cert-manager; single public IP.
- **Workloads:** Scrapers as CronJobs (or Cloud Scheduler → Pub/Sub); Appointment Processor and Dispatchers as Deployments consuming Pub/Sub; API/Web as Deployment with Cloud SQL Auth Proxy sidecar.
- **Cost levers:** Tight resource requests (e.g., 50–100m CPU / 128–256Mi RAM for workers), spot pods if acceptable, zonal cluster, minimal replicas, avoid heavy add-ons initially (start with metrics-server).

### Cheapest cash option: k3s on a single VPS + SQS/RDS
- **Why:** Lowest fixed monthly cost, more DIY ops.
- **Cluster:** k3s on a $10–$15/mo VPS (ARM if possible). nginx or Traefik ingress + cert-manager; Cloudflare DNS/TLS if desired.
- **Messaging:** AWS SQS for queues (managed and cheap).
- **Data:** RDS Postgres t4g.micro/small; Elasticache Redis t4g.micro (or self-host Redis if you must).
- **Workloads:** Same split—Scrapers as CronJobs, Processor/Dispatchers/API as Deployments; single ingress/LB.
- **Cost levers:** Run small pods, scale-to-0 where viable, use spot/preemptible for worker nodes if multi-node later, standard (non-premium) storage classes.

### Quick guidance
- Prefer **GKE Autopilot + Pub/Sub + Cloud SQL** unless every dollar matters. Pick **k3s + SQS/RDS** if you want lowest spend and can accept more ops. I can add concrete manifests and sizing once you confirm the target cloud and expected traffic. 
