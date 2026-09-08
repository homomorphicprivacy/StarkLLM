package main

import (
	"bufio"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"time"
)

func main() {
	fmt.Println("==================================================")
	fmt.Println("             StarkLLM Windows Launcher            ")
	fmt.Println("==================================================")
	fmt.Println()

	exePath, err := os.Executable()
	if err != nil {
		fmt.Printf("[ERROR] Unable to determine launcher location: %v\n", err)
		pauseAndExit(1)
	}
	exeDir := filepath.Dir(exePath)
	_ = os.Chdir(exeDir)

	if _, err := os.Stat("docker-compose.yml"); os.IsNotExist(err) {
		fmt.Println("[ERROR] docker-compose.yml not found in current directory:")
		fmt.Printf("        %s\n", exeDir)
		fmt.Println("Please make sure all extracted files are in the same folder.")
		pauseAndExit(1)
	}

	fmt.Println("[1/4] Checking Docker status...")
	dockerCmd := exec.Command("docker", "info")
	if err := dockerCmd.Run(); err != nil {
		fmt.Println()
		fmt.Println("[ERROR] Docker Desktop is not running or not installed.")
		fmt.Println("        Please install Docker Desktop and start it before launching StarkLLM.")
		fmt.Println("        Download: https://www.docker.com/products/docker-desktop/")
		fmt.Println()
		pauseAndExit(1)
	}
	fmt.Println("  -> Docker is running.")

	fmt.Println("[2/4] Checking Ollama local service...")
	ollamaOk := checkOllama()
	if !ollamaOk {
		fmt.Println()
		fmt.Println("[WARNING] Ollama is not running or unreachable on http://localhost:11434.")
		fmt.Println("          StarkLLM requires Ollama for local LLM inference and embeddings.")
		fmt.Println("          Prerequisite models: qwen3.8:27b, qwen3-embedding:0.6b")
		fmt.Println("          Please ensure Ollama is installed and running.")
		fmt.Println()
	} else {
		fmt.Println("  -> Ollama service detected.")
	}

	fmt.Println("[3/4] Cleaning previous containers and starting StarkLLM...")
	_ = exec.Command("docker", "rm", "-f", "starkllm-backend", "starkllm-frontend").Run()
	_ = exec.Command("docker", "compose", "down", "--remove-orphans").Run()
	composeCmd := exec.Command("docker", "compose", "up", "--build", "-d")
	composeCmd.Stdout = os.Stdout
	composeCmd.Stderr = os.Stderr
	if err := composeCmd.Run(); err != nil {
		fmt.Println()
		fmt.Printf("[ERROR] Failed to start Docker containers: %v\n", err)
		pauseAndExit(1)
	}

	fmt.Println("[4/4] Opening StarkLLM Dashboard (http://localhost:5173)...")
	time.Sleep(2 * time.Second)
	openBrowser("http://localhost:5173")

	fmt.Println()
	fmt.Println("==================================================")
	fmt.Println(" StarkLLM is running at http://localhost:5173")
	fmt.Println("==================================================")
	fmt.Println()
	pauseAndExit(0)
}

func checkOllama() bool {
	client := http.Client{Timeout: 2 * time.Second}
	resp, err := client.Get("http://localhost:11434/api/tags")
	if err != nil {
		return false
	}
	defer resp.Body.Close()
	return resp.StatusCode == 200
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
	fmt.Println("Press Enter to exit...")
	reader := bufio.NewReader(os.Stdin)
	_, _ = reader.ReadString('\n')
	os.Exit(code)
}
