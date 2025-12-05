"""
Quickstart flow: detect project stack, recommend a profile, and initialize aidev.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

import click
from rich.table import Table

from aidev.config import ConfigManager
from aidev.mcp import MCPManager
from aidev.profiles import ProfileManager
from aidev.utils import console, load_json, save_json


@dataclass
class StackDetection:
    """Represents a detected stack signal with a confidence score."""

    name: str
    confidence: float
    reasons: list[str]


@dataclass
class Recommendation:
    """Profile recommendation with rationale."""

    profile: str
    confidence: float
    rationale: str
    tag: str


@dataclass
class QuickstartResult:
    """Outcome of running quickstart."""

    selected_profile: str
    recommended: Recommendation
    detections: list[StackDetection]
    config_path: Path


class QuickstartDetector:
    """Detects project stack characteristics for quickstart."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir

    def detect(self) -> list[StackDetection]:
        """Run all detectors and return sorted stack signals."""
        detections: list[StackDetection] = []
        for detector in (
            self._detect_js,
            self._detect_python,
            self._detect_docker,
            self._detect_k8s,
        ):
            result = detector()
            if result:
                detections.append(result)

        detections.sort(key=lambda d: d.confidence, reverse=True)
        return detections

    def _detect_js(self) -> Optional[StackDetection]:
        """Detect JavaScript/TypeScript projects."""
        reasons: list[str] = []
        confidence = 0.0

        if (self.project_dir / "package.json").exists():
            confidence += 0.6
            reasons.append("Found package.json")
        if (self.project_dir / "tsconfig.json").exists():
            confidence += 0.1
            reasons.append("Found tsconfig.json")
        if list(self.project_dir.glob("*.js")) or list(self.project_dir.glob("src/**/*.js")):
            confidence += 0.1
            reasons.append("JavaScript sources present")
        if list(self.project_dir.glob("*.ts")) or list(self.project_dir.glob("src/**/*.ts")):
            confidence += 0.1
            reasons.append("TypeScript sources present")
        if (self.project_dir / "next.config.js").exists() or (self.project_dir / "next.config.mjs").exists():
            confidence += 0.1
            reasons.append("Found Next.js config")

        confidence = min(confidence, 1.0)
        return StackDetection("javascript", confidence, reasons) if confidence > 0 else None

    def _detect_python(self) -> Optional[StackDetection]:
        """Detect Python projects."""
        reasons: list[str] = []
        confidence = 0.0

        for fname in ("requirements.txt", "pyproject.toml", "Pipfile", "setup.py"):
            if (self.project_dir / fname).exists():
                confidence += 0.5
                reasons.append(f"Found {fname}")
                break

        if list(self.project_dir.glob("*.py")) or list(self.project_dir.glob("src/**/*.py")):
            confidence += 0.2
            reasons.append("Python sources present")

        if (self.project_dir / ".venv").exists() or (self.project_dir / "venv").exists():
            confidence += 0.1
            reasons.append("Virtual environment present")

        confidence = min(confidence, 1.0)
        return StackDetection("python", confidence, reasons) if confidence > 0 else None

    def _detect_docker(self) -> Optional[StackDetection]:
        """Detect Docker usage."""
        reasons: list[str] = []
        confidence = 0.0

        if (self.project_dir / "docker-compose.yml").exists() or (self.project_dir / "docker-compose.yaml").exists():
            confidence += 0.5
            reasons.append("Found docker-compose file")
        if (self.project_dir / "Dockerfile").exists():
            confidence += 0.4
            reasons.append("Found Dockerfile")

        confidence = min(confidence, 1.0)
        return StackDetection("docker", confidence, reasons) if confidence > 0 else None

    def _detect_k8s(self) -> Optional[StackDetection]:
        """Detect Kubernetes manifests."""
        reasons: list[str] = []
        confidence = 0.0

        for dirname in ("k8s", "kubernetes", "manifests", "deploy"):
            if (self.project_dir / dirname).exists():
                confidence += 0.5
                reasons.append(f"Found {dirname}/ directory")
                break

        if list(self.project_dir.glob("*.k8s.yaml")) or list(self.project_dir.glob("*.k8s.yml")):
            confidence += 0.2
            reasons.append("Found *.k8s.yaml manifests")

        confidence = min(confidence, 1.0)
        return StackDetection("kubernetes", confidence, reasons) if confidence > 0 else None


