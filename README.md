# AI Automation Prompt Builder

This is a fork of the AI Automation Suggester, modified to just generate the prompt for you to manually copy and paste into an AI of your choice (like ChatGPT or Claude). It strips out all the API integration, API calls, parsing logic, and provider options.

## Features 
- Crawls your Home Assistant entities and existing automations.
- Builds a comprehensive system prompt string containing all this context.
- Exposes a ai_automation_suggester.get_prompt service that returns the raw prompt, so you can manually copy and paste it into any web-based AI.

## Installation (HACS)
1. Add this repository to HACS as a custom repository.
2. Download the integration.
3. Restart Home Assistant.
4. Go to Settings -> Devices & Services -> Add Integration and search for "AI Automation Prompt Builder".
