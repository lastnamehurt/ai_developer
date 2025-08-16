# Break Glass Hotfix Strategy: 15-Minute Production Deployment

## 🚨 Quick Emergency Decision Tree

```
PRODUCTION EMERGENCY - What's the situation?

├─ 🔴 APP IS DOWN/BROKEN
│   ├─ Bad deployment just happened?
│   │   └─ → [Helm Rollback](#helm-rollback-2-5-minutes) (2-5 min)
│   ├─ Container/image issue?
│   │   └─ → [Container Image Rollback](#container-image-rollback) (2-3 min)  
│   └─ Database migration broke it?
│       └─ → [DB Migration Rollback](#database-migration-rollback) (5-10 min)
│
├─ 🟡 APP WORKING BUT HAS BUGS
│   ├─ Need to undo specific commits?
│   │   └─ → [Git Revert Strategy](#git-revert-strategy) (5-15 min) **Add [HOTFIX] to MR title!**
│   └─ Need new fix deployed fast?
│       └─ → [Emergency Forward Deploy](#emergency-forward-deploy) (15 min)
│
└─ 🟢 NEED PREVENTIVE HOTFIX
    └─ → [Emergency Forward Deploy](#emergency-forward-deploy) (15 min)
```

## 📋 Table of Contents

### 🚨 Emergency Procedures (Start Here)
- [Quick Emergency Decision Tree](#-quick-emergency-decision-tree)
- [Emergency Forward Deploy](#emergency-forward-deploy)
- [Emergency Rollback Procedures](#emergency-rollback-procedures)
  - [Helm Rollback (2-5 minutes)](#helm-rollback-2-5-minutes) - **Fastest**
  - [Git Revert Strategy](#git-revert-strategy) - **Most Complete**
  - [Database Migration Rollback](#database-migration-rollback) - **For Schema Issues**
  - [Container Image Rollback](#container-image-rollback) - **For Image Issues**
  - [Nuclear Option: Manual kubectl](#nuclear-option-manual-kubectl-rollback) - **Pipeline Failure**

### 📖 Reference & Implementation
- [Current State Analysis](#current-state-analysis)
- [Recommended Break Glass Strategies](#recommended-break-glass-strategies)
- [Implementation Timeline](#implementation-recommendations)
- [Security & Compliance](#security--compliance-considerations)
- [Testing Strategy](#testing-strategy)
- [Emergency Contacts](#emergency-contacts)

---

## Executive Summary

This document outlines strategies to implement a "break glass" emergency hotfix system that can bypass normal pipeline stages to achieve production deployment within 15 minutes during critical incidents. The current pipeline has extensive safety mechanisms but lacks emergency bypass capabilities.

## Current State Analysis

### Pipeline Structure
Your current `.gitlab-ci.yml` has a comprehensive 9-stage pipeline:
1. **build** - Docker image creation (~5-10 mins)
2. **test_setup** - E2E tag generation, knapsack reports
3. **static_analysis** - Code quality, linting, security scans (~10-15 mins)
4. **test** - Unit tests with 80 parallel jobs (~15-25 mins)
5. **upload_configuration** - Cloudflare worker config
6. **deploy_sandbox** - Sandbox deployment + verification (~10-15 mins)  
7. **verify_sandbox** - E2E testing (~15-30 mins)
8. **deploy_staging** - Staging deployment (~10-15 mins)
9. **deploy_production** - Production deployment (~10-15 mins)

**Total Normal Pipeline Time: 75-125 minutes**

### Current Emergency Capabilities
- Manual deployment jobs exist but still require full pipeline completion
- Resource groups prevent concurrent deployments to same environment
- Protected environments with approval requirements
- Container image artifacts are preserved for rollbacks

## Recommended Break Glass Strategies

### Strategy 1: Emergency Pipeline Branch (Recommended)

Create a dedicated emergency pipeline that bypasses non-critical stages:

```yaml
# Add to existing .gitlab-ci.yml
.emergency-rules: &emergency-rules
  rules:
    - if: '$EMERGENCY_HOTFIX == "true"'
      when: on_success
    - when: never

emergency_build:
  <<: *emergency-rules
  stage: build
  extends: .build_image
  variables:
    TARGETS: runtime
  needs: []
  timeout: 10 minutes

emergency_critical_tests:
  <<: *emergency-rules
  stage: test
  image: ${CI_BASE_IMAGE}:${CI_BASE_TAG}
  script:
    - cd /app
    - bundle exec rspec spec/critical_path_spec.rb --fail-fast
  needs: [emergency_build]
  timeout: 5 minutes
  parallel: 1

emergency_deploy_production:
  <<: *emergency-rules
  stage: deploy_production
  extends: .deploy_production_us
  variables:
    OVERRIDE_FILES: "-f platform/values.yaml -f production_us.yaml -f platform/production_us.yaml"
    OVERRIDE_SETS: "--set microservice.podDefaults.image=$RUNTIME_IMAGE"
    HELM_ADDITIONAL_FLAGS: "--timeout 10m0s"
  when: manual
  allow_failure: false
  needs: [emergency_critical_tests]
  environment:
    name: production
    url: https://production.checkrhq.net
```

**Activation**: Set `EMERGENCY_HOTFIX=true` when manually triggering pipeline

**Timeline**: ~15 minutes (5m build + 5m critical tests + 5m deploy)

### Strategy 2: Variable-Based Stage Bypass

Implement conditional stage execution based on emergency variables:

```yaml
# Add emergency variables
variables:
  EMERGENCY_HOTFIX:
    description: "Set to 'true' to enable emergency hotfix mode"
    value: "false"
  SKIP_NON_CRITICAL:
    description: "Set to 'true' to skip non-critical stages"
    value: "false"

# Modify existing jobs
unit_tests:
  <<: *only-mr-and-master
  <<: *base_unit_tests
  stage: test
  rules:
    - if: $EMERGENCY_HOTFIX == "true"
      when: never
    - if: $CI_MERGE_REQUEST_IID
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

verify_sandbox_behavior:
  rules:
    - if: $EMERGENCY_HOTFIX == "true"
      when: never
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### Strategy 3: Helm-Based Direct Deployment

Create scripts for direct Kubernetes deployment bypassing GitLab entirely:

```bash
#!/bin/bash
# emergency_deploy.sh
set -euo pipefail

EMERGENCY_IMAGE=${1:-"latest"}
ENVIRONMENT=${2:-"production_us"}

# Validate image exists
docker pull $EMERGENCY_IMAGE

# Deploy with minimal validation
helm upgrade checkr-console ./helm-chart \
  --namespace production \
  --set image.repository=$EMERGENCY_IMAGE \
  --set emergency_deploy=true \
  --timeout 5m \
  --wait

# Verify deployment
kubectl rollout status deployment/checkr-console -n production --timeout=300s
```

### Strategy 4: Emergency Revert/Rollback System

**Critical Issue: Your current pipeline has NO rollback capabilities!**

The current `.gitlab-ci.yml` only moves forward - there are no revert jobs or rollback mechanisms. Here are multiple revert strategies:

#### 4a. Helm-Based Rollback (Fastest - 2-5 minutes)

```yaml
# Add to .gitlab-ci.yml
emergency_rollback_production_us:
  stage: deploy_production
  extends: .deploy_production_us
  script:
    - echo "Rolling back production to version $ROLLBACK_VERSION"
    - helm history checkr-console --namespace production
    - helm rollback checkr-console $ROLLBACK_VERSION --namespace production --wait --timeout=5m
    - kubectl rollout status deployment/checkr-console -n production --timeout=300s
  variables:
    ROLLBACK_VERSION:
      description: "Helm release version to rollback to (0 = previous, 1 = before that, etc.)"
      value: "0"
  when: manual
  allow_failure: false
  rules:
    - if: '$EMERGENCY_ROLLBACK == "true"'
  environment:
    name: production
    action: rollback
  resource_group: production_us

emergency_rollback_production_eu:
  stage: deploy_production
  extends: .deploy_production_eu_eks
  script:
    - echo "Rolling back EU production to version $ROLLBACK_VERSION"
    - helm history checkr-console --namespace production
    - helm rollback checkr-console $ROLLBACK_VERSION --namespace production --wait --timeout=5m
    - kubectl rollout status deployment/checkr-console -n production --timeout=300s
  variables:
    ROLLBACK_VERSION:
      description: "Helm release version to rollback to"
      value: "0"
  when: manual
  allow_failure: false
  rules:
    - if: '$EMERGENCY_ROLLBACK == "true"'
  environment:
    name: production-eu
    action: rollback
  resource_group: production_eu
```

#### 4b. Git Revert + Emergency Deploy (5-15 minutes)

```yaml
emergency_git_revert:
  stage: build
  script:
    - git config --global user.email "ci@checkr.com"
    - git config --global user.name "GitLab CI"
    - git revert $REVERT_COMMIT --no-edit
    - git push origin HEAD:$CI_COMMIT_REF_NAME
  variables:
    REVERT_COMMIT:
      description: "Git commit SHA to revert"
      value: ""
  rules:
    - if: '$EMERGENCY_REVERT == "true" && $REVERT_COMMIT'
  when: manual

emergency_revert_build:
  stage: build
  extends: .build_image
  variables:
    TARGETS: runtime
  needs: [emergency_git_revert]
  rules:
    - if: '$EMERGENCY_REVERT == "true"'

emergency_revert_deploy:
  stage: deploy_production
  extends: .deploy_production_us
  needs: [emergency_revert_build]
  rules:
    - if: '$EMERGENCY_REVERT == "true"'
  when: manual
```

#### 4c. Database Migration Rollback (Critical for Schema Changes)

```yaml
emergency_db_rollback:
  stage: deploy_production
  image: ${CI_BASE_IMAGE}:${CI_BASE_TAG}
  script:
    - cd /app
    - echo "Rolling back database migrations to version $DB_ROLLBACK_VERSION"
    - bundle exec rake db:migrate:down VERSION=$DB_ROLLBACK_VERSION
    - echo "Database rollback completed"
  variables:
    DB_ROLLBACK_VERSION:
      description: "Database migration version to rollback to"
      value: ""
  rules:
    - if: '$EMERGENCY_DB_ROLLBACK == "true" && $DB_ROLLBACK_VERSION'
  when: manual
  environment:
    name: production
  allow_failure: false
```

#### 4d. Container Image Rollback (Direct Kubernetes)

```yaml
emergency_image_rollback:
  stage: deploy_production
  script:
    - echo "Rolling back to previous container image $PREVIOUS_IMAGE"
    - kubectl set image deployment/checkr-console checkr-console=$PREVIOUS_IMAGE -n production
    - kubectl rollout status deployment/checkr-console -n production --timeout=300s
    - kubectl rollout history deployment/checkr-console -n production
  variables:
    PREVIOUS_IMAGE:
      description: "Previous working container image tag"
      value: ""
  rules:
    - if: '$EMERGENCY_IMAGE_ROLLBACK == "true" && $PREVIOUS_IMAGE'
  when: manual
  environment:
    name: production
  resource_group: production_us
```

## Implementation Recommendations

### Phase 1: Immediate Improvements (Week 1)
1. **Add Emergency Variables** - Implement EMERGENCY_HOTFIX variable system
2. **Create Emergency Jobs** - Add bypass jobs that skip non-critical stages
3. **Document Procedures** - Create runbook for emergency deployments
4. **Test Emergency Path** - Validate emergency pipeline in staging

### Phase 2: Enhanced Capabilities (Week 2-3)
1. **Critical Test Suite** - Create minimal test suite for emergency use (~5 minutes)
2. **Automated Rollback** - Implement one-click rollback mechanism
3. **Break Glass Access** - Configure emergency access roles and approvals
4. **Monitoring Integration** - Add alerting for emergency deployments

### Phase 3: Advanced Features (Month 2)
1. **Feature Flags** - Implement feature toggle system for instant rollouts/rollbacks
2. **Canary Deployments** - Add percentage-based deployment capability
3. **Automated Validation** - Post-deployment health checks and auto-rollback
4. **Incident Integration** - Connect to PagerDuty/incident management

## Security & Compliance Considerations

### Access Control
- Emergency deployments require **Maintainer** role or above
- Protected environment settings maintain approval requirements
- Audit trail preserved through GitLab's built-in logging
- Time-limited emergency access tokens

### Validation Requirements
```yaml
emergency_validation:
  script:
    - echo "Emergency deployment requires valid incident ticket"
    - test -n "$INCIDENT_TICKET" || (echo "INCIDENT_TICKET required" && exit 1)
    - echo "Deploying for incident: $INCIDENT_TICKET"
```

### Rollback Safety Net
- Automatic rollback after 30 minutes if health checks fail
- Database migration validation before deployment
- Blue/green deployment pattern for zero-downtime rollbacks

## Timeline Breakdown: 15-Minute Hotfix

| Stage | Duration | Description |
|-------|----------|-------------|
| Build | 5 minutes | Emergency Docker build (cached layers) |
| Critical Tests | 3 minutes | Smoke tests + critical path validation |
| Deploy | 5 minutes | Helm deployment with health checks |
| Validation | 2 minutes | Post-deploy verification |
| **Total** | **15 minutes** | **From code commit to production** |

## Monitoring & Alerting

### Emergency Deployment Metrics
- Deployment frequency in emergency mode
- Success/failure rates for emergency deployments
- Time to recovery during incidents
- Rollback frequency and timing

### Automated Alerts
```yaml
# Add to deployment jobs
after_script:
  - |
    if [ "$EMERGENCY_HOTFIX" = "true" ]; then
      curl -X POST "$SLACK_WEBHOOK" \
        -H 'Content-Type: application/json' \
        -d "{\"text\":\"🚨 Emergency deployment completed for $CI_COMMIT_SHORT_SHA\"}"
    fi
```

# 🚨 Emergency Procedures

## Emergency Forward Deploy

#### Pre-Deployment Checklist
- [ ] Incident ticket created and validated
- [ ] Code change reviewed by second engineer
- [ ] Database migration impact assessed
- [ ] Rollback plan documented

#### Deployment Steps
1. **Prepare Emergency Branch**
   ```bash
   git checkout -b hotfix/INCIDENT-123
   # Make minimal code changes
   git commit -m "hotfix: emergency fix for INCIDENT-123"
   git push -u origin hotfix/INCIDENT-123
   ```

2. **Trigger Emergency Pipeline**
   - Go to GitLab Pipelines → New Pipeline
   - Set `EMERGENCY_HOTFIX=true`
   - Set `INCIDENT_TICKET=INCIDENT-123`
   - Run pipeline

3. **Monitor Deployment**
   - Watch pipeline progress (~15 minutes)
   - Monitor application health metrics
   - Validate fix resolves incident

## Emergency Rollback Procedures

### Quick Reference: When to Use Each Strategy

| 🚨 Scenario | Strategy | ⏱️ Timeline | 📋 Use When |
|-------------|----------|-------------|-------------|
| 🔴 Bad deployment | [Helm Rollback](#helm-rollback-2-5-minutes) | 2-5 minutes | Container/config issues |
| 🐛 Bad code change | [Git Revert](#git-revert-strategy) | 5-15 minutes | Code bugs, no DB changes (**Add [HOTFIX] to MR title!**) |
| 🗄️ Database migration issue | [DB Migration Rollback](#database-migration-rollback) | 5-10 minutes | Schema changes broke app |
| 📦 Container image issue | [Image Rollback](#container-image-rollback) | 2-3 minutes | Image build problems |

---

### Helm Rollback (2-5 minutes)

**When to use**: Bad deployment, container issues, configuration problems

```bash
# Check current releases
helm history checkr-console --namespace production

# Rollback via GitLab Pipeline
# Go to GitLab → Pipelines → New Pipeline
# Set EMERGENCY_ROLLBACK=true
# Set ROLLBACK_VERSION=0 (or specific version number)
# Run pipeline
```

**Manual execution** (if pipeline unavailable):
```bash
kubectl config set-context --current --namespace=production
helm rollback checkr-console 0 --wait --timeout=5m
kubectl rollout status deployment/checkr-console --timeout=300s
```

### Git Revert Strategy

**When to use**: Bad code changes, logic errors, need to undo specific commits

#### Option A: GitLab UI Revert with MR Title Tag (Recommended)

**The Problem**: GitLab's "Revert" button creates a revert commit but triggers the normal 75-125 minute pipeline! 

**The Solution**: Add `[HOTFIX]` or `[EMERGENCY]` to the MR title when reverting:

**Step 1**: Modify MR Title Before Reverting
1. 🖱️ Go to the problematic MR in GitLab
2. ✏️ **Edit the MR title** → Add `[HOTFIX]` at the beginning or end
   - Example: `[HOTFIX] Fix user authentication bug` 
   - Example: `Fix user authentication bug [EMERGENCY]`
3. 💾 Save the MR title change

**Step 2**: Use Revert Button
4. 🔄 Click "Revert" button → GitLab creates revert commit
5. ⚡ **Pipeline automatically detects hotfix tag** and runs emergency pipeline
6. ✅ Emergency deployment ready in ~5-15 minutes

**Enterprise Pipeline Configuration:**

```yaml
# Emergency hotfix detection - comprehensive pattern matching
.hotfix-emergency-detection: &hotfix-emergency-detection
  # Detects emergency patterns in multiple locations with fallbacks
  rules:
    # Priority 1: Explicit manual override (highest precedence)
    - if: '$EMERGENCY_HOTFIX == "true" || $EMERGENCY_REVERT == "true"'
      variables:
        EMERGENCY_MODE: "manual"
        EMERGENCY_REASON: "Manual override via pipeline variables"
    
    # Priority 2: Commit message patterns (direct commits with tags)
    - if: '$CI_COMMIT_MESSAGE =~ /.*\[(HOTFIX|EMERGENCY|CRITICAL)\].*/i'
      variables:
        EMERGENCY_MODE: "commit_message"
        EMERGENCY_REASON: "Emergency tag detected in commit message"
    
    # Priority 3: MR-based revert patterns (GitLab UI revert button)
    # GitLab revert format: "Revert \"[HOTFIX] Original MR Title\""
    - if: '$CI_COMMIT_MESSAGE =~ /^Revert\s+".*\[(HOTFIX|EMERGENCY|CRITICAL)\].*"/i'
      variables:
        EMERGENCY_MODE: "mr_revert"
        EMERGENCY_REASON: "Emergency revert via GitLab UI with tagged MR title"
    
    # Priority 4: Branch name patterns (hotfix branches)
    - if: '$CI_COMMIT_REF_NAME =~ /^(hotfix|emergency|critical)\/.*$/i'
      variables:
        EMERGENCY_MODE: "branch_name"
        EMERGENCY_REASON: "Emergency branch naming pattern detected"
    
    # Priority 5: Incident-driven patterns (Jira integration)
    - if: '$CI_COMMIT_MESSAGE =~ /.*(INCIDENT-|INC-|P0-|SEV1-).*/i'
      variables:
        EMERGENCY_MODE: "incident_driven"
        EMERGENCY_REASON: "Incident ticket reference detected"
    
    - when: never

# Emergency build stage - optimized for speed
emergency_hotfix_build:
  <<: *hotfix-emergency-detection
  stage: build
  extends: .build_image
  variables:
    TARGETS: runtime
    # Aggressive build optimizations for emergency mode
    DOCKER_BUILDKIT: "1"
    BUILDKIT_PROGRESS: "plain"
    # Skip non-critical build steps
    SKIP_VULNERABILITY_SCAN: "true"
    SKIP_IMAGE_OPTIMIZATION: "true"
  script:
    - echo "🚨 EMERGENCY BUILD INITIATED"
    - echo "Emergency Mode: $EMERGENCY_MODE"
    - echo "Reason: $EMERGENCY_REASON" 
    - echo "Commit: $CI_COMMIT_SHORT_SHA"
    - echo "Triggered by: $GITLAB_USER_EMAIL"
    # Alert monitoring systems
    - |
      curl -X POST "$SLACK_EMERGENCY_WEBHOOK" \
        -H 'Content-Type: application/json' \
        -d "{
          \"text\": \"🚨 Emergency Build Started\",
          \"blocks\": [{
            \"type\": \"section\",
            \"text\": {
              \"type\": \"mrkdwn\",
              \"text\": \"*Emergency Mode:* $EMERGENCY_MODE\\n*Reason:* $EMERGENCY_REASON\\n*Commit:* $CI_COMMIT_SHORT_SHA\\n*User:* $GITLAB_USER_EMAIL\\n*Pipeline:* $CI_PIPELINE_URL\"
            }
          }]
        }"
    # Proceed with optimized build
    - !reference [.build_image, script]
  needs: []
  timeout: 10 minutes
  tags:
    - emergency-runner  # Dedicated high-priority runners
  artifacts:
    expire_in: 30 minutes
    reports:
      dotenv: emergency.env
  after_script:
    - echo "EMERGENCY_BUILD_TIME=$(date -Iseconds)" >> emergency.env
    - echo "EMERGENCY_IMAGE_TAG=$RUNTIME_IMAGE" >> emergency.env

# Emergency validation - minimal critical path testing only
emergency_critical_validation:
  <<: *hotfix-emergency-detection  
  stage: test
  image: ${CI_BASE_IMAGE}:${CI_BASE_TAG}
  variables:
    <<: *unit_test_variables
    # Run only P0 critical path tests
    TEST_PATTERN: "spec/critical/**/*_spec.rb"
  script:
    - echo "🔍 Running critical path validation only"
    - cd /app
    # Database check
    - bundle exec rake db:migrate:status | tail -5
    # Critical smoke tests only (max 5 minutes)  
    - timeout 300 bundle exec rspec $TEST_PATTERN --fail-fast --format documentation
  needs: [emergency_hotfix_build]
  timeout: 8 minutes
  allow_failure: false
  artifacts:
    when: always
    expire_in: 1 hour
    reports:
      junit: emergency-test-results.xml

# Emergency deployment - production ready
emergency_hotfix_deploy_us:
  <<: *hotfix-emergency-detection
  stage: deploy_production
  extends: .deploy_production_us
  variables:
    OVERRIDE_FILES: "-f platform/values.yaml -f production_us.yaml -f platform/production_us.yaml"
    OVERRIDE_SETS: "--set microservice.podDefaults.image=$RUNTIME_IMAGE \
                    --set microservice.podDefaults.imagePullSecrets=$DOCKER_SECRET \
                    --set microservice.podDefaults.createSecrets=false \
                    --set microservice.deployments.checkr-console.env.global.CI_COMMIT_SHORT_SHA=$CI_COMMIT_SHORT_SHA \
                    --set microservice.deployments.checkr-console.env.global.EMERGENCY_DEPLOY=true"
    HELM_ADDITIONAL_FLAGS: "--timeout 15m0s --wait --wait-for-jobs"
  script:
    - echo "🚀 EMERGENCY PRODUCTION DEPLOYMENT"
    - echo "Emergency Mode: $EMERGENCY_MODE" 
    - echo "Image: $RUNTIME_IMAGE"
    # Pre-deployment validation
    - helm lint ./helm-chart
    - kubectl cluster-info
    # Emergency deployment with enhanced monitoring
    - |
      helm upgrade checkr-console ./helm-chart \
        $OVERRIDE_FILES $OVERRIDE_SETS $HELM_ADDITIONAL_FLAGS \
        --namespace production \
        --create-namespace \
        --install
    # Post-deployment verification
    - kubectl rollout status deployment/checkr-console -n production --timeout=600s
    - kubectl get pods -n production -l app=checkr-console
    # Health check validation
    - |
      for i in {1..12}; do
        if curl -f -s https://production.checkrhq.net/health > /dev/null; then
          echo "✅ Health check passed after ${i}0 seconds"
          break
        fi
        if [ $i -eq 12 ]; then
          echo "❌ Health check failed after 120 seconds"
          exit 1
        fi
        sleep 10
      done
  environment:
    name: production
    url: https://production.checkrhq.net
  when: manual
  allow_failure: false
  needs: 
    - emergency_hotfix_build
    - emergency_critical_validation
  resource_group: production_us
  timeout: 20 minutes
  after_script:
    # Comprehensive emergency deployment notifications
    - |
      DEPLOYMENT_STATUS="success"
      if [ $CI_JOB_STATUS != "success" ]; then
        DEPLOYMENT_STATUS="failed"
      fi
      
      curl -X POST "$SLACK_EMERGENCY_WEBHOOK" \
        -H 'Content-Type: application/json' \
        -d "{
          \"text\": \"🚨 Emergency Deployment $DEPLOYMENT_STATUS\",
          \"blocks\": [{
            \"type\": \"section\",
            \"text\": {
              \"type\": \"mrkdwn\",
              \"text\": \"*Status:* $DEPLOYMENT_STATUS\\n*Emergency Mode:* $EMERGENCY_MODE\\n*Image:* $RUNTIME_IMAGE\\n*User:* $GITLAB_USER_EMAIL\\n*Pipeline:* $CI_PIPELINE_URL\\n*Production:* https://production.checkrhq.net\"
            }
          }]
        }"
      
      # Alert PagerDuty for failed emergency deployments
      if [ "$DEPLOYMENT_STATUS" = "failed" ]; then
        curl -X POST 'https://events.pagerduty.com/v2/enqueue' \
          -H 'Authorization: Token $PAGERDUTY_TOKEN' \
          -H 'Content-Type: application/json' \
          -d "{
            \"routing_key\": \"$PAGERDUTY_INTEGRATION_KEY\",
            \"event_action\": \"trigger\",
            \"payload\": {
              \"summary\": \"Emergency deployment failed: $CI_COMMIT_SHORT_SHA\",
              \"severity\": \"critical\",
              \"source\": \"gitlab-emergency-pipeline\",
              \"custom_details\": {
                \"pipeline_url\": \"$CI_PIPELINE_URL\",
                \"emergency_mode\": \"$EMERGENCY_MODE\",
                \"user\": \"$GITLAB_USER_EMAIL\"
              }
            }
          }"
      fi

# Emergency rollback capability 
emergency_rollback_production:
  rules:
    - if: '$EMERGENCY_ROLLBACK == "true"'
  stage: deploy_production
  extends: .deploy_production_us
  script:
    - echo "🔄 EMERGENCY ROLLBACK INITIATED"
    - helm history checkr-console --namespace production
    - |
      ROLLBACK_VERSION=${ROLLBACK_VERSION:-0}
      echo "Rolling back to version: $ROLLBACK_VERSION"
      helm rollback checkr-console $ROLLBACK_VERSION --namespace production --wait --timeout=10m
    - kubectl rollout status deployment/checkr-console -n production --timeout=600s
  variables:
    ROLLBACK_VERSION:
      description: "Helm release version to rollback to (0=previous, 1=before that)"
      value: "0"
  environment:
    name: production
    action: rollback
  when: manual
  allow_failure: false
  resource_group: production_us
  timeout: 15 minutes
```

**Why this approach**:
- ✅ **One-step process**: Edit title + click revert = automatic emergency pipeline
- ✅ **Clear intent**: `[HOTFIX]` makes it obvious this is an emergency
- ✅ **No extra steps**: No manual pipeline triggering needed
- ✅ **Works with GitLab UI**: Leverages existing revert functionality

#### Option B: Manual Git Revert (More Control)

```bash
# Find the problematic commit
git log --oneline -10

# Create revert branch
git checkout -b revert/INCIDENT-123
git revert <commit-sha> --no-edit
git push -u origin revert/INCIDENT-123

# Trigger emergency pipeline
# Go to GitLab → Pipelines → New Pipeline
# Set EMERGENCY_REVERT=true
# Set REVERT_COMMIT=<commit-sha>
```

#### Option C: Already Used UI Revert?

**If you already used GitLab's revert button and the normal pipeline is running:**

1. 🛑 Cancel the slow pipeline in GitLab UI (optional)
2. 🚀 Go to GitLab → Pipelines → "New Pipeline"
3. 📋 Select the **revert commit** from the branch/tag dropdown
4. ⚡ Set `EMERGENCY_REVERT=true` variable  
5. ✅ Run emergency pipeline

**Pipeline Configuration Needed:**
```yaml
# Add emergency revert jobs that can be manually triggered
emergency_revert_build:
  rules:
    - if: '$EMERGENCY_REVERT == "true"'
  stage: build
  extends: .build_image
  variables:
    TARGETS: runtime
  needs: []
  timeout: 10 minutes

emergency_revert_deploy:
  rules:
    - if: '$EMERGENCY_REVERT == "true"'
  stage: deploy_production
  extends: .deploy_production_us
  needs: [emergency_revert_build]
  when: manual
  allow_failure: false
```

### Database Migration Rollback

**When to use**: Schema changes broke the application

```bash
# Check current migration version
# In Rails console or database:
SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 5;

# Rollback via GitLab Pipeline
# Set EMERGENCY_DB_ROLLBACK=true
# Set DB_ROLLBACK_VERSION=<target_version>
```

**Manual execution**:
```bash
cd /app
bundle exec rake db:migrate:down VERSION=<version>
```

### Container Image Rollback

**When to use**: Container build issues, image corruption

```bash
# Find previous working image
kubectl describe deployment checkr-console -n production
# Look for previous image in deployment history

# Rollback via GitLab Pipeline
# Set EMERGENCY_IMAGE_ROLLBACK=true
# Set PREVIOUS_IMAGE=<image:tag>
```

### Nuclear Option: Manual kubectl Rollback

**When to use**: All pipeline methods fail

```bash
# Check deployment history
kubectl rollout history deployment/checkr-console -n production

# Rollback to previous revision
kubectl rollout undo deployment/checkr-console -n production

# Check status
kubectl rollout status deployment/checkr-console -n production
```

---

## Post-Emergency Actions
- [ ] Update incident ticket with resolution
- [ ] Verify application functionality
- [ ] Check monitoring/alerting systems
- [ ] Schedule proper fix for next sprint
- [ ] Conduct post-incident review
- [ ] Document lessons learned

## Emergency Contacts
- **On-Call Engineer**: (Pipeline Issues)
- **Platform Team**: (Kubernetes/Infrastructure)  
- **Database Team**: (Migration Issues)
- **Security Team**: (If revert involves security fixes)

---

# 📖 Reference & Implementation

## Testing Strategy

### Emergency Pipeline Testing
- Monthly "fire drill" exercises
- Staging environment emergency deployment tests
- Automated validation of emergency bypass logic
- Performance benchmarking of emergency timeline

### Validation Checklist
- [ ] Emergency pipeline completes in <15 minutes
- [ ] Critical functionality remains intact
- [ ] Rollback mechanism tested and verified
- [ ] Access controls properly configured
- [ ] Monitoring and alerting functional

## Conclusion

Implementing these break glass strategies will provide your team with the capability to deploy critical hotfixes to production within 15 minutes while maintaining appropriate safety controls and audit trails. The phased approach allows for gradual implementation and validation of emergency procedures.

**Next Steps:**
1. Review and approve strategy with engineering leadership
2. Create JIRA ticket for implementation (suggest: EDEVE-XXX)
3. Begin Phase 1 implementation
4. Schedule emergency deployment drill

**Key Success Metrics:**
- Emergency deployment time: <15 minutes
- Emergency deployment success rate: >95%
- Time to incident resolution: <30 minutes
- Zero unplanned production outages during emergency deployments