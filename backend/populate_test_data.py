#!/usr/bin/env python3
"""Script to populate PromptLab with realistic test data.

This script creates:
- 40+ prompts with natural language content
- 3-5 collections with descriptive names
- Random assignment of prompts to collections
- Random tags and descriptions
"""

import random
import requests
import json
import subprocess
import sys
from typing import List, Dict, Optional

def install_dependencies():
    """Install required dependencies if missing."""
    required_packages = ['faker', 'requests']

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing required package: {package}")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✓ Successfully installed {package}")
            except subprocess.CalledProcessError as e:
                print(f"✗ Failed to install {package}. Error: {e}")
                print(f"Please install {package} manually: pip install {package}")
                sys.exit(1)

# Install dependencies before importing them
install_dependencies()

from faker import Faker
import time

# Initialize Faker for realistic text generation
fake = Faker()
Faker.seed(42)  # For reproducible results

class TestDataGenerator:
    """Generates realistic test data for PromptLab."""

    def __init__(self):
        self.prompt_topics = [
            "Chatbot Personality", "Data Analysis", "Creative Writing",
            "Technical Documentation", "Customer Support", "Content Generation",
            "Code Review", "API Design", "Database Optimization",
            "Security Audit", "Performance Testing", "UX Research",
            "Product Management", "Marketing Strategy", "Sales Script",
            "Email Campaign", "Social Media Post", "Blog Article",
            "Technical Interview", "System Design", "Algorithm Explanation",
            "Debugging Guide", "CI/CD Pipeline", "DevOps Best Practices",
            "Cloud Architecture", "Microservices", "Monolith Conversion",
            "API Gateway", "Service Mesh", "Containerization",
            "Orchestration", "Infrastructure as Code", "Observability",
            "Monitoring", "Logging", "Tracing", "Incident Response",
            "Disaster Recovery", "Backup Strategy", "Compliance Check",
            "Risk Assessment", "Threat Modeling", "Penetration Testing"
        ]

        self.tag_categories = [
            ["AI", "Machine Learning", "Deep Learning", "NLP", "Computer Vision"],
            ["Chatbot", "Virtual Assistant", "Conversational AI", "Dialogue Systems"],
            ["Data Analysis", "Data Science", "Statistics", "Visualization", "ETL"],
            ["Creative Writing", "Storytelling", "Content Creation", "Copywriting"],
            ["Technical", "Documentation", "API", "SDK", "Library"],
            ["Testing", "QA", "Automation", "Unit Test", "Integration Test"],
            ["Security", "Compliance", "Audit", "Risk", "Threat"],
            ["DevOps", "CI/CD", "Infrastructure", "Cloud", "Container"],
            ["Product", "Management", "Strategy", "Roadmap", "Prioritization"],
            ["Marketing", "Sales", "Customer", "Support", "Engagement"]
        ]

        self.collection_themes = [
            "AI Assistants",
            "Creative Writing Prompts",
            "Data Analysis Templates",
            "Technical Documentation",
            "Customer Support Scripts",
            "Content Generation",
            "Code Review Guidelines",
            "API Design Patterns",
            "DevOps Best Practices",
            "Security and Compliance"
        ]

    def generate_prompt_title(self) -> str:
        """Generate a realistic prompt title."""
        topic = random.choice(self.prompt_topics)
        modifiers = [
            "Guide for", "Template for", "Best Practices for",
            "Checklist for", "Framework for", "Strategy for",
            "Tactics for", "Approach to", "Methodology for",
            "How to", "The Art of", "Mastering", "Essentials of"
        ]
        modifier = random.choice(modifiers)
        return f"{modifier} {topic}"

    def generate_prompt_content(self, title: str) -> str:
        """Generate realistic prompt content based on title."""
        # Generate paragraphs with realistic structure
        paragraphs = []
        topic_words = title.lower().split()

        # Introduction
        paragraphs.append(
            f"This prompt is designed to help with {random.choice(['creating', 'developing', 'improving', 'optimizing'])} "
            f"{random.choice(['solutions', 'strategies', 'approaches', 'implementations'])} related to {title.lower()}. "
            f"It provides a structured framework for {random.choice(['generating', 'evaluating', 'documenting', 'testing'])} "
            f"{random.choice(['ideas', 'code', 'content', 'systems'])} in the context of {title.lower()}."
        )

        # Main content with bullet points
        paragraphs.append("Key considerations:")
        for i in range(3, 8):
            paragraphs.append(
                f"- {random.choice(['Consider', 'Evaluate', 'Analyze', 'Document', 'Test'])} the {random.choice(['impact', 'effectiveness', 'quality', 'performance'])} "
                f"of {random.choice(['your', 'the', 'this'])} {title.lower()} implementation"
            )

        # Best practices
        paragraphs.append("\nBest practices:")
        for i in range(3, 6):
            paragraphs.append(
                f"- Always {random.choice(['validate', 'test', 'document', 'review', 'optimize'])} your {title.lower()} "
                f"before {random.choice(['deployment', 'release', 'sharing', 'presentation'])}"
            )

        # Conclusion
        paragraphs.append(
            f"By following this prompt, you should be able to {random.choice(['create', 'develop', 'improve', 'optimize'])} "
            f"high-quality {title.lower()} solutions that meet your requirements."
        )

        return "\n\n".join(paragraphs)

    def generate_description(self, title: str) -> str:
        """Generate a description for a prompt."""
        return (
            f"A comprehensive prompt for {title.lower()}, covering key aspects and best practices. "
            f"This template helps ensure consistency and quality in your {title.lower()} work."
        )

    def generate_tags(self, title: str, count: int = 3) -> List[str]:
        """Generate relevant tags for a prompt."""
        # Find relevant tag categories based on title keywords
        title_lower = title.lower()
        relevant_categories = []

        for category in self.tag_categories:
            for tag in category:
                if any(word in title_lower for word in tag.lower().split()):
                    relevant_categories.append(category)
                    break

        # If no specific match, use random categories
        if not relevant_categories:
            relevant_categories = random.sample(self.tag_categories, min(3, len(self.tag_categories)))

        # Select random tags from relevant categories
        tags = []
        for category in relevant_categories[:count]:
            if category:
                tags.append(random.choice(category))

        # Add some generic tags if needed
        while len(tags) < count:
            generic_tags = ["AI", "Template", "Best Practices", "Guide", "Framework"]
            new_tag = random.choice(generic_tags)
            if new_tag not in tags:
                tags.append(new_tag)

        return list(set(tags))  # Remove duplicates

    def generate_collection_name(self) -> str:
        """Generate a realistic collection name."""
        return random.choice(self.collection_themes)

    def generate_collection_description(self, name: str) -> str:
        """Generate a description for a collection."""
        return (
            f"A curated collection of prompts focused on {name.lower()}. "
            f"These templates help standardize and improve your work in this area."
        )

    def generate_prompts(self, count: int = 40) -> List[Dict]:
        """Generate a list of prompt data."""
        prompts = []
        for i in range(count):
            title = self.generate_prompt_title()
            content = self.generate_prompt_content(title)
            description = self.generate_description(title)
            tags = self.generate_tags(title)

            prompts.append({
                "title": title,
                "content": content,
                "description": description,
                "tags": tags
            })
        return prompts

    def generate_collections(self, count: int = 4) -> List[Dict]:
        """Generate a list of collection data."""
        collections = []
        for i in range(count):
            name = self.generate_collection_name()
            description = self.generate_collection_description(name)
            collections.append({
                "name": name,
                "description": description
            })
        return collections

