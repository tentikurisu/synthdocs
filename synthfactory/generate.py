from __future__ import annotations
import argparse
from pathlib import Path
from .config import load_config
from .pipeline import generate_dataset


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic documents")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--count", type=int, help="Number of documents to generate")
    parser.add_argument("--prompt", default="", help="Prompt for document generation")
    args = parser.parse_args()

    cfg = load_config(Path(args.config))

    count = args.count if args.count else int(cfg.dataset.count)
    prompt = args.prompt if args.prompt else ""

    if not prompt:
        print("\nSynthetic Document Factory (local)")
        print("Enter a context/prompt (leave blank for random). Examples:")
        print(
            "  - Utilities company billing reminders on pale blue paper, centered logo"
        )
        print("  - Healthcare clinic appointment letters, green accent, left header")
        print(
            "  - Logistics company delivery dispute letters, orange accent, right header"
        )
        print("  - Bank statements and letters, messy scans, digits hard to read")
        print(
            "Tip: you can include a fake company name in your prompt, e.g. 'Company: Foxmere Holdings (Synthetic)'.\n"
        )
        prompt = input("Prompt/context: ").strip()
        if not prompt:
            raw_n = input(f"How many documents? (default {count}): ").strip()
            count = int(raw_n) if raw_n else count

    generate_dataset(cfg, prompt_override=prompt, count_override=count)


if __name__ == "__main__":
    main()
