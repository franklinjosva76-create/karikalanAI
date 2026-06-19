def detect_tech_stack(self, scraped_content: str, target_url: str = "", language_suffix: str = "") -> str:
        if not scraped_content or len(scraped_content) < 50:
            return "Insufficient content to detect tech stack."

        system_instruction = (
            "You are Karikalan AI (கரிகாலன் AI)'s tech stack detection engine. "
            "Analyze web content and identify the full technology stack with HIGH accuracy. "
            "Look for: meta tags, script imports, CSS conventions, API formats, "
            "framework-specific patterns, CDN URLs, build tool artifacts, error messages. "
            "Structure your response with these sections:\n"
            "🎨 Frontend | 🔧 Backend | 🗄️ Database | 🚀 Deployment | "
            "📦 Package Manager | 🎨 Styling | 🔗 APIs & Integrations | 🛠️ DevOps\n"
            "Rate each detection: [High/Medium/Low confidence]. "
            f"Only list what you can infer from the content. {language_suffix}"
        )

        prompt = (
            f"Target URL: {target_url or 'Not provided'}\n\n"
            f"=== SCRAPED CONTENT (first 5000 chars) ===\n"
            f"{scraped_content[:5000]}\n\n"
            "Detect and report the complete technology stack."
        )

        result, _ = self._infer(system_instruction, prompt)
        return result
