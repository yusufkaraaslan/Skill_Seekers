#!/bin/bash
# Integration Test Runner with Docker Infrastructure
# Manages vector database services and runs integration tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

COMPOSE_FILE="tests/docker-compose.test.yml"

function print_header() {
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║     Skill Seekers Integration Test Runner                ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

function check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker not found${NC}"
        echo "Please install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}Error: docker-compose not found${NC}"
        echo "Please install docker-compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
}

function start_services() {
    echo -e "${BLUE}Starting test infrastructure...${NC}"
    echo ""

    # Use either docker-compose or docker compose
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" up -d
    else
        docker compose -f "$COMPOSE_FILE" up -d
    fi

    echo ""
    echo -e "${YELLOW}Waiting for services to be ready...${NC}"
    sleep 5

    # Check service health
    local all_healthy=true

    echo -n "Weaviate... "
    if curl -s http://localhost:8080/v1/.well-known/ready > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        all_healthy=false
    fi

    echo -n "Qdrant... "
    if curl -s http://localhost:6333/ > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        all_healthy=false
    fi

    echo -n "ChromaDB... "
    if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        all_healthy=false
    fi

    echo ""

    if [ "$all_healthy" = false ]; then
        echo -e "${YELLOW}Warning: Some services may not be ready yet${NC}"
        echo -e "${YELLOW}Waiting an additional 10 seconds...${NC}"
        sleep 10
    fi
}

function stop_services() {
    echo -e "${BLUE}Stopping test infrastructure...${NC}"

    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" down -v
    else
        docker compose -f "$COMPOSE_FILE" down -v
    fi

    echo -e "${GREEN}✓ Services stopped${NC}"
}

function run_tests() {
    echo -e "${BLUE}Running integration tests...${NC}"
    echo ""

    # Install required packages if missing
    local missing_packages=()

    if ! python -c "import weaviate" 2>/dev/null; then
        missing_packages+=("weaviate-client")
    fi

    if ! python -c "import chromadb" 2>/dev/null; then
        missing_packages+=("chromadb")
    fi

    if ! python -c "import qdrant_client" 2>/dev/null; then
        missing_packages+=("qdrant-client")
    fi

    if [ ${#missing_packages[@]} -gt 0 ]; then
        echo -e "${YELLOW}Installing missing packages: ${missing_packages[*]}${NC}"
        pip install "${missing_packages[@]}" > /dev/null 2>&1
        echo -e "${GREEN}✓ Packages installed${NC}"
        echo ""
    fi

    # Run tests
    if pytest tests/test_integration_adaptors.py -v -m integration --tb=short; then
        echo ""
        echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║     All Integration Tests Passed ✓                        ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
        return 0
    else
        echo ""
        echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║     Some Integration Tests Failed ✗                       ║${NC}"
        echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
        return 1
    fi
}

function show_logs() {
    echo -e "${BLUE}Showing service logs...${NC}"
    echo ""

    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" logs --tail=50
    else
        docker compose -f "$COMPOSE_FILE" logs --tail=50
    fi
}

function show_status() {
    echo -e "${BLUE}Service status:${NC}"
    echo ""

    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" ps
    else
        docker compose -f "$COMPOSE_FILE" ps
    fi
}

function show_help() {
    echo "Integration Test Runner"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start     Start vector database services"
    echo "  stop      Stop and clean up services"
    echo "  test      Run integration tests"
    echo "  run       Start services + run tests + stop services (default)"
    echo "  logs      Show service logs"
    echo "  status    Show service status"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0              # Run complete workflow"
    echo "  $0 start        # Just start services"
    echo "  $0 test         # Run tests (services must be running)"
    echo "  $0 stop         # Stop all services"
}

# Main script
print_header
check_docker

# Parse command
COMMAND="${1:-run}"

case "$COMMAND" in
    start)
        start_services
        echo ""
        echo -e "${GREEN}Services started successfully!${NC}"
        echo "Run tests with: $0 test"
        ;;

    stop)
        stop_services
        ;;

    test)
        run_tests
        ;;

    run)
        echo -e "${CYAN}Running complete workflow:${NC}"
        echo "1. Start services"
        echo "2. Run tests"
        echo "3. Stop services"
        echo ""

        start_services
        echo ""

        if run_tests; then
            TEST_RESULT=0
        else
            TEST_RESULT=1
        fi

        echo ""
        stop_services
        exit $TEST_RESULT
        ;;

    logs)
        show_logs
        ;;

    status)
        show_status
        ;;

    help|--help|-h)
        show_help
        ;;

    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
