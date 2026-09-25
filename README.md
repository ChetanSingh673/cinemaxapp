# 🎬 CineBook — Movie Ticket Booking Platform on AWS EKS

> A BookMyShow-inspired microservices application deployed on AWS EKS using Kubernetes Gateway API, MongoDB with EBS dynamic provisioning, and ArgoCD for GitOps.

**Developed by [Learn With KASTRO](https://www.youtube.com/@LearnWithKASTRO)**

---

## 📐 Architecture Overview

```
                          ┌─────────────────────────────────────────────┐
                          │              AWS EKS Cluster                 │
         User             │   kastro-cluster (ap-south-1)               │
          │               │                                              │
          ▼               │   ┌──────────────────────────────────────┐  │
    AWS ALB (internet)    │   │        Kubernetes Gateway API         │  │
    (Gateway API)─────────┼──▶│   GatewayClass + Gateway (HTTP:80)   │  │
                          │   └───────────────┬──────────────────────┘  │
                          │                   │  Path-Based Routing      │
                          │      ┌────────────┼────────────┐            │
                          │      │            │            │            │
                          │   /  │      /auth │  /movies   │  /seats    │
                          │      ▼            ▼            ▼            │
                          │  ┌───────┐  ┌────────┐  ┌────────┐         │
                          │  │Front  │  │ Auth   │  │ Movie  │         │
                          │  │ end   │  │Service │  │Service │         │
                          │  │:5000  │  │:5001   │  │:5002   │         │
                          │  └───┬───┘  └───┬────┘  └───┬────┘         │
                          │      │          │            │              │
                          │      │     ┌────────┐  ┌────────┐          │
                          │      │     │Booking │  │Payment │          │
                          │      │     │Service │  │Service │          │
                          │      │     │:5003   │  │:5004   │          │
                          │      │     └───┬────┘  └───┬────┘          │
                          │      │         │            │               │
                          │  ┌───▼──┐  ┌──▼──┐  ┌─────▼──┐  ┌─────┐  │
                          │  │Mongo │  │Mongo│  │ Mongo  │  │Mongo│  │
                          │  │Auth  │  │Movie│  │Booking │  │Pay  │  │
                          │  │(EBS) │  │(EBS)│  │ (EBS)  │  │(EBS)│  │
                          │  └──────┘  └─────┘  └────────┘  └─────┘  │
                          └─────────────────────────────────────────────┘
```

---

## 🗂️ Project Structure

```
cinebook/
├── frontend/                    # Flask + Jinja2 UI (port 5000)
│   ├── app/main.py
│   ├── templates/               # HTML templates (base, index, cities, movies, seats, payment, confirmation)
│   ├── static/                  # CSS, JS, images
│   ├── requirements.txt
│   └── Dockerfile
├── auth-service/                # User login service (port 5001)
│   ├── app/main.py
│   ├── requirements.txt
│   └── Dockerfile
├── movie-service/               # Movies + showtimes data (port 5002)
│   ├── app/main.py
│   ├── requirements.txt
│   └── Dockerfile
├── booking-service/             # Seat management (port 5003)
│   ├── app/main.py
│   ├── requirements.txt
│   └── Dockerfile
├── payment-service/             # Dummy payment + confirmation (port 5004)
│   ├── app/main.py
│   ├── requirements.txt
│   └── Dockerfile
├── k8s/
│   ├── namespaces/
│   │   └── namespace.yaml
│   ├── mongodb/
│   │   ├── storageclass.yaml    # EBS gp3 StorageClass
│   │   └── mongodb-statefulsets.yaml   # 4 MongoDB StatefulSets + headless Services
│   ├── services/
│   │   ├── secrets.yaml
│   │   └── deployments.yaml    # 5 Deployments + ClusterIP Services
│   ├── gateway/
│   │   ├── gateway.yaml        # GatewayClass + Gateway (AWS ALB)
│   │   └── httproutes.yaml     # HTTPRoute for each service
│   └── argocd/
│       └── argocd-app.yaml     # ArgoCD Application + AppProject
├── build-push.sh                # Docker build & push script
└── README.md
```

---

## 🔢 User Flow

```
Login Page → City Select → Movies List → Movie Detail
         → Seat Selection → Payment → Booking Confirmation
```

---

## 🚀 Step-by-Step Deployment Guide

### PHASE 1 — Cluster Connection

```bash
# Configure kubectl to connect to your EKS cluster
aws eks update-kubeconfig \
  --region ap-south-1 \
  --name kastro-cluster

# Verify connection
kubectl get nodes
kubectl get nodes -o wide
```

---

### PHASE 2 — Install EBS CSI Driver (Dynamic Volume Provisioning)

```bash
# Step 1: Create IAM OIDC provider for the cluster
eksctl utils associate-iam-oidc-provider \
  --region ap-south-1 \
  --cluster kastro-cluster \
  --approve

# Step 2: Create IAM service account for EBS CSI Driver
eksctl create iamserviceaccount \
  --name ebs-csi-controller-sa \
  --namespace kube-system \
  --cluster kastro-cluster \
  --region ap-south-1 \
  --role-name AmazonEKS_EBS_CSI_DriverRole \
  --role-only \
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
  --approve

# Step 3: Get your AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Account ID: $AWS_ACCOUNT_ID"

# Step 4: Add the EBS CSI Driver as an EKS addon
eksctl create addon \
  --name aws-ebs-csi-driver \
  --cluster kastro-cluster \
  --region ap-south-1 \
  --service-account-role-arn arn:aws:iam::${AWS_ACCOUNT_ID}:role/AmazonEKS_EBS_CSI_DriverRole \
  --force

# Step 5: Verify the addon is ACTIVE
eksctl get addon \
  --name aws-ebs-csi-driver \
  --cluster kastro-cluster \
  --region ap-south-1

# Verify CSI driver pods are running
kubectl get pods -n kube-system -l app=ebs-csi-controller
kubectl get pods -n kube-system -l app=ebs-csi-node
```

---

### PHASE 3 — Install Gateway API CRDs

> Source: https://gateway-api.sigs.k8s.io/guides/

```bash
# Install the standard Gateway API CRDs (v1.2.0 - latest stable)
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.0/standard-install.yaml

# Verify CRDs are installed
kubectl get crd | grep gateway.networking.k8s.io

# Expected output:
# gatewayclasses.gateway.networking.k8s.io
# gateways.gateway.networking.k8s.io
# httproutes.gateway.networking.k8s.io
# grpcroutes.gateway.networking.k8s.io
# referencegrants.gateway.networking.k8s.io
```

---

### PHASE 4 — Install AWS Load Balancer Controller

```bash
# Step 1: Add the EKS Helm repo
helm repo add eks https://aws.github.io/eks-charts
helm repo update

# Step 2: Create IAM policy for ALB Controller
curl -o alb-iam-policy.json \
  https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/install/iam_policy.json

aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file://alb-iam-policy.json

# Step 3: Create service account
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

eksctl create iamserviceaccount \
  --cluster kastro-cluster \
  --namespace kube-system \
  --region ap-south-1 \
  --name aws-load-balancer-controller \
  --attach-policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/AWSLoadBalancerControllerIAMPolicy \
  --override-existing-serviceaccounts \
  --approve

# Step 4: Get VPC ID
VPC_ID=$(aws eks describe-cluster \
  --name kastro-cluster \
  --region ap-south-1 \
  --query "cluster.resourcesVpcConfig.vpcId" \
  --output text)
echo "VPC ID: $VPC_ID"

# Step 5: Install ALB Controller via Helm
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=kastro-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set region=ap-south-1 \
  --set vpcId=${VPC_ID} \
  --set enableGatewayAPI=true

# Step 6: Verify ALB Controller is running
kubectl get deployment -n kube-system aws-load-balancer-controller
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller
```

---

### PHASE 5 — Build & Push Docker Images

```bash
# Navigate to the project root
cd cinebook/

# Make the script executable
chmod +x build-push.sh

# Build and push ALL services at once
bash build-push.sh all

# OR build individual services
bash build-push.sh frontend
bash build-push.sh auth-service
bash build-push.sh movie-service
bash build-push.sh booking-service
bash build-push.sh payment-service

# Build with a specific version tag
VERSION=v1.0.0 bash build-push.sh all

# Verify images on DockerHub
docker pull kastrov/cinebook-frontend:latest
docker pull kastrov/cinebook-auth:latest
docker pull kastrov/cinebook-movie:latest
docker pull kastrov/cinebook-booking:latest
docker pull kastrov/cinebook-payment:latest
```

---

### PHASE 6 — Deploy to Kubernetes (Manual)

> Skip this if using ArgoCD. Use this for manual/initial deployment.

```bash
# Step 1: Create namespace
kubectl apply -f k8s/namespaces/namespace.yaml
kubectl get namespace cinebook

# Step 2: Apply EBS StorageClass
kubectl apply -f k8s/mongodb/storageclass.yaml
kubectl get storageclass

# Step 3: Deploy MongoDB StatefulSets
kubectl apply -f k8s/mongodb/mongodb-statefulsets.yaml

# Wait for MongoDB pods to be Running (takes ~60-90s)
kubectl get pods -n cinebook -w
# Press Ctrl+C once all mongodb-* pods show Running

# Verify PVCs are bound (EBS volumes auto-provisioned)
kubectl get pvc -n cinebook
kubectl get pv

# Step 4: Apply Secrets
kubectl apply -f k8s/services/secrets.yaml

# Step 5: Deploy all microservices
kubectl apply -f k8s/services/deployments.yaml
kubectl get pods -n cinebook -w

# Step 6: Apply Gateway API resources
kubectl apply -f k8s/gateway/gateway.yaml
kubectl apply -f k8s/gateway/httproutes.yaml

# Step 7: Verify everything
kubectl get all -n cinebook
kubectl get gateway -n cinebook
kubectl get httproute -n cinebook
```

---

### PHASE 7 — Access the Application

```bash
# Get the ALB DNS name (takes ~2-3 minutes to provision)
kubectl get gateway -n cinebook cinebook-gateway -o jsonpath='{.status.addresses[0].value}'

# OR get it from the AWS Load Balancer Controller events
kubectl describe gateway cinebook-gateway -n cinebook

# OR query AWS directly
aws elbv2 describe-load-balancers \
  --region ap-south-1 \
  --query 'LoadBalancers[?contains(LoadBalancerName, `k8s-cinebook`)].DNSName' \
  --output text

# The app is accessible at:
# http://<ALB-DNS-NAME>/
```

---

### PHASE 8 — ArgoCD Deployment (GitOps)

```bash
# Step 1: Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Step 2: Wait for ArgoCD to be ready
kubectl wait --for=condition=available deployment/argocd-server \
  -n argocd --timeout=300s

# Step 3: Get ArgoCD initial admin password
kubectl get secret argocd-initial-admin-secret \
  -n argocd \
  -o jsonpath="{.data.password}" | base64 -d && echo

# Step 4: Port-forward ArgoCD UI (from your client machine)
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Step 5: Login via CLI
argocd login localhost:8080 \
  --username admin \
  --password <PASSWORD_FROM_STEP_3> \
  --insecure

# Step 6: Push your project to GitHub
# Edit k8s/argocd/argocd-app.yaml and set your repoURL
# git init, git add ., git commit, git remote add origin ..., git push

# Step 7: Apply ArgoCD Application
kubectl apply -f k8s/argocd/argocd-app.yaml

# Step 8: Verify sync
argocd app get cinebook-app
argocd app sync cinebook-app

# Step 9: Watch sync status
argocd app wait cinebook-app --sync --health --timeout 300

# Step 10: Open ArgoCD UI
# Access: https://localhost:8080 (admin / <password>)
```

---

## 🛢️ MongoDB Pod Access Commands

### Connect to MongoDB pods

```bash
# ── Auth MongoDB ─────────────────────────────────────────
kubectl exec -it mongodb-auth-0 -n cinebook -- mongosh authdb

# ── Movie MongoDB ────────────────────────────────────────
kubectl exec -it mongodb-movie-0 -n cinebook -- mongosh moviedb

# ── Booking MongoDB ──────────────────────────────────────
kubectl exec -it mongodb-booking-0 -n cinebook -- mongosh bookingdb

# ── Payment MongoDB ──────────────────────────────────────
kubectl exec -it mongodb-payment-0 -n cinebook -- mongosh paymentdb
```

### Useful MongoDB queries

```javascript
// ── Inside mongosh authdb ──────────────────────────────
// List all users
db.users.find().pretty()

// Count users
db.users.countDocuments()

// Find user by email
db.users.findOne({ email: "user@example.com" })

// ── Inside mongosh moviedb ─────────────────────────────
// List all movies
db.movies.find({}, { title: 1, city: 1, rating: 1 }).pretty()

// Movies by city
db.movies.find({ city: "Chennai" }, { title: 1, rating: 1 })

// ── Inside mongosh bookingdb ───────────────────────────
// All seat layouts
db.seat_layouts.find({}, { key: 1 }).pretty()

// Booking by theatre
db.bookings.find({ theatre_id: "th_che_1" }).pretty()

// ── Inside mongosh paymentdb ───────────────────────────
// All payments
db.payments.find({}, { booking_id: 1, movie_title: 1, amount: 1 }).pretty()

// Payments by user email
db.payments.find({ "user.email": "user@example.com" }).pretty()

// Total revenue
db.payments.aggregate([{ $group: { _id: null, total: { $sum: "$amount" } } }])
```

### Check MongoDB logs and status

```bash
# Check MongoDB pod logs
kubectl logs mongodb-auth-0    -n cinebook --tail=50
kubectl logs mongodb-movie-0   -n cinebook --tail=50
kubectl logs mongodb-booking-0 -n cinebook --tail=50
kubectl logs mongodb-payment-0 -n cinebook --tail=50

# Describe pod for events
kubectl describe pod mongodb-auth-0 -n cinebook

# Check PVC status
kubectl get pvc -n cinebook
kubectl describe pvc data-mongodb-auth-0 -n cinebook

# Check EBS volumes in AWS
aws ec2 describe-volumes \
  --region ap-south-1 \
  --filters Name=tag-key,Values=kubernetes.io/cluster/kastro-cluster \
  --query 'Volumes[*].{ID:VolumeId,Size:Size,State:State,AZ:AvailabilityZone}' \
  --output table
```

---

## 🔍 Verification & Debugging Commands

### Check all resources

```bash
# Overview of all cinebook resources
kubectl get all -n cinebook

# Check pod status
kubectl get pods -n cinebook -o wide

# Check services
kubectl get svc -n cinebook

# Check Gateway and routes
kubectl get gateway -n cinebook
kubectl get httproute -n cinebook
kubectl describe gateway cinebook-gateway -n cinebook

# Check ingress/ALB
kubectl get events -n cinebook --sort-by='.lastTimestamp'
```

### View application logs

```bash
# Frontend logs
kubectl logs -l app=frontend -n cinebook --tail=100 -f

# Auth service logs
kubectl logs -l app=auth-service -n cinebook --tail=100 -f

# Movie service logs
kubectl logs -l app=movie-service -n cinebook --tail=100 -f

# Booking service logs
kubectl logs -l app=booking-service -n cinebook --tail=100 -f

# Payment service logs
kubectl logs -l app=payment-service -n cinebook --tail=100 -f
```

### Restart deployments

```bash
kubectl rollout restart deployment/frontend         -n cinebook
kubectl rollout restart deployment/auth-service     -n cinebook
kubectl rollout restart deployment/movie-service    -n cinebook
kubectl rollout restart deployment/booking-service  -n cinebook
kubectl rollout restart deployment/payment-service  -n cinebook

# Check rollout status
kubectl rollout status deployment/frontend -n cinebook
```

### Port-forward for local testing (without ALB)

```bash
# Test frontend locally
kubectl port-forward svc/frontend -n cinebook 5000:5000

# Test individual services
kubectl port-forward svc/auth-service    -n cinebook 5001:5001
kubectl port-forward svc/movie-service   -n cinebook 5002:5002
kubectl port-forward svc/booking-service -n cinebook 5003:5003
kubectl port-forward svc/payment-service -n cinebook 5004:5004

# Health check from client machine
curl http://localhost:5000/health
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health
curl http://localhost:5004/health
```

---

## 🌐 Gateway API Path Routing Table

| Path Prefix       | Service          | Port |
|-------------------|------------------|------|
| `/`               | frontend         | 5000 |
| `/login`          | frontend         | 5000 |
| `/cities`         | frontend         | 5000 |
| `/auth/*`         | auth-service     | 5001 |
| `/movies/*`       | movie-service    | 5002 |
| `/movie/*`        | movie-service    | 5002 |
| `/seats/*`        | booking-service  | 5003 |
| `/booking/*`      | booking-service  | 5003 |
| `/payment`        | payment-service  | 5004 |
| `/process_payment`| payment-service  | 5004 |

> **Note:** Frontend is the catch-all route. All `/login`, `/cities`, `/seats`, `/payment` UI pages are served by the frontend (Flask renders templates). The backend API services are only called internally (service-to-service) within the cluster. The Gateway API routes `/auth`, `/movies`, `/seats`, `/payment` are for direct API access if needed.

---

## 📦 Environment Variables Reference

| Service          | Variable            | Value                                                        |
|------------------|---------------------|--------------------------------------------------------------|
| frontend         | AUTH_SERVICE_URL    | http://auth-service:5001                                     |
| frontend         | MOVIE_SERVICE_URL   | http://movie-service:5002                                    |
| frontend         | BOOKING_SERVICE_URL | http://booking-service:5003                                  |
| frontend         | PAYMENT_SERVICE_URL | http://payment-service:5004                                  |
| frontend         | SECRET_KEY          | (from Secret: cinebook-secrets)                              |
| auth-service     | MONGO_URI           | mongodb://mongodb-auth-0.mongodb-auth.cinebook.svc...:27017  |
| movie-service    | MONGO_URI           | mongodb://mongodb-movie-0.mongodb-movie.cinebook.svc...:27017|
| booking-service  | MONGO_URI           | mongodb://mongodb-booking-0...                               |
| booking-service  | MOVIE_SERVICE_URL   | http://movie-service:5002                                    |
| payment-service  | MONGO_URI           | mongodb://mongodb-payment-0...                               |
| payment-service  | MOVIE_SERVICE_URL   | http://movie-service:5002                                    |
| payment-service  | BOOKING_SERVICE_URL | http://booking-service:5003                                  |

---

## 🧹 Cleanup

```bash
# Delete all cinebook resources
kubectl delete namespace cinebook

# Delete Gateway API CRDs (optional)
kubectl delete -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.0/standard-install.yaml

# Uninstall ALB Controller
helm uninstall aws-load-balancer-controller -n kube-system

# Uninstall ArgoCD (optional)
kubectl delete namespace argocd

# Delete EBS volumes (after PVCs are deleted — reclaimPolicy: Retain means manual cleanup)
# List EBS volumes tagged with cluster
aws ec2 describe-volumes \
  --region ap-south-1 \
  --filters Name=tag-key,Values=kubernetes.io/cluster/kastro-cluster \
  --query 'Volumes[*].VolumeId' --output text | \
  xargs -I {} aws ec2 delete-volume --volume-id {} --region ap-south-1

# Delete EKS cluster (optional — destructive!)
eksctl delete cluster --name kastro-cluster --region ap-south-1
```

---

## 🗺️ Cities & Movies Available

| City      | Movies Available                                              |
|-----------|---------------------------------------------------------------|
| Chennai   | Dune: Part Two, Oppenheimer, Avengers: Secret Wars, Kalki 2898 AD |
| Bangalore | Gladiator II, Interstellar 2, The Dark Knight Returns, RRR 2 |
| Hyderabad | Baahubali 3, Mission Impossible: Final Chapter, Spider-Man: Across the Spider-Verse 2 |
| Kochi     | Manjummel Boys 2, Avatar 3: Fire and Ash, Lucifer 3          |

---

## 🛠️ Tech Stack

| Layer         | Technology                          |
|---------------|-------------------------------------|
| Frontend      | Python Flask + Jinja2 + HTML/CSS/JS |
| Backend APIs  | Python Flask                        |
| Database      | MongoDB 7.0 (StatefulSet)           |
| Storage       | AWS EBS gp3 (dynamic provisioning)  |
| Container     | Docker + DockerHub                  |
| Orchestration | Kubernetes (AWS EKS)                |
| Routing       | Kubernetes Gateway API v1           |
| Load Balancer | AWS ALB (via LB Controller)         |
| GitOps        | ArgoCD                              |
| Node Size     | t2.medium × 2 worker nodes          |

---

## 📝 Notes

- The `ReclaimPolicy: Retain` on the EBS StorageClass means EBS volumes are **NOT deleted** when PVCs are deleted. You must manually delete them from AWS Console or CLI to avoid cost.
- `t2.medium` nodes have 2 vCPU and 4GB RAM. With 4 MongoDB pods + 5 service pods (2 replicas each = 10 pods) + system pods, the cluster will be near capacity. Consider upgrading to `t3.medium` if you experience OOMKill events.
- The frontend serves all HTML pages directly; backend services are called via internal service-to-service HTTP.
- All payment processing is **dummy/simulated** — no real payment gateway is integrated.

---

## 👨‍💻 Developed By

**Learn With KASTRO**
[YouTube: @LearnWithKASTRO](https://www.youtube.com/@LearnWithKASTRO)
