#!/bin/bash
# ============================================================
# CineBook - Docker Build & Push Script
# DockerHub Username: kastrov
# Usage: bash build-push.sh [service_name | all]
# ============================================================

set -e

DOCKERHUB_USER="kastrov"
VERSION="${VERSION:-latest}"
SERVICES=("frontend" "auth-service" "movie-service" "booking-service" "payment-service")
IMAGE_NAMES=("cinebook-frontend" "cinebook-auth" "cinebook-movie" "cinebook-booking" "cinebook-payment")

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'; BOLD='\033[1m'

log()     { echo -e "${CYAN}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC}   $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

banner() {
echo -e "${BOLD}${CYAN}"
cat << 'BANNER'
  _____ _            ____              _
 / ____(_)          |  _ \            | |
| |     _ _ __   ___| |_) | ___   ___ | | __
| |    | | '_ \ / _ \  _ < / _ \ / _ \| |/ /
| |____| | | | |  __/ |_) | (_) | (_) |   <
 \_____|_|_| |_|\___|____/ \___/ \___/|_|\_\
BANNER
echo -e "${NC}"
}

build_and_push() {
    local service=$1
    local image_name=$2
    local full_tag="${DOCKERHUB_USER}/${image_name}:${VERSION}"

    log "Building ${BOLD}${full_tag}${NC} ..."
    if docker build -t "${full_tag}" "./${service}/"; then
        success "Built ${full_tag}"
    else
        error "Build failed for ${service}"
    fi

    log "Pushing ${full_tag} to DockerHub..."
    if docker push "${full_tag}"; then
        success "Pushed ${full_tag}"
    else
        error "Push failed for ${service}"
    fi

    # Also tag and push as versioned if VERSION != latest
    if [ "${VERSION}" != "latest" ]; then
        local latest_tag="${DOCKERHUB_USER}/${image_name}:latest"
        docker tag "${full_tag}" "${latest_tag}"
        docker push "${latest_tag}"
        success "Also pushed as latest: ${latest_tag}"
    fi
}

build_all() {
    banner
    log "Logging into DockerHub as ${DOCKERHUB_USER}..."
    docker login -u "${DOCKERHUB_USER}" || error "Docker login failed"

    echo ""
    log "Starting build & push for ALL services (version: ${VERSION})"
    echo "─────────────────────────────────────────────────────"

    for i in "${!SERVICES[@]}"; do
        echo ""
        echo -e "${BOLD}[$(( i + 1 ))/${#SERVICES[@]}] ${SERVICES[$i]}${NC}"
        build_and_push "${SERVICES[$i]}" "${IMAGE_NAMES[$i]}"
    done

    echo ""
    echo "─────────────────────────────────────────────────────"
    success "All images built and pushed successfully!"
    echo ""
    echo -e "${BOLD}Images available on DockerHub:${NC}"
    for i in "${!IMAGE_NAMES[@]}"; do
        echo -e "  ${GREEN}✔${NC} ${DOCKERHUB_USER}/${IMAGE_NAMES[$i]}:${VERSION}"
    done
}

build_single() {
    local target=$1
    for i in "${!SERVICES[@]}"; do
        if [ "${SERVICES[$i]}" == "${target}" ]; then
            docker login -u "${DOCKERHUB_USER}" || error "Docker login failed"
            build_and_push "${SERVICES[$i]}" "${IMAGE_NAMES[$i]}"
            return
        fi
    done
    error "Unknown service: ${target}. Valid: ${SERVICES[*]}"
}

# ── Main ──────────────────────────────────────
case "${1:-all}" in
    all)           build_all ;;
    frontend)      build_single "frontend" ;;
    auth-service)  build_single "auth-service" ;;
    movie-service) build_single "movie-service" ;;
    booking-service) build_single "booking-service" ;;
    payment-service) build_single "payment-service" ;;
    *)             error "Unknown argument: $1. Use: all | frontend | auth-service | movie-service | booking-service | payment-service" ;;
esac