class QuickstartRunner:
    """Coordinates detection, recommendation, and project initialization."""

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        profile_manager: Optional[ProfileManager] = None,
        mcp_manager: Optional[MCPManager] = None,
    ) -> None:
        self.config_manager = config_manager or ConfigManager()
        self.profile_manager = profile_manager or ProfileManager()
        self.mcp_manager = mcp_manager or MCPManager()

    def recommend_profile(self, detections: Sequence[StackDetection]) -> Recommendation:
        """Map detections to a recommended profile family."""
        if not detections:
            fallback = self._fallback_profile()
            return Recommendation(fallback, 0.0, "No stack signals found; using default profile", tag="default")

        scores = {"web": 0.0, "qa": 0.0, "infra": 0.0}
        reasons: dict[str, list[str]] = {"web": [], "qa": [], "infra": []}

        for detection in detections:
            if detection.name in ("javascript", "typescript"):
                scores["web"] = max(scores["web"], detection.confidence)
                reasons["web"].extend(detection.reasons)
            if detection.name == "python":
                scores["qa"] = max(scores["qa"], detection.confidence)
                reasons["qa"].extend(detection.reasons)
            if detection.name in ("docker", "kubernetes"):
                scores["infra"] = max(scores["infra"], detection.confidence)
                reasons["infra"].extend(detection.reasons)

        best_profile = max(scores.items(), key=lambda item: item[1])[0]
        confidence = scores[best_profile]
        rationale_reasons = reasons[best_profile] or ["Detected multiple stacks"]
        rationale = "; ".join(rationale_reasons)

        selected_profile = self._find_profile_for_tag(best_profile) or self._fallback_profile()

        return Recommendation(selected_profile, confidence, rationale, tag=best_profile)

    def run(
        self,
        project_dir: Optional[Path] = None,
        profile_override: Optional[str] = None,
        auto_confirm: bool = False,
    ) -> QuickstartResult:
        """Execute the quickstart flow."""
        project_dir = project_dir or Path.cwd()
        detector = QuickstartDetector(project_dir)

        console.rule("[bold cyan]aidev quickstart[/bold cyan]")
        console.print(f"[cyan]Project:[/cyan] {project_dir}")

        # Ensure global setup exists
        self.config_manager.init_directories()
        self.profile_manager.init_builtin_profiles()
        self.mcp_manager.init_builtin_servers()

        # Detect existing project profile, if any
        existing_config_dir = self.config_manager.get_project_config_path(project_dir)
        existing_profile: Optional[str] = None
        if existing_config_dir:
            profile_file = existing_config_dir / "profile"
            if profile_file.exists():
                existing_profile = profile_file.read_text().strip()

        detections = detector.detect()
        self._print_detections(detections)

        recommendation = self.recommend_profile(detections)
        available_profiles = self.profile_manager.list_profiles()

        default_choice = profile_override or existing_profile or recommendation.profile or self._fallback_profile()

        selected_profile = self._select_profile(
            available_profiles=available_profiles,
            default_choice=default_choice,
            recommendation=recommendation,
            auto_confirm=auto_confirm or bool(profile_override),
            existing_profile=existing_profile,
        )

        config_path = self.config_manager.init_project(project_dir=project_dir, profile=selected_profile)
        self._ensure_profile_written(config_path, selected_profile)

        console.print(f"[green]✓[/green] Initialized at {config_path}")
        console.print(
            f"Using profile [bold]{selected_profile}[/bold] "
            f"({'auto' if auto_confirm or profile_override else 'confirmed'})"
        )

        return QuickstartResult(
            selected_profile=selected_profile,
            recommended=recommendation,
            detections=detections,
            config_path=config_path,
        )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _print_detections(self, detections: Sequence[StackDetection]) -> None:
        """Render detection results to the console."""
        if not detections:
            console.print("[yellow]No stack signals detected. Using defaults.[/yellow]")
            return

        table = Table(title="Detected Stack", show_header=True, header_style="bold cyan")
        table.add_column("Stack")
        table.add_column("Confidence")
        table.add_column("Signals")

        for detection in detections:
            confidence_pct = f"{int(detection.confidence * 100)}%"
            reasons = "; ".join(detection.reasons) if detection.reasons else "-"
            table.add_row(detection.name, confidence_pct, reasons)

        console.print(table)

    def _select_profile(
        self,
        available_profiles: Sequence[str],
        default_choice: str,
        recommendation: Recommendation,
        auto_confirm: bool,
        existing_profile: Optional[str],
    ) -> str:
        """Handle user choice of profile."""
        if not available_profiles:
            console.print("[red]No profiles available. Run `ai setup` first.[/red]")
            return default_choice

        if auto_confirm:
            console.print(
                f"[cyan]Auto-selecting profile:[/cyan] {default_choice} "
                f"(recommended: {recommendation.profile}, reason: {recommendation.rationale})"
            )
            return default_choice

        console.print(
            f"Recommended profile: [bold]{recommendation.profile}[/bold] "
            f"({int(recommendation.confidence * 100)}%) - {recommendation.rationale}"
        )
        if existing_profile:
            console.print(f"Existing profile detected: [bold]{existing_profile}[/bold]")

        if click.confirm(f"Use '{default_choice}'?", default=True):
            return default_choice

        return click.prompt(
            "Choose a profile",
            type=click.Choice(list(available_profiles)),
            default=default_choice if default_choice in available_profiles else available_profiles[0],
        )

    def _ensure_profile_written(self, config_path: Path, selected_profile: str) -> None:
        """Write/update project profile and config."""
        profile_file = config_path / "profile"
        profile_file.write_text(selected_profile)

        config_file = config_path / "config.json"
        config_data = load_json(config_file, default={"profile": selected_profile, "environment": {}, "mcp_overrides": {}})
        if config_data.get("profile") != selected_profile:
            config_data["profile"] = selected_profile
        save_json(config_file, config_data)

    def _find_profile_for_tag(self, tag: str) -> Optional[str]:
        """Pick the first available profile that contains the given tag."""
        for name in self.profile_manager.list_profiles():
            profile = self.profile_manager.load_profile(name)
            if not profile:
                continue
            if tag in profile.tags:
                return name
        return None

    def _fallback_profile(self) -> str:
        """Prefer default profile when available, otherwise first available."""
        available = self.profile_manager.list_profiles()
        if "default" in available:
            return "default"
        return available[0] if available else "default"
