# Makefile
REGISTRY ?= jperdek
TAG ?= latest
SERVICES = nao-robot-api skeleton-finder-api copied-volumes-robotics

.PHONY: help build build-all push check-images dev-up dev-down dev-logs clean test status
.PHONY: k8s-deploy k8s-delete k8s-logs k8s-status k8s-get-urls k8s-restart

help:
	@echo "=== Docker Compose Management (Development) ==="
	@echo "  make build-all      # Build all Docker images"
	@echo "  make build-<name>   # Build specific image (e.g., nao-robot-api)"
	@echo "  make push-all       # Push all images to registry"
	@echo "  make check-images   # Check which images exist locally"
	@echo "  make dev-up         # Start development environment"
	@echo "  make dev-down       # Stop development environment"
	@echo "  make dev-logs       # Show logs from running services"
	@echo "  make test           # Test if services are responding"
	@echo "  make status         # Show container status"
	@echo "  make clean          # Stop services and clean images"
	@echo ""
	@echo "=== Kubernetes Management (Production) ==="
	@echo "  make k8s-deploy     # Deploy to Kubernetes"
	@echo "  make k8s-delete     # Remove from Kubernetes"
	@echo "  make k8s-logs       # Show Kubernetes logs"
	@echo "  make k8s-status     # Show Kubernetes status"
	@echo "  make k8s-get-urls   # Get service URLs"
	@echo "  make k8s-restart    # Restart Kubernetes deployments"

# Image management
build-all:
	@echo "Building all Docker images..."
	docker-compose -f docker-compose.build.yml build

build-%:
	@echo "Building $*..."
	docker-compose -f docker-compose.build.yml build $*

push-all:
	@echo "Pushing images to registry..."
	@for service in $(SERVICES); do \
		echo "Pushing $(REGISTRY)/$$service:$(TAG)"; \
		docker push $(REGISTRY)/$$service:$(TAG) || echo "Failed to push $$service"; \
	done

check-images:
	@echo "Checking local images..."
	@for service in $(SERVICES); do \
		if docker image inspect $(REGISTRY)/$$service:$(TAG) >/dev/null 2>&1; then \
			echo "✓ $$service:$(TAG)"; \
		else \
			echo "✗ $$service:$(TAG) - not found"; \
		fi \
	done

# Development environment (Docker Compose)
dev-up: build-all
	@echo "Starting development environment..."
	docker-compose -f docker-compose.dev.yml up -d
	@echo "Services should be available at:"
	@echo "  - naoRobotAPI: http://localhost:5000"
	@echo "  - skeletonFinderAPI: http://localhost:6001"

dev-down:
	@echo "Stopping development environment..."
	docker-compose -f docker-compose.dev.yml down

dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

dev-restart: dev-down dev-up

# Testing
test:
	@echo "Testing services..."
	@echo "Testing naoRobotAPI (port 5000)..."
	@curl -f http://localhost:5000/ >/dev/null 2>&1 && echo "✓ naoRobotAPI is responding" || echo "✗ naoRobotAPI not responding"
	@echo "Testing skeletonFinderAPI (port 6001)..."
	@curl -f http://localhost:6001/ >/dev/null 2>&1 && echo "✓ skeletonFinderAPI is responding" || echo "✗ skeletonFinderAPI not responding"

# Cleanup
clean:
	@echo "Cleaning up..."
	docker-compose -f docker-compose.dev.yml down -v
	@for service in $(SERVICES); do \
		echo "Removing image $(REGISTRY)/$$service:$(TAG)"; \
		docker rmi $(REGISTRY)/$$service:$(TAG) 2>/dev/null || true; \
	done
	@echo "Cleanup complete!"

# Status
status:
	@echo "=== Running Containers ==="
	@docker-compose -f docker-compose.dev.yml ps

# Kubernetes Commands
k8s-deploy: build-all
	@echo "Deploying to Kubernetes..."
	kubectl apply -f k8s/
	@echo "Waiting for services to start..."
	@echo "Waiting for naoRobotAPI..."
	@kubectl wait --for=condition=ready pod -l app=naorobotapi --timeout=120s 2>/dev/null && echo "✓ naoRobotAPI ready" || echo "⚠ naoRobotAPI taking longer to start"
	@echo "Waiting for skeletonFinderAPI..."
	@kubectl wait --for=condition=ready pod -l app=skeletonfinderapi --timeout=120s 2>/dev/null && echo "✓ skeletonFinderAPI ready" || echo "⚠ skeletonFinderAPI taking longer to start"
	@echo "Deployment complete!"
	@make k8s-get-urls

k8s-delete:
	@echo "Removing from Kubernetes..."
	kubectl delete -f k8s/ --ignore-not-found=true
	@echo "Kubernetes resources removed"

k8s-logs:
	@echo "=== naoRobotAPI logs ==="
	@kubectl logs -l app=naorobotapi --tail=50 --prefix=true 2>/dev/null || echo "No naoRobotAPI logs found"
	@echo ""
	@echo "=== skeletonFinderAPI logs ==="
	@kubectl logs -l app=skeletonfinderapi --tail=50 --prefix=true 2>/dev/null || echo "No skeletonFinderAPI logs found"

k8s-status:
	@echo "=== Kubernetes Cluster Status ==="
	@echo "Nodes:"
	@kubectl get nodes 2>/dev/null || echo "Kubernetes not available"
	@echo ""
	@echo "=== Deployments ==="
	@kubectl get deployments 2>/dev/null || echo "No deployments found"
	@echo ""
	@echo "=== Services ==="
	@kubectl get services 2>/dev/null || echo "No services found"
	@echo ""
	@echo "=== Pods ==="
	@kubectl get pods -o wide 2>/dev/null || echo "No pods found"

k8s-get-urls:
	@echo "=== Service URLs ==="
	@echo "Note: Run 'minikube service list' if using Minikube for exact URLs"
	@echo "Or check with: kubectl get services"
	@kubectl get services -o wide 2>/dev/null || echo "Kubernetes not available"

k8s-restart:
	@echo "Restarting Kubernetes deployments..."
	@kubectl rollout restart deployment naorobotapi-deployment 2>/dev/null || echo "naorobotapi-deployment not found"
	@kubectl rollout restart deployment skeletonfinderapi-deployment 2>/dev/null || echo "skeletonfinderapi-deployment not found"
	@echo "Restart complete. Use 'make k8s-status' to check status"