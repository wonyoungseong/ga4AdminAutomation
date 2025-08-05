#!/bin/bash
set -e

# Production Deployment Script for GA4 Admin Portal
# This script handles the complete deployment process

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_REGISTRY="ghcr.io"
PROJECT_NAME="ga4-admin"
NAMESPACE="ga4-admin"
ENVIRONMENT="${ENVIRONMENT:-production}"
DRY_RUN="${DRY_RUN:-false}"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if required tools are installed
    local tools=("docker" "kubectl" "helm")
    for tool in "${tools[@]}"; do
        if ! command -v $tool &> /dev/null; then
            print_error "$tool is not installed or not in PATH"
            exit 1
        fi
    done
    
    # Check if kubectl is configured
    if ! kubectl cluster-info &> /dev/null; then
        print_error "kubectl is not configured or cluster is not accessible"
        exit 1
    fi
    
    # Check if environment file exists
    if [[ ! -f ".env.${ENVIRONMENT}" ]]; then
        print_error "Environment file .env.${ENVIRONMENT} not found"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to build Docker images
build_images() {
    print_status "Building Docker images..."
    
    local tag="${TAG:-latest}"
    local backend_image="${DOCKER_REGISTRY}/${PROJECT_NAME}/backend:${tag}"
    local frontend_image="${DOCKER_REGISTRY}/${PROJECT_NAME}/frontend:${tag}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "DRY RUN: Would build images:"
        print_status "  - ${backend_image}"
        print_status "  - ${frontend_image}"
        return
    fi
    
    # Build backend image
    print_status "Building backend image..."
    docker build -t "${backend_image}" ./backend
    
    # Build frontend image
    print_status "Building frontend image..."
    docker build -t "${frontend_image}" ./frontend \
        --build-arg NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL}"
    
    print_success "Images built successfully"
}

# Function to push Docker images
push_images() {
    print_status "Pushing Docker images..."
    
    local tag="${TAG:-latest}"
    local backend_image="${DOCKER_REGISTRY}/${PROJECT_NAME}/backend:${tag}"
    local frontend_image="${DOCKER_REGISTRY}/${PROJECT_NAME}/frontend:${tag}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "DRY RUN: Would push images:"
        print_status "  - ${backend_image}"
        print_status "  - ${frontend_image}"
        return
    fi
    
    # Login to registry if credentials are provided
    if [[ -n "$DOCKER_USERNAME" && -n "$DOCKER_PASSWORD" ]]; then
        echo "$DOCKER_PASSWORD" | docker login "$DOCKER_REGISTRY" -u "$DOCKER_USERNAME" --password-stdin
    fi
    
    # Push images
    docker push "${backend_image}"
    docker push "${frontend_image}"
    
    print_success "Images pushed successfully"
}

