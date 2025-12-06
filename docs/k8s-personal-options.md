# Kubernetes Options for Low-Cost Personal Projects

## Always-On, Cheapest
- **k3s on a single VPS** (e.g., $5–10/mo). Good for one/few services, low traffic.
- Use Traefik (default) or nginx ingress + cert-manager; metrics-server for autoscaling signals.
- Backups: enable embedded etcd and snapshot; snapshot PVCs if storage supports it.
- Single public IP; Cloudflare DNS + ACME HTTP-01 or DNS-01 for TLS.

## Cloud-Managed, Low-Touch
- **GKE Autopilot** with tight quotas (1–2 vCPU, low RAM), zonal to save. Idle costs scale with pod requests.
- **AKS** with a single low-cost/spot node pool (B-series/DASv5). EKS is usually pricier at tiny scale (control-plane fee + nodes).
- Deploy ingress-nginx or cloud ingress; cert-manager for TLS. Set min replicas small; use HPAs.

## Cost Levers
- Spot/preemptible nodes for non-critical workloads.
- Pack pods tightly: small images (alpine/distroless), set requests/limits carefully.
- Autoscale: HPA with conservative mins; consider Knative/KSv2 for HTTP scale-to-zero.
- Use one ingress + cert-manager behind a single LB; avoid per-service load balancers.
- Disable heavy add-ons (full service mesh/Prometheus stacks) until needed; start with metrics-server.
- Storage: prefer standard/HDD over premium SSD unless required; clean up PVCs/images regularly.

## Simple Recipes
- **k3s on VPS**: install k3s, optionally swap to nginx ingress, add cert-manager, deploy app + HPA. One LB/IP on the VPS.
- **GKE Autopilot**: create Autopilot cluster, deploy ingress (nginx or GKE), cert-manager, app with limits/HPA. Keep regionality zonal; minimal pods.

## Quick Guidance
- If you want the lowest bill and can manage a box: choose k3s on a small VPS.
- If you want cloud experience with low ops: choose GKE Autopilot with tight resource requests.
