# System Prompt Configuration for Google Maps Tool

## Problem

By default, when the Google Maps tool returns formatted markdown output with embedded maps, the LLM may summarize or rewrite the content instead of displaying it exactly as formatted. This causes:

- Loss of formatting (emojis, markdown structure)
- Missing embedded maps (HTML iframes)
- Summarized text instead of detailed results

## Solution: Configure System Prompt

Add a system prompt to your model that instructs it to preserve tool output formatting.

## Step-by-Step Instructions

### 1. Access Model Settings

1. Open Open WebUI at http://localhost:3000
2. Click on **Workspace** in the sidebar
3. Click on the **Models** tab
4. Find your model (e.g., `llama3.2-3b-gpu40:latest`)
5. Click the **Edit** icon (pencil) next to the model name

### 2. Add System Prompt

In the **System Prompt** field, add the following:

```
You are a helpful AI assistant with access to Google Maps integration.

CRITICAL INSTRUCTION FOR GOOGLE MAPS TOOL:
When the Google Maps Integration tool returns output, you MUST copy and paste the ENTIRE output VERBATIM in your response. Do not summarize, describe, or paraphrase it.

Rules:
1. Copy the tool's output character-by-character
2. Keep ALL markdown: **, ##, 📍, ⭐, etc.
3. Keep ALL HTML: <iframe>, <div>, etc.
4. DO NOT say "the tool returned..." or "here are the results..."
5. DO NOT describe what the output contains
6. JUST show the formatted output directly

Example:
User: "Find pizza in Brooklyn"
Tool returns: "📍 Found 5 places..."
Your response: 📍 Found 5 places...  (copy the ENTIRE tool output)

For non-map queries, respond naturally.
```

### 3. Save Configuration

1. Click **Save** at the bottom of the model settings
2. Close the settings dialog

### 4. Test the Configuration

Start a new chat and try:

```
Find pizza restaurants in Brooklyn, New York
```

**Expected Output:**

You should now see:

```markdown
📍 Found 5 places for 'pizza restaurants' near Brooklyn, New York:

1. Lombardi's Pizza ⭐⭐⭐⭐⭐ 4.6/5 (1,234 reviews)
   📍 32 Spring St, New York, NY 10012
   🗺️ Coordinates: 40.721622, -73.995506
   🔗 [View on Google Maps](https://maps.google.com/...)
   🏷️ Types: restaurant, food, point_of_interest

2. Di Fara Pizza ⭐⭐⭐⭐⭐ 4.5/5 (2,567 reviews)
   📍 1424 Avenue J, Brooklyn, NY 11230
   🗺️ Coordinates: 40.625278, -73.961389
   🔗 [View on Google Maps](https://maps.google.com/...)
   🏷️ Types: restaurant, food, point_of_interest

... (more results)

## 🗺️ View on Map
[Interactive Google Maps iframe showing all locations]
```

## Alternative: Per-Chat Instructions

If you don't want to set a global system prompt, you can add instructions at the start of each chat:

```
I want you to display Google Maps tool results exactly as formatted, including all markdown and embedded maps. Don't summarize the output.

Now, find pizza restaurants in Brooklyn.
```

## Troubleshooting

### Maps Still Not Showing

**Issue**: Even with system prompt, maps don't appear

**Solutions**:

1. **Check API Key**: Ensure `GOOGLE_MAPS_EMBED_API_KEY` is configured in tool settings
   - Go to Workspace → Tools → Google Maps Integration → Settings
   - Add your Embed API key

2. **Check Embed Setting**: Verify `EMBED_MAPS` is set to `true`
   - In the same tool settings, check this option

3. **Try a Fresh Chat**: Start a completely new chat to ensure settings apply

4. **Check Model Capabilities**: Some smaller models may struggle with preserving formatting
   - Try a larger model (e.g., llama3.2:70b instead of llama3.2:3b)

### Formatting Still Lost

**Issue**: Text appears but without proper formatting

**Solutions**:

1. **Stronger System Prompt**: Make the instruction more explicit:
   ```
   CRITICAL: When the Google Maps tool returns output, you must copy it VERBATIM.
   Do not change a single character. Include every emoji, every markdown symbol,
   and every HTML tag exactly as provided. Your response should be a direct
   copy-paste of the tool's output.
   ```

2. **Use RAW Output Mode**: If available in Open WebUI settings
   - Check model settings for "Raw Output" or "Passthrough" mode

3. **Update Tool**: Ensure you're using the latest version (v2.0.0) which includes
   explicit formatting instructions in the docstrings

## Model-Specific Notes

### llama3.2:3b
- May require stronger system prompts
- Tends to summarize by default
- Works well with explicit instructions

### llama3.2:70b
- Better at preserving formatting
- Follows tool instructions more reliably
- Recommended for best results

### qwen2.5:72b
- Excellent at preserving structured output
- Very good at following formatting instructions
- Great choice for this use case

## Summary

To get properly formatted Google Maps results with embedded maps:

1. ✅ Add system prompt instructing the model to preserve tool output
2. ✅ Configure Google Maps Embed API key in tool settings
3. ✅ Start a new chat to apply settings
4. ✅ Test with a simple query

The combination of:
- Updated tool code (v2.0.0) with explicit formatting instructions
- System prompt configuration
- Properly configured API keys

Should result in beautifully formatted results with interactive embedded maps appearing directly in your chat!