# Function to deploy to Kubernetes
deploy_k8s() {
    print_status "Deploying to Kubernetes..."
    
    local tag="${TAG:-latest}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "DRY RUN: Would deploy to Kubernetes namespace ${NAMESPACE}"
        return
    fi
    
    # Create namespace if it doesn't exist
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply secrets and configmaps
    print_status "Applying secrets and configmaps..."
    
    # Create secrets from environment file
    kubectl create secret generic app-secrets \
        --from-env-file=".env.${ENVIRONMENT}" \
        --namespace="$NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Update image tags in manifests
    local temp_dir=$(mktemp -d)
    cp -r k8s/* "$temp_dir/"
    
    # Replace image tags
    sed -i "s|ga4-admin/backend:latest|${DOCKER_REGISTRY}/${PROJECT_NAME}/backend:${tag}|g" "$temp_dir/backend-deployment.yaml"
    sed -i "s|ga4-admin/frontend:latest|${DOCKER_REGISTRY}/${PROJECT_NAME}/frontend:${tag}|g" "$temp_dir/frontend-deployment.yaml"
    
    # Apply manifests
    print_status "Applying Kubernetes manifests..."
    kubectl apply -f "$temp_dir/" --namespace="$NAMESPACE"
    
    # Wait for rollout to complete
    print_status "Waiting for deployment to complete..."
    kubectl rollout status deployment/backend --namespace="$NAMESPACE" --timeout=600s
    kubectl rollout status deployment/frontend --namespace="$NAMESPACE" --timeout=600s
    kubectl rollout status deployment/postgres --namespace="$NAMESPACE" --timeout=300s
    
    # Clean up temp directory
    rm -rf "$temp_dir"
    
    print_success "Kubernetes deployment completed"
}

# Function to run health checks
health_check() {
    print_status "Running health checks..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "DRY RUN: Would run health checks"
        return
    fi
    
    # Wait for pods to be ready
    print_status "Waiting for pods to be ready..."
    kubectl wait --for=condition=ready pod -l app=backend --namespace="$NAMESPACE" --timeout=300s
    kubectl wait --for=condition=ready pod -l app=frontend --namespace="$NAMESPACE" --timeout=300s
    
    # Run health checks
    print_status "Testing backend health endpoint..."
    kubectl run health-check-backend --image=curlimages/curl:latest --rm -i --restart=Never --namespace="$NAMESPACE" -- \
        curl -f http://backend:8000/health || {
        print_error "Backend health check failed"
        exit 1
    }
    
    print_status "Testing frontend availability..."
    kubectl run health-check-frontend --image=curlimages/curl:latest --rm -i --restart=Never --namespace="$NAMESPACE" -- \
        curl -f http://frontend:3000/ || {
        print_error "Frontend health check failed"
        exit 1
    }
    
    print_success "Health checks passed"
}

# Function to setup monitoring
setup_monitoring() {
    print_status "Setting up monitoring..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "DRY RUN: Would setup monitoring"
        return
    fi
    
    # Apply monitoring manifests if they exist
    if [[ -d "monitoring" ]]; then
        kubectl apply -f monitoring/ --namespace="$NAMESPACE" || true
    fi
    
    print_success "Monitoring setup completed"
}

# Function to run database migration
migrate_database() {
    print_status "Running database migration..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "DRY RUN: Would run database migration"
        return
    fi
    
    # Check if migration is needed
    if [[ -n "$MIGRATE_FROM_SQLITE" && "$MIGRATE_FROM_SQLITE" == "true" ]]; then
        print_status "Running SQLite to PostgreSQL migration..."
        
        # Create migration job
        kubectl create job migration-job --image="${DOCKER_REGISTRY}/${PROJECT_NAME}/backend:${TAG:-latest}" \
            --namespace="$NAMESPACE" \
            --dry-run=client -o yaml > migration-job.yaml
        
        # Add migration command to job
        cat >> migration-job.yaml << EOF
        spec:
          template:
            spec:
              containers:
              - name: migration
                command: ["python", "/app/scripts/migrate-to-postgres.py"]
                args: ["--sqlite-path", "/app/data/ga4_admin.db", "--postgres-url", "\$(DATABASE_URL)"]
                envFrom:
                - secretRef:
                    name: app-secrets
              restartPolicy: Never
EOF
        
        kubectl apply -f migration-job.yaml
        kubectl wait --for=condition=complete job/migration-job --namespace="$NAMESPACE" --timeout=600s
        
        print_success "Database migration completed"
        
        # Clean up
        rm -f migration-job.yaml
        kubectl delete job migration-job --namespace="$NAMESPACE"
    else
        print_status "No database migration needed"
    fi
}

# Function to display deployment info
show_deployment_info() {
    print_success "Deployment completed successfully!"
    echo ""
    print_status "Deployment Information:"
    echo "  Environment: ${ENVIRONMENT}"
    echo "  Namespace: ${NAMESPACE}"
    echo "  Tag: ${TAG:-latest}"
    echo ""
    
    if [[ "$DRY_RUN" != "true" ]]; then
        print_status "Service endpoints:"
        kubectl get services --namespace="$NAMESPACE"
        echo ""
        
        print_status "Pod status:"
        kubectl get pods --namespace="$NAMESPACE"
        echo ""
        
        print_status "To access the application:"
        echo "  kubectl port-forward service/frontend 3000:3000 --namespace=${NAMESPACE}"
        echo "  kubectl port-forward service/backend 8000:8000 --namespace=${NAMESPACE}"
    fi
}

# Function to rollback deployment
rollback() {
    print_status "Rolling back deployment..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "DRY RUN: Would rollback deployment"
        return
    fi
    
    kubectl rollout undo deployment/backend --namespace="$NAMESPACE"
    kubectl rollout undo deployment/frontend --namespace="$NAMESPACE"
    
    print_success "Rollback completed"
}

# Main deployment function
deploy() {
    print_status "Starting deployment process..."
    
    check_prerequisites
    build_images
    push_images
    migrate_database
    deploy_k8s
    setup_monitoring
    health_check
    show_deployment_info
}

# Main script
main() {
    case "${1:-deploy}" in
        "deploy")
            deploy
            ;;
        "rollback")
            rollback
            ;;
        "health-check")
            health_check
            ;;
        "build")
            check_prerequisites
            build_images
            ;;
        "push")
            check_prerequisites
            push_images
            ;;
        *)
            echo "Usage: $0 {deploy|rollback|health-check|build|push}"
            echo ""
            echo "Commands:"
            echo "  deploy      - Full deployment (default)"
            echo "  rollback    - Rollback to previous version"
            echo "  health-check - Run health checks only"
            echo "  build       - Build Docker images only"
            echo "  push        - Push Docker images only"
            echo ""
            echo "Environment variables:"
            echo "  ENVIRONMENT - Environment to deploy to (default: production)"
            echo "  TAG         - Docker image tag (default: latest)"
            echo "  DRY_RUN     - Set to 'true' for dry run mode"
            echo "  MIGRATE_FROM_SQLITE - Set to 'true' to run migration"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"