class APIClient:
    """Client for interacting with the PromptLab API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def create_prompt(self, prompt_data: Dict) -> Optional[Dict]:
        """Create a new prompt via API."""
        try:
            response = self.session.post(
                f"{self.base_url}/prompts",
                data=json.dumps(prompt_data),
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error creating prompt: {e}")
            return None

    def create_collection(self, collection_data: Dict) -> Optional[Dict]:
        """Create a new collection via API."""
        try:
            response = self.session.post(
                f"{self.base_url}/collections",
                data=json.dumps(collection_data),
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error creating collection: {e}")
            return None

    def update_prompt(self, prompt_id: str, update_data: Dict) -> Optional[Dict]:
        """Update an existing prompt."""
        try:
            response = self.session.patch(
                f"{self.base_url}/prompts/{prompt_id}",
                data=json.dumps(update_data),
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error updating prompt {prompt_id}: {e}")
            return None

    def clear_data(self) -> bool:
        """Clear all existing data from the server."""
        try:
            # Get all prompts and delete them
            response = self.session.get(f"{self.base_url}/prompts")
            if response.status_code == 200:
                prompts = response.json().get("prompts", [])
                for prompt in prompts:
                    self.session.delete(f"{self.base_url}/prompts/{prompt['id']}")

            # Get all collections and delete them
            response = self.session.get(f"{self.base_url}/collections")
            if response.status_code == 200:
                collections = response.json().get("collections", [])
                for collection in collections:
                    self.session.delete(f"{self.base_url}/collections/{collection['id']}")

            return True
        except requests.exceptions.RequestException as e:
            print(f"Error clearing data: {e}")
            return False

def main():
    """Main function to populate test data."""
    import argparse

    parser = argparse.ArgumentParser(description="Populate PromptLab with test data.")
    parser.add_argument("--base-url", default="http://localhost:8000",
                       help="Base URL of the PromptLab API")
    parser.add_argument("--prompts", type=int, default=40,
                       help="Number of prompts to create")
    parser.add_argument("--collections", type=int, default=4,
                       help="Number of collections to create")
    parser.add_argument("--clear", action="store_true",
                       help="Clear existing data before populating")
    parser.add_argument("--dry-run", action="store_true",
                       help="Generate data without sending to API")
    parser.add_argument("--data-source", choices=["template", "dataset"], default="dataset",
                       help="Content source: 'dataset' (HuggingFace, default) or 'template' (built-in generator)")

    args = parser.parse_args()

    print(f"Populating test data...")
    print(f"Base URL: {args.base_url}")
    print(f"Prompts to create: {args.prompts}")
    print(f"Collections to create: {args.collections}")
    print(f"Clear existing data: {args.clear}")
    print(f"Dry run: {args.dry_run}")
    print(f"Data source: {args.data_source}")
    print()

    # Initialize generator and client
    generator = TestDataGenerator()
    client = APIClient(base_url=args.base_url)

    # ── Dataset mode: delegate entirely to the server-side admin endpoint ──
    if args.data_source == "dataset" and not args.dry_run:
        payload = {
            "num_prompts": args.prompts,
            "num_collections": args.collections,
            "append_mode": not args.clear,
            "data_source": "dataset",
        }
        print("Starting server-side population from HuggingFace dataset...")
        print("(First run downloads ~4 MB; subsequent runs use the local cache.)\n")
        resp = client.session.post(f"{args.base_url}/admin/populate-test-data", json=payload)
        if resp.status_code == 409:
            print("✗ A population job is already running. Try again after it finishes.")
            return
        resp.raise_for_status()

        # Poll progress until done
        while True:
            status = client.session.get(f"{args.base_url}/admin/populate-status").json()
            current = status.get("current", 0)
            total = status.get("total", args.prompts)
            error = status.get("error")
            active = status.get("active", True)
            pct = int(current / total * 100) if total else 0
            print(f"  Progress: {current}/{total} ({pct}%)", end="\r", flush=True)
            if error:
                print(f"\n✗ Error during population: {error}")
                return
            if not active:
                break
            time.sleep(1)

        print(f"\n✓ Created {status.get('prompts_created', args.prompts)} prompts "
              f"in {status.get('collections_created', args.collections)} collections")
        print("\nTest data population complete!")
        return

    # Clear existing data if requested
    if args.clear and not args.dry_run:
        print("Clearing existing data...")
        if client.clear_data():
            print("✓ Existing data cleared")
        else:
            print("✗ Failed to clear existing data")
        print()

    # Generate data
    print("Generating test data...")
    prompts = generator.generate_prompts(args.prompts)
    collections = generator.generate_collections(args.collections)
    print(f"✓ Generated {len(prompts)} prompts")
    print(f"✓ Generated {len(collections)} collections")
    print()

    if args.dry_run:
        print("Dry run complete. No data sent to API.")
        print("\nSample prompt:")
        print(f"Title: {prompts[0]['title']}")
        print(f"Tags: {prompts[0]['tags']}")
        print(f"\nSample collection:")
        print(f"Name: {collections[0]['name']}")
        return

    # Create collections first
    print("Creating collections...")
    created_collections = []
    for i, collection in enumerate(collections, 1):
        print(f"  Creating collection {i}/{len(collections)}: {collection['name']}")
        result = client.create_collection(collection)
        if result:
            created_collections.append(result)
            print(f"    ✓ Created (ID: {result['id']})")
        else:
            print(f"    ✗ Failed")
        time.sleep(0.1)  # Small delay to avoid overwhelming the server

    print()

    # Create prompts
    print("Creating prompts...")
    created_prompts = []
    for i, prompt in enumerate(prompts, 1):
        print(f"  Creating prompt {i}/{len(prompts)}: {prompt['title'][:50]}...")
        result = client.create_prompt(prompt)
        if result:
            created_prompts.append(result)
            print(f"    ✓ Created (ID: {result['id']})")
        else:
            print(f"    ✗ Failed")
        time.sleep(0.1)

    print()

    # Randomly assign prompts to collections
    if created_collections and created_prompts:
        print("Assigning prompts to collections...")
        for prompt in created_prompts:
            # Randomly decide if this prompt should be in a collection
            if random.random() < 0.6:  # 60% chance
                collection = random.choice(created_collections)
                update_data = {
                    "collection_id": collection["id"]
                }
                print(f"  Assigning prompt '{prompt['title'][:30]}...' to collection '{collection['name']}'")
                client.update_prompt(prompt["id"], update_data)
                time.sleep(0.05)

        print("✓ Prompts assigned to collections")
        print()

    # Print summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total prompts created: {len(created_prompts)}")
    print(f"Total collections created: {len(created_collections)}")
    print(f"Prompts in collections: {sum(1 for p in created_prompts if p.get('collection_id'))}")
    print(f"Prompts without collections: {sum(1 for p in created_prompts if not p.get('collection_id'))}")
    print()
    print("Test data population complete!")

if __name__ == "__main__":
    main()