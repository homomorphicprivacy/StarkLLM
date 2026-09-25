package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

type OllamaTagsResponse struct {
	Models []struct {
		Name  string `json:"name"`
		Model string `json:"model"`
	} `json:"models"`
}

type PreflightReport struct {
	Timestamp       string   `json:"timestamp"`
	WorkingDir      string   `json:"working_dir"`
	OS              string   `json:"os"`
	DockerRunning   bool     `json:"docker_running"`
	DockerKernel    string   `json:"docker_kernel"`
	OllamaReachable bool     `json:"ollama_reachable"`
	OllamaModels    []string `json:"ollama_models"`
	HasChatModel    bool     `json:"has_chat_model"`
	HasEmbedModel   bool     `json:"has_embed_model"`
	Port8000Free    bool     `json:"port_8000_free"`
	Port5173Free    bool     `json:"port_5173_free"`
	Errors          []string `json:"errors"`
	Warnings        []string `json:"warnings"`
}

func main() {
	fmt.Println("==================================================")
	fmt.Println("             StarkLLM Windows Launcher            ")
	fmt.Println("          Windows Research Beta — Phase 1         ")
	fmt.Println("==================================================")
	fmt.Println()

	exePath, err := os.Executable()
	if err != nil {
		fmt.Printf("[ERROR] Unable to determine launcher location: %v\n", err)
		pauseAndExit(1)
	}
	exeDir := filepath.Dir(exePath)
	_ = os.Chdir(exeDir)

	isPreflightOnly := false
	for _, arg := range os.Args[1:] {
		if arg == "--preflight" || arg == "-check" || arg == "--check" || arg == "/check" {
			isPreflightOnly = true
		}
	}

	report := PreflightReport{
		Timestamp:  time.Now().Format("2006-01-02 15:04:05 MST"),
		WorkingDir: exeDir,
		OS:         fmt.Sprintf("%s/%s", runtime.GOOS, runtime.GOARCH),
		Errors:     []string{},
		Warnings:   []string{},
	}

	// 1. Verify workspace files
	if _, err := os.Stat("docker-compose.yml"); os.IsNotExist(err) {
		msg := fmt.Sprintf("docker-compose.yml not found in current directory: %s", exeDir)
		report.Errors = append(report.Errors, msg)
		fmt.Println("[ERROR] docker-compose.yml not found in current directory:")
		fmt.Printf("        %s\n", exeDir)
		fmt.Println("Please make sure all extracted files are in the same folder.")
		writePreflightReport(report)
		pauseAndExit(1)
	}

	// 2. Check Docker Desktop & WSL2
	fmt.Println("[1/5] Checking Docker Desktop & WSL2 status...")
	dockerInfoOut, dockerErr := exec.Command("docker", "info").CombinedOutput()
	if dockerErr != nil {
		msg := "Docker Desktop is not running or not responsive."
		report.Errors = append(report.Errors, msg)
		fmt.Println()
		fmt.Println("[ERROR] Docker Desktop is not running or not responsive.")
		fmt.Println("        Remediation steps:")
		fmt.Println("        1. Open Docker Desktop from the Start Menu.")
		fmt.Println("        2. Wait until the whale icon in the Windows taskbar is steady.")
		fmt.Println("        3. Ensure WSL2 integration is enabled (Docker Settings -> General).")
		fmt.Println("        Download Docker: https://www.docker.com/products/docker-desktop/")
		fmt.Println()
		writePreflightReport(report)
		pauseAndExit(1)
	}
	report.DockerRunning = true
	// Parse kernel/WSL2 info from docker info
	dockerInfoStr := string(dockerInfoOut)
	for _, line := range strings.Split(dockerInfoStr, "\n") {
		if strings.Contains(line, "Kernel Version:") {
			report.DockerKernel = strings.TrimSpace(strings.TrimPrefix(line, " Kernel Version:"))
			break
		}
	}
	fmt.Printf("  -> Docker is running (Kernel: %s).\n", report.DockerKernel)

	// 3. Clean previous containers first to release local ports
	fmt.Println("[2/5] Cleaning previous StarkLLM containers...")
	_ = exec.Command("docker", "rm", "-f", "starkllm-backend", "starkllm-frontend").Run()
	_ = exec.Command("docker", "compose", "down", "--remove-orphans").Run()
	fmt.Println("  -> Container cleanup complete.")

	// 4. Check Port Availability (8000 and 5173)
	fmt.Println("[3/5] Verifying local network ports (8000, 5173)...")
	port8000Free := isPortAvailable(8000)
	port5173Free := isPortAvailable(5173)
	report.Port8000Free = port8000Free
	report.Port5173Free = port5173Free

	if !port8000Free {
		msg := "Port 8000 is occupied by another application. StarkLLM Backend cannot bind."
		report.Errors = append(report.Errors, msg)
		fmt.Println()
		fmt.Println("[ERROR] Port 8000 is already in use by another application on your system.")
		fmt.Println("        Please close the process using port 8000, or change BACKEND_PORT in .env.")
		writePreflightReport(report)
		pauseAndExit(1)
	}
	if !port5173Free {
		msg := "Port 5173 is occupied by another application. StarkLLM Frontend cannot bind."
		report.Errors = append(report.Errors, msg)
		fmt.Println()
		fmt.Println("[ERROR] Port 5173 is already in use by another application on your system.")
		fmt.Println("        Please close the process using port 5173, or change FRONTEND_PORT in .env.")
		writePreflightReport(report)
		pauseAndExit(1)
	}
	fmt.Println("  -> Ports 8000 (Backend) and 5173 (Frontend) are available.")

	// 5. Check Ollama local service & models
	fmt.Println("[4/5] Checking Ollama service and configured models...")
	configuredTextModel, configuredEmbedModel := loadConfiguredModels()
	fmt.Printf("  -> Configured models: chat='%s', embed='%s'\n", configuredTextModel, configuredEmbedModel)

	ollamaTags, ollamaErr := queryOllamaTags()
	if ollamaErr != nil {
		report.OllamaReachable = false
		msg := "Ollama service is not running or unreachable on http://localhost:11434"
		report.Errors = append(report.Errors, msg)
		fmt.Println()
		fmt.Println("[ERROR] Ollama is not running or unreachable on http://localhost:11434.")
		fmt.Println("        StarkLLM requires Ollama for local LLM inference and embeddings.")
		fmt.Println("        1. Download and start Ollama from https://ollama.com")
		fmt.Println("        2. Pull the configured models:")
		fmt.Printf("             ollama pull %s\n", configuredTextModel)
		fmt.Printf("             ollama pull %s\n", configuredEmbedModel)
		fmt.Println()
		writePreflightReport(report)
		pauseAndExit(1)
	}

	report.OllamaReachable = true
	var missingModels []string
	for _, m := range ollamaTags.Models {
		report.OllamaModels = append(report.OllamaModels, m.Name)
		if modelMatches(m.Name, configuredTextModel) {
			report.HasChatModel = true
		}
		if modelMatches(m.Name, configuredEmbedModel) {
			report.HasEmbedModel = true
		}
	}
	fmt.Printf("  -> Ollama detected with %d model(s) installed.\n", len(report.OllamaModels))

	if !report.HasChatModel {
		missingModels = append(missingModels, configuredTextModel)
		report.Errors = append(report.Errors, fmt.Sprintf("Configured chat model '%s' is missing in Ollama", configuredTextModel))
	}
	if !report.HasEmbedModel {
		missingModels = append(missingModels, configuredEmbedModel)
		report.Errors = append(report.Errors, fmt.Sprintf("Configured embedding model '%s' is missing in Ollama", configuredEmbedModel))
	}

	if len(missingModels) > 0 {
		fmt.Println()
		fmt.Println("[ERROR] Required Ollama model(s) are missing!")
		fmt.Println("        StarkLLM requires the configured models from .env before starting.")
		fmt.Println("        Please open a terminal and run:")
		for _, m := range missingModels {
			fmt.Printf("          ollama pull %s\n", m)
		}
		fmt.Println()
		writePreflightReport(report)
		pauseAndExit(1)
	}
	fmt.Println("  -> Both required models are verified in Ollama.")

	// Write preflight report to disk for diagnostics
	writePreflightReport(report)

	if isPreflightOnly {
		fmt.Println()
		fmt.Println("==================================================")
		fmt.Println(" Preflight diagnostics complete!")
		fmt.Println(" Report written to: preflight_report.txt")
		fmt.Println("==================================================")
		if len(report.Errors) > 0 {
			os.Exit(1)
		}
		os.Exit(0)
	}

	// 6. Start Docker Compose
	fmt.Println()
	fmt.Println("[5/5] Building and launching StarkLLM containers...")
	composeCmd := exec.Command("docker", "compose", "up", "--build", "-d")
	composeCmd.Stdout = os.Stdout
	composeCmd.Stderr = os.Stderr
	if err := composeCmd.Run(); err != nil {
		fmt.Println()
		fmt.Printf("[ERROR] Failed to start Docker containers: %v\n", err)
		fmt.Println("See 'preflight_report.txt' in this directory for diagnostic details.")
		pauseAndExit(1)
	}

	// 7. Health Polling
	fmt.Println()
	fmt.Println("Waiting for backend API to become ready (http://localhost:8000/health)...")
	fmt.Println("(First launch can take 1-2 minutes while Python environment initializes)")
	fmt.Println()

	if waitForBackend("http://localhost:8000/health", 90) {
		fmt.Println("  -> Backend is healthy and ready!")
	} else {
		fmt.Println("  [WARNING] Backend health poll timed out after 90 seconds.")
		fmt.Println("            The container may still be initializing. Opening browser anyway...")
	}

	fmt.Println()
	fmt.Println("Opening StarkLLM Dashboard (http://localhost:5173)...")
	openBrowser("http://localhost:5173")

	fmt.Println()
	fmt.Println("==================================================")
	fmt.Println(" StarkLLM is running at http://localhost:5173")
	fmt.Println(" Diagnostic report saved: preflight_report.txt")
	fmt.Println("==================================================")
	fmt.Println()
	pauseAndExit(0)
}

