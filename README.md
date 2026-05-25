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

## So nutzt du die Integration (Anleitung)
1. Gehe in Home Assistant zu den Entwicklerwerkzeugen (Developer Tools).
2. Wähle den Tab **Dienste** (Services) aus.
3. Suche nach dem Dienst `AI Automation Prompt Builder: get_prompt` (`ai_automation_suggester.get_prompt`).
4. Führe den Dienst aus. Als Antwort erhältst du einen komprimierten Prompt (den sogenannten "System Prompt"), der eine Übersicht deiner Home Assistant Entitäten, Szenen, Skripte und bestehenden Automatisierungen enthält.
5. Kopiere den vollständigen Antwort-Text, wechsle zu einem KI-Tool deiner Wahl (z.B. ChatGPT, Claude, Gemini) und füge den Text dort ein.
6. Die KI beantwortet den Prompt, indem sie dir auf deine Heimautomatisierung maßgeschneiderte, smarte und nützliche neue Automatisierungsideen ausgibt!

## Optimizations
The source code has been highly optimized to produce concise memory-friendly prompts for modern AI models by minimizing redundant Home Assistant object data and extracting pure YAML representations.