func isPortAvailable(port int) bool {
	ln, err := net.Listen("tcp", fmt.Sprintf("127.0.0.1:%d", port))
	if err != nil {
		return false
	}
	_ = ln.Close()
	return true
}

func loadConfiguredModels() (string, string) {
	textModel := "qwen3.8:27b"
	embedModel := "qwen3-embedding:0.6b"

	file, err := os.Open(".env")
	if err != nil {
		return textModel, embedModel
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if strings.HasPrefix(line, "#") || !strings.Contains(line, "=") {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		key := strings.TrimSpace(parts[0])
		val := strings.TrimSpace(parts[1])
		if idx := strings.Index(val, "#"); idx != -1 {
			val = strings.TrimSpace(val[:idx])
		}
		val = strings.Trim(val, "\"'")

		if key == "DEFAULT_TEXT_MODEL" && val != "" {
			textModel = val
		} else if key == "DEFAULT_EMBEDDING_MODEL" && val != "" {
			embedModel = val
		}
	}
	return textModel, embedModel
}

func modelMatches(actualName, targetName string) bool {
	act := strings.ToLower(strings.TrimSpace(actualName))
	tgt := strings.ToLower(strings.TrimSpace(targetName))
	if act == tgt || act == tgt+":latest" {
		return true
	}
	if strings.HasPrefix(act, tgt+":") {
		return true
	}
	return false
}

func queryOllamaTags() (*OllamaTagsResponse, error) {
	client := http.Client{Timeout: 3 * time.Second}
	resp, err := client.Get("http://localhost:11434/api/tags")
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("ollama returned status %d", resp.StatusCode)
	}

	var tags OllamaTagsResponse
	if err := json.NewDecoder(resp.Body).Decode(&tags); err != nil {
		return nil, err
	}
	return &tags, nil
}

func waitForBackend(url string, maxSeconds int) bool {
	client := http.Client{Timeout: 2 * time.Second}
	for i := 1; i <= maxSeconds; i++ {
		resp, err := client.Get(url)
		if err == nil {
			resp.Body.Close()
			if resp.StatusCode == 200 {
				return true
			}
		}
		if i%5 == 0 || i <= 5 {
			fmt.Printf("  Waiting for backend... [%d/%d]\n", i, maxSeconds)
		}
		time.Sleep(1 * time.Second)
	}
	return false
}

func writePreflightReport(r PreflightReport) {
	lines := []string{
		"==================================================",
		"          StarkLLM Preflight Diagnostic Report     ",
		"==================================================",
		fmt.Sprintf("Timestamp:       %s", r.Timestamp),
		fmt.Sprintf("Working Dir:     %s", r.WorkingDir),
		fmt.Sprintf("OS / Platform:   %s", r.OS),
		fmt.Sprintf("Docker Running:  %t", r.DockerRunning),
		fmt.Sprintf("Docker Kernel:   %s", r.DockerKernel),
		fmt.Sprintf("Ollama Reachable:%t", r.OllamaReachable),
		fmt.Sprintf("Port 8000 Free:  %t", r.Port8000Free),
		fmt.Sprintf("Port 5173 Free:  %t", r.Port5173Free),
		"",
		"Ollama Detected Models:",
	}
	if len(r.OllamaModels) == 0 {
		lines = append(lines, "  (None detected or Ollama unreachable)")
	} else {
		for _, m := range r.OllamaModels {
			lines = append(lines, fmt.Sprintf("  - %s", m))
		}
	}
	lines = append(lines, "")
	if len(r.Errors) > 0 {
		lines = append(lines, "Errors:")
		for _, e := range r.Errors {
			lines = append(lines, fmt.Sprintf("  [!] %s", e))
		}
		lines = append(lines, "")
	}
	if len(r.Warnings) > 0 {
		lines = append(lines, "Warnings:")
		for _, w := range r.Warnings {
			lines = append(lines, fmt.Sprintf("  [*] %s", w))
		}
		lines = append(lines, "")
	}
	lines = append(lines, "==================================================")
	content := strings.Join(lines, "\r\n")
	_ = os.WriteFile("preflight_report.txt", []byte(content), 0644)
}

func openBrowser(url string) {
	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "windows":
		cmd = exec.Command("rundll32", "url.dll,FileProtocolHandler", url)
	case "darwin":
		cmd = exec.Command("open", url)
	default:
		cmd = exec.Command("xdg-open", url)
	}
	_ = cmd.Start()
}

func pauseAndExit(code int) {
	fmt.Println()
	fmt.Println("Press Enter to exit...")
	reader := bufio.NewReader(os.Stdin)
	_, _ = reader.ReadString('\n')
	os.Exit(code)
}
